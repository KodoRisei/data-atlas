import re
from dataclasses import dataclass

_NAME_PATTERNS: list[tuple[str, str]] = [
    # (regex, pii_type)
    (r"\bemail\b|\bemail_address\b|\buser_email\b|\bcustomer_email\b", "email"),
    (r"\bphone\b|\bphone_number\b|\bmobile\b|\bcell\b|\bcontact_number\b", "phone"),
    (r"\baddress\b|\bstreet\b|\bzip\b|\bpostal\b|\bcity\b|\bstate\b", "address"),
    (
        r"\bbirth_?date\b|\bdate_?of_?birth\b|\bdob\b|\bage\b",
        "birth_date",
    ),
    (
        r"\bssn\b|\bsocial_?security\b|\bsocial_?security_?number\b",
        "ssn",
    ),
    (
        r"\bcredit_?card\b|\bcard_?number\b|\bpan\b|\bcvv\b",
        "credit_card",
    ),
    (
        r"\bpassword\b|\bpasswd\b|\bhashed_?password\b|\bpwd\b",
        "password",
    ),
    (
        r"\btoken\b|\bapi_?key\b|\bsecret\b|\baccess_?token\b|\brefresh_?token\b",
        "token",
    ),
    (
        r"\bip_?address\b|\bip\b|\bclient_?ip\b|\bremote_?addr\b",
        "ip_address",
    ),
    (
        r"\bfirst_?name\b|\blast_?name\b|\bfull_?name\b|\bdisplay_?name\b"
        r"|\buser_?name(?!_id)\b",
        "name",
    ),
    (r"\blatitude\b|\blongitude\b|\bgeo\b|\blocation\b|\bcoords\b", "address"),
    (r"\biban\b|\baccount_?number\b|\brouting_?number\b", "credit_card"),
]

_COMPILED = [
    (re.compile(pattern, re.IGNORECASE), pii_type)
    for pattern, pii_type in _NAME_PATTERNS
]


@dataclass
class PIIDetectionResult:
    is_pii: bool
    pii_type: str | None
    confidence: float
    reason: str


def detect_pii(column_name: str, data_type: str = "") -> PIIDetectionResult:
    """
    Deterministic PII detection based on column naming conventions.
    Returns confidence 1.0 for exact keyword hits, 0.8 for partial.
    """
    normalized = column_name.lower().replace("-", "_")

    for pattern, pii_type in _COMPILED:
        if pattern.search(normalized):
            # Higher confidence for exact full-name matches
            confidence = 1.0 if re.fullmatch(pattern, normalized) else 0.85
            return PIIDetectionResult(
                is_pii=True,
                pii_type=pii_type,
                confidence=confidence,
                reason=f"Column name '{column_name}' matches pattern for {pii_type}",
            )

    return PIIDetectionResult(
        is_pii=False,
        pii_type=None,
        confidence=1.0,
        reason="No PII pattern matched",
    )


def classify_table_pii_risk(pii_column_count: int, total_columns: int) -> str:
    """Returns: low | medium | high | critical"""
    if pii_column_count == 0:
        return "low"
    ratio = pii_column_count / max(total_columns, 1)
    if pii_column_count >= 5 or ratio >= 0.4:
        return "critical"
    if pii_column_count >= 3 or ratio >= 0.2:
        return "high"
    if pii_column_count >= 1:
        return "medium"
    return "low"
