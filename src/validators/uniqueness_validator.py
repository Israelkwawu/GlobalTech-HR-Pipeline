"""
Duplicate detection validator.

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from src.validators.base_validator import BaseValidator


class UniquenessValidator(BaseValidator):

    name = "uniqueness_check"

    def __init__(
        self,
        columns: list[str],
    ):
        self.columns = columns

    def validate(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        errors = []

        for column in self.columns:

            # ---------------------------------
            # Missing column
            # ---------------------------------

            if column not in df.columns:

                errors.append(
                    {
                        "employee_id": None,
                        "rule": "MISSING_COLUMN",
                        "column": column,
                        "value": None,
                        "message": f"Missing column '{column}'",
                    }
                )

                continue

            # ---------------------------------
            # Ignore null/blank values
            # ---------------------------------

            valid = df[
                df[column].notna()
                & (
                    df[column]
                    .astype(str)
                    .str.strip()
                    != ""
                )
            ]

            if valid.empty:
                continue

            # ---------------------------------
            # One error per duplicated value
            # ---------------------------------

            duplicate_groups = (
                valid[
                    valid[column]
                    .duplicated(keep=False)
                ]
                .groupby(column)
                .first()
                .reset_index()
            )

            for _, row in duplicate_groups.iterrows():

                errors.append(
                    self.error(
                        row=row,
                        rule="DUPLICATE",
                        message=(
                            f"Duplicate value '{row[column]}'"
                        ),
                        column=column,
                    )
                )

        return pd.DataFrame(errors)
    
