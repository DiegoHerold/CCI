import importlib
import signal

from worker.config import Settings
from worker.logging_config import configure_logging
from worker.signals import request_shutdown, shutdown_event


def test_configuration_loads() -> None:
    settings = Settings()

    assert settings.worker_name
    assert settings.app_env == "development"


def test_worker_name_is_read_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("WORKER_NAME", "test-worker")

    settings = Settings()

    assert settings.worker_name == "test-worker"


def test_logging_configuration_does_not_raise() -> None:
    configure_logging(Settings())


def test_main_module_imports() -> None:
    module = importlib.import_module("worker.main")

    assert callable(module.run_worker)


def test_shutdown_signal_sets_shutdown_flag() -> None:
    shutdown_event.clear()

    request_shutdown(signal.SIGTERM, None)

    assert shutdown_event.is_set()
    shutdown_event.clear()
