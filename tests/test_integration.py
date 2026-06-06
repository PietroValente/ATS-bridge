"""
End-to-end integration test — requires all containers running on a fresh state:
  docker compose down -v && docker compose up --build -d && sleep 15

Run with: pytest tests/test_integration.py -v

One test walks the whole pipeline for Alpha: HTTP fetch → normalize → validate
→ gRPC upsert → event publish, then asserts the incremental-sync watermark
makes a second call a no-op. Beta shares this exact manager path via the
adapter registry, so exercising Alpha exercises the machinery for both.
"""
import os

import pytest
import requests

BASE = os.environ.get("PDM_URL", "http://localhost:8000")


@pytest.fixture(autouse=True)
def _check_services():
    try:
        requests.get(f"{BASE}/api/v1/sync/alpha/status", timeout=3)
    except requests.ConnectionError:
        pytest.skip("push_data_manager not reachable — start containers first")


def test_end_to_end_sync_and_idempotency():
    # First sync: pulls all Alpha fixtures and pushes the valid ones.
    r = requests.post(f"{BASE}/api/v1/sync/alpha", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert set(d) >= {"pulled", "pushed", "skipped", "skipped_reasons"}
    assert d["pulled"] >= 9
    assert d["pushed"] >= 7

    # The three malformed fixtures must be skipped for three distinct reasons —
    # this is the validate/normalize split observable from the outside:
    #   alpha-minor   → minor_candidate      (parses, fails business rule)
    #   alpha-noemail → missing_email        (parses, fails business rule)
    #   alpha-baddate → normalization_error  (does not parse)
    reasons = d["skipped_reasons"]
    assert reasons.get("minor_candidate", 0) >= 1
    assert reasons.get("missing_email", 0) >= 1
    assert reasons.get("normalization_error", 0) >= 1

    # Status endpoint reflects the sync that just ran.
    s = requests.get(f"{BASE}/api/v1/sync/alpha/status", timeout=5).json()
    assert s["last_sync_at"] is not None
    assert s["total_pushed"] > 0

    # Second sync is a no-op: the watermark advanced to now() and every fixture
    # is dated in the past, so nothing is pulled or pushed again.
    d2 = requests.post(f"{BASE}/api/v1/sync/alpha", timeout=30).json()
    assert d2["pulled"] == 0
    assert d2["pushed"] == 0
