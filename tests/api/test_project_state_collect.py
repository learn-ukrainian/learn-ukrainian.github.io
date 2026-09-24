"""Unit tests for offline project-state collection helpers (#7188)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.api import project_state_collect as collect_mod
from scripts.api.project_state_collect import (
    SERVICE_DEFINITIONS,
    classify_serving_root,
    collect_local_document,
    collect_primary_state,
    collect_service_row,
    collect_worktree_count,
    resolve_primary_repo_root,
)
from scripts.api.project_state_sanitize import validate_report_document
from scripts.common.release_layout import MANIFEST_NAME

SHA_MAIN = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
SHA_HEAD = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, timeout=30)


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "primary"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(
        repo,
        "remote",
        "add",
        "origin",
        "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git",
    )
    (repo / "tracked.txt").write_text("v1\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "init")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.strip()
    _git(repo, "update-ref", "refs/remotes/origin/main", head)
    (repo / ".git" / "FETCH_HEAD").write_text("", encoding="utf-8")
    return repo


def test_collect_primary_state_fixture_repo(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    state = collect_primary_state(repo)
    assert state is not None
    assert len(state["head_sha"]) == 40
    assert state["origin_main_sha"] == state["head_sha"]
    assert state["dirty_count"] == 0


def test_collect_primary_dirty_count(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "tracked.txt").write_text("dirty\n", encoding="utf-8")
    state = collect_primary_state(repo)
    assert state is not None
    assert state["dirty_count"] == 1


def test_classify_release_root(tmp_path: Path) -> None:
    release = tmp_path / ".runtime" / "api" / "releases" / SHA_MAIN
    release.mkdir(parents=True)
    (release / MANIFEST_NAME).write_text("{}", encoding="utf-8")
    classified = classify_serving_root(release)
    assert classified["serving_mode"] == "release"
    assert classified["serving_sha"] == SHA_MAIN


def test_classify_checkout_root(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    classified = classify_serving_root(repo)
    assert classified["serving_mode"] == "checkout"
    assert classified["checkout_sha"] is not None


def test_worktree_count(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    assert collect_worktree_count(repo) >= 1


def test_resolve_primary_from_dispatch_worktree(tmp_path: Path) -> None:
    primary = _init_repo(tmp_path)
    worktree = tmp_path / "dispatch-worktree"
    _git(primary, "worktree", "add", str(worktree), "-b", "feature/test")
    resolved = resolve_primary_repo_root(worktree)
    assert resolved.resolve() == primary.resolve()


def write_fake_lsof(tmp_path: Path, *, listener_pid: int | None = None, cwd: Path | None = None) -> Path:
    """Stand-in for ``SVC_LSOF_BIN`` so collection never probes the host's live services.

    With no ``listener_pid`` every port reports no listener. Otherwise the api port
    (8765) reports ``listener_pid`` and ``lsof -p`` reports ``cwd`` (the non-/proc path).
    """
    script = tmp_path / "fake-lsof"
    lines = ["#!/bin/sh"]
    if listener_pid is not None:
        lines += [
            f'if [ "$1" = "-tiTCP:8765" ]; then echo {listener_pid}; exit 0; fi',
            f'if [ "$1" = "-p" ]; then echo "p{listener_pid}"; echo "n{cwd}"; exit 0; fi',
        ]
    lines.append("exit 1")
    script.write_text("\n".join(lines) + "\n", encoding="utf-8")
    script.chmod(0o755)
    return script


def _document_with(row: dict[str, object]) -> dict[str, object]:
    return {
        "host_id": "mac-operator",
        "primary": {
            "head_sha": SHA_HEAD,
            "origin_main_sha": SHA_MAIN,
            "origin_main_age_s": 1.0,
            "ahead": 0,
            "behind": 0,
            "dirty_count": 0,
        },
        "worktrees": {"count": 1},
        "services": [row],
        "collected_at": "2026-09-23T00:00:00Z",
    }


def _running(name: str) -> str:
    return "running"


API = next(item for item in SERVICE_DEFINITIONS if item.name == "api")


def test_collect_service_row_default_state_fn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SVC_LSOF_BIN", str(write_fake_lsof(tmp_path)))
    row = collect_service_row(SERVICE_DEFINITIONS[0])
    assert row["name"] == "sources"
    assert row["state"] == "stopped"
    assert row["serving_mode"] == "checkout"
    assert "unresolved_reason" not in row
    validate_report_document(_document_with(row))


def test_running_service_without_listener_pid_is_unresolved() -> None:
    row = collect_service_row(API, service_state=_running, listener_pid=lambda name: None)
    assert row["serving_mode"] == "unknown"
    assert row["unresolved_reason"] == "no_listener_pid"
    assert row["serving_sha"] is None and row["checkout_sha"] is None
    validate_report_document(_document_with(row))


def test_running_service_with_unreadable_cwd_is_unresolved() -> None:
    row = collect_service_row(
        API,
        service_state=_running,
        listener_pid=lambda name: 4242,
        process_cwd=lambda pid: None,
    )
    assert row["serving_mode"] == "unknown"
    assert row["unresolved_reason"] == "cwd_unreadable"
    validate_report_document(_document_with(row))


def test_running_service_with_cwd_outside_git_is_unresolved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Stub git so the verdict never depends on whether tmp_path sits inside a repo.
    monkeypatch.setattr(collect_mod, "_git", lambda cwd, *args: None)
    row = collect_service_row(
        API,
        service_state=_running,
        listener_pid=lambda name: 4242,
        process_cwd=lambda pid: tmp_path,
    )
    assert row["serving_mode"] == "unknown"
    assert row["unresolved_reason"] == "cwd_not_git_repo"
    validate_report_document(_document_with(row))


def test_running_service_with_unborn_head_is_unresolved(tmp_path: Path) -> None:
    unborn = tmp_path / "unborn"
    unborn.mkdir()
    _git(unborn, "init", "-b", "main")
    row = collect_service_row(
        API,
        service_state=_running,
        listener_pid=lambda name: 4242,
        process_cwd=lambda pid: unborn,
    )
    assert row["serving_mode"] == "unknown"
    assert row["unresolved_reason"] == "head_unresolvable"
    validate_report_document(_document_with(row))


def test_running_service_in_checkout_resolves_sha(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    row = collect_service_row(
        API,
        service_state=_running,
        listener_pid=lambda name: 4242,
        process_cwd=lambda pid: repo,
    )
    assert row["serving_mode"] == "checkout"
    assert row["checkout_sha"] is not None
    assert "unresolved_reason" not in row
    validate_report_document(_document_with(row))


def test_collect_local_document_fixture_repo(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    document = collect_local_document(
        "mac-operator",
        repo_root=repo,
        service_state=lambda name: "stopped",
    )
    assert document is not None
    assert document["host_id"] == "mac-operator"
    assert document["primary"]["head_sha"]
    assert len(document["services"]) == 4
