import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app, get_db
import pytest
from datetime import date

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Authentication Tests
def test_login_invalid_credentials():
    response = client.post(
        "/token",
        data={"username": "nonexistent", "password": "wrong"}
    )
    assert response.status_code == 401

def test_access_protected_route_without_token():
    response = client.get("/transactions/")
    assert response.status_code == 401

def test_access_protected_route_with_invalid_token():
    response = client.get(
        "/transactions/",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

# Transaction API Tests
@pytest.fixture
def auth_headers():
    # Create a test user
    response = client.post("/users/", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "username": "testuser"
    })
    assert response.status_code == 200

    # Login to get token
    login_response = client.post(
        "/token",
        data={"username": "testuser", "password": "TestPass123!"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_transaction_invalid_data(auth_headers):
    response = client.post(
        "/transactions/",
        json={
            "date": "invalid-date",
            "amount": "not-a-number",
            "category": "Test",
            "description": "Invalid"
        },
        headers=auth_headers
    )
    assert response.status_code == 422

def test_get_summary_empty_transactions(auth_headers):
    response = client.get(
        "/transactions/summary",
        headers=auth_headers
    )
    data = response.json()
    assert data["total_income"] == 0
    assert data["total_expenses"] == 0
    assert data["net_balance"] == 0

def test_create_transaction_with_zero_amount(auth_headers):
    response = client.post(
        "/transactions/",
        json={
            "date": str(date.today()),
            "amount": 0,
            "transaction_type": "expense",
            "category": "Test",
            "description": "Zero amount test"
        },
        headers=auth_headers
    )
    assert response.status_code == 422
    assert "Transaction amount cannot be zero" in response.json()["detail"][0]["msg"]

def test_get_transactions_by_amount_range(auth_headers):
    # Create some test transactions
    transactions = [
        {"date": str(date.today()), "amount": 50.0, "transaction_type": "expense", "category": "Food", "description": "Test"},
        {"date": str(date.today()), "amount": 100.0, "transaction_type": "expense", "category": "Transport", "description": "Test"},
        {"date": str(date.today()), "amount": 150.0, "transaction_type": "income", "category": "Salary", "description": "Test"}
    ]
    
    for transaction in transactions:
        client.post(
            "/transactions/",
            json=transaction,
            headers=auth_headers
        )

    # Test amount range filter
    response = client.get(
        "/transactions/by-amount/?min_amount=40&max_amount=120",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    filtered_transactions = response.json()
    assert len(filtered_transactions) == 2

