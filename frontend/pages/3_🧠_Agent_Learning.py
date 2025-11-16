import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Agent Learning", page_icon="🧠", layout="wide")

st.title("🧠 Agent Learning & Performance")
st.markdown("Monitor and improve AI agent accuracy through feedback loops")
st.markdown("---")

# Get learning stats
try:
    response = requests.get(f"{API_URL}/api/v1/feedback/stats", timeout=5)
    if response.status_code == 200:
        stats = response.json()
        
        # Overall metrics
        st.subheader("📊 Current Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💳 Credit Assessment Agent")
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Total Applications", stats['credit_agent']['total_applications'])
                st.metric("With Feedback", stats['credit_agent']['with_feedback'])
            with metric_col2:
                st.metric("Correct Predictions", stats['credit_agent']['correct_predictions'])
                st.metric("Accuracy", f"{stats['credit_agent']['accuracy']:.1f}%")
        
        with col2:
            st.markdown("### 🚨 Fraud Detection Agent")
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Total Cases", stats['fraud_agent']['total_cases'])
                st.metric("Resolved Cases", stats['fraud_agent']['resolved_cases'])
            with metric_col2:
                st.metric("Confirmed Fraud", stats['fraud_agent']['confirmed_fraud'])
                st.metric("Accuracy", f"{stats['fraud_agent']['accuracy']:.1f}%")
        
        # Training history
        if stats['recent_training_logs']:
            st.markdown("---")
            st.subheader("📈 Training History")
            
            df = pd.DataFrame(stats['recent_training_logs'])
            
            # Group by agent type
            for agent in df['agent_type'].unique():
                agent_data = df[df['agent_type'] == agent]
                
                st.markdown(f"**{agent.upper()} Agent Performance Over Time**")
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=agent_data['date'], y=agent_data['accuracy'],
                    mode='lines+markers', name='Accuracy'
                ))
                fig.add_trace(go.Scatter(
                    x=agent_data['date'], y=agent_data['precision'],
                    mode='lines+markers', name='Precision'
                ))
                fig.add_trace(go.Scatter(
                    x=agent_data['date'], y=agent_data['recall'],
                    mode='lines+markers', name='Recall'
                ))
                
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Score",
                    yaxis_range=[0, 1],
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Feedback submission form
        st.markdown("---")
        st.subheader("📝 Submit Feedback")
        
        tab1, tab2 = st.tabs(["Credit Application Feedback", "Fraud Case Feedback"])
        
        with tab1:
            with st.form("credit_feedback_form"):
                app_id = st.text_input("Application ID")
                outcome = st.selectbox("Actual Outcome", 
                    ["paid_on_time", "default", "early_payoff", "restructured"])
                notes = st.text_area("Notes (optional)")
                
                submitted = st.form_submit_button("Submit Feedback")
                
                if submitted and app_id:
                    try:
                        payload = {
                            "entity_type": "credit_application",
                            "entity_id": app_id,
                            "actual_outcome": outcome,
                            "notes": notes
                        }
                        
                        resp = requests.post(f"{API_URL}/api/v1/feedback/submit", json=payload)
                        
                        if resp.status_code == 200:
                            result = resp.json()
                            st.success(f"✅ {result['message']}")
                            if result['will_retrain']:
                                st.info("🔄 Agent will retrain with this feedback")
                        else:
                            st.error(f"Error: {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        with tab2:
            with st.form("fraud_feedback_form"):
                case_id = st.text_input("Case ID")
                outcome = st.selectbox("Actual Outcome", 
                    ["confirmed_fraud", "false_positive", "unable_to_determine"])
                notes = st.text_area("Investigation Notes (optional)")
                
                submitted = st.form_submit_button("Submit Feedback")
                
                if submitted and case_id:
                    try:
                        payload = {
                            "entity_type": "fraud_case",
                            "entity_id": case_id,
                            "actual_outcome": outcome,
                            "notes": notes
                        }
                        
                        resp = requests.post(f"{API_URL}/api/v1/feedback/submit", json=payload)
                        
                        if resp.status_code == 200:
                            result = resp.json()
                            st.success(f"✅ {result['message']}")
                            if result['will_retrain']:
                                st.info("🔄 Agent will retrain with this feedback")
                        else:
                            st.error(f"Error: {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
    else:
        st.error("Unable to fetch learning statistics")
        
except Exception as e:
    st.error(f"Error connecting to API: {e}")

# Manual retraining button
st.markdown("---")
st.subheader("🔄 Manual Retraining")
st.info("Agents automatically retrain weekly. Use this button to trigger immediate retraining.")

if st.button("🚀 Retrain Agents Now"):
    st.warning("⏳ Retraining in progress... (This is simulated - run `python retrain_models.py` manually)")
    st.info("In production, this would trigger the retraining pipeline")
