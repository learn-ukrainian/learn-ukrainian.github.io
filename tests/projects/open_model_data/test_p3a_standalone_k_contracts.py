"""Standalone frozen-contract publication uses committed registry baselines."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.projects.open_model_data import freeze_phase3_v3a_taxonomy_denominator_compatibility as v3a
from scripts.projects.open_model_data import phase3_v3b_cooperative_control_plane as v3b
from scripts.projects.open_model_data import phase3_v3c_heldout_extension_solo_custody as v3c


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, timeout=30)


@pytest.fixture
def committed_registry(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    for relative in (
        "registry/projects/open_model_data/contracts/first.json",
        "registry/projects/open_model_data/contracts/second.json",
        "data/projects/open_model_data/payload.json",
        "registry/artifacts/open_model_other_indexes.manifest.json",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"old")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "committed K and A baselines")
    return root


@pytest.mark.parametrize("writer", [v3a, v3b, v3c])
def test_writer_validates_complete_bundle_before_registry_publication(
    committed_registry: Path, monkeypatch: pytest.MonkeyPatch, writer: object
) -> None:
    root = committed_registry
    first = root / "registry/projects/open_model_data/contracts/first.json"
    second = root / "registry/projects/open_model_data/contracts/second.json"
    payload = root / "data/projects/open_model_data/payload.json"
    manifest = root / "registry/artifacts/open_model_other_indexes.manifest.json"
    monkeypatch.setattr(writer, "ROOT", root)
    monkeypatch.setattr(writer, "ARTIFACT_PATH", first)
    monkeypatch.setattr(writer, "MATRIX_PATH" if writer is v3a else "SCHEMA_PATH", second)
    if writer is v3a:
        monkeypatch.setattr(writer, "build_main", lambda: {"main": True})
        monkeypatch.setattr(writer, "build_matrix", lambda _main: {"matrix": True})
    else:
        monkeypatch.setattr(writer, "build_schema", lambda: {"schema": True})
        monkeypatch.setattr(writer, "build_artifact", lambda: {"artifact": True})

    def invalid(*_args: object) -> None:
        raise ValueError("invalid complete bundle")

    monkeypatch.setattr(writer, "validate", invalid)
    with pytest.raises(ValueError, match="invalid complete bundle"):
        writer.write_outputs()
    assert first.read_bytes() == second.read_bytes() == b"old"
    assert payload.read_bytes() == manifest.read_bytes() == b"old"

    monkeypatch.setattr(writer, "validate", lambda *_args: None)
    writer.write_outputs()
    assert first.read_bytes() != b"old"
    assert second.read_bytes() != b"old"
    assert payload.read_bytes() == manifest.read_bytes() == b"old"

    with pytest.raises(ValueError, match="dirty tracked registry output"):
        writer.write_outputs()
