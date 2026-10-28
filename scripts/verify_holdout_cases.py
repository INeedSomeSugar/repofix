"""Admit prospective synthetic tasks only after real Docker baseline and reference checks."""

import argparse
import json
import uuid
from pathlib import Path

from repofix.cases import all_cases, case_fingerprint
from repofix.config import Settings
from repofix.docker_runner import DockerRunner
from repofix.engine import AgentEngine, create_run
from repofix.evaluation import code_fingerprint, write_report
from repofix.storage import RunStore, sha256, utc_now


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    runs_report = args.out.with_name(args.out.stem + "-runs.json")
    if args.out.exists() or runs_report.exists():
        parser.error("use new report paths")
    probe = DockerRunner().preflight()
    if not probe["available"]:
        parser.error("Docker unavailable; no local fallback")
    root = Path(__file__).resolve().parents[1]
    settings = Settings(data_dir=root / "work/holdout-admission" / uuid.uuid4().hex)
    store = RunStore(settings.data_dir / "runs")
    states, checks = [], []
    cases = [c for c in all_cases(include_holdout=True) if c["id"].startswith("holdout_")]
    for case in cases:
        state = create_run(store, case["id"], runner_kind="docker", runner_image=probe["image_id"])
        directory = store.directory(state.run_id)
        baseline = DockerRunner(probe["image_id"]).run_tests(
            directory / "repository", directory / "independent_tests", directory / "baseline-logs"
        )
        state = AgentEngine(settings, store).run(state.run_id)
        states.append(state)
        item = {
            "case_id": case["id"],
            "case_sha256": case_fingerprint(case),
            "baseline_independent": baseline,
            "reference_run_id": state.run_id,
            "reference_status": state.status,
            "passed": bool(
                not baseline["passed"]
                and baseline.get("tests_run", 0) > 0
                and not baseline.get("reason")
                and baseline.get("cleanup_verified")
                and state.status == "verified"
            ),
        }
        checks.append(item)
        print(
            json.dumps({k: v for k, v in item.items() if k != "baseline_independent"}), flush=True
        )
    write_report(states, runs_report)
    report = {
        "schema_version": "repofix.prospective-admission.v1",
        "created_at": utc_now(),
        "code_sha256": code_fingerprint(),
        "script_sha256": sha256(Path(__file__).read_bytes()),
        "image_id": probe["image_id"],
        "case_sha256": {case["id"]: case_fingerprint(case) for case in cases},
        "checks": checks,
        "passed": bool(checks) and all(item["passed"] for item in checks),
        "model_calls": 0,
        "scope": "Self-authored synthetic prospective tasks, no independent human admission.",
        "run_root": str(store.root),
        "runs_report": str(runs_report),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
