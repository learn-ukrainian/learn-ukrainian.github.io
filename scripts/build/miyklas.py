"""МійКлас (miyklas.com.ua) integration for V6 build pipeline.

Provides two capabilities:
1. RESEARCH: fetch theory page content for knowledge packet enrichment
2. ENRICH: inject matching МійКлас URLs into Ресурсі tab

Matching logic: plan YAML `grammar` and `focus` fields are tokenized and
compared against each index entry's `tags` list via keyword overlap scoring.
No per-module manual mapping needed — works for any A1-C1 module.

Issue: #1040
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_INDEX_PATH = _PROJECT_ROOT / "data" / "miyklas" / "grammar_index.yaml"
_BASE_URL = "https://miyklas.com.ua"

# Pre-compiled: strip parenthetical English, punctuation, quotes
_RE_PAREN = re.compile(r"\([^)]*\)")
_RE_NON_ALPHA = re.compile(r"[^\w\s]", re.UNICODE)

# CEFR level → approximate Ukrainian school grade mapping
# Used to boost matches from the appropriate difficulty band
_LEVEL_GRADE_MAP: dict[str, tuple[int, int]] = {
    "a1": (5, 6),
    "a2": (5, 7),
    "b1": (6, 8),
    "b2": (8, 10),
    "c1": (9, 11),
    "c2": (10, 11),
}

# Focus field → category mapping for additional filtering
_FOCUS_CATEGORY: dict[str, str | None] = {
    "phonetics": "phonetics",
    "grammar": None,  # grammar is too broad — match all categories
    "vocabulary": "lexicology",
    "communication": None,
    "review": None,
}


@lru_cache(maxsize=1)
def _load_index() -> list[dict]:
    """Load and cache the МійКлас grammar index YAML."""
    if not _INDEX_PATH.exists():
        return []
    try:
        data = yaml.safe_load(_INDEX_PATH.read_text("utf-8"))
        return data.get("topics", [])
    except Exception:
        return []


def _tokenize(text: str) -> set[str]:
    """Normalize text into a set of lowercase keyword tokens.

    Strips English parentheticals, punctuation, and short tokens.
    """
    text = _RE_PAREN.sub("", text)
    text = _RE_NON_ALPHA.sub(" ", text.lower())
    return {t for t in text.split() if len(t) > 2}


def _extract_plan_keywords(plan: dict) -> set[str]:
    """Extract searchable keywords from plan grammar and focus fields.

    Sources:
    - plan.grammar: list of grammar topic strings
    - plan.focus: single focus keyword
    - plan.content_outline[].section: section titles (Ukrainian part only)
    """
    tokens: set[str] = set()

    # Grammar items (primary matching source)
    for item in plan.get("grammar", []):
        if isinstance(item, str):
            tokens |= _tokenize(item)

    # Focus field
    focus = plan.get("focus", "")
    if focus:
        tokens |= _tokenize(focus)

    # Section titles from content_outline (strip English parentheticals)
    for section in plan.get("content_outline", []):
        title = section.get("section", "")
        if title:
            # Keep only the Ukrainian part (before parenthesis)
            uk_part = _RE_PAREN.sub("", title).strip()
            tokens |= _tokenize(uk_part)

    return tokens


def find_matching_topics(plan: dict, max_results: int = 5) -> list[dict]:
    """Find МійКлас topics that match a plan's grammar content.

    Scoring:
    - Base score = number of tag tokens that overlap with plan keywords
    - Grade proximity bonus: +1 if within the CEFR→grade band
    - Category bonus: +1 if focus field maps to the topic's category
    - Minimum threshold: score >= 2 (avoids noise from single-word matches)

    Returns list of dicts with keys: title, url, grade, category, score.
    """
    index = _load_index()
    if not index:
        return []

    plan_keywords = _extract_plan_keywords(plan)
    if not plan_keywords:
        return []

    level = plan.get("level", "").lower()
    grade_lo, grade_hi = _LEVEL_GRADE_MAP.get(level, (5, 11))
    focus = plan.get("focus", "")
    focus_category = _FOCUS_CATEGORY.get(focus)

    scored: list[tuple[float, dict]] = []

    for entry in index:
        entry_tags = {t.lower() for t in entry.get("tags", [])}
        overlap = plan_keywords & entry_tags
        if not overlap:
            continue

        score = len(overlap)

        # Grade proximity bonus
        entry_grade = entry.get("grade", 0)
        if grade_lo <= entry_grade <= grade_hi:
            score += 1

        # Category alignment bonus
        if focus_category and entry.get("category") == focus_category:
            score += 1

        if score < 2:
            continue

        url_path = entry.get("url", "")
        full_url = f"{_BASE_URL}{url_path}" if url_path.startswith("/") else url_path

        scored.append((score, {
            "title": entry.get("title", ""),
            "url": full_url,
            "grade": entry_grade,
            "category": entry.get("category", ""),
            "score": score,
        }))

    # Sort by score descending, then by grade ascending (foundational first)
    scored.sort(key=lambda x: (-x[0], x[1].get("grade", 99)))
    return [item for _, item in scored[:max_results]]


def build_miyklas_resource_entries(plan: dict) -> list[dict]:
    """Build resource entries for the ENRICH step's Ресурсі tab.

    Returns a list of dicts compatible with _build_resources() format:
    [{title, url, source, type}]
    """
    matches = find_matching_topics(plan, max_results=3)
    return [
        {
            "title": f"МійКлас: {m['title']}",
            "url": m["url"],
            "source": "miyklas.com.ua",
            "type": "articles",
        }
        for m in matches
    ]


def build_miyklas_knowledge_section(plan: dict) -> str:
    """Build a knowledge packet section with МійКлас theory references.

    For the RESEARCH step — adds matched topics as pointers
    (not full page content, which is fetched on-demand by the writer).

    Returns markdown string, or empty string if no matches.
    """
    matches = find_matching_topics(plan, max_results=5)
    if not matches:
        return ""

    lines = [
        "",
        "---",
        "",
        "## МійКлас Grammar References",
        "",
        "*Matched Ukrainian school grammar theory pages from miyklas.com.ua (Grades 5-11, NUS aligned).*",
        "*Use WebFetch to retrieve full theory content for any topic below.*",
        "",
    ]

    for m in matches:
        lines.append(
            f"- **{m['title']}** (Grade {m['grade']}, {m['category']}) — "
            f"[МійКлас]({m['url']})"
        )

    lines.append("")
    return "\n".join(lines)
