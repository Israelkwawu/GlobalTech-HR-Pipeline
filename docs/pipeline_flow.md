# Pipeline Execution Flow

## Overview

The pipeline executes in six major stages.

---

# Stage 1: Ingestion

Input:


data/raw/


Sources:

- CSV
- JSON
- XLSX
- XML

Output:

Standardized DataFrames.

---

# Stage 2: Cleaning

Operations:

1. Normalize names
2. Resolve employee IDs
3. Convert salaries
4. Map departments
5. Standardize dates

---

# Stage 3: Deduplication

Execution order:


Exact ID Match
|
Email Match
|
Fuzzy Match
|
Ghost Detection


---

# Stage 4: Validation

Checks:

- Null values
- Unique constraints
- Regex validation
- Numeric ranges
- Date ranges
- Referential integrity

---

# Stage 5: Analytics

Generate:

- Department headcount
- Country distribution
- Salary analysis
- Tenure analysis
- Benefits enrollment
- Quality dashboard

---

# Stage 6: Export

Outputs:


outputs/
|
├── golden_dataset/
├── reports/
└── review/


---

# Running the Pipeline

Command:

```bash
python pipeline.py
```

Expected Output

Example:

Pipeline Started

✓ Ingestion Complete
✓ Cleaning Complete
✓ Deduplication Complete
✓ Validation Passed
✓ Dataset Exported

Pipeline Completed Successfully

---

These documentation files are ready to place directly under your `docs/` directory. They also provide enough project context for a reviewer, HR stakeholder, or data engineering interviewer to understand the design decisions.