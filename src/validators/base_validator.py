"""
Base validator framework.

All validators inherit from this class.

Author: Israel Kwawu
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class BaseValidator(ABC):
    """
    Abstract validation class.
    """

    name: str = "base"

    @abstractmethod
    def validate(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Validate dataframe.

        Returns
        -------
        DataFrame
            Validation errors.
        """
        pass


    def error(
        self,
        row,
        rule: str,
        message: str,
        column: str | None = None,
    ) -> dict:
        """
        Create validation error record.
        """

        return {
            "employee_id": row.get(
                "employee_id"
            ),
            "rule": rule,
            "column": column,
            "value": (
                row.get(column)
                if column
                else None
            ),
            "message": message,
        }
        
