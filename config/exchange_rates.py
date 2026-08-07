"""
Currency exchange rate configuration.

This module contains fixed exchange rates used to normalize
employee salaries into USD.

Rates represent:
    1 unit of currency = X USD

Example:
    EUR 1.08 means:
    €1 = $1.08 USD

Author: Israel Kwawu
"""

# ============================================================================
# Base Currency
# ============================================================================

BASE_CURRENCY = "USD"


# ============================================================================
# Exchange Rates
# ============================================================================

EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
}


# ============================================================================
# Supported Currencies
# ============================================================================

SUPPORTED_CURRENCIES = tuple(EXCHANGE_RATES.keys())
