import pandas as pd

from src.matching.exact_match import (
    exact_employee_match,
)


def test_exact_employee_match():

    left = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
            ],
            "name": [
                "John Smith",
                "Mary Jones",
            ],
        }
    )


    right = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000003",
            ],
            "salary": [
                80000,
                90000,
            ],
        }
    )


    result = exact_employee_match(
        left,
        right,
    )


    assert len(result) == 1

    assert (
        result.iloc[0]["employee_id"]
        ==
        "GT-000001"
    )


    assert (
        result.iloc[0]["match_method"]
        ==
        "exact_id"
    )
    
