"""
Centralized logging configuration.

Sets up a root logger with both console and rotating-file handlers.
All application modules should import and use this configured logger
rather than calling print() directly.
"""

import logging
import logging.handlers
import os
from pathlib import Path


_CONFIGURED = False


def setup_logging(level: str = "INFO", log_file: str | None = None) -> logging.Logger:
    """
    Configure and return the application-wide logger.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file.  If provided the directory
                  is created automatically.

    Returns:
        The configured root ``traffic`` logger.
    """
    global _CONFIGURED
    logger = logging.getLogger("traffic")

    if _CONFIGURED:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # ── Formatter ────────────────────────────────────────────────────────
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s.%(module)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console handler ──────────────────────────────────────────────────
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    # ── File handler (optional) ──────────────────────────────────────────
    if log_file:
        log_dir = Path(log_file).parent
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    _CONFIGURED = True
    logger.info("Logging initialised — level=%s", level)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a child logger under the ``traffic`` namespace.

    Usage::

        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Processing started")

    Args:
        name: Dotted module name (e.g. ``app.cv.detector``).

    Returns:
        A ``logging.Logger`` instance.
    """
    base = logging.getLogger("traffic")
    if name:
        return base.getChild(name)
    return base
