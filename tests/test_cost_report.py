"""Tests for scripts/analytics/cost_report.py."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

import scripts.analytics.cost_report as cost_report

pytestmark = pytest.mark.reads_content


def _write_meta(
    root: Path,
    *,
    level: str,
    slug: str,
    filename: str,
    phase: str,
    agent: str,
    model: str | None = None,
    prompt_chars: int,
    response_chars: int,
    timestamp: str = "2026-04-10T12:00:00Z",
    with_tokens: bool = False,
    mtime: datetime | None = None,
) -> Path:
    dispatch_dir = root / level / "orchestration" / slug / "dispatch"
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": timestamp,
        "phase": phase,
        "agent": agent,
        "ok": True,
        "returncode": 0,
        "prompt_chars": prompt_chars,
        "response_chars": response_chars,
        "duration_s": 12.5,
    }
    if model is not None:
        payload["model"] = model
    if with_tokens:
        payload["prompt_tokens_est"] = cost_report.estimate_tokens(prompt_chars)
        payload["response_tokens_est"] = cost_report.estimate_tokens(response_chars)
    path = dispatch_dir / filename
    path.write_text(json.dumps(payload), encoding="utf-8")
    if mtime is not None:
        ts = mtime.timestamp()
        os.utime(path, (ts, ts))
    return path


def test_legacy_meta_backfills_tokens_from_chars(tmp_path, monkeypatch):
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", tmp_path)
    _write_meta(
        tmp_path,
        level="a1",
        slug="my-family",
        filename="01-write-meta.json",
        phase="write",
        agent="codex (gpt-5.4)",
        prompt_chars=3800,
        response_chars=760,
    )
    _write_meta(
        tmp_path,
        level="a1",
        slug="my-family",
        filename="02-review-meta.json",
        phase="review",
        agent="codex (gpt-5.4)",
        prompt_chars=1900,
        response_chars=380,
    )
    _write_meta(
        tmp_path,
        level="a2",
        slug="bridge",
        filename="03-write-meta.json",
        phase="write",
        agent="codex (gpt-5.4)",
        prompt_chars=760,
        response_chars=380,
    )

    summary = cost_report.build_cost_summary()

    expected_prompt = round(3800 / 3.8) + round(1900 / 3.8) + round(760 / 3.8)
    expected_response = round(760 / 3.8) + round(380 / 3.8) + round(380 / 3.8)
    assert abs(summary["totals"]["prompt_tokens_est"] - expected_prompt) <= max(1, expected_prompt * 0.01)
    assert abs(summary["totals"]["response_tokens_est"] - expected_response) <= max(1, expected_response * 0.01)
