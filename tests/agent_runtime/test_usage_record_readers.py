"""Every remaining usage reader shares the strict, fault-counting boundary (#10070)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agent_runtime import usage as bridge_usage
from scripts.agent_runtime import acpx_pilot, runner, usage
from scripts.ai_agent_bridge import _cli, _codex
from scripts.analytics import cost_report
from scripts.audit import qg_bakeoff
from scripts.maintenance import reclassify_dispatch_status as reclassify

MODEL = "gpt-6.1-sol"
READERS = ("codex-report", "pilot", "cost", "reclassify")
CORRUPT_LINES = (
    b'\xff\n',
    b'{"task_id":"bad-\xff"}\n',
    b'{not-json\n',
    b'[]\n',
    b'null\n',
    b'"not an object"\n',
    b'42\n',
    b'true\n',
)


@pytest.fixture
def isolated_usage(tmp_path, monkeypatch):
    monkeypatch.delenv("LU_BYPASS_RATE_LIMIT", raising=False)
    for module in (usage, bridge_usage):
        module._reset_rate_limit_cache_for_tests()
        monkeypatch.setattr(module, "_usage_dir", lambda: tmp_path)
    yield tmp_path
    for module in (usage, bridge_usage):
        module._reset_rate_limit_cache_for_tests()


def _record(*, recent=True, executed=True, outcome="ok", entrypoint="bridge"):
    now = datetime.now(UTC)
    return {
        "ts": (now if recent else now - timedelta(days=10)).isoformat(),
        "entrypoint": entrypoint,
        "task_id": "task-10070",
        "model": MODEL,
        "outcome": outcome,
        "event": acpx_pilot.PILOT_EVENT,
        "idempotency_digest": "target" if executed else "other",
        "executed": executed,
        "duration_s": 2.0,
    }


def _line(record):
    return json.dumps(record).encode("utf-8") + b'\n'


def _path(root, reader):
    prefix = (
        f"{acpx_pilot.PILOT_AGENT}-{acpx_pilot.PILOT_ENTRYPOINT}"
        if reader == "pilot" else "codex-bridge"
    )
    return root / f"usage_{prefix}_{datetime.now(UTC):%Y-%m-%d}.jsonl"


def _read(reader, root, counts=None):
    kwargs = {} if counts is None else {"unreadable": counts}
    if reader == "codex-report":
        return list(_cli._iter_codex_usage_records("5h", "all", **kwargs))
    if reader == "pilot":
        return acpx_pilot._has_executed_digest(root, "target", **kwargs)
    if reader == "cost":
        return cost_report.count_runtime_calls(days=7, usage_dir=root, **kwargs)
    return reclassify._load_usage_by_task_id(root, **kwargs)


def _assert_rows(reader, result, first, last=None):
    if reader == "codex-report":
        assert result == [first] + ([last] if last else [])
    elif reader == "pilot":
        assert result is bool(last)
    elif reader == "cost":
        assert result == (2 if last else 1)
    else:
        assert result == {"task-10070": last or first}


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("corrupt", CORRUPT_LINES)
def test_corrupt_line_does_not_drop_or_fabricate_valid_rows(reader, corrupt, isolated_usage, caplog):
    first = _record(executed=False)
    last = _record()
    _path(isolated_usage, reader).write_bytes(_line(first) + corrupt + _line(last))
    counts = {"files": 0, "lines": 0, "records": 0}

    result = _read(reader, isolated_usage, counts)

    _assert_rows(reader, result, first, last)
    assert counts == {"files": 0, "lines": 1, "records": 0}
    assert "unreadable usage records" in caplog.text
    assert str(counts) in caplog.text


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("complete", [False, True])
def test_last_line_without_newline(reader, complete, isolated_usage, caplog):
    first = _record(executed=False)
    last = _record()
    tail = _line(last).rstrip(b'\n') if complete else b'{"executed": tru'
    _path(isolated_usage, reader).write_bytes(_line(first) + tail)
    counts = {"files": 0, "lines": 0, "records": 0}

    result = _read(reader, isolated_usage, counts)

    _assert_rows(reader, result, first, last if complete else None)
    assert counts == {"files": 0, "lines": int(not complete), "records": 0}
    assert bool(caplog.records) is (not complete)


@pytest.mark.parametrize("reader", READERS)
def test_default_reader_reports_corruption(reader, isolated_usage, caplog):
    _path(isolated_usage, reader).write_bytes(b'\xff\n')

    result = _read(reader, isolated_usage)

    assert not result
    assert "unreadable usage records {'files': 0, 'lines': 1, 'records': 0}" in caplog.text


@pytest.mark.parametrize("reader", READERS)
def test_unreadable_file_does_not_drop_other_files(reader, isolated_usage, monkeypatch, caplog):
    good = _path(isolated_usage, reader)
    record = _record()
    good.write_bytes(_line(record))
    bad = good.with_name(good.name.replace("-bridge_", "-delegate_").replace("-acpx-pilot_", "-acpx-pilot_bad_"))
    bad.write_bytes(b'{}\n')
    real_open = open

    def denied(path, *args, **kwargs):
        if Path(path) == bad:
            raise PermissionError("unreadable fixture")
        return real_open(path, *args, **kwargs)

    # The pilot returns as soon as it finds the digest; make the bad file first.
    real_glob = Path.glob

    def ordered_glob(path, pattern):
        return iter(sorted(real_glob(path, pattern), key=lambda p: p != bad))

    monkeypatch.setattr(Path, "glob", ordered_glob)
    monkeypatch.setattr("builtins.open", denied)
    counts = {"files": 0, "lines": 0, "records": 0}

    result = _read(reader, isolated_usage, counts)

    if reader == "pilot":
        assert result is True
    else:
        _assert_rows(reader, result, record)
    assert counts == {"files": 1, "lines": 0, "records": 0}
    assert str(counts) in caplog.text


def test_codex_report_exposes_fault_counts_in_json_and_text(isolated_usage, capsys):
    record = _record()
    _path(isolated_usage, "codex-report").write_bytes(b'\xff\n' + _line(record).rstrip(b'\n'))

    report = _cli._build_codex_usage_report("5h", "bridge")
    _cli._print_codex_usage_report(report)

    assert report["total_calls"] == 1
    assert report["total_duration_s"] == 2.0
    assert report["unreadable"] == {"files": 0, "lines": 1, "records": 0, "total": 1}
    assert json.loads(json.dumps(report))["unreadable"] == report["unreadable"]
    assert "Unreadable usage records: " + str(report["unreadable"]) in capsys.readouterr().out


def test_codex_reader_preserves_window_and_entrypoint_filters(isolated_usage):
    good = _record()
    _path(isolated_usage, "codex-report").write_bytes(
        _line(_record(recent=False)) + _line(_record(entrypoint="delegate")) + _line(good)
    )

    assert list(_cli._iter_codex_usage_records("5h", "bridge")) == [good]


def test_cost_reader_preserves_calendar_window(isolated_usage):
    _path(isolated_usage, "cost").write_bytes(_line(_record()))
    for offset in (-10, 1):
        day = datetime.now(UTC) + timedelta(days=offset)
        (isolated_usage / f"usage_codex-bridge_{day:%Y-%m-%d}.jsonl").write_bytes(_line(_record()))

    assert cost_report.count_runtime_calls(days=7, usage_dir=isolated_usage) == 1
    assert cost_report.count_runtime_calls(days=None, usage_dir=isolated_usage) == 3


@pytest.mark.parametrize("caller", ["runner", "bridge", "bakeoff"])
@pytest.mark.parametrize("events", [1, 2])
def test_headroom_callers_surface_counts_and_keep_admission(caller, events, isolated_usage, monkeypatch, caplog):
    path = _path(isolated_usage, "codex-report")
    path.write_bytes(b'\xff\n' + b''.join(_line(_record(outcome="rate_limited")) for _ in range(events)))

    if caller == "runner":
        ok, reason = runner.has_headroom("codex", MODEL)
    elif caller == "bridge":
        ok, reason = _codex.has_codex_headroom(MODEL)
    else:
        route = next(r for r in qg_bakeoff.SUBSCRIPTION_BARE_ROUTES if r.route_name == "bare_runtime_gpt")
        monkeypatch.setattr(qg_bakeoff.shutil, "which", lambda _name: "fixture-cli")
        if events == 2:
            with pytest.raises(qg_bakeoff.BakeoffConfigError, match="no headroom"):
                qg_bakeoff.preflight_subscription_bare_routes([route])
        else:
            assert qg_bakeoff.preflight_subscription_bare_routes([route]) == {
                "status": "passed", "routes": [route.route_name],
            }
        ok, reason = (events == 1), "rate_limited" if events == 2 else ""

    assert ok is (events == 1)
    assert bool(reason) is (events == 2)
    assert "unreadable usage records {'files': 0, 'lines': 1, 'records': 0}" in caplog.text


@pytest.mark.parametrize("reader", READERS)
@pytest.mark.parametrize("dangling_link", [False, True])
def test_missing_file_matches_shared_reader_rule(reader, dangling_link, isolated_usage, monkeypatch):
    path = _path(isolated_usage, reader)
    if dangling_link:
        path.symlink_to(isolated_usage / "missing-target")
    monkeypatch.setattr(Path, "glob", lambda _self, _pattern: iter([path]))
    counts = {"files": 0, "lines": 0, "records": 0}

    assert not _read(reader, isolated_usage, counts)
    assert counts == {"files": int(dangling_link), "lines": 0, "records": 0}


@pytest.mark.parametrize("reader", READERS)
def test_valid_unicode_and_blank_lines_are_not_corrupt(reader, isolated_usage, caplog):
    record = _record()
    record["note"] = "replacement \ufffd and separators \u0085\u2028\u2029"
    payload = json.dumps(record, ensure_ascii=False).encode("utf-8")
    _path(isolated_usage, reader).write_bytes(b'\n \t\r\n' + payload)
    counts = {"files": 0, "lines": 0, "records": 0}

    result = _read(reader, isolated_usage, counts)

    if reader == "pilot":
        assert result is True
    else:
        _assert_rows(reader, result, record)
    assert counts == {"files": 0, "lines": 0, "records": 0}
    assert not caplog.records


def test_runner_preserves_optional_headroom_counter(isolated_usage):
    _path(isolated_usage, "codex-report").write_bytes(b'[]\n')
    counts = {"files": 0, "lines": 0, "records": 0}

    assert runner.has_headroom("codex", MODEL, unreadable=counts) == (True, "")
    assert counts == {"files": 0, "lines": 1, "records": 0}


@pytest.mark.parametrize("reader", READERS)
def test_missing_usage_directory_is_empty(reader, isolated_usage, monkeypatch):
    missing = isolated_usage / "missing"
    monkeypatch.setattr(_cli.runtime_usage, "_usage_dir", lambda: missing)
    counts = {"files": 0, "lines": 0, "records": 0}
    assert not _read(reader, missing, counts)
    assert counts == {"files": 0, "lines": 0, "records": 0}


def test_codex_reader_counts_stat_failure(isolated_usage, monkeypatch):
    path = _path(isolated_usage, "codex-report")
    path.write_bytes(_line(_record()))
    real_stat = Path.stat

    def denied(candidate, *args, **kwargs):
        if candidate == path:
            raise PermissionError("unreadable fixture")
        return real_stat(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", denied)
    counts = {"files": 0, "lines": 0, "records": 0}
    assert _read("codex-report", isolated_usage, counts) == []
    assert counts == {"files": 1, "lines": 0, "records": 0}


@pytest.mark.parametrize("agent", ["claude", "agy"])
@pytest.mark.parametrize("events", [1, 2])
def test_bakeoff_reports_counts_for_other_subscription_routes(agent, events, isolated_usage, monkeypatch, caplog):
    route = next(
        r for r in qg_bakeoff.SUBSCRIPTION_BARE_ROUTES
        if qg_bakeoff._subscription_identity(r).runtime_agent == agent
    )
    record = _record(outcome="rate_limited")
    record["model"] = route.reviewer_model_id
    path = isolated_usage / f"usage_{agent}-bridge_{datetime.now(UTC):%Y-%m-%d}.jsonl"
    path.write_bytes(b'[]\n' + _line(record) * events)
    cli = isolated_usage / "fixture-cli"
    cli.touch()
    (isolated_usage / ".claude").mkdir()
    monkeypatch.setattr(Path, "home", lambda: isolated_usage)
    monkeypatch.setattr(qg_bakeoff.shutil, "which", lambda _name: str(cli))

    if events == 2:
        with pytest.raises(qg_bakeoff.BakeoffConfigError, match="no headroom"):
            qg_bakeoff.preflight_subscription_bare_routes([route])
    else:
        assert qg_bakeoff.preflight_subscription_bare_routes([route])["status"] == "passed"
    assert "unreadable usage records {'files': 0, 'lines': 1, 'records': 0}" in caplog.text


def test_bakeoff_skips_headroom_without_subscription_routes():
    assert qg_bakeoff.preflight_subscription_bare_routes([]) == {"status": "skipped", "routes": []}
