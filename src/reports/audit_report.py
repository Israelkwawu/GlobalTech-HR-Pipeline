"""
Audit report generation.

Responsibilities
----------------
- Track pipeline execution metadata
- Record processing statistics
- Summarize transformation activities
- Produce audit-ready reports

Author: Israel Kwawu
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json

from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Audit Record Builder
# ============================================================================


def create_audit_record(
    pipeline_name: str,
    source_system: str,
    records_received: int,
    records_processed: int,
    records_failed: int,
    metadata: dict | None = None,
) -> dict:
    """
    Create a pipeline audit record.
    """

    success_rate = (
        round(
            records_processed / records_received * 100,
            2,
        )
        if records_received
        else 100.0
    )

    return {
        "pipeline_name": pipeline_name,
        "source_system": source_system,
        "timestamp": datetime.utcnow().isoformat(),
        "records_received": records_received,
        "records_processed": records_processed,
        "records_failed": records_failed,
        "success_rate": success_rate,
        "metadata": metadata or {},
    }


# ============================================================================
# Helpers
# ============================================================================


def _normalize_source_statistics(
    source_statistics,
) -> list[dict]:
    """
    Normalize audit input.

    Supports:

    List format:
    [
        {
            "source_system": "...",
            "records_received": 100
        }
    ]

    Dictionary format:
    {
        "globaltech_hris": {
            "records_received": 100
        }
    }

    Returns
    -------
    list[dict]
    """

    if source_statistics is None:

        return []

    # Already a list
    if isinstance(
        source_statistics,
        list,
    ):

        return source_statistics

    # Dictionary format

    if isinstance(
        source_statistics,
        dict,
    ):

        normalized = []

        for source, stats in source_statistics.items():

            # If stats is already a dict

            if isinstance(
                stats,
                dict,
            ):

                record = stats.copy()

            else:

                record = {
                    "records_received": 0,
                    "records_processed": 0,
                    "records_failed": 0,
                }

            record.setdefault(
                "source_system",
                source,
            )

            record.setdefault(
                "records_received",
                0,
            )

            record.setdefault(
                "records_processed",
                record.get(
                    "records_received",
                    0,
                ),
            )

            record.setdefault(
                "records_failed",
                0,
            )

            normalized.append(record)

        return normalized

    raise TypeError("source_statistics must be " "a list or dictionary")


# ============================================================================
# Multi Source Audit Report
# ============================================================================


def generate_audit_report(
    source_statistics: list[dict] | dict,
    pipeline_name: str,
) -> dict:
    """
    Generate complete audit report.

    Supports dictionary and list source statistics.
    """

    source_statistics = _normalize_source_statistics(source_statistics)

    total_received = sum(
        item.get(
            "records_received",
            0,
        )
        for item in source_statistics
    )

    total_processed = sum(
        item.get(
            "records_processed",
            0,
        )
        for item in source_statistics
    )

    total_failed = sum(
        item.get(
            "records_failed",
            0,
        )
        for item in source_statistics
    )

    success_rate = (
        round(
            total_processed / total_received * 100,
            2,
        )
        if total_received
        else 100.0
    )

    report = {
        "pipeline_name": pipeline_name,
        "generated_at": datetime.utcnow().isoformat(),
        "sources": source_statistics,
        "summary": {
            "total_received": total_received,
            "total_processed": total_processed,
            "total_failed": total_failed,
            "success_rate": success_rate,
        },
    }

    logger.info("Audit report generated.")

    return report


# ============================================================================
# Export
# ============================================================================


def export_audit_report(
    report: dict,
    output_path: str | Path,
) -> Path:
    """
    Export audit report as JSON.
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
        )

    logger.info(
        "Audit report exported: %s",
        output_path,
    )

    return output_path
