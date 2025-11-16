import streamlit as st
import requests
import pandas as pd
import uuid
import os

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Fraud Monitoring", page_icon="🚨", layout="wide")

st.title("🚨 Fraud Detection Monitoring")
st.markdown("Real-time transaction fraud detection and investigation")

# Fraud Check Form
st.subheader("Check New Transaction")

with st.form("fraud_check_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        txn_id = st.text_input("Transaction ID", value=f"txn-{uuid.uuid4()}", disabled=True)
        customer_id = st.text_input("Customer ID", value="cust-12345")
        amount = st.number_input("Amount ($)", min_value=0.01, value=1500.00)
        merchant_id = st.text_input("Merchant ID", value="merchant-xyz")
    
    with col2:
        merchant_category = st.selectbox("Merchant Category", ["retail", "online", "restaurant", "travel", "other"])
        device_fingerprint = st.text_input("Device Fingerprint", value="device-abc123")
        ip_address = st.text_input("IP Address", value="203.0.113.45")
        
        col_lat, col_long = st.columns(2)
        with col_lat:
            latitude = st.number_input("Latitude", value=26.9124)
        with col_long:
            longitude = st.number_input("Longitude", value=75.7873)
    
    submitted = st.form_submit_button("🔍 Check for Fraud")
    
    if submitted:
        with st.spinner("Analyzing transaction..."):
            try:
                payload = {
                    "transaction_id": txn_id,
                    "customer_id": customer_id,
                    "amount": amount,
                    "merchant_id": merchant_id,
                    "merchant_category": merchant_category,
                    "location": {"lat": latitude, "long": longitude},
                    "device_fingerprint": device_fingerprint,
                    "ip_address": ip_address
                }
                
                response = requests.post(f"{API_URL}/api/v1/fraud/check", json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display results
                    st.success("✅ Analysis Complete")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Fraud Probability", f"{result['fraud_probability']:.1f}%")
                    with col2:
                        st.metric("Risk Level", result['risk_level'].upper())
                    with col3:
                        st.metric("Recommended Action", result['action'].upper())
                    
                    # Detailed results
                    st.subheader("Analysis Details")
                    st.write(f"**Reasoning:** {result['reasoning']}")
                    
                    if result['anomalies']:
                        st.warning("**Detected Anomalies:**")
                        for anomaly in result['anomalies']:
                            st.write(f"- {anomaly}")
                    
                    # Action recommendation
                    if result['action'] == 'block':
                        st.error("🚫 **RECOMMENDED ACTION:** Block this transaction immediately")
                    elif result['action'] == 'verify':
                        st.warning("⚠️ **RECOMMENDED ACTION:** Request additional verification")
                    else:
                        st.success("✅ **RECOMMENDED ACTION:** Approve transaction")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Error connecting to API: {str(e)}")

# Recent Fraud Cases
st.markdown("---")
st.subheader("Recent Fraud Cases")

try:
    response = requests.get(f"{API_URL}/api/v1/fraud/cases")
    if response.status_code == 200:
        cases = response.json()["cases"]
        if cases:
            df = pd.DataFrame(cases)
            
            # Add color coding
            def highlight_risk(row):
                if row['fraud_probability'] > 90:
                    return ['background-color: #ffcccc'] * len(row)
                elif row['fraud_probability'] > 60:
                    return ['background-color: #fff4cc'] * len(row)
                else:
                    return [''] * len(row)
            
            st.dataframe(df.style.apply(highlight_risk, axis=1), use_container_width=True)
        else:
            st.info("No fraud cases in the system")
    else:
        st.warning("Unable to fetch fraud cases")
except:
    st.error("Cannot connect to backend API")
