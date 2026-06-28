"""
Logging for the Hermes Agent processor pipeline.

_SmartHandler routes output to a per-thread capture buffer when one is active
(used by --parallel) and falls back to sys.stdout otherwise.

Usage:
    from processor.log import get_logger, setup
    setup()
    logger = get_logger(__name__)
    logger.info("[SKIP] file.md")
"""

import io
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

_local = threading.local()


class _SmartHandler(logging.StreamHandler):
    """Writes to the thread-local capture buffer when set, else sys.stdout."""

    def emit(self, record: logging.LogRecord) -> None:
        self.stream = getattr(_local, "buf", None) or sys.stdout
        super().emit(record)


def setup(level: str = "INFO", log_file: Path | None = None) -> None:
    """Configure root logger. Safe to call multiple times — updates level and adds handlers."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    if not any(isinstance(h, _SmartHandler) for h in root.handlers):
        h = _SmartHandler()
        h.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(h)
    if log_file is not None:
        _add_file_handler(Path(log_file), root)


def _add_file_handler(path: Path, root: logging.Logger) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))
    root.addHandler(fh)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def capture(fn) -> str:
    """Run fn() capturing all log output in this thread. Thread-safe."""
    buf = io.StringIO()
    _local.buf = buf
    try:
        fn()
    finally:
        _local.buf = None
    return buf.getvalue()
