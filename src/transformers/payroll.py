"""
Payroll transformation utilities.

Responsibilities
----------------
- Normalize payroll records
- Clean salary values
- Normalize currencies
- Normalize pay frequency
- Calculate annual salary
- Convert salary to USD

Author: Israel Kwawu
"""

from __future__ import annotations


import pandas as pd


from config.logging_config import get_logger


from src.transformers.employee_id import namespace_employee_ids
from src.transformers.salary import (
    normalize_salary_columns,
)

logger = get_logger(__name__)


# ============================================================
# Required Payroll Columns
# ============================================================


REQUIRED_COLUMNS = [
    "employee_id",
    "salary",
    "currency",
    "pay_frequency",
]


# ============================================================
# Ensure Payroll Schema
# ============================================================


def ensure_payroll_schema(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Ensure payroll contains required columns.
    """

    df = df.copy()

    for column in REQUIRED_COLUMNS:

        if column not in df.columns:

            logger.warning(
                "Missing payroll column: %s. Creating empty column.",
                column,
            )

            df[column] = None

    return df


# ============================================================
# Normalize Pay Frequency
# ============================================================


def normalize_pay_frequency(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize payroll frequencies.

    Examples:

    Monthly
        ->
    Monthly


    MONTH
        ->
    Monthly


    Bi Weekly
        ->
    Bi-Weekly

    """

    df = df.copy()

    if "pay_frequency" not in df.columns:

        return df

    mapping = {
        "MONTH": "Monthly",
        "MONTHLY": "Monthly",
        "M": "Monthly",
        "BIWEEKLY": "Bi-Weekly",
        "BI-WEEKLY": "Bi-Weekly",
        "BI WEEKLY": "Bi-Weekly",
        "BI_WEEKLY": "Bi-Weekly",
        "WEEKLY": "Weekly",
        "ANNUAL": "Annual",
        "YEARLY": "Annual",
    }

    df["pay_frequency"] = (
        df["pay_frequency"].astype(str).str.upper().str.strip().replace(mapping)
    )

    return df


# ============================================================
# Normalize Currency
# ============================================================


def normalize_currency(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize currency codes.
    """

    df = df.copy()

    if "currency" not in df.columns:

        return df

    mapping = {
        "$": "USD",
        "US$": "USD",
        "DOLLAR": "USD",
        "USDOLLAR": "USD",
        "GH₵": "GHS",
        "CEDI": "GHS",
    }

    df["currency"] = df["currency"].astype(str).str.upper().str.strip().replace(mapping)

    return df


# ============================================================
# Main Payroll Normalization
# ============================================================


def normalize_payroll(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize payroll records.

    Output columns include:

        salary_numeric

        salary_annual

        salary_usd_annual

    """

    logger.info("Starting payroll normalization...")

    if df.empty:

        logger.warning("Payroll dataframe empty.")

        return df

    df = df.copy()

    # --------------------------------------------------------
    # Schema
    # --------------------------------------------------------

    df = ensure_payroll_schema(df)

    # --------------------------------------------------------
    # Currency
    # --------------------------------------------------------

    df = normalize_currency(df)

    # --------------------------------------------------------
    # Pay frequency
    # --------------------------------------------------------

    df = normalize_pay_frequency(df)

    # --------------------------------------------------------
    # Salary processing
    # --------------------------------------------------------

    df = normalize_salary_columns(df)

    if "company_origin" not in df.columns:
        df["company_origin"] = "GlobalTech"

    if "employee_id" in df.columns:
        df = namespace_employee_ids(df)

    # --------------------------------------------------------
    # Validation logging
    # --------------------------------------------------------

    populated = (
        int(df["salary_usd_annual"].notna().sum())
        if "salary_usd_annual" in df.columns
        else 0
    )

    logger.info(
        "Payroll normalized rows=%s salary_usd=%s",
        len(df),
        populated,
    )

    return df
