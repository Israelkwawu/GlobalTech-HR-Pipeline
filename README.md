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

## 4. Architecture

```text
DATA SOURCES
      |
+-----+-----+-----+-----+
|           |           |
CSV        JSON       XLSX
|           |           |
+-----------+-----------+
            |
    INGESTION LAYER
            |
     CLEANING LAYER
            |
  DEDUPLICATION ENGINE
            |
   VALIDATION ENGINE
            |
+-----------+-----------+
|           |           |
Golden   Reports   Review Files
Dataset           

Parquet   HTML/CSV   CSV
```
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

```text
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
```

---


# 7. Pipeline Workflow

## Step 1: Ingestion

```python
load_globaltech_hris()
load_acquiredco_hris()
load_payroll()
load_benefits()
```

## Step 2: Cleaning

- Name standardization
- Employee ID resolution
- Currency normalization
- Department mapping

## Step 3: Deduplication

- Exact Employee ID
- Email matching
- Fuzzy name matching (≥88%)

## Step 4: Validation

- NOT NULL checks
- UNIQUE checks
- Regex validation
- Allowed values
- Salary range validation
- Date validation
- Manager relationship checks

---

# 8. Outputs

- Golden Employee Dataset (Parquet)
- Ghost Employee Report
- Probable Match Review
- Validation Reports
- EDA Dashboard

---

# 9. Installation

```bash
git clone <repository-url>
cd globaltech-hr-pipeline
python -m venv .venv
```

Activate:

- Windows: `.venv\Scripts\activate`
- Linux/macOS: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

# 10. Running the Pipeline

```bash
python pipeline.py
```

# 11. Testing

```bash
pytest tests -v
```

# 12. Configuration

- `config/settings.py`
- `config/exchange_rates.py`
- `config/department_mapping.py`

# 13. Known Limitations

- Fixed exchange rates
- Fuzzy matches require HR review
- Benefits data covers only GlobalTech
- API ingestion simulated with JSON

# 14. Future Improvements

- Apache Airflow
- Cloud data warehouse
- Great Expectations
- ML entity resolution
- HR analytics dashboard
- Automated lineage

# 15. Author

GlobalTech HR Data Engineering Team

# 16. License

Internal enterprise project.

---

This README is suitable for a capstone submission, GitHub portfolio, or interview walkthrough because it demonstrates real-world data engineering practices including ingestion, transformation, entity resolution, validation, testing, and documentation.
