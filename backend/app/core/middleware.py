"""
CareVoice AI Hospital Platform - Middleware Configuration.

Provides CORS configuration and request logging middleware.
"""

import time

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import settings

logger = structlog.get_logger(__name__)


def configure_cors(app: FastAPI) -> None:
    """Configure CORS middleware on the FastAPI application.

    Reads allowed origins from application settings and enables credentials,
    all methods, and all headers for cross-origin requests.

    Args:
        app: The FastAPI application instance.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every incoming HTTP request with structured logging.

    Captures the HTTP method, URL path, response status code, and processing
    duration for each request using structlog.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process a request, log its details, and return the response.

        Args:
            request: The incoming HTTP request.
            call_next: Callable to pass the request to the next middleware/handler.

        Returns:
            The HTTP response from the downstream handler.
        """
        start_time = time.perf_counter()
        response: Response | None = None

        try:
            response = await call_next(request)
            return response
        except Exception:
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            status_code = response.status_code if response else 500
            logger.info(
                "request_completed",
                method=request.method,
                path=str(request.url.path),
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
                client_ip=request.client.host if request.client else None,
            )
