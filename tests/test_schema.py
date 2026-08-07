"""
Tests for employee schema definitions.

Validates:
- Required fields
- Column definitions
- Data types
- Schema behavior

Author: Israel Kwawu
"""

import pandas as pd
import pytest

from src.models.employee_schema import (
    EMPLOYEE_COLUMNS,
    EMPLOYEE_DTYPES,
    REQUIRED_FIELDS,
    OPTIONAL_FIELDS,
    PRIMARY_KEY,
    EMPLOYEE_SCHEMA,
)

from src.models.schema import SchemaValidationError

# ============================================================================
# Schema Definition Tests
# ============================================================================


def test_employee_columns_exist():
    """
    Ensure all expected employee columns are defined.
    """

    expected_columns = [
        "employee_id",
        "first_name",
        "last_name",
        "email",
        "department",
        "country",
        "employment_type",
        "hire_date",
        "salary",
        "currency",
        "salary_usd_annual",
        "manager_id",
        "company_origin",
        "source_systems",
        "dedup_method",
    ]

    for column in expected_columns:
        assert column in EMPLOYEE_COLUMNS


def test_employee_columns_are_unique():
    """
    Ensure schema does not contain duplicate columns.
    """

    assert len(EMPLOYEE_COLUMNS) == len(set(EMPLOYEE_COLUMNS))


def test_required_fields_are_in_columns():
    """
    Required fields must exist in schema columns.
    """

    for field in REQUIRED_FIELDS:
        assert field in EMPLOYEE_COLUMNS


def test_optional_fields_are_in_columns():
    """
    Optional fields must exist in schema columns.
    """

    for field in OPTIONAL_FIELDS:
        assert field in EMPLOYEE_COLUMNS


def test_primary_key_exists():
    """
    Employee ID should be the primary key.
    """

    assert PRIMARY_KEY == "employee_id"

    assert PRIMARY_KEY in EMPLOYEE_COLUMNS


def test_all_columns_have_dtype_definition():
    """
    Every employee column should have a dtype definition.
    """

    for column in EMPLOYEE_COLUMNS:
        assert column in EMPLOYEE_DTYPES


# ============================================================================
# Schema Object Tests
# ============================================================================


def test_schema_accepts_valid_dataframe():
    """
    Valid employee dataframe should pass schema validation.
    """

    df = pd.DataFrame(
        {
            "employee_id": pd.Series(
                ["GT-001042"],
                dtype="string",
            ),
            "first_name": pd.Series(
                ["John"],
                dtype="string",
            ),
            "last_name": pd.Series(
                ["Smith"],
                dtype="string",
            ),
            "email": pd.Series(
                ["john@globaltech.com"],
                dtype="string",
            ),
            "department": pd.Series(
                ["Engineering"],
                dtype="string",
            ),
            "country": pd.Series(
                ["USA"],
                dtype="string",
            ),
        }
    )

    EMPLOYEE_SCHEMA.validate_columns(df)


def test_schema_rejects_missing_required_fields():
    """
    Missing required fields should raise an error.
    """

    df = pd.DataFrame({"employee_id": ["GT-001042"]})

    with pytest.raises(SchemaValidationError):
        EMPLOYEE_SCHEMA.validate_columns(df)


def test_schema_adds_optional_columns():
    """
    Missing optional columns should be added.
    """

    df = pd.DataFrame(
        {
            "employee_id": ["GT-001042"],
            "first_name": ["John"],
            "last_name": ["Smith"],
            "email": ["john@test.com"],
            "department": ["Engineering"],
            "country": ["USA"],
        }
    )

    result = EMPLOYEE_SCHEMA.add_missing_optional_columns(df)

    assert "salary" in result.columns
    assert "manager_id" in result.columns
