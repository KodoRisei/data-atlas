import pytest
from app.metadata.pii_detector import detect_pii, classify_table_pii_risk


@pytest.mark.parametrize(
    "column_name, expected_is_pii, expected_type",
    [
        ("email", True, "email"),
        ("user_email", True, "email"),
        ("customer_email_address", True, "email"),
        ("phone_number", True, "phone"),
        ("mobile", True, "phone"),
        ("birth_date", True, "birth_date"),
        ("date_of_birth", True, "birth_date"),
        ("dob", True, "birth_date"),
        ("ssn", True, "ssn"),
        ("social_security_number", True, "ssn"),
        ("password", True, "password"),
        ("hashed_password", True, "password"),
        ("api_key", True, "token"),
        ("access_token", True, "token"),
        ("first_name", True, "name"),
        ("last_name", True, "name"),
        ("ip_address", True, "ip_address"),
        ("credit_card", True, "credit_card"),
        # Should NOT match
        ("user_id", False, None),
        ("created_at", False, None),
        ("product_name", False, None),
        ("amount", False, None),
        ("status", False, None),
    ],
)
def test_detect_pii(column_name: str, expected_is_pii: bool, expected_type: str | None):
    result = detect_pii(column_name)
    assert result.is_pii == expected_is_pii
    if expected_is_pii:
        assert result.pii_type == expected_type
        assert result.confidence > 0.0


def test_classify_table_risk_low():
    assert classify_table_pii_risk(0, 10) == "low"


def test_classify_table_risk_medium():
    assert classify_table_pii_risk(1, 10) == "medium"


def test_classify_table_risk_high():
    assert classify_table_pii_risk(3, 10) == "high"


def test_classify_table_risk_critical():
    assert classify_table_pii_risk(5, 10) == "critical"
    assert classify_table_pii_risk(10, 15) == "critical"
