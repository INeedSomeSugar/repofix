from __future__ import annotations

import json
from importlib.resources import files

from .storage import sha256


def all_cases(include_upstream: bool = False, include_holdout: bool = False) -> list[dict]:
    data = files("repofix").joinpath("fixtures/cases.json").read_text(encoding="utf-8")
    result = json.loads(data)
    if include_upstream:
        extra = files("repofix").joinpath("fixtures/upstream.json").read_text(encoding="utf-8")
        result.extend(json.loads(extra))
    if include_holdout:
        extra = files("repofix").joinpath("fixtures/holdout.json").read_text(encoding="utf-8")
        result.extend(json.loads(extra))
    return result


def get_case(case_id: str) -> dict:
    for case in all_cases(include_upstream=True, include_holdout=True):
        if case["id"] == case_id:
            return case
    raise ValueError("unknown case id")


def case_fingerprint(case: dict) -> str:
    return sha256(json.dumps(case, sort_keys=True, ensure_ascii=False).encode("utf-8"))


def dataset_type(case_ids: list[str]) -> str:
    prospective = [get_case(key).get("difficulty") == "prospective_holdout_v1" for key in case_ids]
    if prospective and all(prospective):
        return "prospective_synthetic_holdout_v1"
    if any(prospective):
        return "mixed_development_and_prospective_tasks"
    upstream = {isinstance(get_case(key)["provenance"], dict) for key in case_ids}
    if upstream == {True}:
        return "curated_upstream_development_excerpts"
    if upstream == {False, True}:
        return "mixed_trusted_development_tasks"
    return "original_synthetic_development_exercises"


def public_case(case: dict) -> dict:
    return {key: case[key] for key in ("id", "title", "category", "issue", "difficulty")}
