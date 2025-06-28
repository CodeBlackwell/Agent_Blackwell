"""Centralised logging configuration helper.

Import and call :func:`configure_logging` early in application entry points to
ensure consistent log formatting and level across all modules.

The configuration honours the ``LOG_LEVEL`` environment variable (default
``INFO``) and falls back gracefully if logging has already been configured by
another library (calling ``basicConfig`` has no effect once handlers exist).

The chosen format is JSON-like for easy ingestion by log aggregation systems
yet readable in local terminals. Example output::

    {"ts":"2025-06-27T23:45:12.345Z","level":"INFO","module":"my.mod","msg":"Task queued","extra":{}}

"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from types import FrameType
from typing import Any, Dict

__all__ = ["configure_logging"]


class _JsonFormatter(logging.Formatter):
    """Simple JSON formatter (UTC timestamps)."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        # Base payload
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "module": record.name,
            "msg": record.getMessage(),
        }

        # Extra dict support (if provided)
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            payload["extra"] = record.extra  # type: ignore[assignment]
        else:
            payload["extra"] = {}

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str | None = None) -> None:
    """Configure root logger once.

    Safe to call multiple times – subsequent calls are ignored if handlers are
    already present.
    """
    root_logger = logging.getLogger()

    # Determine desired level from argument or environment.
    level_name = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, level_name, logging.INFO)

    if root_logger.handlers:
        # Logging already configured elsewhere – update the level and (optionally)
        # formatter but avoid adding duplicate handlers.
        root_logger.setLevel(log_level)
        for h in root_logger.handlers:
            # If the existing handler is not using our formatter, switch it so we
            # still get structured JSON logs.
            if not isinstance(h.formatter, _JsonFormatter):
                h.setFormatter(_JsonFormatter())
        return

    # Fresh configuration – attach a single stream handler.
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
