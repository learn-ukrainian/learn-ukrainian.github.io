#!/usr/bin/env python3
"""
MCP RAG Server — Ukrainian Textbook Search

Provides hybrid text search (dense + sparse via BGE-M3),
image search (SigLIP 2), and context retrieval from Qdrant.

Tools:
    - search_text: Hybrid text search with optional grade/subject/trust_tier filters
    - search_images: Text-to-image search via Ukrainian text query
    - get_chunk_context: Surrounding chunks for a given chunk_id
    - collection_stats: Index statistics
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Add scripts/ to path so rag package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2].parent / "scripts"))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError:
    print("MCP package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

server = Server("rag")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available RAG tools."""
    return [
        Tool(
            name="search_text",
            description=(
                "Hybrid text search across Ukrainian school textbooks. "
                "Combines dense (semantic) and sparse (keyword) search via BGE-M3. "
                "Returns relevant text chunks with metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query in Ukrainian (e.g., 'як утворюється минулий час')"
                    },
                    "grade": {
                        "type": "integer",
                        "description": "Filter by school grade (1-11). Optional."
                    },
                    "subject": {
                        "type": "string",
                        "description": "Filter by subject (e.g., 'ukrainska-mova', 'bukvar'). Optional."
                    },
                    "trust_tier": {
                        "type": "integer",
                        "description": "Filter by trust tier: 1 = NUS 2022+, 2 = 2017-2021. Optional.",
                        "enum": [1, 2]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 5, max 20)",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="search_images",
            description=(
                "Search textbook images using a Ukrainian text query. "
                "Uses SigLIP 2 for cross-modal text-to-image matching. "
                "Returns image paths with metadata and annotations "
                "(description_uk, associated_text_uk, teaching_value) when available."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Image search query in Ukrainian (e.g., 'яблуко', 'ілюстрація букви А')"
                    },
                    "grade": {
                        "type": "integer",
                        "description": "Filter by school grade (1-11). Optional."
                    },
                    "teaching_value": {
                        "type": "string",
                        "description": "Filter by teaching value: 'high', 'medium', 'low', 'none'. Optional.",
                        "enum": ["high", "medium", "low", "none"]
                    },
                    "subject": {
                        "type": "string",
                        "description": "Filter by subject (e.g., 'bukvar', 'ukrainska-mova'). Optional."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 5, max 20)",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="search_literary",
            description=(
                "Search Ukrainian literary primary sources (chronicles, poetry, legal texts). "
                "Covers Old East Slavic (X-XIII c.), Middle Ukrainian (XIV-XVIII c.), and more. "
                "Returns text chunks with work, author, year, genre, and language period metadata."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query in Ukrainian (e.g., 'хрещення Русі', 'повстання козаків')"
                    },
                    "work": {
                        "type": "string",
                        "description": "Filter by work title. Optional."
                    },
                    "genre": {
                        "type": "string",
                        "description": "Filter by genre (chronicle, poetry, prose, legal, grammar, etc.). Optional."
                    },
                    "period": {
                        "type": "string",
                        "description": "Filter by language period (old_east_slavic, middle_ukrainian, early_modern, modern). Optional."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 5, max 20)",
                        "default": 5
                    }
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="get_full_text",
            description=(
                "Load the full text of a short literary work from the RAG database. "
                "Returns all chunks concatenated in order. Best for works under ~20 pages. "
                "Caps at 50,000 characters."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "work": {
                        "type": "string",
                        "description": "Work title (e.g., 'Слово о полку Ігоревім', 'Літопис Самовидця')"
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Max characters to return (default 50000)",
                        "default": 50000
                    }
                },
                "required": ["work"]
            },
        ),
        Tool(
            name="get_chunk_context",
            description=(
                "Get surrounding text chunks for context. "
                "Given a chunk_id from search results, returns the chunk "
                "and its neighbors from the same textbook."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "chunk_id": {
                        "type": "string",
                        "description": "Chunk ID from search_text results"
                    },
                    "window": {
                        "type": "integer",
                        "description": "Number of chunks before and after to include (default 2)",
                        "default": 2
                    }
                },
                "required": ["chunk_id"]
            },
        ),
        Tool(
            name="collection_stats",
            description="Get statistics for all RAG collections (chunk count, image count, index status).",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="verify_word",
            description=(
                "Check if a Ukrainian word form exists in the VESUM morphological dictionary "
                "(415K lemmas, ~6M inflected forms). Returns lemma, POS, and morphological tags "
                "for each match. Use this to verify that a Ukrainian word form is real "
                "(not a hallucination). Empty result = word does not exist."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "Ukrainian word form to verify (e.g., 'берізонька', 'горонька')"
                    },
                    "pos_filter": {
                        "type": "string",
                        "description": "Optional POS filter (e.g., 'noun', 'verb', 'adj', 'adv'). "
                                       "Only returns matches with this POS."
                    },
                },
                "required": ["word"]
            },
        ),
        Tool(
            name="verify_words",
            description=(
                "Batch-verify multiple Ukrainian word forms against VESUM in a single call. "
                "Much faster than multiple verify_word calls — one SQL query instead of N round-trips. "
                "Returns per-word results: found/not-found with lemma, POS, and tags."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "words": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of Ukrainian word forms to verify (e.g., ['кращий', 'гірший', 'більший'])"
                    },
                    "pos_filter": {
                        "type": "string",
                        "description": "Optional POS filter applied to all words (e.g., 'adj', 'noun')."
                    },
                },
                "required": ["words"]
            },
        ),
        Tool(
            name="verify_lemma",
            description=(
                "Get all inflected forms of a Ukrainian lemma from the VESUM morphological dictionary. "
                "Returns every word form with its POS and morphological tags. "
                "Use this to find the correct declension/conjugation of a word."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "lemma": {
                        "type": "string",
                        "description": "Ukrainian lemma (dictionary form) to look up (e.g., 'коза', 'писати')"
                    },
                },
                "required": ["lemma"]
            },
        ),
        # ── Live source query tools ──────────────────────────────
        Tool(
            name="query_wikipedia",
            description=(
                "Query Ukrainian Wikipedia (uk.wikipedia.org). Modes: "
                "'summary' — article intro paragraph; "
                "'extract' — full article plaintext (up to 50K chars); "
                "'sections' — list section headings with indices; "
                "'section' — read a specific section (requires section parameter); "
                "'search' — keyword search returning titles and snippets. "
                "Results are cached locally (30-day TTL) to avoid redundant API calls."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Article title (for summary/extract/sections/section) or search query (for search)"
                    },
                    "mode": {
                        "type": "string",
                        "description": "Query mode",
                        "enum": ["summary", "extract", "sections", "section", "search"],
                        "default": "summary"
                    },
                    "section": {
                        "type": "integer",
                        "description": "Section index (required for mode='section', get indices from mode='sections')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max search results (default 5, only for search mode)",
                        "default": 5
                    },
                    "force_refresh": {
                        "type": "boolean",
                        "description": "Bypass cache and fetch fresh data from Wikipedia",
                        "default": False
                    }
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="query_grac",
            description=(
                "Query the GRAC corpus (2 billion tokens of Ukrainian text) for word frequency, "
                "lemma form distribution, concordance examples, or collocations. "
                "Use mode='frequency' for word/lemma frequency, 'concordance' for usage examples, "
                "'collocations' for common word combinations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Ukrainian word or lemma to look up"
                    },
                    "mode": {
                        "type": "string",
                        "description": (
                            "Query mode: 'frequency' (word frequency + IPM), "
                            "'lemma_forms' (all forms of a lemma with frequencies), "
                            "'concordance' (KWIC usage examples), "
                            "'collocations' (common word combinations)"
                        ),
                        "enum": ["frequency", "lemma_forms", "concordance", "collocations"],
                        "default": "frequency"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="query_ulif",
            description=(
                "Get declension/conjugation paradigm table from ULIF (Ukrainian Lingua-Information Fund). "
                "Returns full paradigm with all case forms for nouns/adjectives or conjugation for verbs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "Ukrainian word to look up paradigm for (e.g., 'стіл', 'писати')"
                    },
                },
                "required": ["word"]
            },
        ),
        Tool(
            name="query_r2u",
            description=(
                "Look up Russian→Ukrainian translations on r2u.org.ua. "
                "Useful for checking Russianisms — finds proper Ukrainian equivalents for Russian words."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "Russian word to find Ukrainian equivalent for (e.g., 'хорошо', 'кот')"
                    },
                },
                "required": ["word"]
            },
        ),
        Tool(
            name="query_pravopys",
            description=(
                "Look up Ukrainian orthography rules from the official 2019 Pravopys. "
                "Query by topic keyword (e.g., 'апостроф', 'м-який-знак', 'у-в') "
                "or by section number (1-61)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": (
                            "Topic keyword (e.g., 'апостроф', 'м-який-знак', 'у-в', 'подвоєння', "
                            "'велика-літера', 'префікси') or section number as string (e.g., '7')"
                        )
                    },
                },
                "required": ["topic"]
            },
        ),
        # ── Dictionary / reference collections (#1022) ──
        Tool(
            name="search_style_guide",
            description=(
                "Search Антоненко-Давидович style guide (279 entries). "
                "Identifies calques, Russianisms, and unnatural Ukrainian phrasing. "
                "HIGH PRIORITY for quality — use when unsure if a phrase is natural Ukrainian "
                "or a Russian calque. Query in Ukrainian (e.g., 'приймати участь', 'вірний')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Ukrainian phrase or word to check for calques/Russianisms"},
                    "limit": {"type": "integer", "description": "Max results (default 3)", "default": 3},
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="query_cefr_level",
            description=(
                "Look up CEFR level (A1-C1) for a Ukrainian word from the PULS vocabulary database "
                "(5,939 words). Use to verify vocabulary is level-appropriate for the module being written. "
                "Query with a single Ukrainian word."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Ukrainian word to check CEFR level"},
                    "limit": {"type": "integer", "description": "Max results (default 3)", "default": 3},
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="search_definitions",
            description=(
                "Search СУМ-11 (127K entries) — the authoritative Ukrainian explanatory dictionary. "
                "Returns definitions, usage examples, and citations in Ukrainian. "
                "Use to look up exact meanings, check word usage, or find example sentences."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Ukrainian word or phrase to look up"},
                    "limit": {"type": "integer", "description": "Max results (default 3)", "default": 3},
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="search_etymology",
            description=(
                "Search Грінченко dictionary (67K entries) — historical Ukrainian dictionary from 1907. "
                "Use for etymology, historical word forms, and pre-Soviet Ukrainian usage. "
                "Helps verify that a word is genuinely Ukrainian (not a Soviet-era import)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Ukrainian word to look up etymology/historical form"},
                    "limit": {"type": "integer", "description": "Max results (default 3)", "default": 3},
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="search_idioms",
            description=(
                "Search Ukrainian phraseological dictionary (25K entries). "
                "Find Ukrainian idioms, set expressions, and collocations. "
                "Use to make dialogues and examples more natural."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Topic or word to find related Ukrainian idioms"},
                    "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="search_synonyms",
            description=(
                "Search Ukrajinet Ukrainian WordNet (122K synsets). "
                "Find synonyms, antonyms, and semantically related words. "
                "Use for vocabulary variety and finding the most natural word choice."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Ukrainian word to find synonyms/antonyms for"},
                    "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="translate_en_uk",
            description=(
                "Search Балла English→Ukrainian dictionary (79K entries). "
                "Find Ukrainian translations for English words with context."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "English word or phrase to translate to Ukrainian"},
                    "limit": {"type": "integer", "description": "Max results (default 3)", "default": 3},
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="query_e2u",
            description=(
                "Live query e2u.org.ua English→Ukrainian dictionary (331K entries). "
                "Broader coverage than Балла. Use when translate_en_uk has no results, "
                "or for specialized/modern vocabulary. Returns headword + full translation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {"type": "string", "description": "English word to translate to Ukrainian"},
                },
                "required": ["word"]
            },
        ),
    ]


def _log_tool_call(name: str, arguments: dict[str, Any], response_chars: int = 0,
                   duration_s: float = 0.0, error: str = "") -> None:
    """Log MCP tool call to JSONL for build analytics (#1095)."""
    from datetime import datetime as _dt

    log_dir = Path(__file__).resolve().parents[2].parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "mcp-rag-requests.jsonl"

    entry = {
        "ts": _dt.now().isoformat(),
        "tool": name,
        "args": {k: str(v)[:200] for k, v in arguments.items()},
        "response_chars": response_chars,
        "duration_s": round(duration_s, 2),
    }
    if error:
        entry["error"] = error[:500]

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Logging must never break tool calls


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    import time as _time
    _t0 = _time.monotonic()
    try:
        # Dispatch to handler
        _handlers = {
            "search_text": lambda: handle_search_text(arguments),
            "search_images": lambda: handle_search_images(arguments),
            "search_literary": lambda: handle_search_literary(arguments),
            "get_full_text": lambda: handle_get_full_text(arguments),
            "get_chunk_context": lambda: handle_get_chunk_context(arguments),
            "collection_stats": lambda: handle_collection_stats(arguments),
            "verify_word": lambda: handle_verify_word(arguments),
            "verify_words": lambda: handle_verify_words(arguments),
            "verify_lemma": lambda: handle_verify_lemma(arguments),
            "query_wikipedia": lambda: handle_query_wikipedia(arguments),
            "query_grac": lambda: handle_query_grac(arguments),
            "query_ulif": lambda: handle_query_ulif(arguments),
            "query_r2u": lambda: handle_query_r2u(arguments),
            "query_e2u": lambda: handle_query_e2u(arguments),
            "query_pravopys": lambda: handle_query_pravopys(arguments),
            "search_style_guide": lambda: handle_dict_search(arguments, "style_guide", "Антоненко-Давидович"),
            "query_cefr_level": lambda: handle_dict_search(arguments, "puls_cefr", "PULS CEFR"),
            "search_definitions": lambda: handle_dict_search(arguments, "sum11", "СУМ-11"),
            "search_etymology": lambda: handle_dict_search(arguments, "grinchenko_dict", "Грінченко"),
            "search_idioms": lambda: handle_dict_search(arguments, "frazeolohichnyi", "Фразеологічний"),
            "search_synonyms": lambda: handle_dict_search(arguments, "ukrajinet", "Ukrajinet WordNet"),
            "translate_en_uk": lambda: handle_dict_search(arguments, "balla_en_uk", "Балла EN→UK"),
        }
        handler = _handlers.get(name)
        if handler:
            result = await handler()
        else:
            result = [TextContent(type="text", text=f"Unknown tool: {name}")]
            _log_tool_call(name, arguments, error="unknown tool")
            return result

        # Log successful call
        _elapsed = _time.monotonic() - _t0
        _resp_chars = sum(len(t.text) for t in result) if result else 0
        _log_tool_call(name, arguments, response_chars=_resp_chars, duration_s=_elapsed)
        return result
    except Exception as e:
        _elapsed = _time.monotonic() - _t0
        _log_tool_call(name, arguments, duration_s=_elapsed, error=f"{type(e).__name__}: {e}")
        return [TextContent(type="text", text=f"Error in {name}: {type(e).__name__}: {e}")]


async def handle_search_text(args: dict) -> list[TextContent]:
    query = args["query"]
    grade = args.get("grade")
    subject = args.get("subject")
    trust_tier = args.get("trust_tier")
    limit = min(args.get("limit", 5), 20)

    # Run in thread pool since embedding is CPU-bound
    from rag.query import search_text
    hits = await asyncio.to_thread(search_text, query, grade, subject, trust_tier, limit)

    if not hits:
        return [TextContent(type="text", text="No results found.")]

    lines = [f"Found {len(hits)} results for: \"{query}\"\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"### Result {i} (score: {hit['score']:.4f})")
        lines.append(f"- **Section**: {hit['section_title']}")
        lines.append(f"- **Source**: Grade {hit['grade']}, {hit['author']}, tier {hit['trust_tier']}")
        lines.append(f"- **Chunk ID**: `{hit['chunk_id']}`")
        lines.append(f"- **Text**:\n{hit['text']}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_search_literary(args: dict) -> list[TextContent]:
    query = args["query"]
    work = args.get("work")
    genre = args.get("genre")
    period = args.get("period")
    limit = min(args.get("limit", 5), 20)

    from rag.query import search_literary
    hits = await asyncio.to_thread(search_literary, query, work, genre, period, limit)

    if not hits:
        return [TextContent(type="text", text="No literary results found.")]

    lines = [f"Found {len(hits)} results for: \"{query}\"\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"### Result {i} (score: {hit['score']:.4f})")
        lines.append(f"- **Work**: {hit['work']} ({hit['year']})")
        lines.append(f"- **Author**: {hit['author']}")
        lines.append(f"- **Genre/Period**: {hit['genre']} / {hit['language_period']}")
        lines.append(f"- **Chunk ID**: `{hit['chunk_id']}`")
        lines.append(f"- **Text**:\n{hit['text']}")
        if hit.get("original_text"):
            lines.append(f"- **Original text**:\n{hit['original_text']}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]



async def handle_get_full_text(args: dict) -> list[TextContent]:
    work = args["work"]
    max_chars = args.get("max_chars", 50000)

    from rag.query import get_full_text
    result = await asyncio.to_thread(get_full_text, work, max_chars)

    if "error" in result:
        return [TextContent(type="text", text=result["error"])]

    lines = [
        f"# {result['work']} ({result['year']})",
        f"**Author**: {result['author']}",
        f"**Genre/Period**: {result['genre']} / {result['language_period']}",
        f"**Chunks**: {result['chunk_count']}, **Truncated**: {result['truncated']}",
        "",
        "---",
        "",
        result["text"],
    ]
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_search_images(args: dict) -> list[TextContent]:
    query = args["query"]
    grade = args.get("grade")
    teaching_value = args.get("teaching_value")
    subject = args.get("subject")
    limit = min(args.get("limit", 5), 20)

    from rag.query import search_images
    hits = await asyncio.to_thread(
        search_images, query, grade,
        teaching_value=teaching_value, subject=subject, limit=limit,
    )

    if not hits:
        return [TextContent(type="text", text="No image results found.")]

    lines = [f"Found {len(hits)} images for: \"{query}\"\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"### Image {i} (score: {hit['score']:.4f})")
        lines.append(f"- **Path**: `{hit['image_path']}`")
        lines.append(f"- **Source**: Grade {hit['grade']}, {hit['author']}, page {hit['page']}")
        lines.append(f"- **Size**: {hit['width']}x{hit['height']}")
        if hit.get("description_uk"):
            lines.append(f"- **Description**: {hit['description_uk']}")
        if hit.get("associated_text_uk"):
            lines.append(f"- **Associated text**: {hit['associated_text_uk']}")
        if hit.get("teaching_value"):
            lines.append(f"- **Teaching value**: {hit['teaching_value']}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_get_chunk_context(args: dict) -> list[TextContent]:
    chunk_id = args["chunk_id"]
    window = args.get("window", 2)

    from rag.query import get_chunk_context
    chunks = await asyncio.to_thread(get_chunk_context, chunk_id, window)

    if not chunks:
        return [TextContent(type="text", text=f"No context found for chunk: {chunk_id}")]

    if len(chunks) == 1 and "error" in chunks[0]:
        return [TextContent(type="text", text=chunks[0]["error"])]

    lines = [f"Context for `{chunk_id}` (window={window}):\n"]
    for chunk in chunks:
        marker = ">>>" if chunk.get("is_target") else "   "
        lines.append(f"{marker} **[{chunk['chunk_id']}]** — {chunk['section_title']}")
        lines.append(chunk["text"])
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_collection_stats(args: dict) -> list[TextContent]:
    from rag.query import collection_stats
    stats = await asyncio.to_thread(collection_stats)
    return [TextContent(type="text", text=json.dumps(stats, indent=2))]


async def handle_verify_word(args: dict) -> list[TextContent]:
    word = args["word"]
    pos_filter = args.get("pos_filter")

    from rag.query import verify_word
    matches = await asyncio.to_thread(verify_word, word, pos_filter)

    if not matches:
        return [TextContent(type="text", text=f"'{word}' — NOT FOUND in VESUM. This word form may not exist in standard Ukrainian.")]

    lines = [f"'{word}' — {len(matches)} match(es) in VESUM:\n"]
    for m in matches:
        lines.append(f"- **lemma**: {m['lemma']}  |  **pos**: {m['pos']}  |  **tags**: `{m['tags']}`")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_verify_words(args: dict) -> list[TextContent]:
    words = args["words"]
    pos_filter = args.get("pos_filter")

    from rag.query import verify_words
    results = await asyncio.to_thread(verify_words, words, pos_filter)

    lines = [f"Batch verification: {len(words)} words\n"]
    found = 0
    for word in words:
        matches = results.get(word, [])
        if matches:
            found += 1
            tags_str = ", ".join(f"{m['lemma']}({m['pos']})" for m in matches[:3])
            lines.append(f"- **{word}** — FOUND ({len(matches)} match): {tags_str}")
        else:
            lines.append(f"- **{word}** — NOT FOUND")

    lines.insert(1, f"Found: {found}/{len(words)}\n")
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_verify_lemma(args: dict) -> list[TextContent]:
    lemma = args["lemma"]

    from rag.query import verify_lemma
    forms = await asyncio.to_thread(verify_lemma, lemma)

    if not forms:
        return [TextContent(type="text", text=f"Lemma '{lemma}' — NOT FOUND in VESUM.")]

    # Group forms by POS for readability
    by_pos: dict[str, list] = {}
    for f in forms:
        by_pos.setdefault(f["pos"], []).append(f)

    lines = [f"'{lemma}' — {len(forms)} form(s) across {len(by_pos)} POS:\n"]
    for pos, pos_forms in by_pos.items():
        lines.append(f"### {pos} ({len(pos_forms)} forms)")
        for f in pos_forms:
            lines.append(f"- {f['word_form']}  |  `{f['tags']}`")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_query_wikipedia(args: dict) -> list[TextContent]:
    mode = args.get("mode", "summary")
    query = args["query"]
    limit = args.get("limit", 5)
    section_idx = args.get("section")
    force_refresh = args.get("force_refresh", False)

    from rag.source_query import (
        wikipedia_extract,
        wikipedia_search,
        wikipedia_section_text,
        wikipedia_sections,
        wikipedia_summary,
    )
    from rag.wiki_cache import WikiCache

    cache = WikiCache()

    if mode == "search":
        # Search results use short TTL (24h) — cached separately
        cache_key_section = f"q={query}&limit={limit}"
        if not force_refresh:
            cached = cache.get("search", query, cache_key_section)
            if cached is not None:
                if cache.is_negative(cached):
                    return [TextContent(type="text", text=f"No Wikipedia results for: '{query}' (cached)")]
                return [TextContent(type="text", text=cached)]

        results = await asyncio.to_thread(wikipedia_search, query, limit)
        if not results:
            cache.put_negative("search", query, cache_key_section)
            return [TextContent(type="text", text=f"No Wikipedia results for: '{query}'")]
        lines = [f"Wikipedia search: '{query}' — {len(results)} results\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r['title']}** — {r['snippet']}")
        text = "\n".join(lines)
        cache.put("search", query, text, cache_key_section)
        return [TextContent(type="text", text=text)]

    elif mode == "extract":
        if not force_refresh:
            cached = cache.get("extract", query)
            if cached is not None:
                if cache.is_negative(cached):
                    return [TextContent(type="text", text=f"Wikipedia article not found: '{query}' (cached)")]
                return [TextContent(type="text", text=cached)]

        result = await asyncio.to_thread(wikipedia_extract, query)
        if not result:
            cache.put_negative("extract", query)
            return [TextContent(type="text", text=f"Wikipedia article not found: '{query}'")]
        lines = [
            f"# {result['title']}",
            f"**URL**: {result['url']}",
            "",
            result["extract"],
        ]
        text = "\n".join(lines)
        cache.put("extract", query, text)
        return [TextContent(type="text", text=text)]

    elif mode == "sections":
        if not force_refresh:
            cached = cache.get("sections", query)
            if cached is not None:
                if cache.is_negative(cached):
                    return [TextContent(type="text", text=f"Wikipedia article not found: '{query}' (cached)")]
                return [TextContent(type="text", text=cached)]

        result = await asyncio.to_thread(wikipedia_sections, query)
        if not result:
            cache.put_negative("sections", query)
            return [TextContent(type="text", text=f"Wikipedia article not found or has no sections: '{query}'")]
        lines = [f"Sections of '{query}':\n"]
        for s in result:
            indent = "  " * (int(s.get("toclevel", 1)) - 1)
            lines.append(f"{indent}{s.get('number', '')} {s.get('line', '')} (index={s.get('index', '')})")
        text = "\n".join(lines)
        cache.put("sections", query, text)
        return [TextContent(type="text", text=text)]

    elif mode == "section":
        if section_idx is None:
            return [TextContent(type="text", text="Error: 'section' parameter required for mode='section'. Use mode='sections' to get indices.")]

        sec_str = str(section_idx)
        if not force_refresh:
            cached = cache.get("section", query, sec_str)
            if cached is not None:
                if cache.is_negative(cached):
                    return [TextContent(type="text", text=f"Section {section_idx} not found in '{query}' (cached)")]
                return [TextContent(type="text", text=cached)]

        result = await asyncio.to_thread(wikipedia_section_text, query, section_idx)
        if not result:
            cache.put_negative("section", query, sec_str)
            return [TextContent(type="text", text=f"Section {section_idx} not found in '{query}'")]
        lines = [
            f"# {result['title']} — Section {section_idx}",
            "",
            result["text"],
        ]
        text = "\n".join(lines)
        cache.put("section", query, text, sec_str)
        return [TextContent(type="text", text=text)]

    else:  # summary (default)
        if not force_refresh:
            cached = cache.get("summary", query)
            if cached is not None:
                if cache.is_negative(cached):
                    return [TextContent(type="text", text=f"Wikipedia article not found: '{query}' (cached)")]
                return [TextContent(type="text", text=cached)]

        result = await asyncio.to_thread(wikipedia_summary, query)
        if not result:
            cache.put_negative("summary", query)
            return [TextContent(type="text", text=f"Wikipedia article not found: '{query}'")]
        lines = [
            f"# {result['title']}",
            f"**Description**: {result['description']}",
            f"**URL**: {result['url']}",
            "",
            result["extract"],
        ]
        text = "\n".join(lines)
        cache.put("summary", query, text)
        return [TextContent(type="text", text=text)]


async def handle_query_grac(args: dict) -> list[TextContent]:
    query = args["query"]
    mode = args.get("mode", "frequency")
    limit = args.get("limit", 10)

    from rag.source_query import (
        grac_collocations,
        grac_concordance,
        grac_frequency,
        grac_lemma_frequency,
    )

    if mode == "frequency":
        result = await asyncio.to_thread(grac_frequency, query)
        if not result:
            return [TextContent(type="text", text=f"GRAC query failed for: '{query}'")]
        return [TextContent(type="text", text=(
            f"**{result['word']}**: frequency = {result['freq']:,}, "
            f"relative = {result['rel_freq']:.2f} per million"
        ))]

    elif mode == "lemma_forms":
        result = await asyncio.to_thread(grac_lemma_frequency, query)
        if not result:
            return [TextContent(type="text", text=f"GRAC lemma query failed for: '{query}'")]
        lines = [f"Lemma '{result['lemma']}' — total frequency: {result['total_freq']:,}\n"]
        for form in result["forms"][:limit]:
            lines.append(f"- {form['word']}: {form['freq']:,} ({form['pct']:.1f}%)")
        return [TextContent(type="text", text="\n".join(lines))]

    elif mode == "concordance":
        results = await asyncio.to_thread(grac_concordance, query, limit)
        if not results:
            return [TextContent(type="text", text=f"No concordance results for: '{query}'")]
        lines = [f"Concordance for '{query}' — {len(results)} lines\n"]
        for r in results:
            lines.append(f"...{r['left']} **{r['kwic']}** {r['right']}...")
        return [TextContent(type="text", text="\n".join(lines))]

    else:  # collocations
        results = await asyncio.to_thread(grac_collocations, query, limit=limit)
        if not results:
            return [TextContent(type="text", text=f"No collocations found for: '{query}'")]
        lines = [f"Collocations for '{query}' — {len(results)} results\n"]
        for r in results:
            lines.append(f"- **{r['word']}**: freq={r['freq']:,}, score={r['score']:.2f}")
        return [TextContent(type="text", text="\n".join(lines))]


async def handle_query_ulif(args: dict) -> list[TextContent]:
    word = args["word"]

    from rag.source_query import ulif_paradigm
    result = await asyncio.to_thread(ulif_paradigm, word)

    if not result:
        return [TextContent(type="text", text=f"No ULIF paradigm found for: '{word}'")]

    lines = [f"Paradigm for '{word}':\n"]
    for row in result["rows"]:
        lines.append(" | ".join(cell for cell in row))
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_query_r2u(args: dict) -> list[TextContent]:
    word = args["word"]

    from rag.source_query import r2u_translate
    results = await asyncio.to_thread(r2u_translate, word)

    if not results:
        return [TextContent(type="text", text=f"No r2u translation found for: '{word}'")]

    lines = [f"Russian→Ukrainian translations for '{word}':\n"]
    for entry in results[:10]:
        lines.append(f"- **{entry['headword']}**: {entry['translation'][:200]}")
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_query_e2u(args: dict) -> list[TextContent]:
    word = args["word"]

    from rag.source_query import e2u_translate
    results = await asyncio.to_thread(e2u_translate, word)

    if not results:
        return [TextContent(type="text", text=f"No e2u translation found for: '{word}'")]

    lines = [f"English→Ukrainian translations for '{word}' (e2u.org.ua):\n"]
    for entry in results[:10]:
        lines.append(f"- **{entry['headword']}**: {entry['translation'][:200]}")
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_query_pravopys(args: dict) -> list[TextContent]:
    topic = args["topic"]

    from rag.source_query import pravopys_lookup, pravopys_section

    # Check if topic is a number
    if topic.strip().isdigit():
        result = await asyncio.to_thread(pravopys_section, int(topic.strip()))
    else:
        result = await asyncio.to_thread(pravopys_lookup, topic)

    if not result:
        return [TextContent(type="text", text=f"No pravopys section found for: '{topic}'")]

    lines = [
        f"**Pravopys section {result['section']}**",
        f"**URL**: {result['url']}",
        "",
        result["text"][:3000],
    ]
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_dict_search(args: dict, collection: str, label: str) -> list[TextContent]:
    """Generic handler for dictionary/reference collection searches (#1022)."""
    query = args["query"]
    limit = min(args.get("limit", 3), 10)

    from rag.query import search_dictionary
    hits = await asyncio.to_thread(search_dictionary, query, collection, limit)

    if not hits:
        return [TextContent(type="text", text=f"No results in {label} for: \"{query}\"")]

    lines = [f"Found {len(hits)} results in **{label}** for: \"{query}\"\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"### Result {i} (score: {hit['score']:.4f})")
        if hit.get("headword"):
            lines.append(f"- **Headword**: {hit['headword']}")
        if hit.get("source"):
            lines.append(f"- **Source**: {hit['source']}")
        text = hit.get("text", "")
        if text:
            lines.append(f"- **Text**: {text[:500]}")
        meta = hit.get("metadata", {})
        if meta:
            meta_str = ", ".join(f"{k}: {v}" for k, v in list(meta.items())[:5] if v)
            if meta_str:
                lines.append(f"- **Metadata**: {meta_str}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


async def main_stdio():
    """Run the MCP RAG server via stdio (spawned by Claude Code)."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def main_sse(host: str = "127.0.0.1", port: int = 8766):
    """Run the MCP RAG server as a standalone SSE daemon."""
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.responses import Response
    from starlette.routing import Mount, Route

    # Pre-load embedding model at startup to avoid lazy-load crashes in async threads.
    # The BGE-M3 model uses PyTorch which can fail with "Cannot copy out of meta tensor"
    # when lazy-loaded inside asyncio.to_thread() after the server has been running.
    print("Pre-loading embedding model...")
    try:
        from rag.query import get_text_encoder
        encoder = get_text_encoder()
        encoder._load()
        # Warm up with a test encode to ensure weights are materialized
        encoder.encode(["тест"], batch_size=1)
        print("Embedding model pre-loaded and verified ✅")
    except Exception as e:
        print(f"⚠️  Embedding model pre-load failed: {e}")
        print("   search_text and dictionary searches will not work until model loads successfully")

    sse = SseServerTransport("/messages/")

    async def handle_health(request):
        return Response('{"status":"ok"}', media_type="application/json")

    async def handle_sse(request):
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await server.run(
                    streams[0], streams[1], server.create_initialization_options(),
                    stateless=True,
                )
        except Exception:
            # Client disconnected (Gemini timeout, rate limit, etc.)
            # This is normal — don't crash the server
            pass
        return Response()

    app = Starlette(
        routes=[
            Route("/health", endpoint=handle_health),
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    print(f"RAG MCP Server (SSE) running on http://{host}:{port}")
    print(f"  SSE endpoint: http://{host}:{port}/sse")
    print(f"  Messages: http://{host}:{port}/messages/")
    sys.stdout.flush()

    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    srv = uvicorn.Server(config)
    await srv.serve()


if __name__ == "__main__":
    if "--standalone" in sys.argv:
        port = 8766
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
        asyncio.run(main_sse(port=port))
    else:
        asyncio.run(main_stdio())
