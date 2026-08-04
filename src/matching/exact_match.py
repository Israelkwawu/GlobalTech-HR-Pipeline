"""
Exact employee matching.

Matches employees using unique employee IDs.

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from config.logging_config import get_logger


logger = get_logger(__name__)


def exact_employee_match(
    left: pd.DataFrame,
    right: pd.DataFrame,
    id_column: str = "employee_id",
) -> pd.DataFrame:
    """
    Match employees using exact employee ID.

    Parameters
    ----------
    left
        Primary employee dataset.

    right
        Secondary dataset.

    id_column
        Employee identifier column.

    Returns
    -------
    DataFrame
        Matched employee pairs.
    """

    logger.info(
        "Running exact employee ID matching..."
    )

    if id_column not in left.columns:
        raise KeyError(
            f"Missing {id_column}"
        )

    if id_column not in right.columns:
        raise KeyError(
            f"Missing {id_column}"
        )


    matches = left.merge(
        right,
        on=id_column,
        how="inner",
        suffixes=(
            "_left",
            "_right",
        ),
    )


    matches["match_method"] = (
        "exact_id"
    )

    logger.info(
        "Exact matches found: %s",
        len(matches),
    )

    return matches
