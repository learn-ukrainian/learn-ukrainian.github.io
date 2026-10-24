"""Tests for ab ask-pool / ask-glm bridge subcommands (opencode-routed fleet).

pool = poolside.ai laguna-s-2.1 (free code + web-verify specialist).
glm  = Zhipu glm-5.3 (code + review; ⚠️ China-hosted → LOCAL-ONLY, no CI).
"""

from unittest.mock import MagicMock, patch

import pytest

from scripts.ai_agent_bridge._opencode import (
    _CI_ENV_VARS,
    GLM_MODEL,
    POOL_MODEL,
    _assert_glm_egress_allowed,
    _invoke_opencode,
    _parse_opencode_ndjson,
    ask_glm,
    ask_pool,
)
from scripts.lib import rules_core

# --- constants ------------------------------------------------------------


# --- invocation argv (variant + json format) ------------------------------


def test_invoke_opencode_passes_variant_and_json_format():
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(
                returncode=0,
                stdout='{"type":"text","part":{"type":"text","text":"hi"}}',
                stderr="",
            )
            out = _invoke_opencode(
                "review this",
                "deepseek/deepseek-v4.1-flash",
                variant="high",
                output_format="json",
            )
            argv = run_mock.call_args[0][0]
            assert argv[:2] == ["/fake/opencode", "run"]
            fmt_idx = argv.index("--format")
            assert argv[fmt_idx + 1] == "json"
            var_idx = argv.index("--variant")
            assert argv[var_idx + 1] == "high"
            assert "deepseek/deepseek-v4.1-flash" in argv
            # NDJSON parsed down to the assistant text.
            assert out == "hi"


# --- NDJSON parsing -------------------------------------------------------


def test_parse_ndjson_concatenates_text_parts_only():
    stream = "\n".join(
        [
            '{"type":"step_start","part":{"type":"step-start"}}',
            '{"type":"reasoning","part":{"type":"reasoning","text":"THINKING"}}',
            '{"type":"text","part":{"type":"text","text":"Hello "}}',
            '{"type":"text","part":{"type":"text","text":"world"}}',
            '{"type":"step_finish","part":{"reason":"stop"}}',
        ]
    )
    assert _parse_opencode_ndjson(stream) == "Hello world"


def test_parse_ndjson_falls_back_to_raw_when_no_text_parts():
    # Robust to opencode format drift: never silently return empty.
    assert _parse_opencode_ndjson("not json at all\n") == "not json at all"


def test_parse_ndjson_tolerates_blank_and_garbage_lines():
    stream = "\n\ngarbage\n{bad json}\n" + '{"type":"text","part":{"type":"text","text":"ok"}}'
    assert _parse_opencode_ndjson(stream) == "ok"


# --- pool variant validation ---------------------------------------------


# --- GLM China-egress backstop (load-bearing LOCAL-ONLY guard) ------------


def test_assert_glm_egress_allowed_passes_when_no_ci_env(monkeypatch):
    for var in _CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    _assert_glm_egress_allowed()  # no raise


@pytest.mark.parametrize("var", _CI_ENV_VARS)
def test_assert_glm_egress_allowed_raises_under_ci(monkeypatch, var):
    for other in _CI_ENV_VARS:
        monkeypatch.delenv(other, raising=False)
    monkeypatch.setenv(var, "true")
    with pytest.raises(SystemExit, match="China-hosted"):
        _assert_glm_egress_allowed()


def test_assert_glm_egress_refusal_names_the_variable_never_its_value(monkeypatch):
    for other in _CI_ENV_VARS:
        monkeypatch.delenv(other, raising=False)
    sentinel = "https://ci.example.invalid/secret-token-8652"
    monkeypatch.setenv("JENKINS_URL", sentinel)
    with pytest.raises(SystemExit, match="JENKINS_URL") as refused:
        _assert_glm_egress_allowed()
    assert sentinel not in str(refused.value)


def test_ask_glm_refuses_under_ci_before_any_egress(monkeypatch):
    # Guard must fire before send_message / subprocess — i.e. no DB or network.
    for other in _CI_ENV_VARS:
        monkeypatch.delenv(other, raising=False)
    monkeypatch.setenv("CI", "true")
    with patch("scripts.ai_agent_bridge._opencode.send_message") as send_mock:
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            with pytest.raises(SystemExit, match="LOCAL-ONLY"):
                ask_glm("audit this", task_id="t")
            send_mock.assert_not_called()
            run_mock.assert_not_called()


def test_assert_glm_egress_allowed_raises_on_empty_ci_value(monkeypatch):
    # A set-but-empty CI var must STILL refuse (presence check, not truthiness).
    for other in _CI_ENV_VARS:
        monkeypatch.delenv(other, raising=False)
    monkeypatch.setenv("CI", "")
    with pytest.raises(SystemExit, match="China-hosted"):
        _assert_glm_egress_allowed()


def test_invoke_opencode_always_separates_content_with_dashdash():
    # content starting with '-' must be positional (after --), never a flag.
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
            _invoke_opencode("--- a/tricky diff line", "deepseek/deepseek-v4.1-flash", output_format="default")
            argv = run_mock.call_args[0][0]
            assert argv[-2] == "--"
            assert argv[-1] == rules_core.with_core("--- a/tricky diff line")


# --- model override (churn-resistance; tags drift per model-assignment.md) --


def test_retired_pool_override_is_refused_before_message_creation():
    with patch("scripts.ai_agent_bridge._opencode.send_message") as send:
        with pytest.raises(ValueError, match="is retired in the model catalog"):
            ask_pool("hi", task_id="t", model="openrouter/poolside/laguna-s-2.1")
        send.assert_not_called()


def test_ask_glm_refuses_openrouter_glm_before_subprocess(monkeypatch):
    """GLM via OpenRouter must fail at the routing guard inside _run_opencode."""
    for var in _CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    with (
        patch("scripts.ai_agent_bridge._opencode.send_message", return_value=1),
        patch("scripts.ai_agent_bridge._opencode.acknowledge"),
        patch(
            "scripts.ai_agent_bridge._opencode.subprocess.run",
            side_effect=AssertionError("subprocess must not run for refused GLM route"),
        ),
    ):
        with pytest.raises(ValueError, match="is retired in the model catalog"):
            ask_glm("hi", task_id="t", model="openrouter/z-ai/glm-5.3")


# --- capture fix for multi-message streams (first vs last assistant msg) ---


def test_parse_ndjson_multi_message_stream_yields_last_substantive_message():
    """'capture fixed' deterministic check for #5091.

    Synthetic multi-message (preamble narration + final after "tool" turn)
    stream must return a reply containing the LAST substantive message,
    not the first streamed assistant message (narration/prefix).
    """
    stream = "\n".join(
        [
            '{"type":"text","part":{"type":"text","text":"I\'ll read the design document first..."}}',
            '{"type":"tool_use","part":{"type":"tool","tool":"read","callID":"c1","state":{"status":"completed","input":{"path":"foo.md"},"output":"..."}}}',
            '{"type":"text","part":{"type":"text","text":"Here is the full review:\\n\\n## Summary\\nPASS with evidence on lines 12-34."}}',
            '{"type":"step_finish","part":{"reason":"stop"}}',
        ]
    )
    result = _parse_opencode_ndjson(stream)
    assert "Here is the full review" in result
    assert "PASS with evidence" in result
    # Must NOT be just the first (preamble) message.
    assert "I'll read the design document first" not in result
    assert result.strip().startswith("Here is the full review")


# --- token budget plumbing for glm/pool (fixes #5123 length deaths) --------


def test_get_max_output_tokens_defaults_for_glm_pool():
    """Sane defaults kick in for the lanes that exhibited reasoning=length."""
    from scripts.ai_agent_bridge._opencode import (
        GLM_DEFAULT_MAX_OUTPUT_TOKENS,
        GLM_MODEL,
        POOL_DEFAULT_MAX_OUTPUT_TOKENS,
        POOL_MODEL,
        _get_max_output_tokens,
    )

    assert _get_max_output_tokens(GLM_MODEL) == GLM_DEFAULT_MAX_OUTPUT_TOKENS
    assert _get_max_output_tokens(POOL_MODEL) == POOL_DEFAULT_MAX_OUTPUT_TOKENS
    # also matches on prefix variants
    assert _get_max_output_tokens("openrouter/z-ai/glm-5.3") == GLM_DEFAULT_MAX_OUTPUT_TOKENS
    assert _get_max_output_tokens("poolside/poolside/laguna-s-2.1") == POOL_DEFAULT_MAX_OUTPUT_TOKENS


def test_retired_glm_pool_cannot_spawn_with_default_token_budget(monkeypatch):
    from scripts.ai_agent_bridge.routing_guard import RoutingGuardError

    with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run:
        for model in (GLM_MODEL, POOL_MODEL):
            with pytest.raises(RoutingGuardError, match="is retired in the model catalog"):
                _invoke_opencode("review code", model, output_format="json")
        run.assert_not_called()


def test_retired_glm_pool_cannot_spawn_with_token_budget_overrides(monkeypatch):
    from scripts.ai_agent_bridge.routing_guard import RoutingGuardError

    for key in ("AB_OPENCODE_MAX_OUTPUT_TOKENS", "AB_GLM_MAX_OUTPUT_TOKENS", "AB_POOL_MAX_OUTPUT_TOKENS"):
        monkeypatch.setenv(key, "262144")
    with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run:
        for model in (GLM_MODEL, POOL_MODEL):
            with pytest.raises(RoutingGuardError, match="is retired in the model catalog"):
                _invoke_opencode("review code", model, output_format="json")
        run.assert_not_called()


# --- #5911 lifecycle callback wiring (CI catch) ---


def test_retired_glm_and_pool_create_no_messages_or_callbacks(monkeypatch):
    for var in _CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    for fn in (ask_glm, ask_pool):
        seen = []
        with patch("scripts.ai_agent_bridge._opencode.send_message") as send:
            with pytest.raises(ValueError, match="is retired in the model catalog"):
                fn("hi", task_id="t", on_message_created=seen.append)
            send.assert_not_called()
        assert seen == []
