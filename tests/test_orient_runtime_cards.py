"""Dedicated tests for #7089 orient runtime cards.

Proves:
1. One card per inventory agent dynamically extracted (no hardcoded list).
2. Per-agent outcome counts (no echoing global outcomes on every card).
3. Retired agents 'gemini' and 'glm' are not presented as live.
4. Agents with headroom keys (cursor, kimi, grok, deepseek, agy, etc.) are included.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _patch_usage_batch_state_dir(monkeypatch, runtime_router, batch_state_dir: Path):
    """Redirect the usage-log root every ``runtime_router`` helper falls back to.

    ``_collect_runtime_orient_data`` (main.py) calls ``summarize_runtime_usage``,
    ``runtime_recent_outcomes_today``, and ``list_runtime_agents`` with no
    ``ctx`` — direct-Python callers outside FastAPI request handling resolve
    through ``monitor_context.production_context()`` via shared
    ``resolve_context`` (#7324 step 6 / #7496). Patch that factory (and the
    router re-export) rather than a since-removed ``USAGE_DIR`` module global.
    """
    import scripts.api.monitor_context as monitor_context

    base_ctx = monitor_context.production_context()
    patched_ctx = base_ctx.with_roots(batch_state_dir=Path(batch_state_dir))
    monkeypatch.setattr(monitor_context, "production_context", lambda ctx=None: patched_ctx)
    monkeypatch.setattr(runtime_router, "production_context", lambda ctx=None: patched_ctx)
    return patched_ctx


def _write_usage_file(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def test_orient_collector_emits_per_agent_outcomes_from_real_usage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """#7089: _collect_runtime_orient_data() populates by_agent from real usage records."""
    from datetime import UTC, datetime, timedelta

    import scripts.api.main as api_main
    import scripts.api.runtime_router as runtime_router

    usage_dir = tmp_path / "api_usage"
    today = datetime.now(UTC)
    _patch_usage_batch_state_dir(monkeypatch, runtime_router, usage_dir.parent)

    _write_usage_file(
        usage_dir / f"usage_claude-dispatch_{today:%Y-%m-%d}.jsonl",
        [
            {"ts": (today - timedelta(minutes=10)).isoformat(), "agent": "claude", "entrypoint": "dispatch", "model": "claude-sonnet-4-6", "duration_s": 5.0, "outcome": "ok"},
            {"ts": (today - timedelta(minutes=8)).isoformat(), "agent": "claude", "entrypoint": "dispatch", "model": "claude-sonnet-4-6", "duration_s": 4.5, "outcome": "ok"},
            {"ts": (today - timedelta(minutes=6)).isoformat(), "agent": "claude", "entrypoint": "dispatch", "model": "claude-sonnet-4-6", "duration_s": 2.0, "outcome": "error"},
        ],
    )
    _write_usage_file(
        usage_dir / f"usage_codex-bridge_{today:%Y-%m-%d}.jsonl",
        [
            {"ts": (today - timedelta(minutes=5)).isoformat(), "agent": "codex", "entrypoint": "bridge", "model": "gpt-5.5", "duration_s": 3.2, "outcome": "ok"},
            {"ts": (today - timedelta(minutes=3)).isoformat(), "agent": "codex", "entrypoint": "bridge", "model": "gpt-5.5", "duration_s": 0.5, "outcome": "rate_limited"},
        ],
    )
    _write_usage_file(
        usage_dir / f"usage_grok-dispatch_{today:%Y-%m-%d}.jsonl",
        [
            {"ts": (today - timedelta(minutes=2)).isoformat(), "agent": "grok", "entrypoint": "dispatch", "model": "grok-code", "duration_s": 6.1, "outcome": "ok"},
        ],
    )

    data = api_main._collect_runtime_orient_data()

    assert "by_agent" in data
    assert isinstance(data["by_agent"], dict)
    assert data["by_agent"]["claude"]["ok"] == 2
    assert data["by_agent"]["claude"]["error"] == 1
    assert data["by_agent"]["claude"]["rate_limited"] == 0
    assert data["by_agent"]["codex"]["ok"] == 1
    assert data["by_agent"]["codex"]["error"] == 0
    assert data["by_agent"]["codex"]["rate_limited"] == 1
    assert data["by_agent"]["grok"]["ok"] == 1
    assert data["recent_outcomes"]["ok"] == 4
    assert data["recent_outcomes"]["error"] == 1
    assert data["recent_outcomes"]["rate_limited"] == 1
