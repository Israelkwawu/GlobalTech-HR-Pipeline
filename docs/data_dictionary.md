# Employee Golden Dataset Data Dictionary

## Overview

The Golden Employee Dataset contains the unified employee records after:

- ingestion
- cleaning
- transformation
- deduplication
- validation

Storage format:
Parquet


---

# Schema

| Column | Type | Description | Example |
|---|---|---|---|
| employee_id | string | Namespaced unique employee identifier | GT-001042 |
| first_name | string | Employee first name | John |
| last_name | string | Employee last name | Smith |
| email | string | Employee email address | john.smith@email.com |
| department | string | Standard department taxonomy | Engineering |
| country | string | Employee jurisdiction | USA |
| employment_type | string | Employment classification | Full-Time |
| hire_date | datetime64[ns] | Employee start date | 2022-01-15 |
| salary | float | Original salary amount before annualization and currency conversion | 85000 |
| currency | string | Original salary currency | EUR |
| salary_usd_annual | float | Normalized annual salary USD | 92000 |
| manager_id | string | Manager employee ID | GT-000123 |
| company_origin | string | Original company source | GlobalTech |
| source_systems | string | Systems contributing records | globaltech_hris,payroll |
| dedup_method | string | Match strategy applied | exact_id |

---

# Employee ID Convention

Employee IDs are namespaced to prevent collisions.

Format:


COMPANY-XXXXXX


Examples:


GT-001042
AC-001042


---

# Source Lineage

Every record maintains:


source_systems


Example:


globaltech_hris,payroll,benefits


This allows auditing of record origin.

---

# Salary Standardization

All salaries are converted to:


USD annual salary


Conversion rules:

Monthly:


monthly_salary * 12


Bi-weekly:


bi_weekly_salary * 26


---

# Partitioning

Dataset is partitioned by:


company_origin


Example:


company_origin=GlobalTech
company_origin=AcquiredCo