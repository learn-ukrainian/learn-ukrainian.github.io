"""Tests for the needs_artifact pytest setup hook."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.storage import paths
from tests import conftest


def _item(*args: object, **kwargs: object) -> SimpleNamespace:
    marker = pytest.mark.needs_artifact(*args, **kwargs).mark
    return SimpleNamespace(get_closest_marker=lambda name: marker if name == "needs_artifact" else None)


def test_missing_artifact_skips_with_hydration_command(monkeypatch: pytest.MonkeyPatch) -> None:
    error = paths.MissingArtifactError("group-a", "source.json", "/exact/hydrate-command")

    def missing(group: str, rel: str) -> dict:
        assert (group, rel) == ("group-a", "source.json")
        raise error

    monkeypatch.setattr(paths, "find_entry", missing)
    with pytest.raises(pytest.skip.Exception, match=r"needs_artifact:.*exact/hydrate-command"):
        conftest.pytest_runtest_setup(_item("group-a", "source.json"))


def test_present_artifact_runs_without_skipping(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts.guardrails import worktree_containment

    primary = tmp_path / "primary"
    artifact = primary / "data" / "source.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"fixture")
    entry = {"path": "data/source.json", "size": 7, "sha256": hashlib.sha256(b"fixture").hexdigest()}
    monkeypatch.setattr(paths, "find_entry", lambda group, rel: entry)
    monkeypatch.setattr(worktree_containment, "resolve_main_root", lambda root: primary)
    item = _item("group-a", "source.json")
    item.fixturenames = ["data_artifact_factory"]

    assert conftest.pytest_runtest_setup(item) is None
    assert conftest._primary_artifact_path("group-a", "source.json") == artifact
    assert artifact.read_bytes() == b"fixture"


def test_corrupt_artifact_fails_instead_of_skipping(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts.guardrails import worktree_containment

    primary = tmp_path / "primary"
    artifact = primary / "data" / "source.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"tamper!")
    entry = {"path": "data/source.json", "size": 7, "sha256": hashlib.sha256(b"fixture").hexdigest()}
    monkeypatch.setattr(paths, "find_entry", lambda group, rel: entry)
    monkeypatch.setattr(worktree_containment, "resolve_main_root", lambda root: primary)
    item = _item("group-a", "source.json")
    item.fixturenames = ["data_artifact_factory"]

    with pytest.raises(paths.MissingArtifactError, match="sha256"):
        conftest.pytest_runtest_setup(item)


def test_needs_artifact_requires_two_positional_arguments() -> None:
    with pytest.raises(pytest.UsageError, match=r"exactly \(group, rel\)"):
        conftest.pytest_runtest_setup(_item("group-a"))
