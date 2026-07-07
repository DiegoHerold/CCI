import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class InvalidTokenError(ServiceError):
    def __init__(self) -> None:
        super().__init__(401, "INVALID_TOKEN", "Invalid or expired access token")


class ForbiddenError(ServiceError):
    def __init__(self, message: str = "Insufficient permission") -> None:
        super().__init__(403, "FORBIDDEN", message)


class ClientAccessDeniedError(ServiceError):
    def __init__(self) -> None:
        super().__init__(
            403,
            "CLIENT_ACCESS_DENIED",
            "Você não possui acesso a este cliente.",
        )


class NotFoundError(ServiceError):
    def __init__(self, resource: str) -> None:
        super().__init__(404, "NOT_FOUND", f"{resource} not found")


class ConflictError(ServiceError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(409, code, message)


class BusinessRuleError(ServiceError):
    def __init__(self, code: str, message: str, status_code: int = 422) -> None:
        super().__init__(status_code, code, message)


class UpstreamUnavailableError(ServiceError):
    def __init__(self) -> None:
        super().__init__(503, "IDENTITY_SERVICE_UNAVAILABLE", "Identity Service unavailable")


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "system")


def _response(
    request: Request, status_code: int, code: str, message: str
) -> JSONResponse:
    correlation_id = _correlation_id(request)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "correlation_id": correlation_id,
            }
        },
        headers={"X-Correlation-Id": correlation_id},
    )


async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    return _response(request, exc.status_code, exc.code, exc.message)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _response(request, 422, "VALIDATION_ERROR", "Request validation failed")


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unexpected error")
    return _response(request, 500, "INTERNAL_ERROR", "Unexpected error")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ServiceError, service_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
