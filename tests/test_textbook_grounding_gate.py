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


def _chunk_context_call(
    title: str = "Караман Grade 10, p.176",
    text: str = SEARCH_TEXT,
    chunk_id: str = "10-klas-ukrmova-karaman-2018_s0176",
) -> dict[str, Any]:
    """Build a ``get_chunk_context`` call satisfying the Step B enforcement.

    Writer prompt rule ``#R-TEXTBOOK-30W`` (B) requires
    ``mcp__sources__get_chunk_context(chunk_id=<ID>)`` for every fetchable
    plan reference. Before #2294 fixed it, the gate accepted ``search_text``
    evidence alone — m20 build #4 demonstrated the false-pass with
    ``chunk_context_calls=0`` and a matched blockquote.

    Use this helper alongside :func:`_search_call` in happy-path tests so
    the gate's Step B enforcement is satisfied. The pre-bundled dict shape
    matches the canonical claude/codex anthropic-tools result envelope and
    does not require monkeypatching ``_lookup_textbook_metadata`` — the
    matcher reads ``title`` directly from the dict.
    """
    return {
        "tool": "mcp__sources__get_chunk_context",
        "args": {"chunk_id": chunk_id},
        "result": [
            {
                "title": title,
                "source_type": "textbook",
                "text": text,
                "page": 176,
                "grade": 10,
            }
        ],
    }


def test_textbook_grounding_gate_passes_good_fixture(tmp_path: Path) -> None:
    # Step B enforcement (#2294): writer prompt #R-TEXTBOOK-30W (B) requires
    # a get_chunk_context call. Happy-path tests must include it; the
    # gate hard-fails without it even when the blockquote matches.
    _write_tool_calls(tmp_path, [_search_call(), _chunk_context_call()])
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
    assert result["chunk_context_calls"] == 1


def test_textbook_grounding_gate_rejects_bad_fixture(tmp_path: Path) -> None:
    # Bad-fixture path: writer did call get_chunk_context (Step B satisfied),
    # but the module body's blockquote is off-topic / not contained in the
    # retrieved chunk — the matcher rejects on content grounds, NOT Step B.
    _write_tool_calls(tmp_path, [_search_call(), _chunk_context_call()])
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
    _write_tool_calls(tmp_path, [_search_call(), _chunk_context_call()])
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
    chunk_event = {
        "event": "writer_tool_call",
        "tool": "get_chunk_context",
        "args": {"chunk_id": "10-klas-ukrmova-karaman-2018_s0176"},
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
    (tmp_path / "writer_telemetry.jsonl").write_text(
        json.dumps(event, ensure_ascii=False)
        + "\n"
        + json.dumps(chunk_event, ensure_ascii=False)
        + "\n",
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
            },
            _chunk_context_call(),
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
    # search_text result hit + chunk_context result hit = 2.
    assert result["textbook_result_hits"] == 2


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
            },
            {
                # Hermes single-underscore prefix variant of get_chunk_context.
                "tool": "mcp_sources_get_chunk_context",
                "args": {"chunk_id": "10-klas-ukrmova-karaman-2018_s0176"},
                "result": [
                    {
                        "title": "Караман Grade 10, p.176",
                        "source_type": "textbook",
                        "text": SEARCH_TEXT,
                        "page": 176,
                        "grade": 10,
                    }
                ],
            },
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
    assert result["chunk_context_calls"] == 1
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
    chunk_event = {
        "event": "writer_tool_call",
        "tool": "mcp_sources_get_chunk_context",
        "args": {"chunk_id": "10-klas-ukrmova-karaman-2018_s0176"},
        "result": [
            {
                "title": "Караман Grade 10, p.176",
                "source_type": "textbook",
                "text": SEARCH_TEXT,
                "page": 176,
                "grade": 10,
            }
        ],
        "duration_ms": 18,
        "tool_call_id": "call_01_chunk",
        "session_id": "sess_test",
        "ts": 1779220001,
    }
    (tmp_path / "hermes.write.jsonl").write_text(
        json.dumps(event, ensure_ascii=False)
        + "\n"
        + json.dumps(chunk_event, ensure_ascii=False)
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
    assert result["chunk_context_calls"] == 1
    assert result["textbook_result_hits"] == 2
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
    chunk_event = {
        "event": "writer_tool_call",
        "tool": "mcp_sources_get_chunk_context",
        "args": {"chunk_id": "10-klas-ukrmova-karaman-2018_s0315"},
        "result": {"result": inner_markdown},
        "duration_ms": 12,
        "tool_call_id": "call_inner_chunk",
        "session_id": "sess",
        "ts": 1779220001,
    }
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
        + "\n"
        + json.dumps(chunk_event, ensure_ascii=False)
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
    assert result["chunk_context_calls"] == 1
    # The inner-result unwrap parses the markdown; both calls return the
    # same parsed chunk so the dedupe path counts a single hit.
    assert result["textbook_result_hits"] >= 1
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


def test_textbook_grounding_gate_unwraps_gemini_function_response_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pin gemini-cli 0.42.0's list-of-functionResponse envelope shape.

    Gemini-cli ships writer-tool MCP results as
    ``[{"functionResponse": {"id": ..., "name": "mcp_sources_get_chunk_context",
    "response": {"output": "**[<chunk_id>]** — Сторінка <N>\\n\\n<md>"}}}]``
    — neither the canonical ``{"text": <md>}`` shape (claude/codex/direct
    anthropic-tools) nor the Hermes ``{"result": <md>}`` shape the
    2026-05-20 textbook parser fix (`07c12f2dd7`) covered. Without this
    unwrap the 2026-05-21 a1/my-morning gemini-tools build read
    ``textbook_result_hits: 0`` despite making two valid
    ``get_chunk_context`` calls that returned grounded Захарійчук Grade 1
    p.24 and p.52 bodies.

    Empirical reference:
    ``.worktrees/builds/a1-my-morning-20260521-060558/.../writer_tool_calls.json``
    — preserved on build branch ``build/a1/my-morning-20260521-060558``.
    """
    body = (
        "Зворотна форма дієслова показує дію, яка повертається до виконавця. "
        "Учень умивається, одягається, готується до уроку, вітається з учителем, "
        "збирається швидко і повертається до щоденної ранкової справи без зайвих "
        "пояснень сьогодні."
    )
    chunk_id = "10-klas-ukrmova-karaman-2018_s0176"
    chunk_markdown = f"**[{chunk_id}]** — Сторінка 176\n\n{body}"
    # The list-of-functionResponse shape is what writer_tool_calls.json
    # records when the writer is gemini-cli 0.42.0+. The runtime adapter
    # stores the raw provider response untouched so forensic replay sees
    # exactly what gemini-cli emitted.
    (tmp_path / "writer_tool_calls.json").write_text(
        json.dumps(
            [
                {
                    "name": "mcp_sources_get_chunk_context",
                    "arguments": {"chunk_id": chunk_id},
                    "result": [
                        {
                            "functionResponse": {
                                "id": "mcp_sources_get_chunk_context_1779343612984_0",
                                "name": "mcp_sources_get_chunk_context",
                                "response": {"output": chunk_markdown},
                            }
                        }
                    ],
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

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
    assert result["chunk_context_calls"] == 1
    assert result["textbook_result_hits"] == 1
    assert result["matched"] == ["Караман Grade 10, p.176"]


def test_textbook_grounding_gate_parses_get_chunk_context_list_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """m20 build #7 (2026-05-26, codex-tools writer) regression.

    Codex-tools returns the canonical MCP content-block envelope as a
    LIST of text blocks:

        [{"type": "text", "text": "**[<chunk_id>]** — Сторінка N\\n\\n<body>"}]

    The list-branch parser at `_result_items_from_call` already handled
    this shape for `search_text` (parsing the markdown into structured
    textbook items). The equivalent branch for `get_chunk_context` was
    missing — items got appended raw and ``_is_textbook_result`` rejected
    them (``type="text"`` not ``type="textbook"``). Result: round #7
    produced ``matched=[]`` and hard-failed `textbook_grounding` despite
    codex correctly making 2 get_chunk_context calls and pasting verbatim
    ≥30-word blockquotes from the returned chunks.

    The fix mirrors the search_text list-branch handling. This test pins
    the exact codex-tools envelope shape so the bug can't silently come
    back.
    """
    body = (
        "Зворотна форма дієслова показує дію, яка повертається до виконавця. "
        "Учень умивається, одягається, готується до уроку, вітається з учителем, "
        "збирається швидко і повертається до щоденної ранкової справи без зайвих "
        "пояснень сьогодні."
    )
    chunk_id = "10-klas-ukrmova-karaman-2018_s0176"
    chunk_markdown = f"**[{chunk_id}]** — Сторінка 176\n\n{body}"

    # Exact shape codex-tools writer_tool_calls.json round-trip captured
    # at the 2026-05-26 m20 build #7 artifact:
    #     /Users/k/.codex/worktrees/.../a1-my-morning-20260526-181133/
    #     curriculum/l2-uk-en/a1/my-morning/writer_tool_calls.json
    _write_tool_calls(
        tmp_path,
        [
            {
                "tool": "mcp__sources__get_chunk_context",
                "args": {"chunk_id": chunk_id, "window": 1},
                "result": [{"type": "text", "text": chunk_markdown}],
            }
        ],
    )

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

    assert result["passed"] is True, (
        f"Codex-tools list-shape get_chunk_context envelope must parse "
        f"into a textbook item; got result={result!r}"
    )
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
    _write_tool_calls(
        tmp_path,
        [
            _search_call("Кравцова Grade 4, p.113"),
            _chunk_context_call("Кравцова Grade 4, p.113"),
        ],
    )
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan("A1", ["Караман Grade 10, p.176", "Кравцова Grade 4, p.113"]),
        tmp_path,
    )

    assert result["passed"] is True
    assert result["matched"] == ["Кравцова Grade 4, p.113"]


def test_blockquote_under_h3_inherits_h2_section_title(tmp_path: Path) -> None:
    """Build-#7 regression: when the writer organises the module with
    H3 ### Крок N: sub-headings inside an H2 ## Section, the blockquote
    must take the H2 section title (the actual pedagogical scope) for
    the topic match — not the H3 sub-heading's long technical
    meta-description, whose pedagogy-jargon stems flood topic_tokens
    and lock out any concrete-content quote from overlapping. Build #6
    (inline-bold Крок) passed; build #7 (H3 Крок) failed with
    topical_mismatch on real Захарійчук quotes that DID match the
    plan's references. The H3 'meta-talk' below mirrors the actual
    build-#7 section title that caused the false REJECT."""
    _write_tool_calls(
        tmp_path,
        [
            _search_call("Караман Grade 10, p.176"),
            _chunk_context_call("Караман Grade 10, p.176"),
        ],
    )
    # SEARCH_TEXT topics: учень, умивається, одягається, готується,
    # зборатися, зворотна, ранкова. The H2 "Зворотні дієслова" shares
    # "зворотн*", "дієсло*" stems with SEARCH_TEXT → topic check passes
    # when the H2 is used as section_title. The H3 below is
    # methodology-meta-talk (історичні джерела індоєвропейських мов)
    # with zero stem overlap with the quote — so when the gate picks
    # H3 as section_title the topic check fails even though the quote
    # is on-topic for the H2.
    module_text = (
        "## Зворотні дієслова\n\n"
        "Quick framing of the topic.\n\n"
        "### Крок 1: Класифікація типів за історичними джерелами "
        "індоєвропейських мов та порівняльна типологія парадигм\n\n"
        "Sub-step explanation.\n\n"
        f"> **Караман Grade 10, p.176:** {SEARCH_TEXT}\n"
    )

    result = linear_pipeline._textbook_grounding_gate(module_text, _plan(), tmp_path)

    assert result["passed"] is True, (
        f"H3 sub-heading must not poison the topic check; "
        f"reason={result.get('reason')!r} matched={result.get('matched')!r}"
    )
    assert "Караман Grade 10, p.176" in result["matched"]


def test_off_topic_quote_rejected(tmp_path: Path) -> None:
    # Step B IS satisfied (writer called get_chunk_context), but the chunk
    # body is off-topic for the module section. Test isolates the matcher's
    # topical-mismatch logic from the #2294 Step B enforcement.
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
            },
            _chunk_context_call("Караман Grade 10, p.176", text=FARMING_TEXT),
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
            },
            _chunk_context_call("Караман Grade 10, p.176", text=result_text),
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
            },
            _chunk_context_call("Караман Grade 10, p.176", text=APOSTROPHE_TEXT),
        ],
    )
    module_text = (
        "## Orthography\n\n> **Караман Grade 10, p.176:** "
        + APOSTROPHE_TEXT.replace("'", "’")
        + "\n"
    )

    result = linear_pipeline._textbook_grounding_gate(module_text, _plan(), tmp_path)

    assert result["passed"] is True


def test_searched_but_skipped_step_b_gets_diagnostic_reason(tmp_path: Path) -> None:
    """m20 build a1-my-morning-20260523-184413 failure mode (2026-05-23).

    Writer made 2 ``search_text`` calls by topic keyword, ZERO
    ``get_chunk_context`` calls, and pasted wrong-chunk text into the
    blockquote. Existing logic would reject via ``matched=[]`` with
    ``reason=None`` — opaque to the writer's self-correction loop.

    With the diagnostic-clarity override, the reason is explicitly
    ``step_b_skipped_no_get_chunk_context`` so the writer (and reviewer)
    knows to call ``get_chunk_context(chunk_id=...)`` per rule
    #R-TEXTBOOK-30W Step B before pasting the blockquote.
    """
    _write_tool_calls(
        tmp_path,
        [
            {
                "tool": "mcp__sources__search_text",
                "args": {
                    "query": "Захарійчук Христинка чорниці бабуся радіопередача",
                    "subject": "bukvar",
                    "limit": 3,
                },
                "result": [
                    {
                        "title": "Захарійчук Grade 1, p.24",
                        "source_type": "textbook",
                        "text": FARMING_TEXT,  # wrong-chunk content; doesn't match the blockquote
                        "page": 24,
                        "grade": 1,
                    }
                ],
            }
        ],
    )
    # Module text uses an unrelated blockquote that is NOT in the search result
    # (mimics the writer pasting wrong-chunk text or paraphrasing).
    module_text = f"## Morning Routine\n\n> {SEARCH_TEXT}\n\n*— Захарійчук, Grade 1, p.24*\n"

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan("A1", ["Захарійчук Grade 1, p.24"]),
        tmp_path,
    )

    assert result["passed"] is False
    assert result["verdict"] == "REJECT"
    assert result["severity"] == "HARD"
    assert result["search_text_calls"] == 1
    assert result["chunk_context_calls"] == 0
    assert result["reason"] == "step_b_skipped_no_get_chunk_context"


def test_step_b_enforcement_overrides_search_text_blockquote_match(
    tmp_path: Path,
) -> None:
    """m20 build #4 false-pass regression (#2294, 2026-05-26).

    Empirical evidence from build worktree
    ``a1-my-morning-20260525-235634``:

    * ``writer_output.raw.md`` self-reports
      ``<chunk_context_calls>0</chunk_context_calls>``
    * ``writer_tool_calls.json`` has two ``mcp__sources__search_text`` calls
      against ``Захарійчук Grade 1, p.24`` and ``p.52`` and zero
      ``mcp__sources__get_chunk_context`` calls
    * ``python_qg.json`` recorded ``textbook_grounding: passed=true,
      search_text_calls=2, chunk_context_calls=0`` — a false pass.

    The writer prompt rule ``#R-TEXTBOOK-30W`` (B) promised the writer:

        "the gate HARD-rejects regardless of blockquote content"

    when ``chunk_context_calls=0``. Before #2294 the gate did NOT keep that
    promise — it accepted any blockquote that happened to match a search
    result. With Step B enforcement, the gate hard-fails in this scenario
    and surfaces ``step_b_skipped_no_get_chunk_context`` so the writer's
    self-correction loop has an actionable signal.

    This test pins the exact m20 #4 shape: a single ``search_text`` call
    returning content the writer's blockquote DOES match — without this
    fix, ``passed=True``; with this fix, ``passed=False`` and the reason
    is explicit.
    """
    _write_tool_calls(tmp_path, [_search_call()])  # No chunk_context call.
    module_text = (FIXTURES / "good-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        _plan(),
        tmp_path,
    )

    assert result["passed"] is False, (
        "m20 build #4 regression: gate must HARD-reject when "
        "chunk_context_calls=0 and plan_references are fetchable, even when "
        "search_text evidence happens to satisfy the blockquote matcher."
    )
    assert result["verdict"] == "REJECT"
    assert result["severity"] == "HARD"
    assert result["search_text_calls"] == 1
    assert result["chunk_context_calls"] == 0
    assert result["reason"] == "step_b_skipped_no_get_chunk_context"
    # Matcher's per-ref result is preserved as diagnostic context for the
    # writer — the m20 #4 ``matched=[Захарійчук Grade 1, p.24]`` was still
    # informative even while the overall verdict became REJECT.
    assert result["matched"] == ["Караман Grade 10, p.176"]


def test_step_b_enforcement_does_not_apply_when_all_refs_corpus_missing(
    tmp_path: Path,
) -> None:
    """Carve-out: writers cannot fetch chunks that do not exist.

    When every plan reference is flagged ``corpus_missing: true``, the
    writer has nothing to ``get_chunk_context`` against. The Step B
    enforcement (#2294) must NOT fire in that case — the existing
    ``missing_corpus`` rejection path is the right signal, and adding a
    spurious Step B reject would mask the real plan-time corpus gap.
    """
    module_text = (FIXTURES / "bad-module.md").read_text(encoding="utf-8")

    result = linear_pipeline._textbook_grounding_gate(
        module_text,
        {
            "level": "B1",
            "references": [
                {"title": "Absent Grade 9, p.9", "corpus_missing": True},
            ],
        },
        tmp_path,
    )

    assert result["passed"] is False
    assert result["reason"] == "corpus_missing"  # NOT step_b_skipped_no_get_chunk_context


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
