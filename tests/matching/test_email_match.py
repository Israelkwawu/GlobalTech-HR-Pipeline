import pandas as pd
import pytest

from src.matching.email_match import (
    normalize_email,
    normalize_email_column,
    email_match,
    unmatched_emails,
    duplicate_emails,
    validate_unique_emails,
)


def test_normalize_email():

    assert (
        normalize_email(" John.Smith@Example.com ")
        == "john.smith@example.com"
    )


def test_normalize_email_none():

    assert normalize_email(None) is None


def test_normalize_email_column():

    df = pd.DataFrame(
        {
            "email": [
                " JOHN@TEST.COM ",
            ]
        }
    )

    result = normalize_email_column(df)

    assert result.loc[0, "email"] == "john@test.com"


def test_email_match():

    left = pd.DataFrame(
        {
            "employee_id": ["GT-000001"],
            "email": ["john@test.com"],
        }
    )

    right = pd.DataFrame(
        {
            "salary": [50000],
            "email": ["John@Test.com"],
        }
    )

    result = email_match(left, right)

    assert len(result) == 1

    assert (
        result.iloc[0]["match_method"]
        == "email_match"
    )


def test_unmatched_emails():

    left = pd.DataFrame(
        {
            "email": [
                "a@test.com",
                "b@test.com",
            ]
        }
    )

    right = pd.DataFrame(
        {
            "email": [
                "a@test.com",
            ]
        }
    )

    result = unmatched_emails(
        left,
        right,
    )

    assert len(result) == 1

    assert (
        result.iloc[0]["email"]
        == "b@test.com"
    )


def test_duplicate_emails():

    df = pd.DataFrame(
        {
            "email": [
                "a@test.com",
                "A@test.com",
                "b@test.com",
            ]
        }
    )

    result = duplicate_emails(df)

    assert len(result) == 2


def test_validate_unique_emails():

    df = pd.DataFrame(
        {
            "email": [
                "a@test.com",
                "a@test.com",
                "b@test.com",
            ]
        }
    )

    result = validate_unique_emails(df)

    assert result.tolist() == [
        False,
        False,
        True,
    ]


def test_missing_email_column():

    df = pd.DataFrame(
        {
            "name": ["John"],
        }
    )

    with pytest.raises(KeyError):
        normalize_email_column(df)
        
