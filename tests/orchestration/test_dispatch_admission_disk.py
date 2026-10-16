"""Dispatch admission disk guard (#10776).

Disk usage comes from a monkeypatched probe and the reaper and the alert
publisher are fakes: no test reads the host disk, removes a worktree or posts
to Fleet Comms.
"""

from __future__ import annotations

import json
import logging
import types
from collections import namedtuple
from pathlib import Path

import pytest

from scripts.orchestration import dispatch_admission as adm

_GIB = 1024**3
_LIMITS = adm.Thresholds(max_live_write_workers=2, min_mem_available_gib=3.5, max_load_per_cpu=1.5)
_Usage = namedtuple("_Usage", "total used free")


def _disk(used_percent: float, *, size_gib: float = 400.0) -> adm.DiskProbe:
    used = int(size_gib * _GIB * used_percent / 100)
    return adm.DiskProbe(used_bytes=used, free_bytes=int(size_gib * _GIB) - used)


@pytest.fixture
def host(monkeypatch):
    """A healthy host whose disk readings come, in order, from ``readings``."""
    monkeypatch.setattr(
        adm,
        "probe_host",
        lambda: adm.HostProbe(mem_available_bytes=12 * _GIB, load1=2.0, cpu_count=8, proc_available=True),
    )
    monkeypatch.setattr(adm, "probe_pool", lambda _reserve: adm.pool_headroom.PoolCheck(reserve_bytes=0, skipped="n/a"))
    monkeypatch.setattr(adm, "probe_test_slots", lambda: adm.SlotQueueProbe(depth=0, pool_size=4))
    monkeypatch.setattr(adm, "slice_usage_clause", lambda: None)
    state: dict = {"readings": [_disk(50.0)], "probes": 0, "alerts": []}

    def probe_disk():
        state["probes"] += 1
        readings = state["readings"]
        return readings.pop(0) if len(readings) > 1 else readings[0]

    def publish(body, key):
        state["alerts"].append((body, key))

    monkeypatch.setattr(adm, "probe_disk", probe_disk)
    monkeypatch.setattr(adm, "post_disk_alert", publish)
    return state


class _Reaper:
    def __init__(self, outcome: adm.ReaperOutcome | None = None, *, frees_to: adm.DiskProbe | None = None, host=None):
        self.calls: list[Path] = []
        self.outcome = outcome or adm.ReaperOutcome(ran=True, detail="reaper removed 3 worktree(s)", removed=3)
        self.frees_to = frees_to
        self.host = host

    def __call__(self, repo_root: Path) -> adm.ReaperOutcome:
        self.calls.append(repo_root)
        if self.frees_to is not None:
            self.host["readings"] = [self.frees_to]
        return self.outcome


def test_below_the_alert_threshold_is_admitted_without_alert_or_reaper(tmp_path, host):
    host["readings"] = [_disk(79.9)]
    reaper = _Reaper()

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=reaper)

    assert decision.admitted
    assert reaper.calls == []
    assert host["alerts"] == []
    assert "disk 79.9% used, 80.4 GiB free (refuse at 85%, alert at 80%)" in decision.summary()
    record = decision.to_record()
    assert record["disk_used_percent"] == 79.9
    assert record["disk_free_gib"] == 80.4
    assert record["disk_alert"] is None


def test_alert_band_admits_and_alerts_once_then_suppresses_within_six_hours(tmp_path, host):
    host["readings"] = [_disk(82.0)]

    first = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS)
    second = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS)

    assert first.admitted and second.admitted
    assert len(host["alerts"]) == 1
    body, key = host["alerts"][0]
    assert "disk 82.0% used, 72.0 GiB free" in body
    assert "new write dispatches are still admitted" in body
    assert key.startswith("dispatch-admission-disk:")
    assert "[epics alert posted]" in first.summary()
    assert "[epics alert already posted at " in second.summary()
    assert first.to_record()["disk_alert"] == "epics alert posted"


def test_alert_rate_limit_reopens_after_six_hours(tmp_path):
    check = adm.DiskCheck(probe=_disk(81.0))
    sent: list[str] = []
    publish = lambda body, _key: sent.append(body)  # noqa: E731
    start = 1_800_000_000.0

    assert (
        adm.maybe_alert_disk(tmp_path, check, _LIMITS, refused=False, now=start, publish=publish)
        == "epics alert posted"
    )
    later = start + adm.DISK_ALERT_INTERVAL_S - 1
    assert adm.maybe_alert_disk(tmp_path, check, _LIMITS, refused=False, now=later, publish=publish).startswith(
        "epics alert already posted at "
    )
    after = start + adm.DISK_ALERT_INTERVAL_S
    assert (
        adm.maybe_alert_disk(tmp_path, check, _LIMITS, refused=False, now=after, publish=publish)
        == "epics alert posted"
    )
    assert len(sent) == 2
    assert not list(tmp_path.glob("*.json")), "the alert state must not look like a task record"


def test_alert_failure_never_blocks_and_retries_after_the_backoff(tmp_path, host, caplog, monkeypatch):
    host["readings"] = [_disk(83.0)]

    def broken(_body, _key):
        raise RuntimeError("plane down")

    monkeypatch.setattr(adm, "post_disk_alert", broken)
    caplog.set_level(logging.WARNING, logger=adm.__name__)
    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS)

    assert decision.admitted
    assert "[epics alert failed: plane down]" in decision.summary()
    assert "disk alert to epics failed: plane down" in caplog.text
    state = json.loads((tmp_path / adm.DISK_ALERT_STATE_NAME).read_text())
    assert state["last_error"] == "plane down"

    check = adm.DiskCheck(probe=_disk(83.0))
    sent: list[str] = []
    within = state["failed_at"] + adm.DISK_ALERT_RETRY_S - 1
    assert "retry after" in adm.maybe_alert_disk(
        tmp_path, check, _LIMITS, refused=False, now=within, publish=lambda body, _key: sent.append(body)
    )
    after = state["failed_at"] + adm.DISK_ALERT_RETRY_S
    assert (
        adm.maybe_alert_disk(tmp_path, check, _LIMITS, refused=False, now=after, publish=lambda b, _k: sent.append(b))
        == "epics alert posted"
    )
    assert len(sent) == 1


def test_unreadable_alert_state_does_not_silence_the_alert(tmp_path):
    (tmp_path / adm.DISK_ALERT_STATE_NAME).write_text("{not json")
    sent: list[str] = []

    outcome = adm.maybe_alert_disk(
        tmp_path, adm.DiskCheck(probe=_disk(90.0)), _LIMITS, refused=True, publish=lambda b, _k: sent.append(b)
    )

    assert outcome == "epics alert posted"
    assert "new write dispatches are REFUSED" in sent[0]


def test_full_disk_runs_the_reaper_once_then_refuses_with_percent_free_and_outcome(tmp_path, host):
    host["readings"] = [_disk(91.0)]
    reaper = _Reaper(adm.ReaperOutcome(ran=True, detail="reaper removed 0 worktree(s)"))

    decision = adm.evaluate("danger", tmp_path, thresholds=_LIMITS, reaper=reaper)

    assert not decision.admitted
    assert len(reaper.calls) == 1
    assert host["probes"] == 2  # measured before and after the reaper
    assert decision.failures == (
        "disk 91.0% used, 36.0 GiB free on the .worktrees filesystem is at or above the refuse threshold of 85% "
        "(DISPATCH_DISK_REFUSE_USED_PERCENT=85); reaper removed 0 worktree(s)",
    )
    line = decision.refusal_line()
    assert "91.0% used" in line and "36.0 GiB free" in line
    assert len(host["alerts"]) == 1 and "REFUSED" in host["alerts"][0][0]
    record = decision.to_record()
    assert record["disk_reaper"] == "reaper removed 0 worktree(s)"
    assert record["disk_used_percent_before_reaper"] == 91.0


def test_exactly_at_the_refuse_threshold_is_refused(tmp_path, host):
    host["readings"] = [_disk(85.0)]

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=_Reaper())

    assert not decision.admitted


def test_admitted_after_the_reaper_frees_space(tmp_path, host):
    host["readings"] = [_disk(88.0)]
    reaper = _Reaper(frees_to=_disk(70.0), host=host)

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=reaper)

    assert decision.admitted
    assert len(reaper.calls) == 1
    assert host["alerts"] == []  # the disk is below the alert level once reaped
    assert (
        "disk 70.0% used, 120.0 GiB free (refuse at 85%, alert at 80%) [reaper removed 3 worktree(s), 88.0% before]"
        in (decision.summary())
    )


@pytest.mark.parametrize(
    ("reaper", "detail"),
    [
        (lambda _root: (_ for _ in ()).throw(OSError("git lock busy")), "reaper failed: OSError: git lock busy"),
        (lambda _root: "not an outcome", "reaper failed: returned str, not ReaperOutcome"),
    ],
)
def test_a_reaper_that_raises_or_misbehaves_still_refuses_and_says_so(tmp_path, host, reaper, detail):
    host["readings"] = [_disk(90.0)]

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=reaper)

    assert not decision.admitted
    assert decision.failures[0].endswith(detail)


def test_missing_reaper_function_is_reported_unavailable_and_refuses(tmp_path, host, monkeypatch):
    host["readings"] = [_disk(90.0)]
    monkeypatch.setattr(adm, "load_reaper_module", types.SimpleNamespace)

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=adm.run_disk_reaper)

    assert not decision.admitted
    assert decision.failures[0].endswith(
        "reaper unavailable: scripts.orchestration.reap_worktrees.reap_idle_dispatch_worktrees is not present"
    )


def test_unimportable_reaper_module_is_reported_unavailable(monkeypatch):
    def fail():
        raise ImportError("no module")

    monkeypatch.setattr(adm, "load_reaper_module", fail)

    outcome = adm.run_disk_reaper(Path("/nonexistent"))

    assert outcome == adm.ReaperOutcome(
        ran=False, detail="reaper unavailable: scripts.orchestration.reap_worktrees did not import (no module)"
    )


def test_run_disk_reaper_calls_the_seam_with_the_primary_checkout_and_counts_removals(monkeypatch, tmp_path):
    calls: list[dict] = []
    result = types.SimpleNamespace

    def reap_idle_dispatch_worktrees(**kwargs):
        calls.append(kwargs)
        return [result(action="removed"), result(action="skipped"), result(action="preserved_then_removed")]

    module = types.SimpleNamespace(reap_idle_dispatch_worktrees=reap_idle_dispatch_worktrees)
    monkeypatch.setattr(adm, "load_reaper_module", lambda: module)

    outcome = adm.run_disk_reaper(tmp_path)

    assert calls == [{"repo_root": tmp_path}]
    assert outcome == adm.ReaperOutcome(ran=True, detail="reaper removed 2 worktree(s)", removed=2)


def test_without_a_reaper_a_full_disk_refuses_and_says_the_reaper_did_not_run(tmp_path, host):
    host["readings"] = [_disk(86.0)]

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS)

    assert not decision.admitted
    assert host["probes"] == 1
    assert decision.failures[0].endswith("reaper not run in this check")


@pytest.mark.parametrize("mode", ["read-only", "research"])
def test_read_only_dispatch_is_exempt_from_the_disk_check(tmp_path, monkeypatch, mode):
    monkeypatch.setattr(adm, "probe_disk", lambda: pytest.fail("read-only must not read the disk"))

    decision = adm.evaluate(mode, tmp_path, reaper=lambda _root: pytest.fail("read-only must not reap"))

    assert decision.exempt and decision.admitted


def test_a_failing_disk_probe_admits_and_logs_the_reason(tmp_path, host, caplog):
    host["readings"] = [adm.DiskProbe(skipped="disk usage unreadable: OSError: [Errno 5] I/O error")]
    caplog.set_level(logging.WARNING, logger=adm.__name__)
    reaper = _Reaper()

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=reaper)

    assert decision.admitted
    assert reaper.calls == [] and host["alerts"] == []
    assert "disk check skipped (disk usage unreadable: OSError: [Errno 5] I/O error)" in decision.summary()
    assert "disk check skipped: disk usage unreadable" in caplog.text
    assert decision.to_record()["disk_check_skipped"].startswith("disk usage unreadable")


def test_a_probe_that_fails_after_the_reaper_admits(tmp_path, host):
    host["readings"] = [_disk(95.0)]
    reaper = _Reaper(frees_to=adm.DiskProbe(skipped="disk usage unreadable: OSError: gone"), host=host)

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=reaper)

    assert decision.admitted
    assert "disk check skipped (disk usage unreadable: OSError: gone) [reaper removed 3 worktree(s), 95.0% before]" in (
        decision.summary()
    )


def test_read_disk_uses_df_percent_and_reports_unreadable_statvfs(tmp_path):
    probe = adm.read_disk(tmp_path, usage=lambda _path: _Usage(total=100 * _GIB, used=45 * _GIB, free=45 * _GIB))
    assert probe.used_percent == 50.0  # used / (used + available), as df prints it
    assert probe.free_gib == 45.0

    def broken(_path):
        raise PermissionError("statvfs denied")

    unreadable = adm.read_disk(tmp_path, usage=broken)
    assert unreadable.used_percent is None
    assert unreadable.skipped == "disk usage unreadable: PermissionError: statvfs denied"

    invalid = adm.read_disk(tmp_path, usage=lambda _path: _Usage(total=0, used=0, free=0))
    assert invalid.skipped == "disk usage invalid: used=0 free=0"


def test_the_default_loader_imports_the_common_reaper():
    from scripts.orchestration import reap_worktrees

    assert adm.load_reaper_module() is reap_worktrees
    assert reap_worktrees.__name__ == adm.REAPER_MODULE


def test_healthy_test_host_never_reads_the_real_disk_or_posts(monkeypatch):
    monkeypatch.setattr(adm, "read_disk", lambda *_a, **_k: pytest.fail("real disk read"))

    assert adm.probe_disk().skipped == adm.TEST_HOST_POOL_SKIP
    with pytest.raises(RuntimeError, match="test host"):
        adm.post_disk_alert("body", "key")


def test_worktrees_disk_path_is_the_primary_checkouts_worktrees(monkeypatch, tmp_path):
    (tmp_path / ".worktrees").mkdir()
    monkeypatch.setattr(adm, "primary_checkout", lambda: tmp_path)
    assert adm.worktrees_disk_path() == tmp_path / ".worktrees"
    (tmp_path / ".worktrees").rmdir()
    assert adm.worktrees_disk_path() == tmp_path


def test_disk_thresholds_default_to_config_and_honour_env_overrides():
    defaults = adm.load_thresholds({})
    assert (defaults.disk_refuse_used_percent, defaults.disk_alert_used_percent) == (85.0, 80.0)

    custom = adm.load_thresholds(
        {"DISPATCH_DISK_REFUSE_USED_PERCENT": "92.5", "DISPATCH_DISK_ALERT_USED_PERCENT": "75"}
    )
    assert (custom.disk_refuse_used_percent, custom.disk_alert_used_percent) == (92.5, 75.0)


@pytest.mark.parametrize("raw", ["101", "-1", "lots", "nan"])
def test_invalid_disk_threshold_env_is_rejected(raw):
    with pytest.raises(ValueError, match="DISPATCH_DISK_REFUSE_USED_PERCENT"):
        adm.load_thresholds({"DISPATCH_DISK_REFUSE_USED_PERCENT": raw})


def test_publish_runs_the_fleet_comms_channel_publish_command(monkeypatch, tmp_path):
    monkeypatch.delenv("LU_TEST_DISPATCH_HEALTHY_HOST", raising=False)
    monkeypatch.setattr(adm, "primary_checkout", lambda: tmp_path)
    with pytest.raises(RuntimeError, match="fleet_comms publish could not run: project interpreter not found"):
        adm.post_disk_alert("disk full\n", "k")
    interpreter = tmp_path / ".venv" / "bin" / "python"
    interpreter.parent.mkdir(parents=True)
    interpreter.touch()
    seen: dict = {}

    def run(command, **kwargs):
        seen["command"], seen["kwargs"] = command, kwargs
        return adm.subprocess.CompletedProcess(command, 0, "{}", "")

    monkeypatch.setattr(adm.subprocess, "run", run)

    adm.post_disk_alert("disk full\n", "dispatch-admission-disk:t")

    assert seen["command"][0] == str(interpreter)
    assert seen["kwargs"]["cwd"] == tmp_path
    assert seen["command"][1:] == [
        "-m",
        "scripts.fleet_comms",
        "channel",
        "publish",
        "epics",
        "-",
        "--sender",
        "dispatch-admission",
        "--source",
        "dispatch-admission",
        "--kind",
        "report",
        "--idempotency-key",
        "dispatch-admission-disk:t",
    ]
    assert seen["kwargs"]["input"] == "disk full\n"
    assert seen["kwargs"]["timeout"] == adm.DISK_ALERT_PUBLISH_TIMEOUT_S

    monkeypatch.setattr(
        adm.subprocess, "run", lambda command, **_k: adm.subprocess.CompletedProcess(command, 2, "", "no channel\n")
    )
    with pytest.raises(RuntimeError, match="fleet_comms publish exited 2: no channel"):
        adm.post_disk_alert("disk full\n", "k")
