"""
Unit tests for UniquenessValidator.

Author: Israel Kwawu
"""

import pandas as pd

from src.validators.uniqueness_validator import UniquenessValidator


def test_unique_employee_ids():

    df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
                "GT-000003",
            ]
        }
    )

    validator = UniquenessValidator(
        columns=["employee_id"],
    )

    result = validator.validate(df)

    assert result.empty


def test_duplicate_employee_ids():

    df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000001",
                "GT-000002",
            ]
        }
    )

    validator = UniquenessValidator(
        columns=["employee_id"],
    )

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "DUPLICATE"
    assert result.iloc[0]["column"] == "employee_id"


def test_duplicate_emails():

    df = pd.DataFrame(
        {
            "email": [
                "john@test.com",
                "john@test.com",
                "mary@test.com",
            ]
        }
    )

    validator = UniquenessValidator(
        columns=["email"],
    )

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "DUPLICATE"
    assert result.iloc[0]["column"] == "email"


def test_multiple_unique_columns():

    df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
            ],
            "email": [
                "a@test.com",
                "b@test.com",
            ],
        }
    )

    validator = UniquenessValidator(
        columns=[
            "employee_id",
            "email",
        ],
    )

    result = validator.validate(df)

    assert result.empty


def test_missing_column():

    df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
            ]
        }
    )

    validator = UniquenessValidator(
        columns=[
            "email",
        ],
    )

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "MISSING_COLUMN"


def test_null_values_not_duplicates():

    df = pd.DataFrame(
        {
            "email": [
                None,
                None,
                "john@test.com",
            ]
        }
    )

    validator = UniquenessValidator(
        columns=["email"],
    )

    result = validator.validate(df)

    # pandas duplicated() ignores NaN for uniqueness checks
    assert result.empty
