import hmac
import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.api.core.config import settings
from backend.api.features.auth.models import UserModel
from backend.api.features.payments.models import PaymentIntentModel
from backend.api.features.users.service import (
    PLAN_METADATA,
    PLAN_TIER_RANK,
    expire_user_plan_if_needed,
)

logger = logging.getLogger(__name__)
FLUTTERWAVE_API = "https://api.flutterwave.com/v3"
BILLING_DAYS = 30
CHECKOUT_MINUTES = 30
# Match the public pricing page. Election/enterprise remains custom-quoted and
# must not be charged a guessed flat amount through self-service checkout.
PLAN_PRICES_KES = {"pro": 1500, "org": 6500}


def _utc_iso(value: datetime | None) -> str | None:
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def payments_configured() -> bool:
    return bool(settings.FLW_SECRET_KEY.strip() and settings.FLW_SECRET_HASH.strip())


def public_plan_catalog() -> dict:
    return {
        "currency": "KES",
        "billingDays": BILLING_DAYS,
        "checkoutEnabled": payments_configured(),
        "paymentMethods": ["M-Pesa", "Card"],
        "plans": [
            {
                "key": key,
                "name": PLAN_METADATA[key]["name"],
                "amount": amount,
                "currency": "KES",
                "billingDays": BILLING_DAYS,
            }
            for key, amount in PLAN_PRICES_KES.items()
        ],
    }


def _provider_request(method: str, path: str, payload: dict | None = None) -> dict:
    if not settings.FLW_SECRET_KEY.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Secure plan checkout is not configured on this server.",
        )
    try:
        response = httpx.request(
            method,
            f"{FLUTTERWAVE_API}{path}",
            headers={
                "Authorization": f"Bearer {settings.FLW_SECRET_KEY.strip()}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=15.0,
        )
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise ValueError("Unexpected payment provider response")
        return body
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Flutterwave request failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Secure checkout is temporarily unavailable. No plan change was made.",
        ) from None


def _validate_checkout_link(value: object) -> str:
    if not isinstance(value, str):
        raise HTTPException(status_code=503, detail="Secure checkout could not be started.")
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != "checkout.flutterwave.com":
        raise HTTPException(status_code=503, detail="Secure checkout returned an invalid destination.")
    return value


def initiate_checkout(db: Session, user_id: str, plan_key: str) -> dict:
    if not payments_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Paid checkout is not configured yet. No payment was taken and your plan was not changed.",
        )
    if plan_key not in PLAN_PRICES_KES:
        raise HTTPException(status_code=422, detail="Choose an available paid plan.")

    user = db.query(UserModel).filter(UserModel.Id == user_id).first()
    if not user or user.Status != "Active":
        raise HTTPException(status_code=401, detail="Your account is unavailable.")
    if user.Role in {"Admin", "Super Admin"}:
        raise HTTPException(status_code=403, detail="Administrator accounts do not use client plans.")
    user = expire_user_plan_if_needed(db, user)

    current_rank = PLAN_TIER_RANK.get((user.Plan or "free").lower(), 0)
    target_rank = PLAN_TIER_RANK[plan_key]
    if target_rank < current_rank:
        raise HTTPException(status_code=400, detail="Choose your current plan or a higher plan.")

    now = datetime.now(timezone.utc)
    existing = (
        db.query(PaymentIntentModel)
        .filter(
            PaymentIntentModel.UserId == user.Id,
            PaymentIntentModel.PlanKey == plan_key,
            PaymentIntentModel.Status == "pending",
            PaymentIntentModel.ExpiresAt > now,
            PaymentIntentModel.CheckoutUrl.is_not(None),
        )
        .order_by(PaymentIntentModel.CreatedAt.desc())
        .first()
    )
    if existing:
        return {
            "checkout_url": existing.CheckoutUrl,
            "tx_ref": existing.TxRef,
            "amount": existing.Amount,
            "currency": existing.Currency,
            "plan": existing.PlanKey,
            "status": existing.Status,
        }

    amount = PLAN_PRICES_KES[plan_key]
    tx_ref = f"icapsq_{uuid.uuid4().hex}"
    intent = PaymentIntentModel(
        Id=str(uuid.uuid4()),
        UserId=user.Id,
        TxRef=tx_ref,
        PlanKey=plan_key,
        Amount=amount,
        Currency="KES",
        Status="pending",
        CreatedAt=now,
        UpdatedAt=now,
        ExpiresAt=now + timedelta(minutes=CHECKOUT_MINUTES),
    )
    db.add(intent)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not save a plan payment intent")
        raise HTTPException(status_code=503, detail="Secure checkout could not be started.") from None

    payload = {
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": "KES",
        "redirect_url": f"{settings.APP_PUBLIC_URL.rstrip('/')}/pages/payment-return.html",
        "payment_options": "card, mpesa",
        "customer": {"email": user.Email, "name": user.FullName},
        "customizations": {
            "title": "IcapsQ plan",
            "description": f"{PLAN_METADATA[plan_key]['name']} access for {BILLING_DAYS} days",
        },
    }
    try:
        provider = _provider_request("POST", "/payments", payload)
        if provider.get("status") != "success":
            raise HTTPException(status_code=503, detail="Secure checkout could not be started.")
        intent.CheckoutUrl = _validate_checkout_link((provider.get("data") or {}).get("link"))
        intent.UpdatedAt = datetime.now(timezone.utc)
        db.commit()
    except HTTPException:
        intent.Status = "failed"
        intent.UpdatedAt = datetime.now(timezone.utc)
        db.commit()
        raise
    except Exception as exc:
        db.rollback()
        logger.warning("Could not persist checkout link (%s)", type(exc).__name__)
        db.query(PaymentIntentModel).filter(PaymentIntentModel.Id == intent.Id).update(
            {"Status": "failed", "UpdatedAt": datetime.now(timezone.utc)}
        )
        db.commit()
        raise HTTPException(status_code=503, detail="Secure checkout could not be started.") from None

    return {
        "checkout_url": intent.CheckoutUrl,
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": "KES",
        "plan": plan_key,
        "status": "pending",
    }


def _verify_provider_transaction(transaction_id: str) -> dict:
    if not transaction_id.isdigit() or len(transaction_id) > 24:
        raise HTTPException(status_code=422, detail="Payment transaction ID is invalid.")
    return _provider_request("GET", f"/transactions/{transaction_id}/verify")


def _mark_verified_payment(db: Session, intent: PaymentIntentModel, provider_data: dict) -> dict:
    if intent.Status == "paid":
        return {
            "status": "paid",
            "plan": intent.PlanKey,
            "planName": PLAN_METADATA[intent.PlanKey]["name"],
            "expiresAt": None,
        }

    provider_status = str(provider_data.get("status") or "").lower()
    if provider_status != "successful":
        if provider_status in {"failed", "cancelled", "canceled"}:
            intent.Status = "failed"
            intent.UpdatedAt = datetime.now(timezone.utc)
            db.commit()
            return {"status": "failed", "plan": intent.PlanKey}
        return {"status": "pending", "plan": intent.PlanKey}

    if (
        str(provider_data.get("tx_ref") or "") != intent.TxRef
        or str(provider_data.get("currency") or "").upper() != intent.Currency
    ):
        intent.Status = "rejected"
        intent.UpdatedAt = datetime.now(timezone.utc)
        db.commit()
        logger.error("Payment verification mismatch for intent %s", intent.Id)
        raise HTTPException(status_code=409, detail="Payment details could not be verified.")

    raw_amount = provider_data.get("amount", provider_data.get("charged_amount"))
    try:
        paid_amount = Decimal(str(raw_amount))
    except (InvalidOperation, TypeError):
        paid_amount = Decimal("0")
    if not paid_amount.is_finite() or paid_amount != Decimal(intent.Amount):
        intent.Status = "rejected"
        intent.UpdatedAt = datetime.now(timezone.utc)
        db.commit()
        logger.error("Payment amount mismatch for intent %s", intent.Id)
        raise HTTPException(status_code=409, detail="Payment amount could not be verified.")

    user = db.query(UserModel).filter(UserModel.Id == intent.UserId).first()
    if not user or user.Status != "Active":
        intent.Status = "rejected"
        intent.UpdatedAt = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=409, detail="Payment account could not be verified.")

    now = datetime.now(timezone.utc)
    previous_expiry = user.PlanExpiresAt
    if previous_expiry and previous_expiry.tzinfo is None:
        previous_expiry = previous_expiry.replace(tzinfo=timezone.utc)
    billing_starts = max(now, previous_expiry) if previous_expiry else now

    # Claim this transaction exactly once. A repeated return-page request or
    # duplicate webhook must never extend the paid period twice.
    claimed = (
        db.query(PaymentIntentModel)
        .filter(PaymentIntentModel.Id == intent.Id, PaymentIntentModel.Status != "paid")
        .update(
            {
                "Status": "paid",
                "ProviderTransactionId": str(provider_data.get("id") or "") or None,
                "PaidAt": now,
                "UpdatedAt": now,
            },
            synchronize_session=False,
        )
    )
    if claimed != 1:
        db.rollback()
        refreshed = db.query(PaymentIntentModel).filter(PaymentIntentModel.Id == intent.Id).first()
        if refreshed and refreshed.Status == "paid":
            refreshed_user = db.query(UserModel).filter(UserModel.Id == intent.UserId).first()
            refreshed_expiry = _utc_iso(refreshed_user.PlanExpiresAt if refreshed_user else None)
            return {
                "status": "paid",
                "plan": intent.PlanKey,
                "planName": PLAN_METADATA[intent.PlanKey]["name"],
                "expiresAt": refreshed_expiry,
            }
        return {"status": "pending", "plan": intent.PlanKey}

    user.Plan = intent.PlanKey
    user.PlanName = PLAN_METADATA[intent.PlanKey]["name"]
    user.VoterQuota = PLAN_METADATA[intent.PlanKey]["voters"]
    user.PollsQuota = PLAN_METADATA[intent.PlanKey]["polls"]
    user.PlanExpiresAt = billing_starts + timedelta(days=BILLING_DAYS)
    db.commit()
    return {
        "status": "paid",
        "plan": intent.PlanKey,
        "planName": user.PlanName,
        "expiresAt": _utc_iso(user.PlanExpiresAt),
    }


def verify_customer_payment(db: Session, user_id: str, tx_ref: str, transaction_id: str | None) -> dict:
    intent = (
        db.query(PaymentIntentModel)
        .filter(PaymentIntentModel.TxRef == tx_ref, PaymentIntentModel.UserId == user_id)
        .first()
    )
    if not intent:
        raise HTTPException(status_code=404, detail="Payment reference was not found for this account.")
    if intent.Status == "paid":
        user = db.query(UserModel).filter(UserModel.Id == user_id).first()
        expiry = _utc_iso(user.PlanExpiresAt if user else None)
        return {
            "status": "paid",
            "plan": intent.PlanKey,
            "planName": PLAN_METADATA[intent.PlanKey]["name"],
            "expiresAt": expiry,
        }
    if not transaction_id:
        return {"status": "failed" if intent.Status in {"failed", "rejected"} else "pending", "plan": intent.PlanKey}
    provider = _verify_provider_transaction(transaction_id)
    if provider.get("status") != "success" or not isinstance(provider.get("data"), dict):
        raise HTTPException(status_code=503, detail="Payment verification is temporarily unavailable.")
    data = provider["data"]
    if str(data.get("id") or "") != transaction_id:
        raise HTTPException(status_code=409, detail="Payment transaction could not be verified.")
    return _mark_verified_payment(db, intent, data)


def process_flutterwave_webhook(db: Session, header_hash: str | None, event: dict) -> dict:
    expected = settings.FLW_SECRET_HASH.strip()
    if not expected or not settings.FLW_SECRET_KEY.strip():
        raise HTTPException(status_code=503, detail="Payment webhook is not configured.")
    if not header_hash or not hmac.compare_digest(header_hash.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid payment webhook signature.")

    kind = str(event.get("type") or event.get("event") or "").lower()
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    if kind not in {"charge.completed", "charge.completed.v2"}:
        return {"received": True}
    tx_ref = str(data.get("tx_ref") or "")
    transaction_id = str(data.get("id") or "")
    if not tx_ref.startswith("icapsq_") or not transaction_id.isdigit():
        return {"received": True}
    intent = db.query(PaymentIntentModel).filter(PaymentIntentModel.TxRef == tx_ref).first()
    if not intent or intent.Status == "paid":
        return {"received": True}

    provider = _verify_provider_transaction(transaction_id)
    if provider.get("status") != "success" or not isinstance(provider.get("data"), dict):
        raise HTTPException(status_code=503, detail="Payment verification is temporarily unavailable.")
    verified_data = provider["data"]
    if str(verified_data.get("id") or "") != transaction_id:
        raise HTTPException(status_code=409, detail="Payment transaction could not be verified.")
    _mark_verified_payment(db, intent, verified_data)
    return {"received": True}
