import pandas as pd
import pytest


from src.transformers.salary import (
    clean_salary,
    normalize_frequency,
    annual_multiplier,
    calculate_annual_salary,
    calculate_salary_usd,
    normalize_salary_columns,
)

from config.constants import (
    MONTHLY,
    BI_WEEKLY,
    ANNUAL,
)


# ------------------------------
# Salary parsing
# ------------------------------


def test_clean_salary_currency():

    assert clean_salary(
        "$85,000"
    ) == 85000.0


def test_clean_salary_number():

    assert clean_salary(
        50000
    ) == 50000.0


def test_clean_salary_empty():

    assert clean_salary(
        None
    ) is None


# ------------------------------
# Frequency
# ------------------------------


def test_normalize_frequency():
    assert normalize_frequency("Monthly") == MONTHLY


def test_normalize_frequency_yearly():
    assert normalize_frequency("Yearly") == ANNUAL


def test_normalize_frequency_biweekly():
    assert normalize_frequency("biweekly") == BI_WEEKLY


def test_monthly_multiplier():

    assert annual_multiplier(
        "Monthly"
    ) == 12


def test_biweekly_multiplier():

    assert annual_multiplier(
        "Bi-Weekly"
    ) == 26


def test_invalid_frequency():

    with pytest.raises(ValueError):

        annual_multiplier(
            "Unknown"
        )


# ------------------------------
# Annual salary
# ------------------------------


def test_calculate_annual_salary():

    assert calculate_annual_salary(
        5000,
        "Monthly",
    ) == 60000


# ------------------------------
# Currency conversion
# ------------------------------


def test_salary_usd_conversion():

    result = calculate_salary_usd(
        "$1000",
        "EUR",
        "Monthly",
    )

    assert result == 12960.0


# ------------------------------
# DataFrame transformation
# ------------------------------


def test_normalize_salary_dataframe():

    df = pd.DataFrame(
        {
            "salary": [
                "$1000",
                "50000",
            ],
            "currency": [
                "USD",
                "GBP",
            ],
            "pay_frequency": [
                "Monthly",
                "Annual",
            ],
        }
    )


    result = normalize_salary_columns(df)


    assert (
        "salary_usd_annual"
        in result.columns
    )


    assert result.loc[
        0,
        "salary_usd_annual"
    ] == 12000


def test_missing_salary_columns():

    df = pd.DataFrame(
        {
            "salary": [1000]
        }
    )


    with pytest.raises(KeyError):

        normalize_salary_columns(df)
        
