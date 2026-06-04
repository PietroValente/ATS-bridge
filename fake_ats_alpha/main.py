import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Fake ATS Alpha")

FIXTURES_PATH = Path("fixtures/applications.json")


def _load() -> list[dict]:
    return json.loads(FIXTURES_PATH.read_text())


@app.get("/api/applications")
def list_applications(since: Optional[str] = Query(default=None)):
    apps = _load()
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            apps = [
                a for a in apps
                if datetime.fromisoformat(a["applied_at"].replace("Z", "+00:00")) > since_dt
            ]
        except ValueError:
            pass  # malformed since → return all
    return apps


@app.get("/api/applications/{application_id}")
def get_application(application_id: str):
    for a in _load():
        if a["id"] == application_id:
            return a
    raise HTTPException(status_code=404, detail="Not found")
