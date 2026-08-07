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
            "country": [
                "USA",
                "UK",
            ],
            "employment_type": [
                "Full-Time",
                "Full-Time",
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


def assert_validation_failed(df):
    """
    Current pipeline behavior:
    invalid data raises RuntimeError.
    """

    with pytest.raises(
        RuntimeError,
        match="Data quality gate failed",
    ):

        validate(df)


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

    assert_validation_failed(df)


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

    assert_validation_failed(df)


# ============================================================================
# Regex Validation
# ============================================================================


def test_invalid_employee_id_format_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "employee_id",
    ] = "12345"

    assert_validation_failed(df)


def test_invalid_email_format_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "email",
    ] = "invalid-email"

    assert_validation_failed(df)


# ============================================================================
# Salary Validation
# ============================================================================


def test_salary_below_minimum_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "salary_usd_annual",
    ] = 5000

    assert_validation_failed(df)


def test_salary_above_maximum_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "salary_usd_annual",
    ] = 5000000

    assert_validation_failed(df)


# ============================================================================
# Referential Validation
# ============================================================================


def test_missing_manager_reference_fails():

    df = valid_employee_dataframe()

    df.loc[
        0,
        "manager_id",
    ] = "GT-999999"

    assert_validation_failed(df)


# ============================================================================
# Empty Dataset
# ============================================================================


def test_empty_dataframe_passes():

    df = pd.DataFrame()

    result = validate(df)

    assert isinstance(
        result,
        dict,
    )

    assert result["summary"]["total_records"] == 0

    assert result["summary"]["validation_score"] == 100
