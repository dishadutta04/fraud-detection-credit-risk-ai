from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Enum, Text, JSON, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from ..config.database import Base
import enum

# Enums
class KYCStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    BLOCKED = "blocked"
    FLAGGED = "flagged"

class DecisionType(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"

# Database Models
class Customer(Base):
    __tablename__ = "customers"
    
    customer_id = Column(String(36), primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    date_of_birth = Column(DateTime)
    kyc_status = Column(Enum(KYCStatus), default=KYCStatus.PENDING)
    risk_score = Column(Integer, default=500)
    onboarding_date = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Transaction(Base):
    __tablename__ = "transactions"
    
    txn_id = Column(String(62), primary_key=True)
    customer_id = Column(String(36), ForeignKey("customers.customer_id"), nullable=False, index=True)
    amount = Column(DECIMAL(15, 2), nullable=False)
    currency = Column(String(3), default="USD")
    transaction_type = Column(String(20), nullable=False)
    merchant_id = Column(String(50))
    merchant_category = Column(String(10))
    location_lat = Column(Float)
    location_long = Column(Float)
    device_fingerprint = Column(String(255))
    ip_address = Column(String(45))
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)

class FraudCase(Base):
    __tablename__ = "fraud_cases"
    
    case_id = Column(String(62), primary_key=True)
    txn_id = Column(String(62), ForeignKey("transactions.txn_id"), unique=True, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    fraud_type = Column(String(50))
    detection_timestamp = Column(DateTime, server_default=func.now(), index=True)
    agent_version = Column(String(20))
    confidence_score = Column(Float)
    investigation_status = Column(String(20), default="open")
    investigator_id = Column(String(36))
    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)

class CreditApplication(Base):
    __tablename__ = "credit_applications"
    
    app_id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), ForeignKey("customers.customer_id"), nullable=False, index=True)
    requested_amount = Column(DECIMAL(15, 2), nullable=False)
    loan_purpose = Column(String(100))
    employment_status = Column(String(20))
    annual_income = Column(DECIMAL(15, 2))
    credit_bureau_score = Column(Integer)
    alternative_data_score = Column(Integer)
    final_risk_score = Column(Integer)
    decision = Column(Enum(DecisionType), default=DecisionType.MANUAL_REVIEW)
    decision_timestamp = Column(DateTime, server_default=func.now(), index=True)
    agent_version = Column(String(20))
    explainability_json = Column(JSON)
    human_override = Column(Boolean, default=False)
    override_reason = Column(Text)

class AgentLearningLog(Base):
    __tablename__ = "agent_learning_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    agent_type = Column(String(20), nullable=False, index=True)
    model_version = Column(String(20), nullable=False)
    accuracy = Column(Float)
    precision_score = Column(Float)
    recall_score = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)
    false_positive_rate = Column(Float)
    training_samples = Column(Integer)
    evaluation_date = Column(DateTime, server_default=func.now(), index=True)
    promoted_to_production = Column(Boolean, default=False)
