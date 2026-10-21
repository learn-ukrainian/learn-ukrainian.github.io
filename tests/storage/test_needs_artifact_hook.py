"""Tests for the needs_artifact pytest setup hook."""

from __future__ import annotations

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


def test_corrupt_artifact_fails_instead_of_skipping(monkeypatch: pytest.MonkeyPatch) -> None:
    error = paths.MissingArtifactError("group-a", "source.json", "/exact/hydrate-command", "sha256 mismatch")
    monkeypatch.setattr(paths, "find_entry", lambda group, rel: {"path": "data/source.json"})
    monkeypatch.setattr(paths, "verify_file", lambda path, entry, **kw: (_ for _ in ()).throw(error))
    with pytest.raises(paths.MissingArtifactError, match="sha256 mismatch"):
        conftest.pytest_runtest_setup(_item("group-a", "source.json"))
