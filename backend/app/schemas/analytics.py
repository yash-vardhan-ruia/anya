"""
CareVoice AI Hospital Platform - Analytics Schemas.

Pydantic models for reporting dashboard metrics and call sessions metrics.
"""

from pydantic import BaseModel, Field


class DepartmentMetrics(BaseModel):
    department_name: str
    appointment_count: int
    revenue: int


class DashboardStats(BaseModel):
    """Aggregate statistics for admin dashboard."""
    total_patients: int = Field(..., description="Total registered patients")
    total_doctors: int = Field(..., description="Total active doctors")
    total_appointments: int = Field(..., description="Total appointments scheduled")
    total_revenue_paise: int = Field(..., description="Total collected revenue in paise")
    appointments_by_status: dict[str, int] = Field(..., description="Appointment count categorized by status")
    payments_by_status: dict[str, int] = Field(..., description="Payment count categorized by status")


class CallAnalytics(BaseModel):
    """Analytics for Twilio call sessions and Anya conversation rates."""
    total_calls: int = Field(..., description="Total calls handled by Anya")
    completed_calls: int = Field(..., description="Calls completed successfully")
    failed_calls: int = Field(..., description="Calls that failed or were abandoned")
    average_duration_seconds: float = Field(..., description="Average duration of the call sessions")
    conversion_rate: float = Field(..., description="Percentage of calls resulting in confirmed bookings")


class AnalyticsResponse(BaseModel):
    """Full reporting analytics response."""
    stats: DashboardStats
    call_analytics: CallAnalytics
    department_metrics: list[DepartmentMetrics] = Field(default_factory=list)
    monthly_revenue: list[dict[str, str | int]] = Field(default_factory=list, description="Monthly revenue time-series data")


class FrontendDashboardStats(BaseModel):
    totalCalls: int
    totalCallsDelta: float
    activeCalls: int
    activeCallsDelta: float
    appointmentsToday: int
    appointmentsTodayDelta: float
    avgHandleTime: str
    avgHandleTimeDelta: float
    satisfactionScore: float
    satisfactionScoreDelta: float
    totalPatients: int
    totalPatientsDelta: float


class SystemHealthItem(BaseModel):
    name: str
    status: str
    uptime: float
    responseTime: float


class RecentInteraction(BaseModel):
    id: str
    patientName: str
    type: str
    channel: str
    status: str
    duration: str
    sentiment: str
    timestamp: str
    aiConfidence: float


class DoctorUtilization(BaseModel):
    id: str
    name: str
    specialty: str
    avatar: str | None = None
    utilization: float
    appointmentsToday: int
    totalAppointments: int
    status: str


class CallVolumeHour(BaseModel):
    hour: str
    count: int


class CallVolumeDay(BaseModel):
    day: str
    count: int


class CallVolumeType(BaseModel):
    type: str
    count: int


class CallMetrics(BaseModel):
    totalCalls: int
    avgDuration: float
    peakHour: str
    resolutionRate: float
    callsByHour: list[CallVolumeHour]
    callsByDay: list[CallVolumeDay]
    callsByType: list[CallVolumeType]


class DeptAppointmentCount(BaseModel):
    department: str
    count: int


class TypeAppointmentCount(BaseModel):
    type: str
    count: int


class DateAppointmentCount(BaseModel):
    date: str
    count: int


class AppointmentMetrics(BaseModel):
    totalScheduled: int
    completed: int
    cancelled: int
    noShow: int
    byDepartment: list[DeptAppointmentCount]
    byType: list[TypeAppointmentCount]
    trend: list[DateAppointmentCount]


class DeptRevenueAmount(BaseModel):
    department: str
    amount: float


class DateRevenueAmount(BaseModel):
    date: str
    amount: float


class MethodRevenueAmount(BaseModel):
    method: str
    amount: float


class RevenueMetrics(BaseModel):
    totalRevenue: float
    avgPerPatient: float
    outstandingAmount: float
    collectionRate: float
    byDepartment: list[DeptRevenueAmount]
    trend: list[DateRevenueAmount]
    byPaymentMethod: list[MethodRevenueAmount]


class IntentCount(BaseModel):
    intent: str
    count: int


class SentimentTrendItem(BaseModel):
    date: str
    positive: int
    neutral: int
    negative: int


class AIMetrics(BaseModel):
    totalInteractions: int
    avgConfidence: float
    escalationRate: float
    satisfactionScore: float
    intentDistribution: list[IntentCount]
    sentimentTrend: list[SentimentTrendItem]


class FullAnalyticsResponse(BaseModel):
    callMetrics: CallMetrics
    appointmentMetrics: AppointmentMetrics
    revenueMetrics: RevenueMetrics
    aiMetrics: AIMetrics

