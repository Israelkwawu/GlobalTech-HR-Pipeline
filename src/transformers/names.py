"""
Name transformation utilities.

Standardizes employee names by:

- Unicode normalization
- Trimming whitespace
- Collapsing multiple spaces
- Proper title casing
- Preserving apostrophes
- Preserving hyphenated names
- Handling common surname particles

Author: Israel Kwawu
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)

# Common surname particles that should remain lowercase
LOWERCASE_PARTICLES = {
    "de",
    "del",
    "der",
    "van",
    "von",
    "da",
    "dos",
    "di",
    "la",
    "le",
    "du",
}


def normalize_unicode(value: str | None) -> str | None:
    """
    Normalize Unicode characters.

    Example:
        José -> José
    """

    if pd.isna(value):
        return value

    return unicodedata.normalize("NFC", str(value))


def clean_whitespace(value: str | None) -> str | None:
    """
    Remove leading/trailing whitespace and collapse
    multiple internal spaces.
    """

    if pd.isna(value):
        return value

    value = str(value).strip()

    value = re.sub(r"\s+", " ", value)

    return value


def title_case_name(value: str | None) -> str | None:
    """
    Convert names to title case while preserving
    apostrophes, hyphens and surname particles.

    Examples
    --------
    john smith
        -> John Smith

    o'brien
        -> O'Brien

    anne-marie
        -> Anne-Marie

    van der berg
        -> Van der Berg
    """

    if pd.isna(value):
        return value

    value = clean_whitespace(value)

    words = value.split()

    formatted = []

    for index, word in enumerate(words):

        lower = word.lower()

        if index > 0 and lower in LOWERCASE_PARTICLES:
            formatted.append(lower)
            continue

        pieces = []

        for hyphen_piece in word.split("-"):

            apostrophe_parts = [part.capitalize() for part in hyphen_piece.split("'")]

            pieces.append("'".join(apostrophe_parts))

        formatted.append("-".join(pieces))

    return " ".join(formatted)


def standardize_name(value: str | None) -> str | None:
    """
    Apply all standardization steps.
    """

    if pd.isna(value):
        return value

    value = normalize_unicode(value)

    value = clean_whitespace(value)

    value = title_case_name(value)

    return value


def standardize_names(
    df: pd.DataFrame,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Standardize name columns in a DataFrame.

    Parameters
    ----------
    df
        Input DataFrame.

    columns
        Name columns to standardize.

    Returns
    -------
    pd.DataFrame
    """

    if columns is None:
        columns = [
            "first_name",
            "last_name",
        ]

    df = df.copy()

    for column in columns:

        if column not in df.columns:
            continue

        logger.info(
            "Standardizing %s",
            column,
        )

        df[column] = df[column].apply(standardize_name)

    return df
