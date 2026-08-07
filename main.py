"""
GlobalTech HR Data Integration Pipeline CLI.

Application entry point.

Responsibilities
----------------
- Start pipeline execution
- Handle command line arguments
- Configure output directory
- Display pipeline summary

Author: Israel Kwawu
"""

from __future__ import annotations


import argparse
import sys
from pathlib import Path


from config.logging_config import (
    configure_logging,
    get_logger
)

from src.pipeline import run_pipeline


configure_logging()
logger = get_logger(__name__)


# ============================================================
# CLI Arguments
# ============================================================

def create_parser() -> argparse.ArgumentParser:
    """
    Create CLI argument parser.
    """

    parser = argparse.ArgumentParser(
        description=(
            "GlobalTech HR Data Integration Pipeline"
        )
    )

    parser.add_argument(
        "--output",
        "-o",
        default="outputs",
        help=(
            "Output directory "
            "(default: outputs)"
        ),
    )

    return parser


# ============================================================
# Helpers
# ============================================================

def calculate_validation_score(
    summary: dict,
) -> float:
    """
    Calculate validation score.

    Score:
        passed records / total records * 100
    """

    total = summary.get(
        "total_records",
        0,
    )

    failed = summary.get(
        "failed_records",
        0,
    )

    if total == 0:
        return 100.0

    passed = total - failed

    return round(
        (passed / total) * 100,
        2,
    )



def display_charts(
    charts,
):
    """
    Display generated charts safely.
    """

    if not charts:

        return


    # Dictionary format

    if isinstance(
        charts,
        dict,
    ):

        for name, path in charts.items():

            print(
                f" - {name}: {path}"
            )

        return


    # List format

    if isinstance(
        charts,
        list,
    ):

        for chart in charts:

            print(
                f" - {chart}"
            )

        return


    print(
        f" - {charts}"
    )


# ============================================================
# Pipeline Runner
# ============================================================

def main() -> int:
    """
    Execute pipeline.

    Returns
    -------
    int
        Exit code.
    """

    parser = create_parser()

    args = parser.parse_args()


    output_dir = Path(
        args.output
    )


    try:

        logger.info(
            "Launching HR pipeline..."
        )


        result = run_pipeline(
            output_dir
        )


        validation = result.get(
            "validation",
            {},
        )


        summary = validation.get(
            "summary",
            {},
        )


        # ----------------------------------------------------
        # Backward compatible summary fields
        # ----------------------------------------------------

        total_records = summary.get(
            "total_records",
            0,
        )


        validation_score = summary.get(
            "validation_score",
            calculate_validation_score(summary),
        )


        failed_records = summary.get(
            "failed_records",
            0,
        )


        pipeline_status = summary.get(
            "pipeline_passed",
            True,
        )


        logger.info(
            "Pipeline completed successfully"
        )


        export_result = result.get(
            "export",
            "No export information available",
        )


        display_charts(
            result.get(
                "charts"
            )
        )


        return 0



    except Exception as exc:

        logger.exception(
            "Pipeline failed: %s",
            exc,
        )


        return 1



# ============================================================
# Program Entry
# ============================================================

if __name__ == "__main__":

    sys.exit(
        main()
    )
    
