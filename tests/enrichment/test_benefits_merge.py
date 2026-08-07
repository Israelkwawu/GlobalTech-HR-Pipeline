"""
Tests for benefits matching.

Author: Israel Kwawu
"""

import pandas as pd

from src.matching.ghost_detection import (
    detect_benefits_ghosts,
)


def test_benefits_employee_exists():

    employees = pd.DataFrame({"employee_id": ["GT-000001"]})

    benefits = pd.DataFrame({"employee_id": ["GT-000001"]})

    result = detect_benefits_ghosts(
        employees,
        benefits,
    )

    assert result.empty


def test_benefits_missing_employee_detected():

    employees = pd.DataFrame({"employee_id": ["GT-000001"]})

    benefits = pd.DataFrame({"employee_id": ["GT-999999"]})

    result = detect_benefits_ghosts(
        employees,
        benefits,
    )

    assert not result.empty
