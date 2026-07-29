"""
Application settings for the GlobalTech HR Data Integration Pipeline.

This module defines runtime configuration such as:
- project directories
- data locations
- output locations
- pipeline execution settings

Business rules should live in separate configuration modules.

Author: Israel Kwawu
"""

from pathlib import Path


# ============================================================================
# Project Root
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================================
# Data Directories
# ============================================================================

DATA_DIR = PROJECT_ROOT / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

REFERENCE_DATA_DIR = DATA_DIR / "reference"

REPORTS_DATA_DIR = DATA_DIR / "reports"

DEAD_LETTER_DIR = DATA_DIR / "dead_letter"


# ============================================================================
# Output Directories
# ============================================================================

OUTPUT_DIR = PROJECT_ROOT / "outputs"

GOLDEN_DATASET_DIR = OUTPUT_DIR / "golden_dataset"

AUDIT_OUTPUT_DIR = OUTPUT_DIR / "audit"

REVIEW_OUTPUT_DIR = OUTPUT_DIR / "review"

REPORT_OUTPUT_DIR = OUTPUT_DIR / "reports"


# ============================================================================
# Source File Locations
# ============================================================================

GLOBALTECH_HRIS_FILE = (
    RAW_DATA_DIR / "globaltech_hris.csv"
)

ACQUIREDCO_HRIS_FILE = (
    RAW_DATA_DIR / "acquiredco_hris.json"
)

PAYROLL_FILE = (
    RAW_DATA_DIR / "payroll.xlsx"
)

BENEFITS_FILE = (
    RAW_DATA_DIR / "benefits.xml"
)


# ============================================================================
# Intermediate Pipeline Outputs
# ============================================================================

INGESTED_DATA_DIR = (
    PROCESSED_DATA_DIR / "ingested"
)

CLEANED_DATA_DIR = (
    PROCESSED_DATA_DIR / "cleaned"
)

DEDUPLICATED_DATA_DIR = (
    PROCESSED_DATA_DIR / "deduplicated"
)


# ============================================================================
# Pipeline Execution Settings
# ============================================================================

PIPELINE_NAME = "GlobalTech HR Data Integration Pipeline"

ENVIRONMENT = "development"

DEBUG = True

CREATE_MISSING_DIRECTORIES = True


# ============================================================================
# File Processing Settings
# ============================================================================

DEFAULT_ENCODING = "utf-8"

CSV_SEPARATOR = ","

EXCEL_ENGINE = "openpyxl"

JSON_ENCODING = "utf-8"

XML_ENCODING = "utf-8"


# ============================================================================
# Data Processing Settings
# ============================================================================

CHUNK_SIZE = 5000

DEFAULT_DATE_COLUMN_FORMAT = "%Y-%m-%d"

PANDAS_DATE_ERRORS = "coerce"


# ============================================================================
# Logging Settings
# ============================================================================

LOG_DIR = PROJECT_ROOT / "logs"

LOG_FILE = LOG_DIR / "pipeline.log"

LOG_LEVEL = "INFO"


# ============================================================================
# Validation Settings
# ============================================================================

VALIDATION_REPORT_FORMATS = (
    "csv",
    "html",
)

FAIL_PIPELINE_ON_VALIDATION_ERROR = True


# ============================================================================
# Helper Functions
# ============================================================================

def create_project_directories() -> None:
    """
    Create required project directories if they do not exist.

    This is called during pipeline startup.
    """

    directories = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        REFERENCE_DATA_DIR,
        REPORTS_DATA_DIR,
        DEAD_LETTER_DIR,
        OUTPUT_DIR,
        GOLDEN_DATASET_DIR,
        AUDIT_OUTPUT_DIR,
        REVIEW_OUTPUT_DIR,
        REPORT_OUTPUT_DIR,
        INGESTED_DATA_DIR,
        CLEANED_DATA_DIR,
        DEDUPLICATED_DATA_DIR,
        LOG_DIR,
    ]

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        
