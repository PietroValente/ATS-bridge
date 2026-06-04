"""
Integration tests — require all containers to be running:
  docker compose up --build -d && sleep 15

Run with: pytest tests/test_integration.py -v
"""
import sqlite3

import pytest
import requests

BASE = "http://localhost:8000"


@pytest.fixture(autouse=True)
def _check_services():
    try:
        requests.get(f"{BASE}/api/v1/sync/alpha/status", timeout=3)
    except requests.ConnectionError:
        pytest.skip("push_data_manager not reachable — start containers first")


def test_sync_alpha_returns_expected_shape():
    r = requests.post(f"{BASE}/api/v1/sync/alpha", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "pulled" in d and "pushed" in d and "skipped" in d and "skipped_reasons" in d
    assert d["pulled"] >= 9
    assert d["pushed"] >= 7   # at least the clearly valid records
    assert d["skipped"] >= 2  # at minimum: alpha-minor + alpha-noemail


def test_sync_alpha_skipped_reasons_present():
    r = requests.post(f"{BASE}/api/v1/sync/alpha", timeout=30)
    reasons = r.json().get("skipped_reasons", {})
    assert "minor_candidate" in reasons
    assert "missing_email" in reasons
    assert "normalization_error" in reasons


def test_sync_beta_returns_expected_shape():
    r = requests.post(f"{BASE}/api/v1/sync/beta", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["pushed"] >= 7
    assert d["skipped"] >= 2


def test_sync_unknown_ats_returns_400():
    r = requests.post(f"{BASE}/api/v1/sync/gamma", timeout=5)
    assert r.status_code == 400
    assert "error" in r.json()


def test_status_endpoint_after_sync():
    requests.post(f"{BASE}/api/v1/sync/alpha", timeout=30)
    r = requests.get(f"{BASE}/api/v1/sync/alpha/status", timeout=5)
    assert r.status_code == 200
    d = r.json()
    assert d["last_sync_at"] is not None
    assert d["total_pushed"] > 0


def test_sync_idempotent_second_call_pulls_nothing():
    # First sync: pulls everything and advances last_sync_at
    requests.post(f"{BASE}/api/v1/sync/alpha", timeout=30)
    # Second sync: since = last_sync_at (now), fixtures are in the past → 0 pulled
    r = requests.post(f"{BASE}/api/v1/sync/alpha", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d["pulled"] == 0
    assert d["pushed"] == 0
