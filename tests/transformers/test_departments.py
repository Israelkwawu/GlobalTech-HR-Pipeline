import pandas as pd
import pytest

from config.constants import (
    GLOBALTECH,
    ACQUIREDCO,
)

from src.transformers.departments import (
    normalize_department,
    map_department,
    map_departments,
    find_unmapped_departments,
)


def test_normalize_department():

    assert normalize_department(" engineering ") == "Engineering"


def test_normalize_department_none():

    assert normalize_department(None) is None


def test_map_department_globaltech():

    assert (
        map_department(
            "Engineering",
            GLOBALTECH,
        )
        == "Engineering"
    )


def test_map_department_acquiredco():

    assert (
        map_department(
            "Product",
            ACQUIREDCO,
        )
        == "Product"
    )


def test_unknown_department_returns_none():

    assert (
        map_department(
            "Alien Department",
            GLOBALTECH,
        )
        is None
    )


def test_invalid_company():

    with pytest.raises(ValueError):

        map_department(
            "Engineering",
            "ABC",
        )


def test_map_departments_dataframe():

    df = pd.DataFrame(
        {
            "department": [
                "Engineering",
                "Product",
            ],
            "company_origin": [
                GLOBALTECH,
                ACQUIREDCO,
            ],
        }
    )

    result = map_departments(df)

    assert result.loc[0, "department"] == "Engineering"

    assert result.loc[1, "department"] == "Product"


def test_missing_columns():

    df = pd.DataFrame(
        {
            "department": [
                "Engineering",
            ]
        }
    )

    with pytest.raises(KeyError):

        map_departments(df)


def test_find_unmapped_departments():

    df = pd.DataFrame(
        {
            "department": [
                "Engineering",
                None,
                "Finance",
                None,
            ]
        }
    )

    result = find_unmapped_departments(df)

    assert len(result) == 2
