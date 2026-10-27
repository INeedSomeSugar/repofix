from __future__ import annotations

import hashlib

import pytest

from repofix.cases import all_cases, dataset_type, get_case
from repofix.config import Settings
from repofix.docker_runner import DockerRunner
from repofix.engine import create_run
from repofix.experiments import Experiments
from repofix.storage import RunStore
from repofix.workspace import check_python


def test_upstream_suite_does_not_change_original_development_defaults():
    assert len(all_cases()) == 5
    cases = all_cases(include_upstream=True)
    assert len(cases) == 8
    assert len({case["id"] for case in cases}) == 8
    assert dataset_type(["csv_records"]) == "original_synthetic_development_exercises"
    assert dataset_type(["upstream_value_chain"]) == "curated_upstream_development_excerpts"
    mixed = dataset_type(["csv_records", "upstream_value_chain"])
    assert mixed == "mixed_trusted_development_tasks"


@pytest.mark.parametrize("case", all_cases(include_upstream=True)[5:], ids=lambda c: c["id"])
def test_upstream_provenance_policies_and_docker_gate(case, tmp_path):
    provenance = case["provenance"]
    assert get_case(case["id"]) == case
    assert provenance["license"] == "MIT"
    assert provenance["fix_url"].endswith(provenance["snapshots"][1]["commit"])
    for key, content in [
        ("license_sha256", case["files"]["LICENSE.md"]),
        ("public_tests_sha256", case["files"]["tests/test_public.py"]),
        ("independent_tests_sha256", case["heldout"]),
    ]:
        assert hashlib.sha256(content.encode()).hexdigest() == provenance[key]
    for snapshot, source in zip(
        provenance["snapshots"],
        [case["files"]["project/core.py"], case["replay_edits"][0]["new"]],
        strict=True,
    ):
        assert hashlib.sha256(source.encode()).hexdigest() == snapshot["core_sha256"]
        assert snapshot["functions"]
        assert all(span["last_line"] >= span["first_line"] for span in snapshot["functions"])
        check_python(source)
    check_python(case["files"]["tests/test_public.py"], is_test=True)
    check_python(case["heldout"], is_test=True)
    store = RunStore(tmp_path / "runs")
    with pytest.raises(ValueError, match="require_docker"):
        create_run(store, case["id"])
    assert not list((tmp_path / "runs").glob("*/run.json"))
    with pytest.raises(ValueError, match="require_docker"):
        Experiments(Settings(data_dir=tmp_path / "experiment-work")).create(
            [case["id"]], ["feedback"], 1, "replay", "scripted"
        )


def test_docker_experiment_freezes_immutable_image(monkeypatch, tmp_path):
    image_id = "sha256:" + "a" * 64
    monkeypatch.setattr(
        DockerRunner, "preflight", lambda self: {"available": True, "image_id": image_id}
    )
    experiment = Experiments(Settings(data_dir=tmp_path)).create(
        ["upstream_value_chain"], ["feedback"], 1, "replay", "scripted", "docker"
    )
    assert experiment["manifest"]["runner_image_id"] == image_id
    assert experiment["manifest"]["dataset_type"] == "curated_upstream_development_excerpts"


def test_docker_experiment_unavailable_does_not_create_protocol(monkeypatch, tmp_path):
    monkeypatch.setattr(DockerRunner, "preflight", lambda self: {"available": False})
    experiments = Experiments(Settings(data_dir=tmp_path))
    with pytest.raises(ValueError, match="preflight_failed"):
        experiments.create(["csv_records"], ["feedback"], 1, "replay", "scripted", "docker")
    assert not list(tmp_path.rglob("experiment.json"))
