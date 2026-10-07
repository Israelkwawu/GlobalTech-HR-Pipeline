"""Tests for the validator base class."""

import pandas as pd
import pytest

from src.validators.base_validator import BaseValidator


class _EchoValidator(BaseValidator):

    name = "echo"

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            [self.error(df.iloc[0], "ECHO", "checked", "employee_id")]
        )


def test_base_validator_cannot_be_instantiated():

    with pytest.raises(TypeError):
        BaseValidator()


def test_error_record_shape():

    df = pd.DataFrame({"employee_id": ["GT-000001"]})
    result = _EchoValidator().validate(df)

    assert result.iloc[0]["employee_id"] == "GT-000001"
    assert result.iloc[0]["rule"] == "ECHO"
    assert result.iloc[0]["column"] == "employee_id"
    assert result.iloc[0]["message"] == "checked"
