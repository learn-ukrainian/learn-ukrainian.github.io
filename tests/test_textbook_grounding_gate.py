from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.build import linear_pipeline

FIXTURES = Path(__file__).parent / "fixtures" / "textbook_grounding"

SEARCH_TEXT = (
    "Зворотна форма дієслова показує дію, яка повертається до виконавця. "
    "Учень умивається, одягається, готується до уроку, вітається з учителем, "
    "збирається швидко і повертається до щоденної ранкової справи без зайвих "
    "пояснень сьогодні."
)

FARMING_TEXT = (
    "У радянський період колективне господарство планувало посіви, звітувало "
    "про врожай, розподіляло техніку між бригадами, контролювало норми праці, "
    "обговорювало заготівлю зерна, організовувало ремонт тракторів і вело "
    "облік польових робіт протягом сезону."
)

APOSTROPHE_TEXT = (
    "Сім'я пояснює правило про м'який знак, п'ять прикладів, зв'язок між "
    "звуками, обов'язок уважно читати речення, пам'ять про винятки, подвір'я "
    "біля школи та спокійне повторення матеріалу після уроку, коли учні "
    "записують власні короткі відповіді."
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


def _seed_mcp_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Seed a minimal MCP config so codex-tools pre-flight resolves."""
    config_path = tmp_path / ".mcp.json"
    config_path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "sources": {
                        "type": "streamable-http",
                        "url": "http://127.0.0.1:8766/mcp",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    from scripts.agent_runtime import tool_config as tc_mod

    monkeypatch.setattr(tc_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    tc_mod._load_mcp_config.cache_clear()


def _search_call(title: str = "Караман Grade 10, p.176") -> dict[str, Any]:
    return {
        "tool": "mcp__sources__search_text",
        "args": {"query": f"{title} ранкова рутина зворотні дієслова"},
        "result": [
            {
                "title": title,
                "source_type": "textbook",
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
        "result": {
            "title": "Караман Grade 10, p.176",
            "source_type": "textbook",
            "text": SEARCH_TEXT,
            "page": 176,
            "grade": 10,
        },
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


def test_textbook_grounding_gate_reads_mcp_markdown_result(tmp_path: Path) -> None:
    _write_tool_calls(
        tmp_path,
        [
            {
                "name": "mcp__sources__search_text",
                "arguments": {"query": "Караман Grade 10 reflexive verbs"},
                "result": [
                    {
                        "type": "text",
                        "text": (
                            'Found 1 results for: "reflexive verbs"\n\n'
                            "### Result 1\n"
                            "- **Section**: Сторінка 176\n"
                            "- **Source**: Grade 10, karaman\n"
                            "- **Chunk ID**: `10-klas-ukrmova-karaman-2018_s0315`\n"
                            "- **Text**:\n"
                            f"{SEARCH_TEXT}\n"
                        ),
                    }
                ],
            }
        ],
    )
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan(),
        tmp_path,
    )

    assert result["passed"] is True
    assert result["matched"] == ["Караман Grade 10, p.176"]
    assert result["textbook_result_hits"] == 1


def test_textbook_grounding_gate_accepts_hermes_single_underscore_prefix(
    tmp_path: Path,
) -> None:
    """Hermes registers MCP tools with single-underscore (``mcp_sources_X``).

    Prior to the 2026-05-19 normalizer fix, the gate's tool-name match was
    hardcoded to strip only the double-underscore canonical form, so every
    Hermes-routed writer (deepseek/qwen/grok) was reading ``search_text_calls:
    0`` and HARD-REJECTing on ``textbook_grounding`` — even when the calls
    actually fired. This test pins the single-underscore acceptance so the
    regression can't silently come back.
    """
    _write_tool_calls(
        tmp_path,
        [
            {
                "tool": "mcp_sources_search_text",
                "args": {"query": "Караман Grade 10 reflexive verbs"},
                "result": [
                    {
                        "title": "Караман Grade 10, p.176",
                        "source_type": "textbook",
                        "text": SEARCH_TEXT,
                        "page": 176,
                        "grade": 10,
                    }
                ],
            }
        ],
    )
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan(),
        tmp_path,
    )

    assert result["passed"] is True
    assert result["search_text_calls"] == 1
    assert result["matched"] == ["Караман Grade 10, p.176"]


def test_textbook_grounding_gate_reads_hermes_hook_jsonl(tmp_path: Path) -> None:
    """End-to-end pin for the Hermes ``post_tool_call`` shell-hook output.

    The hook (``scripts/agent_runtime/hermes_hooks/log_tool_call.sh``) writes
    one line per MCP tool call to ``$cwd/hermes.write.jsonl`` with the
    Hermes single-underscore prefix and an ``event: writer_tool_call`` sentinel
    so ``_load_jsonl_tool_calls`` picks it up. This test feeds the exact
    on-disk shape the hook produces and asserts the gate sees the call and
    matches the reference — closes the observability gap that previously had
    every Hermes-routed writer build HARD-rejecting on ``textbook_grounding``.
    """
    event = {
        "event": "writer_tool_call",
        "tool": "mcp_sources_search_text",
        "args": {"query": "Караман Grade 10 reflexive verbs"},
        "result": [
            {
                "title": "Караман Grade 10, p.176",
                "source_type": "textbook",
                "text": SEARCH_TEXT,
                "page": 176,
                "grade": 10,
            }
        ],
        "duration_ms": 42,
        "tool_call_id": "call_00_test",
        "session_id": "sess_test",
        "ts": 1779220000,
    }
    (tmp_path / "hermes.write.jsonl").write_text(
        json.dumps(event, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan(),
        tmp_path,
    )

    assert result["passed"] is True
    assert result["search_text_calls"] == 1
    assert result["textbook_result_hits"] == 1
    assert result["matched"] == ["Караман Grade 10, p.176"]


def test_textbook_grounding_gate_unwraps_hermes_inner_result_shape(
    tmp_path: Path,
) -> None:
    """Pin the Hermes-routed MCP-server shape ``{"result": "<markdown>"}``.

    The learn-ukrainian sources MCP server wraps its single-string response
    under an inner ``result`` key (observed 2026-05-19 in the b1
    genitive-nuances build's ``hermes.write.jsonl``). Before this unwrap
    the textbook_grounding gate read ``textbook_result_hits: 0`` for every
    Hermes-routed writer even though the calls fired and returned valid
    grounded chunks — the gate's mapping path didn't know to dive into
    the inner ``result`` key.
    """
    inner_markdown = (
        'Found 1 results for: "Караман reflexive verbs"\n\n'
        "### Result 1\n"
        "- **Section**: Сторінка 176\n"
        "- **Source**: Grade 10, karaman\n"
        "- **Chunk ID**: `10-klas-ukrmova-karaman-2018_s0315`\n"
        "- **Text**:\n"
        f"{SEARCH_TEXT}\n"
    )
    (tmp_path / "hermes.write.jsonl").write_text(
        json.dumps(
            {
                "event": "writer_tool_call",
                "tool": "mcp_sources_search_text",
                "args": {"query": "Караман Grade 10 reflexive verbs"},
                "result": {"result": inner_markdown},
                "duration_ms": 101,
                "tool_call_id": "call_inner",
                "session_id": "sess",
                "ts": 1779220000,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan(),
        tmp_path,
    )

    assert result["passed"] is True
    assert result["search_text_calls"] == 1
    assert result["textbook_result_hits"] == 1
    assert result["matched"] == ["Караман Grade 10, p.176"]


def test_invoke_writer_persists_tool_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_mcp_config(tmp_path, monkeypatch)
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


def test_query_only_reference_match_rejected(tmp_path: Path) -> None:
    _write_tool_calls(
        tmp_path,
        [
            {
                "tool": "mcp__sources__search_text",
                "args": {"query": "Караман Grade 10, p.176"},
                "result": [
                    {
                        "title": "Захарійчук Grade 4, p.22",
                        "source_type": "textbook",
                        "text": SEARCH_TEXT,
                        "page": 22,
                        "grade": 4,
                    }
                ],
            }
        ],
    )
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(module_text, _plan(), tmp_path)

    assert result["passed"] is False
    assert result["matched"] == []
    assert result["missing"] == ["Караман Grade 10, p.176"]


def test_wiki_result_does_not_satisfy_gate(tmp_path: Path) -> None:
    call = _search_call()
    call["result"][0]["source_type"] = "wiki"
    _write_tool_calls(tmp_path, [call])
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(module_text, _plan(), tmp_path)

    assert result["passed"] is False
    assert result["textbook_result_hits"] == 0


def test_a1_fallback_attributes_to_actual_match(tmp_path: Path) -> None:
    _write_tool_calls(tmp_path, [_search_call("Кравцова Grade 4, p.113")])
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan("A1", ["Караман Grade 10, p.176", "Кравцова Grade 4, p.113"]),
        tmp_path,
    )

    assert result["passed"] is True
    assert result["matched"] == ["Кравцова Grade 4, p.113"]


def test_off_topic_quote_rejected(tmp_path: Path) -> None:
    _write_tool_calls(
        tmp_path,
        [
            {
                "tool": "mcp__sources__search_text",
                "args": {"query": "Караман Grade 10, p.176"},
                "result": [
                    {
                        "title": "Караман Grade 10, p.176",
                        "source_type": "textbook",
                        "text": FARMING_TEXT,
                        "page": 176,
                        "grade": 10,
                    }
                ],
            }
        ],
    )
    module_text = f"## Reflexive Verbs\n\n> **Караман Grade 10, p.176:** {FARMING_TEXT}\n"

    result = linear_pipeline._textbook_grounding_gate(module_text, _plan(), tmp_path)

    assert result["passed"] is False
    assert result["reason"] == "topical_mismatch"


def test_missing_corpus_rejects_to_protect_authority(tmp_path: Path) -> None:
    module_text = (FIXTURES / "bad-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        {
            "level": "B1",
            "references": [
                {"title": "Absent Grade 9, p.9", "corpus_missing": True}
            ],
        },
        tmp_path,
    )

    assert result["passed"] is False
    assert result["verdict"] == "REJECT"
    assert result["reason"] == "corpus_missing"
    assert result["missing"] == ["Absent Grade 9, p.9"]


def test_stress_marks_do_not_break_matching(tmp_path: Path) -> None:
    text = SEARCH_TEXT.replace("показує", "при́клад показує")
    result_text = SEARCH_TEXT.replace("показує", "приклад показує")
    _write_tool_calls(
        tmp_path,
        [
            {
                "tool": "mcp__sources__search_text",
                "args": {"query": "Караман Grade 10, p.176"},
                "result": [
                    {
                        "title": "Караман Grade 10, p.176",
                        "source_type": "textbook",
                        "text": result_text,
                        "page": 176,
                        "grade": 10,
                    }
                ],
            }
        ],
    )
    module_text = f"## Morning\n\n> **Караман Grade 10, p.176:** {text}\n"

    result = linear_pipeline._textbook_grounding_gate(module_text, _plan(), tmp_path)

    assert result["passed"] is True


def test_apostrophes_normalized_for_matching(tmp_path: Path) -> None:
    _write_tool_calls(
        tmp_path,
        [
            {
                "tool": "mcp__sources__search_text",
                "args": {"query": "Караман Grade 10, p.176"},
                "result": [
                    {
                        "title": "Караман Grade 10, p.176",
                        "source_type": "textbook",
                        "text": APOSTROPHE_TEXT,
                        "page": 176,
                        "grade": 10,
                    }
                ],
            }
        ],
    )
    module_text = (
        "## Orthography\n\n> **Караман Grade 10, p.176:** "
        + APOSTROPHE_TEXT.replace("'", "’")
        + "\n"
    )

    result = linear_pipeline._textbook_grounding_gate(module_text, _plan(), tmp_path)

    assert result["passed"] is True


def test_empty_references_rejected_for_b1_plus(tmp_path: Path) -> None:
    result = linear_pipeline._textbook_grounding_gate(
        "## Topic\n\nNo quotes.\n",
        {"level": "B1", "references": []},
        tmp_path,
    )

    assert result["passed"] is False
    assert result["reason"] == "missing_references"


def test_invoke_writer_appends_tool_trace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_mcp_config(tmp_path, monkeypatch)
    trace_path = tmp_path / "writer_tool_calls.json"

    def invoker(_agent: str, _prompt: str, **_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(response="writer output", tool_calls=[_search_call()])

    linear_pipeline.invoke_writer(
        "Write.",
        "codex-tools",
        cwd=tmp_path,
        invoker=invoker,
        tool_trace_path=trace_path,
    )
    linear_pipeline.invoke_writer(
        "Write again.",
        "codex-tools",
        cwd=tmp_path,
        invoker=invoker,
        tool_trace_path=trace_path,
    )

    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    assert len(trace) == 2
