"""
Export utilities.

Responsibilities
----------------
- Write pipeline outputs
- Export golden dataset
- Export validation reports
- Export audit artifacts
- Ensure parquet compatibility

Author: Israel Kwawu
"""

from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from config.constants import (
    GOLDEN_DATASET_FILENAME,
    VALIDATION_REPORT_CSV,
    GHOST_EMPLOYEE_REPORT,
    PROBABLE_MATCHES_REPORT,
)

from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Output directory
# ============================================================================


DEFAULT_OUTPUT_DIR = Path("outputs")


# ============================================================================
# Helpers
# ============================================================================


def ensure_output_directory(
    output_dir: Path | str,
) -> Path:
    """
    Create output directory if missing.
    """

    output_path = Path(output_dir)

    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return output_path


def sanitize_dataframe(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Make dataframe safe for parquet export.

    Fixes:
    - mixed int/string columns
    - object dtype failures
    - pyarrow conversion errors
    """

    df = df.copy()

    for column in df.columns:

        # ------------------------------------------------
        # Object columns
        # ------------------------------------------------

        if df[column].dtype == "object":

            df[column] = df[column].astype("string")

    return df


def dataframe_to_records(
    df: pd.DataFrame,
) -> list:
    """
    Convert dataframe to JSON-safe records.
    """

    if df is None:

        return []

    return json.loads(
        df.to_json(
            orient="records",
            date_format="iso",
        )
    )


# ============================================================================
# DataFrame Export
# ============================================================================


def export_dataframe(
    df: pd.DataFrame,
    filename: str | None = None,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    output_path: Path | str | None = None,
) -> Path:
    """
    Export dataframe as parquet/csv.
    """

    if output_path is not None:

        file_path = Path(output_path)

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    elif filename is not None:

        directory = ensure_output_directory(output_dir)

        file_path = directory / filename

    else:

        raise ValueError("filename or output_path required")

    logger.info(
        "Preparing dataframe export: %s",
        file_path,
    )

    df = sanitize_dataframe(df)

    suffix = file_path.suffix.lower()

    if suffix == ".parquet":

        df.to_parquet(
            file_path,
            index=False,
            engine="pyarrow",
        )

    elif suffix == ".csv":

        df.to_csv(
            file_path,
            index=False,
        )

    else:

        raise ValueError(f"Unsupported export format {suffix}")

    logger.info(
        "Export completed: %s",
        file_path,
    )

    return file_path


# ============================================================================
# JSON Export
# ============================================================================


def export_json(
    data,
    filename: str,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> Path:
    """
    Export JSON artifact.
    """

    output_path = ensure_output_directory(output_dir)

    file_path = output_path / filename

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            default=str,
        )

    logger.info(
        "JSON exported: %s",
        file_path,
    )

    return file_path


# ============================================================================
# Pipeline Export
# ============================================================================


def export_pipeline_results(
    golden_dataset: pd.DataFrame,
    validation_errors: pd.DataFrame,
    ghost_employees: pd.DataFrame,
    probable_matches: pd.DataFrame,
    validation_summary: dict | None = None,
    audit_report: list | dict | None = None,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
) -> dict:
    """
    Export complete pipeline output package.

    Output:

    outputs/
    |
    ├── golden_employee_dataset.parquet
    ├── validation_errors.csv
    ├── validation_report.json
    ├── audit_report.json
    ├── ghost_employee_report.csv
    └── probable_matches.csv

    """

    logger.info("Exporting pipeline results...")

    files = {}

    # ------------------------------------------------
    # Golden dataset
    # ------------------------------------------------

    files["golden_dataset"] = export_dataframe(
        golden_dataset,
        GOLDEN_DATASET_FILENAME,
        output_dir,
    )

    # ------------------------------------------------
    # Validation errors
    # ------------------------------------------------

    files["validation_errors"] = export_dataframe(
        validation_errors,
        VALIDATION_REPORT_CSV,
        output_dir,
    )

    # ------------------------------------------------
    # Validation JSON summary
    # ------------------------------------------------

    validation_report = {
        "summary": validation_summary or {},
        "errors": dataframe_to_records(validation_errors),
    }

    files["validation_report"] = export_json(
        validation_report,
        "validation_report.json",
        output_dir,
    )

    # ------------------------------------------------
    # Audit report
    # ------------------------------------------------

    files["audit_report"] = export_json(
        audit_report or [],
        "audit_report.json",
        output_dir,
    )

    # ------------------------------------------------
    # Ghost employees
    # ------------------------------------------------

    files["ghost_employees"] = export_dataframe(
        ghost_employees,
        GHOST_EMPLOYEE_REPORT,
        output_dir,
    )

    # ------------------------------------------------
    # Probable matches
    # ------------------------------------------------

    files["probable_matches"] = export_dataframe(
        probable_matches,
        PROBABLE_MATCHES_REPORT,
        output_dir,
    )

    logger.info("Pipeline export completed.")

    return files


# ============================================================================
# Public Dataset API
# ============================================================================


def export_dataset(
    df: pd.DataFrame,
    output_path: str | Path,
) -> Path:
    """
    Export dataset to explicit path.
    """

    return export_dataframe(
        df=df,
        output_path=output_path,
    )
