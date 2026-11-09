"""Admission and spawn refusals: Claude account, plan headroom, advisor, pool, disk, credit lane and stale spawn recovery."""

import dataclasses
import json
import os
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.dispatcher import git, providers, store, worker
from scripts.dispatcher.types import Invocation, TaskSpec
from tests.dispatcher.conftest import run_git


@pytest.mark.parametrize(
    "extra,code",
    [
        # Ported from tests/test_delegate.py (the claude_account refusal table): unknown labels.
        (["--agent", "claude", "--claude-account", "c"], "claude_account_unknown"),
        (["--agent", "claude", "--claude-account", "B"], "claude_account_unknown"),
        (["--agent", "codex", "--claude-account", "b"], "claude_account_seat_unsupported"),
        (["--agent", "claude", "--claude-account", "b"], "claude_account_ambient_conflict"),
        # API-key labels (C-2643): the same guard, and only their exact names.
        (["--agent", "claude", "--claude-account", "kk"], "claude_account_ambient_conflict"),
        (["--agent", "claude", "--claude-account", "szb"], "claude_account_ambient_conflict"),
        (["--agent", "claude", "--claude-account", "KK"], "claude_account_unknown"),
        (["--agent", "codex", "--claude-account", "szb"], "claude_account_seat_unsupported"),
    ],
)
def test_dispatch_refuses_claude_account_before_any_side_effect(tmp_path, monkeypatch, capsys, extra, code):
    from scripts.dispatcher import cli

    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fixture-ambient-" + "e" * 30)
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(tmp_path / "absent.json"))
    for target, name in ((git, "create_worktree"), (git, "resolve_repo"), (worker, "start")):
        monkeypatch.setattr(target, name, lambda *_a, _name=name, **_k: pytest.fail(f"{_name} ran before refusal"))

    assert cli.main(["dispatch", "--task-id", "claude-account-refused", "--prompt", "test", "--model", "m", *extra]) == 2

    err = capsys.readouterr().err
    assert f"CLAUDE_ACCOUNT_REFUSED: {code}\n" in err
    assert "fixture-ambient" not in err
    assert not tasks.exists()


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_claude_argv_caps_an_api_key_run_and_leaves_a_subscription_run_alone(tmp_path, mode):
    """An uncapped paid run is the defect: only an API-key label carries ``--max-budget-usd``."""
    from scripts.agent_runtime.attempt_boundary import CLAUDE_API_KEY_BUDGET_USD

    spec = TaskSpec("cap", "claude", "m", None, mode, tmp_path, tmp_path / "p", tmp_path / "f")
    spec.prompt_file.write_bytes(b"prompt")
    build = providers.load("claude").build
    for label, amount in CLAUDE_API_KEY_BUDGET_USD.items():
        invocation = build(dataclasses.replace(spec, claude_account=label), {})
        assert invocation.argv[invocation.argv.index("--max-budget-usd") + 1] == f"{amount:.2f}"
        assert invocation.env.get("CLAUDE_CODE_PROMPT_CACHE_TTL") == ("1h" if mode == "workspace-write" else None)
    lowered = dataclasses.replace(spec, claude_account="kk", options={"max_budget_usd": "2.5"})
    assert build(lowered, {}).argv[build(lowered, {}).argv.index("--max-budget-usd") + 1] == "2.50"
    for label in ("a", "b", None):
        invocation = build(dataclasses.replace(spec, claude_account=label), {})
        assert "--max-budget-usd" not in invocation.argv
        assert "CLAUDE_CODE_PROMPT_CACHE_TTL" not in invocation.env


def _plan_headroom_policy(tmp_path, monkeypatch, used, **extra):
    from scripts.dispatcher import headroom

    path = tmp_path / "model-pause.json"
    policy = {"headroom": [{"lane": "claude", "pattern": "claude-*", "max_weekly_used_pct": 90}], **extra}
    path.write_text(json.dumps(policy), encoding="utf-8")
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(path))
    monkeypatch.setattr(headroom.model_pause, "routing_budget_used_pct", lambda _lane, *, account: used)
    return headroom


def test_check_plan_judges_an_api_key_account_by_its_spend_cap(tmp_path, monkeypatch):
    """Defect (#12356): an API-key account has no plan meter, so the plan cap refused it as unknown usage."""
    headroom = _plan_headroom_policy(tmp_path, monkeypatch, None)
    record = {"claude_account": "kk", "mode": "read-only"}
    headroom.check_plan("claude", "claude-opus-5-5", record)
    with pytest.raises(ValueError, match=r"^CLAUDE_ACCOUNT_REFUSED: claude_account_budget_cap_invalid$"):
        headroom.check_plan("claude", "claude-opus-5-5", {**record, "max_budget_usd": "1000"})
    _plan_headroom_policy(tmp_path, monkeypatch, None, pauses=[{"pattern": "claude-*", "until": "2999-01-01T00:00:00Z"}])
    with pytest.raises(headroom.model_pause.ModelPausedRefused, match="MODEL_PAUSED"):
        headroom.check_plan("claude", "claude-opus-5-5", record)


@pytest.mark.parametrize(("used", "reason"), [(95.0, "MODEL_HEADROOM:"), (None, "MODEL_HEADROOM_USAGE_UNKNOWN:")])
def test_check_plan_keeps_subscription_plan_headroom(tmp_path, monkeypatch, used, reason):
    """Control (#12356): a subscription account is still judged by its plan meter."""
    headroom = _plan_headroom_policy(tmp_path, monkeypatch, used)
    for label in ("a", "b"):
        with pytest.raises(headroom.model_pause.ModelPausedRefused, match=f"^{reason}"):
            headroom.check_plan("claude", "claude-opus-5-5", {"claude_account": label, "mode": "read-only"})
    _plan_headroom_policy(tmp_path, monkeypatch, 50.0)
    headroom.check_plan("claude", "claude-opus-5-5", {"claude_account": "a", "mode": "read-only"})


@pytest.mark.parametrize(
    ("model", "mode", "options", "advised"),
    [
        ("claude-sonnet-5-5", "workspace-write", {}, True),
        ("claude-sonnet-5-5", "read-only", {}, False),
        ("claude-opus-5-5", "workspace-write", {}, False),
        ("claude-haiku-5-5", "workspace-write", {}, False),
        ("claude-haiku-5-5", "workspace-write", {"advisor": "opus"}, True),
        ("sonnet[1m]", "workspace-write", {}, True),
        ("haiku", "workspace-write", {}, False),
        ("haiku", "workspace-write", {"advisor": "opus"}, True),
    ],
)
def test_claude_advisor_is_attached_only_to_the_approved_runs(tmp_path, model, mode, options, advised):
    """Advisor spend outside the approved scope is the defect: only the approved runs carry ``--advisor opus``."""
    spec = TaskSpec("adv", "claude", model, None, mode, tmp_path, tmp_path / "p", tmp_path / "f", options=options)
    spec.prompt_file.write_bytes(b"prompt")
    for label in (None, "kk"):
        invocation = providers.load("claude").build(dataclasses.replace(spec, claude_account=label), {})
        assert ("--advisor" in invocation.argv) is advised
        if advised:
            assert invocation.argv[invocation.argv.index("--advisor") + 1] == "opus"
            assert invocation.argv[invocation.argv.index("--model") + 1].startswith(("claude-sonnet-5-5", "claude-haiku-5-5"))
            assert "CLAUDE_CODE_DISABLE_ADVISOR_TOOL" not in invocation.env
            assert "DISABLE_TELEMETRY" not in invocation.env
        else:
            assert invocation.env["CLAUDE_CODE_DISABLE_ADVISOR_TOOL"] == "1"


def test_advised_claude_run_on_another_executor_model_settles_as_a_failure(sandbox, monkeypatch):
    """Defect: an advised run silently executing on an unapproved model settled done."""
    from scripts.dispatcher.providers import claude

    result = {"type": "result", "subtype": "success", "is_error": False, "result": "done", "usage": {},
              "modelUsage": {"claude-sonnet-4-6": {"canonicalModel": "claude-sonnet-4-6"},
                             "claude-opus-5-5": {"canonicalModel": "claude-opus-5-5"}}}
    code = f"import sys\nsys.stdin.read()\nprint({json.dumps(result)!r})\n"
    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(claude, "build", lambda spec, env: Invocation([sys.executable, "-c", code], b"", env, None))
    monkeypatch.setattr(worker, "_reap_settled", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker.headroom, "check_plan", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker.headroom, "check_runtime", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(git, "snapshot_delivery", lambda *_args: {})
    spec = TaskSpec("advised", "claude", "sonnet", None, "workspace-write", sandbox.repo,
                    sandbox.repo / "advised.prompt", sandbox.tasks / "advised.result")
    spec.prompt_file.write_bytes(b"prompt")
    record = store.new_record(spec, {"key": "public", "github": str(sandbox.remote)}, "main",
                              run_git(sandbox.repo, "rev-parse", "HEAD"), {"research_owned_path": []})
    record["prompt_file"] = str(sandbox.tasks / "advised.prompt")
    path = store.create(record, b"prompt")
    (sandbox.tasks / "logs").mkdir()
    worker.supervise(path, {}, 10)
    settled = json.loads(path.read_text())
    assert settled["status"] == "failed"
    assert settled["error"] == (
        "claude_advisor_executor_unverified: approved claude-sonnet-5-5, reported claude-opus-5-5, claude-sonnet-4-6"
    )
    assert (settled["resolved_model"], settled["resolved_model_known"], settled["resolved_model_source"]) == (
        "claude-sonnet-4-6", True, "claude-result-model-usage")


def _spawn_refused_record(tmp_path, monkeypatch, task_id):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    path = store.record_path(task_id)
    record = {"task_id": task_id, "run_nonce": "n" * 32, "status": "spawning", "pid": None,
              "prompt_file": str(path.with_suffix(".prompt"))}
    spec = TaskSpec(task_id, "codex", "m", None, "read-only", tmp_path, path.with_suffix(".prompt"),
                    path.with_suffix(".result"))
    return spec, record, path


def test_dispatch_ambiguous_scope_start_marks_task_failed(tmp_path, monkeypatch) -> None:
    from scripts.dispatcher import admission
    from scripts.orchestration import dispatch_isolation

    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "ambiguous-scope")

    def explode(*_args, **_kwargs):
        raise dispatch_isolation.DispatchIsolationError(
            "systemd-run: worker start marker arrived after the startup timeout (2s) "
            "for unit lu-worker-ambiguous-scope; the scope was stopped and will not be relaunched"
        )

    monkeypatch.setattr(dispatch_isolation, "spawn_detached_worker", explode)
    with pytest.raises(admission.LaunchRefused):
        worker.start(spec, record, b"prompt", 60)

    state = json.loads(path.read_text())
    assert state["status"] == "failed"
    assert state["pid"] is None
    assert state["error"].startswith("dispatch_isolation_failed: ")
    assert "will not be relaunched" in state["error"]


@pytest.mark.parametrize(
    "reason",
    ["inside-driver-scope; systemd-run unavailable", "caller-cgroup-unavailable", "caller-cgroup-unverifiable"],
)
def test_dispatch_fallback_refusal_records_no_worker_started(tmp_path, monkeypatch, reason) -> None:
    from scripts.dispatcher import admission
    from scripts.orchestration import dispatch_isolation

    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "fallback-refusal")
    refusal = f"fallback-refused: {reason}"
    spawn = Mock(side_effect=dispatch_isolation.DispatchIsolationError(refusal))
    popen = Mock()
    monkeypatch.setattr(dispatch_isolation, "spawn_detached_worker", spawn)
    monkeypatch.setattr(subprocess, "Popen", popen)
    with pytest.raises(admission.LaunchRefused):
        worker.start(spec, record, b"prompt", 60)

    spawn.assert_called_once()
    popen.assert_not_called()
    state = json.loads(path.read_text())
    assert state["status"] == "failed"
    assert state["pid"] is None
    assert state["error"].startswith("dispatch_fallback_refused: ")
    assert refusal in state["error"]
    assert "ambiguous" not in state["error"]


def test_dispatch_popen_failure_records_worktree_head(tmp_path, monkeypatch) -> None:
    """Ported from tests/test_delegate.py::test_dispatch_popen_failure_records_worktree_head.

    v2 records the worktree head (``head_sha``) when the record is created; a failed spawn keeps it.
    """
    from scripts.dispatcher import admission
    from scripts.orchestration import dispatch_isolation

    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "popen-head")
    record["head_sha"] = "a" * 40
    monkeypatch.setattr(
        dispatch_isolation, "spawn_detached_worker", Mock(side_effect=FileNotFoundError("no such file"))
    )
    with pytest.raises(admission.LaunchRefused):
        worker.start(spec, record, b"prompt", 60)

    state = json.loads(path.read_text())
    assert state["status"] == "failed"
    assert state["pid"] is None
    assert state["error"] == "worker_spawn_failed: Popen failed: FileNotFoundError: no such file"
    assert state["head_sha"] == "a" * 40


def _fake_pool(directory, *, current, file_cache, high=21 * 1024**3):
    """Ported from tests/test_dispatch_admission.py::_fake_pool."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "memory.current").write_text(f"{current}\n", encoding="ascii")
    (directory / "memory.high").write_text(f"{high}\n", encoding="ascii")
    (directory / "memory.max").write_text(f"{23 * 1024**3}\n", encoding="ascii")
    (directory / "memory.stat").write_text(f"active_file {file_cache}\ninactive_file 0\n", encoding="ascii")
    return directory


def _full_disk(monkeypatch, *readings):
    """Ported from tests/test_delegate_admission.py::_full_disk."""
    from scripts.orchestration import dispatch_admission

    seen = {"readings": list(readings), "alerts": []}

    def probe():
        values = seen["readings"]
        used = values.pop(0) if len(values) > 1 else values[0]
        used_bytes = int(400 * 1024**3 * used / 100)
        return dispatch_admission.DiskProbe(used_bytes=used_bytes, free_bytes=400 * 1024**3 - used_bytes)

    monkeypatch.setattr(dispatch_admission, "probe_disk", probe)
    monkeypatch.setattr(dispatch_admission, "post_disk_alert", lambda body, _key: seen["alerts"].append(body))
    return seen


def _credit_balance_snapshot():
    """Inlined ports of test_credit_lane::_credit_balance_snapshot, _budget, _live and _codex."""
    from datetime import UTC, datetime

    codex = {
        "status": "near_cap", "remaining_pct": 1.0, "burn_pct_7d": 99.0,
        "freshness": "fresh", "age_s": 60.0, "eligible": True, "health": {"healthy": True},
        "credit_balance": 62500.0, "reset_credits": None,
        "runtime": {"headroom_blocked": False, "rate_limited": 0},
        "codexbar": {
            "weekly_used_pct": 99.0, "weekly_remaining_pct": 1.0,
            "weekly_resets_at": "2026-10-03T17:00:00+00:00", "will_last_to_reset": False,
            "pace_summary": "13% in deficit", "freshness": "fresh", "age_s": 60.0, "stale": False,
            "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
    }
    return {
        "agents": {"codex": codex}, "api_accounts": {}, "diagnostics": {"stale": False},
        "recommendation": {"primary_agent_for_code": "codex", "rationale": "", "warnings": []},
    }


# D5 ports of legacy admission contracts; originals remain untouched.
@pytest.fixture
def admission_dispatch(sandbox, monkeypatch):
    """Ported setup from test_delegate_admission::_stub_worktree and credit_lane::dispatch_env."""
    from scripts.dispatcher import cli

    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(git, "ROOT", sandbox.repo)
    monkeypatch.setattr(git, "CONFIG", sandbox.repo / "scripts/config/fleet_repos.yaml")
    spawned = []

    def start(spec, record, prompt, hard_timeout):
        store.create(record, prompt)
        record.update(pid=os.getpid(), process_start=worker._identity(os.getpid()))
        store.replace(record)
        spawned.append(record)

    monkeypatch.setattr(worker, "start", start)

    def dispatch(*flags, model="gpt-6.1-sol", mode="workspace-write", task_id="adm-worker"):
        return cli.main(["dispatch", "--agent", "sol", "--model", model, "--mode", mode,
                         "--task-id", task_id, "--prompt", "Map the parser flags.", *flags])

    yield SimpleNamespace(dispatch=dispatch, box=sandbox, spawned=spawned)
    # The fake supervisor is this test process; release its records before sandbox cancellation.
    for path in sandbox.tasks.glob("*.json"):
        record = json.loads(path.read_text())
        if record.get("pid") == os.getpid():
            record["status"] = "done"
            store.replace(record, path)


def test_dispatch_refuses_a_write_worker_at_the_cap_with_one_line(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_dispatch_refuses_a_write_worker_at_the_cap_with_one_line."""
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")
    assert admission_dispatch.dispatch("--dry-run") == 3
    refusal = [line for line in capsys.readouterr().err.splitlines() if "admission" in line]
    assert refusal == [
        "❌ dispatch admission refused for a workspace-write worker: live write workers 0/0 reached the cap "
        "(DISPATCH_MAX_LIVE_WRITE_WORKERS=0). Wait for a worker to finish or for the host to recover, raise the "
        'threshold through the named environment variable, or pass --force-admission "<reason>" to override.'
    ]
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_read_only_dispatch_is_exempt(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_read_only_dispatch_is_exempt."""
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")
    assert admission_dispatch.dispatch(mode="read-only") == 0
    assert "admission" not in capsys.readouterr().err
    assert "admission" not in store.read("adm-worker")


def test_full_shared_pool_refuses_a_write_worker(admission_dispatch, tmp_path, monkeypatch, capsys):
    """Ported from tests/test_dispatch_admission.py::test_full_shared_pool_refuses_a_write_worker."""

    pool = _fake_pool(tmp_path / "lu.slice", current=21 * 1024**3, file_cache=1024**3 // 2)
    monkeypatch.setenv("LU_SLICE_CGROUP", str(pool))
    assert admission_dispatch.dispatch() == 3
    assert ("lu.slice non-cache use 20.5 GiB plus a 2.5 GiB worker reserve exceeds MemoryHigh 21.0 GiB "
            "(DISPATCH_WORKER_MEM_RESERVE_GIB=2.5)") in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.repo / ".worktrees").exists()
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_file_cache_does_not_count_against_the_pool(admission_dispatch, tmp_path, monkeypatch, capsys):
    """Ported from tests/test_dispatch_admission.py::test_file_cache_does_not_count_against_the_pool."""

    pool = _fake_pool(tmp_path / "lu.slice", current=28 * 1024**3, file_cache=14 * 1024**3)
    monkeypatch.setenv("LU_SLICE_CGROUP", str(pool))
    assert admission_dispatch.dispatch() == 0
    assert "lu.slice 14.0/21.0 GiB non-cache (+14.0 GiB file cache; worker reserve 2.5 GiB)" in capsys.readouterr().err
    record = store.read("adm-worker")
    assert record["admission"]["pool_nonreclaimable_gib"] == 14.0
    assert record["admission"]["pool_file_cache_gib"] == 14.0
    assert record["admission"]["pool_limit_gib"] == 21.0


def test_locked_recheck_refuses_a_dispatch_that_lost_the_race(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_locked_recheck_refuses_a_dispatch_that_lost_the_race."""
    from scripts.dispatcher import host_admission as admission
    from scripts.orchestration import dispatch_admission

    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "1")
    real_evaluate = admission.evaluate
    calls = []

    def evaluate_after_competitor(mode, **kwargs):
        calls.append(kwargs)
        if len(calls) == 2:
            record = dict(schema_version=2, task_id="competitor", status="running", mode="workspace-write",
                          pid=os.getpid(), process_start=worker._identity(os.getpid()))
            store.replace(record)
        return real_evaluate(mode, **kwargs)

    monkeypatch.setattr(admission, "evaluate", evaluate_after_competitor)
    monkeypatch.setattr(git, "create_worktree", lambda *_a, **_k: pytest.fail("must not create a worktree"))
    assert admission_dispatch.dispatch() == 3
    assert len(calls) == 2
    assert "live write workers 1/1 reached the cap" in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()
    assert dispatch_admission.scan_task_records(admission_dispatch.box.tasks).live_task_ids == ("competitor",)


def test_admitted_dispatch_holds_its_slot_while_the_worktree_is_created(admission_dispatch, monkeypatch):
    """Ported from tests/test_delegate_admission.py::test_admitted_dispatch_holds_its_slot_while_the_worktree_is_created."""
    from scripts.guardrails.delegate_ownership import _task_still_active
    from scripts.orchestration import dispatch_admission

    seen = {}
    create = git.create_worktree

    def create_worktree(*args, **kwargs):
        held = store.read("adm-worker")
        seen["record"] = held
        seen["live"] = dispatch_admission.scan_task_records(admission_dispatch.box.tasks).live_task_ids
        assert _task_still_active("adm-worker", os.getpid(), admission_dispatch.box.tasks, created_at=0)
        assert [state["task_id"] for _, state in dispatch_admission.iter_active_records(
            admission_dispatch.box.tasks)] == ["adm-worker"]
        return create(*args, **kwargs)

    monkeypatch.setattr(git, "create_worktree", create_worktree)
    assert admission_dispatch.dispatch() == 0
    held = seen["record"]
    assert held["status"] == "spawning" and held["pid"] is None and held["mode"] == "workspace-write"
    assert held[dispatch_admission.ADMISSION_HOLD_KEY]["owner_pid"] == os.getpid()
    assert seen["live"] == ("adm-worker",)
    final = store.read("adm-worker")
    assert dispatch_admission.ADMISSION_HOLD_KEY not in final
    assert final["run_nonce"] == held["run_nonce"]
    assert final["admission"] == held["admission"]


def test_dispatch_that_stops_after_admission_drops_its_hold(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_dispatch_that_stops_after_admission_drops_its_hold."""
    def disappear(*_args, **_kwargs):
        assert store.read("adm-worker")["admission_hold"]
        raise ValueError("worktree disappeared before its task record was published")

    monkeypatch.setattr(git, "create_worktree", disappear)
    assert admission_dispatch.dispatch() == 2
    assert "disappeared before its task record was published" in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_admission_marks_a_record_whose_dispatcher_died_crashed(admission_dispatch):
    """Ported from tests/test_delegate_admission.py::test_admission_marks_a_record_whose_dispatcher_died_crashed."""
    from scripts.dispatcher import host_admission as admission
    from scripts.orchestration import dispatch_admission
    from tests.worktree_prep_helpers import exited_process_identity

    pid, start = exited_process_identity()
    record = dict(schema_version=2, task_id="orphan", run_nonce="nonce-orphan", status="spawning", pid=None,
                  mode="workspace-write", started_at=store.now(),
                  admission_hold=dict(run_nonce="nonce-orphan", owner_pid=pid, owner_start=start))
    admission_dispatch.box.tasks.mkdir(exist_ok=True)
    store.replace(record)
    decision = admission.evaluate("workspace-write", sweep=True)
    assert decision.live_task_ids == ()
    assert decision.dead_task_ids == ("orphan",)
    healed = store.read("orphan")
    assert healed["status"] == "crashed"
    assert healed["returncode_reason"] == dispatch_admission.ORPHANED_HOLD_REASON
    assert "marked crashed by admission probe" in healed["stderr_excerpt"]
    assert "admission_hold" not in healed


@pytest.mark.parametrize("model", ["gpt-6-astra", "gpt-5-codex", "claude-opus-5-5"])
def test_admission_refuses_off_allowlist_model_on_credit_balance_lane(admission_dispatch, monkeypatch, capsys, model):
    """Ported from tests/test_credit_lane.py::test_admission_refuses_off_allowlist_model_on_credit_balance_lane."""
    from scripts.fleet import credit_lane

    monkeypatch.setattr(credit_lane, "read_routing_budget", _credit_balance_snapshot)
    assert admission_dispatch.dispatch(model=model, mode="read-only") == 2
    err = capsys.readouterr().err
    assert "❌ dispatch refused: CREDIT_PERIOD_MODEL_REFUSED: lane codex is credit_balance_present" in err
    assert f"model {model} is outside the credit-period allowlist [gpt-6.1-sol, gpt-6-luna]" in err
    assert "credit_lanes.yaml" in err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.repo / ".worktrees").exists()
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


@pytest.mark.parametrize("model", ["gpt-6.1-sol", "gpt-6-luna", "codex:gpt-6-luna", "GPT-6.1-Sol", None])
def test_admission_accepts_allowlisted_and_default_models_without_reading_state(monkeypatch, model):
    """Ported from tests/test_credit_lane.py::test_admission_accepts_allowlisted_and_default_models_without_reading_state."""
    from scripts.dispatcher import host_admission as admission
    from scripts.fleet import credit_lane

    monkeypatch.setattr(credit_lane, "read_routing_budget", lambda **_k: pytest.fail("must not read state"))
    assert admission.credit_period_refusal("codex", model) is None


def test_force_admission_records_the_reason(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_force_admission_records_the_reason."""
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")
    assert admission_dispatch.dispatch("--force-admission", "hotfix #1234 while one worker drains") == 0
    assert "overridden by --force-admission ('hotfix #1234 while one worker drains')" in capsys.readouterr().err
    decision = store.read("adm-worker")["admission"]
    assert decision["admitted"] is False
    assert decision["forced"] is True
    assert decision["force_reason"] == "hotfix #1234 while one worker drains"
    assert decision["max_live_write_workers"] == 0


def test_force_admission_requires_a_reason(admission_dispatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_force_admission_requires_a_reason."""
    assert admission_dispatch.dispatch("--force-admission", "   ") == 2
    assert "--force-admission requires a non-empty reason" in capsys.readouterr().err
    assert not admission_dispatch.spawned


def test_live_forced_dispatch_on_a_full_disk_stops_at_the_first_gate(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_live_forced_dispatch_on_a_full_disk_stops_at_the_first_gate."""

    disk = _full_disk(monkeypatch, 90.0)
    assert admission_dispatch.dispatch("--force-admission", "hotfix while the disk drains") == 4
    # Disk admission measures, alerts and refuses; only each task's creator removes its worktree.
    assert disk["alerts"]
    assert "--force-admission cannot override a full disk" in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()
    assert not (admission_dispatch.box.repo / ".worktrees").exists()


def test_locked_recheck_holds_a_disk_refusal_against_a_force_reason(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_locked_recheck_holds_a_disk_refusal_against_a_force_reason."""

    disk = _full_disk(monkeypatch, 60.0, 90.0)
    monkeypatch.setattr(git, "create_worktree", lambda *_a, **_k: pytest.fail("must not create a worktree"))
    assert admission_dispatch.dispatch("--force-admission", "hotfix while the disk drains") == 4
    err = capsys.readouterr().err
    assert "disk 90.0% used" in err and "--force-admission cannot override a full disk" in err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_force_admission_skips_the_early_refusal(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_force_admission_skips_the_early_refusal."""
    from scripts.orchestration import dispatch_admission

    overloaded = dispatch_admission.HostProbe(mem_available_bytes=1024**3, load1=40.0, cpu_count=8, proc_available=True)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: overloaded)
    assert admission_dispatch.dispatch("--force-admission", "drain one worker") == 0
    assert "overridden by --force-admission ('drain one worker'): MemAvailable 1.0 GiB" in capsys.readouterr().err
    assert store.read("adm-worker")["admission"]["forced"] is True


def test_early_refusal_reports_an_invalid_threshold_as_an_invalid_request(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_early_refusal_reports_an_invalid_threshold_as_an_invalid_request."""
    monkeypatch.setenv("DISPATCH_MIN_MEM_AVAILABLE_GIB", "-1")
    assert admission_dispatch.dispatch() == 2
    assert "invalid dispatch admission threshold: DISPATCH_MIN_MEM_AVAILABLE_GIB='-1' must be zero or more" in capsys.readouterr().err
    assert not admission_dispatch.spawned


def test_read_only_dispatch_on_an_overloaded_host_is_exempt(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_read_only_dispatch_on_an_overloaded_host_is_exempt."""
    from scripts.orchestration import dispatch_admission

    overloaded = dispatch_admission.HostProbe(mem_available_bytes=1024**3, load1=40.0, cpu_count=8, proc_available=True)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: overloaded)
    assert admission_dispatch.dispatch(mode="read-only") == 0
    assert "admission" not in capsys.readouterr().err


@pytest.mark.parametrize("failure", ["prompt-collision", "log-directory", "interrupted-setup"])
def test_spawn_setup_failure_never_strands_published_record(tmp_path, monkeypatch, failure):
    """Setup can fail after record publication but before any supervisor exists."""
    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "setup-failure")
    path.parent.mkdir()
    if failure == "prompt-collision":
        spec.prompt_file.write_bytes(b"original prompt")
        expected = FileExistsError
    elif failure == "log-directory":
        (path.parent / "logs").touch()
        expected = FileExistsError
    else:
        create = store.create

        def interrupted(*args):
            create(*args)
            raise KeyboardInterrupt

        monkeypatch.setattr(store, "create", interrupted)
        expected = KeyboardInterrupt
    with pytest.raises(expected):
        worker.start(spec, record, b"submitted prompt", 60)
    state = store.read(spec.task_id)
    assert state["status"] == "failed"
    assert state["returncode_reason"] == "spawn_setup_failed"
    assert state["pid"] is None
    assert state["finished_at"]
    assert "admission_hold" not in state
    if failure == "prompt-collision":
        assert spec.prompt_file.read_bytes() == b"original prompt"


def test_spawn_setup_failure_does_not_overwrite_existing_run(tmp_path, monkeypatch):
    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "duplicate-run")
    other = {**record, "run_nonce": "other-run"}
    store.create(other, b"original")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="task id already exists"):
        worker.start(spec, record, b"duplicate", 60)
    assert path.read_bytes() == before


@pytest.mark.parametrize("command", ["list", "status", "wait", "list-active"])
def test_cli_recovers_old_spawn_without_process(sandbox, command):
    """Existing ownerless records settle through the actual dispatcher entry point."""
    sandbox.tasks.mkdir(exist_ok=True)
    path = sandbox.tasks / "old-spawn.json"
    path.write_text(json.dumps(dict(schema_version=2, task_id="old-spawn", run_nonce="old-nonce",
                                   status="spawning", pid=None, started_at="2026-01-01T00:00:00Z")))
    args = {"list": ["list"], "status": ["status", "old-spawn"],
            "wait": ["wait", "old-spawn", "--run-nonce", "old-nonce", "--timeout", "0.1"],
            "list-active": ["list", "--status", "spawning"]}[command]
    response = json.loads(sandbox.cli(*args, expected=1 if command == "wait" else 0).stdout)
    if command == "list-active":
        assert response == []
    else:
        state = response[0] if command == "list" else response
        assert state["status"] == "crashed"
        assert state["returncode_reason"] == "spawn_process_missing"
        assert state["finished_at"]
    saved = json.loads(path.read_text())
    assert saved["status"] == "crashed"
    assert saved["run_nonce"] == "old-nonce"


@pytest.mark.parametrize("case", ["recent", "live-owner", "unknown-owner", "pid", "terminal", "legacy"])
def test_stale_spawn_recovery_preserves_unproven_or_live_records(tmp_path, monkeypatch, case):
    from scripts.orchestration.dispatch_admission import new_admission_hold

    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    record = dict(schema_version=2, task_id="preserved", run_nonce="same-run", status="spawning",
                  pid=None, started_at="2026-01-01T00:00:00Z")
    if case == "recent":
        record["started_at"] = store.now()
    elif case == "live-owner":
        record["admission_hold"] = new_admission_hold("same-run")
    elif case == "unknown-owner":
        record["admission_hold"] = {"run_nonce": "same-run", "owner_pid": os.getpid(), "owner_identity": "unverifiable"}
    elif case == "pid":
        record.update(pid=os.getpid(), process_start=worker._identity(os.getpid()))
    elif case == "terminal":
        record["status"] = "failed"
    else:
        record.pop("schema_version")
    store.replace(record)
    before = store.record_path("preserved").read_bytes()
    assert worker._observe(record)["status"] == record["status"]
    assert store.record_path("preserved").read_bytes() == before


def test_stale_spawn_recovery_rechecks_process_before_terminalizing(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    stale = dict(schema_version=2, task_id="racing-spawn", run_nonce="same-run", status="spawning",
                 pid=None, started_at="2026-01-01T00:00:00Z")
    current = {**stale, "status": "running", "pid": os.getpid(),
               "process_start": worker._identity(os.getpid())}
    store.replace(current)
    assert worker._observe(stale)["status"] == "running"
    assert store.read("racing-spawn")["status"] == "running"


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_dispatch_prompt_destination_collision_settles_failed_spawn(sandbox, mode):
    """A prompt file that already holds the submission is that task's prompt, not a failed spawn.

    A different occupant still fails closed
    (``test_spawn_setup_failure_never_strands_published_record``).
    """
    sandbox.tasks.mkdir(exist_ok=True)
    prompt = sandbox.tasks / "prompt-collision.prompt"
    prompt.write_text("the operator's submitted prompt")
    sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--task-id", "prompt-collision",
                "--mode", mode, "--prompt-file", str(prompt))
    state = json.loads(sandbox.cli("status", "prompt-collision").stdout)
    assert state["status"] in {"spawning", "running", "done"}
    assert state.get("returncode_reason") != "spawn_setup_failed"
    assert state.get("pid")
    assert prompt.read_text() == "the operator's submitted prompt"


def _write_rate_limits(usage_dir, agent, model, account):
    from datetime import UTC, datetime

    from scripts.agent_runtime import usage

    usage._reset_rate_limit_cache_for_tests()
    for path in usage_dir.glob("usage_*.jsonl"):
        path.unlink()
    stamp = datetime.now(UTC).isoformat()
    rows = []
    for _ in range(2):
        row = {"ts": stamp, "agent": agent, "model": model, "outcome": "rate_limited"}
        if account is not None:
            row["codex_account"] = account
        rows.append(row)
    (usage_dir / f"usage_{agent}-fixture.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_runtime_headroom_gates_each_codex_account_on_its_own_events(tmp_path, monkeypatch):
    """Account a's rate-limit events stopped a b-sub task (#12735).

    The supervisor asked for runtime headroom without the record's Codex account.
    """
    from scripts.agent_runtime import usage
    from scripts.agent_runtime.errors import RateLimitedError
    from scripts.dispatcher import git, headroom

    usage_dir = tmp_path / "usage"
    tasks = tmp_path / "tasks"
    usage_dir.mkdir()
    tasks.mkdir()
    (tasks / "logs").mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.delenv("LU_BYPASS_RATE_LIMIT", raising=False)
    monkeypatch.delenv("CODEX_HOME", raising=False)  # this process is account a ("sub")
    monkeypatch.setattr(usage, "_usage_dir", lambda: usage_dir)
    monkeypatch.setattr(worker.headroom, "check_plan", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker, "_reap_settled", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(git, "snapshot_delivery", lambda *_args, **_kwargs: {})
    usage._reset_rate_limit_cache_for_tests()
    model = "gpt-6.1-sol"
    real = headroom.check_runtime
    seen = {}

    def spy(agent, model_name, *, codex_account=None):
        seen["codex_account"] = codex_account
        try:
            real(agent, model_name, codex_account=codex_account)
        except RateLimitedError:
            seen["admitted"] = False
            raise
        seen["admitted"] = True
        # The real check admitted the task. Stop here so the supervisor never launches a provider.
        raise RateLimitedError(agent, model_name, "headroom-admitted")

    monkeypatch.setattr(worker.headroom, "check_runtime", spy)

    def settle(task_id, agent, codex_account):
        prompt = tmp_path / f"{task_id}.prompt"
        prompt.write_bytes(b"prompt")
        spec = TaskSpec(task_id, agent, model if agent == "codex" else "claude-opus-5-5", None, "read-only",
                        tmp_path, prompt, tasks / f"{task_id}.result", codex_account=codex_account)
        record = store.new_record(spec, {"key": "public", "github": "example/repo"}, "main", "a" * 40,
                                  {"research_owned_path": []})
        record["prompt_file"] = str(tasks / f"{task_id}.prompt")
        path = store.create(record, b"prompt")
        worker.supervise(path, {}, 10)
        return json.loads(path.read_text())

    _write_rate_limits(usage_dir, "codex", model, "sub")
    spared = settle("b-spared", "codex", "b-sub")
    assert seen == {"codex_account": "b-sub", "admitted": True}
    assert spared["status"] == "rate_limited"
    assert spared["error"] == "codex/gpt-6.1-sol rate limited: headroom-admitted"
    assert spared["provider_pgid"] is None
    blocked_a = settle("a-blocked", "codex", "sub")
    assert seen == {"codex_account": "sub", "admitted": False}
    assert blocked_a["status"] == "rate_limited"
    assert "headroom-admitted" not in blocked_a["error"]
    assert "rate_limited" in blocked_a["error"]

    _write_rate_limits(usage_dir, "codex", model, "b-sub")
    blocked_b = settle("b-blocked", "codex", "b-sub")
    assert seen == {"codex_account": "b-sub", "admitted": False}
    assert blocked_b["status"] == "rate_limited"
    assert "headroom-admitted" not in blocked_b["error"]

    _write_rate_limits(usage_dir, "claude", "claude-opus-5-5", None)
    claude_blocked = settle("claude-own", "claude", None)
    assert seen == {"codex_account": None, "admitted": False}
    assert claude_blocked["error"].startswith("claude/claude-opus-5-5 rate limited:")
    _write_rate_limits(usage_dir, "codex", model, "sub")
    claude_clear = settle("claude-clear", "claude", None)
    assert seen == {"codex_account": None, "admitted": True}
    assert claude_clear["error"] == "claude/claude-opus-5-5 rate limited: headroom-admitted"
    usage._reset_rate_limit_cache_for_tests()
