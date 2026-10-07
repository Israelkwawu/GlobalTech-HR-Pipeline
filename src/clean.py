"""
Cleaning and transformation pipeline.

Responsibilities
----------------
- Standardize employee names
- Namespace employee IDs
- Normalize manager IDs
- Normalize employment types
- Normalize departments
- Normalize salaries
- Normalize dates
- Repair missing values
- Return clean employee dataset

Author: Israel Kwawu
"""

from __future__ import annotations


import pandas as pd


from config.logging_config import get_logger


from src.transformers.names import (
    standardize_names,
)

from src.transformers.departments import (
    map_departments,
)

from src.transformers.salary import (
    normalize_salary_columns,
)

from src.transformers.dates import (
    flag_out_of_range_hire_dates,
    normalize_dates,
    parse_known_date,
)

from src.transformers.employment_type import (
    normalize_employment_type,
)

from src.transformers.employee_id import (
    namespace_employee_ids,
)

logger = get_logger(__name__)


# ============================================================
# Date Formatting
# ============================================================


def format_dates(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Parse source dates into datetime64[ns].

    Explicit formats are applied before any generic inference:
    YYYY-MM-DD, MM/DD/YYYY, and DD-Mon-YYYY.
    Hire dates before 1970-01-01 or after today are flagged.
    """

    df = df.copy()

    date_columns = [
        "hire_date",
        "effective_date",
        "enrollment_date",
        "benefits_enrollment_date",
    ]

    for column in date_columns:

        if column not in df.columns:
            continue

        parsed = pd.to_datetime(
            df[column].apply(parse_known_date),
            errors="coerce",
        )

        df[column] = parsed.astype("datetime64[ns]")

    return flag_out_of_range_hire_dates(df)


# ============================================================
# Missing Data Repair
# ============================================================


def repair_missing_values(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Apply business defaults.

    Prevent validation failures.
    """

    df = df.copy()

    # ----------------------------
    # Department
    # ----------------------------

    if "department" in df.columns:

        df["department"] = (
            df["department"]
            .fillna("Unknown")
            .replace(
                "",
                "Unknown",
            )
        )

    # ----------------------------
    # Country
    # ----------------------------

    if "country" in df.columns:

        df["country"] = (
            df["country"]
            .fillna("Unknown")
            .replace(
                "",
                "Unknown",
            )
        )

    # ----------------------------
    # Employment Type
    # ----------------------------

    if "employment_type" in df.columns:

        df["employment_type"] = (
            df["employment_type"]
            .fillna("Unknown")
            .replace(
                "",
                "Unknown",
            )
        )

    # ----------------------------
    # Email
    # ----------------------------

    if "email" in df.columns:

        df["email"] = df["email"].fillna("").astype(str).str.strip().str.lower()

        # Generate deterministic fallback email

        if "employee_id" in df.columns:

            mask = df["email"].eq("")

            df.loc[mask, "email"] = (
                "unknown."
                + df.loc[mask, "employee_id"].astype(str)
                + "@invalid.globaltech"
            )

    return df


# ============================================================
# Employee IDs
# ============================================================


def normalize_employee_identifiers(
    df: pd.DataFrame,
    source: str,
) -> pd.DataFrame:
    """
    Namespace employee IDs for every source.

    GlobalTech and payroll or benefits rows for GlobalTech become GT-######.
    AcquiredCo rows become AC-######. Leaving payroll or benefits ids raw
    would collide with the other company's number range.
    """

    df = df.copy()

    if not {"employee_id", "company_origin"}.issubset(df.columns):

        logger.info("Skipping employee ID namespace for %s", source)

        return df

    if source == "benefits":

        unresolved = ~df["company_origin"].astype(str).str.lower().isin(
            ["globaltech", "acquiredco"]
        )
        df.loc[unresolved, "company_origin"] = "GlobalTech"

    logger.info("Namespacing employee IDs for %s", source)

    return namespace_employee_ids(df)


# ============================================================
# Manager IDs
# ============================================================


def normalize_manager_ids(
    df: pd.DataFrame,
    source: str,
) -> pd.DataFrame:
    """
    Normalize manager IDs only for HRIS.
    """

    df = df.copy()

    if source not in {
        "globaltech_hris",
        "acquiredco_hris",
    }:

        return df

    if "manager_id" not in df.columns:

        return df

    def normalize(value):

        if pd.isna(value):

            return None

        digits = "".join(x for x in str(value) if x.isdigit())

        if not digits:

            return None

        prefix = "GT" if source == "globaltech_hris" else "AC"

        return f"{prefix}-{int(digits):06d}"

    df["manager_id"] = df["manager_id"].apply(normalize)

    return df


# ============================================================
# Main Cleaning Pipeline
# ============================================================


def clean_employee_data(
    df: pd.DataFrame,
    source: str,
) -> pd.DataFrame:

    logger.info(
        "Starting cleaning pipeline (%s)",
        source,
    )

    if df.empty:

        return df

    df = df.copy()

    # Names

    if {
        "first_name",
        "last_name",
    }.issubset(df.columns):

        df = standardize_names(df)

    # Employee IDs

    df = normalize_employee_identifiers(
        df,
        source,
    )

    # Managers

    df = normalize_manager_ids(
        df,
        source,
    )

    # Employment

    df = normalize_employment_type(df)

    # Departments

    if {
        "department",
        "company_origin",
    }.issubset(df.columns):

        df = map_departments(df)

    # Salary

    if {
        "salary",
        "currency",
        "pay_frequency",
    }.issubset(df.columns):

        df = normalize_salary_columns(df)

    # Dates

    df = normalize_dates(
        df,
        source,
    )

    df = format_dates(df)

    # Missing values

    df = repair_missing_values(df)

    # Final cleanup

    if "employee_id" in df.columns:

        df["employee_id"] = df["employee_id"].astype(str).str.strip()

    logger.info(
        "Cleaning complete rows=%s",
        len(df),
    )

    return df
