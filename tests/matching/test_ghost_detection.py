import pandas as pd

from src.matching.ghost_detection import (
    detect_payroll_ghosts,
    detect_benefits_ghosts,
    combine_ghost_reports,
)


def test_detect_payroll_ghosts():

    employees = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000002",
            ]
        }
    )

    payroll = pd.DataFrame(
        {
            "employee_id": [
                "GT-000002",
                "GT-000003",
            ]
        }
    )

    result = detect_payroll_ghosts(
        employees,
        payroll,
    )

    assert len(result) == 1

    assert result.iloc[0]["employee_id"] == "GT-000003"

    assert result.iloc[0]["ghost_source"] == "Payroll"


def test_detect_benefits_ghosts():

    employees = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
            ]
        }
    )

    benefits = pd.DataFrame(
        {
            "employee_id": [
                "GT-000001",
                "GT-000005",
            ]
        }
    )

    result = detect_benefits_ghosts(
        employees,
        benefits,
    )

    assert len(result) == 1

    assert result.iloc[0]["employee_id"] == "GT-000005"


def test_combine_reports():

    payroll = pd.DataFrame(
        {
            "employee_id": ["GT-000003"],
            "ghost_source": ["Payroll"],
            "ghost_employee": [True],
        }
    )

    benefits = pd.DataFrame(
        {
            "employee_id": ["GT-000005"],
            "ghost_source": ["Benefits"],
            "ghost_employee": [True],
        }
    )

    result = combine_ghost_reports(
        payroll,
        benefits,
    )

    assert len(result) == 2
    
    
