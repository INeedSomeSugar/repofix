"""Opt-in Docker execution for built-in fixtures; no automatic local fallback or pulls."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from .runner import child_environment, terminate_tree


def docker_executable() -> str | None:
    found = shutil.which("docker")
    if found:
        return found
    candidates = [
        Path(os.getenv("LOCALAPPDATA", "")) / "Programs/DockerDesktop/resources/bin/docker.exe",
        Path(os.getenv("ProgramFiles", r"C:\Program Files"))
        / "Docker/Docker/resources/bin/docker.exe",
    ]
    return next((str(path) for path in candidates if path.is_file()), None)


class DockerRunner:
    def __init__(self, image: str = "python:3.12-slim"):
        if not image or image.startswith("-") or not re.fullmatch(r"[A-Za-z0-9_./:@-]+", image):
            raise ValueError("invalid_docker_image_reference")
        self.image = image

    def preflight(self) -> dict:
        executable = docker_executable()
        result = {"available": False, "image": self.image, "runtime_verified": False}
        if not executable:
            return {**result, "reason": "docker_cli_missing"}
        try:
            endpoint = os.getenv("DOCKER_HOST", "")
            if not endpoint:
                context = subprocess.run(
                    [
                        executable,
                        "context",
                        "inspect",
                        "--format",
                        "{{json .Endpoints.docker.Host}}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=8,
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if context.returncode:
                    return {**result, "reason": "docker_context_unavailable"}
                endpoint = json.loads(context.stdout)
            if not isinstance(endpoint, str) or not endpoint.startswith(("npipe://", "unix://")):
                return {**result, "reason": "remote_docker_context_not_supported"}
            probe = subprocess.run(
                [executable, "--host", endpoint, "info", "--format", "{{json .OSType}}"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if probe.returncode:
                return {**result, "reason": "docker_daemon_unavailable"}
            if json.loads(probe.stdout) != "linux":
                return {**result, "reason": "linux_container_engine_required"}
            inspect = subprocess.run(
                [
                    executable,
                    "--host",
                    endpoint,
                    "image",
                    "inspect",
                    "--format",
                    "{{json .}}",
                    self.image,
                ],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if inspect.returncode:
                return {**result, "reason": "docker_image_not_present_pull_explicitly"}
            image = json.loads(inspect.stdout)
            if image.get("Os") != "linux" or not re.fullmatch(
                r"sha256:[a-f0-9]{64}", image.get("Id", "")
            ):
                return {**result, "reason": "invalid_linux_image_identity"}
            return {
                **result,
                "available": True,
                "reason": None,
                "executable": executable,
                "image_id": image["Id"],
                "endpoint": endpoint,
            }
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return {**result, "reason": "docker_preflight_failed"}

    def command(
        self,
        executable: str,
        image_id: str,
        name: str,
        repository: Path,
        tests: Path,
        output: Path,
        uid: str,
        endpoint: str,
    ) -> list[str]:
        harness = Path(__file__).with_name("harness.py").resolve()
        paths = [repository.resolve(), tests.resolve(), output.resolve(), harness]
        if any("," in str(path) or "\n" in str(path) for path in paths):
            raise ValueError("unsupported_mount_path")
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", image_id):
            raise ValueError("resolved_image_id_required")
        if not endpoint.startswith(("npipe://", "unix://")) or not re.fullmatch(
            r"[1-9][0-9]*:[1-9][0-9]*", uid
        ):
            raise ValueError("local_endpoint_and_non_root_user_required")
        command = [
            executable,
            "--host",
            endpoint,
            "run",
            "--rm",
            "--pull=never",
            "--name",
            name,
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges=true",
            "--pids-limit=64",
            "--memory=256m",
            "--memory-swap=256m",
            "--cpus=1",
            "--user",
            uid,
            "--tmpfs=/tmp:rw,noexec,nosuid,size=32m",
            "--workdir=/repository",
            "--entrypoint=python",
        ]
        for source, target, readonly in (
            (paths[0], "/repository", True),
            (paths[1], "/tests", True),
            (harness, "/harness.py", True),
            (paths[2], "/results", False),
        ):
            command.extend(
                [
                    "--mount",
                    f"type=bind,src={source},dst={target}" + (",readonly" if readonly else ""),
                ]
            )
        return [
            *command,
            image_id,
            "-I",
            "-S",
            "-B",
            "-X",
            "utf8",
            "/harness.py",
            "/repository",
            "/tests",
            "/results/result.json",
        ]

    def run_tests(self, repository: Path, tests: Path, log_dir: Path, timeout: float = 12) -> dict:
        probe = self.preflight()
        failure = {
            "passed": False,
            "tests_run": 0,
            "failures": 0,
            "errors": 1,
            "output": "",
            "elapsed_seconds": 0.0,
            "isolation": "docker_not_verified",
            "reason": probe["reason"],
        }
        if not probe["available"]:
            return failure
        if os.name != "nt" and os.getuid() == 0:
            return {**failure, "reason": "non_root_host_user_required_for_result_mount"}
        log_dir.mkdir(parents=True, exist_ok=True)
        name = "repofix-" + uuid.uuid4().hex
        output = log_dir / (name + "-output")
        output.mkdir()
        log_path = log_dir / (name + ".log")
        uid = "65534:65534" if os.name == "nt" else f"{os.getuid()}:{os.getgid()}"
        command = self.command(
            probe["executable"],
            probe["image_id"],
            name,
            repository,
            tests,
            output,
            uid,
            probe["endpoint"],
        )
        started = time.monotonic()
        reason = None
        cleanup_ok = False
        with log_path.open("wb") as log:
            process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                shell=False,
                env=child_environment(output),
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                start_new_session=os.name != "nt",
            )
            try:
                while process.poll() is None:
                    if time.monotonic() - started > timeout:
                        reason = "timeout"
                        break
                    if log_path.stat().st_size > 2_000_000:
                        reason = "output_limit"
                        break
                    time.sleep(0.025)
            finally:
                # A killed CLI does not guarantee that its daemon-owned container stops.
                prefix = [probe["executable"], "--host", probe["endpoint"]]
                try:
                    subprocess.run(
                        [*prefix, "rm", "-f", name],
                        capture_output=True,
                        timeout=10,
                        check=False,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    inspected = subprocess.run(
                        [*prefix, "inspect", name],
                        capture_output=True,
                        timeout=8,
                        check=False,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    error = inspected.stderr.decode("utf-8", errors="replace").casefold()
                    cleanup_ok = inspected.returncode == 1 and (
                        "no such object" in error or "no such container" in error
                    )
                except (OSError, subprocess.TimeoutExpired):
                    cleanup_ok = False
                finally:
                    if process.poll() is None:
                        terminate_tree(process)
        payload = {}
        result_path = output / "result.json"
        if result_path.is_file() and result_path.stat().st_size < 4000:
            try:
                payload = json.loads(result_path.read_text("utf-8"))
            except (OSError, ValueError):
                pass
        counters = (
            "tests_run",
            "failures",
            "errors",
            "skipped",
            "expected_failures",
            "unexpected_successes",
        )
        valid = all(type(payload.get(key)) is int and payload[key] >= 0 for key in counters)
        passed = (
            valid
            and payload.get("passed") is True
            and payload["tests_run"] > 0
            and not any(payload[key] for key in counters[1:])
            and process.returncode == 0
            and not reason
            and cleanup_ok
        )
        return {
            **failure,
            **payload,
            "passed": bool(passed),
            "reason": reason or (None if cleanup_ok else "container_cleanup_unverified"),
            "image_id": probe["image_id"],
            "container_name": name,
            "cleanup_verified": cleanup_ok,
            "returncode": process.returncode,
            "isolation": "docker_execution_completed" if cleanup_ok else "docker_not_verified",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "output": log_path.read_bytes()[:24000].decode("utf-8", errors="replace"),
        }
