import streamlit as st
import pandas as pd
import os
import datetime

class DataManager:
    """Handles all data management operations for the expense tracker with password-protected Excel files."""
    
    def __init__(self,expense_file_path):
        self.expense_file_path = expense_file_path
        self.password = None
        self._initialize_session_state()
        self._get_password()
        self._load_existing_expenses()
    
    def _initialize_session_state(self):
        """Initialize session state variables."""
        if 'expenses_df' not in st.session_state:
            st.session_state.expenses_df = pd.DataFrame(columns=['Date', 'Title', 'Amount', 'Category'])
        if 'final_expenses' not in st.session_state:
            st.session_state.final_expenses = pd.DataFrame(columns=['Date', 'Title', 'Amount', 'Category'])
        if 'file_password' not in st.session_state:
            st.session_state.file_password = None
    
    def _get_password(self):
        """Get password from user input or session state."""
        # Check if password is already stored in session state
        if st.session_state.file_password:
            self.password = st.session_state.file_password
        else:
            # Show password input in sidebar
            with st.sidebar:
                st.subheader("🔐 File Security")
                
                # Check if file exists and is encrypted
                if os.path.exists(self.expense_file_path):
                    if self._is_file_encrypted():
                        password_input = st.text_input(
                            "Enter file password:", 
                            type="password", 
                            key="password_input",
                            help="Password required to access your expense data"
                        )
                        
                        if password_input:
                            if st.button("🔓 Unlock File"):
                                if self._test_password(password_input):
                                    st.session_state.file_password = password_input
                                    self.password = password_input
                                    st.success("✅ File unlocked!")
                                    st.rerun()
                                else:
                                    st.error("❌ Incorrect password!")
                        else:
                            st.warning("🔒 File is password protected. Please enter password to continue.")
                            return
                    else:
                        # File exists but not encrypted - set default password for new saves
                        self.password = self._get_default_password()
                        st.session_state.file_password = self.password
                else:
                    # No file exists - get password for new file
                    self.password = self._get_default_password()
                    st.session_state.file_password = self.password
    
    def _get_default_password(self):
        """Get default password or prompt user to set one."""
        with st.sidebar.expander("🔐 Set File Password"):
            new_password = st.text_input(
                "Set password for new file:", 
                type="password", 
                value=None,  # Default password
                help="This password will protect your expense data"
            )
            
            if st.button("💾 Set Password"):
                st.session_state.file_password = new_password
                st.success("Password set!")
                return new_password
            
            return new_password if new_password else "nth"
    
    def _is_file_encrypted(self):
        """Check if the Excel file is password protected."""
        try:
            # Try to open without password first
            pd.read_csv(self.expense_file_path)
            return False  # File opened successfully, not encrypted
        except Exception as e:
            if "password" in str(e).lower() or "encrypted" in str(e).lower():
                return True  # File is encrypted
            return False  # Other error, assume not encrypted
    
    
    def _load_existing_expenses(self):
        """Load existing final expenses from Excel file if it exists."""
        if not self.password:
            return  # Can't load without password
            
        if os.path.exists(self.expense_file_path) and st.session_state.final_expenses.empty:
            try:
                # Create data directory if it doesn't exist
                os.makedirs(os.path.dirname(self.expense_file_path), exist_ok=True)
                
                # Try to load encrypted file first
                try:
                    st.session_state.final_expenses = pd.read_csv(self.expense_file_path)
                except Exception:
                    # Try to load as unencrypted Excel file
                    st.session_state.final_expenses = pd.read_csv(self.expense_file_path)
                
                # Process loaded data
                if not st.session_state.final_expenses.empty:
                    st.session_state.final_expenses['Date'] = pd.to_datetime(st.session_state.final_expenses['Date']).dt.date
                    
                    # Add Category column if it doesn't exist (for backward compatibility)
                    if 'Category' not in st.session_state.final_expenses.columns:
                        st.session_state.final_expenses['Category'] = 'Other'
                        
            except Exception as e:
                st.sidebar.error(f"Error loading expenses: {str(e)}")
    
    def get_current_expenses(self):
        """Get current expenses being processed."""
        return st.session_state.expenses_df
    
    def set_current_expenses(self, expenses_df):
        """Set current expenses being processed."""
        # Ensure Category column exists
        if 'Category' not in expenses_df.columns:
            expenses_df['Category'] = 'Other'
        st.session_state.expenses_df = expenses_df
    
    def clear_current_expenses(self):
        """Clear current expenses."""
        st.session_state.expenses_df = pd.DataFrame(columns=['Date', 'Title', 'Amount', 'Category'])
    
    def get_final_expenses(self):
        """Get final confirmed expenses."""
        return st.session_state.final_expenses
    
    def save_expenses_to_final(self, expenses_df):
        """Save expenses to final expenses and password-protected Excel file."""
        if not self.password:
            st.error("❌ Cannot save: No password set!")
            return False
            
        try:
            # Ensure Category column exists
            if 'Category' not in expenses_df.columns:
                expenses_df['Category'] = 'Other'
            
            # Add to final expenses
            st.session_state.final_expenses = pd.concat([st.session_state.final_expenses, expenses_df], ignore_index=True)
            
            # Remove duplicates based on all columns
            st.session_state.final_expenses = st.session_state.final_expenses.drop_duplicates().reset_index(drop=True)
            
            # Save to password-protected Excel
            self._save_to_encrypted_csv()
            return True
        except Exception as e:
            st.error(f"Error saving expenses: {str(e)}")
            return False
    
    def _save_to_encrypted_csv(self):
        """Save final expenses to password-protected Excel file."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(self.expense_file_path), exist_ok=True)
            
            # Create a copy for saving (to avoid modifying the original)
            save_df = st.session_state.final_expenses.copy()
            
            # Convert date to string for Excel storage
            if not save_df.empty:
                save_df['Date'] = pd.to_datetime(save_df['Date']).dt.strftime('%Y-%m-%d')
            
            # First save main then temp
            save_df.to_csv(self.expense_file_path, index=False)
            save_df.to_csv(self.expense_file_path.replace('.csv',f'{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'), index=False)
        
                
        except Exception as e:
            raise Exception(f"Failed to save Excel: {str(e)}")
    
    
    def delete_expense(self, index):
        """Delete an expense by index from final expenses."""
        try:
            st.session_state.final_expenses = st.session_state.final_expenses.drop(index).reset_index(drop=True)
            self._save_to_encrypted_excel()
            return True
        except Exception as e:
            st.error(f"Error deleting expense: {str(e)}")
            return False
    
    def update_expense(self, index, updated_expense):
        """Update an expense at given index."""
        try:
            for column in updated_expense.keys():
                st.session_state.final_expenses.loc[index, column] = updated_expense[column]
            self._save_to_encrypted_excel()
            return True
        except Exception as e:
            st.error(f"Error updating expense: {str(e)}")
            return False
    
    def get_expense_summary(self):
        """Get summary statistics for final expenses."""
        df = st.session_state.final_expenses
        if df.empty:
            return None
        
        return {
            'total_expenses': df['Amount'].sum(),
            'average_expense': df['Amount'].mean(),
            'transaction_count': len(df),
            'date_range': {
                'start': df['Date'].min(),
                'end': df['Date'].max()
            },
            'categories': df['Category'].unique().tolist(),
            'top_category': df.groupby('Category')['Amount'].sum().idxmax() if 'Category' in df.columns else 'Other',
            'largest_expense': {
                'amount': df['Amount'].max(),
                'title': df.loc[df['Amount'].idxmax(), 'Title']
            }
        }
    
    def get_category_summary(self):
        """Get summary by category."""
        df = st.session_state.final_expenses
        if df.empty or 'Category' not in df.columns:
            return pd.DataFrame()
        
        return df.groupby('Category')['Amount'].agg(['sum', 'count', 'mean']).reset_index()
    
    
    
    def get_file_info(self):
        """Get information about the current file."""
        info = {
            'file_path': self.expense_file_path,
            'file_exists': os.path.exists(self.expense_file_path),
            'is_encrypted': self._is_file_encrypted() if os.path.exists(self.expense_file_path) else False,
            'password_set': bool(self.password),
            'total_records': len(st.session_state.final_expenses)
        }
        
        if info['file_exists']:
            info['file_size'] = os.path.getsize(self.expense_file_path)
            info['last_modified'] = pd.Timestamp.fromtimestamp(os.path.getmtime(self.expense_file_path))
        
        return info