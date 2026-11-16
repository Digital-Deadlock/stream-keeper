"""Small structured logging helper with stable event fields."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


class EventFormatter(logging.Formatter):
    def __init__(self, json_output: bool) -> None:
        super().__init__()
        self.json_output = json_output

    def format(self, record: logging.LogRecord) -> str:
        fields = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        event_fields = getattr(record, "event_fields", {})
        fields.update(event_fields)
        if self.json_output:
            return json.dumps(fields, separators=(",", ":"), sort_keys=True)
        suffix = " ".join(f"{key}={value}" for key, value in event_fields.items())
        return f"{fields['timestamp']} {record.levelname} {record.getMessage()} {suffix}".rstrip()


def configure_logging(level: str, log_format: str) -> logging.Logger:
    logger = logging.getLogger("stream_keeper")
    logger.handlers.clear()
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(EventFormatter(log_format == "json"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_event(
    logger: logging.Logger, level: int, message: str, **fields: object
) -> None:
    logger.log(level, message, extra={"event_fields": fields})

