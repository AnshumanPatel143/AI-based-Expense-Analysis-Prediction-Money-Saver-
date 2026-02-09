"""
app.py - IMPROVED VERSION
Main Streamlit application for Expense Tracker
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys

# Page configuration - MUST BE FIRST
st.set_page_config(
    page_title="Expense Tracker AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import modules with error handling
try:
    from database import ExpenseDatabase
    from forecasting import ExpenseForecaster
    from anomaly_detection import AnomalyDetector
    from email_alerts import EmailAlertSystem
except ImportError as e:
    st.error(f"❌ Missing module: {e}")
    st.info("Make sure all files (database.py, forecasting.py, anomaly_detection.py, email_alerts.py) are in the same directory as app.py")
    st.stop()

# Initialize session state for components (prevents re-initialization)
@st.cache_resource
def initialize_components():
    """Initialize database, forecaster, and detector once"""
    return {
        'db': ExpenseDatabase(),
        'forecaster': ExpenseForecaster(),
        'detector': AnomalyDetector()
    }

# Get components
components = initialize_components()
db = components['db']
forecaster = components['forecaster']
detector = components['detector']

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">💰 Expense Tracker with AI Predictions</h1>', unsafe_allow_html=True)

# Sidebar - Add Expense
st.sidebar.header("➕ Add New Expense")

with st.sidebar.form("expense_form", clear_on_submit=True):
    expense_date = st.date_input("Date", datetime.now())
    expense_amount = st.number_input("Amount (₹)", min_value=0, step=50, value=0)
    expense_category = st.selectbox(
        "Category",
        ['Food', 'Travel', 'Shopping', 'Entertainment', 'Bills', 'Other']
    )
    expense_description = st.text_input("Description (optional)")
    
    submit_button = st.form_submit_button("Add Expense")
    
    if submit_button:
        if expense_amount > 0:
            try:
                db.add_expense(
                    str(expense_date),
                    expense_amount,
                    expense_category,
                    expense_description
                )
                st.success(f"✅ Added ₹{expense_amount} to {expense_category}")
                
                # Check for anomaly
                try:
                    if detector.is_amount_anomalous(expense_amount):
                        st.warning(f"⚠️ This amount (₹{expense_amount}) is unusually high!")
                except:
                    pass  # Skip anomaly check if insufficient data
                
                # Force refresh
                st.rerun()
            except Exception as e:
                st.error(f"Error adding expense: {str(e)}")
        else:
            st.error("Amount must be greater than 0")

# Sidebar - Settings
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Settings")
monthly_budget = st.sidebar.number_input(
    "Monthly Budget (₹)",
    min_value=5000,
    value=25000,
    step=1000
)

# Check if database has data
try:
    df_check = db.get_all_expenses()
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

if len(df_check) == 0:
    st.warning("⚠️ No data found! Click below to generate sample data:")
    if st.button("Generate Sample Data"):
        with st.spinner("Generating 6 months of sample expenses..."):
            try:
                from data_generator import generate_sample_data
                generate_sample_data()
                # Clear cache and reload
                st.cache_resource.clear()
                components['db'].load_csv_to_db()
                st.success("✅ Sample data generated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Error generating data: {str(e)}")
                st.info("Make sure data_generator.py exists in the same directory")
    st.stop()

# Main Dashboard
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📈 Predictions", "⚠️ Anomalies", "📧 Alerts"])

# TAB 1: Dashboard
with tab1:
    try:
        df = db.get_all_expenses()
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_spent = df['amount'].sum()
            st.metric("Total Spent", f"₹{total_spent:,.2f}")
        
        with col2:
            avg_daily = df.groupby('date')['amount'].sum().mean()
            st.metric("Avg Daily Spend", f"₹{avg_daily:,.2f}")
        
        with col3:
            num_transactions = len(df)
            st.metric("Transactions", f"{num_transactions}")
        
        with col4:
            if len(df) > 0:
                top_category = df.groupby('category')['amount'].sum().idxmax()
                st.metric("Top Category", top_category)
            else:
                st.metric("Top Category", "N/A")
        
        st.markdown("---")
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Spending by Category")
            category_data = df.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(
                category_data,
                values='amount',
                names='category',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Daily Spending Trend")
            daily_spending = df.groupby('date')['amount'].sum().reset_index()
            daily_spending['date'] = pd.to_datetime(daily_spending['date'])
            daily_spending = daily_spending.sort_values('date')
            
            fig = px.line(
                daily_spending,
                x='date',
                y='amount',
                markers=True
            )
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Amount (₹)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent expenses table
        st.subheader("Recent Expenses")
        recent = df.head(15)[['date', 'amount', 'category', 'description']]
        st.dataframe(recent, use_container_width=True, height=400)
    
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

# TAB 2: Predictions
with tab2:
    st.subheader("📈 AI-Powered Expense Forecast")
    
    forecast_days = st.slider("Forecast Period (days)", 7, 60, 30)
    
    if st.button("Generate Forecast"):
        with st.spinner("Training AI model... This may take 30-60 seconds"):
            try:
                predictions = forecaster.predict_future(forecast_days)
                
                # Store in session state
                st.session_state.predictions = predictions
                st.success("✅ Forecast generated!")
            except Exception as e:
                st.error(f"Prediction failed: {str(e)}")
                st.info("💡 Tip: Need at least 14 days of data for accurate predictions")
    
    # Display predictions if available
    if 'predictions' in st.session_state:
        try:
            predictions = st.session_state.predictions
            
            # Visualization
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=predictions['Date'],
                y=predictions['Predicted'],
                mode='lines+markers',
                name='Predicted',
                line=dict(color='royalblue', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=predictions['Date'],
                y=predictions['Upper_Bound'],
                fill=None,
                mode='lines',
                name='Upper Bound',
                line=dict(color='lightblue', width=1)
            ))
            
            fig.add_trace(go.Scatter(
                x=predictions['Date'],
                y=predictions['Lower_Bound'],
                fill='tonexty',
                mode='lines',
                name='Lower Bound',
                line=dict(color='lightblue', width=1)
            ))
            
            fig.update_layout(
                title=f"Next {forecast_days} Days Expense Forecast",
                xaxis_title="Date",
                yaxis_title="Predicted Amount (₹)",
                hovermode='x unified',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Monthly prediction
            monthly_pred = predictions['Predicted'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Predicted Monthly Spend", f"₹{monthly_pred:,.2f}")
            with col2:
                budget_diff = monthly_budget - monthly_pred
                st.metric(
                    "Budget Status",
                    f"₹{abs(budget_diff):,.2f}",
                    delta=f"{'Within' if budget_diff >= 0 else 'Over'} Budget",
                    delta_color="normal" if budget_diff >= 0 else "inverse"
                )
            with col3:
                savings_rate = (budget_diff / monthly_budget) * 100 if budget_diff >= 0 else 0
                st.metric("Potential Savings", f"{savings_rate:.1f}%")
            
            # Prediction table
            st.subheader("Detailed Forecast")
            st.dataframe(predictions.head(15), use_container_width=True)
        
        except Exception as e:
            st.error(f"Error displaying predictions: {e}")

# TAB 3: Anomalies
with tab3:
    st.subheader("⚠️ Unusual Spending Detected")
    
    try:
        with st.spinner("Analyzing spending patterns..."):
            anomalies = detector.detect_anomalies()
        
        if len(anomalies) == 0:
            st.success("✅ No unusual expenses detected. All spending looks normal!")
        else:
            st.warning(f"Found {len(anomalies)} unusual transactions:")
            
            # Display anomalies
            anomalies_display = anomalies[['date', 'amount', 'category', 'description']].copy()
            st.dataframe(anomalies_display, use_container_width=True)
            
            # Visualization
            fig = px.scatter(
                anomalies,
                x='date',
                y='amount',
                color='category',
                size='amount',
                hover_data=['description'],
                title="Anomaly Distribution",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error detecting anomalies: {e}")
        st.info("Need sufficient data to detect anomalies")

# TAB 4: Email Alerts
with tab4:
    st.subheader("📧 Configure Email Alerts")
    
    st.info("💡 Get notified when your predicted spending exceeds budget or when anomalies are detected")
    
    st.markdown("""
    **Setup Instructions:**
    1. Use a Gmail account
    2. Generate an App Password at: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
    3. Select "Mail" and generate 16-character password
    4. Use that password below (not your regular Gmail password)
    """)
    
    with st.form("email_config"):
        sender_email = st.text_input("Your Gmail Address", placeholder="youremail@gmail.com")
        sender_password = st.text_input("Gmail App Password (16 characters)", type="password", placeholder="xxxx xxxx xxxx xxxx")
        recipient_email = st.text_input("Alert Recipient Email", placeholder="recipient@example.com")
        
        col1, col2 = st.columns(2)
        with col1:
            send_budget_alert = st.form_submit_button("📊 Send Budget Alert")
        with col2:
            send_anomaly_alert = st.form_submit_button("⚠️ Send Anomaly Alert")
        
        if send_budget_alert or send_anomaly_alert:
            if not all([sender_email, sender_password, recipient_email]):
                st.error("❌ Please fill all fields")
            else:
                try:
                    alert_system = EmailAlertSystem(sender_email, sender_password)
                    
                    if send_budget_alert:
                        if 'predictions' in st.session_state:
                            monthly_pred = st.session_state.predictions['Predicted'].sum()
                        else:
                            monthly_pred = forecaster.get_monthly_prediction()
                        
                        success = alert_system.send_budget_alert(
                            recipient_email,
                            monthly_pred,
                            monthly_budget
                        )
                        
                        if success:
                            st.success("✅ Budget alert email sent successfully!")
                        else:
                            st.error("❌ Failed to send email. Check your credentials.")
                    
                    if send_anomaly_alert:
                        anomalies = detector.detect_anomalies()
                        if len(anomalies) > 0:
                            top_anomaly = anomalies.iloc[0]
                            success = alert_system.send_anomaly_alert(
                                recipient_email,
                                top_anomaly['amount'],
                                top_anomaly['category']
                            )
                            if success:
                                st.success("✅ Anomaly alert email sent successfully!")
                        else:
                            st.info("No anomalies to report!")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("Common issues: Invalid credentials, App Password not enabled, or blocked by Gmail security")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #777; padding: 20px;'>
        <p>Made with ❤️ using Streamlit | AI-Powered by Prophet & Scikit-learn</p>
        <p style='font-size: 12px;'>Perfect for Campus Placements 🎓 | Fintech Project Portfolio</p>
    </div>
    """,
    unsafe_allow_html=True
)