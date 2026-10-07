"""
Tests for employee deduplication engine.

Author: Israel Kwawu
"""

import pandas as pd

from src.deduplicate import deduplicate_employees

# ============================================================================
# Fixtures
# ============================================================================


def employee_dataframe():

    return pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
            ],
            "first_name": [
                "John",
                "Jane",
            ],
            "last_name": [
                "Smith",
                "Doe",
            ],
            "email": [
                "john@test.com",
                "jane@test.com",
            ],
            "full_name": [
                "John Smith",
                "Jane Doe",
            ],
            "department": [
                "Engineering",
                "Finance",
            ],
            "country": [
                "USA",
                "UK",
            ],
            "employment_type": [
                "Full-Time",
                "Full-Time",
            ],
            "source_system": [
                "globaltech_hris",
                "globaltech_hris",
            ],
        }
    )


def payroll_dataframe():

    return pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000003",
            ],
            "email": [
                "john@test.com",
                "ghost@test.com",
            ],
            "full_name": [
                "John Smith",
                "Ghost User",
            ],
            # Required by merge_payroll()
            "salary": [
                85000,
                60000,
            ],
            "currency": [
                "USD",
                "USD",
            ],
            "pay_frequency": [
                "Annual",
                "Annual",
            ],
            "source_system": [
                "payroll",
                "payroll",
            ],
        }
    )


def benefits_dataframe():

    return pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
            ],
            "benefit_plans": [
                "Health Insurance",
            ],
            "source_system": [
                "benefits",
            ],
        }
    )


# ============================================================================
# Tests
# ============================================================================


def test_deduplicate_returns_expected_keys():

    result = deduplicate_employees(
        employee_dataframe(),
        payroll_dataframe(),
        benefits_dataframe(),
    )

    assert "golden_dataset" in result

    assert "exact_matches" in result

    assert "email_matches" in result

    assert "fuzzy_matches" in result

    assert "ghost_employees" in result


def test_golden_dataset_removes_duplicate_employee_ids():

    df = pd.concat(
        [
            employee_dataframe(),
            employee_dataframe().iloc[[0]],
        ],
        ignore_index=True,
    )

    result = deduplicate_employees(
        df,
        payroll_dataframe(),
        benefits_dataframe(),
    )

    golden = result["golden_dataset"]

    assert golden["employee_id"].duplicated().sum() == 0


def test_email_match_collapses_cross_company_employee():

    employees = employee_dataframe()
    employees["company_origin"] = ["GlobalTech", "AcquiredCo"]
    employees.loc[1, "employee_id"] = "AC-000002"
    employees.loc[1, "source_system"] = "acquiredco_hris"
    employees.loc[1, "email"] = "john@test.com"

    result = deduplicate_employees(
        employees,
        payroll_dataframe().iloc[0:0],
        benefits_dataframe().iloc[0:0],
    )

    golden = result["golden_dataset"]

    assert len(golden) == 1
    assert golden.iloc[0]["employee_id"] == "GT-000001"
    assert golden.iloc[0]["dedup_method"] == "email_match"
    assert not result["email_matches"].empty


def test_exact_id_keeps_hris_over_payroll_identity():

    employees = employee_dataframe().iloc[[0]].copy()
    employees["company_origin"] = "GlobalTech"
    employees["first_name"] = "Ada"

    payroll = payroll_dataframe().iloc[[0]].copy()
    payroll["company_origin"] = "AcquiredCo"
    payroll["first_name"] = "Payroll"

    result = deduplicate_employees(
        employees,
        payroll,
        benefits_dataframe().iloc[0:0],
    )

    golden = result["golden_dataset"]
    row = golden.loc[golden["employee_id"].eq("GT-000001")].iloc[0]

    assert row["company_origin"] == "GlobalTech"
    assert row["first_name"] == "Ada"
    assert row["dedup_method"] == "exact_id"
    assert "payroll" in str(row["source_systems"])


def test_fuzzy_review_does_not_merge_records():

    employees = employee_dataframe()
    employees["company_origin"] = ["GlobalTech", "AcquiredCo"]
    employees["hire_date"] = ["2020-01-10", "2020-01-20"]
    employees.loc[1, "company_origin"] = "AcquiredCo"
    employees.loc[1, "employee_id"] = "AC-000050"
    employees.loc[1, "source_system"] = "acquiredco_hris"
    employees.loc[1, "full_name"] = "John Smyth"
    employees.loc[1, "first_name"] = "John"
    employees.loc[1, "last_name"] = "Smyth"
    employees.loc[1, "email"] = "different@test.com"

    result = deduplicate_employees(
        employees,
        payroll_dataframe().iloc[0:0],
        benefits_dataframe().iloc[0:0],
    )

    golden = result["golden_dataset"]
    review = result["fuzzy_matches"]

    assert len(golden) == 2
    assert golden["probable_match"].all()
    assert set(review["match_method"]) == {"fuzzy_name"}
    assert {"record_1_id", "record_2_id", "hire_date_diff_days", "recommended_action"} <= set(
        review.columns
    )


def test_payroll_ghost_report_has_required_fields():

    result = deduplicate_employees(
        employee_dataframe(),
        payroll_dataframe(),
        benefits_dataframe(),
    )

    ghosts = result["ghost_employees"]
    payroll_ghosts = ghosts[ghosts["employee_id"].eq("GT-000003")]

    assert len(payroll_ghosts) == 1
    assert payroll_ghosts.iloc[0]["payroll_employee_id"] == "GT-000003"
    assert payroll_ghosts.iloc[0]["ghost_flag_reason"]
    assert payroll_ghosts.iloc[0]["salary_usd_annual"] == 60000
