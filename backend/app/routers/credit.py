from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from ..config.database import get_db
from ..models.schemas import CreditApplication, Customer, DecisionType
from ..agents.orchestrator import OrchestratorAgent
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/v1/credit", tags=["Credit Assessment"])

# Pydantic models for request/response
class CreditApplicationRequest(BaseModel):
    customer_id: str
    requested_amount: float = Field(..., gt=0)
    loan_purpose: str
    employment_status: str
    annual_income: float
    credit_bureau_score: Optional[int] = None
    alternative_data: Optional[Dict[str, Any]] = None

class CreditApplicationResponse(BaseModel):
    application_id: str
    decision: str
    risk_score: int
    confidence: float
    explainability: Dict[str, Any]
    processing_time_ms: int
    timestamp: str

# Initialize orchestrator
orchestrator = OrchestratorAgent()

@router.post("/assess", response_model=CreditApplicationResponse)
async def assess_credit_application(
    request: CreditApplicationRequest,
    db: Session = Depends(get_db)
):
    """Assess credit application using AI agent"""
    
    try:
        # Check if customer exists
        customer = db.query(Customer).filter(Customer.customer_id == request.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Process through orchestrator
        result = orchestrator.process_request(
            task_type="credit_assessment",
            data=request.dict()
        )
        
        # Save to database
        application = CreditApplication(
            app_id=result["application_id"],
            customer_id=request.customer_id,
            requested_amount=request.requested_amount,
            loan_purpose=request.loan_purpose,
            employment_status=request.employment_status,
            annual_income=request.annual_income,
            credit_bureau_score=request.credit_bureau_score,
            final_risk_score=result["risk_score"],
            decision=DecisionType(result["decision"]),
            agent_version=result["agent_version"],
            explainability_json={
                "positive_factors": result["positive_factors"],
                "risk_factors": result["risk_factors"],
                "reasoning": result["reasoning"]
            }
        )
        
        db.add(application)
        db.commit()
        db.refresh(application)
        
        return CreditApplicationResponse(
            application_id=result["application_id"],
            decision=result["decision"],
            risk_score=result["risk_score"],
            confidence=result["confidence"],
            explainability={
                "positive_factors": result["positive_factors"],
                "risk_factors": result["risk_factors"],
                "reasoning": result["reasoning"]
            },
            processing_time_ms=3200,  # Placeholder
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/applications")
async def get_applications(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all credit applications with optional status filter"""
    
    query = db.query(CreditApplication)
    
    if status:
        query = query.filter(CreditApplication.decision == status)
    
    applications = query.order_by(CreditApplication.decision_timestamp.desc()).limit(100).all()
    
    return {"applications": [
        {
            "app_id": app.app_id,
            "customer_id": app.customer_id,
            "requested_amount": float(app.requested_amount),
            "decision": app.decision.value,
            "risk_score": app.final_risk_score,
            "timestamp": app.decision_timestamp.isoformat()
        } for app in applications
    ]}
