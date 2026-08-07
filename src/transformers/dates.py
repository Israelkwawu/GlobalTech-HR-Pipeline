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

"""
IMPORTANT:

These keys use the canonical schema names AFTER alignment.

Example:

AcquiredCo:
hire_timestamp
        |
        v
align_employee_schema()
        |
        v
hire_date

Therefore we normalize:
(acquiredco_hris, hire_date)

not:
(acquiredco_hris, hire_timestamp)
"""

DATE_COLUMN_FORMATS = {
    # GlobalTech HRIS CSV
    ("globaltech_hris", "hire_date"): DATE_FORMAT_GLOBALTECH,
    # AcquiredCo JSON API
    ("acquiredco_hris", "hire_date"): DATE_FORMAT_ACQUIREDCO,
    # Benefits XML
    ("benefits", "enrollment_date"): DATE_FORMAT_BENEFITS,
    # Payroll Excel
    ("payroll", "effective_date"): DATE_FORMAT_PAYROLL,
}


# ============================================================================
# Single Value Functions
# ============================================================================


def parse_date(
    value: str | datetime | pd.Timestamp | None,
    source: str,
    column: str,
) -> datetime | None:
    """
    Parse date from different source systems.

    Supports:
    - datetime objects
    - pandas timestamps
    - configured source formats
    - ISO dates
    - ISO datetime timestamps
    - common HR export formats
    """

    # ------------------------------------------------------------
    # Empty values
    # ------------------------------------------------------------

    if value is None:

        return None

    if isinstance(value, float) and pd.isna(value):

        return None

    if pd.isna(value):
        return None

    # ------------------------------------------------------------
    # Already parsed dates
    # ------------------------------------------------------------

    if isinstance(
        value,
        pd.Timestamp,
    ):

        return value.to_pydatetime()

    if isinstance(
        value,
        datetime,
    ):

        return value

    value = str(value).strip()

    if value == "" or value.lower() in {
        "null",
        "none",
        "nan",
    }:

        return None

    # ------------------------------------------------------------
    # Configured source format
    # ------------------------------------------------------------

    fmt = DATE_COLUMN_FORMATS.get(
        (
            source,
            column,
        )
    )

    if fmt:

        try:

            return datetime.strptime(
                value,
                fmt,
            )

        except ValueError:

            pass

    # ------------------------------------------------------------
    # Universal fallback formats
    # ------------------------------------------------------------

    fallback_formats = [
        # AcquiredCo JSON
        # 2024-06-27T00:00:00
        "%Y-%m-%dT%H:%M:%S",
        # ISO datetime with milliseconds
        # 2024-06-27T00:00:00.123
        "%Y-%m-%dT%H:%M:%S.%f",
        # Standard datetime
        # 2016-09-21 00:00:00
        "%Y-%m-%d %H:%M:%S",
        # ISO date
        "%Y-%m-%d",
        # European format
        "%d/%m/%Y",
    ]

    for fmt in fallback_formats:

        try:

            return datetime.strptime(
                value,
                fmt,
            )

        except ValueError:

            continue

    # ------------------------------------------------------------
    # Pandas final parser
    # ------------------------------------------------------------

    try:

        parsed = pd.to_datetime(
            value,
            errors="raise",
        )

        return parsed.to_pydatetime()

    except Exception as exc:

        raise ValueError(f"Invalid date '{value}' " f"for {source}.{column}") from exc


def normalize_date(
    value: str | datetime | pd.Timestamp | None,
    source: str,
    column: str,
) -> str | None:
    """
    Normalize date into ISO format.

    Output:
        YYYY-MM-DD

    Invalid or missing dates return None.
    """

    # Handle pandas missing values
    if value is None or pd.isna(value):

        logger.warning(
            "Missing date value source=%s column=%s",
            source,
            column,
        )

        return None

    dt = parse_date(
        value,
        source,
        column,
    )

    # parse_date failed
    if dt is None or pd.isna(dt):

        logger.warning(
            "Invalid date value=%s source=%s column=%s",
            value,
            source,
            column,
        )

        return None

    return dt.strftime(ISO_DATE_FORMAT)


def validate_hire_date(
    value: str | None,
) -> bool:
    """
    Validate normalized hire date.
    """

    if value is None:

        return False

    try:

        dt = datetime.strptime(
            value,
            ISO_DATE_FORMAT,
        )

    except ValueError:

        return False

    current_year = datetime.today().year

    return MIN_HIRE_YEAR <= dt.year <= current_year


# ============================================================================
# DataFrame Functions
# ============================================================================


def normalize_date_column(
    df: pd.DataFrame,
    source: str,
    column: str,
) -> pd.DataFrame:
    """
    Normalize a single date column.
    """

    df = df.copy()

    if column not in df.columns:

        raise KeyError(f"Missing column '{column}'.")

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
    Normalize supported date columns.
    """

    df = df.copy()

    candidate_columns = [
        "hire_date",
        "hire_timestamp",
        "effective_date",
        "enrollment_date",
    ]

    for column in candidate_columns:

        if column not in df.columns:

            continue

        logger.info(
            "Normalizing %s.%s",
            source,
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
    Validate entire date column.
    """

    if column not in df.columns:

        raise KeyError(f"Missing column '{column}'.")

    return df[column].apply(validate_hire_date)
