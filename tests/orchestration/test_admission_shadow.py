"""Injected kernel samples and real local journals; never generate host pressure."""

from __future__ import annotations

import fcntl
import json
from datetime import UTC, datetime, timedelta

import pytest

from scripts.orchestration import admission_shadow as shadow
from scripts.orchestration import dispatch_admission as adm
from scripts.orchestration.pool_headroom import PoolCheck, SliceMemory

NOW = datetime(2026, 10, 20, tzinfo=UTC)
LIMITS = adm.Thresholds(2, 3.5, 1.5)


def pressure(a=0, b=0):
    return {
        key: {"avg10": a, "avg60": b, "avg300": 0, "unknown": None}
        for key in ("cpu.some", "memory.some", "memory.full", "io.some", "io.full")
    }


def context():
    return {"phase": "evaluate", "load_decision": "refuse", "current_admission_decision": "refuse"}


def previous(decision="refuse", stamp=0, low_since=None):
    return {"timestamp": stamp, "psi": {"decision": decision, "low_since": low_since}}


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (40, 30, "admit"),
        (40.001, 0, "refuse"),
        (0, 30.001, "refuse"),
        (25, 0, "refuse"),
        (0, 20, "refuse"),
        (24.99, 19.99, "admit"),
    ],
)
def test_stop_and_resume_boundaries(a, b, expected):
    old = previous("admit" if a >= 40 or b > 30 else "refuse", stamp=30, low_since=0)
    assert shadow.transition(pressure(a, b), old, 60)["decision"] == expected


def test_hysteresis_requires_observed_recovery_and_retains_band():
    first = shadow.transition(pressure(41, 0), {}, 0)
    assert first["decision"] == "refuse"
    band = shadow.transition(pressure(30, 25), {"timestamp": 0, "psi": first}, 1)
    assert band == {"decision": "refuse", "low_since": None, "reason": "hysteresis_band"}
    low = shadow.transition(pressure(), {"timestamp": 1, "psi": band}, 2)
    assert low["decision"] == "refuse"
    almost = shadow.transition(pressure(), {"timestamp": 2, "psi": low}, 61)
    assert almost["decision"] == "refuse"
    resumed = shadow.transition(pressure(), {"timestamp": 61, "psi": almost}, 62)
    assert resumed["decision"] == "admit"
    assert shadow.transition(pressure(30, 25), {"timestamp": 62, "psi": resumed}, 63)["decision"] == "admit"
    assert shadow.transition(pressure(), {"timestamp": 62, "psi": resumed}, 123)["decision"] == "unknown"
    assert shadow.transition(pressure(), {"timestamp": 62, "psi": resumed}, 61)["decision"] == "unknown"


def test_unknown_breaks_recovery(tmp_path):
    missing = shadow.read_pressure(tmp_path)
    assert set(missing) == {"cpu.some", "memory.some", "memory.full", "io.some", "io.full"}
    assert all(v["unknown"] == "unavailable_or_malformed" for v in missing.values())
    assert shadow.transition(missing, previous("admit"), 1) == {
        "decision": "unknown",
        "low_since": None,
        "reason": "cpu_psi_unknown",
    }


@pytest.mark.parametrize(
    "raw",
    [
        "garbled",
        "some avg10=nan avg60=0 avg300=0 total=0",
        "some avg10=0 avg60=inf avg300=0 total=0",
        "some avg10=-1 avg60=0 avg300=0 total=0",
        "some avg10=101 avg60=0 avg300=0 total=0",
        "some avg10=0 avg60=0 total=0",
        "some avg10=0 avg60=0 avg300=0 total=-1",
        "some avg10=0 avg60=0 avg300=0 total=x",
        "some avg10=0 avg60=0 avg300=0 total=0\nsome avg10=0 avg60=0 avg300=0 total=0",
        "x" * 4097,
        "\N{SNOWMAN}",
    ],
)
def test_malformed_psi_is_unknown(tmp_path, raw):
    root = tmp_path / "pressure"
    root.mkdir()
    (root / "cpu").write_text(raw)
    assert shadow.read_pressure(tmp_path)["cpu.some"]["avg10"] is None


def test_kernel_file_format_reads_both_windows_and_ignores_cpu_full(tmp_path):
    root = tmp_path / "pressure"
    root.mkdir()
    for resource in ("cpu", "memory", "io"):
        (root / resource).write_text(
            "some avg10=12.50 avg60=7.25 avg300=1.0 total=123\nfull avg10=4.0 avg60=2.0 avg300=0.0 total=5\n"
        )
    result = shadow.read_pressure(tmp_path)
    assert result["cpu.some"] == {"avg10": 12.5, "avg60": 7.25, "avg300": 1.0, "unknown": None}
    assert "cpu.full" not in result
    assert result["memory.full"]["avg60"] == 2
    assert result["io.full"]["avg60"] == 2


def test_journal_recovers_across_calls_and_midnight(tmp_path):
    before = NOW - timedelta(seconds=30)
    assert shadow.observe(tmp_path, pressure(41), context(), now=before)["psi"]["decision"] == "refuse"
    assert shadow.observe(tmp_path, pressure(), context(), now=NOW)["psi"]["decision"] == "refuse"
    assert (
        shadow.observe(tmp_path, pressure(), context(), now=NOW + timedelta(seconds=59))["psi"]["decision"] == "refuse"
    )
    resumed = shadow.observe(tmp_path, pressure(), context(), now=NOW + timedelta(seconds=60))
    assert resumed["psi"]["decision"] == "admit"
    assert resumed["persistence"] == "recorded"
    rows = [json.loads(line) for line in (tmp_path / "2026-10-20.jsonl").read_text().splitlines()]
    assert len(rows) == 3
    assert rows[-1]["candidate"] == shadow.CANDIDATE


def test_busy_full_and_unavailable_journals_do_not_authorize(tmp_path, monkeypatch):
    with (tmp_path / "observer.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        busy = shadow.observe(tmp_path, pressure(41), context(), now=NOW)
    assert busy["persistence"] == "unknown: journal_unavailable_or_busy"
    monkeypatch.setattr(shadow, "MAX_DAY_BYTES", 1)
    assert shadow.observe(tmp_path, pressure(), context(), now=NOW)["persistence"] == "unknown: journal_limit"
    blocked = tmp_path / "file"
    blocked.write_text("not a directory")
    assert (
        shadow.observe(blocked, pressure(), context(), now=NOW)["persistence"] == "unknown: journal_unavailable_or_busy"
    )


@pytest.mark.parametrize("tail", ['{"schema":"admission-shadow.v1","psi":"bad"}\n', "broken\n", "[]\n"])
def test_corrupt_history_resets_to_unknown(tmp_path, tail):
    (tmp_path / "2026-10-20.jsonl").write_text(tail)
    assert shadow.observe(tmp_path, pressure(), context(), now=NOW)["psi"]["decision"] == "unknown"


def test_invalid_typed_history_cannot_break_admission(tmp_path):
    row = {"schema": shadow.SCHEMA, "candidate": shadow.CANDIDATE, "psi": {"decision": []}}
    (tmp_path / "2026-10-20.jsonl").write_text(json.dumps(row) + "\n")
    assert shadow.observe(tmp_path, pressure(), context(), now=NOW)["psi"]["decision"] == "unknown"


def test_one_day_comparison_keeps_unknowns_and_denominator(tmp_path):
    for minute in range(1440):
        sample = pressure(41) if minute % 2 == 0 else pressure()
        if minute == 1439:
            sample["cpu.some"] = {"avg10": None, "avg60": None, "avg300": None, "unknown": "missing"}
        shadow.observe(tmp_path, sample, context(), now=NOW + timedelta(minutes=minute))
    # A distinct next-day record must not affect the requested day.
    shadow.observe(tmp_path, pressure(99), context(), now=NOW + timedelta(days=1))
    report = shadow.compare_day(tmp_path, "2026-10-20")
    assert report["samples"] == 1440
    assert report["comparisons"] == {"load_refuse__psi_refuse": 1439, "load_refuse__psi_unknown": 1}
    assert report["unknown_signals"] == {"cpu.some": 1}
    assert report["observed_span_seconds"] == 86340
    assert report["current_admission_decisions"] == {"refuse": 1440}
    assert report["enforcement_changed"] is False
    assert report["denominator"] == "sampled evaluations, not unique dispatches"
    assert report["peak_avg60_percent"]["cpu.some"] == 0


def test_report_cli_errors_and_json(tmp_path, capsys):
    assert shadow.main(["--directory", str(tmp_path), "--day", "2026-10-20"]) == 1
    assert json.loads(capsys.readouterr().out) == {"error": "comparison_unavailable"}
    shadow.observe(tmp_path, pressure(41), context(), now=NOW)
    assert shadow.main(["--directory", str(tmp_path), "--day", "2026-10-20"]) == 0
    assert json.loads(capsys.readouterr().out)["samples"] == 1
    assert shadow.main(["--directory", str(tmp_path), "--day", "../bad"]) == 1


def test_invalid_report_rows_cannot_inflate_measurement(tmp_path, monkeypatch):
    row = shadow.observe(tmp_path, pressure(41), context(), now=NOW)
    path = tmp_path / "2026-10-20.jsonl"
    malformed = [
        "{broken}",
        "[]",
        json.dumps({**row, "pressure": []}),
        json.dumps({**row, "current_admission_decision": "wrong"}),
        json.dumps({**row, "phase": "wrong"}),
        json.dumps({**row, "timestamp": NOW.timestamp() - 1}),
    ]
    with path.open("a") as handle:
        handle.write("\n".join(malformed) + "\n")
    report = shadow.compare_day(tmp_path, "2026-10-20")
    assert report["samples"] == 1
    assert report["invalid_rows"] == 6
    assert report["comparisons"] == {"load_refuse__psi_refuse": 1}
    monkeypatch.setattr(shadow, "MAX_DAY_BYTES", 1)
    with pytest.raises(ValueError, match="daily bound"):
        shadow.compare_day(tmp_path, "2026-10-20")


@pytest.fixture
def host(tmp_path, monkeypatch):
    journal = tmp_path / "shadow"
    monkeypatch.setenv(shadow.DIRECTORY_ENV, str(journal))
    monkeypatch.setattr(shadow, "read_pressure", lambda _: pressure(99, 99))
    probe = adm.HostProbe(12 * 1024**3, 0, 8, True)
    monkeypatch.setattr(adm, "probe_host", lambda: probe)
    monkeypatch.setattr(adm, "probe_disk", lambda: adm.DiskProbe(used_bytes=10, free_bytes=90))
    monkeypatch.setattr(adm, "probe_pool", lambda _: PoolCheck(0, SliceMemory(100, 0, 1000, 2000)))
    monkeypatch.setattr(adm, "probe_test_slots", lambda: adm.SlotQueueProbe(0, 4))
    return journal, probe


def test_cheap_path_samples_without_scans_or_admission_changes(host, monkeypatch):
    journal, probe = host

    def forbidden(*args, **kwargs):
        pytest.fail("shadow added an expensive attribution scan")

    for name in ("scan_task_records", "probe_pool", "probe_test_slots"):
        monkeypatch.setattr(adm, name, forbidden)
    monkeypatch.setattr(adm.subprocess, "run", forbidden)
    monkeypatch.setattr(adm.subprocess, "Popen", forbidden)
    assert adm.precheck("danger", thresholds=LIMITS) is None  # PSI must not refuse.
    monkeypatch.setattr(adm, "probe_host", lambda: adm.replace(probe, load1=100))
    refused = adm.precheck("danger", thresholds=LIMITS)
    assert refused.admitted is False
    assert refused.psi_shadow["attribution"]["live_task_ids"] is None
    assert refused.psi_shadow["psi"]["decision"] == "refuse"
    rows = list(journal.glob("*.jsonl"))
    assert len(rows) == 1
    assert len(rows[0].read_text().splitlines()) == 2
    assert adm.precheck("read-only", thresholds=LIMITS) is None
    assert len(rows[0].read_text().splitlines()) == 2


def test_evaluation_reuses_bounded_attribution_and_exposes_diagnostics(host, tmp_path, monkeypatch):
    journal, _ = host
    live = (*(f"task-{n}" for n in range(20)), "/private/location")
    monkeypatch.setattr(adm, "scan_task_records", lambda *_a, **_kw: adm.WorkerScan(live, ()))
    monkeypatch.setattr(
        adm,
        "probe_test_slots",
        lambda: adm.SlotQueueProbe(
            12,
            4,
            holders=({"task_id": "writer", "slots": 2, "private": "do not copy"},),
            queued=({"task_id": "../private"},) * 20,
        ),
    )
    decision = adm.evaluate("danger", tmp_path / "tasks", thresholds=LIMITS)
    assert decision.admitted is False
    assert len(decision.failures) == 2
    observation = decision.to_record()["psi_shadow"]
    attributed = observation["attribution"]
    assert attributed["live_task_count"] == 21
    assert attributed["live_task_ids"] == list(live[:10])
    assert attributed["test_slot_holders"] == [{"task_id": "writer", "slots": 2}]
    assert attributed["test_slot_waiters"] == [{"task_id": "unknown"}] * 10
    assert attributed["pool_nonreclaimable_bytes"] == 100
    assert attributed["pool_limit_bytes"] == 1000
    assert attributed["unattributed_load"].startswith("unknown:")
    assert "PSI shadow refuse (calibration only; recorded" in decision.summary()
    assert observation["current_admission_decision"] == "refuse"
    raw = next(journal.glob("*.jsonl")).read_text()
    assert "private" not in raw


def test_slot_attribution_reuses_the_single_existing_status_probe(tmp_path, monkeypatch):
    monkeypatch.setenv(adm.test_slots.DIR_ENV, str(tmp_path / "slots"))
    holders = [{"task_id": f"holder-{n}", "slots": 1} for n in range(20)]
    queue = [{"task_id": f"waiter-{n}"} for n in range(20)]
    calls = []

    def status():
        calls.append(True)
        return {"enabled": True, "error": None, "pool_size": 4, "queue_depth": 20, "holders": holders, "queue": queue}

    monkeypatch.setattr(adm.test_slots, "status", status)
    sample = adm.probe_test_slots()
    assert calls == [True]
    assert sample.holders == tuple(holders[:10])
    assert sample.queued == tuple(queue[:10])
    assert sample.depth == 20


@pytest.mark.parametrize("gate", ["none", "load", "memory", "pool", "slots", "disk"])
def test_psi_never_changes_existing_protections(host, tmp_path, monkeypatch, gate):
    _, probe = host
    if gate == "load":
        monkeypatch.setattr(adm, "probe_host", lambda: adm.replace(probe, load1=100))
    elif gate == "memory":
        monkeypatch.setattr(adm, "probe_host", lambda: adm.replace(probe, mem_available_bytes=1))
    elif gate == "pool":
        monkeypatch.setattr(adm, "probe_pool", lambda _: PoolCheck(500, SliceMemory(900, 0, 1000, 2000)))
    elif gate == "slots":
        monkeypatch.setattr(adm, "probe_test_slots", lambda: adm.SlotQueueProbe(20, 4))
    elif gate == "disk":
        monkeypatch.setattr(
            adm,
            "check_disk",
            lambda *_a, **_k: (
                adm.DiskCheck(probe=adm.DiskProbe(used_bytes=99, free_bytes=1), refused=True),
                "disk refuses",
            ),
        )
        monkeypatch.setattr(adm, "maybe_alert_disk", lambda *_a, **_k: None)
    missing = {key: {"avg10": None, "avg60": None, "avg300": None, "unknown": "missing"} for key in pressure()}
    for psi in (pressure(99, 99), pressure(), missing):
        monkeypatch.setattr(shadow, "read_pressure", lambda _, p=psi: p)
        decision = adm.evaluate("danger", tmp_path / "tasks", thresholds=LIMITS)
        assert decision.admitted is (gate == "none")
        assert decision.disk_refused is (gate == "disk")


@pytest.mark.parametrize("value", ["/private/location", "a\nb", "x" * 97, 4])
def test_task_labels_cannot_emit_paths_or_unbounded_text(value):
    assert shadow.label(value) == "unknown"
