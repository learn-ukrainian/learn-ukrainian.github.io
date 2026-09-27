"""Tests for the needs_artifact pytest setup hook."""

from __future__ import annotations

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


def test_present_artifact_runs_without_skipping(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(paths, "find_entry", lambda group, rel: {"path": "data/source.json"})
    calls = []
    monkeypatch.setattr(paths, "verify_file", lambda path, entry, **kw: calls.append((path, entry, kw)))
    assert conftest.pytest_runtest_setup(_item("group-a", "source.json")) is None
    assert calls == [
        (paths.DATA_ROOT / "source.json", {"path": "data/source.json"}, {"group": "group-a", "rel": "source.json"})
    ]


def test_corrupt_artifact_fails_instead_of_skipping(monkeypatch: pytest.MonkeyPatch) -> None:
    error = paths.MissingArtifactError("group-a", "source.json", "/exact/hydrate-command", "sha256 mismatch")
    monkeypatch.setattr(paths, "find_entry", lambda group, rel: {"path": "data/source.json"})
    monkeypatch.setattr(paths, "verify_file", lambda path, entry, **kw: (_ for _ in ()).throw(error))
    with pytest.raises(paths.MissingArtifactError, match="sha256 mismatch"):
        conftest.pytest_runtest_setup(_item("group-a", "source.json"))


def test_needs_artifact_requires_two_positional_arguments() -> None:
    with pytest.raises(pytest.UsageError, match=r"exactly \(group, rel\)"):
        conftest.pytest_runtest_setup(_item("group-a"))


def test_ci_audits_collection_and_runtime_skips_from_all_configured_roots() -> None:
    workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    audit = workflow.split("- name: Verify needs_artifact skip set", 1)[1].split("- name: Stop memory sampler", 1)[0]
    assert "needs.changes.outputs.docs_only == 'false'" in audit
    assert "pytest --collect-only -m needs_artifact" in audit
    assert "git ls-files | grep -E" in audit
    assert "collected != expected" in audit
    assert "expected - artifact_skips" in audit and "artifact_skips - expected" in audit
