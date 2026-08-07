"""
Validation report generation.

Responsibilities
----------------
- Summarize validation results
- Generate quality metrics
- Export validation reports

Author: Israel Kwawu
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Summary
# ============================================================================


def build_validation_summary(
    validation_result: dict,
) -> dict:
    """
    Build validation summary.

    Parameters
    ----------
    validation_result:
        Output from validate()

    Returns
    -------
    dict
    """

    summary = validation_result.get(
        "summary",
        {},
    )

    errors = validation_result.get(
        "errors",
        pd.DataFrame(),
    )

    return {
        "passed": validation_result.get(
            "passed",
            False,
        ),
        "total_records": summary.get(
            "total_records",
            0,
        ),
        "passed_records": summary.get(
            "passed_records",
            0,
        ),
        "failed_records": summary.get(
            "failed_records",
            0,
        ),
        "validation_score": summary.get(
            "validation_score",
            0,
        ),
        "total_errors": len(errors),
    }


# ============================================================================
# Error distribution
# ============================================================================


def validation_error_breakdown(
    errors: pd.DataFrame,
) -> pd.DataFrame:
    """
    Count validation failures by rule.
    """

    if errors.empty:

        return pd.DataFrame(
            columns=[
                "rule",
                "count",
            ]
        )

    return (
        errors.groupby("rule")
        .size()
        .reset_index(name="count")
        .sort_values(
            "count",
            ascending=False,
        )
    )


# ============================================================================
# CSV Export
# ============================================================================


def export_validation_report(
    validation_result: dict,
    output_file: str | Path,
) -> Path:
    """
    Export validation errors CSV.
    """

    output_file = Path(output_file)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    errors = validation_result.get(
        "errors",
        pd.DataFrame(),
    )

    errors.to_csv(
        output_file,
        index=False,
    )

    logger.info(
        "Validation report written: %s",
        output_file,
    )

    return output_file


# ============================================================================
# HTML Report
# ============================================================================


def generate_validation_html(
    validation_result: dict,
    output_file: str | Path,
) -> Path:
    """
    Generate simple HTML validation report.
    """

    output_file = Path(output_file)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = build_validation_summary(validation_result)

    breakdown = validation_error_breakdown(
        validation_result.get(
            "errors",
            pd.DataFrame(),
        )
    )

    html = f"""
    <html>
    <head>
        <title>
            Employee Validation Report
        </title>
    </head>

    <body>

    <h1>
        GlobalTech HR Validation Report
    </h1>

    <h2>Summary</h2>

    <pre>
{summary}
    </pre>

    <h2>Error Breakdown</h2>

    {breakdown.to_html(index=False)}

    </body>

    </html>
    """

    output_file.write_text(
        html,
        encoding="utf-8",
    )

    return output_file


def generate_validation_report(
    validation_result: dict,
    output_dir: str | Path,
) -> dict:
    """
    Generate validation reports.

    Parameters
    ----------
    validation_result:
        Result returned by validate()

    output_dir:
        Report output directory


    Returns
    -------
    dict
        Generated report paths
    """

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = validation_result.get(
        "summary",
        {},
    )

    errors = validation_result.get(
        "errors",
        pd.DataFrame(),
    )

    # --------------------------------------------------
    # Summary report
    # --------------------------------------------------

    summary_file = output_dir / "validation_summary.csv"

    pd.DataFrame([summary]).to_csv(
        summary_file,
        index=False,
    )

    # --------------------------------------------------
    # Error report
    # --------------------------------------------------

    errors_file = output_dir / "validation_errors.csv"

    if errors.empty:

        pd.DataFrame(
            columns=[
                "employee_id",
                "rule",
                "column",
                "value",
                "message",
            ]
        ).to_csv(
            errors_file,
            index=False,
        )

    else:

        errors.to_csv(
            errors_file,
            index=False,
        )

    logger.info("Validation reports generated.")

    return {
        "summary": summary_file,
        "errors": errors_file,
    }
