import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Backend API URL
API_URL = "https://finance-tracker-th8d.onrender.com"

# Session state
if 'access_token' not in st.session_state:
    st.session_state.access_token = None

# Define categories for income and expenses
INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Investments",
    "Rental Income",
    "Business",
    "Other Income"
]

EXPENSE_CATEGORIES = [
    "Food",
    "Transportation",
    "Housing",
    "Utilities",
    "Healthcare",
    "Entertainment",
    "Shopping",
    "Education",
    "Insurance",
    "Savings",
    "Other Expenses"
]

def init_session():
    if 'access_token' in st.session_state:
        return st.session_state.access_token
    return None

def login(username, password):
    print(f"Attempting login for user: {username}")
    response = requests.post(f"{API_URL}/token", data={"username": username, "password": password})
    print(f"Login response status: {response.status_code}")
    print(f"Login response content: {response.text}")
    if response.status_code == 200:
        st.session_state.access_token = response.json()["access_token"]
        return True
    return False

def signup(username, email, password):
    try:
        response = requests.post(
            f"{API_URL}/users/", 
            json={"username": username, "email": email, "password": password}
        )
        
        if response.status_code == 200:
            return True
        elif response.status_code == 422:  # Validation error
            error_detail = response.json().get("detail", [{"msg": "Unknown error"}])[0]["msg"]
            st.error(f"Failed to create account: {error_detail}")
            return False
        elif response.status_code == 400:
            error_detail = response.json().get("detail", "Unknown error")
            st.error(f"Failed to create account: {error_detail}")
            return False
        else:
            st.error(f"Failed to create account. Status code: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return False

def get_transaction(transaction_id):
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.get(f"{API_URL}/transactions/{transaction_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def get_transactions():
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.get(f"{API_URL}/transactions/", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def add_transaction(date, amount, transaction_type, category, description):
    if amount == 0:
        st.error("Transaction amount cannot be zero")
        return False
        
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    data = {
        "date": date.strftime("%Y-%m-%d"),
        "amount": amount,
        "transaction_type": transaction_type,
        "category": category,
        "description": description
    }
    response = requests.post(f"{API_URL}/transactions/", json=data, headers=headers)
    if response.status_code == 200:
        st.success("Transaction added successfully.")
        return True
    else:
        error_detail = response.json().get("detail", "Failed to add transaction. Please try again.")
        st.error(error_detail)
        return False

def update_transaction(transaction_id, date, amount, transaction_type, category, description):
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    data = {
        "date": date,
        "amount": amount,
        "transaction_type": transaction_type,
        "category": category,
        "description": description
    }
    response = requests.put(f"{API_URL}/transactions/{transaction_id}", json=data, headers=headers)
    if response.status_code == 200:
        st.success("Transaction updated successfully.")
        return True
    else:
        error_detail = response.json().get("detail", "Failed to update transaction. Please try again.")
        st.error(error_detail)
        return False

def delete_transaction(transaction_id):
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    try:
        response = requests.delete(f"{API_URL}/transactions/{transaction_id}", headers=headers)
        if response.status_code == 200:
            st.success("Transaction deleted successfully.")
            return True
        elif response.status_code == 404:
            st.error("Transaction not found.")
            return False
        elif response.status_code == 403:
            st.error("Not authorized to delete this transaction.")
            return False
        else:
            error_detail = response.json().get("detail", "Failed to delete transaction. Please try again.")
            st.error(error_detail)
            return False
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return False

def get_summary():
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.get(f"{API_URL}/transactions/summary", headers=headers)
    if response.status_code == 200:
        return response.json()
    return {"total_income": 0, "total_expenses": 0, "net_balance": 0}

def main():
    st.set_page_config(page_title="Personal Finance Tracker", layout="wide")
    st.title("Personal Finance Tracker")
    token = init_session()
    if token:
        st.session_state.access_token = token

    if st.session_state.access_token is None:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.header("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login"):
                if login(username, password):
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

        with tab2:
            st.header("Sign Up")
            new_username = st.text_input("New Username", key="signup_username")
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("New Password", type="password", key="signup_password")
            if st.button("Sign Up"):
                if new_username and new_email and new_password:
                    if "@" not in new_email or "." not in new_email:
                        st.error("Please enter a valid email address (must contain '@' and '.')")
                    else:
                        if signup(new_username, new_email, new_password):
                            st.success("Account created successfully. Please log in.")
                else:
                    st.error("Please fill in all fields.")

    else:
        st.sidebar.title("Menu")
        menu = st.sidebar.radio(
            "Navigation",
            ["Dashboard", "Analysis", "Add Transaction", "Transaction List"]
        )

        if menu == "Dashboard":
            st.header("Dashboard")
            summary = get_summary()
            st.markdown("""
                <style>
                .metric-container {
                    background-color: #f0f2f6;
                    padding: 0px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
                </style>
            """, unsafe_allow_html=True)
            
            with st.container():
                st.markdown('<div class="metric-container">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Income", f"${summary['total_income']:.2f}", delta=None)
                col2.metric("Total Expenses", f"${summary['total_expenses']:.2f}", delta=None)
                col3.metric("Net Balance", f"${summary['net_balance']:.2f}", 
                           delta=summary['net_balance'] - summary['total_expenses'])
                st.markdown('</div>', unsafe_allow_html=True)

            transactions = get_transactions()
            if transactions:
                df = pd.DataFrame(transactions)
                df['date'] = pd.to_datetime(df['date'])
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Monthly Overview")
                    monthly_df = df.copy()
                    monthly_df['month'] = monthly_df['date'].dt.strftime('%Y-%m')
                    monthly_summary = monthly_df.groupby(['month', 'transaction_type'])['amount'].sum().unstack().fillna(0)

                    if 'income' not in monthly_summary.columns:
                        monthly_summary['income'] = 0
                    if 'expense' not in monthly_summary.columns:
                        monthly_summary['expense'] = 0

                    monthly_summary['net'] = monthly_summary['income'] - abs(monthly_summary['expense'])

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=monthly_summary.index,
                        y=monthly_summary['income'],
                        name='Income',
                        marker_color='lightgreen'
                    ))
                    fig.add_trace(go.Bar(
                        x=monthly_summary.index,
                        y=-monthly_summary['expense'],
                        name='Expenses',
                        marker_color='lightblue'
                    ))
                    fig.add_trace(go.Scatter(
                        x=monthly_summary.index,
                        y=monthly_summary['net'],
                        name='Net',
                        line=dict(color='blue', width=2),
                        mode='lines+markers'
                    ))

                    fig.update_layout(
                        title='Monthly Financial Overview',
                        barmode='relative',
                        height=400,
                        hovermode='x unified',
                        yaxis_title='Amount ($)',
                        xaxis_title='Month'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    if monthly_summary['expense'].sum() == 0:
                        st.info("No expenses recorded yet. Add some expense transactions to see the complete analysis.")

                with col2:
                    # Daily Transactions
                    st.subheader("Daily Transactions")
                    daily_summary = df.groupby(['date', 'transaction_type'])['amount'].sum().reset_index()
                    fig = px.scatter(daily_summary, 
                                   x='date', 
                                   y='amount',
                                   color='transaction_type',
                                   size='amount',
                                   title='Daily Transaction Overview',
                                   labels={'date': 'Date', 'amount': 'Amount ($)', 'transaction_type': 'Type'})
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

                # Category Analysis in two columns
                st.subheader("Category Analysis")
                col1, col2 = st.columns(2)
                
                with col1:
                    expense_df = df[df['transaction_type'] == 'expense']
                    if not expense_df.empty:
                        expense_by_category = expense_df.groupby('category')['amount'].sum().abs()
                        fig = px.pie(values=expense_by_category.values, 
                                   names=expense_by_category.index, 
                                   title='Expenses by Category',
                                   hole=0.4)
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No expense data available")
                
                with col2:
                    income_df = df[df['transaction_type'] == 'income']
                    if not income_df.empty:
                        income_by_category = income_df.groupby('category')['amount'].sum()
                        fig = px.pie(values=income_by_category.values, 
                                   names=income_by_category.index, 
                                   title='Income by Category',
                                   hole=0.4)
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No income data available")

                st.subheader("Recent Transactions")
                recent_transactions = df.sort_values('date', ascending=False).head(5)
                st.dataframe(
                    recent_transactions[['date', 'transaction_type', 'amount', 'category', 'description']],
                    use_container_width=True
                )
            else:
                st.info("No transactions found. Add some transactions to see your financial analysis.")

        elif menu == "Add Transaction":
            st.header("Transaction Management")
            st.markdown("""
                <style>
                .stSelectbox, .stDateInput, .stNumberInput {
                    margin-bottom: 1rem;
                }
                .transaction-form {
                    background-color: #f8f9fa;
                    padding: 0px;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                </style>
            """, unsafe_allow_html=True)

            with st.container():
                st.markdown('<div class="transaction-form">', unsafe_allow_html=True)
                
                transaction_type = st.selectbox(
                    "Transaction Type",
                    ["income", "expense"],
                    key="trans_type_select",
                    format_func=lambda x: x.capitalize()
                )

                with st.form(key=f"transaction_form_{transaction_type}", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        date = st.date_input(
                            "Date",
                            help="Select the date of the transaction"
                        )
                        amount = st.number_input(
                            "Amount ($)",
                            min_value=0.01,
                            step=0.01,
                            help="Enter the transaction amount"
                        )
                    
                    with col2:
                        categories = INCOME_CATEGORIES if transaction_type == "income" else EXPENSE_CATEGORIES
                        category = st.selectbox(
                            "Category",
                            options=categories,
                            key=f"category_{transaction_type}",
                            help="Select the transaction category"
                        )
                        description = st.text_input(
                            "Description",
                            placeholder="Enter transaction description",
                            help="Add a brief description of the transaction"
                        )
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        submitted = st.form_submit_button(
                            "Add Transaction",
                            use_container_width=True,
                            type="primary"
                        )
                    
                    if submitted:
                        add_transaction(date, amount, transaction_type, category, description)
                
                st.markdown('</div>', unsafe_allow_html=True)

            st.subheader("Existing Transactions")
            transactions = get_transactions()
            if transactions:
                df = pd.DataFrame(transactions)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date', ascending=False)
                st.dataframe(df[['date', 'amount', 'transaction_type', 'category', 'description']])

                transaction_options = df.apply(lambda row: f"{row['description']} ({row['category']}) - ID: {row['id']-1}", axis=1).tolist()
                selected_transaction_index = st.selectbox("Select Transaction to Delete", range(len(transaction_options)), format_func=lambda x: transaction_options[x])

                if st.button("Delete Transaction"):
                    selected_transaction_id = df.iloc[selected_transaction_index]['id']
                    delete_transaction(selected_transaction_id)

        elif menu == "Transaction List":
            st.header("Transaction List")
            transactions = get_transactions()
            df = pd.DataFrame(transactions)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date', ascending=False)

                st.subheader("Filters")
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    start_date = st.date_input("Start Date", df['date'].min())
                with col2:
                    end_date = st.date_input("End Date", df['date'].max())
                with col3:
                    category_filter = st.multiselect("Category", df['category'].unique())
                with col4:
                    min_amount = st.number_input("Min Amount", value=float(df['amount'].min()))
                with col5:
                    max_amount = st.number_input("Max Amount", value=float(df['amount'].max()))

                filtered_df = df[(df['date'] >= pd.Timestamp(start_date)) & (df['date'] <= pd.Timestamp(end_date))]
                if category_filter:
                    filtered_df = filtered_df[filtered_df['category'].isin(category_filter)]
                filtered_df = filtered_df[(filtered_df['amount'] >= min_amount) & (filtered_df['amount'] <= max_amount)]

                st.dataframe(filtered_df[['date', 'amount', 'category', 'description']])
            else:
                st.info("No transactions found. Add some transactions to see them here.")

        elif menu == "Analysis":
            st.header("Financial Analysis")
            transactions = get_transactions()
            if transactions:
                df = pd.DataFrame(transactions)
                df['date'] = pd.to_datetime(df['date'])
                
                total_income = abs(sum(t['amount'] for t in transactions if t['transaction_type'] == 'income'))
                total_expenses = abs(sum(t['amount'] for t in transactions if t['transaction_type'] == 'expense'))
                
                if total_income > 0:
                    expense_ratio = (total_expenses / total_income) * 100
                    
                    col1, col2, col3 = st.columns([2, 1, 2])
                    
                    with col1:
                        st.subheader("Expense Ratio")
                        # Expense Ratio Gauge Chart
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number+delta",
                            value=expense_ratio,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            delta={'reference': 50},
                            title={'text': "Expense to Income Ratio (%)"},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [0, 50], 'color': "lightgreen"},
                                    {'range': [50, 70], 'color': "yellow"},
                                    {'range': [70, 100], 'color': "red"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': 70
                                }
                            }
                        ))
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)

                    with col3:
                        st.subheader("Financial Status")
                        if expense_ratio <= 50:
                            st.success("🌟 Excellent Financial Health!")
                            st.markdown("""
                                - You're saving more than 50% of your income
                                - Great job maintaining financial discipline
                                - Consider investing your surplus
                                - Keep building your emergency fund
                            """)
                        elif expense_ratio <= 70:
                            st.warning("⚠️ Caution Zone")
                            st.markdown("""
                                - Expenses are getting high
                                - Review your monthly subscriptions
                                - Look for areas to reduce spending
                                - Avoid taking on new debt
                            """)
                        else:
                            st.error("🚨 Financial Alert!")
                            st.markdown("""
                                - Expenses are critically high
                                - Immediate action required
                                - Cut non-essential spending
                                - Consider additional income sources
                                - Create an emergency budget
                            """)

                    # Spending Analysis
                    st.subheader("Spending Analysis")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Category-wise Expenses Bar Chart
                        expense_df = df[df['transaction_type'] == 'expense']
                        if not expense_df.empty:
                            expense_by_category = expense_df.groupby('category')['amount'].sum().abs().sort_values(ascending=True)
                            fig = px.bar(
                                x=expense_by_category.values,
                                y=expense_by_category.index,
                                orientation='h',
                                title='Expenses by Category',
                                labels={'x': 'Amount ($)', 'y': 'Category'}
                            )
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        # Spending Patterns
                        monthly_df = df.copy()
                        monthly_df['month'] = monthly_df['date'].dt.strftime('%Y-%m')
                        monthly_df['week'] = monthly_df['date'].dt.strftime('%U')
                        spending_patterns = monthly_df[monthly_df['transaction_type'] == 'expense'].groupby(['month', 'category'])['amount'].sum().abs()

                        fig = px.sunburst(
                            spending_patterns.reset_index(),
                            path=['month', 'category'],
                            values='amount',
                            title='Monthly Spending Patterns',
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Please add some income transactions to see financial health analysis.")
            else:
                st.info("No transactions found. Add some transactions to see your financial analysis.")

        if st.sidebar.button("Logout"):
            st.session_state.access_token = None
            st.rerun()

if __name__ == "__main__":
    main()

