# Copyright notice.

import traceback
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from libs.core.error_handling import (
    ConfigurationError,
    ErrorSeverity,
    NetworkError,
    SessionError,
    ValidationError,
    YesmanError,
)
from libs.core.error_handling import PermissionError as YesmanPermissionError
from libs.core.error_handling import TimeoutError as YesmanTimeoutError


def error_to_status_code(error: YesmanError) -> int:
    """Map YesmanError to HTTP status code.

    Returns:
        Dict containing status information.
    """
    # Map by error type
    if isinstance(error, ValidationError):
        return status.HTTP_400_BAD_REQUEST
    if isinstance(error, ConfigurationError):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(error, SessionError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(error, YesmanPermissionError):
        return status.HTTP_403_FORBIDDEN
    if isinstance(error, NetworkError):
        return status.HTTP_502_BAD_GATEWAY
    if isinstance(error, YesmanTimeoutError):
        return status.HTTP_504_GATEWAY_TIMEOUT

    # Map by severity
    severity_map = {
        ErrorSeverity.LOW: status.HTTP_400_BAD_REQUEST,
        ErrorSeverity.MEDIUM: status.HTTP_400_BAD_REQUEST,
        ErrorSeverity.HIGH: status.HTTP_500_INTERNAL_SERVER_ERROR,
        ErrorSeverity.CRITICAL: status.HTTP_500_INTERNAL_SERVER_ERROR,
    }

    return severity_map.get(error.severity, status.HTTP_500_INTERNAL_SERVER_ERROR)


async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global error handler for all exceptions."""
    # Generate request ID if not present
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Handle YesmanError
    if isinstance(exc, YesmanError):
        error_dict = exc.to_dict()
        error_dict["request_id"] = request_id

        return JSONResponse(
            status_code=error_to_status_code(exc),
            content={"error": error_dict},
        )

    # Handle Starlette HTTP exceptions
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "category": "http",
                    "severity": "medium",
                    "request_id": request_id,
                }
            },
        )

    # Handle FastAPI validation errors
    if isinstance(exc, RequestValidationError):
        errors = []
        for error in exc.errors():
            field = ".".join(str(x) for x in error["loc"])
            errors.append({"field": field, "message": error["msg"], "type": error["type"]})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "category": "validation",
                    "severity": "low",
                    "recovery_hint": "Check the request format and required fields",
                    "context": {"validation_errors": errors},
                    "request_id": request_id,
                }
            },
        )

    # Handle unexpected errors
    # Log the full traceback for debugging
    traceback.format_exc()

    # Return generic error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "category": "system",
                "severity": "high",
                "recovery_hint": ("Please try again later or contact support if the problem persists"),
                "request_id": request_id,
            }
        },
    )


async def add_request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Middleware to add request ID to all requests."""
    # Generate or extract request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    # Process request
    response = await call_next(request)

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


def create_error_response(
    code: str,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    category: str = "application",
    severity: str = "medium",
    recovery_hint: str | None = None,
    context: dict[str, object] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Helper function to create standardized error responses.

    Returns:
        JSON response object the created item.
    """
    error_data: dict[str, object] = {
        "code": code,
        "message": message,
        "category": category,
        "severity": severity,
    }

    if recovery_hint:
        error_data["recovery_hint"] = recovery_hint

    if context:
        error_data["context"] = context

    if request_id:
        error_data["request_id"] = request_id

    return JSONResponse(status_code=status_code, content={"error": error_data})
