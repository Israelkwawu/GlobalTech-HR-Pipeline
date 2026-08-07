"""
Tests for ghost employee detection.

Author: Israel Kwawu
"""

import pandas as pd

from src.matching.ghost_detection import (
    detect_payroll_ghosts,
    combine_ghost_reports,
)


def test_payroll_ghost_employee_detected():

    employees = pd.DataFrame({"employee_id": ["GT-000001"]})

    payroll = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-999999",
            ],
            "salary": [
                80000,
                90000,
            ],
        }
    )

    ghosts = detect_payroll_ghosts(
        employees,
        payroll,
    )

    assert len(ghosts) == 1

    assert ghosts.iloc[0]["employee_id"] == "GT-999999"


def test_no_payroll_ghosts():

    employees = pd.DataFrame({"employee_id": ["GT-000001"]})

    payroll = pd.DataFrame({"employee_id": ["GT-000001"]})

    ghosts = detect_payroll_ghosts(
        employees,
        payroll,
    )

    assert ghosts.empty


def test_combine_ghost_reports():

    payroll_ghosts = pd.DataFrame({"employee_id": ["GT-999999"]})

    benefits_ghosts = pd.DataFrame({"employee_id": ["GT-888888"]})

    result = combine_ghost_reports(
        payroll_ghosts,
        benefits_ghosts,
    )

    assert len(result) == 2
