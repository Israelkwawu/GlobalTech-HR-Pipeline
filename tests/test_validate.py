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
# Passing Validation
# ============================================================================

def test_valid_employee_dataset_passes():

    df = valid_employee_dataframe()

    result = validate(df)

    assert result["passed"] is True

    assert result["errors"].empty

    assert (
        result["summary"]["failed_records"]
        == 0
    )


# ============================================================================
# Null Validation
# ============================================================================

def test_missing_required_field_fails():

    df = valid_employee_dataframe()

    df.loc[0, "email"] = None

    result = validate(df)

    assert result["passed"] is False

    assert not result["errors"].empty

    assert (
        "NULL_VALUE"
        in result["errors"]["rule"].values
    )


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

    result = validate(df)

    assert result["passed"] is False

    assert (
        "DUPLICATE"
        in result["errors"]["rule"].values
    )


# ============================================================================
# Regex Validation
# ============================================================================

def test_invalid_employee_id_format_fails():

    df = valid_employee_dataframe()

    df.loc[0, "employee_id"] = "12345"

    result = validate(df)

    assert result["passed"] is False

    assert (
        "REGEX_FAILURE"
        in result["errors"]["rule"].values
    )


def test_invalid_email_format_fails():

    df = valid_employee_dataframe()

    df.loc[0, "email"] = "invalid-email"

    result = validate(df)

    assert result["passed"] is False

    assert (
        "REGEX_FAILURE"
        in result["errors"]["rule"].values
    )


# ============================================================================
# Salary Validation
# ============================================================================

def test_salary_below_minimum_fails():

    df = valid_employee_dataframe()

    df.loc[0, "salary_usd_annual"] = 5000

    result = validate(df)

    assert result["passed"] is False

    assert (
        "BELOW_MINIMUM"
            in result["errors"]["rule"].values
    
        or 
            "ABOVE_MAXIMUM"
            in result["errors"]["rule"].values
    )


def test_salary_above_maximum_fails():

    df = valid_employee_dataframe()

    df.loc[0, "salary_usd_annual"] = 5000000

    result = validate(df)

    assert result["passed"] is False

    assert (
        "BELOW_MINIMUM"
            in result["errors"]["rule"].values
    
        or 
            "ABOVE_MAXIMUM"
            in result["errors"]["rule"].values
    )


# ============================================================================
# Referential Validation
# ============================================================================

def test_missing_manager_reference_fails():

    df = valid_employee_dataframe()

    df.loc[0, "manager_id"] = "GT-999999"

    result = validate(df)

    assert result["passed"] is False

    assert (
        "INVALID_REFERENCE"
        in result["errors"]["rule"].values
    )


# ============================================================================
# Empty Dataset
# ============================================================================

def test_empty_dataframe_passes():

    df = pd.DataFrame()

    result = validate(df)

    assert result["passed"] is True

    assert (
        result["summary"]["total_records"]
        == 0
    )

    assert (
        result["summary"]["validation_score"]
        == 100
    )
    
