from typing import Optional
import re
from pydantic import BaseModel, field_validator


class CheckoutRequest(BaseModel):
    plan: str

    @field_validator("plan")
    @classmethod
    def normalize_plan(cls, value: str) -> str:
        plan = value.strip().lower()
        if plan == "election":
            raise ValueError("That plan is no longer available.")
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
        if not value or len(value) > 80 or not re.fullmatch(r"(?:icapsq_[a-f0-9]{32}|IC[A-F0-9]{24})", value):
            raise ValueError("Payment reference is invalid.")
        return value

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not value.strip():
            return None
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9]{1,64}", value):
            raise ValueError("Payment transaction ID is invalid.")
        return value
