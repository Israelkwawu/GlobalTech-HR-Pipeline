# Business Rules

## Overview

This document defines business logic applied during processing.

## Why these thresholds

- **88% name similarity.** Close spellings still match. Pairs are reviewed by HR and are not merged, because a wrong merge changes pay. A lower cutoff fills the review file with people who only share a surname.
- **30-day hire window.** Hires more than a month apart are treated as different people. The window also limits comparisons to a date band instead of every employee against every employee.
- **HRIS over payroll over benefits.** Name, department, country, and company stay with HRIS. Pay is filled from payroll. Benefits adds enrollment only. Payroll must not overwrite `company_origin`, or jurisdiction reports follow the pay file instead of the HR file.
- **Gate at more than two failed checks.** One or two broken checks are reported and the extract still ships. A third failed check blocks delivery so payroll does not load a file with several rule families broken.
- **Partitioned Parquet.** Finance filters GlobalTech and AcquiredCo separately. Partitioning by `company_origin` keeps those reads on one company. Review files stay CSV so HR can open them without a parquet reader.

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