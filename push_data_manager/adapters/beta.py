import os
from datetime import datetime, timezone

import requests

from .protocol import NormalizedApplication

_STATUS_MAP = {
    "new_application": "new",
    "screening": "in_review",
    "not_a_fit": "rejected",
    "offer_accepted": "hired",
}


class BetaAdapter:
    def __init__(self) -> None:
        self._base_url = os.environ.get("ATS_BETA_URL", "http://fake_ats_beta:8000")

    def fetch_applications(self, since: datetime) -> list[dict]:
        resp = requests.get(
            f"{self._base_url}/v2/candidates",
            params={"updated_after": int(since.timestamp())},
        )
        resp.raise_for_status()
        return resp.json()

    def normalize(self, raw: dict) -> NormalizedApplication:
        parts = (raw["full_name"] or "").split(" ", 1)
        contact = raw.get("contact") or {}
        applied_at = (
            datetime.fromtimestamp(raw["submitted_timestamp"], tz=timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        return NormalizedApplication(
            external_id=raw["candidate_uuid"],
            ats_source="beta",
            first_name=parts[0],
            last_name=parts[1] if len(parts) > 1 else "",
            email=contact.get("email_address") or "",
            phone=contact.get("mobile") or "",
            age=raw.get("age") or 0,
            job_external_id=raw.get("position_code") or "",
            internal_status=_STATUS_MAP[raw["stage"]],  # KeyError if unknown
            applied_at=applied_at,
        )
