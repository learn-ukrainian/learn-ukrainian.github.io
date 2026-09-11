"""Adversarial capture tests: migration must never delete concurrent/user bytes."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.deploy import retire_codex_skills as migration

PAYLOAD = b"---\nname: example\ndescription: Example skill.\n---\nCanonical content.\n"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    source = root / "agents_extensions/shared/skills/example/SKILL.md"
    source.parent.mkdir(parents=True)
    source.write_bytes(PAYLOAD)
    for command in (
        ["git", "init", "-q"],
        ["git", "config", "user.name", "Migration test"],
        ["git", "config", "user.email", "migration@example.invalid"],
        ["git", "add", "agents_extensions"],
        ["git", "commit", "-qm", "source"],
    ):
        subprocess.run(command, cwd=root, check=True, capture_output=True, timeout=30)
    active = root / ".codex/skills/example/SKILL.md"
    active.parent.mkdir(parents=True)
    active.write_bytes(PAYLOAD)
    return root


def captures(root: Path) -> list[Path]:
    return sorted((root / ".codex/retired-skills").glob("*/skills"))


def test_capture_is_retained_and_repeated_run_never_removes_backup(repo: Path) -> None:
    assert migration.migrate(repo, "apply") == 0
    retained = captures(repo)
    assert len(retained) == 1
    assert not (repo / ".codex/skills").exists()
    assert (retained[0] / "example/SKILL.md").read_bytes() == PAYLOAD
    assert migration.migrate(repo, "apply") == 0
    assert captures(repo) == retained
    assert (retained[0] / "example/SKILL.md").read_bytes() == PAYLOAD


@pytest.mark.parametrize("replace", [False, True])
def test_modified_or_replaced_file_before_capture_is_retained_and_reports_error(
    repo: Path, monkeypatch: pytest.MonkeyPatch, replace: bool,
) -> None:
    original = migration.rename_exclusive
    active = repo / ".codex/skills/example/SKILL.md"

    def edit_then_capture(*args: object) -> None:
        if replace:
            new_file = active.with_suffix(".replacement")
            new_file.write_bytes(b"User replacement")
            os.replace(new_file, active)
        else:
            active.write_bytes(b"User edit")
        original(*args)

    monkeypatch.setattr(migration, "rename_exclusive", edit_then_capture)
    assert migration.migrate(repo, "apply") == 1
    expected = b"User replacement" if replace else b"User edit"
    assert (captures(repo)[0] / "example/SKILL.md").read_bytes() == expected


def test_open_file_descriptor_write_after_success_survives(repo: Path) -> None:
    with (repo / ".codex/skills/example/SKILL.md").open("r+b", buffering=0) as writer:
        assert migration.migrate(repo, "apply") == 0
        writer.seek(0)
        writer.write(b"Late writer content")
        writer.truncate()
    retained = captures(repo)[0] / "example/SKILL.md"
    assert retained.read_bytes() == b"Late writer content"
    assert migration.migrate(repo, "apply") == 0
    assert retained.read_bytes() == b"Late writer content"


def test_open_file_descriptor_write_during_capture_survives_with_error(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = migration.rename_exclusive
    with (repo / ".codex/skills/example/SKILL.md").open("r+b", buffering=0) as writer:
        def capture_then_write(*args: object) -> None:
            original(*args)
            writer.seek(0)
            writer.write(b"Concurrent writer content")
            writer.truncate()

        monkeypatch.setattr(migration, "rename_exclusive", capture_then_write)
        assert migration.migrate(repo, "apply") == 1
    assert (captures(repo)[0] / "example/SKILL.md").read_bytes() == b"Concurrent writer content"


@pytest.mark.parametrize("component", [".codex", ".codex/skills", ".codex/skills/example"])
@pytest.mark.parametrize("during_capture", [False, True])
def test_symlink_swaps_never_touch_external_victim(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component: str, during_capture: bool,
) -> None:
    external = tmp_path / "external"
    external.mkdir()
    (external / "SKILL.md").write_bytes(b"External victim")
    original = migration.rename_exclusive
    saved = repo / "saved-original"

    def swap() -> None:
        target = repo / component
        target.rename(saved)
        target.symlink_to(external, target_is_directory=True)

    def swap_then_capture(*args: object) -> None:
        swap()
        original(*args)

    if during_capture:
        monkeypatch.setattr(migration, "rename_exclusive", swap_then_capture)
    else:
        swap()
    assert migration.migrate(repo, "apply") == 1
    assert (external / "SKILL.md").read_bytes() == b"External victim"
    assert sorted(p.name for p in external.iterdir()) == ["SKILL.md"]
    # The source tree is never reaped, even when its former name is redirected.
    assert saved.exists()
    assert any(p.read_bytes() == PAYLOAD for p in saved.rglob("SKILL.md"))


def test_recreated_active_tree_is_preserved_and_reported(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = migration.rename_exclusive

    def capture_then_recreate(*args: object) -> None:
        original(*args)
        recreated = repo / ".codex/skills/local/SKILL.md"
        recreated.parent.mkdir(parents=True)
        recreated.write_bytes(b"New local skill")

    monkeypatch.setattr(migration, "rename_exclusive", capture_then_recreate)
    assert migration.migrate(repo, "apply") == 1
    assert (repo / ".codex/skills/local/SKILL.md").read_bytes() == b"New local skill"
    assert (captures(repo)[0] / "example/SKILL.md").read_bytes() == PAYLOAD


def test_interruption_after_capture_and_retry_preserve_backup(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = migration.rename_exclusive

    def capture_then_interrupt(*args: object) -> None:
        original(*args)
        raise KeyboardInterrupt

    monkeypatch.setattr(migration, "rename_exclusive", capture_then_interrupt)
    with pytest.raises(KeyboardInterrupt):
        migration.migrate(repo, "apply")
    retained = captures(repo)
    assert len(retained) == 1
    monkeypatch.setattr(migration, "rename_exclusive", original)
    assert migration.migrate(repo, "apply") == 0
    assert captures(repo) == retained
    assert (retained[0] / "example/SKILL.md").read_bytes() == PAYLOAD


def test_rename_failure_preserves_source_and_prior_backups(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    previous = repo / ".codex/retired-skills/previous/skills/local"
    previous.mkdir(parents=True)
    (previous / "SKILL.md").write_bytes(b"Previous user backup")

    def refuse(*args: object) -> None:
        raise OSError("Injected rename failure")

    monkeypatch.setattr(migration, "rename_exclusive", refuse)
    assert migration.migrate(repo, "apply") == 1
    assert (repo / ".codex/skills/example/SKILL.md").read_bytes() == PAYLOAD
    assert (previous / "SKILL.md").read_bytes() == b"Previous user backup"


def test_capture_name_collision_never_reuses_backup(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fixed = migration.uuid.UUID("11111111111141118111111111111111")
    previous = repo / ".codex/retired-skills" / fixed.hex
    previous.mkdir(parents=True)
    (previous / "marker").write_bytes(b"Retain me")
    monkeypatch.setattr(migration.uuid, "uuid4", lambda: fixed)
    assert migration.migrate(repo, "apply") == 1
    assert (previous / "marker").read_bytes() == b"Retain me"
    assert (repo / ".codex/skills/example/SKILL.md").read_bytes() == PAYLOAD


def test_exclusive_rename_refuses_existing_destination(repo: Path) -> None:
    target = repo / "existing"
    target.mkdir()
    # Even an empty destination must never be overwritten.
    with context_directory(repo) as root_fd:
        with pytest.raises(OSError):
            migration.rename_exclusive(root_fd, ".codex/skills", root_fd, "existing")
    assert target.is_dir()
    assert (repo / ".codex/skills/example/SKILL.md").read_bytes() == PAYLOAD


class context_directory:
    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self) -> int:
        self.fd = os.open(self.path, migration.DIRECTORY_FLAGS)
        return self.fd

    def __exit__(self, *args: object) -> None:
        os.close(self.fd)


def test_git_probe_timeout_preserves_active_content(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("git provenance", 30)

    monkeypatch.setattr(migration.subprocess, "run", timeout)
    assert migration.migrate(repo, "apply") == 1
    assert (repo / ".codex/skills/example/SKILL.md").read_bytes() == PAYLOAD
    assert captures(repo) == []


def test_replaced_discovery_tree_is_retained_with_original_untouched(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = migration.rename_exclusive
    active = repo / ".codex/skills"
    saved = repo / ".codex/original-tree"

    def replace_then_capture(*args: object) -> None:
        active.rename(saved)
        (active / "example").mkdir(parents=True)
        (active / "example/SKILL.md").write_bytes(PAYLOAD)
        original(*args)

    monkeypatch.setattr(migration, "rename_exclusive", replace_then_capture)
    assert migration.migrate(repo, "apply") == 1
    assert (saved / "example/SKILL.md").read_bytes() == PAYLOAD
    assert (captures(repo)[0] / "example/SKILL.md").read_bytes() == PAYLOAD
