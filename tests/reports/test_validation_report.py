"""
Tests for validation report generation.

Author: Israel Kwawu
"""

from pathlib import Path

import pandas as pd

from src.reports.validation_report import (
    build_validation_summary,
    validation_error_breakdown,
    export_validation_report,
    generate_validation_html,
)

# ============================================================================
# Fixtures
# ============================================================================


def validation_result():

    return {
        "passed": False,
        "errors": pd.DataFrame(
            {
                "employee_id": [
                    "GT-000001",
                    "GT-000002",
                    "GT-000002",
                ],
                "rule": [
                    "NULL_VALUE",
                    "REGEX_FAILURE",
                    "REGEX_FAILURE",
                ],
                "column": [
                    "email",
                    "email",
                    "email",
                ],
                "message": [
                    "Missing email",
                    "Invalid email",
                    "Invalid email",
                ],
            }
        ),
        "summary": {
            "total_records": 10,
            "passed_records": 8,
            "failed_records": 2,
            "validation_score": 80,
        },
    }


# ============================================================================
# Summary
# ============================================================================


def test_build_validation_summary():

    result = build_validation_summary(validation_result())

    assert result["passed"] is False

    assert result["total_records"] == 10

    assert result["failed_records"] == 2

    assert result["total_errors"] == 3


# ============================================================================
# Error breakdown
# ============================================================================


def test_validation_error_breakdown():

    errors = validation_result()["errors"]

    result = validation_error_breakdown(errors)

    assert len(result) == 2

    assert "REGEX_FAILURE" in result["rule"].values


def test_empty_error_breakdown():

    result = validation_error_breakdown(pd.DataFrame())

    assert result.empty


# ============================================================================
# CSV Export
# ============================================================================


def test_export_validation_report(
    tmp_path,
):

    file = export_validation_report(
        validation_result(),
        tmp_path / "validation.csv",
    )

    assert file.exists()

    loaded = pd.read_csv(file)

    assert len(loaded) == 3


# ============================================================================
# HTML Export
# ============================================================================


def test_generate_validation_html(
    tmp_path,
):

    file = generate_validation_html(
        validation_result(),
        tmp_path / "report.html",
    )

    assert file.exists()

    content = file.read_text(encoding="utf-8")

    assert "GlobalTech HR Validation Report" in content
