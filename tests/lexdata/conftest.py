from __future__ import annotations

import pytest

from scripts.storage import topology
from tests.lexdata._support import Harness, make_sources

WORDS = {1: "м’ята", 2: "Бува́й!", 3: "шуба", 4: "у, в", 5: "Cпасибі!"}


@pytest.fixture
def local_fs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every scratch path counts as a local filesystem (locality has its own tests)."""
    monkeypatch.setattr(topology, "_fs_type_for_path", lambda path: "ext4")


@pytest.fixture
def harness(tmp_path, local_fs) -> Harness:
    root = tmp_path / "repo"
    (root / "scripts").mkdir(parents=True)
    (root / "data").mkdir()
    return Harness(root, make_sources(tmp_path / "fixture-sources.db", WORDS))
