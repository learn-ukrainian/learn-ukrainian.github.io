"""Tests for the git-level primary-checkout ref guard (.githooks/).

Incident class (#5389 / #5396, 2026-07-25): a dispatch worker on a harness
WITHOUT PreToolUse hooks reached out of its worktree and detached the primary
checkout (``checkout: moving from main to FETCH_HEAD``). The fix lives in git
itself: a tracked ``.githooks/reference-transaction`` hook (core.hooksPath is
already set) that vetoes protected-ref moves, plus a ``.githooks/post-checkout``
that makes the previously-shadowed stay-on-main heal actually run.

These tests build a scratch repo + linked worktree per test and exercise the
hooks with the REAL git binary (the repo's agent_runtime git shim is filtered
from PATH): no harness, no shim, exactly the incident's bypass conditions.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_SRC = REPO_ROOT / ".githooks"
OVERRIDE_ENV = "LEARN_UK_ALLOW_PRIMARY_REF_WRITE"


def _real_git() -> str:
    """Absolute path of the real git binary, skipping the agent_runtime shim."""
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if "scripts/agent_runtime/shims" in entry:
            continue
        candidate = Path(entry) / "git"
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    pytest.skip("no real git binary found on PATH")


GIT = _real_git()


def _run(
    args: list[str],
    cwd: Path | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    # Neutralize shim/agent toggles so only the git hooks under test act.
    for key in ("AGENT_NO_MERGE", "AGENT_GIT_SHIM_GUARD_ACTIVE"):
        env.pop(key, None)
    env.pop(OVERRIDE_ENV, None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [GIT, *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


@pytest.fixture()
def scratch_repo(tmp_path: Path) -> dict[str, Path]:
    """A scratch repo on `main` with the tracked .githooks/ installed.

    Returns {"primary": <path>}. The hooks are committed into the repo so
    linked worktrees (created later by tests) carry them too.
    """
    primary = tmp_path / "primary"
    primary.mkdir()
    assert _run(["init", "-q", "-b", "main"], cwd=primary).returncode == 0
    _run(["config", "user.email", "test@example.invalid"], cwd=primary)
    _run(["config", "user.name", "Test User"], cwd=primary)
    (primary / "f").write_text("a\n", encoding="utf-8")
    assert _run(["add", "f"], cwd=primary).returncode == 0
    assert _run(["commit", "-qm", "init"], cwd=primary).returncode == 0

    hooks_dst = primary / ".githooks"
    shutil.copytree(HOOKS_SRC, hooks_dst)
    for hook in hooks_dst.iterdir():
        hook.chmod(hook.stat().st_mode | stat.S_IXUSR)
    assert _run(["add", ".githooks"], cwd=primary).returncode == 0
    assert _run(["commit", "-qm", "add githooks"], cwd=primary).returncode == 0
    assert _run(["config", "core.hooksPath", ".githooks"], cwd=primary).returncode == 0
    return {"primary": primary}


def _add_worktree(primary: Path, name: str = "wt1") -> Path:
    wt = primary.parent / name
    proc = _run(["-C", str(primary), "worktree", "add", "-q", str(wt), "-b", f"{name}-branch"])
    assert proc.returncode == 0, proc.stderr
    return wt


def _head_branch(repo: Path) -> str:
    proc = _run(["-C", str(repo), "symbolic-ref", "--quiet", "--short", "HEAD"])
    return proc.stdout.strip()


def _head_sha(repo: Path) -> str:
    proc = _run(["-C", str(repo), "rev-parse", "HEAD"])
    assert proc.returncode == 0
    return proc.stdout.strip()


# ---------------------------------------------------------------------------
# worker-style reach-across is refused
# ---------------------------------------------------------------------------


def test_worker_detach_of_primary_from_worktree_is_refused(scratch_repo):
    """The exact 2026-07-25 incident: from a worktree, detach the primary."""
    primary = scratch_repo["primary"]
    wt = _add_worktree(primary)
    sha = _head_sha(primary)

    proc = _run(["-C", str(primary), "checkout", sha], cwd=wt)

    assert proc.returncode != 0, "worker-style detach of the primary must be refused"
    assert "BLOCKED by .githooks/reference-transaction" in proc.stderr
    assert OVERRIDE_ENV in proc.stderr  # block message names the override
    assert _head_branch(primary) == "main"  # primary untouched


def test_main_tip_update_ref_from_worktree_is_refused(scratch_repo):
    """A worker moving refs/heads/main directly is refused from any context."""
    primary = scratch_repo["primary"]
    wt = _add_worktree(primary)
    wt_sha = _head_sha(wt)  # == main's sha; craft a second commit to move to
    (wt / "f").write_text("b\n", encoding="utf-8")
    assert _run(["commit", "-qam", "c2"], cwd=wt).returncode == 0
    new_sha = _head_sha(wt)

    proc = _run(
        ["-C", str(primary), "update-ref", "refs/heads/main", new_sha], cwd=wt
    )

    assert proc.returncode != 0
    assert "BLOCKED by .githooks/reference-transaction" in proc.stderr


def test_commit_on_main_in_primary_blocked_when_non_interactive(scratch_repo):
    """Non-interactive commit directly on main in the primary is refused."""
    primary = scratch_repo["primary"]

    proc = _run(["commit", "--allow-empty", "-m", "agent-commit"], cwd=primary)

    assert proc.returncode != 0
    assert "BLOCKED by .githooks/reference-transaction" in proc.stderr
    assert _head_branch(primary) == "main"


# ---------------------------------------------------------------------------
# operator escape hatches
# ---------------------------------------------------------------------------


def test_override_env_allows_intentional_operator_action(scratch_repo):
    """LEARN_UK_ALLOW_PRIMARY_REF_WRITE=1 re-enables scripted operator flows."""
    primary = scratch_repo["primary"]
    wt = _add_worktree(primary)
    sha = _head_sha(primary)

    proc = _run(
        ["-C", str(primary), "checkout", sha],
        cwd=wt,
        env_extra={OVERRIDE_ENV: "1"},
    )

    assert proc.returncode == 0, proc.stderr
    assert _head_branch(primary) == ""  # detached, as the operator intended

    # Cleanup: re-attach under the override too (would otherwise be allowed
    # anyway — symref retarget to main is never blocked).
    heal = _run(["-C", str(primary), "checkout", "main"])
    assert heal.returncode == 0, heal.stderr
    assert _head_branch(primary) == "main"


def test_interactive_tty_is_never_blocked(scratch_repo):
    """A human at a terminal (TTY on stdout/stderr) keeps full control."""
    primary = scratch_repo["primary"]

    import pty

    env = os.environ.copy()
    env.pop(OVERRIDE_ENV, None)
    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen(
            [GIT, "commit", "--allow-empty", "-m", "operator-commit"],
            cwd=str(primary),
            stdin=subprocess.DEVNULL,
            stdout=slave,
            stderr=slave,
            env=env,
        )
        os.close(slave)
        slave = -1
        while True:
            try:
                if not os.read(master, 1024):
                    break
            except OSError:  # EIO: slave side closed
                break
        rc = proc.wait(timeout=30)
    finally:
        os.close(master)
        if slave >= 0:
            os.close(slave)

    assert rc == 0, "interactive (TTY) operator action must not be blocked"


# ---------------------------------------------------------------------------
# normal worktree operations are unaffected
# ---------------------------------------------------------------------------


def test_worktree_operations_unaffected(scratch_repo):
    """Commits, detaches, and further worktree adds inside worktrees pass."""
    primary = scratch_repo["primary"]
    wt = _add_worktree(primary)

    # commit on the worktree branch
    (wt / "f").write_text("work\n", encoding="utf-8")
    proc = _run(["commit", "-qam", "worktree commit"], cwd=wt)
    assert proc.returncode == 0, proc.stderr

    # detach inside the worktree (agents detach their own trees freely)
    proc = _run(["checkout", "--detach", "HEAD"], cwd=wt)
    assert proc.returncode == 0, proc.stderr

    # back onto the branch
    proc = _run(["checkout", "wt1-branch"], cwd=wt)
    assert proc.returncode == 0, proc.stderr

    # creating another worktree FROM the primary (the dispatch flow) still works
    wt2 = primary.parent / "wt2"
    proc = _run(["-C", str(primary), "worktree", "add", "-q", str(wt2), "-b", "wt2-branch"])
    assert proc.returncode == 0, proc.stderr

    # primary is still on main throughout
    assert _head_branch(primary) == "main"


def test_fetch_style_ref_updates_unaffected(scratch_repo, tmp_path):
    """refs/remotes/* and FETCH_HEAD updates (the benign part of the incident) pass."""
    primary = scratch_repo["primary"]
    # Make the primary its own "remote" and fetch from a worktree.
    wt = _add_worktree(primary)
    proc = _run(["remote", "add", "origin", str(primary)], cwd=wt)
    assert proc.returncode == 0, proc.stderr
    proc = _run(["fetch", "-q", "origin"], cwd=wt)
    assert proc.returncode == 0, proc.stderr
    assert _head_branch(primary) == "main"


# ---------------------------------------------------------------------------
# post-checkout heal (wrong-branch primary self-repairs)
# ---------------------------------------------------------------------------


def test_branch_switch_in_primary_is_auto_healed(scratch_repo):
    """checkout -b in the primary is allowed pre-flight (worktree-add is
    indistinguishable) but the post-checkout heal returns it to main."""
    primary = scratch_repo["primary"]

    # The heal path needs scripts/guardrails (plus its scripts.common import)
    # next to the hooks.
    scripts_dst = primary / "scripts" / "guardrails"
    scripts_dst.mkdir(parents=True)
    (primary / "scripts" / "__init__.py").write_text("", encoding="utf-8")
    (scripts_dst / "__init__.py").write_text("", encoding="utf-8")
    common_dst = primary / "scripts" / "common"
    common_dst.mkdir()
    (common_dst / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy(REPO_ROOT / "scripts" / "common" / "git_context.py", common_dst)
    for name in (
        "assert_primary_on_main.py",
        "worktree_containment.py",
        "primary_post_checkout_heal.sh",
    ):
        shutil.copy(REPO_ROOT / "scripts" / "guardrails" / name, scripts_dst / name)

    wt = _add_worktree(primary)

    proc = _run(["-C", str(primary), "checkout", "-q", "-b", "evil"], cwd=wt)
    assert proc.returncode == 0, proc.stderr

    assert _head_branch(primary) == "main", (
        "post-checkout heal must return a wrong-branch primary to main"
    )
