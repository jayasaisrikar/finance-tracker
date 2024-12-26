import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
# import os
# from dotenv import load_dotenv

## api endpoint for the backend service
API_URL = "https://finance-tracker-th8d.onrender.com"

## keep track of user's login status
if 'access_token' not in st.session_state:
    st.session_state.access_token = None

## list of possible income sources
INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Investments",
    "Rental Income",
    "Business",
    "Other Income"
]

## common expense categories
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

## let's check if user is already logged in
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
    with st.spinner('Loading transactions...'):
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
        #st.success("Transaction updated successfully.")
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

def update_transaction_ui(transaction_id, date, amount, transaction_type, category, description):
    st.subheader("Update Transaction")
    
    ## create form for editing
    with st.form(key=f"edit_transaction_form_{transaction_id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_date = st.date_input(
                "Date",
                value=pd.to_datetime(date).date(),
                help="Select the date of the transaction"
            )
            new_amount = st.number_input(
                "Amount ($)",
                value=abs(float(amount)),
                min_value=0.01,
                step=0.01,
                help="Enter the transaction amount"
            )
        
        with col2:
            new_type = st.selectbox(
                "Transaction Type",
                ["income", "expense"],
                index=0 if transaction_type == "income" else 1,
                help="Select the transaction type"
            )
            categories = INCOME_CATEGORIES if new_type == "income" else EXPENSE_CATEGORIES
            new_category = st.selectbox(
                "Category",
                options=categories,
                index=categories.index(category) if category in categories else 0,
                help="Select the transaction category"
            )
            new_description = st.text_input(
                "Description",
                value=description,
                help="Add a brief description of the transaction"
            )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "Update Transaction",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            success = update_transaction(
                transaction_id,
                new_date.strftime("%Y-%m-%d"),
                new_amount,
                new_type,
                new_category,
                new_description
            )
            if success:
                st.success("Transaction updated successfully!")
                time.sleep(1)  # Give user time to see the success message
                st.rerun()
            else:
                st.error("Failed to update transaction. Please try again.")

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
        menu = st.sidebar.selectbox(
            "Navigation",
            ["Dashboard", "Analysis", "Add Transaction", "Transaction List", "User Manual"]
        )

        if menu == "Dashboard":
            col1, col2 = st.columns([0.65, 0.35])
            with col1:
                st.header("Dashboard")
            
            ## add month selector
            transactions = get_transactions()
            if transactions:
                df = pd.DataFrame(transactions)
                df['date'] = pd.to_datetime(df['date'])
                df['month'] = df['date'].dt.strftime('%Y-%m')
                available_months = sorted(df['month'].unique(), reverse=True)
                current_month = datetime.now().strftime('%Y-%m')
                
                with col2:
                    st.markdown("""
                        <style>
                        div[data-testid="stSelectbox"] {
                            margin-top: 15px;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    selected_month = st.selectbox(
                        "📅 Select Month",
                        options=available_months,
                        index=available_months.index(current_month) if current_month in available_months else 0,
                        key="dashboard_month_selector"
                    )
                
                ## filter transactions for selected month
                monthly_df = df[df['month'] == selected_month]
                
                ## calculate monthly summary
                monthly_income = abs(monthly_df[monthly_df['transaction_type'] == 'income']['amount'].sum())
                monthly_expenses = abs(monthly_df[monthly_df['transaction_type'] == 'expense']['amount'].sum())
                monthly_balance = monthly_income - monthly_expenses
                
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
                    col1.metric("Monthly Income", f"${monthly_income:.2f}", delta=None)
                    col2.metric("Monthly Expenses", f"${monthly_expenses:.2f}", delta=None)
                    col3.metric("Monthly Balance", f"${monthly_balance:.2f}", 
                               delta=monthly_balance - monthly_expenses)
                    st.markdown('</div>', unsafe_allow_html=True)

                ## Add Monthly Overview plot
                st.subheader("Monthly Overview")
                monthly_summary = df.groupby(['month', 'transaction_type'])['amount'].sum().unstack().fillna(0)

                if 'income' not in monthly_summary.columns:
                    monthly_summary['income'] = 0  ## no income yet? start with zero
                if 'expense' not in monthly_summary.columns:
                    monthly_summary['expense'] = 0  ## same for expenses

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

                ## Daily Transactions (Full Width)
                st.subheader("Daily Transactions")
                daily_summary = monthly_df.groupby(['date', 'transaction_type'])['amount'].sum().reset_index()
                fig = px.scatter(daily_summary, 
                                x='date', 
                                y='amount',
                                color='transaction_type',
                                size='amount',
                                title=f'Daily Transactions for {selected_month}',
                                labels={'date': 'Date', 'amount': 'Amount ($)', 'transaction_type': 'Type'})
                fig.update_layout(
                    height=500,  # Increased height for full-page feel
                    hovermode='x unified',
                    yaxis_title='Amount ($)',
                    xaxis_title='Date'
                )
                st.plotly_chart(fig, use_container_width=True)

                ## Category Analysis - Side by Side
                st.subheader("Category Analysis")
                col1, col2 = st.columns(2)

                with col1:
                    ## Expense Analysis
                    expense_df = monthly_df[monthly_df['transaction_type'] == 'expense']
                    if not expense_df.empty:
                        expense_by_category = expense_df.groupby('category')['amount'].sum().abs()
                        fig_expense = px.pie(
                            values=expense_by_category.values, 
                            names=expense_by_category.index, 
                            title=f'Expenses by Category for {selected_month}',
                            hole=0.4
                        )
                        fig_expense.update_layout(height=400)
                        st.plotly_chart(fig_expense, use_container_width=True)
                    else:
                        st.info("No expenses recorded for this month")

                with col2:
                    ## Income Analysis
                    income_df = monthly_df[monthly_df['transaction_type'] == 'income']
                    if not income_df.empty:
                        income_by_category = income_df.groupby('category')['amount'].sum()
                        fig_income = px.pie(
                            values=income_by_category.values, 
                            names=income_by_category.index, 
                            title=f'Income by Category for {selected_month}',
                            hole=0.4
                        )
                        fig_income.update_layout(height=400)
                        st.plotly_chart(fig_income, use_container_width=True)
                    else:
                        st.info("No income recorded for this month")

                ## Recent Transactions for the selected month
                st.subheader(f"Recent Transactions for {selected_month}")
                recent_transactions = monthly_df.sort_values('date', ascending=False)
                if not recent_transactions.empty:
                    st.dataframe(
                        recent_transactions[['date', 'transaction_type', 'amount', 'category', 'description']],
                        use_container_width=True
                    )
                else:
                    st.info("No transactions found for this month")
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

                if not filtered_df.empty:
                    st.subheader("Update Transaction")
                    transaction_options = filtered_df.apply(
                        lambda row: f"{row['date'].strftime('%Y-%m-%d')} - {row['description']} ({row['category']}) - ${abs(row['amount'])}", 
                        axis=1
                    ).tolist()
                    
                    selected_transaction_index = st.selectbox(
                        "Select Transaction to Update",
                        range(len(transaction_options)),
                        format_func=lambda x: transaction_options[x]
                    )
                    
                    selected_transaction = filtered_df.iloc[selected_transaction_index]
                    update_transaction_ui(
                        selected_transaction['id'],
                        selected_transaction['date'],
                        selected_transaction['amount'],
                        selected_transaction['transaction_type'],
                        selected_transaction['category'],
                        selected_transaction['description']
                    )
            else:
                st.info("No transactions found. Add some transactions to see them here.")

        elif menu == "Analysis":
            st.header("Financial Analysis")
            transactions = get_transactions()
            if transactions:
                df = pd.DataFrame(transactions)
                df['date'] = pd.to_datetime(df['date'])
                df['month'] = df['date'].dt.strftime('%Y-%m')
                available_months = sorted(df['month'].unique(), reverse=True)
                current_month = datetime.now().strftime('%Y-%m')
                
                selected_month = st.selectbox(
                    "Select Month",
                    options=available_months,
                    index=available_months.index(current_month) if current_month in available_months else 0
                )
                
                ## filter transactions for selected month
                monthly_df = df[df['month'] == selected_month]
                
                ## calculate monthly totals
                monthly_income = abs(monthly_df[monthly_df['transaction_type'] == 'income']['amount'].sum())
                monthly_expenses = abs(monthly_df[monthly_df['transaction_type'] == 'expense']['amount'].sum())
                
                if monthly_income > 0:
                    expense_ratio = (monthly_expenses / monthly_income) * 100
                    
                    col1, col2, col3 = st.columns([2, 1, 2])
                    
                    with col1:
                        st.subheader(f"Expense Ratio for {selected_month}")
                        ## expense ratio gauge chart
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
                        st.subheader(f"Financial Status for {selected_month}")
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

                    ## Spending Analysis
                    st.subheader(f"Spending Analysis for {selected_month}")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        ## category-wise expenses bar chart
                        expense_df = monthly_df[monthly_df['transaction_type'] == 'expense']
                        if not expense_df.empty:
                            expense_by_category = expense_df.groupby('category')['amount'].sum().abs().sort_values(ascending=True)
                            fig = px.bar(
                                x=expense_by_category.values,
                                y=expense_by_category.index,
                                orientation='h',
                                title=f'Expenses by Category for {selected_month}',
                                labels={'x': 'Amount ($)', 'y': 'Category'}
                            )
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No expenses recorded for this month")
                    
                    with col2:
                        ## monthly spending pattern
                        if not monthly_df[monthly_df['transaction_type'] == 'expense'].empty:
                            daily_spending = monthly_df[monthly_df['transaction_type'] == 'expense'].groupby(['date', 'category'])['amount'].sum().abs()
                            fig = px.sunburst(
                                daily_spending.reset_index(),
                                path=['category', 'date'],
                                values='amount',
                                title=f'Daily Spending Pattern for {selected_month}',
                            )
                            fig.update_layout(height=400)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No spending data available for this month")
                else:
                    st.info(f"Please add some income transactions for {selected_month} to see financial health analysis.")
            else:
                st.info("No transactions found. Add some transactions to see your financial analysis.")

        elif menu == "User Manual":
            st.header("📚 User Manual")
            
            st.subheader("🎯 Getting Started")
            st.markdown("""
                Welcome to the Personal Finance Tracker! This guide will help you understand how to use all features effectively.
                
                ### 1️⃣ Dashboard
                - View your monthly financial overview
                - Track income, expenses, and balance
                - Analyze spending patterns through interactive charts
                - View recent transactions
                
                ### 2️⃣ Adding and Deleting Transactions
                1. Navigate to "Add Transaction"
                2. Select transaction type (Income/Expense)
                3. Enter the following details:
                   - Date
                   - Amount
                   - Category
                   - Description
                4. Click "Add Transaction" to save
                5. Navigate to the end to view and delete transactions

                ### 3️⃣ Transaction Management
                - View all transactions in "Transaction List"
                - Filter transactions by:
                  - Date range
                  - Category
                  - Amount range
                - Update existing transactions
                
                ### 4️⃣ Financial Analysis
                - View expense ratio and financial health indicators
                - Analyze category-wise spending
                - Track daily spending patterns
                - Get personalized financial recommendations
                
                ### 💡 Tips for Better Financial Management
                - Regularly update your transactions
                - Categorize transactions correctly
                - Monitor your expense ratio
                - Review monthly spending patterns
                - Set budget goals for different categories
                
                ### 🔍 Understanding the Charts
                1. **Monthly Overview**: Shows income vs expenses trend
                2. **Category Analysis**: Displays spending distribution
                3. **Daily Transactions**: Tracks day-wise spending
                4. **Expense Ratio**: Monitors financial health
                
                ### ⚠️ Important Notes
                - Keep your login credentials secure
                - Regular updates ensure accurate analysis
                - Use appropriate categories for better tracking
                - Monitor financial health indicators regularly
            """)

        if st.sidebar.button("Logout"):
            st.session_state.access_token = None
            st.rerun()

if __name__ == "__main__":
    main()
