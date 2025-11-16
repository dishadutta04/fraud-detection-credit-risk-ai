from app.config.database import SessionLocal
from app.models.schemas import CreditApplication, FraudCase, AgentLearningLog
from datetime import datetime
import json

def calculate_credit_metrics(db):
    """Calculate credit agent performance metrics"""
    
    apps = db.query(CreditApplication).filter(
        CreditApplication.explainability_json.isnot(None)
    ).all()
    
    apps_with_feedback = [
        app for app in apps 
        if app.explainability_json and "actual_outcome" in app.explainability_json
    ]
    
    if not apps_with_feedback:
        print("⚠️  No feedback data available for credit agent")
        return None
    
    total = len(apps_with_feedback)
    correct = len([
        app for app in apps_with_feedback 
        if app.explainability_json.get("prediction_correct") == True
    ])
    
    # Calculate precision and recall
    true_positives = len([
        app for app in apps_with_feedback 
        if app.decision.value == "approved" 
        and app.explainability_json.get("actual_outcome") == "paid_on_time"
    ])
    
    false_positives = len([
        app for app in apps_with_feedback 
        if app.decision.value == "approved" 
        and app.explainability_json.get("actual_outcome") == "default"
    ])
    
    false_negatives = len([
        app for app in apps_with_feedback 
        if app.decision.value == "rejected" 
        and app.explainability_json.get("actual_outcome") == "paid_on_time"
    ])
    
    accuracy = correct / total if total > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "training_samples": total
    }

def calculate_fraud_metrics(db):
    """Calculate fraud agent performance metrics"""
    
    cases = db.query(FraudCase).filter(
        FraudCase.investigation_status.in_(["confirmed", "false_positive"])
    ).all()
    
    if not cases:
        print("⚠️  No resolved fraud cases for training")
        return None
    
    total = len(cases)
    correct = len([
        case for case in cases 
        if (case.fraud_probability > 60 and case.investigation_status == "confirmed") or
           (case.fraud_probability <= 60 and case.investigation_status == "false_positive")
    ])
    
    # Calculate metrics
    true_positives = len([
        case for case in cases 
        if case.fraud_probability > 60 and case.investigation_status == "confirmed"
    ])
    
    false_positives = len([
        case for case in cases 
        if case.fraud_probability > 60 and case.investigation_status == "false_positive"
    ])
    
    false_negatives = len([
        case for case in cases 
        if case.fraud_probability <= 60 and case.investigation_status == "confirmed"
    ])
    
    accuracy = correct / total if total > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr = false_positives / (false_positives + len([c for c in cases if c.investigation_status == "false_positive"])) if total > 0 else 0
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "false_positive_rate": fpr,
        "training_samples": total
    }

def retrain_agents():
    """Main retraining function"""
    
    db = SessionLocal()
    
    try:
        print("🤖 Starting agent retraining process...")
        print("=" * 60)
        
        # Credit Agent
        print("\n📊 Evaluating Credit Assessment Agent...")
        credit_metrics = calculate_credit_metrics(db)
        
        if credit_metrics:
            print(f"   Accuracy: {credit_metrics['accuracy']:.2%}")
            print(f"   Precision: {credit_metrics['precision']:.2%}")
            print(f"   Recall: {credit_metrics['recall']:.2%}")
            print(f"   F1 Score: {credit_metrics['f1_score']:.2%}")
            print(f"   Training Samples: {credit_metrics['training_samples']}")
            
            # Log metrics
            log = AgentLearningLog(
                agent_type="credit",
                model_version="v1.1",
                accuracy=credit_metrics['accuracy'],
                precision_score=credit_metrics['precision'],
                recall_score=credit_metrics['recall'],
                f1_score=credit_metrics['f1_score'],
                training_samples=credit_metrics['training_samples'],
                promoted_to_production=credit_metrics['accuracy'] > 0.75
            )
            db.add(log)
            
            if credit_metrics['accuracy'] > 0.75:
                print("   ✅ Model promoted to production")
            else:
                print("   ⚠️  Model needs improvement (accuracy < 75%)")
        
        # Fraud Agent
        print("\n🚨 Evaluating Fraud Detection Agent...")
        fraud_metrics = calculate_fraud_metrics(db)
        
        if fraud_metrics:
            print(f"   Accuracy: {fraud_metrics['accuracy']:.2%}")
            print(f"   Precision: {fraud_metrics['precision']:.2%}")
            print(f"   Recall: {fraud_metrics['recall']:.2%}")
            print(f"   F1 Score: {fraud_metrics['f1_score']:.2%}")
            print(f"   False Positive Rate: {fraud_metrics['false_positive_rate']:.2%}")
            print(f"   Training Samples: {fraud_metrics['training_samples']}")
            
            # Log metrics
            log = AgentLearningLog(
                agent_type="fraud",
                model_version="v1.1",
                accuracy=fraud_metrics['accuracy'],
                precision_score=fraud_metrics['precision'],
                recall_score=fraud_metrics['recall'],
                f1_score=fraud_metrics['f1_score'],
                false_positive_rate=fraud_metrics['false_positive_rate'],
                training_samples=fraud_metrics['training_samples'],
                promoted_to_production=fraud_metrics['accuracy'] > 0.85
            )
            db.add(log)
            
            if fraud_metrics['accuracy'] > 0.85:
                print("   ✅ Model promoted to production")
            else:
                print("   ⚠️  Model needs improvement (accuracy < 85%)")
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ Retraining process completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during retraining: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    retrain_agents()
