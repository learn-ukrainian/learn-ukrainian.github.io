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
WORK = DASH / "work.html"
ORIENT = DASH / "orient.html"
INDEX = DASH / "index.html"


def test_delegate_idle_copy_distinguishes_now_from_today():
    """#7078: 'No active tasks' must not be the hero when work finished today."""
    html = DELEGATE.read_text(encoding="utf-8")
    assert "Nothing running right now" in html
    assert "finished today" in html
    assert "No tasks today" in html
    assert "taskTouchedToday" in html
    assert "renderActive(active, finishedToday)" in html
    # The unqualified hero lie is gone.
    assert '<div class="empty">No active tasks</div>' not in html


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


def test_work_attention_shows_loading_skeleton():
    """#7078: attention list shows a skeleton during projection load, not a blank box."""
    html = WORK.read_text(encoding="utf-8")
    assert "skeleton-row" in html
    assert "skeleton-bar" in html
    assert "skeleton-pulse" in html
    assert "Loading work projection" in html
    assert 'aria-busy="true"' in html
    assert "removeAttribute('aria-busy')" in html
    # Reduced-motion users get no shimmer (global guard already present).
    assert "prefers-reduced-motion" in html


def test_orient_crosschecks_live_delegate_before_empty_claim():
    """#7078: orient must not claim 'No recent tasks' while /api/delegate/tasks is non-empty."""
    html = ORIENT.read_text(encoding="utf-8")
    assert "/api/delegate/tasks?limit=5" in html
    assert "await renderDelegate(" in html
    # The bare unqualified claim is no longer renderable.
    assert '<div class="empty">No recent tasks</div>' not in html
    assert "delegate.html" in html


def test_index_delegate_card_reports_finished_today():
    """#7078: launchpad delegate card must not read as no work today."""
    html = INDEX.read_text(encoding="utf-8")
    assert "finished today" in html
    assert "taskTouchedToday" in html
    assert "card-stat-delegate" in html
