"""
Fuzzy employee matching.

Uses RapidFuzz to identify probable duplicate
employees based on employee names.

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from rapidfuzz import fuzz

from config.constants import FUZZY_MATCH_THRESHOLD
from config.logging_config import get_logger

logger = get_logger(__name__)


def similarity_score(
    left: str | None,
    right: str | None,
) -> int:
    """
    Return similarity score (0-100).
    """

    if pd.isna(left) or pd.isna(right):
        return 0

    return fuzz.token_sort_ratio(
        str(left),
        str(right),
    )


def is_probable_match(
    left: str,
    right: str,
    threshold: int = FUZZY_MATCH_THRESHOLD,
) -> bool:
    """
    Determine whether two names
    exceed the similarity threshold.
    """

    return (
        similarity_score(
            left,
            right,
        )
        >= threshold
    )


def fuzzy_match(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_column: str = "full_name",
    right_column: str = "full_name",
    threshold: int = FUZZY_MATCH_THRESHOLD,
) -> pd.DataFrame:
    """
    Compare every record in the left DataFrame
    with every record in the right DataFrame.
    """

    logger.info(
        "Running fuzzy matching..."
    )

    matches = []

    for _, l in left.iterrows():

        for _, r in right.iterrows():

            score = similarity_score(
                l[left_column],
                r[right_column],
            )

            if score >= threshold:

                matches.append(
                    {
                        "left_name": l[left_column],
                        "right_name": r[right_column],
                        "score": score,
                        "match_method": "fuzzy_name",
                    }
                )

    logger.info(
        "Probable matches: %s",
        len(matches),
    )

    return pd.DataFrame(matches)


def best_match(
    name: str,
    candidates: pd.Series,
):
    """
    Return the highest-scoring candidate.
    """

    best_name = None
    best_score = 0

    for candidate in candidates:

        score = similarity_score(
            name,
            candidate,
        )

        if score > best_score:

            best_score = score
            best_name = candidate

    return best_name, best_score

