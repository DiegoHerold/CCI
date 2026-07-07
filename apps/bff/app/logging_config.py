import logging
from contextvars import ContextVar
from datetime import datetime, timezone

from pythonjsonlogger.json import JsonFormatter

from app.config import Settings


correlation_id_context: ContextVar[str] = ContextVar(
    "correlation_id",
    default="system",
)


class CCIJsonFormatter(JsonFormatter):
    def __init__(self, settings: Settings) -> None:
        super().__init__("%(message)s")
        self.settings = settings

    def add_fields(self, log_record, record, message_dict) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )
        log_record["level"] = record.levelname
        log_record["service"] = self.settings.service_name
        log_record["env"] = self.settings.app_env
        log_record.setdefault("correlation_id", correlation_id_context.get())
        log_record["message"] = record.getMessage()


def configure_logging(settings: Settings) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(CCIJsonFormatter(settings))

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())

    for logger_name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.setLevel(settings.log_level.upper())

    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers.clear()
    access_logger.propagate = False
    access_logger.disabled = True
