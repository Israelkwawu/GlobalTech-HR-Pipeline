"""
Unit tests for deduplication pipeline.

Author: Israel Kwawu
"""

import pandas as pd

from src.deduplicate import deduplicate_employees


def empty_payroll():
    return pd.DataFrame(
        columns=[
            "employee_id",
            "email",
            "full_name",
        ]
    )


def empty_benefits():
    return pd.DataFrame(
        columns=[
            "employee_id",
            "plan_type",
        ]
    )


def test_exact_id_duplicate_removed():

    employee_df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000001",
                "GT-000002",
            ],
            "email": [
                "a@test.com",
                "a@test.com",
                "b@test.com",
            ],
            "first_name": [
                "John",
                "John",
                "Jane",
            ],
            "last_name": [
                "Smith",
                "Smith",
                "Doe",
            ],
        }
    )

    result = deduplicate_employees(
        employee_df,
        empty_payroll(),
        empty_benefits(),
    )

    golden = result["golden_dataset"]

    assert len(golden) == 2


def test_email_duplicate_detection():

    employee_df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "AC-000001",
            ],
            "email": [
                "same@test.com",
                "same@test.com",
            ],
            "first_name": [
                "John",
                "John",
            ],
            "last_name": [
                "Smith",
                "Smith",
            ],
        }
    )

    payroll_df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001"
            ],
            "email": [
                "same@test.com"
            ],
        }
    )


    result = deduplicate_employees(
        employee_df,
        payroll_df,
        empty_benefits(),
    )

    assert isinstance(
        result["email_matches"],
        pd.DataFrame,
    )


def test_unique_records_unchanged():

    employee_df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
            ],
            "email": [
                "a@test.com",
                "b@test.com",
            ],
            "first_name": [
                "John",
                "Jane",
            ],
            "last_name": [
                "Smith",
                "Doe",
            ],
        }
    )

    result = deduplicate_employees(
        employee_df,
        empty_payroll(),
        empty_benefits(),
    )

    golden = result["golden_dataset"]

    assert len(golden) == 2


def test_empty_employee_dataframe():

    employee_df = pd.DataFrame(
        columns=[
            "employee_id",
            "email",
            "first_name",
            "last_name",
        ]
    )

    result = deduplicate_employees(
        employee_df,
        empty_payroll(),
        empty_benefits(),
    )

    assert result["golden_dataset"].empty


def test_missing_optional_columns_does_not_crash():

    employee_df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001"
            ],
            "email": [
                "john@test.com"
            ],
        }
    )

    result = deduplicate_employees(
        employee_df,
        empty_payroll(),
        empty_benefits(),
    )

    assert "golden_dataset" in result


def test_result_contains_all_reports():

    employee_df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001"
            ],
            "email": [
                "john@test.com"
            ],
            "first_name": [
                "John"
            ],
            "last_name": [
                "Smith"
            ],
        }
    )

    result = deduplicate_employees(
        employee_df,
        empty_payroll(),
        empty_benefits(),
    )


    assert set(result.keys()) == {
        "golden_dataset",
        "exact_matches",
        "email_matches",
        "fuzzy_matches",
        "ghost_employees",
    }
    
