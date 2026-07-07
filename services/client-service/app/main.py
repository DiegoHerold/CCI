from fastapi import FastAPI

from app.api.routes.clients import router as clients_router
from app.api.routes.context import router as context_router
from app.api.routes.health import router as health_router
from app.config import get_settings
from app.errors import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware import CorrelationIdMiddleware, RequestLoggingMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    application = FastAPI(
        title="CCI Client Service",
        version="1.0.0",
        description="Clients, competencies, client access and operational context.",
    )
    application.include_router(health_router)
    application.include_router(context_router)
    application.include_router(clients_router)
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(application)
    return application


app = create_app()
