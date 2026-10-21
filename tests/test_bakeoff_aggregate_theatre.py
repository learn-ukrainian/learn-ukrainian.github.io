from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.audit import bakeoff_aggregate

CONTENT_DIMS = bakeoff_aggregate.CONTENT_DIMS


def _write_jsonl(path: Path, events: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(event, ensure_ascii=False) for event in events) + "\n", "utf-8")


def _writer_markdown(writer: str, *, tool_citation: bool = False) -> str:
    words = " ".join(f"{writer} ранок школа дім кава" for _index in range(30))
    reasoning = ""
    if tool_citation:
        reasoning = '<plan_reasoning section="intro">Checked with `mcp__sources__verify_words`.</plan_reasoning>\n\n'
    return f"---\nlevel: A1\nslug: my-morning\n---\n\n# {writer}\n\n{reasoning}{words}\n"


def _writer_events(
    writer: str,
    *,
    calls: int = 3,
    theatre_count: int = 0,
    emit_theatre_event: bool = False,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = [
        {
            "event": "writer_cot_emit",
            "writer": writer,
            "module": "a1/my-morning",
            "section": "intro",
            "block_present": True,
            "fields_filled": ["word_budget", "plan_vocab", "register", "teaching_sequence"],
        }
    ]
    for index in range(calls):
        events.append(
            {
                "event": "writer_tool_call",
                "writer": writer,
                "module": "a1/my-morning",
                "tool": "verify_words" if index == 0 else "search_definitions",
                "result_summary": {"verified": 1},
            }
        )
    if emit_theatre_event:
        events.append(
            {
                "event": "writer_tool_theatre",
                "writer": writer,
                "module": "a1/my-morning",
                "violations": ["verify_words"],
            }
        )
    events.extend(
        [
            {
                "event": "writer_end_gate",
                "writer": writer,
                "module": "a1/my-morning",
                "gate_present": True,
            },
            {
                "event": "phase_writer_summary",
                "writer": writer,
                "module": "a1/my-morning",
                "sections_total": 1,
                "sections_with_cot": 1,
                "tool_calls_total": calls,
                "verify_words_calls": 1 if calls else 0,
                "end_gate_fired": True,
                "tool_theatre_violation_count": theatre_count,
            },
        ]
    )
    return events


def _review_events(
    writer: str,
    reviewer: str,
    scores: list[float],
    *,
    reviewer_fixes_unparseable: bool = False,
    weighted_score: float | None = None,
) -> list[dict[str, Any]]:
    events = [
        {
            "event": "reviewer_dim_evidence",
            "reviewer": reviewer,
            "module": "a1/my-morning",
            "writer_under_review": writer,
            "dim": dim,
            "evidence_quotes": ["one", "two"],
            "score": score,
        }
        for dim, score in zip(CONTENT_DIMS, scores, strict=True)
    ]
    if reviewer_fixes_unparseable:
        events.append(
            {
                "event": "reviewer_fixes_unparseable",
                "reviewer": reviewer,
                "module": "a1/my-morning",
                "writer_under_review": writer,
            }
        )
    events.append(
        {
            "event": "phase_review_summary",
            "reviewer": reviewer,
            "module": "a1/my-morning",
            "writer_under_review": writer,
            "dims_scored": len(CONTENT_DIMS),
            "dims_with_evidence": len(CONTENT_DIMS),
            "weighted_score": weighted_score if weighted_score is not None else sum(scores) / len(scores),
            "min_dim_score": min(scores),
        }
    )
    return events


def _fixture(
    tmp_path: Path,
    writer_events: dict[str, list[dict[str, Any]]],
    review_scores: dict[str, list[float]],
    *,
    writer_markdown: dict[str, str] | None = None,
    review_extra: dict[tuple[str, str], dict[str, Any]] | None = None,
) -> Path:
    bakeoff_dir = tmp_path / "bakeoff"
    bakeoff_dir.mkdir()
    writer_markdown = writer_markdown or {}
    review_extra = review_extra or {}
    writers = list(writer_events)
    for writer in writers:
        (bakeoff_dir / f"{writer}.md").write_text(
            writer_markdown.get(writer, _writer_markdown(writer)),
            "utf-8",
        )
        _write_jsonl(bakeoff_dir / f"{writer}.write.jsonl", writer_events[writer])
    for writer in writers:
        for reviewer in writers:
            if writer == reviewer:
                continue
            _write_jsonl(
                bakeoff_dir / f"{writer}-{reviewer}.review.jsonl",
                _review_events(writer, reviewer, review_scores[writer], **review_extra.get((writer, reviewer), {})),
            )
    return bakeoff_dir


def _run_report(bakeoff_dir: Path, writers: tuple[str, ...] = ("bad", "good")) -> str:
    output = bakeoff_dir / "REPORT.md"
    exit_code = bakeoff_aggregate.main(
        [
            "--bakeoff-dir",
            str(bakeoff_dir),
            "--writers",
            ",".join(writers),
            "--output",
            str(output),
        ]
    )
    assert exit_code == 0
    return output.read_text("utf-8")


def test_writer_with_theatre_violations_excluded_from_winner(tmp_path: Path) -> None:
    bakeoff_dir = _fixture(
        tmp_path,
        {
            "bad": _writer_events("bad", calls=8, theatre_count=2),
            "good": _writer_events("good", calls=2),
        },
        {
            "bad": [9, 9, 9, 9, 9, 9],
            "good": [8, 8, 8, 8, 8, 8],
        },
    )

    report = _run_report(bakeoff_dir)

    assert "Candidate winner: good" in report
    assert "bad (blocked: tool theatre)" in report
    assert "| Tool-theatre clean | 0 (2 violation(s)) | 3 (0 violations) |" in report


def test_winner_gate_uses_min_dim_not_weighted(tmp_path: Path) -> None:
    bakeoff_dir = _fixture(
        tmp_path,
        {
            "bad": _writer_events("bad", calls=9),
            "good": _writer_events("good", calls=2),
        },
        {
            "bad": [10, 10, 10, 10, 10, 4],
            "good": [8, 8, 8, 8, 8, 8],
        },
        review_extra={
            ("bad", "good"): {"weighted_score": 9},
            ("good", "bad"): {"weighted_score": 7},
        },
    )

    report = _run_report(bakeoff_dir)

    assert "Candidate winner: good" in report
    assert "bad (blocked: min_dim < 8)" in report


def test_reviewer_fixes_unparseable_emits_protocol_broken_banner(tmp_path: Path) -> None:
    bakeoff_dir = _fixture(
        tmp_path,
        {
            "bad": _writer_events("bad"),
            "good": _writer_events("good"),
        },
        {
            "bad": [8, 8, 8, 8, 8, 8],
            "good": [8, 8, 8, 8, 8, 8],
        },
        review_extra={("bad", "good"): {"reviewer_fixes_unparseable": True}},
    )

    report = _run_report(bakeoff_dir)

    assert "## REVIEWER PROTOCOL BROKEN" in report
    assert "bad-good (bad-good.review.jsonl)" in report


def test_suspicious_zero_calls_with_citations_flagged(tmp_path: Path) -> None:
    bakeoff_dir = _fixture(
        tmp_path,
        {
            "bad": _writer_events("bad", calls=0),
            "good": _writer_events("good", calls=2),
        },
        {
            "bad": [8, 8, 8, 8, 8, 8],
            "good": [8, 8, 8, 8, 8, 8],
        },
        writer_markdown={"bad": _writer_markdown("bad", tool_citation=True)},
    )

    report = _run_report(bakeoff_dir)

    assert "writer cites tools but emitted zero calls - suspect cross-contamination/theatre: bad." in report
    assert "| verify_words density (calls per 100 words) | 0 (0 calls; cites tool names) |" in report


def test_winner_ranking_section_present(tmp_path: Path) -> None:
    bakeoff_dir = _fixture(
        tmp_path,
        {
            "bad": _writer_events("bad", calls=1),
            "good": _writer_events("good", calls=2),
        },
        {
            "bad": [8, 8, 8, 8, 8, 8],
            "good": [8, 8, 8, 8, 8, 8],
        },
    )

    report = _run_report(bakeoff_dir)

    assert "## Winner ranking by tool-call density" in report
    assert "| writer | density | theatre violations | min_dim | verdict |" in report


def test_summary_tool_call_total_drift_warns_and_summary_wins(tmp_path: Path) -> None:
    bad_events = _writer_events("bad", calls=1)
    for event in bad_events:
        if event.get("event") == "phase_writer_summary":
            event["tool_calls_total"] = 5
    bakeoff_dir = _fixture(
        tmp_path,
        {
            "bad": bad_events,
            "good": _writer_events("good", calls=2),
        },
        {
            "bad": [8, 8, 8, 8, 8, 8],
            "good": [8, 8, 8, 8, 8, 8],
        },
    )

    report = _run_report(bakeoff_dir)

    assert (
        "writer tool-call total drift for bad: "
        "phase_writer_summary.tool_calls_total=5, writer_tool_call events=1"
    ) in report
    assert "| bad | 3.23 | 0 | 8.00 (immersion) | eligible |" in report
