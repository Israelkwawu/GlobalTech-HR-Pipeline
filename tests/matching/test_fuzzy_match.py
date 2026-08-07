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


def test_similarity_with_none():

    assert (
        similarity_score(
            None,
            "John",
        )
        == 0
    )
