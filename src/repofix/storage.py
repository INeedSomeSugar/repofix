from __future__ import annotations

import hashlib
import json
import os
import re
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .schema import RunState


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    # Windows readers may briefly hold a non-delete-sharing handle while polling JSON.
    # Keep the previous checkpoint valid and retry the atomic rename after they close it.
    for attempt in range(30):
        try:
            os.replace(temporary, path)
            break
        except PermissionError:
            if attempt == 29:
                raise
            time.sleep(0.01)


class RunBusyError(RuntimeError):
    pass


class RunStore:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def directory(self, run_id: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{32}", run_id):
            raise ValueError("invalid run id")
        directory = self.root / run_id
        if directory.is_symlink():
            raise ValueError("symlink run directory is forbidden")
        return directory

    def save(self, state: RunState) -> None:
        state.updated_at = utc_now()
        atomic_json(self.directory(state.run_id) / "run.json", state.model_dump())

    def load(self, run_id: str) -> RunState:
        return RunState.model_validate_json(
            (self.directory(run_id) / "run.json").read_text(encoding="utf-8")
        )

    def recent(self, limit: int = 30) -> list[RunState]:
        paths = sorted(self.root.glob("*/run.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        result = []
        for path in paths[:limit]:
            try:
                result.append(self.load(path.parent.name))
            except (ValueError, OSError):
                continue
        return result

    def event(self, run_id: str, kind: str, **data) -> None:
        entry = {"time": utc_now(), "kind": kind, **data}
        with (self.directory(run_id) / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            handle.flush()

    def events(self, run_id: str) -> list[dict]:
        path = self.directory(run_id) / "events.jsonl"
        if not path.exists():
            return []
        events = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events

    @contextmanager
    def lock(self, run_id: str):
        """OS-managed lock: automatically released after a process crash."""
        path = self.directory(run_id) / "run.lock"
        with path.open("a+b") as handle:
            if path.stat().st_size == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise RunBusyError("this run is already executing") from None
            try:
                yield
            finally:
                handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def elapsed(start: float) -> float:
    return round(time.monotonic() - start, 3)
