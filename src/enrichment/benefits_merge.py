"""
Benefits enrichment.

Aggregates multiple benefit enrollments
into one employee-level record.

Author: Israel Kwawu
"""

from __future__ import annotations


import re

import pandas as pd


from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# Employee ID Normalization
# ============================================================


def normalize_employee_id(
    value,
) -> str | None:
    """
    Convert employee IDs into canonical format.

    Examples:

    1
    ->
    GT-000001

    GT-1
    ->
    GT-000001

    ACQ_20
    ->
    AC-000020

    """

    if pd.isna(value):

        return None

    value = str(value).strip()

    if value.lower() in {
        "nan",
        "none",
        "",
    }:

        return None

    # Already normalized

    if re.fullmatch(
        r"(GT|AC)-\d{6}",
        value.upper(),
    ):

        return value.upper()

    digits = re.sub(
        r"\D",
        "",
        value,
    )

    if not digits:

        return None

    # Benefits provider normally follows
    # GlobalTech employee namespace

    return f"GT-{int(digits):06d}"


# ============================================================
# Ensure Columns
# ============================================================


def _ensure_columns(
    df: pd.DataFrame,
    columns: list[str],
):

    df = df.copy()

    for column in columns:

        if column not in df.columns:

            logger.warning(
                "Missing benefits column %s",
                column,
            )

            if column in {
                "premium_employee",
                "premium_employer",
            }:

                df[column] = 0

            else:

                df[column] = None

    return df


# ============================================================
# Deduplicate Benefit Records
# ============================================================


def _deduplicate_benefits(
    df: pd.DataFrame,
):
    """
    Remove duplicate benefit rows.
    """

    before = len(df)

    df = df.drop_duplicates(
        subset=[
            "employee_id",
            "plan_type",
        ],
        keep="last",
    )

    logger.info(
        "Removed benefit duplicates: %s",
        before - len(df),
    )

    return df


# ============================================================
# Main Merge
# ============================================================


def merge_benefits(
    employees: pd.DataFrame,
    benefits: pd.DataFrame,
) -> pd.DataFrame:

    logger.info("Starting benefits enrichment...")

    employees = employees.copy()

    benefits = benefits.copy()

    if benefits.empty:

        logger.info("Benefits dataset empty.")

        return employees

    # --------------------------------------------------------
    # Ensure schema
    # --------------------------------------------------------

    benefits = _ensure_columns(
        benefits,
        [
            "employee_id",
            "plan_type",
            "premium_employee",
            "premium_employer",
        ],
    )

    # --------------------------------------------------------
    # Normalize IDs
    # --------------------------------------------------------

    employees["employee_id"] = employees["employee_id"].apply(normalize_employee_id)

    benefits["employee_id"] = benefits["employee_id"].apply(normalize_employee_id)

    # Remove invalid IDs

    benefits = benefits[benefits["employee_id"].notna()]

    employees = employees[employees["employee_id"].notna()]

    # --------------------------------------------------------
    # Remove employee duplicates before enrichment
    # --------------------------------------------------------

    employee_duplicates = employees["employee_id"].duplicated(keep=False)

    duplicate_count = employee_duplicates.sum()

    if duplicate_count:

        logger.warning(
            "Removing %s duplicate employees before benefits merge",
            duplicate_count,
        )

        employees = employees.sort_values("employee_id").drop_duplicates(
            subset=["employee_id"],
            keep="first",
        )

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    for column in [
        "premium_employee",
        "premium_employer",
    ]:

        benefits[column] = pd.to_numeric(
            benefits[column],
            errors="coerce",
        ).fillna(0)

    # --------------------------------------------------------
    # Remove duplicate benefit rows
    # --------------------------------------------------------

    benefits = _deduplicate_benefits(benefits)

    # --------------------------------------------------------
    # Aggregate benefits
    # --------------------------------------------------------

    aggregated = benefits.groupby(
        "employee_id",
        as_index=False,
    ).agg(
        benefit_plans=(
            "plan_type",
            lambda values: ", ".join(
                sorted(set(str(v).strip() for v in values if pd.notna(v)))
            ),
        ),
        benefit_count=(
            "plan_type",
            "count",
        ),
        total_employee_premium=(
            "premium_employee",
            "sum",
        ),
        total_employer_premium=(
            "premium_employer",
            "sum",
        ),
    )

    aggregated["benefits_matched"] = True

    logger.info(
        "Benefit employees aggregated=%s",
        len(aggregated),
    )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    result = employees.merge(
        aggregated,
        on="employee_id",
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # Defaults
    # --------------------------------------------------------

    result["benefit_count"] = result["benefit_count"].fillna(0).astype(int)

    result["total_employee_premium"] = result["total_employee_premium"].fillna(0)

    result["total_employer_premium"] = result["total_employer_premium"].fillna(0)

    result["benefit_plans"] = result["benefit_plans"].fillna("")

    if "source_systems" not in result.columns:

        result["source_systems"] = ""

    if "dedup_method" not in result.columns:

        result["dedup_method"] = "single_source"

    if "benefits_matched" not in result.columns:

        result["benefits_matched"] = False

    enrolled = result["benefits_matched"].fillna(False).astype(bool)

    def _append_benefits(value: str) -> str:

        parts = [
            part for part in str(value).split(",") if part and part not in {"nan", "None"}
        ]

        if "benefits" not in parts:

            parts.append("benefits")

        return ",".join(parts)

    result.loc[enrolled, "source_systems"] = result.loc[enrolled, "source_systems"].map(
        _append_benefits
    )

    current_method = result.loc[enrolled, "dedup_method"].fillna("single_source")

    result.loc[enrolled, "dedup_method"] = current_method.where(
        current_method.ne("single_source"),
        "exact_id",
    )

    # Final safety

    duplicate_ids = result["employee_id"].duplicated().sum()

    if duplicate_ids:

        logger.error(
            "Benefits merge created %s duplicates",
            duplicate_ids,
        )

        result = result.drop_duplicates(
            subset=["employee_id"],
            keep="first",
        )

    logger.info(
        "Benefits merge complete rows=%s",
        len(result),
    )

    return result.reset_index(drop=True)
