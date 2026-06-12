"""
Razorpay webhook handler - verifies signatures and dispatches payment events.
"""

from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/razorpay",
    status_code=status.HTTP_200_OK,
    summary="Handle Razorpay webhook",
)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Handle incoming Razorpay webhook events.

    Verifies the webhook signature using the shared secret, then dispatches
    the event payload to the payment service for processing.
    """
    body = await request.body()

    expected_signature = hmac.new(
        key=settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, x_razorpay_signature):
        logger.warning("Razorpay webhook signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    payload = await request.json()
    event_type = payload.get("event", "unknown")

    logger.info("Received Razorpay webhook event: %s", event_type)

    await PaymentService.handle_webhook_event(db=db, event=payload)

    return {"status": "ok"}
