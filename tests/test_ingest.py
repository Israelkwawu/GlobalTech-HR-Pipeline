"""
Unit tests for src.ingest.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.ingest import (
    align_employee_schema,
    load_acquiredco_hris,
    load_benefits,
    load_globaltech_hris,
    load_payroll,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = PROJECT_ROOT / "data" / "raw"


# ==========================================================
# GlobalTech HRIS
# ==========================================================


def test_load_globaltech_hris():
    df = load_globaltech_hris(
        RAW_DATA / "globaltech_hris.csv"
    )

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


def test_load_acquiredco_hris():
    df = load_acquiredco_hris(
        RAW_DATA / "acquiredco_api.json"
    )

    assert isinstance(df, pd.DataFrame)
    assert not df.empty

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


def test_load_payroll():
    df = load_payroll(
        RAW_DATA / "payroll_data.xlsx"
    )

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


def test_load_benefits():
    df = load_benefits(
        RAW_DATA / "benefits_enrollment.xml"
    )

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


def test_align_globaltech_schema():
    df = load_globaltech_hris(
        RAW_DATA / "globaltech_hris.csv"
    )

    aligned = align_employee_schema(
        df,
        "globaltech_hris",
    )

    assert "employee_id" in aligned.columns
    assert "first_name" in aligned.columns
    assert "last_name" in aligned.columns


def test_align_acquiredco_schema():
    df = load_acquiredco_hris(
        RAW_DATA / "acquiredco_api.json"
    )

    aligned = align_employee_schema(
        df,
        "acquiredco_hris",
    )

    assert "employee_id" in aligned.columns
    assert "first_name" in aligned.columns
    assert "last_name" in aligned.columns


def test_align_payroll_schema():
    df = load_payroll(
        RAW_DATA / "payroll_data.xlsx"
    )

    aligned = align_employee_schema(
        df,
        "payroll",
    )

    assert "salary" in aligned.columns
    assert "currency" in aligned.columns


def test_align_benefits_schema():
    df = load_benefits(
        RAW_DATA / "benefits_enrollment.xml"
    )

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


def test_aligned_columns_are_unique():
    df = load_globaltech_hris(
        RAW_DATA / "globaltech_hris.csv"
    )

    aligned = align_employee_schema(
        df,
        "globaltech_hris",
    )

    assert len(aligned.columns) == len(set(aligned.columns))


def test_alignment_returns_dataframe():
    df = load_globaltech_hris(
        RAW_DATA / "globaltech_hris.csv"
    )

    aligned = align_employee_schema(
        df,
        "globaltech_hris",
    )

    assert isinstance(aligned, pd.DataFrame)
    
    
