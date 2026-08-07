"""
Pipeline integration tests.

Author: Israel Kwawu
"""

import pandas as pd

from src.pipeline import run_pipeline


def employee_dataframe(employee_id):

    return pd.DataFrame(
        {
            "employee_id": [str(employee_id)],
            "first_name": ["John"],
            "last_name": ["Smith"],
            "email": [f"user{employee_id}@test.com"],
            "department": ["Engineering"],
            "job_title": ["Software Engineer"],
            "country": ["Ghana"],
            "employment_type": ["Full-Time"],
            "manager_id": [None],
            "salary_usd_annual": [50000],
            "company_origin": ["GlobalTech"],
            "hire_date": ["2016-09-21"],
        }
    )


def acquiredco_dataframe():

    return pd.DataFrame(
        {
            "employee_identifier": ["2"],
            "manager_employee_id": [None],
            "name.first": ["John"],
            "name.last": ["Smith"],
            "name.full": ["John Smith"],
            "contact.email": ["user2@test.com"],
            "assignment.department": ["Engineering"],
            "assignment.role": ["Developer"],
            "assignment.location": ["Ghana"],
            "assignment.hire_timestamp": ["2016-09-21"],
            "employment.type": ["Full-Time"],
            "employment.status": ["Active"],
        }
    )


def test_pipeline_returns_results(
    monkeypatch,
):

    # --------------------------------------------------
    # Mock ingestion
    # --------------------------------------------------

    monkeypatch.setattr(
        "src.pipeline.load_globaltech_hris",
        lambda: employee_dataframe(1),
    )

    monkeypatch.setattr(
        "src.pipeline.load_acquiredco_hris",
        lambda: acquiredco_dataframe(),
    )

    monkeypatch.setattr(
        "src.pipeline.load_payroll",
        lambda: pd.DataFrame(
            {
                "employee_id": [],
                "salary": [],
                "currency": [],
                "pay_frequency": [],
            }
        ),
    )

    monkeypatch.setattr(
        "src.pipeline.load_benefits",
        lambda: pd.DataFrame(
            columns=[
                "employee_id",
            ]
        ),
    )

    # --------------------------------------------------
    # Mock reports
    # --------------------------------------------------

    monkeypatch.setattr(
        "src.pipeline.generate_validation_report",
        lambda *args, **kwargs: {},
    )

    monkeypatch.setattr(
        "src.pipeline.generate_quality_report",
        lambda *args, **kwargs: {
            "metrics": {},
            "files": {},
        },
    )

    monkeypatch.setattr(
        "src.pipeline.generate_audit_report",
        lambda *args, **kwargs: {},
    )

    # --------------------------------------------------
    # Mock output
    # --------------------------------------------------

    monkeypatch.setattr(
        "src.pipeline.export_dataset",
        lambda *args, **kwargs: "output.parquet",
    )

    monkeypatch.setattr(
        "src.pipeline.generate_visualizations",
        lambda *args, **kwargs: {},
    )

    result = run_pipeline()

    assert isinstance(
        result,
        dict,
    )

    assert "golden_dataset" in result

    assert "validation" in result

    assert "reports" in result

    assert "export" in result

    assert "charts" in result
