"""Dispatch admission disk guard (#10776).

Disk usage comes from a monkeypatched probe and the reaper and the alert
publisher are fakes: no test reads the host disk, removes a worktree or posts
to Fleet Comms.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import logging
import os
import sys
import threading
import time
import types
from collections import namedtuple
from dataclasses import dataclass
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


def _in_process(repo_root: Path, _timeout_s: float) -> adm.ReaperOutcome:
    """The reaper call without the child process, so a fake ``reap_clean_pushed`` is visible."""
    return adm.reap_clean_pushed_once(repo_root)


class _Reaper:
    def __init__(self, outcome: adm.ReaperOutcome | None = None, *, frees_to: adm.DiskProbe | None = None, host=None):
        self.calls: list[Path] = []
        self.timeouts: list[float | None] = []
        self.outcome = outcome or adm.ReaperOutcome(ran=True, detail="reaper removed 3 worktree(s)", removed=3)
        self.frees_to = frees_to
        self.host = host

    def __call__(self, repo_root: Path, timeout_s: float | None = None) -> adm.ReaperOutcome:
        self.calls.append(repo_root)
        self.timeouts.append(timeout_s)
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
        (lambda _root, _t: (_ for _ in ()).throw(OSError("git lock busy")), "reaper failed: OSError: git lock busy"),
        (lambda _root, _t: "not an outcome", "reaper failed: returned str, not ReaperOutcome"),
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

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=_in_process)

    assert not decision.admitted
    assert decision.failures[0].endswith(
        "reaper unavailable: scripts.orchestration.reap_worktrees.reap_clean_pushed is not present"
    )


@dataclass(frozen=True)
class _CleanPushedOutcome:
    """Test double with the field names of ``reap_worktrees.CleanPushedOutcome`` (#10778)."""

    path: str
    action: str
    reason: str


@dataclass(frozen=True)
class _CleanPushedReport:
    """Test double with the field names of ``reap_worktrees.CleanPushedReport`` (#10778)."""

    dry_run: bool
    removed: tuple[_CleanPushedOutcome, ...]
    skipped: tuple[_CleanPushedOutcome, ...]
    freed_mb: int
    lock_busy: bool = False
    refusal: str | None = None


def _skip(path: str, reason: str) -> _CleanPushedOutcome:
    return _CleanPushedOutcome(path=path, action="skipped", reason=reason)


class _ReapCleanPushed:
    """A fake ``reap_clean_pushed`` that records its calls and may free the disk."""

    def __init__(self, report: _CleanPushedReport | Exception, *, host=None, frees_to=None):
        self.calls: list[dict] = []
        self.report = report
        self.host = host
        self.frees_to = frees_to

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.report, Exception):
            raise self.report
        if self.frees_to is not None:
            self.host["readings"] = [self.frees_to]
        return self.report

    def install(self, monkeypatch) -> None:
        monkeypatch.setattr(adm, "load_reaper_module", lambda: types.SimpleNamespace(reap_clean_pushed=self))


def test_reap_clean_pushed_is_called_once_as_an_apply_run_with_a_short_lock_timeout(monkeypatch, tmp_path):
    fake = _ReapCleanPushed(_CleanPushedReport(dry_run=False, removed=(), skipped=(), freed_mb=0))
    fake.install(monkeypatch)

    outcome = adm.reap_clean_pushed_once(tmp_path)

    assert fake.calls == [{"repo_root": tmp_path, "dry_run": False, "lock_timeout_s": adm.DISK_REAPER_LOCK_TIMEOUT_S}]
    assert adm.DISK_REAPER_LOCK_TIMEOUT_S == 5.0
    assert outcome == adm.ReaperOutcome(ran=True, detail="reaper removed 0 worktree(s), freed 0 MB")


def test_removed_trees_free_the_disk_and_the_dispatch_is_admitted(monkeypatch, tmp_path, host):
    host["readings"] = [_disk(90.0)]
    removed = tuple(
        _CleanPushedOutcome(path=f".worktrees/dispatch/a/t{i}", action="removed", reason="ok") for i in (1, 2)
    )
    report = _CleanPushedReport(dry_run=False, removed=removed, skipped=(), freed_mb=3072)
    fake = _ReapCleanPushed(report, host=host, frees_to=_disk(70.0))
    fake.install(monkeypatch)
    monkeypatch.setattr(adm, "primary_checkout", lambda: tmp_path)

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=_in_process)

    assert decision.admitted
    assert [call["repo_root"] for call in fake.calls] == [tmp_path]
    assert "[reaper removed 2 worktree(s), freed 3072 MB, 90.0% before]" in decision.summary()


def test_removals_that_leave_the_disk_full_refuse_with_counts_and_top_skip_reasons(monkeypatch, tmp_path, host):
    host["readings"] = [_disk(92.0)]
    removed = (_CleanPushedOutcome(path=".worktrees/dispatch/a/t1", action="removed", reason="ok"),)
    skipped = (
        _skip(".worktrees/dispatch/a/t2", "uncommitted or untracked changes"),
        _skip(".worktrees/dispatch/a/t3", "unpublished_reflog_commit"),
        _skip(".worktrees/dispatch/a/t4", "uncommitted or untracked changes"),
        _skip(".worktrees/dispatch/a/t5", "late_change"),
        _skip(".worktrees/dispatch/a/t6", "unpublished_reflog_commit"),
        _skip(".worktrees/dispatch/a/t7", "uncommitted or untracked changes"),
        _skip(".worktrees/dispatch/a/t8", "uninspectable"),
        _skip(".worktrees/dispatch/a/t9", "x" * 200),
    )
    fake = _ReapCleanPushed(_CleanPushedReport(dry_run=False, removed=removed, skipped=skipped, freed_mb=512))
    fake.install(monkeypatch)
    monkeypatch.setattr(adm, "primary_checkout", lambda: tmp_path)

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=_in_process)

    assert not decision.admitted
    assert decision.failures[0].endswith(
        "reaper removed 1 worktree(s), freed 512 MB; skipped 8: uncommitted or untracked changes (3); "
        "unpublished_reflog_commit (2); late_change (1)"
    )


def test_skip_reasons_are_truncated():
    report = _CleanPushedReport(dry_run=False, removed=(), skipped=(_skip("p", "x" * 200),), freed_mb=0)

    assert adm._reaper_outcome(report).detail.endswith("skipped 1: " + "x" * 80 + " (1)")


@pytest.mark.parametrize(
    ("report", "detail"),
    [
        (
            _CleanPushedReport(
                dry_run=False,
                removed=(),
                skipped=(),
                freed_mb=0,
                lock_busy=True,
                refusal="another cleanup holds the reaper lock",
            ),
            "reaper did not run: lock busy (another cleanup holds the reaper lock)",
        ),
        (
            _CleanPushedReport(
                dry_run=False, removed=(), skipped=(), freed_mb=0, refusal="refs_stale: git fetch origin timed out"
            ),
            "reaper refused (refs_stale: git fetch origin timed out)",
        ),
    ],
)
def test_a_busy_or_refusing_reaper_still_refuses_and_says_why(monkeypatch, tmp_path, host, report, detail):
    host["readings"] = [_disk(90.0)]
    _ReapCleanPushed(report).install(monkeypatch)
    monkeypatch.setattr(adm, "primary_checkout", lambda: tmp_path)

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=_in_process)

    assert not decision.admitted
    assert decision.failures[0].endswith(detail)
    assert host["probes"] == 2  # measured again after the reaper, never admitted on its say-so


def test_reap_clean_pushed_that_raises_or_returns_a_wrong_shape_is_reaper_failed(monkeypatch, tmp_path):
    _ReapCleanPushed(OSError("git lock busy")).install(monkeypatch)
    assert adm.reap_clean_pushed_once(tmp_path) == adm.ReaperOutcome(
        ran=False, detail="reaper failed: OSError: git lock busy"
    )

    _ReapCleanPushed([types.SimpleNamespace(action="removed")]).install(monkeypatch)  # type: ignore[arg-type]
    outcome = adm.reap_clean_pushed_once(tmp_path)
    assert not outcome.ran
    assert outcome.detail.startswith("reaper failed: AttributeError:")


def test_the_common_reaper_matches_the_reap_clean_pushed_contract():
    """The seam's contract with #10778; strict once ``reap_clean_pushed`` is in the tree."""
    from scripts.orchestration import reap_worktrees

    function = getattr(reap_worktrees, adm.REAPER_FUNCTION, None)
    if function is None:
        # #10778 has not landed: the seam must say so and never admit on it.
        assert adm.reap_clean_pushed_once(Path("/nonexistent")) == adm.ReaperOutcome(
            ran=False,
            detail="reaper unavailable: scripts.orchestration.reap_worktrees.reap_clean_pushed is not present",
        )
        return
    parameters = inspect.signature(function).parameters
    for name in ("repo_root", "dry_run", "lock_timeout_s"):
        assert parameters[name].kind is inspect.Parameter.KEYWORD_ONLY, name
    report_fields = {field.name for field in dataclasses.fields(reap_worktrees.CleanPushedReport)}
    assert {field.name for field in dataclasses.fields(_CleanPushedReport)} <= report_fields
    outcome_fields = {field.name for field in dataclasses.fields(reap_worktrees.CleanPushedOutcome)}
    assert {field.name for field in dataclasses.fields(_CleanPushedOutcome)} <= outcome_fields


@pytest.mark.xfail(
    strict=True,
    reason="#10778: reap_clean_pushed is not in the tree yet; whichever of #10776/#10778 lands second removes this marker",
)
def test_the_common_reaper_provides_reap_clean_pushed():
    """Fails while ``reap_clean_pushed`` is missing; the strict marker turns its arrival into a required pass."""
    from scripts.orchestration import reap_worktrees

    assert callable(getattr(reap_worktrees, adm.REAPER_FUNCTION, None))


def test_unimportable_reaper_module_is_reported_unavailable(monkeypatch):
    def fail():
        raise ImportError("no module")

    monkeypatch.setattr(adm, "load_reaper_module", fail)

    outcome = adm.reap_clean_pushed_once(Path("/nonexistent"))

    assert outcome == adm.ReaperOutcome(
        ran=False, detail="reaper unavailable: scripts.orchestration.reap_worktrees did not import (no module)"
    )


def test_without_a_reaper_a_full_disk_refuses_and_says_the_reaper_did_not_run(tmp_path, host):
    host["readings"] = [_disk(86.0)]

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS)

    assert not decision.admitted
    assert host["probes"] == 1
    assert decision.failures[0].endswith("reaper not run in this check")


@pytest.mark.parametrize("mode", ["read-only", "research"])
def test_read_only_dispatch_is_exempt_from_the_disk_check(tmp_path, monkeypatch, mode):
    monkeypatch.setattr(adm, "probe_disk", lambda: pytest.fail("read-only must not read the disk"))

    decision = adm.evaluate(mode, tmp_path, reaper=lambda _root, _t: pytest.fail("read-only must not reap"))

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


# --- Round 3 (#10776): hard stop, one shared reaper attempt, deadline, redaction, alert state ----------

_NOTHING_FREED = "reaper removed 0 worktree(s), freed 0 MB"


def test_a_disk_refusal_is_marked_as_a_hard_stop_and_does_not_offer_the_force_flag(tmp_path, host):
    host["readings"] = [_disk(90.0)]

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=_Reaper())

    assert decision.disk_refused and decision.disk is not None and decision.disk.refused
    assert decision.to_record()["disk_refused"] is True
    assert "--force-admission cannot override a full disk" in decision.refusal_line()
    assert 'pass --force-admission "<reason>"' not in decision.refusal_line()


def test_other_refusals_are_not_disk_refusals(tmp_path, host):
    host["readings"] = [_disk(50.0)]
    capped = dataclasses.replace(_LIMITS, max_live_write_workers=0)

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=capped, reaper=_Reaper())

    assert not decision.admitted and not decision.disk_refused
    assert 'pass --force-admission "<reason>" to override' in decision.refusal_line()


def test_six_concurrent_checks_share_one_reaper_attempt(tmp_path, host):
    host["readings"] = [_disk(90.0)]
    release = threading.Event()
    entries: list[Path] = []
    start = threading.Barrier(6)
    decisions: list[adm.AdmissionDecision] = []

    def blocking_reaper(repo_root: Path, _timeout_s: float | None = None) -> adm.ReaperOutcome:
        entries.append(repo_root)
        release.wait(10)
        return adm.ReaperOutcome(ran=True, detail=_NOTHING_FREED)

    def check() -> None:
        start.wait(10)
        decisions.append(adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=blocking_reaper))

    threads = [threading.Thread(target=check) for _ in range(6)]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + 10
    while sum(not thread.is_alive() for thread in threads) < 5 and time.monotonic() < deadline:
        time.sleep(0.01)
    release.set()
    for thread in threads:
        thread.join(10)

    assert len(entries) == 1
    assert len(decisions) == 6 and not any(decision.admitted for decision in decisions)
    waiting = [d for d in decisions if "reaper attempt in progress in another dispatch" in d.failures[0]]
    assert len(waiting) == 5


def test_retries_within_the_cooldown_reuse_the_recorded_outcome(tmp_path, host):
    host["readings"] = [_disk(90.0)]
    reaper = _Reaper(adm.ReaperOutcome(ran=True, detail=_NOTHING_FREED))

    decisions = [adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=reaper) for _ in range(3)]

    assert len(reaper.calls) == 1
    assert not any(decision.admitted for decision in decisions)
    for retry in decisions[1:]:
        assert retry.failures[0].endswith(f"reaper attempted 0 s ago: {_NOTHING_FREED}")
    state = json.loads((tmp_path / adm.DISK_REAPER_STATE_NAME).read_text())
    assert state["detail"] == _NOTHING_FREED and state["freed"] is False


def test_the_cooldown_expires_and_an_attempt_that_freed_space_resets_it(tmp_path):
    limits = dataclasses.replace(_LIMITS, disk_reaper_cooldown_s=600.0)
    clock = {"t": 1_800_000_000.0}
    nothing = _Reaper(adm.ReaperOutcome(ran=True, detail=_NOTHING_FREED))

    assert adm.attempt_disk_reaper(tmp_path, nothing, limits, now=lambda: clock["t"]).ran
    clock["t"] += 599
    held = adm.attempt_disk_reaper(tmp_path, nothing, limits, now=lambda: clock["t"])
    assert held == adm.ReaperOutcome(ran=False, detail=f"reaper attempted 599 s ago: {_NOTHING_FREED}")
    clock["t"] += 1
    assert adm.attempt_disk_reaper(tmp_path, nothing, limits, now=lambda: clock["t"]).ran
    assert len(nothing.calls) == 2

    freeing = _Reaper(adm.ReaperOutcome(ran=True, detail="reaper removed 2 worktree(s), freed 900 MB", removed=2))
    clock["t"] += 700
    adm.attempt_disk_reaper(tmp_path, freeing, limits, now=lambda: clock["t"])
    clock["t"] += 1
    adm.attempt_disk_reaper(tmp_path, freeing, limits, now=lambda: clock["t"])
    assert len(freeing.calls) == 2
    assert freeing.timeouts == [adm.DISK_REAPER_TIMEOUT_S, adm.DISK_REAPER_TIMEOUT_S]


def test_a_last_attempt_dated_in_the_future_counts_as_just_made(tmp_path):
    (tmp_path / adm.DISK_REAPER_STATE_NAME).write_text(
        json.dumps({"last_attempt_at": 1_900_000_000.0, "detail": _NOTHING_FREED, "freed": False})
    )
    clock = {"t": 1_800_000_000.0}
    reaper = _Reaper()

    held = adm.attempt_disk_reaper(tmp_path, reaper, _LIMITS, now=lambda: clock["t"])

    assert held == adm.ReaperOutcome(ran=False, detail=f"reaper attempted 0 s ago: {_NOTHING_FREED}")
    assert json.loads((tmp_path / adm.DISK_REAPER_STATE_NAME).read_text())["last_attempt_at"] == clock["t"]
    clock["t"] += adm.DISK_REAPER_COOLDOWN_S
    assert adm.attempt_disk_reaper(tmp_path, reaper, _LIMITS, now=lambda: clock["t"]).ran
    assert len(reaper.calls) == 1


@pytest.mark.parametrize(
    "raw", ["{not json", '{"last_attempt_at": 1' + "0" * 400 + ', "detail": "x", "freed": false}', "[]"]
)
def test_a_malformed_reaper_state_does_not_block_the_reaper(tmp_path, raw):
    (tmp_path / adm.DISK_REAPER_STATE_NAME).write_text(raw)
    reaper = _Reaper()

    assert adm.attempt_disk_reaper(tmp_path, reaper, _LIMITS).ran
    assert len(reaper.calls) == 1


def _state_writes_fail(monkeypatch, *, after: int = 0) -> list[str]:
    """Every reaper state write after the first ``after`` fails with ENOSPC; returns the write log."""
    real_open = Path.open
    writes: list[str] = []

    def open_(self, mode="r", *args, **kwargs):
        if self.name.startswith(f"{adm.DISK_REAPER_STATE_NAME}.tmp") and "w" in mode:
            writes.append(self.name)
            if len(writes) > after:
                raise OSError(28, "No space left on device", str(self))
        return real_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_)
    return writes


def _expired_attempt(tasks: Path) -> None:
    (tasks / adm.DISK_REAPER_ATTEMPT_LOCK_NAME).touch()
    (tasks / adm.DISK_REAPER_STATE_NAME).write_text(
        json.dumps({"last_attempt_at": time.time() - 3600, "detail": _NOTHING_FREED, "freed": False})
    )


def test_a_reaper_attempt_that_cannot_be_recorded_is_not_made(tmp_path, host, monkeypatch):
    """Review reproducer (round 3): ENOSPC on the state write, three immediate retries at 100%."""
    host["readings"] = [_disk(100.0)]
    _expired_attempt(tmp_path)
    _state_writes_fail(monkeypatch)
    reaper = _Reaper(adm.ReaperOutcome(ran=True, detail=_NOTHING_FREED))

    decisions = [adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=reaper) for _ in range(3)]

    assert reaper.calls == []  # record, then act: no marker, no reaper
    for decision in decisions:
        assert not decision.admitted and decision.disk_refused
        assert "reaper not run: cannot record reaper attempt (" in decision.failures[0]
        assert "No space left on device" in decision.failures[0]
        assert str(tmp_path) not in decision.failures[0]
    assert [p.name for p in tmp_path.iterdir() if ".tmp" in p.name] == []


def test_a_recorded_attempt_holds_the_cooldown_when_its_outcome_cannot_be_written(tmp_path, host, monkeypatch):
    host["readings"] = [_disk(100.0)]
    _expired_attempt(tmp_path)
    writes = _state_writes_fail(monkeypatch, after=1)  # the marker is written; the outcome write fails
    reaper = _Reaper(adm.ReaperOutcome(ran=True, detail=_NOTHING_FREED))

    decisions = [adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=reaper) for _ in range(3)]

    assert len(reaper.calls) == 1
    assert len(writes) == 2
    assert not any(decision.admitted for decision in decisions)
    for retry in decisions[1:]:
        assert "reaper attempted 0 s ago: " in retry.failures[0]
    state = json.loads((tmp_path / adm.DISK_REAPER_STATE_NAME).read_text())
    assert state["freed"] is False and state["ran"] is False


def test_the_attempt_marker_is_on_disk_before_the_reaper_runs(tmp_path):
    seen: list[dict] = []

    def reaper(_root: Path, _timeout_s: float | None = None) -> adm.ReaperOutcome:
        seen.append(json.loads((tmp_path / adm.DISK_REAPER_STATE_NAME).read_text()))
        return adm.ReaperOutcome(ran=True, detail=_NOTHING_FREED)

    adm.attempt_disk_reaper(tmp_path, reaper, _LIMITS, now=lambda: 1_800_000_000.0)

    assert seen == [
        {
            "last_attempt_at": 1_800_000_000.0,
            "detail": adm.DISK_REAPER_STARTED,
            "ran": False,
            "removed": 0,
            "freed_mb": 0,
            "freed": False,
        }
    ]
    assert json.loads((tmp_path / adm.DISK_REAPER_STATE_NAME).read_text())["detail"] == _NOTHING_FREED


def test_disk_reaper_cooldown_and_timeout_default_to_config_and_honour_env_overrides():
    defaults = adm.load_thresholds({})
    assert (defaults.disk_reaper_cooldown_s, defaults.disk_reaper_timeout_s) == (600.0, 90.0)
    assert (adm.DISK_REAPER_COOLDOWN_S, adm.DISK_REAPER_TIMEOUT_S) == (600.0, 90.0)

    custom = adm.load_thresholds({"DISPATCH_DISK_REAPER_COOLDOWN_S": "0", "DISPATCH_DISK_REAPER_TIMEOUT_S": "30"})
    assert (custom.disk_reaper_cooldown_s, custom.disk_reaper_timeout_s) == (0.0, 30.0)


@pytest.mark.parametrize(
    ("name", "raw"),
    [
        ("DISPATCH_DISK_REAPER_TIMEOUT_S", "0"),
        ("DISPATCH_DISK_REAPER_TIMEOUT_S", "inf"),
        ("DISPATCH_DISK_REAPER_TIMEOUT_S", "-5"),
        ("DISPATCH_DISK_REAPER_COOLDOWN_S", "inf"),
        ("DISPATCH_DISK_REAPER_COOLDOWN_S", "soon"),
    ],
)
def test_invalid_disk_reaper_timing_env_is_rejected(name, raw):
    with pytest.raises(ValueError, match=name):
        adm.load_thresholds({name: raw})


def _gone(pid: int) -> bool:
    """The pid has exited (a zombie awaiting its new parent counts as gone)."""
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        try:
            if Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0] == "Z":
                return True
        except (OSError, IndexError):
            pass
        time.sleep(0.05)
    return False


def test_a_stuck_reaper_is_stopped_at_the_deadline_and_admission_refuses(tmp_path, host, monkeypatch):
    host["readings"] = [_disk(90.0)]
    monkeypatch.setattr(
        adm, "disk_reaper_command", lambda _root: ([sys.executable, "-c", "import time; time.sleep(60)"], tmp_path)
    )
    monkeypatch.setattr(adm, "primary_checkout", lambda: tmp_path)
    limits = dataclasses.replace(_LIMITS, disk_reaper_timeout_s=1.0)

    started = time.monotonic()
    decision = adm.evaluate("workspace-write", tmp_path, thresholds=limits, reaper=adm.run_disk_reaper)
    elapsed = time.monotonic() - started

    assert elapsed < 1.0 + 2 * adm.DISK_REAPER_KILL_GRACE_S
    assert not decision.admitted and decision.disk_refused
    assert decision.failures[0].endswith("reaper timed out after 1 s and was stopped")


def test_the_reaper_process_group_is_killed_even_when_it_ignores_sigterm(tmp_path, monkeypatch):
    pid_file = tmp_path / "grandchild.pid"
    ignore = "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
    script = (
        "import signal, subprocess, sys, time\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        f"child = subprocess.Popen([sys.executable, '-c', {ignore + 'time.sleep(60)'!r}])\n"
        "open(sys.argv[1], 'w').write(str(child.pid))\n"
        "time.sleep(60)\n"
    )
    monkeypatch.setattr(
        adm, "disk_reaper_command", lambda _root: ([sys.executable, "-c", script, str(pid_file)], tmp_path)
    )
    monkeypatch.setattr(adm, "DISK_REAPER_KILL_GRACE_S", 0.5)

    started = time.monotonic()
    outcome = adm.run_disk_reaper(tmp_path, timeout_s=2.0)

    assert time.monotonic() - started < 2.0 + 2 * 0.5 + 1.0
    assert outcome == adm.ReaperOutcome(ran=False, detail="reaper timed out after 2 s and was stopped")
    assert _gone(int(pid_file.read_text()))


@pytest.mark.parametrize(
    ("script", "expected"),
    [
        (
            "print('chatter'); print("
            + repr(
                json.dumps(
                    {
                        "ran": True,
                        "detail": "reaper removed 1 worktree(s), freed 5 MB",
                        "removed": 1,
                        "freed_mb": 5,
                        "lock_busy": False,
                    }
                )
            )
            + ")",
            adm.ReaperOutcome(ran=True, detail="reaper removed 1 worktree(s), freed 5 MB", removed=1, freed_mb=5),
        ),
        (
            "import sys; sys.stderr.write('boom\\nfatal: index locked\\n'); sys.exit(3)",
            adm.ReaperOutcome(ran=False, detail="reaper failed: the reaper process exited 3: fatal: index locked"),
        ),
        (
            "print('not json')",
            adm.ReaperOutcome(ran=False, detail="reaper failed: the reaper process printed no outcome"),
        ),
        (
            "print('{\"ran\": true}')",
            adm.ReaperOutcome(ran=False, detail="reaper failed: the reaper process printed no outcome"),
        ),
    ],
)
def test_the_reaper_child_outcome_is_parsed_or_reported_failed(tmp_path, monkeypatch, script, expected):
    monkeypatch.setattr(adm, "disk_reaper_command", lambda _root: ([sys.executable, "-c", script], tmp_path))

    assert adm.run_disk_reaper(tmp_path, timeout_s=30.0) == expected


def test_a_reaper_child_that_cannot_start_is_unavailable_or_failed(tmp_path, monkeypatch):
    def no_interpreter(_root):
        raise FileNotFoundError("project interpreter not found")

    monkeypatch.setattr(adm, "disk_reaper_command", no_interpreter)
    assert adm.run_disk_reaper(tmp_path) == adm.ReaperOutcome(
        ran=False, detail="reaper unavailable: project interpreter not found"
    )

    monkeypatch.setattr(adm, "disk_reaper_command", lambda _root: ([str(tmp_path / "missing-python")], tmp_path))
    outcome = adm.run_disk_reaper(tmp_path)
    assert not outcome.ran and outcome.detail.startswith("reaper failed: could not start the reaper process:")


def test_the_default_child_command_runs_this_module_from_its_own_checkout():
    command, cwd = adm.disk_reaper_command(Path("/srv/checkout"))

    assert command[1:] == ["-m", "scripts.orchestration.dispatch_admission", "--run-disk-reaper", "/srv/checkout"]
    assert cwd == Path(adm.__file__).resolve().parents[2]


def test_the_child_entry_prints_one_json_outcome_and_keeps_reaper_output_off_stdout(monkeypatch, tmp_path, capsys):
    def noisy(**_kwargs):
        print("reaper chatter")
        return _CleanPushedReport(dry_run=False, removed=(), skipped=(), freed_mb=0)

    monkeypatch.setattr(adm, "load_reaper_module", lambda: types.SimpleNamespace(reap_clean_pushed=noisy))

    assert adm._reaper_child_main(["--run-disk-reaper", str(tmp_path)]) == 0
    captured = capsys.readouterr()
    assert len(captured.out.splitlines()) == 1
    assert "reaper chatter" in captured.err
    assert adm._parse_child_outcome(captured.out) == adm.ReaperOutcome(ran=True, detail=_NOTHING_FREED)
    assert adm._reaper_child_main([]) == 2


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_reaper_child_help_prints_usage_and_exits_zero(flag, capsys):
    assert adm._reaper_child_main([flag]) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("usage: python -m scripts.orchestration.dispatch_admission")
    assert captured.err == ""


def test_the_real_reaper_child_starts_and_reports_an_outcome(tmp_path, monkeypatch):
    # The real reaper (once #10778 lands) refuses to touch anything with this set.
    monkeypatch.setenv("LU_REAPER_DISABLED", "1")

    outcome = adm.run_disk_reaper(tmp_path / "no-checkout", timeout_s=60.0)

    assert outcome.detail.startswith("reaper ")
    assert not outcome.detail.startswith(
        ("reaper timed out", "reaper failed: the reaper process", "reaper failed: could not start")
    ), outcome.detail


@pytest.mark.parametrize(
    ("text", "redacted"),
    [
        ("lock /home/someone/repo/.reaper.lock is held", "lock <path> is held"),
        ("held (~/learn-ukrainian/x.lock)", "held (<path>)"),
        ("see ~someone/x and /srv/data/a:12", "see <path> and <path>"),
        ("origin/main is 3/4 behind; refs/heads/x", "origin/main is 3/4 behind; refs/heads/x"),
        ("reaper removed 0 worktree(s), freed 0 MB", "reaper removed 0 worktree(s), freed 0 MB"),
        ("lock %2Fhome%2Fsomeone%2Frepo.lock is held", "lock <path> is held"),
        ("url file%3A%2F%2F%2Fvar%2Ftmp%2Fa failed", "url <path> failed"),
        ("double %252Fsrv%252Fdata%252Fx", "double <path>"),
        ("held (%7E%2Frepo%2Fx.lock)", "held (<path>)"),
        ("disk 50%25 used; origin%2Fmain; 100% full", "disk 50%25 used; origin%2Fmain; 100% full"),
    ],
)
def test_redact_paths(text, redacted):
    assert adm.redact_paths(text) == redacted


def test_reaper_paths_are_redacted_from_the_refusal_record_state_and_alert(monkeypatch, tmp_path, host):
    host["readings"] = [_disk(90.0)]
    lock = "/home/someone/learn-ukrainian/batch_state/reaper.lock"
    report = _CleanPushedReport(
        dry_run=False, removed=(), skipped=(), freed_mb=0, lock_busy=True, refusal=f"another cleanup holds {lock}"
    )
    _ReapCleanPushed(report).install(monkeypatch)
    monkeypatch.setattr(adm, "primary_checkout", lambda: tmp_path)

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=_in_process)

    assert decision.failures[0].endswith("reaper did not run: lock busy (another cleanup holds <path>)")
    published = host["alerts"][0][0]
    recorded = (tmp_path / adm.DISK_REAPER_STATE_NAME).read_text()
    for text in (decision.refusal_line(), decision.summary(), json.dumps(decision.to_record()), published, recorded):
        assert "/home" not in text and "someone" not in text


def test_a_failed_alert_publish_is_redacted(tmp_path):
    def broken(_body, _key):
        raise RuntimeError(
            "fleet_comms publish could not run: [Errno 2] No such file: '/home/someone/.venv/bin/python'"
        )

    outcome = adm.maybe_alert_disk(tmp_path, adm.DiskCheck(probe=_disk(82.0)), _LIMITS, refused=False, publish=broken)

    assert "/home" not in outcome and "<path>" in outcome
    assert "/home" not in (tmp_path / adm.DISK_ALERT_STATE_NAME).read_text()


@pytest.mark.parametrize("key", ["posted_at", "failed_at"])
@pytest.mark.parametrize("value", ["1" + "0" * 400, '"yesterday"', "true"])
def test_a_malformed_alert_time_counts_as_an_alert_failure(tmp_path, key, value):
    (tmp_path / adm.DISK_ALERT_STATE_NAME).write_text(f'{{"{key}": {value}}}')
    sent: list[str] = []
    start = 1_800_000_000.0
    publish = lambda body, _key: sent.append(body)  # noqa: E731
    check = adm.DiskCheck(probe=_disk(82.0))

    outcome = adm.maybe_alert_disk(tmp_path, check, _LIMITS, refused=False, now=start, publish=publish)

    assert outcome.startswith(f"epics alert failed: alert state malformed ({key} ")
    assert sent == []
    state = json.loads((tmp_path / adm.DISK_ALERT_STATE_NAME).read_text())
    assert state["failed_at"] == start and state["last_error"].startswith("alert state malformed")
    later = start + adm.DISK_ALERT_RETRY_S
    assert adm.maybe_alert_disk(tmp_path, check, _LIMITS, refused=False, now=later, publish=publish) == (
        "epics alert posted"
    )
    assert len(sent) == 1


def test_a_backward_clock_step_does_not_allow_a_second_alert_within_the_window(tmp_path):
    check = adm.DiskCheck(probe=_disk(81.0))
    sent: list[str] = []
    publish = lambda body, _key: sent.append(body)  # noqa: E731
    start = 1_800_000_000.0

    assert adm.maybe_alert_disk(tmp_path, check, _LIMITS, refused=False, now=start, publish=publish) == (
        "epics alert posted"
    )
    stepped_back = start - 1
    assert adm.maybe_alert_disk(tmp_path, check, _LIMITS, refused=False, now=stepped_back, publish=publish).startswith(
        "epics alert already posted at "
    )
    within = stepped_back + adm.DISK_ALERT_INTERVAL_S - 1
    assert adm.maybe_alert_disk(tmp_path, check, _LIMITS, refused=False, now=within, publish=publish).startswith(
        "epics alert already posted at "
    )
    after = stepped_back + adm.DISK_ALERT_INTERVAL_S
    assert adm.maybe_alert_disk(tmp_path, check, _LIMITS, refused=False, now=after, publish=publish) == (
        "epics alert posted"
    )
    assert len(sent) == 2


def test_a_dispatch_that_reuses_a_worktree_skips_the_disk_guard(tmp_path, host):
    host["readings"] = [_disk(99.0)]
    reaper = _Reaper()

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, reaper=reaper, disk_guard=False)

    assert decision.admitted and not decision.disk_refused
    assert reaper.calls == [] and host["probes"] == 0 and host["alerts"] == []
    assert "disk check skipped (dispatch reuses an existing worktree)" in decision.summary()
