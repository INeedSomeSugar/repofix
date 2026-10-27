import json

from repofix.storage import atomic_json


def test_checkpoint_survives_transient_windows_reader_lock(tmp_path, monkeypatch):
    import os

    path = tmp_path / "checkpoint.json"
    atomic_json(path, {"turn": 1})
    original_replace = os.replace
    attempts = []

    def briefly_locked(source, destination):
        attempts.append(1)
        if len(attempts) <= 2:
            assert json.loads(path.read_text(encoding="utf-8"))["turn"] == 1
            raise PermissionError("simulated reader lock")
        return original_replace(source, destination)

    monkeypatch.setattr(os, "replace", briefly_locked)
    atomic_json(path, {"turn": 2})
    assert len(attempts) == 3
    assert json.loads(path.read_text(encoding="utf-8")) == {"turn": 2}
