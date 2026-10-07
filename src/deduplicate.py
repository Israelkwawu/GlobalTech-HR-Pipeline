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
from src.matching.fuzzy_match import fuzzy_match


from src.matching.ghost_detection import (
    detect_benefits_ghosts,
    detect_payroll_ghosts,
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


def _ensure_row_provenance(df: pd.DataFrame, default_source: str) -> pd.DataFrame:
    """
    Keep the source already stored on each row.

    A combined HRIS frame contains both GlobalTech and AcquiredCo.
    Stamping every row with one source would erase that distinction.
    """

    df = df.copy()

    if "source_systems" not in df.columns or df["source_systems"].fillna("").eq("").all():
        if "source_system" in df.columns:
            df["source_systems"] = df["source_system"].fillna(default_source)
        else:
            df["source_systems"] = default_source

    if "dedup_method" not in df.columns:
        df["dedup_method"] = "single_source"
    else:
        df["dedup_method"] = df["dedup_method"].fillna("single_source")

    return df


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
# Source priority
# ============================================================


_SOURCE_RANK = {
    "globaltech_hris": 0,
    "acquiredco_hris": 0,
    "payroll": 1,
    "benefits": 2,
}


def _source_rank(value) -> int:
    """Lower rank wins. HRIS outranks payroll, which outranks benefits."""

    if pd.isna(value):
        return 99

    ranks = [
        _SOURCE_RANK[part.strip()]
        for part in str(value).split(",")
        if part.strip() in _SOURCE_RANK
    ]

    return min(ranks) if ranks else 99


def _union_sources(values) -> str:
    parts: list[str] = []

    for value in values:
        if pd.isna(value):
            continue

        for part in str(value).split(","):
            part = part.strip()

            if part and part not in {"nan", "None"} and part not in parts:
                parts.append(part)

    return ",".join(parts)


def _is_blank(value) -> bool:
    if pd.isna(value):
        return True

    return str(value).strip().lower() in {"", "nan", "none", "<na>"}


def _collapse_group(
    group: pd.DataFrame,
    method: str | None,
) -> pd.Series:
    """
    Keep the highest-priority row and fill gaps from the rest.

    HRIS identity wins over payroll and benefits. GlobalTech wins a
    tie between the two HRIS systems because payroll migration targets
    the GlobalTech platform.
    """

    ranked = group.copy()
    ranked["_priority"] = ranked.get(
        "source_systems",
        pd.Series("", index=ranked.index),
    ).map(_source_rank)

    if "company_origin" in ranked.columns:
        ranked["_origin_rank"] = (
            ranked["company_origin"]
            .map({"GlobalTech": 0, "AcquiredCo": 1})
            .fillna(2)
        )
    else:
        ranked["_origin_rank"] = 0

    ranked["_missing"] = ranked.isna().sum(axis=1)
    ranked = ranked.sort_values(["_priority", "_origin_rank", "_missing"])
    survivor = ranked.iloc[0].copy()

    for _, row in ranked.iloc[1:].iterrows():
        for column in ranked.columns:
            if str(column).startswith("_"):
                continue

            if column in {"source_systems", "dedup_method"}:
                continue

            if _is_blank(survivor[column]) and not _is_blank(row[column]):
                survivor[column] = row[column]

    if "source_systems" in ranked.columns:
        survivor["source_systems"] = _union_sources(ranked["source_systems"])

    if method and len(ranked) > 1:
        survivor["dedup_method"] = method

    return survivor.drop(labels=[c for c in survivor.index if str(c).startswith("_")])


def _collapse_by_employee_id(df: pd.DataFrame) -> pd.DataFrame:
    """Pass 1. Same namespaced id is one employee. HRIS fields survive."""

    if df.empty or "employee_id" not in df.columns:
        return df

    before = len(df)
    collapsed = [
        _collapse_group(group, "exact_id" if len(group) > 1 else None)
        for _, group in df.groupby("employee_id", dropna=False, sort=False)
    ]
    result = pd.DataFrame(collapsed).reset_index(drop=True)

    logger.info("Exact-id rows before=%s after=%s", before, len(result))

    return result


def _email_key(series: pd.Series) -> pd.Series:
    key = series.astype("string").str.strip().str.lower()
    return key.mask(key.isin(["", "nan", "none", "<na>", "nat"]))


def _collapse_cross_company_email(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    """
    Pass 2. The same email at GlobalTech and AcquiredCo is one person.

    The GlobalTech id is kept. The AcquiredCo id is remapped so later
    payroll and benefits rows still attach to the surviving employee.
    """

    empty_matches = pd.DataFrame(
        columns=["email", "record_1_id", "record_2_id", "match_method"]
    )

    if df.empty or "email" not in df.columns:
        return df, empty_matches, {}

    work = df.copy()
    work["_email_key"] = _email_key(work["email"])
    kept = [work[work["_email_key"].isna()]]
    matches = []
    alias: dict[str, str] = {}

    keyed = work.dropna(subset=["_email_key"])

    for email, group in keyed.groupby("_email_key", sort=False):
        origins = set(group.get("company_origin", pd.Series(dtype=str)).astype(str))
        cross_company = "GlobalTech" in origins and "AcquiredCo" in origins

        if len(group) > 1 and cross_company:
            survivor = _collapse_group(group.drop(columns=["_email_key"]), "email_match")
            survivor_id = str(survivor["employee_id"])

            for employee_id in group["employee_id"].dropna().astype(str):
                if employee_id != survivor_id:
                    alias[employee_id] = survivor_id

            ids = [str(value) for value in group["employee_id"].dropna().tolist()]

            if len(ids) >= 2:
                matches.append(
                    {
                        "email": email,
                        "record_1_id": ids[0],
                        "record_2_id": ids[1],
                        "match_method": "email_match",
                    }
                )

            kept.append(pd.DataFrame([survivor]))
        else:
            kept.append(group.drop(columns=["_email_key"]))

    result = pd.concat(kept, ignore_index=True) if kept else df.iloc[0:0]

    if "_email_key" in result.columns:
        result = result.drop(columns=["_email_key"])

    match_frame = pd.DataFrame(matches) if matches else empty_matches

    logger.info("Cross-company email collapses=%s", len(match_frame))

    return result.reset_index(drop=True), match_frame, alias


def _apply_id_alias(df: pd.DataFrame, alias: dict[str, str]) -> pd.DataFrame:
    if df.empty or not alias or "employee_id" not in df.columns:
        return df

    df = df.copy()
    df["employee_id"] = df["employee_id"].astype("string").replace(alias)
    return df


def _flag_probable_matches(
    golden: pd.DataFrame,
    review: pd.DataFrame,
) -> pd.DataFrame:
    """Pass 3 flags pairs for HR. It does not merge them."""

    golden = golden.copy()
    golden["probable_match"] = False

    if review.empty:
        return golden

    flagged = set(review["record_1_id"].dropna().astype(str)) | set(
        review["record_2_id"].dropna().astype(str)
    )
    mask = golden["employee_id"].astype(str).isin(flagged)
    golden.loc[mask, "probable_match"] = True

    method = golden["dedup_method"].fillna("single_source")
    golden.loc[mask, "dedup_method"] = method.where(method.ne("single_source"), "fuzzy_name")

    return golden


# ============================================================
# MAIN
# ============================================================


def deduplicate_employees(
    employee_df,
    payroll_df,
    benefits_df,
):

    logger.info("Deduplication start")

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

    employees = _ensure_row_provenance(employees, "globaltech_hris")
    payroll = _ensure_row_provenance(payroll, "payroll")
    benefits = _ensure_row_provenance(benefits, "benefits")

    logger.info(
        "Dedup sources employees=%s payroll=%s benefits=%s",
        len(employees),
        len(payroll),
        len(benefits),
    )

    # --------------------------------------------------------
    # PASS 1
    # Exact ID match, HRIS > Payroll > Benefits
    # --------------------------------------------------------

    employees = _collapse_by_employee_id(employees)

    exact_matches = exact_employee_match(
        employees,
        payroll,
    )

    # --------------------------------------------------------
    # PASS 2
    # Cross-company email match, applied to the golden population
    # --------------------------------------------------------

    employees, email_matches, id_alias = _collapse_cross_company_email(employees)

    payroll = _apply_id_alias(payroll, id_alias)
    benefits = _apply_id_alias(benefits, id_alias)

    # --------------------------------------------------------
    # Ghost employees
    # Salary is converted inside detection, and ghosts stay
    # out of the golden dataset.
    # --------------------------------------------------------

    payroll_ghosts = detect_payroll_ghosts(
        employees,
        payroll,
    )

    benefits_ghosts = detect_benefits_ghosts(
        employees,
        benefits,
    )

    if not benefits_ghosts.empty:
        logger.warning(
            "Benefits rows with no HRIS match=%s. They stay out of the payroll ghost report.",
            len(benefits_ghosts),
        )

    ghosts = payroll_ghosts

    # --------------------------------------------------------
    # Enrich, then collapse any remaining exact ids
    # --------------------------------------------------------

    golden_dataset = merge_payroll(
        employees,
        payroll,
    )

    golden_dataset = merge_benefits(
        golden_dataset,
        benefits,
    )

    golden_dataset = _collapse_by_employee_id(golden_dataset)

    # --------------------------------------------------------
    # PASS 3
    # Fuzzy name + hire date. Flag only. Do not merge.
    # --------------------------------------------------------

    fuzzy_matches = fuzzy_match(
        golden_dataset,
        golden_dataset,
    )

    golden_dataset = _flag_probable_matches(
        golden_dataset,
        fuzzy_matches,
    )

    duplicate_ids = golden_dataset["employee_id"].duplicated().sum()

    if duplicate_ids:

        raise RuntimeError(f"Golden dataset duplicate IDs={duplicate_ids}")

    salary_populated = (
        int(golden_dataset["salary"].notna().sum())
        if "salary" in golden_dataset.columns
        else 0
    )

    logger.info(
        "Golden dataset ready rows=%s unique=%s salary=%s",
        len(golden_dataset),
        golden_dataset["employee_id"].nunique(),
        salary_populated,
    )

    return {
        "golden_dataset": golden_dataset,
        "exact_matches": exact_matches,
        "email_matches": email_matches,
        "fuzzy_matches": fuzzy_matches,
        "ghost_employees": ghosts,
    }
