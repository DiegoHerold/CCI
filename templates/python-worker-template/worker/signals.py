import signal
from threading import Event
from types import FrameType


shutdown_event = Event()


def request_shutdown(
    signum: int,
    frame: FrameType | None,
) -> None:
    del signum, frame
    shutdown_event.set()


def register_signal_handlers() -> None:
    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
