import logging

from worker.config import get_settings
from worker.logging_config import configure_logging
from worker.signals import register_signal_handlers, shutdown_event


logger = logging.getLogger(__name__)


def run_worker(poll_interval_seconds: float = 1.0) -> None:
    settings = get_settings()
    configure_logging(settings)
    register_signal_handlers()

    logger.info("worker started")
    try:
        while not shutdown_event.wait(poll_interval_seconds):
            pass
    finally:
        logger.info("worker stopped")


if __name__ == "__main__":
    run_worker()
