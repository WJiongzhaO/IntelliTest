"""Centralized logging configuration."""

import logging
import sys

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create a logger with consistent formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    return logger
