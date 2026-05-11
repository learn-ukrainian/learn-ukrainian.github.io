#!/usr/bin/env python3
"""
MCP Sources Server — Ukrainian curriculum knowledge base

Serves SQLite FTS5 search over textbook chunks, literary sources
(chronicles / poetry / legal texts), Ukrainian Wikipedia articles, and
a stack of dictionaries (VESUM, СУМ, Грінченко, Балла, Антоненко-Давидович,
Фразеологічний, Правопис 2019). Used by the build pipeline for knowledge
packet assembly and by agents during writing / review.

Historically this was called the "RAG server" — the current implementation
is FTS5, not vector-based retrieval. Renamed for clarity (#1024 follow-up).
The Python backing package is still `scripts/rag/` for backwards compat
with imports; rename there is a follow-up.

Tools:
    - search_sources, search_text, search_literary, search_external, search_images, get_chunk_context
    - verify_word, verify_words, verify_lemma (VESUM)
    - query_wikipedia, query_pravopys, query_e2u, query_r2u, query_ulif
    - search_definitions, search_grinchenko_1907, search_esum, search_idioms, search_synonyms
    - search_slovnyk_me, search_heritage
    - search_style_guide (Антоненко-Давидович)
    - translate_en_uk (Балла)
"""

import asyncio
import contextlib
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests

# Add repo root and scripts/ to path so both scripts.* and legacy top-level
# packages are importable.
PROJECT_ROOT = Path(__file__).resolve().parents[2].parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
for _path in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError:
    print("MCP package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Server ID published to MCP clients. Matches the key in .mcp.json
# ("sources"). Agent tool prefixes become mcp__sources__*.
server = Server("sources")

VERIFY_SOURCE_ATTRIBUTION_SOURCES = (
    "grinchenko_1907",
    "esum",
    "sum11",
    "antonenko_davydovych",
    "literary",
    "heritage",
    "wikipedia",
    "style_guide",
)

COMPLETENESS_NOTES = {
    "antonenko_davydovych": (
        "Антоненко-Давидович: 279 of ~600+ entries indexed — incomplete; "
        "if discusses=false here, Tier 2 escalation may still find it."
    ),
    "sum11": (
        "СУМ-11: 127K entries; Soviet-era political/ideological coverage "
        "flagged via sovietization_risk metadata."
    ),
    "grinchenko_1907": "Грінченко 1907: 67K entries; lexicographic snapshot circa 1907, NOT etymology.",
    "esum": "ЕСУМ: etymological dictionary; coverage skewed toward inherited vocabulary.",
    "wikipedia": "Live source; results reflect current uk.wikipedia.org state.",
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available RAG tools."""
    return [
        Tool(
            name="search_sources",
            description=(
                "Unified Ukrainian source search across textbooks, literary corpora, "
                "Wikipedia, external articles, AND the ukrainian_wiki corpus "
                "(compiled Ukrainian textbook pedagogy). Use this for general retrieval "
                "when you want all relevant Ukrainian-source content in one query. "
                "Use the corpus-specific tools (search_text, search_literary, etc.) "
                "only when you need to scope to a single source."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query in Ukrainian (e.g., 'голосні звуки', 'як утворюється минулий час')"
                    },
                    "track": {
                        "type": "string",
                        "description": "Optional curriculum track for retrieval prep and reranking (e.g., 'a1'). Defaults to empty string."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results to return (default 10, max 20)",
                        "default": 10
                    }
                },
                "required": ["query"]
            },
        ),
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
            name="search_external",
            description=(
                "Search the external articles corpus (YouTube transcripts + blogs: "
                "Realna Istoriia, Ukrainian Lessons, Istoriia Movy, and related sources). "
                "Supports channel/register/decolonization filters and optional "
                "track-aware reranking for curriculum use."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "FTS5 search query in Ukrainian or English"
                    },
                    "track": {
                        "type": "string",
                        "description": "Optional curriculum track for channel-affinity reranking"
                    },
                    "channel": {
                        "type": "string",
                        "description": "Optional channel filter (e.g. 'realna_istoria')"
                    },
                    "register": {
                        "type": "string",
                        "enum": ["spoken", "scripted", "interview", "mixed"],
                    },
                    "decolonization": {
                        "type": "string",
                        "enum": ["strong", "moderate", "none", "neutral"],
                    },
                    "min_quality_tier": {
                        "type": "integer",
                        "default": 2,
                        "description": "1=highest quality only, 3=include background corpus",
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 10,
                        "description": "Max results to return (default 10, max 20)",
                    },
                },
                "required": ["query"],
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
            name="check_modern_form",
            description=(
                "Check if a Ukrainian word form is a currently-codified modern form or an archaic/historical form. "
                "This is metadata extraction from VESUM tags, not a separate diachronic analysis. "
                "Returns JSON with 'is_modern_codified', 'has_archaic_form', and 'has_only_archaic_form' flags."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "Ukrainian word form to check (e.g., 'звір', 'Сибір')"
                    },
                },
                "required": ["word"]
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
            name="verify_quote",
            description=(
                "Verify whether a Ukrainian literary quote is genuinely attested in the corpus for a given author. "
                "Returns boolean verdict + matched line(s) with work/year provenance + confidence score. "
                "Use INSTEAD of search_literary + grep + manual line reading when checking a quotation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "author": {
                        "type": "string",
                        "description": "Author name in Ukrainian (e.g., 'Шевченко', 'Леся Українка'). Matched against the literary corpus author column with normalization.",
                    },
                    "text": {
                        "type": "string",
                        "description": "The quoted text to verify, in Ukrainian. Accents/stress marks and punctuation differences tolerated.",
                    },
                    "min_confidence": {
                        "type": "number",
                        "description": "Minimum fuzzy-match confidence to count as 'matched' (0.0-1.0). Default 0.80.",
                        "default": 0.80,
                    },
                },
                "required": ["author", "text"],
            },
        ),
        Tool(
            name="verify_source_attribution",
            description=(
                "Verify whether a named authoritative source discusses a given claim/topic/headword. "
                "Returns boolean verdict + supporting evidence chunks with provenance. "
                "Use INSTEAD of dispatching sub-agents or composing multiple search tools manually."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source identifier. Must be one of the allowed values.",
                        "enum": list(VERIFY_SOURCE_ATTRIBUTION_SOURCES),
                    },
                    "claim": {
                        "type": "string",
                        "description": (
                            "The headword, claim, or topic in Ukrainian "
                            "(e.g., 'Сибір', 'давноминулий час')."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max evidence chunks to return (default 5).",
                        "default": 5,
                    },
                },
                "required": ["source", "claim"],
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
                "Search Антоненко-Давидович «Як ми говоримо» style guide. "
                "Coverage: 279 of estimated 600+ discussion items (~46% indexed). "
                "Identifies calques, Russianisms, and unnatural Ukrainian phrasing. "
                "HIGH PRIORITY for quality — use when unsure if a phrase is natural "
                "Ukrainian or a Russian calque. Query in Ukrainian (e.g., 'приймати "
                "участь', 'вірний'). **Absence of result is NOT evidence of absence "
                "in source** — 54% of canonical entries are unindexed. For full "
                "coverage, Tier 2 escalate to "
                "https://www.ukrlib.com.ua/books/printit.php?tid=4002. Issue: #1663."
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
                "Look up CEFR level (A1-C1) for a Ukrainian word from the PULS "
                "vocabulary database (puls.peremova.org). Coverage: 5,939 words "
                "indexed. **Vocabulary list, not pedagogy** — tells you the CEFR "
                "level a word belongs to but does not tell you how to teach it. "
                "C2 not covered. Use to verify vocabulary is level-appropriate "
                "for the module being written. Query with a single Ukrainian word."
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
                "Search СУМ-11 — Ukrainian explanatory dictionary from 1970–1980. "
                "Coverage: 127,069 of canonical 127K entries (~100% indexed). "
                "**Systematic exclusion: proper nouns** — toponyms (Київ, Львів, "
                "Дніпро, Сибір) and personal names (Шевченко) are NOT covered; "
                "absence of those is expected, not informative. Returns definitions, "
                "usage examples, and citations in Ukrainian. "
                "**WARNING: partially Sovietized for ideologically loaded headwords** "
                "(ленін*, більшовик*, радянськ*, національний, соціалістичн*, etc.). "
                "Each result carries `sovietization_risk` (0=clean, 1=keyword-match, "
                "2=high) and `sovietization_keywords`. When `sovietization_risk > 0`, "
                "treat as potentially Soviet-framed: do not reproduce verbatim, prefer "
                "СУМ-20 (#1667, license-blocked) or Грінченко for the same headword, "
                "or omit and route to neutral phrasing. ~5.6% of corpus (7,152 "
                "entries) is flagged. Issue: #1659."
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
            name="search_grinchenko_1907",
            description=(
                "Search Грінченко «Словарь української мови» (1907) — historical "
                "Ukrainian lexicographic dictionary. Coverage: 67,275 of canonical "
                "~67K entries (~100% indexed). **NOT etymology** — this is "
                "lexicographic (definitions + usage citations), not diachronic "
                "word-origin analysis. True "
                "etymology lives in `search_esum` (ЕСУМ, vol 1 А–Г live; vols 2-6 "
                "pending #1662). **Systematic exclusion: proper nouns** — toponyms "
                "(Київ, Львів, Дніпро, Сибір) and personal names (Шевченко) are NOT "
                "covered. Use for pre-Soviet Ukrainian usage attestation: helps "
                "verify a word is genuinely Ukrainian, not a Soviet-era import."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Ukrainian word to look up historical form/usage"},
                    "limit": {"type": "integer", "description": "Max results (default 3)", "default": 3},
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="search_esum",
            description=(
                "Search ЕСУМ (Етимологічний словник української мови) etymology entries. "
                "PoC scope: volume 1 only (А–Г); volumes 2–6 are follow-up work. "
                "Use for Ukrainian word-origin checks and cognate evidence."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Ukrainian word or etymology term to search"},
                    "volume": {
                        "type": "integer",
                        "description": "Optional ЕСУМ volume filter. This PoC currently supports volume 1.",
                    },
                    "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="search_idioms",
            description=(
                "Search Ukrainian phraseological dictionary (Фразеологічний). "
                "Coverage: 24,683 of canonical ~25K entries (~99% indexed). "
                "Find Ukrainian idioms, set expressions, and collocations. "
                "Use to make dialogues and examples more natural. Single-source "
                "dictionary — for cross-validation against another phraseology "
                "authority, fall back to corpus search via `search_literary`."
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
                "Search Ukrajinet Ukrainian WordNet. Coverage: 122,441 synsets "
                "(matches upstream README). **QUALITY CAVEAT: synsets are largely "
                "auto-translated from Open English WordNet** — not natively curated "
                "Ukrainian lexicography. Quality audit pending under EPIC #1657 "
                "Tier 3. Use for vocabulary variety and rough synonym/antonym "
                "discovery, but **DO NOT cite as authoritative**: cross-validate "
                "against `search_definitions` (СУМ-11) or `search_grinchenko_1907` "
                "(Грінченко) before treating a synonym as established Ukrainian. "
                "The 3,360-synset version cited in older docs is the 2023 paper's "
                "initial release; current production is the auto-MT-expanded set."
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
                "Search Балла English→Ukrainian dictionary. Coverage: 78,704 of "
                "canonical ~79K entries (~100% indexed). **One-way only** — UK→EN "
                "reverse not built. For broader coverage of specialized/modern "
                "vocabulary, fall back to `query_e2u` (live e2u.org.ua, 331K "
                "entries). Find Ukrainian translations for English words with "
                "context."
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
        Tool(
            name="query_sum20",
            description=(
                "Live query СУМ-20 (Словник української мови у 20 томах) via "
                "slovnyk.me/dict/newsum — modern post-Soviet academic Ukrainian "
                "explanatory dictionary, ULIF NAS Ukraine, 2010–ongoing. "
                "Coverage: volumes 1–16 (А–Р); vols 17–20 (С–Я) not yet "
                "published online. **Per-query live fetch with citation**, no "
                "bulk-ingest, no DB caching. Use as the **modern definitional "
                "baseline** to REPLACE Sovietized СУМ-11 entries (#1659): when "
                "`search_definitions` returns `sovietization_risk > 0`, fall "
                "back to `query_sum20`. Backed by slovnyk.me's clean per-word "
                "URLs (replaces the broken sum20ua.com search-page parser). "
                "License posture: per-query lookup with attribution only; "
                "no bulk crawl and no DB caching. Prefer official ULIF "
                "routes for authoritative СУМ-20 when available. Issue: #1667."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {"type": "string", "description": "Ukrainian headword to look up in СУМ-20 (must be in А–Р range)"},
                },
                "required": ["word"]
            },
        ),
        Tool(
            name="query_slovnyk_me",
            description=(
                "Live query slovnyk.me — Ukrainian dictionary aggregator with "
                "clean per-word URLs. One tool, many dictionaries. Use this "
                "instead of `query_sum20` when you need access beyond just "
                "СУМ-20. Per-query live fetch with citation, no bulk crawl, "
                "no DB caching.\n\n"
                "Available `dict` values:\n"
                "- `newsum` — СУМ-20 (modern, 2010–) — DEFAULT for definitions\n"
                "- `sum` — СУМ-11 (Sovietized, 1970–80) — fallback only\n"
                "- `davydov` (`antonenko` alias) — Antonenko-Davydovych «Як ми говоримо»\n"
                "- `synonyms_karavansky` (`karavansky` alias) — Karavansky synonyms\n"
                "- `franko` — dictionary from Ivan Franko's works\n"
                "- `slang_lviv` — Lviv regional lexicon\n"
                "- `holoskevych` — Holoskevych 1929 orthographic dictionary\n"
                "- `phraseology` — Фразеологічний словник\n"
                "- `orthography` — Орфографічний словник\n"
                "- `orthoepy` — Орфоепічний словник\n"
                "- `vts` — Великий тлумачний словник сучасної мови (alternate modern)\n"
                "- `foreign_melnychuk` — foreign-words dictionary (Мельничук)\n"
                "- `ukrrus` / `rusukr` / `engukr` — bilinguals\n\n"
                "License posture: slovnyk.me © notice plus third-party source "
                "rights; per-query lookup with attribution only, no bulk crawl "
                "and no DB caching. Issue: #1667."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {"type": "string", "description": "Ukrainian word to look up"},
                    "dict": {
                        "type": "string",
                        "description": "Dictionary slug (newsum, sum, davydov, synonyms_karavansky, franko, slang_lviv, holoskevych, phraseology, orthography, orthoepy, vts, foreign_melnychuk, ukrrus, rusukr, engukr). Backward aliases antonenko, karavansky, ukr_rus, rus_ukr, eng_ukr are accepted.",
                        "default": "newsum",
                    },
                },
                "required": ["word"]
            },
        ),
        Tool(
            name="search_slovnyk_me",
            description=(
                "Search slovnyk.me as a single-source dictionary aggregator. "
                "Uses curated rows in data/sources.db when present, with optional "
                "live direct-entry fallback to /dict/{slug}/{word}. Does NOT crawl "
                "slovnyk.me /search, /terms, or sitemap. Returns dictionary slug, "
                "source URL, bounded text/snippet, `is_modern`, `is_dialect`, "
                "`is_russianism`, `sovietization_risk`, and ranking score. Use this "
                "when a prompt needs slovnyk.me specifically, especially СУМ-20 or "
                "regional dictionaries. Dictionaries already indexed locally "
                "(СУМ-11, Грінченко, Антоненко-Давидович, phraseology, EN→UK) "
                "are blocked here; use their canonical tools. For heritage-defense "
                "decisions, prefer `search_heritage`."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Ukrainian headword to look up"},
                    "dictionaries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional dictionary slugs. Default: curated modern + heritage set.",
                    },
                    "limit": {"type": "integer", "description": "Max results (default 5, max 20)", "default": 5},
                    "live": {
                        "type": "boolean",
                        "description": "Allow live direct-entry fallback if local rows are absent. Default: true.",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="search_heritage",
            description=(
                "Canonical heritage-defense lookup for distinguishing authentic "
                "Ukrainian archaisms, historisms, dialectisms, and inherited words "
                "from Russianisms/surzhyk. Merges existing tools/sources: "
                "Грінченко 1907, ЕСУМ, slovnyk.me modern/regional dictionaries, "
                "and Антоненко-Давидович style warnings. Ranks pre-Soviet and "
                "etymological attestations above modern-only rows, and demotes "
                "style-guide Russianism warnings rather than dropping them."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Ukrainian headword to verify"},
                    "limit": {"type": "integer", "description": "Max merged results (default 8, max 20)", "default": 8},
                    "include_live_slovnyk": {
                        "type": "boolean",
                        "description": "Allow live slovnyk.me direct-entry fallback. Default: true.",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="check_russian_shadow",
            description=(
                "Detects Russian-pattern morphology in Ukrainian text. No Russian text ingested "
                "— uses pymorphy3 morphological model only."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The Ukrainian word to check for Russian morphological patterns."
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Confidence threshold (0.0 to 1.0). Default is 0.7.",
                        "default": 0.7
                    }
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
    log_path = log_dir / "mcp-sources-requests.jsonl"

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


async def handle_check_russian_shadow(args: dict):
    word = args.get("word", "")
    threshold = args.get("threshold", 0.7)

    import asyncio
    import json
    import os
    import sys

    # ensure scripts is in path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from scripts.verification.check_ru_morph import is_russian_pattern

    result = await asyncio.to_thread(is_russian_pattern, word, threshold)
    from mcp.types import TextContent
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


def _normalize_quote_text(value: str) -> str:
    text = "".join(
        ch for ch in unicodedata.normalize("NFKD", str(value).lower())
        if not "\u0300" <= ch <= "\u036f"
    )
    text = text.translate(str.maketrans({ch: " " for ch in "«»“”„\"'`"}))
    return re.sub(r"\s+", " ", text).strip()


def _normalize_author_name(value: str) -> str:
    text = _normalize_quote_text(str(value).replace(".", " "))
    tokens = [t for t in text.split() if len(t) > 1]
    patronymics = ("ович", "евич", "ич", "івна", "ївна", "овна", "евна")
    tokens = [t for t in tokens if not t.endswith(patronymics)]
    return tokens[-1] if tokens else text


def _best_quote_excerpt(text_query: str, chunk_text: str) -> str:
    from rapidfuzz import fuzz

    lines = [line.strip() for line in str(chunk_text).splitlines() if line.strip()]
    windows = [" ".join(lines[i:i + width]) for i in range(len(lines)) for width in range(1, 5)]
    if not windows:
        windows = [str(chunk_text)]
    return max(windows, key=lambda line: fuzz.partial_ratio(text_query, _normalize_quote_text(line)))


async def handle_verify_quote(args: dict) -> list[TextContent]:
    author_query = _normalize_author_name(args.get("author", ""))
    text_query = _normalize_quote_text(args.get("text", ""))
    if not author_query:
        raise ValueError("author is required")
    if not text_query:
        raise ValueError("text is required")

    min_confidence = max(0.0, min(float(args.get("min_confidence", 0.80)), 1.0))
    keywords = {word for word in text_query.split() if len(word) >= 3}

    from wiki.sources_db import search_literary

    hits = await asyncio.to_thread(search_literary, keywords, 20)
    candidates = []
    from rapidfuzz import fuzz

    for hit in hits:
        if _normalize_author_name(hit.get("author", "")) != author_query:
            continue
        chunk_text = hit.get("text", "")
        line = _best_quote_excerpt(text_query, chunk_text)
        confidence = fuzz.partial_ratio(text_query, _normalize_quote_text(chunk_text)) / 100
        candidates.append({
            "line": line,
            "work": hit.get("title") or hit.get("source_file") or "",
            "year": hit.get("year"),
            "confidence": round(confidence, 4),
            "context_chunk_id": hit.get("chunk_id"),
        })

    candidates.sort(key=lambda item: item["confidence"], reverse=True)
    matched = bool(candidates and candidates[0]["confidence"] >= min_confidence)
    result = {
        "matched": matched,
        "best_confidence": candidates[0]["confidence"] if candidates else 0.0,
        "matched_lines": [item for item in candidates if item["confidence"] >= min_confidence][:3]
        if matched else candidates[:3],
        "search_normalized": {
            "author_query": author_query,
            "text_query": text_query,
        },
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]


def _normalize_attribution_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^\w]+", " ", without_marks, flags=re.UNICODE).strip()


def _attribution_chunk(hit: dict[str, Any]) -> str:
    for key in ("definition", "definitions", "etymology_text", "snippet", "text"):
        value = hit.get(key)
        if value:
            return str(value)
    title = hit.get("title") or hit.get("word") or hit.get("lemma") or ""
    return str(title)


def _attribution_confidence(claim: str, hit: dict[str, Any]) -> float:
    claim_norm = _normalize_attribution_text(claim)
    if not claim_norm:
        return 0.0

    haystack_parts = [
        str(hit.get(key, ""))
        for key in ("word", "lemma", "title", "definition", "definitions", "etymology_text", "snippet", "text")
        if hit.get(key)
    ]
    haystack_norm = _normalize_attribution_text(" ".join(haystack_parts))
    if not haystack_norm:
        return 0.0
    if claim_norm in haystack_norm:
        return 1.0

    claim_token_count = max(1, len(claim_norm.split()))
    tokens = haystack_norm.split()
    candidates = tokens[:]
    if claim_token_count > 1:
        candidates.extend(
            " ".join(tokens[i:i + claim_token_count])
            for i in range(0, max(0, len(tokens) - claim_token_count + 1))
        )
    return max((SequenceMatcher(None, claim_norm, candidate).ratio() for candidate in candidates), default=0.0)


def _attribution_evidence(hit: dict[str, Any], confidence: float) -> dict[str, Any]:
    section = (
        hit.get("section")
        or hit.get("source")
        or hit.get("source_family")
        or hit.get("title")
        or hit.get("work")
        or None
    )
    return {
        "chunk": _attribution_chunk(hit),
        "section": section,
        "page": hit.get("page"),
        "confidence": round(confidence, 3),
    }


def _parse_wikipedia_search_hits(text: str) -> list[dict[str, Any]]:
    if text.startswith("No Wikipedia results"):
        return []
    hits = []
    for line in text.splitlines():
        match = re.match(r"\d+\.\s+\*\*(.*?)\*\*\s+—\s+(.*)", line)
        if match:
            title, snippet = match.groups()
            hits.append({
                "title": title,
                "snippet": snippet,
                "text": f"{title} — {snippet}",
                "source": "uk.wikipedia.org",
            })
    return hits


def _looks_like_wikipedia_search_response(text: str) -> bool:
    return text.startswith(("Wikipedia search:", "No Wikipedia results"))


async def handle_verify_source_attribution(args: dict) -> list[TextContent]:
    source = str(args.get("source", ""))
    claim = str(args.get("claim", "")).strip()
    limit = max(1, min(int(args.get("limit", 5)), 20))

    if source not in VERIFY_SOURCE_ATTRIBUTION_SOURCES:
        allowed = ", ".join(VERIFY_SOURCE_ATTRIBUTION_SOURCES)
        raise ValueError(f"Invalid source '{source}'. Expected one of: {allowed}")
    if not claim:
        raise ValueError("claim must be a non-empty string")

    from wiki import sources_db as sdb

    completeness_note = None
    if source == "grinchenko_1907":
        hits = await asyncio.to_thread(sdb.search_grinchenko_1907, claim, limit)
    elif source == "esum":
        hits = await asyncio.to_thread(sdb.search_esum, claim, None, limit)
    elif source == "sum11":
        hits = await asyncio.to_thread(sdb.search_definitions, claim, limit)
    elif source == "antonenko_davydovych":
        hits = await asyncio.to_thread(sdb.search_style_guide, claim, limit)
    elif source == "literary":
        keywords = {word for word in claim.lower().split() if len(word) >= 3}
        hits = await asyncio.to_thread(sdb.search_literary, keywords, limit)
    elif source == "heritage":
        hits = await asyncio.to_thread(sdb.search_heritage, claim, limit, include_live_slovnyk=True)
    elif source == "wikipedia":
        try:
            wiki_result = await handle_query_wikipedia({"query": claim, "mode": "search", "limit": limit})
            wiki_text = wiki_result[0].text if wiki_result else ""
            hits = _parse_wikipedia_search_hits(wiki_text)
            if not hits and not _looks_like_wikipedia_search_response(wiki_text):
                completeness_note = "Wikipedia returned unexpected response format"
        except requests.RequestException as exc:
            hits = []
            completeness_note = f"Wikipedia query failed: {exc}"
        except TimeoutError as exc:
            hits = []
            completeness_note = f"Wikipedia query failed: {exc}"
        except Exception as exc:
            hits = []
            completeness_note = f"Wikipedia query failed: {exc}"
    else:
        hits = await asyncio.to_thread(sdb.search_style_guide, claim, limit)

    scored = [
        (hit, _attribution_confidence(claim, hit))
        for hit in hits
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    evidence = [
        _attribution_evidence(hit, confidence)
        for hit, confidence in scored[:limit]
    ]
    payload: dict[str, Any] = {
        "discusses": any(confidence >= 0.85 for _, confidence in scored),
        "source": source,
        "evidence_count": len(evidence),
        "evidence": evidence,
    }
    if completeness_note:
        payload["completeness_note"] = completeness_note
    elif source in COMPLETENESS_NOTES:
        payload["completeness_note"] = COMPLETENESS_NOTES[source]

    return [TextContent(type="text", text=json.dumps(payload, indent=2, ensure_ascii=False))]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    import time as _time
    _t0 = _time.monotonic()
    try:
        # Dispatch to handler
        _handlers = {
            "search_sources": lambda: handle_search_sources(arguments),
            "search_text": lambda: handle_search_text(arguments),
            "search_images": lambda: handle_search_images(arguments),
            "search_literary": lambda: handle_search_literary(arguments),
            "search_external": lambda: handle_search_external(arguments),
            "get_full_text": lambda: handle_get_full_text(arguments),
            "get_chunk_context": lambda: handle_get_chunk_context(arguments),
            "collection_stats": lambda: handle_collection_stats(arguments),
            "check_russian_shadow": lambda: handle_check_russian_shadow(arguments),
            "check_modern_form": lambda: handle_check_modern_form(arguments),
            "verify_quote": lambda: handle_verify_quote(arguments),
            "verify_word": lambda: handle_verify_word(arguments),
            "verify_source_attribution": lambda: handle_verify_source_attribution(arguments),
            "verify_words": lambda: handle_verify_words(arguments),
            "verify_lemma": lambda: handle_verify_lemma(arguments),
            "query_wikipedia": lambda: handle_query_wikipedia(arguments),
            "query_grac": lambda: handle_query_grac(arguments),
            "query_ulif": lambda: handle_query_ulif(arguments),
            "query_r2u": lambda: handle_query_r2u(arguments),
            "query_e2u": lambda: handle_query_e2u(arguments),
            "query_sum20": lambda: handle_query_sum20(arguments),
            "query_slovnyk_me": lambda: handle_query_slovnyk_me(arguments),
            "query_pravopys": lambda: handle_query_pravopys(arguments),
            "search_slovnyk_me": lambda: handle_search_slovnyk_me(arguments),
            "search_heritage": lambda: handle_search_heritage(arguments),
            "search_style_guide": lambda: handle_dict_search(arguments, "style_guide", "Антоненко-Давидович"),
            "query_cefr_level": lambda: handle_dict_search(arguments, "puls_cefr", "PULS CEFR"),
            "search_definitions": lambda: handle_dict_search(arguments, "sum11", "СУМ-11"),
            "search_grinchenko_1907": lambda: handle_dict_search(arguments, "grinchenko_dict", "Грінченко"),
            "search_esum": lambda: handle_search_esum(arguments),
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
    limit = min(args.get("limit", 5), 20)

    from wiki.sources_db import search_textbooks
    keywords = {w for w in query.lower().split() if len(w) >= 3}
    hits = await asyncio.to_thread(search_textbooks, keywords, limit)

    if not hits:
        return [TextContent(type="text", text="No results found.")]

    lines = [f"Found {len(hits)} results for: \"{query}\"\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"### Result {i}")
        lines.append(f"- **Section**: {hit.get('section_title', hit.get('title', ''))}")
        lines.append(f"- **Source**: Grade {hit.get('grade', '?')}, {hit.get('author', '?')}")
        lines.append(f"- **Chunk ID**: `{hit.get('chunk_id', '')}`")
        lines.append(f"- **Text**:\n{hit.get('text', '')}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_search_sources(args: dict) -> list[TextContent]:
    query = args["query"]
    # Empty-string track is intentional: `_prepare_query()` handles ad-hoc
    # string queries without needing a concrete curriculum track.
    track = str(args.get("track", "") or "")
    limit = min(args.get("limit", 10), 20)

    from wiki.sources_db import search_sources

    hits = await asyncio.to_thread(search_sources, query, track=track, limit=limit)

    if not hits:
        return [TextContent(type="text", text="[]")]

    return [TextContent(type="text", text=json.dumps(hits, ensure_ascii=False, indent=2))]


async def handle_search_literary(args: dict) -> list[TextContent]:
    query = args["query"]
    limit = min(args.get("limit", 5), 20)

    from wiki.sources_db import search_literary
    keywords = {w for w in query.lower().split() if len(w) >= 3}
    hits = await asyncio.to_thread(search_literary, keywords, limit)

    if not hits:
        return [TextContent(type="text", text="No literary results found.")]

    lines = [f"Found {len(hits)} results for: \"{query}\"\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"### Result {i}")
        lines.append(f"- **Author**: {hit.get('author', '?')}")
        lines.append(f"- **Source**: {hit.get('source_file', '?')}")
        lines.append(f"- **Chunk ID**: `{hit.get('chunk_id', '')}`")
        lines.append(f"- **Text**:\n{hit.get('text', '')}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]



async def handle_search_external(args: dict) -> list[TextContent]:
    query = args["query"]
    limit = min(args.get("max_results", 10), 20)

    from wiki.sources_db import search_external

    keywords = {w for w in query.lower().split() if len(w) >= 3}
    hits = await asyncio.to_thread(
        search_external,
        keywords,
        max_total=limit,
        channel=args.get("channel"),
        register=args.get("register"),
        decolonization=args.get("decolonization"),
        min_quality_tier=args.get("min_quality_tier", 2),
        track=args.get("track"),
    )

    if not hits:
        return [TextContent(type="text", text="[]")]

    payload = [
        {
            "chunk_id": hit.get("chunk_id", ""),
            "title": hit.get("title", ""),
            "text": hit.get("text", ""),
            "url": hit.get("url", ""),
            "channel_id": hit.get("channel_id", ""),
            "channel_name": hit.get("source_name", hit.get("channel_id", "")),
            "speaker": hit.get("speaker", ""),
            "register_tag": hit.get("register_tag", ""),
            "decolonization_tag": hit.get("decolonization_tag", ""),
            "quality_tier": hit.get("quality_tier"),
            "publish_date": hit.get("publish_date", ""),
            "duration_s": hit.get("duration_s"),
            "chunk_start_ts": hit.get("chunk_start_ts"),
            "chunk_end_ts": hit.get("chunk_end_ts"),
            "video_id": hit.get("video_id", ""),
            "fts_score": hit.get("fts_score", hit.get("rank")),
            "adjusted_score": hit.get("adjusted_score", hit.get("rank")),
        }
        for hit in hits
    ]
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False, indent=2))]


async def handle_get_full_text(args: dict) -> list[TextContent]:
    work = args["work"]
    max_chars = args.get("max_chars", 50000)

    from wiki.sources_db import search_literary
    keywords = {w for w in work.lower().split() if len(w) >= 3}
    hits = await asyncio.to_thread(search_literary, keywords, 100)

    if not hits:
        return [TextContent(type="text", text=f"No literary text found for: '{work}'")]

    # Concatenate all matching chunks up to max_chars
    text_parts = []
    total = 0
    for h in hits:
        chunk_text = h.get("text", "")
        if total + len(chunk_text) > max_chars:
            break
        text_parts.append(chunk_text)
        total += len(chunk_text)

    return [TextContent(type="text", text="\n\n---\n\n".join(text_parts))]


async def handle_search_images(args: dict) -> list[TextContent]:
    return [TextContent(type="text", text="Image search deferred — will be available for l2-uk-direct track.")]


async def handle_get_chunk_context(args: dict) -> list[TextContent]:
    chunk_id = args["chunk_id"]

    from wiki.sources_db import _get_conn
    try:
        conn = _get_conn()
    except FileNotFoundError:
        return [TextContent(type="text", text="Sources database not found.")]

    # Search all tables for the chunk_id
    for table in ("textbooks", "literary_texts"):
        row = conn.execute(
            f"SELECT * FROM {table} WHERE chunk_id = ?", (chunk_id,)
        ).fetchone()
        if row:
            return [TextContent(type="text", text=f"**[{chunk_id}]** — {dict(row).get('title', '')}\n\n{dict(row).get('text', '')}")]

    return [TextContent(type="text", text=f"No context found for chunk: {chunk_id}")]


async def handle_collection_stats(args: dict) -> list[TextContent]:
    from wiki.sources_db import list_tables
    stats = await asyncio.to_thread(list_tables)
    return [TextContent(type="text", text=json.dumps(stats, indent=2))]


def _is_archaic(tags: str | None) -> bool:
    """Helper to check if 'arch' tag exists in VESUM tag string."""
    if not tags:
        return False
    return "arch" in tags.split(":")


async def handle_check_modern_form(args: dict) -> list[TextContent]:
    word = args["word"]

    from scripts.verification.vesum import verify_word
    matches = await asyncio.to_thread(verify_word, word, None)

    if not matches:
        return [TextContent(type="text", text=json.dumps({
            "is_modern_codified": False,
            "has_archaic_form": False,
            "has_only_archaic_form": False,
            "error": "Word not found in VESUM."
        }))]

    has_archaic = False
    has_modern = False
    for m in matches:
        if _is_archaic(m.get("tags")):
            has_archaic = True
        else:
            has_modern = True

    return [TextContent(type="text", text=json.dumps({
        "is_modern_codified": has_modern,
        "has_archaic_form": has_archaic,
        "has_only_archaic_form": has_archaic and not has_modern
    }))]


async def handle_verify_word(args: dict) -> list[TextContent]:
    word = args["word"]
    pos_filter = args.get("pos_filter")

    from scripts.verification.vesum import verify_word
    matches = await asyncio.to_thread(verify_word, word, pos_filter)

    if not matches:
        return [TextContent(type="text", text=f"'{word}' — NOT FOUND in VESUM. This word form may not exist in standard Ukrainian.")]

    lines = [f"'{word}' — {len(matches)} match(es) in VESUM:\n"]
    for m in matches:
        tags = m.get("tags") or ""
        archaic = _is_archaic(tags)
        lines.append(f"- **lemma**: {m.get('lemma')}  |  **pos**: {m.get('pos')}  |  **tags**: `{tags}`  |  **is_archaic**: {archaic}")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_verify_words(args: dict) -> list[TextContent]:
    words = args["words"]
    pos_filter = args.get("pos_filter")

    from scripts.verification.vesum import verify_words
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

    from scripts.verification.vesum import verify_lemma
    forms = await asyncio.to_thread(verify_lemma, lemma)

    if not forms:
        return [TextContent(type="text", text=f"Lemma '{lemma}' — NOT FOUND in VESUM.")]

    # Group forms by POS for readability
    by_pos: dict[str, list] = {}
    has_archaic_forms = False
    for f in forms:
        is_archaic = _is_archaic(f.get("tags"))
        if is_archaic:
            has_archaic_forms = True
        f["is_archaic"] = is_archaic
        by_pos.setdefault(f.get("pos", "unknown"), []).append(f)

    lines = [f"'{lemma}' — {len(forms)} form(s) across {len(by_pos)} POS (has_archaic_forms: {has_archaic_forms}):\n"]
    for pos, pos_forms in by_pos.items():
        lines.append(f"### {pos} ({len(pos_forms)} forms)")
        for f in pos_forms:
            tags = f.get("tags") or ""
            is_archaic = f.get("is_archaic", False)
            lines.append(f"- {f.get('word_form')}  |  `{tags}`  |  **is_archaic**: {is_archaic}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


def _lookup_wikipedia_in_db(query: str) -> dict | None:
    """Serve the pre-ingested wikipedia table in sources.db as a persistent
    cache (#1170). Matches by exact title first, then by FTS5 title match.
    Returns None if the query isn't in the DB — callers must then fall back
    to the live API.
    """
    import contextlib
    import sqlite3
    from pathlib import Path as _Path

    db = _Path(__file__).resolve().parents[3] / "data" / "sources.db"
    if not db.exists():
        return None
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        # 1. Exact title match (case-insensitive) — the common case after
        #    fetch_wikipedia.py has ingested a batch from plan topics.
        row = conn.execute(
            "SELECT title, url, text FROM wikipedia WHERE LOWER(title) = LOWER(?) LIMIT 1",
            (query,),
        ).fetchone()
        if row:
            return dict(row)
        # 2. FTS5 title search — tolerates minor variations (e.g. caller
        #    passes "Тарас Шевченко" when DB has "Шевченко Тарас Григорович").
        #    Use MATCH on the title column only to avoid pulling large
        #    body-text hits for short queries.
        row = conn.execute(
            """SELECT w.title, w.url, w.text
               FROM wikipedia w
               JOIN wikipedia_fts fts ON fts.rowid = w.id
               WHERE wikipedia_fts MATCH ?
               ORDER BY rank LIMIT 1""",
            (f'title:"{query}"',),
        ).fetchone()
        if row:
            return dict(row)
    except sqlite3.Error:
        return None
    finally:
        if conn is not None:
            with contextlib.suppress(Exception):
                conn.close()
    return None


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

            # Persistent DB cache hit (#1170): pre-ingested wikipedia table in
            # sources.db serves as a long-lived, curated cache. If the query
            # maps to an already-fetched article we return it without an API
            # round trip AND without touching the file cache — the DB is the
            # source of truth for batch-ingested entries.
            db_hit = _lookup_wikipedia_in_db(query)
            if db_hit is not None:
                lines = [
                    f"# {db_hit['title']}",
                    f"**URL**: {db_hit['url']}",
                    "",
                    db_hit["text"],
                ]
                text = "\n".join(lines)
                cache.put("extract", query, text)
                return [TextContent(type="text", text=text)]

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


async def handle_query_sum20(args: dict) -> list[TextContent]:
    """Live single-query lookup of СУМ-20 via slovnyk.me/dict/newsum.

    Backed by slovnyk.me's clean per-word URLs (#1677 routes around the
    broken sum20ua.com search-page parser). Per-query live fetch with
    citation. NO bulk crawl, NO DB persist. Issue: #1667.
    """
    word = args["word"]

    from rag.source_query import slovnyk_me_lookup
    result = await asyncio.to_thread(slovnyk_me_lookup, word, "newsum")

    if not result:
        return [TextContent(
            type="text",
            text=(
                f"No СУМ-20 entry found for '{word}'. "
                f"Note: СУМ-20 covers vols 1–16 (А–Р) only — words starting "
                f"С–Я are not yet published. For СУМ-11 (1970–1980, partially "
                f"Sovietized) fallback, use `search_definitions` or "
                f"`query_slovnyk_me(word, dict='sum')`."
            ),
        )]

    return [TextContent(
        type="text",
        text=(
            f"**СУМ-20 entry for '{word}'**\n"
            f"**URL**: {result['url']}\n"
            f"**Source**: {result['dict_label']} (via slovnyk.me — © Slovnyk.me; "
            f"original © Український мовно-інформаційний фонд НАН України)\n\n"
            f"{result['text'][:3000]}"
        ),
    )]


async def handle_query_slovnyk_me(args: dict) -> list[TextContent]:
    """Live single-query lookup against slovnyk.me — multi-dictionary.

    Per-query live fetch with citation. NO bulk crawl, NO DB persist.
    License posture: slovnyk.me © notice plus third-party source rights;
    per-query lookup with attribution only. Issue: #1667.
    """
    word = args["word"]
    dict_slug = args.get("dict", "newsum")

    from rag.source_query import SLOVNYK_ME_DICTS, resolve_slovnyk_me_dict_slug, slovnyk_me_lookup

    canonical_slug = resolve_slovnyk_me_dict_slug(dict_slug)
    if canonical_slug not in SLOVNYK_ME_DICTS:
        valid = ", ".join(sorted(SLOVNYK_ME_DICTS.keys()))
        return [TextContent(
            type="text",
            text=(
                f"Unknown dictionary slug '{dict_slug}'. "
                f"Valid options: {valid}"
            ),
        )]

    result = await asyncio.to_thread(slovnyk_me_lookup, word, canonical_slug)

    if not result:
        return [TextContent(
            type="text",
            text=(
                f"No entry found for '{word}' in slovnyk.me/{canonical_slug} "
                f"({SLOVNYK_ME_DICTS[canonical_slug]})."
            ),
        )]

    return [TextContent(
        type="text",
        text=(
            f"**{result['dict_label']} — entry for '{word}'**\n"
            f"**URL**: {result['url']}\n"
            f"**Source**: slovnyk.me (per-query live fetch, © Slovnyk.me)\n\n"
            f"{result['text'][:3000]}"
        ),
    )]


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
    """Generic handler for dictionary/reference collection searches — uses SQLite."""
    query = args.get("query", args.get("word", ""))
    limit = min(args.get("limit", 3), 10)

    # Map old Qdrant collection names to sources_db functions
    from wiki import sources_db as sdb
    _LOOKUP = {
        "style_guide": sdb.search_style_guide,
        "puls_cefr": sdb.query_cefr_level,
        "sum11": sdb.search_definitions,
        "grinchenko_dict": sdb.search_grinchenko_1907,
        "frazeolohichnyi": sdb.search_idioms,
        "ukrajinet": sdb.search_synonyms,
        "balla_en_uk": sdb.translate_en_uk,
    }

    func = _LOOKUP.get(collection)
    if not func:
        return [TextContent(type="text", text=f"Unknown collection: {collection}")]

    hits = await asyncio.to_thread(func, query, limit)

    if not hits:
        return [TextContent(type="text", text=f"No results in {label} for: \"{query}\"")]

    lines = [f"Found {len(hits)} results in **{label}** for: \"{query}\"\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"### Result {i}")
        word = hit.get("word", hit.get("words", ""))
        if word:
            lines.append(f"- **Headword**: {word}")
        if hit.get("source"):
            lines.append(f"- **Source**: {hit['source']}")
        # Sovietization flag (СУМ-11 only — issue #1659). Surfaced prominently
        # so reviewer can decide before reading the definition.
        risk = hit.get("sovietization_risk")
        if risk is not None and risk > 0:
            keywords = hit.get("sovietization_keywords", "")
            risk_label = "HIGH" if risk == 2 else "present"
            lines.append(
                f"- **⚠️ Sovietization risk**: {risk_label} "
                f"(matched: {keywords or 'unknown'}). "
                f"Treat definition as potentially Soviet-framed — see #1659."
            )
        definition = hit.get("definition", hit.get("definitions", ""))
        if definition:
            lines.append(f"- **Definition**: {str(definition)[:500]}")
        text = hit.get("text", "")
        if text and text != definition:
            lines.append(f"- **Text**: {text[:500]}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


async def handle_search_slovnyk_me(args: dict) -> list[TextContent]:
    """Search slovnyk.me curated rows plus optional live direct-entry fallback."""
    query = args.get("query", args.get("word", ""))
    dictionaries = args.get("dictionaries")
    if dictionaries is not None and not isinstance(dictionaries, list):
        dictionaries = [str(dictionaries)]
    limit = min(args.get("limit", 5), 20)
    live = bool(args.get("live", True))

    from wiki import sources_db as sdb

    hits = await asyncio.to_thread(
        sdb.search_slovnyk_me,
        query,
        limit,
        dictionaries,
        live=live,
    )
    if not hits:
        return [TextContent(type="text", text=f"No slovnyk.me results for: \"{query}\"")]

    lines = [f"Found {len(hits)} slovnyk.me result(s) for: \"{query}\"\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"### Result {i}")
        lines.append(f"- **Headword**: {hit.get('word', '')}")
        lines.append(f"- **Dictionary**: {hit.get('dictionary_label', hit.get('dictionary_slug', ''))}")
        if hit.get("source_url"):
            lines.append(f"- **URL**: {hit['source_url']}")
        flags = []
        if hit.get("is_modern"):
            flags.append("modern")
        if hit.get("is_dialect"):
            flags.append("heritage/regional")
        if hit.get("is_russianism"):
            flags.append("possible Russianism/calque")
        if flags:
            lines.append(f"- **Flags**: {', '.join(flags)}")
        risk = int(hit.get("sovietization_risk") or 0)
        if risk > 0:
            lines.append(
                f"- **Sovietization risk**: {risk} "
                f"({hit.get('sovietization_keywords', '') or 'keywords unknown'})"
            )
        snippet = str(hit.get("snippet") or hit.get("text") or "")
        if snippet:
            lines.append(f"- **Snippet**: {snippet[:700]}")
        lines.append(f"- **Score**: {float(hit.get('score', 0.0)):.1f}")
        lines.append("")
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_search_heritage(args: dict) -> list[TextContent]:
    """Merge heritage-defense sources for a headword."""
    query = args.get("query", args.get("word", ""))
    limit = min(args.get("limit", 8), 20)
    include_live_slovnyk = bool(args.get("include_live_slovnyk", True))

    from wiki import sources_db as sdb

    hits = await asyncio.to_thread(
        sdb.search_heritage,
        query,
        limit,
        include_live_slovnyk=include_live_slovnyk,
    )
    if not hits:
        return [TextContent(type="text", text=f"No heritage evidence found for: \"{query}\"")]

    lines = [f"Found {len(hits)} heritage evidence row(s) for: \"{query}\"\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"### Evidence {i}")
        lines.append(f"- **Source family**: {hit.get('source_family', '')}")
        lines.append(f"- **Source**: {hit.get('source', '')}")
        lines.append(f"- **Headword**: {hit.get('word', '')}")
        lines.append(f"- **Classification**: {hit.get('classification', '')}")
        lines.append(f"- **Authentic Ukrainian**: {bool(hit.get('is_authentic_ukrainian'))}")
        lines.append(f"- **Russianism/calque warning**: {bool(hit.get('is_russianism'))}")
        if hit.get("url"):
            lines.append(f"- **URL**: {hit['url']}")
        tags = hit.get("evidence_tags") or []
        if tags:
            lines.append(f"- **Evidence tags**: {', '.join(tags)}")
        risk = int(hit.get("sovietization_risk") or 0)
        if risk > 0:
            lines.append(
                f"- **Sovietization risk**: {risk} "
                f"({hit.get('sovietization_keywords', '') or 'keywords unknown'})"
            )
        text = str(hit.get("text") or "")
        if text:
            lines.append(f"- **Text**: {text[:700]}")
        lines.append(f"- **Score**: {float(hit.get('score', 0.0)):.1f}")
        lines.append("")
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_search_esum(args: dict) -> list[TextContent]:
    """Search ЕСУМ entries in sources.db."""
    query = args.get("query", "")
    volume = args.get("volume")
    limit = min(args.get("limit", 5), 10)

    from wiki import sources_db as sdb

    hits = await asyncio.to_thread(sdb.search_esum, query, volume, limit)
    if not hits:
        # Placeholder / hint for unimplemented volumes or missing entries (#1658)
        hint = {
            "status": "not_implemented",
            "hint": f"Tier 2 WebFetch goroh.pp.ua/Етимологія/{query}"
        }
        return [TextContent(type="text", text=json.dumps(hint, ensure_ascii=False))]

    lines = [f"Found {len(hits)} results in **ЕСУМ** for: \"{query}\"\n"]
    for i, hit in enumerate(hits, 1):
        lines.append(f"### Result {i}")
        lines.append(f"- **Lemma**: {hit.get('lemma', '')}")
        lines.append(f"- **Volume**: {hit.get('vol', '')}")
        lines.append(f"- **Page**: {hit.get('page', '')}")
        text = str(hit.get("etymology_text", ""))
        if text:
            lines.append(f"- **Etymology**: {text[:800]}")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]


async def main_stdio():
    """Run the MCP sources server via stdio (spawned by Claude Code)."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def create_http_app():
    """Create the standalone HTTP app with SSE and Streamable HTTP transports."""
    import anyio
    from mcp.server.sse import SseServerTransport
    from mcp.server.streamable_http import StreamableHTTPServerTransport
    from starlette.applications import Starlette
    from starlette.responses import Response
    from starlette.routing import Mount, Route

    sse = SseServerTransport("/messages/")

    def _scope_with_default_accept(scope):
        method = scope.get("method")
        default_accept = b"text/event-stream" if method == "GET" else b"application/json"
        headers = [
            (name, value)
            for name, value in scope["headers"]
            if name.lower() != b"accept"
        ]
        accept_values = [
            value.strip()
            for name, value in scope["headers"]
            if name.lower() == b"accept"
            for value in value.split(b",")
        ]
        if not accept_values or accept_values == [b"*/*"]:
            headers.append((b"accept", default_accept))
            return {**scope, "headers": headers}
        return scope

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

    class StreamableHTTPEndpoint:
        async def __call__(self, scope, receive, send):
            http_transport = StreamableHTTPServerTransport(
                mcp_session_id=None,
                is_json_response_enabled=True,
            )
            scope = _scope_with_default_accept(scope)

            async with http_transport.connect() as streams:
                read_stream, write_stream = streams

                async def run_streamable_http_server():
                    with contextlib.suppress(Exception):
                        await server.run(
                            read_stream,
                            write_stream,
                            server.create_initialization_options(),
                            stateless=True,
                        )

                async with anyio.create_task_group() as tg:
                    tg.start_soon(run_streamable_http_server)
                    await http_transport.handle_request(scope, receive, send)
                    await http_transport.terminate()
                    tg.cancel_scope.cancel()

    app = Starlette(
        routes=[
            Route("/health", endpoint=handle_health),
            Route("/sse", endpoint=handle_sse),
            Route("/mcp", endpoint=StreamableHTTPEndpoint(), methods=["GET", "POST", "DELETE"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    return app


async def main_sse(host: str = "127.0.0.1", port: int = 8766):
    """Run the MCP sources server as a standalone SSE daemon."""
    import uvicorn

    # Verify SQLite sources database exists
    from wiki.sources_db import source_count
    try:
        total = source_count()
        print(f"SQLite sources database: {total:,} entries ✅")
    except FileNotFoundError:
        print("⚠️  Sources database not found. Run: .venv/bin/python scripts/wiki/build_sources_db.py")

    # create_http_app keeps server.run(..., stateless=True) for HTTP transports.
    app = create_http_app()

    print(f"MCP Sources Server (SSE) running on http://{host}:{port}")
    print(f"  SSE endpoint: http://{host}:{port}/sse")
    print(f"  Streamable HTTP endpoint: http://{host}:{port}/mcp")
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
