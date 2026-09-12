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


@pytest.fixture
def python_skill(repo: Path) -> Path:
    relative = Path("example/scripts/bounded_completion.py")
    source = repo / "agents_extensions/shared/skills" / relative
    source.parent.mkdir()
    source.write_text("raise RuntimeError('must never execute during migration')\n")
    subprocess.run(["git", "add", "agents_extensions"], cwd=repo, check=True, timeout=30)
    legacy = repo / ".codex/skills" / relative
    legacy.parent.mkdir()
    legacy.write_bytes(source.read_bytes())
    cache = legacy.parent / "__pycache__"
    cache.mkdir()
    return cache


@pytest.mark.parametrize("name", [
    "bounded_completion.cpython-312.pyc",
    "bounded_completion.cpython-314.opt-1.pyc",
    "bounded_completion.pypy310.opt-foo.pyc",
])
@pytest.mark.parametrize("canonical_cache_exists", [False, True])
def test_python_runtime_cache_is_retained_without_execution(
    repo: Path, python_skill: Path, name: str, canonical_cache_exists: bool,
) -> None:
    if canonical_cache_exists:
        (repo / "agents_extensions/shared/skills/example/scripts/__pycache__").mkdir()
    cache = python_skill / name
    payload = b"Opaque runtime bytes, never load or unmarshal them"
    cache.write_bytes(payload)
    assert migration.migrate(repo, "verify") == 0
    assert migration.migrate(repo, "apply") == 0
    retained = captures(repo)[0] / cache.relative_to(repo / ".codex/skills")
    assert retained.read_bytes() == payload
    assert migration.migrate(repo, "apply") == 0
    assert retained.read_bytes() == payload


@pytest.mark.parametrize("name", [
    "bounded_completion.cpython-312.py",
    "bounded_completion..pyc",
    ".cpython-312.pyc",
    "missing.cpython-312.pyc",
    "bounded_completion.cpython-312.opt-!.pyc",
    "notes.txt",
])
def test_unknown_cache_content_is_preserved_and_rejected(repo: Path, python_skill: Path, name: str) -> None:
    cache = python_skill / name
    cache.write_bytes(b"User content")
    assert migration.migrate(repo, "apply") == 1
    assert cache.read_bytes() == b"User content"
    assert not captures(repo)


@pytest.mark.parametrize("unsafe", [
    "untracked", "source-symlink", "source-parent-symlink", "index-symlink",
    "cache-symlink", "cache-directory-symlink", "nested",
])
def test_runtime_cache_requires_regular_tracked_source_and_safe_entries(
    repo: Path, python_skill: Path, unsafe: str,
) -> None:
    source = repo / "agents_extensions/shared/skills/example/scripts/bounded_completion.py"
    cache = python_skill / "bounded_completion.cpython-312.pyc"
    cache.write_bytes(b"Runtime bytes")
    if unsafe == "untracked":
        subprocess.run(["git", "rm", "--cached", "-f", str(source)], cwd=repo, check=True, capture_output=True, timeout=30)
    elif unsafe == "source-parent-symlink":
        outside = repo / "outside-scripts"
        source.parent.rename(outside)
        source.parent.symlink_to(outside, target_is_directory=True)
    elif unsafe in ("source-symlink", "index-symlink"):
        content = source.read_bytes()
        source.unlink()
        outside = repo / "outside.py"
        outside.write_bytes(content)
        source.symlink_to(outside)
        if unsafe == "index-symlink":
            subprocess.run(["git", "add", str(source)], cwd=repo, check=True, timeout=30)
            source.unlink()
            source.write_bytes(content)
    elif unsafe == "cache-symlink":
        cache.unlink()
        cache.symlink_to(source)
    elif unsafe == "cache-directory-symlink":
        outside = repo / "outside-cache"
        python_skill.rename(outside)
        python_skill.symlink_to(outside, target_is_directory=True)
    else:
        (python_skill / "nested").mkdir()
    assert migration.migrate(repo, "apply") == 1
    assert python_skill.exists()
    assert not captures(repo)


def test_runtime_cache_write_during_capture_is_retained_with_error(
    repo: Path, python_skill: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = python_skill / "bounded_completion.cpython-312.pyc"
    cache.write_bytes(b"Runtime bytes")
    original = migration.rename_exclusive
    with cache.open("r+b", buffering=0) as writer:
        def capture_then_write(*args: object) -> None:
            original(*args)
            writer.seek(0)
            writer.write(b"Concurrent cache write")
            writer.truncate()

        monkeypatch.setattr(migration, "rename_exclusive", capture_then_write)
        assert migration.migrate(repo, "apply") == 1
    retained = captures(repo)[0] / cache.relative_to(repo / ".codex/skills")
    assert retained.read_bytes() == b"Concurrent cache write"


@pytest.mark.parametrize("ancestor", ["agents_extensions", "agents_extensions/shared"])
def test_runtime_cache_rejects_upper_canonical_source_symlink(
    repo: Path, python_skill: Path, ancestor: str,
) -> None:
    cache = python_skill / "bounded_completion.cpython-312.pyc"
    cache.write_bytes(b"Retain runtime bytes")
    canonical = repo / ancestor
    outside = repo.parent / "outside-source"
    canonical.rename(outside)
    canonical.symlink_to(outside, target_is_directory=True)
    relative = cache.relative_to(repo / ".codex/skills").as_posix()
    assert not migration.cache_source_is_tracked(repo, relative)
    assert migration.migrate(repo, "apply") == 1
    assert cache.read_bytes() == b"Retain runtime bytes"
    assert not captures(repo)


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
