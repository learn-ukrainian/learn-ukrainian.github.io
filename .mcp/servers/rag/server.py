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
    from mcp.types import Tool, TextContent
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
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "search_text":
            return await handle_search_text(arguments)
        elif name == "search_images":
            return await handle_search_images(arguments)
        elif name == "search_literary":
            return await handle_search_literary(arguments)
        elif name == "get_full_text":
            return await handle_get_full_text(arguments)
        elif name == "get_chunk_context":
            return await handle_get_chunk_context(arguments)
        elif name == "collection_stats":
            return await handle_collection_stats(arguments)
        elif name == "verify_word":
            return await handle_verify_word(arguments)
        elif name == "verify_lemma":
            return await handle_verify_lemma(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
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


async def main():
    """Run the MCP RAG server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
