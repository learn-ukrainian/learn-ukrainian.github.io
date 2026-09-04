"""Dedicated tests for #7089 orient runtime cards.

Proves:
1. One card per inventory agent dynamically extracted (no hardcoded list).
2. Per-agent outcome counts (no echoing global outcomes on every card).
3. Retired agents 'gemini' and 'glm' are not presented as live.
4. Agents with headroom keys (cursor, kimi, grok, deepseek, agy, etc.) are included.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ORIENT = ROOT / "dashboards" / "orient.html"


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
    patched_ctx = replace(base_ctx, roots=replace(base_ctx.roots, batch_state_dir=Path(batch_state_dir)))
    monkeypatch.setattr(monitor_context, "production_context", lambda ctx=None: patched_ctx)
    monkeypatch.setattr(runtime_router, "production_context", lambda ctx=None: patched_ctx)
    return patched_ctx


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


def test_orient_html_marks_retired_cli_lanes():
    """gemini/glm are permanently retired and must not be presented as live."""
    html = ORIENT.read_text(encoding="utf-8")
    assert "RETIRED_AGENTS" in html
    assert re.search(
        r"RETIRED_AGENTS\s*=\s*new Set\(\[[^\]]*'(?:gemini|glm)'[^\]]*'(?:gemini|glm)'[^\]]*\]\)",
        html,
    )


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


def test_orient_runtime_cards_inventory_agents_and_retired_lanes_hidden():
    """#7089: one card per inventory agent; gemini/glm not presented as live."""
    payload = {
        "agents": ["claude", "codex", "cursor", "kimi", "grok", "deepseek", "agy", "gemini", "glm"],
        "headroom": {
            "claude": True,
            "codex": True,
            "cursor": True,
            "kimi": True,
            "grok": True,
            "deepseek": True,
            "agy": True,
            "gemini": True,
            "glm": True,
        },
        "by_agent": {
            "glm": {"ok": 4, "error": 0, "rate_limited": 0},
            "gemini": {"ok": 2, "error": 0, "rate_limited": 0},
        },
    }
    out = _eval_orient_runtime_js(payload)
    html = out["html"]

    # Each live agent has a card title
    for agent in ("claude", "codex", "cursor", "kimi", "grok", "deepseek", "agy"):
        assert f"<div class=\"title\">{agent}</div>" in html

    # Retired CLI seats must NOT reappear from agents/headroom/by_agent history
    assert "<div class=\"title\">gemini</div>" not in html
    assert "<div class=\"title\">glm</div>" not in html


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


def test_orient_runtime_cards_real_collector_payload_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """#7089: API-to-render contract test using live collector output with non-zero per-agent outcomes."""
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

    # Obtain real payload directly from collector
    real_payload = api_main._collect_runtime_orient_data()
    assert real_payload["recent_outcomes"]["ok"] == 4

    # Render via orient JS
    out = _eval_orient_runtime_js(real_payload)
    html = out["html"]

    # Global total ok (4) must not be echoed on individual cards
    # Claude card has ok 2, error 1, rate 0
    assert re.search(
        r"<div class=\"title\">claude</div>[\s\S]*?<span class=\"pill ok\">ok 2</span>[\s\S]*?<span class=\"pill err\">error 1</span>[\s\S]*?<span class=\"pill warn\">rate 0</span>",
        html,
    )
    # Codex card has ok 1, error 0, rate 1
    assert re.search(
        r"<div class=\"title\">codex</div>[\s\S]*?<span class=\"pill ok\">ok 1</span>[\s\S]*?<span class=\"pill err\">error 0</span>[\s\S]*?<span class=\"pill warn\">rate 1</span>",
        html,
    )
    # Grok card has ok 1, error 0, rate 0
    assert re.search(
        r"<div class=\"title\">grok</div>[\s\S]*?<span class=\"pill ok\">ok 1</span>[\s\S]*?<span class=\"pill err\">error 0</span>[\s\S]*?<span class=\"pill warn\">rate 0</span>",
        html,
    )
    # Agents without usage today show ok 0, error 0, rate 0
    for idle_agent in ("cursor", "agy"):
        if idle_agent in real_payload.get("agents", []):
            assert re.search(
                rf"<div class=\"title\">{idle_agent}</div>[\s\S]*?<span class=\"pill ok\">ok 0</span>[\s\S]*?<span class=\"pill err\">error 0</span>[\s\S]*?<span class=\"pill warn\">rate 0</span>",
                html,
            )

    # Retired CLI seats are not rendered
    assert "<div class=\"title\">gemini</div>" not in html
    assert "<div class=\"title\">glm</div>" not in html


def test_orient_endpoint_to_render_contract(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """#7089: End-to-end GET /api/orient response rendered into HTML cards."""
    from datetime import UTC, datetime, timedelta

    from fastapi.testclient import TestClient

    import scripts.api.main as api_main
    import scripts.api.runtime_router as runtime_router

    del runtime_router, monkeypatch  # #7494: ctx is injected, not module-patched
    from scripts.api.monitor_context import fixture_context

    # #7494: the orient handler now threads the APP'S context into every
    # collector, so this end-to-end test builds a fixture app whose
    # batch_state root holds the seeded usage file — module-level patching
    # of the production fallback no longer reaches request handling.
    usage_dir = tmp_path / "batch_state" / "api_usage"
    today = datetime.now(UTC)

    _write_usage_file(
        usage_dir / f"usage_claude-dispatch_{today:%Y-%m-%d}.jsonl",
        [
            {"ts": (today - timedelta(minutes=10)).isoformat(), "agent": "claude", "entrypoint": "dispatch", "model": "claude-sonnet-4-6", "duration_s": 5.0, "outcome": "ok"},
        ],
    )

    client = TestClient(api_main.create_app(fixture_context(tmp_path)))
    response = client.get("/api/orient?sections=runtime&fresh=true")
    assert response.status_code == 200
    data = response.json()
    assert "runtime" in data
    runtime_data = data["runtime"]

    # Verify collector contract on live endpoint
    assert "by_agent" in runtime_data
    assert runtime_data["by_agent"]["claude"]["ok"] == 1
    assert runtime_data["recent_outcomes"]["ok"] == 1

    out = _eval_orient_runtime_js(runtime_data)
    html = out["html"]

    assert re.search(
        r"<div class=\"title\">claude</div>[\s\S]*?<span class=\"pill ok\">ok 1</span>[\s\S]*?<span class=\"pill err\">error 0</span>[\s\S]*?<span class=\"pill warn\">rate 0</span>",
        html,
    )
    assert "<div class=\"title\">gemini</div>" not in html
    assert "<div class=\"title\">glm</div>" not in html
