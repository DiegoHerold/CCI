import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger(__name__)


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "system")


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
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


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    return _error_response(request, exc.status_code, "HTTP_ERROR", str(exc.detail))


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return _error_response(
        request,
        422,
        "VALIDATION_ERROR",
        "Request validation failed",
    )


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    correlation_id = _correlation_id(request)
    logger.exception(
        "unexpected error",
        extra={"correlation_id": correlation_id},
    )
    return _error_response(
        request,
        500,
        "INTERNAL_ERROR",
        "Unexpected error",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)
