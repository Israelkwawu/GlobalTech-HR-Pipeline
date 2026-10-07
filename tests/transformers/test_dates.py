"""Tests for explicit source date parsing."""

from src.transformers.dates import normalize_date, parse_known_date


def test_globaltech_iso_date():

    assert normalize_date("2020-01-15", "globaltech_hris", "hire_date") == "2020-01-15"


def test_acquiredco_us_date():

    assert normalize_date("06/27/2020", "acquiredco_hris", "hire_date") == "2020-06-27"


def test_benefits_day_month_name_date():

    parsed = parse_known_date("15-Jan-2022")

    assert parsed.year == 2022
    assert parsed.month == 1
    assert parsed.day == 15


def test_benefits_date_does_not_depend_on_generic_inference():

    assert (
        normalize_date("15-Jan-2022", "benefits", "benefits_enrollment_date")
        == "2022-01-15"
    )
