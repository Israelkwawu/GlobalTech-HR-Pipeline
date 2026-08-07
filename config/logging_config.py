"""
Logging configuration for the GlobalTech HR Data Integration Pipeline.

This module provides a centralized logging setup used across all
pipeline modules.

Features:
- Console logging
- File logging
- Standardized log format
- Configurable log levels

Author: Israel Kwawu
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from config.settings import LOG_DIR, LOG_FILE, LOG_LEVEL
from config.constants import LOG_FORMAT

# ============================================================================
# Logging Constants
# ============================================================================

LOG_FILE_NAME = "pipeline.log"


# ============================================================================
# Create Log Directory
# ============================================================================


def create_log_directory() -> None:
    """
    Ensure the log directory exists.
    """

    Path(LOG_DIR).mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================================
# Logging Configuration
# ============================================================================


def configure_logging(
    level: str | None = None,
) -> None:
    """
    Configure application logging.

    Parameters
    ----------
    level : str, optional
        Logging level.
        Examples:
            DEBUG
            INFO
            WARNING
            ERROR
    """

    create_log_directory()

    log_level = (level or LOG_LEVEL).upper()

    numeric_level = getattr(
        logging,
        log_level,
        logging.INFO,
    )

    formatter = logging.Formatter(LOG_FORMAT)

    # ------------------------------------------------------------------------
    # Console Handler
    # ------------------------------------------------------------------------

    console_handler = logging.StreamHandler(sys.stdout)

    console_handler.setLevel(numeric_level)

    console_handler.setFormatter(formatter)

    # ------------------------------------------------------------------------
    # File Handler
    # ------------------------------------------------------------------------

    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8",
    )

    file_handler.setLevel(numeric_level)

    file_handler.setFormatter(formatter)

    # ------------------------------------------------------------------------
    # Root Logger
    # ------------------------------------------------------------------------

    root_logger = logging.getLogger()

    root_logger.setLevel(numeric_level)

    # Prevent duplicate handlers
    if not root_logger.handlers:

        root_logger.addHandler(console_handler)

        root_logger.addHandler(file_handler)


# ============================================================================
# Logger Factory
# ============================================================================


def get_logger(
    name: str,
) -> logging.Logger:
    """
    Create a named logger.

    Parameters
    ----------
    name : str
        Module name.

    Returns
    -------
    logging.Logger
    """

    return logging.getLogger(name)
