import pytest
from app.core.errors import ValidationError
from app.services.bootstrap import validate_required


@pytest.mark.parametrize(
    ("value", "field", "maximum"),
    [
        ("", "business_code", 64),
        ("   ", "business_code", 64),
        ("x" * 65, "business_code", 64),
    ],
)
def test_required_rejects_invalid_identifier(value, field, maximum):
    with pytest.raises(ValidationError):
        validate_required(value, field, maximum)


def test_required_strips_valid_identifier():
    assert validate_required("  ERP03  ", "business_code", 64) == "ERP03"
