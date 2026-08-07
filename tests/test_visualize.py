"""
Visualization tests.

Author: Israel Kwawu
"""

from pathlib import Path

import pandas as pd

from src.visualize import (
    chart_department_headcount,
    chart_country_headcount,
    chart_salary_distribution,
    chart_tenure_distribution,
    chart_benefits_rate,
    chart_quality_summary,
    generate_visualizations,
)

# ============================================================================
# Fixtures
# ============================================================================


def sample_dataframe() -> pd.DataFrame:
    """
    Sample Golden Dataset.
    """

    return pd.DataFrame(
        {
            "department": [
                "Engineering",
                "Finance",
                "Engineering",
                "HR",
            ],
            "country": [
                "USA",
                "Canada",
                "USA",
                "Germany",
            ],
            "employment_type": [
                "Full-Time",
                "Contractor",
                "Full-Time",
                "Part-Time",
            ],
            "salary_usd_annual": [
                120000,
                85000,
                98000,
                60000,
            ],
            "hire_date": [
                "2020-01-01",
                "2021-05-10",
                "2018-08-01",
                "2023-03-15",
            ],
            "benefit_plans": [
                "Medical",
                None,
                "Medical",
                "Dental",
            ],
        }
    )


# ============================================================================
# Individual Charts
# ============================================================================


def test_department_chart_created(tmp_path):

    chart_department_headcount(
        sample_dataframe(),
        tmp_path,
    )

    assert (tmp_path / "01_headcount_department.png").exists()


def test_country_chart_created(tmp_path):

    chart_country_headcount(
        sample_dataframe(),
        tmp_path,
    )

    assert (tmp_path / "02_headcount_country.png").exists()


def test_salary_chart_created(tmp_path):

    chart_salary_distribution(
        sample_dataframe(),
        tmp_path,
    )

    assert (tmp_path / "03_salary_distribution.png").exists()


def test_tenure_chart_created(tmp_path):

    chart_tenure_distribution(
        sample_dataframe(),
        tmp_path,
    )

    assert (tmp_path / "04_tenure_distribution.png").exists()


def test_benefits_chart_created(tmp_path):

    chart_benefits_rate(
        sample_dataframe(),
        tmp_path,
    )

    assert (tmp_path / "05_benefits_enrollment.png").exists()


def test_quality_summary_chart_created(tmp_path):

    validation = {
        "summary": {
            "passed_checks": 9,
            "failed_checks": 1,
            "passed_records": 90,
            "failed_records": 10,
            "pipeline_passed": False,
        }
    }

    chart_quality_summary(
        validation,
        tmp_path,
    )

    assert (tmp_path / "06_quality_summary.png").exists()


# ============================================================================
# Dashboard
# ============================================================================


def test_generate_visualizations(tmp_path):

    validation = {
        "summary": {
            "passed_checks": 8,
            "failed_checks": 0,
            "passed_records": 100,
            "failed_records": 0,
            "pipeline_passed": True,
        }
    }

    result = generate_visualizations(
        sample_dataframe(),
        validation,
        tmp_path,
    )

    assert result["output_directory"] == str(tmp_path)

    assert "generated_at" in result

    assert len(result["charts"]) >= 6

    for chart in result["charts"]:

        assert (tmp_path / chart).exists()

    if "report" in result:

        assert Path(result["report"]).exists()
