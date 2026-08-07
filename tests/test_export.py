"""
Tests for export utilities.

Author: Israel Kwawu
"""

from pathlib import Path

import pandas as pd

from src.export import (
    ensure_output_directory,
    export_dataframe,
    export_json,
    export_pipeline_results,
)

# ============================================================================
# Fixtures
# ============================================================================


def sample_dataframe():

    return pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
            ],
            "name": [
                "John Smith",
                "Jane Doe",
            ],
        }
    )


# ============================================================================
# Directory tests
# ============================================================================


def test_create_output_directory(
    tmp_path,
):

    output = tmp_path / "output"

    result = ensure_output_directory(output)

    assert result.exists()
    assert result.is_dir()


# ============================================================================
# CSV export
# ============================================================================


def test_export_csv(
    tmp_path,
):

    df = sample_dataframe()

    file_path = export_dataframe(
        df,
        "employees.csv",
        tmp_path,
    )

    assert file_path.exists()

    loaded = pd.read_csv(file_path)

    assert len(loaded) == 2


# ============================================================================
# Parquet export
# ============================================================================


def test_export_parquet(
    tmp_path,
):

    df = sample_dataframe()

    file_path = export_dataframe(
        df,
        "employees.parquet",
        tmp_path,
    )

    assert file_path.exists()

    loaded = pd.read_parquet(file_path)

    assert len(loaded) == 2


# ============================================================================
# JSON export
# ============================================================================


def test_export_json(
    tmp_path,
):

    data = {
        "status": "success",
        "records": 10,
    }

    file_path = export_json(
        data,
        "summary.json",
        tmp_path,
    )

    assert file_path.exists()

    assert file_path.read_text(encoding="utf-8")


# ============================================================================
# Full pipeline export
# ============================================================================


def test_export_pipeline_results(
    tmp_path,
):

    df = sample_dataframe()

    files = export_pipeline_results(
        golden_dataset=df,
        validation_errors=pd.DataFrame(),
        ghost_employees=pd.DataFrame(),
        probable_matches=pd.DataFrame(),
        output_dir=tmp_path,
    )

    assert "golden_dataset" in files

    assert "validation_report" in files

    assert "ghost_employees" in files

    assert "probable_matches" in files

    for file in files.values():

        assert Path(file).exists()
