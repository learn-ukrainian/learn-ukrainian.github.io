"""Tests for the #5803-follow-up primary-integrity wiring in scripts/delegate.py.

- pre-dispatch gate: unrepaired primary drift blocks NEW write-capable
  dispatches (running ones are never touched)
- instructive fetch failure: no silent fallback to a stale local base
- worktree prompt tells workers to fetch from origin INSIDE the worktree
- GIT_CEILING_DIRECTORIES damage-reduction env for worker spawns
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate

_GIT_REDIRECT = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_PREFIX",
    }
)


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECT}


def _git(repo: Path, *args: str, check: bool = True, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
        env=env or _clean_env(),
        timeout=30,
    )


def _init_repo(path: Path) -> Path:
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(path)],
        check=True,
        env=_clean_env(),
        timeout=30,
    )
    _git(path, "config", "user.email", "gate-test@example.com")
    _git(path, "config", "user.name", "gate-test")
    # Mirror the real repo's .gitignore so the watchdog's own state/log files
    # under data/telemetry/ (and dispatch state under batch_state/) do not
    # count as primary-checkout dirt.
    (path / ".gitignore").write_text("data/telemetry/\nbatch_state/\n.worktrees/\n")
    (path / "README.md").write_text("fixture\n")
    _git(path, "add", ".gitignore", "README.md")
    _git(path, "commit", "-q", "-m", "init")
    return path


@pytest.fixture
def primary_repo(tmp_path, monkeypatch):
    """A fixture 'primary' checkout wired in as delegate._REPO_ROOT with an
    isolated tasks dir and watchdog state under gitignored-looking tmp paths."""
    repo = _init_repo(tmp_path / "primary")
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo)
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks_dir)
    return repo


# ---------------------------------------------------------------------------
# pre-dispatch gate
# ---------------------------------------------------------------------------


def test_gate_allows_healthy_primary(primary_repo):
    assert delegate._resolve_primary_integrity_error(mode="danger") is None
    assert delegate._resolve_primary_integrity_error(mode="workspace-write") is None


def test_gate_exempts_read_only_mode(primary_repo):
    _git(primary_repo, "checkout", "-q", "--detach", "HEAD")
    assert delegate._resolve_primary_integrity_error(mode="read-only") is None


def test_gate_blocks_unrepaired_drift(primary_repo):
    _git(primary_repo, "checkout", "-q", "--detach", "HEAD")
    (primary_repo / "README.md").write_text("human work\n")  # dirty → never repaired

    error = delegate._resolve_primary_integrity_error(mode="danger")
    assert error is not None
    assert "UNREPAIRED" in error
    # Primary NOT touched.
    proc = _git(primary_repo, "symbolic-ref", "-q", "HEAD", check=False)
    assert proc.returncode != 0
    assert (primary_repo / "README.md").read_text() == "human work\n"


def test_gate_repairs_safe_drift_then_allows(primary_repo):
    _git(primary_repo, "checkout", "-q", "--detach", "HEAD")

    # First call records the stable-main baseline and blocks.
    error = delegate._resolve_primary_integrity_error(mode="danger")
    assert error is not None
    assert "baseline" in error

    # Second call: main observed stable → watchdog repairs → dispatch allowed.
    assert delegate._resolve_primary_integrity_error(mode="danger") is None
    proc = _git(primary_repo, "symbolic-ref", "-q", "HEAD")
    assert proc.stdout.strip() == "refs/heads/main"


def test_gate_defers_while_dispatch_running(primary_repo):
    _git(primary_repo, "checkout", "-q", "--detach", "HEAD")
    delegate._TASKS_DIR.mkdir(parents=True)
    (delegate._TASKS_DIR / "codex-live.json").write_text(
        f'{{"task_id": "codex/live", "status": "running", "pid": {os.getpid()}}}'
    )

    error = delegate._resolve_primary_integrity_error(mode="danger")
    assert error is not None
    assert "deferred" in error
    # Still detached — the running dispatch was not killed or raced.
    proc = _git(primary_repo, "symbolic-ref", "-q", "HEAD", check=False)
    assert proc.returncode != 0


def test_gate_fail_open_on_watchdog_error(primary_repo, monkeypatch, capsys):
    # None in sys.modules makes `from <module> import ...` raise ImportError;
    # both import paths fail → the generic except must fail OPEN.
    monkeypatch.setitem(sys.modules, "scripts.audit.check_primary_integrity", None)
    monkeypatch.setitem(sys.modules, "audit.check_primary_integrity", None)
    assert delegate._resolve_primary_integrity_error(mode="danger") is None
    assert "watchdog errored" in capsys.readouterr().err


def test_monitor_api_failure_warns_but_does_not_block_dispatch(monkeypatch, capsys):
    def unavailable(*_args, **_kwargs):
        raise OSError("Connection refused")

    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(delegate.urllib.request, "urlopen", unavailable)
    monkeypatch.setattr(delegate, "_append_dispatch_event", lambda event, **fields: events.append((event, fields)))

    assert delegate._warn_if_monitor_api_unreachable() is None

    output = capsys.readouterr().err
    assert "MONITOR API UNREACHABLE" in output
    assert "offline fallbacks" in output
    assert "services.sh status api" in output
    assert events[0][0] == "monitor_api_unreachable_pre_dispatch"


def test_healthy_monitor_api_emits_no_dispatch_warning(monkeypatch, capsys):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(delegate.urllib.request, "urlopen", lambda *_args, **_kwargs: Response())

    delegate._warn_if_monitor_api_unreachable()

    assert capsys.readouterr().err == ""


# ---------------------------------------------------------------------------
# instructive fetch failure (no silent stale-base fallback)
# ---------------------------------------------------------------------------


def test_ensure_worktree_fetch_failure_is_actionable_error(tmp_tasks_dir, tmp_path, monkeypatch):
    """#5803 follow-up: the old silent fallback to local base is WHY a worker
    went to the primary for freshness. Fetch failure must now be an actionable
    error naming `git fetch origin`."""
    target = tmp_path / "offline-worktree"

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            return subprocess.CompletedProcess(cmd, 1, "", "fatal: unable to access")
        if cmd[:2] == ["git", "rev-parse"] and "--verify" in cmd:
            return subprocess.CompletedProcess(cmd, 1, "", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="git fetch origin main"):
        delegate._ensure_worktree(
            agent="codex",
            task_id="5803-offline",
            raw_path=str(target),
            base="main",
        )


def test_ensure_worktree_fetch_failure_mentions_canonical_remote(tmp_tasks_dir, tmp_path, monkeypatch):
    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            return subprocess.CompletedProcess(cmd, 1, "", "fatal: unable to access")
        if cmd[:2] == ["git", "rev-parse"] and "--verify" in cmd:
            return subprocess.CompletedProcess(cmd, 1, "", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="canonical remote"):
        delegate._ensure_worktree(
            agent="codex",
            task_id="5803-offline-2",
            raw_path=str(tmp_path / "wt2"),
            base="main",
        )


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    monkeypatch.setattr(delegate, "_TASKS_DIR", tasks_dir)
    return tasks_dir


# ---------------------------------------------------------------------------
# worktree prompt removes the workflow reason to visit the primary
# ---------------------------------------------------------------------------


def test_worktree_prompt_teaches_in_worktree_fetch():
    prompt = delegate._augment_prompt_with_worktree("do the thing", Path("/tmp/wt"))
    assert "git fetch origin main" in prompt
    assert "INSIDE this worktree" in prompt
    assert "primary checkout" in prompt


# ---------------------------------------------------------------------------
# GIT_CEILING_DIRECTORIES damage reduction
# ---------------------------------------------------------------------------


def test_git_ceiling_env_set_to_worktree_parent():
    env: dict[str, str] = {}
    worktree = Path("/repo/.worktrees/dispatch/codex/task-1")
    delegate._apply_worktree_git_ceiling(env, worktree)
    assert env["GIT_CEILING_DIRECTORIES"] == "/repo/.worktrees/dispatch/codex"


def test_git_ceiling_env_appends_to_existing():
    env = {"GIT_CEILING_DIRECTORIES": "/elsewhere"}
    worktree = Path("/repo/.worktrees/dispatch/codex/task-1")
    delegate._apply_worktree_git_ceiling(env, worktree)
    assert env["GIT_CEILING_DIRECTORIES"] == f"/elsewhere{os.pathsep}/repo/.worktrees/dispatch/codex"


def test_git_ceiling_keeps_linked_worktree_ops_working(tmp_path):
    """Integration proof for the comment in _apply_worktree_git_ceiling: with
    the ceiling at the worktree PARENT, git from the worktree root AND from a
    subdirectory still resolves the worktree's own repo."""
    repo = _init_repo(tmp_path / "primary")
    worktree = tmp_path / "dispatch" / "codex" / "task-1"
    worktree.parent.mkdir(parents=True)
    _git(repo, "worktree", "add", "-q", "-b", "codex/task-1", str(worktree))
    (worktree / "sub").mkdir()

    env = _clean_env()
    env["GIT_CEILING_DIRECTORIES"] = str(worktree.parent)

    top = _git(worktree, "rev-parse", "--show-toplevel", env=env)
    assert top.stdout.strip() == str(worktree)
    sub = _git(worktree / "sub", "rev-parse", "--show-toplevel", env=env)
    assert sub.stdout.strip() == str(worktree)
    # status works from a subdirectory too.
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=worktree / "sub",
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert status.returncode == 0


def test_git_ceiling_blocks_upward_discovery_to_primary(tmp_path):
    """If the worktree's .git pointer is gone, upward discovery must stop at
    the ceiling instead of silently binding to an ancestor repo."""
    repo = _init_repo(tmp_path / "primary")
    nested = repo / ".worktrees" / "dispatch" / "codex" / "task-1"
    nested.mkdir(parents=True)  # plain dir INSIDE the primary, no .git pointer

    env = _clean_env()
    env["GIT_CEILING_DIRECTORIES"] = str(nested.parent)
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=nested,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert proc.returncode != 0  # fails loudly…
    # …instead of discovering the primary checkout.
    assert str(repo) not in proc.stdout
