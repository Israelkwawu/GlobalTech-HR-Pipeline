import pandas as pd

from src.matching.fuzzy_match import (
    similarity_score,
    is_probable_match,
    fuzzy_match,
    best_match,
)


def test_similarity_score():

    score = similarity_score(
        "John Smith",
        "Jon Smith",
    )

    assert score > 85


def test_is_probable_match():

    assert is_probable_match(
        "John Smith",
        "Jon Smith",
    )


def test_fuzzy_match():

    left = pd.DataFrame(
        {
            "full_name": [
                "John Smith",
            ]
        }
    )

    right = pd.DataFrame(
        {
            "full_name": [
                "Jon Smith",
                "Michael Brown",
            ]
        }
    )

    result = fuzzy_match(
        left,
        right,
    )

    assert len(result) == 1

    assert result.iloc[0]["match_method"] == "fuzzy_name"


def test_best_match():

    candidates = pd.Series(
        [
            "Jon Smith",
            "Michael Brown",
        ]
    )

    name, score = best_match(
        "John Smith",
        candidates,
    )

    assert name == "Jon Smith"

    assert score > 85


def test_fuzzy_match_blocks_on_hire_date():

    left = pd.DataFrame(
        {
            "employee_id": ["GT-000001"],
            "full_name": ["John Smith"],
            "hire_date": ["2020-01-01"],
        }
    )

    right = pd.DataFrame(
        {
            "employee_id": ["AC-000002", "AC-000003"],
            "full_name": ["Jon Smith", "Jon Smith"],
            "hire_date": ["2020-01-15", "2021-06-01"],
        }
    )

    result = fuzzy_match(left, right)

    assert len(result) == 1
    assert result.iloc[0]["record_2_id"] == "AC-000002"
    assert result.iloc[0]["hire_date_diff_days"] <= 30
    assert result.iloc[0]["probable_match"]


def test_similarity_with_none():

    assert (
        similarity_score(
            None,
            "John",
        )
        == 0
    )
