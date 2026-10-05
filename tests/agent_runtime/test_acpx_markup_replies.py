"""Leaked tool syntax fails parsing and cannot complete an ACP ask (#9671).

Provider syntax references:
https://github.com/MoonshotAI/Kimi-K2/blob/main/docs/tool_call_guidance.md
https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4
https://ai.google.dev/gemma/docs/functiongemma/full-function-calling-sequence-with-functiongemma
https://github.com/NousResearch/Hermes-Function-Calling/blob/main/prompt_assets/sys_prompt.yml
DeepSeek legacy syntax also reproduces the existing test_ask_contract fixture.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.agent_runtime.adapters import acpx
from scripts.agent_runtime.result import Result

MARKUP_REPLIES = (
    pytest.param(
        '<｜DSML｜function_calls><｜DSML｜invoke name="search">'
        '<｜DSML｜parameter name="query" string="true">needle</｜DSML｜parameter>'
        "</｜DSML｜invoke></｜DSML｜function_calls>",
        id="deepseek-dsml",
    ),
    pytest.param(
        '<｜DSML｜tool_calls><｜DSML｜invoke name="search"></｜DSML｜invoke></｜DSML｜tool_calls>',
        id="deepseek-dsml-tool-calls",
    ),
    pytest.param(
        '<｜DSML｜invoke name="search"><｜DSML｜parameter name="query" string="true">'
        "needle</｜DSML｜parameter></｜DSML｜invoke>",
        id="deepseek-dsml-invoke",
    ),
    pytest.param(
        "<function_calls><invoke><tool_name>search</tool_name>"
        "<parameters><query>needle</query></parameters></invoke></function_calls>",
        id="claude-xml",
    ),
    pytest.param(
        '<antml:function_calls><antml:invoke name="search">'
        '<antml:parameter name="query">needle</antml:parameter>'
        "</antml:invoke></antml:function_calls>",
        id="claude-antml",
    ),
    pytest.param('<antml:invoke name="search"></antml:invoke>', id="claude-antml-invoke"),
    pytest.param('<tool_call>{"name":"search","arguments":{"query":"needle"}}</tool_call>', id="hermes-xml"),
    pytest.param(
        "<tool_call>search<arg_key>query</arg_key><arg_value>needle</arg_value></tool_call>",
        id="glm-xml",
    ),
    pytest.param(
        "<|tool_calls_section_begin|><|tool_call_begin|>functions.search:0"
        '<|tool_call_argument_begin|>{"query":"needle"}'
        "<|tool_call_end|><|tool_calls_section_end|>",
        id="kimi-section",
    ),
    pytest.param(
        '<|tool_call_begin|>functions.search:0<|tool_call_argument_begin|>{"query":"needle"}<|tool_call_end|>',
        id="kimi-call",
    ),
    pytest.param(
        "<start_function_call>call:search{query:<escape>needle<escape>}<end_function_call>",
        id="functiongemma",
    ),
    pytest.param(
        '<|tool_call>call:search{query:<|"|>needle<|"|>}<tool_call|>',
        id="gemma4",
    ),
    pytest.param(
        '<|tool_call>call:search{query:<|"|>needle<|"|>}<tool_call|><|tool_response>',
        id="gemma4-response-boundary",
    ),
    pytest.param(
        "<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>function<｜tool▁sep｜>search\n"
        '```json\n{"query":"needle"}\n```<｜tool▁call▁end｜><｜tool▁calls▁end｜>',
        id="deepseek-legacy",
    ),
)


def _parse_reply(response: str, *, adapter=None, chunk_size: int | None = None, tool_updates=()):
    """Feed actual JSON-RPC chunks and a successful terminal to the parser."""
    chunks = (
        [response]
        if chunk_size is None
        else [response[i : i + chunk_size] for i in range(0, len(response), chunk_size)]
    )
    events = [
        {"jsonrpc": "2.0", "id": 2, "method": "session/prompt", "params": {}},
        *[
            {"jsonrpc": "2.0", "method": "session/update", "params": {"sessionId": "fixture", "update": update}}
            for update in tool_updates
        ],
        *[
            {
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {
                    "sessionId": "fixture",
                    "update": {
                        "sessionUpdate": "agent_message_chunk",
                        "content": {"type": "text", "text": chunk},
                    },
                },
            }
            for chunk in chunks
        ],
        {"jsonrpc": "2.0", "id": 2, "result": {"stopReason": "end_turn"}},
    ]
    return (adapter or acpx.AcpxAdapter()).parse_response(
        stdout="\n".join(json.dumps(event) for event in events), stderr="", returncode=0, output_file=None
    )


@pytest.mark.parametrize("markup", MARKUP_REPLIES)
@pytest.mark.parametrize("wrapper", ["{}", " \n{}\n ", "```xml\n{}\n```", "~~~\n{}\n~~~"])
def test_markup_only_reply_fails_typed(markup: str, wrapper: str) -> None:
    parsed = _parse_reply(wrapper.format(markup), chunk_size=7)
    assert parsed.ok is False
    assert parsed.failure_code == "result_invalid"
    assert parsed.response == ""
    assert parsed.rate_limited is False
    assert parsed.stderr_excerpt == "ACP reply contains only tool-call markup, without an answer"


@pytest.mark.parametrize("markup", MARKUP_REPLIES)
@pytest.mark.parametrize(
    "wrapper", ["Example: `{}`.", "This is a tool call:\n```xml\n{}\n```", "{}\nThe answer is 42."]
)
def test_prose_quoting_markup_passes_unchanged(markup: str, wrapper: str) -> None:
    response = wrapper.format(markup)
    parsed = _parse_reply(response, chunk_size=3)
    assert parsed.ok is True
    assert parsed.failure_code is None
    assert parsed.response == response


@pytest.mark.parametrize("response", ["", "Answer: 42", "<p>Answer: 42</p>", '{"answer":42}', "`<tool_call>`"])
def test_ordinary_replies_keep_existing_behavior(response: str) -> None:
    parsed = _parse_reply(response)
    assert parsed.ok is True
    assert parsed.response == response


def test_multiple_calls_fail_but_intervening_prose_passes() -> None:
    call = '<tool_call>{"name":"search","arguments":{}}</tool_call>'
    assert _parse_reply(call + "\n\t" + call).failure_code == "result_invalid"
    response = call + "\nThe answer is 42.\n" + call
    assert _parse_reply(response).response == response
    assert _parse_reply(response).ok is True


@pytest.mark.parametrize("markup_only", [False, True])
@pytest.mark.parametrize("grok_wrapper", [False, True])
def test_structured_tool_trace_does_not_replace_a_final_answer(markup_only: bool, grok_wrapper: bool) -> None:
    arguments = {"query": "needle"}
    raw_input = (
        {"variant": "UseTool", "tool_name": "search", "tool_input": arguments}
        if grok_wrapper
        else json.dumps(arguments)
    )
    updates = (
        {
            "sessionUpdate": "tool_call",
            "toolCallId": "call-1",
            "name": "use_tool" if grok_wrapper else "search",
            "title": "Search",
            "rawInput": raw_input,
            "status": "pending",
        },
        {
            "sessionUpdate": "tool_call_update",
            "toolCallId": "call-1",
            "status": "completed",
            "rawOutput": {"matches": []},
        },
    )
    response = '<tool_call>{"name":"search","arguments":{}}</tool_call>' if markup_only else "No matches found."
    parsed = _parse_reply(response, tool_updates=updates)
    if markup_only:
        assert parsed.ok is False
        assert parsed.failure_code == "result_invalid"
        assert parsed.response == ""
    else:
        assert parsed.ok is True
        assert parsed.response == response
        assert parsed.tool_calls == [
            {
                "id": "call-1",
                "name": "search",
                "title": "Search",
                "arguments": arguments,
                "result": {"matches": []},
                "status": "completed",
            }
        ]


@pytest.mark.parametrize(
    "adapter_class",
    [
        acpx.AcpxAdapter,
        acpx.AcpxGrokShadowAdapter,
        acpx.AcpxClaudeShadowAdapter,
        acpx.AcpxKimiShadowAdapter,
        acpx.AcpxKimiCcShadowAdapter,
        acpx.AcpxCursorShadowAdapter,
        acpx.AcpxPoolShadowAdapter,
        acpx.AcpxAgyShadowAdapter,
        acpx.AcpxGlmShadowAdapter,
        acpx.AcpxGemmaShadowAdapter,
        acpx.AcpxDeepSeekShadowAdapter,
    ],
)
def test_every_acp_adapter_rejects_markup_only(adapter_class) -> None:
    parsed = _parse_reply('<tool_call>{"name":"search","arguments":{}}</tool_call>', adapter=adapter_class())
    assert parsed.ok is False
    assert parsed.failure_code == "result_invalid"


def test_markup_failure_reaches_durable_ask_outcome_and_replay(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use the real ask controller/store, with no external provider invocation."""
    from agent_runtime.runner import _privacy_safe_failure_code
    from scripts.ai_agent_bridge import _acp_compat
    from scripts.fleet_comms.authority import AuthorityService

    parsed = _parse_reply('<｜DSML｜function_calls><｜DSML｜invoke name="search"/></｜DSML｜function_calls>')
    code = _privacy_safe_failure_code(
        outcome="error",
        rate_limited=parsed.rate_limited,
        stalled=False,
        returncode=0,
        explicit_code=parsed.failure_code,
    )
    result = Result(
        ok=parsed.ok,
        agent="grok",
        model="fixture",
        mode="read-only",
        response=parsed.response,
        stderr_excerpt=parsed.stderr_excerpt,
        duration_s=0.0,
        session_id=None,
        rate_limited=parsed.rate_limited,
        stalled=False,
        returncode=0,
        failure_code=code,
        transport_outcome="error",
    )
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "fleet"))
    invoke = Mock(return_value=result)
    monkeypatch.setattr("agent_runtime.runner.invoke_inter_agent", invoke)
    monkeypatch.setattr(acpx, "probe_participant_reachability", Mock(return_value=None))

    @contextmanager
    def execution_cwd(*_args, **_kwargs):
        yield tmp_path

    monkeypatch.setattr("scripts.ai_agent_bridge._acp_execution.acp_execution_cwd", execution_cwd)
    live = _acp_compat.run_compat_ask("grok", "question", task_id="markup-9671", source="codex")
    replay = _acp_compat.run_compat_ask("grok", "question", task_id="markup-9671", source="codex")
    assert live.ok is False
    assert replay.ok is False
    assert replay.failure_code == "result_invalid"
    assert replay.response == ""
    assert invoke.call_count == 1
    with AuthorityService() as authority:
        rows = authority.store.connection.execute("SELECT job_id FROM authority_jobs").fetchall()
        assert len(rows) == 1
        job = authority.get_job(rows[0]["job_id"])
        events = authority.store.connection.execute(
            "SELECT metadata_json FROM authority_job_events WHERE job_id = ? AND event_type = 'finished'",
            (job.job_id,),
        ).fetchall()
    assert job.state == "failed"
    assert job.lease_owner is None
    assert len(events) == 1
    assert json.loads(events[0]["metadata_json"])["failure"] == {
        "phase": "result_parse",
        "code": "result_invalid",
        "retryable": False,
    }
