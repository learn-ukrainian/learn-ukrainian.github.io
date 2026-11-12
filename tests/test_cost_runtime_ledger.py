"""Tests for runtime-ledger empty-state signals in cost windows (#7086)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import lu_machinery.telemetry.cost_report as cost_report
import pytest

pytestmark = pytest.mark.reads_content

_NOW = datetime(2026, 8, 22, 12, 0, 0, tzinfo=UTC)


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


def test_empty_ledger_with_runtime_rows_flags_ledger_empty(tmp_path):
    curriculum = tmp_path / "curriculum"
    usage_dir = tmp_path / "api_usage"
    curriculum.mkdir()
    _write_usage_rows(usage_dir, day="2026-08-22", rows=28)

    payload = cost_report.build_cost_windows(root=curriculum, usage_dir=usage_dir, now=_NOW)

    week = payload["windows"]["last_7_days"]
    assert week["records_total"] == 0
    assert week["totals"]["cost_usd_est"] == 0.0
    assert week["runtime_calls_total"] == 28
    assert week["ledger_empty"] is True
    assert any("ledger is empty" in warning for warning in week["warnings"])
    assert payload["windows"]["last_30_days"]["runtime_calls_total"] == 28
    assert payload["windows"]["all_time"]["runtime_calls_total"] == 28
    assert payload["windows"]["all_time"]["ledger_empty"] is True


def test_malformed_usage_lines_are_skipped(tmp_path):
    curriculum = tmp_path / "curriculum"
    usage_dir = tmp_path / "api_usage"
    curriculum.mkdir()
    usage_dir.mkdir()
    (usage_dir / "usage_kimi-delegate_2026-08-22.jsonl").write_text(
        '{"agent": "kimi", "outcome": "ok"}\nnot-json\n\n[]\n', encoding="utf-8"
    )

    payload = cost_report.build_cost_windows(root=curriculum, usage_dir=usage_dir, now=_NOW)

    assert payload["windows"]["last_7_days"]["runtime_calls_total"] == 1
    assert payload["windows"]["last_7_days"]["ledger_empty"] is True
    for window in payload["windows"].values():
        assert window["unreadable"] == {"files": 0, "lines": 2, "records": 0}
        assert any("unreadable usage records" in warning and "'lines': 2" in warning for warning in window["warnings"])


@pytest.mark.parametrize("scripts_on_path", [False, True])
def test_usage_import_preserves_redactor_identity(scripts_on_path):
    root = Path(__file__).resolve().parent.parent
    probe = """
import importlib
import sys
sys.path.insert(0, sys.argv[1])
redactor = importlib.import_module(sys.argv[2])
usage = importlib.import_module(sys.argv[3])
assert usage.redact_text is redactor.redact_text
assert usage.redact_value is redactor.redact_value
"""
    result = subprocess.run(
        [
            sys.executable, "-I", "-c", probe,
            str(root / "scripts" if scripts_on_path else root),
            "secret_redactor" if scripts_on_path else "lu_machinery.secret_redactor",
            "agent_runtime.usage" if scripts_on_path else "lu_machinery.agent_runtime.usage",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
