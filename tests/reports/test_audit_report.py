"""
Tests for audit report generation.

Author: Israel Kwawu
"""

import json

from src.reports.audit_report import (
    create_audit_record,
    generate_audit_report,
    export_audit_report,
)

# ============================================================================
# Audit Record
# ============================================================================


def test_create_audit_record():

    result = create_audit_record(
        pipeline_name="GlobalTech HR Pipeline",
        source_system="globaltech_hris",
        records_received=1000,
        records_processed=980,
        records_failed=20,
    )

    assert result["pipeline_name"] == "GlobalTech HR Pipeline"

    assert result["records_received"] == 1000

    assert result["success_rate"] == 98

    assert "timestamp" in result


def test_zero_records_success_rate():

    result = create_audit_record(
        pipeline_name="Test",
        source_system="test",
        records_received=0,
        records_processed=0,
        records_failed=0,
    )

    assert result["success_rate"] == 100


# ============================================================================
# Full Report
# ============================================================================


def test_generate_audit_report():

    sources = [
        {
            "source_system": "globaltech_hris",
            "records_received": 1000,
            "records_processed": 990,
            "records_failed": 10,
        },
        {
            "source_system": "payroll",
            "records_received": 1000,
            "records_processed": 1000,
            "records_failed": 0,
        },
    ]

    report = generate_audit_report(
        sources,
        "GlobalTech HR Pipeline",
    )

    assert report["summary"]["total_received"] == 2000

    assert report["summary"]["total_processed"] == 1990

    assert report["summary"]["total_failed"] == 10

    assert len(report["sources"]) == 2


# ============================================================================
# Export
# ============================================================================


def test_export_audit_report(
    tmp_path,
):

    report = {
        "pipeline": "test",
        "records": 100,
    }

    file = export_audit_report(
        report,
        tmp_path / "audit.json",
    )

    assert file.exists()

    with open(
        file,
        encoding="utf-8",
    ) as f:

        loaded = json.load(f)

    assert loaded["pipeline"] == "test"
