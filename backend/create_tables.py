from app.config.database import engine, Base
from app.models.schemas import Customer, Transaction, FraudCase, CreditApplication, AgentLearningLog

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully!")
