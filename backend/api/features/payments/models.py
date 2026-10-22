from sqlalchemy import Column, DateTime, Integer, String

from backend.api.core.database import Base


class PaymentIntentModel(Base):
    __tablename__ = "PaymentIntents"

    Id = Column(String, primary_key=True)
    UserId = Column(String, nullable=False, index=True)
    TxRef = Column(String, nullable=False, unique=True, index=True)
    PlanKey = Column(String, nullable=False)
    Amount = Column(Integer, nullable=False)
    Currency = Column(String(3), nullable=False, default="KES")
    Status = Column(String, nullable=False, default="pending", index=True)
    CheckoutUrl = Column(String(1024), nullable=True)
    ProviderTransactionId = Column(String, nullable=True, unique=True)
    CreatedAt = Column(DateTime(timezone=True), nullable=False)
    UpdatedAt = Column(DateTime(timezone=True), nullable=False)
    ExpiresAt = Column(DateTime(timezone=True), nullable=False)
    PaidAt = Column(DateTime(timezone=True), nullable=True)
