"""Logging configuration."""

import logging
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger


def setup_logging(log_level: str = "INFO", request_id: Optional[str] = None):
    """Setup JSON logging."""
    logger = logging.getLogger("mcs")
    logger.setLevel(getattr(logging, log_level.upper()))

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s",
        timestamp=True,
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Add request_id to context
    if request_id:
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record

        logging.setLogRecordFactory(record_factory)

    return logger


def get_logger(name: str = "mcs") -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)

