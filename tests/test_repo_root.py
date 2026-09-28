"""Unit and integration tests for repository root resolver and primary checkout anchoring."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.common.repo_root import main_checkout_root, project_interpreter, resolve_repo_root


def test_main_checkout_root_resolves_primary_checkout_from_worktree(tmp_path):
    """Verify that main_checkout_root correctly identifies primary repo root from a worktree."""
    main_repo = tmp_path / "main"
    worktree = main_repo / ".worktrees" / "dispatch" / "agy" / "task-123"
    git_dir = main_repo / ".git" / "worktrees" / "task-123"

    git_dir.mkdir(parents=True)
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n")

    assert main_checkout_root(worktree) == main_repo


def test_main_checkout_root_is_identity_in_primary_checkout(tmp_path):
    """Verify that main_checkout_root is an identity function in a primary checkout."""
    main_repo = tmp_path / "main"
    (main_repo / ".git").mkdir(parents=True)

    assert main_checkout_root(main_repo) == main_repo


def test_resolve_repo_root_generalized_depths(tmp_path):
    """Verify resolve_repo_root with different parents/depth levels."""
    main_repo = tmp_path / "main"
    worktree = main_repo / ".worktrees" / "dispatch" / "agy" / "task-123"
    git_dir = main_repo / ".git" / "worktrees" / "task-123"

    git_dir.mkdir(parents=True)
    (worktree / "scripts" / "ai_agent_bridge").mkdir(parents=True)
    (worktree / ".git").write_text(f"gitdir: {git_dir}\n")

    # depth = 1 (scripts/delegate.py)
    dummy_delegate = worktree / "scripts" / "delegate.py"
    assert resolve_repo_root(dummy_delegate, 1) == main_repo

    # depth = 2 (scripts/ai_agent_bridge/_config.py)
    dummy_config = worktree / "scripts" / "ai_agent_bridge" / "_config.py"
    assert resolve_repo_root(dummy_config, 2) == main_repo


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
        "scripts/ai_agent_bridge/_config.py",
        "scripts/ai_agent_bridge/_env.py",
        "scripts/ai_agent_bridge/_dispatch_wrappers.py",
        "scripts/ai_agent_bridge/_monitor_cache.py",
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
    script = (
        "from scripts.ai_agent_bridge._config import DB_PATH, PID_DIR; "
        "print(f'{DB_PATH};{PID_DIR}')"
    )
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


def test_bridge_dispatch_wrappers_repo_root_resolves_to_primary_in_worktree(wt_layout):
    """Verify that importing _dispatch_wrappers.py from a worktree layout resolves REPO_ROOT to primary."""
    main_repo, worktree = wt_layout

    script = "from scripts.ai_agent_bridge._dispatch_wrappers import REPO_ROOT; print(REPO_ROOT)"
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(worktree),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    resolved_repo_root = Path(proc.stdout.strip())
    assert resolved_repo_root.resolve() == main_repo.resolve()


def test_bridge_monitor_cache_project_root_resolves_to_primary_in_worktree(wt_layout):
    """Verify that importing _monitor_cache.py from a worktree layout resolves _PROJECT_ROOT to primary."""
    main_repo, worktree = wt_layout

    script = "from scripts.ai_agent_bridge._monitor_cache import _PROJECT_ROOT; print(_PROJECT_ROOT)"
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(worktree),
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    resolved_project_root = Path(proc.stdout.strip())
    assert resolved_project_root.resolve() == main_repo.resolve()


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


def test_project_interpreter_accepts_running_python3_of_the_requested_checkout(tmp_path, monkeypatch):
    requested = tmp_path / "requested"
    python3 = _write_venv_python(requested, "python3")
    monkeypatch.setattr(sys, "executable", str(python3))

    assert project_interpreter(requested) == python3


def test_project_interpreter_accepts_running_python3_of_the_primary_checkout(tmp_path, monkeypatch):
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees" / "dispatch" / "grok" / "task"
    _link_worktree(primary, worktree)
    python3 = _write_venv_python(primary, "python3")
    monkeypatch.setattr(sys, "executable", str(python3))

    assert project_interpreter(worktree) == python3


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


def test_project_interpreter_rejects_another_checkouts_versioned_python(tmp_path, monkeypatch):
    """A missing checkout must not inherit another checkout's ``python3.12``.

    The ownership check used to allow only ``python`` and ``python3``, so
    ``.venv/bin/python3.12`` was returned as if it were a hosted interpreter.
    """
    foreign = _write_venv_python(tmp_path / "other-checkout", "python3.12")
    monkeypatch.setattr(sys, "executable", str(foreign))

    with pytest.raises(FileNotFoundError, match="not the requested checkout"):
        project_interpreter(Path("/no-such-checkout"))


def test_project_interpreter_rejects_a_versioned_symlink_out_of_another_checkouts_venv(tmp_path, monkeypatch):
    """``python3.12`` still belongs to its venv when the file is a symlink to the toolchain."""
    foreign = _symlink_venv_python(tmp_path / "other-checkout", _toolchain_python(tmp_path))
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


def test_project_interpreter_accepts_running_python3_12_of_the_requested_checkout(tmp_path, monkeypatch):
    """The requested checkout's own versioned entrypoint is accepted."""
    requested = tmp_path / "requested"
    python312 = _symlink_venv_python(requested, _toolchain_python(tmp_path))
    monkeypatch.setattr(sys, "executable", str(python312))

    assert project_interpreter(requested) == python312


def test_project_interpreter_accepts_running_python3_12_of_the_primary_checkout(tmp_path, monkeypatch):
    """A linked worktree may run on the primary checkout's ``python3.12``."""
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees" / "dispatch" / "grok" / "task"
    _link_worktree(primary, worktree)
    python312 = _symlink_venv_python(primary, _toolchain_python(tmp_path))
    monkeypatch.setattr(sys, "executable", str(python312))

    assert project_interpreter(worktree) == python312


def test_project_interpreter_accepts_a_symlink_into_the_requested_checkouts_venv(tmp_path, monkeypatch):
    """A symlink that resolves into the requested checkout's ``.venv/bin`` is accepted."""
    requested = tmp_path / "requested"
    python312 = _write_venv_python(requested, "python3.12")
    alias = tmp_path / "runner"
    alias.symlink_to(python312)
    monkeypatch.setattr(sys, "executable", str(alias))

    assert project_interpreter(requested) == alias


def test_project_interpreter_accepts_hosted_python3_12(tmp_path, monkeypatch):
    """A versioned interpreter outside any checkout ``.venv/bin`` is the CI fallback."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    hosted = tmp_path / "hostedtoolcache" / "Python" / "3.12.8" / "x64" / "bin" / "python3.12"
    hosted.parent.mkdir(parents=True)
    hosted.write_text("", encoding="utf-8")
    alias = tmp_path / "hosted-alias"
    alias.symlink_to(hosted)
    monkeypatch.setattr(sys, "executable", str(alias))

    assert project_interpreter(checkout) == alias


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


def test_project_interpreter_uses_sys_executable_when_no_project_venv_exists(tmp_path, monkeypatch):
    """(c) CI: no ``.venv`` anywhere, and ``sys.executable`` is not inside a checkout ``.venv``."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    ci_python = tmp_path / "hostedtoolcache" / "Python" / "3.12.8" / "x64" / "bin" / "python"
    ci_python.parent.mkdir(parents=True)
    ci_python.write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(ci_python))

    assert project_interpreter(checkout) == ci_python
