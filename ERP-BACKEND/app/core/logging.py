"""Structured JSON logging for ERP03."""

import json
import logging
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured observability."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "path": getattr(record, "path", None),
            "duration_ms": getattr(record, "duration_ms", None),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure structured JSON logging for the application."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    logger = logging.getLogger("erp03")
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.propagate = False

    return logger
