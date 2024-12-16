from pydantic import BaseModel, validator
from datetime import date
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

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
    def adjust_amount_based_on_type(cls, v, values):
        if 'transaction_type' in values and values['transaction_type'] == 'expense':
            return -abs(float(v))  # Make sure expense is negative and convert to float
        return abs(float(v))  # Make sure income is positive and convert to float

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

