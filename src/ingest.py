"""
Data ingestion module for the GlobalTech HR Data Integration Pipeline.

Responsible for loading raw data from all source systems into pandas
DataFrames with basic validation and source tagging.

Author: Israel Kwawu
"""

from __future__ import annotations

from pathlib import Path
import json
import pandas as pd
from pandas.errors import EmptyDataError, ParserError
import xml.etree.ElementTree as ET

from config.logging_config import get_logger
from config.settings import RAW_DATA_DIR
from src.utils.file_utils import (
    log_file_error,
    log_file_loaded,
    normalize_column_names,
    validate_extension,
    validate_file_exists,
)
from src.utils.helpers import (
    add_source_system,
    log_dataframe_summary,
    standardize_missing_values,
    log_dataframe_schema,
    add_missing_columns,
    reorder_columns
)

from src.models.employee_schema import (
    EMPLOYEE_COLUMNS,
    REQUIRED_FIELDS,
    EMPLOYEE_DTYPES,
)

from src.utils.dead_letter import write_dead_letter

logger = get_logger(__name__)

def load_globaltech_hris(
    file_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Load the GlobalTech HRIS CSV export.

    Parameters
    ----------
    file_path : str | Path, optional
        Path to the GlobalTech HRIS CSV.
        Defaults to the configured raw data directory.

    Returns
    -------
    pd.DataFrame
        Raw HRIS data.

    Raises
    ------
    FileNotFoundError
        If the file cannot be found.

    ValueError
        If the file extension is not CSV.

    RuntimeError
        If the CSV cannot be parsed.
    """

    source_name = "globaltech_hris"

    if file_path is None:
        file_path = RAW_DATA_DIR / "globaltech_hris.csv"

    try:
        # ------------------------------------------------------------------
        # Validate input
        # ------------------------------------------------------------------

        validate_file_exists(file_path)
        validate_extension(file_path, [".csv"])

        logger.info(
            "Loading GlobalTech HRIS from %s",
            file_path,
        )

        # ------------------------------------------------------------------
        # Read CSV
        # ------------------------------------------------------------------

        df = pd.read_csv(
            file_path,
            encoding="utf-8",
        )

        # ------------------------------------------------------------------
        # Basic standardization
        # ------------------------------------------------------------------

        df = normalize_column_names(df)

        df = standardize_missing_values(df)

        df = add_source_system(
            df,
            source_name,
        )

        # ------------------------------------------------------------------
        # Logging
        # ------------------------------------------------------------------

        log_file_loaded(
            source=source_name,
            path=file_path,
            records=len(df),
        )
        
        log_dataframe_schema(source_name, df)

        log_dataframe_summary(
            "GlobalTech HRIS",
            df,
        )

        return df

    except FileNotFoundError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )
        
        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise

    except ValueError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )

        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise

    except EmptyDataError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )

        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise RuntimeError(
            "GlobalTech HRIS file is empty."
        ) from exc

    except ParserError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )

        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise RuntimeError(
            "Unable to parse GlobalTech HRIS CSV."
        ) from exc

    except Exception as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )
        
        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise RuntimeError(
            "Unexpected error while loading GlobalTech HRIS."
        ) from exc
        


def load_acquiredco_hris(
    file_path: str | Path | None = None,
    page_size: int = 500,
) -> pd.DataFrame:
    """
    Load the AcquiredCo HRIS JSON export.

    Simulates a paginated BambooHR API by reading the JSON file
    in chunks before loading it into a DataFrame.

    Parameters
    ----------
    file_path : str | Path, optional
        Path to the JSON file.

    page_size : int, default=500
        Number of records per simulated API page.

    Returns
    -------
    pd.DataFrame
        Raw AcquiredCo API data.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.

    ValueError
        If the file extension is invalid.

    RuntimeError
        If the JSON cannot be parsed.
    """

    source_name = "acquiredco_hris"

    if file_path is None:
        file_path = RAW_DATA_DIR / "acquiredco_api.json"

    try:
        # ------------------------------------------------------------------
        # Validate input
        # ------------------------------------------------------------------

        validate_file_exists(file_path)
        validate_extension(file_path, [".json"])

        logger.info(
            "Loading AcquiredCo API data from %s",
            file_path,
        )

        # ------------------------------------------------------------------
        # Read JSON
        # ------------------------------------------------------------------

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # ------------------------------------------------------------------
        # Log API metadata (if present)
        # ------------------------------------------------------------------

        if isinstance(data, dict):
            logger.info(
                "API Status=%s | Timestamp=%s | Total Records=%s",
                data.get("status"),
                data.get("timestamp"),
                data.get("total_records"),
            )

        # ------------------------------------------------------------------
        # Extract employee records
        # ------------------------------------------------------------------

        if isinstance(data, dict):

            if "employees" in data:
                records = data["employees"]
            else:
                raise RuntimeError(
                    "JSON does not contain an 'employees' key."
                )

        elif isinstance(data, list):

            records = data

        else:
            raise RuntimeError(
                "Unsupported JSON structure."
            )

        # ------------------------------------------------------------------
        # Simulate API Pagination
        # ------------------------------------------------------------------

        total_records = len(records)

        logger.info(
            "Beginning paginated ingestion (%s records, page size=%s)",
            total_records,
            page_size,
        )

        for page_number, start in enumerate(
            range(0, total_records, page_size),
            start=1,
        ):
            end = min(start + page_size, total_records)

            logger.info(
                "Fetched page %s (%s records)",
                page_number,
                end - start,
            )

        # ------------------------------------------------------------------
        # Flatten nested JSON
        # ------------------------------------------------------------------

        df = pd.json_normalize(records)

        # ------------------------------------------------------------------
        # Basic standardization
        # ------------------------------------------------------------------

        df = normalize_column_names(df)

        df = standardize_missing_values(df)

        df = add_source_system(
            df,
            source_name,
        )

        # ------------------------------------------------------------------
        # Logging
        # ------------------------------------------------------------------

        log_file_loaded(
            source=source_name,
            path=file_path,
            records=len(df),
        )

        log_dataframe_schema(
            source_name,
            df,
        )

        log_dataframe_summary(
            source_name,
            df,
        )

        return df

    except FileNotFoundError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )
        
        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise
    
    except json.JSONDecodeError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )

        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise RuntimeError(
            "Malformed JSON file."
        ) from exc
        
    except ValueError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )

        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise

    except Exception as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )
        
        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise RuntimeError(
            "Unexpected error while loading AcquiredCo HRIS."
        ) from exc
       
    
def load_benefits(
    file_path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Load the MedShield Benefits XML export.

    Parameters
    ----------
    file_path : str | Path, optional
        Path to benefits XML.

    Returns
    -------
    pd.DataFrame
        Benefits enrollment records.

    Raises
    ------
    FileNotFoundError
        If XML file is missing.

    RuntimeError
        If XML cannot be parsed.
    """

    source_name = "benefits"

    if file_path is None:
        file_path = RAW_DATA_DIR / "benefits_enrollment.xml"

    try:

        # ------------------------------------------------------------------
        # Validate
        # ------------------------------------------------------------------

        validate_file_exists(file_path)
        validate_extension(file_path, [".xml"])

        logger.info(
            "Loading Benefits from %s",
            file_path,
        )

        # ------------------------------------------------------------------
        # Parse XML
        # ------------------------------------------------------------------

        tree = ET.parse(file_path)
        root = tree.getroot()

        records = [
            {
                child.tag: child.text
                for child in node
            }
            for node in root
        ]

        df = pd.DataFrame(records)

        # ------------------------------------------------------------------
        # Standardize
        # ------------------------------------------------------------------

        df = normalize_column_names(df)

        df = standardize_missing_values(df)

        df = add_source_system(
            df,
            source_name,
        )

        # ------------------------------------------------------------------
        # Logging
        # ------------------------------------------------------------------

        log_file_loaded(
            source=source_name,
            path=file_path,
            records=len(df),
        )
        
        log_dataframe_schema(source_name, df)

        log_dataframe_summary(
            "Benefits",
            df,
        )

        return df

    except FileNotFoundError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )
        
        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise
    
    except ET.ParseError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )

        raise RuntimeError(
            "Malformed Benefits XML."
        ) from exc
        
    except ValueError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )

        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise
    
    except Exception as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )
        
        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise RuntimeError(
            "Unexpected error while loading Benefits."
        ) from exc
        
        
def load_payroll(
    file_path: str | Path | None = None,
    sheet_name: str | int = 0,
) -> pd.DataFrame:
    """
    Load the ADP Payroll Excel export.

    Parameters
    ----------
    file_path : str | Path, optional
        Path to the payroll Excel file.

    sheet_name : str | int, default=0
        Worksheet name or index.

    Returns
    -------
    pd.DataFrame
        Payroll data.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.

    RuntimeError
        If the workbook cannot be read.
    """

    source_name = "payroll"

    if file_path is None:
        file_path = RAW_DATA_DIR / "payroll_data.xlsx"

    try:

        # ------------------------------------------------------------------
        # Validate file
        # ------------------------------------------------------------------

        validate_file_exists(file_path)
        validate_extension(file_path, [".xlsx"])

        logger.info(
            "Loading Payroll from %s",
            file_path,
        )

        # ------------------------------------------------------------------
        # Read Excel
        # ------------------------------------------------------------------

        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine="openpyxl",
        )

        # ------------------------------------------------------------------
        # Standardize
        # ------------------------------------------------------------------

        df = normalize_column_names(df)

        df = standardize_missing_values(df)

        df = add_source_system(
            df,
            source_name,
        )

        # ------------------------------------------------------------------
        # Logging
        # ------------------------------------------------------------------

        duplicate_count = int(df.duplicated().sum())

        logger.info(
            "Payroll duplicate records detected: %s",
            duplicate_count,
        )

        log_file_loaded(
            source=source_name,
            path=file_path,
            records=len(df),
        )
        
        log_dataframe_schema(source_name, df)

        log_dataframe_summary(
            "Payroll",
            df,
        )

        return df

    except FileNotFoundError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )

        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise
    
    except ValueError as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )

        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise
    
    except Exception as exc:

        log_file_error(
            source_name,
            file_path,
            exc,
        )

        write_dead_letter(
            source_system=source_name,
            file_name=Path(file_path).name,
            error=exc,
        )

        raise RuntimeError(
            "Unexpected error while loading Payroll."
        ) from exc
        

def align_employee_schema(
    df: pd.DataFrame,
    source_system: str,
) -> pd.DataFrame:
    """
    Align a source DataFrame to the canonical employee schema.

    Parameters
    ----------
    df : pd.DataFrame
        Raw source DataFrame.

    source_system : str
        One of:
        - globaltech_hris
        - acquiredco_hris
        - payroll
        - benefits

    Returns
    -------
    pd.DataFrame
        DataFrame aligned to the canonical employee schema.
    """

    logger.info(
        "Aligning schema for source '%s'",
        source_system,
    )

    mappings = {

        # --------------------------------------------------------------
        # GlobalTech HRIS
        # --------------------------------------------------------------
        "globaltech_hris": {
            "employee_id": "employee_id",
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "email",
            "department": "department",
            "job_title": "job_title",
            "hire_date": "hire_date",
            "country": "country",
            "employment_type": "employment_type",
            "manager_id": "manager_id",
        },

        # --------------------------------------------------------------
        # AcquiredCo
        # --------------------------------------------------------------
        "acquiredco_hris": {
            "employee_identifier": "employee_id",
            "first": "first_name",
            "last": "last_name",
            "email": "email",
            "department": "department",
            "role": "job_title",
            "location": "country",
            "hire_timestamp": "hire_date",
            "type": "employment_type",
            "manager_employee_id": "manager_id",
        },

        # --------------------------------------------------------------
        # Payroll
        # --------------------------------------------------------------
        "payroll": {
            "employee_id": "employee_id",
            "base_salary": "salary",
            "currency": "currency",
            "pay_frequency": "pay_frequency",
        },

        # --------------------------------------------------------------
        # Benefits
        # --------------------------------------------------------------
        "benefits": {
            "employee_id": "employee_id",
            "plan_type": "benefit_plan",
            "coverage_level": "coverage_level",
            "enrollment_date": "benefits_enrollment_date",
        },
    }

    if source_system not in mappings:
        raise ValueError(
            f"Unsupported source: {source_system}"
        )

    mapping = mappings[source_system]

    # Keep only mapped columns
    available = {
        src: dst
        for src, dst in mapping.items()
        if src in df.columns
    }

    aligned = (
        df[list(available.keys())]
        .rename(columns=available)
        .copy()
    )

    # Preserve provenance
    aligned["source_system"] = source_system

    # Add missing canonical columns
    aligned = add_missing_columns(
        aligned,
        EMPLOYEE_COLUMNS,
    )

    # Reorder columns
    aligned = reorder_columns(
        aligned,
        EMPLOYEE_COLUMNS,
    )

    # Apply configured dtypes
    for column, dtype in EMPLOYEE_DTYPES.items():

        if column not in aligned.columns:
            continue

        try:
            aligned[column] = aligned[column].astype(dtype)

        except Exception:

            logger.warning(
                "Unable to cast '%s' to %s",
                column,
                dtype,
            )

    logger.info(
        "%s successfully aligned (%s rows)",
        source_system,
        len(aligned),
    )

    return aligned

