"""delegate.py dispatch host admission, prompt liveness and peak RSS (#8645 part A).

Task records live under tmp_path. Memory and load come from a monkeypatched
probe; no test allocates memory, generates load, or spawns a worker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import shutil
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


def test_admission_reads_once_and_parses_only_active_records(tasks_dir, monkeypatch):
    tasks_dir.mkdir()
    for index in range(200):
        (tasks_dir / f"finished-{index}.json").write_text(json.dumps({"status": "done", "pid": 123}))
    _running_record(tasks_dir, "active", pid=os.getpid())
    reads = []
    parses = []
    read_bytes = Path.read_bytes
    loads = json.loads

    def read(path):
        if path.parent == tasks_dir:
            reads.append(path.name)
        return read_bytes(path)

    def parse(raw, *args, **kwargs):
        result = loads(raw, *args, **kwargs)
        if isinstance(result, dict) and result.get("status") in ("running", "done"):
            parses.append(result["status"])
        return result

    monkeypatch.setattr(Path, "read_bytes", read)
    monkeypatch.setattr(json, "loads", parse)
    monkeypatch.setattr(delegate, "_read_state", lambda *_: pytest.fail("admission must not hydrate task sidecars"))
    result = delegate._evaluate_dispatch_admission("danger", sweep=False)
    assert result.live_task_ids == ("active",)
    assert parses == ["running"]
    assert len(reads) == len(set(reads)) == 201


@pytest.mark.parametrize("block", ["admission_hold", "worktree_prep"])
@pytest.mark.parametrize("reader", ["admission", "reconcile"])
@pytest.mark.parametrize("real_namespace", [False, True], ids=["hermetic", "bwrap"])
def test_foreign_dispatcher_keeps_hold_and_record(tasks_dir, tmp_path, monkeypatch, block, reader, real_namespace):
    from scripts.guardrails.delegate_ownership import OwnershipLedger
    from scripts.orchestration import dead_worker_state as dead
    from scripts.orchestration import reconcile_sweep

    proc = None
    if real_namespace:
        if not shutil.which("bwrap"):
            pytest.skip("bwrap unavailable; hermetic namespace cases still run")
        code = """
import json, sys
from scripts.orchestration.dispatch_admission import new_admission_hold
print(json.dumps(new_admission_hold('namespace-nonce')), flush=True)
sys.stdin.read()
"""
        proc = subprocess.Popen(
            ["bwrap", "--unshare-pid", "--dev-bind", "/", "/", "--proc", "/proc", sys.executable, "-c", code],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        line = proc.stdout.readline()
        if not line:
            _out, err = proc.communicate(timeout=10)
            if any(reason in err for reason in ("Operation not permitted", "No permissions", "Permission denied")):
                pytest.skip(f"second PID namespace unavailable: {err.strip()}")
            pytest.fail(f"namespace dispatcher failed: {err.strip()}")
        hold = json.loads(line)
    else:
        hold = {
            "run_nonce": "namespace-nonce", "owner_pid": 999_999_998, "owner_start": 100,
            "owner_identity": {
                "pid": 999_999_998, "start_time": 100, "host_pid": None,
                "pid_namespace": "pid:[999999]", "recorder_pid_namespace": "pid:[999999]",
            },
        }
        monkeypatch.setattr(dead, "_pid_namespace", lambda process="self": dead.INITIAL_PID_NAMESPACE)
        monkeypatch.setattr(dead, "_proc_pid_namespace", lambda: dead.INITIAL_PID_NAMESPACE)
    try:
        tasks_dir.mkdir(exist_ok=True)
        path = tasks_dir / "foreign-dispatcher.json"
        record = {
            "task_id": "foreign-dispatcher", "run_nonce": "namespace-nonce", "status": "spawning",
            "mode": "danger", "pid": None, block: hold,
        }
        path.write_text(json.dumps(record))
        before = path.read_bytes()
        if reader == "admission":
            result = delegate._evaluate_dispatch_admission("danger", sweep=True)
            assert result.dead_task_ids == ()
            assert result.live_task_ids == ("foreign-dispatcher",)
        else:
            result = reconcile_sweep.run_reconcile_sweep(
                apply=True, task_dir=tasks_dir,
                ledger=OwnershipLedger(tmp_path / "claims.sqlite3", task_state_dir=tasks_dir),
            )
            assert result.zombie_tasks == []
            assert result.live_tasks == ["foreign-dispatcher"]
        assert path.read_bytes() == before
        if real_namespace:
            assert proc.poll() is None
    finally:
        if proc is not None and proc.poll() is None:
            proc.communicate(input="", timeout=10)


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


@pytest.mark.parametrize("model", ["grok-4.7", "glm-5", "other-model", "unknown", ""])
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


def test_omitted_model_on_allowed_agent_waits_for_resolution():
    args = delegate.build_parser().parse_args([
        "dispatch", "--task-id", "synthetic-language-job", "--agent", "claude", "--language-lane",
        "--research-task-family", "reviews",
    ])
    delegate._require_ukrainian_model_family(args, None)


def test_omitted_model_on_disallowed_agent_refused():
    args = delegate.build_parser().parse_args([
        "dispatch", "--task-id", "synthetic-language-job", "--agent", "grok", "--language-lane",
        "--research-task-family", "data",
    ])
    with pytest.raises(delegate._DispatchRouteRefused, match="UKRAINIAN_MODEL_REFUSED"):
        delegate._require_ukrainian_model_family(args, None)


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
    from agent_runtime import telemetry

    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setattr(telemetry, "_probe_version", lambda *_a, **_k: "test")
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
    monkeypatch.setattr(
        dispatch_admission.admission_shadow, "read_pressure",
        lambda _: {"cpu.some": {"avg10": None, "avg60": None}},
    )
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
        "lu.slice pool check skipped (test host), test-slot queue check skipped (test host), "
        "disk check skipped (test host), PSI shadow unknown (calibration only; "
        "unknown: test journal not configured; CPU ownership unknown, unattributed load unknown); "
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


def _full_disk(monkeypatch, *readings: float) -> dict[str, list]:
    """Disk readings in order (the last repeats); a fake reaper and alert publisher (#10776)."""
    seen: dict[str, list] = {"readings": list(readings), "reaper": [], "alerts": []}

    def probe():
        values = seen["readings"]
        used = values.pop(0) if len(values) > 1 else values[0]
        used_bytes = int(400 * _GIB * used / 100)
        return dispatch_admission.DiskProbe(used_bytes=used_bytes, free_bytes=400 * _GIB - used_bytes)

    def reaper(repo_root, _timeout_s=None):
        seen["reaper"].append(repo_root)
        return dispatch_admission.ReaperOutcome(ran=True, detail="reaper removed 0 worktree(s)")

    monkeypatch.setattr(dispatch_admission, "probe_disk", probe)
    monkeypatch.setattr(dispatch_admission, "run_disk_reaper", reaper)
    monkeypatch.setattr(dispatch_admission, "post_disk_alert", lambda body, _key: seen["alerts"].append(body))
    return seen


def test_live_dispatch_on_a_full_disk_reaps_once_then_refuses_with_no_side_effects(tasks_dir, monkeypatch, capsys):
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setattr(
        delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("a refused dispatch must not spawn")
    )
    disk = _full_disk(monkeypatch, 90.0)

    rc = delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-disk-full"))

    assert rc == delegate._ADMISSION_DISK_REFUSED_EXIT == 4
    assert len(disk["reaper"]) == 1
    assert len(disk["alerts"]) == 1
    refusal = [line for line in capsys.readouterr().err.splitlines() if "admission refused" in line]
    assert len(refusal) == 1
    assert (
        "disk 90.0% used, 40.0 GiB free on the .worktrees filesystem is at or above the refuse threshold of 90% "
        "(DISPATCH_DISK_REFUSE_USED_PERCENT=90); reaper removed 0 worktree(s)"
    ) in refusal[0]
    assert not delegate._state_path("adm-disk-full").exists()


def test_live_dispatch_admitted_after_the_reaper_frees_space_reaps_only_outside_the_lock(
    tasks_dir, monkeypatch, capsys
):
    _stub_worktree(monkeypatch, tasks_dir)

    class _Proc:
        pid = 13581
        stdin = _FakeStdin()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda cmd, **_kwargs: _Proc())
    disk = _full_disk(monkeypatch, 88.0, 60.0)

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "adm-disk-reaped")) == 0

    assert len(disk["reaper"]) == 1  # the locked recheck measures again but never reaps
    assert disk["alerts"] == []
    admitted = [line for line in capsys.readouterr().err.splitlines() if "dispatch admission: admitted" in line]
    assert len(admitted) == 1
    assert "disk 60.0% used, 160.0 GiB free (reap at 85%, refuse at 90%, alert at 80%) [reaper removed 0 worktree(s), 88.0% before]" in (
        admitted[0]
    )
    state = delegate._read_state(delegate._state_path("adm-disk-reaped"))
    assert state is not None
    assert state["admission"]["disk_used_percent"] == 60.0
    assert state["admission"]["disk_free_gib"] == 160.0


def test_dry_run_on_a_full_disk_refuses_without_running_the_reaper(tasks_dir, monkeypatch, capsys):
    _pin_origin_main_to_head(monkeypatch)
    disk = _full_disk(monkeypatch, 92.0)

    assert delegate.cmd_dispatch(_dry_run_args()) == delegate._ADMISSION_DISK_REFUSED_EXIT

    assert disk["reaper"] == []
    assert "92.0% used, 32.0 GiB free" in capsys.readouterr().err


def test_read_only_dispatch_is_exempt_from_the_disk_guard(tasks_dir, monkeypatch, capsys):
    disk = _full_disk(monkeypatch, 99.0)

    assert delegate.cmd_dispatch(_dry_run_args(mode="read-only", task_id="adm-disk-reader")) == 0

    assert disk["reaper"] == [] and disk["alerts"] == []
    assert "admission" not in capsys.readouterr().err


def test_capacity_pick_shows_the_disk_decision_without_reaping(tmp_path, monkeypatch, capsys):
    from scripts.fleet import usage

    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(dispatch_admission, "slice_usage_clause", lambda: None)
    monkeypatch.setattr(
        dispatch_admission.admission_shadow, "read_pressure",
        lambda _: {"cpu.some": {"avg10": None, "avg60": None}},
    )
    monkeypatch.setattr(capacity_pick, "fetch_active_in_flight", lambda **_kwargs: {})
    monkeypatch.setattr(
        usage,
        "read_budget",
        lambda **_kwargs: {"agents": {}, "recommendation": {"warnings": []}, "diagnostics": {}},
    )
    disk = _full_disk(monkeypatch, 82.0)

    assert capacity_pick.main([]) == 0
    assert capsys.readouterr().out.splitlines()[-1].endswith(
        "disk 82.0% used, 72.0 GiB free (reap at 85%, refuse at 90%, alert at 80%) [epics alert posted], "
        "PSI shadow unknown (calibration only; unknown: test journal not configured; "
        "CPU ownership unknown, unattributed load unknown)"
    )

    disk["readings"] = [91.0]
    assert capacity_pick.main(["--json"]) == 0
    admission = json.loads(capsys.readouterr().out)["admission"]
    assert admission["admitted"] is False
    assert admission["line"].startswith(
        "admission (write dispatch): would REFUSE now: disk 91.0% used, 36.0 GiB free on the .worktrees "
        "filesystem is at or above the refuse threshold of 90% (DISPATCH_DISK_REFUSE_USED_PERCENT=90); "
        "reaper not run in this check"
    )
    assert admission["disk_used_percent"] == 91.0
    assert admission["disk_free_gib"] == 36.0
    assert disk["reaper"] == []  # capacity_pick only reports
    assert len(disk["alerts"]) == 1  # rate-limited across both calls


# --- Round 3 (#10776): a disk refusal is a hard stop in both gates; reuse skips the guard -----------


def test_a_force_reason_never_turns_a_disk_refusal_into_an_admit(tasks_dir, monkeypatch, capsys):
    """Review reproducer: a 90% disk passed to the pre-lock report with a force reason."""
    _full_disk(monkeypatch, 90.0)
    decision = delegate._evaluate_dispatch_admission("danger", sweep=False)
    assert not decision.admitted

    rc = delegate._report_dispatch_admission(decision, force_reason="hotfix while the disk drains")

    assert rc == delegate._ADMISSION_DISK_REFUSED_EXIT
    assert not delegate._admission_allows_dispatch(decision, force_reason="hotfix while the disk drains")
    err = capsys.readouterr().err
    assert "--force-admission cannot override a full disk" in err
    assert "overridden by --force-admission" not in err


def test_a_force_reason_still_overrides_the_other_checks(tasks_dir, monkeypatch, capsys):
    _full_disk(monkeypatch, 50.0)
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")
    decision = delegate._evaluate_dispatch_admission("danger", sweep=False)

    assert delegate._report_dispatch_admission(decision, force_reason="drain") is None
    assert delegate._admission_allows_dispatch(decision, force_reason="drain")
    assert not delegate._admission_allows_dispatch(decision, force_reason=None)
    assert delegate._report_dispatch_admission(decision, force_reason=None) == delegate._ADMISSION_REFUSED_EXIT
    assert "overridden by --force-admission ('drain')" in capsys.readouterr().err


def test_live_forced_dispatch_on_a_full_disk_stops_at_the_first_gate(tasks_dir, monkeypatch, capsys):
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setattr(
        delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("a refused dispatch must not spawn")
    )
    disk = _full_disk(monkeypatch, 90.0)
    args = _live_danger_args(tasks_dir, "adm-disk-forced")
    args.force_admission = "hotfix while the disk drains"

    assert delegate.cmd_dispatch(args) == delegate._ADMISSION_DISK_REFUSED_EXIT

    assert len(disk["reaper"]) == 1
    assert "--force-admission cannot override a full disk" in capsys.readouterr().err
    assert not delegate._state_path("adm-disk-forced").exists()


def test_locked_recheck_holds_a_disk_refusal_against_a_force_reason(tasks_dir, monkeypatch, capsys):
    """The pre-lock check passes; the disk fills before the locked recheck; force must not publish a hold."""
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setattr(
        delegate, "_ensure_worktree", lambda **_kwargs: pytest.fail("a refused dispatch must not create a worktree")
    )
    monkeypatch.setattr(
        delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("a refused dispatch must not spawn")
    )
    monkeypatch.setattr(
        delegate, "_publish_admission_hold", lambda *_args, **_kwargs: pytest.fail("no hold after a disk refusal")
    )
    disk = _full_disk(monkeypatch, 60.0, 90.0)
    args = _live_danger_args(tasks_dir, "adm-disk-locked")
    args.force_admission = "hotfix while the disk drains"

    assert delegate.cmd_dispatch(args) == delegate._ADMISSION_DISK_REFUSED_EXIT

    assert disk["reaper"] == []  # never under the lock
    err = capsys.readouterr().err
    assert "disk 90.0% used" in err and "--force-admission cannot override a full disk" in err
    assert not delegate._state_path("adm-disk-locked").exists()


def test_forced_dry_run_on_a_full_disk_is_refused(tasks_dir, monkeypatch, capsys):
    _pin_origin_main_to_head(monkeypatch)
    disk = _full_disk(monkeypatch, 92.0)

    rc = delegate.cmd_dispatch(_dry_run_args("--force-admission", "hotfix"))

    assert rc == delegate._ADMISSION_DISK_REFUSED_EXIT
    assert disk["reaper"] == []
    assert "--force-admission cannot override a full disk" in capsys.readouterr().err


def test_live_dispatch_reusing_an_existing_worktree_skips_the_disk_guard(tasks_dir, monkeypatch, capsys):
    _stub_worktree(monkeypatch, tasks_dir)

    class _Proc:
        pid = 13583
        stdin = _FakeStdin()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda cmd, **_kwargs: _Proc())
    disk = _full_disk(monkeypatch, 95.0)
    args = _live_danger_args(tasks_dir, "adm-disk-reuse")
    (_dispatch_worktree(tasks_dir) / ".git").write_text("gitdir: elsewhere\n", encoding="utf-8")

    assert delegate.cmd_dispatch(args) == 0

    assert disk["reaper"] == [] and disk["alerts"] == []
    admitted = [line for line in capsys.readouterr().err.splitlines() if "dispatch admission: admitted" in line]
    assert len(admitted) == 1 and "disk check skipped (dispatch reuses an existing worktree)" in admitted[0]


def test_a_reused_worktree_removed_before_the_lock_gets_the_disk_guard_and_is_refused(tasks_dir, monkeypatch, capsys):
    """Review reproducer (round 3): cleanup removes the checkout after reuse detection, at 95%."""
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setattr(
        delegate, "_ensure_worktree", lambda **_kwargs: pytest.fail("no worktree is created on a full disk")
    )
    disk = _full_disk(monkeypatch, 95.0)
    args = _live_danger_args(tasks_dir, "adm-disk-reuse-gone")
    checkout = _dispatch_worktree(tasks_dir) / ".git"
    checkout.write_text("gitdir: elsewhere\n", encoding="utf-8")
    detect = delegate._dispatch_reuses_worktree
    probes: list[bool] = []

    def detect_then_cleanup(*probe_args, **probe_kwargs):
        reused = detect(*probe_args, **probe_kwargs)
        probes.append(reused)
        checkout.unlink(missing_ok=True)  # the cleanup lands right after detection
        return reused

    monkeypatch.setattr(delegate, "_dispatch_reuses_worktree", detect_then_cleanup)

    assert delegate.cmd_dispatch(args) == delegate._ADMISSION_DISK_REFUSED_EXIT

    assert probes == [True, False]  # decided again under the worktree lock, before creation
    assert disk["reaper"] == []  # never under the lock
    err = capsys.readouterr().err
    assert "disk 95.0% used" in err and "reaper not run in this check" in err
    assert not delegate._state_path("adm-disk-reuse-gone").exists()


def test_dispatch_reuses_worktree_detects_existing_checkouts_without_git(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    existing = repo / ".worktrees" / "dispatch" / "codex" / "old"
    (existing / ".git").parent.mkdir(parents=True)
    (existing / ".git").write_text("gitdir: x\n", encoding="utf-8")
    bare_dir = repo / ".worktrees" / "dispatch" / "codex" / "empty"
    bare_dir.mkdir(parents=True)
    kwargs = {"agent": "codex", "task_id": "old", "repo_root": repo}
    monkeypatch.setattr(
        delegate, "_resolve_verified_worktree_path", lambda _path: pytest.fail("the reuse probe must not run git")
    )

    assert delegate._dispatch_reuses_worktree(str(existing), **kwargs)
    assert not delegate._dispatch_reuses_worktree(str(bare_dir), **kwargs)
    assert not delegate._dispatch_reuses_worktree(str(repo / "nope"), **kwargs)
    assert not delegate._dispatch_reuses_worktree(None, **kwargs)  # --cwd dispatches keep the guard (#8775)
    monkeypatch.setattr(delegate, "_auto_worktree_path", lambda agent, task_id, repo_root=None: existing)
    assert delegate._dispatch_reuses_worktree("auto", **kwargs)
    monkeypatch.setattr(delegate, "_auto_worktree_path", lambda agent, task_id, repo_root=None: repo / "new")
    assert not delegate._dispatch_reuses_worktree("auto", **kwargs)
    # A validated explicit path is probed as is, never resolved again (#8775).
    monkeypatch.setattr(
        delegate, "_normalize_worktree_path", lambda *_a, **_k: pytest.fail("the validated path was resolved again")
    )
    assert delegate._dispatch_reuses_worktree(str(existing), validated=existing, **kwargs)
    assert not delegate._dispatch_reuses_worktree(str(bare_dir), validated=bare_dir, **kwargs)


# --- #10799: a refused dispatch costs almost no CPU ---------------------------------------------

_OVERLOADED = dispatch_admission.HostProbe(mem_available_bytes=1 * _GIB, load1=40.0, cpu_count=8, proc_available=True)
_HISTORY_RECORDS = 400
_UNMATCHED_LEASES = 6


def _seed_history(tasks: Path, scratch: Path, *, records: int = _HISTORY_RECORDS) -> None:
    """A realistic hot history: terminal records (every tenth with snapshot sidecars), two live
    codex writers, and young scratch leases no record owns (the case the sweep scanned per lease)."""
    tasks.mkdir(parents=True, exist_ok=True)
    for index in range(records):
        task_id = f"history-{index:05d}"
        record = {
            "task_id": task_id, "status": "done", "mode": "workspace-write", "agent": "claude",
            "pid": 100_000 + index, "run_nonce": f"nonce-{index}", "prompt": "brief " * 300,
        }
        (tasks / f"{task_id}.json").write_text(json.dumps(record), encoding="utf-8")
        if index % 10 == 0:
            for phase in ("pre", "post"):
                sidecar = delegate._read_only_snapshot_sidecar_path(task_id, phase)
                sidecar.parent.mkdir(parents=True, exist_ok=True)
                sidecar.write_text(json.dumps({f"path-{n}.txt": "0" * 40 for n in range(200)}), encoding="utf-8")
    for task_id in ("live-codex-a", "live-codex-b"):
        path = _running_record(tasks, task_id, pid=os.getpid())
        path.write_text(json.dumps({**json.loads(path.read_text(encoding="utf-8")), "agent": "codex"}), encoding="utf-8")
    namespace = scratch / "learn-ukrainian"
    for index in range(_UNMATCHED_LEASES):
        (namespace / f"unowned-lease-{index}").mkdir(parents=True)


def _tree_state(root: Path) -> dict[str, tuple[int, int]]:
    return {
        str(path.relative_to(root)): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
    }


def _write_dispatch_args(task_id: str, *extra: str):
    return delegate.build_parser().parse_args([
        "dispatch", "--agent", "codex", "--task-id", task_id, "--initiator", "codex", "--prompt", "test",
        "--mode", "workspace-write", "--worktree", "--owned-path", "scripts/example.py", *extra,
    ])


def _local_placement(monkeypatch) -> None:
    monkeypatch.setattr(delegate, "_dispatch_may_forward", lambda: False)


def _forbid_expensive_reads(monkeypatch) -> list[str]:
    """Record every call into the work an early refusal must skip (some callers suppress exceptions)."""
    from scripts.orchestration import task_record_store

    calls: list[str] = []

    def sentinel(name):
        def forbidden(*_args, **_kwargs):
            calls.append(name)
            raise AssertionError(f"{name} ran before the early host refusal")

        return forbidden

    for owner, name in (
        (delegate, "_sweep_runtime_tmp_orphans"),
        (delegate, "_read_runtime_tmp_state_for_legacy_lease"),
        (delegate, "_hydrate_read_only_checkout_snapshots"),
        (delegate, "_load_read_only_snapshot_sidecar"),
        (delegate, "_check_capacity_hint"),
        (delegate, "_run_dor_preflight"),
        (delegate, "_authoring_review_admission"),
        (dispatch_admission, "scan_task_records"),
        (task_record_store, "iter_task_records"),
    ):
        monkeypatch.setattr(owner, name, sentinel(name))
    return calls


@pytest.mark.parametrize("dry_run", [False, True], ids=["live", "dry-run"])
def test_early_host_refusal_skips_the_sweep_hint_and_history(tasks_dir, tmp_path, monkeypatch, capsys, dry_run):
    _seed_history(tasks_dir, tmp_path / "scratch")
    _local_placement(monkeypatch)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: _OVERLOADED)
    calls = _forbid_expensive_reads(monkeypatch)
    before = _tree_state(tmp_path)

    rc = delegate.cmd_dispatch(_write_dispatch_args("early-refusal", *(["--dry-run"] if dry_run else [])))

    assert rc == delegate._ADMISSION_REFUSED_EXIT == 3
    assert calls == []
    refusal = [line for line in capsys.readouterr().err.splitlines() if "admission" in line]
    assert refusal == [
        "❌ dispatch admission refused for a workspace-write worker: MemAvailable 1.0 GiB is below the floor of "
        "8.5 GiB (DISPATCH_MIN_MEM_AVAILABLE_GIB=8.5); load 5.00 per CPU (1-minute load 40.00 on 8 CPUs) is above "
        "the limit of 1.00 (DISPATCH_MAX_LOAD_PER_CPU=1). Wait for a worker to finish or for the host to recover, "
        'raise the threshold through the named environment variable, or pass --force-admission "<reason>" to override.'
    ]
    assert _tree_state(tmp_path) == before


def test_early_refusal_text_matches_full_admission(tasks_dir, monkeypatch):
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: _OVERLOADED)

    early = dispatch_admission.precheck("danger")
    full = dispatch_admission.evaluate("danger", tasks_dir)

    assert early is not None and not early.admitted and not full.admitted
    assert early.failures == full.failures
    assert early.refusal_line() == full.refusal_line()


@pytest.mark.parametrize(
    "probe",
    [
        dispatch_admission.HostProbe(mem_available_bytes=64 * _GIB, load1=1.0, cpu_count=8, proc_available=True),
        dispatch_admission.HostProbe(mem_available_bytes=None, load1=None, cpu_count=8, proc_available=False),
    ],
    ids=["healthy", "unknown"],
)
def test_precheck_admits_nothing_and_refuses_only_failures(probe, monkeypatch):
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: probe)
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")  # the cap is the full admission's check

    assert dispatch_admission.precheck("workspace-write") is None


def test_precheck_exempts_read_only_and_rejects_invalid_thresholds(monkeypatch):
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: _OVERLOADED)
    assert dispatch_admission.precheck("read-only") is None
    monkeypatch.setenv("DISPATCH_MAX_LOAD_PER_CPU", "lots")
    with pytest.raises(ValueError, match="DISPATCH_MAX_LOAD_PER_CPU='lots' is not a number"):
        dispatch_admission.precheck("danger")


def test_read_only_dispatch_on_an_overloaded_host_is_exempt(tasks_dir, monkeypatch, capsys):
    _local_placement(monkeypatch)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: _OVERLOADED)

    assert delegate.cmd_dispatch(_dry_run_args(mode="read-only", task_id="early-reader")) == 0
    assert "admission" not in capsys.readouterr().err


def test_early_refusal_steps_aside_for_a_full_disk(tasks_dir, monkeypatch, capsys):
    """An overloaded host with a full disk still gets the reaper attempt and the disk hard stop (#10776)."""
    _stub_worktree(monkeypatch, tasks_dir)
    _local_placement(monkeypatch)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: _OVERLOADED)
    monkeypatch.setattr(
        delegate.subprocess, "Popen", lambda *_args, **_kwargs: pytest.fail("a refused dispatch must not spawn")
    )
    disk = _full_disk(monkeypatch, 90.0)

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "early-full-disk")) == 4

    assert len(disk["reaper"]) == 1
    refusal = [line for line in capsys.readouterr().err.splitlines() if "admission refused" in line]
    assert len(refusal) == 1 and "MemAvailable 1.0 GiB" in refusal[0] and "refuse threshold" in refusal[0]
    assert not delegate._state_path("early-full-disk").exists()


def test_force_admission_skips_the_early_refusal(tasks_dir, monkeypatch, capsys):
    _stub_worktree(monkeypatch, tasks_dir)
    _local_placement(monkeypatch)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: _OVERLOADED)

    args = _dry_run_args("--force-admission", "drain one worker", task_id="early-forced")
    assert delegate.cmd_dispatch(args) == 0

    assert "overridden by --force-admission ('drain one worker'): MemAvailable 1.0 GiB" in capsys.readouterr().err
    assert delegate._read_state(delegate._state_path(args.task_id))["admission"]["forced"] is True


def test_early_refusal_reports_an_invalid_threshold_as_an_invalid_request(tasks_dir, monkeypatch, capsys):
    _local_placement(monkeypatch)
    monkeypatch.setenv("DISPATCH_MIN_MEM_AVAILABLE_GIB", "-1")

    assert delegate.cmd_dispatch(_write_dispatch_args("early-invalid")) == 2
    assert "invalid dispatch admission threshold: DISPATCH_MIN_MEM_AVAILABLE_GIB='-1' must be zero or more" in (
        capsys.readouterr().err
    )


def test_dispatch_that_passes_the_early_check_runs_as_before(tasks_dir, monkeypatch, capsys):
    _stub_worktree(monkeypatch, tasks_dir)
    _local_placement(monkeypatch)
    prechecks = []
    real_precheck = dispatch_admission.precheck
    monkeypatch.setattr(
        dispatch_admission, "precheck", lambda mode, **kwargs: prechecks.append(mode) or real_precheck(mode, **kwargs)
    )
    spawned: list[list[str]] = []

    class _Proc:
        pid = 13581
        stdin = _FakeStdin()

    monkeypatch.setattr(delegate.subprocess, "Popen", lambda cmd, **_kwargs: spawned.append(cmd) or _Proc())

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "early-passed")) == 0

    assert prechecks == ["danger"]
    assert len([cmd for cmd in spawned if "_worker" in cmd]) == 1
    err = capsys.readouterr().err
    assert len([line for line in err.splitlines() if "dispatch admission: admitted — live write workers 0/2" in line]) == 1
    assert delegate._read_state(delegate._state_path("early-passed"))["admission"]["admitted"] is True


def test_forwarding_client_does_not_refuse_on_its_own_load(tasks_dir, monkeypatch):
    """A client that may forward checks no local load: the host that runs the worker admits it."""
    _stub_worktree(monkeypatch, tasks_dir)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: _OVERLOADED)
    monkeypatch.setattr(sys, "argv", ["scripts/delegate.py", "dispatch", "--agent", "codex"])
    monkeypatch.setattr(delegate, "_dispatch_may_forward", lambda: True)
    monkeypatch.setattr(job_host_exec, "decide_dispatch_placement", lambda **_kwargs: ("vps", "available", "host-job"))
    sent = []
    monkeypatch.setattr(job_host_exec, "forward_dispatch", lambda **kwargs: sent.append(kwargs["argv"]) or 0)

    assert delegate.cmd_dispatch(_live_danger_args(tasks_dir, "early-forward")) == 0

    assert len(sent) == 1
    assert not delegate._state_path("early-forward").exists()


@pytest.mark.parametrize("marker", [None, "v1", "plane"])
@pytest.mark.parametrize("allow_notebook", [False, True])
def test_may_forward_agrees_with_placement(tmp_path, monkeypatch, marker, allow_notebook):
    """The network-free answer is the one placement gives when a VPS worker host is available."""
    from tests.orchestration.test_job_host_exec import _entry, _payload

    plane = tmp_path / "batch_state" / "fleet-comms"
    if marker is not None:
        marker_dir = plane / "v1" if marker == "v1" else plane
        marker_dir.mkdir(parents=True)
        (marker_dir / job_host_exec.RETIRED_LOCAL_MARKER).write_text("retired\n", encoding="utf-8")
    if allow_notebook:
        monkeypatch.setenv(job_host_exec.ENV_ALLOW_NOTEBOOK, "1")
    else:
        monkeypatch.delenv(job_host_exec.ENV_ALLOW_NOTEBOOK, raising=False)
    monkeypatch.setattr(delegate, "_REPO_ROOT", tmp_path)

    placement, _reason, _host = job_host_exec.decide_dispatch_placement(
        repo_root=tmp_path, occupancy=_payload(**{"host-job": _entry()})
    )

    assert delegate._dispatch_may_forward() is (placement == "vps")
    assert delegate._dispatch_may_forward() is (marker is not None and not allow_notebook)


def test_runtime_tmp_sweep_resolves_legacy_ownership_once(tmp_path, monkeypatch):
    """Leases no record owns cost one task-id scan per sweep, not one per lease."""
    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(delegate, "scratch_scan_roots", lambda: [tmp_path / "scratch"])
    _seed_history(tasks, tmp_path / "scratch", records=50)
    # A record whose stem differs from its task id still owns its lease through the task-id scan.
    delegate._write_state_atomic(delegate._state_path("legacy/owner"), {"task_id": "legacy/owner", "status": "running"})
    owned = tmp_path / "scratch" / "learn-ukrainian" / delegate._runtime_tmp_lease_name("legacy/owner")
    owned.mkdir()
    reads: list[str] = []
    real_read = delegate._read_state_json
    monkeypatch.setattr(delegate, "_read_state_json", lambda path: reads.append(path.name) or real_read(path))

    result = delegate._sweep_runtime_tmp_orphans()

    assert result["leases_reaped"] == 0 and result["errors"] == 0
    record_count = len(list(tasks.glob("*.json")))
    assert len(reads) <= record_count + 1, len(reads)
    assert delegate._read_runtime_tmp_task_id_marker(owned) == "legacy/owner"


def test_capacity_hint_reads_stored_fields_without_sidecars(tasks_dir, tmp_path, monkeypatch, capsys):
    from scripts.api import lane_health

    _seed_history(tasks_dir, tmp_path / "scratch", records=50)
    monkeypatch.setattr(lane_health, "compute_lane_health", lambda _tasks: {})  # its own reader is not under test
    hydrated = []
    monkeypatch.setattr(delegate, "_hydrate_read_only_checkout_snapshots", lambda state: hydrated.append(state) or state)
    monkeypatch.setattr(delegate, "_load_read_only_snapshot_sidecar", lambda *args: hydrated.append(args))
    parsed = []
    loads = json.loads

    def parse(raw, *args, **kwargs):
        result = loads(raw, *args, **kwargs)
        if isinstance(result, dict) and "status" in result:
            parsed.append(result["status"])
        return result

    monkeypatch.setattr(json, "loads", parse)

    delegate._check_capacity_hint("codex")

    assert hydrated == []
    assert parsed == ["running", "running"]
    assert "lane 'codex' has 2 task(s) in flight while idle capacity is available in: claude" in capsys.readouterr().err


def _fresh_refusal_cpu_s(tmp_path: Path, task_id: str) -> tuple[float, subprocess.CompletedProcess]:
    env = {key: value for key, value in os.environ.items() if key not in {"LU_TEST_DISPATCH_HEALTHY_HOST", "PYTEST_CURRENT_TEST", "LEARN_UKRAINIAN_DISPATCH_TASK_ID"}}
    scratch = tmp_path / "scratch"
    env.update({
        "LU_TASKS_DIR": str(tmp_path / "tasks"),
        "LU_SCRATCH_ROOT": str(scratch),
        "LU_SCRATCH_SCAN_ROOT": str(scratch),
        "TMPDIR": str(tmp_path / "tmp"),
        job_host_exec.ENV_ALLOW_NOTEBOOK: "1",
        # Any real host is below a 1 PiB floor, so the refusal needs no probe stub in the child.
        "DISPATCH_MIN_MEM_AVAILABLE_GIB": "1048576",
        "DISPATCH_ADMISSION_ENV_FILE": "",
        "LU_OPEN_PR_FREEZE_THRESHOLD": "0",
    })
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    proc = subprocess.run(
        [sys.executable, str(Path(delegate.__file__)), "dispatch", "--agent", "codex", "--task-id", task_id,
         "--initiator", "codex", "--prompt", "test", "--mode", "workspace-write", "--worktree",
         "--owned-path", "scripts/example.py"],
        cwd=delegate._REPO_ROOT, env=env, capture_output=True, text=True, timeout=300, check=False,
    )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    return (after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime), proc


@pytest.mark.skipif(not Path("/proc/meminfo").is_file(), reason="the refusal reads MemAvailable from /proc")
def test_early_host_refusal_costs_under_two_cpu_seconds_in_a_fresh_process(tmp_path):
    _seed_history(tmp_path / "tasks", tmp_path / "scratch", records=2_000)
    (tmp_path / "tmp").mkdir()  # the child's TMPDIR: tempfile probes it, so it is not compared
    before = {name: _tree_state(tmp_path / name) for name in ("tasks", "scratch")}

    for attempt in range(3):
        cpu_s, proc = _fresh_refusal_cpu_s(tmp_path, f"early-fresh-{attempt}")
        assert proc.returncode == 3, proc.stderr
        assert "dispatch admission refused for a workspace-write worker: MemAvailable" in proc.stderr
        assert cpu_s < 2.0, f"refusal used {cpu_s:.2f} CPU s"
    assert {name: _tree_state(tmp_path / name) for name in ("tasks", "scratch")} == before


def _freeze_check(monkeypatch, tmp_path, open_prs: int) -> int | None:
    from types import SimpleNamespace

    from scripts.orchestration import pr_freeze

    fetched: list[str] = []

    def fetch(repo):
        fetched.append(repo)
        return open_prs

    monkeypatch.setattr(pr_freeze, "fetch_open_pr_count", fetch)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv(pr_freeze.CACHE_ENV, "0")
    args = argparse.Namespace(mode="workspace-write", branch=None, pr=None, cwd=None, worktree="auto", task_id="freeze")
    repo = SimpleNamespace(github="example/repo", role="public-monorepo")
    return delegate._check_open_pr_freeze(args, repo)


def test_open_pr_freeze_is_off_by_default(monkeypatch, tmp_path, capsys):
    """With no override a new-PR dispatch is admitted however many PRs are open (#11272)."""
    monkeypatch.delenv("LU_OPEN_PR_FREEZE_THRESHOLD", raising=False)
    assert _freeze_check(monkeypatch, tmp_path, open_prs=500) is None
    assert "dispatch refused" not in capsys.readouterr().err


@pytest.mark.parametrize("threshold, open_prs, expected", [("5", 4, None), ("5", 5, 3), ("5", 50, 3), ("0", 500, None)])
def test_open_pr_freeze_explicit_opt_in(monkeypatch, tmp_path, threshold, open_prs, expected):
    monkeypatch.setenv("LU_OPEN_PR_FREEZE_THRESHOLD", threshold)
    assert _freeze_check(monkeypatch, tmp_path, open_prs=open_prs) == expected
