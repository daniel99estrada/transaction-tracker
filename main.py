import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import json
import calendar

# Set page configuration
st.set_page_config(page_title="Finance Tracker", layout="wide")

# Initialize session state for data storage
if 'transactions' not in st.session_state:
    st.session_state.transactions = []
    
if 'categories' not in st.session_state:
    st.session_state.categories = {
        'Income': ['Salary', 'Freelance', 'Investments', 'Gifts', 'Other Income'],
        'Expense': ['Food', 'Transportation', 'Housing', 'Utilities', 'Entertainment', 
                   'Healthcare', 'Education', 'Shopping', 'Travel', 'Other Expense']
    }

# Function to save transactions to file
def save_transactions():
    with open('transactions.json', 'w') as f:
        json.dump(st.session_state.transactions, f)
        
# Function to load transactions from file
def load_transactions():
    if os.path.exists('transactions.json'):
        with open('transactions.json', 'r') as f:
            st.session_state.transactions = json.load(f)

# Load data on app start
load_transactions()

# Convert transactions to DataFrame
def get_transaction_df():
    if not st.session_state.transactions:
        return pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount', 'Description'])
    return pd.DataFrame(st.session_state.transactions)

# Main app title
st.title("💰 Personal Finance Tracker")

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Add Transaction", "View Transactions", "Monthly Analysis", "Yearly Analysis"])

# Tab 1: Add Transaction
with tab1:
    st.header("Add New Transaction")
    
    col1, col2 = st.columns(2)
    
    with col1:
        transaction_date = st.date_input("Date", datetime.now())
        transaction_type = st.selectbox("Type", ["Income", "Expense"])
        transaction_category = st.selectbox("Category", 
                                          st.session_state.categories[transaction_type])
        
    with col2:
        transaction_amount = st.number_input("Amount", min_value=0.01, format="%.2f")
        transaction_description = st.text_input("Description (Optional)")
        
    if st.button("Add Transaction"):
        new_transaction = {
            'Date': transaction_date.strftime('%Y-%m-%d'),
            'Type': transaction_type,
            'Category': transaction_category,
            'Amount': float(transaction_amount),
            'Description': transaction_description
        }
        
        st.session_state.transactions.append(new_transaction)
        save_transactions()
        st.success("Transaction added successfully!")

    # Custom category management
    st.divider()
    st.subheader("Manage Categories")
    
    category_type = st.selectbox("Category Type", ["Income", "Expense"], key="cat_type")
    new_category = st.text_input("New Category Name")
    
    if st.button("Add Category"):
        if new_category and new_category not in st.session_state.categories[category_type]:
            st.session_state.categories[category_type].append(new_category)
            st.success(f"Added {new_category} to {category_type} categories!")
        else:
            st.error("Please enter a unique category name.")

# Tab 2: View Transactions
with tab2:
    st.header("Transaction History")
    
    df = get_transaction_df()
    
    if not df.empty:
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.multiselect("Filter by Type", 
                                        options=["Income", "Expense"],
                                        default=["Income", "Expense"])
        
        with col2:
            all_categories = st.session_state.categories['Income'] + st.session_state.categories['Expense']
            filter_category = st.multiselect("Filter by Category", 
                                           options=all_categories,
                                           default=[])
        
        with col3:
            if 'Date' in df.columns:
                min_date = pd.to_datetime(df['Date']).min().date()
                max_date = pd.to_datetime(df['Date']).max().date()
                date_range = st.date_input("Date Range", 
                                          [min_date, max_date],
                                          min_value=min_date,
                                          max_value=max_date)
        
        # Apply filters
        filtered_df = df.copy()
        
        if filter_type:
            filtered_df = filtered_df[filtered_df['Type'].isin(filter_type)]
            
        if filter_category:
            filtered_df = filtered_df[filtered_df['Category'].isin(filter_category)]
            
        if 'Date' in filtered_df.columns and len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df = filtered_df[
                (pd.to_datetime(filtered_df['Date']).dt.date >= start_date) & 
                (pd.to_datetime(filtered_df['Date']).dt.date <= end_date)
            ]
        
        # Show filtered transactions with ability to sort
        if not filtered_df.empty:
            st.dataframe(filtered_df.sort_values('Date', ascending=False), 
                        use_container_width=True)
            
            if st.button("Delete All Transactions"):
                confirm = st.checkbox("I confirm I want to delete all transactions")
                if confirm:
                    st.session_state.transactions = []
                    save_transactions()
                    st.success("All transactions deleted!")
                    st.experimental_rerun()
        else:
            st.info("No transactions match your filters.")
    else:
        st.info("No transactions yet. Add some in the 'Add Transaction' tab!")

# Tab 3: Monthly Analysis
with tab3:
    st.header("Monthly Financial Analysis")
    
    df = get_transaction_df()
    
    if not df.empty:
        # Convert date string to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Add year and month columns
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['MonthName'] = df['Date'].dt.month_name()
        df['YearMonth'] = df['Date'].dt.strftime('%Y-%m')
        
        # Get unique years and months for filtering
        years = sorted(df['Year'].unique())
        
        # Year selection
        selected_year = st.selectbox("Select Year", years, index=len(years)-1)
        
        # Filter data for selected year
        yearly_data = df[df['Year'] == selected_year]
        
        if not yearly_data.empty:
            # Create month selector
            months = sorted(yearly_data['Month'].unique())
            month_names = [calendar.month_name[m] for m in months]
            
            selected_month_name = st.selectbox("Select Month", month_names)
            selected_month = list(calendar.month_name).index(selected_month_name)
            
            # Filter data for selected month
            monthly_data = yearly_data[yearly_data['Month'] == selected_month]
            
            if not monthly_data.empty:
                # Monthly summary
                st.subheader(f"Summary for {selected_month_name} {selected_year}")
                
                col1, col2, col3 = st.columns(3)
                
                monthly_income = monthly_data[monthly_data['Type'] == 'Income']['Amount'].sum()
                monthly_expenses = monthly_data[monthly_data['Type'] == 'Expense']['Amount'].sum()
                monthly_balance = monthly_income - monthly_expenses
                
                col1.metric("Total Income", f"${monthly_income:.2f}")
                col2.metric("Total Expenses", f"${monthly_expenses:.2f}")
                col3.metric("Balance", f"${monthly_balance:.2f}", 
                           f"{(monthly_balance/monthly_income*100):.1f}%" if monthly_income > 0 else "")
                
                # Income breakdown
                st.subheader("Income Breakdown")
                income_by_category = monthly_data[monthly_data['Type'] == 'Income'].groupby('Category')['Amount'].sum().reset_index()
                
                if not income_by_category.empty:
                    fig = px.pie(income_by_category, values='Amount', names='Category', 
                                title=f"Income Sources - {selected_month_name} {selected_year}",
                                color_discrete_sequence=px.colors.sequential.Greens)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No income recorded for {selected_month_name} {selected_year}")
                
                # Expense breakdown
                st.subheader("Expense Breakdown")
                expense_by_category = monthly_data[monthly_data['Type'] == 'Expense'].groupby('Category')['Amount'].sum().reset_index()
                
                if not expense_by_category.empty:
                    fig = px.pie(expense_by_category, values='Amount', names='Category', 
                                title=f"Expense Categories - {selected_month_name} {selected_year}",
                                color_discrete_sequence=px.colors.sequential.Reds)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No expenses recorded for {selected_month_name} {selected_year}")
                
                # Daily spending pattern
                st.subheader("Daily Spending Pattern")
                
                daily_data = monthly_data.copy()
                daily_data['Day'] = daily_data['Date'].dt.day
                
                # Group by day and type
                daily_grouped = daily_data.groupby(['Day', 'Type'])['Amount'].sum().unstack().fillna(0)
                
                # Make sure both columns exist
                if 'Income' not in daily_grouped.columns:
                    daily_grouped['Income'] = 0
                if 'Expense' not in daily_grouped.columns:
                    daily_grouped['Expense'] = 0
                
                # Create figure with dual y-axes
                fig = px.line(daily_grouped.reset_index(), x='Day', y=['Income', 'Expense'],
                             title=f"Daily Financial Activity - {selected_month_name} {selected_year}",
                             labels={'value': 'Amount ($)', 'variable': 'Type'},
                             color_discrete_map={'Income': 'green', 'Expense': 'red'})
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Top expenses for the month
                st.subheader("Top Expenses")
                top_expenses = monthly_data[monthly_data['Type'] == 'Expense'].sort_values('Amount', ascending=False).head(5)
                
                if not top_expenses.empty:
                    fig = px.bar(top_expenses, x='Amount', y='Description', orientation='h',
                                title=f"Top Expenses - {selected_month_name} {selected_year}",
                                color='Category', color_discrete_sequence=px.colors.sequential.Reds)
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No expenses recorded for {selected_month_name} {selected_year}")
            else:
                st.info(f"No transactions found for {selected_month_name} {selected_year}")
        else:
            st.info(f"No transactions found for {selected_year}")
    else:
        st.info("Add some transactions to see monthly analysis!")

# Tab 4: Yearly Analysis
with tab4:
    st.header("Yearly Financial Analysis")
    
    df = get_transaction_df()
    
    if not df.empty:
        # Convert date string to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Add year and month columns
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['MonthName'] = df['Date'].dt.month_name()
        df['YearMonth'] = df['Date'].dt.strftime('%Y-%m')
        
        # Get unique years for filtering
        years = sorted(df['Year'].unique())
        
        # Year selection
        selected_year = st.selectbox("Select Year for Analysis", years, index=len(years)-1, key="yearly_analysis")
        
        # Filter data for selected year
        yearly_data = df[df['Year'] == selected_year]
        
        if not yearly_data.empty:
            # Yearly summary
            st.subheader(f"Annual Summary for {selected_year}")
            
            col1, col2, col3 = st.columns(3)
            
            yearly_income = yearly_data[yearly_data['Type'] == 'Income']['Amount'].sum()
            yearly_expenses = yearly_data[yearly_data['Type'] == 'Expense']['Amount'].sum()
            yearly_balance = yearly_income - yearly_expenses
            yearly_savings_rate = (yearly_balance / yearly_income * 100) if yearly_income > 0 else 0
            
            col1.metric("Total Income", f"${yearly_income:.2f}")
            col2.metric("Total Expenses", f"${yearly_expenses:.2f}")
            col3.metric("Net Savings", f"${yearly_balance:.2f}", 
                       f"{yearly_savings_rate:.1f}%" if yearly_income > 0 else "")
            
            # Monthly trend throughout the year
            st.subheader("Monthly Financial Trends")
            
            # Group by month and type
            monthly_grouped = yearly_data.groupby(['Month', 'Type'])['Amount'].sum().unstack().fillna(0)
            
            # Make sure both columns exist
            if 'Income' not in monthly_grouped.columns:
                monthly_grouped['Income'] = 0
            if 'Expense' not in monthly_grouped.columns:
                monthly_grouped['Expense'] = 0
                
            monthly_grouped['Net'] = monthly_grouped['Income'] - monthly_grouped['Expense']
            monthly_grouped = monthly_grouped.reset_index()
            
            # Add month names
            month_names = {i: calendar.month_abbr[i] for i in range(1, 13)}
            monthly_grouped['MonthName'] = monthly_grouped['Month'].map(month_names)
            
            # Sort by month
            monthly_grouped = monthly_grouped.sort_values('Month')
            
            # Create the monthly trend chart
            fig = px.bar(monthly_grouped, x='MonthName', y=['Income', 'Expense'],
                        title=f"Monthly Income and Expenses - {selected_year}",
                        barmode='group',
                        color_discrete_map={'Income': 'green', 'Expense': 'red'})
            
            # Add net savings line
            fig.add_trace(go.Scatter(x=monthly_grouped['MonthName'], y=monthly_grouped['Net'],
                                    mode='lines+markers', name='Net Savings',
                                    line=dict(color='blue', width=3)))
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Income sources for the year
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Income Sources")
                income_by_category = yearly_data[yearly_data['Type'] == 'Income'].groupby('Category')['Amount'].sum().reset_index()
                
                if not income_by_category.empty:
                    fig = px.pie(income_by_category, values='Amount', names='Category', 
                                title=f"Income Sources - {selected_year}",
                                color_discrete_sequence=px.colors.sequential.Greens)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No income recorded for {selected_year}")
            
            with col2:
                st.subheader("Expense Categories")
                expense_by_category = yearly_data[yearly_data['Type'] == 'Expense'].groupby('Category')['Amount'].sum().reset_index()
                
                if not expense_by_category.empty:
                    fig = px.pie(expense_by_category, values='Amount', names='Category', 
                                title=f"Expense Categories - {selected_year}",
                                color_discrete_sequence=px.colors.sequential.Reds)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No expenses recorded for {selected_year}")
            
            # Expense category trends by month
            st.subheader("Monthly Expense Category Trends")
            
            expense_categories = yearly_data[yearly_data['Type'] == 'Expense']['Category'].unique()
            
            if len(expense_categories) > 0:
                selected_categories = st.multiselect(
                    "Select Categories to Display",
                    options=expense_categories,
                    default=expense_categories[:min(5, len(expense_categories))]
                )
                
                if selected_categories:
                    # Filter for selected categories
                    category_data = yearly_data[
                        (yearly_data['Type'] == 'Expense') & 
                        (yearly_data['Category'].isin(selected_categories))
                    ]
                    
                    # Group by month and category
                    monthly_category_data = category_data.groupby(['Month', 'Category'])['Amount'].sum().reset_index()
                    
                    # Add month names
                    monthly_category_data['MonthName'] = monthly_category_data['Month'].map(month_names)
                    
                    # Create line chart
                    fig = px.line(monthly_category_data, x='MonthName', y='Amount', color='Category',
                                 title=f"Monthly Expense Trends by Category - {selected_year}",
                                 markers=True, line_shape='linear')
                    
                    # Ensure x-axis is in month order
                    month_order = [calendar.month_abbr[i] for i in range(1, 13)]
                    fig.update_layout(xaxis={'categoryorder': 'array', 'categoryarray': month_order})
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Please select at least one category to display")
            else:
                st.info(f"No expense categories found for {selected_year}")
            
            # Average monthly spending
            st.subheader("Average Monthly Spending")
            
            avg_monthly = yearly_data[yearly_data['Type'] == 'Expense'].groupby(['Month'])['Amount'].sum().reset_index()
            avg_monthly['MonthName'] = avg_monthly['Month'].map(month_names)
            avg_monthly = avg_monthly.sort_values('Month')
            
            overall_avg = avg_monthly['Amount'].mean()
            
            fig = px.bar(avg_monthly, x='MonthName', y='Amount',
                        title=f"Monthly Expenses vs. Average ({overall_avg:.2f}) - {selected_year}",
                        color_discrete_sequence=['indianred'])
            
            # Add average line
            fig.add_hline(y=overall_avg, line_dash="dash", line_color="green",
                         annotation_text=f"Avg: ${overall_avg:.2f}")
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info(f"No transactions found for {selected_year}")
    else:
        st.info("Add some transactions to see yearly analysis!")

# Add a footer
st.divider()
st.caption("Personal Finance Tracker App © 2025")