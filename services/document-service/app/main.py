from fastapi import FastAPI

from app.api.routes.document_routes import router as document_router
from app.api.routes.health import router as health_router
from app.api.routes.preview_routes import router as preview_router
from app.api.routes.status_routes import router as status_router
from app.api.routes.upload_routes import router as upload_router
from app.config import get_settings
from app.errors import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware import CorrelationIdMiddleware, RequestLoggingMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    application = FastAPI(
        title="CCI Document Service",
        version="1.0.0",
        description="Uploads, original document metadata, MinIO storage and duplicate detection.",
    )
    application.include_router(health_router)
    application.include_router(upload_router)
    application.include_router(status_router)
    application.include_router(preview_router)
    application.include_router(document_router)
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(application)
    return application


app = create_app()
