"""Tests for ab ask-gemma bridge subcommand (opencode-routed Google Gemma 4 lane).

gemma = Google Gemma 4 31B-it (Apr 2026, Apache-2.0), since 2026-07-07 via
Google AI Studio DIRECT (``google-ais`` provider, $0 — Gemma has NO paid SKU
on the Gemini API; user order + key). Runs TOOLLESS (``--agent chat``): gemma
is not a tool-calling model. The PAID OpenRouter ``-it`` endpoint stays a
``--model`` fallback; OR ``:free`` is pool-starved. A $0 surface-review +
source-constrained wiki-drafting lane to OFFLOAD from metered Claude/Codex.
Western-hosted + permissively licensed → NO egress guard (unlike the
China-hosted GLM lane); the guard-difference is the load-bearing test here.
"""

from unittest.mock import MagicMock, patch

from scripts.ai_agent_bridge._opencode import (
    _CI_ENV_VARS,
    GEMMA_MODEL,
    ask_gemma,
)

# --- constant -------------------------------------------------------------


def test_gemma_model_is_ais_direct_zero_cost_31b():
    # Default pin = Google AI Studio direct (user order 2026-07-07): $0 by
    # construction (no paid Gemma SKU on the Gemini API), on the user's own
    # free-tier quota — deliberately NOT the pool-starved OR ``:free`` variant
    # and NOT the paid OR endpoint (that one is a --model fallback only).
    assert GEMMA_MODEL == "google-ais/gemma-4-31b-it"
    assert not GEMMA_MODEL.endswith(":free")
    assert GEMMA_MODEL.startswith("google-ais/gemma")  # guard allowlist shape


# --- invocation: json format, no variant (not a reasoning-variant model) ---


def test_ask_gemma_uses_json_format_and_no_variant():
    with (
        patch("scripts.ai_agent_bridge._opencode.send_message", return_value=1),
        patch("scripts.ai_agent_bridge._opencode.acknowledge"),
        patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"),
        patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock,
    ):
        run_mock.return_value = MagicMock(
            returncode=0,
            stdout='{"type":"text","part":{"type":"text","text":"привіт"}}',
            stderr="",
        )
        ask_gemma("review this", task_id="t")
        argv = run_mock.call_args[0][0]
        assert argv[:2] == ["/fake/opencode", "run"]
        assert argv[argv.index("--format") + 1] == "json"
        # Gemma is a plain chat model — never pass poolside's --variant.
        assert "--variant" not in argv
        # TOOLLESS seat: ask-gemma must pin the "chat" agent (gemma is not a
        # tool-caller; Google upstreams reject the aggregate tool schema).
        assert argv[argv.index("--agent") + 1] == "chat"
        assert GEMMA_MODEL in argv


# --- model override (churn-resistance; tags drift per model-assignment.md) --


def test_ask_gemma_defaults_to_pinned_model():
    with (
        patch("scripts.ai_agent_bridge._opencode.send_message", return_value=1),
        patch("scripts.ai_agent_bridge._opencode.acknowledge"),
        patch("scripts.ai_agent_bridge._opencode._invoke_opencode", return_value="ok") as inv,
    ):
        ask_gemma("hi", task_id="t")
        assert inv.call_args[0][1] == GEMMA_MODEL


def test_ask_gemma_honors_model_override():
    # e.g. the 26B-A4B MoE (#1 on the lang-uk leaderboard), also $0 on AIS.
    with (
        patch("scripts.ai_agent_bridge._opencode.send_message", return_value=1),
        patch("scripts.ai_agent_bridge._opencode.acknowledge"),
        patch("scripts.ai_agent_bridge._opencode._invoke_opencode", return_value="ok") as inv,
    ):
        ask_gemma("hi", task_id="t", model="google-ais/gemma-4-26b-a4b-it")
        assert inv.call_args[0][1] == "google-ais/gemma-4-26b-a4b-it"


# --- NO egress guard (load-bearing: gemma is Western-hosted, unlike glm) ----


def test_ask_gemma_runs_under_ci_no_egress_guard(monkeypatch):
    # Gemma is OpenRouter/Google (Western-hosted) → must NOT be gated like GLM.
    # Setting a CI env var must NOT block it; the call proceeds to opencode.
    for var in _CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("CI", "true")
    with (
        patch("scripts.ai_agent_bridge._opencode.send_message", return_value=1) as send_mock,
        patch("scripts.ai_agent_bridge._opencode.acknowledge"),
        patch("scripts.ai_agent_bridge._opencode._invoke_opencode", return_value="ok") as inv,
    ):
        ask_gemma("audit this", task_id="t")
        # Reached the transport (no SystemExit / refusal) even under CI.
        inv.assert_called_once()
        assert send_mock.called
