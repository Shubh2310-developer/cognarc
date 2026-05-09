"""
COGNARC — Structured Application Logger
apps/api/app/core/logger.py

Single source of truth for structured logging in the Python API.
Per §17: no print() in committed code. Import this everywhere.

Usage:
    from app.core.logger import get_logger
    log = get_logger("my.module")
    log.info("message", context={"key": "value"})
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Optional


class StructuredFormatter(logging.Formatter):
    """JSON formatter for production; pretty for development."""

    def __init__(self, pretty: bool = False, service: str = "cognarc-api") -> None:
        super().__init__()
        self.pretty = pretty
        self.service = service

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "service": self.service,
            "message": record.getMessage(),
        }
        # Extra context injected via extra={"context": {...}} in logger calls
        ctx = getattr(record, "context", None)
        if isinstance(ctx, dict):
            entry.update(ctx)
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)

        if self.pretty:
            icons = {"debug": "🔍", "info": "ℹ️", "warning": "⚠️", "error": "❌"}
            icon = icons.get(entry["level"], "•")
            extras = {k: v for k, v in entry.items() if k not in ("timestamp", "level", "service", "message")}
            suffix = f" {json.dumps(extras, default=str)}" if extras else ""
            return f"{icon} [{entry['timestamp'][:19]}] {entry['level'].upper()} — {entry['message']}{suffix}"

        return json.dumps(entry, default=str)


class StructuredLogger:
    """
    Structured logger wrapper.
    Supports: log.info("msg", context={"key": "val"})
    Passes context via logging.extra dict for StructuredFormatter to pick up.
    """

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _log(self, level: int, message: str, context: Optional[dict] = None) -> None:
        extra = {"context": context} if context else {}
        self._logger.log(level, message, extra=extra)

    def debug(self, message: str, context: Optional[dict] = None) -> None:
        self._log(logging.DEBUG, message, context)

    def info(self, message: str, context: Optional[dict] = None) -> None:
        self._log(logging.INFO, message, context)

    def warning(self, message: str, context: Optional[dict] = None) -> None:
        self._log(logging.WARNING, message, context)

    def warn(self, message: str, context: Optional[dict] = None) -> None:
        self._log(logging.WARNING, message, context)

    def error(self, message: str, context: Optional[dict] = None) -> None:
        self._log(logging.ERROR, message, context)

    def exception(self, message: str, context: Optional[dict] = None) -> None:
        extra = {"context": context} if context else {}
        self._logger.exception(message, extra=extra)


def get_logger(name: str = "cognarc-api", level: str = "INFO", pretty: bool = False) -> StructuredLogger:
    """Return a named structured logger."""
    base_logger = logging.getLogger(name)
    if not base_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter(pretty=pretty, service=name))
        base_logger.addHandler(handler)
    base_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    base_logger.propagate = False
    return StructuredLogger(base_logger)


# Module-level singleton
logger: StructuredLogger = get_logger("cognarc-api")
