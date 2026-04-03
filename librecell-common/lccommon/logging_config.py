#
# Centralized logging configuration for LibreCell.
#
from __future__ import annotations

import json
import logging
import sys
from typing import Optional


class JsonFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_format: bool = False,
) -> None:
    """Configure logging for all LibreCell modules.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional file path. If set, logs go to file instead of stderr.
        json_format: If True, use structured JSON output.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Remove existing handlers to allow reconfiguration
    for h in root.handlers[:]:
        root.removeHandler(h)

    if json_format:
        formatter = JsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(module)16s %(levelname)8s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    if log_file:
        handler = logging.FileHandler(log_file, encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stderr)

    handler.setFormatter(formatter)
    root.addHandler(handler)
