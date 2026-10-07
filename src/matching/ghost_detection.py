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

from src.transformers.salary import normalize_salary_columns

logger = get_logger(__name__)


# ============================================================
# Payroll Ghost Detection
# ============================================================


def _employee_name(frame: pd.DataFrame) -> pd.Series:
    """Build a display name from the columns that are present."""

    if "full_name" in frame.columns:
        return frame["full_name"].astype("string")

    if {"first_name", "last_name"}.issubset(frame.columns):
        return (
            frame["first_name"].fillna("").astype(str)
            + " "
            + frame["last_name"].fillna("").astype(str)
        ).str.strip()

    if "name" in frame.columns:
        return frame["name"].astype("string")

    return pd.Series([pd.NA] * len(frame), index=frame.index)


def _with_annual_usd(payroll: pd.DataFrame) -> pd.DataFrame:
    """
    Convert payroll salary before ghost reporting.

    Missing currency or frequency defaults to USD and Annual so a raw
    salary amount is still expressed as salary_usd_annual.
    """

    payroll = payroll.copy()

    if "salary_usd_annual" in payroll.columns and payroll["salary_usd_annual"].notna().any():
        return payroll

    if "currency" not in payroll.columns:
        payroll["currency"] = "USD"

    if "pay_frequency" not in payroll.columns:
        payroll["pay_frequency"] = "Annual"

    return normalize_salary_columns(payroll)


def detect_payroll_ghosts(
    employees: pd.DataFrame,
    payroll: pd.DataFrame,
) -> pd.DataFrame:
    """
    Detect payroll records without HRIS employees.

    Comparison uses the namespaced employee id. Stripping the GT/AC
    prefix would treat GlobalTech 1042 and AcquiredCo 1042 as one person.

    The report is separate from the golden dataset.
    """

    logger.info("Starting payroll ghost detection...")

    employees = employees.copy()
    payroll = _with_annual_usd(payroll)

    employee_ids = set(employees["employee_id"].dropna().astype(str).str.strip())
    payroll_ids = payroll["employee_id"].astype("string").str.strip()
    ghosts = payroll.loc[~payroll_ids.isin(employee_ids)].copy()

    if ghosts.empty:

        logger.info("No payroll ghosts detected.")

        return pd.DataFrame(
            columns=[
                "payroll_employee_id",
                "name",
                "salary_usd_annual",
                "ghost_flag_reason",
                "ghost_employee",
                "employee_id",
            ]
        )

    ghosts["payroll_employee_id"] = ghosts["employee_id"].astype("string").str.strip()
    ghosts["name"] = _employee_name(ghosts)
    ghosts["ghost_flag_reason"] = "Payroll record has no matching HRIS employee"
    ghosts["ghost_employee"] = True
    ghosts["detected_at"] = datetime.utcnow()
    ghosts["source_system"] = "payroll"

    if "salary_usd_annual" not in ghosts.columns:
        ghosts["salary_usd_annual"] = pd.NA

    logger.warning("Payroll ghost employees detected. Count=%s", len(ghosts))

    return ghosts.reset_index(drop=True)


# ============================================================
# Benefits Ghost Detection
# ============================================================


def detect_benefits_ghosts(
    employees: pd.DataFrame,
    benefits: pd.DataFrame,
):

    employees = employees.copy()

    benefits = benefits.copy()

    employee_ids = set(employees["employee_id"].dropna().astype(str).str.strip())

    benefit_ids = benefits["employee_id"].astype("string").str.strip()

    ghosts = benefits.loc[~benefit_ids.isin(employee_ids)].copy()

    if ghosts.empty:

        return pd.DataFrame()

    ghosts["ghost_employee"] = True

    ghosts["ghost_flag_reason"] = "Benefits record has no matching HRIS employee"

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

    logger.info("Ghost employee report rows=%s", len(result))

    return result
