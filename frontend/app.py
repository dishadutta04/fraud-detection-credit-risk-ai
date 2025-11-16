import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Fraud Detection AI System",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<p class="main-header">🔒 Fraud Detection & Credit Risk AI System</p>', unsafe_allow_html=True)
st.markdown("---")

# Check API health
try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    if response.status_code == 200:
        st.success("✅ System Online")
    else:
        st.error("❌ System Error")
except:
    st.error("❌ Cannot connect to backend API")

# Dashboard metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📊 Transactions Today",
        value="1,234",
        delta="+15%"
    )

with col2:
    st.metric(
        label="🚨 Fraud Detected",
        value="23",
        delta="-5%",
        delta_color="inverse"
    )

with col3:
    st.metric(
        label="💳 Credit Applications",
        value="156",
        delta="+8%"
    )

with col4:
    st.metric(
        label="🎯 Detection Accuracy",
        value="94.2%",
        delta="+1.2%"
    )

st.markdown("---")

# Recent Activity
st.subheader("📈 Recent Activity")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Fraud Alerts")
    try:
        response = requests.get(f"{API_URL}/api/v1/fraud/cases")
        if response.status_code == 200:
            cases = response.json()["cases"][:5]
            if cases:
                df = pd.DataFrame(cases)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No fraud cases detected")
        else:
            st.warning("Unable to fetch fraud cases")
    except:
        st.error("API connection error")

with col2:
    st.markdown("### Credit Applications")
    try:
        response = requests.get(f"{API_URL}/api/v1/credit/applications")
        if response.status_code == 200:
            applications = response.json()["applications"][:5]
            if applications:
                df = pd.DataFrame(applications)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No recent applications")
        else:
            st.warning("Unable to fetch applications")
    except:
        st.error("API connection error")

# Visualization
st.markdown("---")
st.subheader("📊 Analytics")

# Sample data for demo
demo_data = pd.DataFrame({
    'Date': pd.date_range(start='2025-11-01', periods=15, freq='D'),
    'Transactions': [120, 135, 142, 158, 149, 167, 178, 185, 192, 201, 215, 223, 234, 245, 256],
    'Fraud_Detected': [2, 3, 1, 4, 2, 5, 3, 6, 4, 3, 7, 5, 4, 6, 8]
})

col1, col2 = st.columns(2)

with col1:
    fig1 = px.line(demo_data, x='Date', y='Transactions', title='Daily Transaction Volume')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.bar(demo_data, x='Date', y='Fraud_Detected', title='Fraud Detection Trends')
    st.plotly_chart(fig2, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("**🔒 Fraud Detection AI System** | Powered by LangGraph, FastAPI & Streamlit")
