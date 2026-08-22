"""Dedicated tests for #7089 orient runtime cards.

Proves:
1. One card per inventory agent dynamically extracted (no hardcoded list).
2. Per-agent outcome counts (no echoing global outcomes on every card).
3. Retired agent 'gemini' is not presented as live.
4. Agents with headroom keys (cursor, kimi, grok, deepseek, agy, etc.) are included.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ORIENT = ROOT / "dashboards" / "orient.html"


def _extract_runtime_js_block() -> str:
    html = ORIENT.read_text(encoding="utf-8")
    start = html.find("function escapeHtml(")
    end = html.find("async function renderDelegate(")
    if start < 0 or end <= start:
        raise ValueError("Runtime JS block not found in orient.html")
    return html[start:end]


def test_orient_html_does_not_hardcode_agent_trio():
    """#7089: orient.html must not hardcode ['claude', 'gemini', 'codex']."""
    html = ORIENT.read_text(encoding="utf-8")
    assert "['claude', 'gemini', 'codex']" not in html
    assert '["claude", "gemini", "codex"]' not in html
    assert "extractRuntimeAgents" in html
    assert "getAgentHeadroom" in html
    assert "getAgentOutcomes" in html


def test_orient_html_marks_gemini_as_retired():
    """#7089: gemini is retired in /api/fleet/agents and must not be presented as live."""
    html = ORIENT.read_text(encoding="utf-8")
    assert "RETIRED_AGENTS" in html
    assert "'gemini'" in html or '"gemini"' in html


def _eval_orient_runtime_js(runtime_payload: dict) -> dict:
    if shutil.which("node") is None:
        pytest.skip("node required for JS execution test")
    runtime_json = json.dumps(runtime_payload)
    js_block = _extract_runtime_js_block()

    script = f"""
    let domContent = "";
    const document = {{
      getElementById(id) {{
        return {{
          set innerHTML(val) {{ domContent = val; }},
          get innerHTML() {{ return domContent; }},
          textContent: ""
        }};
      }},
      createElement(tag) {{
        return {{
          set textContent(val) {{ this._text = val; }},
          get innerHTML() {{ return String(this._text || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }}
        }};
      }}
    }};

    {js_block}

    const payload = {runtime_json};
    renderRuntime(payload);
    console.log(JSON.stringify({{ html: domContent }}));
    """
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return json.loads(result.stdout)


def test_orient_runtime_cards_inventory_agents_and_gemini_retired():
    """#7089: one card per inventory agent; gemini retired not presented as live."""
    payload = {
        "agents": ["claude", "codex", "cursor", "kimi", "grok", "deepseek", "agy", "gemini"],
        "headroom": {
            "claude": True,
            "codex": True,
            "cursor": True,
            "kimi": True,
            "grok": True,
            "deepseek": True,
            "agy": True,
            "gemini": True,
        },
    }
    out = _eval_orient_runtime_js(payload)
    html = out["html"]

    # Each live agent has a card title
    for agent in ("claude", "codex", "cursor", "kimi", "grok", "deepseek", "agy"):
        assert f"<div class=\"title\">{agent}</div>" in html

    # Retired agent gemini must NOT be present as a live card
    assert "<div class=\"title\">gemini</div>" not in html


def test_orient_runtime_cards_headroom_keys_inclusion():
    """#7089: cursor/kimi/grok/deepseek/agy included when headroom keys exist."""
    payload = {
        "headroom": {
            "cursor": True,
            "kimi": False,
            "grok": True,
            "deepseek": False,
            "agy": True,
        },
    }
    out = _eval_orient_runtime_js(payload)
    html = out["html"]

    assert "<div class=\"title\">cursor</div>" in html
    assert "<div class=\"title\">kimi</div>" in html
    assert "<div class=\"title\">grok</div>" in html
    assert "<div class=\"title\">deepseek</div>" in html
    assert "<div class=\"title\">agy</div>" in html

    # Check green vs red headroom indicators
    # cursor is True (green check)
    assert re.search(r"<div class=\"title\">cursor</div>\s*<div class=\"big\" style=\"color:var\(--green\)\">&#10003;</div>", html)
    # kimi is False (red cross)
    assert re.search(r"<div class=\"title\">kimi</div>\s*<div class=\"big\" style=\"color:var\(--red\)\">&#10007;</div>", html)


def test_orient_runtime_cards_per_agent_outcome_counts():
    """#7089: per-agent outcome counts; cards do not reprint global recent_outcomes."""
    payload = {
        "agents": ["claude", "codex", "cursor"],
        "headroom": {"claude": True, "codex": True, "cursor": True},
        "recent_outcomes": {"ok": 999, "error": 888, "rate_limited": 777},
        "by_agent": {
            "claude": {"ok": 12, "error": 1, "rate_limited": 0},
            "codex": {"ok": 3, "error": 0, "rate_limited": 2},
        },
    }
    out = _eval_orient_runtime_js(payload)
    html = out["html"]

    # Global 999/888/777 must not be reprinted in pills
    assert "ok 999" not in html
    assert "error 888" not in html
    assert "rate 777" not in html

    # Claude card has ok 12, error 1, rate 0
    assert re.search(
        r"<div class=\"title\">claude</div>[\s\S]*?<span class=\"pill ok\">ok 12</span>[\s\S]*?<span class=\"pill err\">error 1</span>[\s\S]*?<span class=\"pill warn\">rate 0</span>",
        html,
    )

    # Codex card has ok 3, error 0, rate 2
    assert re.search(
        r"<div class=\"title\">codex</div>[\s\S]*?<span class=\"pill ok\">ok 3</span>[\s\S]*?<span class=\"pill err\">error 0</span>[\s\S]*?<span class=\"pill warn\">rate 2</span>",
        html,
    )

    # Cursor card has no recorded outcomes -> 0s
    assert re.search(
        r"<div class=\"title\">cursor</div>[\s\S]*?<span class=\"pill ok\">ok 0</span>[\s\S]*?<span class=\"pill err\">error 0</span>[\s\S]*?<span class=\"pill warn\">rate 0</span>",
        html,
    )


def test_orient_runtime_cards_empty_runtime():
    """#7089: empty runtime shows empty message."""
    out = _eval_orient_runtime_js({})
    assert "<div class=\"empty\">No runtime agents</div>" in out["html"]
