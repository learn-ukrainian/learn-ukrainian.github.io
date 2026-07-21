from __future__ import annotations

from pathlib import Path

from scripts.agent_runtime.adapters import agy as agy_module
from scripts.agent_runtime.adapters.agy import AgyAdapter
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.build import linear_pipeline

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "agy"
CONVERSATION_ID = "7cd3ba85-817f-4a03-8223-1ff39ca42419"


def _plan(tmp_path: Path, *, log_file: Path, app_data: Path) -> InvocationPlan:
    return InvocationPlan(
        cmd=["agy"],
        cwd=tmp_path,
        stdin_payload="",
        output_file=None,
        env_overrides={
            "AGY_RUNTIME_LOG_FILE": str(log_file),
            "AGY_APP_DATA_DIR": str(app_data),
        },
        env_unsets=(),
        liveness_paths=(log_file,),
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
    plan = _build(tmp_path, model="Gemini 3.5 Flash (High)")
    assert _model_after_flag(plan) == "gemini-3.5-flash-high"


def test_build_invocation_unknown_model_falls_back_to_default(tmp_path: Path) -> None:
    # A stale/unknown identifier degrades to the adapter default rather than
    # passing an invalid --model value.
    plan = _build(tmp_path, model="tui-controlled")
    assert _model_after_flag(plan) == "gemini-3.6-flash-high"


def test_build_invocation_none_model_falls_back_to_default(tmp_path: Path) -> None:
    # No model -> resolves the adapter default slug.
    plan = _build(tmp_path, model=None)
    assert _model_after_flag(plan) == "gemini-3.6-flash-high"
