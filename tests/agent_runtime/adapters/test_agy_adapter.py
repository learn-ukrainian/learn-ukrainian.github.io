from __future__ import annotations

import json
import re
import time
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters import agy as agy_module
from scripts.agent_runtime.adapters.agy import AgyAdapter
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.build import linear_pipeline

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "agy"
CONVERSATION_ID = "7cd3ba85-817f-4a03-8223-1ff39ca42419"


def _plan(
    tmp_path: Path,
    *,
    log_file: Path,
    app_data: Path,
    cmd: list[str] | None = None,
) -> InvocationPlan:
    return InvocationPlan(
        cmd=cmd or ["agy"],
        cwd=tmp_path,
        stdin_payload="",
        output_file=None,
        env_overrides={
            "AGY_RUNTIME_LOG_FILE": str(log_file),
            "AGY_APP_DATA_DIR": str(app_data),
        },
        env_unsets=(),
        liveness_paths=(log_file,),
        metadata={},
    )


def _write_transcript(app_data: Path) -> None:
    transcript = (
        app_data
        / "brain"
        / CONVERSATION_ID
        / ".system_generated"
        / "logs"
        / "transcript.jsonl"
    )
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        (FIXTURES / "verify_words_transcript.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def test_parse_response_extracts_mcp_calls_from_real_agy_transcript(
    tmp_path: Path,
) -> None:
    stdout = (FIXTURES / "verify_words_stdout.txt").read_text(encoding="utf-8")
    app_data = tmp_path / "antigravity-cli"
    log_file = tmp_path / "agy.log"
    log_file.write_text(
        f"I0521 printmode.go:130] Print mode: conversation={CONVERSATION_ID}, sending message\n",
        encoding="utf-8",
    )
    _write_transcript(app_data)

    result = AgyAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
        plan=_plan(tmp_path, log_file=log_file, app_data=app_data),
    )

    assert result.ok is True
    assert result.response == stdout.strip()
    assert result.tool_calls == [
        {
            "name": "mcp__sources__verify_words",
            "arguments": {"words": ["стіл", "ранок"]},
            "output_summary": (
                '[{"text": "Batch verification: 2 words\\n\\nFound: 2/2\\n\\n'
                '- **стіл** — FOUND (2 match): стіл(noun), стіл(noun)\\n'
                '- **ранок** — FOUND (3 match): ранка(noun), ранок(noun), '
                'ранок(noun)", "type": "text"}]'
            ),
            "timestamp": "2026-05-21T14:12:12Z",
            "result": [
                {
                    "type": "text",
                    "text": (
                        "Batch verification: 2 words\n\nFound: 2/2\n\n"
                        "- **стіл** — FOUND (2 match): стіл(noun), стіл(noun)\n"
                        "- **ранок** — FOUND (3 match): ранка(noun), "
                        "ранок(noun), ранок(noun)"
                    ),
                }
            ],
        }
    ]


def test_parse_response_accepts_stdout_marker_shape() -> None:
    stdout = "\n".join(
        [
            '● mcp_sources_search_text({"query":"Захарійчук 52","limit":3})',
            "⎿ Found 1 results for: \"Захарійчук 52\"",
            "",
            "Final response.",
        ]
    )

    result = AgyAdapter().parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
        plan=None,
    )

    assert result.tool_calls == [
        {
            "name": "mcp__sources__search_text",
            "arguments": {"query": "Захарійчук 52", "limit": 3},
            "output_summary": (
                '[{"text": "Found 1 results for: \\"Захарійчук 52\\"", '
                '"type": "text"}]'
            ),
            "timestamp": "",
            "result": [
                {"type": "text", "text": 'Found 1 results for: "Захарійчук 52"'}
            ],
        }
    ]


def test_parse_response_inlines_safe_saved_tool_result_pointer(tmp_path: Path) -> None:
    app_data = tmp_path / "antigravity-cli"
    log_file = tmp_path / "agy.log"
    log_file.write_text(
        f"I0521 printmode.go:130] Print mode: conversation={CONVERSATION_ID}, sending message\n",
        encoding="utf-8",
    )
    conversation_root = app_data / "brain" / CONVERSATION_ID
    output_file = conversation_root / "steps" / "103" / "output.txt"
    output_file.parent.mkdir(parents=True)
    output_file.write_text("inline result from agy steps file", encoding="utf-8")
    transcript = conversation_root / ".system_generated" / "logs" / "transcript.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        "\n".join(
            [
                (
                    '{"created_at":"2026-05-21T14:12:12Z",'
                    '"tool_calls":[{"name":"call_mcp_tool","args":{'
                    '"ServerName":"\\"sources\\"",'
                    '"ToolName":"\\"search_text\\"",'
                    '"Arguments":"{\\"query\\":\\"ранок\\"}"}}]}'
                ),
                (
                    '{"type":"MCP_TOOL","content":"The output was large and was '
                    f'saved to: {output_file.as_uri()}"}}'
                ),
            ]
        ),
        encoding="utf-8",
    )

    result = AgyAdapter().parse_response(
        stdout="Final response.",
        stderr="",
        returncode=0,
        output_file=None,
        plan=_plan(tmp_path, log_file=log_file, app_data=app_data),
    )

    assert result.tool_calls[0]["result"] == [
        {"type": "text", "text": "inline result from agy steps file"}
    ]
    assert result.tool_calls[0]["output_summary"] == (
        '[{"text": "inline result from agy steps file", "type": "text"}]'
    )


def test_parse_response_pairs_duplicate_planner_intents_by_step_index(
    tmp_path: Path,
) -> None:
    conversation_id = "fbfc8314-a4b6-4d64-9dec-5c9b6f6684bb"
    app_data = tmp_path / "antigravity-cli"
    log_file = tmp_path / "agy.log"
    log_file.write_text(
        f"I0521 printmode.go:130] Print mode: conversation={conversation_id}, sending message\n",
        encoding="utf-8",
    )
    transcript = (
        app_data
        / "brain"
        / conversation_id
        / ".system_generated"
        / "logs"
        / "transcript.jsonl"
    )
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        (FIXTURES / "duplicate_intents_transcript.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = AgyAdapter().parse_response(
        stdout="Final response.",
        stderr="",
        returncode=0,
        output_file=None,
        plan=_plan(tmp_path, log_file=log_file, app_data=app_data),
    )

    assert [call["name"] for call in result.tool_calls] == [
        "mcp__sources__query_wikipedia",
        "mcp__sources__query_wikipedia",
        "mcp__sources__search_text",
        "mcp__sources__query_wikipedia",
        "mcp__sources__query_wikipedia",
        "mcp__sources__search_grinchenko_1907",
        "mcp__sources__search_literary",
    ]
    assert [call["result"][0]["text"] for call in result.tool_calls] == [
        "wiki-section-error",
        "wiki-sections-output",
        "search-text-output",
        "wiki-section-1-output",
        "wiki-section-2-output",
        "grinchenko-output",
        "literary-output",
    ]


def _planner_intent(tool: str, query: str, *, step_index: int) -> dict[str, object]:
    return {
        "step_index": step_index,
        "type": "PLANNER_RESPONSE",
        "tool_calls": [
            {
                "name": "call_mcp_tool",
                "args": {
                    "Arguments": f'{{"query":"{query}"}}',
                    "ServerName": '"sources"',
                    "ToolName": f'"{tool}"',
                },
            }
        ],
    }


def _mcp_result(content: str, *, step_index: int) -> dict[str, object]:
    return {"step_index": step_index, "type": "MCP_TOOL", "content": content}


def test_pairing_preserves_orphan_mcp_result_without_planner_intent(
    tmp_path: Path,
) -> None:
    # #4761 Finding 3: an MCP result with no captured planner intent (e.g. a tool
    # whose ToolName failed to serialize) must be preserved as a result-only call,
    # never dropped — otherwise tool_call_count undercounts real executions.
    events = [
        _planner_intent("query_wikipedia", "Колядки", step_index=1),
        _mcp_result("out-A", step_index=2),
        _mcp_result("orphan-out", step_index=3),
    ]
    calls = agy_module._pair_transcript_by_step_index(
        events, transcript_path=tmp_path / "transcript.jsonl"
    )
    assert [call["name"] for call in calls] == ["mcp__sources__query_wikipedia", ""]
    assert [call["result"][0]["text"] for call in calls] == ["out-A", "orphan-out"]


def test_pairing_keeps_genuine_repeat_calls_distinct(tmp_path: Path) -> None:
    # #4761 Finding 3: the same tool+args issued AGAIN after its first result landed
    # is a genuine second execution — both results must be kept, not collapsed by a
    # global (tool, args) dedupe.
    events = [
        _planner_intent("query_wikipedia", "Колядки", step_index=1),
        _mcp_result("out-1", step_index=2),
        _planner_intent("query_wikipedia", "Колядки", step_index=3),
        _mcp_result("out-2", step_index=4),
    ]
    calls = agy_module._pair_transcript_by_step_index(
        events, transcript_path=tmp_path / "transcript.jsonl"
    )
    assert [call["name"] for call in calls] == [
        "mcp__sources__query_wikipedia",
        "mcp__sources__query_wikipedia",
    ]
    assert [call["result"][0]["text"] for call in calls] == ["out-1", "out-2"]


def test_pairing_dedupes_reemitted_pending_intent(tmp_path: Path) -> None:
    # A still-pending intent re-listed on a later planner turn (agy re-emission) is
    # NOT a new call: one intent, one result.
    events = [
        _planner_intent("query_wikipedia", "Колядки", step_index=1),
        _planner_intent("query_wikipedia", "Колядки", step_index=2),  # re-emit, still pending
        _mcp_result("out-1", step_index=3),
    ]
    calls = agy_module._pair_transcript_by_step_index(
        events, transcript_path=tmp_path / "transcript.jsonl"
    )
    assert [call["name"] for call in calls] == ["mcp__sources__query_wikipedia"]
    assert [call["result"][0]["text"] for call in calls] == ["out-1"]


def test_saved_tool_result_pointer_requires_prefix(tmp_path: Path) -> None:
    text = "bare pointer file:///etc/hosts"
    transcript = tmp_path / "transcript.jsonl"

    result = agy_module._inline_saved_tool_result_pointer(
        text,
        transcript_path=transcript,
    )

    assert result == text
    assert agy_module._SAVED_OUTPUT_POINTER_RE.search(text) is None


def test_render_writer_prompt_includes_agy_specific_directives() -> None:
    plan_path = linear_pipeline.plan_path_for("a1", "my-morning")
    plan = linear_pipeline.plan_check(plan_path)

    prompt = linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_path.read_text(encoding="utf-8"),
        knowledge_packet="Knowledge packet stub.",
        writer="agy-tools",
    )

    assert "## agy-tools writer directives" in prompt
    assert "Use `mcp_sources_*` tools directly." in prompt
    assert "Do NOT issue curl-via-Bash for MCP retrieval" in prompt
    assert "Allowed bash: NONE except `curl` against `http://127.0.0.1:8766/mcp`" in prompt


def test_render_writer_prompt_omits_agy_directives_for_other_writers() -> None:
    plan_path = linear_pipeline.plan_path_for("a1", "my-morning")
    plan = linear_pipeline.plan_check(plan_path)

    prompt = linear_pipeline.render_writer_prompt(
        plan=plan,
        plan_content=plan_path.read_text(encoding="utf-8"),
        knowledge_packet="Knowledge packet stub.",
        writer="claude-tools",
    )

    assert "## agy-tools writer directives" not in prompt
    assert "Do NOT issue curl-via-Bash for MCP retrieval" not in prompt


def _build(tmp_path: Path, *, model: str | None):
    return AgyAdapter().build_invocation(
        prompt="hello",
        mode="danger",
        cwd=tmp_path,
        model=model,
        task_id="t-1",
        session_id=None,
        tool_config=None,
    )


def _model_after_flag(plan) -> str | None:
    if "--model" not in plan.cmd:
        return None
    return plan.cmd[plan.cmd.index("--model") + 1]


def _value_after_flag(plan, flag: str) -> str | None:
    if flag not in plan.cmd:
        return None
    return plan.cmd[plan.cmd.index(flag) + 1]


def test_build_invocation_sets_print_timeout(tmp_path: Path) -> None:
    plan = _build(tmp_path, model=None)
    assert _value_after_flag(plan, "--print-timeout") == agy_module._AGY_PRINT_TIMEOUT


def test_build_invocation_maps_model_slug(tmp_path: Path) -> None:
    # Runtime slugs pass through as ``agy models`` ids (verified 2026-07-21 for 3.6).
    plan = _build(tmp_path, model="gemini-3.6-flash-high")
    assert _model_after_flag(plan) == "gemini-3.6-flash-high"


def test_build_invocation_accepts_display_string(tmp_path: Path) -> None:
    # Legacy display labels normalize to the slug form.
    plan = _build(tmp_path, model="Gemini 3.8 Flash (High)")
    assert _model_after_flag(plan) == "gemini-3.8-flash-high"


def test_build_invocation_unknown_explicit_model_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported AGY model") as error:
        _build(tmp_path, model="gemini-9.9-pro-preview")
    assert "gemini-3.8-flash-high" not in str(error.value)


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("gemini-9.9-pro-preview", "For Gemini Pro, use `--model gemini-3.1-pro-high`."),
        (
            "gemini-9.9-flash-preview",
            "Accepted AGY model ids: " + ", ".join(f"`{slug}`" for slug in agy_module._AGY_MODEL_SLUGS) + ".",
        ),
        (
            "unknown-local-model",
            "Accepted AGY model ids: " + ", ".join(f"`{slug}`" for slug in agy_module._AGY_MODEL_SLUGS) + ".",
        ),
    ],
)
def test_unknown_model_suggestion(model: str, expected: str) -> None:
    assert agy_module.unknown_model_suggestion(model) == expected


def test_delegate_dispatch_rejects_unknown_agy_model_before_launch(monkeypatch, capsys) -> None:
    from scripts import delegate

    real_popen = delegate.subprocess.Popen

    def unexpected_dispatch(*args, **kwargs):
        command = args[0]
        if isinstance(command, list) and "_worker" in command:
            pytest.fail("unknown AGY model reached worker dispatch")
        return real_popen(*args, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "Popen", unexpected_dispatch)
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--task-id",
            "unknown-agy-model",
            "--agent",
            "agy",
            "--model",
            "gemini-9.9-pro-preview",
            "--prompt",
            "test",
        ]
    )

    result = delegate.cmd_dispatch(args)

    assert result == 2
    err = capsys.readouterr().err
    assert "For Gemini Pro, use `--model gemini-3.1-pro-high`." in err
    assert "gemini-3.8-flash-high" not in err


def test_build_invocation_none_model_falls_back_to_default(tmp_path: Path) -> None:
    # No model -> resolves the adapter default slug.
    plan = _build(tmp_path, model=None)
    assert _model_after_flag(plan) == "gemini-3.8-flash-high"


def test_build_invocation_maps_pro_preview_to_supported_slug(tmp_path: Path) -> None:
    plan = _build(tmp_path, model="gemini-3.1-pro-preview")
    assert _model_after_flag(plan) == "gemini-3.1-pro-high"


@pytest.mark.parametrize("tier", ["high", "medium", "low"])
@pytest.mark.parametrize("display_label", [False, True])
def test_build_invocation_remaps_retired_flash_aliases(tmp_path: Path, tier: str, display_label: bool) -> None:
    model = f"Gemini 3.5 Flash ({tier.title()})" if display_label else f"gemini-3.5-flash-{tier}"
    plan = _build(tmp_path, model=model)
    assert _model_after_flag(plan) == f"gemini-3.8-flash-{tier}"
    assert f"gemini-3.5-flash-{tier}" not in agy_module._AGY_MODEL_SLUGS


# --- #7994: agy 2026-09 transcript shape (tool results are ``type: GENERIC``) ---

GENERIC_CONVERSATION_ID = "00000000-aaaa-4bbb-8ccc-000000000001"
GENERIC_PROMPT = "# V7 UPGRADE writer — preserve and expand an existing module\n\nMode: upgrade."


def _write_generic_transcript(app_data: Path, conversation_id: str = GENERIC_CONVERSATION_ID) -> Path:
    transcript = agy_module._brain_transcript_path(app_data, conversation_id)
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        (FIXTURES / "generic_results_transcript.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return transcript


def _parse_generic(
    tmp_path: Path,
    *,
    log_text: str | None,
    cmd: list[str] | None = None,
):
    app_data = tmp_path / "antigravity-cli"
    log_file = tmp_path / "agy.log"
    if log_text is not None:
        log_file.write_text(log_text, encoding="utf-8")
    _write_generic_transcript(app_data)
    plan = _plan(tmp_path, log_file=log_file, app_data=app_data, cmd=cmd)
    return AgyAdapter().parse_response(
        stdout="module text", stderr="", returncode=0, output_file=None, plan=plan
    )


def test_parse_response_pairs_generic_results_with_sources_mcp_calls(tmp_path: Path) -> None:
    # Writer 195757 grounded via search_text/verify_words, yet the adapter wrote
    # writer_tool_calls.json as [] because results were no longer ``MCP_TOOL``.
    result = _parse_generic(
        tmp_path,
        log_text=f"I0919 server.go:1185] Created conversation {GENERIC_CONVERSATION_ID}\n",
    )

    assert [call["name"] for call in result.tool_calls] == [
        "mcp__sources__search_text",
        "mcp__sources__verify_words",
        "mcp__sources__query_pravopys",
        "mcp__sources__search_text",
    ]
    assert result.tool_calls[0]["arguments"] == {"query": "м'який знак пом'якшує"}
    texts = [call["result"][0]["text"] for call in result.tool_calls]
    assert "М'який знак пом'якшує" in texts[0]
    assert texts[1].startswith("Batch verification: 3 words")
    assert "Tool call failed: query_pravopys" in texts[2]
    assert "Апостроф пишемо після губних" in texts[3]
    # Builtin (view_file / run_command) results must never be credited to MCP calls.
    assert not any("BUILTIN" in text for text in texts)


def test_generic_transcript_satisfies_tools_writer_runtime_gate(tmp_path: Path) -> None:
    result = _parse_generic(
        tmp_path,
        log_text=f"I0919 session.go:177] Print mode: conversation={GENERIC_CONVERSATION_ID}, sending message\n",
    )
    events: list[tuple[str, dict[str, object]]] = []

    summary = linear_pipeline.emit_writer_response_telemetry(
        "module text",
        writer="agy-tools",
        module="special-signs",
        sections=[],
        tool_calls=result.tool_calls,
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert summary["tool_calls_total"] >= 1
    assert summary["verify_words_calls"] == 1
    tools = [fields["tool"] for event, fields in events if event == "writer_tool_call"]
    assert "search_text" in tools
    linear_pipeline._enforce_tools_writer_runtime_gate(
        writer="agy-tools", module="special-signs", phase_writer_summary=summary
    )


@pytest.mark.parametrize(
    "line",
    [
        "I0919 server.go:3133] GetConversationDetail: found conversation {id} (active=true)",
        "I0919 conversation_manager.go:654] Forwarding user message to conversation {id} (items=1, media=0)",
        "I0919 server.go:1194] Starting conversation update stream for {id}",
        "I0919 log.go:1] map[blocking:false cascade_id:{id} cascade_send_latency_ms:1]",
    ],
)
def test_conversation_id_recovered_from_alternate_log_phrases(tmp_path: Path, line: str) -> None:
    log_file = tmp_path / "agy.log"
    log_file.write_text(
        "I0919 log.go:1] trajectory_id:f5b120e3-eb45-4ea3-81a4-d42f55efd849\n"
        + line.format(id=GENERIC_CONVERSATION_ID)
        + "\n",
        encoding="utf-8",
    )
    assert agy_module._conversation_id_from_log(log_file) == GENERIC_CONVERSATION_ID


@pytest.mark.parametrize("log_text", [None, "I0919 no conversation id in this log\n"])
def test_log_without_conversation_id_binds_no_transcript(tmp_path: Path, log_text: str | None) -> None:
    # A brain transcript opening with this run's own prompt is present, but the
    # runtime log names no conversation: nothing binds, nothing is credited.
    result = _parse_generic(tmp_path, log_text=log_text, cmd=["agy", "-p", GENERIC_PROMPT])
    assert result.tool_calls == []
    assert result.ok is False
    assert result.stderr_excerpt.splitlines()[0] == agy_module.AGY_TRANSCRIPT_UNBOUND


def test_generic_pairing_dedupes_reemitted_pending_intent(tmp_path: Path) -> None:
    events = [
        _planner_intent("query_wikipedia", "Колядки", step_index=1),
        _planner_intent("query_wikipedia", "Колядки", step_index=2),  # re-emit, still pending
        {"step_index": 3, "type": "GENERIC", "content": "out-1"},
        _planner_intent("query_wikipedia", "Колядки", step_index=4),  # genuine repeat
        {"step_index": 5, "type": "GENERIC", "content": "out-2"},
        {"step_index": 6, "type": "GENERIC", "content": "not a tool result"},
    ]
    calls = agy_module._pair_transcript_generic_results(
        events, transcript_path=tmp_path / "transcript.jsonl"
    )
    assert [call["result"][0]["text"] for call in calls] == ["out-1", "out-2"]


# --- per-attempt scoped home (#8617) ---------------------------------------------------


def _build_with(tmp_path: Path, tool_config: dict | None):
    return AgyAdapter().build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="t-scoped",
        session_id=None,
        tool_config=tool_config,
    )


def test_agy_home_override_sets_home_and_app_data_dir(tmp_path: Path) -> None:
    scoped = tmp_path / "att.agy-home"
    plan = _build_with(tmp_path, {"agy_home_override": str(scoped)})
    assert plan.env_overrides["HOME"] == str(scoped)
    assert plan.env_overrides["AGY_APP_DATA_DIR"] == str(scoped / ".gemini" / "antigravity-cli")
    assert "AGY_RUNTIME_LOG_FILE" in plan.env_overrides


@pytest.mark.parametrize("tool_config", [None, {}, {"mcp_server_names": ["sources"]}, {"agy_home_override": ""}])
def test_no_agy_home_override_leaves_home_and_app_data_alone(tmp_path: Path, tool_config: dict | None) -> None:
    plan = _build_with(tmp_path, tool_config)
    assert set(plan.env_overrides) == {"AGY_RUNTIME_LOG_FILE"}


def test_transcript_path_follows_agy_app_data_dir_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_home = tmp_path / "real-home"
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: real_home))
    scoped = tmp_path / "att.agy-home"
    plan = _build_with(tmp_path, {"agy_home_override": str(scoped)})
    log_file = Path(plan.env_overrides["AGY_RUNTIME_LOG_FILE"])
    log_file.write_text(f"conversation={CONVERSATION_ID}\n", encoding="utf-8")
    try:
        # The same conversation id exists under the real home too: the scoped one must win.
        _write_transcript(real_home / ".gemini" / "antigravity-cli")
        _write_transcript(scoped / ".gemini" / "antigravity-cli")
        found = agy_module._transcript_path_from_plan(plan)
    finally:
        log_file.unlink(missing_ok=True)
    assert found == agy_module._brain_transcript_path(scoped / ".gemini" / "antigravity-cli", CONVERSATION_ID)


def test_transcript_path_defaults_to_real_home_without_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_home = tmp_path / "real-home"
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: real_home))
    plan = _build_with(tmp_path, None)
    log_file = Path(plan.env_overrides["AGY_RUNTIME_LOG_FILE"])
    log_file.write_text(f"conversation={CONVERSATION_ID}\n", encoding="utf-8")
    try:
        _write_transcript(real_home / ".gemini" / "antigravity-cli")
        found = agy_module._transcript_path_from_plan(plan)
    finally:
        log_file.unlink(missing_ok=True)
    assert found == agy_module._brain_transcript_path(real_home / ".gemini" / "antigravity-cli", CONVERSATION_ID)


# #8502/#8503: stderr verbatim from dispatch ``ci-select-quickwin`` (agy 1.2.8,
# 2026-09-22) — agy killed the agent's backgrounded pytest and exited 0.
_ABANDONED_STDERR = (
    "root agent idle; waiting up to 5s for 1 background task(s)\nterminating 1 background task(s) on exit"
)


@pytest.mark.parametrize(
    ("stderr", "reason"),
    [
        (_ABANDONED_STDERR, agy_module.AGY_BACKGROUND_TASK_ABANDONED),
        (
            "terminating 2 background task(s) and 1 daemon task(s) on exit",
            agy_module.AGY_BACKGROUND_TASK_ABANDONED,
        ),
        (
            "[agy] print timeout after 2h0m0s with turn in progress; returning partial output",
            agy_module.AGY_PRINT_TIMEOUT_PARTIAL,
        ),
    ],
)
def test_parse_response_fails_run_cut_off_mid_work(stderr: str, reason: str) -> None:
    result = AgyAdapter().parse_response(
        stdout="Waiting for task-220 to complete.",
        stderr=stderr,
        returncode=0,
        output_file=None,
        plan=None,
    )

    assert result.ok is False
    assert result.response == ""
    assert result.stderr_excerpt is not None
    assert result.stderr_excerpt.splitlines()[0] == reason


def test_parse_response_keeps_run_whose_only_stop_was_a_daemon(tmp_path: Path) -> None:
    plan = _background_plan(tmp_path, CONVERSATION_ID, _fixture_lines("verify_words_transcript.jsonl"))

    result = AgyAdapter().parse_response(
        stdout="RESULT=CANARY_DONE_8502",
        stderr="terminating 0 background task(s) and 1 daemon task(s) on exit",
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert result.ok is True
    assert result.response == "RESULT=CANARY_DONE_8502"


# Live probes, agy 1.2.10 (2026-09-24). "finished": a 45s command was
# backgrounded, the agent idled, the task-finished system message arrived and
# the agent replied with the output. "abandoned": the 120s command outlived a
# 40s --print-timeout and agy killed it.
_FINISHED_CONVERSATION_ID = "3aca585b-1812-499a-8884-4a49d135a486"
_ABANDONED_CONVERSATION_ID = "44c10a19-f720-4b45-a838-64076907b9d7"
_IDLE_WAIT_STDERR = "root agent idle; waiting up to 2h0m0s for 1 background task(s)"


def _background_plan(tmp_path: Path, conversation_id: str, transcript_lines: list[str]) -> InvocationPlan:
    app_data = tmp_path / "antigravity-cli"
    transcript = agy_module._brain_transcript_path(app_data, conversation_id)
    transcript.parent.mkdir(parents=True)
    transcript.write_text("\n".join(transcript_lines) + "\n", encoding="utf-8")
    log_file = tmp_path / "agy.log"
    log_file.write_text(f"I0924 server.go:1185] Created conversation {conversation_id}\n", encoding="utf-8")
    return _plan(tmp_path, log_file=log_file, app_data=app_data)


def _fixture_lines(name: str) -> list[str]:
    return (FIXTURES / name).read_text(encoding="utf-8").splitlines()


def test_parse_response_accepts_background_work_with_completion_evidence(tmp_path: Path) -> None:
    plan = _background_plan(
        tmp_path, _FINISHED_CONVERSATION_ID, _fixture_lines("background_task_finished_transcript.jsonl")
    )
    stdout = "I have launched the command and am waiting for it to finish.\nPROBE_DONE_7731"

    result = AgyAdapter().parse_response(
        stdout=stdout, stderr=_IDLE_WAIT_STDERR, returncode=0, output_file=None, plan=plan
    )

    assert result.ok is True
    assert result.response == stdout


@pytest.mark.parametrize("stderr", ["root agent idle; waiting up to 5s for 1 background task(s)", ""])
def test_parse_response_rejects_interim_waiting_reply_without_transcript(stderr: str) -> None:
    # Reviewer reproduction (#8502 r2): exit 0, the agent's interim reply and
    # at most the idle-wait diagnostic previously parsed as ok=True. With no
    # transcript bound to the run there is no evidence at all.
    result = AgyAdapter().parse_response(
        stdout="Waiting for task-220 to complete.",
        stderr=stderr,
        returncode=0,
        output_file=None,
        plan=None,
    )

    assert result.ok is False
    assert result.response == ""
    assert result.stderr_excerpt.splitlines()[0] == agy_module.AGY_TRANSCRIPT_UNBOUND


def test_parse_response_rejects_unfinished_task_even_with_empty_stderr(tmp_path: Path) -> None:
    # Reviewer reproduction (#8502 r3): the abandoned transcript with EMPTY
    # stderr parsed as ok=True because the check keyed on the idle-wait line.
    plan = _background_plan(
        tmp_path, _ABANDONED_CONVERSATION_ID, _fixture_lines("background_task_abandoned_transcript.jsonl")
    )

    result = AgyAdapter().parse_response(
        stdout="I have started the command and will wait for it to finish.",
        stderr="",
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert result.ok is False
    assert result.response == ""
    assert result.stderr_excerpt.splitlines()[0] == agy_module.AGY_BACKGROUND_TASK_UNCONFIRMED


def test_parse_response_never_borrows_earlier_same_prompt_run(tmp_path: Path) -> None:
    # Reviewer reproduction (#8502 r3): this run's log names its conversation,
    # but that transcript is missing; an EARLIER finished run with the same
    # prompt sits in brain/. Its evidence must not settle this run.
    app_data = tmp_path / "antigravity-cli"
    earlier = agy_module._brain_transcript_path(app_data, _FINISHED_CONVERSATION_ID)
    earlier.parent.mkdir(parents=True)
    earlier.write_text(
        "\n".join(_fixture_lines("background_task_finished_transcript.jsonl")) + "\n", encoding="utf-8"
    )
    log_file = tmp_path / "agy.log"
    log_file.write_text(f"I0924 server.go:1185] Created conversation {_ABANDONED_CONVERSATION_ID}\n", encoding="utf-8")
    prompt = "Run this exact shell command: `sleep 45 && echo PROBE_DONE_7731`."
    plan = _plan(tmp_path, log_file=log_file, app_data=app_data, cmd=["agy", "-p", prompt])

    result = AgyAdapter().parse_response(
        stdout="Waiting for task-220 to complete.", stderr="", returncode=0, output_file=None, plan=plan
    )

    assert result.ok is False
    assert result.stderr_excerpt.splitlines()[0] == agy_module.AGY_TRANSCRIPT_UNBOUND


_RETRY_CONVERSATION_ID = "5953861f-3323-4774-b095-c20d69cc13c7"


@pytest.mark.parametrize(
    ("log_names_retry", "reason"),
    [(False, agy_module.AGY_TRANSCRIPT_UNBOUND), (True, agy_module.AGY_BACKGROUND_TASK_UNCONFIRMED)],
)
def test_same_second_retry_never_borrows_earlier_finished_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, log_names_retry: bool, reason: str
) -> None:
    # Reviewer reproduction (#8502 r4): an earlier run of the same prompt opened
    # its conversation at 1000.1 and finished; the retry spawned at 1000.9. The
    # removed prompt fallback compared whole seconds and credited the earlier
    # run's completion evidence to the retry's interim reply (ok=True).
    _fake_agy(tmp_path, monkeypatch, "1.2.10")
    finished = _fixture_lines("background_task_finished_transcript.jsonl")
    prompt = json.loads(finished[0])["content"].removeprefix("<USER_REQUEST>\n").removesuffix("\n</USER_REQUEST>")
    opened_this_second = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    app_data = tmp_path / "antigravity-cli"
    plan = AgyAdapter().build_invocation(
        prompt=prompt,
        mode="danger",
        cwd=tmp_path,
        model=None,
        task_id="t-retry",
        session_id=None,
        tool_config={"agy_home_override": str(tmp_path / "agy-home")},
    )
    plan.env_overrides["AGY_APP_DATA_DIR"] = str(app_data)
    earlier = [re.sub(r'"created_at": "[^"]+"', f'"created_at": "{opened_this_second}"', line) for line in finished]
    transcripts = {_FINISHED_CONVERSATION_ID: earlier}
    if log_names_retry:
        # The retry's own conversation stopped at its interim reply.
        transcripts[_RETRY_CONVERSATION_ID] = [
            line.replace(_FINISHED_CONVERSATION_ID, _RETRY_CONVERSATION_ID) for line in earlier[:4]
        ]
    for conversation_id, lines in transcripts.items():
        transcript = agy_module._brain_transcript_path(app_data, conversation_id)
        transcript.parent.mkdir(parents=True)
        transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log_file = Path(plan.env_overrides["AGY_RUNTIME_LOG_FILE"])
    log_file.write_text(
        f"I0924 server.go:1239] Created conversation {_RETRY_CONVERSATION_ID}\n" if log_names_retry else "",
        encoding="utf-8",
    )
    try:
        result = AgyAdapter().parse_response(
            stdout="I have launched the command and am waiting for it to finish.",
            stderr="",
            returncode=0,
            output_file=None,
            plan=plan,
        )
    finally:
        log_file.unlink(missing_ok=True)

    assert result.ok is False
    assert result.response == ""
    assert result.stderr_excerpt.splitlines()[0] == reason


def test_parse_response_rejects_claimed_wait_with_no_task_in_transcript(tmp_path: Path) -> None:
    plan = _background_plan(tmp_path, CONVERSATION_ID, _fixture_lines("verify_words_transcript.jsonl"))

    result = AgyAdapter().parse_response(
        stdout="Waiting for task-220 to complete.",
        stderr=_IDLE_WAIT_STDERR,
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert result.ok is False
    assert result.stderr_excerpt.splitlines()[0] == agy_module.AGY_BACKGROUND_TASK_UNCONFIRMED


def test_parse_response_rejects_background_task_that_never_finished(tmp_path: Path) -> None:
    plan = _background_plan(
        tmp_path, _ABANDONED_CONVERSATION_ID, _fixture_lines("background_task_abandoned_transcript.jsonl")
    )

    result = AgyAdapter().parse_response(
        stdout="I have started the command and will wait for it to finish.",
        stderr="root agent idle; waiting up to 40s for 1 background task(s)",
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert result.ok is False
    assert result.stderr_excerpt.splitlines()[0] == agy_module.AGY_BACKGROUND_TASK_UNCONFIRMED


def test_parse_response_rejects_finished_task_with_no_reply_after_it(tmp_path: Path) -> None:
    lines = _fixture_lines("background_task_finished_transcript.jsonl")[:-1]  # drop the final reply
    plan = _background_plan(tmp_path, _FINISHED_CONVERSATION_ID, lines)

    result = AgyAdapter().parse_response(
        stdout="I have launched the command and am waiting for it to finish.",
        stderr=_IDLE_WAIT_STDERR,
        returncode=0,
        output_file=None,
        plan=plan,
    )

    assert result.ok is False
    assert result.stderr_excerpt.splitlines()[0] == agy_module.AGY_BACKGROUND_TASK_UNCONFIRMED


# Live write canary, agy 1.2.10 (2026-09-24, #8502 r3), run through
# ``runner.invoke("agy", mode="danger")`` with this adapter: the 60s
# ``sleep 60 && echo CANARY_8502_R3_DONE > canary.txt`` was backgrounded as
# task-18, the agent replied "Waiting 60 seconds…", the task-finished message
# arrived at step 20, and the agent then committed (b4d19d2) and replied. The
# runtime returned ok=True with stderr "root agent idle; waiting up to 2h0m0s
# for 1 background task(s)". Every event, step index, status and timestamp is
# kept; local paths are synthetic (/work/repo, /agy-app-data), model
# ``thinking`` is dropped, and the read-only exploration of steps 1-16 is
# redacted.
_CANARY_CONVERSATION_ID = "01a753b2-d67a-4b03-99cc-358e6493e70b"
_CANARY_FIXTURE = f"background_task_write_canary_{_CANARY_CONVERSATION_ID}.jsonl"
_CANARY_STDOUT = "Waiting 60 seconds for the command to finish...\nb4d19d2 (HEAD -> main) canary 8502-r3\nCANARY_8502_R3_DONE"


@pytest.mark.parametrize("stderr", [_IDLE_WAIT_STDERR, ""])
def test_parse_response_accepts_live_write_canary(tmp_path: Path, stderr: str) -> None:
    plan = _background_plan(tmp_path, _CANARY_CONVERSATION_ID, _fixture_lines(_CANARY_FIXTURE))

    result = AgyAdapter().parse_response(
        stdout=_CANARY_STDOUT, stderr=stderr, returncode=0, output_file=None, plan=plan
    )

    assert result.ok is True
    assert result.response == _CANARY_STDOUT


def test_parse_response_rejects_live_write_canary_cut_before_task_finished(tmp_path: Path) -> None:
    # The same run truncated right after the interim reply (step 19): the task
    # never finished, whatever stderr says.
    lines = [line for line in _fixture_lines(_CANARY_FIXTURE) if int(json.loads(line)["step_index"]) <= 19]
    plan = _background_plan(tmp_path, _CANARY_CONVERSATION_ID, lines)

    result = AgyAdapter().parse_response(
        stdout="Waiting 60 seconds for the command to finish...", stderr="", returncode=0, output_file=None, plan=plan
    )

    assert result.ok is False
    assert result.stderr_excerpt.splitlines()[0] == agy_module.AGY_BACKGROUND_TASK_UNCONFIRMED


def _fake_agy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version_output: str) -> Path:
    fake = tmp_path / "bin" / "agy"
    fake.parent.mkdir()
    fake.write_text(f"#!/bin/sh\nprintf '%s\\n' '{version_output}'\n", encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setattr(agy_module.shutil, "which", lambda name: str(fake) if name == "agy" else None)
    agy_module._agy_version.cache_clear()
    return fake


@pytest.mark.parametrize(
    ("version_output", "code"),
    [("1.2.8", "agy_version_unsupported"), ("agy dev build", "agy_version_unverified")],
)
def test_build_invocation_refuses_agy_without_background_wait(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version_output: str, code: str
) -> None:
    _fake_agy(tmp_path, monkeypatch, version_output)

    with pytest.raises(ValueError, match=code):
        _build(tmp_path, model=None)


@pytest.mark.parametrize("version_output", ["1.2.9", "1.2.10", "2.0.0"])
def test_build_invocation_accepts_agy_with_background_wait(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version_output: str
) -> None:
    fake = _fake_agy(tmp_path, monkeypatch, version_output)

    plan = _build(tmp_path, model=None)

    assert plan.cmd[0] == str(fake.resolve())


def test_parse_response_fails_structured_run_cut_off_mid_work(tmp_path: Path) -> None:
    schema = {"type": "object", "properties": {"verdict": {"type": "string"}}, "required": ["verdict"]}
    plan = InvocationPlan(
        cmd=["agy"],
        cwd=tmp_path,
        stdin_payload="",
        output_file=None,
        env_overrides={},
        env_unsets=(),
        liveness_paths=(),
        metadata={"output_schema": schema},
    )
    envelope = '{"status": "SUCCESS", "structured_output": {"verdict": "APPROVE"}}'

    result = AgyAdapter().parse_response(
        stdout=envelope, stderr=_ABANDONED_STDERR, returncode=0, output_file=None, plan=plan
    )

    assert result.ok is False
    assert result.stderr_excerpt.splitlines()[0] == agy_module.AGY_BACKGROUND_TASK_ABANDONED
