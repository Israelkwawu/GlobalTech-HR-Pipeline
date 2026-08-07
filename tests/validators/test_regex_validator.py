"""
Unit tests for RegexValidator.

Author: Israel Kwawu
"""

import pandas as pd

from config.constants import (
    EMAIL_REGEX,
    EMPLOYEE_ID_REGEX,
)

from src.validators.regex_validator import RegexValidator


def test_valid_values():

    df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
            ],
            "email": [
                "john@test.com",
            ],
        }
    )

    validator = RegexValidator(
        {
            "employee_id": EMPLOYEE_ID_REGEX,
            "email": EMAIL_REGEX,
        }
    )

    result = validator.validate(df)

    assert result.empty


def test_invalid_email():

    df = pd.DataFrame(
        {
            "email": [
                "bad-email",
            ]
        }
    )

    validator = RegexValidator(
        {
            "email": EMAIL_REGEX,
        }
    )

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "REGEX_FAILURE"
    assert result.iloc[0]["column"] == "email"


def test_invalid_employee_id():

    df = pd.DataFrame(
        {
            "employee_id": [
                "12345",
            ]
        }
    )

    validator = RegexValidator(
        {
            "employee_id": EMPLOYEE_ID_REGEX,
        }
    )

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "REGEX_FAILURE"


def test_missing_column_is_ignored():

    df = pd.DataFrame(
        {
            "name": [
                "John",
            ]
        }
    )

    validator = RegexValidator(
        {
            "email": EMAIL_REGEX,
        }
    )

    result = validator.validate(df)

    assert result.empty


def test_multiple_invalid_rows():

    df = pd.DataFrame(
        {
            "email": [
                "bad",
                "also_bad",
            ]
        }
    )

    validator = RegexValidator(
        {
            "email": EMAIL_REGEX,
        }
    )

    result = validator.validate(df)

    assert len(result) == 2
