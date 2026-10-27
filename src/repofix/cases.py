from __future__ import annotations

import json
from importlib.resources import files

from .storage import sha256


def all_cases() -> list[dict]:
    data = files("repofix").joinpath("fixtures/cases.json").read_text(encoding="utf-8")
    return json.loads(data)


def get_case(case_id: str) -> dict:
    for case in all_cases():
        if case["id"] == case_id:
            return case
    raise ValueError("unknown case id")


def case_fingerprint(case: dict) -> str:
    return sha256(json.dumps(case, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def public_case(case: dict) -> dict:
    return {key: case[key] for key in ("id", "title", "category", "issue", "difficulty")}
