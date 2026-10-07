"""
Employee ID transformation utilities.

Responsibilities
----------------
- Namespace employee IDs
- Normalize manager IDs
- Validate employee ID format
- Standardize employee identifiers
- Apply namespaced IDs to DataFrames
- Capture malformed IDs for review

Author: Israel Kwawu
"""

from __future__ import annotations


import re

import pandas as pd


from config.constants import (
    COMPANY_ID_PREFIXES,
    EMPLOYEE_ID_PATTERN,
    GLOBALTECH,
    ACQUIREDCO,
)


from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# Company Resolver
# ============================================================


def resolve_company_prefix(
    company: str | None,
) -> str | None:
    """
    Resolve company namespace.

    Examples:

        GlobalTech -> GT
        AcquiredCo -> AC
    """

    if company is None:
        return None

    company = str(company).strip().lower()

    mapping = {
        "globaltech": COMPANY_ID_PREFIXES[GLOBALTECH],
        "globaltech_hris": COMPANY_ID_PREFIXES[GLOBALTECH],
        "gt": COMPANY_ID_PREFIXES[GLOBALTECH],
        "acquiredco": COMPANY_ID_PREFIXES[ACQUIREDCO],
        "acquiredco_hris": COMPANY_ID_PREFIXES[ACQUIREDCO],
        "ac": COMPANY_ID_PREFIXES[ACQUIREDCO],
    }

    return mapping.get(company)


# ============================================================
# Safe Empty Check
# ============================================================


def _is_empty(
    value,
) -> bool:

    if value is None:

        return True

    try:

        return bool(pd.isna(value))

    except TypeError:

        return False


# ============================================================
# Single Employee ID Normalization
# ============================================================


def namespace_employee_id(
    employee_id: str | int | None,
    company: str,
) -> str | None:
    """
    Convert employee ID into canonical format.

    Examples:

        1
        ->
        GT-000001

        EMP-123
        ->
        GT-000123
    """

    if _is_empty(employee_id):

        return None

    if str(employee_id).strip().lower() in {
        "nan",
        "none",
        "<na>",
    }:
        return None

    prefix = resolve_company_prefix(company)

    if prefix is None:

        raise ValueError(f"Unsupported company '{company}'")

    digits = re.sub(
        r"\D",
        "",
        str(employee_id),
    )

    if not digits:

        logger.error(
            "Employee ID contains no digits: %s",
            employee_id,
        )

        raise ValueError(f"Invalid employee ID: {employee_id}")

    return f"{prefix}-{int(digits):06d}"


# ============================================================
# Manager ID Normalization
# ============================================================


def normalize_manager_id(
    manager_id: str | int | None,
    company: str,
) -> str | None:
    """
    Normalize manager references.
    """

    if _is_empty(manager_id):

        return None

    return namespace_employee_id(
        manager_id,
        company,
    )


# ============================================================
# Validation
# ============================================================


def is_valid_employee_id(
    employee_id: str | None,
) -> bool:
    """
    Validate canonical employee ID.
    """

    if _is_empty(employee_id):

        return False

    return bool(EMPLOYEE_ID_PATTERN.fullmatch(str(employee_id).strip()))


# ============================================================
# DataFrame Employee ID Transformation
# ============================================================


def namespace_employee_ids(
    df: pd.DataFrame,
    company_column: str = "company_origin",
    id_column: str = "employee_id",
) -> pd.DataFrame:
    """
    Namespace employee IDs in dataframe.

    Invalid IDs are logged and converted to None
    instead of crashing the pipeline.

    """

    df = df.copy()

    if id_column not in df.columns:

        raise KeyError(f"Missing '{id_column}'")

    if company_column not in df.columns:

        raise KeyError(f"Missing '{company_column}'")

    dead_letters = []

    def process_row(row):

        try:

            return namespace_employee_id(
                row[id_column],
                row[company_column],
            )

        except ValueError as exc:

            dead_letters.append(
                {
                    "employee_id": row[id_column],
                    "company": row[company_column],
                    "reason": str(exc),
                }
            )

            return None

    df[id_column] = df.apply(
        process_row,
        axis=1,
    )

    if dead_letters:

        logger.error(
            "Employee ID dead-letter records=%s",
            len(dead_letters),
        )

    return df


# ============================================================
# Manager DataFrame Transformation
# ============================================================


def namespace_manager_ids(
    df: pd.DataFrame,
    company_column: str = "company_origin",
    manager_column: str = "manager_id",
) -> pd.DataFrame:
    """
    Normalize manager IDs.
    """

    df = df.copy()

    if manager_column not in df.columns:

        return df

    if company_column not in df.columns:

        logger.warning("Missing company column. " "Skipping manager normalization.")

        return df

    def process_manager(row):

        try:

            return normalize_manager_id(
                row[manager_column],
                row[company_column],
            )

        except ValueError:

            return None

    df[manager_column] = df.apply(
        process_manager,
        axis=1,
    )

    return df


# ============================================================
# Validate DataFrame IDs
# ============================================================


def validate_employee_ids(
    df: pd.DataFrame,
    column: str = "employee_id",
) -> pd.Series:
    """
    Validate employee IDs.
    """

    if column not in df.columns:

        raise KeyError(f"Missing '{column}'")

    return df[column].apply(is_valid_employee_id)
