"""
CareVoice AI Hospital Platform - Custom Exceptions & Handlers.

Defines domain-specific exceptions and registers FastAPI exception handlers
for consistent JSON error responses.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str = "Resource", identifier: str | None = None) -> None:
        self.resource = resource
        self.identifier = identifier
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} with id '{identifier}' not found"
        self.detail = detail
        super().__init__(self.detail)


class ConflictError(Exception):
    """Raised when an operation conflicts with the current state (e.g., duplicate)."""

    def __init__(self, detail: str = "Resource already exists") -> None:
        self.detail = detail
        super().__init__(self.detail)


class AuthorizationError(Exception):
    """Raised when a user lacks permission to perform an action."""

    def __init__(self, detail: str = "You do not have permission to perform this action") -> None:
        self.detail = detail
        super().__init__(self.detail)


class ValidationError(Exception):
    """Raised for domain-level validation failures."""

    def __init__(self, detail: str = "Validation error", errors: list[dict] | None = None) -> None:
        self.detail = detail
        self.errors = errors or []
        super().__init__(self.detail)


class PaymentError(Exception):
    """Raised when a payment processing operation fails."""

    def __init__(self, detail: str = "Payment processing failed") -> None:
        self.detail = detail
        super().__init__(self.detail)


async def _not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError and return a 404 JSON response."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "detail": exc.detail,
        },
    )


async def _conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    """Handle ConflictError and return a 409 JSON response."""
    return JSONResponse(
        status_code=409,
        content={
            "error": "conflict",
            "detail": exc.detail,
        },
    )


async def _authorization_handler(_request: Request, exc: AuthorizationError) -> JSONResponse:
    """Handle AuthorizationError and return a 403 JSON response."""
    return JSONResponse(
        status_code=403,
        content={
            "error": "forbidden",
            "detail": exc.detail,
        },
    )


async def _validation_handler(_request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError and return a 422 JSON response."""
    content: dict = {
        "error": "validation_error",
        "detail": exc.detail,
    }
    if exc.errors:
        content["errors"] = exc.errors
    return JSONResponse(
        status_code=422,
        content=content,
    )


async def _payment_handler(_request: Request, exc: PaymentError) -> JSONResponse:
    """Handle PaymentError and return a 402 JSON response."""
    return JSONResponse(
        status_code=402,
        content={
            "error": "payment_error",
            "detail": exc.detail,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    app.add_exception_handler(NotFoundError, _not_found_handler)
    app.add_exception_handler(ConflictError, _conflict_handler)
    app.add_exception_handler(AuthorizationError, _authorization_handler)
    app.add_exception_handler(ValidationError, _validation_handler)
    app.add_exception_handler(PaymentError, _payment_handler)
