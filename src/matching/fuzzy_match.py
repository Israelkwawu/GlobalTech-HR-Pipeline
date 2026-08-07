"""
Fuzzy employee matching.

Uses RapidFuzz to identify probable duplicate
employees based on employee names.

Responsibilities
----------------
- Compare employee names
- Detect probable duplicate employees
- Reduce comparisons using blocking
- Produce match confidence scores

Author: Israel Kwawu
"""

from __future__ import annotations


import pandas as pd

from rapidfuzz import fuzz

from config.constants import (
    FUZZY_MATCH_THRESHOLD,
)

from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Helpers
# ============================================================================


def _safe_string(
    value,
) -> str:
    """
    Convert any value into a safe string.

    Handles:
    - None
    - NaN
    - integers
    - floats
    """

    if pd.isna(value):

        return ""

    value = str(value).strip()

    if value.lower() == "nan":

        return ""

    return value


# ============================================================================
# Similarity
# ============================================================================


def similarity_score(
    left: str | None,
    right: str | None,
) -> int:
    """
    Return similarity score between two names.

    Returns
    -------
    int
        Score from 0-100.
    """

    left = _safe_string(left)

    right = _safe_string(right)

    if not left or not right:

        return 0

    return fuzz.token_sort_ratio(
        left,
        right,
    )


def is_probable_match(
    left: str,
    right: str,
    threshold: int = FUZZY_MATCH_THRESHOLD,
) -> bool:
    """
    Determine if two names are probable matches.
    """

    return (
        similarity_score(
            left,
            right,
        )
        >= threshold
    )


# ============================================================================
# Blocking
# ============================================================================


def _blocking_key(
    names: pd.Series,
) -> pd.Series:
    """
    Generate blocking key from full name.

    Example
    -------
    John Smith -> s
    Jane Doe   -> d

    Uses surname initial to reduce
    unnecessary comparisons.
    """

    names = names.apply(_safe_string).astype(str).str.strip()

    return names.str.split().str[-1].str.lower().str[0].fillna("")


# ============================================================================
# Fuzzy Matching
# ============================================================================


def fuzzy_match(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_column: str = "full_name",
    right_column: str = "full_name",
    threshold: int = FUZZY_MATCH_THRESHOLD,
) -> pd.DataFrame:
    """
    Perform fuzzy employee matching.
    """

    logger.info("Running blocked fuzzy matching...")

    # ----------------------------------------------------
    # Validate input
    # ----------------------------------------------------

    if left_column not in left.columns:

        raise KeyError(f"Missing column '{left_column}' " "in left dataframe")

    if right_column not in right.columns:

        raise KeyError(f"Missing column '{right_column}' " "in right dataframe")

    # ----------------------------------------------------
    # Empty input handling
    # ----------------------------------------------------

    empty_result = pd.DataFrame(
        columns=[
            "left_name",
            "right_name",
            "score",
            "match_method",
        ]
    )

    if left.empty or right.empty:

        return empty_result

    left = left.copy()

    right = right.copy()

    # ----------------------------------------------------
    # Normalize names
    # ----------------------------------------------------

    left[left_column] = left[left_column].apply(_safe_string)

    right[right_column] = right[right_column].apply(_safe_string)

    # Remove empty names

    left = left[left[left_column].str.len() > 2]

    right = right[right[right_column].str.len() > 2]

    if left.empty or right.empty:

        return empty_result

    # ----------------------------------------------------
    # Blocking
    # ----------------------------------------------------

    left["block"] = _blocking_key(left[left_column])

    right["block"] = _blocking_key(right[right_column])

    grouped_right = {key: group for key, group in right.groupby("block")}

    matches = []

    # ----------------------------------------------------
    # Compare candidates
    # ----------------------------------------------------

    for _, left_row in left.iterrows():

        candidates = grouped_right.get(
            left_row["block"],
            pd.DataFrame(),
        )

        if candidates.empty:

            continue

        for _, right_row in candidates.iterrows():

            score = similarity_score(
                left_row[left_column],
                right_row[right_column],
            )

            if score >= threshold:

                matches.append(
                    {
                        "left_name": left_row[left_column],
                        "right_name": right_row[right_column],
                        "score": score,
                        "match_method": "fuzzy_name",
                    }
                )

    logger.info(
        "Probable matches found: %s",
        len(matches),
    )

    if not matches:

        return empty_result

    return (
        pd.DataFrame(matches)
        .sort_values(
            by="score",
            ascending=False,
        )
        .reset_index(drop=True)
    )


# ============================================================================
# Best Match
# ============================================================================


def best_match(
    name: str,
    candidates: pd.Series,
) -> tuple[str | None, int]:
    """
    Return highest scoring candidate.
    """

    name = _safe_string(name)

    best_name = None

    best_score = 0

    for candidate in candidates:

        candidate = _safe_string(candidate)

        score = similarity_score(
            name,
            candidate,
        )

        if score > best_score:

            best_score = score

            best_name = candidate

    return (
        best_name,
        best_score,
    )
