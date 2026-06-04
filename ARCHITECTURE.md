# Architecture

## Components

```
curl → push_data_manager (Django, :8000)
           │
           ├─── HTTP GET ──→ fake_ats_alpha (FastAPI, :8001)
           ├─── HTTP GET ──→ fake_ats_beta  (FastAPI, :8002)
           │
           └─── gRPC ──→ talent_pool (Python, :50051)
                              │
                              └─── PUBLISH ──→ Redis pub/sub ──→ event_logger
```

Six containers, one network, zero authentication between services.

---

## How multi-ATS is handled

The core problem is: each ATS has a different field layout, different status vocabulary, and different timestamp format. Spreading `if ats_source == "alpha": ... elif ats_source == "beta": ...` throughout the manager code is the wrong answer — every new ATS multiplies the surface area of those branches.

The solution is a registry of adapters:

```python
REGISTRY: dict[str, ATSAdapter] = {
    "alpha": AlphaAdapter(),
    "beta":  BetaAdapter(),
}
```

Each adapter implements two methods: `fetch_applications(since)` and `normalize(raw)`. The manager looks up the adapter once by name and calls the same interface regardless of which ATS it's talking to. Adding a third ATS means adding one file and one line in the registry — nothing else changes.

The boundary between normalisation and validation is intentional. The adapter raises on data it cannot make sense of (invalid birth_date, unknown status). The manager catches those exceptions and records them as `normalization_error`. Structural validation (email not empty, age ≥ 18) lives exclusively in the manager because these are internal business rules that apply the same way regardless of source ATS.

---

## gRPC contract

Defined in `/proto/klaaryo.proto`. Stubs are generated at Docker build time into each container that needs them; no generated files are committed to the repo.

```
UpsertCandidate(NormalizedCandidate) → UpsertResult
  candidate keyed on (ats_source, external_id)
  returns: candidate_pk, created: bool, changed_fields: []string

GetCandidate(GetCandidateRequest) → Candidate
ListCandidates(ListCandidatesRequest) → ListCandidatesResponse
  ats_source="" returns all candidates
```

`applied_at` is a plain ISO 8601 string in both the normalised schema and the proto, not a proto Timestamp. This avoids timezone conversion friction between services.

---

## Event payload

Published on Redis pub/sub after every non-no-op UpsertCandidate:

```json
{
  "event_id":      "uuid-v4",
  "event_type":    "candidate.created" | "candidate.updated",
  "occurred_at":   "2026-06-04T12:00:00Z",
  "candidate_pk":  42,
  "ats_source":    "alpha",
  "external_id":   "alpha-001",
  "changed_fields": ["internal_status"]
}
```

Rule: if `created=True` → emit `candidate.created`. If `created=False` and `changed_fields` is non-empty → emit `candidate.updated`. If `created=False` and `changed_fields` is empty (no-op) → no event.

---

## Event bus

Redis pub/sub. The talent_pool talks to an `EventBus` Protocol, not to Redis directly. The concrete `RedisEventBus` is instantiated once at server startup and injected into the servicer. Swapping the implementation means changing one line in `server.py`.

---

## Idempotency

**Sync**: keyed on `(ats_source, external_id)` with a UNIQUE constraint in SQLite. `upsert_candidate` compares all tracked fields field-by-field; it emits an event only when at least one field differs.

**Event consumer**: UNIQUE constraint on `event_id` in the `processed_events` table. Duplicate delivery hits `IntegrityError` → logged as `[SKIPPED]`, otherwise `[PROCESSED]`.

---

## Import rule (push_data_manager)

```
managers/       ← adapters, db_models, utils
rest_views/     ← managers only
grpc_handlers/  ← managers only  (not used in this scope)
event_consumers/← managers only  (not used in this scope)
```

`rest_views/sync_views.py` imports exactly one thing: `SyncManager` from `managers`. It contains no model access, no adapter calls, no gRPC imports.
