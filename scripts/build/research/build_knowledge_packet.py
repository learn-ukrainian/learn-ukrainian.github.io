"""Build a Knowledge Packet from plan + RAG for the V6 pipeline.

Reads a plan YAML, extracts search queries from each section's points,
queries the RAG textbook index, and produces a structured markdown packet
that the writer LLM consumes as inline context.

The packet is organized by plan section so the writer can reference
textbook excerpts directly when writing each section.

Usage:
    from research.build_knowledge_packet import build_packet
    packet = build_packet(Path("curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml"))

Issue: #994
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# Add scripts/ to path for rag imports
SCRIPTS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SCRIPTS_DIR))


def _extract_search_queries(section: dict) -> list[str]:
    """Extract Ukrainian search queries from a plan section's points.

    Strategy:
    1. Take the section title (strip English in parentheses)
    2. Extract Ukrainian phrases from each point (quoted Ukrainian words,
       textbook references, key terms)
    3. Deduplicate and limit to avoid over-querying
    """
    queries = []

    # Section title — strip English parenthetical
    title = section.get("section", "")
    # "Звуки і літери (Sounds and Letters)" → "Звуки і літери"
    uk_title = re.split(r"\s*\(", title)[0].strip()
    if uk_title and _has_cyrillic(uk_title):
        queries.append(uk_title)

    # Extract key terms from points
    points = section.get("points", [])
    for point in points:
        if not isinstance(point, str):
            continue
        # Extract textbook references for targeted search
        # e.g., "Большакова Grade 1 p.24" → search what's on that page
        refs = re.findall(
            r"((?:Большакова|Вашуленко|Заболотний|Авраменко|Пономарова|"
            r"Кравцова|Захарійчук|Варзацька|Літвінова|Караман|Голуб)"
            r"\s+Grade\s+\d+\s+p\.\d+)",
            point,
        )
        for ref in refs:
            # Parse "Большакова Grade 1 p.24" → author, grade, page
            match = re.match(r"(\w+)\s+Grade\s+(\d+)\s+p\.(\d+)", ref)
            if match:
                queries.append(f"{match.group(1)} сторінка {match.group(3)}")

        # Extract Ukrainian phrases (words in Cyrillic, 2+ words)
        # Look for quoted phrases or key Ukrainian terms
        cyrillic_phrases = re.findall(
            r"[А-ЯІЇЄҐа-яіїєґ'][А-ЯІЇЄҐа-яіїєґ'ʼ\s\-]{4,40}",
            point,
        )
        for phrase in cyrillic_phrases:
            phrase = phrase.strip()
            if len(phrase.split()) >= 2 and _has_cyrillic(phrase):
                queries.append(phrase)

    # Deduplicate preserving order, limit to 4 queries per section
    seen = set()
    unique = []
    for q in queries:
        q_lower = q.lower().strip()
        if q_lower not in seen and len(q_lower) > 3:
            seen.add(q_lower)
            unique.append(q)
    return unique[:4]


def _has_cyrillic(text: str) -> bool:
    """Check if text contains Cyrillic characters."""
    return bool(re.search(r"[А-ЯІЇЄҐа-яіїєґ]", text))


def _extract_grade_hint(plan: dict) -> int | None:
    """Extract a grade hint from plan references for targeted RAG search."""
    refs = plan.get("references", [])
    grades = []
    for ref in refs:
        title = ref.get("title", "") + " " + ref.get("notes", "")
        matches = re.findall(r"Grade\s+(\d+)", title)
        grades.extend(int(g) for g in matches)
    if grades:
        return min(grades)  # Use lowest grade (most foundational)
    return None


def _search_rag(query: str, grade: int | None = None,
                limit: int = 3) -> list[dict]:
    """Query the RAG textbook index. Returns list of hit dicts."""
    try:
        from rag.query import search_text
        return search_text(query, grade=grade, limit=limit)
    except Exception as e:
        # RAG server might not be running — degrade gracefully
        print(f"  ⚠️  RAG search failed for '{query}': {e}")
        return []


def _format_hit(hit: dict) -> str:
    """Format a single RAG hit as markdown."""
    text = hit.get("text", "").strip()
    if not text:
        return ""

    grade = hit.get("grade", "?")
    author = hit.get("author", "unknown")
    page = hit.get("page", "?")
    score = hit.get("score", 0)
    chunk_id = hit.get("chunk_id", "")

    # Clean up text — remove excessive whitespace
    text = re.sub(r"\s{2,}", " ", text)
    # Truncate very long excerpts
    if len(text) > 400:
        text = text[:400] + "..."

    return (
        f"> **Source:** Grade {grade}, {author}, p.{page} "
        f"(score: {score:.2f})\n"
        f"> **Chunk:** `{chunk_id}`\n"
        f">\n"
        f"> {text}\n"
    )


def _build_section_packet(section: dict, grade_hint: int | None) -> str:
    """Build knowledge packet content for one plan section."""
    title = section.get("section", "Untitled")
    queries = _extract_search_queries(section)

    if not queries:
        return f"### {title}\n\n*No search queries extracted.*\n"

    lines = [f"### {title}\n"]

    seen_chunks = set()
    hits_added = 0

    for query in queries:
        results = _search_rag(query, grade=grade_hint, limit=3)
        for hit in results:
            chunk_id = hit.get("chunk_id", "")
            if chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk_id)

            formatted = _format_hit(hit)
            if formatted:
                lines.append(formatted)
                hits_added += 1

            if hits_added >= 5:  # Max 5 excerpts per section
                break
        if hits_added >= 5:
            break

    if hits_added == 0:
        lines.append("*No relevant textbook excerpts found.*\n")

    return "\n".join(lines)


def build_packet(plan_path: Path) -> str:
    """Build a complete Knowledge Packet from a plan file.

    Args:
        plan_path: Path to the plan YAML file.

    Returns:
        Markdown string with structured textbook excerpts per section.
    """
    plan = yaml.safe_load(plan_path.read_text("utf-8"))

    title = plan.get("title", "Unknown")
    slug = plan.get("slug", "unknown")
    level = plan.get("level", "?")
    module_id = plan.get("module", "?")
    grade_hint = _extract_grade_hint(plan)

    header = (
        f"# Knowledge Packet: {title}\n\n"
        f"**Module:** {module_id} | **Level:** {level} | "
        f"**Slug:** {slug}\n"
        f"**Grade hint:** {grade_hint or 'none'}\n\n"
        f"---\n\n"
        f"## Textbook Excerpts by Section\n\n"
        f"*Curated from Ukrainian school textbooks via RAG. "
        f"Use these as source material — cite specific examples, "
        f"adapt pedagogy, but write original prose.*\n\n"
    )

    sections = plan.get("content_outline", [])
    section_packets = []
    total_hits = 0

    for section in sections:
        packet = _build_section_packet(section, grade_hint)
        section_packets.append(packet)
        total_hits += packet.count("> **Source:**")

    # Add references section
    refs = plan.get("references", [])
    ref_lines = ["---\n\n## Plan References\n"]
    for ref in refs:
        ref_title = ref.get("title", "")
        ref_notes = ref.get("notes", "")
        ref_url = ref.get("url", "")
        line = f"- **{ref_title}**"
        if ref_notes:
            line += f": {ref_notes}"
        if ref_url:
            line += f" ([link]({ref_url}))"
        ref_lines.append(line)

    footer = (
        f"\n---\n\n"
        f"*Knowledge Packet generated for V6 pipeline. "
        f"{total_hits} textbook excerpts from RAG.*\n"
    )

    return header + "\n\n".join(section_packets) + "\n" + "\n".join(ref_lines) + footer


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build knowledge packet from plan")
    parser.add_argument("plan", type=Path, help="Path to plan YAML")
    parser.add_argument("--output", "-o", type=Path, help="Output file (default: stdout)")
    args = parser.parse_args()

    result = build_packet(args.plan)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, "utf-8")
        print(f"✅ Written to {args.output} ({result.count('> **Source:**')} excerpts)")
    else:
        print(result)
