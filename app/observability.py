import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status_code", "duration_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def configure_logging(log_level: str, log_format: str = "text") -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "autoposter"):
        logging.getLogger(logger_name).setLevel(level)
