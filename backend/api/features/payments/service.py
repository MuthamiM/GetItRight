import hmac
import logging
import re
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
IPAY_CHECKOUT_URL = "https://payments.ipayafrica.com/v3/ke"
IPAY_SEARCH_URL = "https://apis.ipayafrica.com/payments/v2/transaction/search"
IPAY_IPN_URL = "https://www.ipayafrica.com/ipn/"
BILLING_DAYS = 30
CHECKOUT_MINUTES = 30
# Keep payment amounts aligned with the plan prices shown during signup.
PLAN_PRICES_KES = {"pro": 499, "org": 899, "election": 1399}


def _utc_iso(value: datetime | None) -> str | None:
    if not value:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def payments_configured() -> bool:
    provider = settings.PAYMENT_PROVIDER.strip().lower()
    if provider == "ipay":
        live_mode_ready = settings.ENVIRONMENT.lower() != "production" or settings.IPAY_LIVE == "1"
        return bool(settings.IPAY_VENDOR_ID.strip() and settings.IPAY_HASH_KEY.strip() and live_mode_ready)
    if provider == "flutterwave":
        return bool(settings.FLW_SECRET_KEY.strip() and settings.FLW_SECRET_HASH.strip())
    return False


def public_plan_catalog() -> dict:
    return {
        "currency": "KES",
        "billingDays": BILLING_DAYS,
        "checkoutEnabled": payments_configured(),
        "provider": settings.PAYMENT_PROVIDER.strip().lower(),
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


def _ipay_fields(intent: PaymentIntentModel, user: UserModel) -> dict:
    vendor = settings.IPAY_VENDOR_ID.strip().lower()
    hash_key = settings.IPAY_HASH_KEY.strip()
    oid = intent.TxRef
    if not vendor or not hash_key or not re.fullmatch(r"[a-z0-9]{1,12}", vendor):
        raise HTTPException(status_code=503, detail="iPay checkout is not configured correctly.")

    phone = re.sub(r"\D", "", str(user.PhoneNumber or ""))
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith(("7", "1")):
        phone = "254" + phone
    if not re.fullmatch(r"254[17]\d{8}", phone):
        raise HTTPException(status_code=422, detail="Add a valid Kenyan mobile number to your profile before paying.")

    email = (user.Email or "").strip().lower()
    if len(email) > 30 or "@" not in email:
        raise HTTPException(status_code=422, detail="Your account email must be valid and no longer than 30 characters for checkout.")
    if not re.fullmatch(r"IC[A-F0-9]{24}", oid):
        raise HTTPException(status_code=503, detail="The payment reference is invalid.")

    fields = {
        "live": settings.IPAY_LIVE.strip(),
        "oid": oid,
        "inv": oid[:15],
        "ttl": str(intent.Amount),
        "tel": phone,
        "eml": email,
        "vid": vendor,
        "curr": "KES",
        "p1": intent.PlanKey,
        "p2": "",
        "p3": "",
        "p4": "",
        "cbk": f"{settings.APP_PUBLIC_URL.rstrip('/')}/{settings.API_PREFIX.strip('/')}/payments/ipay/callback",
        "cst": "1",
        "crl": "0",
    }
    if fields["live"] not in {"0", "1"}:
        raise HTTPException(status_code=503, detail="iPay checkout mode is not configured correctly.")
    if settings.ENVIRONMENT.lower() == "production" and fields["live"] != "1":
        raise HTTPException(status_code=503, detail="iPay live checkout has not been enabled on this server.")
    signed = "".join(fields[key] for key in (
        "live", "oid", "inv", "ttl", "tel", "eml", "vid", "curr",
        "p1", "p2", "p3", "p4", "cbk", "cst", "crl",
    ))
    fields["hsh"] = hmac.new(hash_key.encode("utf-8"), signed.encode("utf-8"), "sha1").hexdigest()
    return fields


def _ipay_checkout_response(intent: PaymentIntentModel, user: UserModel) -> dict:
    return {
        "provider": "ipay",
        "checkout_url": IPAY_CHECKOUT_URL,
        "checkout_fields": _ipay_fields(intent, user),
        "tx_ref": intent.TxRef,
        "amount": intent.Amount,
        "currency": intent.Currency,
        "plan": intent.PlanKey,
        "status": intent.Status,
    }


def _create_ipay_checkout(db: Session, user: UserModel, plan_key: str) -> dict:
    now = datetime.now(timezone.utc)
    existing = (
        db.query(PaymentIntentModel)
        .filter(
            PaymentIntentModel.UserId == user.Id,
            PaymentIntentModel.PlanKey == plan_key,
            PaymentIntentModel.Status == "pending",
            PaymentIntentModel.ExpiresAt > now,
            PaymentIntentModel.CheckoutUrl == IPAY_CHECKOUT_URL,
        )
        .order_by(PaymentIntentModel.CreatedAt.desc())
        .first()
    )
    if existing:
        return _ipay_checkout_response(existing, user)

    intent = PaymentIntentModel(
        Id=str(uuid.uuid4()),
        UserId=user.Id,
        TxRef=f"IC{uuid.uuid4().hex[:24].upper()}",
        PlanKey=plan_key,
        Amount=PLAN_PRICES_KES[plan_key],
        Currency="KES",
        Status="pending",
        CheckoutUrl=IPAY_CHECKOUT_URL,
        CreatedAt=now,
        UpdatedAt=now,
        ExpiresAt=now + timedelta(minutes=CHECKOUT_MINUTES),
    )
    # Validate the payer's details before persisting a checkout intent.
    _ipay_fields(intent, user)
    db.add(intent)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not save an iPay plan payment intent")
        raise HTTPException(status_code=503, detail="Secure checkout could not be started.") from None
    return _ipay_checkout_response(intent, user)


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

    if settings.PAYMENT_PROVIDER.strip().lower() == "ipay":
        return _create_ipay_checkout(db, user, plan_key)

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
            "provider": "flutterwave",
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
        "provider": "flutterwave",
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


def _verify_ipay_transaction(oid: str) -> dict | None:
    vendor = settings.IPAY_VENDOR_ID.strip().lower()
    hash_key = settings.IPAY_HASH_KEY.strip()
    if not vendor or not hash_key:
        raise HTTPException(status_code=503, detail="iPay payment verification is not configured.")
    if not re.fullmatch(r"IC[A-F0-9]{24}", oid):
        raise HTTPException(status_code=422, detail="Payment reference is invalid.")

    request_hash = hmac.new(
        hash_key.encode("utf-8"), f"{oid}{vendor}".encode("utf-8"), "sha256"
    ).hexdigest()
    try:
        response = httpx.post(
            IPAY_SEARCH_URL,
            data={"vid": vendor, "oid": oid, "hash": request_hash},
            headers={"Accept": "application/json"},
            timeout=15.0,
        )
        response.raise_for_status()
        body = response.json()
    except Exception as exc:
        logger.warning("iPay transaction search failed (%s)", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail="Payment verification is temporarily unavailable. No plan change was made.",
        ) from None

    if not isinstance(body, dict):
        raise HTTPException(status_code=503, detail="iPay returned an invalid verification response.")
    if str(body.get("status")) != "1":
        return None
    data = body.get("data")
    if not isinstance(data, dict):
        raise HTTPException(status_code=503, detail="iPay returned an incomplete verification response.")
    if str(data.get("oid") or "") != oid or str(data.get("vid") or "").lower() != vendor:
        raise HTTPException(status_code=409, detail="Payment details could not be verified.")

    transaction_code = str(data.get("transaction_code") or "")
    first_name = str(data.get("firstname") or "")
    last_name = str(data.get("lastname") or "")
    paid_at = str(data.get("paid_at") or "")
    payment_mode = str(data.get("payment_mode") or "")
    session_id = str(data.get("session_id") or "")
    supplied_hash = str(body.get("hash") or "").lower()
    signed_response = "".join((oid, vendor, transaction_code, first_name, last_name, paid_at, payment_mode, session_id))
    expected_hash = hmac.new(
        hash_key.encode("utf-8"), signed_response.encode("utf-8"), "sha256"
    ).hexdigest()
    if not supplied_hash or not hmac.compare_digest(supplied_hash, expected_hash):
        logger.error("iPay transaction response signature mismatch for order %s", oid)
        raise HTTPException(status_code=409, detail="Payment details could not be verified.")

    return {
        "status": "successful",
        "tx_ref": oid,
        "currency": "KES",
        "amount": data.get("transaction_amount"),
        "id": transaction_code,
    }


def handle_ipay_callback(db: Session, query: dict) -> str | None:
    oid = str(query.get("id") or "")
    if not re.fullmatch(r"IC[A-F0-9]{24}", oid):
        return None
    intent = db.query(PaymentIntentModel).filter(PaymentIntentModel.TxRef == oid).first()
    if not intent:
        return None
    if intent.Status == "paid":
        return oid

    token_names = ("ivm", "qwh", "afd", "poi", "uyt", "ifd")
    tokens = {name: str(query.get(name) or "") for name in token_names}
    if not all(re.fullmatch(r"[A-Za-z0-9]{1,128}", value) for value in tokens.values()):
        return oid
    params = {"vendor": settings.IPAY_VENDOR_ID.strip().lower(), "id": oid, **tokens}
    if not params["vendor"]:
        return oid
    try:
        response = httpx.get(IPAY_IPN_URL, params=params, timeout=12.0)
        response.raise_for_status()
        ipn_status = response.text.strip()
    except Exception as exc:
        logger.warning("iPay callback IPN check failed (%s)", type(exc).__name__)
        return oid

    if ipn_status in {"aei7p7yrx4ae34", "cr5i3pgy9867e1"}:
        try:
            verified = _verify_ipay_transaction(oid)
            if verified:
                _mark_verified_payment(db, intent, verified)
        except HTTPException as exc:
            logger.warning("iPay callback could not complete transaction search (%s)", exc.status_code)
    elif ipn_status in {"fe2707etr5s4wq", "dtfi4p7yty45wq", "eq3i7p5yt7645e"}:
        intent.Status = "failed"
        intent.UpdatedAt = datetime.now(timezone.utc)
        db.commit()
    return oid


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
    if intent.Status in {"failed", "rejected"}:
        return {"status": "failed", "plan": intent.PlanKey}
    if intent.TxRef.startswith("IC"):
        provider_data = _verify_ipay_transaction(intent.TxRef)
        if not provider_data:
            return {"status": "pending", "plan": intent.PlanKey}
        return _mark_verified_payment(db, intent, provider_data)
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
