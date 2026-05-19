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


def test_textbook_grounding_gate_matches_via_get_chunk_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin the writer_prompt §"Textbook quotes" Step B retrieval path.

    The writer prompt instructs every CORE-level writer to:

    * Step A: call ``search_text`` to resolve a ``chunk_id`` from a
      plan reference.
    * Step B: call ``get_chunk_context(chunk_id=...)`` to fetch the
      verbatim body, then paste ≥30 contiguous words into a blockquote.

    Before 2026-05-20 the textbook_grounding gate only ingested ``search_text``
    results, so a writer doing the prompt-prescribed thing produced
    ``matched=[]`` and HARD-REJECTED. Observed on 2026-05-19 a1/my-morning
    build: the writer's two verbatim blockquotes WERE in the chunk_context
    bodies but the gate never saw them. This test pins the fix end-to-end —
    seed only a get_chunk_context call, assert the gate matches the plan
    reference.
    """
    # The chunk_context shape the sources MCP server emits is
    # ``"**[<chunk_id>]** — Сторінка <N>\n\n<body>"``. The chunk's chunk_id
    # encodes source_file + page; _lookup_textbook_metadata is monkey-
    # patched so the test does not depend on a populated sources.db.
    body = (
        "Зворотна форма дієслова показує дію, яка повертається до виконавця. "
        "Учень умивається, одягається, готується до уроку, вітається з учителем, "
        "збирається швидко і повертається до щоденної ранкової справи без зайвих "
        "пояснень сьогодні."
    )
    chunk_id = "10-klas-ukrmova-karaman-2018_s0176"
    chunk_markdown = (
        f"**[{chunk_id}]** — Сторінка 176\n\n{body}"
    )
    (tmp_path / "hermes.write.jsonl").write_text(
        json.dumps(
            {
                "event": "writer_tool_call",
                "tool": "mcp_sources_get_chunk_context",
                "args": {"chunk_id": chunk_id},
                "result": {"result": chunk_markdown},
                "duration_ms": 12,
                "tool_call_id": "call_chunk",
                "session_id": "sess",
                "ts": 1779220000,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    # Cyrillic-native metadata (per ADR
    # docs/decisions/2026-05-15-cyrillic-native-matcher.md) — never derive
    # author from Latin source_file segments. Monkeypatch the DB lookup so
    # CI does not depend on a populated sources.db at the chosen path.
    monkeypatch.setattr(
        linear_pipeline,
        "_lookup_textbook_metadata",
        lambda source_file: {"author_uk": "Караман", "grade": "10"}
        if source_file == "10-klas-ukrmova-karaman-2018"
        else None,
    )

    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan(),
        tmp_path,
    )

    assert result["passed"] is True, result
    assert result["search_text_calls"] == 0
    assert result["chunk_context_calls"] == 1
    assert result["textbook_result_hits"] == 1
    assert result["matched"] == ["Караман Grade 10, p.176"]


def test_parse_mcp_get_chunk_context_markdown_no_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parser still extracts text + page when the DB lookup fails.

    If the DB is missing the parser must still return an item with the
    body and chunk_id-derived page, so the A1-fallback substring path in
    ``_textbook_grounding_gate`` can still attempt a match by body
    content alone. The synthesized title is the only thing that gets
    skipped — the item is still ``source_type='textbook'``.
    """
    monkeypatch.setattr(
        linear_pipeline,
        "_lookup_textbook_metadata",
        lambda _source_file: None,
    )
    chunk_id = "10-klas-ukrmova-karaman-2018_s0176"
    text = f"**[{chunk_id}]** — Сторінка 176\n\nЦе тіло чанку для тесту."
    items = linear_pipeline._parse_mcp_get_chunk_context_markdown(text)
    assert len(items) == 1
    item = items[0]
    assert item["source_type"] == "textbook"
    assert item["chunk_id"] == chunk_id
    assert item["page"] == 176
    assert item["source_file"] == "10-klas-ukrmova-karaman-2018"
    assert "title" not in item  # No DB → no synthesized title.
    assert item["text"] == "Це тіло чанку для тесту."


def test_invoke_writer_backfills_tool_calls_from_sidecar_jsonl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin the invoke_writer sidecar-JSONL backfill for Hermes-routed writers.

    ``hermes -z`` strips tool-call traces from stdout, so the Hermes adapter
    returns ``tool_calls_total=None`` and ``_runtime_tool_calls`` returns
    ``None``. Without backfill, ``detect_tool_theatre`` and
    ``_enforce_writer_runtime_gates`` see zero calls and treat every cited
    tool as a violation, even when the ``post_tool_call`` shell hook
    captured the calls in ``$cwd/hermes.write.jsonl``. This test simulates
    that situation by:

    * Creating a fake Hermes-style invoker that returns
      ``tool_calls_total=None`` (signal: telemetry unavailable).
    * Seeding ``$cwd/hermes.write.jsonl`` with one captured MCP call.
    * Asserting the trace file written by ``invoke_writer`` contains the
      backfilled call (proves the in-memory path also saw it).
    """
    _seed_mcp_config(tmp_path, monkeypatch)
    trace_path = tmp_path / "writer_tool_calls.json"

    # Simulate the hook's output (one MCP call captured during the writer
    # session). ``event: writer_tool_call`` is required for
    # ``_load_jsonl_tool_calls`` to keep this line.
    (tmp_path / "hermes.write.jsonl").write_text(
        json.dumps(
            {
                "event": "writer_tool_call",
                "tool": "mcp_sources_verify_word",
                "args": {"word": "стіл"},
                "result": {"valid": True, "matches": 2},
                "duration_ms": 9,
                "tool_call_id": "call_test",
                "session_id": "sess",
                "ts": 1779220000,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    def hermes_like_invoker(
        _agent: str, _prompt: str, **_kwargs: Any
    ) -> SimpleNamespace:
        # tool_calls_total=None mirrors HermesDeepSeekParseResult / Grok /
        # Qwen — the adapter explicitly returns "unknown" for the call
        # count because Hermes -z doesn't expose the trace on stdout.
        return SimpleNamespace(
            response="writer output",
            tool_calls=[],
            tool_calls_total=None,
        )

    response = linear_pipeline.invoke_writer(
        "Write.",
        "deepseek-tools",
        cwd=tmp_path,
        invoker=hermes_like_invoker,
        tool_trace_path=trace_path,
    )

    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    assert response == "writer output"
    assert len(trace) == 1
    assert trace[0]["tool"] == "mcp_sources_verify_word"
    assert trace[0]["args"] == {"word": "стіл"}


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
