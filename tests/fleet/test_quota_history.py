"""Quota history collector and reader: five-slot projection, privacy allowlist, and observed-change reports (#11144)."""

from __future__ import annotations

import datetime as dt
import json
import os
import socketserver
import stat
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

from scripts.fleet import quota_history as qh

NOW = dt.datetime(2026, 10, 20, 8, 0, tzinfo=dt.UTC)
# Distinctive values: each must never appear in a persisted or printed record.
SENTINELS = ("sentinel-email@example.invalid", "acct-SENTINEL-7781", "tok-SENTINEL-9913", "4242.42")


def _payload() -> dict[str, Any]:
    """Five slots in the Monitor's observed shape, with nested identity, credit and secret fields."""
    secret = {"email": SENTINELS[0], "account_id": SENTINELS[1], "token": SENTINELS[2], "credit_balance": 4242.42}
    return {
        "generated_at": "2026-10-20T07:59:00Z",
        "agents": {
            "codex": {
                "codexbar": {
                    "weekly_used_pct": 40,
                    "weekly_resets_at": "2026-10-22T10:00:00Z",
                    "fetched_at": "2026-10-20T07:55:00Z",
                    "stale": False,
                    "freshness": "fresh",
                    "identity": secret,
                }
            },
            "grok": {
                "codexbar": {
                    "weekly_used_pct": 10.5,
                    "weekly_resets_at": None,
                    "fetched_at": "2026-10-20T07:58:00Z",
                    "stale": False,
                    "freshness": "live",
                }
            },
            "gemini": {
                "codexbar": {
                    "weekly_used_pct": 80,
                    "fetched_at": "2026-10-19T20:00:00Z",
                    "stale": True,
                    "freshness": "stale_last_good",
                }
            },
        },
        "claude_accounts": {
            "claude:a": {
                "weekly": {"left_pct": 70, "resets_at": "2026-10-23T09:00:00Z", "email": SENTINELS[0]},
                "updated": "2026-10-20T07:50:00Z",
                "stale": False,
                "status": "ok",
                "account_id": SENTINELS[1],
            },
            "claude:b": {
                "weekly": {"left_pct": 25, "resets_at": "not-a-date"},
                "updated": "2026-10-20T07:51:00Z",
                "stale": False,
                "status": "ok",
            },
        },
        "diagnostics": {"stale": False, "data_age_s": 300.0, "stale_threshold_s": 900},
    }


def _by_slot(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["slot"]: row for row in rows}


def _sample(slot: str, observed: str, used: float | None = None, resets: str | None = None, source: str | None = None):
    """A stored record as collect would write it; a sample without ``used`` is an explicit unknown."""
    if used is None:
        fields = qh._fields("unknown", "source_unavailable", source, None, resets)
    else:
        fields = qh._fields("known", None, source or observed, used, resets)
    return {"provider": qh.SLOT_PROVIDER[slot], "slot": slot, "window": "weekly", "observed_at": observed, **fields}


def _write(path: Path, records: list[dict[str, Any]]) -> Path:
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def _direct_localhost(monkeypatch: pytest.MonkeyPatch) -> None:
    """The local Monitor fixture must never route through an HTTP proxy from the environment."""
    for name in ("http_proxy", "HTTP_PROXY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")


def test_five_slots_map_to_observed_fields_and_nested_identity_is_dropped() -> None:
    rows = _by_slot(_collect_from_payload(_payload()))
    assert list(rows) == ["codex", "claude:a", "claude:b", "grok", "antigravity"]
    assert all(set(row) == qh.RECORD_FIELDS for row in rows.values())
    assert rows["codex"] == {
        "provider": "codex",
        "slot": "codex",
        "window": "weekly",
        "observed_at": "2026-10-20T08:00:00Z",
        "source_observed_at": "2026-10-20T07:55:00Z",
        "used_percent": 40.0,
        "resets_at": "2026-10-22T10:00:00Z",
        "status": "known",
        "reason": None,
    }
    assert rows["claude:a"]["used_percent"] == 30.0  # 100 - left_pct
    assert rows["claude:a"]["resets_at"] == "2026-10-23T09:00:00Z"
    assert rows["grok"]["status"] == "known" and rows["grok"]["resets_at"] is None
    assert (rows["antigravity"]["status"], rows["antigravity"]["reason"]) == ("stale", "source_stale")
    assert rows["antigravity"]["used_percent"] is None and rows["antigravity"]["resets_at"] is None


def _collect_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Run the projection on an in-memory payload by serving it from a local fixture."""
    with _MonitorFixture(payload) as base:
        return qh.collect(base, 5, now=NOW)


def test_invalid_values_and_unparseable_timestamps_stay_unknown_without_fabrication() -> None:
    payload = _payload()
    payload["agents"]["codex"]["codexbar"]["weekly_used_pct"] = True  # bool is not a number
    payload["agents"]["grok"]["codexbar"]["weekly_used_pct"] = float("nan")
    payload["claude_accounts"]["claude:a"]["weekly"]["left_pct"] = 140  # out of range
    payload["claude_accounts"]["claude:b"]["weekly"]["resets_at"] = "2026-10-23"  # naive, no zone
    rows = _by_slot(_collect_from_payload(payload))
    assert {rows[slot]["status"] for slot in ("codex", "grok", "claude:a")} == {"unknown"}
    assert {rows[slot]["reason"] for slot in ("codex", "grok", "claude:a")} == {"value_invalid"}
    assert rows["claude:b"]["status"] == "known" and rows["claude:b"]["resets_at"] is None
    assert rows["codex"]["used_percent"] is None and rows["codex"]["resets_at"] is None  # unknowns carry no values


def test_missing_rows_and_non_fresh_labels_are_explicit_unknowns() -> None:
    payload = _payload()
    del payload["agents"]["codex"]
    del payload["claude_accounts"]["claude:a"]
    payload["claude_accounts"]["claude:b"]["status"] = "error"
    payload["agents"]["grok"]["codexbar"]["freshness"] = "unavailable"
    rows = _by_slot(_collect_from_payload(payload))
    assert (rows["codex"]["status"], rows["codex"]["reason"]) == ("unknown", "row_missing")
    assert (rows["claude:a"]["status"], rows["claude:a"]["reason"]) == ("unknown", "row_missing")
    assert (rows["claude:b"]["status"], rows["claude:b"]["reason"]) == ("unknown", "not_fresh")
    assert (rows["grok"]["status"], rows["grok"]["reason"]) == ("unknown", "not_fresh")
    assert all(row["used_percent"] is None for row in rows.values() if row["status"] != "known")


def test_unreachable_monitor_yields_five_unknowns_and_a_non_object_payload_does_too() -> None:
    unreachable = qh.collect("http://127.0.0.1:9", 1, now=NOW)
    assert [row["reason"] for row in unreachable] == ["source_unavailable"] * 5
    assert all(row["status"] == "unknown" and row["used_percent"] is None for row in unreachable)
    with _MonitorFixture([1, 2, 3]) as base:
        assert {row["reason"] for row in qh.collect(base, 5, now=NOW)} == {"source_unavailable"}


def test_nested_sentinels_are_never_persisted_or_printed(tmp_path: Path, monkeypatch, capsys) -> None:
    store = tmp_path / "history.jsonl"
    with _MonitorFixture(_payload()) as base:
        monkeypatch.setenv("DELEGATE_MONITOR_API", base)
        assert qh.main(["collect", "--file", str(store)]) == 0
    text = store.read_text(encoding="utf-8") + capsys.readouterr().out
    assert not [needle for needle in SENTINELS if needle in text]
    assert all(set(json.loads(line)) == qh.RECORD_FIELDS for line in store.read_text().splitlines())


def test_held_out_sentinel_and_reset_boundary_fixture(tmp_path: Path, monkeypatch, capsys) -> None:
    """Separate driver-style fixture: a different identity sentinel and a reset exactly at a UTC midnight boundary."""
    held_out = "HELD-OUT-identity-5518"
    payload = _payload()
    payload["claude_accounts"]["claude:a"]["weekly"]["email"] = held_out
    payload["claude_accounts"]["claude:a"]["weekly"]["resets_at"] = "2026-10-26T00:00:00+00:00"
    payload["claude_accounts"]["claude:a"]["updated"] = dt.datetime.now(dt.UTC).isoformat()  # the CLI uses the clock
    store = tmp_path / "held.jsonl"
    with _MonitorFixture(payload) as base:
        monkeypatch.setenv("DELEGATE_MONITOR_API", base)
        qh.main(["collect", "--file", str(store)])
    assert held_out not in store.read_text() + capsys.readouterr().out
    record = _by_slot([json.loads(line) for line in store.read_text().splitlines()])["claude:a"]
    assert record["resets_at"] == "2026-10-26T00:00:00Z"  # Monday, exactly at midnight UTC


def test_append_is_append_only_private_and_one_write_per_collection(tmp_path: Path) -> None:
    store = tmp_path / "state" / "quota" / "samples.jsonl"
    rows = _collect_from_payload(_payload())
    qh.append(store, rows)
    qh.append(store, rows)
    lines = store.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 10 and lines[:5] == lines[5:]  # second collection appended after the first, unchanged
    assert stat.S_IMODE(store.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.parent.stat().st_mode) == 0o700


def test_append_failure_returns_one_with_fixed_message(tmp_path: Path, monkeypatch, capsys) -> None:
    locked = tmp_path / "read-only"
    locked.mkdir(mode=0o500)
    monkeypatch.setenv("DELEGATE_MONITOR_API", "http://127.0.0.1:9")
    try:
        assert qh.main(["collect", "--file", str(locked / "history" / "samples.jsonl")]) == 1
    finally:
        locked.chmod(0o700)
    assert capsys.readouterr().err == "quota-history: append failed; no rows written\n"
    assert not (locked / "history").exists()


def test_unsafe_history_path_is_refused_by_the_cli_with_a_fixed_message(tmp_path: Path, monkeypatch, capsys) -> None:
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x")
    monkeypatch.setenv("DELEGATE_MONITOR_API", "http://127.0.0.1:9")
    assert qh.main(["collect", "--file", str(blocker / "samples.jsonl")]) == 1
    assert capsys.readouterr().err == "quota-history: unsafe history path refused; no rows written\n"
    assert blocker.read_text() == "x"


def test_load_rejects_malformed_and_foreign_lines(tmp_path: Path) -> None:
    good = _sample("codex", "2026-10-20T08:00:00Z", 40.0, "2026-10-22T10:00:00Z", "2026-10-20T07:55:00Z")
    bad = [
        "{not json",
        json.dumps({**good, "email": "x@example.invalid"}),
        json.dumps({**good, "provider": "grok"}),
        json.dumps({**good, "used_percent": True}),
        json.dumps({**good, "used_percent": 150}),
        json.dumps({**good, "observed_at": "2026-10-20"}),
        json.dumps({**good, "reason": "made_up"}),
        json.dumps({**good, "slot": ["codex"]}),
        json.dumps({**good, "status": "unknown"}),
        json.dumps([good]),
    ]
    path = tmp_path / "h.jsonl"
    path.write_text("\n".join([json.dumps(good), *bad, ""]), encoding="utf-8")
    samples, malformed = qh.load(path)
    assert len(samples) == 1 and malformed == len(bad)
    assert qh.load(tmp_path / "missing.jsonl") == ([], 0)


def test_unicode_line_separators_and_invalid_utf8_never_split_or_admit_a_record(tmp_path: Path) -> None:
    good = _sample("codex", "2026-10-20T08:00:00Z", 40.0, None, "2026-10-20T07:55:00Z")
    raw_separator = json.dumps({**good, "note": "a b"}, ensure_ascii=False).encode("utf-8")
    path = tmp_path / "h.jsonl"
    path.write_bytes(json.dumps(good).encode() + b"\n" + raw_separator + b"\n" + b"\xff\xfe broken\n")
    samples, malformed = qh.load(path)
    assert len(samples) == 1 and malformed == 2  # the U+2028 line is one rejected record, not two fragments


def test_drop_and_reset_jump_are_reported_with_weekdays_and_no_schedule(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "h.jsonl",
        [
            _sample("codex", "2026-10-19T10:00:00Z", 60.0, "2026-10-19T12:00:00Z"),
            _sample("codex", "2026-10-20T10:00:00Z", 12.0, "2026-10-22T10:00:00Z"),
        ],
    )
    report = qh.analyze(*qh.load(path))
    kinds = [event["kind"] for event in report["events"]]
    assert kinds == ["used_drop", "reset_timestamp_jump"]
    drop, jump = report["events"]
    assert (drop["previous_used_percent"], drop["used_percent"], drop["observed_weekday"]) == (60.0, 12.0, "Tuesday")
    assert (jump["previous_resets_weekday"], jump["resets_weekday"]) == ("Monday", "Thursday")
    assert "no reset schedule is inferred" in qh._render(report)
    assert "exact time is unknown" in drop["uncertainty"]


def test_duplicates_out_of_order_lines_and_unchanged_windows_create_no_events(tmp_path: Path) -> None:
    record = _sample("codex", "2026-10-20T09:00:00Z", 40.0, "2026-10-22T10:00:00Z", "2026-10-20T08:55:00Z")
    repeat = {**record, "observed_at": "2026-10-20T10:00:00Z"}  # same source sample, observed again
    later_low = _sample("codex", "2026-10-20T11:00:00Z", 35.0, "2026-10-22T10:00:00Z", "2026-10-20T10:55:00Z")
    early_high = _sample("codex", "2026-10-20T08:30:00Z", 30.0, "2026-10-22T10:00:00Z", "2026-10-20T08:25:00Z")
    report = qh.analyze([record, repeat, later_low, early_high], malformed=0)
    assert report["duplicate_samples"] == 1
    assert report["out_of_order_samples"] == 1  # the 08:30 line arrives after 09:00 and 10:00
    assert report["events"] == [
        qh._event("used_drop", record, later_low),
    ]
    flat = [
        _sample("grok", "2026-10-20T08:00:00Z", 10.0, None, "2026-10-20T07:58:00Z"),
        _sample("grok", "2026-10-20T09:00:00Z", 10.0, None, "2026-10-20T08:58:00Z"),
    ]
    assert qh.analyze(flat, 0)["events"] == []


def test_non_string_freshness_label_is_not_fresh_and_does_not_crash() -> None:
    payload = _payload()
    payload["agents"]["grok"]["codexbar"]["freshness"] = ["fresh"]  # a foreign shape, not a label
    payload["agents"]["codex"]["codexbar"]["freshness"] = {"state": "fresh"}
    rows = _by_slot(_collect_from_payload(payload))
    assert (rows["grok"]["status"], rows["grok"]["reason"]) == ("unknown", "not_fresh")
    assert (rows["codex"]["status"], rows["codex"]["reason"]) == ("unknown", "not_fresh")


def test_unknown_and_stale_samples_are_never_compared_and_first_observation_is_not_a_reset() -> None:
    samples = [
        _sample("claude:a", "2026-10-20T08:00:00Z", 90.0, "2026-10-23T09:00:00Z"),
        _sample("claude:a", "2026-10-20T09:00:00Z"),  # explicit unknown between two known samples
        _sample("claude:a", "2026-10-20T10:00:00Z", 5.0, "2026-10-23T09:00:00Z"),
    ]
    report = qh.analyze(samples, 0)
    assert [event["kind"] for event in report["events"]] == ["used_drop"]
    assert report["events"][0]["previous_observed_at"] == "2026-10-20T08:00:00Z"
    assert qh.analyze([samples[0]], 0)["events"] == []  # a lone first observation is not a reset


def test_empty_or_all_unknown_history_cannot_certify_anything(tmp_path: Path, capsys) -> None:
    report = qh.analyze([], 0)
    assert report["known_samples"] == 0 and report["events"] == []
    assert "cannot evidence any reset" in qh._render(report)
    assert qh.main(["resets", "--file", str(tmp_path / "absent.jsonl")]) == 0
    assert "no known samples" in capsys.readouterr().out


def test_resets_cli_text_and_json_outputs(tmp_path: Path, capsys) -> None:
    path = _write(
        tmp_path / "h.jsonl",
        [
            _sample("antigravity", "2026-10-18T06:00:00Z", 55.0, None),
            _sample("antigravity", "2026-10-19T06:00:00Z", 3.0, None),
            "not json",
        ],
    )
    assert qh.main(["resets", "--file", str(path)]) == 0
    text = capsys.readouterr().out
    assert "malformed lines: 1" in text and "used_drop antigravity" in text
    assert "55.0% -> 3.0%" in text and "(observed Monday)" in text  # 2026-10-19 is a Monday
    assert qh.main(["resets", "--file", str(path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["malformed_lines"] == 1 and report["events"][0]["kind"] == "used_drop"


def test_default_path_honours_override_then_xdg_state(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LU_QUOTA_HISTORY_FILE", str(tmp_path / "override.jsonl"))
    assert qh.default_path() == tmp_path / "override.jsonl"
    monkeypatch.delenv("LU_QUOTA_HISTORY_FILE")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    assert qh.default_path() == tmp_path / "state" / "learn-ukrainian" / "quota-history" / "samples.jsonl"


def test_utc_normalises_offsets_and_rejects_naive_or_non_string() -> None:
    assert qh._utc("2026-10-20T10:00:00+02:00") == "2026-10-20T08:00:00Z"
    assert qh._utc("2026-10-20T08:00:00") is None
    assert qh._utc(1729411200) is None


def test_help_exits_zero_and_names_both_commands(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        qh.main(["--help"])
    out = capsys.readouterr().out
    assert exc.value.code == 0 and "collect" in out and "resets" in out


def _five(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return _by_slot(_collect_from_payload(payload))


def _status(row: dict[str, Any]) -> tuple[str, str | None]:
    return row["status"], row["reason"]


# --- Freshness evidence: a value is known only when its source observation proves it fresh (F2) ---


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (None, ("unknown", "source_time_invalid")),
        ("not-a-time", ("unknown", "source_time_invalid")),
        ("2026-10-20T07:59:00", ("unknown", "source_time_invalid")),  # naive: no zone
        (1729411200, ("unknown", "source_time_invalid")),
        ("2099-01-01T00:00:00Z", ("unknown", "source_time_invalid")),  # after the observation
        ("2026-10-20T08:00:00.000001Z", ("unknown", "source_time_invalid")),  # one microsecond after
        ("2001-01-01T00:00:00Z", ("stale", "source_stale")),
        ("2026-10-20T07:44:59Z", ("stale", "source_stale")),  # 901 s, past the published 900 s threshold
    ],
)
def test_source_time_must_prove_freshness_for_agent_and_account_rows(source: Any, expected: tuple) -> None:
    payload = _payload()
    payload["agents"]["codex"]["codexbar"]["fetched_at"] = source
    payload["claude_accounts"]["claude:a"]["updated"] = source
    rows = _five(payload)
    for slot in ("codex", "claude:a"):
        assert _status(rows[slot]) == expected
        assert rows[slot]["used_percent"] is None and rows[slot]["resets_at"] is None
    assert [rows[slot]["status"] for slot in ("claude:b", "grok", "antigravity")] == ["known", "known", "stale"]


def test_source_time_at_the_observation_or_exactly_at_the_threshold_is_known() -> None:
    payload = _payload()
    payload["agents"]["codex"]["codexbar"]["fetched_at"] = "2026-10-20T08:00:00Z"
    payload["claude_accounts"]["claude:a"]["updated"] = "2026-10-20T07:45:00+00:00"  # exactly 900 s
    rows = _five(payload)
    assert _status(rows["codex"]) == _status(rows["claude:a"]) == ("known", None)
    assert rows["codex"]["source_observed_at"] == "2026-10-20T08:00:00Z"


def test_expired_snapshot_marks_agent_rows_stale_but_keeps_live_account_rows() -> None:
    payload = _payload()
    payload["diagnostics"] = {"stale": True, "data_age_s": 86400, "stale_threshold_s": 300}
    for slot in ("claude:a", "claude:b"):
        payload["claude_accounts"][slot]["updated"] = "2026-10-20T07:58:00Z"
    payload["agents"]["codex"]["codexbar"]["fetched_at"] = "2026-10-20T07:59:30Z"  # a recent label cannot outvote it
    rows = _five(payload)
    assert {slot: row["status"] for slot, row in rows.items()} == {
        "codex": "stale",
        "claude:a": "known",
        "claude:b": "known",
        "grok": "stale",
        "antigravity": "stale",
    }
    assert _status(rows["codex"]) == ("stale", "source_stale") and rows["codex"]["used_percent"] is None
    assert rows["claude:a"]["used_percent"] == 30.0


@pytest.mark.parametrize("data_age", [None, 0, 899.9, 900])
def test_snapshot_within_its_threshold_or_without_an_age_keeps_fresh_agent_rows(data_age: Any) -> None:
    payload = _payload()
    payload["diagnostics"] = {"stale": True, "data_age_s": data_age, "stale_threshold_s": 900}
    rows = _five(payload)
    assert _status(rows["codex"]) == _status(rows["grok"]) == ("known", None)


@pytest.mark.parametrize("data_age", [True, "60", 10**400, float("inf"), [60]])
def test_an_unverifiable_snapshot_age_is_past_the_bound_for_agent_rows(data_age: Any) -> None:
    payload = _payload()
    payload["diagnostics"]["data_age_s"] = data_age
    rows = _five(payload)
    assert _status(rows["codex"]) == _status(rows["grok"]) == ("stale", "source_stale")
    assert _status(rows["claude:a"]) == _status(rows["claude:b"]) == ("known", None)


@pytest.mark.parametrize(
    "diagnostics",
    [
        None,
        [],
        {},
        {"stale_threshold_s": True},
        {"stale_threshold_s": "900"},
        {"stale_threshold_s": 10**400},
        {"stale_threshold_s": float("nan")},
        {"stale_threshold_s": 0},
        {"stale_threshold_s": -5},
    ],
)
def test_without_a_usable_published_threshold_the_monitors_own_bound_applies(diagnostics: Any) -> None:
    payload = _payload()
    if diagnostics is None:
        del payload["diagnostics"]
    else:
        payload["diagnostics"] = diagnostics
    payload["claude_accounts"]["claude:a"]["updated"] = "2026-10-20T07:44:59Z"  # 901 s: past the 900 s bound
    payload["claude_accounts"]["claude:b"]["updated"] = "2026-10-20T07:45:00Z"  # exactly 900 s
    rows = _five(payload)
    assert [_status(rows[slot]) for slot in ("codex", "claude:b", "grok")] == [("known", None)] * 3
    assert _status(rows["claude:a"]) == ("stale", "source_stale")
    assert _status(rows["antigravity"]) == ("stale", "source_stale")  # an explicit stale stays stale


def test_fallback_bound_is_the_monitors_routing_budget_max_age() -> None:
    from scripts.api import state_router

    assert qh.ROUTING_BUDGET_MAX_AGE_S == state_router.ROUTING_BUDGET_MAX_AGE_S


def test_a_missing_or_non_boolean_stale_flag_is_not_proof_of_freshness() -> None:
    payload = _payload()
    del payload["agents"]["codex"]["codexbar"]["stale"]
    payload["claude_accounts"]["claude:a"]["stale"] = "false"
    rows = _five(payload)
    assert _status(rows["codex"]) == _status(rows["claude:a"]) == ("unknown", "not_fresh")
    assert _status(rows["claude:b"]) == ("known", None)


def test_observation_time_follows_the_response_so_a_just_refreshed_sample_stays_known() -> None:
    def body() -> bytes:
        payload = _payload()
        payload["agents"]["codex"]["codexbar"]["fetched_at"] = dt.datetime.now(dt.UTC).isoformat()
        return json.dumps(payload).encode("utf-8")

    with _MonitorFixture(None, render=body) as base:
        rows = _by_slot(qh.collect(base, 5))
    assert _status(rows["codex"]) == ("known", None)
    assert rows["codex"]["source_observed_at"] <= rows["codex"]["observed_at"]


# --- Hostile scalars are invalid input, never a crash that loses the other slots (F3) ---


def test_number_pct_and_time_parsers_are_total_on_hostile_scalars() -> None:
    for hostile in (10**400, -(10**400), True, False, float("inf"), float("-inf"), float("nan"), "7", None, [1]):
        assert qh._number(hostile) is None and qh._pct(hostile) is None
    assert (qh._number(7), qh._number(-2.5)) == (7.0, -2.5)
    assert (qh._pct(0), qh._pct(100), qh._pct(100.0001)) == (0.0, 100.0, None)
    assert qh._utc("0001-01-01T00:00:00+01:00") is None  # UTC value before year 1
    assert qh._utc("9999-12-31T23:59:59-01:00") is None  # UTC value after year 9999
    assert qh._utc("0001-01-01T00:00:00+00:00") == "0001-01-01T00:00:00Z"
    assert qh._utc("9999-12-31T23:59:59+00:00") == "9999-12-31T23:59:59Z"
    assert qh._moment(["2026-10-20T08:00:00Z"]) is None
    assert qh._moment("2026-10-20T10:00:00+02:00") == dt.datetime(2026, 10, 20, 8, 0, tzinfo=dt.UTC)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("weekly_used_pct", 10**400, ("unknown", "value_invalid")),
        ("weekly_used_pct", -(10**400), ("unknown", "value_invalid")),
        ("fetched_at", "0001-01-01T00:00:00+01:00", ("unknown", "source_time_invalid")),
        ("fetched_at", "9999-12-31T23:59:59-01:00", ("unknown", "source_time_invalid")),
        ("weekly_resets_at", "9999-12-31T23:59:59-01:00", ("known", None)),
        ("weekly_resets_at", "0001-01-01T00:00:00+01:00", ("known", None)),
    ],
)
def test_one_hostile_scalar_never_aborts_the_other_four_slots(field: str, value: Any, expected: tuple) -> None:
    payload = _payload()
    payload["agents"]["codex"]["codexbar"][field] = value
    payload["claude_accounts"]["claude:b"]["weekly"]["left_pct"] = 10**400
    rows = _five(payload)
    assert _status(rows["codex"]) == expected
    assert rows["codex"]["resets_at"] is None  # an unrepresentable reset is dropped, never guessed
    assert _status(rows["claude:b"]) == ("unknown", "value_invalid")
    assert [rows[slot]["status"] for slot in ("claude:a", "grok", "antigravity")] == ["known", "known", "stale"]


@pytest.mark.parametrize(
    "raw",
    [
        b"[" * 100_000 + b"]" * 100_000,  # nesting deeper than the parser's recursion limit
        b'{"agents": {"codex": {"codexbar": {"weekly_used_pct": ' + b"9" * 5000 + b"}}}}",  # over the digit limit
        b'{"agents": ',  # truncated
    ],
)
def test_an_unparseable_monitor_document_is_five_explicit_unknowns(raw: bytes) -> None:
    with _MonitorFixture(None, raw=raw) as base:
        rows = qh.collect(base, 5, now=NOW)
    assert [_status(row) for row in rows] == [("unknown", "source_unavailable")] * 5


def test_a_malformed_http_response_is_five_explicit_unknowns() -> None:
    class Garbage(socketserver.StreamRequestHandler):
        def handle(self) -> None:
            self.rfile.readline()
            self.wfile.write(b"NOT-HTTP garbage\r\n\r\n")

    with socketserver.TCPServer(("127.0.0.1", 0), Garbage) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            rows = qh.collect(f"http://127.0.0.1:{server.server_address[1]}", 5, now=NOW)
        finally:
            server.shutdown()
            thread.join()
    assert [_status(row) for row in rows] == [("unknown", "source_unavailable")] * 5


def test_reader_counts_hostile_and_unproven_records_as_malformed_and_keeps_valid_history(
    tmp_path: Path, capsys
) -> None:
    first = _sample("codex", "2026-10-20T08:00:00Z", 40.0, None, "2026-10-20T07:55:00Z")
    second = _sample("codex", "2026-10-20T09:00:00Z", 10.0, None, "2026-10-20T08:55:00Z")
    hostile = [
        json.dumps({**first, "used_percent": 10**400}),
        json.dumps({**first, "used_percent": -(10**400)}),
        json.dumps({**first, "observed_at": "9999-12-31T23:59:59-01:00"}),
        json.dumps({**first, "source_observed_at": "0001-01-01T00:00:00+01:00"}),
        json.dumps({**first, "resets_at": "9999-12-31T23:59:59-01:00"}),
        json.dumps({**first, "source_observed_at": None}),  # known without source evidence
        json.dumps({**first, "source_observed_at": "2026-10-20T08:00:01Z"}),  # source after the observation
        "[" * 100_000,
        '{"used_percent": ' + "9" * 5000 + "}",
    ]
    path = tmp_path / "h.jsonl"
    path.write_text("\n".join([json.dumps(first), *hostile, json.dumps(second), ""]), encoding="utf-8")
    samples, malformed = qh.load(path)
    assert [sample["used_percent"] for sample in samples] == [40.0, 10.0] and malformed == len(hostile)
    assert qh.main(["resets", "--file", str(path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["malformed_lines"] == len(hostile) and [event["kind"] for event in report["events"]] == ["used_drop"]


# --- The history path: private, regular, reached without a symlink, never modified when refused (F1) ---

ROWS = [_sample(slot, "2026-10-20T08:00:00Z") for slot in qh.SLOT_PROVIDER]


def _private_dir(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path


def _state(path: Path) -> tuple[bytes, int, int]:
    info = path.stat()
    return path.read_bytes(), stat.S_IMODE(info.st_mode), info.st_mtime_ns


@pytest.mark.parametrize(
    ("dir_mode", "file_mode"), [(0o755, 0o644), (0o700, 0o644), (0o755, 0o600), (0o700, 0o640), (0o710, 0o600)]
)
def test_existing_history_with_any_group_or_other_bit_is_refused_unmodified(
    tmp_path: Path, dir_mode: int, file_mode: int
) -> None:
    directory = _private_dir(tmp_path / "history")
    target = directory / "samples.jsonl"
    target.write_bytes(b"PRIOR\n")
    target.chmod(file_mode)
    directory.chmod(dir_mode)
    before = (_state(target), stat.S_IMODE(directory.stat().st_mode))
    with pytest.raises(qh.UnsafeHistoryPathError):
        qh.append(target, ROWS)
    assert (_state(target), stat.S_IMODE(directory.stat().st_mode)) == before == (before[0], dir_mode)


def test_existing_private_history_is_appended_without_changing_its_modes(tmp_path: Path) -> None:
    target = _private_dir(tmp_path / "history") / "samples.jsonl"
    target.write_bytes(b"PRIOR\n")
    target.chmod(0o600)
    qh.append(target, ROWS)
    lines = target.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "PRIOR" and [json.loads(line) for line in lines[1:]] == ROWS
    assert stat.S_IMODE(target.stat().st_mode) == 0o600 and stat.S_IMODE(target.parent.stat().st_mode) == 0o700


def test_symlinked_history_file_is_refused_and_its_target_is_untouched(tmp_path: Path) -> None:
    victim = _private_dir(tmp_path / "elsewhere") / "victim.jsonl"
    victim.write_bytes(b"PRIOR\n")
    victim.chmod(0o600)
    link = _private_dir(tmp_path / "history") / "samples.jsonl"
    link.symlink_to(victim)
    before = _state(victim)
    with pytest.raises(qh.UnsafeHistoryPathError):
        qh.append(link, ROWS)
    assert _state(victim) == before and link.is_symlink()


def test_dangling_history_symlink_is_refused_and_creates_nothing(tmp_path: Path) -> None:
    absent = _private_dir(tmp_path / "elsewhere") / "absent.jsonl"
    link = _private_dir(tmp_path / "history") / "samples.jsonl"
    link.symlink_to(absent)
    with pytest.raises(qh.UnsafeHistoryPathError):
        qh.append(link, ROWS)
    assert not absent.exists()


@pytest.mark.parametrize("below", [("samples.jsonl",), ("deeper", "samples.jsonl"), ("a", "b", "samples.jsonl")])
def test_symlinked_history_directory_or_ancestor_is_refused_without_creating_anything(
    tmp_path: Path, below: tuple[str, ...]
) -> None:
    real = _private_dir(tmp_path / "real")
    (tmp_path / "link").symlink_to(real, target_is_directory=True)
    with pytest.raises(qh.UnsafeHistoryPathError):
        qh.append(Path(tmp_path / "link", *below), ROWS)
    assert list(real.iterdir()) == []


def test_non_regular_history_entries_are_refused_without_blocking(tmp_path: Path) -> None:
    directory = _private_dir(tmp_path / "history")
    os.mkfifo(directory / "pipe.jsonl", 0o600)  # no reader: a plain open for writing would wait forever
    (directory / "dir.jsonl").mkdir(mode=0o700)
    for name in ("pipe.jsonl", "dir.jsonl"):
        with pytest.raises(qh.UnsafeHistoryPathError):
            qh.append(directory / name, ROWS)


def test_a_directory_that_vanishes_during_the_walk_is_refused(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(qh, "open_unit_dir", lambda *args, **kwargs: None)
    with pytest.raises(qh.UnsafeHistoryPathError):
        qh.append(tmp_path / "history" / "samples.jsonl", ROWS)
    assert not (tmp_path / "history").exists()


def test_concurrent_appending_processes_each_land_whole_records(tmp_path: Path) -> None:
    store = tmp_path / "history" / "samples.jsonl"
    script = (
        "import json, sys\nfrom pathlib import Path\nfrom scripts.fleet import quota_history as qh\n"
        "rows = json.loads(sys.argv[2])\nfor _ in range(20):\n    qh.append(Path(sys.argv[1]), rows)\n"
    )
    repo = Path(__file__).resolve().parents[2]
    workers = [
        subprocess.Popen([sys.executable, "-c", script, str(store), json.dumps(ROWS)], cwd=repo) for _ in range(6)
    ]
    assert [worker.wait(timeout=60) for worker in workers] == [0] * 6
    samples, malformed = qh.load(store)
    assert len(samples) == 6 * 20 * 5 and malformed == 0
    assert stat.S_IMODE(store.stat().st_mode) == 0o600 and stat.S_IMODE(store.parent.stat().st_mode) == 0o700


class _Handler(BaseHTTPRequestHandler):
    body: bytes = b""
    render: Any = None

    def do_GET(self) -> None:
        body = self.render() if self.render is not None else self.body
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        return


class _MonitorFixture:
    """A local, single-purpose Monitor fixture on 127.0.0.1; never a provider or the real Monitor.

    It serves ``payload`` as JSON, or ``raw`` bytes verbatim, or a body ``render`` builds per request.
    """

    def __init__(self, payload: Any, *, raw: bytes | None = None, render: Any = None) -> None:
        body = raw if raw is not None else json.dumps(payload).encode("utf-8")
        attributes = {"body": body, "render": None if render is None else staticmethod(render)}
        handler = type("Handler", (_Handler,), attributes)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> str:
        self.thread.start()
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()
