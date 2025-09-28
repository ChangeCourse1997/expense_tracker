import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_manager import DataManager

st.set_page_config(page_title="Expense Analysis", page_icon="📊", layout="wide")

# Initialize data manager
expense_file_path = st.session_state.get('expense_file_path', 'data/final_expenses.csv')
data_manager = DataManager(expense_file_path)

st.title("📊 Expense Analysis Dashboard")

final_expenses = data_manager.get_final_expenses()

if final_expenses.empty:
    st.info("No expense data available. Please upload and process a bank statement first.")
    st.markdown("👈 Use the **Upload & Process** page to get started!")
else:
    df = final_expenses.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Month'] = df['Date'].dt.to_period('M')
    df['Year'] = df['Date'].dt.year
    
    # Filters
    st.sidebar.header("📅 Filters")
    
    # Date range filter
    min_date = df['Date'].min().date()
    max_date = df['Date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Category filter
    categories = st.sidebar.multiselect(
        "Select Categories",
        options=df['Category'].unique(),
        default=df['Category'].unique()
    )
    
    # Amount range filter
    min_amount = float(df['Amount'].min())
    max_amount = float(df['Amount'].max())
    
    amount_range = st.sidebar.slider(
        "Amount Range ($)",
        min_value=min_amount,
        max_value=max_amount,
        value=(min_amount, max_amount),
        step=1.0
    )
    
    # Filter data
    if len(date_range) == 2:
        mask = (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
        filtered_df = df[mask & df['Category'].isin(categories)]
    else:
        filtered_df = df[df['Category'].isin(categories)]
    
    # Apply amount filter
    filtered_df = filtered_df[
        (filtered_df['Amount'] >= amount_range[0]) & 
        (filtered_df['Amount'] <= amount_range[1])
    ]
    
    if filtered_df.empty:
        st.warning("No data matches your current filters. Please adjust the filter criteria.")
    else:
        # Key Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_expenses = filtered_df['Amount'].sum()
            st.metric("Total Expenses", f"${total_expenses:.2f}")
        
        with col2:
            avg_expense = filtered_df['Amount'].mean()
            st.metric("Average Expense", f"${avg_expense:.2f}")
        
        with col3:
            total_transactions = len(filtered_df)
            st.metric("Total Transactions", total_transactions)
        
        with col4:
            categories_count = filtered_df['Category'].nunique()
            st.metric("Categories Used", categories_count)
        
        # Charts Row 1
        col1, col2 = st.columns(2)
        
        with col1:
            # Expenses by Category
            st.subheader("💳 Expenses by Category")
            category_summary = filtered_df.groupby('Category')['Amount'].sum().reset_index()
            fig_pie = px.pie(category_summary, values='Amount', names='Category', 
                           title="Spending Distribution by Category",
                           color_discrete_sequence=px.colors.qualitative.Set3)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Daily Spending Trend for Latest 30 Days
            st.subheader("📈 Daily Spending Trend (Latest 30 Days)")
            
            # Calculate the date 30 days ago from the latest date in the data
            latest_date = df['Date'].max()
            thirty_days_ago = latest_date - timedelta(days=30)
            
            # Filter data for latest 30 days
            recent_df = df[(df['Date'] >= thirty_days_ago) & (df['Date'] <= latest_date)]
            recent_df = recent_df[recent_df['Category'].isin(categories)]  # Apply category filter
            recent_df = recent_df[(recent_df['Amount'] >= amount_range[0]) & 
                                (recent_df['Amount'] <= amount_range[1])]  # Apply amount filter
            
            if not recent_df.empty:
                # Group by date and sum amounts
                daily_summary = recent_df.groupby(recent_df['Date'].dt.date)['Amount'].sum().reset_index()
                daily_summary.columns = ['Date', 'Amount']
                
                # Create a complete date range for the last 30 days (to show days with no expenses as 0)
                date_range_30 = pd.date_range(start=thirty_days_ago.date(), end=latest_date.date(), freq='D')
                complete_dates = pd.DataFrame({'Date': date_range_30.date})
                
                # Merge to include days with no expenses
                daily_complete = complete_dates.merge(daily_summary, on='Date', how='left')
                daily_complete['Amount'] = daily_complete['Amount'].fillna(0)
                
                # Create the line chart
                fig_line = px.line(daily_complete, x='Date', y='Amount', 
                                 title="Daily Expense Trend (Latest 30 Days)",
                                 labels={'Date': 'Date', 'Amount': 'Daily Expenses ($)'},
                                 markers=True)
                
                # Add a trend line
                fig_line.add_scatter(x=daily_complete['Date'], y=daily_complete['Amount'].rolling(window=7, center=True).mean(), 
                                   mode='lines', name='7-day Moving Average', 
                                   line=dict(color='red', width=2, dash='dash'))
                
                fig_line.update_layout(
                    xaxis_title="Date", 
                    yaxis_title="Daily Expenses ($)",
                    hovermode='x unified'
                )
                fig_line.update_traces(line=dict(color='blue', width=2), selector=dict(name='Amount'))
                st.plotly_chart(fig_line, use_container_width=True)
                
                # Show some stats for the 30-day period
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("30-Day Total", f"${recent_df['Amount'].sum():.2f}")
                with col_b:
                    st.metric("Daily Average", f"${recent_df['Amount'].sum() / 30:.2f}")
                with col_c:
                    active_days = len(daily_summary[daily_summary['Amount'] > 0])
                    st.metric("Active Days", f"{active_days}/30")
            else:
                st.info("No data available for the latest 30 days with current filters.")
        
        # Charts Row 2
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily Spending Pattern by Day of Week
            st.subheader("📅 Daily Spending Pattern")
            filtered_df['DayOfWeek'] = filtered_df['Date'].dt.day_name()
            daily_summary = filtered_df.groupby('DayOfWeek')['Amount'].sum().reset_index()
            
            # Order days properly
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            daily_summary['DayOfWeek'] = pd.Categorical(daily_summary['DayOfWeek'], categories=day_order, ordered=True)
            daily_summary = daily_summary.sort_values('DayOfWeek')
            
            fig_bar = px.bar(daily_summary, x='DayOfWeek', y='Amount',
                           title="Spending by Day of Week",
                           color='Amount',
                           color_continuous_scale='Blues')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Top Spending Categories (Bar Chart)
            st.subheader("🏆 Top Spending Categories")
            top_categories = category_summary.sort_values('Amount', ascending=True).tail(8)
            
            fig_hbar = px.bar(top_categories, x='Amount', y='Category',
                            title="Categories by Total Spending",
                            orientation='h',
                            color='Amount',
                            color_continuous_scale='Reds')
            fig_hbar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_hbar, use_container_width=True)
        
        # Detailed Analysis Section
        st.header("🔍 Detailed Analysis")
        
        # Category Analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Category Statistics")
            category_stats = filtered_df.groupby('Category').agg({
                'Amount': ['sum', 'mean', 'count', 'std']
            }).round(2)
            category_stats.columns = ['Total ($)', 'Average ($)', 'Count', 'Std Dev ($)']
            category_stats = category_stats.sort_values('Total ($)', ascending=False)
            category_stats['Total (%)'] = (category_stats['Total ($)'] / category_stats['Total ($)'].sum() * 100).round(1)
            
            st.dataframe(category_stats, use_container_width=True)
        
        with col2:
            st.subheader("💰 Top 10 Largest Expenses")
            top_expenses = filtered_df.nlargest(10, 'Amount')[['Date', 'Title', 'Amount', 'Category']]
            top_expenses['Date'] = top_expenses['Date'].dt.strftime('%Y-%m-%d')
            st.dataframe(top_expenses, use_container_width=True)
        
        # Monthly Expense Totals
        st.subheader("📅 Monthly Expense Totals")
        
        if len(filtered_df['Month'].unique()) > 1:
            # Group by month and sum total expenses (no category breakdown)
            monthly_totals = filtered_df.groupby('Month')['Amount'].sum().reset_index()
            monthly_totals['Month_str'] = monthly_totals['Month'].astype(str)
            
            # Create a simple bar chart showing total monthly expenses
            fig_monthly = px.bar(monthly_totals, x='Month_str', y='Amount',
                               title="Total Monthly Expenses",
                               labels={'Month_str': 'Month', 'Amount': 'Total Expenses ($)'},
                               color='Amount',
                               color_continuous_scale='Blues')
            
            # Add value labels on top of bars
            fig_monthly.update_traces(texttemplate='$%{y:.0f}', textposition='outside')
            fig_monthly.update_layout(
                xaxis_title="Month", 
                yaxis_title="Total Expenses ($)",
                showlegend=False
            )
            st.plotly_chart(fig_monthly, use_container_width=True)
            
            # Show month-over-month change if we have multiple months
            if len(monthly_totals) > 1:
                monthly_totals_sorted = monthly_totals.sort_values('Month_str')
                current_month = monthly_totals_sorted.iloc[-1]['Amount']
                previous_month = monthly_totals_sorted.iloc[-2]['Amount']
                change = current_month - previous_month
                change_pct = (change / previous_month) * 100 if previous_month != 0 else 0
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Latest Month", f"${current_month:.2f}")
                with col_b:
                    st.metric("Previous Month", f"${previous_month:.2f}")
                with col_c:
                    st.metric("Change", f"${change:.2f}", f"{change_pct:+.1f}%")
        else:
            st.info("Monthly breakdown requires data from multiple months.")
        
        # Expense Distribution
        st.subheader("📊 Expense Amount Distribution")
        fig_hist = px.histogram(filtered_df, x='Amount', nbins=30,
                              title="Distribution of Expense Amounts",
                              labels={'Amount': 'Expense Amount ($)', 'count': 'Frequency'})
        fig_hist.update_layout(bargap=0.1)
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Raw Data Table
        with st.expander("📋 View Raw Data"):
            display_df = filtered_df.copy()
            display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
            display_df = display_df[['Date', 'Title', 'Amount', 'Category']].sort_values('Date', ascending=False)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Download data
            csv = display_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download Filtered Data as CSV",
                data=csv,
                file_name=f"expenses_filtered_{date.today()}.csv",
                mime="text/csv"
            )
        
        # Summary Statistics
        with st.expander("📈 Summary Statistics"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Amount Statistics:**")
                st.write(f"- Mean: ${filtered_df['Amount'].mean():.2f}")
                st.write(f"- Median: ${filtered_df['Amount'].median():.2f}")
                st.write(f"- Standard Deviation: ${filtered_df['Amount'].std():.2f}")
                st.write(f"- Min: ${filtered_df['Amount'].min():.2f}")
                st.write(f"- Max: ${filtered_df['Amount'].max():.2f}")
            
            with col2:
                st.write("**Date Range:**")
                st.write(f"- From: {filtered_df['Date'].min().strftime('%Y-%m-%d')}")
                st.write(f"- To: {filtered_df['Date'].max().strftime('%Y-%m-%d')}")
                st.write(f"- Days Covered: {(filtered_df['Date'].max() - filtered_df['Date'].min()).days}")
                st.write(f"- Unique Categories: {filtered_df['Category'].nunique()}")
                st.write(f"- Average Daily Spending: ${filtered_df['Amount'].sum() / max(1, (filtered_df['Date'].max() - filtered_df['Date'].min()).days):.2f}")