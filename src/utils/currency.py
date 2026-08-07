"""
Currency conversion utilities.

Converts salaries into USD using fixed exchange rates.
"""

from __future__ import annotations

from config.exchange_rates import EXCHANGE_RATES


def normalize_currency(currency: str | None) -> str | None:
    if currency is None:
        return None

    return str(currency).strip().upper()


def get_exchange_rate(currency: str) -> float:
    """
    Return the USD exchange rate for a currency.
    """

    currency = normalize_currency(currency)

    if currency not in EXCHANGE_RATES:
        raise ValueError(f"Unsupported currency: {currency}")

    return float(EXCHANGE_RATES[currency])


def convert_to_usd(
    amount: float,
    currency: str,
) -> float:
    """
    Convert an amount to USD.
    """

    rate = get_exchange_rate(currency)

    return round(
        float(amount) * rate,
        2,
    )
