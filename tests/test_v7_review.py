from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.build import linear_pipeline, v7_review
from scripts.common.thresholds import QG_DIMS


def _lesson(path: Path, *, writer: str = "gemini-tools") -> Path:
    path.write_text(
        f"""---
level: A1
slug: my-morning
writer: {writer}
---

# Мій ранок

\"Я прокидаюся о сьомій\" and then I make coffee.
""",
        encoding="utf-8",
    )
    return path


def _review_response(dim: str) -> str:
    return json.dumps(
        {
            "score": 8.5,
            "evidence": f"\"{dim} quote one\"",
            "evidence_quotes": [f"{dim} quote one", f"{dim} quote two"],
            "rubric_mapping": f"{dim} maps to the fixture rubric.",
            "verdict": "PASS",
        }
    )


@pytest.fixture(autouse=True)
def _cheap_packet(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        v7_review.linear_pipeline,
        "build_knowledge_packet",
        lambda **_kwargs: "knowledge packet",
    )


@pytest.fixture()
def fake_reviewer(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    def invoke(
        prompt: str,
        reviewer: str,
        *,
        dim: str,
        writer_under_review: str,
        module: str,
        event_sink: Any,
        **kwargs: Any,
    ) -> str:
        calls.append(
            {
                "prompt": prompt,
                "reviewer": reviewer,
                "dim": dim,
                "writer_under_review": writer_under_review,
                "module": module,
                "kwargs": kwargs,
            }
        )
        response = _review_response(dim)
        linear_pipeline.parse_review_response(
            response,
            dim,
            reviewer=reviewer,
            module=module,
            writer_under_review=writer_under_review,
            event_sink=event_sink,
        )
        return response

    monkeypatch.setattr(v7_review.linear_pipeline, "invoke_reviewer_dim", invoke)
    return calls


def _events_from_stdout(stdout: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in stdout.splitlines() if line.strip()]


def test_v7_review_refuses_self_review(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    content = _lesson(tmp_path / "claude.md", writer="claude-tools")

    exit_code = v7_review.main(
        [
            "a1",
            "my-morning",
            "--content",
            str(content),
            "--reviewer",
            "claude-tools",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Self-review refused" in captured.err


def test_v7_review_success_emits_all_dim_events(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    fake_reviewer: list[dict[str, Any]],
) -> None:
    content = _lesson(tmp_path / "gemini.md", writer="gemini-tools")

    exit_code = v7_review.main(
        [
            "a1",
            "my-morning",
            "--content",
            str(content),
            "--reviewer",
            "claude-tools",
        ]
    )

    captured = capsys.readouterr()
    events = _events_from_stdout(captured.out)
    dim_events = [event for event in events if event["event"] == "reviewer_dim_evidence"]
    summaries = [event for event in events if event["event"] == "phase_review_summary"]

    assert exit_code == 0
    assert [call["dim"] for call in fake_reviewer] == list(QG_DIMS)
    assert len(dim_events) == len(QG_DIMS)
    assert {event["dim"] for event in dim_events} == set(QG_DIMS)
    assert all(event["reviewer"] == "claude-tools" for event in dim_events)
    assert all(event["writer_under_review"] == "gemini-tools" for event in dim_events)
    assert summaries[0]["dims_scored"] == len(QG_DIMS)
    assert summaries[0]["dims_with_evidence"] == len(QG_DIMS)


def test_v7_review_telemetry_out_writes_file_not_stdout(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    fake_reviewer: list[dict[str, Any]],
) -> None:
    content = _lesson(tmp_path / "gpt55.md", writer="codex-tools")
    telemetry = tmp_path / "review.jsonl"

    exit_code = v7_review.main(
        [
            "a1",
            "my-morning",
            "--content",
            str(content),
            "--reviewer",
            "gemini-tools",
            "--telemetry-out",
            str(telemetry),
        ]
    )

    captured = capsys.readouterr()
    events = [json.loads(line) for line in telemetry.read_text("utf-8").splitlines()]
    dim_events = [event for event in events if event["event"] == "reviewer_dim_evidence"]

    assert exit_code == 0
    assert captured.out == ""
    assert len(fake_reviewer) == len(QG_DIMS)
    assert len(dim_events) == len(QG_DIMS)
    assert events[-1]["event"] == "module_done"
