"""
GlobalTech HR Data Integration Pipeline.

Responsibilities
----------------
- Execute complete ETL workflow
- Ingest source systems
- Clean employee data
- Deduplicate employees
- Validate golden dataset
- Generate reports
- Export datasets
- Generate visualizations

Author: Israel Kwawu
"""

from __future__ import annotations


from pathlib import Path
import json


import pandas as pd


from config.logging_config import get_logger

# ============================================================
# Pipeline Components
# ============================================================

from src.ingest import (
    load_globaltech_hris,
    load_acquiredco_hris,
    load_payroll,
    load_benefits,
    align_employee_schema,
)


from src.clean import (
    clean_employee_data,
)


from src.deduplicate import (
    deduplicate_employees,
)


from src.transformers.benefits import (
    normalize_benefits,
)


from src.transformers.payroll import (
    normalize_payroll,
)


from src.transformers.employment_type import (
    normalize_employment_type,
)


from src.validate import (
    validate as validate_dataset,
)


from src.export import (
    export_dataset,
)


from src.visualize import (
    generate_visualizations,
)


from src.reports.validation_report import (
    generate_validation_report,
)


from src.reports.quality_report import (
    generate_quality_report,
)


from src.reports.audit_report import (
    generate_audit_report,
    export_audit_report,
)

logger = get_logger(__name__)


DEFAULT_OUTPUT_DIR = Path("outputs")


def _assign_company_origin(
    df: pd.DataFrame,
    default: str,
) -> pd.DataFrame:
    """
    Fill only missing or non-company origins.

    Payroll rows already carry GlobalTech or AcquiredCo from the source
    file. Replacing the whole column would namespace every id as GlobalTech
    and hide AcquiredCo pay records.
    """

    df = df.copy()

    if "company_origin" not in df.columns:
        df["company_origin"] = default
        return df

    normalized = (
        df["company_origin"]
        .astype("string")
        .str.strip()
        .replace(
            {
                "globaltech": "GlobalTech",
                "GLOBALTECH": "GlobalTech",
                "acquiredco": "AcquiredCo",
                "ACQUIREDCO": "AcquiredCo",
            }
        )
    )
    recognized = normalized.isin(["GlobalTech", "AcquiredCo"])
    df["company_origin"] = normalized.where(recognized, default)
    return df


# ============================================================
# Golden Dataset Preparation
# ============================================================


def prepare_golden_dataset(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Final cleanup before validation.

    Ensures golden dataset satisfies
    quality rules.
    """

    df = df.copy()

    # --------------------------------------------------------
    # Email normalization
    # --------------------------------------------------------

    if "email" in df.columns:

        df["email"] = df["email"].astype(str).str.strip().str.lower()

        # remove empty emails

        df.loc[
            df["email"].isin(
                [
                    "",
                    "nan",
                    "none",
                ]
            ),
            "email",
        ] = None

        # Keep first employee
        # if duplicate email exists

        if "employee_id" in df.columns:

            populated = df["email"].notna()
            ranked = df.loc[populated].copy()

            if "company_origin" in ranked.columns:
                ranked["_origin_rank"] = (
                    ranked["company_origin"]
                    .map({"GlobalTech": 0, "AcquiredCo": 1})
                    .fillna(2)
                )
            else:
                ranked["_origin_rank"] = 0

            ranked = ranked.sort_values("_origin_rank").drop_duplicates(
                subset=["email"],
                keep="first",
            )
            ranked = ranked.drop(columns=["_origin_rank"])
            df = pd.concat([ranked, df.loc[~populated]], ignore_index=True)

    # --------------------------------------------------------
    # Employment type normalization
    # --------------------------------------------------------

    df = normalize_employment_type(df)

    # --------------------------------------------------------
    # Manager cleanup
    # --------------------------------------------------------

    if {
        "employee_id",
        "manager_id",
    }.issubset(df.columns):

        valid_employee_ids = set(df["employee_id"].dropna())

        invalid_manager = df["manager_id"].notna() & ~df["manager_id"].isin(
            valid_employee_ids
        )

        df.loc[
            invalid_manager,
            "manager_id",
        ] = None

    return df.reset_index(drop=True)


# ============================================================
# Pipeline Class
# ============================================================


class HRPipeline:

    def __init__(
        self,
        output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ):

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.audit_statistics = []

    # ========================================================
    # INGESTION
    # ========================================================

    def ingest(self) -> dict:

        logger.info("Starting ingestion...")

        sources = {
            "globaltech": load_globaltech_hris(),
            "acquiredco": load_acquiredco_hris(),
            "payroll": load_payroll(),
            "benefits": load_benefits(),
        }

        for name, df in sources.items():

            logger.info(
                "%s records loaded: %s",
                name,
                len(df),
            )

        logger.info("Ingestion complete.")

        return sources

    # ========================================================
    # TRANSFORMATION
    # ========================================================

    def transform(
        self,
        sources: dict,
    ) -> dict:
        """
        Transform all source systems.

        Returns:

        {
            employees,
            payroll,
            benefits
        }
        """

        logger.info("Starting transformation...")

        # ====================================================
        # GlobalTech HRIS
        # ====================================================

        globaltech = align_employee_schema(
            sources["globaltech"],
            "globaltech_hris",
        )

        globaltech["company_origin"] = "GlobalTech"

        globaltech["source_system"] = "globaltech_hris"

        globaltech = clean_employee_data(
            globaltech,
            "globaltech_hris",
        )

        logger.info(
            "GlobalTech cleaned rows=%s",
            len(globaltech),
        )

        # ====================================================
        # AcquiredCo HRIS
        # ====================================================

        acquiredco = align_employee_schema(
            sources["acquiredco"],
            "acquiredco_hris",
        )

        acquiredco["company_origin"] = "AcquiredCo"

        acquiredco["source_system"] = "acquiredco_hris"

        acquiredco = clean_employee_data(
            acquiredco,
            "acquiredco_hris",
        )

        logger.info(
            "AcquiredCo cleaned rows=%s",
            len(acquiredco),
        )

        # ====================================================
        # Combine employee masters
        # ====================================================

        employees = pd.concat(
            [
                globaltech,
                acquiredco,
            ],
            ignore_index=True,
        )

        logger.info(
            "Combined employees=%s",
            len(employees),
        )

        # ====================================================
        # Payroll
        # ====================================================

        payroll = align_employee_schema(
            sources["payroll"],
            "payroll",
        )

        payroll = _assign_company_origin(payroll, "GlobalTech")

        payroll["source_system"] = "payroll"

        payroll = normalize_payroll(payroll)

        logger.info(
            "Payroll normalized rows=%s",
            len(payroll),
        )

        # ====================================================
        # Benefits
        # ====================================================

        benefits = align_employee_schema(
            sources["benefits"],
            "benefits",
        )

        benefits = _assign_company_origin(benefits, "GlobalTech")

        benefits["source_system"] = "benefits"

        benefits = normalize_benefits(benefits)

        logger.info(
            "Benefits normalized rows=%s",
            len(benefits),
        )

        logger.info("Transformation complete.")

        return {
            "employees": employees,
            "payroll": payroll,
            "benefits": benefits,
        }

    # ========================================================
    # DEDUPLICATION
    # ========================================================

    def deduplicate(
        self,
        employee_df: pd.DataFrame,
        payroll_df: pd.DataFrame,
        benefits_df: pd.DataFrame,
    ) -> dict:
        """
        Create golden employee dataset.
        """

        logger.info("Starting deduplication...")

        result = deduplicate_employees(
            employee_df,
            payroll_df,
            benefits_df,
        )

        golden_dataset = result.get("golden_dataset")

        logger.info(
            "Golden dataset created rows=%s",
            len(golden_dataset),
        )

        return result

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(
        self,
        golden_dataset: pd.DataFrame,
    ) -> dict:
        """
        Validate final golden dataset.
        """

        logger.info("Preparing dataset for validation...")

        golden_dataset = prepare_golden_dataset(golden_dataset)

        logger.info(
            "Validation dataset rows=%s",
            len(golden_dataset),
        )

        logger.info("Starting validation...")

        validation_result = validate_dataset(
            golden_dataset,
            self.output_dir,
        )

        summary = validation_result.get(
            "summary",
            {},
        )

        logger.info(
            "Validation summary=%s",
            summary,
        )

        return validation_result

    # ========================================================
    # REPORT GENERATION
    # ========================================================

    def generate_reports(
        self,
        validation_result: dict,
        golden_dataset: pd.DataFrame,
    ) -> dict:
        """
        Generate pipeline reports.
        """

        logger.info("Generating reports...")

        reports_dir = self.output_dir / "reports"

        reports_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # --------------------------------------------
        # Validation report
        # --------------------------------------------

        validation_report = generate_validation_report(
            validation_result,
            reports_dir,
        )

        with open(
            reports_dir / "validation_report.json",
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                validation_report,
                file,
                indent=4,
                default=str,
            )

        # --------------------------------------------
        # Quality report
        # --------------------------------------------

        quality_report = generate_quality_report(
            golden_dataset,
            validation_result,
            reports_dir,
        )

        # --------------------------------------------
        # Audit report
        # --------------------------------------------

        audit_report = generate_audit_report(
            self.audit_statistics,
            "GlobalTech HR Data Integration Pipeline",
        )

        export_audit_report(
            audit_report,
            reports_dir / "audit_report.json",
        )

        logger.info("Reports generated.")

        return {
            "validation": validation_report,
            "quality": quality_report,
            "audit": audit_report,
        }

    # ========================================================
    # EXPORT
    # ========================================================

    def export(
        self,
        golden_dataset: pd.DataFrame,
        ghost_employees: pd.DataFrame | None = None,
        probable_matches: pd.DataFrame | None = None,
    ) -> Path:
        """
        Export the golden dataset and the HR review files.

        The golden dataset is partitioned by company_origin.
        Ghost and probable-match files stay as CSV for HR review.
        """

        logger.info("Exporting golden dataset...")

        output_file = self.output_dir / "golden_employee_dataset"

        exported = export_dataset(
            golden_dataset,
            output_file,
            partition_by="company_origin",
        )

        ghost_columns = [
            "payroll_employee_id",
            "name",
            "salary_usd_annual",
            "ghost_flag_reason",
        ]

        if ghost_employees is not None:
            ghost_frame = ghost_employees.copy()

            for column in ghost_columns:
                if column not in ghost_frame.columns:
                    ghost_frame[column] = pd.NA

            ghost_frame.reindex(columns=ghost_columns).to_csv(
                self.output_dir / "ghost_employees.csv",
                index=False,
            )

        review_columns = [
            "record_1_id",
            "record_2_id",
            "similarity_score",
            "hire_date_diff_days",
            "recommended_action",
        ]

        if probable_matches is not None:
            review = probable_matches.copy()

            for column in review_columns:
                if column not in review.columns:
                    review[column] = pd.NA

            review.reindex(columns=review_columns).to_csv(
                self.output_dir / "probable_matches.csv",
                index=False,
            )

        return exported

    # ========================================================
    # VISUALIZATION
    # ========================================================

    def visualize(
        self,
        golden_dataset: pd.DataFrame,
        validation_result: dict,
    ) -> dict:
        """
        Generate analytics charts.
        """

        charts_dir = self.output_dir / "charts"

        charts_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return generate_visualizations(
            golden_dataset,
            validation_result,
            charts_dir,
        )

    # ========================================================
    # RUN PIPELINE
    # ========================================================

    def run(self) -> dict:
        """
        Execute complete ETL pipeline.

        Includes diagnostic logging for:
        - salary transformation
        - payroll enrichment
        - golden dataset quality
        """

        logger.info("===== HR PIPELINE START =====")

        # ========================================================
        # 1. INGEST
        # ========================================================

        sources = self.ingest()

        for name, df in sources.items():

            logger.info(
                "[INGEST] %s rows=%s columns=%s",
                name,
                len(df),
                list(df.columns),
            )

        # ========================================================
        # 2. TRANSFORM
        # ========================================================

        logger.info("===== TRANSFORMATION START =====")

        transformed = self.transform(sources)

        employees = transformed["employees"]

        payroll = transformed["payroll"]

        benefits = transformed["benefits"]

        logger.info(
            "[EMPLOYEES] rows=%s columns=%s",
            len(employees),
            list(employees.columns),
        )

        logger.info(
            "[PAYROLL] rows=%s columns=%s",
            len(payroll),
            list(payroll.columns),
        )

        logger.info(
            "[BENEFITS] rows=%s columns=%s",
            len(benefits),
            list(benefits.columns),
        )

        # ========================================================
        # Salary diagnostic after payroll transform
        # ========================================================

        salary_columns = [
            "employee_id",
            "salary",
            "currency",
            "pay_frequency",
            "salary_usd_annual",
        ]

        existing_salary_columns = [c for c in salary_columns if c in payroll.columns]

        if existing_salary_columns:

            logger.info(
                "Payroll salary preview:\n%s",
                payroll[existing_salary_columns].head(10).to_string(),
            )

            if "salary_usd_annual" in payroll.columns:

                logger.info(
                    "Payroll salary_usd_annual stats:\n%s",
                    payroll["salary_usd_annual"].describe().to_string(),
                )

        else:

            logger.warning("No salary columns found after payroll transformation")

        # ========================================================
        # 3. DEDUPLICATION
        # ========================================================

        logger.info("===== DEDUPLICATION START =====")

        deduplication_result = self.deduplicate(
            employees,
            payroll,
            benefits,
        )

        golden_dataset = deduplication_result["golden_dataset"]

        logger.info(
            "[GOLDEN BEFORE CLEANUP] rows=%s columns=%s",
            len(golden_dataset),
            list(golden_dataset.columns),
        )

        # ========================================================
        # Salary diagnostic after merge
        # ========================================================

        existing_salary_columns = [
            c for c in salary_columns if c in golden_dataset.columns
        ]

        if existing_salary_columns:

            logger.info(
                "Golden salary preview:\n%s",
                golden_dataset[existing_salary_columns].head(10).to_string(),
            )

        else:

            logger.error("Salary columns disappeared after enrichment")

        # ========================================================
        # 4. FINAL CLEANUP
        # ========================================================

        logger.info("Preparing final golden dataset...")

        golden_dataset = prepare_golden_dataset(golden_dataset)

        logger.info(
            "[GOLDEN AFTER CLEANUP] rows=%s columns=%s",
            len(golden_dataset),
            list(golden_dataset.columns),
        )

        # ========================================================
        # Final Salary Validation Diagnostic
        # ========================================================

        salary_columns = [
            "salary",
            "salary_numeric",
            "salary_annual",
            "salary_usd_annual",
            "currency",
            "pay_frequency",
        ]

        existing_salary_columns = [
            c for c in salary_columns if c in golden_dataset.columns
        ]

        if existing_salary_columns:

            logger.info(
                """
                ========== FINAL SALARY CHECK ==========
                Columns:
                %s

                Sample:
                %s

                Statistics:
                %s
                ========================================
                """,
                existing_salary_columns,
                golden_dataset[existing_salary_columns].head(20).to_string(),
                golden_dataset[existing_salary_columns]
                .describe(include="all")
                .to_string(),
            )

        else:

            logger.error("FINAL DATASET HAS NO SALARY FIELDS")

        # ========================================================
        # 5. VALIDATION
        # ========================================================

        logger.info("===== VALIDATION START =====")

        validation_result = self.validate(golden_dataset)

        # ========================================================
        # 6. REPORTS
        # ========================================================

        reports = self.generate_reports(
            validation_result,
            golden_dataset,
        )

        # ========================================================
        # 7. EXPORT
        # ========================================================

        exported_file = self.export(
            golden_dataset,
            deduplication_result.get("ghost_employees"),
            deduplication_result.get("fuzzy_matches"),
        )

        # ========================================================
        # 8. VISUALIZATION
        # ========================================================

        charts = self.visualize(
            golden_dataset,
            validation_result,
        )

        logger.info("===== HR PIPELINE COMPLETE =====")

        return {
            "golden_dataset": golden_dataset,
            "validation": validation_result,
            "reports": reports,
            "export": exported_file,
            "charts": charts,
            "deduplication": deduplication_result,
            "transformed_sources": transformed,
        }


# ============================================================
# Public API
# ============================================================


def run_pipeline(
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict:
    """
    Pipeline entry point.
    """

    pipeline = HRPipeline(output_dir)

    return pipeline.run()
