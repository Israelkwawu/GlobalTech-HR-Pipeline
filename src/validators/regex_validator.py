"""
Regex based validation.

Responsibilities
----------------
- Validate employee IDs
- Validate email addresses
- Apply regex rules to DataFrames

Author: Israel Kwawu
"""

from __future__ import annotations

import re

import pandas as pd

from src.validators.base_validator import BaseValidator


class RegexValidator(BaseValidator):

    name = "regex_check"


    def __init__(
        self,
        rules: dict[str, str],
    ):
        """
        Parameters
        ----------
        rules:
            Mapping of column -> regex pattern

        Example:

        {
            "employee_id": r"^(GT|AC)-\\d{6}$",
            "email": EMAIL_REGEX
        }
        """

        self.rules = rules


    def validate(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        errors = []

        for _, row in df.iterrows():

            for column, pattern in self.rules.items():

                if column not in df.columns:
                    continue


                value = row.get(column)


                if pd.isna(value):

                    continue


                if not re.fullmatch(
                    pattern,
                    str(value),
                ):

                    errors.append(
                        self.error(
                            row,
                            "REGEX_FAILURE",
                            f"Invalid format for {column}",
                            column,
                        )
                    )


        return pd.DataFrame(errors)
    
