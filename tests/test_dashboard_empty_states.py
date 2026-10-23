"""Static + behavioral contracts for #7078 hero empty-states.

Covers delegate.html, work.html, orient.html, and index.html only.
Deliberately separate from tests/test_dashboards.py: no generate_playground_data
imports, no shared mutable surface.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboards"
DELEGATE = DASH / "delegate.html"
def test_delegate_idle_copy_behavioral_js():
    """Evaluate the shipped idle-copy JS in Node against fixed scenarios."""
    if shutil.which("node") is None:
        pytest.skip("node required for JS parity check")
    html_path = json.dumps(str(DELEGATE))
    script = f"""
    const fs = require('fs');
    const html = fs.readFileSync({html_path}, 'utf8');
    const start = html.indexOf('function isToday(');
    const end = html.indexOf('function renderActive(');
    if (start < 0 || end <= start) {{ throw new Error('idle-copy block not found'); }}
    eval(html.slice(start, end));
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 1, 0, 0);
    const old = new Date(now.getFullYear() - 1, 0, 1);
    const out = {{
      emptyToday: idleCopy(0),
      oneToday: idleCopy(1),
      manyToday: idleCopy(3),
      touchedStartedToday: taskTouchedToday({{ started_at: todayStart.toISOString(), duration_s: 60 }}),
      touchedFinishedToday: taskTouchedToday({{
        started_at: new Date(todayStart.getTime() - 3600e3).toISOString(), duration_s: 7200
      }}),
      untouchedOld: taskTouchedToday({{ started_at: old.toISOString(), duration_s: 60 }}),
      untouchedMissing: taskTouchedToday({{ status: 'done' }}),
    }};
    console.log(JSON.stringify(out));
    """
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    out = json.loads(result.stdout)
    assert out["emptyToday"].startswith("No tasks today")
    assert "Nothing running right now" in out["oneToday"]
    assert "1 task finished today" in out["oneToday"]
    assert "3 tasks finished today" in out["manyToday"]
    assert out["touchedStartedToday"] is True
    assert out["touchedFinishedToday"] is True
    assert out["untouchedOld"] is False
    assert out["untouchedMissing"] is False
