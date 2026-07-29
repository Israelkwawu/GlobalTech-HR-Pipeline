"""
Tests for pipeline configuration modules.

Validates:
- Constants
- Currency configuration
- Department mappings
- Application settings

Author: Israel Kwawu
"""

import re

from config.constants import (
    COMPANIES,
    SOURCE_SYSTEMS,
    SUPPORTED_CURRENCIES,
    EMPLOYMENT_TYPES,
    EMPLOYEE_ID_REGEX,
    EMAIL_REGEX,
)

from config.exchange_rates import (
    EXCHANGE_RATES,
    BASE_CURRENCY,
)

from config.department_mapping import (
    STANDARD_DEPARTMENTS,
    DEPARTMENT_MAP,
)

from config.settings import (
    PROJECT_ROOT,
    RAW_DATA_DIR,
    OUTPUT_DIR,
)


# ============================================================================
# Constants Tests
# ============================================================================


def test_supported_companies_exist():
    assert "GlobalTech" in COMPANIES
    assert "AcquiredCo" in COMPANIES


def test_source_systems_are_defined():

    expected_sources = [
        "globaltech_hris",
        "acquiredco_hris",
        "payroll",
        "benefits",
    ]

    for source in expected_sources:
        assert source in SOURCE_SYSTEMS


def test_supported_currencies_exist():

    assert "USD" in SUPPORTED_CURRENCIES
    assert "EUR" in SUPPORTED_CURRENCIES
    assert "GBP" in SUPPORTED_CURRENCIES


def test_employment_types_exist():

    assert "Full-Time" in EMPLOYMENT_TYPES
    assert "Part-Time" in EMPLOYMENT_TYPES
    assert "Contractor" in EMPLOYMENT_TYPES


# ============================================================================
# Regex Tests
# ============================================================================


def test_email_regex_is_valid():

    pattern = re.compile(
        EMAIL_REGEX
    )

    assert pattern.match(
        "employee@globaltech.com"
    )


def test_employee_id_regex_is_valid():

    pattern = re.compile(
        EMPLOYEE_ID_REGEX
    )

    assert pattern.match(
        "GT-001042"
    )

    assert pattern.match(
        "AC-001042"
    )

    assert not pattern.match(
        "001042"
    )


# ============================================================================
# Exchange Rate Tests
# ============================================================================


def test_exchange_rates_have_base_currency():

    assert BASE_CURRENCY in EXCHANGE_RATES

    assert (
        EXCHANGE_RATES[BASE_CURRENCY]
        == 1.00
    )


def test_all_exchange_rates_are_positive():

    for rate in EXCHANGE_RATES.values():

        assert rate > 0


# ============================================================================
# Department Mapping Tests
# ============================================================================


def test_department_mapping_not_empty():

    assert len(
        DEPARTMENT_MAP
    ) > 0


def test_standard_departments_exist():

    assert (
        "Engineering"
        in STANDARD_DEPARTMENTS
    )

    assert (
        "Finance"
        in STANDARD_DEPARTMENTS
    )


def test_department_mapping_values_are_standard():

    for department in DEPARTMENT_MAP.values():

        assert (
            department
            in STANDARD_DEPARTMENTS
        )


# ============================================================================
# Settings Tests
# ============================================================================


def test_project_directories_exist():

    assert PROJECT_ROOT.exists()

    assert RAW_DATA_DIR.name == "raw"

    assert OUTPUT_DIR.name == "outputs"
    
    