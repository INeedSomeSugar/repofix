from pathlib import Path

import pytest

from repofix.config import Settings
from repofix.storage import RunStore


@pytest.fixture
def settings(tmp_path: Path):
    return Settings(data_dir=tmp_path)


@pytest.fixture
def store(tmp_path: Path):
    return RunStore(tmp_path / "runs")
