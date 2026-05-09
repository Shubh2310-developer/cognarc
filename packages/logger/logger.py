"""
COGNARC — Structured Logger (Python)
packages/logger/logger.py

Provides structured JSON logging for all Python services.
Per §17 — no print() in committed code. Use this logger.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    """Formats log records as JSON for production; pretty-prints for development."""

    def __init__(self, pretty: bool = False, service: str = "cognarc") -> None:
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

        # Include extra context fields if provided
        if hasattr(record, "context") and isinstance(record.context, dict):  # type: ignore[union-attr]
            entry.update(record.context)  # type: ignore[arg-type]

        # Include exception info if present
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)

        if self.pretty:
            icons = {"debug": "🔍", "info": "ℹ️", "warn": "⚠️", "error": "❌"}
            icon = icons.get(entry["level"], "•")
            extras = {k: v for k, v in entry.items() if k not in ("timestamp", "level", "service", "message")}
            extras_str = f" {json.dumps(extras)}" if extras else ""
            return f"{icon} [{entry['timestamp']}] {entry['level'].upper()} — {entry['message']}{extras_str}"

        return json.dumps(entry, default=str)


def get_logger(
    name: str = "cognarc",
    level: str = "INFO",
    pretty: bool = False,
) -> logging.Logger:
    """
    Create a structured logger for a specific service.

    Args:
        name: Logger name (usually module name or service name).
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        pretty: If True, human-readable output (use for local dev).

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter(pretty=pretty, service=name))
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    return logger


# Module-level convenience logger
logger = get_logger("cognarc")
