from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..config.database import get_db
from ..models.schemas import CreditApplication, FraudCase, AgentLearningLog
import uuid

router = APIRouter(prefix="/api/v1/feedback", tags=["Self-Learning"])

class FeedbackRequest(BaseModel):
    entity_type: str  # "credit_application" or "fraud_case"
    entity_id: str
    actual_outcome: str  # "default", "paid_on_time", "confirmed_fraud", "false_positive"
    notes: Optional[str] = None

class FeedbackResponse(BaseModel):
    feedback_id: str
    status: str
    message: str
    will_retrain: bool

@router.post("/submit", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """Submit feedback for agent learning"""
    
    try:
        feedback_id = str(uuid.uuid4())
        
        if request.entity_type == "credit_application":
            # Update credit application with actual outcome
            app = db.query(CreditApplication).filter(
                CreditApplication.app_id == request.entity_id
            ).first()
            
            if not app:
                raise HTTPException(status_code=404, detail="Application not found")
            
            # Store outcome in explainability JSON
            if app.explainability_json is None:
                app.explainability_json = {}
            
            app.explainability_json["actual_outcome"] = request.actual_outcome
            app.explainability_json["feedback_date"] = datetime.utcnow().isoformat()
            app.explainability_json["feedback_notes"] = request.notes
            
            # Calculate accuracy
            was_correct = (
                (app.decision.value == "approved" and request.actual_outcome == "paid_on_time") or
                (app.decision.value == "rejected" and request.actual_outcome == "default")
            )
            
            app.explainability_json["prediction_correct"] = was_correct
            
            db.commit()
            
            return FeedbackResponse(
                feedback_id=feedback_id,
                status="recorded",
                message=f"Feedback recorded for credit application. Prediction was {'correct' if was_correct else 'incorrect'}.",
                will_retrain=True
            )
        
        elif request.entity_type == "fraud_case":
            # Update fraud case with actual outcome
            case = db.query(FraudCase).filter(
                FraudCase.case_id == request.entity_id
            ).first()
            
            if not case:
                raise HTTPException(status_code=404, detail="Fraud case not found")
            
            # Update investigation status
            case.investigation_status = "confirmed" if "confirmed" in request.actual_outcome else "false_positive"
            case.resolution_notes = request.notes
            case.resolved_at = datetime.utcnow()
            
            # Calculate accuracy
            was_correct = (
                (case.fraud_probability > 60 and request.actual_outcome == "confirmed_fraud") or
                (case.fraud_probability <= 60 and request.actual_outcome == "false_positive")
            )
            
            db.commit()
            
            return FeedbackResponse(
                feedback_id=feedback_id,
                status="recorded",
                message=f"Feedback recorded for fraud case. Detection was {'correct' if was_correct else 'incorrect'}.",
                will_retrain=True
            )
        
        else:
            raise HTTPException(status_code=400, detail="Invalid entity_type")
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_learning_stats(db: Session = Depends(get_db)):
    """Get agent learning statistics"""
    
    try:
        # Credit agent stats
        credit_apps = db.query(CreditApplication).filter(
            CreditApplication.explainability_json.isnot(None)
        ).all()
        
        credit_total = len(credit_apps)
        credit_with_feedback = len([
            app for app in credit_apps 
            if app.explainability_json and "actual_outcome" in app.explainability_json
        ])
        credit_correct = len([
            app for app in credit_apps 
            if app.explainability_json 
            and app.explainability_json.get("prediction_correct") == True
        ])
        
        credit_accuracy = (credit_correct / credit_with_feedback * 100) if credit_with_feedback > 0 else 0
        
        # Fraud agent stats
        fraud_cases = db.query(FraudCase).all()
        fraud_total = len(fraud_cases)
        fraud_resolved = len([
            case for case in fraud_cases 
            if case.investigation_status in ["confirmed", "false_positive"]
        ])
        
        fraud_confirmed = len([
            case for case in fraud_cases 
            if case.investigation_status == "confirmed"
        ])
        fraud_false_positives = len([
            case for case in fraud_cases 
            if case.investigation_status == "false_positive"
        ])
        
        fraud_accuracy = (fraud_confirmed / fraud_resolved * 100) if fraud_resolved > 0 else 0
        
        # Get latest learning logs
        latest_logs = db.query(AgentLearningLog).order_by(
            AgentLearningLog.evaluation_date.desc()
        ).limit(10).all()
        
        return {
            "credit_agent": {
                "total_applications": credit_total,
                "with_feedback": credit_with_feedback,
                "correct_predictions": credit_correct,
                "accuracy": round(credit_accuracy, 2)
            },
            "fraud_agent": {
                "total_cases": fraud_total,
                "resolved_cases": fraud_resolved,
                "confirmed_fraud": fraud_confirmed,
                "false_positives": fraud_false_positives,
                "accuracy": round(fraud_accuracy, 2)
            },
            "recent_training_logs": [
                {
                    "agent_type": log.agent_type,
                    "model_version": log.model_version,
                    "accuracy": log.accuracy,
                    "precision": log.precision_score,
                    "recall": log.recall_score,
                    "date": log.evaluation_date.isoformat()
                } for log in latest_logs
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
