"""Hybrid usage: agent JSONL lane summaries for routing-budget enrichment."""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
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
