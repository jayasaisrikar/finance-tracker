from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import crud, models, schemas, auth
from .database import engine, get_db
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Backend is live and running!"}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://fintracker.streamlit.app/","https://fin-tracker.streamlit.app/"],  # Connect to streamlit app
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    return crud.create_user(db=db, user=user)

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user

@app.post("/transactions/", response_model=schemas.Transaction)
def create_transaction(
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    return crud.create_user_transaction(db=db, transaction=transaction, user_id=current_user.id)

@app.get("/transactions/", response_model=list[schemas.Transaction])
def read_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    transactions = crud.get_transactions(db, user_id=current_user.id, skip=skip, limit=limit)
    return transactions

@app.put("/transactions/{transaction_id}", response_model=schemas.Transaction)
def update_transaction(
    transaction_id: int,
    transaction: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if db_transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this transaction")
    return crud.update_transaction(db=db, transaction_id=transaction_id, transaction=transaction)

@app.delete("/transactions/{transaction_id}", response_model=schemas.Transaction)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    db_transaction = crud.get_transaction(db, transaction_id=transaction_id)
    if db_transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if db_transaction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this transaction")
    return crud.delete_transaction(db=db, transaction_id=transaction_id)

@app.get("/transactions/summary")
def get_transaction_summary(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    transactions = crud.get_transactions(db, user_id=current_user.id)
    total_income = sum(t.amount for t in transactions if t.transaction_type == "income")
    total_expenses = abs(sum(t.amount for t in transactions if t.transaction_type == "expense"))
    net_balance = total_income - total_expenses
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": net_balance
    }

@app.get("/transactions/by-amount/")
def get_transactions_by_amount(
    min_amount: float,
    max_amount: float,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    transactions = crud.get_transactions_by_amount_range(
        db, 
        user_id=current_user.id, 
        min_amount=min_amount, 
        max_amount=max_amount
    )
    return transactions

