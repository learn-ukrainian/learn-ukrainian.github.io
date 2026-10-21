"""Unit and integration tests for repository root resolver and primary checkout anchoring."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.common.repo_root import main_checkout_root, project_interpreter


def test_main_checkout_root_resolves_primary_checkout_from_worktree(tmp_path):
    """Verify that main_checkout_root correctly identifies primary repo root from a worktree."""
    main_repo = tmp_path / "main"
    worktree = main_repo / ".worktrees" / "dispatch" / "agy" / "task-123"
    git_dir = main_repo / ".git" / "worktrees" / "task-123"

    git_dir.mkdir(parents=True)
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n")

    assert main_checkout_root(worktree) == main_repo


@pytest.fixture
def wt_layout(tmp_path) -> tuple[Path, Path]:
    """Sets up a mock primary repo and a mock worktree layout.

    Returns a tuple of (mock_primary_root, mock_worktree_root).
    """
    main_repo = tmp_path / "main"
    worktree = main_repo / ".worktrees" / "dispatch" / "agy" / "task-123"
    git_dir = main_repo / ".git" / "worktrees" / "task-123"

    git_dir.mkdir(parents=True)
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n")

    # Copy the bridge and common module code files to the mock worktree
    src_root = Path(__file__).resolve().parents[1]

    # Create empty init for the bridge package to avoid loading other bridge modules
    bridge_init = worktree / "scripts" / "ai_agent_bridge" / "__init__.py"
    bridge_init.parent.mkdir(parents=True, exist_ok=True)
    bridge_init.write_text("", encoding="utf-8")

    files_to_copy = [
        "scripts/common/__init__.py",
        "scripts/common/bridge_paths.py",
        "scripts/common/repo_root.py",
        "scripts/common/github_client.py",
        "scripts/ai_agent_bridge/_config.py",
        "scripts/ai_agent_bridge/_env.py",
        "scripts/ai_agent_bridge/_dispatch_wrappers.py",
        "scripts/ai_agent_bridge/_monitor_cache.py",
        "scripts/review/__init__.py",
        "scripts/review/verdict_parser.py",
    ]
    for f in files_to_copy:
        dest = worktree / f
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text((src_root / f).read_text(encoding="utf-8"), encoding="utf-8")

    return main_repo, worktree


def test_bridge_config_state_paths_resolve_to_primary_in_worktree(wt_layout):
    """Verify that importing _config.py from a worktree layout resolves state paths to the primary root."""
    main_repo, worktree = wt_layout

    # Run subprocess to check DB_PATH and PID_DIR
    script = "from scripts.ai_agent_bridge._config import DB_PATH, PID_DIR; print(f'{DB_PATH};{PID_DIR}')"
    env = os.environ.copy()
    env.pop("AB_DB_PATH", None)  # Exercise the default path, not the suite's isolated override.
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(worktree),
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    db_path_str, pid_dir_str = proc.stdout.strip().split(";")

    expected_db_path = main_repo / ".mcp" / "servers" / "message-broker" / "messages.db"
    expected_pid_dir = main_repo / ".mcp" / "servers" / "message-broker" / "pids"

    assert Path(db_path_str).resolve() == expected_db_path.resolve()
    assert Path(pid_dir_str).resolve() == expected_pid_dir.resolve()


def _write_venv_python(checkout: Path, name: str = "python") -> Path:
    interpreter = checkout / ".venv" / "bin" / name
    interpreter.parent.mkdir(parents=True, exist_ok=True)
    interpreter.write_text("", encoding="utf-8")
    return interpreter


def _link_worktree(primary: Path, worktree: Path) -> None:
    git_dir = primary / ".git" / "worktrees" / "task"
    git_dir.mkdir(parents=True, exist_ok=True)
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n", encoding="utf-8")


def test_project_interpreter_rejects_another_checkouts_venv(tmp_path, monkeypatch):
    """An explicit root must not inherit a different checkout's interpreter.

    ``scripts.api.batch_router`` passes ``live_repo_root`` to
    ``project_interpreter`` (the dispatcher scan command). A missing checkout
    used to accept any running ``sys.executable`` ending in ``.venv/bin/python``,
    so ``project_interpreter(Path("/no-such-checkout"))`` returned this repo's
    interpreter.
    """
    foreign = _write_venv_python(tmp_path / "other-checkout")
    monkeypatch.setattr(sys, "executable", str(foreign))

    with pytest.raises(FileNotFoundError, match="not the requested checkout"):
        project_interpreter(Path("/no-such-checkout"))


def _toolchain_python(tmp_path: Path) -> Path:
    toolchain = tmp_path / "toolchain" / "python3.12"
    toolchain.parent.mkdir(parents=True, exist_ok=True)
    toolchain.write_text("", encoding="utf-8")
    return toolchain


def _symlink_venv_python(checkout: Path, target: Path, name: str = "python3.12") -> Path:
    interpreter = checkout / ".venv" / "bin" / name
    interpreter.parent.mkdir(parents=True, exist_ok=True)
    interpreter.symlink_to(target)
    return interpreter


def _symlink_checkout_venv_to_store(checkout: Path, store: Path, toolchain: Path) -> Path:
    """Point ``checkout/.venv`` at ``store`` and return the ``python3.12`` entry.

    The store has no ``bin/python``, so resolution cannot stop at the early
    ``.venv/bin/python`` match and has to classify ``sys.executable``.
    """
    entry = store / "bin" / "python3.12"
    entry.parent.mkdir(parents=True)
    entry.symlink_to(toolchain)
    checkout.mkdir(parents=True, exist_ok=True)
    venv = checkout / ".venv"
    venv.symlink_to(os.path.relpath(store, checkout))
    executable = venv / "bin" / "python3.12"
    assert venv.is_symlink()
    assert executable.parent.parent.name == ".venv"
    assert not (store / "bin" / "python").exists()
    assert Path(os.path.realpath(executable.parent)).parent == store.resolve()
    return executable


@pytest.mark.parametrize("shape", ["direct", "alias-to-venv", "venv-to-store", "alias-to-venv-to-store"])
@pytest.mark.parametrize("own_venv", [False, True], ids=["foreign-refused", "own-accepted"])
def test_project_interpreter_classifies_each_venv_symlink_shape(tmp_path, monkeypatch, shape, own_venv):
    """Every intermediate .venv owner counts, including one hidden by a second hop."""
    requested = tmp_path / "requested"
    owner = requested if own_venv else tmp_path / "foreign"
    toolchain = _toolchain_python(tmp_path)
    if shape in {"venv-to-store", "alias-to-venv-to-store"}:
        executable = _symlink_checkout_venv_to_store(owner, tmp_path / "store", toolchain)
    else:
        executable = _symlink_venv_python(owner, toolchain)
    if shape in {"alias-to-venv", "alias-to-venv-to-store"}:
        alias = tmp_path / "venv-alias"
        alias.symlink_to(owner / ".venv")
        executable = alias / "bin" / "python3.12"
    monkeypatch.setattr(sys, "executable", str(executable))

    if own_venv:
        assert project_interpreter(requested) == executable
    else:
        with pytest.raises(FileNotFoundError, match="not the requested checkout"):
            project_interpreter(requested)


def test_project_interpreter_refuses_directory_symlink_loop(tmp_path, monkeypatch):
    """A loop cannot be mistaken for hosted Python, even without a named owner."""
    alias_a = tmp_path / "alias-a"
    alias_b = tmp_path / "alias-b"
    alias_a.symlink_to(alias_b)
    alias_b.symlink_to(alias_a)
    monkeypatch.setattr(sys, "executable", str(alias_a / "bin" / "python3.12"))

    with pytest.raises(FileNotFoundError, match=r"^project interpreter not found: .* is a symlink loop$"):
        project_interpreter(tmp_path / "requested")


def test_project_interpreter_refuses_an_unreadable_path_component(tmp_path, monkeypatch):
    """A PermissionError in the walk reaches callers as FileNotFoundError (#9201)."""
    blocked = tmp_path / "blocked"
    executable = blocked / "bin" / "python3.12"
    executable.parent.mkdir(parents=True)
    executable.touch()
    real_lstat = os.lstat

    def lstat(path, *args, **kwargs):
        if Path(path) == blocked:
            raise PermissionError(13, "Permission denied", str(path))
        return real_lstat(path, *args, **kwargs)

    monkeypatch.setattr(os, "lstat", lstat)
    monkeypatch.setattr(sys, "executable", str(executable))

    with pytest.raises(FileNotFoundError, match=r"^project interpreter not found: .* cannot be inspected: ") as excinfo:
        project_interpreter(tmp_path / "requested")
    assert isinstance(excinfo.value.__cause__, PermissionError)


def test_project_interpreter_refuses_a_final_link_that_vanishes_before_readlink(tmp_path, monkeypatch):
    """A race on the final readlink fails closed instead of reading as hosted Python (#9201)."""
    toolchain = _toolchain_python(tmp_path)
    alias = tmp_path / "hosted" / "python3.12"
    alias.parent.mkdir()
    alias.symlink_to(toolchain)
    real_readlink = os.readlink

    def readlink(path, *args, **kwargs):
        if Path(path) == alias:
            raise FileNotFoundError(2, "No such file or directory", str(path))
        return real_readlink(path, *args, **kwargs)

    monkeypatch.setattr(os, "readlink", readlink)
    monkeypatch.setattr(sys, "executable", str(alias))

    with pytest.raises(FileNotFoundError, match=r"^project interpreter not found: .* cannot be inspected: "):
        project_interpreter(tmp_path / "requested")


def test_project_interpreter_rejects_another_checkouts_versioned_python(tmp_path, monkeypatch):
    """A missing checkout must not inherit another checkout's ``python3.12``.

    The ownership check used to allow only ``python`` and ``python3``, so
    ``.venv/bin/python3.12`` was returned as if it were a hosted interpreter.
    """
    foreign = _write_venv_python(tmp_path / "other-checkout", "python3.12")
    monkeypatch.setattr(sys, "executable", str(foreign))

    with pytest.raises(FileNotFoundError, match="not the requested checkout"):
        project_interpreter(Path("/no-such-checkout"))


def test_project_interpreter_rejects_a_symlink_that_resolves_into_another_checkouts_venv(tmp_path, monkeypatch):
    """A symlink outside ``.venv/bin`` counts when its target is that entrypoint."""
    foreign = _write_venv_python(tmp_path / "other-checkout", "python3.12")
    alias = tmp_path / "runner"
    alias.symlink_to(Path("other-checkout") / ".venv" / "bin" / "python3.12")
    assert alias.resolve() == foreign.resolve()
    monkeypatch.setattr(sys, "executable", str(alias))

    with pytest.raises(FileNotFoundError, match="not the requested checkout"):
        project_interpreter(Path("/no-such-checkout"))


def test_project_interpreter_rejects_when_parent_resolution_names_another_checkout(tmp_path, monkeypatch):
    """View U may name the requested checkout while view R names a foreign one.

    ``requested/.venv`` points at ``foreign/.venv``. The unresolved path names
    the requested checkout; parent resolution names the foreign checkout. Any
    foreign owner is refused.
    """
    foreign = tmp_path / "foreign-checkout"
    _symlink_venv_python(foreign, _toolchain_python(tmp_path))
    requested = tmp_path / "requested"
    requested.mkdir()
    (requested / ".venv").symlink_to(Path("..") / "foreign-checkout" / ".venv")
    executable = requested / ".venv" / "bin" / "python3.12"
    assert executable.parent.parent.name == ".venv"
    assert Path(os.path.realpath(executable.parent)) == (foreign / ".venv" / "bin").resolve()
    assert not (requested / ".venv" / "bin" / "python").exists()
    monkeypatch.setattr(sys, "executable", str(executable))

    with pytest.raises(FileNotFoundError, match="not the requested checkout"):
        project_interpreter(requested)


def test_project_interpreter_accepts_the_requested_worktree_venv_when_primary_has_none(tmp_path, monkeypatch):
    """(b) When the primary checkout has no ``.venv``, the worktree's own interpreter is used."""
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees" / "dispatch" / "grok" / "task"
    _link_worktree(primary, worktree)
    local = _write_venv_python(worktree)
    foreign = _write_venv_python(tmp_path / "other-checkout")
    monkeypatch.setattr(sys, "executable", str(foreign))

    assert project_interpreter(worktree) == local


def test_project_interpreter_prefers_the_primary_checkout_venv(tmp_path, monkeypatch):
    """(a) The primary checkout's ``.venv/bin/python`` wins when the worktree also has one."""
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees" / "dispatch" / "grok" / "task"
    _link_worktree(primary, worktree)
    primary_python = _write_venv_python(primary)
    _write_venv_python(worktree)
    foreign = _write_venv_python(tmp_path / "other-checkout")
    monkeypatch.setattr(sys, "executable", str(foreign))

    assert project_interpreter(worktree) == primary_python


def test_project_interpreter_uses_the_primary_venv_when_the_checkout_has_none(tmp_path, monkeypatch):
    """(a) A linked worktree with no ``.venv`` uses the primary checkout's interpreter."""
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees" / "dispatch" / "grok" / "task"
    _link_worktree(primary, worktree)
    primary_python = _write_venv_python(primary)
    foreign = _write_venv_python(tmp_path / "other-checkout")
    monkeypatch.setattr(sys, "executable", str(foreign))

    assert project_interpreter(worktree) == primary_python
