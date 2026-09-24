"""Tests for DeepSeekAdapter — the OpenCode first-party dispatch default.

Operator 2026-08-13: DeepSeek dispatch routes through opencode to
first-party ``deepseek/*`` (api.deepseek.com) with ``--variant high`` by
default (#8514: provider id ``deepseek``, not the retired ``deepseek-direct``).
The Hermes adapter remains for ``ask-hermes`` only and must not appear in the
default dispatch command. First-party DeepSeek is China-hosted → CI refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

from agent_runtime.adapters.deepseek import DeepSeekAdapter
from agent_runtime.routes import DEEPSEEK_FIRST_PARTY_FORBIDDEN_MARKER

FAKE_OPENCODE = "/usr/local/bin/opencode"


def _build(prompt: str, tmp_path: Path, **kw):
    with patch("agent_runtime.adapters.deepseek.shutil.which", return_value=FAKE_OPENCODE):
        return DeepSeekAdapter().build_invocation(
            prompt=prompt,
            mode=kw.pop("mode", "read-only"),
            cwd=tmp_path,
            model=kw.pop("model", None),
            task_id=kw.pop("task_id", None),
            session_id=kw.pop("session_id", None),
            tool_config=kw.pop("tool_config", None),
            effort=kw.pop("effort", None),
        )


def test_default_dispatch_plan_is_opencode_first_party_flash_at_high(tmp_path):
    """Omitted --model/--effort → opencode run --model
    deepseek/deepseek-flash --variant high; no hermes anywhere."""
    plan = _build("Review this diff.", tmp_path)

    assert plan.cmd[0] == FAKE_OPENCODE
    assert plan.cmd[1] == "run"
    assert plan.cmd[plan.cmd.index("--model") + 1] == "deepseek/deepseek-flash"
    # NDJSON event stream is the only stdout surface that survives the
    # runner's PTY spawn (#8514: opencode 1.18.x writes the formatted
    # transcript to stderr and leaves stdout empty under a TTY).
    assert plan.cmd[plan.cmd.index("--format") + 1] == "json"
    assert plan.cmd[plan.cmd.index("--variant") + 1] == "high"
    assert plan.cmd[-2] == "--"
    assert plan.cmd[-1] == "Review this diff."
    assert "hermes" not in " ".join(plan.cmd).lower()
    assert plan.env_overrides.get("OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX") == "131072"


def _ndjson_events(*events: dict) -> str:
    return "\n".join(json.dumps(e) for e in events)


def _text_event(text: str, session: str = "ses_x") -> dict:
    return {"type": "text", "sessionID": session, "part": {"type": "text", "text": text}}


def test_parse_response_extracts_last_assistant_text_from_ndjson(tmp_path):
    """--format json NDJSON: the reply of record is the LAST assistant
    message, not the whole event blob or the preamble narration (#8514)."""
    plan = _build("x", tmp_path)
    stdout = _ndjson_events(
        {"type": "step_start", "sessionID": "ses_x", "part": {"type": "step-start"}},
        _text_event("Let me check…"),
        {
            "type": "tool_use",
            "sessionID": "ses_x",
            "part": {"type": "tool", "tool": "read", "state": {"status": "completed"}},
        },
        _text_event("OK"),
        {"type": "step_finish", "sessionID": "ses_x", "part": {"type": "step_finish", "reason": "stop"}},
    )

    result = DeepSeekAdapter().parse_response(stdout=stdout, stderr="", returncode=0, plan=plan)

    assert result.ok is True
    assert result.response == "OK"
    assert result.session_id == "ses_x"


def test_parse_response_survives_pty_empty_stdout(tmp_path):
    """Edge case from #8514: under a PTY, opencode 1.18.x leaves stdout empty
    and writes banner+reply to stderr — no text means the parse fails closed
    instead of inventing a response."""
    plan = _build("x", tmp_path)
    result = DeepSeekAdapter().parse_response(
        stdout="",
        stderr="\x1b[0m\n> build · deepseek-flash\n\x1b[0m\nOK\n\x1b[0m",
        returncode=0,
        plan=plan,
    )

    assert result.ok is False
    assert result.response == ""
    assert result.stderr_excerpt


def test_explicit_model_and_effort_overrides_win(tmp_path):
    """--model deepseek-v4-pro routes to the first-party Pro pin (reachable
    only via explicit override); --effort max maps to --variant max."""
    plan = _build("Deep pass.", tmp_path, model="deepseek-v4-pro", effort="max")

    assert plan.cmd[plan.cmd.index("--model") + 1] == "deepseek/deepseek-v4-pro"
    assert plan.cmd[plan.cmd.index("--variant") + 1] == "max"


def test_retired_v4_identity_cannot_launch_moving_flash_alias(tmp_path):
    with pytest.raises(ValueError, match="retired for historical records"):
        _build("Check.", tmp_path, model="deepseek-v4-flash")


def test_cached_alias_drift_refuses_new_flash_dispatch(tmp_path):
    with patch(
        "agent_runtime.adapters.deepseek._cached_flash_name",
        return_value="DeepSeek V4.2 Flash",
    ), pytest.raises(ValueError, match="alias drift"):
        _build("Check.", tmp_path)


def test_provider_prefixed_model_passes_through(tmp_path):
    plan = _build("Check.", tmp_path, model="deepseek/deepseek-flash")

    assert plan.cmd[plan.cmd.index("--model") + 1] == "deepseek/deepseek-flash"


def test_mode_mapping_adds_auto_for_write_modes(tmp_path):
    assert "--auto" not in _build("x", tmp_path, mode="read-only").cmd
    assert "--auto" in _build("x", tmp_path, mode="workspace-write").cmd
    assert "--auto" in _build("x", tmp_path, mode="danger").cmd

    with pytest.raises(ValueError, match="unsupported mode"):
        _build("x", tmp_path, mode="invalid_mode")


def test_trail_isolation_is_refused(tmp_path):
    from agent_runtime.trail_isolation import TrailIsolationError

    with pytest.raises(TrailIsolationError, match="trail isolation refused for DeepSeek"):
        _build("x", tmp_path, tool_config={"trail_isolation": True})


def test_ci_refusal_for_first_party_route(tmp_path, monkeypatch):
    """The same first-party CI refuse as the Hermes route must hold."""
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    with pytest.raises(ValueError, match=DEEPSEEK_FIRST_PARTY_FORBIDDEN_MARKER):
        _build("Should fail in CI", tmp_path)
