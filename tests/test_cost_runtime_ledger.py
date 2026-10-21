"""Tests for runtime-ledger empty-state signals in cost windows (#7086)."""

from __future__ import annotations

import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

import scripts.analytics.cost_report as cost_report

pytestmark = pytest.mark.reads_content

_NOW = datetime(2026, 8, 22, 12, 0, 0, tzinfo=UTC)


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
            "secret_redactor" if scripts_on_path else "scripts.secret_redactor",
            "agent_runtime.usage" if scripts_on_path else "scripts.agent_runtime.usage",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
