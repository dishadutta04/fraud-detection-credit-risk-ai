import streamlit as st
import requests
import pandas as pd
import os

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Credit Applications", page_icon="💳", layout="wide")

st.title("💳 Credit Application Assessment")
st.markdown("AI-powered credit risk evaluation")

# Credit Application Form
st.subheader("New Credit Application")

with st.form("credit_application_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        customer_id = st.text_input("Customer ID", value="cust-12345")
        requested_amount = st.number_input("Requested Amount ($)", min_value=1000.0, value=50000.0, step=1000.0)
        loan_purpose = st.selectbox("Loan Purpose", ["home_renovation", "debt_consolidation", "business", "education", "medical", "other"])
        employment_status = st.selectbox("Employment Status", ["employed", "self_employed", "unemployed", "retired"])
    
    with col2:
        annual_income = st.number_input("Annual Income ($)", min_value=0.0, value=75000.0, step=1000.0)
        credit_bureau_score = st.number_input("Credit Bureau Score", min_value=300, max_value=850, value=720)
        utility_score = st.number_input("Utility Payment Score", min_value=300, max_value=900, value=850)
        rent_history = st.selectbox("Rent Payment History", ["excellent", "good", "fair", "poor"])
    
    submitted = st.form_submit_button("🎯 Assess Application")
    
    if submitted:
        with st.spinner("Evaluating application..."):
            try:
                payload = {
                    "customer_id": customer_id,
                    "requested_amount": requested_amount,
                    "loan_purpose": loan_purpose,
                    "employment_status": employment_status,
                    "annual_income": annual_income,
                    "credit_bureau_score": credit_bureau_score,
                    "alternative_data": {
                        "utility_payment_score": utility_score,
                        "rent_payment_history": rent_history
                    }
                }
                
                response = requests.post(f"{API_URL}/api/v1/credit/assess", json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("✅ Assessment Complete")
                    
                    # Display decision
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        decision_color = {"approved": "🟢", "rejected": "🔴", "manual_review": "🟡"}
                        st.metric("Decision", f"{decision_color.get(result['decision'], '⚪')} {result['decision'].upper()}")
                    with col2:
                        st.metric("Risk Score", f"{result['risk_score']}/1000")
                    with col3:
                        st.metric("Confidence", f"{result['confidence']*100:.1f}%")
                    
                    # Explainability
                    st.subheader("Decision Factors")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.success("**Positive Factors:**")
                        for factor in result['explainability']['positive_factors']:
                            st.write(f"✅ {factor}")
                    
                    with col2:
                        st.warning("**Risk Factors:**")
                        for factor in result['explainability']['risk_factors']:
                            st.write(f"⚠️ {factor}")
                    
                    st.info(f"**Reasoning:** {result['explainability']['reasoning']}")
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Recent Applications
st.markdown("---")
st.subheader("Recent Credit Applications")

try:
    response = requests.get(f"{API_URL}/api/v1/credit/applications")
    if response.status_code == 200:
        applications = response.json()["applications"]
        if applications:
            df = pd.DataFrame(applications)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No applications in the system")
except:
    st.error("Cannot connect to backend API")
