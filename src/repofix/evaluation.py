from __future__ import annotations

import json
from pathlib import Path

from .cases import dataset_type
from .engine import public_state
from .schema import RunState
from .storage import sha256, utc_now


def code_fingerprint() -> str:
    directory = Path(__file__).parent
    manifest = {p.name: sha256(p.read_bytes()) for p in sorted(directory.glob("*.py"))}
    return sha256(json.dumps(manifest, sort_keys=True).encode())


def write_report(states: list[RunState], destination: Path) -> dict:
    if destination.exists() or destination.with_suffix(".md").exists():
        raise ValueError("report already exists; use a new output name")
    groups = []
    combinations = sorted({(s.provider, s.model, s.strategy) for s in states})
    for provider, model, strategy in combinations:
        group = [
            s for s in states if (s.provider, s.model, s.strategy) == (provider, model, strategy)
        ]
        real = provider == "deepseek"
        verified = sum(s.status == "verified" for s in group)
        groups.append(
            {
                "provider": provider,
                "model": model,
                "strategy": strategy,
                "attempted": len(group),
                "verified": verified,
                "errors": sum(s.status == "error" for s in group),
                "budget_exhausted": sum(s.status == "budget_exhausted" for s in group),
                "real_model_repair_rate": verified / len(group) if real and group else None,
                "replay_pipeline_pass_rate": verified / len(group) if not real and group else None,
                "observed_tokens": sum(s.observed_tokens for s in group) if real else None,
                "token_accounting_complete": real
                and all(public_state(s)["token_accounting_complete"] for s in group),
                "elapsed_seconds": round(sum(s.elapsed_seconds for s in group), 3),
            }
        )
    report = {
        "created_at": utc_now(),
        "code_sha256": code_fingerprint(),
        "dataset_type": dataset_type([state.case_id for state in states]),
        "interpretation": "Small development demonstration; not SWE-bench, not an independent "
        "human-reviewed benchmark, and not a production effectiveness claim.",
        "grouping": "Provider, exact model id, and strategy are never pooled.",
        "denominator": "All attempted runs, including provider errors and budget exhaustion.",
        "independence": "Grading assertions are outside the model-visible repository; "
        "they are authored by this project, not an external review panel.",
        "groups": groups,
        "runs": [public_state(s) for s in states],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
    lines = [
        "# RepoFix 开发任务评测",
        "",
        f"生成时间：{report['created_at']}",
        f"代码 SHA-256：{report['code_sha256']}",
        "",
        "任务为本项目自行编写的合成开发样例。独立评分测试不提供给模型，"
        "但不代表外部专家或公开基准验证。小样本仅展示当前执行情况。",
        "",
        "| 供应商 | 模型 | 策略 | 尝试 | 通过 | 错误 | 已知 token |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for group in groups:
        lines.append(
            f"| {group['provider']} | {group['model']} | {group['strategy']} | "
            f"{group['attempted']} | {group['verified']} | {group['errors']} | "
            f"{group['observed_tokens'] if group['observed_tokens'] is not None else 'N/A'} |"
        )
    lines += [
        "",
        "| 任务 | 策略 | 状态 | 模型轮数 | 工具次数 | run_id |",
        "|---|---|---|---:|---:|---|",
    ]
    for state in states:
        lines.append(
            f"| {state.case_id} | {state.strategy} | {state.status} | "
            f"{state.turns} | {state.tool_calls} | {state.run_id} |"
        )
    lines += [
        "",
        "评分要求：原始可见测试失败，源码确实改变，最终可见测试与独立测试全部通过。",
        "token 为接口返回的实际用量，缺失时不估算。回放不产生真实模型修复率。",
        "",
    ]
    with destination.with_suffix(".md").open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return report
