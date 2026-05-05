from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.audit import bakeoff_aggregate

WRITERS = ("gemini", "claude", "gpt55")
CONTENT_DIMS = bakeoff_aggregate.CONTENT_DIMS


def _write_jsonl(path: Path, events: list[dict[str, Any]], *, malformed: bool = False) -> None:
    lines = [json.dumps(event, ensure_ascii=False) for event in events]
    if malformed:
        lines.insert(1, "{this is not json")
    path.write_text("\n".join(lines) + "\n", "utf-8")


def _writer_markdown(writer: str) -> str:
    repeated = " ".join(f"{writer} ранок кава школа дім" for _index in range(25))
    return f"""---
level: A1
slug: my-morning
module: a1-020
---

# Мій ранок

{repeated}
"""


def _writer_events(writer: str) -> list[dict[str, Any]]:
    tool_profiles = {
        "gemini": [
            ("verify_words", {"verified": 20, "failed": 0, "failed_words": []}),
            ("search_definitions", {"count": 2}),
            ("search_literary", {"count": 1}),
            ("search_style_guide", {"count": 1}),
        ],
        "claude": [
            ("verify_words", {"verified": 12, "failed": 1, "failed_words": ["взірець"]}),
            ("search_definitions_slovnyk", {"count": 1}),
            ("search_style_guide", {"count": 1}),
        ],
        "gpt55": [
            ("verify_words", {"verified": 10, "failed": 0, "failed_words": []}),
            ("search_definitions", {"count": 1}),
        ],
    }
    tools = tool_profiles[writer]
    events: list[dict[str, Any]] = [
        {
            "event": "writer_cot_emit",
            "ts": "2026-05-05T00:00:00+00:00",
            "writer": writer,
            "module": "a1/my-morning",
            "section": "intro",
            "block_present": True,
            "block_chars": 120,
            "fields_filled": ["word_budget", "plan_vocab", "register", "teaching_sequence"],
        },
        {
            "event": "writer_cot_emit",
            "ts": "2026-05-05T00:00:01+00:00",
            "writer": writer,
            "module": "a1/my-morning",
            "section": "practice",
            "block_present": True,
            "block_chars": 140,
            "fields_filled": ["word_budget", "plan_vocab", "register", "teaching_sequence"],
        },
    ]
    for tool, result_summary in tools:
        events.append(
            {
                "event": "writer_tool_call",
                "ts": "2026-05-05T00:00:02+00:00",
                "writer": writer,
                "module": "a1/my-morning",
                "section": "practice",
                "tool": tool,
                "args_summary": {"count": 3},
                "result_summary": result_summary,
                "duration_ms": 10,
            }
        )
    gate_present = writer != "gpt55"
    events.extend(
        [
            {
                "event": "writer_end_gate",
                "ts": "2026-05-05T00:00:03+00:00",
                "writer": writer,
                "module": "a1/my-morning",
                "gate_present": gate_present,
                "gate_actions": ["rescanned_words", "rescanned_sources"],
                "removed_count": 0,
            },
            {
                "event": "phase_writer_summary",
                "ts": "2026-05-05T00:00:04+00:00",
                "writer": writer,
                "module": "a1/my-morning",
                "sections_total": 2,
                "sections_with_cot": 2,
                "tool_calls_total": len(tools),
                "verify_words_calls": 1,
                "end_gate_fired": gate_present,
                "removed_via_gate": 0,
            },
        ]
    )
    return events


def _scores_for(writer: str, reviewer: str) -> dict[str, float]:
    scores = {
        "gemini": {
            "gemini": [10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
            "claude": [9.0, 10.0, 9.0, 8.0, 9.0, 9.0],
            "gpt55": [9.0, 10.0, 8.0, 9.0, 9.0, 10.0],
        },
        "claude": {
            "gemini": [8.0, 9.0, 8.0, 8.0, 8.0, 8.0],
            "claude": [8.5, 9.0, 8.5, 8.5, 8.5, 8.5],
            "gpt55": [7.5, 8.0, 8.0, 7.5, 8.0, 8.0],
        },
        "gpt55": {
            "gemini": [7.0, 8.0, 7.0, 7.0, 7.0, 7.0],
            "claude": [7.5, 8.0, 7.0, 7.5, 7.0, 7.5],
            "gpt55": [8.5, 9.0, 8.5, 8.5, 8.5, 8.5],
        },
    }
    return dict(zip(CONTENT_DIMS, scores[writer][reviewer], strict=True))


def _review_events(writer: str, reviewer: str) -> list[dict[str, Any]]:
    dim_scores = _scores_for(writer, reviewer)
    events: list[dict[str, Any]] = []
    for dim, score in dim_scores.items():
        events.append(
            {
                "event": "reviewer_dim_evidence",
                "ts": "2026-05-05T00:00:10+00:00",
                "reviewer": reviewer,
                "module": "a1/my-morning",
                "writer_under_review": writer,
                "dim": dim,
                "evidence_quotes": [f"{dim} quote one", f"{dim} quote two"],
                "rubric_mapping": f"{dim} maps to fixture rubric",
                "score": score,
            }
        )
    for audit_type in bakeoff_aggregate.REVIEW_AUDIT_TYPES:
        events.append(
            {
                "event": "reviewer_audit_call",
                "ts": "2026-05-05T00:00:11+00:00",
                "reviewer": reviewer,
                "module": "a1/my-morning",
                "writer_under_review": writer,
                "dim": "naturalness",
                "audit_type": audit_type,
                "tool": "search_style_guide" if audit_type == "sovietization_check" else "search_text",
                "items_checked": 2,
                "items_failed": 0,
                "flags_raised": ["SUM-11 ideological residue"] if audit_type == "sovietization_check" else [],
            }
        )
    events.append(
        {
            "event": "phase_review_summary",
            "ts": "2026-05-05T00:00:12+00:00",
            "reviewer": reviewer,
            "module": "a1/my-morning",
            "writer_under_review": writer,
            "dims_scored": len(dim_scores),
            "dims_with_evidence": len(dim_scores),
            "audit_calls_total": len(bakeoff_aggregate.REVIEW_AUDIT_TYPES),
            "flags_raised_total": 1,
            "min_dim_score": min(dim_scores.values()),
            "weighted_score": round(sum(dim_scores.values()) / len(dim_scores), 2),
        }
    )
    return events


def _make_fixture(tmp_path: Path) -> Path:
    bakeoff_dir = tmp_path / "audit" / "bakeoff-fixture"
    bakeoff_dir.mkdir(parents=True)
    for writer in WRITERS:
        (bakeoff_dir / f"{writer}.md").write_text(_writer_markdown(writer), "utf-8")
        _write_jsonl(
            bakeoff_dir / f"{writer}.write.jsonl",
            _writer_events(writer),
            malformed=(writer == "gpt55"),
        )
    for writer in WRITERS:
        for reviewer in WRITERS:
            _write_jsonl(
                bakeoff_dir / f"{writer}-{reviewer}.review.jsonl",
                _review_events(writer, reviewer),
            )
    return bakeoff_dir


def _run_aggregate(bakeoff_dir: Path) -> str:
    output = bakeoff_dir / "REPORT.md"
    exit_code = bakeoff_aggregate.main(
        [
            "--bakeoff-dir",
            str(bakeoff_dir),
            "--writers",
            ",".join(WRITERS),
            "--output",
            str(output),
        ]
    )
    assert exit_code == 0
    return output.read_text("utf-8")


def _section_lines(report: str, heading: str) -> list[str]:
    lines = report.splitlines()
    start = lines.index(heading)
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return lines[start:end]


def _table_rows(report: str, heading: str) -> list[str]:
    return [line for line in _section_lines(report, heading) if line.startswith("| ")]


def _cell_count(table_row: str) -> int:
    return len(table_row.strip().strip("|").split("|"))


def test_bakeoff_aggregate_report_contains_required_tables_and_findings(tmp_path: Path, capsys) -> None:
    report = _run_aggregate(_make_fixture(tmp_path))
    captured = capsys.readouterr()

    headings = [
        "## Prompt adherence - writers",
        "## Prompt adherence - reviewers",
        "## Content quality - writers",
        "## Tool usage",
        "## Cross-reviewer bias check",
        "## Findings + recommendations",
    ]
    for heading in headings:
        assert heading in report
        assert _table_rows(report, heading)

    assert "Candidate winner: gemini" in report
    assert "gemini over-rated its own-family writer" in report
    assert "No writer used: search_grinchenko_1907" in report
    assert "malformed JSONL skipped" in captured.err
    assert "malformed JSONL skipped" in report


def test_bakeoff_aggregate_content_min_dim_and_weighted_score(tmp_path: Path) -> None:
    report = _run_aggregate(_make_fixture(tmp_path))

    assert "| **min dim** | 9.00 (naturalness) | 8.00 (immersion) | 7.50 (naturalness) |" in report
    assert "| **weighted score** | 9.37 | 8.18 | 7.72 |" in report


def test_bakeoff_aggregate_missing_writer_telemetry_marks_absent(tmp_path: Path, capsys) -> None:
    bakeoff_dir = _make_fixture(tmp_path)
    (bakeoff_dir / "claude.write.jsonl").unlink()

    report = _run_aggregate(bakeoff_dir)
    captured = capsys.readouterr()

    assert "missing JSONL file" in captured.err
    assert "telemetry absent" in report


def test_bakeoff_aggregate_table_column_counts_match_agents(tmp_path: Path) -> None:
    report = _run_aggregate(_make_fixture(tmp_path))

    expected_counts = {
        "## Prompt adherence - writers": 4,
        "## Prompt adherence - reviewers": 4,
        "## Content quality - writers": 4,
        "## Tool usage": 4,
        "## Cross-reviewer bias check": 5,
        "## Findings + recommendations": 2,
    }
    for heading, expected_count in expected_counts.items():
        for row in _table_rows(report, heading):
            assert _cell_count(row) == expected_count, row
