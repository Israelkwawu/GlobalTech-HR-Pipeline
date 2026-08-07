"""
Unit tests for ReferentialValidator.

Author: Israel Kwawu
"""

import pandas as pd

from src.validators.referential_validator import ReferentialValidator


def test_valid_manager_references():

    df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
                "GT-000003",
            ],
            "manager_id": [
                None,
                "GT-000001",
                "GT-000002",
            ],
        }
    )

    validator = ReferentialValidator(
        source_column="manager_id",
        reference_column="employee_id",
    )

    result = validator.validate(df)

    assert result.empty


def test_invalid_manager_reference():

    df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
            ],
            "manager_id": [
                "GT-999999",
                "GT-000001",
            ],
        }
    )

    validator = ReferentialValidator(
        source_column="manager_id",
        reference_column="employee_id",
    )

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "INVALID_REFERENCE"
    assert result.iloc[0]["column"] == "manager_id"


def test_null_manager_allowed():

    df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
            ],
            "manager_id": [
                None,
                "",
            ],
        }
    )

    validator = ReferentialValidator(
        source_column="manager_id",
        reference_column="employee_id",
    )

    result = validator.validate(df)

    assert result.empty


def test_missing_source_column():

    df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
            ]
        }
    )

    validator = ReferentialValidator(
        source_column="manager_id",
        reference_column="employee_id",
    )

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "MISSING_COLUMN"


def test_missing_reference_column():

    df = pd.DataFrame(
        {
            "manager_id": [
                "GT-000001",
            ]
        }
    )

    validator = ReferentialValidator(
        source_column="manager_id",
        reference_column="employee_id",
    )

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "MISSING_COLUMN"
