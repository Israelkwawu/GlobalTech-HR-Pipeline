"""
Referential integrity validation.

Responsibilities
----------------
- Validate foreign key relationships
- Detect missing references

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from src.validators.base_validator import BaseValidator


class ReferentialValidator(BaseValidator):

    name = "referential_check"

    def __init__(
        self,
        source_column: str,
        reference_column: str,
    ):
        self.source_column = source_column
        self.reference_column = reference_column

    def validate(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        errors = []

        # -----------------------------------------
        # Required columns
        # -----------------------------------------

        if self.source_column not in df.columns:

            errors.append(
                {
                    "employee_id": None,
                    "rule": "MISSING_COLUMN",
                    "column": self.source_column,
                    "value": None,
                    "message": f"Missing column '{self.source_column}'",
                }
            )

            return pd.DataFrame(errors)

        if self.reference_column not in df.columns:

            errors.append(
                {
                    "employee_id": None,
                    "rule": "MISSING_COLUMN",
                    "column": self.reference_column,
                    "value": None,
                    "message": f"Missing column '{self.reference_column}'",
                }
            )

            return pd.DataFrame(errors)

        valid_values = set(
            df[self.reference_column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        for _, row in df.iterrows():

            value = row[self.source_column]

            # CEOs / top-level employees are allowed
            if (
                pd.isna(value)
                or str(value).strip() == ""
            ):
                continue

            if str(value).strip() not in valid_values:

                errors.append(
                    self.error(
                        row=row,
                        rule="INVALID_REFERENCE",
                        message=(
                            f"{self.source_column} '{value}' "
                            "does not exist."
                        ),
                        column=self.source_column,
                    )
                )

        return pd.DataFrame(errors)
    
