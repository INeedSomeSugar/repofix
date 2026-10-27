from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from .cases import all_cases, public_case
from .config import Settings
from .engine import AgentEngine, create_run, public_state
from .evaluation import write_report
from .providers import DeepSeekProvider, ProviderError
from .schema import Limits
from .storage import RunStore


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="RepoFix execution-feedback coding agent")
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="list trusted fixed development tasks")
    listing.add_argument("--include-upstream", action="store_true")
    sub.add_parser("doctor", help="check DeepSeek model catalog without revealing credentials")
    runner_check = sub.add_parser(
        "runner-check", help="check Docker readiness without pulling images"
    )
    runner_check.add_argument("--image", default="python:3.12-slim")
    serve = sub.add_parser("serve", help="open a loopback-only demo service")
    serve.add_argument("--port", type=int, default=int(os.environ.get("REPOFIX_PORT", "8011")))
    run = sub.add_parser("run")
    run.add_argument("--case", required=True)
    run.add_argument("--provider", choices=["replay", "deepseek"], default="replay")
    run.add_argument("--strategy", choices=["feedback", "single_patch"], default="feedback")
    run.add_argument("--max-turns", type=int, default=12)
    run.add_argument("--pause-after-turns", type=int, default=0)
    run.add_argument("--runner", choices=["local", "docker"], default="local")
    run.add_argument("--image", default="python:3.12-slim")
    resume = sub.add_parser("resume")
    resume.add_argument("run_id")
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--provider", choices=["replay", "deepseek"], default="replay")
    evaluate.add_argument("--cases", nargs="+", default=[case["id"] for case in all_cases()])
    evaluate.add_argument(
        "--strategies", nargs="+", choices=["feedback", "single_patch"], default=["feedback"]
    )
    evaluate.add_argument("--max-turns", type=int, default=12)
    evaluate.add_argument("--out", type=Path)
    experiment = sub.add_parser("experiment", help="freeze and resume repeat development trials")
    experiment.add_argument("action", choices=["create", "run", "status", "export"])
    experiment.add_argument("--id")
    experiment.add_argument("--provider", choices=["replay", "deepseek"], default="deepseek")
    experiment.add_argument("--cases", nargs="+", default=[case["id"] for case in all_cases()])
    experiment.add_argument("--strategies", nargs="+", default=["feedback", "single_patch"])
    experiment.add_argument("--repeats", type=int, default=2)
    experiment.add_argument("--out", type=Path)
    experiment.add_argument("--runner", choices=["local", "docker"], default="local")
    args = parser.parse_args(argv)
    if args.command == "runner-check":
        from .docker_runner import DockerRunner

        result = DockerRunner(args.image).preflight()
        emit(result)
        return 0 if result["available"] else 1
    if args.command == "list":
        emit([public_case(case) for case in all_cases(include_upstream=args.include_upstream)])
        return 0
    settings = Settings.from_env()
    if args.command == "experiment":
        from .experiments import Experiments

        experiments = Experiments(settings)
        if args.action == "create":
            model = "scripted-replay-not-a-model"
            if args.provider == "deepseek":
                provider = DeepSeekProvider(settings)
                try:
                    provider.discover()
                    model = provider.model
                finally:
                    provider.close()
            result = experiments.create(
                args.cases, args.strategies, args.repeats, args.provider, model, args.runner
            )
            emit(
                {
                    "experiment_id": result["experiment_id"],
                    "manifest_sha256": result["manifest_sha256"],
                    "trial_count": len(result["trials"]),
                }
            )
        else:
            if not args.id:
                parser.error("experiment requires --id")
            if args.action == "run":
                result = experiments.run(args.id)
            elif args.action == "export":
                if not args.out:
                    parser.error("experiment export requires --out")
                result = experiments.export(args.id, args.out)
            else:
                result = experiments.summary(args.id)
            emit({key: value for key, value in result.items() if key != "trials"})
        return 0
    if args.command == "doctor":
        provider = None
        try:
            provider = DeepSeekProvider(settings)
            models = provider.discover()
            emit(
                {
                    "provider": "deepseek",
                    "credential_present": True,
                    "catalog_verified": True,
                    "selected_model": provider.model,
                    "available_models": models,
                }
            )
            return 0
        except ProviderError as exc:
            emit({"provider": "deepseek", "error": str(exc)})
            return 1
        finally:
            if provider:
                provider.close()
    if args.command == "serve":
        import uvicorn

        from .api import create_app

        uvicorn.run(create_app(settings), host="127.0.0.1", port=args.port, log_level="warning")
        return 0
    store = RunStore(settings.data_dir / "runs")
    engine = AgentEngine(settings, store)
    if args.command == "run":
        state = create_run(
            store,
            args.case,
            args.provider,
            args.strategy,
            Limits(max_turns=args.max_turns),
            runner_kind=args.runner,
            runner_image=args.image,
        )
        result = engine.run(state.run_id, pause_after_turns=args.pause_after_turns)
        emit(public_state(result))
        return 0 if result.status in {"verified", "paused"} else 1
    if args.command == "resume":
        result = engine.run(args.run_id)
        emit(public_state(result))
        return 0 if result.status == "verified" else 1
    states = []
    for case_id in args.cases:
        for strategy in args.strategies:
            state = create_run(
                store, case_id, args.provider, strategy, Limits(max_turns=args.max_turns)
            )
            state = engine.run(state.run_id)
            states.append(state)
            emit(
                {
                    "run_id": state.run_id,
                    "case_id": case_id,
                    "strategy": strategy,
                    "status": state.status,
                    "error_code": state.error_code,
                }
            )
    destination = args.out or Path("reports") / (
        "evaluation-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".json"
    )
    report = write_report(states, destination)
    emit({"report": str(destination.resolve()), "groups": report["groups"]})
    return 0 if all(state.status == "verified" for state in states) else 1


if __name__ == "__main__":
    raise SystemExit(main())
