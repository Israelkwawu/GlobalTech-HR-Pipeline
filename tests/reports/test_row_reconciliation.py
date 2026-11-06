"""Tests that every source row has a destination."""

import pandas as pd

from src.deduplicate import deduplicate_employees
from src.pipeline import prepare_golden_dataset
from src.reports.row_reconciliation import assert_rows_balanced, reconcile_rows
from tests.test_deduplicate import (
    benefits_dataframe,
    employee_dataframe,
    payroll_dataframe,
)


def _books(result, golden=None, extra_routed=None):
    ledger = result["row_ledger"]
    routed = ledger["routed"]
    if extra_routed is not None and not extra_routed.empty:
        routed = pd.concat([routed, extra_routed], ignore_index=True)

    detail, summary = reconcile_rows(
        ledger["hris"],
        ledger["payroll"],
        ledger["benefits"],
        golden if golden is not None else result["golden_dataset"],
        routed,
        ledger["payroll_ghost_rows"],
        ledger["benefits_ghost_rows"],
        ledger["id_alias"],
    )
    assert_rows_balanced(detail, ledger["hris"], ledger["payroll"], ledger["benefits"])
    return detail, summary


def test_every_source_row_is_in_the_golden_set_or_a_named_destination():
    employees = pd.concat(
        [employee_dataframe(), employee_dataframe().iloc[[0]]],
        ignore_index=True,
    )

    detail, summary = _books(
        deduplicate_employees(employees, payroll_dataframe(), benefits_dataframe())
    )

    hris = detail.loc[detail["population"].eq("hris"), "disposition"].value_counts()
    payroll = detail.loc[detail["population"].eq("payroll"), "disposition"].value_counts()

    assert hris["in_golden"] == 2
    assert hris["folded_exact_id"] == 1
    assert payroll["payroll_attached"] == 1
    assert payroll["payroll_ghost"] == 1
    assert detail.loc[detail["population"].eq("benefits"), "disposition"].item() == "benefits_attached"
    assert set(summary.loc[summary["disposition"].eq("TOTAL"), "destination"]) == {"balanced"}


def test_duplicate_email_inside_one_company_is_excluded_and_listed():
    employees = employee_dataframe()
    employees["company_origin"] = "GlobalTech"
    employees.loc[1, "email"] = "john@test.com"

    result = deduplicate_employees(
        employees,
        payroll_dataframe().iloc[0:0],
        benefits_dataframe().iloc[0:0],
    )
    routed = []
    golden = prepare_golden_dataset(result["golden_dataset"], routed)
    extra = pd.concat(routed, ignore_index=True)

    detail, _ = _books(result, golden, extra)

    assert len(golden) == 1
    assert (detail["disposition"] == "excluded_duplicate_email").sum() == 1
    assert (detail["disposition"] == "in_golden").sum() == 1


def test_missing_employee_id_is_excluded_instead_of_merged():
    employees = employee_dataframe()
    blank = employees.iloc[[0]].copy()
    blank["employee_id"] = None
    blank["email"] = "blank@test.com"
    employees = pd.concat([employees, blank], ignore_index=True)

    detail, _ = _books(
        deduplicate_employees(
            employees,
            payroll_dataframe().iloc[0:0],
            benefits_dataframe().iloc[0:0],
        )
    )

    missing = detail.loc[detail["disposition"].eq("excluded_missing_employee_id")]
    assert len(missing) == 1
    assert missing.iloc[0]["email"] == "blank@test.com"
    assert (detail["disposition"] == "in_golden").sum() == 2


def test_unaccounted_row_is_listed_and_the_run_continues():
    result = deduplicate_employees(
        employee_dataframe(),
        payroll_dataframe().iloc[0:0],
        benefits_dataframe().iloc[0:0],
    )
    ledger = result["row_ledger"]
    detail, _ = reconcile_rows(
        ledger["hris"],
        ledger["payroll"],
        ledger["benefits"],
        result["golden_dataset"].iloc[0:0],
        ledger["routed"],
        ledger["payroll_ghost_rows"],
        ledger["benefits_ghost_rows"],
        ledger["id_alias"],
    )

    unaccounted = assert_rows_balanced(detail, ledger["hris"], ledger["payroll"], ledger["benefits"])

    assert unaccounted == len(ledger["hris"])
    assert (detail["disposition"] == "unaccounted").all()
