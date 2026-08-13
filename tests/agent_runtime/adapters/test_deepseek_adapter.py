"""Tests for DeepSeekAdapter — the OpenCode first-party dispatch default.

Operator 2026-08-13: DeepSeek dispatch routes through opencode to
``deepseek-direct/*`` (api.deepseek.com) with ``--variant high`` by default.
The Hermes adapter remains for ``ask-hermes`` only and must not appear in the
default dispatch command. First-party DeepSeek is China-hosted → CI refused.
"""

from __future__ import annotations

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
    deepseek-direct/deepseek-v4-flash --variant high; no hermes anywhere."""
    plan = _build("Review this diff.", tmp_path)

    assert plan.cmd[0] == FAKE_OPENCODE
    assert plan.cmd[1] == "run"
    assert plan.cmd[plan.cmd.index("--model") + 1] == "deepseek-direct/deepseek-v4-flash"
    assert plan.cmd[plan.cmd.index("--variant") + 1] == "high"
    assert plan.cmd[-2] == "--"
    assert plan.cmd[-1] == "Review this diff."
    assert "hermes" not in " ".join(plan.cmd).lower()
    assert plan.env_overrides.get("OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX") == "131072"


def test_explicit_model_and_effort_overrides_win(tmp_path):
    """--model deepseek-v4-pro routes to the first-party Pro pin (reachable
    only via explicit override); --effort max maps to --variant max."""
    plan = _build("Deep pass.", tmp_path, model="deepseek-v4-pro", effort="max")

    assert plan.cmd[plan.cmd.index("--model") + 1] == "deepseek-direct/deepseek-v4-pro"
    assert plan.cmd[plan.cmd.index("--variant") + 1] == "max"


def test_provider_prefixed_model_passes_through(tmp_path):
    plan = _build("Check.", tmp_path, model="deepseek-direct/deepseek-v4-flash")

    assert plan.cmd[plan.cmd.index("--model") + 1] == "deepseek-direct/deepseek-v4-flash"


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
