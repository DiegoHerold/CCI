from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.clients import router as clients_router
from app.api.routes.executions import router as executions_router
from app.api.routes.health import router as health_router
from app.api.routes.logs import router as logs_router
from app.api.routes.platform import router as platform_router
from app.config import get_settings
from app.errors import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware import CorrelationIdMiddleware, RequestLoggingMiddleware


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    application = FastAPI(
        title="CCI BFF",
        version="0.1.0",
        description="Porta de entrada da CCI para a futura aplicação web.",
    )
    application.include_router(health_router)
    application.include_router(platform_router)
    application.include_router(auth_router)
    application.include_router(clients_router)
    application.include_router(executions_router)
    application.include_router(logs_router)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(application)
    return application


app = create_app()
