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
        "minimum": "1980-01-01",
        "maximum": "2030-12-31",
    }
}


# ============================================================
# Quality Gate
# ============================================================


# Maximum allowed failed validation checks

MAX_FAILED_CHECKS = 0


# Maximum allowed percentage of failed rows

MAX_FAILURE_RATE = 0.0
