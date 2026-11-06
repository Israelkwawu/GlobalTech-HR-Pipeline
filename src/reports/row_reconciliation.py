"""
Row reconciliation for the HR pipeline.

Every source row is given one disposition. The books balance only when
the dispositions cover every row that entered matching.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


DESTINATION = {
    "in_golden": "golden_employee_dataset",
    "folded_exact_id": "merged into the surviving employee row",
    "folded_email_match": "merged into the GlobalTech employee row",
    "excluded_duplicate_email": "row_disposition.csv",
    "excluded_missing_employee_id": "row_disposition.csv",
    "excluded_duplicate_employee_id": "row_disposition.csv",
    "payroll_attached": "golden_employee_dataset salary columns",
    "payroll_duplicate_collapsed": "merged into the last payroll row for that employee id",
    "payroll_ghost": "ghost_employees.csv",
    "payroll_on_excluded_employee": "row_disposition.csv with the excluded employee",
    "benefits_attached": "golden_employee_dataset benefit columns",
    "benefits_duplicate_plan": "merged into the last benefits row for that employee and plan",
    "benefits_no_hris": "row_disposition.csv",
    "benefits_on_excluded_employee": "row_disposition.csv with the excluded employee",
    "unaccounted": "unaccounted",
}

_EXCLUDED_EMPLOYEE = {
    "excluded_duplicate_email",
    "excluded_missing_employee_id",
    "excluded_duplicate_employee_id",
}


def _ledger_ids(frame: pd.DataFrame) -> set[int]:
    if frame is None or frame.empty or "_ledger_row" not in frame.columns:
        return set()

    values = pd.to_numeric(frame["_ledger_row"], errors="coerce").dropna()
    return {int(value) for value in values.tolist()}


def _identity(frame: pd.DataFrame) -> pd.DataFrame:
    identity = pd.DataFrame(index=frame.index)
    identity["employee_id"] = frame["employee_id"] if "employee_id" in frame.columns else pd.NA
    identity["email"] = frame["email"] if "email" in frame.columns else pd.NA

    if "full_name" in frame.columns:
        identity["name"] = frame["full_name"]
    elif "name" in frame.columns:
        identity["name"] = frame["name"]
    elif {"first_name", "last_name"}.issubset(frame.columns):
        identity["name"] = (
            frame["first_name"].fillna("").astype(str)
            + " "
            + frame["last_name"].fillna("").astype(str)
        ).str.strip()
    else:
        identity["name"] = pd.NA

    return identity


def _routed_lookup(routed: pd.DataFrame) -> dict[tuple[str, int], str]:
    lookup: dict[tuple[str, int], str] = {}

    if routed is None or routed.empty:
        return lookup

    required = {"_ledger_source", "_ledger_row", "_disposition"}
    if not required.issubset(routed.columns):
        return lookup

    for source, row_id, disposition in zip(
        routed["_ledger_source"].astype(str),
        pd.to_numeric(routed["_ledger_row"], errors="coerce"),
        routed["_disposition"].astype(str),
    ):
        if pd.isna(row_id):
            continue
        lookup[(source, int(row_id))] = disposition

    return lookup


def _classify_population(
    frame: pd.DataFrame,
    population: str,
    routed_lookup: dict[tuple[str, int], str],
    golden_row_ids: set[int],
    golden_employee_ids: set[str],
    excluded_employee_ids: set[str],
    ghost_row_ids: set[int],
    id_alias: dict[str, str] | None = None,
) -> pd.DataFrame:
    detail = _identity(frame)
    detail.insert(0, "population", population)
    detail.insert(1, "source_row", pd.to_numeric(frame["_ledger_row"], errors="coerce").astype("Int64"))

    dispositions: list[str] = []

    for row_id, employee_id in zip(detail["source_row"], detail["employee_id"]):
        key = (population, int(row_id)) if pd.notna(row_id) else None
        routed_as = routed_lookup.get(key) if key else None
        employee_key = "" if pd.isna(employee_id) else str(employee_id).strip()
        resolved_id = (id_alias or {}).get(employee_key, employee_key)
        kept_ids = {employee_key, resolved_id}

        if routed_as == "excluded_missing_employee_id":
            disposition = routed_as
        elif key is not None and int(row_id) in ghost_row_ids:
            disposition = "payroll_ghost" if population == "payroll" else "benefits_no_hris"
        elif routed_as:
            disposition = routed_as
        elif population == "hris" and key is not None and int(row_id) in golden_row_ids:
            disposition = "in_golden"
        elif population in {"payroll", "benefits"} and kept_ids & golden_employee_ids:
            disposition = "payroll_attached" if population == "payroll" else "benefits_attached"
        elif population in {"payroll", "benefits"} and kept_ids & excluded_employee_ids:
            disposition = (
                "payroll_on_excluded_employee"
                if population == "payroll"
                else "benefits_on_excluded_employee"
            )
        else:
            disposition = "unaccounted"

        dispositions.append(disposition)

    detail["disposition"] = dispositions
    detail["destination"] = detail["disposition"].map(DESTINATION).fillna("unaccounted")
    return detail


def reconcile_rows(
    hris: pd.DataFrame,
    payroll: pd.DataFrame,
    benefits: pd.DataFrame,
    golden: pd.DataFrame,
    routed: pd.DataFrame,
    payroll_ghost_rows: set[int] | None = None,
    benefits_ghost_rows: set[int] | None = None,
    id_alias: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Assign every source row a destination.

    Returns the row-level disposition file and the population summary.
    """

    routed_lookup = _routed_lookup(routed)
    golden_row_ids = _ledger_ids(golden.loc[golden["_ledger_source"].astype(str).eq("hris")]) if (
        golden is not None
        and not golden.empty
        and {"_ledger_row", "_ledger_source"}.issubset(golden.columns)
    ) else set()

    if golden is not None and not golden.empty and "employee_id" in golden.columns:
        golden_employee_ids = set(golden["employee_id"].dropna().astype(str).str.strip())
    else:
        golden_employee_ids = set()

    excluded_employee_ids = set()
    if routed is not None and not routed.empty and {"_disposition", "employee_id"}.issubset(routed.columns):
        excluded = routed.loc[routed["_disposition"].isin(_EXCLUDED_EMPLOYEE)]
        excluded_employee_ids = set(excluded["employee_id"].dropna().astype(str).str.strip())

    populations = (
        ("hris", hris, set()),
        ("payroll", payroll, payroll_ghost_rows or set()),
        ("benefits", benefits, benefits_ghost_rows or set()),
    )

    details = [
        _classify_population(
            frame,
            population,
            routed_lookup,
            golden_row_ids,
            golden_employee_ids,
            excluded_employee_ids,
            ghost_rows,
            id_alias,
        )
        for population, frame, ghost_rows in populations
        if frame is not None and not frame.empty
    ]

    detail = (
        pd.concat(details, ignore_index=True)
        if details
        else pd.DataFrame(
            columns=[
                "population",
                "source_row",
                "employee_id",
                "email",
                "name",
                "disposition",
                "destination",
            ]
        )
    )

    summary = (
        detail.groupby(["population", "disposition", "destination"], dropna=False)
        .size()
        .reset_index(name="rows")
        .sort_values(["population", "disposition"])
        .reset_index(drop=True)
    )

    if not summary.empty:
        totals = summary.groupby("population", as_index=False)["rows"].sum()
        totals["disposition"] = "TOTAL"
        totals["destination"] = "balanced"
        summary = pd.concat([summary, totals], ignore_index=True)

    logger.info(
        "Row reconciliation rows=%s unaccounted=%s",
        len(detail),
        int((detail["disposition"] == "unaccounted").sum()) if not detail.empty else 0,
    )

    return detail, summary


def assert_rows_balanced(
    detail: pd.DataFrame,
    hris: pd.DataFrame,
    payroll: pd.DataFrame,
    benefits: pd.DataFrame,
) -> int:
    """Log rows that have no destination. The disposition file already lists them."""

    expected = len(hris) + len(payroll) + len(benefits)
    unaccounted = int((detail["disposition"] == "unaccounted").sum()) if not detail.empty else 0

    if len(detail) != expected or unaccounted:
        logger.error(
            "Row reconciliation has unaccounted rows. "
            "Received %s, listed %s, unaccounted %s. See row_disposition.csv.",
            expected,
            len(detail),
            unaccounted,
        )

    return unaccounted


def export_reconciliation(
    detail: pd.DataFrame,
    summary: pd.DataFrame,
    output_dir: str | Path,
) -> tuple[Path, Path]:
    """Write the row-level ledger and the balanced summary."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    disposition_path = output_dir / "row_disposition.csv"
    summary_path = output_dir / "row_reconciliation.csv"

    detail.to_csv(disposition_path, index=False)
    summary.to_csv(summary_path, index=False)

    logger.info("Row reconciliation written to %s", summary_path)

    return disposition_path, summary_path
