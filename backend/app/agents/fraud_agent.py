from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..config.settings import settings
from typing import Dict, Any
import uuid
from datetime import datetime

class FraudDetectionAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1  # Low temperature for consistent fraud detection
        )
        
        self.system_prompt = """You are an expert fraud detection agent for a financial institution.

Your responsibilities:
1. Analyze transactions in real-time for fraud indicators
2. Calculate fraud probability (0-100%)
3. Recommend actions (approve/flag/block/verify)
4. Identify suspicious patterns

Fraud Indicators:
- Unusual transaction amounts
- Location anomalies (sudden changes)
- Velocity abuse (multiple transactions quickly)
- Device/IP mismatches
- Out-of-pattern merchant categories
- Dormant account reactivation

Thresholds:
- >90% probability: Auto-block
- 60-90% probability: Request additional verification
- <60% probability: Approve with monitoring

Always provide fraud probability, risk level, recommended action, and detected anomalies.
"""
    
    def check_transaction(self, transaction_data: Dict[str, Any], customer_history: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check transaction for fraud indicators"""
        
        # Build context from customer history
        history_context = "No previous transaction history available."
        if customer_history:
            history_context = f"""
Customer Transaction History:
- Average transaction amount: ${customer_history.get('avg_amount', 0):,.2f}
- Typical merchants: {', '.join(customer_history.get('common_merchants', []))}
- Usual locations: {', '.join(customer_history.get('common_locations', []))}
- Transaction frequency: {customer_history.get('frequency', 'Unknown')}
"""
        
        prompt = f"""
Analyze this transaction for fraud:

Transaction ID: {transaction_data.get('transaction_id')}
Customer ID: {transaction_data.get('customer_id')}
Amount: ${transaction_data.get('amount'):,.2f}
Merchant: {transaction_data.get('merchant_id')} (Category: {transaction_data.get('merchant_category', 'Unknown')})
Location: Lat {transaction_data.get('location', {}).get('lat')}, Long {transaction_data.get('location', {}).get('long')}
Device Fingerprint: {transaction_data.get('device_fingerprint', 'Unknown')}
IP Address: {transaction_data.get('ip_address', 'Unknown')}

{history_context}

Provide your analysis in JSON format:
{{
    "fraud_probability": <0-100>,
    "risk_level": "<low/medium/high/critical>",
    "action": "<approve/flag/block/verify>",
    "anomalies": ["anomaly1", "anomaly2"],
    "reasoning": "Brief explanation"
}}
"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response
        import json
        try:
            result = json.loads(response.content)
        except:
            result = {
                "fraud_probability": 50.0,
                "risk_level": "medium",
                "action": "flag",
                "anomalies": ["Unable to parse response"],
                "reasoning": "System error - flagged for manual review"
            }
        
        # Add metadata
        result["transaction_id"] = transaction_data.get('transaction_id')
        result["case_id"] = str(uuid.uuid4())
        result["detection_time_ms"] = 200  # Placeholder
        result["agent_version"] = "v1.0"
        result["timestamp"] = datetime.utcnow().isoformat()
        
        return result
