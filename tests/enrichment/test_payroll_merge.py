"""
Tests for payroll matching and merging.

Author: Israel Kwawu
"""

import pandas as pd

from src.enrichment.payroll_merge import prepare_payroll
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


def test_prepare_payroll_annualizes_before_usd_conversion():

    payroll = pd.DataFrame(
        {
            "employee_id": ["1042", "1043"],
            "company_origin": ["GlobalTech", "GlobalTech"],
            "salary": ["$5,000", "1000"],
            "currency": ["USD", "EUR"],
            "pay_frequency": ["Monthly", "Bi-Weekly"],
        }
    )

    result = prepare_payroll(payroll)

    assert result.loc[0, "salary_annual"] == 60000
    assert result.loc[0, "salary_usd_annual"] == 60000
    assert result.loc[1, "salary_annual"] == 26000
    assert result.loc[1, "salary_usd_annual"] == 28080
    assert result.loc[0, "salary"] == "$5,000"


def test_unmatched_payroll_employee_not_matched():

    employees = pd.DataFrame({"employee_id": ["GT-000001"]})

    payroll = pd.DataFrame({"employee_id": ["GT-999999"]})

    result = exact_employee_match(
        employees,
        payroll,
    )

    assert result.empty
