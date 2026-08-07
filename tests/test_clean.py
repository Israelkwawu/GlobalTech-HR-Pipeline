import pandas as pd

from config.constants import GLOBALTECH

from src.clean import clean_employee_data


def test_clean_pipeline():

    df = pd.DataFrame(
        {
            "employee_id": [1],
            "first_name": ["  john"],
            "last_name": ["SMITH "],
            "department": ["engineering"],
            "company_origin": [GLOBALTECH],
            "salary": ["$1000"],
            "currency": ["USD"],
            "pay_frequency": ["Monthly"],
            "hire_date": ["21/09/2016"],
        }
    )

    result = clean_employee_data(
        df,
        "globaltech_hris",
    )

    assert result.loc[0, "employee_id"] == "GT-000001"

    assert result.loc[0, "first_name"] == "John"

    assert result.loc[0, "last_name"] == "Smith"

    assert result.loc[0, "department"] == "Engineering"

    assert result.loc[0, "salary_usd_annual"] == 12000

    assert result.loc[0, "hire_date"] == "2016-09-21"


def test_clean_pipeline_partial_dataframe():

    df = pd.DataFrame(
        {
            "employee_id": [1],
            "company_origin": [GLOBALTECH],
        }
    )

    result = clean_employee_data(
        df,
        "globaltech_hris",
    )

    assert len(result) == 1


def test_clean_pipeline_empty_dataframe():

    df = pd.DataFrame()

    result = clean_employee_data(
        df,
        "globaltech_hris",
    )

    assert result.empty


def test_clean_pipeline_preserves_columns():

    df = pd.DataFrame(
        {
            "employee_id": [1],
            "company_origin": [GLOBALTECH],
            "custom_column": ["ABC"],
        }
    )

    result = clean_employee_data(
        df,
        "globaltech_hris",
    )

    assert "custom_column" in result.columns

    assert result.loc[0, "custom_column"] == "ABC"


def test_clean_pipeline_returns_dataframe():

    df = pd.DataFrame(
        {
            "employee_id": [1],
            "company_origin": [GLOBALTECH],
        }
    )

    result = clean_employee_data(
        df,
        "globaltech_hris",
    )

    assert isinstance(
        result,
        pd.DataFrame,
    )
