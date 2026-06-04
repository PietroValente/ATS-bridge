import json
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Fake ATS Beta")

FIXTURES_PATH = Path("fixtures/candidates.json")


def _load() -> list[dict]:
    return json.loads(FIXTURES_PATH.read_text())


@app.get("/v2/candidates")
def list_candidates(updated_after: Optional[int] = Query(default=None)):
    candidates = _load()
    if updated_after is not None:
        candidates = [c for c in candidates if c["submitted_timestamp"] > updated_after]
    return candidates


@app.get("/v2/candidates/{candidate_uuid}")
def get_candidate(candidate_uuid: str):
    for c in _load():
        if c["candidate_uuid"] == candidate_uuid:
            return c
    raise HTTPException(status_code=404, detail="Not found")
