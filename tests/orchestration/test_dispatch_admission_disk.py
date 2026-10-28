"""Dispatch admission disk guard (#10776).

Disk usage comes from a monkeypatched probe and the alert publisher is a
fake: no test reads the host disk or posts to Fleet Comms. Admission never
removes anything.
"""

from __future__ import annotations

import dataclasses
import json
import logging
from collections import namedtuple

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


def test_below_the_alert_threshold_is_admitted_without_alert(tmp_path, host):
    host["readings"] = [_disk(74.9)]

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS)

    assert decision.admitted
    assert host["alerts"] == []
    assert "disk 74.9% used, 100.4 GiB free (refuse at 90%, alert at 75%)" in decision.summary()
    record = decision.to_record()
    assert record["disk_used_percent"] == 74.9
    assert record["disk_free_gib"] == 100.4
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


def test_full_disk_refuses_with_percent_and_free_space(tmp_path, host):
    host["readings"] = [_disk(91.0)]

    decision = adm.evaluate("danger", tmp_path, thresholds=_LIMITS)

    assert not decision.admitted
    assert host["probes"] == 1
    assert decision.failures == (
        "disk 91.0% used, 36.0 GiB free on the .worktrees filesystem is at or above the refuse threshold of 90% "
        "(DISPATCH_DISK_REFUSE_USED_PERCENT=90)",
    )
    line = decision.refusal_line()
    assert "91.0% used" in line and "36.0 GiB free" in line
    assert len(host["alerts"]) == 1 and "REFUSED" in host["alerts"][0][0]
    record = decision.to_record()
    assert "disk_reaper" not in record and "disk_used_percent_before_reaper" not in record


def test_exactly_at_the_refuse_threshold_is_refused(tmp_path, host):
    host["readings"] = [_disk(90.0)]

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS)

    assert not decision.admitted


@pytest.mark.parametrize("mode", ["read-only", "research"])
def test_read_only_dispatch_is_exempt_from_the_disk_check(tmp_path, monkeypatch, mode):
    monkeypatch.setattr(adm, "probe_disk", lambda: pytest.fail("read-only must not read the disk"))

    decision = adm.evaluate(mode, tmp_path)

    assert decision.exempt and decision.admitted


def test_a_failing_disk_probe_admits_and_logs_the_reason(tmp_path, host, caplog):
    host["readings"] = [adm.DiskProbe(skipped="disk usage unreadable: OSError: [Errno 5] I/O error")]
    caplog.set_level(logging.WARNING, logger=adm.__name__)

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS)

    assert decision.admitted
    assert host["alerts"] == []
    assert "disk check skipped (disk usage unreadable: OSError: [Errno 5] I/O error)" in decision.summary()
    assert "disk check skipped: disk usage unreadable" in caplog.text
    assert decision.to_record()["disk_check_skipped"].startswith("disk usage unreadable")


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
    assert (defaults.disk_reap_used_percent, defaults.disk_refuse_used_percent) == (85.0, 90.0)
    assert defaults.disk_alert_used_percent == 75.0

    custom = adm.load_thresholds(
        {"DISPATCH_DISK_REFUSE_USED_PERCENT": "92.5", "DISPATCH_DISK_ALERT_USED_PERCENT": "78"}
    )
    assert (custom.disk_refuse_used_percent, custom.disk_alert_used_percent) == (92.5, 78.0)


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


# --- Round 3 (#10776): hard stop, redaction, alert state ----------


def test_a_disk_refusal_is_marked_as_a_hard_stop_and_does_not_offer_the_force_flag(tmp_path, host):
    host["readings"] = [_disk(90.0)]

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS)

    assert decision.disk_refused and decision.disk is not None and decision.disk.refused
    assert decision.to_record()["disk_refused"] is True
    assert "--force-admission cannot override a full disk" in decision.refusal_line()
    assert 'pass --force-admission "<reason>"' not in decision.refusal_line()


def test_other_refusals_are_not_disk_refusals(tmp_path, host):
    host["readings"] = [_disk(50.0)]
    capped = dataclasses.replace(_LIMITS, max_live_write_workers=0)

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=capped)

    assert not decision.admitted and not decision.disk_refused
    assert 'pass --force-admission "<reason>" to override' in decision.refusal_line()


@pytest.mark.parametrize(
    ("text", "redacted"),
    [
        ("lock /home/someone/repo/.cleanup.lock is held", "lock <path> is held"),
        ("held (~/learn-ukrainian/x.lock)", "held (<path>)"),
        ("see ~someone/x and /srv/data/a:12", "see <path> and <path>"),
        ("origin/main is 3/4 behind; refs/heads/x", "origin/main is 3/4 behind; refs/heads/x"),
        ("removed 0 worktree(s), freed 0 MB", "removed 0 worktree(s), freed 0 MB"),
        ("lock %2Fhome%2Fsomeone%2Frepo.lock is held", "lock <path> is held"),
        ("url file%3A%2F%2F%2Fvar%2Ftmp%2Fa failed", "url <path> failed"),
        ("double %252Fsrv%252Fdata%252Fx", "double <path>"),
        ("held (%7E%2Frepo%2Fx.lock)", "held (<path>)"),
        ("disk 50%25 used; origin%2Fmain; 100% full", "disk 50%25 used; origin%2Fmain; 100% full"),
    ],
)
def test_redact_paths(text, redacted):
    assert adm.redact_paths(text) == redacted


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

    decision = adm.evaluate("workspace-write", tmp_path, thresholds=_LIMITS, disk_guard=False)

    assert decision.admitted and not decision.disk_refused
    assert host["probes"] == 0 and host["alerts"] == []
    assert "disk check skipped (dispatch reuses an existing worktree)" in decision.summary()


# --- Two watermarks (#10871): the cto alert at 85, refuse only at 90 ---------------------------------------------


@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
@pytest.mark.parametrize(("used", "admitted"), [(84.0, True), (85.0, True), (89.0, True), (90.0, False)])
def test_write_dispatch_boundaries_refuse_only_at_90(tmp_path, host, mode, used, admitted):
    host["readings"] = [_disk(used)]

    decision = adm.evaluate(mode, tmp_path, thresholds=_LIMITS)

    assert decision.admitted is admitted
    assert host["probes"] == 1
    assert decision.disk_refused is (not admitted)


@pytest.mark.parametrize("mode", ["read-only", "research"])
@pytest.mark.parametrize("used", [84.0, 85.0, 89.0, 90.0, 99.0])
def test_read_only_dispatch_is_admitted_unchecked_at_every_level(tmp_path, host, monkeypatch, mode, used):
    host["readings"] = [_disk(used)]

    decision = adm.evaluate(mode, tmp_path, thresholds=_LIMITS)
    early = adm.precheck(mode, thresholds=_LIMITS)

    assert decision.admitted and decision.exempt and decision.disk is None
    assert early is None
    assert host["probes"] == 0 and host["alerts"] == []


@pytest.mark.parametrize(("used", "steps_aside"), [(89.0, False), (90.0, True)])
def test_precheck_steps_aside_for_the_disk_only_at_the_refuse_watermark(host, monkeypatch, used, steps_aside):
    monkeypatch.setattr(
        adm,
        "probe_host",
        lambda: adm.HostProbe(mem_available_bytes=1 * _GIB, load1=1.0, cpu_count=8, proc_available=True),
    )
    host["readings"] = [_disk(used)]

    early = adm.precheck("workspace-write", thresholds=_LIMITS)

    assert (early is None) is steps_aside


def test_default_watermarks_are_85_and_90():
    defaults = adm.config_defaults()
    assert (defaults.disk_reap_used_percent, defaults.disk_refuse_used_percent) == (85.0, 90.0)


@pytest.mark.parametrize(
    "env",
    [
        {"DISPATCH_DISK_REAP_USED_PERCENT": "90", "DISPATCH_DISK_REFUSE_USED_PERCENT": "90"},
        {"DISPATCH_DISK_REAP_USED_PERCENT": "92", "DISPATCH_DISK_REFUSE_USED_PERCENT": "88"},
        {"DISPATCH_DISK_REFUSE_USED_PERCENT": "85"},  # equal to the default reap watermark
        {"DISPATCH_DISK_REFUSE_USED_PERCENT": "70"},  # below the default reap watermark
        {"DISPATCH_DISK_REAP_USED_PERCENT": "90"},  # equal to the default refuse watermark
        {"DISPATCH_DISK_REAP_USED_PERCENT": "99"},
    ],
)
def test_reap_not_below_refuse_is_a_typed_configuration_error(env):
    with pytest.raises(adm.DiskWatermarkConfigError, match=r"DISPATCH_DISK_REAP_USED_PERCENT=.* must be below"):
        adm.load_thresholds(env)
    assert issubclass(adm.DiskWatermarkConfigError, ValueError)


def test_valid_watermark_overrides_are_read():
    custom = adm.load_thresholds({"DISPATCH_DISK_REAP_USED_PERCENT": "70", "DISPATCH_DISK_REFUSE_USED_PERCENT": "95"})
    assert (custom.disk_reap_used_percent, custom.disk_refuse_used_percent) == (70.0, 95.0)


@pytest.mark.parametrize("raw", ["101", "-1", "lots", "nan"])
def test_invalid_reap_watermark_keeps_the_existing_handling(raw):
    with pytest.raises(ValueError, match="DISPATCH_DISK_REAP_USED_PERCENT"):
        adm.load_thresholds({"DISPATCH_DISK_REAP_USED_PERCENT": raw})


def test_watermarks_come_from_the_deployment_env_file_too(tmp_path):
    env_file = tmp_path / "dispatch-admission.env"
    env_file.write_text("DISPATCH_DISK_REFUSE_USED_PERCENT=85\n")

    with pytest.raises(adm.DiskWatermarkConfigError):
        adm.load_thresholds({"DISPATCH_ADMISSION_ENV_FILE": str(env_file)})
