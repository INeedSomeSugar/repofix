import json

import pytest

from repofix.cases import all_cases, get_case
from repofix.engine import AgentEngine, create_run
from repofix.evaluation import write_report
from repofix.providers import ProviderError
from repofix.schema import Limits
from repofix.workspace import Workspace


@pytest.mark.parametrize("case_id", [case["id"] for case in all_cases()])
def test_replay_executes_failing_baseline_and_independent_grading(settings, store, case_id):
    state = create_run(store, case_id)
    result = AgentEngine(settings, store).run(state.run_id)
    assert result.status == "verified", result.error_code
    assert not result.baseline["passed"]
    assert result.final_public["passed"] and result.grade["passed"]
    assert result.grade["source_changed"]
    assert result.grade["patch_sha256"] == result.patch_sha256
    assert result.model == "scripted-replay-not-a-model"
    Workspace(store.directory(state.run_id)).verify_integrity(state.manifest)


def call(name, arguments, number):
    return {
        "message": {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": f"call_{number}",
                    "type": "function",
                    "function": {"name": name, "arguments": json.dumps(arguments)},
                }
            ],
        },
        "usage": {"total_tokens": 20},
        "finish_reason": "tool_calls",
    }


class FeedbackProvider:
    model = "unit-test-script-not-a-model"

    def __init__(self):
        self.index = 0
        self.saw_failure = False

    def complete(self, messages, tools, max_tokens):
        assert "class IndependentTests" not in json.dumps(messages)
        assert "test_invalid_window" not in json.dumps(messages)
        original = get_case("rolling_average")["files"]["project/core.py"]
        solution = get_case("rolling_average")["replay_edits"][0]["new"]
        wrong = "def rolling_average(values, window):\n    return []\n"
        index, self.index = self.index, self.index + 1
        if index == 0:
            return call(
                "replace_text", {"path": "project/core.py", "old": original, "new": wrong}, index
            )
        if index == 1:
            return call("run_tests", {}, index)
        if index == 2:
            result = json.loads(messages[-1]["content"])
            self.saw_failure = result["passed"] is False and result["failures"] == 2
            assert self.saw_failure
            return call(
                "replace_text", {"path": "project/core.py", "old": wrong, "new": solution}, index
            )
        if index == 3:
            return call("run_tests", {}, index)
        return {"message": {"role": "assistant", "content": "已根据执行反馈修复。"}, "usage": {}}


def test_execution_failure_is_returned_to_next_model_turn(settings, store):
    state = create_run(store, "rolling_average")
    provider = FeedbackProvider()
    result = AgentEngine(settings, store).run(state.run_id, provider)
    assert result.status == "verified" and provider.saw_failure
    assert result.turns == 5


def test_single_patch_stops_without_iterative_feedback(settings, store):
    state = create_run(store, "rolling_average", strategy="single_patch")
    provider = FeedbackProvider()
    result = AgentEngine(settings, store).run(state.run_id, provider)
    assert result.status == "failed"
    assert provider.index == 1 and not provider.saw_failure


def test_resume_uses_checkpoint_without_resetting_usage_or_history(settings, store):
    state = create_run(store, "csv_records")
    engine = AgentEngine(settings, store)
    paused = engine.run(state.run_id, pause_after_turns=4)
    assert paused.status == "paused" and paused.turns == 4
    patch = (store.directory(state.run_id) / "patch.diff").read_bytes()
    assert patch
    finished = AgentEngine(settings, store).run(state.run_id)
    assert finished.status == "verified" and finished.turns == 6
    assert (store.directory(state.run_id) / "patch.diff").read_bytes() == patch
    before = len(store.events(state.run_id))
    engine.run(state.run_id)
    assert len(store.events(state.run_id)) == before


def test_turn_budget_does_not_claim_success(settings, store):
    state = create_run(store, "csv_records", limits=Limits(max_turns=1))
    result = AgentEngine(settings, store).run(state.run_id)
    assert result.status == "budget_exhausted" and result.error_code == "turn_limit"
    assert result.grade is None


def test_provider_failure_is_persisted_and_retryable(settings, store):
    class Failing:
        model = "test"

        def complete(self, *args):
            raise ProviderError("provider_http_401")

    state = create_run(store, "csv_records")
    result = AgentEngine(settings, store).run(state.run_id, Failing())
    assert result.status == "error" and store.load(state.run_id).error_code == "provider_http_401"
    assert AgentEngine(settings, store).run(state.run_id).status == "verified"


def test_changed_task_cannot_be_silently_resumed(settings, store, monkeypatch):
    state = create_run(store, "csv_records")
    monkeypatch.setattr("repofix.engine.case_fingerprint", lambda case: "changed")
    result = AgentEngine(settings, store).run(state.run_id)
    assert result.error_code == "case_changed_since_run_creation"


def test_replay_has_no_real_model_repair_metric(settings, store, tmp_path):
    state = create_run(store, "csv_records")
    state = AgentEngine(settings, store).run(state.run_id)
    report = write_report([state], tmp_path / "report.json")
    assert report["groups"][0]["real_model_repair_rate"] is None
    assert report["groups"][0]["observed_tokens"] is None
    with pytest.raises(ValueError, match="already exists"):
        write_report([state], tmp_path / "report.json")
