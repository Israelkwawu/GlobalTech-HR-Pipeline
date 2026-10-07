"""
Benefits transformation utilities.
"""

from __future__ import annotations

import pandas as pd

from src.transformers.dates import normalize_date_column
from src.transformers.employee_id import namespace_employee_ids


def normalize_benefits(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize benefits enrollment data.

    Benefits covers GlobalTech employees, so ids are namespaced as GT-######.
    Enrollment dates such as 15-Jan-2022 use an explicit day-month-year parse.
    """

    df = df.copy()

    if df.empty:
        return df

    if "company_origin" not in df.columns:
        df["company_origin"] = "GlobalTech"

    if "employee_id" in df.columns:
        df = namespace_employee_ids(df)

    if "benefits_enrollment_date" in df.columns:
        df = normalize_date_column(
            df,
            "benefits",
            "benefits_enrollment_date",
        )

    return df
