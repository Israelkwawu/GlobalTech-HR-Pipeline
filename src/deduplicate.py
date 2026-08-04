"""
Employee deduplication engine.

Responsibilities
----------------
- Exact ID matching
- Email matching
- Fuzzy name matching
- Ghost employee detection
- Produce golden employee dataset

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from config.logging_config import get_logger

from src.matching.exact_match import exact_employee_match
from src.matching.email_match import email_match
from src.matching.fuzzy_match import fuzzy_match
from src.matching.ghost_detection import (
    detect_payroll_ghosts,
    detect_benefits_ghosts,
    combine_ghost_reports,
)

logger = get_logger(__name__)


def deduplicate_employees(
    employee_df: pd.DataFrame,
    payroll_df: pd.DataFrame,
    benefits_df: pd.DataFrame,
):
    """
    Execute the complete deduplication workflow.

    Returns
    -------
    dict
        {
            "golden_dataset": ...,
            "exact_matches": ...,
            "email_matches": ...,
            "fuzzy_matches": ...,
            "ghost_employees": ...
        }
    """

    logger.info(
        "Starting deduplication..."
    )

    # ----------------------------------------------------
    # Exact ID
    # ----------------------------------------------------

    exact_matches = exact_employee_match(
        employee_df,
        payroll_df,
    )

    # ----------------------------------------------------
    # Email
    # ----------------------------------------------------

    if (
        "email" in payroll_df.columns
        and "email" in employee_df.columns
    ):

        email_matches = email_match(
            employee_df,
            payroll_df,
        )

    else:
        email_matches = pd.DataFrame()

    # ----------------------------------------------------
    # Fuzzy
    # ----------------------------------------------------

    if (
        "full_name" in employee_df.columns
        and "full_name" in payroll_df.columns
    ):

        fuzzy_matches = fuzzy_match(
            employee_df,
            payroll_df,
        )

    else:

        fuzzy_matches = pd.DataFrame()

    # ----------------------------------------------------
    # Ghosts
    # ----------------------------------------------------

    payroll_ghosts = detect_payroll_ghosts(
        employee_df,
        payroll_df,
    )

    benefits_ghosts = detect_benefits_ghosts(
        employee_df,
        benefits_df,
    )

    ghosts = combine_ghost_reports(
        payroll_ghosts,
        benefits_ghosts,
    )

    # ----------------------------------------------------
    # Golden dataset
    # ----------------------------------------------------

    golden_dataset = (
        employee_df
        .drop_duplicates(
            subset="employee_id"
        )
        .copy()
    )

    logger.info(
        "Golden dataset contains %s employees.",
        len(golden_dataset),
    )

    return {
        "golden_dataset": golden_dataset,
        "exact_matches": exact_matches,
        "email_matches": email_matches,
        "fuzzy_matches": fuzzy_matches,
        "ghost_employees": ghosts,
    }
    
