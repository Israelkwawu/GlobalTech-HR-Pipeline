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

matplotlib.use("Agg")

import matplotlib.pyplot as plt

import pandas as pd


from config.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Helpers
# ============================================================================


GENERATED_CHARTS = []

COLORBLIND_SAFE_PALETTE = [
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#CC79A7",
    "#56B4E9",
    "#D55E00",
]


def annotate_source(ax):
    """
    Add pipeline source annotation.
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
    Save high resolution chart.
    """

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


def add_report_header(
    fig,
):
    """
    Add overall dashboard title and timestamp.
    """

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

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

    Handles:

    $111,833
    100000
    """

    return (
        series.astype(str)
        .str.replace(
            ",",
            "",
            regex=False,
        )
        .str.replace(
            "$",
            "",
            regex=False,
        )
        .pipe(
            pd.to_numeric,
            errors="coerce",
        )
    )


# ============================================================================
# Charts
# ============================================================================


def chart_department_headcount(
    df,
    output_dir,
):

    if "department" not in df.columns:
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

    annotate_source(ax)

    save_chart(
        fig,
        output_dir / "01_headcount_department.png",
    )


def chart_country_headcount(
    df,
    output_dir,
):

    if "country" not in df.columns:
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
        output_dir / "02_headcount_country.png",
    )


def chart_salary_distribution(
    df,
    output_dir,
):

    salary_column = "salary_usd_annual"

    required = {
        salary_column,
        "employment_type",
    }

    if not required.issubset(df.columns):
        return

    temp = df.copy()

    temp[salary_column] = ensure_numeric(temp[salary_column])

    temp = temp[temp[salary_column] > 0]

    groups = []

    labels = []

    for name, group in temp.groupby("employment_type"):

        values = group[salary_column].dropna()

        if not values.empty:

            groups.append(values)

            labels.append(str(name))

    if not groups:
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # Matplotlib 3.11+
    ax.boxplot(
        groups,
        tick_labels=labels,
    )

    ax.set_title("Salary Distribution by Employment Type")

    ax.set_xlabel("Employment Type")

    ax.set_ylabel("Annual Salary USD")

    annotate_source(ax)

    save_chart(
        fig,
        output_dir / "03_salary_distribution.png",
    )


def chart_tenure_distribution(
    df: pd.DataFrame,
    output_dir: Path,
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

        logger.warning("Tenure chart skipped. Missing hire_date")

        return

    dates = pd.to_datetime(
        df["hire_date"],
        errors="coerce",
    )

    # ------------------------------------------------------------
    # Normalize timezone
    # ------------------------------------------------------------

    try:

        # Remove timezone if present

        if hasattr(dates.dt, "tz") and dates.dt.tz is not None:

            dates = dates.dt.tz_localize(None)

    except Exception:

        pass

    # Current date as timezone-naive

    today = pd.Timestamp.today()

    tenure = (today - dates).dt.days / 365

    tenure = tenure[tenure.notna() & (tenure >= 0)]

    if tenure.empty:

        logger.warning("Tenure chart skipped. No valid dates")

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
        output_dir / "04_tenure_distribution.png",
    )


def chart_benefits_rate(
    df,
    output_dir,
):

    if "benefit_plans" not in df.columns:
        return

    if "department" not in df.columns:
        return

    enrollment = (
        df.groupby("department")["benefit_plans"]
        .apply(lambda x: x.notna().mean() * 100)
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

    ax.set_ylabel("Enrollment %")

    plt.xticks(
        rotation=45,
        ha="right",
    )

    annotate_source(ax)

    save_chart(
        fig,
        output_dir / "05_benefits_enrollment.png",
    )


def chart_quality_summary(
    validation_result,
    output_dir,
):
    """
    Generate grouped data quality summary chart.

    Shows passed and failed records for each
    individual validation check.
    """

    if not validation_result:
        logger.warning(
            "Quality summary chart skipped. "
            "No validation result."
        )
        return

    report = validation_result.get(
        "report",
        pd.DataFrame(),
    )

    if report is None or report.empty:
        logger.warning(
            "Quality summary chart skipped. "
            "Validation report is empty."
        )
        return

    required_columns = {
        "check",
        "passed",
        "failed",
    }

    missing = required_columns - set(report.columns)

    if missing:
        logger.warning(
            "Quality summary chart skipped. "
            "Missing columns=%s",
            missing,
        )
        return

    data = report[
        [
            "check",
            "passed",
            "failed",
        ]
    ].copy()

    # ------------------------------------------------------------
    # Convert to numeric
    # ------------------------------------------------------------

    data["passed"] = pd.to_numeric(
        data["passed"],
        errors="coerce",
    ).fillna(0)

    data["failed"] = pd.to_numeric(
        data["failed"],
        errors="coerce",
    ).fillna(0)

    if data.empty:
        return

    # ------------------------------------------------------------
    # Create grouped bar chart
    # ------------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(14, 7)
    )

    x = range(len(data))

    width = 0.38

    passed_bars = ax.bar(
        [i - width / 2 for i in x],
        data["passed"],
        width=width,
        label="Passed",
    )

    failed_bars = ax.bar(
        [i + width / 2 for i in x],
        data["failed"],
        width=width,
        label="Failed",
    )

    # ------------------------------------------------------------
    # Axis configuration
    # ------------------------------------------------------------

    ax.set_title(
        "Data Quality Summary"
    )

    ax.set_xlabel(
        "Validation Check"
    )

    ax.set_ylabel(
        "Records"
    )

    ax.set_xticks(
        list(x)
    )

    ax.set_xticklabels(
        data["check"],
        rotation=45,
        ha="right",
    )

    ax.legend()

    # ------------------------------------------------------------
    # Add values above bars
    # ------------------------------------------------------------

    for bar in passed_bars:

        value = int(bar.get_height())

        if value > 0:

            ax.text(
                bar.get_x()
                + bar.get_width() / 2,
                bar.get_height(),
                str(value),
                ha="center",
                va="bottom",
                fontsize=8,
            )

    for bar in failed_bars:

        value = int(bar.get_height())

        if value > 0:

            ax.text(
                bar.get_x()
                + bar.get_width() / 2,
                bar.get_height(),
                str(value),
                ha="center",
                va="bottom",
                fontsize=8,
            )

    annotate_source(ax)

    fig.tight_layout()

    save_chart(
        fig,
        output_dir / "06_quality_summary.png",
    )

def chart_quality_granular(
    validation_result: dict,
    output_dir: Path,
):
    """
    Generate granular data quality chart.

    Shows the failure rate for every validation check,
    while retaining passed and failed record counts.

    The chart is sorted by failure rate so the checks
    requiring the most attention appear at the top.
    """

    if not validation_result:
        logger.warning(
            "Granular quality chart skipped. "
            "No validation result."
        )
        return

    report = validation_result.get(
        "report",
        pd.DataFrame(),
    )

    if report is None or report.empty:
        logger.warning(
            "Granular quality chart skipped. "
            "Validation report is empty."
        )
        return

    required_columns = {
        "check",
        "total",
        "passed",
        "failed",
    }

    missing = required_columns - set(report.columns)

    if missing:
        logger.warning(
            "Granular quality chart skipped. "
            "Missing columns=%s",
            missing,
        )
        return

    data = report[
        [
            "check",
            "total",
            "passed",
            "failed",
        ]
    ].copy()

    # ------------------------------------------------------------
    # Ensure numeric values
    # ------------------------------------------------------------

    for column in [
        "total",
        "passed",
        "failed",
    ]:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce",
        ).fillna(0)

    # ------------------------------------------------------------
    # Calculate failure rate
    # ------------------------------------------------------------

    data["failure_rate"] = 0.0

    valid_total = data["total"] > 0

    data.loc[
        valid_total,
        "failure_rate",
    ] = (
        data.loc[valid_total, "failed"]
        / data.loc[valid_total, "total"]
        * 100
    )

    # ------------------------------------------------------------
    # Remove checks with no records
    # ------------------------------------------------------------

    data = data[
        data["total"] > 0
    ].copy()

    if data.empty:
        logger.warning(
            "Granular quality chart skipped. "
            "No validation records available."
        )
        return

    # ------------------------------------------------------------
    # Sort highest failure rate first
    # ------------------------------------------------------------

    data = data.sort_values(
        "failure_rate",
        ascending=True,
    )

    # ------------------------------------------------------------
    # Create chart
    # ------------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(
            13,
            max(7, len(data) * 0.5),
        )
    )

    y = range(len(data))

    bars = ax.barh(
        y,
        data["failure_rate"],
    )

    ax.set_yticks(y)

    ax.set_yticklabels(
        data["check"]
    )

    ax.set_xlabel(
        "Failure Rate (%)"
    )

    ax.set_ylabel(
        "Validation Check"
    )

    ax.set_title(
        "Granular Data Quality — Failure Rate by Check"
    )

    # ------------------------------------------------------------
    # Add failure-rate labels
    # ------------------------------------------------------------

    for index, (_, row) in enumerate(
        data.iterrows()
    ):

        failure_rate = row["failure_rate"]

        failed = int(row["failed"])

        total = int(row["total"])

        ax.text(
            failure_rate,
            index,
            (
                f"  {failure_rate:.2f}%"
                f" ({failed}/{total})"
            ),
            va="center",
            fontsize=9,
        )

    # ------------------------------------------------------------
    # Highlight failed checks
    # ------------------------------------------------------------

    for bar, (_, row) in zip(
        bars,
        data.iterrows(),
    ):

        if row["failed"] > 0:

            bar.set_alpha(1.0)

        else:

            bar.set_alpha(0.35)

    # ------------------------------------------------------------
    # Add overall quality information
    # ------------------------------------------------------------

    summary = validation_result.get(
        "summary",
        {},
    )

    overall_failure_rate = summary.get(
        "failure_rate",
        0,
    )

    ax.axvline(
        overall_failure_rate,
        linestyle="--",
        linewidth=1,
        label=(
            f"Overall failure rate: "
            f"{overall_failure_rate:.2f}%"
        ),
    )

    ax.legend(
        loc="lower right"
    )

    annotate_source(ax)

    fig.tight_layout()

    save_chart(
        fig,
        output_dir / "07_quality_granular.png",
    )

def create_eda_report_dashboard(
    df: pd.DataFrame,
    validation_result: dict,
    output_dir: Path,
):
    """
    Create final high-resolution EDA report PNG.
    """

    fig, axes = plt.subplots(
        3,
        2,
        figsize=(18, 20),
    )

    # ------------------------------------------------
    # Chart 1 Department
    # ------------------------------------------------

    dept = df["department"].fillna("Unknown").value_counts().head(10)

    axes[0, 0].barh(
        dept.index,
        dept.values,
    )

    axes[0, 0].set_title("Headcount by Department")

    axes[0, 0].set_xlabel("Employees")

    axes[0, 0].set_ylabel("Department")

    # ------------------------------------------------
    # Chart 2 Country
    # ------------------------------------------------

    country = df["country"].fillna("Unknown").value_counts().head(10)

    axes[0, 1].bar(
        country.index,
        country.values,
    )

    axes[0, 1].set_title("Headcount by Country")

    axes[0, 1].set_xlabel("Country")

    axes[0, 1].set_ylabel("Employees")

    # ------------------------------------------------
    # Chart 3 Salary Distribution by Employment Type
    # ------------------------------------------------

    salary_column = "salary_usd_annual"

    if {
        salary_column,
        "employment_type",
    }.issubset(df.columns):

        salary_data = df.copy()

        salary_data[salary_column] = ensure_numeric(
            salary_data[salary_column]
        )

        salary_data = salary_data[
            salary_data[salary_column].notna()
            & (salary_data[salary_column] > 0)
        ]

        if not salary_data.empty:

            groups = []
            labels = []

            for employment_type, group in (
                salary_data
                .groupby("employment_type")
            ):

                values = group[
                    salary_column
                ].dropna()

                if not values.empty:

                    groups.append(values)

                    labels.append(
                        str(employment_type)
                    )

            if groups:

                axes[1, 0].boxplot(
                    groups,
                    tick_labels=labels,
                    showmeans=True,
                    patch_artist=False,
                )

                axes[1, 0].set_title(
                    "Salary Distribution by Employment Type"
                )

                axes[1, 0].set_xlabel(
                    "Employment Type"
                )

                axes[1, 0].set_ylabel(
                    "Annual Salary (USD)"
                )

                axes[1, 0].tick_params(
                    axis="x",
                    rotation=30,
                    labelsize=8,
                )

                axes[1, 0].yaxis.set_major_formatter(
                    plt.FuncFormatter(
                        lambda x, _: f"${x:,.0f}"
                    )
                )

            else:

                axes[1, 0].text(
                    0.5,
                    0.5,
                    "No salary data available",
                    ha="center",
                    va="center",
                )

                axes[1, 0].set_title(
                    "Salary Distribution by Employment Type"
                )

        else:

            axes[1, 0].text(
                0.5,
                0.5,
                "No valid salary data",
                ha="center",
                va="center",
            )

            axes[1, 0].set_title(
                "Salary Distribution by Employment Type"
            )

    else:

        axes[1, 0].text(
            0.5,
            0.5,
            "Required salary fields unavailable",
            ha="center",
            va="center",
        )

        axes[1, 0].set_title(
            "Salary Distribution by Employment Type"
        )

    # ------------------------------------------------
    # Chart 4 Tenure
    # ------------------------------------------------

    dates = pd.to_datetime(
        df["hire_date"],
        errors="coerce",
    )

    tenure = (datetime.utcnow() - dates.dt.tz_localize(None)).dt.days / 365

    axes[1, 1].hist(
        tenure.dropna(),
        bins=20,
    )

    axes[1, 1].set_title("Tenure Distribution")

    axes[1, 1].set_xlabel("Years")

    # ------------------------------------------------
    # Chart 5 Benefits
    # ------------------------------------------------

    benefits = (
        df.groupby("department")["benefit_plans"]
        .apply(lambda x: x.notna().mean() * 100)
        .head(10)
    )

    axes[2, 0].bar(
        benefits.index,
        benefits.values,
    )

    axes[2, 0].set_title("Benefits Enrollment Rate")

    axes[2, 0].set_ylabel("%")

    # ------------------------------------------------
    # Chart 6 Quality - Granular
    # ------------------------------------------------

    report = validation_result.get(
        "report",
        pd.DataFrame(),
    )

    if (
        isinstance(report, pd.DataFrame)
        and not report.empty
        and {
            "check",
            "passed",
            "failed",
        }.issubset(report.columns)
    ):

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

        x = range(len(quality))

        width = 0.38

        axes[2, 1].bar(
            [
                i - width / 2
                for i in x
            ],
            quality["passed"],
            width=width,
            label="Passed",
        )

        axes[2, 1].bar(
            [
                i + width / 2
                for i in x
            ],
            quality["failed"],
            width=width,
            label="Failed",
        )

        axes[2, 1].set_xticks(
            list(x)
        )

        axes[2, 1].set_xticklabels(
            quality["check"],
            rotation=45,
            ha="right",
            fontsize=7,
        )

        axes[2, 1].set_title(
            "Data Quality Summary by Check"
        )

        axes[2, 1].set_ylabel(
            "Records"
        )

        axes[2, 1].legend(
            fontsize=8
        )

    else:

        axes[2, 1].text(
            0.5,
            0.5,
            "Validation report unavailable",
            ha="center",
            va="center",
        )

        axes[2, 1].set_title(
            "Data Quality Summary"
        )

    # Add header LAST

    add_report_header(fig)

    # Add annotations

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

    return output

# ============================================================================
# Dashboard Generator
# ============================================================================


def generate_visualizations(
    df: pd.DataFrame,
    validation_result: dict,
    output_dir: Path | str,
):

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
    
    chart_quality_granular(
        validation_result,
        output_dir,
    )

    dashboard = create_eda_report_dashboard(
        df,
        validation_result,
        output_dir,
    )

    return {
        "output_directory": str(output_dir),
        "generated_at": datetime.utcnow().isoformat(),
        "report": str(dashboard),
        "charts": [
            "01_headcount_department.png",
            "02_headcount_country.png",
            "03_salary_distribution.png",
            "04_tenure_distribution.png",
            "05_benefits_enrollment.png",
            "06_quality_summary.png",
            "07_quality_granular.png",
            "HR_EDA_Visualization_Report.png",
        ],
    }
