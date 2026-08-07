"""
Numeric range validation.

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from src.validators.base_validator import BaseValidator


class RangeValidator(BaseValidator):

    name = "range_check"

    def __init__(
        self,
        column: str,
        minimum: float | None = None,
        maximum: float | None = None,
    ):
        self.column = column
        self.minimum = minimum
        self.maximum = maximum

    def validate(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        errors = []

        if self.column not in df.columns:

            return pd.DataFrame(errors)

        for _, row in df.iterrows():

            value = row.get(self.column)

            if pd.isna(value):
                continue

            try:

                value = float(value)

            except ValueError:

                errors.append(
                    self.error(
                        row,
                        "INVALID_NUMBER",
                        f"{self.column} is not numeric",
                        self.column,
                    )
                )

                continue

            if self.minimum is not None and value < self.minimum:

                errors.append(
                    self.error(
                        row,
                        "BELOW_MINIMUM",
                        (f"{self.column} " f"below minimum " f"{self.minimum}"),
                        self.column,
                    )
                )

            if self.maximum is not None and value > self.maximum:

                errors.append(
                    self.error(
                        row,
                        "ABOVE_MAXIMUM",
                        (f"{self.column} " f"above maximum " f"{self.maximum}"),
                        self.column,
                    )
                )

        return pd.DataFrame(errors)
