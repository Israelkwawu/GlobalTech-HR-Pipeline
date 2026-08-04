"""
Cleaning and transformation pipeline.

Responsibilities
----------------
- Standardize employee names
- Namespace employee IDs
- Normalize departments
- Normalize salaries
- Normalize dates
- Return a clean employee dataset

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from config.logging_config import get_logger

from src.transformers.names import standardize_names
from src.transformers.employee_id import namespace_employee_ids
from src.transformers.departments import map_departments
from src.transformers.salary import normalize_salary_columns
from src.transformers.dates import normalize_dates


logger = get_logger(__name__)


def clean_employee_data(
    df: pd.DataFrame,
    source: str,
) -> pd.DataFrame:
    """
    Execute the complete cleaning pipeline.

    Parameters
    ----------
    df
        Raw employee DataFrame.

    source
        Source system name.

    Returns
    -------
    pd.DataFrame
        Cleaned employee DataFrame.
    """

    logger.info(
        "Starting cleaning pipeline (%s)...",
        source,
    )

    df = df.copy()

    # ------------------------------------------------------------------
    # Names
    # ------------------------------------------------------------------

    if {
        "first_name",
        "last_name",
    }.issubset(df.columns):

        logger.info(
            "Standardizing employee names..."
        )

        df = standardize_names(df)

    # ------------------------------------------------------------------
    # Employee IDs
    # ------------------------------------------------------------------

    if {
        "employee_id",
        "company_origin",
    }.issubset(df.columns):

        logger.info(
            "Namespacing employee IDs..."
        )

        df = namespace_employee_ids(df)

    # ------------------------------------------------------------------
    # Departments
    # ------------------------------------------------------------------

    if {
        "department",
        "company_origin",
    }.issubset(df.columns):

        logger.info(
            "Mapping departments..."
        )

        df = map_departments(df)

    # ------------------------------------------------------------------
    # Salary
    # ------------------------------------------------------------------

    if {
        "salary",
        "currency",
        "pay_frequency",
    }.issubset(df.columns):

        logger.info(
            "Normalizing salaries..."
        )

        df = normalize_salary_columns(df)

    # ------------------------------------------------------------------
    # Dates
    # ------------------------------------------------------------------

    logger.info(
        "Normalizing dates..."
    )

    df = normalize_dates(
        df,
        source,
    )

    logger.info(
        "Cleaning pipeline complete."
    )

    return df

