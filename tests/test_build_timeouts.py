"""Regression tests for bounded subprocess calls in scripts/build (#7213 slice 10)."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace


def _result(*, stdout="", stderr="", returncode=0) -> SimpleNamespace:
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


def test_phase_mdx_timeout_marks_phase_failed(monkeypatch, tmp_path: Path) -> None:
    import scripts.build.build_module_direct as bmd

    status_path = tmp_path / "status" / "tse.status.json"
    ctx = bmd.DirectModuleContext(
        slug="tse",
        level="a1",
        yaml_path=tmp_path / "tse.yaml",
        status_path=status_path,
    )

    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(bmd.subprocess, "run", fake_run)

    assert bmd.phase_mdx(ctx) is False
    assert status_path.is_file()
    assert ctx.status_data["phases"]["mdx"]["status"] == "failed"
    assert ctx.status_data["phases"]["mdx"]["error"] == "timeout"


def _make_archive(ra, tmp_path: Path, worktree: Path):
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    return ra.RunArchive(
        project_root=tmp_path,
        worktree_path=worktree,
        archive_dir=archive_dir,
        level="a1",
        slug="demo",
        run_id="20260824-000000",
        parent_run_id=None,
        base_ref="HEAD",
    )


def test_write_commit_diff_summary_subprocesses_are_bounded(monkeypatch, tmp_path: Path) -> None:
    import scripts.build.run_archive as ra

    worktree = tmp_path / "wt"
    worktree.mkdir()
    archive = _make_archive(ra, tmp_path, worktree)
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if "rev-parse" in command:
            return _result(stdout="abc1234\n")
        return _result(stdout=" module.md | 2 +-\n 1 file changed\n")

    monkeypatch.setattr(ra.subprocess, "run", fake_run)
    archive.write_commit_diff_summary()

    diff_calls = [command for command in calls if "diff" in command]
    head_calls = [command for command in calls if "rev-parse" in command]
    assert len(diff_calls) == len(head_calls) == 1

    summary = json.loads((archive.archive_dir / "commit_diff_summary.json").read_text(encoding="utf-8"))
    assert summary["head_ref"] == "abc1234"
    assert summary["files_changed"] == 1


def test_write_commit_diff_summary_timeout_degrades_to_empty_summary(monkeypatch, tmp_path: Path) -> None:
    import scripts.build.run_archive as ra

    worktree = tmp_path / "wt"
    worktree.mkdir()
    archive = _make_archive(ra, tmp_path, worktree)

    def timeout_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(ra.subprocess, "run", timeout_run)
    archive.write_commit_diff_summary()

    summary = json.loads((archive.archive_dir / "commit_diff_summary.json").read_text(encoding="utf-8"))
    assert summary["paths"] == []
    assert summary["files_changed"] == 0
    assert summary["head_ref"] == "HEAD"


def _make_worktree(v7, tmp_path: Path):
    path = tmp_path / "wt"
    path.mkdir()
    return v7.BuildWorktree(
        path=path,
        branch="build/a1/demo-20260824-000000",
        base_sha="abc1234",
        repo_root=tmp_path,
        run_id="20260824-000000",
    )


def test_persist_build_artifacts_timeout_returns_false_with_warning(monkeypatch, tmp_path: Path, capsys) -> None:
    import scripts.build.v7_build as v7

    worktree = _make_worktree(v7, tmp_path)
    monkeypatch.setattr(v7, "_ensure_persist_target_is_not_primary_checkout", lambda _w: None)
    monkeypatch.setattr(v7, "_persist_artifact_paths", lambda _w, **_kw: ["module.md"])

    def timeout_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(v7.subprocess, "run", timeout_run)

    assert v7._persist_build_artifacts(worktree, level="a1", slug="demo", result="failed") is False
    captured = capsys.readouterr()
    assert "warning" in captured.err.lower()


def _worktree_args(worktree_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        level="a1",
        slug="demo",
        writer="claude",
        effort=None,
        reviewer=None,
        writer_timeout=1800,
        dry_run=False,
        out=None,
        worktree=str(worktree_path),
        keep_worktree=True,
        telemetry_out=None,
        no_resume=False,
        use_generator=False,
    )


def test_run_in_worktree_child_timeout_maps_to_exit_one(monkeypatch, tmp_path: Path, capsys) -> None:
    import scripts.build.v7_build as v7

    worktree = _make_worktree(v7, tmp_path)
    monkeypatch.setattr(v7, "_setup_worktree", lambda _level, _slug, _raw: worktree)
    monkeypatch.setattr(
        v7.run_archive.RunArchive, "write_commit_diff_summary", lambda self, **_kw: None
    )
    monkeypatch.setattr(v7, "_persist_build_artifacts", lambda _w, **_kw: True)

    seen_timeouts: list[int] = []

    def fake_run(command, **kwargs):
        if command[1] == "scripts/build/v7_build.py":
            seen_timeouts.append(kwargs["timeout"])
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return _result(returncode=1)

    monkeypatch.setattr(v7.subprocess, "run", fake_run)

    rc = v7._run_in_worktree(_worktree_args(worktree.path), ["a1", "demo"])

    assert rc == 1
    assert seen_timeouts == [v7.WORKTREE_CHILD_TIMEOUT_S]
    assert "terminated" in capsys.readouterr().err
