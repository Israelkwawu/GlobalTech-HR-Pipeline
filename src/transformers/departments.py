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

    if pd.isna(department):
        return None

    value = str(department).strip()

    # preserve codes
    if "-" in value:
        return value.upper()

    # preserve known acronyms
    special = {
        "it": "Information Technology",
        "hr": "Human Resources",
        "devops": "DevOps",
    }

    lower = value.lower()

    if lower in special:
        return special[lower]

    return value.title()


def map_department(
    department: str | None,
    company: str,
) -> str | None:
    """
    Map one department into the standard taxonomy.
    """

    department = normalize_department(department)

    if department is None:
        return None

    company = str(company).strip()

    if company == GLOBALTECH:
        mapping = GLOBALTECH_DEPARTMENT_MAP

    elif company == ACQUIREDCO:
        mapping = ACQUIREDCO_DEPARTMENT_MAP

    else:
        raise ValueError(f"Unsupported company: {company}")

    return mapping.get(department)


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
        raise KeyError(f"Missing columns: {missing}")

    logger.info("Mapping departments...")

    original = df[department_column].copy()

    df[department_column] = df.apply(
        lambda row: map_department(
            row[department_column],
            row[company_column],
        ),
        axis=1,
    )

    lost = original.notna() & df[department_column].isna()

    if lost.any():
        pairs = pd.DataFrame(
            {
                "department": original[lost],
                "company": df.loc[lost, company_column],
            }
        ).drop_duplicates()
        logger.warning(
            "Unmapped departments rows=%s unique=%s examples=%s",
            int(lost.sum()),
            len(pairs),
            pairs.head(8).to_dict("records"),
        )

    return df


def find_unmapped_departments(
    df: pd.DataFrame,
    department_column: str = "department",
) -> pd.DataFrame:
    """
    Return rows whose department could not be mapped.
    """

    return df[df[department_column].isna()]
