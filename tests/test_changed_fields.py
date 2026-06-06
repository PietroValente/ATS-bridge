"""
Unit test for repository.upsert_candidate — the change-detection engine.

The (created, changed_fields) tuple this returns is what drives every event
the system emits: created → candidate.created, changed_fields non-empty →
candidate.updated, both empty → no event. Getting this wrong means spurious
events or missed updates, so the full insert → no-op → update lifecycle is
exercised end-to-end against one real SQLite file.
"""
import os
import tempfile

import repository

_BASE = {
    "external_id": "alpha-001",
    "ats_source": "alpha",
    "first_name": "Mario",
    "last_name": "Rossi",
    "email": "mario.rossi@example.com",
    "phone": "+39 02 1234567",
    "age": 35,
    "job_external_id": "REQ-001",
    "internal_status": "new",
    "applied_at": "2026-01-15T09:00:00Z",
}


def _make_db():
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    repository.init_db(f.name)
    return f.name


def test_upsert_lifecycle():
    db = _make_db()
    try:
        # 1. First insert: created, no changed fields, pk is a UUID string.
        pk, created, changed = repository.upsert_candidate(db, _BASE)
        assert created is True
        assert changed == []
        assert isinstance(pk, str) and len(pk) == 36

        # 2. Identical re-upsert: no-op (drives "no event"), pk is stable.
        pk2, created, changed = repository.upsert_candidate(db, _BASE)
        assert pk2 == pk
        assert created is False
        assert changed == []

        # 3. One field changes: detected precisely, pk unchanged.
        _, created, changed = repository.upsert_candidate(db, {**_BASE, "internal_status": "hired"})
        assert created is False
        assert changed == ["internal_status"]

        # 4. Several fields change at once: all detected, none spurious.
        _, created, changed = repository.upsert_candidate(
            db, {**_BASE, "internal_status": "rejected", "phone": "+39 06 9999999"}
        )
        assert created is False
        assert set(changed) == {"internal_status", "phone"}

        # 5. Same external_id, different ats_source: the UNIQUE(ats_source,
        # external_id) key makes this a distinct candidate with its own pk.
        pk_beta, created, _ = repository.upsert_candidate(db, {**_BASE, "ats_source": "beta"})
        assert created is True
        assert pk_beta != pk
    finally:
        os.unlink(db)
