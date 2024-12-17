import pytest
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import main

@pytest.fixture
def sample_transactions():
    return pd.DataFrame({
        'date': ['2024-03-01', '2024-03-02', '2024-03-03'],
        'amount': [1000, -50, -30],
        'transaction_type': ['income', 'expense', 'expense'],
        'category': ['Salary', 'Food', 'Transport'],
        'description': ['Monthly salary', 'Groceries', 'Bus fare']
    })

def test_expense_ratio_calculation(sample_transactions):
    total_income = sample_transactions[sample_transactions['transaction_type'] == 'income']['amount'].sum()
    total_expenses = abs(sample_transactions[sample_transactions['transaction_type'] == 'expense']['amount'].sum())
    expense_ratio = (total_expenses / total_income) * 100
    assert expense_ratio == 8.0

def test_category_analysis(sample_transactions):
    expense_df = sample_transactions[sample_transactions['transaction_type'] == 'expense']
    category_totals = expense_df.groupby('category')['amount'].sum().abs()
    assert len(category_totals) == 2
    assert category_totals['Food'] == 50
    assert category_totals['Transport'] == 30

@patch('streamlit.plotly_chart')
def test_monthly_overview_chart(mock_plotly_chart, sample_transactions):
    monthly_df = sample_transactions.copy()
    monthly_df['date'] = pd.to_datetime(monthly_df['date'])
    monthly_df['month'] = monthly_df['date'].dt.strftime('%Y-%m')
    
    monthly_summary = monthly_df.groupby(['month', 'transaction_type'])['amount'].sum().unstack().fillna(0)
    assert monthly_summary['income'].iloc[0] == 1000
    assert monthly_summary['expense'].iloc[0] == -80