"""
Tests for payroll matching and merging.

Author: Israel Kwawu
"""

import pandas as pd

from src.matching.exact_match import exact_employee_match


def test_payroll_employee_exact_id_match():

    employees = pd.DataFrame(
        {
            "employee_id": ["GT-000001"],
            "name": ["John Smith"],
        }
    )

    payroll = pd.DataFrame(
        {
            "employee_id": ["GT-000001"],
            "salary": [90000],
        }
    )

    result = exact_employee_match(
        employees,
        payroll,
    )

    assert len(result) == 1


def test_unmatched_payroll_employee_not_matched():

    employees = pd.DataFrame({"employee_id": ["GT-000001"]})

    payroll = pd.DataFrame({"employee_id": ["GT-999999"]})

    result = exact_employee_match(
        employees,
        payroll,
    )

    assert result.empty
