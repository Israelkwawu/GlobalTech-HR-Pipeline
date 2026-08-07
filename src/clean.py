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
    normalize_dates,
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
    Convert supported date formats into ISO format.

    Supported input formats
    -----------------------
    - YYYY-MM-DD
    - DD/MM/YYYY
    - DD-MM-YYYY
    - Mixed formats

    Output
    ------
    YYYY-MM-DD
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

        # Preserve missing values
        values = (
            df[column]
            .replace({"": pd.NA, "None": pd.NA, "nan": pd.NA})
            .astype("string")
            .str.strip()
        )

        # Allocate output
        parsed = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

        # -----------------------------------------------------
        # ISO dates (YYYY-MM-DD)
        # -----------------------------------------------------
        iso_mask = values.str.match(
            r"^\d{4}-\d{2}-\d{2}$",
            na=False,
        )

        parsed.loc[iso_mask] = pd.to_datetime(
            values.loc[iso_mask],
            format="%Y-%m-%d",
            errors="coerce",
        )

        # -----------------------------------------------------
        # Day-first dates (DD/MM/YYYY or DD-MM-YYYY)
        # -----------------------------------------------------
        dmy_mask = values.str.match(
            r"^\d{2}[/-]\d{2}[/-]\d{4}$",
            na=False,
        )

        parsed.loc[dmy_mask] = pd.to_datetime(
            values.loc[dmy_mask],
            dayfirst=True,
            errors="coerce",
        )

        # -----------------------------------------------------
        # Remaining unknown formats
        # -----------------------------------------------------
        remaining = ~(iso_mask | dmy_mask)

        if remaining.any():
            parsed.loc[remaining] = pd.to_datetime(
                values.loc[remaining],
                format="mixed",
                errors="coerce",
            )

        df[column] = parsed.dt.strftime("%Y-%m-%d")

    return df


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
    Namespace only HRIS employee IDs.

    HRIS:
        1 -> GT-000001

    AcquiredCo:
        1 -> AC-000001

    Payroll:
        keep original

    Benefits:
        keep original
    """

    df = df.copy()

    if source in {
        "globaltech_hris",
        "acquiredco_hris",
    } and {
        "employee_id",
        "company_origin",
    }.issubset(df.columns):

        logger.info("Namespacing employee IDs...")

        df = namespace_employee_ids(df)

    else:

        logger.info(
            "Skipping employee ID namespace for %s",
            source,
        )

    return df


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
