"""
Benefits transformation utilities.
"""

from __future__ import annotations

import pandas as pd


def normalize_benefits(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize benefits enrollment data.
    """

    df = df.copy()

    if df.empty:
        return df

    if "benefits_enrollment_date" in df.columns:

        df["benefits_enrollment_date"] = pd.to_datetime(
            df["benefits_enrollment_date"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

    return df
