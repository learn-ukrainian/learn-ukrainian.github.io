"""Quota history collector and reader: five-slot projection, privacy allowlist, and observed-change reports (#11144)."""

from __future__ import annotations

import datetime as dt
import json
import stat
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
                "codexbar": {"weekly_used_pct": 10.5, "weekly_resets_at": None, "fetched_at": None, "freshness": "live"}
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
    payload["claude_accounts"]["claude:b"]["status"] = "error"
    payload["agents"]["grok"]["codexbar"]["freshness"] = "unavailable"
    rows = _by_slot(_collect_from_payload(payload))
    assert (rows["codex"]["status"], rows["codex"]["reason"]) == ("unknown", "row_missing")
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
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x")
    monkeypatch.setenv("DELEGATE_MONITOR_API", "http://127.0.0.1:9")
    assert qh.main(["collect", "--file", str(blocker / "samples.jsonl")]) == 1
    assert capsys.readouterr().err == "quota-history: append failed; no rows written\n"


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


class _Handler(BaseHTTPRequestHandler):
    body: bytes = b""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, *args: object) -> None:
        return


class _MonitorFixture:
    """A local, single-purpose Monitor fixture on 127.0.0.1; never a provider or the real Monitor."""

    def __init__(self, payload: Any) -> None:
        handler = type("Handler", (_Handler,), {"body": json.dumps(payload).encode("utf-8")})
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> str:
        self.thread.start()
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()
