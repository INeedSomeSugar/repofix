"""Run trusted engineering probes with the actual DockerRunner, without model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from repofix.docker_runner import DockerRunner

BOUNDARIES = """import errno
import json
import os
from pathlib import Path
import socket
import subprocess
import threading
import time
import unittest

class Boundaries(unittest.TestCase):
    def test_identity_and_privileges(self):
        self.assertNotEqual(os.getuid(), 0)
        lines = Path("/proc/self/status").read_text().splitlines()
        status = dict(line.split(":", 1) for line in lines if ":" in line)
        self.assertEqual(int(status["CapEff"].strip(), 16), 0)
        self.assertEqual(status["NoNewPrivs"].strip(), "1")

    def test_readonly_mounts(self):
        for name in ["/repository/canary.txt", "/tests/test_probe.py", "/harness.py"]:
            with self.subTest(path=name), self.assertRaises(OSError) as caught:
                with open(name, "r+b"):
                    pass
            self.assertIn(caught.exception.errno, [errno.EROFS, errno.EACCES])
        with self.assertRaises(OSError):
            Path("/usr/repofix-probe").write_text("blocked")

    def test_writable_results_and_tmp(self):
        Path("/results/probe.txt").write_text("ok")
        Path("/tmp/probe.txt").write_text("ok")
        self.assertEqual(Path("/results/probe.txt").read_text(), "ok")

    def test_tmp_noexec(self):
        path = Path("/tmp/exec-probe")
        path.write_text("#!/bin/sh\\nexit 0\\n")
        path.chmod(0o755)
        with self.assertRaises(PermissionError):
            subprocess.run([str(path)], check=False)

    def test_no_network(self):
        self.assertEqual({name for _, name in socket.if_nameindex()}, {"lo"})
        with socket.socket() as client:
            client.settimeout(0.5)
            self.assertNotEqual(client.connect_ex(("192.0.2.1", 443)), 0)

    def test_no_host_credentials_or_docker_socket(self):
        for name in ["DEEPSEEK_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN", "REPOFIX_PROBE_SECRET"]:
            self.assertNotIn(name, os.environ)
        self.assertFalse(Path("/var/run/docker.sock").exists())

    def test_effective_cgroup_limits(self):
        root = Path("/sys/fs/cgroup")
        names = ["memory.max", "memory.swap.max", "pids.max", "cpu.max"]
        limits = {name: (root / name).read_text().strip() for name in names}
        Path("/results/effective-limits.json").write_text(json.dumps(limits))
        self.assertEqual(int(limits["memory.max"]), 256 * 1024 * 1024)
        self.assertEqual(int(limits["memory.swap.max"]), 0)
        self.assertEqual(int(limits["pids.max"]), 64)
        quota, period = map(int, limits["cpu.max"].split())
        self.assertEqual(quota / period, 1)

    def test_memory_limit_enforced(self):
        events = Path("/sys/fs/cgroup/memory.events")
        before = dict(line.split() for line in events.read_text().splitlines())
        command = ["python", "-I", "-S", "-c", "a=bytearray(384*1024*1024)"]
        child = subprocess.run(command, capture_output=True, timeout=8)
        after = dict(line.split() for line in events.read_text().splitlines())
        self.assertNotEqual(child.returncode, 0)
        self.assertGreater(int(after["oom_kill"]), int(before["oom_kill"]))

    def test_pid_limit_enforced(self):
        stop = threading.Event()
        threads = []
        blocked = False
        try:
            for _ in range(80):
                worker = threading.Thread(target=stop.wait)
                try:
                    worker.start()
                except RuntimeError:
                    blocked = True
                    break
                threads.append(worker)
            self.assertTrue(blocked)
            self.assertLess(len(threads), 64)
        finally:
            stop.set()
            for worker in threads:
                worker.join(timeout=2)

    def test_z_inspection_window(self):
        time.sleep(2)
"""


class RecordingRunner(DockerRunner):
    name = None

    def command(self, *args):
        command = super().command(*args)
        self.name = args[2]
        return command


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("Refusing to overwrite a historical report")
    root = Path(__file__).resolve().parents[1]
    work = root / "work" / ("docker-boundaries-" + uuid.uuid4().hex)
    work.mkdir(parents=True)
    runner = RecordingRunner()
    preflight = runner.preflight()
    if not preflight["available"]:
        raise SystemExit(json.dumps(preflight))
    prefix = [preflight["executable"], "--host", preflight["endpoint"]]
    outcomes = []
    os.environ["REPOFIX_PROBE_SECRET"] = "synthetic-sentinel-not-a-credential"
    for case, body, timeout in [
        ("boundaries", BOUNDARIES, 20),
        (
            "timeout",
            "import time, unittest\nclass Probe(unittest.TestCase):\n"
            " def test_sleep(self): time.sleep(30)\n",
            2,
        ),
        (
            "output_limit",
            "import sys, time, unittest\nclass Probe(unittest.TestCase):\n"
            " def test_output(self):\n"
            "  sys.stdout.write('x'*2100000); sys.stdout.flush(); time.sleep(30)\n",
            10,
        ),
    ]:
        directory = work / case
        repository, tests, logs = (directory / part for part in ["repository", "tests", "logs"])
        repository.mkdir(parents=True)
        tests.mkdir()
        (repository / "canary.txt").write_text("unchanged", "utf-8")
        (tests / "test_probe.py").write_text(body, "utf-8")
        frozen = hashlib.sha256((tests / "test_probe.py").read_bytes()).hexdigest()
        runner.name = None
        inspected = None
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(runner.run_tests, repository, tests, logs, timeout)
            while not future.done() and inspected is None:
                if runner.name:
                    result = subprocess.run(
                        [*prefix, "inspect", runner.name], capture_output=True, timeout=5
                    )
                    if result.returncode == 0:
                        raw = json.loads(result.stdout)[0]
                        if raw["State"]["Running"]:
                            keys = [
                                "NetworkMode",
                                "ReadonlyRootfs",
                                "CapDrop",
                                "SecurityOpt",
                                "PidsLimit",
                                "Memory",
                                "MemorySwap",
                                "NanoCpus",
                                "AutoRemove",
                                "Tmpfs",
                            ]
                            inspected = {
                                "host_config": {key: raw["HostConfig"].get(key) for key in keys},
                                "user": raw["Config"]["User"],
                                "mounts": [
                                    {k: mount[k] for k in ["Destination", "RW"]}
                                    for mount in raw["Mounts"]
                                ],
                            }
                time.sleep(0.05)
            outcome = future.result()
        expected = (
            outcome["passed"]
            if case == "boundaries"
            else (not outcome["passed"] and outcome["reason"] == case)
        )
        unchanged = (
            repository / "canary.txt"
        ).read_text() == "unchanged" and frozen == hashlib.sha256(
            (tests / "test_probe.py").read_bytes()
        ).hexdigest()
        outcomes.append(
            {
                "case": case,
                "expected_behavior_observed": bool(
                    expected and unchanged and outcome.get("cleanup_verified") and inspected
                ),
                "frozen_inputs_unchanged": unchanged,
                "inspect": inspected,
                "runner_result": outcome,
            }
        )
    os.environ.pop("REPOFIX_PROBE_SECRET", None)
    leftovers = (
        subprocess.check_output([*prefix, "ps", "-aq", "--filter", "name=repofix-"])
        .decode()
        .split()
    )
    report = {
        "checked_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Trusted engineering probes on this Docker/WSL host; "
            "not an arbitrary-code security certification"
        ),
        "model_calls": 0,
        "preflight": preflight,
        "runner_source_sha256": hashlib.sha256(
            (root / "src/repofix/docker_runner.py").read_bytes()
        ).hexdigest(),
        "probe_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "outcomes": outcomes,
        "leftover_repofix_containers": len(leftovers),
        "passed": all(item["expected_behavior_observed"] for item in outcomes) and not leftovers,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    print(
        json.dumps(
            {
                "report": str(args.out),
                "passed": report["passed"],
                "cases": [
                    {
                        "case": item["case"],
                        "expected_behavior_observed": item["expected_behavior_observed"],
                    }
                    for item in outcomes
                ],
            }
        )
    )
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
