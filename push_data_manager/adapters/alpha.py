import os
from datetime import date, datetime

import requests

from .protocol import NormalizedApplication

_STATUS_MAP = {
    "NEW": "new",
    "IN_REVIEW": "in_review",
    "REJECTED": "rejected",
    "HIRED": "hired",
}


def _age(birth_date_str: str) -> int:
    # date.fromisoformat raises ValueError on invalid input — intentional.
    # The manager catches this and records it as normalization_error.
    born = date.fromisoformat(birth_date_str)
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


class AlphaAdapter:
    def __init__(self) -> None:
        self._base_url = os.environ.get("ATS_ALPHA_URL", "http://fake_ats_alpha:8000")

    def fetch_applications(self, since: datetime) -> list[dict]:
        resp = requests.get(
            f"{self._base_url}/api/applications",
            params={"since": since.isoformat()},
        )
        resp.raise_for_status()
        return resp.json()

    def normalize(self, raw: dict) -> NormalizedApplication:
        return NormalizedApplication(
            external_id=raw["id"],
            ats_source="alpha",
            first_name=raw["first_name"],
            last_name=raw["last_name"],
            email=raw.get("email") or "",
            phone=raw.get("phone_number") or "",
            age=_age(raw["birth_date"]),                             # ValueError if invalid
            job_external_id=raw.get("job_req_id") or "",
            internal_status=_STATUS_MAP[raw["application_status"]], # KeyError if unknown
            applied_at=raw["applied_at"],
        )
