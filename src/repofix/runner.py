from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path


def child_environment(temp_dir: Path) -> dict[str, str]:
    # Do not inherit API keys, proxies, user Python configuration, or plugin settings.
    env = {name: os.environ[name] for name in ("SystemRoot", "WINDIR") if name in os.environ}
    env.update({"TEMP": str(temp_dir), "TMP": str(temp_dir), "HOME": str(temp_dir)})
    return env


def terminate_tree(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)


def run_tests(repository: Path, tests: Path, log_dir: Path, timeout: float = 12.0) -> dict:
    log_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = log_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"tests-{uuid.uuid4().hex}.log"
    result_path = log_path.with_suffix(".result.json")
    command = [
        sys.executable,
        "-I",
        "-S",
        "-B",
        "-X",
        "utf8",
        str(Path(__file__).with_name("harness.py")),
        str(repository),
        str(tests),
        str(result_path),
    ]
    options = (
        {"creationflags": subprocess.CREATE_NO_WINDOW}
        if os.name == "nt"
        else {
            "start_new_session": True,
        }
    )
    started = time.monotonic()
    reason = None
    with log_path.open("wb") as output:
        process = subprocess.Popen(
            command,
            cwd=repository,
            env=child_environment(temp_dir),
            shell=False,
            stdout=output,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            **options,
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
            if process.poll() is None:
                terminate_tree(process)
    raw = log_path.read_bytes()
    text = raw[:24000].decode("utf-8", errors="replace")
    payload = None
    if result_path.exists() and result_path.stat().st_size < 4000:
        try:
            candidate = json.loads(result_path.read_text(encoding="utf-8"))
            counters = (
                "tests_run",
                "failures",
                "errors",
                "skipped",
                "unexpected_successes",
                "expected_failures",
            )
            if all(type(candidate.get(key)) is int and candidate[key] >= 0 for key in counters):
                payload = candidate
        except (ValueError, OSError):
            pass
    payload = payload or {"passed": False, "tests_run": 0, "failures": 0, "errors": 1}
    payload.update(
        {
            "passed": bool(
                payload.get("passed") is True
                and process.returncode == 0
                and not reason
                and payload.get("tests_run", 0) > 0
                and not any(
                    payload.get(key, 0)
                    for key in (
                        "failures",
                        "errors",
                        "skipped",
                        "unexpected_successes",
                        "expected_failures",
                    )
                )
            ),
            "returncode": process.returncode,
            "reason": reason,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "output": text,
            "output_truncated": len(raw) > 24000,
            "isolation": "trusted_builtin_local_process",
        }
    )
    return payload
