"""
Employment type normalization.

Responsibilities
----------------
- Standardize employment type values
- Map source variations
- Enforce allowed output values

Author: Israel Kwawu
"""

from __future__ import annotations


import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================
# Allowed Output Values
# ============================================================


ALLOWED_EMPLOYMENT_TYPES = {
    "Full-Time",
    "Part-Time",
    "Contractor",
    "Unknown",
}


# ============================================================
# Mapping
# ============================================================


EMPLOYMENT_TYPE_MAP = {
    # Full time
    "FT": "Full-Time",
    "FULL_TIME": "Full-Time",
    "FULL-TIME": "Full-Time",
    "FULL TIME": "Full-Time",
    "FULLTIME": "Full-Time",
    # Part time
    "PT": "Part-Time",
    "PART_TIME": "Part-Time",
    "PART-TIME": "Part-Time",
    "PART TIME": "Part-Time",
    "PARTTIME": "Part-Time",
    # Contractor
    "CT": "Contractor",
    "CONTRACT": "Contractor",
    "CONTRACTOR": "Contractor",
    "TEMP": "Contractor",
    "TEMPORARY": "Contractor",
}


# ============================================================
# Normalizer
# ============================================================


def normalize_employment_type(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize employment type column.

    Examples
    --------

    Input:

        FT
        Full-Time
        full_time
        contractor


    Output:

        Full-Time
        Full-Time
        Full-Time
        Contractor

    """

    df = df.copy()

    if "employment_type" not in df.columns:

        return df

    logger.info("Normalizing employment types...")

    df["employment_type"] = (
        df["employment_type"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.strip()
        .str.upper()
        .replace(EMPLOYMENT_TYPE_MAP)
        .where(lambda x: x.isin(ALLOWED_EMPLOYMENT_TYPES), "Unknown")
    )

    logger.info(
        "Employment types=%s",
        df["employment_type"].value_counts().to_dict(),
    )

    return df
