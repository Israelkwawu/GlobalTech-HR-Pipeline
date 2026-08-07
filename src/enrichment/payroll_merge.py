"""
Payroll enrichment.

Responsibilities
----------------
- Match payroll records to employees
- Resolve employee namespaces
- Normalize payroll identifiers
- Normalize salaries
- Treat payroll base_salary as annual compensation
- Convert currency to USD
- Merge payroll enrichment
- Preserve provenance

Author: Israel Kwawu
"""

from __future__ import annotations


import re

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# Currency Rates
# ============================================================


CURRENCY_RATES_TO_USD = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
}


# ============================================================
# Employee ID Normalization
# ============================================================


def normalize_employee_id(
    value,
    company_origin=None,
):
    """
    Normalize employee identifiers.

    Examples:

    1829
        ->
    GT-001829


    ACQ_00137
        ->
    AC-000137

    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value.startswith(
        (
            "GT-",
            "AC-",
        )
    ):
        return value

    # AcquiredCo format

    if value.upper().startswith("ACQ_"):

        digits = re.sub(
            r"\D",
            "",
            value,
        )

        return f"AC-{int(digits):06d}"

    digits = re.sub(
        r"\D",
        "",
        value,
    )

    if not digits:

        return value

    number = int(digits)

    if str(company_origin).lower() == "acquiredco":

        return f"AC-{number:06d}"

    return f"GT-{number:06d}"


# ============================================================
# Matching ID
# ============================================================


def create_match_id(
    df: pd.DataFrame,
):

    df = df.copy()

    df["match_id"] = (
        df["employee_id"].astype(str).str.extract(r"(\d+)")[0].astype("Int64")
    )

    return df


# ============================================================
# Salary Cleaning
# ============================================================


def clean_salary(
    value,
):
    """
    Convert salary values.

    Examples:

    "$111,833"
        ->
    111833


    50000
        ->
    50000

    """

    if pd.isna(value):

        return None

    value = str(value)

    value = re.sub(
        r"[^\d.]",
        "",
        value,
    )

    if value == "":

        return None

    return float(value)


# ============================================================
# Salary Normalization
# ============================================================


def normalize_salary(
    payroll: pd.DataFrame,
):

    payroll = payroll.copy()

    if "salary" not in payroll.columns:

        if "base_salary" in payroll.columns:

            logger.info("Mapping base_salary -> salary")

            payroll["salary"] = payroll["base_salary"]

    if "salary" in payroll.columns:

        payroll["salary_numeric"] = payroll["salary"].apply(clean_salary)

    return payroll


# ============================================================
# Annual Salary
# ============================================================


def calculate_salary_annual(
    row,
):
    """
    IMPORTANT

    Payroll base_salary is already annual.

    pay_frequency is metadata only.

    DO NOT multiply.

    Example:

    59714 Bi-Weekly

    remains:

    59714 annual salary

    """

    salary = row.get("salary_numeric")

    if pd.isna(salary):

        return None

    return salary


# ============================================================
# USD Conversion
# ============================================================


def calculate_salary_usd(
    row,
):

    salary = row.get("salary_annual")

    if pd.isna(salary):

        return None

    currency = (
        str(
            row.get(
                "currency",
                "USD",
            )
        )
        .upper()
        .strip()
    )

    rate = CURRENCY_RATES_TO_USD.get(
        currency,
        1,
    )

    return salary * rate


# ============================================================
# Prepare Payroll
# ============================================================


def prepare_payroll(
    payroll: pd.DataFrame,
):

    payroll = payroll.copy()

    # ------------------------------------------------
    # Company origin
    # ------------------------------------------------

    if "company_origin" not in payroll.columns:

        if "source" in payroll.columns:

            payroll["company_origin"] = payroll["source"].replace(
                {
                    "GlobalTech": "GlobalTech",
                    "AcquiredCo": "AcquiredCo",
                }
            )

        else:

            logger.warning("""
Payroll has no company origin.

Defaulting GlobalTech.
""")

            payroll["company_origin"] = "GlobalTech"

    # ------------------------------------------------
    # Employee IDs
    # ------------------------------------------------

    payroll["employee_id"] = payroll.apply(
        lambda row: normalize_employee_id(
            row["employee_id"],
            row["company_origin"],
        ),
        axis=1,
    )

    # ------------------------------------------------
    # Salary
    # ------------------------------------------------

    payroll = normalize_salary(payroll)

    payroll["salary_annual"] = payroll.apply(
        calculate_salary_annual,
        axis=1,
    )

    payroll["salary_usd_annual"] = payroll.apply(
        calculate_salary_usd,
        axis=1,
    )

    logger.info(
        """
========== PAYROLL SALARY CHECK ==========

%s

==========================================
""",
        payroll[
            [
                "employee_id",
                "salary",
                "currency",
                "pay_frequency",
                "salary_annual",
                "salary_usd_annual",
            ]
        ]
        .head(20)
        .to_string(),
    )

    return payroll


# ============================================================
# Deduplicate
# ============================================================


def deduplicate_ids(
    df,
    name,
):

    before = len(df)

    df = df.drop_duplicates(
        subset=["employee_id"],
        keep="last",
    )

    removed = before - len(df)

    if removed:

        logger.warning(
            "%s duplicate IDs removed=%s",
            name,
            removed,
        )

    return df


# ============================================================
# Payroll Columns
# ============================================================


def select_payroll_columns(
    payroll,
):

    columns = [
        "employee_id",
        "salary",
        "currency",
        "pay_frequency",
        "salary_numeric",
        "salary_annual",
        "salary_usd_annual",
        "bonus_target_pct",
        "effective_date",
        "company_origin",
    ]

    available = [c for c in columns if c in payroll.columns]

    return payroll[available].copy()


# ============================================================
# Merge Payroll
# ============================================================


def merge_payroll(
    employees: pd.DataFrame,
    payroll: pd.DataFrame,
):

    logger.info("Starting payroll merge")

    if payroll.empty:

        return employees

    employees = employees.copy()

    payroll = prepare_payroll(payroll)

    # Normalize HRIS IDs

    employees["employee_id"] = employees.apply(
        lambda row: normalize_employee_id(
            row["employee_id"],
            row.get("company_origin"),
        ),
        axis=1,
    )

    employees = deduplicate_ids(
        employees,
        "Employees",
    )

    payroll = deduplicate_ids(
        payroll,
        "Payroll",
    )

    # Keep employee IDs as primary key

    payroll = select_payroll_columns(payroll)

    logger.info(
        """
========== MATCH CHECK ==========

Employee IDs:

%s


Payroll IDs:

%s

=================================
""",
        employees["employee_id"].head().tolist(),
        payroll["employee_id"].head().tolist(),
    )

    merged = employees.merge(
        payroll,
        on="employee_id",
        how="left",
        suffixes=(
            "",
            "_payroll",
        ),
    )

    # ------------------------------------------------
    # Promote payroll fields
    # ------------------------------------------------

    fields = [
        "salary",
        "currency",
        "pay_frequency",
        "salary_numeric",
        "salary_annual",
        "salary_usd_annual",
        "bonus_target_pct",
        "effective_date",
        "company_origin",
    ]

    for field in fields:

        payroll_field = field + "_payroll"

        if payroll_field in merged.columns:

            merged[field] = merged[payroll_field].combine_first(merged[field])

            merged.drop(
                columns=[payroll_field],
                inplace=True,
            )

    # ------------------------------------------------
    # Remove duplicate ID columns
    # ------------------------------------------------

    merged.drop(
        columns=["employee_id_payroll"],
        errors="ignore",
        inplace=True,
    )

    # ------------------------------------------------
    # Provenance
    # ------------------------------------------------

    if "source_systems" in merged.columns:

        merged["source_systems"] = (
            merged["source_systems"]
            .fillna("")
            .astype(str)
            .apply(lambda x: x if "payroll" in x else f"{x},payroll")
        )

    else:

        merged["source_systems"] = "payroll"

    logger.info(
        """
========== PAYROLL MERGE RESULT ==========

Rows:
%s

Salary populated:
%s

Salary USD populated:
%s

==========================================
""",
        len(merged),
        merged["salary"].notna().sum(),
        merged["salary_usd_annual"].notna().sum(),
    )

    return merged
