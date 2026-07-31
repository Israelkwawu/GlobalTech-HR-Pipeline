# GlobalTech HR Data Integration Pipeline Architecture

## 1. Overview

The GlobalTech HR Data Integration Pipeline consolidates employee data from multiple HR and business systems into a single trusted **Golden Employee Dataset**.

### Integrated Sources

- GlobalTech HRIS (Workday CSV export)
- AcquiredCo HRIS (BambooHR JSON API)
- Combined Payroll System (ADP Excel export)
- Benefits Provider (MedShield XML export)

### Business Objectives

- Day 1 merger integration planning
- Payroll migration
- Benefits enrollment verification
- Compliance reporting
- Workforce analytics

---

## 2. Architecture Design

The pipeline follows a modular ETL architecture.

```text
DATA SOURCES
      |
      v
INGESTION LAYER
      |
      v
CLEANING & TRANSFORMATION
      |
      v
DEDUPLICATION ENGINE
      |
      v
DATA QUALITY VALIDATION
      |
      v
EXPORT & REPORTING
```

---

## 3. Pipeline Layers

### 3.1 Ingestion Layer

Responsibilities:

- Read CSV files
- Simulate paginated API ingestion
- Load Excel payroll records
- Parse XML benefits records
- Add source metadata
- Handle malformed records

**Output:** Standardized Pandas DataFrames.

### 3.2 Cleaning Layer

Processes:

- Name normalization
- Employee ID namespacing
- Currency conversion
- Department taxonomy mapping
- Date normalization
- Missing value handling

Example:

Before:

```text
Employee ID: 1042
Company: AcquiredCo
```

After:

```text
Employee ID: AC-001042
```

### 3.3 Deduplication Layer

#### Pass 1: Employee ID Match

Highest-confidence match.

```text
GT-001042 == GT-001042
```

#### Pass 2: Email Match

```text
john.smith@company.com
```

#### Pass 3: Fuzzy Matching

Uses:

- Name similarity
- Hire date proximity

Library:

```text
rapidfuzz
```

Potential matches are flagged for HR review.

### 3.4 Validation Layer

Validation includes:

- Completeness checks
- Uniqueness checks
- Format validation
- Range validation
- Referential integrity

The pipeline fails if more than two critical validation checks fail.

---

## 4. Output Architecture

### Golden Dataset

**Format:** `Parquet`

Contains:

- Clean employee records
- Deduplicated employees
- Source lineage
- Standardized fields

### Review Outputs

#### Ghost Employees

Payroll employees without HRIS records.

Purpose:

- Fraud detection
- Payroll compliance

#### Probable Matches

Employees requiring manual HR review.

---

## 5. Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| Processing | Pandas |
| Matching | RapidFuzz |
| Storage | Parquet |
| Validation | Custom Framework |
| Visualization | Matplotlib |
| Testing | Pytest |

---

## 6. Design Principles

The pipeline emphasizes:

- Separation of concerns
- Configuration-driven processing
- Reproducibility
- Data lineage tracking
- Automated validation
- Testability
