"""
General helper functions for the GlobalTech HR Data Integration Pipeline.

These utilities provide reusable operations for:
- DataFrame manipulation
- Missing value handling
- Logging summaries
- Timestamp generation

Author: Israel Kwawu
"""

from __future__ import annotations

from datetime import datetime, timezone

import logging
import pandas as pd

from src.transformers.dates import parse_known_date

logger = logging.getLogger(__name__)


# ============================================================================
# DataFrame Helpers
# ============================================================================


def add_missing_columns(
    df: pd.DataFrame,
    columns: list[str],
    default_value=pd.NA,
) -> pd.DataFrame:
    """
    Add missing columns to a DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.

    columns : list[str]
        Columns that should exist.

    default_value :
        Default value for missing columns.

    Returns
    -------
    pd.DataFrame
    """

    df = df.copy()

    for column in columns:
        if column not in df.columns:
            df[column] = default_value

    return df


def reorder_columns(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Reorder DataFrame columns.

    Any columns not listed are appended to the end.

    Parameters
    ----------
    df : pd.DataFrame

    columns : list[str]

    Returns
    -------
    pd.DataFrame
    """

    ordered = [c for c in columns if c in df.columns]
    remaining = [c for c in df.columns if c not in ordered]

    return df[ordered + remaining]


def standardize_missing_values(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Replace common missing value representations with pd.NA.

    Examples
    --------
    "", "NULL", "null", "None", "N/A", "NA"

    Returns
    -------
    pd.DataFrame
    """

    return df.replace(
        {
            "": pd.NA,
            " ": pd.NA,
            "NULL": pd.NA,
            "null": pd.NA,
            "None": pd.NA,
            "none": pd.NA,
            "N/A": pd.NA,
            "NA": pd.NA,
        }
    )


# ============================================================================
# Record Helpers
# ============================================================================


def add_source_system(
    df: pd.DataFrame,
    source: str,
) -> pd.DataFrame:
    """
    Add source_system column.

    Parameters
    ----------
    df : pd.DataFrame

    source : str

    Returns
    -------
    pd.DataFrame
    """

    df = df.copy()

    df["source_system"] = source

    return df


def dataframe_summary(
    df: pd.DataFrame,
) -> dict:
    """
    Return a summary of a DataFrame.

    Returns
    -------
    dict
    """

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }


# ============================================================================
# Time Helpers
# ============================================================================


def current_timestamp() -> str:
    """
    Return current UTC timestamp in ISO-8601 format.

    Returns
    -------
    str
    """

    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# Logging Helpers
# ============================================================================


def log_dataframe_summary(
    name: str,
    df: pd.DataFrame,
) -> None:
    """
    Log DataFrame statistics.

    Parameters
    ----------
    name : str

    df : pd.DataFrame
    """

    summary = dataframe_summary(df)

    logger.info(
        ("%s | Rows=%s | Columns=%s | " "Missing=%s | Duplicates=%s"),
        name,
        summary["rows"],
        summary["columns"],
        summary["missing_values"],
        summary["duplicate_rows"],
    )


# ============================================================================
# Validation Helpers
# ============================================================================


def ensure_dataframe(
    obj,
) -> pd.DataFrame:
    """
    Ensure an object is a pandas DataFrame.

    Raises
    ------
    TypeError
    """

    if not isinstance(obj, pd.DataFrame):
        raise TypeError("Expected a pandas DataFrame.")

    return obj


def is_dataframe_empty(
    df: pd.DataFrame,
) -> bool:
    """
    Check whether a DataFrame is empty.

    Returns
    -------
    bool
    """

    return df.empty


def log_dataframe_schema(
    name: str,
    df: pd.DataFrame,
) -> None:
    """
    Log DataFrame schema.
    """
    logger.info("%s columns=%s", name, len(df.columns))


def clean_date_columns(
    df: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """
    Normalize date columns safely.

    Invalid or missing dates become NaT.

    Parameters
    ----------
    df:
        Input dataframe

    columns:
        Date columns to normalize

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe
    """

    df = df.copy()

    for column in columns:

        if column in df.columns:

            df[column] = pd.to_datetime(
                df[column].apply(parse_known_date),
                errors="coerce",
            )

    return df
