from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
from . import auth

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    print(f"Creating user with hashed password: {hashed_password}")  # Debug print
    db_user = models.User(
        email=user.email, 
        username=user.username, 
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_transactions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).filter(models.Transaction.user_id == user_id).offset(skip).limit(limit).all()

def create_user_transaction(db: Session, transaction: schemas.TransactionCreate, user_id: int):
    transaction_dict = transaction.dict()
    # Ensure the amount is properly converted based on transaction type
    if transaction_dict['transaction_type'] == 'expense':
        transaction_dict['amount'] = -abs(transaction_dict['amount'])
    else:
        transaction_dict['amount'] = abs(transaction_dict['amount'])
    
    db_transaction = models.Transaction(**transaction_dict, user_id=user_id)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def update_transaction(db: Session, transaction_id: int, transaction: schemas.TransactionCreate):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if db_transaction:
        for key, value in transaction.dict().items():
            setattr(db_transaction, key, value)
        db.commit()
        db.refresh(db_transaction)
    return db_transaction

def delete_transaction(db: Session, transaction_id: int):
    db_transaction = db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()
    if db_transaction:
        db.delete(db_transaction)
        db.commit()
    return db_transaction

def get_transactions_by_date_range(db: Session, user_id: int, start_date: datetime, end_date: datetime):
    return db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.date >= start_date,
        models.Transaction.date <= end_date
    ).all()

def get_transactions_by_category(db: Session, user_id: int, category: str):
    return db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.category == category
    ).all()

def get_transactions_by_amount_range(db: Session, user_id: int, min_amount: float, max_amount: float):
    return db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.amount >= min_amount,
        models.Transaction.amount <= max_amount
    ).all()

