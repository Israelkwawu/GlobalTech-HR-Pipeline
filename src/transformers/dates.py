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

import re
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

# AcquiredCo HRIS uses US dates. Benefits uses an English month abbreviation.
DATE_FORMAT_ACQUIREDCO_MDY = "%m/%d/%Y"
DATE_FORMAT_BENEFITS_DMY = "%d-%b-%Y"

DATE_COLUMN_FORMATS = {
    # GlobalTech HRIS CSV: 2016-09-21
    ("globaltech_hris", "hire_date"): DATE_FORMAT_GLOBALTECH,
    # AcquiredCo JSON API: 06/27/2024
    ("acquiredco_hris", "hire_date"): DATE_FORMAT_ACQUIREDCO_MDY,
    # Benefits XML: 15-Jan-2022
    ("benefits", "enrollment_date"): DATE_FORMAT_BENEFITS_DMY,
    ("benefits", "benefits_enrollment_date"): DATE_FORMAT_BENEFITS_DMY,
    # Payroll Excel
    ("payroll", "effective_date"): DATE_FORMAT_PAYROLL,
}

# Tried, in order, before generic inference.
REQUIRED_DATE_FORMATS = (
    DATE_FORMAT_GLOBALTECH,
    DATE_FORMAT_ACQUIREDCO_MDY,
    DATE_FORMAT_BENEFITS_DMY,
)

ENGLISH_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

BENEFITS_DATE_PATTERN = re.compile(r"^(\d{1,2})-([A-Za-z]{3})-(\d{4})$")


# ============================================================================
# Single Value Functions
# ============================================================================


def _parse_day_mon_year(value: str) -> datetime | None:
    """
    Parse Benefits dates such as 15-Jan-2022.

    Month names are matched in English so the result does not depend
    on the machine locale.
    """

    match = BENEFITS_DATE_PATTERN.fullmatch(value.strip())

    if not match:
        return None

    day, month_name, year = match.groups()
    month = ENGLISH_MONTHS.get(month_name.lower())

    if month is None:
        return None

    try:
        return datetime(int(year), month, int(day))
    except ValueError:
        return None


def _strptime(value: str, fmt: str) -> datetime | None:
    """Parse one explicit format. Benefits dates bypass locale-sensitive %b."""

    if fmt == DATE_FORMAT_BENEFITS_DMY:
        return _parse_day_mon_year(value)

    try:
        return datetime.strptime(value, fmt)
    except ValueError:
        return None


def parse_known_date(
    value: str | datetime | pd.Timestamp | None,
) -> datetime | None:
    """
    Parse a date using the three source formats before generic inference.

    Order:
    - GlobalTech YYYY-MM-DD
    - AcquiredCo MM/DD/YYYY
    - Benefits DD-Mon-YYYY
    - Remaining known exports
    - pandas inference
    """

    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    if not isinstance(value, (str, datetime, pd.Timestamp)) and pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if isinstance(value, datetime):
        return value

    text = str(value).strip()

    if text == "" or text.lower() in {"null", "none", "nan", "nat"}:
        return None

    for fmt in REQUIRED_DATE_FORMATS:
        parsed = _strptime(text, fmt)
        if parsed is not None:
            return parsed

    for fmt in (
        DATE_FORMAT_ACQUIREDCO,
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y",
    ):
        parsed = _strptime(text, fmt)
        if parsed is not None:
            return parsed

    try:
        parsed = pd.to_datetime(text, errors="raise")
        return parsed.to_pydatetime()
    except Exception:
        return None


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
    # Configured source format, then the three required formats,
    # then generic inference.
    # ------------------------------------------------------------

    fmt = DATE_COLUMN_FORMATS.get((source, column))

    if fmt:
        parsed = _strptime(value, fmt)
        if parsed is not None:
            return parsed

    parsed = parse_known_date(value)

    if parsed is not None:
        return parsed

    raise ValueError(f"Invalid date '{value}' for {source}.{column}")


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

    earliest = datetime(MIN_HIRE_YEAR, 1, 1)
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

    return earliest <= dt.replace(hour=0, minute=0, second=0, microsecond=0) <= today


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
        "benefits_enrollment_date",
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
