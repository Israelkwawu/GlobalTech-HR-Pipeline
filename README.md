# GlobalTech HR Data Integration Pipeline

## Multi-Source Employee Data Integration & Quality Platform

---

# 1. Project Overview

GlobalTech Corporation recently acquired AcquiredCo and requires a unified employee dataset to support merger activities.

The HR leadership team needs a trusted employee data platform to enable:

- Day 1 integration planning
- Payroll migration
- Benefits enrollment verification
- Compliance reporting
- Workforce analytics

Currently, employee information exists across multiple systems with inconsistent schemas, duplicate records, different currencies, and incompatible data formats.

This project builds an automated data integration pipeline that ingests, cleans, validates, deduplicates, and produces a Golden Employee Dataset.

---

# 2. Business Problem

## Current Data Sources

| Source | System | Format | Records | Challenges |
|---|---|---|---|---|
| GlobalTech HRIS | Workday Export | CSV | 15,000 | Department codes vary |
| AcquiredCo HRIS | BambooHR API | JSON | 3,000 | Employee ID collisions |
| Payroll | ADP Export | Excel | 18,500 | Mixed currencies and duplicates |
| Benefits | MedShield | XML | 12,000 | Partial enrollment |

---

# 3. Project Goals

The pipeline provides:

## Data Integration

- Load multiple data formats
- Standardize employee schemas
- Track source lineage

## Data Cleaning

- Normalize names
- Resolve employee IDs
- Convert currencies
- Standardize dates
- Map departments

## Data Deduplication

- Exact employee ID matching
- Email matching
- Fuzzy name matching
- Ghost employee detection

## Data Quality

- Automated validation rules
- Quality scoring
- Pipeline execution gate

## Analytics

Generate HR insights:

- Headcount analysis
- Salary distribution
- Tenure analysis
- Benefits coverage
- Data quality dashboard

---

# 4. Architecture

             DATA SOURCES
                  |
    +-------------+-------------+
    |             |             |
   CSV           JSON          XLSX
    |             |             |
    +-------------+-------------+
                  |
          INGESTION LAYER
                  |
          CLEANING LAYER
                  |
        DEDUPLICATION ENGINE
                  |
         VALIDATION ENGINE
                  |
    +-------------+-------------+
    |             |             |

Golden Dataset Reports Review Files
Parquet HTML/CSV CSV Outputs


---

# 5. Technology Stack

| Area | Technology |
|---|---|
| Programming Language | Python 3.11+ |
| Data Processing | Pandas |
| File Formats | CSV, JSON, Excel, XML, Parquet |
| Matching Algorithm | RapidFuzz |
| Visualization | Matplotlib |
| Testing | Pytest |
| Configuration | Python Modules |
| Documentation | Markdown |

---

# 6. Project Structure


globaltech-hr-pipeline/

├── pipeline.py
│
├── config/
│ ├── settings.py
│ ├── exchange_rates.py
│ └── department_mapping.py
│
├── data/
│ ├── raw/
│ ├── processed/
│ ├── reports/
│ └── dead_letter/
│
├── src/
│ ├── ingest.py
│ ├── clean.py
│ ├── dedup.py
│ ├── validate.py
│ ├── visualize.py
│ ├── export.py
│
│ ├── matching/
│ ├── transformers/
│ ├── validators/
│ └── utils/
│
├── outputs/
│ ├── golden_dataset/
│ ├── reports/
│ └── review/
│
├── tests/
│
└── docs/


---

# 7. Pipeline Workflow

## Step 1: Ingestion

Loads:

- Workday CSV
- BambooHR JSON
- ADP Excel
- MedShield XML


Example:

```python
load_globaltech_hris()
load_acquiredco_api()
load_payroll()
load_benefits()
```

Output:

Standardized DataFrames.

Step 2: Cleaning
Name Standardization

Examples:

Before:

o'BRIEN, john

After:

John O'Brien
Employee ID Resolution

Problem:

1042

exists in both companies.

Solution:

GlobalTech:

GT-001042


AcquiredCo:

AC-001042
Currency Normalization

Supported currencies:

USD
EUR
GBP

Output column:

salary_usd_annual
Step 3: Deduplication

The pipeline uses three matching passes.

Pass 1: Exact Employee ID

Highest confidence.

Example:

GT-001042 = GT-001042
Pass 2: Email Matching

Example:

john.smith@email.com
Pass 3: Fuzzy Matching

Uses:

Employee name similarity
Hire date proximity

Threshold:

Similarity >= 88%

Matches are sent for HR review.

Step 4: Data Validation

The pipeline performs:

NOT NULL checks
UNIQUE checks
Regex validation
Allowed value checks
Salary range validation
Date validation
Manager relationship checks

Minimum checks:

12+

Pipeline gate:

PASS:

Failed checks <= 2

FAIL:

Failed checks > 2
8. Outputs
Golden Employee Dataset

Location:

outputs/golden_dataset/

Format:

Parquet

Contains:

Clean employee records
Deduplicated employees
Source lineage
Salary normalization

Example:

employee_id
first_name
last_name
department
salary_usd_annual
source_systems
dedup_method
Ghost Employee Report

Location:

outputs/review/ghost_employees.csv

Contains:

Payroll employees without HRIS records.

Purpose:

Fraud detection
Payroll compliance
Probable Match Review

Location:

outputs/review/probable_matches.csv

Contains:

Matching candidates
Similarity score
Hire date difference
Recommended action
Validation Reports

Generated:

outputs/reports/

Files:

validation_report.csv
validation_report.html
eda_dashboard.png
9. Installation
Clone Repository
git clone <repository-url>

cd globaltech-hr-pipeline
Create Virtual Environment
python -m venv .venv

Activate:

Windows
.venv\Scripts\activate
Linux/Mac
source .venv/bin/activate
Install Dependencies
pip install -r requirements.txt
10. Running the Pipeline

Execute:

python pipeline.py

Example output:

=====================================
GLOBALTECH HR DATA PIPELINE
=====================================

Loading HRIS data...
✓ GlobalTech HRIS loaded

Loading AcquiredCo data...
✓ BambooHR data loaded

Loading Payroll...
✓ Payroll loaded

Cleaning records...
✓ Transformation complete

Running deduplication...
✓ Duplicate analysis complete

Running validation...
✓ Validation passed

Exporting dataset...
✓ Golden dataset generated

Pipeline completed successfully
11. Testing

Run all tests:

pytest tests -v

Expected:

==============================
XX passed
==============================
12. Configuration

Important configuration files:

Exchange Rates
config/exchange_rates.py

Defines currency conversion.

Department Mapping
config/department_mapping.py

Maps source departments into the unified taxonomy.

Pipeline Settings
config/settings.py

Contains:

File paths
Validation thresholds
Output locations
13. Known Limitations
Currency conversion uses fixed exchange rates.
Fuzzy matches require HR confirmation.
Benefits data only covers GlobalTech employees.
Department mappings require periodic maintenance.
API ingestion is simulated using local JSON files.
14. Future Improvements

Possible enhancements:

Deploy pipeline using Apache Airflow
Store data in a cloud warehouse
Add Great Expectations validation
Add ML-based entity resolution
Build HR analytics dashboard
Add automated data lineage tracking
15. Author

GlobalTech HR Data Engineering Team

16. License

Internal enterprise project.


This README is suitable for a capstone submission, GitHub portfolio, or an interview walkthrough because it