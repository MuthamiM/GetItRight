import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from backend.api.core.database import get_db
from backend.api.features.payments.schemas import CheckoutRequest, VerifyPaymentRequest
from backend.api.features.payments.service import (
    initiate_checkout,
    process_flutterwave_webhook,
    public_plan_catalog,
    verify_customer_payment,
)
from backend.api.middleware.auth_middleware import get_current_user_token

router = APIRouter(prefix="/payments", tags=["Plan Payments"])


@router.get("/plans")
def get_public_plan_catalog():
    return public_plan_catalog()


@router.post("/checkout")
def create_plan_checkout(
    payload: CheckoutRequest,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    return initiate_checkout(db, current_user["sub"], payload.plan)


@router.post("/verify")
def verify_plan_payment(
    payload: VerifyPaymentRequest,
    current_user: dict = Depends(get_current_user_token),
    db: Session = Depends(get_db),
):
    return verify_customer_payment(db, current_user["sub"], payload.tx_ref, payload.transaction_id)


@router.post("/webhook/flutterwave")
async def flutterwave_webhook(request: Request, db: Session = Depends(get_db)):
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > 64 * 1024:
        raise HTTPException(status_code=413, detail="Webhook payload is too large.")
    body_chunks = bytearray()
    async for chunk in request.stream():
        body_chunks.extend(chunk)
        if len(body_chunks) > 64 * 1024:
            raise HTTPException(status_code=413, detail="Webhook payload is too large.")
    try:
        event = json.loads(body_chunks)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook payload.") from None
    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="Invalid webhook payload.")
    return await run_in_threadpool(
        process_flutterwave_webhook,
        db,
        request.headers.get("verif-hash"),
        event,
    )
