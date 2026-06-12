"""
Analytics endpoints - dashboard stats, appointment breakdowns, revenue, and call analytics.
"""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_admin
from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.analytics import (
    AnalyticsResponse,
    CallAnalytics,
    DashboardStats,
    FrontendDashboardStats,
    SystemHealthItem,
    RecentInteraction,
    DoctorUtilization,
    FullAnalyticsResponse,
)
from app.services import AnalyticsService

router = APIRouter()


@router.get(
    "",
    response_model=FullAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full detailed operational analytics",
)
async def get_full_detailed_analytics(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> FullAnalyticsResponse:
    """Retrieve full dynamic operational analytics matching frontend requirements."""
    return await AnalyticsService.get_full_analytics(db=db)



@router.get(
    "/dashboard",
    response_model=DashboardStats,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard statistics",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> DashboardStats:
    """Retrieve high-level dashboard statistics including patient, appointment, and revenue summaries."""
    analytics = await AnalyticsService.get_analytics(db=db)
    return analytics.stats


@router.get(
    "/appointments",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get appointments by department",
)
async def get_appointments_by_department(
    date_from: datetime.date | None = Query(None, description="Start date for analysis"),
    date_to: datetime.date | None = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AnalyticsResponse:
    """Get appointment distribution across departments for a given date range."""
    return await AnalyticsService.get_analytics(db=db)


@router.get(
    "/revenue",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get revenue by period",
)
async def get_revenue_by_period(
    period: str = Query(
        "monthly",
        description="Aggregation period: daily, weekly, monthly, yearly",
    ),
    date_from: datetime.date | None = Query(None, description="Start date for analysis"),
    date_to: datetime.date | None = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> AnalyticsResponse:
    """Get revenue data aggregated by the specified period within a date range."""
    return await AnalyticsService.get_analytics(db=db)


@router.get(
    "/calls",
    response_model=CallAnalytics,
    status_code=status.HTTP_200_OK,
    summary="Get call analytics",
)
async def get_call_analytics(
    date_from: datetime.date | None = Query(None, description="Start date for analysis"),
    date_to: datetime.date | None = Query(None, description="End date for analysis"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> CallAnalytics:
    """Get AI voice call analytics including volume, duration, and intent breakdowns."""
    analytics = await AnalyticsService.get_analytics(db=db)
    return analytics.call_analytics


@router.get(
    "/stats",
    response_model=FrontendDashboardStats,
    status_code=status.HTTP_200_OK,
    summary="Get bento dashboard stats",
)
async def get_bento_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> FrontendDashboardStats:
    """Retrieve real-time aggregated dashboard stats."""
    return await AnalyticsService.get_dashboard_stats(db=db)


@router.get(
    "/system-health",
    response_model=list[SystemHealthItem],
    status_code=status.HTTP_200_OK,
    summary="Get system components health status",
)
async def get_system_health(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> list[SystemHealthItem]:
    """Retrieve operational status for external APIs and databases."""
    return await AnalyticsService.get_system_health(db=db)


@router.get(
    "/recent-interactions",
    response_model=list[RecentInteraction],
    status_code=status.HTTP_200_OK,
    summary="Get recent voice triage activities",
)
async def get_recent_interactions(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> list[RecentInteraction]:
    """Retrieve recent active and completed call interactions."""
    return await AnalyticsService.get_recent_interactions(db=db)


@router.get(
    "/doctor-utilization",
    response_model=list[DoctorUtilization],
    status_code=status.HTTP_200_OK,
    summary="Get doctor utilization percentage statistics",
)
async def get_doctor_utilization(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
) -> list[DoctorUtilization]:
    """Retrieve active clinician utilization data."""
    return await AnalyticsService.get_doctor_utilization(db=db)
