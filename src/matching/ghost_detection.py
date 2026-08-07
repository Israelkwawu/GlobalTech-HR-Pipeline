"""
Ghost employee detection.

Responsibilities
----------------
- Detect payroll employees missing from HRIS
- Detect benefits employees missing from HRIS
- Produce compliance review files

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from datetime import datetime

from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# Normalize IDs
# ============================================================


def normalize_match_id(
    value,
):
    """
    Convert IDs to comparable numeric values.

    GT-001042 -> 1042
    AC-001042 -> 1042
    1042 -> 1042
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    digits = "".join(c for c in value if c.isdigit())

    if not digits:
        return None

    return int(digits)


# ============================================================
# Payroll Ghost Detection
# ============================================================


def detect_payroll_ghosts(
    employees: pd.DataFrame,
    payroll: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detect payroll records without HRIS employees.

    Compliance requirement:

    Payroll employee without HRIS record
    = ghost employee
    """

    logger.info("Starting payroll ghost detection...")

    employees = employees.copy()

    payroll = payroll.copy()

    # ------------------------------------------
    # Create matching keys
    # ------------------------------------------

    employees["match_id"] = employees["employee_id"].apply(normalize_match_id)

    payroll["match_id"] = payroll["employee_id"].apply(normalize_match_id)

    # ------------------------------------------
    # Find payroll only records
    # ------------------------------------------

    ghosts = payroll[~payroll["match_id"].isin(employees["match_id"])].copy()

    if ghosts.empty:

        logger.info("No payroll ghosts detected.")

        return pd.DataFrame()

    # ------------------------------------------
    # Compliance fields
    # ------------------------------------------

    ghosts["ghost_employee"] = True

    ghosts["ghost_reason"] = "Payroll record has no matching HRIS employee"

    ghosts["detected_at"] = datetime.utcnow()

    ghosts["source_system"] = "payroll"

    logger.warning(
        """
Payroll ghost employees detected.

Count=%s
""",
        len(ghosts),
    )

    return ghosts.drop(
        columns=["match_id"],
        errors="ignore",
    )


# ============================================================
# Benefits Ghost Detection
# ============================================================


def detect_benefits_ghosts(
    employees: pd.DataFrame,
    benefits: pd.DataFrame,
):

    employees = employees.copy()

    benefits = benefits.copy()

    employees["match_id"] = employees["employee_id"].apply(normalize_match_id)

    benefits["match_id"] = benefits["employee_id"].apply(normalize_match_id)

    ghosts = benefits[~benefits["match_id"].isin(employees["match_id"])].copy()

    if ghosts.empty:

        return pd.DataFrame()

    ghosts["ghost_employee"] = True

    ghosts["ghost_reason"] = "Benefits record has no matching HRIS employee"

    ghosts["detected_at"] = datetime.utcnow()

    ghosts["source_system"] = "benefits"

    logger.warning(
        "Benefits ghosts detected=%s",
        len(ghosts),
    )

    return ghosts.drop(
        columns=["match_id"],
        errors="ignore",
    )


# ============================================================
# Combine Reports
# ============================================================


def combine_ghost_reports(
    payroll_ghosts,
    benefits_ghosts,
):

    reports = []

    if not payroll_ghosts.empty:

        reports.append(payroll_ghosts)

    if not benefits_ghosts.empty:

        reports.append(benefits_ghosts)

    if not reports:

        return pd.DataFrame()

    result = pd.concat(
        reports,
        ignore_index=True,
    )

    logger.info(
        """
Ghost employee report generated.

Total=%s
""",
        len(result),
    )

    return result
