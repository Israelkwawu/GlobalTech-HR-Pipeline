import pandas as pd

from src.transformers.names import (
    clean_whitespace,
    normalize_unicode,
    standardize_name,
    standardize_names,
    title_case_name,
)


def test_clean_whitespace():

    assert clean_whitespace("  John   Smith  ") == "John Smith"


def test_unicode_normalization():

    value = "José"

    assert normalize_unicode(value) == "José"


def test_title_case():

    assert title_case_name("john smith") == "John Smith"


def test_apostrophe():

    assert title_case_name("o'brien") == "O'Brien"


def test_hyphenated():

    assert title_case_name("anne-marie") == "Anne-Marie"


def test_van_der_berg():

    assert title_case_name("van der berg") == "Van der Berg"


def test_de_la_cruz():

    assert title_case_name("de la cruz") == "De la Cruz"


def test_multiple_spaces():

    assert standardize_name("   john      smith   ") == "John Smith"


def test_none_value():

    assert pd.isna(standardize_name(None))


def test_dataframe_standardization():

    df = pd.DataFrame(
        {
            "first_name": [
                " john ",
                "MARY",
            ],
            "last_name": [
                "o'brien",
                "van der berg",
            ],
        }
    )

    result = standardize_names(df)

    assert result.loc[0, "first_name"] == "John"

    assert result.loc[0, "last_name"] == "O'Brien"

    assert result.loc[1, "first_name"] == "Mary"

    assert result.loc[1, "last_name"] == "Van der Berg"


def test_missing_column():

    df = pd.DataFrame({"employee_id": [1, 2]})

    result = standardize_names(df)

    assert "employee_id" in result.columns


def test_returns_new_dataframe():

    df = pd.DataFrame(
        {
            "first_name": ["john"],
            "last_name": ["smith"],
        }
    )

    result = standardize_names(df)

    assert result is not df
