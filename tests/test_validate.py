"""
Unit tests for validation pipeline.

Tests:
- Passing dataset
- Null validation failures
- Duplicate detection
- Regex validation
- Salary range validation
- Referential validation

Author: Israel Kwawu
"""

import pandas as pd
import pytest

from src.validate import validate

# ============================================================================
# Fixtures
# ============================================================================


def valid_employee_dataframe():

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
            "department": [
                "Engineering",
                "Finance",
            ],
            "job_title": [
                "Engineer",
                "Analyst",
            ],
            "country": [
                "USA",
                "UK",
            ],
            "employment_type": [
                "Full-Time",
                "Full-Time",
            ],
            "currency": [
                "USD",
                "USD",
            ],
            "hire_date": [
                "2020-01-15",
                "2021-06-01",
            ],
            "salary_usd_annual": [
                80000,
                90000,
            ],
            "manager_id": [
                "GT-000002",
                "GT-000001",
            ],
        }
    )


# ============================================================================
# Helpers
# ============================================================================


def check_status(df, check):
    """Return one check row. The gate allows up to two failed checks."""

    result = validate(df)
    report = result["report"].set_index("check")

    return result, report.loc[check]


def assert_check_failed(df, check):
    result, row = check_status(df, check)

    assert row["status"] == "FAIL"
    assert row["failed"] > 0

    return result


def assert_validation_passed(df):
    """
    Valid datasets should complete successfully.
    """

    result = validate(df)

    assert isinstance(
        result,
        dict,
    )

    assert "summary" in result

    assert result["summary"]["failed_records"] == 0

    return result


# ============================================================================
# Passing Validation
# ============================================================================


def test_valid_employee_dataset_passes():

    df = valid_employee_dataframe()

    result = assert_validation_passed(df)

    assert result["summary"]["validation_score"] == 100


# ============================================================================
# Null Validation
# ============================================================================


def test_missing_required_field_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "email",
    ] = None

    assert_check_failed(df, "email_not_null")


# ============================================================================
# Duplicate Validation
# ============================================================================


def test_duplicate_employee_id_fails():

    df = valid_employee_dataframe()

    duplicate = df.iloc[0].copy()

    df = pd.concat(
        [
            df,
            duplicate.to_frame().T,
        ],
        ignore_index=True,
    )

    assert_check_failed(df, "employee_id_unique")


# ============================================================================
# Regex Validation
# ============================================================================


def test_invalid_employee_id_format_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "employee_id",
    ] = "12345"

    assert_check_failed(df, "employee_id_regex")


def test_invalid_email_format_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "email",
    ] = "invalid-email"

    assert_check_failed(df, "email_regex")


# ============================================================================
# Salary Validation
# ============================================================================


def test_salary_below_minimum_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "salary_usd_annual",
    ] = 5000

    assert_check_failed(df, "salary_range")


def test_salary_above_maximum_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "salary_usd_annual",
    ] = 5000000

    assert_check_failed(df, "salary_range")


# ============================================================================
# Referential Validation
# ============================================================================


def test_missing_manager_reference_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "manager_id",
    ] = "GT-999999"

    assert_check_failed(df, "manager_reference")


def test_null_employee_ids_are_not_duplicates():

    df = valid_employee_dataframe()
    df.loc[0, "employee_id"] = None
    df.loc[1, "employee_id"] = None

    result, row = check_status(df, "employee_id_unique")

    assert row["status"] == "PASS"
    assert result["summary"]["pipeline_passed"] is True


def test_missing_column_does_not_pass():

    df = valid_employee_dataframe().drop(columns=["country"])

    result, row = check_status(df, "country_not_null")

    assert row["status"] == "FAIL"
    assert row["failed"] > 0
    assert row["pass_rate"] < 100


def test_hire_date_before_1970_fails():

    df = valid_employee_dataframe()
    df.loc[0, "hire_date"] = "1969-12-31"

    assert_check_failed(df, "hire_date_range")


def test_hire_date_after_today_fails():

    df = valid_employee_dataframe()
    df.loc[0, "hire_date"] = "2999-01-01"

    assert_check_failed(df, "hire_date_range")


def test_gate_allows_two_failed_checks():

    df = valid_employee_dataframe()
    df.loc[0, "email"] = None
    df.loc[0, "salary_usd_annual"] = 1000

    result = validate(df)

    assert result["summary"]["failed_checks"] <= 2
    assert result["summary"]["pipeline_passed"] is True


def test_gate_halts_after_more_than_two_failed_checks():

    df = valid_employee_dataframe()
    df.loc[0, "email"] = None
    df.loc[0, "salary_usd_annual"] = 1000
    df.loc[0, "manager_id"] = "GT-999999"

    with pytest.raises(RuntimeError, match="Data quality gate failed"):
        validate(df)


# ============================================================================
# Empty Dataset
# ============================================================================


def test_empty_dataframe_passes():

    df = valid_employee_dataframe().iloc[0:0]

    result = validate(df)

    assert isinstance(result, dict)
    assert result["summary"]["total_records"] == 0
    assert result["summary"]["pipeline_passed"] is True
    assert result["summary"]["failed_checks"] == 0
