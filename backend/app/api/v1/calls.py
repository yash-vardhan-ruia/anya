"""
Call session endpoints - list, get, and active call count.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin
from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.call_session import CallSession

router = APIRouter()


@router.get(
    "/active",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get active calls count",
)
async def get_active_calls(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> dict:
    """Return the count of currently active call sessions."""
    result = await db.execute(
        select(func.count(CallSession.id)).where(
            CallSession.status == "in_progress"
        )
    )
    count = result.scalar() or 0
    return {"active_calls": count}


@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List call sessions",
)
async def list_calls(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> dict:
    """List call sessions with pagination."""
    offset = (page - 1) * page_size

    count_result = await db.execute(select(func.count(CallSession.id)))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(CallSession)
        .order_by(CallSession.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    calls = result.scalars().all()

    return {
        "items": [
            {
                "id": str(call.id),
                "callerId": str(call.patient_id) if call.patient_id else "",
                "callerName": call.patient.full_name if call.patient else "Guest Patient",
                "callerPhone": call.from_number,
                "agentId": "anya",
                "agentName": "Anya AI",
                "type": "inbound",
                "status": "completed" if call.status == "completed" else ("failed" if call.status == "failed" else "active"),
                "intent": "Hospital Triage & Booking",
                "duration": int((call.ended_at - call.started_at).total_seconds()) if (call.ended_at and call.started_at) else 0,
                "startedAt": call.started_at.isoformat() if call.started_at else (call.created_at.isoformat() if call.created_at else None),
                "endedAt": call.ended_at.isoformat() if call.ended_at else None,
                "sentiment": "positive" if "thank you" in (call.transcript or "").lower() else ("negative" if any(x in (call.transcript or "").lower() for x in ["worry", "pain", "fever", "hurt", "bad"]) else "neutral"),
                "aiConfidence": 0.95,
                "transcript": call.transcript or "",
                "department": "General Medicine",
                "resolution": "Appointment Booked" if "complete" in str(call.conversation_state).lower() else "Inquiry Resolved",
            }
            for call in calls
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get(
    "/{call_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get call session details",
)
async def get_call(
    call_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> dict:
    """Retrieve a single call session by its unique ID."""
    result = await db.execute(
        select(CallSession).where(CallSession.id == call_id)
    )
    call = result.scalar_one_or_none()

    if call is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(f"Call session {call_id} not found")

    return {
        "id": str(call.id),
        "callerId": str(call.patient_id) if call.patient_id else "",
        "callerName": call.patient.full_name if call.patient else "Guest Patient",
        "callerPhone": call.from_number,
        "agentId": "anya",
        "agentName": "Anya AI",
        "type": "inbound",
        "status": "completed" if call.status == "completed" else ("failed" if call.status == "failed" else "active"),
        "intent": "Hospital Triage & Booking",
        "duration": int((call.ended_at - call.started_at).total_seconds()) if (call.ended_at and call.started_at) else 0,
        "startedAt": call.started_at.isoformat() if call.started_at else (call.created_at.isoformat() if call.created_at else None),
        "endedAt": call.ended_at.isoformat() if call.ended_at else None,
        "sentiment": "positive" if "thank you" in (call.transcript or "").lower() else ("negative" if any(x in (call.transcript or "").lower() for x in ["worry", "pain", "fever", "hurt", "bad"]) else "neutral"),
        "aiConfidence": 0.95,
        "transcript": call.transcript or "",
        "recordingUrl": "",
        "department": "General Medicine",
        "resolution": "Appointment Booked" if "complete" in str(call.conversation_state).lower() else "Inquiry Resolved",
    }
