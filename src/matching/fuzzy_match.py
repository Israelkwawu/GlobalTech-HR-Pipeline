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
    MAX_HIRE_DATE_DIFF_DAYS,
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


REVIEW_COLUMNS = [
    "record_1_id",
    "record_2_id",
    "left_name",
    "right_name",
    "similarity_score",
    "score",
    "hire_date_diff_days",
    "recommended_action",
    "probable_match",
    "match_method",
]


def _hire_date_window(
    left_date: pd.Timestamp,
    right: pd.DataFrame,
    window_days: int,
) -> pd.DataFrame:
    """
    Return right-hand rows hired within window_days of left_date.

    Candidates are taken from a date-sorted frame with a sliding window
    so the comparison stays inside the hire-date block instead of all pairs.
    """

    if pd.isna(left_date) or right.empty:
        return right.iloc[0:0]

    start = left_date - pd.Timedelta(days=window_days)
    end = left_date + pd.Timedelta(days=window_days)
    dates = right["_hire_date_sort"]
    start_at = dates.searchsorted(start, side="left")
    end_at = dates.searchsorted(end, side="right")

    return right.iloc[int(start_at) : int(end_at)]


# ============================================================================
# Fuzzy Matching
# ============================================================================


def fuzzy_match(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_column: str = "full_name",
    right_column: str = "full_name",
    threshold: int = FUZZY_MATCH_THRESHOLD,
    window_days: int = MAX_HIRE_DATE_DIFF_DAYS,
) -> pd.DataFrame:
    """
    Perform fuzzy employee matching.

    When both frames carry hire_date, candidates are limited to records
    hired within window_days of each other. Pairs at or above the
    similarity threshold are flagged for HR review and are not merged.
    """

    logger.info("Running hire-date blocked fuzzy matching...")

    if left_column not in left.columns:

        raise KeyError(f"Missing column '{left_column}' in left dataframe")

    if right_column not in right.columns:

        raise KeyError(f"Missing column '{right_column}' in right dataframe")

    empty_result = pd.DataFrame(columns=REVIEW_COLUMNS)

    if left.empty or right.empty:

        return empty_result

    left = left.copy()
    right = right.copy()

    left[left_column] = left[left_column].apply(_safe_string)
    right[right_column] = right[right_column].apply(_safe_string)

    left = left[left[left_column].str.len() > 2]
    right = right[right[right_column].str.len() > 2]

    if left.empty or right.empty:

        return empty_result

    use_hire_block = "hire_date" in left.columns and "hire_date" in right.columns

    if use_hire_block:

        right["_hire_date_sort"] = pd.to_datetime(right["hire_date"], errors="coerce")
        left["_hire_date_sort"] = pd.to_datetime(left["hire_date"], errors="coerce")
        right = right.dropna(subset=["_hire_date_sort"]).sort_values("_hire_date_sort")
        left = left.dropna(subset=["_hire_date_sort"])

    if left.empty or right.empty:

        return empty_result

    matches = []

    for _, left_row in left.iterrows():

        if use_hire_block:

            candidates = _hire_date_window(
                left_row["_hire_date_sort"],
                right,
                window_days,
            )

        else:

            candidates = right

        if candidates.empty:

            continue

        for _, right_row in candidates.iterrows():

            left_id = left_row.get("employee_id")
            right_id = right_row.get("employee_id")

            if (
                pd.notna(left_id)
                and pd.notna(right_id)
                and str(left_id) == str(right_id)
            ):

                continue

            score = similarity_score(
                left_row[left_column],
                right_row[right_column],
            )

            if score < threshold:

                continue

            if use_hire_block:

                hire_gap = abs(
                    (left_row["_hire_date_sort"] - right_row["_hire_date_sort"]).days
                )

            else:

                hire_gap = None

            pair = tuple(
                sorted(
                    str(value)
                    for value in (left_id, right_id)
                    if pd.notna(value)
                )
            )

            matches.append(
                {
                    "record_1_id": None if pd.isna(left_id) else str(left_id),
                    "record_2_id": None if pd.isna(right_id) else str(right_id),
                    "left_name": left_row[left_column],
                    "right_name": right_row[right_column],
                    "similarity_score": score,
                    "score": score,
                    "hire_date_diff_days": hire_gap,
                    "recommended_action": "HR review required before any merge",
                    "probable_match": True,
                    "match_method": "fuzzy_name",
                    "_pair": pair,
                }
            )

    logger.info("Probable matches found: %s", len(matches))

    if not matches:

        return empty_result

    review = pd.DataFrame(matches).sort_values(by="score", ascending=False)

    if review["_pair"].map(len).eq(2).any():

        review = review.drop_duplicates(subset=["_pair"])

    return review.drop(columns=["_pair"]).reset_index(drop=True)


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
