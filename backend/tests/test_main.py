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
def test_create_transaction_invalid_data():
    # First create and login user
    client.post("/users/", json={
        "email": "test@example.com",
        "password": "testpass",
        "username": "testuser"
    })
    login_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    access_token = login_response.json()["access_token"]

    # Test invalid transaction data
    response = client.post(
        "/transactions/",
        json={
            "date": "invalid-date",
            "amount": "not-a-number",
            "category": "Test",
            "description": "Invalid"
        },
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422

def test_get_summary_empty_transactions():
    # Create and login user
    client.post("/users/", json={
        "email": "test@example.com",
        "password": "testpass",
        "username": "testuser"
    })
    login_response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/transactions/summary",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    data = response.json()
    assert data["total_income"] == 0
    assert data["total_expenses"] == 0
    assert data["net_balance"] == 0
