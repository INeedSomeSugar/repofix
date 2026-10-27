"""Verify old-code failures and upstream-fixed replay results with actual Docker."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from repofix.cases import all_cases
from repofix.config import Settings
from repofix.docker_runner import DockerRunner
from repofix.engine import AgentEngine, create_run, public_state
from repofix.evaluation import write_report
from repofix.storage import RunStore


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    failures_path = args.out.with_name(args.out.stem + "-baseline-independent.json")
    if args.out.exists() or failures_path.exists():
        raise SystemExit("Refusing to overwrite historical reports")
    root = Path(__file__).resolve().parents[1]
    # No provider credentials are read or used by this replay validation.
    settings = replace(Settings(data_dir=root / "work"), model="")
    store = RunStore(settings.data_dir / "runs")
    engine = AgentEngine(settings, store)
    states, baselines = [], []
    for case in all_cases(include_upstream=True)[5:]:
        state = create_run(store, case["id"], runner_kind="docker")
        directory = store.directory(state.run_id)
        original_grade = DockerRunner().run_tests(
            directory / "repository", directory / "independent_tests", directory / "baseline-audit"
        )
        baseline_detected = (
            not original_grade["passed"]
            and original_grade["tests_run"] > 0
            and original_grade["failures"] + original_grade["errors"] > 0
            and original_grade.get("cleanup_verified") is True
            and original_grade.get("reason") is None
        )
        baselines.append(
            {
                "case_id": case["id"],
                "run_id": state.run_id,
                "defect_detected": baseline_detected,
                "result": original_grade,
            }
        )
        result = engine.run(state.run_id)
        states.append(result)
        print(
            json.dumps(
                {
                    "case_id": case["id"],
                    "status": result.status,
                    "baseline_independent_defect_detected": baseline_detected,
                }
            )
        )
        if not baseline_detected or result.status != "verified":
            break
    write_report(states, args.out)
    failures_path.write_text(json.dumps(baselines, ensure_ascii=False, indent=2), "utf-8")
    passed = len(states) == 3 and all(s.status == "verified" for s in states)
    passed = passed and all(item["defect_detected"] for item in baselines)
    print(json.dumps({"passed": passed, "runs": [public_state(s)["run_id"] for s in states]}))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
