from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from scripts.build import linear_pipeline

FIXTURES = Path(__file__).parent / "fixtures" / "textbook_grounding"

SEARCH_TEXT = (
    "Зворотна форма дієслова показує дію, яка повертається до виконавця. "
    "Учень умивається, одягається, готується до уроку, вітається з учителем, "
    "збирається швидко і повертається до щоденної ранкової справи без зайвих "
    "пояснень сьогодні."
)


def _plan(level: str = "A1", references: list[str] | None = None) -> dict[str, Any]:
    return {
        "level": level,
        "references": [
            {"title": title}
            for title in (references or ["Караман Grade 10, p.176"])
        ],
    }


def _write_tool_calls(module_dir: Path, calls: list[dict[str, Any]]) -> None:
    (module_dir / "writer_tool_calls.json").write_text(
        json.dumps(calls, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _search_call(title: str = "Караман Grade 10, p.176") -> dict[str, Any]:
    return {
        "tool": "mcp__sources__search_text",
        "args": {"query": f"{title} ранкова рутина зворотні дієслова"},
        "result": [
            {
                "title": title,
                "text": SEARCH_TEXT,
                "page": 176,
                "grade": 10,
            }
        ],
    }


def test_textbook_grounding_gate_passes_good_fixture(tmp_path: Path) -> None:
    _write_tool_calls(tmp_path, [_search_call()])
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan(),
        tmp_path,
    )

    assert result["passed"] is True
    assert result["verdict"] == "PASS"
    assert result["matched"] == ["Караман Grade 10, p.176"]
    assert result["search_text_calls"] == 1


def test_textbook_grounding_gate_rejects_bad_fixture(tmp_path: Path) -> None:
    _write_tool_calls(tmp_path, [_search_call()])
    module_text = (FIXTURES / "bad-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan(),
        tmp_path,
    )

    assert result["passed"] is False
    assert result["verdict"] == "REJECT"
    assert result["missing"] == ["Караман Grade 10, p.176"]


def test_textbook_grounding_gate_requires_all_references_above_a1(tmp_path: Path) -> None:
    _write_tool_calls(tmp_path, [_search_call()])
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan("B1", ["Караман Grade 10, p.176", "Кравцова Grade 4, p.113"]),
        tmp_path,
    )

    assert result["passed"] is False
    assert result["required"] == 2
    assert result["matched"] == ["Караман Grade 10, p.176"]
    assert result["missing"] == ["Кравцова Grade 4, p.113"]


def test_textbook_grounding_gate_reads_jsonl_writer_trace(tmp_path: Path) -> None:
    event = {
        "event": "writer_tool_call",
        "tool": "search_text",
        "args_summary": {"query_chars": 32},
        "result_excerpt": SEARCH_TEXT,
    }
    (tmp_path / "writer_telemetry.jsonl").write_text(
        json.dumps(event, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan("A1"),
        tmp_path,
    )

    assert result["passed"] is True


def test_invoke_writer_persists_tool_trace(tmp_path: Path) -> None:
    trace_path = tmp_path / "writer_tool_calls.json"

    def invoker(_agent: str, _prompt: str, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(response="writer output", tool_calls=[_search_call()])

    response = linear_pipeline.invoke_writer(
        "Write.",
        "codex-tools",
        cwd=tmp_path,
        invoker=invoker,
        tool_trace_path=trace_path,
    )

    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    assert response == "writer output"
    assert trace[0]["tool"] == "mcp__sources__search_text"
