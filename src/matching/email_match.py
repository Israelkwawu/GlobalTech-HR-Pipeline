"""
Email matching utilities.

Matches employee records using normalized email addresses.

Responsibilities
----------------
- Normalize email addresses
- Perform exact email matching
- Identify unmatched records
- Validate email uniqueness

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


def normalize_email(
    email: str | None,
) -> str | None:
    """
    Normalize an email address.

    Examples
    --------
    " John.Smith@Example.com "
        -> "john.smith@example.com"
    """

    if pd.isna(email):
        return None

    return str(email).strip().lower()


def normalize_email_column(
    df: pd.DataFrame,
    column: str = "email",
) -> pd.DataFrame:
    """
    Normalize a DataFrame email column.
    """

    df = df.copy()

    if column not in df.columns:
        raise KeyError(f"Missing '{column}' column.")

    logger.info("Normalizing email column...")

    df[column] = df[column].apply(normalize_email)

    return df


def email_match(
    left: pd.DataFrame,
    right: pd.DataFrame,
    email_column: str = "email",
) -> pd.DataFrame:
    """
    Match employees using email addresses.

    Parameters
    ----------
    left
        Primary employee dataset.

    right
        Secondary employee dataset.

    email_column
        Email column name.

    Returns
    -------
    pd.DataFrame
        Matched employee pairs.
    """

    if email_column not in left.columns:
        raise KeyError(f"Missing '{email_column}' in left DataFrame.")

    if email_column not in right.columns:
        raise KeyError(f"Missing '{email_column}' in right DataFrame.")

    logger.info("Running email matching...")

    left = normalize_email_column(
        left,
        email_column,
    )

    right = normalize_email_column(
        right,
        email_column,
    )

    matches = left.merge(
        right,
        how="inner",
        on=email_column,
        suffixes=(
            "_left",
            "_right",
        ),
    )

    matches["match_method"] = "email_match"

    logger.info(
        "Email matches found: %s",
        len(matches),
    )

    return matches


def unmatched_emails(
    left: pd.DataFrame,
    right: pd.DataFrame,
    email_column: str = "email",
) -> pd.DataFrame:
    """
    Return records in the left DataFrame whose email
    does not exist in the right DataFrame.
    """

    left = normalize_email_column(
        left,
        email_column,
    )

    right = normalize_email_column(
        right,
        email_column,
    )

    unmatched = left[~left[email_column].isin(right[email_column])].copy()

    logger.info(
        "Unmatched emails: %s",
        len(unmatched),
    )

    return unmatched


def duplicate_emails(
    df: pd.DataFrame,
    email_column: str = "email",
) -> pd.DataFrame:
    """
    Return duplicate email records within a DataFrame.
    """

    df = normalize_email_column(
        df,
        email_column,
    )

    duplicates = df[
        df.duplicated(
            subset=email_column,
            keep=False,
        )
    ].sort_values(email_column)

    logger.info(
        "Duplicate emails found: %s",
        len(duplicates),
    )

    return duplicates


def validate_unique_emails(
    df: pd.DataFrame,
    email_column: str = "email",
) -> pd.Series:
    """
    Return a boolean Series indicating whether each email
    address is unique within the DataFrame.
    """

    df = normalize_email_column(
        df,
        email_column,
    )

    return ~df.duplicated(
        subset=email_column,
        keep=False,
    )
