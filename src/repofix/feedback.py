"""Separate frozen tests from model hypotheses; preserve public-tested source snapshots."""

from __future__ import annotations

import json
import re
import time
import uuid

from .storage import atomic_json, sha256
from .workspace import PolicyError, Workspace, content_manifest


def fingerprint(manifest: dict) -> str:
    return sha256(json.dumps(manifest, sort_keys=True).encode())


def save_checkpoint(workspace: Workspace) -> str:
    manifest = {
        path: digest
        for path, digest in content_manifest(workspace.root).items()
        if path.startswith("project/")
    }
    key = fingerprint(manifest)[:32]
    target = workspace.run_dir / "checkpoints" / key
    target.mkdir(parents=True, exist_ok=True)
    for path, digest in manifest.items():
        data = (workspace.root / path).read_bytes()
        if sha256(data) != digest:
            raise PolicyError("source changed while saving checkpoint")
        destination = target / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    atomic_json(target / "manifest.json", manifest)
    return key


def restore_checkpoint(workspace: Workspace, call_id: str, checkpoint_id: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{32}", checkpoint_id):
        raise PolicyError("invalid checkpoint id")
    target = workspace.run_dir / "checkpoints" / checkpoint_id
    manifest = json.loads((target / "manifest.json").read_text("utf-8"))
    expected = {
        path
        for path in content_manifest(workspace.run_dir / "original")
        if path.startswith("project/")
    }
    if set(manifest) != expected or fingerprint(manifest)[:32] != checkpoint_id:
        raise PolicyError("checkpoint manifest mismatch")
    sources = {}
    for path, digest in manifest.items():
        data = (target / path).read_bytes()
        if sha256(data) != digest:
            raise PolicyError("checkpoint source hash mismatch")
        sources[path] = data.decode("utf-8")
    # Validate every byte before touching the working tree. Each file has a resumable intent.
    for path, source in sources.items():
        transaction_id = sha256(json.dumps([call_id, checkpoint_id, path]).encode())
        transaction = workspace.transactions / f"{transaction_id}.json"
        before = sha256(workspace.resolve(path).read_bytes())
        signature = sha256(json.dumps(["restore_checkpoint", checkpoint_id, path]).encode())
        if transaction.exists():
            before = json.loads(transaction.read_text("utf-8"))["before_sha256"]
        workspace._commit(transaction_id, path, source, before, signature)
    return {
        "checkpoint_id": checkpoint_id,
        "restored_sources": sorted(sources),
        "notice": "Source only restored; generated tests are retained and must be rechecked.",
    }


def run_layered_tests(workspace: Workspace, manifest: dict, runner, timeout: float = 12) -> dict:
    workspace.verify_integrity(manifest)
    current = content_manifest(workspace.root)
    test_files = [path for path in current if path.startswith("tests/") and path.endswith(".py")]
    generated = [path for path in test_files if path not in manifest]
    suites = workspace.run_dir / "test-suites" / uuid.uuid4().hex
    for layer in ("trusted", "agent_generated"):
        directory = suites / layer
        directory.mkdir(parents=True)
        for path in test_files:
            # Keep package/helper files in each suite; discovered test modules never mix.
            is_test = path.rsplit("/", 1)[-1].startswith("test_")
            belongs = path in manifest if layer == "trusted" else path in generated
            if is_test and not belongs:
                continue
            destination = directory / path.removeprefix("tests/")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((workspace.root / path).read_bytes())
    started = time.monotonic()
    trusted = runner(
        workspace.root, suites / "trusted", workspace.run_dir / "logs", timeout=timeout
    )
    agent = None
    remaining = timeout - (time.monotonic() - started)
    if generated:
        if remaining > 0 and trusted.get("tests_run") and not trusted.get("reason"):
            agent = runner(
                workspace.root,
                suites / "agent_generated",
                workspace.run_dir / "logs",
                timeout=remaining,
            )
        else:
            agent = {
                "passed": False,
                "tests_run": 0,
                "failures": 0,
                "errors": 1,
                "reason": "generated_suite_not_executed",
                "output": "",
            }
    requires_review = bool(trusted["passed"] and agent is not None and not agent["passed"])
    result = {
        "test_policy": "layered_v1",
        "trusted": trusted,
        "agent_generated": agent,
        "agent_test_files": generated,
        "requires_spec_review": requires_review,
        "workspace_sha256": fingerprint(current),
        "passed": bool(trusted["passed"] and (agent is None or agent["passed"])),
        "reason": trusted.get("reason") or (agent or {}).get("reason"),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "output": "Frozen public tests:\n"
        + trusted.get("output", "")
        + ("\nModel-generated hypotheses:\n" + agent.get("output", "") if agent else ""),
        "notice": "Generated assertions are hypotheses. Check the issue specification before "
        "changing source to satisfy them. Independent grading has not been exposed.",
    }
    for counter in (
        "tests_run",
        "failures",
        "errors",
        "skipped",
        "unexpected_successes",
        "expected_failures",
    ):
        result[counter] = trusted.get(counter, 0) + (agent or {}).get(counter, 0)
    if trusted["passed"]:
        result["checkpoint_id"] = save_checkpoint(workspace)
    return result
