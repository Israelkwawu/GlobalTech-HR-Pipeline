"""
Employee ID transformation utilities.

Responsibilities
----------------
- Namespace employee IDs
- Validate employee ID format
- Standardize employee IDs
- Apply namespaced IDs to DataFrames

Author: Israel Kwawu
"""

from __future__ import annotations

import re

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)

EMPLOYEE_ID_PATTERN = re.compile(r"^(GT|AC)-\d{6}$")

COMPANY_PREFIX = {
    "GlobalTech": "GT",
    "AcquiredCo": "AC",
    "globaltech": "GT",
    "acquiredco": "AC",
    "GT": "GT",
    "AC": "AC",
}


def namespace_employee_id(
    employee_id: str | int | None,
    company: str,
) -> str | None:
    """
    Convert an employee ID into a namespaced ID.

    Examples
    --------
    42 -> GT-000042
    1042 -> AC-001042
    """

    if pd.isna(employee_id):
        return None

    prefix = COMPANY_PREFIX.get(company)

    if prefix is None:
        raise ValueError(
            f"Unsupported company '{company}'."
        )

    digits = re.sub(r"\D", "", str(employee_id))

    if not digits:
        raise ValueError(
            "Employee ID contains no digits."
        )

    return f"{prefix}-{int(digits):06d}"


def is_valid_employee_id(
    employee_id: str | None,
) -> bool:
    """
    Validate employee ID format.
    """

    if pd.isna(employee_id):
        return False

    return bool(
        EMPLOYEE_ID_PATTERN.fullmatch(
            str(employee_id)
        )
    )


def namespace_employee_ids(
    df: pd.DataFrame,
    company_column: str = "company_origin",
    id_column: str = "employee_id",
) -> pd.DataFrame:
    """
    Namespace employee IDs in a DataFrame.
    """

    df = df.copy()

    if id_column not in df.columns:
        return df

    if company_column not in df.columns:
        raise KeyError(
            f"Missing '{company_column}' column."
        )

    logger.info(
        "Namespacing employee IDs..."
    )

    df[id_column] = df.apply(
        lambda row: namespace_employee_id(
            row[id_column],
            row[company_column],
        ),
        axis=1,
    )

    return df


def validate_employee_ids(
    df: pd.DataFrame,
    column: str = "employee_id",
) -> pd.Series:
    """
    Return boolean Series indicating valid IDs.
    """

    return df[column].apply(
        is_valid_employee_id
    )
    
