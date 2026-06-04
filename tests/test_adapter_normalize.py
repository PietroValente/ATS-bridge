"""
Unit tests for AlphaAdapter.normalize.

These tests exercise the normalization logic in isolation — no HTTP calls,
no Django, no gRPC. The key invariant being tested is the boundary between
normalization (adapter's job: raise on bad data) and validation (manager's
job: decide to skip based on the normalized value).
"""
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


def test_normalize_valid_record():
    result = _adapter.normalize(_VALID_RAW)
    assert result.external_id == "alpha-001"
    assert result.ats_source == "alpha"
    assert result.first_name == "Mario"
    assert result.last_name == "Rossi"
    assert result.email == "mario.rossi@example.com"
    assert result.internal_status == "new"
    assert result.job_external_id == "REQ-001"
    assert result.applied_at == "2026-01-15T09:00:00Z"
    assert result.age >= 18  # born 1990, definitely adult


def test_normalize_all_status_mappings():
    for raw_status, expected in [
        ("NEW", "new"),
        ("IN_REVIEW", "in_review"),
        ("REJECTED", "rejected"),
        ("HIRED", "hired"),
    ]:
        raw = {**_VALID_RAW, "application_status": raw_status}
        assert _adapter.normalize(raw).internal_status == expected


def test_normalize_invalid_birth_date_raises():
    """Adapter raises ValueError; the manager catches it as normalization_error."""
    raw = {**_VALID_RAW, "birth_date": "not-a-date"}
    with pytest.raises(ValueError):
        _adapter.normalize(raw)


def test_normalize_unknown_status_raises():
    """Adapter raises KeyError; the manager catches it as normalization_error."""
    raw = {**_VALID_RAW, "application_status": "PENDING"}
    with pytest.raises(KeyError):
        _adapter.normalize(raw)


def test_normalize_empty_email_passes_through():
    """Normalization succeeds; validation (manager) rejects on missing_email."""
    raw = {**_VALID_RAW, "email": ""}
    result = _adapter.normalize(raw)
    assert result.email == ""


def test_normalize_null_phone_becomes_empty_string():
    raw = {**_VALID_RAW, "phone_number": None}
    result = _adapter.normalize(raw)
    assert result.phone == ""


def test_normalize_minor_passes_through():
    """Age < 18 is a valid normalize result; manager rejects it as minor_candidate."""
    raw = {**_VALID_RAW, "birth_date": "2012-01-15"}
    result = _adapter.normalize(raw)
    assert result.age < 18
