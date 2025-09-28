import streamlit as st
import pandas as pd
from datetime import date
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_manager import DataManager
from utils.pdf_processor import PDFProcessor

st.set_page_config(page_title="Upload & Process", page_icon="📤", layout="wide")

# Initialize PDF processor
pdf_processor = PDFProcessor()

st.title("📤 Upload & Process Bank Statement (only citibank)")

# File path configuration at the top
st.header("📂 File Configuration")
col1, col2 = st.columns([3, 1])

with col1:
    # Get file path from user
    default_path = st.session_state.get('expense_file_path', 'data/final_expenses.csv')
    expense_file_path = st.text_input(
        "Expense File Path:", 
        value=default_path,
        help="Enter the path where your expenses CSV file should be stored/loaded from"
    )
    
with col2:
    st.write("")  # Spacing
    st.write("")  # Spacing
    if st.button("📁 Set File Path"):
        st.session_state.expense_file_path = expense_file_path
        # Clear existing data manager to reinitialize with new path
        if 'data_manager' in st.session_state:
            del st.session_state.data_manager
        st.success("File path updated!")
        st.rerun()

# Initialize or get data manager with user-specified path
if 'data_manager' not in st.session_state or st.session_state.get('expense_file_path') != expense_file_path:
    st.session_state.expense_file_path = expense_file_path
    st.session_state.data_manager = DataManager(expense_file_path)

data_manager = st.session_state.data_manager

# Display current file info
file_info = data_manager.get_file_info()
if file_info['file_exists']:
    st.info(f"✅ Using file: {file_info['file_path']} ({file_info['total_records']} records)")
else:
    st.warning(f"📄 New file will be created: {file_info['file_path']}")

st.divider()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Upload Bank Statement PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Extract Expenses", type="primary"):
            with st.spinner("Processing PDF..."):
                extracted_expenses = pdf_processor.extract_expenses_from_pdf(uploaded_file)
                if extracted_expenses:
                    data_manager.set_current_expenses(pd.DataFrame(extracted_expenses))
                    st.success(f"Extracted {len(extracted_expenses)} expenses!")
                else:
                    st.warning("No expenses found. Please check your PDF format.")

with col2:
    st.header("Quick Stats")
    current_expenses = data_manager.get_current_expenses()
    if not current_expenses.empty:
        total_amount = current_expenses['Amount'].sum()
        avg_amount = current_expenses['Amount'].mean()
        total_transactions = len(current_expenses)
        
        st.metric("Total Expenses", f"${total_amount:.2f}")
        st.metric("Average Transaction", f"${avg_amount:.2f}")
        st.metric("Total Transactions", total_transactions)

# Preview and Edit Expenses
current_expenses = data_manager.get_current_expenses()
if not current_expenses.empty:
    st.header("📋 Preview & Edit Expenses")
    
    # Add new expense manually
    with st.expander("➕ Add New Expense"):
        with st.form("add_expense_form"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                new_date = st.date_input("Date", value=date.today())
            with col2:
                new_title = st.text_input("Title")
            with col3:
                new_amount = st.number_input("Amount", min_value=0.00, step=0.01)
            with col4:
                categories = ['Food & Dining', 'Transportation', 'Shopping', 'Utilities', 
                            'Healthcare', 'Entertainment', 'Groceries', 'Other']
                new_category = st.selectbox("Category", categories)
            
            submitted = st.form_submit_button("Add Expense")
            
            if submitted and new_title:
                new_expense = pd.DataFrame({
                    'Date': [new_date],
                    'Title': [new_title],
                    'Amount': [new_amount],
                    'Category': [new_category]
                })
                updated_expenses = pd.concat([current_expenses, new_expense], ignore_index=True)
                data_manager.set_current_expenses(updated_expenses)
                st.success("Expense added!")
                st.rerun()
    
    # Display and edit expenses with better state management
    st.subheader("Edit Expenses")
    
    # Initialize edited expenses in session state only once
    if f"edited_expenses_{id(current_expenses)}" not in st.session_state:
        st.session_state[f"edited_expenses_{id(current_expenses)}"] = current_expenses.copy()
    
    # Use a unique key for the data editor to prevent conflicts
    edited_df = st.data_editor(
        st.session_state[f"edited_expenses_{id(current_expenses)}"],
        column_config={
            "Date": st.column_config.DateColumn("Date"),
            "Title": st.column_config.TextColumn("Title"),
            "Amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=['Food & Dining', 'Transportation', 'Shopping', 'Utilities', 
                        'Healthcare', 'Entertainment', 'Groceries', 'Other']
            )
        },
        num_rows="dynamic",
        use_container_width=True,
        key=f"expense_editor_{id(current_expenses)}"
    )

    # # Update session state only when there are actual changes
    # if not edited_df.equals(st.session_state[f"edited_expenses_{id(current_expenses)}"]):
    #     st.session_state[f"edited_expenses_{id(current_expenses)}"] = edited_df
    
    # Save buttons with form to prevent unnecessary reruns
    col1, col2, col3 = st.columns(3)
    with col2:
        with st.form("save_expenses_form"):
            save_button = st.form_submit_button("✅ Confirm & Save Expenses", type="primary", use_container_width=True)
            
            if save_button:
                # Update session state only when there are actual changes
                if not edited_df.equals(st.session_state[f"edited_expenses_{id(current_expenses)}"]):
                    st.session_state[f"edited_expenses_{id(current_expenses)}"] = edited_df
                current_edited = st.session_state[f"edited_expenses_{id(current_expenses)}"]
                success = data_manager.save_expenses_to_final(current_edited)
                
                if success:
                    # Clear states
                    data_manager.clear_current_expenses()
                    # Clean up old session state keys
                    keys_to_remove = [key for key in st.session_state.keys() if key.startswith("edited_expenses_")]
                    for key in keys_to_remove:
                        del st.session_state[key]
                    st.success("Expenses saved successfully!")
                    st.rerun()
                else:
                    st.error("Failed to save expenses. Please try again.")

# Show recent final expenses preview
st.header("📊 Recent Final Expenses")
final_expenses = data_manager.get_final_expenses()
if not final_expenses.empty:
    # Show recent expenses without making it editable to avoid performance issues
    recent_expenses = final_expenses.tail(10)
    st.dataframe(recent_expenses, use_container_width=True)
    
    # Add summary info
    summary = data_manager.get_expense_summary()
    if summary:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Saved", f"${summary['total_expenses']:.2f}")
        with col2:
            st.metric("Average", f"${summary['average_expense']:.2f}")
        with col3:
            st.metric("Count", summary['transaction_count'])
        with col4:
            st.metric("Top Category", summary['top_category'])
else:
    st.info("No final expenses saved yet. Process and confirm some expenses first!")