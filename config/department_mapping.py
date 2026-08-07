"""
Department taxonomy configuration.

Maps source-specific department identifiers
into a standardized company-wide department structure.

Sources:
- GlobalTech HRIS: department codes + names
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
    "Data Science",
    "Quality Assurance",
    "Communications",
    "Business Development",
    "DevOps",
}


GLOBALTECH_DEPARTMENT_MAP = {
    # Codes
    "ENG-01": "Engineering",
    "FIN-01": "Finance",
    "HR-01": "Human Resources",
    "MKT-03": "Marketing",
    "IT-01": "Information Technology",
    # Existing department names
    "Engineering": "Engineering",
    "Finance": "Finance",
    "Human Resources": "Human Resources",
    "Information Technology": "Information Technology",
    "IT": "Information Technology",
    "Legal": "Legal",
    "Manufacturing": "Manufacturing",
    "Marketing": "Marketing",
    "Operations": "Operations",
    "Product": "Product",
    "Sales": "Sales",
    "Strategy": "Strategy",
    "Supply Chain": "Supply Chain",
    "Customer Success": "Customer Support",
    "Communications": "Communications",
    "Data Science": "Data Science",
    "Quality Assurance": "Quality Assurance",
    "Business Development": "Business Development",
    "Devops": "DevOps",
    "DevOps": "DevOps",
}


ACQUIREDCO_DEPARTMENT_MAP = {
    "Engineering": "Engineering",
    "Finance": "Finance",
    "Human Resources": "Human Resources",
    "Information Technology": "Information Technology",
    "IT": "Information Technology",
    "Legal": "Legal",
    "Manufacturing": "Manufacturing",
    "Marketing": "Marketing",
    "Operations": "Operations",
    "Product": "Product",
    "Sales": "Sales",
    "Strategy": "Strategy",
    "Supply Chain": "Supply Chain",
    "Customer Success": "Customer Support",
    "Communications": "Communications",
    "Data Science": "Data Science",
    "Quality Assurance": "Quality Assurance",
    "Business Development": "Business Development",
    "Devops": "DevOps",
    "DevOps": "DevOps",
}
