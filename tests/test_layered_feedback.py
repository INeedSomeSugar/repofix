import json

import pytest

from repofix.cases import get_case
from repofix.engine import AgentEngine, create_run
from repofix.evaluation import write_report
from repofix.feedback import restore_checkpoint, run_layered_tests
from repofix.runner import run_tests
from repofix.schema import Limits, RunState
from repofix.workspace import PolicyError, Workspace

BAD_TEST = """import unittest
from project.core import rolling_average
class GeneratedHypothesis(unittest.TestCase):
    def test_wrong_expectation(self):
        self.assertEqual(rolling_average([1, 2, 3], 2), [])
"""


def tool(name, args, key):
    return {
        "id": key,
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args)},
    }


class Script:
    model = "scripted-feedback-regression-not-a-model"

    def __init__(self, steps):
        self.steps = steps
        self.seen = []

    def complete(self, messages, tools, max_tokens):
        assert "class IndependentTests" not in json.dumps(messages)
        index = sum(m["role"] == "assistant" for m in messages)
        self.seen = messages.copy()
        calls = self.steps[index](messages) if index < len(self.steps) else []
        return {
            "message": {"role": "assistant", "content": "scripted test", "tool_calls": calls},
            "usage": {},
            "finish_reason": "tool_calls" if calls else "stop",
        }


def repaired_workspace(store):
    state = create_run(store, "rolling_average")
    workspace = Workspace(store.directory(state.run_id))
    for index, edit in enumerate(get_case("rolling_average")["replay_edits"]):
        workspace.replace_text(f"fix_{index}", **edit)
    return state, workspace


def test_original_and_generated_failures_have_separate_results_and_checkpoint(store):
    state, workspace = repaired_workspace(store)
    workspace.write_test("hypothesis", "tests/test_agent_wrong.py", BAD_TEST)
    result = run_layered_tests(workspace, state.manifest, run_tests)
    assert result["trusted"]["passed"]
    assert not result["agent_generated"]["passed"]
    assert result["requires_spec_review"] and not result["passed"]
    assert result["agent_test_files"] == ["tests/test_agent_wrong.py"]
    assert result["trusted"]["tests_run"] == 2 and result["agent_generated"]["tests_run"] == 1
    assert result["checkpoint_id"]


def test_restore_is_explicit_hash_checked_idempotent_and_retains_generated_tests(store):
    state, workspace = repaired_workspace(store)
    checkpoint = run_layered_tests(workspace, state.manifest, run_tests)["checkpoint_id"]
    correct = workspace.read_file("project/core.py")["content"]
    workspace.write_test("hypothesis", "tests/test_agent_wrong.py", BAD_TEST)
    workspace.replace_text(
        "regression",
        "project/core.py",
        correct,
        "def rolling_average(values, window):\n    return []\n",
    )
    restored = restore_checkpoint(workspace, "rollback", checkpoint)
    assert workspace.read_file("project/core.py")["content"] == correct
    assert workspace.read_file("tests/test_agent_wrong.py")["content"] == BAD_TEST
    assert restore_checkpoint(workspace, "rollback", checkpoint) == restored
    workspace.verify_integrity(state.manifest)


def test_corrupt_checkpoint_cannot_mutate_current_source(store):
    state, workspace = repaired_workspace(store)
    checkpoint = run_layered_tests(workspace, state.manifest, run_tests)["checkpoint_id"]
    source = workspace.root / "project/core.py"
    before = source.read_bytes()
    (workspace.run_dir / "checkpoints" / checkpoint / "project/core.py").write_text("corrupt")
    with pytest.raises(PolicyError, match="checkpoint source hash"):
        restore_checkpoint(workspace, "rollback", checkpoint)
    assert source.read_bytes() == before


def test_checkpoint_path_traversal_is_rejected(store):
    state = create_run(store, "rolling_average")
    with pytest.raises(PolicyError, match="invalid checkpoint"):
        restore_checkpoint(Workspace(store.directory(state.run_id)), "rollback", "../original")


def test_unresolved_generated_assertion_never_becomes_verified(settings, store):
    edits = get_case("rolling_average")["replay_edits"]
    steps = [
        lambda m: [tool("replace_text", edit, f"fix_{i}") for i, edit in enumerate(edits)],
        lambda m: [
            tool("write_test", {"path": "tests/test_agent_wrong.py", "content": BAD_TEST}, "hyp")
        ],
        lambda m: [tool("run_tests", {}, "test")],
    ]
    state = create_run(store, "rolling_average")
    result = AgentEngine(settings, store).run(state.run_id, Script(steps))
    assert result.status == "needs_review"
    assert result.final_public["trusted"]["passed"] and result.grade["passed"]
    assert not result.final_public["agent_generated"]["passed"]
    assert len(result.checkpoints) == 1
    before = len(store.events(state.run_id))
    assert AgentEngine(settings, store).run(state.run_id).status == "needs_review"
    assert len(store.events(state.run_id)) == before


def test_repeated_failure_stops_before_later_calls_in_same_batch(settings, store):
    edit = get_case("rolling_average")["replay_edits"][0]
    steps = [
        lambda m: [tool("run_tests", {}, "test1")],
        lambda m: [tool("run_tests", {}, "test2"), tool("replace_text", edit, "too_late")],
    ]
    state = create_run(store, "rolling_average", limits=Limits(max_repeated_test_states=2))
    result = AgentEngine(settings, store).run(state.run_id, Script(steps))
    assert result.status == "stalled" and result.stop_reason == "repeated_test_state"
    assert result.turns == 2 and result.tool_calls == 2
    assert result.grade is not None and not result.grade["passed"]
    assert not result.pending_calls
    assert not Workspace(store.directory(state.run_id)).diff()
    assert store.events(state.run_id)[-2]["cancelled_call_ids"] == ["too_late"]


def test_repeat_guard_survives_pause_and_resume(settings, store):
    state = create_run(store, "rolling_average", limits=Limits(max_repeated_test_states=2))
    script = Script(
        [lambda m: [tool("run_tests", {}, "test1")], lambda m: [tool("run_tests", {}, "test2")]]
    )
    paused = AgentEngine(settings, store).run(state.run_id, script, pause_after_turns=1)
    assert paused.status == "paused" and list(paused.tested_states.values()) == [1]
    stopped = AgentEngine(settings, store).run(state.run_id, script)
    assert stopped.status == "stalled" and stopped.turns == 2


def test_changed_workspace_is_not_misclassified_as_repeated_testing(settings, store):
    edit = get_case("rolling_average")["replay_edits"][0]
    state = create_run(store, "rolling_average", limits=Limits(max_repeated_test_states=2))
    script = Script(
        [
            lambda m: [tool("run_tests", {}, "test1")],
            lambda m: [tool("replace_text", edit, "fix")],
            lambda m: [tool("run_tests", {}, "test2")],
        ]
    )
    result = AgentEngine(settings, store).run(state.run_id, script)
    assert result.status == "verified" and result.stop_reason is None
    assert sorted(result.tested_states.values()) == [1, 1]


def test_old_saved_runs_keep_legacy_policy(store):
    state = create_run(store, "rolling_average")
    old = state.model_dump(
        exclude={"feedback_policy", "tested_states", "checkpoints", "stop_reason"}
    )
    assert RunState.model_validate(old).feedback_policy == "legacy_all"


def test_reports_do_not_pool_different_feedback_policies(store, tmp_path):
    legacy = create_run(store, "rolling_average", feedback_policy="legacy_all")
    layered = create_run(store, "rolling_average")
    report = write_report([legacy, layered], tmp_path / "mixed-policy.json")
    assert len(report["groups"]) == 2
    assert {g["feedback_policy"] for g in report["groups"]} == {"legacy_all", "layered_v1"}
