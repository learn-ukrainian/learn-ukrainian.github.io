#!/usr/bin/env python3
"""Build a Verified Knowledge Packet from plan + RAG textbook search.

Reads a plan YAML, queries RAG per content_outline section, and produces
a structured markdown file with textbook excerpts organized by section.

This replaces the LLM-driven research phase in V6. The output is injected
INLINE into the writing prompt — the writer never needs to read a file.

Usage:
    .venv/bin/python scripts/research/build_knowledge_packet.py a1 1
    .venv/bin/python scripts/research/build_knowledge_packet.py a1 --all

Issue: #994
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

logger = logging.getLogger(__name__)

# Priority textbook authors by grade range
PRIORITY_AUTHORS_EARLY = ["bolshakova", "vashulenko", "zaharijchuk"]  # Grade 1-2
PRIORITY_AUTHORS_LATE = ["zabolotnyi", "avramenko", "litvinova", "golub"]  # Grade 5-11

# Grade mapping by phase
PHASE_GRADES = {
    "A1.1": [1, 2],
    "A1.2": [1, 2, 3],
    "A1.3": [3, 4, 5],
    "A1.4": [3, 4, 5],
    "A1.5": [4, 5, 6],
    "A1.6": [4, 5, 6],
    "A1.7": [5, 6, 7],
    "A1.8": [5, 6, 7],
}


def _extract_ukrainian_keywords(text: str) -> str:
    """Extract Ukrainian keywords from section title and points for RAG search.

    English kills semantic matching — extract only Cyrillic content.
    """
    # Get all Cyrillic words/phrases
    cyrillic_words = re.findall(r'[А-ЯҐЄІЇа-яґєіїʼ\']+(?:\s+[А-ЯҐЄІЇа-яґєіїʼ\']+)*', text)
    # Filter out very short words and duplicates
    keywords = []
    seen = set()
    for w in cyrillic_words:
        w_lower = w.lower()
        if len(w) >= 2 and w_lower not in seen:
            keywords.append(w)
            seen.add(w_lower)
    return " ".join(keywords[:10])  # Limit to 10 keywords


def _is_exercise_chunk(text: str) -> bool:
    """Detect if a chunk is primarily exercises, not theory.

    Exercise chunks are low-value for knowledge packets — we want
    explanations and examples, not instructions to students.
    """
    exercise_markers = [
        "Вправа ", "вправа ", "Завдання", "завдання",
        "Спишіть", "спишіть", "Прочитайте", "прочитайте",
        "Запишіть", "запишіть", "Випишіть", "випишіть",
        "Перепишіть", "перепишіть", "Доберіть", "доберіть",
        "Складіть", "складіть", "Поставте", "поставте",
        "Визначте", "визначте", "Утворіть", "утворіть",
    ]
    marker_count = sum(1 for m in exercise_markers if m in text)
    # If 3+ exercise markers in one chunk, it's mostly exercises
    return marker_count >= 3


def _heuristic_score(result: dict, grades: list[int]) -> float:
    """Compute a heuristic boost/penalty for pedagogical relevance.

    Applied AFTER ColBERT reranking to fine-tune ordering.
    Returns a modifier (-0.3 to +0.3) added to the ColBERT score.
    """
    boost = 0.0
    author = result.get("author", "").lower()
    grade = result.get("grade", 0)
    text = result.get("text", "")

    # Author priority: Большакова/Вашуленко for Grade 1-2, Заболотний/Авраменко for 5-11
    target_early = max(grades) <= 4 if grades else False
    if target_early:
        if author in PRIORITY_AUTHORS_EARLY:
            boost += 0.15
    else:
        if author in PRIORITY_AUTHORS_LATE:
            boost += 0.15

    # Grade match: prefer chunks from the exact target grades
    if grade in grades:
        boost += 0.10
    elif grade and grades and abs(grade - min(grades)) <= 1:
        boost += 0.05  # Adjacent grade — still useful

    # Exercise penalty: demote exercise-heavy chunks
    if _is_exercise_chunk(text):
        boost -= 0.25

    # Length bonus: longer theory excerpts have more context
    if len(text) > 500 and not _is_exercise_chunk(text):
        boost += 0.05

    return boost


def _search_rag(query: str, grades: list[int], limit: int = 3) -> list[dict]:
    """Search RAG textbooks for a query with ColBERT reranking + heuristics (#1098).

    Pipeline: dense+sparse retrieval → ColBERT reranking → heuristic boosts.
    """
    try:
        from rag.query import get_text_encoder, search_text
    except ImportError:
        logger.warning("RAG not available — install rag dependencies")
        return []

    # Over-fetch: get 3x candidates for reranking
    fetch_limit = limit * 3
    results = []
    for grade in grades:
        try:
            hits = search_text(query, grade=grade, limit=fetch_limit)
            if hits:
                results.extend(hits)
        except Exception as e:
            logger.debug("RAG search failed for grade %d: %s", grade, e)

    # Deduplicate by chunk_id
    seen_ids = set()
    unique = []
    for r in results:
        chunk_id = r.get("chunk_id", r.get("id", ""))
        if chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            unique.append(r)

    if not unique:
        return []

    # Stage 1: ColBERT reranking — token-level MaxSim
    try:
        encoder = get_text_encoder()
        # Get more candidates from ColBERT than we need, so heuristics can reorder
        colbert_limit = min(len(unique), limit * 2)
        reranked = encoder.colbert_rerank(query, unique, text_key="text", limit=colbert_limit)
    except Exception as e:
        logger.warning("ColBERT reranking failed, falling back to score sort: %s", e)
        unique.sort(key=lambda x: x.get("score", 0), reverse=True)
        reranked = unique[:limit * 2]

    # Stage 2: Heuristic reranking — author priority, exercise penalty, grade match
    for r in reranked:
        base_score = r.get("colbert_score", r.get("score", 0))
        h_boost = _heuristic_score(r, grades)
        r["final_score"] = base_score + h_boost
        r["heuristic_boost"] = round(h_boost, 3)

    reranked.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    return reranked[:limit]


def _format_result(result: dict) -> str:
    """Format a single RAG result as a citation block."""
    # RAG returns 'author' field directly; fall back to 'source' for legacy compat
    author = result.get("author", result.get("source", result.get("metadata", {}).get("source", "unknown")))
    section = result.get("section_title", result.get("section", result.get("metadata", {}).get("section", "")))
    text = result.get("text", result.get("content", "")).strip()
    score = result.get("score", result.get("relevance_score", 0))
    grade = result.get("grade", result.get("metadata", {}).get("grade", "?"))

    # Clean HTML entities (from МійКлас scraper)
    import html
    text = html.unescape(text)
    # Strip navigation/copyright junk
    for junk in ["Copyright ©", "Відправити відгук", "Знайшли помилку?",
                 "Попередня тема", "Наступна тема", "Усі теми",
                 "Матеріали для вчителів", "Додаткові завдання (Мій+)"]:
        if junk in text:
            text = text[:text.index(junk)].rstrip()

    # Truncate at sentence boundary — keep excerpts useful
    # Average chunk is 1400 chars; show up to 800 to preserve pedagogical content
    if len(text) > 800:
        # Find last sentence-ending punctuation before 800 chars
        for end_char in [". ", ".\n", "? ", "!\n"]:
            last_end = text[:800].rfind(end_char)
            if last_end > 300:  # Don't truncate too aggressively
                text = text[:last_end + 1]
                break
        else:
            text = text[:800] + "..."

    lines = []
    lines.append(f"> **Source:** {author}, Grade {grade}")
    if section:
        lines.append(f"> **Section:** {section}")
    lines.append(f"> **Score:** {score:.2f}")
    lines.append(">")
    for line in text.split("\n"):
        lines.append(f"> {line}")
    lines.append("")
    return "\n".join(lines)


def _match_miyklas_urls(plan: dict) -> list[dict]:
    """Match plan topics to МійКлас URL index entries.

    Returns list of matching lesson dicts with path, title, tags.
    Issue: #1040
    """
    index_path = PROJECT_ROOT / "docs" / "resources" / "miyklas-url-index.yaml"
    if not index_path.exists():
        return []

    try:
        index = yaml.safe_load(index_path.read_text("utf-8"))
    except Exception:
        return []

    # Build search terms from plan
    search_terms: set[str] = set()
    title = plan.get("title", "").lower()
    search_terms.update(title.split())
    for section in plan.get("content_outline", []):
        section_title = section.get("section", "").lower()
        search_terms.update(section_title.split())
    for hint in plan.get("activity_hints", []):
        search_terms.update(hint.get("focus", "").lower().split())

    # Collect all lessons from all grades
    all_lessons: list[dict] = []
    for grade_key, grade_data in index.items():
        if not grade_key.startswith("grade_"):
            continue
        if isinstance(grade_data, dict):
            for _section_key, section_val in grade_data.items():
                if isinstance(section_val, list):
                    all_lessons.extend(section_val)

    # Match by tags
    base_url = index.get("base_url", "https://www.miyklas.com.ua")
    matched: list[dict] = []
    for lesson in all_lessons:
        if not isinstance(lesson, dict):
            continue
        tags = [t.lower() for t in lesson.get("tags", [])]
        hit = False
        for tag in tags:
            if tag in search_terms:
                hit = True
                break
            for term in search_terms:
                if len(term) > 3 and (term in tag or tag in term):
                    hit = True
                    break
            if hit:
                break
        if hit:
            lesson_copy = dict(lesson)
            lesson_copy["full_url"] = base_url + lesson["path"]
            matched.append(lesson_copy)

    return matched[:3]  # Limit to 3 most relevant


def _fetch_miyklas_theory(plan: dict) -> list[str]:
    """Fetch МійКлас theory pages matching the plan's topics.

    Uses lightpanda headless browser for JS-rendered content.
    Falls back to link-only if lightpanda is not available.
    Issue: #1040
    """
    import shutil
    import subprocess

    matched = _match_miyklas_urls(plan)
    if not matched:
        return []

    lightpanda_bin = shutil.which("lightpanda")
    if not lightpanda_bin:
        logger.warning("lightpanda not found — МійКлас content will be link-only")
        lines: list[str] = []
        for lesson in matched:
            title = lesson.get("title", "Unknown")
            url = lesson["full_url"]
            lines.append(f"### {title}")
            lines.append(f"> **Source:** МійКлас — [{title}]({url})")
            lines.append("*(lightpanda not installed — install with: brew or binary download)*")
            lines.append("")
        return lines

    lines: list[str] = []
    for lesson in matched:
        url = lesson["full_url"]
        title = lesson.get("title", "Unknown")

        try:
            # Step 1: Fetch the topic index page to find the first theory sub-page
            result = subprocess.run(
                [lightpanda_bin, "fetch", "--dump", "markdown",
                 "--wait-until", "networkidle", "--wait-ms", "5000",
                 "--strip-mode", "ui,css", url],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0 or not result.stdout:
                raise RuntimeError(f"lightpanda exit {result.returncode}")

            # Find the first theory sub-page link (contains /re- in the URL)
            theory_url = None
            for match in re.finditer(r'\((https://www\.miyklas\.com\.ua/[^)]+/re-[^)]+)\)', result.stdout):
                theory_url = match.group(1)
                break

            if not theory_url:
                raise RuntimeError("No theory sub-page found on index page")

            # Step 2: Fetch the actual theory content page
            result = subprocess.run(
                [lightpanda_bin, "fetch", "--dump", "markdown",
                 "--wait-until", "networkidle", "--wait-ms", "5000",
                 "--strip-mode", "ui,css", theory_url],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0 or not result.stdout:
                raise RuntimeError(f"lightpanda exit {result.returncode} on theory page")

            text = result.stdout

            # Find theory section start FIRST — then strip junk only after it
            theory_start = -1
            for marker in ["### Теорія", "Теорія:", "# 1.", f"# {title[:30]}"]:
                pos = text.find(marker)
                if pos >= 0:
                    theory_start = pos
                    break
            if theory_start < 0:
                theory_start = len(text) // 3  # Skip nav, take middle

            chunk = text[theory_start:]

            # Strip trailing junk AFTER extracting the theory chunk
            for junk in ["Copyright ©", "Відправити відгук", "Знайшли помилку?",
                         "Попередня тема", "Наступна тема", "Усі теми",
                         "Додаткові завдання"]:
                if junk in chunk:
                    chunk = chunk[:chunk.index(junk)].rstrip()

            # Strip navigation lines (links with empty text, menu items)
            chunk_lines = []
            for line in chunk.split("\n"):
                # Skip lines that are pure navigation: empty links, menu items, image refs
                if re.match(r'^\s*\(\[?\]\(', line):
                    continue
                if re.match(r'^\s*!\[', line):
                    continue
                if re.match(r'^\s*\*\*\s*$', line):
                    continue
                if any(nav in line for nav in ["МійВчитель", "Початок", "Вебінари",
                       "Новини сайту", "Пошук на сайті", "Оновлення", "cdn.miyklas"]):
                    continue
                chunk_lines.append(line)
            chunk = "\n".join(chunk_lines)

            # Strip remaining markdown links and images but keep text
            chunk = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', chunk)
            chunk = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', chunk)
            # Strip exercise listings
            chunk = re.sub(r'Складність:\s*\w+\s*\d+', '', chunk)
            chunk = re.sub(r'\n{3,}', '\n\n', chunk).strip()

            # Truncate at sentence boundary — keep it useful but concise
            if len(chunk) > 800:
                for end_char in [". ", ".\n", "? ", "!\n"]:
                    last_end = chunk[:800].rfind(end_char)
                    if last_end > 300:
                        chunk = chunk[:last_end + 1]
                        break
                else:
                    chunk = chunk[:800] + "..."

            if len(chunk) > 100:
                lines.append(f"### {title}")
                lines.append(f"> **Source:** МійКлас — [{title}]({url})")
                lines.append("")
                lines.append(chunk)
                lines.append("")
            else:
                lines.append(f"### {title}")
                lines.append(f"> **Source:** МійКлас — [{title}]({url})")
                lines.append("*(Content too short or failed to extract)*")
                lines.append("")

        except Exception as e:
            logger.warning("МійКлас fetch failed for %s: %s", url, e)
            lines.append(f"### {title}")
            lines.append(f"> **Source:** МійКлас — [{title}]({url})")
            lines.append(f"*(Fetch failed: {e})*")
            lines.append("")

    return lines


def build_packet(plan_path: Path) -> str:
    """Build a knowledge packet from a plan file.

    Returns markdown string structured by plan section.
    """
    plan = yaml.safe_load(plan_path.read_text("utf-8"))
    slug = plan.get("slug", plan_path.stem)
    title = plan.get("title", slug)
    phase = plan.get("phase", "")
    phase_key = phase.split("[")[0].strip() if phase else ""

    # Determine which grades to search
    grades = PHASE_GRADES.get(phase_key, [1, 2, 3, 5])

    sections = plan.get("content_outline", [])
    grammar = plan.get("grammar", [])
    lines = []
    lines.append(f"# Verified Knowledge Packet: {title}")
    lines.append(f"**Module:** {slug} | **Phase:** {phase}")
    lines.append(f"**Textbook grades searched:** {', '.join(str(g) for g in grades)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    total_results = 0

    # Search per section
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_name = section.get("section", "")
        points = section.get("points", [])

        lines.append(f"## {section_name}")
        lines.append("")

        # Build search query from section name + points
        search_text_parts = [section_name]
        for p in points[:3]:  # First 3 points
            if isinstance(p, str):
                # Strip video embed instructions
                if "EMBED VIDEO" in p or "YouTubeVideo" in p:
                    continue
                search_text_parts.append(p[:200])

        combined = " ".join(search_text_parts)
        query = _extract_ukrainian_keywords(combined)

        if not query or len(query) < 3:
            # Fallback: use section name without English
            query = re.sub(r'\([^)]*\)', '', section_name).strip()

        if not query:
            lines.append("*No Ukrainian keywords found for RAG search.*")
            lines.append("")
            continue

        # Budget: guarantee every section gets at least 2 excerpts.
        # Total cap = 20 excerpts (~10K chars). Each section gets 2-3.
        MAX_EXCERPTS = 20
        n_sections = len([s for s in sections if isinstance(s, dict)])
        remaining_sections = max(1, n_sections - sections.index(section))
        # Reserve 2 per remaining section, give this section up to 3
        reserved = 2 * (remaining_sections - 1)
        available = max(0, MAX_EXCERPTS - total_results - reserved)
        per_section = min(3, max(2, available))
        if total_results >= MAX_EXCERPTS:
            lines.append("*(Budget reached — see excerpts in earlier sections)*")
            lines.append("")
            continue

        results = _search_rag(query, grades, limit=per_section)

        if results:
            for r in results:
                if r.get("score", 0) >= 0.25:  # Skip low relevance
                    total_results += 1
                    lines.append(_format_result(r))
        else:
            lines.append(f"*No textbook results found for: {query}*")
            lines.append("")

    # Grammar-specific search (only if budget allows)
    if grammar and total_results < MAX_EXCERPTS:
        lines.append("## Grammar Reference")
        lines.append("")
        grammar_query = _extract_ukrainian_keywords(" ".join(str(g) for g in grammar))
        if grammar_query:
            grammar_budget = min(2, MAX_EXCERPTS - total_results)
            results = _search_rag(grammar_query, grades, limit=grammar_budget)
            if results:
                for r in results:
                    if r.get("score", 0) >= 0.25:
                        total_results += 1
                        lines.append(_format_result(r))
            else:
                lines.append(f"*No grammar results for: {grammar_query}*")
                lines.append("")

    # МійКлас theory pages (#1040) — always include (concise links, not bulk text)
    miyklas_content = _fetch_miyklas_theory(plan)
    if miyklas_content:
        lines.append("")
        lines.append("## МійКлас Theory (miyklas.com.ua)")
        lines.append("")
        lines.append("*Ukrainian school curriculum theory — use this terminology and teaching approach.*")
        lines.append("")
        lines.extend(miyklas_content)
        total_results += 1

    # Summary
    lines.append("---")
    lines.append(f"**Total textbook excerpts found:** {total_results}")
    lines.append(f"**Grades searched:** {', '.join(str(g) for g in grades)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build Verified Knowledge Packet from plan + RAG")
    parser.add_argument("level", help="Level (e.g., a1)")
    parser.add_argument("module", nargs="?", type=int, help="Module number (e.g., 1)")
    parser.add_argument("--all", action="store_true", help="Build for all modules")
    parser.add_argument("--output-dir", type=str, help="Output directory (default: research/)")
    args = parser.parse_args()

    curriculum_root = PROJECT_ROOT / "curriculum" / "l2-uk-en"
    manifest = curriculum_root / "curriculum.yaml"
    data = yaml.safe_load(manifest.read_text())
    slugs = data.get("levels", {}).get(args.level, {}).get("modules", [])

    if not slugs:
        print(f"No modules found for level {args.level}")
        sys.exit(1)

    if args.module:
        if args.module > len(slugs):
            print(f"Module {args.module} not found (max {len(slugs)})")
            sys.exit(1)
        targets = [(args.module, slugs[args.module - 1])]
    elif args.all:
        targets = [(i + 1, s) for i, s in enumerate(slugs)]
    else:
        print("Specify --module N or --all")
        sys.exit(1)

    plans_dir = curriculum_root / "plans" / args.level
    output_dir = Path(args.output_dir) if args.output_dir else curriculum_root / args.level / "research"
    output_dir.mkdir(parents=True, exist_ok=True)

    for num, slug in targets:
        plan_path = plans_dir / f"{slug}.yaml"
        if not plan_path.exists():
            print(f"M{num:02d} {slug}: SKIP (no plan)")
            continue

        print(f"M{num:02d} {slug}: building knowledge packet...", end=" ", flush=True)
        packet = build_packet(plan_path)

        out_path = output_dir / f"{slug}-knowledge-packet.md"
        out_path.write_text(packet, "utf-8")

        # Count results
        result_count = packet.count("> **Source:**")
        print(f"✅ ({result_count} textbook excerpts)")


if __name__ == "__main__":
    main()
