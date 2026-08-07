"""
File utility functions for the GlobalTech HR Data Integration Pipeline.

This module provides reusable helper functions for:
- File existence checks
- Directory creation
- File extension validation
- Safe loading wrappers
- Record counting

Author: Israel Kwawu
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Directory Utilities
# ============================================================================


def ensure_directory(path: str | Path) -> Path:
    """
    Create a directory if it does not already exist.

    Parameters
    ----------
    path : str | Path
        Directory path.

    Returns
    -------
    Path
        Directory path.
    """

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)

    return directory


# ============================================================================
# File Validation
# ============================================================================


def validate_file_exists(path: str | Path) -> Path:
    """
    Validate that a file exists.

    Parameters
    ----------
    path : str | Path
        File path.

    Raises
    ------
    FileNotFoundError
        If file does not exist.
    """

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise FileNotFoundError(f"Not a file: {file_path}")

    return file_path


def validate_extension(
    path: str | Path,
    allowed_extensions: Iterable[str],
) -> None:
    """
    Validate a file extension.

    Parameters
    ----------
    path : str | Path

    allowed_extensions : Iterable[str]

    Raises
    ------
    ValueError
        Unsupported extension.
    """

    suffix = Path(path).suffix.lower()

    allowed = {
        ext.lower() if ext.startswith(".") else f".{ext.lower()}"
        for ext in allowed_extensions
    }

    if suffix not in allowed:
        raise ValueError(
            f"Unsupported file extension '{suffix}'. "
            f"Expected one of {sorted(allowed)}."
        )


# ============================================================================
# File Information
# ============================================================================


def get_file_size(path: str | Path) -> int:
    """
    Return file size in bytes.
    """

    file_path = validate_file_exists(path)

    return file_path.stat().st_size


def is_empty_file(path: str | Path) -> bool:
    """
    Check whether a file is empty.
    """

    return get_file_size(path) == 0


# ============================================================================
# Logging Helpers
# ============================================================================


def log_file_loaded(
    source: str,
    path: str | Path,
    records: int,
) -> None:
    """
    Log successful file ingestion.

    Parameters
    ----------
    source : str
        Source system.

    path : str | Path
        File path.

    records : int
        Number of loaded records.
    """

    logger.info(
        "[%s] Loaded %s records from %s",
        source,
        records,
        Path(path).name,
    )


def log_file_error(
    source: str,
    path: str | Path,
    error: Exception,
) -> None:
    """
    Log file loading failures.

    Parameters
    ----------
    source : str

    path : str | Path

    error : Exception
    """

    logger.error(
        "[%s] Failed loading %s: %s",
        source,
        Path(path),
        error,
    )


# ============================================================================
# Generic Helpers
# ============================================================================


def count_records(df) -> int:
    """
    Return the number of records in a DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    int
    """

    return len(df)


def normalize_column_names(df):
    """
    Normalize DataFrame column names.

    Rules
    -----
    - Strip whitespace
    - Lowercase
    - Replace spaces with underscores

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
    """

    df = df.copy()

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    return df
