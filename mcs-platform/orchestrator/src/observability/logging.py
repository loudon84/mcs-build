"""Logging configuration."""

import contextvars
import logging
import sys
from typing import Optional

from pythonjsonlogger import jsonlogger

# Per-request request_id，避免在 extra 中重复传递导致 LogRecord  overwrite KeyError
_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


def setup_logging(log_level: str = "INFO", request_id: Optional[str] = None):
    """配置 JSON 日志。仅首次调用时添加 handler 与 factory；request_id 写入 context 供 factory 读取。"""
    logger = logging.getLogger("mcs")
    logger.setLevel(getattr(logging, log_level.upper()))

    # 仅首次添加 handler，避免每次请求重复添加
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(request_id)s %(message)s",
            timestamp=True,
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        _old_factory = logging.getLogRecordFactory()

        def _record_factory(*args, **kwargs):
            record = _old_factory(*args, **kwargs)
            record.request_id = _request_id_var.get()
            return record

        logging.setLogRecordFactory(_record_factory)

    if request_id is not None:
        _request_id_var.set(request_id)

    return logger


def get_logger(name: str = "mcs") -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)

