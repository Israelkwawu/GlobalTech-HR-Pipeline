"""
Data validation rules.

Defines:
- Required fields
- Unique fields
- Allowed values
- Regex rules
- Numeric ranges
- Date ranges
- Quality gate thresholds

Author: Israel Kwawu
"""

from __future__ import annotations

from datetime import date

# ============================================================
# Required Fields
# ============================================================


REQUIRED_FIELDS = [
    "employee_id",
    "first_name",
    "last_name",
    "email",
    "department",
    "job_title",
    # "hire_date",
    "country",
    "employment_type",
]


# ============================================================
# Unique Fields
# ============================================================


UNIQUE_FIELDS = [
    "employee_id",
    "email",
]


# ============================================================
# Allowed Values
# ============================================================


ALLOWED_EMPLOYMENT_TYPES = {
    "Full-Time",
    "Part-Time",
    "Contractor",
}


ALLOWED_CURRENCIES = {
    "USD",
    "EUR",
    "GBP",
}


# ============================================================
# Regex Validation
# ============================================================


REGEX_RULES = {
    "employee_id": r"^(GT|AC)-\d{6}$",
    "email": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
}


# ============================================================
# Numeric Rules
# ============================================================


NUMERIC_RANGES = {
    "salary_usd_annual": {
        "minimum": 15000,
        "maximum": 2000000,
    }
}


# ============================================================
# Date Rules
# ============================================================


DATE_RANGES = {
    "hire_date": {
        "minimum": "1970-01-01",
        "maximum": date.today().isoformat(),
    }
}


# ============================================================
# Quality Gate
# ============================================================


# Halt only when more than this many checks fail.
# One or two failing checks stay in the report and do not block delivery.

MAX_FAILED_CHECKS = 2
