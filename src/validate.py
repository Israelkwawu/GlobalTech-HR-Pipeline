"""
Data quality validation pipeline.

Responsibilities
----------------
- Validate Golden Employee Dataset
- Execute data quality checks
- Produce validation report
- Produce validation errors
- Enforce pipeline quality gate

Author: Israel Kwawu
"""

from __future__ import annotations


from datetime import datetime

from pathlib import Path

import re

import pandas as pd


from config.logging_config import get_logger

from config import validation_rules as rules

from src.validators.null_validator import NullValidator
from src.validators.range_validator import RangeValidator
from src.validators.referential_validator import ReferentialValidator
from src.validators.regex_validator import RegexValidator
from src.validators.uniqueness_validator import UniquenessValidator

logger = get_logger(__name__)


# ============================================================================
# Validator
# ============================================================================


class DataQualityValidator:
    """
    Executes data quality checks against golden employee dataset.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        output_dir: str | Path = "outputs",
    ) -> None:

        self.df = df.copy()

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.results: list[dict] = []

        self.errors: list[list] = []

        # ------------------------------------------------------------
        # Pre-validation normalization
        # ------------------------------------------------------------

        self._normalize_columns()

    # ========================================================================
    # Main Validation Entry
    # ========================================================================

    def validate(
        self,
    ) -> dict:
        """
        Execute all validation checks.
        """

        logger.info("Starting data quality validation...")

        self._check_required_fields()

        self._check_unique_fields()

        self._check_allowed_values()

        self._check_regex_rules()

        self._check_salary_range()

        self._check_hire_date_range()

        self._check_manager_reference()

        report = pd.DataFrame(self.results)

        errors = pd.DataFrame(
            self.errors,
            columns=[
                "employee_id",
                "check",
                "column",
                "value",
                "message",
            ],
        )

        summary = self._build_summary(report)

        # Export even when failed

        self._export_reports(
            report,
            errors,
        )

        logger.error(
            """
========== VALIDATION ERRORS ==========

%s

========================================
""",
            ("\n".join(map(str, self.errors)) if self.errors else "No errors"),
        )

        self._pipeline_gate(summary)

        return {
            "pipeline_passed": summary["pipeline_passed"],
            "checks_run": summary["checks_run"],
            "passed_checks": summary["passed_checks"],
            "failed_checks": summary["failed_checks"],
            "report": report,
            "errors": errors,
            "summary": summary,
        }

    # ========================================================================
    # Normalization Before Validation
    # ========================================================================

    def _normalize_columns(
        self,
    ):
        """
        Normalize fields before checks.

        Prevents false failures caused by:
        - email casing
        - whitespace
        - employment type casing
        - numeric IDs
        """

        # ------------------------------------------------------------
        # Email normalization
        # ------------------------------------------------------------

        if "email" in self.df.columns:

            self.df["email"] = self.df["email"].astype("string").str.strip().str.lower()

            self.df["email"] = self.df["email"].replace(
                {
                    "": None,
                    "nan": None,
                }
            )

        # ------------------------------------------------------------
        # Employee IDs
        # ------------------------------------------------------------

        for column in [
            "employee_id",
            "manager_id",
        ]:

            if column in self.df.columns:

                self.df[column] = self.df[column].astype("string").str.strip()

        # ------------------------------------------------------------
        # Employment type
        # ------------------------------------------------------------

        if "employment_type" in self.df.columns:

            self.df["employment_type"] = (
                self.df["employment_type"].astype("string").str.strip().str.title()
            )

        logger.info("Validation normalization complete.")

    # ========================================================================
    # Required Fields
    # ========================================================================

    def _check_required_fields(
        self,
    ):
        """
        Check required columns are populated.
        """

        validator = NullValidator(list(rules.REQUIRED_FIELDS))
        findings = validator.validate(self.df)

        for column in rules.REQUIRED_FIELDS:

            check = f"{column}_not_null"

            if column not in self.df.columns:

                self._record_missing_column(
                    check,
                    f"{column} must exist and not be null",
                )

                continue

            if findings.empty or "column" not in findings.columns:

                failed_rows = self.df.iloc[0:0]

            else:

                failed_ids = findings.loc[
                    findings["column"] == column,
                    "employee_id",
                ]

                failed_rows = self.df[self.df["employee_id"].isin(failed_ids)]

                if failed_rows.empty and not findings.loc[findings["column"] == column].empty:

                    failed_rows = self.df[
                        self.df[column].isna()
                        | self.df[column].astype(str).str.strip().eq("")
                    ]

            self._add_errors(
                failed_rows,
                check,
                column,
                f"{column} cannot be null",
            )

            failed = len(failed_rows)

            self._record_result(
                check,
                f"{column} must not be null",
                len(self.df),
                len(self.df) - failed,
                failed,
            )

    # ========================================================================
    # Unique Field Checks
    # ========================================================================

    def _check_unique_fields(
        self,
    ):
        """
        Validate unique columns.

        Empty values are ignored.

        Example:

            email = None

        is not considered a duplicate.
        """

        uniqueness = UniquenessValidator(list(rules.UNIQUE_FIELDS))
        uniqueness.validate(self.df)

        for column in rules.UNIQUE_FIELDS:

            if column not in self.df.columns:

                self._record_missing_column(
                    f"{column}_unique",
                    f"{column} must exist and be unique",
                )

                continue

            populated = self.df[column].notna() & (
                self.df[column].astype(str).str.strip().ne("")
            )

            duplicates = self.df[column].duplicated(keep=False) & populated

            failed_rows = self.df[duplicates]

            self._add_errors(
                failed_rows,
                f"{column}_unique",
                column,
                f"{column} contains duplicates",
            )

            failed = len(failed_rows)

            self._record_result(
                f"{column}_unique",
                f"{column} must be unique",
                len(self.df),
                len(self.df) - failed,
                failed,
            )

    # ========================================================================
    # Allowed Values
    # ========================================================================

    def _check_allowed_values(
        self,
    ):
        """
        Validate allowed enum values.

        Handles:

        Full-Time
        FULL-TIME
        full_time

        as equivalent.
        """

        checks = {
            "employment_type": rules.ALLOWED_EMPLOYMENT_TYPES,
            "currency": rules.ALLOWED_CURRENCIES,
        }

        for column, allowed in checks.items():

            if column not in self.df.columns:

                self._record_missing_column(
                    f"{column}_values",
                    f"{column} must exist and be in the allowed set",
                )

                continue

            normalized_allowed = {
                str(value).strip().replace("_", "-").title() for value in allowed
            }

            values = (
                self.df[column]
                .astype("string")
                .str.strip()
                .str.replace(
                    "_",
                    "-",
                    regex=False,
                )
                .str.title()
            )

            invalid = ~values.isin(normalized_allowed) & values.notna()

            failed_rows = self.df[invalid]

            self._add_errors(
                failed_rows,
                f"{column}_values",
                column,
                f"Invalid {column} value",
            )

            failed = len(failed_rows)

            self._record_result(
                f"{column}_values",
                f"{column} must be in allowed set",
                len(self.df),
                len(self.df) - failed,
                failed,
            )

    # ========================================================================
    # Regex Validation
    # ========================================================================

    def _check_regex_rules(
        self,
    ):
        """
        Validate regex based fields.
        Example:
        email format
        employee ID format
        """

        for column, pattern in rules.REGEX_RULES.items():

            if column not in self.df.columns:

                self._record_missing_column(
                    f"{column}_regex",
                    f"{column} must exist and match the required format",
                )

                continue

            findings = RegexValidator({column: pattern}).validate(self.df)

            if findings.empty or "value" not in findings.columns:

                failed_rows = self.df.iloc[0:0]

            else:

                failed_values = set(findings["value"].dropna().astype(str))

                failed_rows = self.df[
                    self.df[column].astype("string").isin(failed_values)
                ]

            self._add_errors(
                failed_rows,
                f"{column}_regex",
                column,
                "Invalid format",
            )

            failed = len(failed_rows)

            self._record_result(
                f"{column}_regex",
                f"{column} matches required format",
                len(self.df),
                len(self.df) - failed,
                failed,
            )

    # ========================================================================
    # Salary Validation
    # ========================================================================

    # ========================================================================
    # Salary Validation
    # ========================================================================

    def _check_salary_range(self):
        """
        Validate annual salary values.

        Rules
        -----
        - Salary validation only applies to employees with payroll data.
        - Missing salary is allowed because:
            * HRIS may contain employees before payroll migration.
            * Contractors may not have payroll records.
            * New hires may not yet be processed.
        - Missing salary is logged as payroll coverage information.
        - Salary outside configured limits fails validation.
        """

        column = "salary_usd_annual"

        # ------------------------------------------------------------
        # Skip if salary column does not exist
        # ------------------------------------------------------------

        if column not in self.df.columns:

            RangeValidator(
                column,
                rules.NUMERIC_RANGES[column]["minimum"],
                rules.NUMERIC_RANGES[column]["maximum"],
            ).validate(self.df)

            self._record_missing_column(
                "salary_range",
                "salary_usd_annual must exist before range checks",
            )

            logger.error("Salary validation failed. Missing column=%s", column)

            return

        # ------------------------------------------------------------
        # Convert salary values
        # ------------------------------------------------------------

        values = pd.to_numeric(
            self.df[column],
            errors="coerce",
        )

        # ------------------------------------------------------------
        # Employees with payroll salary
        # ------------------------------------------------------------

        has_salary = values.notna()

        # ------------------------------------------------------------
        # Validate only available salaries
        # ------------------------------------------------------------

        minimum_salary = rules.NUMERIC_RANGES[column]["minimum"]

        maximum_salary = rules.NUMERIC_RANGES[column]["maximum"]

        RangeValidator(
            column,
            minimum_salary,
            maximum_salary,
        ).validate(self.df)

        invalid = has_salary & ((values < minimum_salary) | (values > maximum_salary))

        failed_rows = self.df[invalid]

        self._add_errors(
            failed_rows,
            "salary_range",
            column,
            (f"Salary must be between " f"{minimum_salary} and {maximum_salary}"),
        )

        failed = len(failed_rows)

        validated_records = int(has_salary.sum())

        self._record_result(
            "salary_range",
            "Salary between allowed limits",
            validated_records,
            validated_records - failed,
            failed,
        )

        # ------------------------------------------------------------
        # Payroll coverage logging
        # ------------------------------------------------------------

        missing_salary_count = int((~has_salary).sum())

        logger.info(
            """
========== SALARY VALIDATION ==========

Total employees:
%s

Employees with payroll salary:
%s

Employees without payroll salary:
%s

Salary validation failures:
%s

Allowed range:
%s - %s

======================================

""",
            len(self.df),
            validated_records,
            missing_salary_count,
            failed,
            minimum_salary,
            maximum_salary,
        )

    # ========================================================================
    # Hire Date Validation
    # ========================================================================

    def _check_hire_date_range(
        self,
    ):
        """
        Validate employee hire dates.

        Missing dates are allowed because:
        - Some acquired employees may have incomplete HR records.
        - Missing dates are handled as data quality warnings.
        """

        column = "hire_date"

        if column not in self.df.columns:

            self._record_missing_column(
                "hire_date_range",
                "hire_date must exist and fall between 1970-01-01 and today",
            )

            return

        dates = pd.to_datetime(
            self.df[column],
            errors="coerce",
        )

        config = rules.DATE_RANGES.get(column)

        if not config:
            return

        minimum = pd.Timestamp(config["minimum"]).normalize()

        maximum = pd.Timestamp(config["maximum"]).normalize()

        dates = dates.dt.normalize()

        invalid = dates.notna() & ((dates < minimum) | (dates > maximum))

        failed_rows = self.df[invalid]

        self._add_errors(
            failed_rows,
            "hire_date_range",
            column,
            "Invalid hire date",
        )

        failed = len(failed_rows)

        self._record_result(
            "hire_date_range",
            "Hire date between valid range",
            len(self.df),
            len(self.df) - failed,
            failed,
        )

        logger.info(
            """
    ========== HIRE DATE VALIDATION ==========

    Total employees:
    %s

    Missing hire dates:
    %s

    Invalid hire dates:
    %s

    ==========================================
    """,
            len(self.df),
            int(dates.isna().sum()),
            failed,
        )

    # ========================================================================
    # Manager Reference Validation
    # ========================================================================

    def _check_manager_reference(
        self,
    ):
        """
        Validate manager references.

        Rules:
        - Empty manager IDs are allowed
        - Manager must exist in employee_id
        - Self references are allowed
        - Handles namespaced IDs

        Example:

            employee_id
                GT-000001

            manager_id
                GT-000010

            GT-000010 must exist
        """

        findings = ReferentialValidator(
            "manager_id",
            "employee_id",
        ).validate(self.df)

        if "manager_id" not in self.df.columns or "employee_id" not in self.df.columns:

            self._record_missing_column(
                "manager_reference",
                "manager_id and employee_id must exist for referential checks",
            )

            return

        if findings.empty or "value" not in findings.columns:

            failed_rows = self.df.iloc[0:0]

        else:

            invalid_manager_ids = set(findings["value"].dropna().astype(str).str.strip())

            failed_rows = self.df[
                self.df["manager_id"].astype("string").str.strip().isin(invalid_manager_ids)
            ]

        self._add_errors(
            failed_rows,
            "manager_reference",
            "manager_id",
            "Manager does not exist",
        )

        failed = len(failed_rows)

        self._record_result(
            "manager_reference",
            "Manager IDs must exist",
            len(self.df),
            len(self.df) - failed,
            failed,
        )

    # ========================================================================
    # Result Helpers
    # ========================================================================

    def _record_result(
        self,
        check: str,
        description: str,
        total: int,
        passed: int,
        failed: int,
    ):
        """
        Store validation result.
        """

        if total:
            pass_rate = round(passed / total * 100, 2)
        elif failed:
            pass_rate = 0.0
        else:
            pass_rate = 100.0

        self.results.append(
            {
                "check": check,
                "description": description,
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": pass_rate,
                "status": "FAIL" if failed else "PASS",
            }
        )

    def _record_missing_column(
        self,
        check: str,
        description: str,
    ):
        """
        A check cannot pass when the column it guards is absent.

        Empty frames still fail the check so a missing critical field
        is never reported as a 100% pass.
        """

        total = max(len(self.df), 1)

        self._record_result(
            check,
            description,
            total,
            0,
            total,
        )

    def _add_errors(
        self,
        rows: pd.DataFrame,
        check: str,
        column: str,
        message: str,
    ):
        """
        Collect validation failures.
        """

        for _, row in rows.iterrows():

            self.errors.append(
                [
                    row.get("employee_id"),
                    check,
                    column,
                    row.get(column),
                    message,
                ]
            )

    # ========================================================================
    # Summary
    # ========================================================================

    def _build_summary(
        self,
        report: pd.DataFrame,
    ) -> dict:
        """
        Build validation summary.

        Includes:
        - record counts
        - check counts
        - validation score
        - pipeline status
        """

        # Number of validation checks

        total_checks = len(report)

        failed_checks = int((report["status"] == "FAIL").sum())

        passed_checks = int((report["status"] == "PASS").sum())

        # --------------------------------------------------------
        # Dataset record counts
        # --------------------------------------------------------

        total_records = len(self.df)

        failed_records = int(report["failed"].sum())

        # Avoid counting failed checks multiple times
        if failed_records > total_records:

            failed_records = total_records

        passed_records = total_records - failed_records

        validation_score = (
            round(
                (passed_records / total_records) * 100,
                2,
            )
            if total_records
            else 100.0
        )

        failure_rate = (
            round(
                (failed_records / total_records) * 100,
                2,
            )
            if total_records
            else 0
        )

        # The delivery gate counts failed checks, not the row failure rate.
        # The pipeline halts only when more than MAX_FAILED_CHECKS fail.
        pipeline_passed = failed_checks <= rules.MAX_FAILED_CHECKS

        return {
            # Timestamp
            "generated_at": datetime.utcnow().isoformat(),
            # Validation checks
            "checks_run": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            # Records
            "total_records": total_records,
            "passed_records": passed_records,
            "failed_records": failed_records,
            # Scores
            "validation_score": validation_score,
            "failure_rate": failure_rate,
            # Gate
            "pipeline_passed": pipeline_passed,
        }

    # ========================================================================
    # Quality Gate
    # ========================================================================

    def _pipeline_gate(
        self,
        summary: dict,
    ):
        """
        Stop pipeline when quality threshold fails.
        """

        if not summary["pipeline_passed"]:

            logger.critical(
                "Pipeline blocked. " "Failed checks=%s Failure rate=%s%%",
                summary["failed_checks"],
                summary["failure_rate"],
            )

            logger.error(
                """
========== VALIDATION ERRORS ==========

%s

========================================
""",
                self.errors,
            )

            logger.error(
                """
========== QUALITY GATE FAILURE ==========

Summary:
%s

==========================================
""",
                summary,
            )

            raise RuntimeError("Data quality gate failed")

    # ========================================================================
    # Export Reports
    # ========================================================================

    def _export_reports(
        self,
        report: pd.DataFrame,
        errors: pd.DataFrame,
    ):
        """
        Export validation reports.
        """

        report.to_csv(
            self.output_dir / "validation_report.csv",
            index=False,
        )

        report.to_html(
            self.output_dir / "validation_report.html",
            index=False,
        )

        errors.to_csv(
            self.output_dir / "validation_errors.csv",
            index=False,
        )


# ============================================================================
# Public API
# ============================================================================


def validate(
    df: pd.DataFrame,
    output_dir: str | Path = "outputs",
) -> dict:
    """
    Validate golden employee dataset.
    """

    validator = DataQualityValidator(
        df,
        output_dir,
    )

    return validator.validate()
