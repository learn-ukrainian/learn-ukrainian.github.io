from __future__ import annotations

from pathlib import Path

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
