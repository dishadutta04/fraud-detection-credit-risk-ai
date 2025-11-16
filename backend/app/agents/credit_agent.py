from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from langchain_core.messages import HumanMessage, SystemMessage
from ..config.settings import settings
from typing import Dict, Any
import uuid
from datetime import datetime

class CreditAssessmentAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.3
        )
        
        self.system_prompt = """You are an expert credit risk assessment agent for a financial institution.
        
Your responsibilities:
1. Analyze credit applications using traditional and alternative data
2. Calculate risk scores (0-1000, where 1000 is lowest risk)
3. Provide clear explanations for your decisions
4. Identify key risk factors and positive indicators

Decision Rules:
- Score >750: Auto-approve
- Score 300-750: Manual review
- Score <300: Auto-reject

Always provide:
1. Final risk score
2. Decision (approved/rejected/manual_review)
3. Confidence level (0-1)
4. Top 3 positive factors
5. Top 3 risk factors
"""
    
    def assess_application(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess credit application and return decision"""
        
        # Create prompt with application data
        prompt = f"""
Analyze this credit application:

Customer ID: {application_data.get('customer_id')}
Requested Amount: ${application_data.get('requested_amount'):,.2f}
Loan Purpose: {application_data.get('loan_purpose')}
Employment Status: {application_data.get('employment_status')}
Annual Income: ${application_data.get('annual_income', 0):,.2f}
Credit Bureau Score: {application_data.get('credit_bureau_score', 'N/A')}

Alternative Data:
- Utility Payment Score: {application_data.get('alternative_data', {}).get('utility_payment_score', 'N/A')}
- Rent Payment History: {application_data.get('alternative_data', {}).get('rent_payment_history', 'N/A')}

Provide your assessment in JSON format:
{{
    "risk_score": <0-1000>,
    "decision": "<approved/rejected/manual_review>",
    "confidence": <0.0-1.0>,
    "positive_factors": ["factor1", "factor2", "factor3"],
    "risk_factors": ["factor1", "factor2", "factor3"],
    "reasoning": "Brief explanation"
}}
"""
        
        # Invoke LLM
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # Parse response (simplified - add proper JSON parsing)
        import json
        try:
            result = json.loads(response.content)
        except:
            # Fallback if JSON parsing fails
            result = {
                "risk_score": 500,
                "decision": "manual_review",
                "confidence": 0.5,
                "positive_factors": ["Requires manual review"],
                "risk_factors": ["Unable to parse LLM response"],
                "reasoning": "System error - manual review required"
            }
        
        # Add metadata
        result["application_id"] = str(uuid.uuid4())
        result["agent_version"] = "v1.0"
        result["timestamp"] = datetime.utcnow().isoformat()
        
        return result
