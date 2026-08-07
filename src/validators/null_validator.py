"""
Required field validation.
"""

from __future__ import annotations

import pandas as pd

from src.validators.base_validator import BaseValidator


class NullValidator(BaseValidator):

    name = "null_check"

    def __init__(
        self,
        required_fields: list[str],
    ):
        self.required_fields = required_fields

    def validate(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        errors = []

        for _, row in df.iterrows():

            for field in self.required_fields:

                if (
                    field not in df.columns
                    or pd.isna(row.get(field))
                    or str(row.get(field)).strip() == ""
                ):

                    errors.append(
                        self.error(
                            row,
                            "NULL_VALUE",
                            f"Missing required field {field}",
                            field,
                        )
                    )

        return pd.DataFrame(errors)
