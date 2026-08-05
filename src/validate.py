"""
Data quality validation pipeline.

Coordinates all validation rules and produces a single
validation report for the Golden Employee Dataset.

Responsibilities
----------------
- Build validation rule set
- Execute validators
- Aggregate validation errors
- Produce validation summary

Author: Israel Kwawu
"""

from __future__ import annotations

import pandas as pd

from config.constants import (
    EMAIL_REGEX,
    EMPLOYEE_ID_REGEX,
    MIN_ANNUAL_SALARY_USD,
    MAX_ANNUAL_SALARY_USD,
)

from config.logging_config import get_logger

from src.validators.null_validator import NullValidator
from src.validators.uniqueness_validator import UniquenessValidator
from src.validators.regex_validator import RegexValidator
from src.validators.range_validator import RangeValidator
from src.validators.referential_validator import ReferentialValidator

logger = get_logger(__name__)


# ============================================================================
# Required Fields
# ============================================================================

REQUIRED_FIELDS = [
    "employee_id",
    "first_name",
    "last_name",
    "email",
    "department",
    "country",
    "employment_type",
]


# ============================================================================
# Validation Pipeline
# ============================================================================

class ValidationPipeline:
    """
    Executes all data quality validation rules.
    """

    def __init__(self) -> None:

        self.validators = [

            NullValidator(
                REQUIRED_FIELDS,
            ),

            UniquenessValidator(
                [
                    "employee_id",
                    "email",
                ],
            ),

            RegexValidator(
                {
                    "employee_id": EMPLOYEE_ID_REGEX,
                    "email": EMAIL_REGEX,
                },
            ),

            RangeValidator(
                column="salary_usd_annual",
                minimum=MIN_ANNUAL_SALARY_USD,
                maximum=MAX_ANNUAL_SALARY_USD,
            ),

            ReferentialValidator(
                source_column="manager_id",
                reference_column="employee_id",
            ),

        ]

    def validate(
        self,
        df: pd.DataFrame,
    ) -> dict:
        """
        Execute every validator.

        Parameters
        ----------
        df
            Employee dataset.

        Returns
        -------
        dict
        """

        logger.info(
            "Starting validation (%s rules)...",
            len(self.validators),
        )
        
        if df.empty:

            return {
                "passed": True,
                "errors": pd.DataFrame(
                    columns=[
                        "employee_id",
                        "rule",
                        "column",
                        "value",
                        "message",
                    ]
                ),
                "summary": {
                    "total_records": 0,
                    "passed_records": 0,
                    "failed_records": 0,
                    "total_errors": 0,
                    "validation_score": 100.0,
                    "passed": True,
                },
            }


        error_frames = []

        for validator in self.validators:

            logger.info(
                "Running %s",
                validator.name,
            )

            errors = validator.validate(df)

            if not errors.empty:
                error_frames.append(errors)

        if error_frames:

            errors = pd.concat(
                error_frames,
                ignore_index=True,
            )

        else:

            errors = pd.DataFrame(
                columns=[
                    "employee_id",
                    "rule",
                    "column",
                    "value",
                    "message",
                ]
            )

        summary = self._build_summary(
            df,
            errors,
        )

        logger.info(
            "Validation finished: %.2f%%",
            summary["validation_score"],
        )

        return {
            "passed": errors.empty,
            "errors": errors,
            "summary": summary,
        }

    @staticmethod
    def _build_summary(
        df: pd.DataFrame,
        errors: pd.DataFrame,
    ) -> dict:
        """
        Build validation metrics.
        """

        total_records = len(df)

        failed_records = (
            errors["employee_id"].nunique()
            if not errors.empty
            else 0
        )

        passed_records = (
            total_records - failed_records
        )

        validation_score = (
            round(
                passed_records
                / total_records
                * 100,
                2,
            )
            if total_records
            else 100.0
        )

        return {

            "total_records": total_records,

            "passed_records": passed_records,

            "failed_records": failed_records,

            "total_errors": len(errors),

            "validation_score": validation_score,

            "passed": errors.empty,

        }


# ============================================================================
# Public API
# ============================================================================

def validate(
    df: pd.DataFrame,
) -> dict:
    """
    Validate an employee dataset.

    Parameters
    ----------
    df
        Employee DataFrame.

    Returns
    -------
    dict
        Validation report.
    """

    pipeline = ValidationPipeline()

    return pipeline.validate(df)

