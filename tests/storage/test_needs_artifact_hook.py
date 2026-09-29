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
    audit = workflow.split("  needs-artifact-audit:", 1)[1].split("  contracts:", 1)[0]
    assert "needs.changes.outputs.docs_only == 'false'" in audit
    assert "pytest --collect-only -m needs_artifact" in audit
    assert "git ls-files | grep -E" in audit
    assert "collected != expected" in audit
    assert "expected - artifact_skips" in audit and "artifact_skips - expected" in audit
    assert "::group::" in audit
    assert "tail -n 200 ci-artifacts/needs-artifact-collected.txt" in audit
    assert "::endgroup::" in audit
    assert "actions/upload-artifact" in audit
    assert "if: failure()" in audit
    assert "path: ci-artifacts/" in audit
    assert "retention-days: 7" in audit


@pytest.mark.parametrize(
    ("collection_status", "expect_group", "expect_exit"),
    [
        (2, True, 2),
        (1, True, 1),
        (0, False, 0),
        (5, False, 0),
    ],
)
def test_ci_needs_artifact_collection_failure_branch_behavior(
    tmp_path: Path, collection_status: int, expect_group: bool, expect_exit: int
) -> None:
    import subprocess

    workflow = (Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    audit = workflow.split("  needs-artifact-audit:", 1)[1].split("  contracts:", 1)[0]
    assert 'if [ "${collection_status:-0}" -ne 0 ] && [ "$collection_status" -ne 5 ]; then' in audit

    artifacts_dir = tmp_path / "ci-artifacts"
    artifacts_dir.mkdir()
    collected = artifacts_dir / "needs-artifact-collected.txt"
    collected.write_text("dummy error output from pytest\n", encoding="utf-8")

    script = f"""
    set -euo pipefail
    collection_status={collection_status}
    if [ "${{collection_status:-0}}" -ne 0 ] && [ "$collection_status" -ne 5 ]; then
      echo "::group::pytest needs_artifact collection failure"
      tail -n 200 ci-artifacts/needs-artifact-collected.txt
      echo "::endgroup::"
      exit "$collection_status"
    fi
    """
    proc = subprocess.run(["bash", "-c", script], cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert proc.returncode == expect_exit
    if expect_group:
        assert "::group::pytest needs_artifact collection failure" in proc.stdout
        assert "dummy error output from pytest" in proc.stdout
        assert "::endgroup::" in proc.stdout
    else:
        assert "::group::" not in proc.stdout
        assert "dummy error output" not in proc.stdout
