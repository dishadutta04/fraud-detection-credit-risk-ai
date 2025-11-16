from app.config.database import SessionLocal
from app.models.schemas import Customer, KYCStatus
from datetime import datetime

db = SessionLocal()

customers = [
    Customer(
        customer_id="cust-12345",
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+91-9876543210",
        date_of_birth=datetime(1990, 5, 15),
        kyc_status=KYCStatus.VERIFIED,
        risk_score=720
    ),
    Customer(
        customer_id="cust-67890",
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        phone="+91-9876543211",
        date_of_birth=datetime(1985, 8, 22),
        kyc_status=KYCStatus.VERIFIED,
        risk_score=680
    )
]

try:
    for customer in customers:
        db.add(customer)
    db.commit()
    print("✅ Sample customers added successfully!")
    print(f"   - {customers[0].first_name} {customers[0].last_name} (ID: {customers[0].customer_id})")
    print(f"   - {customers[1].first_name} {customers[1].last_name} (ID: {customers[1].customer_id})")
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
