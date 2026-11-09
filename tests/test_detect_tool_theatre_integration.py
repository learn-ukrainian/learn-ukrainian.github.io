from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.result import Result
from build import linear_pipeline


def _events(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_runtime_tool_calls_now_returns_real_data(tmp_path: Path) -> None:
    result = Result(
        ok=True,
        agent="claude",
        model="claude-opus-4-7",
        mode="workspace-write",
        response=(
            '<plan_reasoning section="vocab">'
            "`verify_words` checked."
            "</plan_reasoning>"
        ),
        stderr_excerpt=None,
        duration_s=1.0,
        session_id="session-123",
        rate_limited=False,
        stalled=False,
        returncode=0,
        tool_calls=[
            {
                "name": "mcp__sources__verify_words",
                "arguments": {"words": ["ранок"]},
                "output_summary": "verified",
                "timestamp": "2026-05-07T10:00:00Z",
            }
        ],
    )

    calls = linear_pipeline._runtime_tool_calls(result)

    assert len(calls) == 1
    assert calls[0]["name"] == "mcp__sources__verify_words"
    assert linear_pipeline.detect_tool_theatre(result.response, calls) == []


def test_phase_writer_summary_counts_runtime_tool_calls(tmp_path: Path) -> None:
    writer_output = (
        '<plan_reasoning section="vocab">'
        "`verify_words` checked."
        "</plan_reasoning>"
    )
    result = Result(
        ok=True,
        agent="claude",
        model="claude-opus-4-7",
        mode="workspace-write",
        response=writer_output,
        stderr_excerpt=None,
        duration_s=1.0,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        tool_calls=[
            {
                "name": "mcp__sources__verify_words",
                "arguments": {"words": ["ранок"]},
                "output_summary": "verified",
                "timestamp": "2026-05-07T10:00:00Z",
            }
        ],
    )
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        summary = linear_pipeline.emit_writer_response_telemetry(
            writer_output,
            writer="claude-tools",
            module="a1/my-morning",
            sections=["vocab"],
            tool_calls=linear_pipeline._runtime_tool_calls(result),
        )

    events = _events(telemetry)
    phase_summary = next(
        event for event in events if event["event"] == "phase_writer_summary"
    )
    assert summary["tool_calls_total"] == 1
    assert summary["verify_words_calls"] == 1
    assert summary["tool_theatre_violations"] == []
    assert phase_summary["tool_calls_total"] == 1
    assert phase_summary["tool_theatre_violations"] == []
