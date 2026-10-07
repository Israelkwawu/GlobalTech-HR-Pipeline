"""
Unit tests for src.ingest.
"""

from pathlib import Path
import json

import pandas as pd
import pytest

from src.ingest import (
    align_employee_schema,
    load_acquiredco_hris,
    load_benefits,
    load_globaltech_hris,
    load_payroll,
)

def write_globaltech_csv(path: Path) -> Path:
    path.write_text(
        "employee_id,first_name,last_name,email,department,job_title,"
        "hire_date,country,employment_type,manager_id\n"
        "1042,Ada,Lovelace,ada@globaltech.test,ENG-01,Engineer,"
        "2020-01-15,USA,Full-Time,1000\n",
        encoding="utf-8",
    )
    return path


def write_acquiredco_json(path: Path) -> Path:
    payload = {
        "status": "ok",
        "timestamp": "2024-01-01T00:00:00",
        "total_records": 2,
        "employees": [
            {
                "employee_identifier": "10",
                "name": {"first": "Grace", "last": "Hopper", "full": "Grace Hopper"},
                "contact": {"email": "grace@acquiredco.test"},
                "assignment": {
                    "department": "Engineering",
                    "role": "Engineer",
                    "location": "UK",
                    "hire_timestamp": "06/27/2020",
                },
                "employment": {"type": "Full-Time"},
                "manager_employee_id": None,
            },
            {
                "employee_identifier": "11",
                "name": {"first": "Alan", "last": "Turing", "full": "Alan Turing"},
                "contact": {"email": "alan@acquiredco.test"},
                "assignment": {
                    "department": "Research",
                    "role": "Scientist",
                    "location": "UK",
                    "hire_timestamp": "01/15/2019",
                },
                "employment": {"type": "Full-Time"},
                "manager_employee_id": "10",
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_payroll_xlsx(path: Path) -> Path:
    pd.DataFrame(
        {
            "employee_id": [1042, 3001],
            "source": ["GlobalTech", "AcquiredCo"],
            "base_salary": ["$85,000", "70000"],
            "currency": ["USD", "EUR"],
            "pay_frequency": ["Annual", "Monthly"],
        }
    ).to_excel(path, index=False)
    return path


def write_benefits_xml(path: Path) -> Path:
    path.write_text(
        """
        <enrollments>
          <enrollment>
            <employee_id>1042</employee_id>
            <plan_type>Medical</plan_type>
            <coverage_level>Employee</coverage_level>
            <enrollment_date>15-Jan-2022</enrollment_date>
            <premium_employee>100</premium_employee>
            <premium_employer>400</premium_employer>
          </enrollment>
        </enrollments>
        """.strip(),
        encoding="utf-8",
    )
    return path


# ==========================================================
# GlobalTech HRIS
# ==========================================================


def test_load_globaltech_hris(tmp_path):
    df = load_globaltech_hris(write_globaltech_csv(tmp_path / "globaltech_hris.csv"))

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "employee_id" in df.columns
    assert "source_system" in df.columns
    assert (df["source_system"] == "globaltech_hris").all()


def test_globaltech_missing_file():
    with pytest.raises(FileNotFoundError):
        load_globaltech_hris("missing.csv")


def test_globaltech_invalid_extension(tmp_path):
    file = tmp_path / "employees.txt"
    file.write_text("hello")

    with pytest.raises(ValueError):
        load_globaltech_hris(file)


# ==========================================================
# AcquiredCo HRIS
# ==========================================================


def test_load_acquiredco_hris(tmp_path):
    df = load_acquiredco_hris(
        write_acquiredco_json(tmp_path / "acquiredco_api.json"),
        page_size=1,
    )

    assert isinstance(df, pd.DataFrame)
    assert not df.empty

    assert len(df) == 2
    assert "employee_identifier" in df.columns
    assert "name.first" in df.columns
    assert "contact.email" in df.columns
    assert "source_system" in df.columns


def test_acquiredco_missing_file():
    with pytest.raises(FileNotFoundError):
        load_acquiredco_hris("missing.json")


def test_acquiredco_invalid_extension(tmp_path):
    file = tmp_path / "employees.csv"
    file.write_text("hello")

    with pytest.raises(ValueError):
        load_acquiredco_hris(file)


def test_acquiredco_bad_json(tmp_path):
    file = tmp_path / "bad.json"
    file.write_text("{invalid json")

    with pytest.raises(RuntimeError):
        load_acquiredco_hris(file)


# ==========================================================
# Payroll
# ==========================================================


def test_load_payroll(tmp_path):
    df = load_payroll(write_payroll_xlsx(tmp_path / "payroll_data.xlsx"))

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "employee_id" in df.columns
    assert "source_system" in df.columns


def test_payroll_missing_file():
    with pytest.raises(FileNotFoundError):
        load_payroll("missing.xlsx")


def test_payroll_invalid_extension(tmp_path):
    file = tmp_path / "payroll.csv"
    file.write_text("hello")

    with pytest.raises(ValueError):
        load_payroll(file)


# ==========================================================
# Benefits
# ==========================================================


def test_load_benefits(tmp_path):
    df = load_benefits(write_benefits_xml(tmp_path / "benefits_enrollment.xml"))

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "employee_id" in df.columns
    assert "plan_type" in df.columns
    assert "source_system" in df.columns


def test_benefits_missing_file():
    with pytest.raises(FileNotFoundError):
        load_benefits("missing.xml")


def test_benefits_invalid_extension(tmp_path):
    file = tmp_path / "benefits.txt"
    file.write_text("hello")

    with pytest.raises(ValueError):
        load_benefits(file)


def test_benefits_bad_xml(tmp_path):
    file = tmp_path / "bad.xml"
    file.write_text("<employees><employee></employees>")

    with pytest.raises(RuntimeError):
        load_benefits(file)


# ==========================================================
# Schema Alignment
# ==========================================================


def test_align_globaltech_schema(tmp_path):
    df = load_globaltech_hris(write_globaltech_csv(tmp_path / "globaltech_hris.csv"))

    aligned = align_employee_schema(
        df,
        "globaltech_hris",
    )

    assert "employee_id" in aligned.columns
    assert "first_name" in aligned.columns
    assert "last_name" in aligned.columns
    assert aligned.loc[0, "dedup_method"] == "single_source"
    assert aligned.loc[0, "source_systems"] == "globaltech_hris"
    assert aligned.loc[0, "company_origin"] == "GlobalTech"


def test_align_acquiredco_schema(tmp_path):
    df = load_acquiredco_hris(write_acquiredco_json(tmp_path / "acquiredco_api.json"))

    aligned = align_employee_schema(
        df,
        "acquiredco_hris",
    )

    assert "employee_id" in aligned.columns
    assert "first_name" in aligned.columns
    assert "last_name" in aligned.columns


def test_align_payroll_schema(tmp_path):
    df = load_payroll(write_payroll_xlsx(tmp_path / "payroll_data.xlsx"))

    aligned = align_employee_schema(
        df,
        "payroll",
    )

    assert "salary" in aligned.columns
    assert "currency" in aligned.columns
    assert set(aligned["company_origin"]) == {"GlobalTech", "AcquiredCo"}
    assert (aligned["dedup_method"] == "single_source").all()


def test_align_benefits_schema(tmp_path):
    df = load_benefits(write_benefits_xml(tmp_path / "benefits_enrollment.xml"))

    aligned = align_employee_schema(
        df,
        "benefits",
    )

    assert "benefit_plan" in aligned.columns
    assert "coverage_level" in aligned.columns


def test_align_unknown_source():
    df = pd.DataFrame()

    with pytest.raises(ValueError):
        align_employee_schema(
            df,
            "unknown",
        )


def test_aligned_columns_are_unique(tmp_path):
    df = load_globaltech_hris(write_globaltech_csv(tmp_path / "globaltech_hris.csv"))

    aligned = align_employee_schema(
        df,
        "globaltech_hris",
    )

    assert len(aligned.columns) == len(set(aligned.columns))


def test_alignment_returns_dataframe(tmp_path):
    df = load_globaltech_hris(write_globaltech_csv(tmp_path / "globaltech_hris.csv"))

    aligned = align_employee_schema(
        df,
        "globaltech_hris",
    )

    assert isinstance(aligned, pd.DataFrame)
