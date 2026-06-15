"""
CareVoice AI Hospital Platform - Main FastAPI Application.

Assembles routers, hooks up global exceptions, configures CORS and Structlog logging middlewares,
and exposes WebSocket/health check routes.
"""

import structlog
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import configure_cors, RequestLoggingMiddleware
from app.api.v1.router import router as api_v1_router
from app.api.webhooks import razorpay
from app.api.v1.live_voice import router as live_voice_ws_router

logger = structlog.get_logger(__name__)

# Initialize FastAPI with metadata
app = FastAPI(
    title=settings.APP_NAME,
    description="State-of-the-art AI Hospital voice booking system powered by Anya.",
    version="1.0.0",
    debug=settings.DEBUG,
)

# 1. CORS Configuration
configure_cors(app)

# 2. Structured Request Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# 3. Prometheus Metrics (exposes /metrics for Prometheus scraping)
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

# 4. Global Exception Handling
register_exception_handlers(app)

# 5. Mount API Routes
app.include_router(api_v1_router, prefix="/api")

# 6. Mount Webhook Routers
app.include_router(razorpay.router, prefix="/webhooks", tags=["Webhooks"])

# 7. Mount Voice Assistants Routers (WebSocket Bridges)
app.include_router(live_voice_ws_router)  # Handles WebSocket connection on root '/ws/live-voice/{session_id}'


@app.get("/health", status_code=200, tags=["Health"])
async def health_check() -> dict:
    """Service health verification endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "debug_mode": settings.DEBUG,
    }


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("CareVoice AI Hospital Platform starting up...", base_url=settings.BASE_URL)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("CareVoice AI Hospital Platform shutting down...")
