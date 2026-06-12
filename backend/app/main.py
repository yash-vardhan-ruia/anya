"""
CareVoice AI Hospital Platform - Main FastAPI Application.

Assembles routers, hooks up global exceptions, configures CORS and Structlog logging middlewares,
and exposes WebSocket/health check routes.
"""

import structlog
from fastapi import FastAPI
from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import configure_cors, RequestLoggingMiddleware
from app.api.v1.router import router as api_v1_router
from app.api.webhooks import razorpay, twilio
from app.voice import voice_router, ws_router

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

# 3. Global Exception Handling
register_exception_handlers(app)

# 4. Mount API Routes
app.include_router(api_v1_router, prefix="/api")

# 5. Mount Webhook Routers
app.include_router(razorpay.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(twilio.router, prefix="/webhooks", tags=["Webhooks"])

# 6. Mount Voice Assistants Routers (TwiML and WebSocket Bridges)
app.include_router(voice_router, prefix="/voice", tags=["Voice"])
app.include_router(ws_router)  # Handles WebSocket connection on root '/ws/voice/{call_sid}'


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
