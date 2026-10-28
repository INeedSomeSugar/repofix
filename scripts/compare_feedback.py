"""Freeze, resume and export a three-arm Docker comparison; never retry failed trials silently."""

from __future__ import annotations

import argparse
import json
import uuid
import zipfile
from collections import Counter
from dataclasses import replace
from pathlib import Path

from repofix.cases import case_fingerprint, get_case
from repofix.config import Settings
from repofix.docker_runner import DockerRunner
from repofix.engine import AgentEngine, create_run, public_state
from repofix.evaluation import code_fingerprint, write_report
from repofix.experiments import distribution, fingerprint
from repofix.providers import DeepSeekProvider
from repofix.schema import Limits
from repofix.storage import RunStore, atomic_json, sha256, utc_now

ARMS = [
    {"name": "single_patch", "strategy": "single_patch", "feedback_policy": "legacy_all"},
    {"name": "legacy_feedback", "strategy": "feedback", "feedback_policy": "legacy_all"},
    {"name": "layered_feedback", "strategy": "feedback", "feedback_policy": "layered_v1"},
]
SCRIPT = Path(__file__).resolve()


class AuditedDeepSeekProvider(DeepSeekProvider):
    def __init__(self, settings, metadata_path, transport=None):
        super().__init__(settings, transport=transport)
        self.metadata_path = metadata_path

    def _request(self, method, route, body=None):
        reply = super()._request(method, route, body)
        if route == "chat/completions":
            usage = reply.get("usage") or {}
            metadata = {
                "at": utc_now(),
                "requested_model": self.model,
                "response_model": reply.get("model")
                if isinstance(reply.get("model"), str)
                else None,
                "response_id": reply.get("id") if isinstance(reply.get("id"), str) else None,
                "usage": {
                    key: usage.get(key) if isinstance(usage.get(key), int) else None
                    for key in ("prompt_tokens", "completion_tokens", "total_tokens")
                },
            }
            with self.metadata_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(metadata, ensure_ascii=False) + "\n")
        return reply


def trial_grid(cases, repeats):
    trials = []
    for repeat in range(1, repeats + 1):
        for index, case in enumerate(cases):
            shift = (index + repeat - 1) % len(ARMS)
            order = ARMS[shift:] + ARMS[:shift]
            if repeat % 2 == 0:
                order = list(reversed(order))
            trials.extend(
                {"case_id": case, "repeat": repeat, "arm": arm["name"], "run_id": None}
                for arm in order
            )
    return trials


class Comparison:
    def __init__(self, settings):
        self.settings = settings
        self.plans = RunStore(settings.data_dir / "feedback-comparisons")

    def path(self, key):
        return self.plans.directory(key) / "plan.json"

    def freeze(self, admission_path, repeats=2, provider="deepseek", model=""):
        admission = json.loads(admission_path.read_text("utf-8"))
        if not 1 <= repeats <= 3 or provider not in {"deepseek", "replay"} or not model:
            raise ValueError("invalid_comparison_configuration")
        if not admission["passed"] or admission["code_sha256"] != code_fingerprint():
            raise ValueError("successful_current_code_admission_required")
        cases = list(admission["case_sha256"])
        if not cases or any(
            get_case(case)["difficulty"] != "prospective_holdout_v1"
            or case_fingerprint(get_case(case)) != digest
            for case, digest in admission["case_sha256"].items()
        ):
            raise ValueError("prospective_fixture_mismatch")
        probe = DockerRunner().preflight()
        if not probe["available"] or probe["image_id"] != admission["image_id"]:
            raise ValueError("admitted_local_docker_image_required")
        manifest = {
            "provider": provider,
            "model": model,
            "cases": cases,
            "case_sha256": admission["case_sha256"],
            "arms": ARMS,
            "repeats": repeats,
            "limits": Limits().model_dump(),
            "runner_image_id": probe["image_id"],
            "code_sha256": code_fingerprint(),
            "script_sha256": sha256(SCRIPT.read_bytes()),
            "admission_sha256": sha256(admission_path.read_bytes()),
            "dataset": "prospective_synthetic_holdout_v1",
            "order": "rotate_by_case_and_repeat_then_reverse_even_repeats",
            "interpretation": "First evaluation after freeze; self-authored, not human-reviewed; "
            "pretraining contamination unknown. After exposure these tasks cannot be reused "
            "as untouched holdout for later changes.",
            "treatment": "Layered prompt, test execution, checkpoint tool and repeat guard jointly "
            "change; no causal attribution to test labels alone.",
        }
        key = uuid.uuid4().hex
        directory = self.plans.directory(key)
        directory.mkdir()
        plan = {
            "schema_version": "repofix.feedback-comparison.v1",
            "comparison_id": key,
            "created_at": utc_now(),
            "manifest": manifest,
            "manifest_sha256": fingerprint(manifest),
            "trials": trial_grid(cases, repeats),
        }
        atomic_json(self.path(key), plan)
        (directory / "admission.json").write_bytes(admission_path.read_bytes())
        sources = Path(__file__).resolve().parents[1] / "src/repofix"
        with zipfile.ZipFile(directory / "source.zip", "x", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(sources.rglob("*")):
                if (
                    path.is_file()
                    and path.suffix in {".py", ".json"}
                    and "__pycache__" not in str(path)
                ):
                    archive.writestr(
                        "src/repofix/" + path.relative_to(sources).as_posix(), path.read_bytes()
                    )
            archive.writestr("scripts/compare_feedback.py", SCRIPT.read_bytes())
        return plan

    def load(self, key, check_code=True):
        plan = json.loads(self.path(key).read_text("utf-8"))
        manifest = plan["manifest"]
        if fingerprint(manifest) != plan["manifest_sha256"]:
            raise ValueError("comparison_manifest_changed")
        if manifest["arms"] != ARMS:
            raise ValueError("comparison_arms_changed")
        if check_code and (
            code_fingerprint() != manifest["code_sha256"]
            or sha256(SCRIPT.read_bytes()) != manifest["script_sha256"]
        ):
            raise ValueError("comparison_code_changed")
        if any(
            case_fingerprint(get_case(case)) != digest
            for case, digest in manifest["case_sha256"].items()
        ):
            raise ValueError("comparison_fixture_changed")
        if (
            sha256(self.path(key).with_name("admission.json").read_bytes())
            != manifest["admission_sha256"]
        ):
            raise ValueError("comparison_admission_changed")
        expected = trial_grid(manifest["cases"], manifest["repeats"])
        if [tuple(t[k] for k in ("case_id", "repeat", "arm")) for t in plan["trials"]] != [
            tuple(t[k] for k in ("case_id", "repeat", "arm")) for t in expected
        ]:
            raise ValueError("comparison_trial_grid_changed")
        ids = [t["run_id"] for t in plan["trials"] if t["run_id"]]
        if len(ids) != len(set(ids)):
            raise ValueError("comparison_duplicate_run")
        return plan

    def store(self, key):
        return RunStore(self.plans.directory(key) / "runs")

    @staticmethod
    def validate_state(state, trial, manifest, key):
        arm = next(arm for arm in ARMS if arm["name"] == trial["arm"])
        if (
            state.case_id != trial["case_id"]
            or state.strategy != arm["strategy"]
            or state.feedback_policy != arm["feedback_policy"]
            or state.provider != manifest["provider"]
            or state.model not in {"", manifest["model"]}
            or state.case_sha256 != manifest["case_sha256"][trial["case_id"]]
            or state.runner_kind != "docker"
            or state.runner_image != manifest["runner_image_id"]
            or state.execution_image_id not in {None, manifest["runner_image_id"]}
            or state.experiment_id != key
            or state.repeat_index != trial["repeat"]
            or state.limits.model_dump() != manifest["limits"]
        ):
            raise ValueError("comparison_trial_run_binding_mismatch")

    def run(self, key, stop_after=None):
        with self.plans.lock(key):
            plan = self.load(key)
            manifest = plan["manifest"]
            store = self.store(key)
            settings = replace(self.settings, model=manifest["model"])
            completed_now = 0
            for trial in plan["trials"]:
                self.load(key)
                if trial["run_id"]:
                    state = store.load(trial["run_id"])
                    self.validate_state(state, trial, manifest, key)
                    if state.status not in {"created", "queued", "running", "paused"}:
                        continue
                else:
                    arm = next(a for a in ARMS if a["name"] == trial["arm"])
                    state = create_run(
                        store,
                        trial["case_id"],
                        manifest["provider"],
                        arm["strategy"],
                        Limits(**manifest["limits"]),
                        runner_kind="docker",
                        runner_image=manifest["runner_image_id"],
                        feedback_policy=arm["feedback_policy"],
                    )
                    state.experiment_id, state.repeat_index = key, trial["repeat"]
                    store.save(state)
                    trial["run_id"] = state.run_id
                    atomic_json(self.path(key), plan)
                if manifest["provider"] == "deepseek":
                    provider = AuditedDeepSeekProvider(
                        settings, store.directory(state.run_id) / "provider-metadata.jsonl"
                    )
                    try:
                        state = AgentEngine(settings, store).run(state.run_id, provider)
                    finally:
                        provider.close()
                else:
                    state = AgentEngine(settings, store).run(state.run_id)
                print(
                    json.dumps(
                        {**trial, "status": state.status, "observed_tokens": state.observed_tokens},
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
                completed_now += 1
                if stop_after and completed_now >= stop_after:
                    break
            return self.summary(key)

    def summary(self, key):
        plan = self.load(key, check_code=False)
        manifest, store = plan["manifest"], self.store(key)
        trials = []
        for trial in plan["trials"]:
            state = store.load(trial["run_id"]) if trial["run_id"] else None
            if state:
                self.validate_state(state, trial, manifest, key)
            trials.append({**trial, "result": public_state(state) if state else None})
        groups = []
        for arm in ARMS:
            states = [t["result"] for t in trials if t["arm"] == arm["name"] and t["result"]]
            model_metadata = []
            for trial in trials:
                if trial["arm"] == arm["name"] and trial["run_id"]:
                    path = store.directory(trial["run_id"]) / "provider-metadata.jsonl"
                    if path.exists():
                        model_metadata.extend(
                            json.loads(line) for line in path.read_text("utf-8").splitlines()
                        )
            real = manifest["provider"] == "deepseek"
            complete_usage = bool(states) and all(s["token_accounting_complete"] for s in states)
            finished = all(
                s["status"] not in {"created", "queued", "running", "paused"} for s in states
            )
            planned = len(manifest["cases"]) * manifest["repeats"]
            groups.append(
                {
                    **arm,
                    "planned": planned,
                    "attempted": len(states),
                    "finished": finished and len(states) == planned,
                    "verified": sum(s["status"] == "verified" for s in states),
                    "statuses": dict(Counter(s["status"] for s in states)),
                    "observed_tokens": sum(s["observed_tokens"] for s in states) if real else None,
                    "total_tokens": sum(s["observed_tokens"] for s in states)
                    if real and complete_usage
                    else None,
                    "token_accounting_complete": real and complete_usage,
                    "elapsed_seconds": distribution([s["elapsed_seconds"] for s in states]),
                    "model_calls": sum(s["turns"] for s in states) if real else 0,
                    "response_models": dict(
                        Counter(row["response_model"] for row in model_metadata)
                    ),
                    "response_model_accounting_complete": real
                    and bool(model_metadata)
                    and len(model_metadata) == sum(s["turns"] for s in states)
                    and all(row["response_model"] for row in model_metadata),
                }
            )
        paired = []
        for repeat in range(1, manifest["repeats"] + 1):
            for case in manifest["cases"]:
                rows = {
                    t["arm"]: t["result"]
                    for t in trials
                    if t["case_id"] == case and t["repeat"] == repeat
                }
                paired.append(
                    {
                        "case_id": case,
                        "repeat": repeat,
                        "outcomes": {
                            arm: result["status"] if result else None
                            for arm, result in rows.items()
                        },
                    }
                )
        return {
            "schema_version": plan["schema_version"],
            "comparison_id": key,
            "created_at": plan["created_at"],
            "manifest": manifest,
            "manifest_sha256": plan["manifest_sha256"],
            "complete": all(group["finished"] for group in groups),
            "groups": groups,
            "paired_outcomes": paired,
            "trials": trials,
            "run_root": str(store.root),
        }

    def export(self, key, output):
        report = self.summary(key)
        raw = output.with_name(output.stem + "-runs.json")
        paths = [
            output,
            output.with_suffix(".md"),
            raw,
            raw.with_suffix(".md"),
            output.with_name(output.stem + "-plan.json"),
        ]
        if any(path.exists() for path in paths):
            raise ValueError("comparison_report_exists_choose_new_path")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
        plan_path = output.with_name(output.stem + "-plan.json")
        plan_path.write_bytes(self.path(key).read_bytes())
        states = [self.store(key).load(t["run_id"]) for t in report["trials"] if t["run_id"]]
        write_report(states, raw)
        lines = [
            "# RepoFix 冻结合成任务三组对照",
            "",
            f"协议：{key}",
            f"完整执行：{report['complete']}",
            "",
            "| 组别 | 已尝试/计划 | verified | 实际token | 耗时中位数(秒) |",
            "| --- | --- | --- | --- | --- |",
        ]
        for group in report["groups"]:
            lines.append(
                f"| {group['name']} | {group['attempted']}/{group['planned']} | "
                f"{group['verified']} | {group['total_tokens']} | "
                f"{group['elapsed_seconds']['median']} |"
            )
        lines += [
            "",
            "自编合成任务，首次模型运行前冻结；未经过独立人工审核，预训练污染未知。",
            "全部尝试包括错误与预算耗尽；相同任务的重复运行不是独立新任务。",
            "新协议同时改变提示、分层执行、检查点工具及停止策略，不能归因到单一机制。",
            "原始消息与逐次用量留在运行目录；旧开发实验不合并统计。",
            "",
        ]
        output.with_suffix(".md").write_text("\n".join(lines), "utf-8")
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["create", "run", "status", "export"])
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--provider", choices=["deepseek", "replay"], default="deepseek")
    parser.add_argument("--id")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    settings = Settings.from_env()
    comparison = Comparison(settings)
    if args.action == "create":
        if not args.admission:
            parser.error("create requires --admission")
        model = "scripted-replay-not-a-model"
        if args.provider == "deepseek":
            provider = DeepSeekProvider(settings)
            try:
                provider.discover()
                model = provider.model
            finally:
                provider.close()
        plan = comparison.freeze(args.admission, args.repeats, args.provider, model)
        print(
            json.dumps(
                {
                    "comparison_id": plan["comparison_id"],
                    "trials": len(plan["trials"]),
                    "manifest_sha256": plan["manifest_sha256"],
                }
            )
        )
        return
    if not args.id:
        parser.error("action requires --id")
    if args.action == "run":
        report = comparison.run(args.id)
    elif args.action == "export":
        if not args.out:
            parser.error("export requires --out")
        report = comparison.export(args.id, args.out)
    else:
        report = comparison.summary(args.id)
    print(
        json.dumps(
            {k: v for k, v in report.items() if k not in {"trials", "manifest", "paired_outcomes"}},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
