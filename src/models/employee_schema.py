"""
Canonical employee schema for the GlobalTech HR Data Integration Pipeline.

All source systems must be aligned to this schema before cleaning,
deduplication, validation, and export.

Sources:
- GlobalTech HRIS (Workday CSV)
- AcquiredCo HRIS (BambooHR JSON)
- Payroll (ADP Excel)
- Benefits Provider (MedShield XML)

Author: Israel Kwawu
"""

from __future__ import annotations

from src.models.schema import DataFrameSchema

# ============================================================================
# Employee Columns
# ============================================================================

EMPLOYEE_COLUMNS = [
    "employee_id",
    "first_name",
    "last_name",
    "email",
    "department",
    "country",
    "employment_type",
    "hire_date",
    "salary",
    "currency",
    "salary_usd_annual",
    "manager_id",
    "company_origin",
    "source_systems",
    "dedup_method",
]


# ============================================================================
# Employee Data Types
# ============================================================================

EMPLOYEE_DTYPES = {
    "employee_id": "string",
    "first_name": "string",
    "last_name": "string",
    "email": "string",
    "department": "string",
    "country": "string",
    "employment_type": "string",
    "hire_date": "datetime64[ns]",
    "salary": "float64",
    "currency": "string",
    "salary_usd_annual": "float64",
    "manager_id": "string",
    "company_origin": "string",
    "source_systems": "string",
    "dedup_method": "string",
}


# ============================================================================
# Required Fields
# ============================================================================

REQUIRED_FIELDS = [
    "employee_id",
    "first_name",
    "last_name",
    "email",
    "department",
    "country",
]


# ============================================================================
# Optional Fields
# ============================================================================

OPTIONAL_FIELDS = [
    "manager_id",
    "salary",
    "currency",
    "salary_usd_annual",
    "employment_type",
    "hire_date",
    "company_origin",
    "source_systems",
    "dedup_method",
]


# ============================================================================
# Primary Key
# ============================================================================

PRIMARY_KEY = "employee_id"


# ============================================================================
# Employee Schema Object
# ============================================================================

EMPLOYEE_SCHEMA = DataFrameSchema(
    columns=EMPLOYEE_COLUMNS,
    dtypes=EMPLOYEE_DTYPES,
    required_fields=REQUIRED_FIELDS,
    optional_fields=OPTIONAL_FIELDS,
)


# ============================================================================
# Schema Metadata
# ============================================================================

EMPLOYEE_SCHEMA_DESCRIPTION = {
    "employee_id": {
        "description": "Unique namespaced employee identifier",
        "example": "GT-001042",
        "type": "string",
    },
    "first_name": {
        "description": "Employee first name",
        "example": "John",
        "type": "string",
    },
    "last_name": {
        "description": "Employee last name",
        "example": "Smith",
        "type": "string",
    },
    "email": {
        "description": "Employee corporate email",
        "example": "john.smith@globaltech.com",
        "type": "string",
    },
    "department": {
        "description": "Standardized department taxonomy",
        "example": "Engineering",
        "type": "string",
    },
    "country": {
        "description": "Employee work jurisdiction",
        "example": "USA",
        "type": "string",
    },
    "employment_type": {
        "description": "Employment classification",
        "example": "Full-Time",
        "type": "string",
    },
    "hire_date": {
        "description": "Employee hire date",
        "example": "2022-01-15",
        "type": "datetime",
    },
    "salary": {
        "description": "Original salary value",
        "example": 85000.0,
        "type": "float",
    },
    "currency": {
        "description": "Original salary currency",
        "example": "USD",
        "type": "string",
    },
    "salary_usd_annual": {
        "description": "Annual salary converted to USD",
        "example": 85000.0,
        "type": "float",
    },
    "manager_id": {
        "description": "Employee ID of direct manager",
        "example": "GT-000120",
        "type": "string",
    },
    "company_origin": {
        "description": "Original company source",
        "example": "GlobalTech",
        "type": "string",
    },
    "source_systems": {
        "description": "Systems contributing to final record",
        "example": "globaltech_hris,payroll",
        "type": "string",
    },
    "dedup_method": {
        "description": "Method used to resolve duplicates",
        "example": "exact_id",
        "type": "string",
    },
}
