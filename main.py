import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import json
import calendar
import base64

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

# Delete transaction function
def delete_transaction(index):
    st.session_state.transactions.pop(index)
    save_transactions()
    st.success("Transaction deleted!")
    st.rerun()

# Function to download dataframe as CSV
def get_csv_download_link(df, filename="transactions.csv", link_text="Download CSV"):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{link_text}</a>'
    return href

# Main app title
st.title("Schmoney Machine 💰")

# Create tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Add Transaction", "View Transactions", "Analysis", "Export Data"])

# Tab 1: Add Transaction
with tab1:
    st.header("What's new:")
    
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

    # Category management
    st.divider()
    st.subheader("Manage Categories")
    
    category_type = st.selectbox("Category Type", ["Income", "Expense"], key="cat_type")
    
    # Display existing categories
    st.write("Current Categories:")
    for i, category in enumerate(st.session_state.categories[category_type]):
        col1, col2 = st.columns([4, 1])
        col1.write(f"• {category}")
        if col2.button("Delete", key=f"del_cat_{i}"):
            st.session_state.categories[category_type].remove(category)
            st.success(f"Deleted {category} from {category_type} categories!")
            st.rerun()
    
    # Add new category
    new_category = st.text_input("New Category Name")
    if st.button("Add Category"):
        if new_category and new_category not in st.session_state.categories[category_type]:
            st.session_state.categories[category_type].append(new_category)
            st.success(f"Added {new_category} to {category_type} categories!")
            st.rerun()
        else:
            st.error("Please enter a unique category name.")

# Tab 2: View Transactions
with tab2:
    st.header("Transaction History")
    
    df = get_transaction_df()
    
    if not df.empty:
        # Filter options in expander for cleaner UI
        with st.expander("Filter Options", expanded=False):
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
        
        # Show filtered transactions with ability to delete individual transactions
        if not filtered_df.empty:
            # Download button for filtered transactions
            st.markdown(get_csv_download_link(filtered_df, 
                                            filename="filtered_transactions.csv", 
                                            link_text="Download Filtered Transactions"), 
                        unsafe_allow_html=True)
            
            # Display transactions with delete buttons
            st.subheader("Transactions")
            
            for i, row in enumerate(filtered_df.sort_values('Date', ascending=False).itertuples()):
                col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 2, 1.5, 3, 0.8])
                
                col1.write(pd.to_datetime(row.Date).strftime('%Y-%m-%d'))
                col2.write(row.Type)
                col3.write(row.Category)
                col4.write(f"${row.Amount:.2f}")
                col5.write(row.Description or "-")
                
                # Find the index in the original list
                original_index = st.session_state.transactions.index(
                    next(t for t in st.session_state.transactions 
                         if (t['Date'] == row.Date and 
                             t['Type'] == row.Type and 
                             t['Category'] == row.Category and 
                             t['Amount'] == row.Amount and 
                             t['Description'] == row.Description))
                )
                
                if col6.button("Delete", key=f"del_{i}"):
                    delete_transaction(original_index)
            
            st.divider()
            
            # Bulk delete option
            if st.button("Delete All Displayed Transactions"):
                confirm = st.checkbox("I confirm I want to delete all displayed transactions")
                if confirm:
                    # Get indices of transactions to delete
                    indices_to_delete = []
                    for row in filtered_df.itertuples():
                        for i, t in enumerate(st.session_state.transactions):
                            if (t['Date'] == row.Date and 
                                t['Type'] == row.Type and 
                                t['Category'] == row.Category and 
                                t['Amount'] == row.Amount and 
                                t['Description'] == row.Description):
                                indices_to_delete.append(i)
                    
                    # Delete transactions in reverse order to avoid index shifting
                    for index in sorted(indices_to_delete, reverse=True):
                        st.session_state.transactions.pop(index)
                    
                    save_transactions()
                    st.success("Selected transactions deleted!")
                    st.rerun()
        else:
            st.info("No transactions match your filters.")
    else:
        st.info("No transactions yet. Add some in the 'Add Transaction' tab!")

# Tab 3: Analysis
with tab3:
    st.header("Financial Analysis")
    
    df = get_transaction_df()
    
    if not df.empty:
        # Convert date string to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Add year and month columns
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        df['MonthName'] = df['Date'].dt.month_name()
        
        # Get unique years and months for filtering
        years = sorted(df['Year'].unique())
        
        # Analysis period selection
        period_type = st.radio("Select Analysis Period", ["Monthly", "Yearly"], horizontal=True)
        
        if period_type == "Monthly":
            # Year and month selection
            col1, col2 = st.columns(2)
            with col1:
                selected_year = st.selectbox("Select Year", years, index=len(years)-1)
            
            # Filter data for selected year
            yearly_data = df[df['Year'] == selected_year]
            
            if not yearly_data.empty:
                # Create month selector
                months = sorted(yearly_data['Month'].unique())
                month_names = [calendar.month_name[m] for m in months]
                
                with col2:
                    selected_month_name = st.selectbox("Select Month", month_names)
                
                selected_month = list(calendar.month_name).index(selected_month_name)
                
                # Filter data for selected month
                data_to_analyze = yearly_data[yearly_data['Month'] == selected_month]
                period_label = f"{selected_month_name} {selected_year}"
            else:
                st.info(f"No transactions found for {selected_year}")
                st.stop()
                
        else:  # Yearly analysis
            selected_year = st.selectbox("Select Year", years, index=len(years)-1)
            
            # Filter data for selected year
            data_to_analyze = df[df['Year'] == selected_year]
            period_label = str(selected_year)
            
            if data_to_analyze.empty:
                st.info(f"No transactions found for {selected_year}")
                st.stop()
        
        # Display summary
        st.subheader(f"Summary for {period_label}")
        
        col1, col2, col3 = st.columns(3)
        
        period_income = data_to_analyze[data_to_analyze['Type'] == 'Income']['Amount'].sum()
        period_expenses = data_to_analyze[data_to_analyze['Type'] == 'Expense']['Amount'].sum()
        period_balance = period_income - period_expenses
        
        col1.metric("Total Income", f"${period_income:.2f}")
        col2.metric("Total Expenses", f"${period_expenses:.2f}")
        col3.metric("Balance", f"${period_balance:.2f}", 
                   f"{(period_balance/period_income*100):.1f}%" if period_income > 0 else "")
        
        # Download button for analysis data
        analyzed_summary = pd.DataFrame({
            'Metric': ['Income', 'Expenses', 'Balance'],
            'Amount': [period_income, period_expenses, period_balance]
        })
        st.markdown(get_csv_download_link(analyzed_summary, 
                                       filename=f"summary_{period_label.replace(' ', '_')}.csv", 
                                       link_text=f"Download {period_label} Summary"), 
                    unsafe_allow_html=True)
        
        # Income and Expense pie charts side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Income Breakdown")
            income_by_category = data_to_analyze[data_to_analyze['Type'] == 'Income'].groupby('Category')['Amount'].sum().reset_index()
            
            if not income_by_category.empty:
                fig = px.pie(income_by_category, values='Amount', names='Category', 
                            title=f"Income Sources - {period_label}",
                            color_discrete_sequence=px.colors.sequential.Greens)
                st.plotly_chart(fig, use_container_width=True)
                
                # Download button for income breakdown
                st.markdown(get_csv_download_link(income_by_category, 
                                               filename=f"income_breakdown_{period_label.replace(' ', '_')}.csv", 
                                               link_text="Download Income Breakdown"), 
                            unsafe_allow_html=True)
            else:
                st.info(f"No income recorded for {period_label}")
        
        with col2:
            st.subheader("Expense Breakdown")
            expense_by_category = data_to_analyze[data_to_analyze['Type'] == 'Expense'].groupby('Category')['Amount'].sum().reset_index()
            
            if not expense_by_category.empty:
                fig = px.pie(expense_by_category, values='Amount', names='Category', 
                            title=f"Expense Categories - {period_label}",
                            color_discrete_sequence=px.colors.sequential.Reds)
                st.plotly_chart(fig, use_container_width=True)
                
                # Download button for expense breakdown
                st.markdown(get_csv_download_link(expense_by_category, 
                                               filename=f"expense_breakdown_{period_label.replace(' ', '_')}.csv", 
                                               link_text="Download Expense Breakdown"), 
                            unsafe_allow_html=True)
            else:
                st.info(f"No expenses recorded for {period_label}")
    else:
        st.info("Add some transactions to see analysis!")

# Tab 4: Export Data
with tab4:
    st.header("Export Data")
    
    df = get_transaction_df()
    
    if not df.empty:
        # Display export options
        st.subheader("Download Options")
        
        # Download all transactions
        st.markdown("### All Transactions")
        st.markdown(get_csv_download_link(df, 
                                       filename="all_transactions.csv", 
                                       link_text="Download All Transactions"), 
                    unsafe_allow_html=True)
        
        # Export by time period
        st.markdown("### Export by Time Period")
        
        # Convert date to datetime for filtering
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Year'] = df['Date'].dt.year
            df['Month'] = df['Date'].dt.month
            
            # Year and month selection
            col1, col2 = st.columns(2)
            
            with col1:
                export_period = st.radio("Select Export Period", ["Monthly", "Yearly", "Custom Range"])
            
            if export_period == "Yearly":
                years = sorted(df['Year'].unique())
                selected_year = st.selectbox("Select Year to Export", years, key="export_year")
                
                year_df = df[df['Year'] == selected_year]
                
                if not year_df.empty:
                    download_filename = f"transactions_{selected_year}.csv"
                    st.markdown(get_csv_download_link(year_df, 
                                                   filename=download_filename, 
                                                   link_text=f"Download {selected_year} Transactions"), 
                                unsafe_allow_html=True)
                else:
                    st.info(f"No transactions found for {selected_year}")
                    
            elif export_period == "Monthly":
                col1, col2 = st.columns(2)
                
                with col1:
                    years = sorted(df['Year'].unique())
                    selected_year = st.selectbox("Select Year", years, key="export_month_year")
                
                year_df = df[df['Year'] == selected_year]
                
                if not year_df.empty:
                    with col2:
                        months = sorted(year_df['Month'].unique())
                        month_names = [calendar.month_name[m] for m in months]
                        selected_month_name = st.selectbox("Select Month", month_names, key="export_month")
                    
                    selected_month = list(calendar.month_name).index(selected_month_name)
                    month_df = year_df[year_df['Month'] == selected_month]
                    
                    if not month_df.empty:
                        download_filename = f"transactions_{selected_month_name}_{selected_year}.csv"
                        st.markdown(get_csv_download_link(month_df, 
                                                       filename=download_filename, 
                                                       link_text=f"Download {selected_month_name} {selected_year} Transactions"), 
                                    unsafe_allow_html=True)
                    else:
                        st.info(f"No transactions found for {selected_month_name} {selected_year}")
                else:
                    st.info(f"No transactions found for {selected_year}")
                    
            else:  # Custom range
                min_date = df['Date'].min().date()
                max_date = df['Date'].max().date()
                custom_date_range = st.date_input("Select Date Range", 
                                                [min_date, max_date],
                                                min_value=min_date,
                                                max_value=max_date,
                                                key="export_custom_range")
                
                if len(custom_date_range) == 2:
                    start_date, end_date = custom_date_range
                    filtered_df = df[
                        (df['Date'].dt.date >= start_date) & 
                        (df['Date'].dt.date <= end_date)
                    ]
                    
                    if not filtered_df.empty:
                        download_filename = f"transactions_{start_date}_to_{end_date}.csv"
                        st.markdown(get_csv_download_link(filtered_df, 
                                                       filename=download_filename, 
                                                       link_text=f"Download Transactions ({start_date} to {end_date})"), 
                                    unsafe_allow_html=True)
                    else:
                        st.info(f"No transactions found between {start_date} and {end_date}")
        
        # Export by type
        st.markdown("### Export by Transaction Type")
        export_type = st.radio("Select Transaction Type", ["All", "Income Only", "Expenses Only"], horizontal=True)
        
        if export_type == "Income Only":
            income_df = df[df['Type'] == 'Income']
            if not income_df.empty:
                st.markdown(get_csv_download_link(income_df, 
                                               filename="income_transactions.csv", 
                                               link_text="Download All Income Transactions"), 
                            unsafe_allow_html=True)
            else:
                st.info("No income transactions found")
                
        elif export_type == "Expenses Only":
            expense_df = df[df['Type'] == 'Expense']
            if not expense_df.empty:
                st.markdown(get_csv_download_link(expense_df, 
                                               filename="expense_transactions.csv", 
                                               link_text="Download All Expense Transactions"), 
                            unsafe_allow_html=True)
            else:
                st.info("No expense transactions found")
    else:
        st.info("No transactions yet. Add some in the 'Add Transaction' tab!")

# Add a footer
st.divider()
st.caption("Personal Finance Tracker App © 2025")