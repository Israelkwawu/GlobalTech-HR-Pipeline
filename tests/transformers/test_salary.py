"""
Salary transformer tests.

Author: Israel Kwawu
"""

import pandas as pd

from src.transformers.salary import (
    clean_salary,
    annualize_salary,
    convert_to_usd,
    normalize_salary_columns,
)

# ============================================================================
# Salary Cleaning
# ============================================================================


def test_clean_salary_currency():

    assert clean_salary("$85,000") == 85000.0


def test_clean_salary_text():

    assert clean_salary("EUR 50,000") == 50000.0


def test_clean_salary_number():

    assert clean_salary(50000) == 50000.0


def test_clean_salary_none():

    assert clean_salary(None) is None


# ============================================================================
# Annualization
# ============================================================================


def test_monthly_salary():

    assert (
        annualize_salary(
            5000,
            "Monthly",
        )
        == 60000
    )


def test_biweekly_salary():

    assert (
        annualize_salary(
            2000,
            "Bi-Weekly",
        )
        == 52000
    )


def test_weekly_salary():

    assert (
        annualize_salary(
            1000,
            "Weekly",
        )
        == 52000
    )


def test_annual_salary():

    assert (
        annualize_salary(
            90000,
            "Annual",
        )
        == 90000
    )


def test_unknown_frequency_defaults_to_annual():

    assert (
        annualize_salary(
            80000,
            "Unknown",
        )
        == 80000
    )


def test_missing_salary_returns_none():

    assert (
        annualize_salary(
            None,
            "Monthly",
        )
        is None
    )


# ============================================================================
# Currency Conversion
# ============================================================================


def test_convert_usd():

    assert (
        convert_to_usd(
            1000,
            "USD",
        )
        == 1000
    )


def test_convert_eur():

    assert (
        convert_to_usd(
            1000,
            "EUR",
        )
        == 1080
    )


def test_convert_gbp():

    assert (
        convert_to_usd(
            1000,
            "GBP",
        )
        == 1270
    )


def test_unknown_currency_defaults_rate_one():

    assert (
        convert_to_usd(
            1000,
            "XYZ",
        )
        == 1000
    )


def test_missing_amount_returns_none():

    assert (
        convert_to_usd(
            None,
            "USD",
        )
        is None
    )


# ============================================================================
# DataFrame Transformation
# ============================================================================


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

    assert "salary_numeric" in result.columns

    assert "salary_annual" in result.columns

    assert "salary_usd_annual" in result.columns

    assert result.loc[0, "salary_numeric"] == 1000

    assert result.loc[0, "salary_annual"] == 12000

    assert result.loc[0, "salary_usd_annual"] == 12000

    assert result.loc[1, "salary_numeric"] == 50000

    assert result.loc[1, "salary_annual"] == 50000

    assert result.loc[1, "salary_usd_annual"] == 63500


# ============================================================================
# Alias Mapping
# ============================================================================


def test_base_salary_mapping():

    df = pd.DataFrame(
        {
            "base_salary": [5000],
            "currency": ["USD"],
            "pay_frequency": ["Monthly"],
        }
    )

    result = normalize_salary_columns(df)

    assert result.loc[0, "salary_numeric"] == 5000

    assert result.loc[0, "salary_annual"] == 60000


def test_currency_alias_mapping():

    df = pd.DataFrame(
        {
            "salary": [1000],
            "currency_code": ["EUR"],
            "pay_frequency": ["Monthly"],
        }
    )

    result = normalize_salary_columns(df)

    assert result.loc[0, "salary_usd_annual"] == 12960


def test_frequency_alias_mapping():

    df = pd.DataFrame(
        {
            "salary": [1000],
            "currency": ["USD"],
            "frequency": ["Monthly"],
        }
    )

    result = normalize_salary_columns(df)

    assert result.loc[0, "salary_annual"] == 12000


# ============================================================================
# Missing Columns
# ============================================================================


def test_missing_required_columns_returns_original_dataframe():

    df = pd.DataFrame(
        {
            "salary": [1000],
        }
    )

    result = normalize_salary_columns(df)

    assert "salary_numeric" not in result.columns

    assert "salary_usd_annual" not in result.columns

    assert result.equals(df)
