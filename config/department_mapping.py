"""
Department taxonomy configuration.

Maps source-specific department identifiers
into a standardized company-wide department structure.

Sources:
- GlobalTech HRIS: department codes
- AcquiredCo HRIS: department names

Author: Israel Kwawu
"""


# ============================================================================
# Standard Department Taxonomy
# ============================================================================

STANDARD_DEPARTMENTS = (
    "Engineering",
    "Product",
    "Marketing",
    "Sales",
    "Finance",
    "Human Resources",
    "Operations",
    "Legal",
    "Customer Success",
    "Information Technology",
)


# ============================================================================
# GlobalTech Department Code Mapping
# ============================================================================

GLOBALTECH_DEPARTMENT_MAP = {

    "ENG-01": "Engineering",

    "PROD-01": "Product",

    "MKT-03": "Marketing",

    "SAL-01": "Sales",

    "FIN-01": "Finance",

    "HR-01": "Human Resources",

    "OPS-01": "Operations",

    "LEG-01": "Legal",

    "CS-01": "Customer Success",

    "IT-01": "Information Technology",
}


# ============================================================================
# AcquiredCo Department Mapping
# ============================================================================

ACQUIREDCO_DEPARTMENT_MAP = {

    "Engineering": "Engineering",

    "Software Engineering": "Engineering",

    "Product Management": "Product",

    "Marketing": "Marketing",

    "Sales": "Sales",

    "Accounting": "Finance",

    "Finance": "Finance",

    "People Operations": "Human Resources",

    "Human Resources": "Human Resources",

    "Operations": "Operations",

    "Legal": "Legal",

    "Customer Support": "Customer Success",
}


# ============================================================================
# Combined Lookup Mapping
# ============================================================================

DEPARTMENT_MAP = {
    **GLOBALTECH_DEPARTMENT_MAP,
    **ACQUIREDCO_DEPARTMENT_MAP,
}


# ============================================================================
# Helper Functions
# ============================================================================

def normalize_department(
    department: str,
) -> str | None:
    """
    Convert a source department value into
    the standard taxonomy.

    Parameters
    ----------
    department : str
        Source department code or name

    Returns
    -------
    str | None
        Standard department name or None if unmapped
    """

    if not department:
        return None

    department = department.strip()

    return DEPARTMENT_MAP.get(
        department
    )


def is_valid_department(
    department: str,
) -> bool:
    """
    Check whether a department belongs
    to the standard taxonomy.
    """

    return department in STANDARD_DEPARTMENTS
