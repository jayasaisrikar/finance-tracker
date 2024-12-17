from pydantic import BaseModel, validator
from datetime import date
from typing import Optional
import re

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
            
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain at least one number")
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
            
        return v

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class TransactionBase(BaseModel):
    date: date
    amount: float
    transaction_type: str  # 'income' or 'expense'
    category: str
    description: str

    @validator('amount')
    def validate_and_adjust_amount(cls, v, values):
        # Check for zero amount
        if v == 0:
            raise ValueError("Transaction amount cannot be zero")
            
        # Adjust amount based on transaction type
        if 'transaction_type' in values and values['transaction_type'] == 'expense':
            return -abs(float(v))  # Make sure expense is negative
        return abs(float(v))  # Make sure income is positive

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

