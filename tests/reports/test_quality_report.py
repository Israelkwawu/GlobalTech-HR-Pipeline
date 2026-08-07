"""
Tests for quality reporting.

Author: Israel Kwawu
"""

from pathlib import Path

import pandas as pd

from src.reports.quality_report import (
    calculate_completeness,
    calculate_uniqueness,
    calculate_validity,
    generate_quality_report,
)


def sample_dataframe():

    return pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
                "GT-000002",
            ],
            "email": [
                "a@test.com",
                "b@test.com",
                None,
            ],
            "department": [
                "IT",
                "HR",
                "Finance",
            ],
        }
    )


# ============================================================================
# Completeness
# ============================================================================


def test_completeness():

    df = sample_dataframe()

    result = calculate_completeness(df)

    assert result < 100
    assert result > 0


def test_empty_completeness():

    assert calculate_completeness(pd.DataFrame()) == 100


# ============================================================================
# Uniqueness
# ============================================================================


def test_employee_id_uniqueness():

    df = sample_dataframe()

    result = calculate_uniqueness(
        df,
        "employee_id",
    )

    assert result == 66.67


def test_missing_column_uniqueness():

    df = sample_dataframe()

    assert (
        calculate_uniqueness(
            df,
            "missing",
        )
        == 0
    )


# ============================================================================
# Validity
# ============================================================================


def test_validity():

    errors = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
            ]
        }
    )

    result = calculate_validity(
        errors,
        10,
    )

    assert result == 90


# ============================================================================
# Full Report
# ============================================================================


def test_generate_quality_report():

    df = sample_dataframe()

    report = generate_quality_report(df)

    assert "metrics" in report
    assert "files" in report

    metrics = report["metrics"]

    assert metrics["records"] == 3
    assert metrics["columns"] == 3
    assert "completeness" in metrics
    assert "employee_id_uniqueness" in metrics
    assert "validity" in metrics

    # No export requested
    assert report["files"] == {}


def test_generate_quality_report_exports(tmp_path):

    df = sample_dataframe()

    report = generate_quality_report(
        df,
        output_path=tmp_path,
    )

    files = report["files"]

    assert "csv" in files
    assert "html" in files

    assert Path(files["csv"]).exists()
    assert Path(files["html"]).exists()
