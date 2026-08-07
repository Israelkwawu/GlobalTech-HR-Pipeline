"""
Employee ID transformation utilities.

Responsibilities
----------------
- Namespace employee IDs
- Normalize manager IDs
- Validate employee ID format
- Standardize employee identifiers
- Apply namespaced IDs to DataFrames

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

    Returns:

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
# Safe Value Check
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

        GlobalTech

        1
        ->
        GT-000001


        AcquiredCo

        ACQ_24

        ->
        AC-000024

    """

    if _is_empty(employee_id):

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

        logger.warning(
            "Invalid employee ID: %s",
            employee_id,
        )

        return None

    return f"{prefix}-" f"{int(digits):06d}"


# ============================================================
# Manager ID Normalization
# ============================================================


def normalize_manager_id(
    manager_id: str | int | None,
    company: str,
) -> str | None:
    """
    Normalize manager reference.

    Example:

        12765

        becomes

        GT-012765

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
    Validate canonical ID.

    Valid:

        GT-000001
        AC-000001

    """

    if _is_empty(employee_id):

        return False

    return bool(EMPLOYEE_ID_PATTERN.fullmatch(str(employee_id).strip()))


# ============================================================
# Employee ID DataFrame Transformation
# ============================================================


def namespace_employee_ids(
    df: pd.DataFrame,
    company_column: str = "company_origin",
    id_column: str = "employee_id",
) -> pd.DataFrame:
    """
    Namespace employee IDs.

    Only HRIS sources should call this.

    """

    df = df.copy()

    if id_column not in df.columns:

        return df

    if company_column not in df.columns:

        raise KeyError(f"Missing '{company_column}'")

    df[id_column] = df.apply(
        lambda row: namespace_employee_id(
            row[id_column],
            row[company_column],
        ),
        axis=1,
    )

    return df


# ============================================================
# Manager ID DataFrame Transformation
# ============================================================


def namespace_manager_ids(
    df: pd.DataFrame,
    company_column: str = "company_origin",
    manager_column: str = "manager_id",
) -> pd.DataFrame:
    """
    Normalize manager references.

    Example:

        12765

        becomes

        GT-012765

    """

    df = df.copy()

    if manager_column not in df.columns:

        return df

    if company_column not in df.columns:

        logger.warning("Company column missing. Skipping managers.")

        return df

    df[manager_column] = df.apply(
        lambda row: normalize_manager_id(
            row[manager_column],
            row[company_column],
        ),
        axis=1,
    )

    return df


# ============================================================
# Validation Helpers
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
