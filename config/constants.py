"""
Application-wide constants for the GlobalTech HR Data Integration Pipeline.

This module centralizes immutable values shared across the application
to avoid hardcoding strings and magic values throughout the codebase.

Author: Israel
"""

from __future__ import annotations

# ============================================================================
# Pipeline Metadata
# ============================================================================

PIPELINE_NAME = "GlobalTech HR Data Integration Pipeline"
PIPELINE_VERSION = "1.0.0"

# ============================================================================
# Company Names
# ============================================================================

GLOBALTECH = "GlobalTech"
ACQUIREDCO = "AcquiredCo"

COMPANIES = (
    GLOBALTECH,
    ACQUIREDCO,
)

# ============================================================================
# Source Systems
# ============================================================================

SOURCE_GLOBALTECH_HRIS = "globaltech_hris"
SOURCE_ACQUIREDCO_HRIS = "acquiredco_hris"
SOURCE_PAYROLL = "payroll"
SOURCE_BENEFITS = "benefits"

SOURCE_SYSTEMS = (
    SOURCE_GLOBALTECH_HRIS,
    SOURCE_ACQUIREDCO_HRIS,
    SOURCE_PAYROLL,
    SOURCE_BENEFITS,
)

# ============================================================================
# Employee ID Prefixes
# ============================================================================

GLOBALTECH_ID_PREFIX = "GT"
ACQUIREDCO_ID_PREFIX = "AC"

# ============================================================================
# Employment Types
# ============================================================================

FULL_TIME = "Full-Time"
PART_TIME = "Part-Time"
CONTRACTOR = "Contractor"

EMPLOYMENT_TYPES = (
    FULL_TIME,
    PART_TIME,
    CONTRACTOR,
)

# ============================================================================
# Supported Currencies
# ============================================================================

USD = "USD"
EUR = "EUR"
GBP = "GBP"

SUPPORTED_CURRENCIES = (
    USD,
    EUR,
    GBP,
)

BASE_CURRENCY = USD

# ============================================================================
# Pay Frequencies
# ============================================================================

ANNUAL = "Annual"
MONTHLY = "Monthly"
BI_WEEKLY = "Bi-Weekly"
WEEKLY = "Weekly"
HOURLY = "Hourly"
DAILY = "Daily"
SEMI_MONTHLY = "Semi-Monthly"
QUARTERLY = "Quarterly"

PAY_FREQUENCIES = (
    ANNUAL,
    MONTHLY,
    BI_WEEKLY,
    WEEKLY,
    HOURLY,
    DAILY,
    SEMI_MONTHLY,
    QUARTERLY,
)

# Annualization factors
PAY_FREQUENCY_MULTIPLIERS = {
    ANNUAL: 1,
    MONTHLY: 12,
    BI_WEEKLY: 26,
    WEEKLY: 52,
    HOURLY: 2080,
    DAILY: 260,
    SEMI_MONTHLY: 24,
    QUARTERLY: 4,
}

# ============================================================================
# Company Origin
# ============================================================================

COMPANY_ORIGIN_GLOBALTECH = GLOBALTECH
COMPANY_ORIGIN_ACQUIREDCO = ACQUIREDCO

# ============================================================================
# Deduplication Methods
# ============================================================================

DEDUP_EXACT_ID = "exact_id"
DEDUP_EMAIL = "email_match"
DEDUP_FUZZY = "fuzzy_name"
DEDUP_SINGLE_SOURCE = "single_source"

DEDUP_METHODS = (
    DEDUP_EXACT_ID,
    DEDUP_EMAIL,
    DEDUP_FUZZY,
    DEDUP_SINGLE_SOURCE,
)

# ============================================================================
# Record Status
# ============================================================================

ACTIVE = "Active"
INACTIVE = "Inactive"
TERMINATED = "Terminated"

EMPLOYMENT_STATUS = (
    ACTIVE,
    INACTIVE,
    TERMINATED,
)

# ============================================================================
# Validation Limits
# ============================================================================

MIN_HIRE_YEAR = 1970

MIN_ANNUAL_SALARY_USD = 15_000
MAX_ANNUAL_SALARY_USD = 2_000_000

FUZZY_MATCH_THRESHOLD = 88
MAX_HIRE_DATE_DIFF_DAYS = 30

MAX_FAILED_VALIDATION_CHECKS = 2

# ============================================================================
# Date Formats
# ============================================================================

DATE_FORMAT_GLOBALTECH = "%Y-%m-%d"
DATE_FORMAT_ACQUIREDCO = "%m/%d/%Y"
DATE_FORMAT_BENEFITS = "%d-%b-%Y"

SUPPORTED_DATE_FORMATS = (
    DATE_FORMAT_GLOBALTECH,
    DATE_FORMAT_ACQUIREDCO,
    DATE_FORMAT_BENEFITS,
)

# ============================================================================
# File Formats
# ============================================================================

CSV = ".csv"
JSON = ".json"
XML = ".xml"
XLSX = ".xlsx"
PARQUET = ".parquet"
HTML = ".html"

# ============================================================================
# Regular Expressions
# ============================================================================

EMAIL_REGEX = (
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

GLOBALTECH_EMPLOYEE_ID_REGEX = r"^GT-\d{6}$"
ACQUIREDCO_EMPLOYEE_ID_REGEX = r"^AC-\d{6}$"

EMPLOYEE_ID_REGEX = (
    r"^(GT|AC)-\d{6}$"
)

# ============================================================================
# Logging
# ============================================================================

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

DEFAULT_LOG_LEVEL = "INFO"

# ============================================================================
# Output Filenames
# ============================================================================

GOLDEN_DATASET_FILENAME = "golden_employee_dataset.parquet"

VALIDATION_REPORT_CSV = "validation_report.csv"
VALIDATION_REPORT_HTML = "validation_report.html"

GHOST_EMPLOYEE_REPORT = "ghost_employees.csv"

PROBABLE_MATCHES_REPORT = "probable_matches.csv"

# ============================================================================
# Missing Value Placeholders
# ============================================================================

NULL_STRINGS = {
    "",
    " ",
    "NULL",
    "null",
    "None",
    "none",
    "N/A",
    "n/a",
    "NaN",
    "nan",
}
