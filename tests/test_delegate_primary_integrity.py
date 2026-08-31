"""Tests for the #5803-follow-up primary-integrity wiring in scripts/delegate.py.

- pre-dispatch gate: unrepaired primary drift blocks NEW write-capable
  dispatches (running ones are never touched)
- instructive fetch failure: no silent fallback to a stale local base
- worktree prompt tells workers to fetch from origin INSIDE the worktree
- GIT_CEILING_DIRECTORIES damage-reduction env for worker spawns
- #7522: the dispatch base SHA is pinned to the canonical GitHub remote,
  never to a lagging host-mirror origin
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


def test_gate_never_repairs_safe_drift_implicitly(primary_repo):
    _git(primary_repo, "checkout", "-q", "--detach", "HEAD")

    first = delegate._resolve_primary_integrity_error(mode="danger")
    second = delegate._resolve_primary_integrity_error(mode="danger")

    assert first is not None and second is not None
    assert "explicit doctor" in second
    proc = _git(primary_repo, "symbolic-ref", "-q", "HEAD", check=False)
    assert proc.returncode != 0


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


def _pin_single_remote_host(monkeypatch):
    """Pin the single-remote host shape (#7522): origin IS the canonical
    GitHub remote — the plain origin fetch flow — regardless of which fleet
    host (some carry a mirror origin + a separate github remote) runs the
    suite."""
    monkeypatch.setattr(
        delegate,
        "_git_remote_urls",
        lambda _root: {"origin": "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git"},
    )


def test_ensure_worktree_fetch_failure_is_actionable_error(tmp_tasks_dir, tmp_path, monkeypatch):
    """#5803 follow-up: the old silent fallback to local base is WHY a worker
    went to the primary for freshness. Fetch failure must now be an actionable
    error naming `git fetch origin`."""
    target = tmp_path / "offline-worktree"
    _pin_single_remote_host(monkeypatch)

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            return subprocess.CompletedProcess(cmd, 1, "", "fatal: unable to access")
        if cmd[:2] == ["git", "rev-parse"] and "--verify" in cmd:
            return subprocess.CompletedProcess(cmd, 1, "", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match=r"git fetch origin \+refs/heads/main:refs/remotes/origin/main"):
        delegate._ensure_worktree(
            agent="codex",
            task_id="5803-offline",
            raw_path=str(target),
            base="main",
        )


def test_ensure_worktree_fetch_failure_mentions_canonical_remote(tmp_tasks_dir, tmp_path, monkeypatch):
    _pin_single_remote_host(monkeypatch)

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


# ---------------------------------------------------------------------------
# canonical GitHub base remote (#7522)
# ---------------------------------------------------------------------------

_MIRROR_URL = "https://git.internal.mirror/learn-ukrainian.github.io"
_CANONICAL_URL = "https://github.com/learn-ukrainian/learn-ukrainian.github.io.git"
_STALE_MIRROR_SHA = "1111111111111111111111111111111111111111"
_CANONICAL_SHA = "2222222222222222222222222222222222222222"


def _pin_two_remote_host(monkeypatch):
    """Two-remote host shape (#7522): lagging non-GitHub `origin` mirror plus
    a `github` remote pointing at the canonical GitHub repository."""
    monkeypatch.setattr(
        delegate,
        "_git_remote_urls",
        lambda _root: {"origin": _MIRROR_URL, "github": _CANONICAL_URL},
    )


def test_fetch_base_origin_is_github_keeps_single_origin_fetch(tmp_tasks_dir, monkeypatch):
    """Hosts whose origin already IS the canonical GitHub remote (the primary
    fleet hosts) must keep the plain single-origin fetch — no speculative
    second remote, no behavior change (#7522)."""
    _pin_single_remote_host(monkeypatch)
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, "sha\n", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    assert delegate._fetch_base("main") is True

    fetches = [c for c in calls if c[:2] == ["git", "fetch"]]
    assert fetches == [["git", "fetch", "origin", "+refs/heads/main:refs/remotes/origin/main"]]


def test_fetch_base_two_remote_host_prefers_canonical_github_sha(tmp_tasks_dir, monkeypatch, capsys):
    """origin = non-GitHub mirror AND `github` = canonical remote: the base
    must be fetched from `github` (landing in refs/remotes/origin/<branch>),
    the mirror is probed read-only via ls-remote only to warn, and the warning
    must name both SHAs and both remotes (#7522)."""
    _pin_two_remote_host(monkeypatch)
    fetches: list[list[str]] = []
    probes: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            fetches.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["git", "ls-remote"]:
            probes.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, _STALE_MIRROR_SHA + "\trefs/heads/main\n", "")
        if cmd[:2] == ["git", "rev-parse"]:
            return subprocess.CompletedProcess(cmd, 0, _CANONICAL_SHA + "\n", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    assert delegate._fetch_base("main") is True

    refspec = "+refs/heads/main:refs/remotes/origin/main"
    # The canonical fetch is the ONLY fetch — origin is probed read-only.
    assert fetches == [["git", "fetch", "github", refspec]]
    assert probes == [["git", "ls-remote", "origin", "refs/heads/main"]]
    err = capsys.readouterr().err
    assert _STALE_MIRROR_SHA in err
    assert _CANONICAL_SHA in err
    assert "'origin'" in err and _MIRROR_URL in err
    assert "'github'" in err and _CANONICAL_URL in err


def test_fetch_base_canonical_fetch_failure_fails_closed_never_stale_origin(tmp_tasks_dir, monkeypatch):
    """Canonical fetch failure must raise, never silently return the stale
    mirror SHA — even when the mirror probe itself succeeds (#7522)."""
    _pin_two_remote_host(monkeypatch)
    fetches: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            fetches.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 128, "", "fatal: remote end hung up unexpectedly")
        if cmd[:2] == ["git", "ls-remote"]:
            return subprocess.CompletedProcess(cmd, 0, _STALE_MIRROR_SHA + "\trefs/heads/main\n", "")
        return subprocess.CompletedProcess(cmd, 0, _STALE_MIRROR_SHA + "\n", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as excinfo:
        delegate._fetch_base("main")
    message = str(excinfo.value)
    assert "canonical GitHub remote" in message
    assert "'github'" in message and _CANONICAL_URL in message
    assert "origin" in message and _MIRROR_URL in message
    assert "remote end hung up" in message
    assert "git remote -v" in message
    # Only the canonical remote was ever fetched — the reachable mirror
    # never touched refs/remotes/origin/main.
    refspec = "+refs/heads/main:refs/remotes/origin/main"
    assert fetches == [["git", "fetch", "github", refspec]]

    fetches.clear()

    def fake_run_timeout(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            fetches.append(list(cmd))
            raise subprocess.TimeoutExpired(cmd, 180.0)
        if cmd[:2] == ["git", "ls-remote"]:
            return subprocess.CompletedProcess(cmd, 0, _STALE_MIRROR_SHA + "\trefs/heads/main\n", "")
        return subprocess.CompletedProcess(cmd, 0, _STALE_MIRROR_SHA + "\n", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run_timeout)

    with pytest.raises(RuntimeError, match="timed out"):
        delegate._fetch_base("main")
    assert fetches == [["git", "fetch", "github", refspec]]


def test_fetch_base_canonical_failure_never_poisons_origin_tracking_ref(tmp_path, monkeypatch):
    """#7522 review follow-up, real git end to end: with a previously-good
    refs/remotes/origin/main pinned to the canonical SHA, a canonical fetch
    failure must fail closed AND leave the tracking ref at its pre-fetch
    value — the reachable lagging mirror is probed with ls-remote, never
    fetched over the tracking ref."""
    seed = _init_repo(tmp_path / "seed")
    mirror = tmp_path / "mirror.git"
    canonical = tmp_path / "canonical.git"
    env = _clean_env()

    subprocess.run(
        ["git", "clone", "-q", "--bare", str(seed), str(mirror)],
        check=True,
        env=env,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(seed), str(canonical)],
        check=True,
        env=env,
        capture_output=True,
        timeout=30,
    )
    # The mirror stays behind; only the canonical remote advances.
    (seed / "README.md").write_text("canonical advance\n")
    _git(seed, "commit", "-qam", "advance canonical main")
    _git(seed, "push", "-q", str(canonical), "main")
    canonical_sha = _git(canonical, "rev-parse", "main").stdout.strip()
    mirror_sha = _git(mirror, "rev-parse", "main").stdout.strip()
    assert canonical_sha != mirror_sha

    primary = tmp_path / "primary"
    subprocess.run(
        ["git", "clone", "-q", str(mirror), str(primary)],
        check=True,
        env=env,
        capture_output=True,
        timeout=30,
    )
    # `github` carries the canonical GitHub URL in config; an insteadOf
    # rewrite routes the actual fetch to the local bare fixture, so the
    # remote-classification code under test sees the genuine host shape.
    _git(primary, "remote", "add", "github", _CANONICAL_URL)
    _git(primary, "config", f"url.{canonical}.insteadOf", _CANONICAL_URL)
    # A previous good dispatch pinned the tracking ref to the canonical SHA.
    _git(primary, "fetch", "-q", "github", "+refs/heads/main:refs/remotes/origin/main")
    assert _git(primary, "rev-parse", "refs/remotes/origin/main").stdout.strip() == canonical_sha
    # Now the canonical remote dies; the lagging mirror still answers.
    _git(primary, "config", "--unset", f"url.{canonical}.insteadOf")
    _git(primary, "config", f"url.{tmp_path / 'dead-remote.git'}.insteadOf", _CANONICAL_URL)

    monkeypatch.setattr(delegate, "_REPO_ROOT", primary.resolve())

    with pytest.raises(RuntimeError, match="canonical GitHub remote"):
        delegate._fetch_base("main")

    after = _git(primary, "rev-parse", "refs/remotes/origin/main").stdout.strip()
    assert after == canonical_sha
    assert after != mirror_sha


def test_fetch_existing_branch_uses_canonical_github_remote(tmp_tasks_dir, monkeypatch):
    """--branch reuse must fetch the PR branch from the canonical GitHub
    remote, not a mirror that may lag or not carry it (#7522)."""
    _pin_two_remote_host(monkeypatch)
    fetches: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"]:
            fetches.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 0, "sha\n", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    delegate._fetch_existing_branch("cursor/lane-branch")

    assert fetches == [
        ["git", "fetch", "github", "+refs/heads/cursor/lane-branch:refs/remotes/origin/cursor/lane-branch"]
    ]


def test_fetch_existing_branch_canonical_failure_never_falls_back_to_mirror(tmp_tasks_dir, monkeypatch):
    _pin_two_remote_host(monkeypatch)

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "fetch"] and cmd[2] == "github":
            return subprocess.CompletedProcess(cmd, 128, "", "fatal: remote end hung up unexpectedly")
        return subprocess.CompletedProcess(cmd, 0, "sha\n", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as excinfo:
        delegate._fetch_existing_branch("cursor/lane-branch")
    message = str(excinfo.value)
    assert "canonical GitHub remote" in message
    assert "origin" in message and "git remote -v" in message


def test_base_branch_name_strips_remote_prefixes():
    assert delegate._base_branch_name("main") == "main"
    assert delegate._base_branch_name("origin/main") == "main"
    assert delegate._base_branch_name("github/main") == "main"
    assert delegate._origin_base_ref("main") == "origin/main"
    assert delegate._origin_base_ref("origin/main") == "origin/main"
    assert delegate._origin_base_ref("github/main") == "origin/main"


def test_validate_branch_reuse_name_rejects_github_prefix():
    with pytest.raises(ValueError, match="github/"):
        delegate._validate_branch_reuse_name("github/feature")


def test_worktree_base_pins_canonical_github_sha_when_origin_mirror_lags(tmp_path, monkeypatch, capsys):
    """#7522 acceptance, real git end to end: a host whose origin is a mirror
    1+ commits behind GitHub and whose `github` remote is canonical must get a
    worktree whose base commit equals the canonical GitHub main SHA."""
    seed = _init_repo(tmp_path / "seed")
    mirror = tmp_path / "mirror.git"
    canonical = tmp_path / "canonical.git"
    env = _clean_env()

    subprocess.run(
        ["git", "clone", "-q", "--bare", str(seed), str(mirror)],
        check=True,
        env=env,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(seed), str(canonical)],
        check=True,
        env=env,
        capture_output=True,
        timeout=30,
    )
    # The mirror stays behind; only the canonical remote advances.
    (seed / "README.md").write_text("canonical advance\n")
    _git(seed, "commit", "-qam", "advance canonical main")
    _git(seed, "push", "-q", str(canonical), "main")
    canonical_sha = _git(canonical, "rev-parse", "main").stdout.strip()
    mirror_sha = _git(mirror, "rev-parse", "main").stdout.strip()
    assert canonical_sha != mirror_sha

    primary = tmp_path / "primary"
    subprocess.run(
        ["git", "clone", "-q", str(mirror), str(primary)],
        check=True,
        env=env,
        capture_output=True,
        timeout=30,
    )
    # `github` carries the canonical GitHub URL in config; an insteadOf
    # rewrite routes the actual fetch to the local bare fixture, so the
    # remote-classification code under test sees the genuine host shape.
    _git(primary, "remote", "add", "github", _CANONICAL_URL)
    _git(primary, "config", f"url.{canonical}.insteadOf", _CANONICAL_URL)

    monkeypatch.setattr(delegate, "_REPO_ROOT", primary.resolve())
    worktree = tmp_path / "dispatch" / "glm" / "7522-fixture"

    resolved = delegate._resolve_worktree_base_sha(
        agent="glm",
        task_id="7522-fixture",
        raw_path=str(worktree),
        base="main",
        branch=None,
    )
    assert resolved == canonical_sha

    path, _branch, telemetry = delegate._ensure_worktree(
        agent="glm",
        task_id="7522-fixture",
        raw_path=str(worktree),
        base="main",
        resolved_base_sha=resolved,
    )
    log_sha = _git(path, "log", "-1", "--format=%H").stdout.strip()
    assert log_sha == canonical_sha
    assert log_sha != mirror_sha
    assert telemetry["base_sha"] == canonical_sha

    err = capsys.readouterr().err
    assert mirror_sha in err and canonical_sha in err
    assert "'origin'" in err and str(mirror) in err
    assert "'github'" in err and "github.com/learn-ukrainian/learn-ukrainian.github.io" in err


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
