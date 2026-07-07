import logging
import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.logging_config import correlation_id_context


logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-Id") or str(uuid4())
        request.state.correlation_id = correlation_id
        token = correlation_id_context.set(correlation_id)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-Id"] = correlation_id
            return response
        finally:
            correlation_id_context.reset(token)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started_at = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers.setdefault("Cache-Control", "no-store")
            return response
        finally:
            logger.info(
                "request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round(
                        (time.perf_counter() - started_at) * 1000, 2
                    ),
                },
            )

