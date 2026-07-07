from contextvars import ContextVar
import logging
from sys import stdout

from pythonjsonlogger.json import JsonFormatter

from app.config import Settings


correlation_id_context: ContextVar[str] = ContextVar(
    "correlation_id", default="system"
)


class ContextFilter(logging.Filter):
    def __init__(self, service: str, env: str) -> None:
        super().__init__()
        self.service = service
        self.env = env

    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service
        record.env = self.env
        record.correlation_id = correlation_id_context.get()
        return True


def configure_logging(settings: Settings) -> None:
    handler = logging.StreamHandler(stdout)
    handler.setFormatter(
        JsonFormatter(
            "%(asctime)s %(levelname)s %(service)s %(env)s "
            "%(correlation_id)s %(message)s"
        )
    )
    handler.addFilter(ContextFilter(settings.service_name, settings.app_env))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())

