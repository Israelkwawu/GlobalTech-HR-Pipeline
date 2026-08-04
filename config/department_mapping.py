"""
Department taxonomy configuration.

Maps source-specific department identifiers
into a standardized company-wide department structure.

Sources:
- GlobalTech HRIS: department codes
- AcquiredCo HRIS: department names

Author: Israel Kwawu
"""

from __future__ import annotations

STANDARD_DEPARTMENTS = {
    "Engineering",
    "Finance",
    "Human Resources",
    "Information Technology",
    "Legal",
    "Manufacturing",
    "Marketing",
    "Operations",
    "Product",
    "Sales",
    "Strategy",
    "Supply Chain",
    "Customer Support",
}

GLOBALTECH_DEPARTMENT_MAP = {
    "Engineering": "Engineering",
    "Manufacturing": "Manufacturing",
    "Strategy": "Strategy",
    "IT": "Information Technology",
    "Finance": "Finance",
    "HR": "Human Resources",
    "Operations": "Operations",
    "Marketing": "Marketing",
    "Sales": "Sales",
}

ACQUIREDCO_DEPARTMENT_MAP = {
    "Engineering": "Engineering",
    "Product": "Product",
    "Finance": "Finance",
    "Human Resources": "Human Resources",
    "Marketing": "Marketing",
    "Sales": "Sales",
    "Operations": "Operations",
    "Customer Success": "Customer Support",
}

