"""Dispatch dependencies must be present without overwriting or escaping either checkout."""

import errno
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.dispatcher import environment, git
from scripts.dispatcher.types import TaskSpec
from scripts.orchestration.worktree_artifacts import is_disposable_path
from scripts.storage.topology import STORE_FILES

LINKS = (*(f"data/{STORE_FILES[store][0]}" for store in ("sources", "vesum")), "node_modules", "site/node_modules")


@pytest.fixture
def layout(tmp_path):
    primary, worktree = tmp_path / "primary", tmp_path / "worktree"
    primary.mkdir()
    worktree.mkdir()
    for relative in LINKS:
        target = primary / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative.endswith(".db"):
            target.write_text("database sentinel")
        else:
            target.mkdir()
    return primary, worktree


def run_git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


@pytest.mark.parametrize("full_checkout", [False, True])
def test_creation_and_recreation_provision_clean_reapable_links(layout, full_checkout):
    """Missing dependencies, dirty ignored links, and fix-round omissions must fail."""
    primary, _unused = layout
    run_git(primary, "init", "-b", "main")
    run_git(primary, "config", "user.name", "Fixture")
    run_git(primary, "config", "user.email", "fixture@example.invalid")
    ignore = Path(__file__).resolve().parents[2] / ".gitignore"
    (primary / ".gitignore").write_bytes(ignore.read_bytes())
    run_git(primary, "add", ".gitignore")
    run_git(primary, "commit", "-m", "fixture")
    sha = run_git(primary, "rev-parse", "HEAD")
    worktree = primary / ".worktrees/dispatch/codex/fixture"
    for round_number in range(2):
        git.create_worktree(primary, worktree, f"codex/fixture-{round_number}", sha, full_checkout=full_checkout)
        git.provision_links(primary, worktree)
        for relative in LINKS:
            link = worktree / relative
            assert link.is_symlink()
            assert link.readlink() == primary / relative
            assert run_git(worktree, "check-ignore", relative) == relative
            assert is_disposable_path(Path(relative), worktree=worktree, primary=primary)
        assert run_git(worktree, "status", "--porcelain") == ""
        run_git(primary, "worktree", "remove", str(worktree))
        assert (primary / "data/sources.db").read_text() == "database sentinel"
        assert (primary / "node_modules").is_dir()
        assert not (primary / "node_modules").is_symlink()


@pytest.mark.parametrize("kind", ["file", "directory", "link", "dangling"])
def test_existing_destination_is_never_overwritten(layout, kind):
    """Provisioning must preserve real entries and both live and dangling links."""
    primary, worktree = layout
    entry = worktree / "node_modules"
    if kind == "file":
        entry.write_text("keep")
    elif kind == "directory":
        entry.mkdir()
    else:
        entry.symlink_to(primary / ("node_modules" if kind == "link" else "absent"))
    before = entry.lstat()
    git.provision_links(primary, worktree)
    assert entry.lstat() == before


def test_missing_targets_are_not_linked(tmp_path):
    """Absent primary dependencies must not become dangling worktree links."""
    primary, worktree = tmp_path / "primary", tmp_path / "worktree"
    primary.mkdir()
    worktree.mkdir()
    git.provision_links(primary, worktree)
    assert list(worktree.iterdir()) == []


@pytest.mark.parametrize("side,relative", [("source", "node_modules"), ("source", "data"), ("destination", "data")])
def test_symlink_escape_is_refused(layout, tmp_path, side, relative):
    """Source symlinks and destination ancestor links must not escape checkout boundaries."""
    primary, worktree = layout
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sources.db").write_text("outside sentinel")
    root = primary if side == "source" else worktree
    entry = root / relative
    if entry.exists():
        entry.rename(root / "saved")
    entry.symlink_to(outside)
    git.provision_links(primary, worktree)
    assert (outside / "sources.db").read_text() == "outside sentinel"
    assert sorted(p.name for p in outside.iterdir()) == ["sources.db"]
    if side == "source":
        assert not (worktree / relative).exists()


def test_atomic_creation_preserves_racing_entry(layout, monkeypatch):
    """A competing creator between inspection and symlink creation must never lose its entry."""
    primary, worktree = layout
    original = git.os.symlink

    def competing_creator(source, destination, *, dir_fd):
        if destination == "node_modules" and source == primary / "node_modules":
            (worktree / "node_modules").write_text("racing writer")
        return original(source, destination, dir_fd=dir_fd)

    monkeypatch.setattr(git.os, "symlink", competing_creator)
    git.provision_links(primary, worktree)
    assert (worktree / "node_modules").read_text() == "racing writer"


def test_unexpected_io_failure_is_reported(layout, monkeypatch):
    """Permission and I/O failures must not silently produce incomplete provisioning."""
    primary, worktree = layout

    def denied(*args, **kwargs):
        raise PermissionError(errno.EACCES, "denied")

    monkeypatch.setattr(git.os, "symlink", denied)
    with pytest.raises(PermissionError):
        git.provision_links(primary, worktree)


@pytest.mark.parametrize("relative", ["node_modules", "site/node_modules"])
@pytest.mark.parametrize("tool,args", [("npm", ["install"]), ("npx", ["npm", "install"])])
def test_child_env_refuses_shared_install_without_changing_git_gh(layout, monkeypatch, relative, tool, args):
    """Dispatch PATH must guard shared installs without enabling legacy git/gh policies."""
    primary, worktree = layout
    git.provision_links(primary, worktree)
    target = primary / relative / "sentinel"
    target.write_text("keep")
    binaries = worktree.parent / "bin"
    binaries.mkdir()
    for name in ("npm", "npx"):
        binary = binaries / name
        binary.write_text(
            '#!/bin/sh\ncase "$*" in *install*) printf corrupted > node_modules/sentinel;; *) echo real-tool;; esac\n'
        )
        binary.chmod(0o755)
    original_path = os.pathsep.join(
        [str(binaries), *(entry for entry in os.get_exec_path() if not entry.endswith("/scripts/agent_runtime/shims"))]
    )
    monkeypatch.setenv("PATH", original_path)
    spec = TaskSpec("fixture", "codex", "stub", None, "workspace-write", worktree, worktree / "prompt", worktree / "final")
    env = environment.child_env(spec)
    result = subprocess.run(
        [tool, *args], cwd=worktree / Path(relative).parent, env=env, capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 1, result.stderr
    assert "shim refused" in result.stderr
    assert target.read_text() == "keep"
    assert sorted(path.name for path in target.parent.iterdir()) == ["sentinel"]
    shim_dir = Path(env["PATH"].split(os.pathsep)[0])
    assert sorted(path.name for path in shim_dir.iterdir()) == ["npm", "npx"]
    for name in ("git", "gh"):
        real = shutil.which(name, path=original_path)
        assert real is not None
        assert shutil.which(name, path=env["PATH"]) == real
    monkeypatch.setenv("PATH", env["PATH"])
    repeated = environment.child_env(spec)
    passthrough = subprocess.run(
        [tool, "--version"], cwd=worktree, env=repeated, capture_output=True, text=True, timeout=10
    )
    assert passthrough.returncode == 0, passthrough.stderr
    assert passthrough.stdout == "real-tool\n"


@pytest.mark.parametrize("missing", ["directory", "npm", "npx", "npm_guard.py", "interpreter"])
def test_unavailable_guard_skips_shared_install_links_only(layout, monkeypatch, caplog, missing):
    """Missing npm/npx protection must not expose the primary install to children."""
    primary, worktree = layout
    if missing == "directory":
        monkeypatch.setattr(environment, "_NPM_SHIMS", worktree / "missing-shims")
    else:
        runtime = Path(environment.__file__).resolve().parents[1] / "agent_runtime"
        unavailable = Path(sys.executable) if missing == "interpreter" else runtime / (
            f"shims/{missing}" if missing in ("npm", "npx") else missing
        )
        access = os.access
        monkeypatch.setattr(os, "access", lambda path, mode: path != unavailable and access(path, mode))
    git.provision_links(primary, worktree)
    for relative in LINKS:
        assert (worktree / relative).is_symlink() == relative.endswith(".db")
    assert "npm/npx guard unavailable" in caplog.text
    (worktree / "node_modules").symlink_to(primary / "node_modules")
    spec = TaskSpec("fixture", "codex", "stub", None, "workspace-write", worktree, worktree / "prompt", worktree / "final")
    with pytest.raises(ValueError, match="npm/npx guard unavailable"):
        environment.child_env(spec)


@pytest.mark.parametrize("tool", ["npm", "npx"])
@pytest.mark.parametrize("route", ["child", "legacy_path", "legacy_pinned"])
def test_foreign_dispatcher_shims_cannot_recurse(layout, monkeypatch, tool, route):
    """Nested dispatch and legacy lookup must reach real tools without wrapper recursion."""
    _primary, worktree = layout
    foreign = worktree.parent / "other/scripts/dispatcher/npm_shims"
    shutil.copytree(environment._NPM_SHIMS, foreign)
    runtime = Path(environment.__file__).resolve().parents[1] / "agent_runtime"
    (foreign.parents[1] / "agent_runtime").symlink_to(runtime, target_is_directory=True)
    binaries = worktree.parent / "bin"
    binaries.mkdir()
    binary = binaries / tool
    binary.write_text('#!/bin/sh\nprintf "real-tool\\n"\n')
    binary.chmod(0o755)
    original_path = os.pathsep.join([f"{foreign}/.", str(binaries), "/usr/bin", "/bin"])
    monkeypatch.setenv("PATH", original_path)
    spec = TaskSpec("fixture", "codex", "stub", None, "workspace-write", worktree, worktree / "prompt", worktree / "final")
    env = environment.child_env(spec)
    if route == "child":
        assert str(foreign) not in env["PATH"]
        assert str(foreign) not in env["AGENT_ORIGINAL_PATH"]
    else:
        env["AGENT_ORIGINAL_PATH"] = original_path
        if route == "legacy_pinned":
            env[f"AGENT_REAL_{tool.upper()}"] = str(foreign / tool)
    result = subprocess.run(
        [tool, "--version"], cwd=worktree, env=env, capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "real-tool\n"
