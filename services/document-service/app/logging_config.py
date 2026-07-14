import logging.config

from pythonjsonlogger import jsonlogger

from app.config import Settings


def configure_logging(settings: Settings) -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": jsonlogger.JsonFormatter,
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(service)s %(env)s",
                }
            },
            "filters": {
                "service_context": {
                    "()": ServiceContextFilter,
                    "service": settings.service_name,
                    "env": settings.app_env,
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "filters": ["service_context"],
                }
            },
            "root": {
                "level": settings.log_level,
                "handlers": ["console"],
            },
        }
    )


class ServiceContextFilter(logging.Filter):
    def __init__(self, service: str, env: str) -> None:
        super().__init__()
        self.service = service
        self.env = env

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service
        record.env = self.env
        return True
