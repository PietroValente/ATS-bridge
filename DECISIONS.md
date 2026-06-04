# Decisions

## Architectural decisions

### 1. Adapter registry instead of if/elif chains

A dict mapping `ats_source → adapter instance` means the manager never knows which ATS it's talking to. The manager calls `adapter.fetch_applications()` and `adapter.normalize()` — same interface every time. The registry is the only place that knows which ATS exists. Adding a third ATS is one file plus one line in `__init__.py`.

The alternative — branching in the manager — starts reasonable with two sources and becomes unmaintainable at five.

### 2. Normalization raises, validation decides

Each adapter's `normalize()` raises on data it cannot process: `date.fromisoformat("not-a-date")` raises `ValueError`, `STATUS_MAP["PENDING"]` raises `KeyError`. The manager catches both as `normalization_error`.

Structural validation (email present, age ≥ 18) lives in the manager because those rules are internal business rules that apply the same way to every source. Keeping them in the manager means I can change them without touching any adapter.

### 3. Raw sqlite3 in talent_pool instead of an ORM

talent_pool is pure Python, no Django. Adding an ORM (SQLAlchemy, or Django configured for a second service) would be significant overhead for a service that needs one table and three operations. The `repository.py` module is 60 lines and the upsert logic is directly readable.

### 4. Initial `since` sentinel = 2020-01-01

The spec says "7 days ago on first run". With static fixture data, 7 days would make the system unusable the week after development — the evaluator would get 0 candidates on their first sync. Using 2020-01-01 as the sentinel makes the system reliably pull all fixtures on first run regardless of when it's evaluated, which is what the demo actually needs.

### 5. Fixtures mounted as volumes, not baked into the image

`fake_ats_alpha/fixtures/` and `fake_ats_beta/fixtures/` are mounted into their containers via docker-compose volumes. This means the `candidate.updated` demo scenario (edit a fixture → re-sync → verify changed_fields) can be demonstrated by editing files on the host and restarting the container, without rebuilding the image.

---

## Things the AI proposed that I rejected

### 1. Abstract base class with `__init_subclass__` registry auto-registration

AI suggested a metaclass approach where each adapter class automatically registers itself on definition. Rejected: it's a clever trick that adds indirection without solving a real problem. At two adapters, a plain dict in `__init__.py` is more readable. If we ever had 20 adapters it might make sense, but that's a hypothetical. The spec explicitly warns against this.

### 2. Celery or async task queue for sync

AI suggested wrapping sync in a Celery task so it runs in the background without blocking the HTTP response. Rejected: the trigger is a curl command and the sync completes in under a second on the local fixture data. Celery adds a worker process, a broker, and task state management for zero benefit in this scope.

### 3. Outbox pattern for event publication

AI proposed writing events to a database table (outbox) before publishing to Redis, to guarantee at-least-once delivery if Redis is down at publish time. Rejected for this scope: the spec explicitly says not to add this unless I think it through and document it. The simple path (publish immediately after upsert) is correct here. A Redis failure during publish loses the event — that's an acceptable trade-off given the demo context.

### 4. Job model as a first-class entity

AI initially modelled Job as a Django model with its own sync flow. Rejected immediately: the spec is explicit that `job_req_id` / `position_code` is just a string that travels with the candidate. There is no Job entity in this assessment.

### 5. Connection pool for gRPC in push_data_manager

AI proposed a module-level channel object to avoid creating a new channel on every sync call. Rejected: the sync is triggered manually with curl, so there are no concurrent calls. A new channel per call is 1–2ms of overhead on a LAN. Connection pooling is the right answer in production under load; it's premature optimisation here.

---

## Trade-offs

### Static vs dynamic fixture timestamps

Using fixed dates in 2026-01 through 2026-03 means the ATS filtering by `applied_at` / `submitted_timestamp` will work correctly as long as the initial `since` sentinel is far enough in the past (2020-01-01). The trade-off: if someone evaluates the system years from now with a 7-day window, the behaviour changes. I chose correctness over literal spec compliance on the "7 days" default.

### Django runserver vs gunicorn

Using `python manage.py runserver` avoids adding gunicorn to requirements and keeps the Dockerfile simpler. The trade-off: runserver is single-threaded and not safe for concurrent requests. For a manually-triggered curl demo this is irrelevant. The spec says no production-readiness, so this is the right call.

---

## Things I would do differently

### 1. Run `makemigrations` as part of the Dockerfile

I wrote the initial migration by hand (`0001_initial.py`) rather than generating it with Django. This works but is fragile — if the model changes, someone needs to remember to update the migration manually rather than running `manage.py makemigrations`. I would add a build-time `makemigrations` step in CI (not in the Dockerfile, where the DB path might not match) to catch drift.

### 2. Use `grpc.aio` for an async gRPC server in talent_pool

The current talent_pool uses a `ThreadPoolExecutor` which is fine for low concurrency but holds a thread per in-flight request. For a service that sits under a real sync load, `grpc.aio` + asyncio would be cleaner. I kept the synchronous version because it's simpler to reason about and the spec load doesn't justify it.
