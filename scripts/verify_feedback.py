"""Exercise wrong test hypotheses, repeated states, and explicit rollback without a model."""

import argparse
import json
import uuid
from pathlib import Path

from repofix.cases import get_case
from repofix.config import Settings
from repofix.engine import AgentEngine, create_run
from repofix.evaluation import code_fingerprint, write_report
from repofix.storage import RunStore, sha256, utc_now

BAD_TEST = """import unittest
from project.core import rolling_average
class GeneratedHypothesis(unittest.TestCase):
    def test_wrong_expectation(self):
        self.assertEqual(rolling_average([1, 2, 3], 2), [])
"""


class Scenario:
    model = "scripted-feedback-validation-not-a-model"

    def __init__(self, scenario):
        self.scenario = scenario

    def complete(self, messages, tools, max_tokens):
        turn = sum(message["role"] == "assistant" for message in messages)
        edit = get_case("rolling_average")["replay_edits"][0]
        wrong = "def rolling_average(values, window):\n    return []\n"
        if self.scenario == "repeated_state":
            step = [("run_tests", {})]
        elif self.scenario == "wrong_hypothesis":
            steps = [
                [("replace_text", edit)],
                [("write_test", {"path": "tests/test_agent_wrong.py", "content": BAD_TEST})],
                [("run_tests", {})],
            ]
            step = steps[turn] if turn < len(steps) else []
        else:
            checkpoint = next(
                (
                    json.loads(m["content"]).get("checkpoint_id")
                    for m in messages
                    if m["role"] == "tool" and json.loads(m["content"]).get("checkpoint_id")
                ),
                "",
            )
            steps = [
                [("replace_text", edit)],
                [("run_tests", {})],
                [("replace_text", {"path": edit["path"], "old": edit["new"], "new": wrong})],
                [("run_tests", {})],
                [("restore_checkpoint", {"checkpoint_id": checkpoint})],
                [("run_tests", {})],
            ]
            step = steps[turn] if turn < len(steps) else []
        calls = [
            {
                "id": f"scenario_{turn}_{index}",
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)},
            }
            for index, (name, args) in enumerate(step)
        ]
        return {
            "message": {
                "role": "assistant",
                "content": "合成回归轨迹，非真实模型。",
                "tool_calls": calls,
            },
            "usage": {},
            "finish_reason": "stop",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", choices=["local", "docker"], default="docker")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    scenarios_path = args.output.with_name(args.output.stem + "-runs.json")
    if args.output.exists() or scenarios_path.exists():
        parser.error("use new output paths")
    root = Path(__file__).resolve().parents[1]
    settings = Settings(data_dir=root / "work" / "feedback-validation" / uuid.uuid4().hex)
    store = RunStore(settings.data_dir / "runs")
    image = "python:3.12-slim"
    if args.runner == "docker":
        from repofix.docker_runner import DockerRunner

        probe = DockerRunner().preflight()
        if not probe["available"]:
            parser.error("Docker unavailable; no local fallback")
        image = probe["image_id"]
    expected = {
        "wrong_hypothesis": "needs_review",
        "repeated_state": "stalled",
        "checkpoint_restore": "verified",
    }
    states, checks = [], []
    for scenario, status in expected.items():
        state = create_run(store, "rolling_average", runner_kind=args.runner, runner_image=image)
        result = AgentEngine(settings, store).run(state.run_id, Scenario(scenario))
        states.append(result)
        check = {
            "scenario": scenario,
            "run_id": result.run_id,
            "expected_status": status,
            "actual_status": result.status,
            "passed": result.status == status,
        }
        if scenario == "wrong_hypothesis":
            check["passed"] &= bool(
                result.final_public
                and result.final_public["trusted"]["passed"]
                and not result.final_public["agent_generated"]["passed"]
            )
        if scenario == "repeated_state":
            check["passed"] &= result.turns == result.limits.max_repeated_test_states
        checks.append(check)
        print(json.dumps(check), flush=True)
    write_report(states, scenarios_path)
    report = {
        "schema_version": "repofix.feedback-validation.v0.3",
        "created_at": utc_now(),
        "runner": args.runner,
        "execution_image": image,
        "code_sha256": code_fingerprint(),
        "script_sha256": sha256(Path(__file__).read_bytes()),
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
        "run_root": str(store.root),
        "runs_report": str(scenarios_path),
        "notice": "Scripted synthetic regression only; real-model effectiveness is unknown.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
