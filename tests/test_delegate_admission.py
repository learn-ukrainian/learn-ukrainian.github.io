"""delegate.py dispatch host admission, prompt liveness and peak RSS (#8645 part A).

Task records live under tmp_path. Memory and load come from a monkeypatched
probe; no test allocates memory, generates load, or spawns a worker.
"""

from __future__ import annotations

import hashlib
import json
import os
import resource
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from scripts.fleet import capacity_pick
from scripts.orchestration import dispatch_admission, job_host_exec

_GIB = 1024**3


@pytest.mark.parametrize("task_family", ["data", "text", "word cards", "word-cards", "word_cards", "dataset", "reviews"])
@pytest.mark.parametrize("model", ["gpt-6.1-sol", "gemini-3.8-flash-high", "claude-opus-5-5"])
def test_ukrainian_content_model_families_pass(task_family, model):
    args = delegate.build_parser().parse_args([
        "dispatch", "--task-id", "synthetic-language-job", "--agent", "codex", "--model", model, "--language-lane",
        "--research-task-family", task_family,
    ])
    refusal, target = delegate._admit_dispatch_target(args, agent="codex", trees=None)
    assert refusal is None
    assert target.model == model


@pytest.mark.parametrize("model", ["grok-4.7", "glm-5", "other-model", "unknown", "", None])
def test_ukrainian_content_unknown_or_disallowed_model_refused(model):
    args = delegate.build_parser().parse_args([
        "dispatch", "--task-id", "synthetic-language-job", "--agent", "codex", "--language-lane", "--research-task-family", "data",
    ])
    args.model = model
    refusal, target = delegate._admit_dispatch_target(args, agent="codex", trees=None)
    assert refusal.startswith("UKRAINIAN_MODEL_REFUSED:")
    assert target is None


@pytest.mark.parametrize("task_family", ["data", "text", "word cards", "dataset", "reviews"])
@pytest.mark.parametrize("language_lane", [False, None, "unknown"])
def test_ukrainian_content_unknown_language_refused(task_family, language_lane):
    args = delegate.build_parser().parse_args([
        "dispatch", "--task-id", "synthetic-language-job", "--agent", "codex", "--model", "gpt-6.1-sol", "--research-task-family", task_family,
    ])
    args.language_lane = language_lane
    refusal, target = delegate._admit_dispatch_target(args, agent="codex", trees=None)
    assert "language is missing or unknown" in refusal
    assert target is None


def test_ukrainian_lane_without_content_family_refuses_other_model():
    args = delegate.build_parser().parse_args(["dispatch", "--task-id", "synthetic-language-job", "--agent", "codex", "--model", "grok-4.7", "--language-lane"])
    refusal, target = delegate._admit_dispatch_target(args, agent="codex", trees=None)
    assert refusal.startswith("UKRAINIAN_MODEL_REFUSED:")
    assert target is None


@pytest.mark.parametrize("model", ["grok-4.7", "glm-5", "other-model", None])
def test_ukrainian_content_substituted_model_refused(model):
    args = delegate.build_parser().parse_args([
        "dispatch", "--task-id", "synthetic-language-job", "--agent", "codex", "--model", "gpt-6.1-sol", "--language-lane", "--research-task-family", "text",
    ])
    refusal, target = delegate._admit_dispatch_target(
        args, agent="codex", trees=None, route=lambda _request: ("codex", model, "synthetic-substitution"),
    )
    assert refusal.startswith("UKRAINIAN_MODEL_REFUSED:")
    assert target is None


@pytest.fixture
def tasks_dir(tmp_path, monkeypatch):
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path / "scratch"))
    for name in (
        "_resolve_dirty_primary_checkout_error",
        "_resolve_primary_integrity_error",
    ):
        monkeypatch.setattr(delegate, name, lambda **_kwargs: None)
    for name in (
        "_warn_node_modules_integrity",
        "_warn_venv_integrity",
        "_warn_worktree_cleanup_integrity",
        "_warn_if_monitor_api_unreachable",
    ):
        monkeypatch.setattr(delegate, name, lambda: None)
    monkeypatch.setattr(
        delegate,
        "_sweep_runtime_tmp_orphans",
        lambda: {"leases_reaped": 0, "bytes_freed": 0, "errors": 0, "error_details": []},
    )
    monkeypatch.setattr(job_host_exec, "decide_dispatch_placement", lambda **_kwargs: ("local", "test", None))
    return tasks


def _running_record(tasks: Path, task_id: str, *, pid: int, mode: str = "workspace-write") -> Path:
    tasks.mkdir(parents=True, exist_ok=True)
    path = tasks / f"{task_id}.json"
    path.write_text(
        json.dumps(
            {
                "task_id": task_id,
                "status": "running",
                "mode": mode,
                "pid": pid,
                "run_nonce": f"nonce-{task_id}",
                "started_at": datetime.now(UTC).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def _lease_task_id(prefix: str) -> str:
    """One lease task id for this case. A shared id names one shared lease directory (#9927)."""
    current = os.environ.get("PYTEST_CURRENT_TEST", prefix)
    node = current.split(" ", 1)[0]
    digest = hashlib.sha256(node.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _dry_run_args(*extra: str, mode: str = "workspace-write", task_id: str | None = None):
    if task_id is None:
        task_id = _lease_task_id("adm-probe")
    argv = [
        "dispatch",
        "--agent",
        "codex",
        "--task-id",
        task_id,
        "--initiator",
        "codex",
        "--prompt",
        "test",
        "--mode",
        mode,
        "--dry-run",
        *extra,
    ]
    if mode != "read-only":
        # A write dispatch declares its scope (#9739); an ordinary path keeps a new branch unprotected.
        argv.extend(("--worktree", "--owned-path", "scripts/example.py"))
    return delegate.build_parser().parse_args(argv)


def _pin_origin_main_to_head(monkeypatch) -> None:
    """Give write-dispatch review admission (#9739) a canonical default branch at the checkout's own HEAD.

    Admission observes the default branch and the open PRs on GitHub (A7);
    here that is HEAD and none, so the dispatch is a fresh branch with no
    commits of its own and these tests check host admission, not the network
    or the runner's clone depth (tests/test_authoring_review_feasibility.py
    covers authored branches against a real remote). The dry-run worktree base
    is that HEAD too.
    """
    from tests.test_authoring_review_feasibility import pin_review_target

    head = _git(delegate._REPO_ROOT, "rev-parse", "HEAD")
    pin_review_target(monkeypatch, head)
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: head)


def test_dispatch_refuses_a_write_worker_at_the_cap_with_one_line(tasks_dir, monkeypatch, capsys):
    _pin_origin_main_to_head(monkeypatch)
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")

    args = _dry_run_args()
    rc = delegate.cmd_dispatch(args)

    assert rc == delegate._ADMISSION_REFUSED_EXIT == 3
    refusal = [line for line in capsys.readouterr().err.splitlines() if "admission" in line]
    assert refusal == [
        "❌ dispatch admission refused for a workspace-write worker: live write workers 0/0 reached the cap "
        "(DISPATCH_MAX_LIVE_WRITE_WORKERS=0). Wait for a worker to finish or for the host to recover, raise the "
        'threshold through the named environment variable, or pass --force-admission "<reason>" to override.'
    ]
    assert not delegate._state_path(args.task_id).exists()


def test_dispatch_refuses_on_low_memory_and_high_load(tasks_dir, monkeypatch, capsys):
    _pin_origin_main_to_head(monkeypatch)
    monkeypatch.setattr(
        dispatch_admission,
        "probe_host",
        lambda: dispatch_admission.HostProbe(
            mem_available_bytes=1 * _GIB, load1=20.0, cpu_count=8, proc_available=True
        ),
    )

    assert delegate.cmd_dispatch(_dry_run_args(mode="danger")) == 3

    err = capsys.readouterr().err
    assert "MemAvailable 1.0 GiB is below the floor of 8.5 GiB" in err
    assert "load 2.50 per CPU" in err


def test_read_only_dispatch_is_exempt(tasks_dir, monkeypatch, capsys):
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")

    rc = delegate.cmd_dispatch(_dry_run_args(mode="read-only", task_id="adm-reader"))

    assert rc == 0
    assert "admission" not in capsys.readouterr().err
    state = delegate._read_state(delegate._state_path("adm-reader"))
    assert state is not None and "admission" not in state


def test_force_admission_records_the_reason(tasks_dir, monkeypatch, capsys):
    # Admission metadata must not depend on a real origin/main fetch.
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")

    args = _dry_run_args("--force-admission", "hotfix #1234 while one worker drains")
    rc = delegate.cmd_dispatch(args)

    assert rc == 0
    assert "overridden by --force-admission ('hotfix #1234 while one worker drains')" in capsys.readouterr().err
    state = delegate._read_state(delegate._state_path(args.task_id))
    assert state is not None
    admission = state["admission"]
    assert admission["admitted"] is False
    assert admission["forced"] is True
    assert admission["force_reason"] == "hotfix #1234 while one worker drains"
    assert admission["max_live_write_workers"] == 0


def test_force_admission_requires_a_reason(tasks_dir, capsys):
    assert delegate.cmd_dispatch(_dry_run_args("--force-admission", "   ")) == 2
    assert "--force-admission requires a non-empty reason" in capsys.readouterr().err


def test_admission_sweeps_dead_workers_to_crashed_and_frees_their_slot(tasks_dir, monkeypatch):
    dead = _running_record(tasks_dir, "dead-writer", pid=424242)
    _running_record(tasks_dir, "live-writer", pid=515151)
    monkeypatch.setattr(delegate, "_pid_alive", lambda pid: pid == 515151)
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "2")

    decision = delegate._evaluate_dispatch_admission("workspace-write", sweep=True)

    assert decision.admitted
    assert decision.live_task_ids == ("live-writer",)
    swept = json.loads(dead.read_text(encoding="utf-8"))
    assert swept["status"] == "crashed"
    assert "marked crashed by admission probe" in swept["stderr_excerpt"]


def test_dry_run_reports_dead_workers_without_marking_them(tasks_dir, monkeypatch, capsys):
    _pin_origin_main_to_head(monkeypatch)
    dead = _running_record(tasks_dir, "dead-writer", pid=424242)
    monkeypatch.setattr(delegate, "_pid_alive", lambda _pid: False)

    assert delegate.cmd_dispatch(_dry_run_args()) == 0

    assert json.loads(dead.read_text(encoding="utf-8"))["status"] == "running"
    assert "1 record(s) dead pid, not counted: dead-writer" in capsys.readouterr().err


class _FakeStdin:
    def write(self, _data):
        pass

    def close(self):
        pass


def _dispatch_worktree(tasks: Path, name: str = "wt") -> Path:
    """An explicit ``--worktree`` inside the fixture primary's codex dispatch subtree (#8775)."""
    return tasks.parent / "primary" / ".worktrees" / "dispatch" / "codex" / name


def _live_danger_args(tasks: Path, task_id: str):
    import argparse

    _dispatch_worktree(tasks).mkdir(parents=True, exist_ok=True)
    return argparse.Namespace(
        agent="codex",
        task_id=task_id,
        prompt="test",
        prompt_file=None,
        mode="danger",
        model=None,
        cwd=None,
        worktree=str(_dispatch_worktree(tasks)),
        base="main",
        hard_timeout=3600,
        owned_path=["scripts/example.py"],
    )


def _stub_worktree(monkeypatch, tasks: Path):
    """A prepared worktree without git: live-dispatch tests stop at the admission lock or at Popen."""
    wt = _dispatch_worktree(tasks)
    primary = tasks.parent / "primary"
    (primary / ".git").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    monkeypatch.chdir(primary)
    monkeypatch.setattr(delegate, "_resolve_write_cwd_error", lambda **_kwargs: None)

    def run(cmd, **kwargs):
        # The creation inventory requests binary, NUL-delimited Git output;
        # other dispatch probes opt into text mode, just as subprocess does.
        text_mode = (
            kwargs.get("text") or kwargs.get("universal_newlines") or kwargs.get("encoding") or kwargs.get("errors")
        )
        output = "" if text_mode else b""
        return delegate.subprocess.CompletedProcess(cmd, 0, output, output)

    monkeypatch.setattr(delegate.subprocess, "run", run)
    monkeypatch.setattr(delegate, "_resolve_worktree_base_sha", lambda **_kwargs: "abc1234")
    monkeypatch.setattr(
        delegate,
        "_ensure_worktree",
        lambda **_kwargs: (wt, "codex/adm", {"base_sha": "abc1234", "layout": "dispatch"}),
    )
    monkeypatch.setattr(delegate, "_resolve_sha", lambda *_args, **_kwargs: "abc1234")
    # Git is stubbed, so branch authorship cannot be enumerated; these tests
    # cover host admission. Authoring-review admission has its own tests (#9739).
    monkeypatch.setattr(delegate, "_authoring_review_admission", lambda *_args, **_kwargs: None)


def test_live_dispatch_records_the_admission_snapshot(tasks_dir, monkeypatch, capsys):
    _stub_worktree(monkeypatch, tasks_dir)
    spawned: list[list[str]] = []

    class _Proc:
        pid = 13579
        stdin = _FakeStdin()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda cmd, **_kwargs: spawned.append(cmd) or _Proc())

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-live")) == 0

    assert len(spawned) == 1
    assert "🚦 dispatch admission: admitted — live write workers 0/2" in capsys.readouterr().err
    state = delegate._read_state(delegate._state_path("adm-live"))
    assert state is not None
    assert state["admission"]["admitted"] is True
    assert state["admission"]["forced"] is False
    assert state["admission"]["mem_available_gib"] == 64.0
    assert (tasks_dir / dispatch_admission.LOCK_FILE_NAME).is_file()


@pytest.mark.parametrize("mode", ["workspace-write", "danger", "read-only"])
@pytest.mark.parametrize(
    "research_paths,owned_paths,conflicts",
    [
        (["tests/**"], ["tests/test_incoming.py"], False),
        (["tests/test_incoming.py"], ["tests/test_holder.py"], True),
    ],
    ids=["broad-research-disjoint-writer", "narrow-research-overlapping-writer"],
)
def test_dispatch_ownership_uses_commit_scope(
    tasks_dir, monkeypatch, capsys, mode, research_paths, owned_paths, conflicts
):
    """#10015: real ownership admission ignores research classification in both directions."""
    import sqlite3

    from scripts.guardrails import delegate_ownership as ownership

    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setenv("DELEGATE_OWNERSHIP_MODE", "refuse")
    pid = os.getpid()
    state_dir = Path(os.environ["LEARN_UKRAINIAN_OWNERSHIP_TASK_STATE_DIR"])
    _running_record(state_dir, "holder", pid=pid)
    holder = ownership.admit_write_paths(
        task_id="holder", mode="workspace-write", owned_paths=["tests/test_holder.py"], pid=pid
    )
    assert holder.admitted
    admissions = []
    real_admit = ownership.admit_write_paths

    def capture_admission(**kwargs):
        result = real_admit(**kwargs)
        admissions.append(result)
        return result

    monkeypatch.setattr(ownership, "admit_write_paths", capture_admission)
    spawned = []

    class _Proc:
        pid = 13579
        stdin = _FakeStdin()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda cmd, **_kwargs: spawned.append(cmd) or _Proc())
    args = _live_danger_args(tasks_dir, "ownership-incoming")
    args.mode = mode
    args.owned_path = owned_paths
    args.research_owned_path = research_paths

    rc = delegate.cmd_dispatch(args)

    refused = conflicts and mode != "read-only"
    err = capsys.readouterr().err
    assert rc == (2 if refused else 0), err
    assert len(admissions) == 1
    assert admissions[0].skipped is (mode == "read-only")
    assert admissions[0].admitted is (not refused)
    assert bool(admissions[0].conflicts) is refused
    assert len([cmd for cmd in spawned if "_worker" in cmd]) == (0 if refused else 1)
    state = delegate._read_state(delegate._state_path(args.task_id))
    if refused:
        assert "write-path ownership refused" in err
        assert state is None
    else:
        assert state["owned_paths"] == owned_paths
    with sqlite3.connect(os.environ["LEARN_UKRAINIAN_OWNERSHIP_LEDGER"]) as conn:
        rows = conn.execute("SELECT claim_json, pid FROM write_claims WHERE task_id = ?", (args.task_id,)).fetchall()
    if refused or mode == "read-only":
        assert rows == []
    else:
        assert [json.loads(claim)["raw"] for claim, _pid in rows] == owned_paths
        assert [claim_pid for _claim, claim_pid in rows] == [_Proc.pid]


@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
def test_dispatch_without_commit_scope_refuses_before_ownership(tasks_dir, monkeypatch, capsys, mode):
    """Research paths cannot replace the required --owned-path at authoring admission."""
    from scripts.guardrails import delegate_ownership as ownership

    real_authoring_admission = delegate._authoring_review_admission
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setattr(delegate, "_authoring_review_admission", real_authoring_admission)
    monkeypatch.setattr(
        ownership, "admit_write_paths", lambda **_kwargs: pytest.fail("ownership must not run without commit scope")
    )
    monkeypatch.setattr(
        delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("an unscoped writer must not spawn")
    )
    args = _live_danger_args(tasks_dir, "ownership-unscoped")
    args.mode = mode
    args.owned_path = None
    args.research_owned_path = ["tests/**"]

    assert delegate.cmd_dispatch(args) == 2

    err = capsys.readouterr().err
    assert delegate.AUTHORING_REVIEW_SCOPE_UNKNOWN in err
    assert "write dispatch declares no --owned-path" in err
    assert not delegate._state_path(args.task_id).exists()


def test_locked_recheck_refuses_a_dispatch_that_lost_the_race(tasks_dir, monkeypatch, capsys):
    """Two dispatches pass the early check; the locked re-check refuses the one that finds the cap full."""
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setattr(
        delegate, "_ensure_worktree", lambda **_kwargs: pytest.fail("a refused dispatch must not create a worktree")
    )
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "1")
    monkeypatch.setattr(
        delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("a refused dispatch must not spawn")
    )
    real_evaluate = delegate._evaluate_dispatch_admission
    calls = {"n": 0}

    def evaluate_after_competitor(mode, **kwargs):
        calls["n"] += 1
        if calls["n"] == 2:  # the competitor published its record between the two checks
            _running_record(tasks_dir, "competitor", pid=515151, mode="workspace-write")
        return real_evaluate(mode, **kwargs)

    monkeypatch.setattr(delegate, "_evaluate_dispatch_admission", evaluate_after_competitor)
    monkeypatch.setattr(delegate, "_pid_alive", lambda pid: pid == 515151)

    rc = delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-race"))

    assert rc == 3
    assert calls["n"] == 2
    assert "live write workers 1/1 reached the cap" in capsys.readouterr().err
    # Refused before the worktree, the task record and the runtime tmp lease (#8717).
    assert not delegate._state_path("adm-race").exists()
    lease_root = Path(tasks_dir.parent / "scratch" / "learn-ukrainian" / "adm-race")
    assert not lease_root.exists()


# --- #8717: admission runs before the worktree and holds the slot until the spawn ------------


# ``_stub_worktree`` replaces ``subprocess.run`` for delegate; the scratch repo needs the real one.
_REAL_RUN = subprocess.run


def _git(cwd: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    proc = _REAL_RUN(["git", *args], cwd=cwd, capture_output=True, text=True, check=True, env=env, timeout=30)
    return proc.stdout.strip()


def _scratch_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "base")
    return repo


def _mechanical_canary_args(*extra: str):
    return delegate.build_parser().parse_args([
        "dispatch", "--agent", "claude", "--model", "claude-haiku-5-5",
        "--task-id", "haiku-mechanical-canary", "--mode", "read-only", "--dry-run",
        "--research-task-family", "mechanical_classification",
        "--research-owned-path", "package-lock.json",
        "--prompt", "Classify the lockfile format. Read only.", *extra,
    ])


def _lockfile_repo(root: Path, content: str = '{"lockfileVersion": 3}') -> Path:
    repo = _scratch_repo(root)
    (repo / "package-lock.json").write_text(content, encoding="utf-8")
    _git(repo, "add", "package-lock.json")
    _git(repo, "-c", "user.email=t@example.com", "-c", "user.name=t", "commit", "-q", "-m", "lockfile")
    return repo


def _content_gate(args, repo: Path, *, cwd: Path | None = None):
    return delegate._kimi_dispatch_gate(
        args, agent=args.agent, route=lambda request: (request.seat, request.model, "explicit"),
        repo_role="public-monorepo", target_repo_root=repo, validated_worktree=None, validated_cwd=cwd,
    )


@pytest.mark.parametrize("explicit_cwd", [False, True])
@pytest.mark.parametrize("family", ["mechanical_classification", "readonly_recon", "routine_mechanical"])
def test_readonly_mechanical_without_worktree_reads_checkout_and_commit(tmp_path, monkeypatch, explicit_cwd, family):
    repo = _lockfile_repo(tmp_path)
    args = _mechanical_canary_args("--research-task-family", family)

    def write_resolver_must_not_run(*args, **kwargs):
        pytest.fail("read-only mechanical task reached Kimi's write-only tree resolver")

    monkeypatch.setattr(delegate, "_kimi_start_trees", write_resolver_must_not_run)
    # An explicit cwd wins over the default checkout, including when the default
    # cannot be read. Both the on-disk and committed content readers are real.
    refusal, start, target = _content_gate(
        args, tmp_path / "unavailable" if explicit_cwd else repo, cwd=repo if explicit_cwd else None,
    )
    assert refusal is None and start is None
    assert target.model == "claude-haiku-5-5"


@pytest.mark.parametrize("unsafe_tree", ["disk", "commit"])
def test_readonly_mechanical_without_worktree_checks_both_content_trees(tmp_path, unsafe_tree):
    safe, unsafe = '{"lockfileVersion": 3}', '{"name": "Україна"}'
    repo = _lockfile_repo(tmp_path, unsafe if unsafe_tree == "commit" else safe)
    (repo / "package-lock.json").write_text(unsafe if unsafe_tree == "disk" else safe, encoding="utf-8")
    refusal, start, target = _content_gate(_mechanical_canary_args(), repo)
    assert "owned content must be plain UTF-8 without Cyrillic" in refusal
    assert start is None and target is None


def test_readonly_mechanical_unreadable_checkout_reports_resolution_stage(tmp_path):
    refusal, start, target = _content_gate(_mechanical_canary_args(), tmp_path / "missing")
    assert refusal == "MECHANICAL_TASK_REFUSED: task input unavailable at tree resolution (RuntimeError) (#9996)"
    assert start is None and target is None


@pytest.mark.parametrize("unsafe", [False, True])
def test_substituted_readonly_mechanical_route_checks_checkout_without_worktree(tmp_path, unsafe):
    repo = _lockfile_repo(tmp_path, '{"name": "Україна"}' if unsafe else '{"lockfileVersion": 3}')
    args = _mechanical_canary_args("--model", "claude-sonnet-5-5")
    refusal, start, target = delegate._kimi_dispatch_gate(
        args, agent=args.agent, route=lambda request: ("claude", "claude-haiku-5-5", "test-substitution"),
        repo_role="public-monorepo", target_repo_root=repo, validated_worktree=None, validated_cwd=None,
    )
    assert start is None
    if unsafe:
        assert "owned content must be plain UTF-8 without Cyrillic" in refusal and target is None
    else:
        assert refusal is None and target.model == "claude-haiku-5-5"


@pytest.mark.parametrize("selector", ["--worktree", "--branch"])
def test_readonly_mechanical_with_worktree_keeps_start_tree_resolution(tmp_path, monkeypatch, selector):
    from scripts.agent_runtime.kimi_admission import worktree_trees

    repo = _lockfile_repo(tmp_path)
    commit = _git(repo, "rev-parse", "HEAD")
    calls = []

    def start_trees(args, **kwargs):
        calls.append(args)
        return worktree_trees(repo), commit

    monkeypatch.setattr(delegate, "_kimi_start_trees", start_trees)
    extra = (selector,) if selector == "--worktree" else (selector, "existing-branch")
    args = _mechanical_canary_args(*extra)
    refusal, start, target = _content_gate(args, repo)
    assert refusal is None and target.model == "claude-haiku-5-5"
    assert start == commit and calls == [args]


@pytest.mark.parametrize("agent,model,path", [
    ("kimi", "kimi-code/k3", "site/src/components/LiveStatus.tsx"),
    ("claude", "claude-haiku-5-5", "package-lock.json"),
])
def test_write_content_gate_without_worktree_still_refuses(tmp_path, agent, model, path):
    args = _mechanical_canary_args(
        "--agent", agent, "--model", model, "--mode", "workspace-write",
        "--research-task-family", "routine_mechanical", "--research-owned-path", path, "--owned-path", path,
    )
    # Remove the canary's research path when checking Kimi's narrower allowlist.
    args.research_owned_path = [path]
    refusal, start, target = _content_gate(args, tmp_path)
    assert refusal and start is None and target is None
    if agent == "kimi":
        assert "ROUTING REFUSED: KIMI CODING-ONLY" in refusal and "ValueError" in refusal
        with pytest.raises(ValueError, match="workspace-write without a dispatch worktree"):
            delegate._kimi_start_trees(
                args, agent=agent, target_repo_root=tmp_path, validated_worktree=None, validated_cwd=None,
            )
    else:
        assert refusal == "MECHANICAL_TASK_REFUSED: task input unavailable at tree resolution (ValueError) (#9996)"


def _load_rises_after_the_first_probe(monkeypatch) -> dict[str, int]:
    """The early check sees a quiet host; every later probe sees load over the limit (the impl-8654-r3 incident)."""
    calls = {"n": 0}

    def probe():
        calls["n"] += 1
        load = 1.0 if calls["n"] == 1 else 40.0
        return dispatch_admission.HostProbe(mem_available_bytes=64 * _GIB, load1=load, cpu_count=8, proc_available=True)

    monkeypatch.setattr(dispatch_admission, "probe_host", probe)
    return calls


def test_refused_dispatch_leaves_no_worktree_registration_or_task_record(tasks_dir, tmp_path, monkeypatch, capsys):
    repo = _scratch_repo(tmp_path)
    worktree = _dispatch_worktree(tasks_dir, "wt-refused")
    _stub_worktree(monkeypatch, tasks_dir)

    def real_worktree_add(**_kwargs):
        _git(repo, "worktree", "add", "-q", "-b", "codex/adm", str(worktree), "HEAD")
        return worktree, "codex/adm", {"base_sha": _git(repo, "rev-parse", "HEAD"), "layout": "dispatch"}

    monkeypatch.setattr(delegate, "_ensure_worktree", real_worktree_add)
    real_popen = subprocess.Popen

    def popen_git_only(cmd, *args, **kwargs):
        if cmd[0] != "git":
            pytest.fail("a refused dispatch must not spawn")
        return real_popen(cmd, *args, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "Popen", popen_git_only)
    probes = _load_rises_after_the_first_probe(monkeypatch)
    args = _live_danger_args(tasks_dir, "adm-refused")
    args.worktree = str(worktree)

    rc = delegate.cmd_dispatch(args)

    assert rc == delegate._ADMISSION_REFUSED_EXIT
    assert probes["n"] == 2
    assert "load 5.00 per CPU" in capsys.readouterr().err
    assert not worktree.exists()
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1
    assert not delegate._state_path("adm-refused").exists()
    assert not list(tasks_dir.glob("adm-refused*.json"))


def test_admitted_dispatch_holds_its_slot_while_the_worktree_is_created(tasks_dir, monkeypatch):
    """The hold published under the admission lock counts for other dispatches until the full record replaces it."""
    _stub_worktree(monkeypatch, tasks_dir)
    seen: dict[str, object] = {}

    def ensure_worktree(**kwargs):
        seen["record"] = delegate._read_state(delegate._state_path("adm-held"))
        seen["live"] = dispatch_admission.scan_task_records(tasks_dir).live_task_ids
        return _dispatch_worktree(tasks_dir), "codex/adm", {"base_sha": "abc1234", "layout": "dispatch"}

    monkeypatch.setattr(delegate, "_ensure_worktree", ensure_worktree)

    class _Proc:
        pid = 13579
        stdin = _FakeStdin()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_args, **_kwargs: _Proc())

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-held")) == 0

    held = seen["record"]
    assert isinstance(held, dict)
    assert held["status"] == "spawning" and held["pid"] is None and held["mode"] == "danger"
    assert held[dispatch_admission.ADMISSION_HOLD_KEY]["owner_pid"] == os.getpid()
    assert seen["live"] == ("adm-held",)
    final = delegate._read_state(delegate._state_path("adm-held"))
    assert final is not None
    assert dispatch_admission.ADMISSION_HOLD_KEY not in final
    assert final["admission"] == held["admission"]


def test_dispatch_that_stops_after_admission_drops_its_hold(tasks_dir, monkeypatch, capsys):
    from scripts.fleet import ignored_task_output

    _stub_worktree(monkeypatch, tasks_dir)
    inventory = ignored_task_output.creation_inventory

    def inventory_then_disappear(worktree, **kwargs):
        # Simulate loss after successful preparation, before record publication.
        # An already-missing tree now correctly fails the creation inventory first.
        baseline = inventory(worktree, **kwargs)
        worktree.rmdir()
        return baseline

    monkeypatch.setattr(ignored_task_output, "creation_inventory", inventory_then_disappear)
    monkeypatch.setattr(delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("must not spawn"))

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-stopped")) == 1

    assert "disappeared before its task record was published" in capsys.readouterr().err
    assert not delegate._state_path("adm-stopped").exists()


def test_worktree_reservation_keeps_the_admission_hold_and_retire_restores_it(tasks_dir):
    admission = {"admitted": True}
    delegate._publish_admission_hold("adm-prep", "nonce-p", mode="workspace-write", admission=admission)
    owner = dispatch_admission.new_admission_hold("nonce-p")
    prep = {
        "path": str(tasks_dir / "wt"),
        "run_nonce": "nonce-p",
        "reserved_at": "2026-09-24T00:00:00+00:00",
        "owner_pid": owner["owner_pid"],
        "owner_start": owner["owner_start"],
    }

    delegate._publish_worktree_prep("adm-prep", "nonce-p", prep)
    reserved = delegate._read_state(delegate._state_path("adm-prep"))
    assert reserved["worktree_prep"] == prep
    assert reserved["mode"] == "workspace-write" and reserved["admission"] == admission
    assert dispatch_admission.scan_task_records(tasks_dir).live_task_ids == ("adm-prep",)

    delegate._retire_worktree_prep("adm-prep", "nonce-p")
    restored = delegate._read_state(delegate._state_path("adm-prep"))
    assert "worktree_prep" not in restored
    assert restored[dispatch_admission.ADMISSION_HOLD_KEY]["owner_pid"] == os.getpid()
    assert dispatch_admission.scan_task_records(tasks_dir).live_task_ids == ("adm-prep",)

    delegate._release_admission_hold("adm-prep", "nonce-p")
    assert not delegate._state_path("adm-prep").exists()


def test_admission_hold_refuses_to_overwrite_another_runs_live_record(tasks_dir):
    _running_record(tasks_dir, "adm-dup", pid=os.getpid())

    with pytest.raises(RuntimeError, match="refusing to overwrite"):
        delegate._publish_admission_hold("adm-dup", "nonce-other", mode="danger", admission={})


@pytest.mark.parametrize(
    ("block", "reason"),
    [
        ("worktree_prep", "dispatch_died_during_worktree_prep"),
        (dispatch_admission.ADMISSION_HOLD_KEY, dispatch_admission.ORPHANED_HOLD_REASON),
    ],
)
def test_admission_marks_a_record_whose_dispatcher_died_crashed(tasks_dir, block, reason):
    """Admission heals orphaned pid-less records with the same healer status/wait/list/reconcile use."""
    from tests.worktree_prep_helpers import exited_process_identity

    pid, start = exited_process_identity()
    tasks_dir.mkdir(parents=True, exist_ok=True)
    path = tasks_dir / "orphan.json"
    path.write_text(
        json.dumps(
            {
                "task_id": "orphan",
                "run_nonce": "nonce-orphan",
                "status": "spawning",
                "pid": None,
                "mode": "workspace-write",
                "started_at": datetime.now(UTC).isoformat(),
                block: {"run_nonce": "nonce-orphan", "owner_pid": pid, "owner_start": start},
            }
        ),
        encoding="utf-8",
    )

    decision = delegate._evaluate_dispatch_admission("workspace-write", sweep=True)

    assert decision.live_task_ids == ()
    assert decision.dead_task_ids == ("orphan",)
    healed = json.loads(path.read_text(encoding="utf-8"))
    assert healed["status"] == "crashed"
    assert healed["returncode_reason"] == reason
    assert "marked crashed by admission probe" in healed["stderr_excerpt"]


def test_terminal_fields_record_peak_rss_of_reaped_children(monkeypatch):
    class _Usage:
        ru_maxrss = 3 * 1024 * 1024 if sys.platform == "darwin" else 3 * 1024  # 3 MiB

    monkeypatch.setattr(resource, "getrusage", lambda _who: _Usage())

    fields = delegate._core_terminal_fields(
        status="done",
        duration_s=1.0,
        response="ok",
        result_file=None,
        stderr_excerpt=None,
        returncode=0,
        returncode_reason=None,
        dirty_on_exit=False,
        commits_ahead=1,
        needs_finalize=False,
        finalize_error=None,
        last_error=None,
    )

    assert fields["peak_rss_mib"] == 3.0


def test_capacity_pick_prints_the_admission_line(tmp_path, monkeypatch, capsys):
    from scripts.fleet import usage

    tasks = tmp_path / "tasks"
    _running_record(tasks, "busy", pid=515151)
    dead = _running_record(tasks, "gone", pid=424242)
    monkeypatch.setattr(dispatch_admission, "process_alive", lambda pid: pid == 515151)
    monkeypatch.setattr(dispatch_admission, "slice_usage_clause", lambda: None)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    monkeypatch.setattr(
        usage,
        "read_budget",
        lambda **_kwargs: {"agents": {}, "recommendation": {"warnings": []}, "diagnostics": {}},
    )

    assert capacity_pick.main([]) == 0
    assert capsys.readouterr().out.splitlines()[-1] == (
        "admission (write dispatch): would admit now | live write workers 1/2, "
        "MemAvailable 64.0 GiB (floor 8.5 GiB), load 0.00 per CPU (limit 1.00), "
        "lu.slice pool check skipped (test host); "
        "1 record(s) dead pid, not counted: gone"
    )

    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "1")
    assert capacity_pick.main(["--json"]) == 0
    admission = json.loads(capsys.readouterr().out)["admission"]
    assert admission["admitted"] is False
    assert admission["line"].startswith("admission (write dispatch): would REFUSE now: live write workers 1/1")
    # capacity_pick only reports; marking dead records crashed is dispatch's job.
    assert json.loads(dead.read_text(encoding="utf-8"))["status"] == "running"


def test_live_dispatch_admitted_line_shows_a_skipped_pool_check(tasks_dir, tmp_path, monkeypatch, capsys):
    """delegate.py configures no logging, so the pool skip reason must be on the admitted line (#9975)."""
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setenv("LU_SLICE_CGROUP", str(tmp_path / "absent" / "lu.slice"))

    class _Proc:
        pid = 13580
        stdin = _FakeStdin()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda cmd, **_kwargs: _Proc())

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-pool-skip")) == 0

    admitted = [line for line in capsys.readouterr().err.splitlines() if "dispatch admission: admitted" in line]
    assert len(admitted) == 1
    assert "lu.slice pool check skipped (lu.slice memory.current unavailable: " in admitted[0]
    state = delegate._read_state(delegate._state_path("adm-pool-skip"))
    assert state is not None
    assert "memory.current unavailable" in state["admission"]["pool_check_skipped"]
