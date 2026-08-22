"""Tests for runtime-ledger empty-state signals in cost windows (#7086)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import scripts.analytics.cost_report as cost_report
from tests.project_python import project_python

_NOW = datetime(2026, 8, 22, 12, 0, 0, tzinfo=UTC)


def _write_meta(root: Path, *, level: str = "a1", slug: str = "my-family") -> None:
    dispatch_dir = root / level / "orchestration" / slug / "dispatch"
    dispatch_dir.mkdir(parents=True, exist_ok=True)
    (dispatch_dir / "01-write-meta.json").write_text(
        json.dumps(
            {
                "timestamp": "2026-08-20T12:00:00Z",
                "phase": "write",
                "agent": "kimi (k2)",
                "model": "k2",
                "ok": True,
                "returncode": 0,
                "prompt_chars": 3800,
                "response_chars": 380,
                "prompt_tokens_est": 1000,
                "response_tokens_est": 100,
                "duration_s": 9.0,
            }
        ),
        encoding="utf-8",
    )


def _write_usage_rows(usage_dir: Path, *, day: str, rows: int, agent: str = "kimi") -> None:
    usage_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "ts": f"{day}T08:{32 + idx:02d}:00+00:00",
                "agent": agent,
                "entrypoint": "delegate",
                "outcome": "ok",
                "duration_s": 9.0,
                "tokens": None,
            }
        )
        for idx in range(rows)
    ]
    (usage_dir / f"usage_{agent}-delegate_{day}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_empty_ledger_with_runtime_rows_flags_ledger_empty(tmp_path, monkeypatch):
    curriculum = tmp_path / "curriculum"
    usage_dir = tmp_path / "api_usage"
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", curriculum)
    monkeypatch.setattr(cost_report, "API_USAGE_DIR", usage_dir)
    curriculum.mkdir()
    _write_usage_rows(usage_dir, day="2026-08-22", rows=28)

    payload = cost_report.build_cost_windows(now=_NOW)

    week = payload["windows"]["last_7_days"]
    assert week["records_total"] == 0
    assert week["totals"]["cost_usd_est"] == 0.0
    assert week["runtime_calls_total"] == 28
    assert week["ledger_empty"] is True
    assert any("ledger is empty" in warning for warning in week["warnings"])
    assert payload["windows"]["last_30_days"]["runtime_calls_total"] == 28
    assert payload["windows"]["all_time"]["runtime_calls_total"] == 28
    assert payload["windows"]["all_time"]["ledger_empty"] is True


def test_populated_ledger_is_not_flagged(tmp_path, monkeypatch):
    curriculum = tmp_path / "curriculum"
    usage_dir = tmp_path / "api_usage"
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", curriculum)
    monkeypatch.setattr(cost_report, "API_USAGE_DIR", usage_dir)
    _write_meta(curriculum)
    _write_usage_rows(usage_dir, day="2026-08-22", rows=5)

    payload = cost_report.build_cost_windows(now=_NOW)

    week = payload["windows"]["last_7_days"]
    assert week["records_total"] == 1
    assert week["runtime_calls_total"] == 5
    assert week["ledger_empty"] is False
    assert not any("ledger is empty" in warning for warning in week["warnings"])


def test_empty_everything_is_not_flagged(tmp_path, monkeypatch):
    curriculum = tmp_path / "curriculum"
    usage_dir = tmp_path / "api_usage"
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", curriculum)
    monkeypatch.setattr(cost_report, "API_USAGE_DIR", usage_dir)
    curriculum.mkdir()

    payload = cost_report.build_cost_windows(now=_NOW)

    for window in payload["windows"].values():
        assert window["runtime_calls_total"] == 0
        assert window["ledger_empty"] is False


def test_missing_usage_dir_is_not_flagged(tmp_path, monkeypatch):
    curriculum = tmp_path / "curriculum"
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", curriculum)
    monkeypatch.setattr(cost_report, "API_USAGE_DIR", tmp_path / "does-not-exist")
    curriculum.mkdir()

    payload = cost_report.build_cost_windows(now=_NOW)

    assert payload["windows"]["last_7_days"]["runtime_calls_total"] == 0
    assert payload["windows"]["last_7_days"]["ledger_empty"] is False


def test_old_usage_rows_only_count_in_all_time(tmp_path, monkeypatch):
    curriculum = tmp_path / "curriculum"
    usage_dir = tmp_path / "api_usage"
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", curriculum)
    monkeypatch.setattr(cost_report, "API_USAGE_DIR", usage_dir)
    curriculum.mkdir()
    _write_usage_rows(usage_dir, day="2026-07-01", rows=10)
    _write_usage_rows(usage_dir, day="2026-08-10", rows=3)

    payload = cost_report.build_cost_windows(now=_NOW)

    assert payload["windows"]["last_7_days"]["runtime_calls_total"] == 0
    assert payload["windows"]["last_7_days"]["ledger_empty"] is False
    assert payload["windows"]["last_30_days"]["runtime_calls_total"] == 3
    assert payload["windows"]["last_30_days"]["ledger_empty"] is True
    assert payload["windows"]["all_time"]["runtime_calls_total"] == 13


def test_malformed_usage_lines_are_skipped(tmp_path, monkeypatch):
    curriculum = tmp_path / "curriculum"
    usage_dir = tmp_path / "api_usage"
    monkeypatch.setattr(cost_report, "CURRICULUM_ROOT", curriculum)
    monkeypatch.setattr(cost_report, "API_USAGE_DIR", usage_dir)
    curriculum.mkdir()
    usage_dir.mkdir()
    (usage_dir / "usage_kimi-delegate_2026-08-22.jsonl").write_text(
        '{"agent": "kimi", "outcome": "ok"}\nnot-json\n\n[]\n', encoding="utf-8"
    )

    payload = cost_report.build_cost_windows(now=_NOW)

    assert payload["windows"]["last_7_days"]["runtime_calls_total"] == 1
    assert payload["windows"]["last_7_days"]["ledger_empty"] is True


def test_cost_report_cli_still_runs():
    result = subprocess.run(
        [str(project_python()), "scripts/analytics/cost_report.py", "--all", "--json"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert "records_total" in payload


def test_cost_html_hero_never_shows_zero_dollar_when_ledger_empty():
    """renderSummary must not present a $0 week when ledger_empty (#7086)."""
    html_path = Path(__file__).resolve().parent.parent / "dashboards" / "cost.html"
    html = html_path.read_text(encoding="utf-8")
    helpers = html[html.index("let activeWindow") : html.index("function renderWindow")]
    script = f"""
    {helpers}
    const stubs = {{ summary: {{ innerHTML: '' }} }};
    global.document = {{ getElementById: (id) => stubs[id] }};
    renderSummary({{ windows: {{ last_7_days: {{
      ledger_empty: true,
      runtime_calls_total: 28,
      totals: {{ cost_usd_est: 0, prompt_tokens_est: 0, response_tokens_est: 0, calls: 0 }},
    }} }} }});
    const emptyHero = stubs.summary.innerHTML;
    renderSummary({{ windows: {{ last_7_days: {{
      ledger_empty: false,
      runtime_calls_total: 28,
      totals: {{ cost_usd_est: 12.34, prompt_tokens_est: 1000, response_tokens_est: 100, calls: 3 }},
    }} }} }});
    console.log(JSON.stringify({{ emptyHero, populatedHero: stubs.summary.innerHTML }}));
    """
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True, timeout=30)
    output = json.loads(result.stdout)

    assert "~$0.00" not in output["emptyHero"]
    assert 'class="value"' in output["emptyHero"]
    assert "ledger empty" in output["emptyHero"]
    assert "~$12.34" in output["populatedHero"]
