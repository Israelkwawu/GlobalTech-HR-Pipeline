"""
Salary normalization utilities.

Responsibilities
----------------
- Normalize salary values
- Clean salary strings
- Convert pay frequency to annual salary
- Convert currencies to USD
- Produce salary_usd_annual
- Preserve original salary columns

Author: Israel Kwawu
"""

from __future__ import annotations


import re

import pandas as pd


from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# Currency Conversion
# ============================================================


CURRENCY_RATES_TO_USD = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
}


# ============================================================
# Salary Cleaning
# ============================================================


def clean_salary(
    value,
):
    """
    Convert salary values into numeric.

    Examples:

    "$85,000"
        -> 85000


    "EUR 50,000"
        -> 50000
    """

    if pd.isna(value):

        return None

    if isinstance(
        value,
        (int, float),
    ):

        return float(value)

    value = str(value)

    value = re.sub(
        r"[^\d.]",
        "",
        value,
    )

    if value == "":

        return None

    return float(value)


# ============================================================
# Frequency Conversion
# ============================================================


def annualize_salary(
    salary,
    frequency,
):

    if pd.isna(salary):

        return None

    frequency = str(frequency).lower().strip().replace("_", "-").replace(" ", "-")

    multiplier = {
        "monthly": 12,
        "month": 12,
        "monthly-salary": 12,
        "bi-weekly": 26,
        "biweekly": 26,
        "bi-week": 26,
        "fortnightly": 26,
        "weekly": 52,
        "annual": 1,
        "yearly": 1,
        "year": 1,
    }.get(
        frequency,
        1,
    )

    return salary * multiplier


# ============================================================
# Currency Conversion
# ============================================================


def convert_to_usd(
    amount,
    currency,
):

    if pd.isna(amount):

        return None

    currency = str(currency).upper().strip()

    if currency not in CURRENCY_RATES_TO_USD:

        logger.warning(
            "Unknown currency '%s'. Defaulting rate=1",
            currency,
        )

        rate = 1.0

    else:

        rate = CURRENCY_RATES_TO_USD[currency]

    return round(
        amount * rate,
        2,
    )


# ============================================================
# Column Preparation
# ============================================================


def _prepare_salary_columns(
    df: pd.DataFrame,
):

    df = df.copy()

    # ADP payroll source

    if "salary" not in df.columns and "base_salary" in df.columns:

        logger.info("Mapping base_salary -> salary")

        df["salary"] = df["base_salary"]

    # Currency aliases

    if "currency" not in df.columns:

        for candidate in [
            "currency_code",
            "curr",
        ]:

            if candidate in df.columns:

                df["currency"] = df[candidate]

                break

    # Frequency aliases

    if "pay_frequency" not in df.columns:

        for candidate in [
            "frequency",
            "payment_frequency",
        ]:

            if candidate in df.columns:

                df["pay_frequency"] = df[candidate]

                break

    return df


# ============================================================
# Main API
# ============================================================


def normalize_salary_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    df = _prepare_salary_columns(df)

    required = {
        "salary",
        "currency",
        "pay_frequency",
    }

    missing = required - set(df.columns)

    if missing:

        logger.error(
            "Missing salary columns=%s",
            missing,
        )

        return df

    logger.info(
        "Normalizing salaries rows=%s",
        len(df),
    )

    # --------------------------------------------------------
    # Numeric salary
    # --------------------------------------------------------

    df["salary_numeric"] = df["salary"].apply(clean_salary)

    # --------------------------------------------------------
    # Annual salary
    # --------------------------------------------------------

    df["salary_annual"] = df.apply(
        lambda row: annualize_salary(
            row["salary_numeric"],
            row["pay_frequency"],
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # USD conversion
    # --------------------------------------------------------

    df["salary_usd_annual"] = df.apply(
        lambda row: convert_to_usd(
            row["salary_annual"],
            row["currency"],
        ),
        axis=1,
    )

    logger.info(
        """
SALARY NORMALIZATION COMPLETE

Rows:
%s

Salary populated:
%s

USD annual populated:
%s

""",
        len(df),
        df["salary_numeric"].notna().sum(),
        df["salary_usd_annual"].notna().sum(),
    )

    return df
