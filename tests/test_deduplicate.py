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


def test_email_match_detects_same_employee():

    result = deduplicate_employees(
        employee_dataframe(),
        payroll_dataframe(),
        benefits_dataframe(),
    )

    matches = result["email_matches"]

    assert not matches.empty
