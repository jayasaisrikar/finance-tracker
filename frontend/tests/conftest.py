import pytest
import streamlit as st
from unittest.mock import MagicMock

class MockSessionState(dict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)

@pytest.fixture(autouse=True)
def mock_streamlit():
    # Create a mock session state
    session_state = MockSessionState(access_token=None)
    st.session_state = session_state
    st.error = MagicMock()
    st.success = MagicMock()
    st.info = MagicMock()
    st.rerun = MagicMock()
    
    return st
