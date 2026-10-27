"""Frozen, counterbalanced repeat trials over the trusted built-in development tasks."""

from __future__ import annotations

import json
import math
import uuid
from collections import Counter
from dataclasses import replace
from pathlib import Path
from statistics import median

from .cases import case_fingerprint, get_case
from .config import Settings
from .engine import AgentEngine, create_run, public_state
from .evaluation import code_fingerprint
from .schema import Limits
from .storage import RunStore, atomic_json, sha256, utc_now


def fingerprint(value) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode())


def distribution(values: list[float]) -> dict:
    ordered = sorted(values)
    return {
        "count": len(values),
        "min": min(values) if values else None,
        "median": median(values) if values else None,
        "p95": ordered[math.ceil(0.95 * len(values)) - 1] if values else None,
        "max": max(values) if values else None,
    }


class Experiments:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.plans = RunStore(settings.data_dir / "experiments")
        self.runs = RunStore(settings.data_dir / "runs")

    def path(self, key: str) -> Path:
        return self.plans.directory(key) / "experiment.json"

    def create(
        self,
        case_ids: list[str],
        strategies: list[str],
        repeats: int,
        provider: str,
        model: str,
        runner_kind: str = "local",
    ) -> dict:
        if (
            not case_ids
            or len(set(case_ids)) != len(case_ids)
            or len(set(strategies)) != len(strategies)
            or not strategies
            or set(strategies) - {"feedback", "single_patch"}
            or not 1 <= repeats <= 5
            or provider not in {"deepseek", "replay"}
            or not model
            or runner_kind not in {"local", "docker"}
        ):
            raise ValueError("invalid_experiment_configuration")
        cases = {key: case_fingerprint(get_case(key)) for key in case_ids}
        key = uuid.uuid4().hex
        self.plans.directory(key).mkdir()
        manifest = {
            "provider": provider,
            "requested_model": model,
            "case_sha256": cases,
            "case_order": case_ids,
            "strategies": strategies,
            "repeats": repeats,
            "limits": Limits().model_dump(),
            "runner_kind": runner_kind,
            "code_sha256": code_fingerprint(),
            "dataset_type": "original_synthetic_development_exercises",
            "order": "strategy_order_reversed_by_case_and_repeat_parity",
        }
        trials = []
        for repeat in range(1, repeats + 1):
            for case_index, case_id in enumerate(case_ids):
                order = strategies if (case_index + repeat) % 2 else list(reversed(strategies))
                for strategy in order:
                    trials.append(
                        {"case_id": case_id, "repeat": repeat, "strategy": strategy, "run_id": None}
                    )
        experiment = {
            "experiment_id": key,
            "created_at": utc_now(),
            "manifest": manifest,
            "manifest_sha256": fingerprint(manifest),
            "trials": trials,
        }
        atomic_json(self.path(key), experiment)
        return experiment

    def load(self, key: str, *, check_code: bool = True) -> dict:
        experiment = json.loads(self.path(key).read_text("utf-8"))
        manifest = experiment["manifest"]
        if fingerprint(manifest) != experiment["manifest_sha256"]:
            raise ValueError("experiment_manifest_changed")
        if check_code and code_fingerprint() != manifest["code_sha256"]:
            raise ValueError("code_changed_since_experiment_freeze_create_a_new_experiment")
        if any(
            case_fingerprint(get_case(case_id)) != expected
            for case_id, expected in manifest["case_sha256"].items()
        ):
            raise ValueError("fixture_changed_since_experiment_freeze")
        expected = []
        for repeat in range(1, manifest["repeats"] + 1):
            for index, case_id in enumerate(manifest["case_order"]):
                order = (
                    manifest["strategies"]
                    if (index + repeat) % 2
                    else list(reversed(manifest["strategies"]))
                )
                expected.extend((case_id, repeat, strategy) for strategy in order)
        actual = [
            (trial["case_id"], trial["repeat"], trial["strategy"]) for trial in experiment["trials"]
        ]
        if actual != expected:
            raise ValueError("trial_grid_changed")
        run_ids = [trial["run_id"] for trial in experiment["trials"] if trial["run_id"]]
        if len(run_ids) != len(set(run_ids)):
            raise ValueError("duplicate_run_in_repeat_trials")
        return experiment

    def run(self, key: str) -> dict:
        with self.plans.lock(key):
            experiment = self.load(key)
            manifest = experiment["manifest"]
            settings = replace(self.settings, model=manifest["requested_model"])
            engine = AgentEngine(settings, self.runs)
            for trial in experiment["trials"]:
                self.load(key)
                if trial["run_id"]:
                    state = self.runs.load(trial["run_id"])
                    if state.status not in {"created", "running", "paused"}:
                        continue  # Errors stay in the denominator; never silently retry.
                else:
                    state = create_run(
                        self.runs,
                        trial["case_id"],
                        manifest["provider"],
                        trial["strategy"],
                        Limits(**manifest["limits"]),
                        runner_kind=manifest["runner_kind"],
                    )
                    trial["run_id"] = state.run_id
                    state.experiment_id = key
                    state.repeat_index = trial["repeat"]
                    self.runs.save(state)
                    atomic_json(self.path(key), experiment)
                result = engine.run(state.run_id)
                print(
                    json.dumps(
                        {
                            "repeat": trial["repeat"],
                            "case_id": trial["case_id"],
                            "strategy": trial["strategy"],
                            "status": result.status,
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
            return self.summary(key)

    def summary(self, key: str) -> dict:
        experiment = self.load(key, check_code=False)
        manifest = experiment["manifest"]
        trials = []
        for trial in experiment["trials"]:
            state = self.runs.load(trial["run_id"]) if trial["run_id"] else None
            if state and (
                state.case_id != trial["case_id"]
                or state.strategy != trial["strategy"]
                or state.provider != manifest["provider"]
                or state.case_sha256 != manifest["case_sha256"][trial["case_id"]]
                or state.runner_kind != manifest["runner_kind"]
                or state.experiment_id != key
                or state.repeat_index != trial["repeat"]
                or state.model not in {"", manifest["requested_model"]}
            ):
                raise ValueError("trial_run_binding_mismatch")
            trials.append({**trial, "result": public_state(state) if state else None})
        groups = []
        for strategy in manifest["strategies"]:
            states = [
                trial["result"]
                for trial in trials
                if trial["strategy"] == strategy and trial["result"]
            ]
            real = manifest["provider"] == "deepseek"
            verified = sum(state["status"] == "verified" for state in states)
            complete = (
                real
                and bool(states)
                and all(state["token_accounting_complete"] for state in states)
            )
            observed = sum(state["observed_tokens"] for state in states)
            groups.append(
                {
                    "strategy": strategy,
                    "attempted": len(states),
                    "verified": verified,
                    "status_counts": dict(Counter(state["status"] for state in states)),
                    "real_model_repair_rate": verified / len(states) if real and states else None,
                    "replay_pipeline_pass_rate": verified / len(states)
                    if not real and states
                    else None,
                    "observed_tokens": observed if real else None,
                    "total_tokens": observed if complete else None,
                    "token_accounting_complete": complete,
                    "tokens_per_verified_run": observed / verified
                    if complete and verified
                    else None,
                    "elapsed_seconds": distribution([state["elapsed_seconds"] for state in states]),
                    "tokens": distribution([state["observed_tokens"] for state in states])
                    if complete
                    else {"count": 0, "median": None, "p95": None},
                }
            )
        paired = Counter()
        by_case = []
        if set(manifest["strategies"]) == {"feedback", "single_patch"}:
            for case_id in manifest["case_sha256"]:
                counts = Counter()
                for repeat in range(1, manifest["repeats"] + 1):
                    pair = {
                        trial["strategy"]: trial["result"]
                        for trial in trials
                        if trial["case_id"] == case_id and trial["repeat"] == repeat
                    }
                    if len(pair) != 2 or any(
                        value is None or value["status"] in {"created", "running", "paused"}
                        for value in pair.values()
                    ):
                        counts["not_completed"] += 1
                        continue
                    a, b = (
                        pair[name]["status"] == "verified" for name in ("feedback", "single_patch")
                    )
                    outcome = (
                        "both_verified"
                        if a and b
                        else "feedback_only"
                        if a
                        else ("single_patch_only" if b else "neither_verified")
                    )
                    counts[outcome] += 1
                paired.update(counts)
                by_case.append({"case_id": case_id, "pairs": dict(counts)})
        return {
            "schema_version": "repofix.experiment.v0.2",
            "experiment_id": key,
            "manifest": manifest,
            "manifest_sha256": experiment["manifest_sha256"],
            "trial_count": len(trials),
            "groups": groups,
            "paired_outcomes": dict(paired),
            "per_case": by_case,
            "trials": trials,
            "interpretation": (
                "Repeated trusted synthetic development trials only; not external benchmark "
                "or general repair accuracy. Identical caps do not imply equal actual compute."
            ),
        }

    def export(self, key: str, output: Path) -> dict:
        if output.suffix != ".json" or output.exists() or output.with_suffix(".md").exists():
            raise ValueError("use_a_new_json_output_path")
        report = self.summary(key)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        lines = [
            "# RepoFix 重复开发试验",
            "",
            report["interpretation"],
            "",
            f"协议SHA256：{report['manifest_sha256']}",
            f"模型：{report['manifest']['requested_model']}；每任务重复：{report['manifest']['repeats']}",
            "",
            "| 策略 | 尝试 | 通过 | 已知token | 完整token统计 | 耗时中位数/秒 |",
            "|---|---:|---:|---:|---|---:|",
        ]
        for group in report["groups"]:
            lines.append(
                f"| {group['strategy']} | {group['attempted']} | {group['verified']} | "
                f"{group['observed_tokens']} | {group['token_accounting_complete']} | "
                f"{group['elapsed_seconds']['median']} |"
            )
        lines.extend(["", "## 全部逐任务配对结果", ""])
        lines.extend(
            f"- {row['case_id']}: {json.dumps(row['pairs'], ensure_ascii=False)}"
            for row in report["per_case"]
        )
        lines.extend(["", "## 原始运行", ""])
        lines.extend(
            f"- {trial['case_id']} / repeat={trial['repeat']} / {trial['strategy']}: "
            f"{trial['result']['status'] if trial['result'] else 'not_started'} / {trial['run_id']}"
            for trial in report["trials"]
        )
        output.with_suffix(".md").write_text("\n".join(lines) + "\n", "utf-8")
        return report
