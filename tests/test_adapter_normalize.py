"""
Unit test for the normalize/validate boundary (AlphaAdapter.normalize).

This is the single most important contract in the manager pipeline: the
adapter RAISES on data it cannot parse (bad birth_date, unknown status) so
the manager can bucket it as normalization_error, but it PASSES THROUGH data
that parses yet fails a business rule (empty email, minor age, null phone) —
because deciding to skip those is the manager's job, not the adapter's.
"""
from datetime import date

import pytest

from adapters.alpha import AlphaAdapter

_adapter = AlphaAdapter()

_VALID_RAW = {
    "id": "alpha-001",
    "first_name": "Mario",
    "last_name": "Rossi",
    "email": "mario.rossi@example.com",
    "phone_number": "+39 02 1234567",
    "birth_date": "1990-03-15",
    "job_req_id": "REQ-001",
    "application_status": "NEW",
    "applied_at": "2026-01-15T09:00:00Z",
}


def test_normalize_boundary():
    # --- 1. A clean record maps every field and computes age exactly. ---
    result = _adapter.normalize(_VALID_RAW)
    assert result.external_id == "alpha-001"
    assert result.ats_source == "alpha"
    assert result.first_name == "Mario"
    assert result.last_name == "Rossi"
    assert result.email == "mario.rossi@example.com"
    assert result.job_external_id == "REQ-001"
    assert result.applied_at == "2026-01-15T09:00:00Z"
    # Born 1990-03-15; the March birthday has passed by any sync date past March,
    # so age is exactly the year delta — verifies the age arithmetic, not a range.
    assert result.age == date.today().year - 1990

    # --- 2. Every source status maps to its internal value. ---
    for raw_status, expected in [
        ("NEW", "new"),
        ("IN_REVIEW", "in_review"),
        ("REJECTED", "rejected"),
        ("HIRED", "hired"),
    ]:
        assert _adapter.normalize({**_VALID_RAW, "application_status": raw_status}).internal_status == expected

    # --- 3. Structurally-invalid-but-parseable data PASSES THROUGH unchanged.
    # The adapter must not reject these; the manager's _validate() decides. ---
    assert _adapter.normalize({**_VALID_RAW, "email": ""}).email == ""          # → manager: missing_email
    assert _adapter.normalize({**_VALID_RAW, "phone_number": None}).phone == ""  # null phone is tolerated
    assert _adapter.normalize({**_VALID_RAW, "birth_date": "2012-01-15"}).age < 18  # → manager: minor_candidate

    # --- 4. Unparseable data RAISES. The manager catches these as
    # normalization_error; the exception type is the adapter's contract. ---
    with pytest.raises(ValueError):
        _adapter.normalize({**_VALID_RAW, "birth_date": "not-a-date"})
    with pytest.raises(KeyError):
        _adapter.normalize({**_VALID_RAW, "application_status": "PENDING"})
