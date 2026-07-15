"""Canonical-normalize + permanent-alias tests for the native grok seat rename.

Covers the load-bearing migration contract:
- ``grok-build`` permanently aliases to ``grok``
- Hermes demoted to ``grok-hermes``
- ``GROK_AGENT=1`` autodetect returns canonical ``grok``
- V7 ``grok-tools`` maps explicitly to hermes (not split-prefix native)
- codex ``--print-config`` sha is unchanged by this rename
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"


@pytest.fixture(autouse=True)
def _scripts_on_path(monkeypatch):
    import sys

    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))


def test_normalize_seat_maps_alias_and_hermes():
    from agent_runtime.agent_identity import (
        HERMES_GROK_SEAT,
        NATIVE_GROK_SEAT,
        is_hermes_grok_seat,
        is_native_grok_seat,
        normalize_seat,
        seat_read_aliases,
        tools_writer_runtime_agent,
    )

    assert normalize_seat("grok-build") == NATIVE_GROK_SEAT
    assert normalize_seat("GROK-BUILD") == NATIVE_GROK_SEAT
    assert normalize_seat("grok") == NATIVE_GROK_SEAT
    assert normalize_seat("grok-hermes") == HERMES_GROK_SEAT
    assert is_native_grok_seat("grok-build")
    assert is_native_grok_seat("grok")
    assert not is_native_grok_seat("grok-hermes")
    assert is_hermes_grok_seat("grok-hermes")
    assert seat_read_aliases("grok") == ("grok", "grok-build")
    assert seat_read_aliases("grok-build") == ("grok", "grok-build")
    assert tools_writer_runtime_agent("grok-tools") == HERMES_GROK_SEAT
    assert tools_writer_runtime_agent("claude-tools") == "claude"


def test_tool_config_canonical_order_prefers_native_over_hermes_prefix():
    from agent_runtime.tool_config import _canonical_agent_name

    assert _canonical_agent_name("grok-build") == "grok"
    assert _canonical_agent_name("grok-build-review") == "grok"
    assert _canonical_agent_name("grok") == "grok"
    assert _canonical_agent_name("grok-hermes") == "grok-hermes"
    assert _canonical_agent_name("grok-hermes-extra") == "grok-hermes"


def test_grok_agent_env_autodetect_returns_canonical(monkeypatch):
    from ai_agent_bridge import _cli

    monkeypatch.delenv("SESSION_HANDOFF_AGENT", raising=False)
    monkeypatch.delenv("CLAUDE_AGENT_NAME", raising=False)
    monkeypatch.delenv("CODEX_SESSION", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS", raising=False)
    monkeypatch.delenv("GEMINI_SESSION", raising=False)
    monkeypatch.setenv("GROK_AGENT", "1")
    assert _cli._detect_caller_identity_from_env() == "grok"


def test_grok_agent_non_sentinel_does_not_false_positive(monkeypatch):
    from ai_agent_bridge import _cli

    for key in (
        "SESSION_HANDOFF_AGENT",
        "CLAUDE_AGENT_NAME",
        "CODEX_SESSION",
        "CLAUDE_PROJECT_DIR",
        "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS",
        "GEMINI_SESSION",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GROK_AGENT", "my-custom-agent")
    assert _cli._detect_caller_identity_from_env() is None


def test_budget_agent_key_dual_reads_historical_alias():
    # Import via the scripts package path used by the API app. Avoid bare
    # `api.state_router`, which can resolve to a stale/duplicate module object
    # after other tests insert `scripts/` on sys.path (pre-commit suite order).
    from scripts.api.state_router import _agent_key

    assert _agent_key("grok") == "grok"
    assert _agent_key("grok-build") == "grok"
    assert _agent_key("GROK-BUILD") == "grok"
    # Hermes path must NOT fold into the native subscription bucket.
    assert _agent_key("grok-hermes") is None


def test_codex_print_config_sha_unchanged_by_grok_seat_rename(capsys):
    """Identity rename must not touch codex judge attestation bytes."""
    from audit import layerb_judge_bridge

    assert layerb_judge_bridge.main(["--print-config"]) == 0
    out = capsys.readouterr().out
    import json

    config = json.loads(out)
    assert config["family"] == "codex"
    assert (
        config["config_sha256"]
        == "18a92b5adec75a0ea8dd72c192b7b6663dc611377d13047c569d4d68c5a66a62"
    )


def test_historical_grok_build_transport_string_frozen_in_judge_material():
    """Attestation transport string is immutable provenance — do not rewrite."""
    from audit import layerb_judge_bridge

    cfg = layerb_judge_bridge.BridgeConfig(
        family="grok",
        model="grok-4.5",
        model_version="grok-4.5",
        timeout_seconds=120.0,
    )
    assert cfg.transport == "grok-build-subscription-traced.v1"
    material = cfg.material()
    assert material["transport"] == "grok-build-subscription-traced.v1"
    assert material["family"] == "grok"


def test_no_live_judge_path_selects_hermes_grok_as_default():
    """Default review stall / judge seats prefer native grok, not hermes."""
    from agent_runtime.registry import AGENTS
    from audit.layerb_judge_bridge import BridgeConfig

    # Judge family "grok" is the native-seat judge family (transport string
    # still says grok-build-subscription for frozen provenance).
    native = AGENTS["grok"]
    hermes = AGENTS["grok-hermes"]
    assert "GrokBuildAdapter" in native["adapter"]
    assert "HermesGrokAdapter" in hermes["adapter"]
    # Building a grok-family judge config must not require hermes.
    cfg = BridgeConfig(
        family="grok",
        model="grok-4.5",
        model_version="grok-4.5",
        timeout_seconds=60.0,
    )
    assert "hermes" not in cfg.transport
    assert "grok-build-subscription" in cfg.transport
