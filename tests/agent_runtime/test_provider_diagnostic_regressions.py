"""#9539 review regressions, using installed CLI/SDK and repository diagnostics.

Positive diagnostic provenance (no paid CLI calls):
* Kimi: installed @moonshot-ai/kimi-code dist/main.mjs,
  formatNativeTurnFailure + formatStartupError, and PROVIDER_*_ERROR_CODE.
* Cursor: installed cursor-agent index.js, requireAuth Error diagnostic.
* Gemini: test_gemini_adapter_auth.py::TestRateLimitMarkersFromCodexReview;
  scripts/etymology/bulk_ocr_gemini.py's captured TerminalQuotaError.
* SDK formats: installed Kimi bundle's GaxiosError.extractAPIErrorFromResponse
  and installed Hermes openai/_base_client.py::_make_status_error.
* AGY: installed binary embeds googleapi's "googleapi: Error %d:" formatter.
* Gemini retry prefix: upstream packages/core/src/utils/retry.ts::logRetryAttempt,
  corroborating the review's Gaxios retry block; the SDK exception is installed in Kimi.
* HTTP/transport: test_runner_failover.py::_TRIGGER_CASES and
  adapters/test_hermes_deepseek_adapter.py's captured in-band errors.
"""

from __future__ import annotations

import json

import pytest

from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.failover import classify_failover_trigger
from agent_runtime.failure_codes import provider_failure_code, provider_stderr_error
from tests.agent_runtime.test_sibling_provider_signals import ADAPTERS, CONTENT, _agy_plan, _stdout

# These are repository captures or diagnostics from the identified CLI/SDK
# formatters, with numeric status inputs substituted. No account identifiers.
LIMIT_DIAGNOSTICS = [
    "Rate limit exceeded. Free tier limits have been reached.",
    "Rate limit exceeded. Please try again.",
    "quota exceeded",
    "TerminalQuotaError: You have exhausted your capacity on this model.\nYour quota will reset after 19h25m58s.",
    "Error code: 429",
    "Request failed with status code 429",
    "GaxiosError: Request failed with status code 429",
    "Attempt 1 failed. Retrying with backoff... GaxiosError: Request failed with status code 429",
    "googleapi: Error 429:",
    "HTTP 429: Too Many Requests",
]


@pytest.mark.parametrize("diagnostic", LIMIT_DIAGNOSTICS)
def test_gemini_real_terminal_limit_sets_api_cooldown(diagnostic, tmp_path, monkeypatch):
    from ai_llm import cooldown

    cooldowns = []
    monkeypatch.setattr(cooldown, "set_api_cooldown", lambda: cooldowns.append(True))
    result = ADAPTERS["gemini"]().parse_response(
        stdout="",
        stderr=diagnostic,
        returncode=1,
        output_file=None,
        plan=InvocationPlan(cmd=["gemini"], cwd=tmp_path),
    )
    assert result.failure_code == "rate_limited"
    assert result.rate_limited is True
    assert cooldowns == [True]


@pytest.mark.parametrize(
    "code,expected,trigger",
    [
        ("provider.rate_limit", "rate_limited", "rate_limited"),
        ("provider.auth_error", "provider_auth", "auth"),
        ("provider.overloaded", "provider_overloaded", "overloaded"),
        ("provider.connection_error", "transport_error", "transport"),
    ],
)
def test_kimi_terminal_codes_survive_wrapped_error(code, expected, trigger):
    diagnostic = f"error: failed to run prompt: {code}:"
    result = ADAPTERS["kimi"]().parse_response(stdout="", stderr=diagnostic, returncode=1, output_file=None)
    assert result.failure_code == expected
    assert result.rate_limited is (trigger == "rate_limited")
    assert (
        classify_failover_trigger(
            parse=result,
            returncode=1,
            kill_reason=None,
            stdout_text=CONTENT,
            stderr_text=diagnostic,
        )
        == trigger
    )


@pytest.mark.parametrize("adapter", ADAPTERS)
@pytest.mark.parametrize(
    "diagnostic,expected,trigger",
    [
        ("Error: Authentication required.", "provider_auth", "auth"),
        ("HTTP 401: Authentication Fails, Your api key: ****robe is invalid", "provider_auth", "auth"),
        ("HTTP 503 overloaded", "provider_overloaded", "overloaded"),
        ("connection refused", "transport_error", "transport"),
    ],
)
def test_failed_adapter_keeps_provider_auth_overload_transport(adapter, diagnostic, expected, trigger):
    result = ADAPTERS[adapter]().parse_response(stdout="", stderr=diagnostic, returncode=1, output_file=None)
    assert result.failure_code == expected
    assert result.rate_limited is False
    assert (
        classify_failover_trigger(
            parse=result,
            returncode=1,
            kill_reason=None,
            stdout_text=CONTENT,
            stderr_text=diagnostic,
        )
        == trigger
    )


@pytest.mark.parametrize("adapter", ["agy", "grok", "deepseek", "glm"])
@pytest.mark.parametrize(
    "diagnostic",
    [
        "Error code: 429",
        "Request failed with status code 429",
        "Too Many Requests",
        "Request rejected: Error code: 429",
        "Request rejected: Too Many Requests",
    ],
)
def test_provider_labelled_fields_search_entire_message(adapter, diagnostic, tmp_path):
    if adapter == "agy":
        plan = _agy_plan(tmp_path, "")
        plan.cmd.extend(["--output-format", "stream-json"])
        stdout = json.dumps(
            {
                "event": "result",
                "result": {
                    "conversation_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "status": "ERROR",
                    "response": "",
                    "error": diagnostic,
                },
            }
        )
    elif adapter == "grok":
        plan = None
        stdout = json.dumps({"type": "error", "error": diagnostic})
    else:
        plan = None
        stdout = json.dumps({"type": "error", "error": {"name": "APIError", "data": {"message": diagnostic}}})
    result = ADAPTERS[adapter]().parse_response(stdout=stdout, stderr="", returncode=1, output_file=None, plan=plan)
    assert result.failure_code == "rate_limited"
    assert result.rate_limited is True


@pytest.mark.parametrize("status", [400, 401, 403, 404, 408, 418, 429, 500, 502, 503, 504])
def test_explicit_status_never_falls_back_to_body_words(status):
    expected = (
        "rate_limited"
        if status == 429
        else "provider_auth"
        if status in (401, 403)
        else "provider_overloaded"
        if status >= 500
        else "provider_error"
    )
    # Adversarial body: status must override misleading words.
    body = "rate limit exceeded; authentication required; connection refused"
    assert provider_failure_code(body, status) == expected
    assert provider_failure_code(f"Error code: {status} - {body}") == expected


def test_kimi_gh_login_is_github_auth_not_provider_auth():
    diagnostic = "To get started with GitHub CLI, please run:  gh auth login"
    result = ADAPTERS["kimi"]().parse_response(stdout="", stderr=diagnostic, returncode=1, output_file=None)
    assert result.failure_code == "github_auth_required"
    assert result.rate_limited is False
    assert (
        classify_failover_trigger(
            parse=result,
            returncode=1,
            kill_reason=None,
            stdout_text="",
            stderr_text=diagnostic,
        )
        == "auth"
    )


@pytest.mark.parametrize("adapter", ADAPTERS)
@pytest.mark.parametrize("diagnostic", LIMIT_DIAGNOSTICS)
def test_success_and_tool_diagnostics_never_trigger_provider_failure(adapter, diagnostic, tmp_path):
    stdout = _stdout(adapter, diagnostic, tool=True)
    result = ADAPTERS[adapter]().parse_response(
        stdout=stdout,
        stderr=json.dumps({"type": "tool_result", "output": diagnostic}),
        returncode=0,
        output_file=None,
        plan=_agy_plan(tmp_path, diagnostic) if adapter == "agy" else None,
    )
    assert result.ok is True
    assert result.rate_limited is False
    assert result.failure_code is None


def test_stderr_prose_cannot_supply_provider_diagnostic():
    assert provider_stderr_error("rate limit regression test returned 429") == ""
    assert provider_failure_code("quota discussion containing 429") == "provider_error"


@pytest.mark.parametrize("diagnostic", ["provider.rate_limit docs", "provider.openrouter rate limit exceeded docs"])
def test_bare_provider_token_without_terminal_colon_is_not_a_diagnostic(diagnostic):
    assert provider_stderr_error(diagnostic) == ""


@pytest.mark.parametrize(
    "prefix", ["error", "opencode", "kimi", "grok", "agy", "gemini", "cursor", "provider", "acp transport"]
)
@pytest.mark.parametrize("body", ["test_rate_limit.py::test_x FAILED", "... see provider.rate_limit docs"])
def test_generic_prefix_cannot_attribute_later_provider_mentions(prefix, body):
    assert provider_stderr_error(f"{prefix}: {body}") == ""


@pytest.mark.parametrize(
    "prefix", ["error", "opencode", "kimi", "grok", "agy", "gemini", "cursor", "provider", "acp transport"]
)
@pytest.mark.parametrize(
    "body,expected",
    [
        ("Rate limit exceeded", "rate_limited"),
        ("Too Many Requests", "rate_limited"),
        ("HTTP 429: Too Many Requests", "rate_limited"),
        ("Authentication required", "provider_auth"),
        ("Service unavailable", "provider_overloaded"),
        ("connection refused", "transport_error"),
    ],
)
def test_generic_prefix_keeps_immediate_provider_marker(prefix, body, expected):
    diagnostic = f"{prefix}: {body}"
    assert provider_stderr_error(diagnostic) == diagnostic
    assert provider_failure_code(diagnostic) == expected


@pytest.mark.parametrize("code", ["openrouter", "unknown"])
def test_provider_name_does_not_override_rate_limit_wording(code):
    diagnostic = f"Rate limit exceeded for provider.{code}"
    assert provider_failure_code(provider_stderr_error(diagnostic)) == "rate_limited"


@pytest.mark.parametrize(
    "code", ["rate_limit", "auth_error", "overloaded", "connection_error", "filtered", "api_error"]
)
def test_recognized_provider_codes_still_override_prose(code):
    expected = {
        "rate_limit": "rate_limited",
        "auth_error": "provider_auth",
        "overloaded": "provider_overloaded",
        "connection_error": "transport_error",
        "filtered": "provider_policy_refusal",
        "api_error": "provider_error",
    }[code]
    assert provider_failure_code(f"provider.{code}: Rate limit exceeded for provider.openrouter") == expected


@pytest.mark.parametrize(
    "adapter_module,adapter_name",
    [
        ("hermes_deepseek", "HermesDeepSeekAdapter"),
        ("hermes_grok", "HermesGrokAdapter"),
        ("hermes_qwen", "HermesQwenAdapter"),
    ],
)
@pytest.mark.parametrize(
    "status,expected,trigger",
    [
        (401, "provider_auth", "auth"),
        (403, "provider_auth", "auth"),
        (429, "rate_limited", "rate_limited"),
        (500, "provider_overloaded", "overloaded"),
        (503, "provider_overloaded", "overloaded"),
        (400, "provider_error", None),
    ],
)
@pytest.mark.parametrize("returncode", [0, 1])
def test_hermes_inband_status_is_typed_by_adapter(adapter_module, adapter_name, status, expected, trigger, returncode):
    import importlib

    cls = getattr(importlib.import_module(f"agent_runtime.adapters.{adapter_module}"), adapter_name)
    # Installed Hermes agent/api_error_summary.py::_http_prefix.
    diagnostic = f"HTTP {status}: "
    result = cls().parse_response(stdout=diagnostic, stderr="", returncode=returncode, output_file=None)
    assert result.failure_code == expected
    assert result.provider_error_text == diagnostic.strip()
    assert result.rate_limited is (status == 429)
    assert (
        classify_failover_trigger(
            parse=result,
            returncode=returncode,
            kill_reason=None,
            stdout_text=diagnostic,
            stderr_text="",
        )
        == trigger
    )


@pytest.mark.parametrize("field", ["error", "message"])
@pytest.mark.parametrize("returncode", [0, 1])
def test_grok_native_error_message_field(field, returncode):
    # Installed grok binary's --output-format JSON documentation explicitly
    # labels terminal diagnostics as {"type":"error","message":...}.
    result = ADAPTERS["grok"]().parse_response(
        stdout=json.dumps({"type": "error", field: "Error code: 429", "text": CONTENT}),
        stderr="",
        returncode=returncode,
        output_file=None,
    )
    assert result.failure_code == "rate_limited"
    assert result.provider_error_text == "Error code: 429"
    assert result.rate_limited is True


@pytest.mark.parametrize("adapter", ADAPTERS)
@pytest.mark.parametrize("pretty", [False, True])
def test_review_api_error_wrapper_only_owns_its_json_payload(adapter, pretty):
    # Supplied review's [API Error: {"error":{"code":429,...RESOURCE_EXHAUSTED}}]
    # format, with the same API code/status fields as test_gemini_adapter_auth.
    payload = json.dumps({"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}}, indent=2 if pretty else None)
    diagnostic = "[API Error: " + payload + "]"
    result = ADAPTERS[adapter]().parse_response(stdout="", stderr=diagnostic, returncode=1, output_file=None)
    assert result.failure_code == "rate_limited"
    assert result.rate_limited is True
    # This is an adversarial, separate tool envelope after an unknown API
    # error; it must not become part of the attributed diagnostic payload.
    tool = json.dumps({"type": "tool_result", "output": "HTTP 429: Too Many Requests"})
    assert provider_failure_code(provider_stderr_error('[API Error: {"error": {}}]\n' + tool)) == "provider_error"
