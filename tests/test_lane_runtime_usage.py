"""Hybrid usage: agent JSONL lane summaries for routing-budget enrichment."""

from __future__ import annotations

import ast
import json
import os
import sys
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime import usage as usage_mod


def _write_line(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def test_summarize_lane_runtime_counts_and_blocks(tmp_path: Path, monkeypatch) -> None:
    usage_mod._reset_rate_limit_cache_for_tests()
    monkeypatch.setattr(usage_mod, "_usage_dir", lambda: tmp_path)
    now = time.time()
    ts_recent = datetime.fromtimestamp(now - 10, tz=UTC).isoformat()
    ts_ok = datetime.fromtimestamp(now - 30, tz=UTC).isoformat()
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    path = tmp_path / f"usage_codex-bridge_{day}.jsonl"
    _write_line(
        path,
        {
            "ts": ts_ok,
            "agent": "codex",
            "entrypoint": "bridge",
            "model": "gpt-5.5",
            "outcome": "ok",
        },
    )
    for _ in range(2):
        _write_line(
            path,
            {
                "ts": ts_recent,
                "agent": "codex",
                "entrypoint": "bridge",
                "model": "gpt-5.5",
                "outcome": "rate_limited",
            },
        )

    summary = usage_mod.summarize_lane_runtime("codex", window_s=300, usage_dir=tmp_path, now=now)
    assert summary["ok"] == 1
    assert summary["rate_limited"] >= 2
    assert summary["headroom_blocked"] is True
    assert "rate_limited" in summary["headroom_reason"]
    assert "gpt-5.5" in summary["models_rate_limited"]


def test_summarize_lane_runtime_ignores_stale_events(tmp_path: Path, monkeypatch) -> None:
    usage_mod._reset_rate_limit_cache_for_tests()
    monkeypatch.setattr(usage_mod, "_usage_dir", lambda: tmp_path)
    now = time.time()
    old = datetime.fromtimestamp(now - 3600, tz=UTC)
    day = old.strftime("%Y-%m-%d")
    path = tmp_path / f"usage_claude-bridge_{day}.jsonl"
    # Touch mtime into the past so file-level skip applies
    _write_line(
        path,
        {
            "ts": (old).isoformat(),
            "agent": "claude",
            "entrypoint": "bridge",
            "model": "opus",
            "outcome": "rate_limited",
        },
    )
    # Force mtime old
    import os

    os.utime(path, (now - 3600, now - 3600))

    summary = usage_mod.summarize_lane_runtime("claude", window_s=300, usage_dir=tmp_path, now=now)
    assert summary["total"] == 0
    assert summary["headroom_blocked"] is False


def _stamp(now: float, age_s: float, *, utc: bool = True) -> str:
    moment = datetime.fromtimestamp(now - age_s, tz=UTC).replace(microsecond=0)
    if utc:
        return moment.strftime("%Y-%m-%dT%H:%M:%SZ")
    return moment.astimezone(timezone(timedelta(hours=2))).isoformat()


def test_gemini_runtime_counts_agy_and_legacy_records_once(tmp_path: Path) -> None:
    """AC-01/AC-02: both prefixes, all outcome categories, faults, and one copy."""
    from agent_runtime.agent_identity import resolve_retired_agent_alias

    usage_mod._reset_rate_limit_cache_for_tests()
    assert resolve_retired_agent_alias("gemini") == "agy"
    now = time.time()
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    agy = tmp_path / f"usage_agy-dispatch_{day}.jsonl"
    gemini = tmp_path / f"usage_gemini-dispatch_{day}.jsonl"
    rate_iso = _stamp(now, 10)
    rate_ts = datetime.fromisoformat(rate_iso.replace("Z", "+00:00")).timestamp()
    for record in (
        {"ts": _stamp(now, 30), "outcome": "ok", "model": "gemini-3.8-flash-high"},
        {"ts": _stamp(now, 25), "outcome": "error"},
        {"ts": _stamp(now, 22), "outcome": "timeout"},
        {"ts": _stamp(now, 21), "outcome": "cancelled"},
        {"ts": rate_iso, "outcome": "rate_limited", "model": "gemini-3.8-flash-high"},
    ):
        _write_line(agy, record)
    _write_line(
        gemini,
        {"ts": _stamp(now, 20, utc=False), "outcome": "rate_limited", "model": "gemini-3.5-flash"},
    )
    with gemini.open("a", encoding="utf-8") as handle:
        handle.write("{not-json\n[]\n")
    os.link(gemini, tmp_path / f"usage_agy-alias_{day}.jsonl")

    stale = tmp_path / f"usage_gemini-stale_{day}.jsonl"
    _write_line(stale, {"ts": _stamp(now, 15), "outcome": "rate_limited", "model": "should-not-appear"})
    os.utime(stale, (now - 3600, now - 3600))

    missing = tmp_path / "missing-usage.jsonl"
    for name in ("agy", "gemini"):
        (tmp_path / f"usage_{name}-missing_{day}.jsonl").symlink_to(missing)

    _write_line(tmp_path / f"usage_codex-bridge_{day}.jsonl", {"ts": _stamp(now, 12), "outcome": "ok"})
    _write_line(tmp_path / f"usage_claude-bridge_{day}.jsonl", {"ts": _stamp(now, 12), "outcome": "error"})
    _write_line(tmp_path / f"usage_grok-bridge_{day}.jsonl", {"ts": _stamp(now, 12), "outcome": "timeout"})
    _write_line(tmp_path / f"usage_glm-bridge_{day}.jsonl", {"ts": _stamp(now, 12), "outcome": "ok"})

    gemini_summary = usage_mod.summarize_lane_runtime("gemini", window_s=300, usage_dir=tmp_path, now=now)
    agy_summary = usage_mod.summarize_lane_runtime("agy", window_s=300, usage_dir=tmp_path, now=now)
    assert gemini_summary["ok"] == 1
    assert gemini_summary["error"] == 1
    assert gemini_summary["timeout"] == 1
    assert gemini_summary["other"] == 1
    assert gemini_summary["rate_limited"] == 2
    assert gemini_summary["total"] == 6
    assert agy_summary["total"] == gemini_summary["total"]
    assert agy_summary["rate_limited"] == 2
    assert gemini_summary["models_rate_limited"] == ["gemini-3.5-flash", "gemini-3.8-flash-high"]
    assert "should-not-appear" not in gemini_summary["models_rate_limited"]
    assert gemini_summary["headroom_blocked"] is True
    assert "rate_limited" in gemini_summary["headroom_reason"]
    assert gemini_summary["last_rate_limited_at"] == datetime.fromtimestamp(rate_ts, tz=UTC).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    assert gemini_summary["unreadable"] == {"files": 1, "lines": 2, "records": 1, "total": 4}
    assert agy_summary["unreadable"] == gemini_summary["unreadable"]

    usage_mod._RATE_LIMIT_CACHE[("agy", "gemini-3.8-flash-high")] = rate_ts
    usage_mod._RATE_LIMIT_CACHE[("agy", "gemini-extra")] = now - 12
    try:
        cached = usage_mod.summarize_lane_runtime("gemini", window_s=300, usage_dir=tmp_path, now=now)
        assert cached["rate_limited"] == 3
        assert cached["models_rate_limited"] == [
            "gemini-3.5-flash",
            "gemini-3.8-flash-high",
            "gemini-extra",
        ]
    finally:
        usage_mod._reset_rate_limit_cache_for_tests()

    codex = usage_mod.summarize_lane_runtime("codex", window_s=300, usage_dir=tmp_path, now=now)
    claude = usage_mod.summarize_lane_runtime("claude", window_s=300, usage_dir=tmp_path, now=now)
    grok = usage_mod.summarize_lane_runtime("grok", window_s=300, usage_dir=tmp_path, now=now)
    cursor = usage_mod.summarize_lane_runtime("cursor", window_s=300, usage_dir=tmp_path, now=now)
    glm = usage_mod.summarize_lane_runtime("glm", window_s=300, usage_dir=tmp_path, now=now)
    assert (codex["ok"], codex["total"], codex["rate_limited"], codex["unreadable"]["total"]) == (1, 1, 0, 0)
    assert (claude["error"], claude["total"]) == (1, 1)
    assert (grok["timeout"], grok["total"]) == (1, 1)
    assert cursor["total"] == 0
    assert glm["total"] == 1


def test_gemini_telemetry_names_read_retired_alias_map(monkeypatch) -> None:
    """The Gemini row reads the canonical alias map and never calls the admission resolver."""
    source = Path(usage_mod.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned = "resolve_retired_agent_alias"
    seen: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            seen.extend(alias.name for alias in node.names if alias.name == banned)
        elif isinstance(node, ast.Call):
            func = node.func
            called = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if called == banned:
                seen.append(f"call:{node.lineno}")
    assert seen == []

    from agent_runtime.agent_identity import RETIRED_AGENT_ALIASES

    assert usage_mod.RETIRED_AGENT_ALIASES is RETIRED_AGENT_ALIASES
    assert RETIRED_AGENT_ALIASES["gemini"] == "agy"
    assert usage_mod._gemini_telemetry_names() == ("agy", "gemini")

    monkeypatch.setattr(usage_mod, "RETIRED_AGENT_ALIASES", {"glm": "cursor"})
    assert usage_mod._gemini_telemetry_names() == ("agy", "gemini")

    monkeypatch.setattr(usage_mod, "RETIRED_AGENT_ALIASES", {"gemini": "", "glm": "cursor"})
    assert usage_mod._gemini_telemetry_names() == ("agy", "gemini")

    monkeypatch.setattr(usage_mod, "RETIRED_AGENT_ALIASES", {"gemini": None, "glm": "cursor"})
    assert usage_mod._gemini_telemetry_names() == ("agy", "gemini")

    monkeypatch.setattr(usage_mod, "RETIRED_AGENT_ALIASES", {"gemini": "gemini", "glm": "cursor"})
    assert usage_mod._gemini_telemetry_names() == ("agy", "gemini")

    monkeypatch.setattr(usage_mod, "RETIRED_AGENT_ALIASES", {"gemini": "map-successor", "glm": "cursor"})
    assert usage_mod._gemini_telemetry_names() == ("agy", "gemini", "map-successor")


def test_fleet_burn_counts_agy_and_gemini_across_windows_once(tmp_path: Path) -> None:
    """5h, 7d, and 30d burn see both aliases once, including every outcome class."""
    usage_mod._reset_rate_limit_cache_for_tests()
    now = time.time()
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    agy = tmp_path / f"usage_agy-dispatch_{day}.jsonl"
    gemini = tmp_path / f"usage_gemini-dispatch_{day}.jsonl"
    for record in (
        {"ts": _stamp(now, 60), "outcome": "ok", "duration_s": 3600},
        {"ts": _stamp(now, 50), "outcome": "error"},
        {"ts": _stamp(now, 40), "outcome": "timeout"},
        {"ts": _stamp(now, 30), "outcome": "cancelled"},
        {"ts": _stamp(now, 20), "outcome": "rate_limited", "duration_s": 1800},
        {"ts": _stamp(now, 6 * 3600 + 60), "outcome": "ok"},
    ):
        _write_line(agy, record)
    _write_line(gemini, {"ts": _stamp(now, 10 * 86400 + 60), "outcome": "error"})
    _write_line(gemini, {"ts": _stamp(now, 40 * 86400), "outcome": "timeout"})
    with gemini.open("a", encoding="utf-8") as handle:
        handle.write("{not-json\n")
    os.link(gemini, tmp_path / f"usage_agy-alias_{day}.jsonl")
    _write_line(
        tmp_path / f"usage_codex-bridge_{day}.jsonl", {"ts": _stamp(now, 30), "outcome": "ok", "duration_s": 1800}
    )
    _write_line(tmp_path / f"usage_claude-bridge_{day}.jsonl", {"ts": _stamp(now, 3 * 86400), "outcome": "error"})
    _write_line(tmp_path / f"usage_grok-bridge_{day}.jsonl", {"ts": _stamp(now, 20 * 86400), "outcome": "timeout"})
    _write_line(tmp_path / f"usage_glm-bridge_{day}.jsonl", {"ts": _stamp(now, 30), "outcome": "ok"})

    gemini_burn = usage_mod.summarize_fleet_burn("gemini", usage_dir=tmp_path, now=now)
    agy_burn = usage_mod.summarize_fleet_burn("agy", usage_dir=tmp_path, now=now)
    assert gemini_burn["agent"] == "gemini"
    assert agy_burn["agent"] == "agy"
    assert gemini_burn["windows"]["5h"]["counts"] == {
        "ok": 1,
        "error": 1,
        "rate_limited": 1,
        "timeout": 1,
        "other": 1,
        "total": 5,
    }
    assert gemini_burn["windows"]["5h"]["hours"] == 1.5
    assert gemini_burn["windows"]["7d"]["counts"]["ok"] == 2
    assert gemini_burn["windows"]["7d"]["counts"]["total"] == 6
    assert gemini_burn["windows"]["30d"]["counts"]["error"] == 2
    assert gemini_burn["windows"]["30d"]["counts"]["timeout"] == 1
    assert gemini_burn["windows"]["30d"]["counts"]["total"] == 7
    assert gemini_burn["unreadable"] == {"files": 0, "lines": 1, "records": 0, "total": 1}
    assert agy_burn["windows"] == gemini_burn["windows"]
    assert agy_burn["unreadable"] == gemini_burn["unreadable"]

    codex = usage_mod.summarize_fleet_burn("codex", usage_dir=tmp_path, now=now)
    claude = usage_mod.summarize_fleet_burn("claude", usage_dir=tmp_path, now=now)
    grok = usage_mod.summarize_fleet_burn("grok", usage_dir=tmp_path, now=now)
    cursor = usage_mod.summarize_fleet_burn("cursor", usage_dir=tmp_path, now=now)
    assert codex["windows"]["5h"]["counts"]["total"] == 1
    assert codex["windows"]["5h"]["hours"] == 0.5
    assert codex["unreadable"]["total"] == 0
    assert claude["windows"]["5h"]["counts"]["total"] == 0
    assert claude["windows"]["7d"]["counts"]["total"] == 1
    assert grok["windows"]["7d"]["counts"]["total"] == 0
    assert grok["windows"]["30d"]["counts"]["total"] == 1
    assert cursor["windows"]["5h"]["counts"]["total"] == 0


def _usage_corrupt_line(kind: str, now: float) -> bytes:
    """One bad usage line. The in-string kind is JSON except for byte 0xFF."""
    if kind == "json-non-object":
        return b"[]\n"
    if kind == "invalid-utf8":
        return b"\xff\n"
    if kind == "invalid-utf8-in-string":
        payload = json.dumps(
            {
                "ts": _stamp(now, 45),
                "outcome": "ok",
                "duration_s": 10,
                "model": "MODEL_TOKEN",
            }
        ).encode("ascii")
        return payload.replace(b"MODEL_TOKEN", b"gemini-\xff") + b"\n"
    raise AssertionError(kind)


def _corrupt_combined_usage(tmp_path: Path, corrupt_kind: str) -> float:
    """Valid Gemini and AGY rows, then one bad AGY line, then another AGY row.

    The row after the bad line is the one a file-level abort would drop.
    A directory and a broken symlink are file faults and must not erase hours.
    """
    usage_mod._reset_rate_limit_cache_for_tests()
    now = time.time()
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    agy = tmp_path / f"usage_agy-dispatch_{day}.jsonl"
    gemini = tmp_path / f"usage_gemini-dispatch_{day}.jsonl"
    _write_line(agy, {"ts": _stamp(now, 60), "outcome": "ok", "duration_s": 3600})
    with agy.open("ab") as handle:
        handle.write(b"\n")
        handle.write(_usage_corrupt_line(corrupt_kind, now))
        handle.write(b"\n")
    _write_line(agy, {"outcome": "ok", "duration_s": 999})
    _write_line(agy, {"ts": "not-a-timestamp", "outcome": "ok", "duration_s": 999})
    _write_line(agy, {"ts": _stamp(now, 6 * 3600 + 60), "outcome": "ok", "duration_s": 7200})
    _write_line(
        gemini,
        {
            "ts": _stamp(now, 30),
            "outcome": "rate_limited",
            "duration_s": 1800,
            "model": "gemini-3.8-flash-high",
        },
    )
    _write_line(gemini, {"ts": _stamp(now, 10 * 86400 + 60), "outcome": "error", "duration_s": 3600})
    os.link(gemini, tmp_path / f"usage_agy-alias_{day}.jsonl")
    (tmp_path / f"usage_agy-dir_{day}.jsonl").mkdir()
    missing = tmp_path / "missing-usage.jsonl"
    for name in ("agy", "gemini"):
        (tmp_path / f"usage_{name}-missing_{day}.jsonl").symlink_to(missing)
    codex = tmp_path / f"usage_codex-bridge_{day}.jsonl"
    _write_line(codex, {"ts": _stamp(now, 15), "outcome": "ok", "duration_s": 1800})
    with codex.open("ab") as handle:
        handle.write(b"[]\n")
    _write_line(tmp_path / f"usage_claude-bridge_{day}.jsonl", {"ts": _stamp(now, 3 * 86400), "outcome": "error"})
    _write_line(
        tmp_path / f"usage_glm-bridge_{day}.jsonl",
        {"ts": _stamp(now, 15), "outcome": "ok", "duration_s": 100000},
    )
    return now


@pytest.mark.parametrize(
    "corrupt_kind",
    ["json-non-object", "invalid-utf8", "invalid-utf8-in-string"],
)
def test_fleet_burn_keeps_gemini_agy_durations_when_agy_evidence_is_corrupt(
    tmp_path: Path, corrupt_kind: str
) -> None:
    """Malformed AGY lines keep 5h, 7d, and 30d durations and show the fault.

    A non-object, a standalone invalid byte, and an invalid byte inside a
    JSON string are one unreadable line. Replacement decoding would count
    the third as an ok row.
    """
    now = _corrupt_combined_usage(tmp_path, corrupt_kind)
    if corrupt_kind == "invalid-utf8-in-string":
        line = _usage_corrupt_line(corrupt_kind, now)
        replaced = json.loads(line.decode("utf-8", errors="replace"))
        assert replaced["outcome"] == "ok"
        assert replaced["model"] == "gemini-\ufffd"
        assert replaced["ts"] == _stamp(now, 45)
        with pytest.raises(UnicodeDecodeError):
            line.decode("utf-8", errors="strict")
    expected_unreadable = {"files": 2, "lines": 1, "records": 0, "total": 3}
    expected_5h = {"ok": 1, "error": 0, "rate_limited": 1, "timeout": 0, "other": 0, "total": 2}

    gemini_burn = usage_mod.summarize_fleet_burn("gemini", usage_dir=tmp_path, now=now)
    agy_burn = usage_mod.summarize_fleet_burn("agy", usage_dir=tmp_path, now=now)
    assert gemini_burn["windows"]["5h"]["counts"] == expected_5h
    assert gemini_burn["windows"]["5h"]["hours"] == 1.5
    assert gemini_burn["windows"]["7d"]["counts"] == {
        "ok": 2,
        "error": 0,
        "rate_limited": 1,
        "timeout": 0,
        "other": 0,
        "total": 3,
    }
    assert gemini_burn["windows"]["7d"]["hours"] == 3.5
    assert gemini_burn["windows"]["30d"]["counts"] == {
        "ok": 2,
        "error": 1,
        "rate_limited": 1,
        "timeout": 0,
        "other": 0,
        "total": 4,
    }
    assert gemini_burn["windows"]["30d"]["hours"] == 4.5
    assert gemini_burn["windows"]["5h"]["window_s"] == 5 * 3600
    assert gemini_burn["windows"]["7d"]["window_s"] == 7 * 24 * 3600
    assert gemini_burn["windows"]["30d"]["window_s"] == 30 * 24 * 3600
    assert gemini_burn["unreadable"] == expected_unreadable
    assert agy_burn["agent"] == "agy"
    assert agy_burn["windows"] == gemini_burn["windows"]
    assert agy_burn["unreadable"] == gemini_burn["unreadable"]

    gemini_runtime = usage_mod.summarize_lane_runtime("gemini", usage_dir=tmp_path, now=now)
    agy_runtime = usage_mod.summarize_lane_runtime("agy", usage_dir=tmp_path, now=now)
    assert gemini_runtime["total"] == expected_5h["total"]
    assert gemini_runtime["ok"] == 1
    assert gemini_runtime["rate_limited"] == 1
    assert gemini_runtime["unreadable"] == gemini_burn["unreadable"]
    assert agy_runtime["total"] == gemini_runtime["total"]
    assert agy_runtime["unreadable"] == gemini_runtime["unreadable"]

    codex = usage_mod.summarize_fleet_burn("codex", usage_dir=tmp_path, now=now)
    claude = usage_mod.summarize_fleet_burn("claude", usage_dir=tmp_path, now=now)
    assert codex["windows"]["5h"]["counts"]["total"] == 1
    assert codex["windows"]["5h"]["hours"] == 0.5
    assert codex["unreadable"] == {"files": 0, "lines": 1, "records": 0, "total": 1}
    assert claude["windows"]["5h"]["counts"]["total"] == 0
    assert claude["windows"]["7d"]["counts"]["total"] == 1
    assert claude["unreadable"]["total"] == 0


def test_literal_ufffd_counts_and_invalid_bytes_inside_a_string_do_not(tmp_path: Path) -> None:
    """UTF-8 for U+FFFD is a real model string. A lone 0xFF in that string is not."""
    usage_mod._reset_rate_limit_cache_for_tests()
    now = time.time()
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    agy = tmp_path / f"usage_agy-dispatch_{day}.jsonl"
    gemini = tmp_path / f"usage_gemini-dispatch_{day}.jsonl"
    _write_line(agy, {"ts": _stamp(now, 60), "outcome": "ok", "duration_s": 3600})
    ufffd_line = (
        json.dumps(
            {
                "ts": _stamp(now, 40),
                "outcome": "rate_limited",
                "duration_s": 1800,
                "model": "gemini-\ufffd",
            },
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")
    assert b"\xef\xbf\xbd" in ufffd_line
    assert b"\xff" not in ufffd_line
    assert json.loads(ufffd_line.decode("utf-8"))["model"] == "gemini-\ufffd"
    bad_line = _usage_corrupt_line("invalid-utf8-in-string", now)
    assert b"\xff" in bad_line
    assert b"\xef\xbf\xbd" not in bad_line
    with agy.open("ab") as handle:
        handle.write(ufffd_line)
        handle.write(bad_line)
    _write_line(agy, {"ts": _stamp(now, 6 * 3600 + 60), "outcome": "timeout", "duration_s": 7200})
    _write_line(
        gemini,
        {"ts": _stamp(now, 10 * 86400 + 60), "outcome": "error", "duration_s": 3600},
    )
    os.link(gemini, tmp_path / f"usage_agy-alias_{day}.jsonl")
    _write_line(
        tmp_path / f"usage_codex-bridge_{day}.jsonl",
        {"ts": _stamp(now, 15), "outcome": "ok", "duration_s": 1800},
    )
    _write_line(
        tmp_path / f"usage_claude-bridge_{day}.jsonl",
        {"ts": _stamp(now, 3 * 86400), "outcome": "error"},
    )

    expected_unreadable = {"files": 0, "lines": 1, "records": 0, "total": 1}
    gemini_burn = usage_mod.summarize_fleet_burn("gemini", usage_dir=tmp_path, now=now)
    agy_burn = usage_mod.summarize_fleet_burn("agy", usage_dir=tmp_path, now=now)
    assert gemini_burn["windows"]["5h"]["counts"] == {
        "ok": 1,
        "error": 0,
        "rate_limited": 1,
        "timeout": 0,
        "other": 0,
        "total": 2,
    }
    assert gemini_burn["windows"]["5h"]["hours"] == 1.5
    assert gemini_burn["windows"]["7d"]["counts"]["total"] == 3
    assert gemini_burn["windows"]["7d"]["hours"] == 3.5
    assert gemini_burn["windows"]["30d"]["counts"] == {
        "ok": 1,
        "error": 1,
        "rate_limited": 1,
        "timeout": 1,
        "other": 0,
        "total": 4,
    }
    assert gemini_burn["windows"]["30d"]["hours"] == 4.5
    assert gemini_burn["unreadable"] == expected_unreadable
    assert agy_burn["windows"] == gemini_burn["windows"]
    assert agy_burn["unreadable"] == gemini_burn["unreadable"]

    gemini_runtime = usage_mod.summarize_lane_runtime("gemini", usage_dir=tmp_path, now=now)
    agy_runtime = usage_mod.summarize_lane_runtime("agy", usage_dir=tmp_path, now=now)
    assert gemini_runtime["ok"] == 1
    assert gemini_runtime["rate_limited"] == 1
    assert gemini_runtime["total"] == 2
    assert gemini_runtime["models_rate_limited"] == ["gemini-\ufffd"]
    assert gemini_runtime["headroom_blocked"] is False
    assert gemini_runtime["unreadable"] == expected_unreadable
    assert agy_runtime["total"] == gemini_runtime["total"]
    assert agy_runtime["models_rate_limited"] == gemini_runtime["models_rate_limited"]
    assert agy_runtime["unreadable"] == gemini_runtime["unreadable"]

    codex = usage_mod.summarize_fleet_burn("codex", usage_dir=tmp_path, now=now)
    claude = usage_mod.summarize_fleet_burn("claude", usage_dir=tmp_path, now=now)
    assert codex["windows"]["5h"]["counts"]["total"] == 1
    assert codex["windows"]["5h"]["hours"] == 0.5
    assert codex["unreadable"]["total"] == 0
    assert claude["windows"]["5h"]["counts"]["total"] == 0
    assert claude["windows"]["7d"]["counts"]["total"] == 1
    assert claude["unreadable"]["total"] == 0


def test_runtime_cache_ignores_other_lanes_and_drops_stale_alias_entries(tmp_path: Path) -> None:
    """A Codex cache entry stays put. A stale AGY entry is removed and not counted."""
    usage_mod._reset_rate_limit_cache_for_tests()
    now = time.time()
    fresh = now - 12
    foreign = now - 10
    usage_mod._RATE_LIMIT_CACHE[("codex", "gpt-6.1-sol")] = foreign
    usage_mod._RATE_LIMIT_CACHE[("agy", "stale-model")] = now - 10_000
    usage_mod._RATE_LIMIT_CACHE[("agy", "gemini-fresh")] = fresh
    try:
        summary = usage_mod.summarize_lane_runtime("gemini", window_s=300, usage_dir=tmp_path, now=now)
        assert summary["rate_limited"] == 1
        assert summary["models_rate_limited"] == ["gemini-fresh"]
        assert summary["headroom_blocked"] is False
        assert summary["unreadable"]["total"] == 0
        assert ("agy", "stale-model") not in usage_mod._RATE_LIMIT_CACHE
        assert usage_mod._RATE_LIMIT_CACHE[("codex", "gpt-6.1-sol")] == foreign
        assert usage_mod._RATE_LIMIT_CACHE[("agy", "gemini-fresh")] == fresh
    finally:
        usage_mod._reset_rate_limit_cache_for_tests()


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads mode-000 directories")
def test_unlistable_usage_directory_counts_as_one_unreadable_file(tmp_path: Path) -> None:
    """A directory the process cannot list is a file fault, not a crash or a row."""
    usage_mod._reset_rate_limit_cache_for_tests()
    now = time.time()
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    root = tmp_path / "api_usage"
    root.mkdir()
    _write_line(
        root / f"usage_codex-bridge_{day}.jsonl",
        {"ts": _stamp(now, 20), "outcome": "rate_limited", "model": "hidden"},
    )
    root.chmod(0)
    try:
        summary = usage_mod.summarize_lane_runtime("codex", window_s=300, usage_dir=root, now=now)
    finally:
        root.chmod(0o700)
    assert summary["total"] == 0
    assert summary["rate_limited"] == 0
    assert summary["models_rate_limited"] == []
    assert summary["unreadable"] == {"files": 1, "lines": 0, "records": 0, "total": 1}


_EMPTY_BURN_COUNTS = {"ok": 0, "error": 0, "rate_limited": 0, "timeout": 0, "other": 0, "total": 0}
_BURN_WINDOW_S = {"5h": 5 * 3600, "7d": 7 * 24 * 3600, "30d": 30 * 24 * 3600}
_DIRECTORY_FAULT = {"files": 1, "lines": 0, "records": 0, "total": 1}


def _assert_empty_burn(burn: dict, agent: str) -> None:
    """All three burn windows exist and hold no rows."""
    assert burn["source"] == "agent_runtime_jsonl"
    assert burn["agent"] == agent
    assert set(burn["windows"]) == set(_BURN_WINDOW_S)
    for name, window in burn["windows"].items():
        assert window["window_s"] == _BURN_WINDOW_S[name]
        assert window["counts"] == _EMPTY_BURN_COUNTS
        assert window["hours"] == 0.0


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads mode-000 directories")
def test_unlistable_usage_directory_is_unreadable_burn_for_each_alias_and_codex(tmp_path: Path) -> None:
    """Gemini, AGY, and Codex burn report one fault when the usage directory cannot be listed.

    A missing directory stays empty. A readable directory keeps 5h, 7d, and 30d
    counts, one copy of a hard-linked file, and the JSON line fault. An in-process
    rate-limit cache does not hide the directory fault or invent burn rows.
    """
    usage_mod._reset_rate_limit_cache_for_tests()
    now = time.time()
    day = datetime.fromtimestamp(now, tz=UTC).strftime("%Y-%m-%d")
    missing = tmp_path / "no-such-usage"
    assert not missing.exists()
    for agent in ("gemini", "agy", "codex"):
        _assert_empty_burn(usage_mod.summarize_fleet_burn(agent, usage_dir=missing, now=now), agent)
        runtime = usage_mod.summarize_lane_runtime(agent, window_s=300, usage_dir=missing, now=now)
        assert runtime["total"] == 0
        assert runtime["unreadable"] == {"files": 0, "lines": 0, "records": 0, "total": 0}

    root = tmp_path / "api_usage"
    root.mkdir()
    agy = root / f"usage_agy-dispatch_{day}.jsonl"
    gemini = root / f"usage_gemini-dispatch_{day}.jsonl"
    _write_line(agy, {"ts": _stamp(now, 60), "outcome": "ok", "duration_s": 3600})
    _write_line(
        agy,
        {"ts": _stamp(now, 20), "outcome": "rate_limited", "model": "gemini-3.8-flash-high"},
    )
    _write_line(gemini, {"ts": _stamp(now, 6 * 3600 + 60), "outcome": "error", "duration_s": 3600})
    _write_line(gemini, {"ts": _stamp(now, 10 * 86400), "outcome": "timeout"})
    with gemini.open("a", encoding="utf-8") as handle:
        handle.write("{not-json\n")
    os.link(gemini, root / f"usage_agy-alias_{day}.jsonl")
    _write_line(
        root / f"usage_codex-bridge_{day}.jsonl",
        {"ts": _stamp(now, 30), "outcome": "ok", "duration_s": 1800},
    )
    listed = sorted(path.name for path in root.glob("usage_*.jsonl"))
    assert len(listed) == 4

    expected_5h = {"ok": 1, "error": 0, "rate_limited": 1, "timeout": 0, "other": 0, "total": 2}
    expected_7d = {"ok": 1, "error": 1, "rate_limited": 1, "timeout": 0, "other": 0, "total": 3}
    expected_30d = {"ok": 1, "error": 1, "rate_limited": 1, "timeout": 1, "other": 0, "total": 4}
    line_fault = {"files": 0, "lines": 1, "records": 0, "total": 1}
    gemini_burn = usage_mod.summarize_fleet_burn("gemini", usage_dir=root, now=now)
    agy_burn = usage_mod.summarize_fleet_burn("agy", usage_dir=root, now=now)
    assert gemini_burn["windows"]["5h"]["counts"] == expected_5h
    assert gemini_burn["windows"]["5h"]["hours"] == 1.0
    assert gemini_burn["windows"]["7d"]["counts"] == expected_7d
    assert gemini_burn["windows"]["7d"]["hours"] == 2.0
    assert gemini_burn["windows"]["30d"]["counts"] == expected_30d
    assert gemini_burn["windows"]["30d"]["hours"] == 2.0
    assert gemini_burn["windows"]["5h"]["window_s"] == _BURN_WINDOW_S["5h"]
    assert gemini_burn["windows"]["7d"]["window_s"] == _BURN_WINDOW_S["7d"]
    assert gemini_burn["windows"]["30d"]["window_s"] == _BURN_WINDOW_S["30d"]
    assert gemini_burn["unreadable"] == line_fault
    assert agy_burn["windows"] == gemini_burn["windows"]
    assert agy_burn["unreadable"] == gemini_burn["unreadable"]
    codex_burn = usage_mod.summarize_fleet_burn("codex", usage_dir=root, now=now)
    assert codex_burn["windows"]["5h"]["counts"]["total"] == 1
    assert codex_burn["windows"]["5h"]["hours"] == 0.5
    assert codex_burn["windows"]["7d"]["counts"]["total"] == 1
    assert codex_burn["windows"]["30d"]["counts"]["total"] == 1
    assert codex_burn["unreadable"]["total"] == 0
    claude_burn = usage_mod.summarize_fleet_burn("claude", usage_dir=root, now=now)
    _assert_empty_burn(claude_burn, "claude")
    assert claude_burn["unreadable"]["total"] == 0
    gemini_runtime = usage_mod.summarize_lane_runtime("gemini", window_s=300, usage_dir=root, now=now)
    assert gemini_runtime["ok"] == 1
    assert gemini_runtime["rate_limited"] == 1
    assert gemini_runtime["total"] == 2
    assert gemini_runtime["models_rate_limited"] == ["gemini-3.8-flash-high"]
    assert gemini_runtime["headroom_blocked"] is False
    assert gemini_runtime["unreadable"] == line_fault

    root.chmod(0)
    try:
        for agent in ("gemini", "agy", "codex"):
            runtime = usage_mod.summarize_lane_runtime(agent, window_s=300, usage_dir=root, now=now)
            burn = usage_mod.summarize_fleet_burn(agent, usage_dir=root, now=now)
            assert runtime["total"] == 0
            assert runtime["rate_limited"] == 0
            assert runtime["unreadable"] == _DIRECTORY_FAULT
            assert burn["unreadable"] == runtime["unreadable"], agent
            _assert_empty_burn(burn, agent)
        usage_mod._RATE_LIMIT_CACHE[("agy", "gemini-fresh")] = now - 12
        usage_mod._RATE_LIMIT_CACHE[("codex", "kept-model")] = now - 8
        cached = usage_mod.summarize_lane_runtime("gemini", window_s=300, usage_dir=root, now=now)
        assert cached["rate_limited"] == 1
        assert cached["total"] == 1
        assert cached["models_rate_limited"] == ["gemini-fresh"]
        assert cached["headroom_blocked"] is False
        assert cached["unreadable"] == _DIRECTORY_FAULT
        cached_burn = usage_mod.summarize_fleet_burn("gemini", usage_dir=root, now=now)
        assert cached_burn["unreadable"] == _DIRECTORY_FAULT
        _assert_empty_burn(cached_burn, "gemini")
        assert usage_mod._RATE_LIMIT_CACHE[("codex", "kept-model")] == now - 8
        codex_runtime = usage_mod.summarize_lane_runtime("codex", window_s=300, usage_dir=root, now=now)
        assert codex_runtime["rate_limited"] == 1
        assert codex_runtime["models_rate_limited"] == ["kept-model"]
        assert codex_runtime["unreadable"] == _DIRECTORY_FAULT
        claude_hidden = usage_mod.summarize_fleet_burn("claude", usage_dir=root, now=now)
        assert claude_hidden["unreadable"] == _DIRECTORY_FAULT
        _assert_empty_burn(claude_hidden, "claude")
    finally:
        root.chmod(0o700)
        usage_mod._reset_rate_limit_cache_for_tests()
