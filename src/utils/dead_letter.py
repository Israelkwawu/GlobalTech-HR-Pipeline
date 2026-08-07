"""
Dead Letter Queue utilities.

Records that cannot be processed are written to the dead-letter log
instead of terminating the pipeline.

Author: Israel Kwawu
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import csv
from typing import Any

from config.logging_config import get_logger
from config.settings import DEAD_LETTER_DIR

logger = get_logger(__name__)

DEAD_LETTER_FILE = DEAD_LETTER_DIR / "dead_letter_log.csv"

HEADERS = [
    "timestamp",
    "source_system",
    "file_name",
    "record_identifier",
    "error_type",
    "error_message",
    "raw_record",
]


def _initialize_dead_letter_file() -> None:
    """
    Create the dead-letter CSV if it does not exist.
    """

    DEAD_LETTER_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if DEAD_LETTER_FILE.exists():
        return

    with open(
        DEAD_LETTER_FILE,
        mode="w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=HEADERS,
        )

        writer.writeheader()


def write_dead_letter(
    *,
    source_system: str,
    file_name: str,
    error: Exception,
    raw_record: Any | None = None,
    record_identifier: str | None = None,
) -> None:
    """
    Write a failed record to the dead-letter log.

    Parameters
    ----------
    source_system : str
        Source system name.

    file_name : str
        Source file.

    error : Exception
        Exception that occurred.

    raw_record : Any, optional
        Original record that failed.

    record_identifier : str, optional
        Employee ID or other unique identifier.
    """

    _initialize_dead_letter_file()

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_system": source_system,
        "file_name": file_name,
        "record_identifier": record_identifier,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "raw_record": str(raw_record),
    }

    with open(
        DEAD_LETTER_FILE,
        mode="a",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=HEADERS,
        )

        writer.writerow(row)

    logger.warning(
        "Dead-letter record written for source '%s'.",
        source_system,
    )


def dead_letter_count() -> int:
    """
    Return the number of dead-letter records.
    """

    if not DEAD_LETTER_FILE.exists():
        return 0

    with open(
        DEAD_LETTER_FILE,
        encoding="utf-8",
    ) as file:

        return max(sum(1 for _ in file) - 1, 0)


def clear_dead_letter_log() -> None:
    """
    Remove the dead-letter log.
    Useful during testing.
    """

    if DEAD_LETTER_FILE.exists():
        DEAD_LETTER_FILE.unlink()

    logger.info("Dead-letter log cleared.")
