"""B2: the upload model matches spec 8.1."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.upload import ReadingsUpload

EXAMPLE = (
    Path(__file__).resolve().parents[2] / "docs" / "contract" / "examples" / "readings_upload.json"
)


def example() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_contract_example_passes():
    upload = ReadingsUpload.model_validate(example())
    assert upload.serial == "SPROUT-001"
    assert upload.readings[0].reading_id == "SPROUT-001-000123"
    assert upload.events[0].trigger == "auto"


def test_missing_required_field_fails():
    body = example()
    del body["readings"][0]["battery_mv"]
    with pytest.raises(ValidationError):
        ReadingsUpload.model_validate(body)


def test_wrong_type_fails():
    body = example()
    body["sent_boot_id"] = "seventeen"
    with pytest.raises(ValidationError):
        ReadingsUpload.model_validate(body)


@pytest.mark.parametrize(
    ("where", "field", "value"),
    [
        ("readings", "time_status", "guessed"),
        ("events", "trigger", "button"),
        ("events", "delivery", "maybe"),
    ],
)
def test_value_outside_enum_fails(where, field, value):
    body = example()
    body[where][0][field] = value
    with pytest.raises(ValidationError):
        ReadingsUpload.model_validate(body)


def test_renamed_field_fails():
    # Spec 3.1: a quietly renamed field must fail loudly, not be stored as null.
    body = deepcopy(example())
    body["readings"][0]["moisture"] = body["readings"][0].pop("moisture_pct")
    with pytest.raises(ValidationError):
        ReadingsUpload.model_validate(body)
