from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from ..config.database import get_db
from ..models.schemas import Transaction, FraudCase, TransactionStatus
from ..agents.orchestrator import OrchestratorAgent

router = APIRouter(prefix="/api/v1/fraud", tags=["Fraud Detection"])

class FraudCheckRequest(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float = Field(..., gt=0)
    merchant_id: str
    merchant_category: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None

class FraudCheckResponse(BaseModel):
    transaction_id: str
    fraud_probability: float
    risk_level: str
    action: str
    detection_time_ms: int
    anomalies: List[str]
    reasoning: str

orchestrator = OrchestratorAgent()

@router.post("/check", response_model=FraudCheckResponse)
async def check_fraud(
    request: FraudCheckRequest,
    db: Session = Depends(get_db)
):
    """Check transaction for fraud"""
    
    try:
        # Process through orchestrator
        result = orchestrator.process_request(
            task_type="fraud_detection",
            data=request.dict()
        )
        
        # Save transaction FIRST
        transaction = Transaction(
            txn_id=request.transaction_id,
            customer_id=request.customer_id,
            amount=request.amount,
            transaction_type="debit",
            merchant_id=request.merchant_id,
            merchant_category=request.merchant_category,
            location_lat=request.location.get('lat') if request.location else None,
            location_long=request.location.get('long') if request.location else None,
            device_fingerprint=request.device_fingerprint,
            ip_address=request.ip_address,
            status=TransactionStatus.APPROVED if result['action'] == 'approve' else TransactionStatus.FLAGGED
        )
        
        db.add(transaction)
        db.commit()  # Commit transaction FIRST
        db.refresh(transaction)
        
        # Create fraud case AFTER transaction is committed
        if result['fraud_probability'] > 60:
            fraud_case = FraudCase(
                case_id=result["case_id"],
                txn_id=request.transaction_id,  # Now this exists in transactions table
                fraud_probability=result["fraud_probability"],
                fraud_type="suspicious_activity",
                agent_version=result["agent_version"],
                confidence_score=result["fraud_probability"] / 100.0
            )
            db.add(fraud_case)
            db.commit()  # Commit fraud case
            db.refresh(fraud_case)
        
        return FraudCheckResponse(
            transaction_id=result["transaction_id"],
            fraud_probability=result["fraud_probability"],
            risk_level=result["risk_level"],
            action=result["action"],
            detection_time_ms=result["detection_time_ms"],
            anomalies=result["anomalies"],
            reasoning=result["reasoning"]
        )
        
    except Exception as e:
        db.rollback()  # Rollback on error
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cases")
async def get_fraud_cases(db: Session = Depends(get_db)):
    """Get all fraud cases"""
    
    cases = db.query(FraudCase).order_by(FraudCase.detection_timestamp.desc()).limit(100).all()
    
    return {"cases": [
        {
            "case_id": case.case_id,
            "txn_id": case.txn_id,
            "fraud_probability": case.fraud_probability,
            "status": case.investigation_status,
            "timestamp": case.detection_timestamp.isoformat()
        } for case in cases
    ]}
