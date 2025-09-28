import streamlit as st
import pandas as pd
from utils.data_manager import DataManager

# Configure page
st.set_page_config(
    page_title="Monthly Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # Initialize data manager
# data_manager = DataManager()

# # Custom CSS
# st.markdown("""
# <style>
#     .metric-container {
#         background-color: #f0f2f6;
#         padding: 1rem;
#         border-radius: 0.5rem;
#         margin: 0.5rem 0;
#     }
#     .expense-item {
#         background-color: #ffffff;
#         padding: 0.5rem;
#         border-radius: 0.25rem;
#         border: 1px solid #e0e0e0;
#         margin: 0.25rem 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # Sidebar navigation
# st.sidebar.title("🏦 Expense Tracker")

# # Main content
# st.title("💰 Monthly Expense Tracker")
# st.markdown("Welcome to your personal expense tracking dashboard!")

# # Quick overview
# col1, col2, col3 = st.columns(3)

# with col1:
#     st.info("📤 **Upload & Process**\nUpload bank statements and extract expenses")

# with col2:
#     st.info("📊 **Expense Analysis**\nAnalyze your spending patterns and trends")

# with col3:
#     if not data_manager.get_final_expenses().empty:
#         total_expenses = data_manager.get_final_expenses()['Amount'].sum()
#         st.success(f"💳 **Total Tracked**\n${total_expenses:.2f}")
#     else:
#         st.warning("📋 **No Data Yet**\nStart by uploading a statement")

# # Navigation instructions
# st.markdown("---")
# st.markdown("### 🧭 Navigation")
# st.markdown("Use the sidebar or the pages in the file explorer to navigate between:")
# st.markdown("- **pages/1_📤_Upload_Process.py** - Upload and process bank statements")
# st.markdown("- **pages/2_📊_Expense_Analysis.py** - Analyze your expenses")

# # Footer
# st.sidebar.markdown("---")
# st.sidebar.info("💡 **Tips:**\n- Customize the PDF extraction logic for your bank\n- Add more expense categories as needed\n- Use filters to analyze specific time periods")

# # Add this to your main.py or create a separate password management page

import streamlit as st
from utils.data_manager import DataManager

def show_password_management():
    """Display password management interface."""
    
    data_manager = DataManager()
    
    st.sidebar.subheader("🔐 File Security")
    
    # Show file information
    file_info = data_manager.get_file_info()
    
    with st.sidebar.expander("📄 File Info"):
        st.write(f"**File:** {file_info['file_path']}")
        st.write(f"**Exists:** {'✅' if file_info['file_exists'] else '❌'}")
        st.write(f"**Protected:** {'🔒' if file_info['is_encrypted'] else '🔓'}")
        st.write(f"**Records:** {file_info['total_records']}")
        
        if file_info['file_exists']:
            st.write(f"**Size:** {file_info['file_size']} bytes")
            st.write(f"**Modified:** {file_info['last_modified'].strftime('%Y-%m-%d %H:%M')}")
    if "password" not in st.session_state:
        st.session_state["password"] = None

    if not st.session_state["password"]:
        st.title("🔐 Enter Password to Continue")
        pwd = st.text_input("Password:", type="password")
        if st.button("Unlock"):
            if data_manager._test_password(pwd):  # implement this
                st.session_state["password"] = pwd
                st.rerun()
            else:
                st.error("Incorrect password")
        st.stop()  # block rest of the app until password is correct
    # Password management
    with st.sidebar.expander("🔑 Password Settings"):
        if file_info['password_set']:
            st.success("✅ Password is set")
            
            # Change password
            new_password = st.text_input("New Password:", type="password")
            confirm_password = st.text_input("Confirm Password:", type="password")
            
            if st.button("🔄 Change Password"):
                if new_password and new_password == confirm_password:
                    if data_manager.change_password(new_password):
                        st.rerun()
                    else:
                        st.error("Failed to change password!")
                elif new_password != confirm_password:
                    st.error("Passwords don't match!")
                else:
                    st.error("Please enter a new password!")
        else:
            st.warning("⚠️ No password set")

# Add this to your main.py
def enhanced_main():
    """Enhanced main page with password management."""
    st.title("Welcome, click bank statements to get started")
    
   

if __name__ == "__main__":
    enhanced_main()