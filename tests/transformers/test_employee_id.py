import pandas as pd
import pytest

from src.transformers.employee_id import (
    is_valid_employee_id,
    namespace_employee_id,
    namespace_employee_ids,
    validate_employee_ids,
)


def test_globaltech_namespace():

    assert (
        namespace_employee_id(
            42,
            "GlobalTech",
        )
        == "GT-000042"
    )


def test_acquiredco_namespace():

    assert (
        namespace_employee_id(
            1042,
            "AcquiredCo",
        )
        == "AC-001042"
    )


def test_string_id():

    assert (
        namespace_employee_id(
            "500",
            "GT",
        )
        == "GT-000500"
    )


def test_extract_digits():

    assert (
        namespace_employee_id(
            "EMP-123",
            "GT",
        )
        == "GT-000123"
    )


def test_invalid_company():

    with pytest.raises(ValueError):
        namespace_employee_id(
            1,
            "Amazon",
        )


def test_no_digits():

    with pytest.raises(ValueError):
        namespace_employee_id(
            "ABC",
            "GT",
        )


def test_valid_employee_id():

    assert is_valid_employee_id("GT-001234")


def test_valid_acquiredco_id():

    assert is_valid_employee_id("AC-999999")


def test_invalid_employee_id():

    assert not is_valid_employee_id("GT123")


def test_invalid_prefix():

    assert not is_valid_employee_id("HR-000123")


def test_none_is_invalid():

    assert not is_valid_employee_id(None)


def test_dataframe_namespace():

    df = pd.DataFrame(
        {
            "employee_id": [
                1,
                100,
            ],
            "company_origin": [
                "GlobalTech",
                "AcquiredCo",
            ],
        }
    )

    result = namespace_employee_ids(df)

    assert result.loc[0, "employee_id"] == "GT-000001"

    assert result.loc[1, "employee_id"] == "AC-000100"


def test_dataframe_missing_company():

    df = pd.DataFrame({"employee_id": [1]})

    with pytest.raises(KeyError):
        namespace_employee_ids(df)


def test_validate_dataframe():

    df = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "BAD-ID",
                "AC-000500",
            ]
        }
    )

    result = validate_employee_ids(df)

    assert result.tolist() == [
        True,
        False,
        True,
    ]


def test_returns_copy():

    df = pd.DataFrame(
        {
            "employee_id": [1],
            "company_origin": ["GlobalTech"],
        }
    )

    result = namespace_employee_ids(df)

    assert result is not df
