"""
Date transformation utilities.

Responsibilities
----------------
- Parse dates from multiple source systems
- Normalize dates into ISO format (YYYY-MM-DD)
- Validate hire dates
- Apply transformations to DataFrames

Author: Israel Kwawu
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from config.constants import (
    DATE_FORMAT_GLOBALTECH,
    DATE_FORMAT_ACQUIREDCO,
    DATE_FORMAT_BENEFITS,
    DATE_FORMAT_PAYROLL,
    ISO_DATE_FORMAT,
    MIN_HIRE_YEAR,
)

from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Source Date Formats
# ============================================================================

DATE_COLUMN_FORMATS = {
    ("globaltech_hris", "hire_date"): DATE_FORMAT_GLOBALTECH,
    ("acquiredco_hris", "hire_timestamp"): DATE_FORMAT_ACQUIREDCO,
    ("benefits", "enrollment_date"): DATE_FORMAT_BENEFITS,
    ("payroll", "effective_date"): DATE_FORMAT_PAYROLL,
}


# ============================================================================
# Single Value Functions
# ============================================================================

def parse_date(
    value: str | None,
    source: str,
    column: str,
) -> datetime | None:
    """
    Parse a date using the configured source/column format.

    Parameters
    ----------
    value
        Raw date string.

    source
        Source system name.

    column
        Date column name.

    Returns
    -------
    datetime | None
    """

    if pd.isna(value):
        return None

    try:
        fmt = DATE_COLUMN_FORMATS[(source, column)]
    except KeyError as exc:
        raise ValueError(
            f"No date format configured for "
            f"{source}.{column}"
        ) from exc

    try:
        return datetime.strptime(
            str(value).strip(),
            fmt,
        )

    except ValueError as exc:
        raise ValueError(
            f"Invalid date '{value}' "
            f"for {source}.{column}. "
            f"Expected format {fmt}."
        ) from exc


def normalize_date(
    value: str | None,
    source: str,
    column: str,
) -> str | None:
    """
    Convert a date into ISO format.

    Returns
    -------
    str | None
        YYYY-MM-DD
    """

    dt = parse_date(
        value,
        source,
        column,
    )

    if dt is None:
        return None

    return dt.strftime(
        ISO_DATE_FORMAT,
    )


def validate_hire_date(
    value: str | None,
) -> bool:
    """
    Validate normalized hire date.
    """

    if pd.isna(value):
        return False

    try:

        dt = datetime.strptime(
            value,
            ISO_DATE_FORMAT,
        )

    except ValueError:
        return False

    current_year = datetime.today().year

    return (
        MIN_HIRE_YEAR
        <= dt.year
        <= current_year
    )


# ============================================================================
# DataFrame Functions
# ============================================================================

def normalize_date_column(
    df: pd.DataFrame,
    source: str,
    column: str,
) -> pd.DataFrame:
    """
    Normalize one date column.
    """

    df = df.copy()

    if column not in df.columns:
        raise KeyError(
            f"Missing column '{column}'."
        )

    logger.info(
        "Normalizing %s...",
        column,
    )

    df[column] = df[column].apply(
        lambda value: normalize_date(
            value,
            source,
            column,
        )
    )

    return df


def normalize_dates(
    df: pd.DataFrame,
    source: str,
) -> pd.DataFrame:
    """
    Normalize every supported date column
    in a DataFrame.
    """

    df = df.copy()

    candidate_columns = (
        "hire_date",
        "hire_timestamp",
        "effective_date",
        "enrollment_date",
    )

    for column in candidate_columns:

        if column not in df.columns:
            continue

        logger.info(
            "Normalizing %s...",
            column,
        )

        df[column] = df[column].apply(
            lambda value: normalize_date(
                value,
                source,
                column,
            )
        )

    return df


def validate_date_column(
    df: pd.DataFrame,
    column: str = "hire_date",
) -> pd.Series:
    """
    Validate an entire date column.

    Returns
    -------
    pd.Series
        Boolean validation results.
    """

    if column not in df.columns:
        raise KeyError(
            f"Missing column '{column}'."
        )

    return df[column].apply(
        validate_hire_date,
    )