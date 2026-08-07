"""
Employee deduplication engine.

Responsibilities
----------------
- Resolve duplicate employee identities
- Apply multi-pass matching
- Preserve employee namespaces
- Merge payroll and benefits
- Detect ghost employees
- Create golden employee dataset

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


from src.enrichment.payroll_merge import (
    merge_payroll,
)


from src.enrichment.benefits_merge import (
    merge_benefits,
)

logger = get_logger(__name__)


# ============================================================
# Company Origin
# ============================================================


def _ensure_company_origin(
    df: pd.DataFrame,
    default: str,
):

    df = df.copy()

    if "company_origin" not in df.columns:

        if "source_system" in df.columns:

            df["company_origin"] = (
                df["source_system"]
                .map(
                    {
                        "globaltech_hris": "GlobalTech",
                        "acquiredco_hris": "AcquiredCo",
                        "payroll": default,
                        "benefits": default,
                    }
                )
                .fillna(default)
            )

        else:

            df["company_origin"] = default

    return df


# ============================================================
# Namespace IDs
# ============================================================


def _namespace_ids(
    df: pd.DataFrame,
):

    df = df.copy()

    if "employee_id" not in df.columns:

        return df

    def normalize(row):

        value = row["employee_id"]

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

        digits = "".join(c for c in value if c.isdigit())

        if not digits:

            return value

        company = str(
            row.get(
                "company_origin",
                "",
            )
        ).lower()

        if "acquired" in company:

            prefix = "AC"

        else:

            prefix = "GT"

        return f"{prefix}-" f"{int(digits):06d}"

    df["employee_id"] = df.apply(
        normalize,
        axis=1,
    )

    return df


# ============================================================
# Names
# ============================================================


def _ensure_full_name(
    df: pd.DataFrame,
):

    df = df.copy()

    if "full_name" not in df.columns:

        if {
            "first_name",
            "last_name",
        }.issubset(df.columns):

            df["full_name"] = (
                df["first_name"].fillna("").astype(str)
                + " "
                + df["last_name"].fillna("").astype(str)
            ).str.strip()

    return df


# ============================================================
# Prepare Source
# ============================================================


def _prepare_source(
    df: pd.DataFrame,
    source: str,
):

    df = df.copy()

    if source == "employee":

        df = _ensure_company_origin(
            df,
            "Unknown",
        )

    elif source == "payroll":

        df = _ensure_company_origin(
            df,
            "GlobalTech",
        )

    elif source == "benefits":

        df = _ensure_company_origin(
            df,
            "GlobalTech",
        )

    df = _namespace_ids(df)

    df = _ensure_full_name(df)

    return df


# ============================================================
# Source Priority
# ============================================================


def _add_provenance(
    df,
    source,
):

    df = df.copy()

    if "source_systems" not in df.columns:

        df["source_systems"] = ""

    df["source_systems"] = df["source_systems"].fillna("").astype(str)

    df["source_systems"] = df["source_systems"].apply(
        lambda x: x if source in x else f"{x},{source}".strip(",")
    )

    if "dedup_method" not in df.columns:

        df["dedup_method"] = "single_source"

    return df


# ============================================================
# Deduplicate Master
# ============================================================


def _deduplicate_master(
    df,
):

    before = len(df)

    duplicates = df.duplicated(
        subset=["employee_id"],
        keep=False,
    )

    count = int(duplicates.sum())

    if count:

        logger.warning(
            """
Employee duplicates detected.

Rows:
%s

Resolving by employee namespace.
""",
            count,
        )

        df = df.sort_values(by=["employee_id"]).drop_duplicates(
            subset=["employee_id"],
            keep="first",
        )

    logger.info(
        "Employee rows before=%s after=%s",
        before,
        len(df),
    )

    return df


# ============================================================
# MAIN
# ============================================================


def deduplicate_employees(
    employee_df,
    payroll_df,
    benefits_df,
):

    logger.info("===== DEDUPLICATION START =====")

    employees = _prepare_source(
        employee_df,
        "employee",
    )

    payroll = _prepare_source(
        payroll_df,
        "payroll",
    )

    benefits = _prepare_source(
        benefits_df,
        "benefits",
    )

    employees = _add_provenance(
        employees,
        "globaltech_hris",
    )

    payroll = _add_provenance(
        payroll,
        "payroll",
    )

    benefits = _add_provenance(
        benefits,
        "benefits",
    )

    logger.info(
        """
SOURCE COUNTS

Employees:
%s

Payroll:
%s

Benefits:
%s
""",
        len(employees),
        len(payroll),
        len(benefits),
    )

    # --------------------------------------------------------
    # PASS 1
    # Exact ID match
    # --------------------------------------------------------

    exact_matches = exact_employee_match(
        employees,
        payroll,
    )

    # --------------------------------------------------------
    # PASS 2
    # Email match
    # --------------------------------------------------------

    email_matches = email_match(
        employees,
        payroll,
    )

    # --------------------------------------------------------
    # PASS 3
    # Fuzzy match
    # --------------------------------------------------------

    fuzzy_matches = fuzzy_match(
        employees,
        payroll,
    )

    # --------------------------------------------------------
    # Ghost employees
    # --------------------------------------------------------

    payroll_ghosts = detect_payroll_ghosts(
        employees,
        payroll,
    )

    benefits_ghosts = detect_benefits_ghosts(
        employees,
        benefits,
    )

    ghosts = combine_ghost_reports(
        payroll_ghosts,
        benefits_ghosts,
    )

    # --------------------------------------------------------
    # Build golden employee
    # --------------------------------------------------------

    employees = _deduplicate_master(employees)

    golden_dataset = merge_payroll(
        employees,
        payroll,
    )

    golden_dataset = merge_benefits(
        golden_dataset,
        benefits,
    )

    golden_dataset = _deduplicate_master(golden_dataset)

    duplicate_ids = golden_dataset["employee_id"].duplicated().sum()

    if duplicate_ids:

        raise RuntimeError(f"Golden dataset duplicate IDs={duplicate_ids}")

    logger.info(
        """
===== GOLDEN DATASET READY =====

Rows:
%s

Unique employees:
%s

Salary populated:
%s

================================
""",
        len(golden_dataset),
        golden_dataset["employee_id"].nunique(),
        (
            golden_dataset["salary"].notna().sum()
            if "salary" in golden_dataset.columns
            else 0
        ),
    )

    return {
        "golden_dataset": golden_dataset,
        "exact_matches": exact_matches,
        "email_matches": email_matches,
        "fuzzy_matches": fuzzy_matches,
        "ghost_employees": ghosts,
    }
