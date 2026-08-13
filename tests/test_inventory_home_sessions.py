"""Tests for the allowlisted home-session inventory and retention CLI."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from scripts.hygiene import inventory_home_sessions as inventory


def _old_file(path: Path, *, age_days: float = 15.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("session\n", encoding="utf-8")
    timestamp = time.time() - age_days * 86400
    os.utime(path, (timestamp, timestamp))
    return path


def test_inventory_reports_provider_roots_and_only_stale_session_files(tmp_path: Path) -> None:
    old = _old_file(tmp_path / ".codex" / "sessions" / "2026" / "old.jsonl")
    _old_file(tmp_path / ".codex" / "config.toml")
    recent = _old_file(tmp_path / ".claude" / "projects" / "recent.jsonl", age_days=2)

    roots, candidates = inventory.inventory_home_sessions(home=tmp_path, retention_days=14)

    by_provider = {root.provider: root for root in roots}
    assert by_provider["codex"].exists is True
    assert by_provider["codex"].size_bytes is not None
    assert by_provider["claude"].session_files == 1
    assert {candidate.path for candidate in candidates} == {str(old)}
    assert str(recent) not in {candidate.path for candidate in candidates}


def test_apply_requires_explicit_environment_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    old = _old_file(tmp_path / ".codex" / "sessions" / "old.jsonl")
    _roots, candidates = inventory.inventory_home_sessions(home=tmp_path, retention_days=14)
    monkeypatch.delenv(inventory.APPLY_ENV, raising=False)

    with pytest.raises(PermissionError, match="LU_HOME_SESSION_APPLY=1"):
        inventory.apply_retention(
            candidates=candidates,
            home=tmp_path,
            archive_root=tmp_path / "archive",
            action="archive",
            retention_days=14,
        )

    assert old.exists()


def test_apply_archives_only_stale_allowlisted_session_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = _old_file(tmp_path / ".codex" / "sessions" / "old.jsonl")
    config = _old_file(tmp_path / ".codex" / "config.toml")
    _roots, candidates = inventory.inventory_home_sessions(home=tmp_path, retention_days=14)
    monkeypatch.setenv(inventory.APPLY_ENV, "1")

    results = inventory.apply_retention(
        candidates=candidates,
        home=tmp_path,
        archive_root=tmp_path / "archive",
        action="archive",
        retention_days=14,
    )

    archived = tmp_path / "archive" / "codex" / "sessions" / "old.jsonl"
    assert results == [{"path": str(old), "action": "archived", "archive_path": str(archived)}]
    assert not old.exists()
    assert archived.read_text(encoding="utf-8") == "session\n"
    assert config.exists()


def test_symlinked_session_file_is_never_a_candidate(tmp_path: Path) -> None:
    outside = _old_file(tmp_path / "outside.jsonl")
    session_dir = tmp_path / ".cursor" / "chats"
    session_dir.mkdir(parents=True)
    (session_dir / "linked.jsonl").symlink_to(outside)

    _roots, candidates = inventory.inventory_home_sessions(home=tmp_path, retention_days=14)

    assert candidates == []
    assert outside.exists()


def test_retention_boundary_uses_unrounded_file_age(tmp_path: Path) -> None:
    almost_old = _old_file(tmp_path / ".grok" / "sessions" / "almost-old.jsonl", age_days=13.99)

    _roots, candidates = inventory.inventory_home_sessions(home=tmp_path, retention_days=14)

    assert str(almost_old) not in {candidate.path for candidate in candidates}


def _tree_snapshot(root: Path) -> dict[str, bytes]:
    """Map every regular file under ``root`` (relative path -> bytes)."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def test_inventory_is_read_only_and_never_deletes(tmp_path: Path) -> None:
    stale = _old_file(tmp_path / ".codex" / "sessions" / "2026" / "old.jsonl")
    config = _old_file(tmp_path / ".codex" / "config.toml")
    recent = _old_file(tmp_path / ".claude" / "projects" / "recent.jsonl", age_days=2)

    before = _tree_snapshot(tmp_path)
    _roots, candidates = inventory.inventory_home_sessions(home=tmp_path, retention_days=14)

    # The stale file is reported as a candidate but must survive the scan.
    assert str(stale) in {candidate.path for candidate in candidates}
    assert candidates
    assert _tree_snapshot(tmp_path) == before
    assert stale.exists()
    assert config.exists()
    assert recent.exists()
    # No archive directory or any other side effect was created.
    assert sorted(path.name for path in tmp_path.iterdir()) == [".claude", ".codex"]


def test_apply_delete_refused_without_environment_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = _old_file(tmp_path / ".grok" / "sessions" / "old.jsonl")
    _roots, candidates = inventory.inventory_home_sessions(home=tmp_path, retention_days=14)
    monkeypatch.delenv(inventory.APPLY_ENV, raising=False)

    with pytest.raises(PermissionError, match="LU_HOME_SESSION_APPLY=1"):
        inventory.apply_retention(
            candidates=candidates,
            home=tmp_path,
            archive_root=tmp_path / "archive",
            action="delete",
            retention_days=14,
        )

    assert old.exists()


def test_apply_delete_removes_only_stale_allowlisted_session_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = _old_file(tmp_path / ".codex" / "sessions" / "old.jsonl")
    config = _old_file(tmp_path / ".codex" / "config.toml")
    recent = _old_file(tmp_path / ".claude" / "projects" / "recent.jsonl", age_days=2)
    _roots, candidates = inventory.inventory_home_sessions(home=tmp_path, retention_days=14)
    monkeypatch.setenv(inventory.APPLY_ENV, "1")

    results = inventory.apply_retention(
        candidates=candidates,
        home=tmp_path,
        archive_root=tmp_path / "archive",
        action="delete",
        retention_days=14,
        repo_root=tmp_path / "repo",
    )

    assert results == [{"path": str(old), "action": "deleted"}]
    assert not old.exists()
    assert config.exists()
    assert recent.exists()
    assert not (tmp_path / "archive").exists()


def test_apply_delete_skips_when_delete_guard_refuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """assert_delete_target refusal must leave the session file untouched."""
    old = _old_file(tmp_path / ".codex" / "sessions" / "old.jsonl")
    _roots, candidates = inventory.inventory_home_sessions(home=tmp_path, retention_days=14)
    monkeypatch.setenv(inventory.APPLY_ENV, "1")

    def _refuse(*_args, **_kwargs):
        raise ValueError("outside approved deletion roots")

    monkeypatch.setattr(inventory, "assert_delete_target", _refuse)

    results = inventory.apply_retention(
        candidates=candidates,
        home=tmp_path,
        archive_root=tmp_path / "archive",
        action="delete",
        retention_days=14,
        repo_root=tmp_path / "repo",
    )

    assert results == [
        {
            "path": str(old),
            "action": "skipped",
            "reason": "delete guard refused: outside approved deletion roots",
        }
    ]
    assert old.exists()


def test_main_apply_refused_without_environment_gate(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(inventory.APPLY_ENV, raising=False)

    assert inventory.main(["--apply"]) == 2
    assert "LU_HOME_SESSION_APPLY=1" in capsys.readouterr().err
