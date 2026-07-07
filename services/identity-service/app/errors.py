import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers or {}


class InvalidCredentialsError(ServiceError):
    def __init__(self) -> None:
        super().__init__(
            401,
            "INVALID_CREDENTIALS",
            "Invalid email or password",
            {"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenError(ServiceError):
    def __init__(self) -> None:
        super().__init__(
            401,
            "INVALID_TOKEN",
            "Invalid or expired access token",
            {"WWW-Authenticate": "Bearer"},
        )


class InvalidRefreshTokenError(ServiceError):
    def __init__(self) -> None:
        super().__init__(401, "INVALID_REFRESH_TOKEN", "Invalid refresh token")


class RateLimitExceededError(ServiceError):
    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            429,
            "RATE_LIMIT_EXCEEDED",
            "Too many login attempts. Try again later.",
            {"Retry-After": str(retry_after)},
        )


class PasswordPolicyError(ServiceError):
    def __init__(self) -> None:
        super().__init__(
            422,
            "VALIDATION_ERROR",
            "The password does not meet the minimum security requirements.",
        )


class ForbiddenError(ServiceError):
    def __init__(self, message: str = "Insufficient permission") -> None:
        super().__init__(403, "FORBIDDEN", message)


class NotFoundError(ServiceError):
    def __init__(self, resource: str = "User") -> None:
        super().__init__(404, "NOT_FOUND", f"{resource} not found")


class ConflictError(ServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(409, "CONFLICT", message)


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "system")


def _response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    correlation_id = _correlation_id(request)
    response_headers = {"X-Correlation-Id": correlation_id, **(headers or {})}
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "correlation_id": correlation_id,
            }
        },
        headers=response_headers,
    )


async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    return _response(
        request, exc.status_code, exc.code, exc.message, exc.headers
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _response(
        request, 422, "VALIDATION_ERROR", "Request validation failed"
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unexpected error",
        extra={"correlation_id": _correlation_id(request)},
    )
    return _response(request, 500, "INTERNAL_ERROR", "Unexpected error")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ServiceError, service_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
