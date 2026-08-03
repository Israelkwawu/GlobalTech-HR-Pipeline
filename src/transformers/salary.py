"""
Salary transformation utilities.

Responsibilities:

- Clean salary strings
- Normalize pay frequency
- Convert currencies
- Calculate annual USD salary
"""

from __future__ import annotations

import re

import pandas as pd

from src.utils.currency import convert_to_usd

from config.logging_config import get_logger

from config.constants import PAY_FREQUENCY_MULTIPLIERS


logger = get_logger(__name__)

def clean_salary(
    value: str | float | int | None,
) -> float | None:
    """
    Convert salary strings into numbers.

    Examples
    --------
    "$85,000" -> 85000.0

    "100000" -> 100000.0
    """

    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    value = str(value)

    value = re.sub(
        r"[^0-9.]+",
        "",
        value,
    )

    if not value:
        return None

    return float(value)


def normalize_frequency(
    frequency: str | None,
) -> str | None:
    """
    Normalize pay frequency names to canonical values.
    """

    if frequency is None:
        return None

    value = (
        str(frequency)
        .strip()
        .lower()
        .replace("_", "-")
    )

    mapping = {
        "annual": "Annual",
        "yearly": "Annual",
        "monthly": "Monthly",
        "bi-weekly": "Bi-Weekly",
        "biweekly": "Bi-Weekly",
        "weekly": "Weekly",
        "hourly": "Hourly",
        "daily": "Daily",
        "semi-monthly": "Semi-Monthly",
        "semimonthly": "Semi-Monthly",
        "quarterly": "Quarterly",
    }

    return mapping.get(value)


def annual_multiplier(
    frequency: str,
) -> int:
    frequency = normalize_frequency(frequency)

    if frequency is None:
        raise ValueError("Pay frequency is required.")

    if frequency not in PAY_FREQUENCY_MULTIPLIERS:
        raise ValueError(
            f"Unsupported pay frequency: {frequency}"
        )

    return PAY_FREQUENCY_MULTIPLIERS[frequency]


def calculate_annual_salary(
    salary: float,
    frequency: str,
) -> float:
    """
    Convert salary to annual amount.
    """

    return salary * annual_multiplier(
        frequency
    )


def calculate_salary_usd(
    salary,
    currency,
    frequency,
):
    """
    Calculate annual salary in USD.
    """

    salary = clean_salary(salary)

    annual_salary = calculate_annual_salary(
        salary,
        frequency,
    )

    return convert_to_usd(
        annual_salary,
        currency,
    )


def normalize_salary_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add salary_usd_annual column.

    Required columns:
        salary
        currency
        pay_frequency
    """

    df = df.copy()

    required = {
        "salary",
        "currency",
        "pay_frequency",
    }

    missing = required - set(df.columns)

    if missing:
        raise KeyError(
            f"Missing columns: {missing}"
        )


    logger.info(
        "Normalizing salaries..."
    )


    df["salary_usd_annual"] = df.apply(
        lambda row:
            calculate_salary_usd(
                row["salary"],
                row["currency"],
                row["pay_frequency"],
            ),
        axis=1,
    )

    return df

