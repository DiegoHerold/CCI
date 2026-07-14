from fastapi import FastAPI

from app.api.routes.annotation_routes import router as annotation_router
from app.api.routes.category_routes import router as category_router
from app.api.routes.extraction_rule_routes import router as extraction_rule_router
from app.api.routes.field_routes import router as field_router
from app.api.routes.health import router as health_router
from app.api.routes.signal_routes import router as signal_router
from app.api.routes.template_routes import router as template_router
from app.api.routes.version_routes import router as version_router
from app.config import get_settings
from app.errors import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware import CorrelationIdMiddleware, RequestLoggingMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)
    application = FastAPI(
        title="CCI Template Service",
        version="1.0.0",
        description="Categorias, templates, campos, anotações, regras técnicas e versionamento.",
    )
    application.include_router(health_router)
    application.include_router(category_router)
    application.include_router(template_router)
    application.include_router(field_router)
    application.include_router(signal_router)
    application.include_router(annotation_router)
    application.include_router(extraction_rule_router)
    application.include_router(version_router)
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(application)
    return application


app = create_app()
