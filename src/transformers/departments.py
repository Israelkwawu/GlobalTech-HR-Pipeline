"""
Department transformation utilities.

Responsibilities
----------------
- Normalize department values
- Map departments into a common taxonomy
- Detect unmapped departments
"""

from __future__ import annotations

import pandas as pd

from config.department_mapping import (
    GLOBALTECH_DEPARTMENT_MAP,
    ACQUIREDCO_DEPARTMENT_MAP,
)

from config.constants import (
    GLOBALTECH,
    ACQUIREDCO,
)

from config.logging_config import get_logger

logger = get_logger(__name__)


def normalize_department(
    department: str | None,
) -> str | None:
    """
    Normalize department values.

    Examples
    --------
    engineering -> Engineering

    FINANCE -> Finance
    """

    if pd.isna(department):
        return None

    return (
        str(department)
        .strip()
        .title()
    )


def map_department(
    department: str | None,
    company: str,
) -> str | None:
    """
    Map one department into the standard taxonomy.
    """

    department = normalize_department(
        department
    )

    if department is None:
        return None

    company = str(company).strip()

    if company == GLOBALTECH:
        mapping = GLOBALTECH_DEPARTMENT_MAP

    elif company == ACQUIREDCO:
        mapping = ACQUIREDCO_DEPARTMENT_MAP

    else:
        raise ValueError(
            f"Unsupported company: {company}"
        )

    result = mapping.get(department)

    if result is None:

        logger.warning(
            "Unmapped department '%s' from %s",
            department,
            company,
        )

    return result


def map_departments(
    df: pd.DataFrame,
    department_column: str = "department",
    company_column: str = "company_origin",
) -> pd.DataFrame:
    """
    Map every department in a DataFrame.
    """

    df = df.copy()

    required = {
        department_column,
        company_column,
    }

    missing = required - set(df.columns)

    if missing:
        raise KeyError(
            f"Missing columns: {missing}"
        )

    logger.info(
        "Mapping departments..."
    )

    df[department_column] = df.apply(
        lambda row:
            map_department(
                row[department_column],
                row[company_column],
            ),
        axis=1,
    )

    return df


def find_unmapped_departments(
    df: pd.DataFrame,
    department_column: str = "department",
) -> pd.DataFrame:
    """
    Return rows whose department could not be mapped.
    """

    return df[
        df[department_column].isna()
    ]
    
