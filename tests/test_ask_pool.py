"""Tests for ab ask-pool / ask-glm bridge subcommands (opencode-routed fleet).

pool = poolside.ai laguna-m.1 (free code + web-verify specialist).
glm  = Zhipu glm-5.2 (code + review; ⚠️ China-hosted → LOCAL-ONLY, no CI).
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

# --- constants ------------------------------------------------------------


def test_pool_model_is_native_poolside_provider():
    # NOT the openrouter/* path (that one cannot browse).
    assert POOL_MODEL == "poolside/poolside/laguna-m.1"


def test_glm_model_is_zai_coding_plan():
    assert GLM_MODEL == "zai-coding-plan/glm-5.2"


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
                POOL_MODEL,
                variant="high",
                output_format="json",
            )
            argv = run_mock.call_args[0][0]
            assert argv[:2] == ["/fake/opencode", "run"]
            fmt_idx = argv.index("--format")
            assert argv[fmt_idx + 1] == "json"
            var_idx = argv.index("--variant")
            assert argv[var_idx + 1] == "high"
            assert POOL_MODEL in argv
            # NDJSON parsed down to the assistant text.
            assert out == "hi"


def test_invoke_opencode_no_variant_by_default():
    with patch("scripts.ai_agent_bridge._opencode.shutil.which", return_value="/fake/opencode"):
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run_mock:
            run_mock.return_value = MagicMock(returncode=0, stdout="plain", stderr="")
            _invoke_opencode("hello", GLM_MODEL, output_format="default")
            argv = run_mock.call_args[0][0]
            assert "--variant" not in argv
            assert argv[argv.index("--format") + 1] == "default"


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


def test_ask_pool_rejects_invalid_variant():
    with pytest.raises(SystemExit, match="invalid --variant"):
        ask_pool("hi", task_id="t", variant="turbo")


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
            _invoke_opencode("--- a/tricky diff line", POOL_MODEL, output_format="default")
            argv = run_mock.call_args[0][0]
            assert argv[-2] == "--"
            assert argv[-1] == "--- a/tricky diff line"


# --- model override (churn-resistance; tags drift per model-assignment.md) --


def test_ask_pool_defaults_to_pinned_model():
    with (
        patch("scripts.ai_agent_bridge._opencode.send_message", return_value=1),
        patch("scripts.ai_agent_bridge._opencode.acknowledge"),
        patch("scripts.ai_agent_bridge._opencode._invoke_opencode", return_value="ok") as inv,
    ):
        ask_pool("hi", task_id="t")
        assert inv.call_args[0][1] == POOL_MODEL


def test_ask_pool_honors_model_override():
    with (
        patch("scripts.ai_agent_bridge._opencode.send_message", return_value=1),
        patch("scripts.ai_agent_bridge._opencode.acknowledge"),
        patch("scripts.ai_agent_bridge._opencode._invoke_opencode", return_value="ok") as inv,
    ):
        ask_pool("hi", task_id="t", model="openrouter/poolside/laguna-m.1")
        assert inv.call_args[0][1] == "openrouter/poolside/laguna-m.1"


def test_ask_glm_honors_model_override_when_not_ci(monkeypatch):
    for var in _CI_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    with (
        patch("scripts.ai_agent_bridge._opencode.send_message", return_value=1),
        patch("scripts.ai_agent_bridge._opencode.acknowledge"),
        patch("scripts.ai_agent_bridge._opencode._invoke_opencode", return_value="ok") as inv,
    ):
        ask_glm("hi", task_id="t", model="openrouter/z-ai/glm-5.2")
        assert inv.call_args[0][1] == "openrouter/z-ai/glm-5.2"


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


def test_parse_ndjson_single_message_no_regression():
    """No regression on single-message replies (the common non-tool case)."""
    stream = "\n".join(
        [
            '{"type":"step_start","part":{}}',
            '{"type":"text","part":{"type":"text","text":"Single complete answer here."}}',
            '{"type":"step_finish","part":{"reason":"stop"}}',
        ]
    )
    assert _parse_opencode_ndjson(stream) == "Single complete answer here."
