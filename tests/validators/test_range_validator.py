"""
Unit tests for RangeValidator.

Author: Israel Kwawu
"""

import pandas as pd

from src.validators.range_validator import RangeValidator


def test_values_within_range():

    df = pd.DataFrame(
        {
            "salary": [
                20000,
                50000,
                100000,
            ]
        }
    )

    validator = RangeValidator(
        column="salary",
        minimum=15000,
        maximum=200000,
    )

    result = validator.validate(df)

    assert result.empty


def test_salary_below_minimum():

    df = pd.DataFrame(
        {
            "salary": [
                1000,
            ]
        }
    )

    validator = RangeValidator(
        column="salary",
        minimum=15000,
        maximum=200000,
    )

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "BELOW_MINIMUM"


def test_salary_above_maximum():

    df = pd.DataFrame(
        {
            "salary": [
                5000000,
            ]
        }
    )

    validator = RangeValidator(
        column="salary",
        minimum=15000,
        maximum=200000,
    )

    result = validator.validate(df)

    assert len(result) == 1
    assert result.iloc[0]["rule"] == "ABOVE_MAXIMUM"


def test_null_salary_is_ignored():

    df = pd.DataFrame(
        {
            "salary": [
                None,
            ]
        }
    )

    validator = RangeValidator(
        column="salary",
        minimum=15000,
        maximum=200000,
    )

    result = validator.validate(df)

    assert result.empty


def test_missing_column():

    df = pd.DataFrame(
        {
            "email": [
                "a@test.com",
            ]
        }
    )

    validator = RangeValidator(
        column="salary",
        minimum=15000,
        maximum=200000,
    )

    result = validator.validate(df)

    assert result.empty


def test_multiple_invalid_values():

    df = pd.DataFrame(
        {
            "salary": [
                1000,
                5000000,
                50000,
            ]
        }
    )

    validator = RangeValidator(
        column="salary",
        minimum=15000,
        maximum=200000,
    )

    result = validator.validate(df)

    assert len(result) == 2

    assert set(result["rule"]) == {
        "BELOW_MINIMUM",
        "ABOVE_MAXIMUM",
    }
    
