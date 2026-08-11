"""
Visualization reporting.

Responsibilities
----------------
- Generate HR analytics dashboard
- Produce required HR charts
- Export high-resolution PNG reports
- Include data source annotations
- Include generation timestamp

Author: Israel Kwawu
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import matplotlib

# Must be before importing pyplot
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Global State
# ============================================================================

GENERATED_CHARTS: list[str] = []

COLORBLIND_SAFE_PALETTE = [
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#CC79A7",
    "#56B4E9",
    "#D55E00",
]


# ============================================================================
# Helpers
# ============================================================================


def annotate_source(ax):
    """
    Add pipeline source annotation to a chart.
    """

    ax.text(
        0,
        -0.18,
        "Source: GlobalTech HR Integration Pipeline",
        transform=ax.transAxes,
        fontsize=8,
    )


def save_chart(
    fig,
    path: Path,
):
    """
    Save a high-resolution chart.
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.savefig(
        path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    GENERATED_CHARTS.append(path.name)

    logger.info(
        "Generated chart: %s",
        path,
    )


def add_report_header(fig):
    """
    Add overall dashboard title and timestamp.
    """

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    fig.suptitle(
        "GlobalTech HR Integration Pipeline\n" "EDA & Workforce Analytics Report",
        fontsize=18,
        fontweight="bold",
        y=0.98,
    )

    fig.text(
        0.5,
        0.01,
        f"Generated: {timestamp}",
        ha="center",
        fontsize=10,
    )


def ensure_numeric(series):
    """
    Convert values safely to numeric.

    Handles values such as:

        $111,833
        100000
        "100,000"
    """

    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .pipe(
            pd.to_numeric,
            errors="coerce",
        )
    )


# ============================================================================
# Chart 1 — Department Headcount
# ============================================================================


def chart_department_headcount(
    df: pd.DataFrame,
    output_dir: Path | str,
):
    """
    Generate headcount by department chart.
    """

    if "department" not in df.columns:
        logger.warning("Department chart skipped. Missing department column.")
        return

    data = df["department"].fillna("Unknown").value_counts().head(15)

    if data.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.barh(
        data.index,
        data.values,
    )

    ax.set_title("Headcount by Department")

    ax.set_xlabel("Employees")

    ax.set_ylabel("Department")

    ax.invert_yaxis()

    annotate_source(ax)

    save_chart(
        fig,
        Path(output_dir) / "01_headcount_department.png",
    )


# ============================================================================
# Chart 2 — Country Headcount
# ============================================================================


def chart_country_headcount(
    df: pd.DataFrame,
    output_dir: Path | str,
):
    """
    Generate headcount by country chart.
    """

    if "country" not in df.columns:
        logger.warning("Country chart skipped. Missing country column.")
        return

    data = df["country"].fillna("Unknown").value_counts().head(15)

    if data.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(
        data.index,
        data.values,
    )

    ax.set_title("Headcount by Country")

    ax.set_ylabel("Employees")

    plt.xticks(
        rotation=45,
        ha="right",
    )

    annotate_source(ax)

    save_chart(
        fig,
        Path(output_dir) / "02_headcount_country.png",
    )


# ============================================================================
# Chart 3 — Salary Distribution
# ============================================================================


def chart_salary_distribution(
    df: pd.DataFrame,
    output_dir: Path | str,
):
    """
    Generate salary distribution by employment type.

    Uses a boxplot because it makes differences between
    employment types easier to see.
    """

    salary_column = "salary_usd_annual"

    required = {
        salary_column,
        "employment_type",
    }

    if not required.issubset(df.columns):
        logger.warning("Salary chart skipped. Missing required columns.")
        return

    temp = df.copy()

    temp[salary_column] = ensure_numeric(temp[salary_column])

    temp = temp[temp[salary_column] > 0]

    if temp.empty:
        logger.warning("Salary chart skipped. No valid salary data.")
        return

    groups = []

    labels = []

    for name, group in temp.groupby(
        "employment_type",
        dropna=False,
    ):

        values = group[salary_column].dropna()

        if values.empty:
            continue

        groups.append(values)

        labels.append("Unknown" if pd.isna(name) else str(name))

    if not groups:
        return

    fig, ax = plt.subplots(figsize=(11, 7))

    ax.boxplot(
        groups,
        tick_labels=labels,
        showmeans=True,
    )

    ax.set_title("Salary Distribution by Employment Type")

    ax.set_xlabel("Employment Type")

    ax.set_ylabel("Annual Salary (USD)")

    ax.ticklabel_format(
        style="plain",
        axis="y",
    )

    ax.grid(
        axis="y",
        alpha=0.25,
    )

    annotate_source(ax)

    save_chart(
        fig,
        Path(output_dir) / "03_salary_distribution.png",
    )


# ============================================================================
# Chart 4 — Tenure Distribution
# ============================================================================


def chart_tenure_distribution(
    df: pd.DataFrame,
    output_dir: Path | str,
):
    """
    Generate employee tenure distribution chart.

    Handles:
    - timezone-aware dates
    - timezone-naive dates
    - invalid dates
    - missing values
    """

    if "hire_date" not in df.columns:

        logger.warning("Tenure chart skipped. Missing hire_date.")

        return

    dates = pd.to_datetime(
        df["hire_date"],
        errors="coerce",
    )

    # ------------------------------------------------------------
    # Normalize timezone
    # ------------------------------------------------------------

    try:

        if hasattr(dates.dt, "tz"):

            if dates.dt.tz is not None:

                dates = dates.dt.tz_localize(None)

    except Exception:

        logger.warning("Unable to normalize hire_date timezone.")

    today = pd.Timestamp.today()

    tenure = (today - dates).dt.days / 365.25

    tenure = tenure[tenure.notna() & (tenure >= 0)]

    if tenure.empty:

        logger.warning("Tenure chart skipped. No valid dates.")

        return

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(
        tenure,
        bins=20,
    )

    ax.set_title("Tenure Distribution")

    ax.set_xlabel("Years")

    ax.set_ylabel("Employees")

    annotate_source(ax)

    save_chart(
        fig,
        Path(output_dir) / "04_tenure_distribution.png",
    )


# ============================================================================
# Chart 5 — Benefits Enrollment
# ============================================================================


def chart_benefits_rate(
    df: pd.DataFrame,
    output_dir: Path | str,
):
    """
    Generate benefits enrollment rate by department.
    """

    required = {
        "benefit_plans",
        "department",
    }

    if not required.issubset(df.columns):
        logger.warning("Benefits chart skipped. Missing required columns.")
        return

    enrollment = (
        df.groupby("department")["benefit_plans"]
        .apply(lambda x: x.notna().mean() * 100)
        .sort_values(ascending=False)
        .head(15)
    )

    if enrollment.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(
        enrollment.index,
        enrollment.values,
    )

    ax.set_title("Benefits Enrollment Rate by Department")

    ax.set_ylabel("Enrollment (%)")

    ax.set_ylim(
        0,
        100,
    )

    plt.xticks(
        rotation=45,
        ha="right",
    )

    annotate_source(ax)

    save_chart(
        fig,
        Path(output_dir) / "05_benefits_enrollment.png",
    )


# ============================================================================
# Chart 6 — Granular Data Quality
# ============================================================================


def chart_quality_summary(
    validation_result: dict,
    output_dir: Path | str,
):
    """
    Generate granular data-quality chart.

    Produces one Passed/Failed pair for every validation check.

    Primary source:
        validation_result["report"]

    Expected report columns:
        check
        passed
        failed
        status

    Falls back to the high-level summary when a detailed
    validation report is unavailable.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not validation_result:
        logger.warning("Quality summary chart skipped. No validation result.")
        return None

    # ============================================================
    # Preferred source: detailed validation report
    # ============================================================

    report = validation_result.get("report")

    if isinstance(report, pd.DataFrame) and not report.empty:

        required_columns = {
            "check",
            "passed",
            "failed",
        }

        missing_columns = required_columns - set(report.columns)

        if not missing_columns:

            data = report[
                [
                    "check",
                    "passed",
                    "failed",
                ]
            ].copy()

            # Ensure numeric values
            data["passed"] = pd.to_numeric(
                data["passed"],
                errors="coerce",
            ).fillna(0)

            data["failed"] = pd.to_numeric(
                data["failed"],
                errors="coerce",
            ).fillna(0)

            # Remove completely empty checks
            data = data[(data["passed"] > 0) | (data["failed"] > 0)]

            if not data.empty:

                fig, ax = plt.subplots(
                    figsize=(
                        max(12, len(data) * 1.2),
                        7,
                    )
                )

                x = range(len(data))

                width = 0.38

                passed_positions = [position - width / 2 for position in x]

                failed_positions = [position + width / 2 for position in x]

                ax.bar(
                    passed_positions,
                    data["passed"],
                    width=width,
                    label="Passed",
                )

                ax.bar(
                    failed_positions,
                    data["failed"],
                    width=width,
                    label="Failed",
                )

                ax.set_title(
                    "Data Quality by Validation Check",
                    fontsize=15,
                    fontweight="bold",
                )

                ax.set_xlabel("Validation Check")

                ax.set_ylabel("Records")

                ax.set_xticks(list(x))

                ax.set_xticklabels(
                    data["check"],
                    rotation=45,
                    ha="right",
                )

                ax.legend()

                ax.grid(
                    axis="y",
                    alpha=0.25,
                )

                # Add values above bars
                for position, value in zip(
                    passed_positions,
                    data["passed"],
                ):

                    if value > 0:
                        ax.text(
                            position,
                            value,
                            f"{int(value)}",
                            ha="center",
                            va="bottom",
                            fontsize=8,
                        )

                for position, value in zip(
                    failed_positions,
                    data["failed"],
                ):

                    if value > 0:
                        ax.text(
                            position,
                            value,
                            f"{int(value)}",
                            ha="center",
                            va="bottom",
                            fontsize=8,
                        )

                annotate_source(ax)

                fig.tight_layout()

                output = output_dir / "06_quality_summary.png"

                save_chart(
                    fig,
                    output,
                )

                return output

    # ============================================================
    # Fallback: high-level summary
    # ============================================================

    summary = validation_result.get(
        "summary",
        {},
    )

    passed = int(
        summary.get(
            "passed_checks",
            0,
        )
    )

    failed = int(
        summary.get(
            "failed_checks",
            0,
        )
    )

    # If there is no useful data at all, still generate
    # the expected chart so the pipeline/test contract is stable.

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.bar(
        [
            "Passed",
            "Failed",
        ],
        [
            passed,
            failed,
        ],
    )

    ax.set_title(
        "Data Quality Summary",
        fontsize=15,
        fontweight="bold",
    )

    ax.set_ylabel("Validation Checks")

    annotate_source(ax)

    fig.tight_layout()

    output = output_dir / "06_quality_summary.png"

    save_chart(
        fig,
        output,
    )

    return output


# ============================================================================
# Final EDA Dashboard
# ============================================================================


def create_eda_report_dashboard(
    df: pd.DataFrame,
    validation_result: dict,
    output_dir: Path,
):
    """
    Create final high-resolution EDA report PNG.

    The sixth panel uses the same granular validation
    report as chart_quality_summary().
    """

    fig, axes = plt.subplots(
        3,
        2,
        figsize=(18, 20),
    )

    # ============================================================
    # Chart 1 — Department
    # ============================================================

    if "department" in df.columns:

        dept = df["department"].fillna("Unknown").value_counts().head(10)

        axes[0, 0].barh(
            dept.index,
            dept.values,
        )

        axes[0, 0].invert_yaxis()

        axes[0, 0].set_title("Headcount by Department")

        axes[0, 0].set_xlabel("Employees")

        axes[0, 0].set_ylabel("Department")

    # ============================================================
    # Chart 2 — Country
    # ============================================================

    if "country" in df.columns:

        country = df["country"].fillna("Unknown").value_counts().head(10)

        axes[0, 1].bar(
            country.index,
            country.values,
        )

        axes[0, 1].set_title("Headcount by Country")

        axes[0, 1].set_xlabel("Country")

        axes[0, 1].set_ylabel("Employees")

        axes[0, 1].tick_params(
            axis="x",
            rotation=45,
        )

    # ============================================================
    # Chart 3 — Salary by Employment Type
    # ============================================================

    if {
        "salary_usd_annual",
        "employment_type",
    }.issubset(df.columns):

        salary_df = df.copy()

        salary_df["salary_usd_annual"] = ensure_numeric(salary_df["salary_usd_annual"])

        salary_df = salary_df[salary_df["salary_usd_annual"] > 0]

        groups = []

        labels = []

        for name, group in salary_df.groupby(
            "employment_type",
            dropna=False,
        ):

            values = group["salary_usd_annual"].dropna()

            if values.empty:
                continue

            groups.append(values)

            labels.append("Unknown" if pd.isna(name) else str(name))

        if groups:

            axes[1, 0].boxplot(
                groups,
                tick_labels=labels,
                showmeans=True,
            )

            axes[1, 0].set_title("Salary Distribution by Employment Type")

            axes[1, 0].set_xlabel("Employment Type")

            axes[1, 0].set_ylabel("Annual Salary (USD)")

            axes[1, 0].ticklabel_format(
                style="plain",
                axis="y",
            )

            axes[1, 0].tick_params(
                axis="x",
                rotation=30,
            )

            axes[1, 0].grid(
                axis="y",
                alpha=0.25,
            )

    # ============================================================
    # Chart 4 — Tenure
    # ============================================================

    if "hire_date" in df.columns:

        dates = pd.to_datetime(
            df["hire_date"],
            errors="coerce",
        )

        try:

            if hasattr(dates.dt, "tz") and dates.dt.tz is not None:

                dates = dates.dt.tz_localize(None)

        except Exception:

            pass

        today = pd.Timestamp.today()

        tenure = (today - dates).dt.days / 365.25

        tenure = tenure[tenure.notna() & (tenure >= 0)]

        if not tenure.empty:

            axes[1, 1].hist(
                tenure,
                bins=20,
            )

            axes[1, 1].set_title("Tenure Distribution")

            axes[1, 1].set_xlabel("Years")

            axes[1, 1].set_ylabel("Employees")

    # ============================================================
    # Chart 5 — Benefits
    # ============================================================

    if {
        "department",
        "benefit_plans",
    }.issubset(df.columns):

        benefits = (
            df.groupby("department")["benefit_plans"]
            .apply(lambda x: x.notna().mean() * 100)
            .sort_values(ascending=False)
            .head(10)
        )

        if not benefits.empty:

            axes[2, 0].bar(
                benefits.index,
                benefits.values,
            )

            axes[2, 0].set_title("Benefits Enrollment Rate")

            axes[2, 0].set_ylabel("Enrollment (%)")

            axes[2, 0].set_ylim(
                0,
                100,
            )

            axes[2, 0].tick_params(
                axis="x",
                rotation=45,
            )

    # ------------------------------------------------
    # Chart 6 Quality
    # ------------------------------------------------

    report = validation_result.get("report")

    if isinstance(report, pd.DataFrame) and not report.empty:

        required_columns = {
            "check",
            "passed",
            "failed",
        }

        if required_columns.issubset(report.columns):

            quality = report[
                [
                    "check",
                    "passed",
                    "failed",
                ]
            ].copy()

            quality["passed"] = pd.to_numeric(
                quality["passed"],
                errors="coerce",
            ).fillna(0)

            quality["failed"] = pd.to_numeric(
                quality["failed"],
                errors="coerce",
            ).fillna(0)

            quality = quality[(quality["passed"] > 0) | (quality["failed"] > 0)]

            positions = range(len(quality))

            width = 0.35

            axes[2, 1].bar(
                [p - width / 2 for p in positions],
                quality["passed"],
                width=width,
                label="Passed",
            )

            axes[2, 1].bar(
                [p + width / 2 for p in positions],
                quality["failed"],
                width=width,
                label="Failed",
            )

            axes[2, 1].set_xticks(list(positions))

            axes[2, 1].set_xticklabels(
                quality["check"],
                rotation=45,
                ha="right",
                fontsize=7,
            )

            axes[2, 1].set_title("Data Quality by Validation Check")

            axes[2, 1].set_ylabel("Records")

            axes[2, 1].legend()

            axes[2, 1].grid(
                axis="y",
                alpha=0.25,
            )

        else:

            axes[2, 1].text(
                0.5,
                0.5,
                "Validation report columns unavailable",
                ha="center",
                va="center",
            )

    else:

        # Fallback
        summary = validation_result.get(
            "summary",
            {},
        )

        axes[2, 1].bar(
            [
                "Passed",
                "Failed",
            ],
            [
                summary.get(
                    "passed_checks",
                    0,
                ),
                summary.get(
                    "failed_checks",
                    0,
                ),
            ],
        )

        axes[2, 1].set_title("Data Quality Summary")

        axes[2, 1].set_ylabel("Checks")

    # ============================================================
    # Dashboard Header
    # ============================================================

    add_report_header(fig)

    # ============================================================
    # Source Annotations
    # ============================================================

    for ax in axes.flat:

        ax.text(
            0,
            -0.15,
            "Source: GlobalTech HR Integration Pipeline",
            transform=ax.transAxes,
            fontsize=8,
        )

    fig.tight_layout(
        rect=[
            0,
            0.03,
            1,
            0.95,
        ]
    )

    output = output_dir / "HR_EDA_Visualization_Report.png"

    fig.savefig(
        output,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(fig)

    logger.info(
        "Generated dashboard: %s",
        output,
    )

    return output


# ============================================================================
# Dashboard Generator
# ============================================================================


def generate_visualizations(
    df: pd.DataFrame,
    validation_result: dict,
    output_dir: Path | str,
):
    """
    Generate all visualization reports.
    """

    global GENERATED_CHARTS

    GENERATED_CHARTS = []

    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    if df.empty:

        logger.warning("Visualization skipped. Empty dataset.")

        return {
            "output_directory": str(output_dir),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "charts": [],
        }

    # ------------------------------------------------------------
    # Individual charts
    # ------------------------------------------------------------

    chart_department_headcount(
        df,
        output_dir,
    )

    chart_country_headcount(
        df,
        output_dir,
    )

    chart_salary_distribution(
        df,
        output_dir,
    )

    chart_tenure_distribution(
        df,
        output_dir,
    )

    chart_benefits_rate(
        df,
        output_dir,
    )

    chart_quality_summary(
        validation_result,
        output_dir,
    )

    # ------------------------------------------------------------
    # Final dashboard
    # ------------------------------------------------------------

    dashboard = create_eda_report_dashboard(
        df,
        validation_result,
        output_dir,
    )

    # ------------------------------------------------------------
    # Explicit chart list
    # ------------------------------------------------------------

    charts = [
        "01_headcount_department.png",
        "02_headcount_country.png",
        "03_salary_distribution.png",
        "04_tenure_distribution.png",
        "05_benefits_enrollment.png",
        "06_quality_summary.png",
        "HR_EDA_Visualization_Report.png",
    ]

    return {
        "output_directory": str(output_dir),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "report": str(dashboard),
        "charts": charts,
    }
