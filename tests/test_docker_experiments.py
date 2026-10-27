from __future__ import annotations

import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from repofix.docker_runner import DockerRunner
from repofix.engine import AgentEngine, create_run
from repofix.experiments import Experiments
from repofix.storage import atomic_json

IMAGE = "sha256:" + "a" * 64
ENDPOINT = "npipe:////./pipe/dockerDesktopLinuxEngine"


def test_docker_command_has_frozen_image_local_endpoint_and_resource_limits(tmp_path):
    command = DockerRunner().command(
        "docker",
        IMAGE,
        "repofix-fixture",
        tmp_path / "repo",
        tmp_path / "tests",
        tmp_path / "out",
        "65534:65534",
        ENDPOINT,
    )
    for flag in (
        "--pull=never",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges=true",
        "--memory=256m",
        "--pids-limit=64",
        "--cpus=1",
    ):
        assert flag in command
    assert command[:3] == ["docker", "--host", ENDPOINT]
    assert IMAGE in command and "python:3.12-slim" not in command
    mounts = [command[index + 1] for index, value in enumerate(command) if value == "--mount"]
    assert len(mounts) == 4 and sum(value.endswith(",readonly") for value in mounts) == 3
    assert "--env" not in command and "--env-file" not in command


@pytest.mark.parametrize(
    "endpoint,uid", [("tcp://other:2375", "65534:65534"), (ENDPOINT, "0:0"), (ENDPOINT, "1:0")]
)
def test_remote_endpoint_and_root_user_are_rejected(tmp_path, endpoint, uid):
    with pytest.raises(ValueError, match="local_endpoint"):
        DockerRunner().command(
            "docker", IMAGE, "fixture", tmp_path, tmp_path, tmp_path, uid, endpoint
        )


def test_absent_docker_cannot_silently_execute_locally(tmp_path, monkeypatch, store, settings):
    monkeypatch.setattr("repofix.docker_runner.docker_executable", lambda: None)
    result = DockerRunner().run_tests(tmp_path, tmp_path, tmp_path / "logs")
    assert not result["passed"] and result["reason"] == "docker_cli_missing"
    state = create_run(store, "csv_records", "replay", runner_kind="docker")
    final = AgentEngine(settings, store).run(state.run_id)
    assert final.status == "error" and final.error_code == "docker_cli_missing"
    assert final.turns == 0 and not final.messages and not final.usage


def test_preflight_freezes_actual_linux_image_id(monkeypatch):
    monkeypatch.delenv("DOCKER_HOST", raising=False)
    monkeypatch.setattr("repofix.docker_runner.docker_executable", lambda: "docker")
    seen = []

    def run(command, **kwargs):
        seen.append(command)
        if "context" in command:
            return SimpleNamespace(returncode=0, stdout=json.dumps(ENDPOINT))
        if "info" in command:
            return SimpleNamespace(returncode=0, stdout='"linux"')
        return SimpleNamespace(returncode=0, stdout=json.dumps({"Os": "linux", "Id": IMAGE}))

    monkeypatch.setattr("repofix.docker_runner.subprocess.run", run)
    result = DockerRunner().preflight()
    assert result["available"] and result["image_id"] == IMAGE
    assert not result["runtime_verified"]
    assert all("--host" in command for command in seen[1:])


def test_remote_context_is_rejected_before_contacting_daemon(monkeypatch):
    monkeypatch.setenv("DOCKER_HOST", "ssh://remote.example")
    monkeypatch.setattr("repofix.docker_runner.docker_executable", lambda: "docker")
    monkeypatch.setattr(
        "repofix.docker_runner.subprocess.run", lambda *a, **k: pytest.fail("contacted daemon")
    )
    assert DockerRunner().preflight()["reason"] == "remote_docker_context_not_supported"


@pytest.mark.parametrize(
    "inspect_error,passed",
    [
        (b"Error: No such object: fixture", True),
        (b"error: no such object: fixture", True),
        (b"Error response from daemon: No such container: fixture", True),
        (b"Cannot connect to Docker daemon", False),
    ],
)
def test_cleanup_connection_error_is_not_proof_of_container_removal(
    tmp_path, monkeypatch, inspect_error, passed
):
    runner = DockerRunner()
    monkeypatch.setattr(
        runner,
        "preflight",
        lambda: {
            "available": True,
            "reason": None,
            "executable": "docker",
            "image_id": IMAGE,
            "endpoint": ENDPOINT,
        },
    )

    def popen(command, **kwargs):
        mount = next(
            command[i + 1]
            for i, value in enumerate(command)
            if value == "--mount" and "dst=/results" in command[i + 1]
        )
        from pathlib import Path

        directory = Path(mount.split("src=", 1)[1].split(",dst=", 1)[0])
        (directory / "result.json").write_text(
            json.dumps(
                {
                    "passed": True,
                    "tests_run": 1,
                    "failures": 0,
                    "errors": 0,
                    "skipped": 0,
                    "expected_failures": 0,
                    "unexpected_successes": 0,
                }
            ),
            encoding="utf-8",
        )
        return SimpleNamespace(poll=lambda: 0, returncode=0)

    monkeypatch.setattr("repofix.docker_runner.subprocess.Popen", popen)
    monkeypatch.setattr(
        "repofix.docker_runner.subprocess.run",
        lambda *a, **k: SimpleNamespace(returncode=1, stderr=inspect_error),
    )
    result = runner.run_tests(tmp_path, tmp_path, tmp_path / "logs")
    assert result["passed"] is passed
    assert result["cleanup_verified"] is passed


def test_repeat_experiment_resume_keeps_run_ids_and_never_counts_replay_as_model(
    settings, tmp_path
):
    experiments = Experiments(settings)
    plan = experiments.create(
        ["csv_records"], ["feedback", "single_patch"], 2, "replay", "scripted-replay-not-a-model"
    )
    key = plan["experiment_id"]
    report = experiments.run(key)
    assert report["trial_count"] == 4
    assert report["paired_outcomes"] == {"both_verified": 2}
    ids = [trial["run_id"] for trial in report["trials"]]
    again = experiments.run(key)
    assert ids == [trial["run_id"] for trial in again["trials"]]
    assert all(group["real_model_repair_rate"] is None for group in report["groups"])
    assert all(group["total_tokens"] is None for group in report["groups"])
    output = tmp_path / "repeated.json"
    experiments.export(key, output)
    assert output.with_suffix(".md").exists()
    with pytest.raises(ValueError):
        experiments.export(key, output)


def test_manifest_and_trial_order_changes_are_rejected(settings):
    experiments = Experiments(settings)
    plan = experiments.create(
        ["csv_records"], ["feedback", "single_patch"], 2, "replay", "scripted-replay-not-a-model"
    )
    key = plan["experiment_id"]
    plan["trials"].reverse()
    atomic_json(experiments.path(key), plan)
    with pytest.raises(ValueError, match="trial_grid"):
        experiments.load(key)


def test_changed_code_prevents_resuming_frozen_experiment(settings, monkeypatch):
    experiments = Experiments(settings)
    plan = experiments.create(["csv_records"], ["feedback"], 1, "replay", "fixture")
    monkeypatch.setattr("repofix.experiments.code_fingerprint", lambda: "changed")
    with pytest.raises(ValueError, match="code_changed"):
        experiments.run(plan["experiment_id"])


def test_provider_errors_stay_in_repeat_denominator_and_unknown_usage_stays_null(
    settings, monkeypatch
):
    experiments = Experiments(replace(settings, api_key="fixture"))
    plan = experiments.create(["csv_records"], ["feedback"], 2, "deepseek", "fixture")

    def fail(engine, run_id):
        state = engine.store.load(run_id)
        state.status, state.model, state.error_code = "error", "fixture", "fixture_provider_error"
        engine.store.save(state)
        return state

    monkeypatch.setattr(AgentEngine, "run", fail)
    report = experiments.run(plan["experiment_id"])
    group = report["groups"][0]
    assert group["attempted"] == 2 and group["verified"] == 0
    assert group["real_model_repair_rate"] == 0
    assert group["total_tokens"] is None and not group["token_accounting_complete"]
