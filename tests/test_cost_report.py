"""Tests for scripts/analytics/cost_report.py."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import scripts.analytics.cost_report as cost_report


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


def test_unknown_model_uses_default_rate_and_warns(tmp_path, monkeypatch):
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", tmp_path)
    _write_meta(
        tmp_path,
        level="a1",
        slug="mystery",
        filename="01-write-meta.json",
        phase="write",
        agent="codex (mystery-model)",
        model="mystery-model",
        prompt_chars=3800,
        response_chars=380,
    )

    summary = cost_report.build_cost_summary()

    prompt_tokens = round(3800 / 3.8)
    response_tokens = round(380 / 3.8)
    expected_cost = ((prompt_tokens * 5.0) + (response_tokens * 20.0)) / 1_000_000
    assert summary["totals"]["cost_usd_est"] == round(expected_cost, 6)
    assert any("mystery-model" in warning for warning in summary["warnings"])


def test_per_phase_aggregation_sums_correctly(tmp_path, monkeypatch):
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", tmp_path)
    _write_meta(
        tmp_path,
        level="a1",
        slug="alpha",
        filename="01-write-meta.json",
        phase="write",
        agent="codex (gpt-5.4)",
        prompt_chars=3800,
        response_chars=380,
    )
    _write_meta(
        tmp_path,
        level="a1",
        slug="alpha",
        filename="02-review-meta.json",
        phase="review",
        agent="codex (gpt-5.4)",
        prompt_chars=760,
        response_chars=190,
    )
    _write_meta(
        tmp_path,
        level="a2",
        slug="beta",
        filename="03-write-meta.json",
        phase="write",
        agent="codex (gpt-5.4)",
        prompt_chars=1900,
        response_chars=380,
    )

    summary = cost_report.build_cost_summary()
    by_phase = {item["name"]: item for item in summary["per_phase"]}

    assert by_phase["write"]["calls"] == 2
    assert by_phase["write"]["prompt_tokens_est"] == round(3800 / 3.8) + round(1900 / 3.8)
    assert by_phase["review"]["response_tokens_est"] == round(190 / 3.8)


def test_since_filter_uses_meta_file_mtime(tmp_path, monkeypatch):
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", tmp_path)
    _write_meta(
        tmp_path,
        level="a1",
        slug="old",
        filename="01-write-meta.json",
        phase="write",
        agent="codex (gpt-5.4)",
        prompt_chars=3800,
        response_chars=380,
        mtime=datetime(2026, 3, 20, tzinfo=UTC),
    )
    _write_meta(
        tmp_path,
        level="a1",
        slug="new",
        filename="02-write-meta.json",
        phase="write",
        agent="codex (gpt-5.4)",
        prompt_chars=1900,
        response_chars=190,
        mtime=datetime(2026, 4, 10, tzinfo=UTC),
    )

    summary = cost_report.build_cost_summary(since=datetime(2026, 4, 1, tzinfo=UTC))

    assert summary["records_total"] == 1
    assert summary["top_modules"][0]["name"] == "a1/new"


def test_json_output_is_valid_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", tmp_path)
    _write_meta(
        tmp_path,
        level="a1",
        slug="json-demo",
        filename="01-write-meta.json",
        phase="write",
        agent="codex (gpt-5.4)",
        prompt_chars=3800,
        response_chars=380,
    )

    assert cost_report.main(["--all", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["totals"]["prompt_tokens_est"] > 0
    assert payload["records_total"] == 1


def test_cost_report_smoke_runs_on_repo_data():
    result = subprocess.run(
        [".venv/bin/python", "scripts/analytics/cost_report.py", "--all"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Estimated cost report" in result.stdout
