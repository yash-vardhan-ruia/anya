"""
Billing endpoints - invoice creation and retrieval.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin
from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.billing import (
    InvoiceDetailResponse,
    InvoiceListResponse,
    InvoiceResponse,
)
from app.services import BillingService

router = APIRouter()


@router.post(
    "/invoices",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invoice",
)
async def create_invoice(
    appointment_id: UUID = Query(..., description="Appointment ID to invoice"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> InvoiceResponse:
    """Create a new invoice for a completed appointment."""
    try:
        return await BillingService.create_invoice(
            db=db, appointment_id=appointment_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/invoices",
    response_model=InvoiceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List invoices",
)
async def list_invoices(
    patient_id: UUID | None = Query(None, description="Filter by patient ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> InvoiceListResponse:
    """List invoices with optional patient filter and pagination."""
    skip = (page - 1) * page_size
    total, items = await BillingService.list_invoices(
        db=db, patient_id=patient_id, skip=skip, limit=page_size
    )
    return InvoiceListResponse(total=total, items=items)


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get invoice by ID",
)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> InvoiceDetailResponse:
    """Retrieve a single invoice with full detail by its unique ID."""
    invoice = await BillingService.get_invoice(db=db, invoice_id=invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return invoice
