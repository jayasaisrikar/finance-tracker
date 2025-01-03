import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from datetime import date, datetime, timedelta

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def user_create_data():
    return schemas.UserCreate(
        email="test@example.com",
        password="TestPass123!",
        username="testuser"
    )

@pytest.fixture
def test_user(db: Session, user_create_data):
    return crud.create_user(db, user_create_data)

# User Tests
def test_create_user_duplicate_email(db: Session):
    # Create first user
    user1 = schemas.UserCreate(
        email="test@example.com",
        password="TestPass123!",
        username="testuser1"
    )
    crud.create_user(db, user1)
    
    # Try to create second user with same email
    user2 = schemas.UserCreate(
        email="test@example.com",
        password="TestPass123!",
        username="testuser2"
    )
    with pytest.raises(Exception):
        crud.create_user(db, user2)

def test_create_user_duplicate_username(db: Session):
    user1 = schemas.UserCreate(
        email="test1@example.com",
        password="TestPass123!",
        username="testuser"
    )
    crud.create_user(db, user1)
    
    user2 = schemas.UserCreate(
        email="test2@example.com",
        password="TestPass123!",
        username="testuser"
    )
    with pytest.raises(Exception):
        crud.create_user(db, user2)

# Transaction Tests
def test_create_transaction_with_negative_amount(db: Session, test_user):
    transaction = schemas.TransactionCreate(
        date=date.today(),
        amount=100.50,
        transaction_type="expense",
        category="Food",
        description="Groceries"
    )
    db_transaction = crud.create_user_transaction(db, transaction, test_user.id)
    assert db_transaction.amount == -100.50

def test_get_transactions_by_date_range(db: Session):
    user = schemas.UserCreate(
        email="test@example.com",
        password="TestPass123!",  # Meets password requirements
        username="testuser"
    )
    db_user = crud.create_user(db, user)
    
    # Create transactions with different dates
    dates = [date.today() - timedelta(days=i) for i in range(10)]
    for d in dates:
        transaction = schemas.TransactionCreate(
            date=d,
            amount=100.0,
            transaction_type="income",
            category="Salary",
            description="Test"
        )
        crud.create_user_transaction(db, transaction, db_user.id)
    
    # Test date range query
    start_date = date.today() - timedelta(days=5)
    end_date = date.today()
    transactions = crud.get_transactions_by_date_range(db, db_user.id, start_date, end_date)
    assert len(transactions) == 6

def test_get_transactions_by_category(db: Session):
    user = schemas.UserCreate(
        email="test@example.com",
        password="TestPass123!",  # Meets password requirements
        username="testuser"
    )
    db_user = crud.create_user(db, user)
    
    categories = ["Food", "Transport", "Food", "Entertainment"]
    for category in categories:
        transaction = schemas.TransactionCreate(
            date=date.today(),
            amount=100.0,
            transaction_type="expense",
            category=category,
            description="Test"
        )
        crud.create_user_transaction(db, transaction, db_user.id)
    
    food_transactions = crud.get_transactions_by_category(db, db_user.id, "Food")
    assert len(food_transactions) == 2

def test_delete_nonexistent_transaction(db: Session):
    result = crud.delete_transaction(db, 999)
    assert result is None

def test_update_nonexistent_transaction(db: Session):
    transaction = schemas.TransactionCreate(
        date=date.today(),
        amount=100.0,
        transaction_type="income",
        category="Salary",
        description="Test"
    )
    result = crud.update_transaction(db, 999, transaction)
    assert result is None

def test_get_transactions_by_amount_range(db: Session):
    user = schemas.UserCreate(
        email="test@example.com",
        password="TestPass123!",  # Meets password requirements
        username="testuser"
    )
    db_user = crud.create_user(db, user)
    
    amounts = [50.0, 100.0, 150.0, 200.0]
    for amount in amounts:
        transaction = schemas.TransactionCreate(
            date=date.today(),
            amount=amount,
            transaction_type="expense",
            category="Test",
            description="Test"
        )
        crud.create_user_transaction(db, transaction, db_user.id)
    
    filtered_transactions = crud.get_transactions_by_amount_range(db, db_user.id, 75.0, 175.0)
    assert len(filtered_transactions) == 2 

def test_password_validation(db: Session):
    # Test too short password
    with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
        user = schemas.UserCreate(
            email="test@example.com",
            username="testuser",
            password="Abc1!"
        )
    
    # Test no uppercase
    with pytest.raises(ValueError, match="Password must contain at least one uppercase letter"):
        user = schemas.UserCreate(
            email="test@example.com",
            username="testuser",
            password="password1!"
        )
    
    # Test no number
    with pytest.raises(ValueError, match="Password must contain at least one number"):
        user = schemas.UserCreate(
            email="test@example.com",
            username="testuser",
            password="Password!"
        )
    
    # Test no special character
    with pytest.raises(ValueError, match="Password must contain at least one special character"):
        user = schemas.UserCreate(
            email="test@example.com",
            username="testuser",
            password="Password1"
        )
    
    # Test valid password
    user = schemas.UserCreate(
        email="test@example.com",
        username="testuser",
        password="Password1!"
    )
    assert user.password == "Password1!"

