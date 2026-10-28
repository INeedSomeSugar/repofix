import json
import zipfile
from collections import Counter

import httpx
import pytest

from repofix.cases import all_cases, case_fingerprint, dataset_type, get_case
from repofix.config import Settings
from repofix.docker_runner import DockerRunner
from repofix.engine import create_run
from repofix.evaluation import code_fingerprint
from repofix.storage import atomic_json, sha256
from repofix.workspace import check_python
from scripts.build_holdout_cases import build
from scripts.compare_feedback import ARMS, AuditedDeepSeekProvider, Comparison

IMAGE = "sha256:" + "c" * 64
CASES = [case["id"] for case in build()]


def prepared(tmp_path, monkeypatch):
    monkeypatch.setattr(
        DockerRunner, "preflight", lambda self: {"available": True, "image_id": IMAGE}
    )
    admission = tmp_path / "admission.json"
    atomic_json(
        admission,
        {
            "passed": True,
            "code_sha256": code_fingerprint(),
            "image_id": IMAGE,
            "case_sha256": {key: case_fingerprint(get_case(key)) for key in CASES},
        },
    )
    comparison = Comparison(Settings(data_dir=tmp_path / "work"))
    plan = comparison.freeze(admission, provider="replay", model="scripted-replay-not-a-model")
    return comparison, plan


def test_new_frozen_cases_do_not_enter_default_development_or_upstream_lists():
    assert len(all_cases()) == 5 and len(all_cases(include_upstream=True)) == 8
    assert len(all_cases(include_holdout=True)) == 8
    assert dataset_type(CASES) == "prospective_synthetic_holdout_v1"
    assert dataset_type(["csv_records", CASES[0]]) == "mixed_development_and_prospective_tasks"


@pytest.mark.parametrize("case", build(), ids=lambda c: c["id"])
def test_holdout_specs_hashes_policy_and_docker_gate(case, tmp_path):
    assert get_case(case["id"]) == case
    provenance = case["provenance"]
    assert provenance["independent_human_review"] is False
    assert sha256(case["heldout"].encode()) == provenance["independent_tests_sha256"]
    check_python(case["files"]["project/core.py"])
    check_python(case["replay_edits"][0]["new"])
    check_python(case["files"]["tests/test_public.py"], is_test=True)
    check_python(case["heldout"], is_test=True)
    from repofix.storage import RunStore

    store = RunStore(tmp_path / "runs")
    with pytest.raises(ValueError, match="require_docker"):
        create_run(store, case["id"])
    state = create_run(store, case["id"], runner_kind="docker", runner_image=IMAGE)
    visible = store.directory(state.run_id) / "repository"
    assert not any("IndependentTests" in p.read_text("utf-8") for p in visible.rglob("*.py"))


def test_freeze_binds_admission_and_balances_three_arm_positions(tmp_path, monkeypatch):
    comparison, plan = prepared(tmp_path, monkeypatch)
    loaded = comparison.load(plan["comparison_id"])
    assert len(loaded["trials"]) == 18
    positions = {arm["name"]: Counter() for arm in ARMS}
    for index, trial in enumerate(loaded["trials"]):
        positions[trial["arm"]][index % 3] += 1
    assert all(sorted(counts.values()) == [2, 2, 2] for counts in positions.values())
    directory = comparison.path(plan["comparison_id"]).parent
    assert (
        sha256((directory / "admission.json").read_bytes()) == plan["manifest"]["admission_sha256"]
    )
    with zipfile.ZipFile(directory / "source.zip") as archive:
        assert archive.testzip() is None
        assert "src/repofix/fixtures/holdout.json" in archive.namelist()


@pytest.mark.parametrize("mutation", ["manifest", "grid", "duplicate_run"])
def test_changed_manifest_grid_or_run_ids_are_rejected(tmp_path, monkeypatch, mutation):
    comparison, plan = prepared(tmp_path, monkeypatch)
    if mutation == "manifest":
        plan["manifest"]["model"] = "tampered"
    elif mutation == "grid":
        plan["trials"].reverse()
    else:
        for trial in plan["trials"][:2]:
            trial["run_id"] = "a" * 32
    atomic_json(comparison.path(plan["comparison_id"]), plan)
    with pytest.raises(ValueError, match="comparison_"):
        comparison.load(plan["comparison_id"])


def test_failed_trials_are_not_retried_or_reported_as_zero_cost(tmp_path, monkeypatch):
    comparison, plan = prepared(tmp_path, monkeypatch)
    calls = []

    def fail(engine, run_id):
        calls.append(run_id)
        state = engine.store.load(run_id)
        state.status, state.error_code = "error", "synthetic_transport_error"
        engine.store.save(state)
        return state

    monkeypatch.setattr("scripts.compare_feedback.AgentEngine.run", fail)
    key = plan["comparison_id"]
    first = comparison.run(key, stop_after=1)
    assert not first["complete"] and len(calls) == 1
    final = comparison.run(key)
    assert final["complete"] and len(calls) == 18
    assert all(group["statuses"] == {"error": 6} for group in final["groups"])
    assert all(group["total_tokens"] is None for group in final["groups"])
    comparison.run(key)
    assert len(calls) == 18


def test_state_budget_tampering_blocks_resume_before_execution(tmp_path, monkeypatch):
    comparison, plan = prepared(tmp_path, monkeypatch)

    def fail(engine, run_id):
        state = engine.store.load(run_id)
        state.status = "error"
        engine.store.save(state)
        return state

    monkeypatch.setattr("scripts.compare_feedback.AgentEngine.run", fail)
    key = plan["comparison_id"]
    partial = comparison.run(key, stop_after=1)
    store = comparison.store(key)
    state = store.load(partial["trials"][0]["run_id"])
    state.limits.max_turns -= 1
    store.save(state)
    with pytest.raises(ValueError, match="run_binding"):
        comparison.run(key)


def test_code_or_fixture_drift_blocks_execution(tmp_path, monkeypatch):
    comparison, plan = prepared(tmp_path, monkeypatch)
    key = plan["comparison_id"]
    original = code_fingerprint()
    monkeypatch.setattr("scripts.compare_feedback.code_fingerprint", lambda: "changed")
    with pytest.raises(ValueError, match="code_changed"):
        comparison.load(key)
    monkeypatch.setattr("scripts.compare_feedback.code_fingerprint", lambda: original)
    monkeypatch.setattr("scripts.compare_feedback.case_fingerprint", lambda case: "changed")
    with pytest.raises(ValueError, match="fixture_changed"):
        comparison.load(key)


def test_admission_must_match_success_and_current_image(tmp_path, monkeypatch):
    comparison, plan = prepared(tmp_path, monkeypatch)
    admission = tmp_path / "admission.json"
    data = json.loads(admission.read_text("utf-8"))
    data["passed"] = False
    atomic_json(admission, data)
    with pytest.raises(ValueError, match="admission_required"):
        comparison.freeze(admission, provider="replay", model="replay")
    data["passed"] = True
    atomic_json(admission, data)
    monkeypatch.setattr(DockerRunner, "preflight", lambda self: {"available": False})
    with pytest.raises(ValueError, match="docker_image_required"):
        comparison.freeze(admission, provider="replay", model="replay")


def test_provider_metadata_keeps_actual_response_model_without_credentials(tmp_path):
    def transport(request):
        return httpx.Response(
            200,
            json={
                "id": "fixture-response",
                "model": "fixture-exact-response-model",
                "choices": [
                    {"message": {"role": "assistant", "content": "done"}, "finish_reason": "stop"}
                ],
                "usage": {"prompt_tokens": 8, "completion_tokens": 2, "total_tokens": 10},
            },
        )

    path = tmp_path / "metadata.jsonl"
    provider = AuditedDeepSeekProvider(
        Settings(data_dir=tmp_path, api_key="fixture-secret-value", model="fixture-request"),
        path,
        transport=httpx.MockTransport(transport),
    )
    try:
        provider.complete([], [], 128)
    finally:
        provider.close()
    row = json.loads(path.read_text("utf-8"))
    assert row["response_model"] == "fixture-exact-response-model"
    assert row["requested_model"] == "fixture-request" and row["usage"]["total_tokens"] == 10
    assert "fixture-secret-value" not in path.read_text("utf-8")
