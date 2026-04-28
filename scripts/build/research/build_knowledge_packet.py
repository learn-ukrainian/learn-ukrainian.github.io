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
from build.linear_pipeline import LinearPipelineError

# Add scripts/ to path for rag imports
SCRIPTS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SCRIPTS_DIR))

# Pre-compiled regexes (avoid recompilation per call)
_RE_CYRILLIC = re.compile(r"[А-ЯІЇЄҐа-яіїєґ]")
_RE_TEXTBOOK_REF = re.compile(
    r"((?:Большакова|Вашуленко|Заболотний|Авраменко|Пономарова|"
    r"Кравцова|Захарійчук|Варзацька|Літвінова|Караман|Голуб)"
    r"\s+Grade\s+\d+\s+p\.\d+)"
)
_RE_TEXTBOOK_PARSE = re.compile(r"(\w+)\s+Grade\s+(\d+)\s+p\.(\d+)")
_RE_CYRILLIC_PHRASE = re.compile(
    r"[А-ЯІЇЄҐа-яіїєґ'][А-ЯІЇЄҐа-яіїєґ'ʼ\s\-]{4,40}"
)
_RE_GRADE = re.compile(r"Grade\s+(\d+)")
_RE_MULTI_SPACE = re.compile(r"\s{2,}")
_RE_PAREN_SPLIT = re.compile(r"\s*\(")

KNOWLEDGE_PACKET_FLOOR = 5


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
    uk_title = _RE_PAREN_SPLIT.split(title)[0].strip()
    if uk_title and _has_cyrillic(uk_title):
        queries.append(uk_title)

    # Extract key terms from points
    points = section.get("points", [])
    for point in points:
        if not isinstance(point, str):
            continue
        # Extract textbook references for targeted search
        # e.g., "Большакова Grade 1 p.24" → search what's on that page
        refs = _RE_TEXTBOOK_REF.findall(point)
        for ref in refs:
            match = _RE_TEXTBOOK_PARSE.match(ref)
            if match:
                queries.append(f"{match.group(1)} сторінка {match.group(3)}")

        # Extract Ukrainian phrases (words in Cyrillic, 2+ words)
        # Look for quoted phrases or key Ukrainian terms
        cyrillic_phrases = _RE_CYRILLIC_PHRASE.findall(point)
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
    return bool(_RE_CYRILLIC.search(text))


def _extract_grade_hint(plan: dict) -> int | None:
    """Extract a grade hint from plan references for targeted RAG search."""
    refs = plan.get("references", [])
    grades = []
    for ref in refs:
        title = ref.get("title", "") + " " + ref.get("notes", "")
        matches = _RE_GRADE.findall(title)
        grades.extend(int(g) for g in matches)
    if grades:
        return min(grades)  # Use lowest grade (most foundational)
    return None


# Priority textbook authors by grade range (the native reviewer-recommended)
_PRIORITY_AUTHORS_EARLY = {"bolshakova", "vashulenko", "zaharijchuk"}  # Grade 1-2
_PRIORITY_AUTHORS_LATE = {"zabolotnyi", "avramenko", "litvinova", "golub"}  # Grade 5-11

# Exercise markers — chunks that are mostly student instructions, not theory
_EXERCISE_MARKERS = (
    "Вправа ", "вправа ", "Завдання", "завдання",
    "Спишіть", "спишіть", "Прочитайте", "прочитайте",
    "Запишіть", "запишіть", "Випишіть", "випишіть",
    "Перепишіть", "перепишіть", "Доберіть", "доберіть",
    "Складіть", "складіть", "Поставте", "поставте",
    "Визначте", "визначте", "Утворіть", "утворіть",
)


def _is_exercise_chunk(text: str) -> bool:
    """Detect if a chunk is primarily exercises, not theory.

    Exercise chunks are low-value for knowledge packets — we want
    explanations and examples, not instructions to students.
    """
    marker_count = sum(1 for m in _EXERCISE_MARKERS if m in text)
    return marker_count >= 3


def _heuristic_score(hit: dict, grade_hint: int | None) -> float:
    """Compute a heuristic boost/penalty for pedagogical relevance (#1098).

    Applied after initial retrieval to reorder results by:
    - Author priority (textbook authors recommended by the native reviewer)
    - Grade match (prefer chunks from the target grade)
    - Exercise penalty (demote exercise-heavy chunks)
    - Length bonus (longer theory excerpts have more context)

    Returns a modifier (-0.3 to +0.3) added to the retrieval score.
    """
    boost = 0.0
    author = hit.get("author", "").lower()
    grade = hit.get("grade", 0)
    text = hit.get("text", "")

    # Author priority
    target_early = grade_hint is not None and grade_hint <= 4
    if target_early:
        if author in _PRIORITY_AUTHORS_EARLY:
            boost += 0.15
    else:
        if author in _PRIORITY_AUTHORS_LATE:
            boost += 0.15

    # Grade match
    if grade_hint and grade == grade_hint:
        boost += 0.10
    elif grade_hint and grade and abs(grade - grade_hint) <= 1:
        boost += 0.05  # Adjacent grade — still useful

    # Exercise penalty
    if _is_exercise_chunk(text):
        boost -= 0.25

    # Length bonus for theory-rich excerpts
    if len(text) > 500 and not _is_exercise_chunk(text):
        boost += 0.05

    return boost


def _search_rag(query: str, grade: int | None = None,
                limit: int = 3, allow_degraded: bool = False) -> list[dict]:
    """Query the RAG textbook index with heuristic reranking (#1098).

    Over-fetches 3x candidates, then reranks by pedagogical relevance:
    author priority, grade match, exercise penalty.
    """
    try:
        from rag.query import search_text
        # Over-fetch for reranking headroom
        candidates = search_text(query, grade=grade, limit=limit * 3)
    except Exception as e:
        if allow_degraded:
            # RAG server might not be running — degrade gracefully
            print(f"  ⚠️  RAG search failed for '{query}': {e}")
            return []
        # Fall-through to re-raise as LinearPipelineError in build_packet
        raise

    if not candidates:
        return []

    # Apply heuristic boosts
    for hit in candidates:
        base_score = hit.get("score", 0)
        h_boost = _heuristic_score(hit, grade)
        hit["final_score"] = base_score + h_boost

    # Re-sort by boosted score
    candidates.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    return candidates[:limit]


def _format_hit(hit: dict) -> str:
    """Format a single RAG hit as markdown."""
    text = hit.get("text", "").strip()
    if not text or len(text) < 50:
        return ""  # Skip empty or too-short excerpts (TOC entries, page numbers)

    grade = hit.get("grade", "?")
    author = hit.get("author", "unknown")
    page = hit.get("page", "?")
    score = hit.get("score", 0)
    chunk_id = hit.get("chunk_id", "")

    # Clean up text — remove excessive whitespace
    text = _RE_MULTI_SPACE.sub(" ", text)
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


def _build_section_packet(section: dict, grade_hint: int | None, allow_degraded: bool = False) -> str:
    """Build knowledge packet content for one plan section."""
    title = section.get("section", "Untitled")
    queries = _extract_search_queries(section)

    if not queries:
        return f"### {title}\n\n*No search queries extracted.*\n"

    lines = [f"### {title}\n"]

    seen_chunks = set()
    hits_added = 0

    for query in queries:
        results = _search_rag(query, grade=grade_hint, limit=3, allow_degraded=allow_degraded)
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
        if not allow_degraded:
            raise LinearPipelineError(
                f"Section {title!r} retrieved 0 chunks from RAG (floor: {KNOWLEDGE_PACKET_FLOOR})"
            )
        lines.append("*No relevant textbook excerpts found.*\n")
    elif hits_added < KNOWLEDGE_PACKET_FLOOR and not allow_degraded:
        raise LinearPipelineError(
            f"Section {title!r} retrieved only {hits_added} chunks from RAG (floor: {KNOWLEDGE_PACKET_FLOOR})"
        )

    # Also search for dialogue/situational examples on the topic
    # Textbooks have real conversations that the writer should adapt
    if queries:
        topic_keyword = queries[0].split()[0] if queries[0] else title
        dialogue_query = f"{topic_keyword} діалог розмова вправа"
        try:
            dialogue_results = _search_rag(dialogue_query, grade=grade_hint, limit=2, allow_degraded=allow_degraded)
        except Exception:
            if allow_degraded:
                dialogue_results = []
            else:
                raise
        dialogue_hits = 0
        for hit in dialogue_results:
            chunk_id = hit.get("chunk_id", "")
            if chunk_id in seen_chunks:
                continue
            seen_chunks.add(chunk_id)
            formatted = _format_hit(hit)
            if formatted:
                if dialogue_hits == 0:
                    lines.append("\n**Textbook dialogue/exercise examples:**\n")
                lines.append(formatted)
                dialogue_hits += 1

    return "\n".join(lines)


def build_packet(plan_path: Path, allow_degraded_rag: bool = False) -> str:
    """Build a complete Knowledge Packet from a plan file.

    Args:
        plan_path: Path to the plan YAML file.
        allow_degraded_rag: If True, log warnings and return thin packets on RAG failure.

    Returns:
        Markdown string with structured textbook excerpts per section.
    """
    if not allow_degraded_rag:
        _verify_qdrant_liveness()

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
        packet = _build_section_packet(section, grade_hint, allow_degraded=allow_degraded_rag)
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

    # МійКлас grammar references (#1040)
    miyklas_section = ""
    try:
        from build.miyklas import build_miyklas_knowledge_section
        miyklas_section = build_miyklas_knowledge_section(plan)
    except Exception as e:
        if allow_degraded_rag:
            print(f"  ⚠️  МійКлас integration skipped: {e}")
        else:
            raise LinearPipelineError(f"МійКлас integration failed: {e}") from e

    return (
        header
        + "\n\n".join(section_packets)
        + "\n"
        + "\n".join(ref_lines)
        + miyklas_section
        + footer
    )


def _verify_qdrant_liveness() -> None:
    """Verify Qdrant is reachable and collections are populated.

    Fail-fast check for knowledge packet generation.
    """
    from rag.config import TEXT_COLLECTION
    from rag.query import collection_stats, get_client

    try:
        client = get_client()
        # 1. Connection check
        client.get_collections()
    except Exception as e:
        raise LinearPipelineError(
            "Qdrant on 127.0.0.1:6334 is not reachable. "
            "Start it with: ./services.sh start rag"
        ) from e

    # 2. Population check
    try:
        stats = collection_stats()
        text_stats = stats.get(TEXT_COLLECTION, {})
        if "error" in text_stats:
            raise LinearPipelineError(
                f"Qdrant collection {TEXT_COLLECTION!r} check failed: {text_stats['error']}"
            )
        count = text_stats.get("points_count", 0)
        if count == 0:
            raise LinearPipelineError(
                f"Qdrant collection {TEXT_COLLECTION!r} is empty. "
                "Ensure RAG indices are built and data/qdrant/ is populated."
            )
    except LinearPipelineError:
        raise
    except Exception as e:
        raise LinearPipelineError(f"Failed to verify Qdrant stats: {e}") from e


# CLI for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build knowledge packet from plan")
    parser.add_argument("plan", type=Path, help="Path to plan YAML")
    parser.add_argument("--output", "-o", type=Path, help="Output file (default: stdout)")
    parser.add_argument("--allow-degraded-rag", action="store_true", help="Allow thin packets on RAG failure")
    args = parser.parse_args()

    result = build_packet(args.plan, allow_degraded_rag=args.allow_degraded_rag)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, "utf-8")
        print(f"✅ Written to {args.output} ({result.count('> **Source:**')} excerpts)")
    else:
        print(result)
