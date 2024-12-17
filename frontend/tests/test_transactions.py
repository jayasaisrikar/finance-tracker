import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import get_transactions, add_transaction, get_summary

@pytest.fixture(autouse=True)
def setup_test():
    # Initialize session state before each test
    st.session_state.access_token = "test_token"

def test_get_transactions_success(requests_mock):
    mock_transactions = [
        {
            "id": 1,
            "date": "2024-03-20",
            "amount": 1000.0,
            "transaction_type": "income",
            "category": "Salary",
            "description": "Monthly salary"
        }
    ]
    requests_mock.get(
        "http://localhost:8000/transactions/",
        json=mock_transactions
    )
    
    transactions = get_transactions()
    assert len(transactions) == 1
    assert transactions[0]["amount"] == 1000.0

def test_add_transaction_success(requests_mock):
    # Mock successful transaction addition
    requests_mock.post(
        "http://localhost:8000/transactions/",
        json={
            "id": 1,
            "date": "2024-03-20",
            "amount": 50.0,
            "transaction_type": "expense",
            "category": "Food",
            "description": "Groceries"
        },
        status_code=200
    )
    
    result = add_transaction(
        "2024-03-20",
        50.0,
        "expense",
        "Food",
        "Groceries"
    )
    assert result is True

def test_get_summary_success(requests_mock):
    # Mock successful summary fetch
    mock_summary = {
        "total_income": 1000.0,
        "total_expenses": 500.0,
        "net_balance": 500.0
    }
    requests_mock.get(
        "http://localhost:8000/transactions/summary",
        json=mock_summary
    )
    
    summary = get_summary()
    assert summary["total_income"] == 1000.0
    assert summary["total_expenses"] == 500.0
    assert summary["net_balance"] == 500.0