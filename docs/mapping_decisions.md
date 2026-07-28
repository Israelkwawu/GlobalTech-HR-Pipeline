# Data Mapping Decisions

## Overview

This document explains transformation decisions made when aligning different source systems into the GlobalTech employee schema.

---

# 1. Employee ID Mapping

## Problem

GlobalTech and AcquiredCo both use numeric employee identifiers.

Example:


1042


could represent two different employees.

---

## Decision

Create a namespace-based identifier.

Mapping:

| Source | Output |
|-|-|
| GlobalTech | GT-XXXXXX |
| AcquiredCo | AC-XXXXXX |

Example:


1042 → GT-001042
1042 → AC-001042


---

# 2. Department Mapping

## Problem

Different systems represent departments differently.

Example:

GlobalTech:


ENG-01


AcquiredCo:


Engineering


---

## Decision

Create a standard taxonomy.

Example:

| Source Value | Standard Department |
|-|-|
| ENG-01 | Engineering |
| Engineering | Engineering |
| MKT-03 | Marketing |

Unmapped departments are logged for review.

---

# 3. Salary Mapping

## Problem

Payroll contains multiple currencies.

Supported currencies:

- USD
- EUR
- GBP

---

## Decision

Keep original salary fields and create:


salary_usd_annual


Example:

Before:


salary=70000
currency=EUR
frequency=Monthly


After:


salary_usd_annual=92000


---

# 4. Date Mapping

## Problem

Sources use different formats.

Examples:


2022-01-15
01/15/2022
15-Jan-2022


---

## Decision

Convert all dates to:


datetime64[ns]


Invalid dates are flagged.

---

# 5. Duplicate Resolution Priority

Source trust order:

1. HRIS
2. Payroll
3. Benefits

HRIS records are considered the system of record.
