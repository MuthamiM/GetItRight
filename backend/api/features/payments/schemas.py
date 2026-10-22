from typing import Optional
from pydantic import BaseModel, field_validator


class CheckoutRequest(BaseModel):
    plan: str

    @field_validator("plan")
    @classmethod
    def normalize_plan(cls, value: str) -> str:
        plan = value.strip().lower()
        if plan not in {"pro", "org"}:
            raise ValueError("Choose a paid plan.")
        return plan


class VerifyPaymentRequest(BaseModel):
    tx_ref: str
    transaction_id: Optional[str] = None

    @field_validator("tx_ref")
    @classmethod
    def validate_reference(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 80 or not value.startswith("icapsq_"):
            raise ValueError("Payment reference is invalid.")
        return value

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None
        value = value.strip()
        if not value.isdigit() or len(value) > 24:
            raise ValueError("Payment transaction ID is invalid.")
        return value
