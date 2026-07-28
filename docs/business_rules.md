# Business Rules

## Overview

This document defines business logic applied during processing.

---

# Employee Identification Rules

## Rule 1

Every employee must have a unique namespaced ID.

Valid formats:


GT-\d{6}
AC-\d{6}


---

# Salary Rules

## Annual Salary Calculation

Monthly:


salary * 12


Bi-weekly:


salary * 26


---

## Salary Validation

Allowed range:


$15,000 - $2,000,000


Employees outside this range are flagged.

---

# Department Rules

All employees must map to an approved department taxonomy.

Unmapped values:

- Logged
- Reported
- Sent for manual review

---

# Deduplication Rules

## Exact Match

Condition:


same employee_id


Action:

Merge records.

---

## Email Match

Condition:


same email


Action:

Mark as duplicate.

---

## Fuzzy Match

Conditions:


name similarity >= 88%
hire date difference <= 30 days


Action:

Send to HR review.

---

# Ghost Employee Rule

Definition:

Payroll record exists but no HRIS record exists.

Action:

Create:


ghost_employees.csv


---

# Validation Gate

Pipeline status:

PASS:


failed_checks <= 2


FAIL:


failed_checks > 2


---

# Data Quality Requirements

Mandatory fields:

- employee_id
- first_name
- last_name
- email
- department
- country