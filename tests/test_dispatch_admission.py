"""Host admission for write-capable dispatches (#8645 part A).

Every record lives under tmp_path; memory and load come from a monkeypatched
probe, never from allocating memory or generating load.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.orchestration import dispatch_admission as adm
from scripts.orchestration import worktree_prep

_GIB = 1024**3
_LIMITS = adm.Thresholds(max_live_write_workers=2, min_mem_available_gib=3.5, max_load_per_cpu=1.5)


def _healthy_probe() -> adm.HostProbe:
    return adm.HostProbe(mem_available_bytes=12 * _GIB, load1=2.0, cpu_count=8, proc_available=True)


def _record(tasks_dir: Path, task_id: str, *, status: str = "running", mode: str = "workspace-write", **fields) -> Path:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "task_id": task_id,
        "status": status,
        "mode": mode,
        "pid": fields.pop("pid", 1000 + len(list(tasks_dir.glob("*.json")))),
        "run_nonce": f"nonce-{task_id}",
        "started_at": fields.pop("started_at", datetime.now(UTC).isoformat()),
        **fields,
    }
    path = tasks_dir / f"{task_id}.json"
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return path


@pytest.fixture
def probe(monkeypatch):
    current = {"probe": _healthy_probe()}
    monkeypatch.setattr(adm, "probe_host", lambda *_a, **_k: current["probe"])
    return current


def test_cap_reached_is_refused(tmp_path, probe):
    tasks = tmp_path / "tasks"
    _record(tasks, "a", pid=11)
    _record(tasks, "b", pid=12, mode="danger")

    decision = adm.evaluate("workspace-write", tasks, pid_alive=lambda _pid: True, thresholds=_LIMITS)

    assert not decision.admitted
    assert decision.live_task_ids == ("a", "b")
    [failure] = decision.failures
    assert "live write workers 2/2 reached the cap (DISPATCH_MAX_LIVE_WRITE_WORKERS=2)" in failure
    assert "--force-admission" in decision.refusal_line()


def test_read_only_and_terminal_records_do_not_hold_write_slots(tmp_path, probe):
    tasks = tmp_path / "tasks"
    _record(tasks, "reader", pid=11, mode="read-only")
    _record(tasks, "finished", pid=12, status="done")
    _record(tasks, "writer", pid=13)

    decision = adm.evaluate("danger", tasks, pid_alive=lambda _pid: True, thresholds=_LIMITS)

    assert decision.admitted
    assert decision.live_task_ids == ("writer",)


def test_dead_pid_does_not_count_and_is_handed_to_the_sweeper(tmp_path, probe):
    tasks = tmp_path / "tasks"
    _record(tasks, "alive", pid=11)
    _record(tasks, "dead-writer", pid=12)
    _record(tasks, "dead-reader", pid=13, mode="read-only", status="spawning")
    swept: list[str] = []

    decision = adm.evaluate(
        "workspace-write",
        tasks,
        pid_alive=lambda pid: pid == 11,
        on_dead=lambda _path, state: swept.append(state["task_id"]),
        thresholds=_LIMITS,
    )

    assert decision.admitted
    assert decision.live_task_ids == ("alive",)
    assert sorted(swept) == ["dead-reader", "dead-writer"]
    assert decision.swept
    assert "2 record(s) marked crashed" in decision.summary()


def test_report_only_evaluation_names_dead_records_without_sweeping(tmp_path, probe):
    tasks = tmp_path / "tasks"
    _record(tasks, "dead", pid=12)

    decision = adm.evaluate("workspace-write", tasks, pid_alive=lambda _pid: False, thresholds=_LIMITS)

    assert not decision.swept
    assert decision.dead_task_ids == ("dead",)
    assert "1 record(s) dead pid, not counted: dead" in decision.summary()


def test_pidless_spawning_record_holds_a_slot_only_during_the_grace_window(tmp_path, probe):
    tasks = tmp_path / "tasks"
    stale = (datetime.now(UTC) - timedelta(seconds=adm.PIDLESS_SPAWNING_GRACE_S + 60)).isoformat()
    _record(tasks, "publishing", status="spawning", pid=None)
    _record(tasks, "orphaned", status="spawning", pid=None, started_at=stale)

    decision = adm.evaluate("workspace-write", tasks, pid_alive=lambda _pid: False, thresholds=_LIMITS)

    assert decision.live_task_ids == ("publishing",)
    assert decision.dead_task_ids == ()


def test_pidless_spawning_record_from_the_future_does_not_hold_a_slot(tmp_path, probe, caplog):
    tasks = tmp_path / "tasks"
    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    skewed = (datetime.now(UTC) + timedelta(seconds=adm.PIDLESS_CLOCK_SKEW_S / 2)).isoformat()
    _record(tasks, "future", status="spawning", pid=None, started_at=future)
    _record(tasks, "skewed", status="spawning", pid=None, started_at=skewed)

    with caplog.at_level("WARNING", logger=adm.__name__):
        decision = adm.evaluate("workspace-write", tasks, pid_alive=lambda _pid: False, thresholds=_LIMITS)

    assert decision.live_task_ids == ("skewed",)
    assert "pidless spawning record future has started_at" in caplog.text
    assert "skewed" not in caplog.text


def test_low_mem_available_is_refused(tmp_path, probe):
    probe["probe"] = adm.HostProbe(mem_available_bytes=int(2.5 * _GIB), load1=1.0, cpu_count=8, proc_available=True)

    decision = adm.evaluate("workspace-write", tmp_path / "tasks", thresholds=_LIMITS)

    assert not decision.admitted
    [failure] = decision.failures
    assert failure == ("MemAvailable 2.5 GiB is below the floor of 3.5 GiB (DISPATCH_MIN_MEM_AVAILABLE_GIB=3.5)")


def test_high_load_per_cpu_is_refused(tmp_path, probe):
    probe["probe"] = adm.HostProbe(mem_available_bytes=12 * _GIB, load1=14.0, cpu_count=8, proc_available=True)

    decision = adm.evaluate("workspace-write", tmp_path / "tasks", thresholds=_LIMITS)

    assert not decision.admitted
    [failure] = decision.failures
    assert failure.startswith("load 1.75 per CPU (1-minute load 14.00 on 8 CPUs) is above the limit of 1.50")
    assert "DISPATCH_MAX_LOAD_PER_CPU=1.5" in failure


def test_single_cpu_load_failure_uses_singular(tmp_path, probe):
    probe["probe"] = adm.HostProbe(mem_available_bytes=12 * _GIB, load1=3.0, cpu_count=1, proc_available=True)

    decision = adm.evaluate("workspace-write", tmp_path / "tasks", thresholds=_LIMITS)

    [failure] = decision.failures
    assert "(1-minute load 3.00 on 1 CPU) is above" in failure


def test_every_failed_check_is_named_in_one_refusal_line(tmp_path, probe):
    tasks = tmp_path / "tasks"
    _record(tasks, "a", pid=11)
    _record(tasks, "b", pid=12)
    probe["probe"] = adm.HostProbe(mem_available_bytes=1 * _GIB, load1=40.0, cpu_count=8, proc_available=True)

    decision = adm.evaluate("workspace-write", tasks, pid_alive=lambda _pid: True, thresholds=_LIMITS)

    line = decision.refusal_line()
    assert "\n" not in line
    assert len(decision.failures) == 3
    for name in (adm.ENV_MAX_LIVE_WRITE_WORKERS, adm.ENV_MIN_MEM_AVAILABLE_GIB, adm.ENV_MAX_LOAD_PER_CPU):
        assert name in line


def test_read_only_mode_is_exempt_without_scanning(tmp_path, monkeypatch):
    monkeypatch.setattr(adm, "scan_task_records", lambda *_a, **_k: pytest.fail("read-only must not scan"))
    monkeypatch.setattr(adm, "probe_host", lambda *_a, **_k: pytest.fail("read-only must not probe"))

    decision = adm.evaluate("read-only", tmp_path / "tasks", thresholds=_LIMITS)

    assert decision.exempt and decision.admitted


def test_without_proc_memory_and_cpu_are_unknown_and_only_the_cap_applies(tmp_path, monkeypatch):
    missing_proc = tmp_path / "no-proc"
    no_proc_probe = adm.read_host(missing_proc)
    assert no_proc_probe == adm.HostProbe(
        mem_available_bytes=None, load1=None, cpu_count=os.cpu_count(), proc_available=False
    )
    monkeypatch.setattr(adm, "probe_host", lambda *_a, **_k: no_proc_probe)
    tasks = tmp_path / "tasks"
    _record(tasks, "a", pid=11)

    admitted = adm.evaluate("workspace-write", tasks, pid_alive=lambda _pid: True, thresholds=_LIMITS)
    assert admitted.admitted
    summary = admitted.summary()
    assert "MemAvailable unknown" in summary
    assert "load unknown" in summary
    assert "only the worker cap is enforced" in summary

    _record(tasks, "b", pid=12)
    refused = adm.evaluate("workspace-write", tasks, pid_alive=lambda _pid: True, thresholds=_LIMITS)
    assert not refused.admitted
    assert [f.split(" reached")[0] for f in refused.failures] == ["live write workers 2/2"]


def test_probe_host_reads_meminfo_and_loadavg(tmp_path):
    proc = tmp_path / "proc"
    proc.mkdir()
    (proc / "meminfo").write_text("MemTotal:       15728640 kB\nMemAvailable:    3670016 kB\n", encoding="ascii")
    (proc / "loadavg").write_text("3.25 2.00 1.00 2/900 12345\n", encoding="ascii")

    probe = adm.read_host(proc)

    assert probe.proc_available
    assert probe.mem_available_bytes == 3670016 * 1024
    assert probe.mem_available_gib == pytest.approx(3.5)
    assert probe.load1 == 3.25


def test_thresholds_default_to_config_and_honour_env_overrides():
    from scripts import config

    defaults = adm.load_thresholds({})
    assert defaults == adm.Thresholds(
        max_live_write_workers=config.DISPATCH_MAX_LIVE_WRITE_WORKERS,
        min_mem_available_gib=config.DISPATCH_MIN_MEM_AVAILABLE_GIB,
        max_load_per_cpu=config.DISPATCH_MAX_LOAD_PER_CPU,
    )
    assert (defaults.max_live_write_workers, defaults.min_mem_available_gib, defaults.max_load_per_cpu) == (5, 3.5, 1.5)

    overridden = adm.load_thresholds(
        {
            adm.ENV_MAX_LIVE_WRITE_WORKERS: "0",
            adm.ENV_MIN_MEM_AVAILABLE_GIB: "6",
            adm.ENV_MAX_LOAD_PER_CPU: "0.75",
        }
    )
    assert overridden == adm.Thresholds(max_live_write_workers=0, min_mem_available_gib=6.0, max_load_per_cpu=0.75)


@pytest.mark.parametrize(
    ("name", "raw"),
    [
        (adm.ENV_MAX_LIVE_WRITE_WORKERS, "five"),
        (adm.ENV_MAX_LIVE_WRITE_WORKERS, "2.5"),
        (adm.ENV_MIN_MEM_AVAILABLE_GIB, "-1"),
        (adm.ENV_MAX_LOAD_PER_CPU, "nan"),
    ],
)
def test_invalid_threshold_env_is_rejected(name, raw):
    with pytest.raises(ValueError, match=name):
        adm.load_thresholds({name: raw})


def test_admission_lock_is_exclusive_across_holders(tmp_path):
    tasks = tmp_path / "tasks"
    with adm.admission_lock(tasks), pytest.raises(adm.AdmissionLockTimeout), adm.admission_lock(tasks, timeout_s=0.1):
        pass
    # Released on exit: the next holder gets it at once.
    with adm.admission_lock(tasks, timeout_s=0.1):
        pass
    assert (tasks / adm.LOCK_FILE_NAME).is_file()


# --- #8717: pid-less records owned by a live dispatcher --------------------------------------


def _own_identity() -> dict:
    return worktree_prep.process_identity(os.getpid())


def _pidless_owned_record(tasks_dir: Path, task_id: str, *, block: str, owner: dict, age_s: float) -> Path:
    """A pid-less ``spawning`` write record whose ``block`` (worktree_prep or admission_hold) names ``owner``."""
    return _record(
        tasks_dir,
        task_id,
        status="spawning",
        pid=None,
        started_at=(datetime.now(UTC) - timedelta(seconds=age_s)).isoformat(),
        **{block: {"run_nonce": f"nonce-{task_id}", "owner_pid": owner["pid"], "owner_start": owner["start"]}},
    )


@pytest.mark.parametrize("block", ["worktree_prep", adm.ADMISSION_HOLD_KEY])
def test_pidless_record_of_a_live_dispatcher_holds_a_slot_past_the_grace_window(tmp_path, probe, block):
    """A slow ``git worktree add`` (up to 900 s) keeps its admitted slot while the dispatcher lives."""
    tasks = tmp_path / "tasks"
    _pidless_owned_record(tasks, "slow-prep", block=block, owner=_own_identity(), age_s=300)
    assert adm.PIDLESS_SPAWNING_GRACE_S < 300

    decision = adm.evaluate("workspace-write", tasks, thresholds=_LIMITS)

    assert decision.live_task_ids == ("slow-prep",)
    assert decision.dead_task_ids == ()


@pytest.mark.parametrize("block", ["worktree_prep", adm.ADMISSION_HOLD_KEY])
def test_pidless_record_of_a_dead_dispatcher_is_not_counted_and_is_handed_to_the_sweeper(tmp_path, probe, block):
    from tests.worktree_prep_helpers import exited_process_identity

    tasks = tmp_path / "tasks"
    pid, start = exited_process_identity()
    path = _pidless_owned_record(tasks, "orphan", block=block, owner={"pid": pid, "start": start}, age_s=10)
    swept: list[Path] = []

    decision = adm.evaluate("workspace-write", tasks, on_dead=lambda p, _state: swept.append(p), thresholds=_LIMITS)

    assert decision.live_task_ids == ()
    assert decision.dead_task_ids == ("orphan",)
    assert swept == [path]


def test_pidless_record_of_a_gone_dispatcher_without_start_time_is_not_counted_or_swept(tmp_path, probe):
    """Without a recorded start time a missing pid frees the slot, but is no proof for marking it crashed."""
    from tests.worktree_prep_helpers import exited_process_identity

    tasks = tmp_path / "tasks"
    pid, _start = exited_process_identity()
    _pidless_owned_record(tasks, "no-start", block="worktree_prep", owner={"pid": pid, "start": None}, age_s=10)

    decision = adm.evaluate("workspace-write", tasks, on_dead=lambda *_a: pytest.fail("no proof"), thresholds=_LIMITS)

    assert decision.live_task_ids == ()
    assert decision.dead_task_ids == ()


@pytest.fixture(autouse=True)
def _omit_live_slice(monkeypatch):
    """Admission fixtures do not read the host's lu-dispatch.slice."""
    monkeypatch.setattr(adm, "slice_usage_clause", lambda: None)


def test_summary_adds_active_slice_use_without_changing_the_decision(tmp_path, probe, monkeypatch):
    tasks = tmp_path / "tasks"
    _record(tasks, "writer", pid=11)
    monkeypatch.setattr(adm, "slice_usage_clause", lambda: "lu-dispatch.slice 0.4/11.0 GiB")

    decision = adm.evaluate("workspace-write", tasks, pid_alive=lambda _pid: True, thresholds=_LIMITS)

    assert decision.admitted
    assert decision.failures == ()
    assert "lu-dispatch.slice 0.4/11.0 GiB" in decision.summary()


def test_summary_omits_the_slice_when_it_is_not_reported(tmp_path, probe):
    tasks = tmp_path / "tasks"
    _record(tasks, "writer", pid=11)

    summary = adm.evaluate("workspace-write", tasks, pid_alive=lambda _pid: True, thresholds=_LIMITS).summary()

    assert "lu-dispatch.slice" not in summary
