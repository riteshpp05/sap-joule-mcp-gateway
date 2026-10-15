"""
core/logger.py
--------------
Production-grade structured logging for SAP Joule Gateway.
Provides standardized formatting, contextual correlation ID tracking, and loglevel filtering.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


class CorrelationFilter(logging.Filter):
    """Injects correlation_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = "-"
        return True


def setup_logger(name: str = "sap_joule_gateway", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured enterprise logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] [corr=%(correlation_id)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(CorrelationFilter())
        logger.addHandler(handler)

    return logger


logger = setup_logger()
