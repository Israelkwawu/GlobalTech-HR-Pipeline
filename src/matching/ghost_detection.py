"""
Ghost employee detection.

Responsibilities
----------------
- Detect payroll records missing from HR
- Detect benefits records missing from HR
- Detect orphan records
- Produce ghost employee report

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


def detect_ghost_records(
    reference_df: pd.DataFrame,
    candidate_df: pd.DataFrame,
    id_column: str = "employee_id",
    source: str = "Unknown",
) -> pd.DataFrame:
    """
    Detect records that exist in candidate_df
    but not in reference_df.
    """

    if id_column not in reference_df.columns:
        raise KeyError(f"Missing '{id_column}' in reference dataset.")

    if id_column not in candidate_df.columns:
        raise KeyError(f"Missing '{id_column}' in candidate dataset.")

    logger.info(
        "Checking %s for ghost employees...",
        source,
    )

    ghosts = candidate_df[
        ~candidate_df[id_column].isin(
            reference_df[id_column]
        )
    ].copy()

    ghosts["ghost_employee"] = True
    ghosts["ghost_source"] = source

    logger.info(
        "%s ghost employees found.",
        len(ghosts),
    )

    return ghosts


def detect_payroll_ghosts(
    employee_df: pd.DataFrame,
    payroll_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detect payroll employees
    missing from HR.
    """

    return detect_ghost_records(
        employee_df,
        payroll_df,
        source="Payroll",
    )


def detect_benefits_ghosts(
    employee_df: pd.DataFrame,
    benefits_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detect benefits employees
    missing from HR.
    """

    return detect_ghost_records(
        employee_df,
        benefits_df,
        source="Benefits",
    )


def combine_ghost_reports(
    *reports: pd.DataFrame,
) -> pd.DataFrame:
    """
    Combine multiple ghost reports.
    """

    if not reports:
        return pd.DataFrame()

    return (
        pd.concat(
            reports,
            ignore_index=True,
        )
        .drop_duplicates()
    )
    
