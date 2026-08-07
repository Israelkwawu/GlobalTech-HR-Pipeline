"""
Data quality reporting.

Responsibilities
----------------
- Calculate dataset quality metrics
- Measure completeness
- Measure uniqueness
- Measure validity

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Completeness
# ============================================================================


def calculate_completeness(
    df: pd.DataFrame,
) -> float:
    """
    Calculate percentage of non-null values.

    Returns
    -------
    float
        Completeness percentage.
    """

    if df.empty:
        return 100.0

    total_cells = df.shape[0] * df.shape[1]

    missing_cells = df.isna().sum().sum()

    return round(
        (1 - missing_cells / total_cells) * 100,
        2,
    )


# ============================================================================
# Uniqueness
# ============================================================================


def calculate_uniqueness(
    df: pd.DataFrame,
    column: str,
) -> float:
    """
    Calculate uniqueness percentage.
    """

    if column not in df.columns:
        return 0.0

    if df.empty:
        return 100.0

    unique_count = df[column].nunique()

    return round(
        (unique_count / len(df)) * 100,
        2,
    )


# ============================================================================
# Validity
# ============================================================================


def calculate_validity(
    errors: pd.DataFrame,
    total_records: int,
) -> float:
    """
    Calculate percentage of records without errors.
    """

    if total_records == 0:
        return 100.0

    if errors.empty:
        return 100.0

    failed_records = errors["employee_id"].nunique()

    return round(
        (1 - failed_records / total_records) * 100,
        2,
    )


# ============================================================================
# Full Quality Report
# ============================================================================


def generate_quality_report(
    df: pd.DataFrame,
    validation_result: dict | pd.DataFrame | None = None,
    output_path: str | None = None,
) -> dict:
    """
    Generate complete quality metrics report.

    Parameters
    ----------
    df:
        Golden employee dataset.

    validation_result:
        ValidationPipeline output dictionary
        or validation errors DataFrame.

    output_path:
        Directory for exported reports.
    """

    import os

    # -------------------------------------------------
    # Extract validation errors
    # -------------------------------------------------

    if validation_result is None:

        validation_errors = pd.DataFrame()

    elif isinstance(validation_result, dict):

        validation_errors = validation_result.get(
            "errors",
            pd.DataFrame(),
        )

    else:

        validation_errors = validation_result

    # -------------------------------------------------
    # Build metrics
    # -------------------------------------------------

    report = {
        "records": len(df),
        "columns": len(df.columns),
        "completeness": calculate_completeness(df),
        "employee_id_uniqueness": (
            calculate_uniqueness(
                df,
                "employee_id",
            )
        ),
        "validity": calculate_validity(
            validation_errors,
            len(df),
        ),
    }

    files = {}

    # -------------------------------------------------
    # Export
    # -------------------------------------------------

    if output_path:

        os.makedirs(
            output_path,
            exist_ok=True,
        )

        report_df = pd.DataFrame([report])

        csv_file = os.path.join(
            output_path,
            "quality_report.csv",
        )

        html_file = os.path.join(
            output_path,
            "quality_report.html",
        )

        report_df.to_csv(
            csv_file,
            index=False,
        )

        report_df.to_html(
            html_file,
            index=False,
        )

        files = {
            "csv": csv_file,
            "html": html_file,
        }

    logger.info("Quality report generated.")

    return {
        "metrics": report,
        "files": files,
    }
