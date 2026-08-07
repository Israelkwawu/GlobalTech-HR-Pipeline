"""
Unit tests for NullValidator.

Author: Israel Kwawu
"""

import pandas as pd

from src.validators.null_validator import NullValidator


def test_no_null_values():

    df = pd.DataFrame(
        {
            "email": [
                "a@test.com",
                "b@test.com",
            ]
        }
    )

    validator = NullValidator(["email"])

    result = validator.validate(df)

    assert result.empty


def test_detect_null_value():

    df = pd.DataFrame(
        {
            "email": [
                "a@test.com",
                None,
            ]
        }
    )

    validator = NullValidator(["email"])

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "NULL_VALUE"
    assert result.iloc[0]["column"] == "email"


def test_detect_blank_string():

    df = pd.DataFrame(
        {
            "email": [
                "",
            ]
        }
    )

    validator = NullValidator(["email"])

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "NULL_VALUE"


def test_missing_required_column():

    df = pd.DataFrame({"name": ["John"]})

    validator = NullValidator(["email"])

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "NULL_VALUE"


def test_multiple_required_columns():

    df = pd.DataFrame(
        {
            "email": [
                None,
            ],
            "department": [
                "",
            ],
        }
    )

    validator = NullValidator(
        [
            "email",
            "department",
        ]
    )

    result = validator.validate(df)

    assert len(result) == 2
