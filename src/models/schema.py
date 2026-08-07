"""
Schema utilities for the GlobalTech HR Data Integration Pipeline.

This module provides reusable helpers for validating and enforcing
DataFrame schemas. It is intentionally generic so it can support
multiple schema definitions (e.g., employee, payroll, benefits).

Author: Israel Kwawu
"""

from __future__ import annotations

from typing import Dict, Iterable, List

import pandas as pd


class SchemaValidationError(Exception):
    """Raised when a DataFrame does not satisfy the expected schema."""


class DataFrameSchema:
    """
    Represents a tabular schema for a pandas DataFrame.

    Parameters
    ----------
    columns : list[str]
        Expected column order.
    dtypes : dict[str, str]
        Mapping of column names to pandas dtype strings.
    required_fields : list[str]
        Columns that must exist in the DataFrame.
    optional_fields : list[str], optional
        Optional columns that may or may not exist.
    """

    def __init__(
        self,
        columns: List[str],
        dtypes: Dict[str, str],
        required_fields: List[str],
        optional_fields: List[str] | None = None,
    ) -> None:
        self.columns = columns
        self.dtypes = dtypes
        self.required_fields = required_fields
        self.optional_fields = optional_fields or []

    def validate_columns(self, df: pd.DataFrame) -> None:
        """
        Validate that all required columns exist.

        Raises
        ------
        SchemaValidationError
            If any required columns are missing.
        """
        missing = [col for col in self.required_fields if col not in df.columns]

        if missing:
            raise SchemaValidationError(f"Missing required columns: {missing}")

    def validate_dtypes(self, df: pd.DataFrame) -> None:
        """
        Validate DataFrame column data types.

        Raises
        ------
        SchemaValidationError
            If any column has an unexpected dtype.
        """
        mismatches = {}

        for column, expected_dtype in self.dtypes.items():

            if column not in df.columns:
                continue

            actual_dtype = str(df[column].dtype)

            if actual_dtype != expected_dtype:
                mismatches[column] = {
                    "expected": expected_dtype,
                    "actual": actual_dtype,
                }

        if mismatches:
            raise SchemaValidationError(f"Schema dtype mismatch: {mismatches}")

    def enforce_column_order(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Return a DataFrame with columns ordered
        according to the schema.
        """
        existing = [c for c in self.columns if c in df.columns]
        remaining = [c for c in df.columns if c not in existing]

        return df[existing + remaining]

    def add_missing_optional_columns(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Add optional columns that do not exist.

        Missing columns are initialized with pandas.NA.
        """
        for column in self.optional_fields:

            if column not in df.columns:
                df[column] = pd.NA

        return df

    def cast_dtypes(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Cast DataFrame columns to the schema dtypes
        where possible.
        """
        for column, dtype in self.dtypes.items():

            if column not in df.columns:
                continue

            try:
                df[column] = df[column].astype(dtype)

            except (TypeError, ValueError):
                # Leave conversion errors for validation
                pass

        return df

    def validate(
        self,
        df: pd.DataFrame,
    ) -> None:
        """
        Perform complete schema validation.
        """
        self.validate_columns(df)
        self.validate_dtypes(df)

    def apply(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Apply schema normalization.

        Steps
        -----
        1. Validate required columns
        2. Add missing optional columns
        3. Cast dtypes
        4. Reorder columns

        Returns
        -------
        pandas.DataFrame
        """
        self.validate_columns(df)

        df = self.add_missing_optional_columns(df)
        df = self.cast_dtypes(df)
        df = self.enforce_column_order(df)

        return df
