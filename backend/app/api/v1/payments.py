"""
Payment endpoints - Razorpay order creation, verification, and payment listing.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import get_current_admin
from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.payment import (
    PaymentCreateRequest,
    PaymentListResponse,
    PaymentOrderResponse,
    PaymentResponse,
    PaymentVerifyRequest,
)
from app.services import PaymentService

router = APIRouter()


@router.post(
    "/orders",
    response_model=PaymentOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Razorpay order",
)
async def create_payment_order(
    payload: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> PaymentOrderResponse:
    """Create a Razorpay payment order for a given invoice."""
    try:
        payment = await PaymentService.create_payment_order(
            db=db, invoice_id=payload.invoice_id
        )
        return PaymentOrderResponse(
            payment_id=payment.id,
            invoice_id=payment.invoice_id,
            amount=payment.amount,
            razorpay_order_id=payment.razorpay_order_id,
            razorpay_key_id=settings.RAZORPAY_KEY_ID,
            status=payment.status,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/verify",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify payment",
)
async def verify_payment(
    payload: PaymentVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> PaymentResponse:
    """Verify a Razorpay payment signature and mark it as completed."""
    success = await PaymentService.verify_payment_signature(
        db=db,
        razorpay_order_id=payload.razorpay_order_id,
        razorpay_payment_id=payload.razorpay_payment_id,
        razorpay_signature=payload.razorpay_signature,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment signature verification failed",
        )
    payment = await PaymentService.get_payment_by_order_id(
        db=db, order_id=payload.razorpay_order_id
    )
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found",
        )
    return payment


@router.get(
    "/",
    response_model=PaymentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List payments",
)
async def list_payments(
    patient_id: UUID | None = Query(None, description="Filter by patient ID"),
    payment_status: str | None = Query(
        None, alias="status", description="Filter by payment status"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> PaymentListResponse:
    """List payments with optional filters for patient and status, with pagination."""
    skip = (page - 1) * page_size
    total, items = await PaymentService.list_payments(
        db=db, skip=skip, limit=page_size, status=payment_status, patient_id=patient_id
    )
    return PaymentListResponse(total=total, items=items)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get payment by ID",
)
async def get_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> PaymentResponse:
    """Retrieve a single payment by its unique ID."""
    payment = await PaymentService.get_payment(db=db, payment_id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )
    return payment
