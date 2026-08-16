"""Guard tests for the mid-dispatch primary-tree tripwire (#6818).

The agy escape class: a write-capable dispatch child starts in an isolated
worktree (passing the spawn-time #4444 guard) and then resolves absolute paths
into the PRIMARY checkout while running. These tests build a real primary
repo + registered dispatch worktree and prove the watch detects a tracked
primary write DURING the dispatch, records attribution, and (only when the
operator gate is on) kills the child.

Mutation contract (#M-16): neutering detection — e.g. making
``PrimaryTreeWatch.maybe_check`` return ``[]`` or dropping the runner loop
wiring — must fail ``test_end_to_end_runner_detects_primary_write`` and
``test_detects_new_tracked_write``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime import primary_tree_watch as ptw
from agent_runtime import runner as runner_mod
from agent_runtime.primary_tree_watch import PrimaryTreeWatch
from agent_runtime.result import ParseResult
from agent_runtime.runner import (
    PrimaryTreeWriteError,
    _execute_invocation_plan,
    _raise_for_kill_reason,
)

_GIT_SCRUB = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_COMMON_DIR",
    "GIT_CONFIG_GLOBAL",
}


def _git(repo: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if k not in _GIT_SCRUB}
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


@pytest.fixture
def repo(tmp_path: Path) -> SimpleNamespace:
    """Primary checkout on main + a registered dispatch worktree."""
    main = tmp_path / "main"
    main.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in _GIT_SCRUB}
    subprocess.run(
        ["git", "init", "-q", "-b", "main", str(main)],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    _git(main, "config", "user.email", "t@example.com")
    _git(main, "config", "user.name", "T")
    (main / ".gitignore").write_text(".worktrees/\n")
    (main / "tracked.txt").write_text("original\n")
    (main / "pkg").mkdir()
    (main / "pkg" / "module.py").write_text("x = 1\n")
    _git(main, "add", "-A")
    _git(main, "commit", "-q", "-m", "init")
    dispatch_wt = main / ".worktrees" / "dispatch" / "agy" / "task-1"
    _git(main, "worktree", "add", "-q", "-b", "agy/task-1", str(dispatch_wt))
    return SimpleNamespace(main=main.resolve(), dispatch_wt=dispatch_wt.resolve())


def _start(repo, **overrides) -> PrimaryTreeWatch | None:
    kwargs = dict(
        cwd=repo.dispatch_wt,
        mode="workspace-write",
        agent_name="agy",
        task_id="task-1",
        event_sink=None,
        repo_tree=repo.main,
        interval_s=0.01,
    )
    kwargs.update(overrides)
    return PrimaryTreeWatch.start(**kwargs)


def _events(repo) -> list[dict]:
    path = repo.main / "data" / "telemetry" / "primary-integrity" / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# applicability
# ---------------------------------------------------------------------------


def test_mode_sets_do_not_drift():
    # The watch and the spawn-time guard must agree on what "write-capable" is.
    assert ptw.WRITE_CAPABLE_MODES == runner_mod._WRITE_CAPABLE_MODES


def test_start_returns_none_for_read_only_mode(repo):
    assert _start(repo, mode="read-only") is None


def test_start_returns_none_for_primary_checkout_cwd(repo):
    # The spawn-time guard refuses this spawn anyway; the watch must not
    # double-report a cwd that is itself the primary.
    assert _start(repo, cwd=repo.main) is None


def test_start_returns_none_outside_repo_tree(repo, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    assert _start(repo, cwd=outside) is None


def test_start_returns_none_when_disabled_by_interval(repo):
    assert _start(repo, interval_s=0) is None


def test_start_builds_watch_for_dispatch_worktree(repo):
    watch = _start(repo)
    assert watch is not None
    assert watch.main_root == repo.main
    assert watch.baseline == set()


# ---------------------------------------------------------------------------
# detection
# ---------------------------------------------------------------------------


def test_no_writes_no_events(repo):
    watch = _start(repo)
    assert watch.maybe_check(force=True) == []
    assert _events(repo) == []


def test_detects_new_tracked_write(repo):
    watch = _start(repo)
    (repo.main / "tracked.txt").write_text("ESCAPED\n")
    assert watch.maybe_check(force=True) == ["tracked.txt"]
    events = _events(repo)
    assert len(events) == 1
    event = events[0]
    assert event["event"] == ptw.EVENT_NAME
    assert event["agent"] == "agy"
    assert event["task_id"] == "task-1"
    assert event["paths"] == ["tracked.txt"]
    assert event["worktree"] == str(repo.dispatch_wt)
    # Reported exactly once: the same escape never duplicates.
    assert watch.maybe_check(force=True) == []
    assert len(_events(repo)) == 1


def test_baseline_dirty_paths_are_not_reported(repo):
    # A human already mid-edit in the primary is baseline, not an escape.
    (repo.main / "tracked.txt").write_text("human edit\n")
    watch = _start(repo)
    assert watch.baseline == {"tracked.txt"}
    assert watch.maybe_check(force=True) == []
    # A DIFFERENT tracked file going dirty afterwards still fires.
    (repo.main / "pkg" / "module.py").write_text("x = 2\n")
    assert watch.maybe_check(force=True) == ["pkg/module.py"]


def test_untracked_files_are_out_of_scope(repo):
    # Untracked pollution belongs to the #6866 root-entry canary; this watch
    # stays cheap with -uno.
    watch = _start(repo)
    (repo.main / "junk.tmp").write_text("junk\n")
    assert watch.maybe_check(force=True) == []


def test_worktree_writes_are_not_reported(repo):
    watch = _start(repo)
    (repo.dispatch_wt / "tracked.txt").write_text("legit worker edit\n")
    assert watch.maybe_check(force=True) == []


def test_throttle_skips_until_interval_and_force_bypasses(repo):
    watch = _start(repo, interval_s=3600)
    (repo.main / "tracked.txt").write_text("ESCAPED\n")
    # Non-forced check inside the interval: no probe yet.
    assert watch.maybe_check() == []
    assert _events(repo) == []
    # Forced probe (the post-exit sweep) sees it.
    assert watch.maybe_check(force=True) == ["tracked.txt"]


def test_event_sink_receives_the_event(repo):
    seen: list[tuple[str, dict]] = []
    watch = _start(repo, event_sink=lambda name, **fields: seen.append((name, fields)))
    (repo.main / "tracked.txt").write_text("ESCAPED\n")
    watch.maybe_check(force=True)
    assert len(seen) == 1
    name, fields = seen[0]
    assert name == ptw.EVENT_NAME
    assert fields["paths"] == ["tracked.txt"]


def test_probe_failures_fail_open_and_self_disable(repo, monkeypatch):
    watch = _start(repo)
    monkeypatch.setattr(ptw, "_tracked_dirty_paths", lambda _root: None)
    for _ in range(5):
        assert watch.maybe_check(force=True) == []
    # Self-disabled after repeated failures: even a real escape stays silent
    # rather than crashing the dispatch (fail-open by design).
    assert watch._probe_failures == ptw._MAX_PROBE_FAILURES


def test_enforce_gate_defaults_off(repo, monkeypatch):
    monkeypatch.delenv("LU_PRIMARY_TREE_WATCH_ENFORCE", raising=False)
    watch = _start(repo)
    assert watch.enforce is False
    monkeypatch.setenv("LU_PRIMARY_TREE_WATCH_ENFORCE", "1")
    assert watch.enforce is True


# ---------------------------------------------------------------------------
# runner wiring
# ---------------------------------------------------------------------------


@dataclass
class _Plan:
    cmd: list[str]
    cwd: Path
    stdin_payload: str = ""
    output_file: Path | None = None
    env_overrides: dict[str, str] = field(default_factory=dict)
    env_unsets: tuple[str, ...] = ()
    liveness_paths: tuple[Path, ...] = ()


class _Adapter:
    def liveness_signal_paths(self, _plan: _Plan) -> tuple[Path, ...]:
        return ()

    def parse_response(self, *, stdout: str, **_kwargs: object) -> ParseResult:
        return ParseResult(ok=True, response=stdout)


def _run_plan(plan: _Plan, *, mode: str = "workspace-write", task_id: str = "task-1"):
    return _execute_invocation_plan(
        agent_name="agy",
        adapter=_Adapter(),
        plan=plan,
        prompt="tripwire test",
        mode=mode,
        cwd=plan.cwd,
        model="test-model",
        task_id=task_id,
        session_id=None,
        entrypoint="runtime-test",
        hard_timeout=30,
        stall_timeout=30,
    )


def _disable_fleet_capture(monkeypatch):
    monkeypatch.setattr(
        runner_mod.FleetCapture,
        "start",
        classmethod(lambda cls, **_kw: (_ for _ in ()).throw(RuntimeError("off"))),
    )


def test_runner_starts_watch_and_final_checks(monkeypatch, tmp_path):
    calls = SimpleNamespace(start_kwargs=None, final_checks=0)

    class _StubWatch:
        enforce = False

        def maybe_check(self, *, force: bool = False):
            return []

        def final_check(self):
            calls.final_checks += 1
            return []

    def _stub_start(cls=None, **kwargs):
        calls.start_kwargs = kwargs
        return _StubWatch()

    monkeypatch.setattr(
        runner_mod.PrimaryTreeWatch, "start", classmethod(lambda cls, **kw: _stub_start(**kw))
    )
    _disable_fleet_capture(monkeypatch)
    plan = _Plan(cmd=[sys.executable, "-c", "print('hi')"], cwd=tmp_path)
    outcome = _run_plan(plan)
    assert outcome.parse.ok is True
    assert calls.start_kwargs["cwd"] == tmp_path
    assert calls.start_kwargs["mode"] == "workspace-write"
    assert calls.start_kwargs["agent_name"] == "agy"
    assert calls.start_kwargs["task_id"] == "task-1"
    # Post-exit sweep always runs (once in the normal path, once as the
    # finally safety net — both are required to be reachable).
    assert calls.final_checks >= 1
    assert outcome.kill_reason is None


def test_runner_kills_on_escape_only_when_enforced(monkeypatch, tmp_path):
    class _StubWatch:
        enforce = True

        def __init__(self):
            self._fired = False

        def maybe_check(self, *, force: bool = False):
            if self._fired:
                return []
            self._fired = True
            return ["scripts/api/fleet_router.py"]

        def final_check(self):
            return []

    monkeypatch.setattr(
        runner_mod.PrimaryTreeWatch, "start", classmethod(lambda cls, **kw: _StubWatch())
    )
    monkeypatch.setattr(runner_mod, "_POLL_INTERVAL_S", 0.05)
    _disable_fleet_capture(monkeypatch)
    plan = _Plan(cmd=[sys.executable, "-c", "import time; time.sleep(30)"], cwd=tmp_path)
    started = time.monotonic()
    outcome = _run_plan(plan)
    assert outcome.kill_reason == "primary_tree_write"
    assert outcome.escaped_primary_paths == ("scripts/api/fleet_router.py",)
    assert time.monotonic() - started < 20


def test_end_to_end_runner_detects_primary_write(monkeypatch, repo):
    """THE guard test: a child that writes a tracked primary file mid-dispatch
    is detected and attributed, without being killed (enforce off)."""
    monkeypatch.setattr(runner_mod, "_RUNNER_REPO_TREE", repo.main)
    monkeypatch.setattr(runner_mod, "_POLL_INTERVAL_S", 0.05)
    monkeypatch.setenv("LU_PRIMARY_TREE_WATCH_INTERVAL_S", "0.05")
    monkeypatch.delenv("LU_PRIMARY_TREE_WATCH_ENFORCE", raising=False)
    _disable_fleet_capture(monkeypatch)
    target = repo.main / "tracked.txt"
    script = (
        "import pathlib, time; "
        f"pathlib.Path({str(target)!r}).write_text('ESCAPED'); "
        "time.sleep(1.0)"
    )
    plan = _Plan(cmd=[sys.executable, "-c", script], cwd=repo.dispatch_wt)
    outcome = _run_plan(plan)
    assert outcome.kill_reason is None  # detection only — the gate is off
    assert outcome.returncode == 0
    assert "tracked.txt" in outcome.escaped_primary_paths
    events = _events(repo)
    assert len(events) == 1
    assert events[0]["paths"] == ["tracked.txt"]
    assert events[0]["agent"] == "agy"
    assert events[0]["task_id"] == "task-1"


def test_end_to_end_clean_child_records_nothing(monkeypatch, repo):
    monkeypatch.setattr(runner_mod, "_RUNNER_REPO_TREE", repo.main)
    monkeypatch.setenv("LU_PRIMARY_TREE_WATCH_INTERVAL_S", "0.05")
    _disable_fleet_capture(monkeypatch)
    # The child edits its own worktree — the sanctioned flow must stay silent.
    target = repo.dispatch_wt / "tracked.txt"
    script = f"import pathlib; pathlib.Path({str(target)!r}).write_text('legit')"
    plan = _Plan(cmd=[sys.executable, "-c", script], cwd=repo.dispatch_wt)
    outcome = _run_plan(plan)
    assert outcome.parse.ok is True
    assert outcome.escaped_primary_paths == ()
    assert _events(repo) == []


def test_raise_for_kill_reason_maps_primary_tree_write(monkeypatch, tmp_path):
    records: list[dict] = []
    monkeypatch.setattr(runner_mod, "write_record", records.append)
    execution = runner_mod._ExecutionOutcome(
        parse=ParseResult(ok=False, response=""),
        duration_s=1.0,
        returncode=-15,
        kill_reason="primary_tree_write",
        stdout_text="",
        stderr_text="",
        liveness_paths=(),
        escaped_primary_paths=("scripts/api/fleet_router.py",),
    )
    with pytest.raises(PrimaryTreeWriteError) as exc_info:
        _raise_for_kill_reason(
            agent_name="agy",
            kill_reason="primary_tree_write",
            execution=execution,
            prompt="p",
            entrypoint="runtime-test",
            model="m",
            mode="workspace-write",
            task_id="task-1",
            cwd=tmp_path,
            session_id=None,
            stdout_silence_timeout=None,
            initial_response_timeout=None,
            stall_timeout=30,
            hard_timeout=30,
        )
    assert exc_info.value.paths == ["scripts/api/fleet_router.py"]
    assert len(records) == 1
    assert records[0]["failure_code"] == "primary_tree_write"
