"""
Currency exchange rate configuration.

This module contains fixed exchange rates used to normalize
employee salaries into USD.

Rates represent:
    1 unit of currency = X USD

Example:
    EUR 1.10 means:
    €1 = $1.10 USD

Author: Israel Kwawu
"""

from decimal import Decimal


# ============================================================================
# Base Currency
# ============================================================================

BASE_CURRENCY = "USD"


# ============================================================================
# Exchange Rates
# ============================================================================

EXCHANGE_RATES = {
    "USD": Decimal("1.00"),
    "EUR": Decimal("1.10"),
    "GBP": Decimal("1.25"),
}


# ============================================================================
# Supported Currencies
# ============================================================================

SUPPORTED_CURRENCIES = tuple(
    EXCHANGE_RATES.keys()
)


# ============================================================================
# Helper Functions
# ============================================================================

def get_exchange_rate(currency: str) -> Decimal:
    """
    Retrieve exchange rate for a currency.

    Parameters
    ----------
    currency : str
        Currency code (USD, EUR, GBP)

    Returns
    -------
    Decimal
        Conversion rate to USD

    Raises
    ------
    ValueError
        If currency is unsupported.
    """

    currency = currency.upper()

    if currency not in EXCHANGE_RATES:
        raise ValueError(
            f"Unsupported currency: {currency}"
        )

    return EXCHANGE_RATES[currency]


def convert_to_usd(
    amount: float,
    currency: str,
) -> float:
    """
    Convert salary amount to USD.

    Parameters
    ----------
    amount : float
        Original salary amount

    currency : str
        Original currency code

    Returns
    -------
    float
        Salary converted to USD
    """

    rate = get_exchange_rate(currency)

    return float(
        Decimal(str(amount)) * rate
    )
    
