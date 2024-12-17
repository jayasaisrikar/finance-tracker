import pytest
import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import login, signup

@pytest.fixture(autouse=True)
def setup_test():
    # Reset session state before each test
    st.session_state.access_token = None

def test_successful_login(requests_mock):
    # Mock the login API endpoint
    requests_mock.post(
        "http://localhost:8000/token",
        json={"access_token": "test_token", "token_type": "bearer"}
    )
    
    result = login("testuser", "password123")
    assert result == True
    assert st.session_state.access_token == "test_token"

def test_failed_login(requests_mock):
    # Mock failed login
    requests_mock.post(
        "http://localhost:8000/token",
        status_code=401
    )
    
    result = login("testuser", "wrongpassword")
    assert result == False
    assert st.session_state.access_token is None

def test_successful_signup(requests_mock):
    # Mock successful signup
    requests_mock.post(
        "http://localhost:8000/users/",
        json={"id": 1, "username": "testuser", "email": "test@example.com"}
    )
    
    result = signup("testuser", "test@example.com", "password123")
    assert result == True

def test_failed_signup_duplicate_user(requests_mock):
    # Mock duplicate user signup
    requests_mock.post(
        "http://localhost:8000/users/",
        status_code=400,
        json={"detail": "Username already taken"}
    )
    
    result = signup("existinguser", "test@example.com", "password123")
    assert result == False

def test_signup_invalid_email():
    result = signup("testuser", "invalidemail", "password123")
    assert result == False