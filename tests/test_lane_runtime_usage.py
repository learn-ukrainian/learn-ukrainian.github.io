"""Hybrid usage: agent JSONL lane summaries for routing-budget enrichment."""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

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
    assert agy_burn["windows"] == gemini_burn["windows"]

    codex = usage_mod.summarize_fleet_burn("codex", usage_dir=tmp_path, now=now)
    claude = usage_mod.summarize_fleet_burn("claude", usage_dir=tmp_path, now=now)
    grok = usage_mod.summarize_fleet_burn("grok", usage_dir=tmp_path, now=now)
    cursor = usage_mod.summarize_fleet_burn("cursor", usage_dir=tmp_path, now=now)
    assert codex["windows"]["5h"]["counts"]["total"] == 1
    assert codex["windows"]["5h"]["hours"] == 0.5
    assert claude["windows"]["5h"]["counts"]["total"] == 0
    assert claude["windows"]["7d"]["counts"]["total"] == 1
    assert grok["windows"]["7d"]["counts"]["total"] == 0
    assert grok["windows"]["30d"]["counts"]["total"] == 1
    assert cursor["windows"]["5h"]["counts"]["total"] == 0
