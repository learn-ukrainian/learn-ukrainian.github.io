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

    with pytest.raises(FileNotFoundError, match="symlink loop"):
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

    with pytest.raises(FileNotFoundError, match="cannot be inspected") as excinfo:
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

    with pytest.raises(FileNotFoundError, match="cannot be inspected"):
        project_interpreter(tmp_path / "requested")


def test_project_interpreter_refuses_a_final_path_that_vanishes_before_the_link_check(tmp_path, monkeypatch):
    """A path gone before the link check is refused, not accepted as hosted Python (#9201)."""
    vanished = tmp_path / "hosted" / "python3.12"
    vanished.parent.mkdir()
    vanished.symlink_to(_toolchain_python(tmp_path))
    vanished.unlink()
    monkeypatch.setattr(sys, "executable", str(vanished))

    with pytest.raises(FileNotFoundError, match="cannot be inspected") as excinfo:
        project_interpreter(tmp_path / "requested")
    assert isinstance(excinfo.value.__cause__, FileNotFoundError)


def test_project_interpreter_refuses_foreign_owner_after_own_venv_hop(tmp_path, monkeypatch):
    """An allowed first owner cannot hide a foreign owner later in the chain."""
    requested = tmp_path / "requested"
    foreign = tmp_path / "foreign"
    _symlink_checkout_venv_to_store(foreign, tmp_path / "store", _toolchain_python(tmp_path))
    requested.mkdir()
    (requested / ".venv").symlink_to(foreign / ".venv")
    executable = requested / ".venv" / "bin" / "python3.12"
    monkeypatch.setattr(sys, "executable", str(executable))

    with pytest.raises(FileNotFoundError, match="not the requested checkout"):
        project_interpreter(requested)


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


def test_project_interpreter_rejects_an_alias_directory_of_another_checkouts_venv(tmp_path, monkeypatch):
    """``venv-alias -> other/.venv`` still names that foreign interpreter.

    The entrypoint's own components are ``venv-alias/bin``, not ``.venv/bin``.
    ``python3.12`` is a symlink to the toolchain, so resolving the file itself
    would drop ``.venv``. Only the parent directory is resolved.
    """
    foreign_root = tmp_path / "other-checkout"
    _symlink_venv_python(foreign_root, _toolchain_python(tmp_path))
    alias = tmp_path / "venv-alias"
    alias.symlink_to(Path("other-checkout") / ".venv")
    executable = alias / "bin" / "python3.12"
    assert alias.is_symlink()
    assert executable.parent.parent.name != ".venv"
    assert Path(os.path.realpath(executable.parent)) == (foreign_root / ".venv" / "bin").resolve()
    monkeypatch.setattr(sys, "executable", str(executable))

    with pytest.raises(FileNotFoundError, match="not the requested checkout"):
        project_interpreter(Path("/no-such-checkout"))


def test_project_interpreter_rejects_a_foreign_venv_symlinked_to_a_store(tmp_path, monkeypatch):
    """``foreign-checkout/.venv -> venv-store`` still names that foreign checkout.

    Resolving the parent first lands in ``venv-store/bin`` and drops ``.venv``,
    so the path as given has to be classified too. ``python3.12`` is a symlink
    to the toolchain; following that file would drop ``.venv`` as well.
    """
    foreign = tmp_path / "foreign-checkout"
    executable = _symlink_checkout_venv_to_store(foreign, tmp_path / "venv-store", _toolchain_python(tmp_path))
    assert os.readlink(foreign / ".venv") == os.path.relpath(tmp_path / "venv-store", foreign)
    monkeypatch.setattr(sys, "executable", str(executable))

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


def test_project_interpreter_accepts_an_alias_directory_of_the_requested_checkouts_venv(tmp_path, monkeypatch):
    """A directory symlink onto the requested checkout's ``.venv`` is accepted.

    The checkout path is compared after the same parent-directory resolution,
    so a symlink in that checkout's parent still matches.
    """
    real_parent = tmp_path / "real-parent"
    linked_parent = tmp_path / "linked-parent"
    real_parent.mkdir()
    linked_parent.symlink_to(real_parent)
    requested = linked_parent / "requested"
    _symlink_venv_python(requested, _toolchain_python(tmp_path))
    alias = tmp_path / "venv-alias"
    alias.symlink_to(Path("linked-parent") / "requested" / ".venv")
    executable = alias / "bin" / "python3.12"
    assert alias.is_symlink()
    assert executable.parent.parent.name != ".venv"
    monkeypatch.setattr(sys, "executable", str(executable))

    assert project_interpreter(requested) == executable


def test_project_interpreter_accepts_an_alias_directory_of_the_primary_checkout(tmp_path, monkeypatch):
    """A linked worktree may run through a directory symlink onto the primary ``.venv``."""
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees" / "dispatch" / "grok" / "task"
    _link_worktree(primary, worktree)
    _symlink_venv_python(primary, _toolchain_python(tmp_path))
    alias = tmp_path / "venv-alias"
    alias.symlink_to(Path("primary") / ".venv")
    executable = alias / "bin" / "python3.12"
    assert alias.is_symlink()
    monkeypatch.setattr(sys, "executable", str(executable))

    assert project_interpreter(worktree) == executable


def test_project_interpreter_accepts_the_requested_venv_symlinked_to_a_store(tmp_path, monkeypatch):
    """The requested checkout's ``.venv -> venv-store`` is still that checkout.

    Parent resolution drops ``.venv``, but the path as given names the
    requested checkout, and the store directory is not itself a ``.venv``.
    """
    requested = tmp_path / "requested"
    executable = _symlink_checkout_venv_to_store(
        requested, tmp_path / "requested-venv-store", _toolchain_python(tmp_path)
    )
    monkeypatch.setattr(sys, "executable", str(executable))

    assert project_interpreter(requested) == executable


def test_project_interpreter_accepts_the_worktree_venv_symlinked_to_a_store(tmp_path, monkeypatch):
    """A linked worktree's own ``.venv -> venv-store`` is accepted when the primary has none."""
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees" / "dispatch" / "grok" / "task"
    _link_worktree(primary, worktree)
    executable = _symlink_checkout_venv_to_store(
        worktree, tmp_path / "worktree-venv-store", _toolchain_python(tmp_path)
    )
    monkeypatch.setattr(sys, "executable", str(executable))

    assert project_interpreter(worktree) == executable


def test_project_interpreter_accepts_the_primary_venv_symlinked_to_a_store(tmp_path, monkeypatch):
    """A linked worktree may run the primary ``.venv`` when that directory points at a store."""
    primary = tmp_path / "primary"
    worktree = primary / ".worktrees" / "dispatch" / "grok" / "task"
    _link_worktree(primary, worktree)
    executable = _symlink_checkout_venv_to_store(primary, tmp_path / "primary-venv-store", _toolchain_python(tmp_path))
    monkeypatch.setattr(sys, "executable", str(executable))

    assert project_interpreter(worktree) == executable


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
