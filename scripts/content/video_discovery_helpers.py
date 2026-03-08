"""Helper functions for video_discovery.py — keyword building, blog/RAG search, formatting.

Extracted to reduce module complexity and improve maintainability index.
All functions are imported back into video_discovery.py for backward compatibility.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Keyword cleaning — extract clean lemmas from vocab hint strings
# ---------------------------------------------------------------------------

def extract_lemmas_from_hints(hints: list[str]) -> list[str]:
    """Extract clean lemmas from vocabulary hint strings.

    Input examples:
        "цей / ця / це / ці (this) -- High frequency"  -> ["цей", "ця", "це", "ці"]
        "книга (book)"  -> ["книга"]
        "ходити / йти (to walk/go)"  -> ["ходити", "йти"]

    Returns a flat list of individual Ukrainian words (lemmas).
    """
    lemmas: list[str] = []
    for hint in hints:
        if not hint or not isinstance(hint, str):
            continue
        clean = re.split(r'\s*[\(\u2014]', hint)[0].strip()
        clean = re.split(r'\s+[-\u2013]\s+', clean)[0].strip()
        parts = [p.strip() for p in clean.split("/")]
        for part in parts:
            words = part.split()
            for w in words:
                w = w.strip(",;.")
                if w and re.match(r"^[\u0430-\u044f\u0456\u0457\u0454\u0491\u0410-\u042f\u0406\u0407\u0404\u0490\u2019\u0027\u02bc-]+$", w):
                    lemmas.append(w)
    return lemmas


def build_search_keywords(
    topic_title: str,
    vocab_hints: list[str] | dict,
    max_keywords: int = 8,
) -> list[str]:
    """Build clean keyword list for video/blog search."""
    keywords = [topic_title]

    hints_list: list[str] = []
    if isinstance(vocab_hints, dict):
        hints_list = vocab_hints.get("required", [])[:10]
    elif isinstance(vocab_hints, list):
        hints_list = vocab_hints[:10]

    lemmas = extract_lemmas_from_hints(hints_list)
    seen: set[str] = {topic_title.lower()}
    for lemma in lemmas:
        if lemma.lower() not in seen:
            seen.add(lemma.lower())
            keywords.append(lemma)
        if len(keywords) >= max_keywords:
            break

    return keywords


def _extract_noun_phrases(text: str) -> list[str]:
    """Extract key noun phrases from objective strings."""
    phrases: list[str] = []
    if not text:
        return phrases
    cleaned = re.sub(
        r"^(Learner\s+)?can\s+\w+\s+(and\s+\w+\s+)?",
        "", text, flags=re.IGNORECASE,
    ).strip()
    cleaned = re.sub(
        r"^(\u0423\u0447\u0435\u043d\u044c|\u0421\u0442\u0443\u0434\u0435\u043d\u0442)\s+(\u043c\u043e\u0436\u0435|\u0437\u0434\u0430\u0442\u043d\u0438\u0439|\u0432\u043c\u0456\u0454)\s+\w+\s+",
        "", cleaned, flags=re.IGNORECASE,
    ).strip()
    if cleaned and len(cleaned) > 3:
        cleaned = re.sub(r"^\d+\s+", "", cleaned)
        phrases.append(cleaned)
    return phrases


def build_discovery_keywords(
    plan: dict,
    max_keywords: int = 12,
) -> list[str]:
    """Build keyword list for discovery from full plan metadata."""
    if not plan:
        return []

    keywords: list[str] = []
    seen: set[str] = set()

    def _add(term: str) -> bool:
        if len(keywords) >= max_keywords:
            return False
        key = term.lower().strip()
        if not key or key in seen:
            return False
        seen.add(key)
        keywords.append(term.strip())
        return True

    title = plan.get("title", "")
    if title:
        _add(title)

    _generic = {
        "\u0432\u0441\u0442\u0443\u043f", "\u043f\u0456\u0434\u0441\u0443\u043c\u043e\u043a",
        "introduction", "summary", "conclusion",
        "\u043f\u0440\u0435\u0437\u0435\u043d\u0442\u0430\u0446\u0456\u044f", "presentation",
        "\u043f\u0440\u0430\u043a\u0442\u0438\u043a\u0430", "practice",
        "\u043f\u0440\u043e\u0434\u0443\u043a\u0446\u0456\u044f", "production",
        "\u043f\u0440\u043e\u0434\u0443\u043a\u0446\u0456\u044f \u0442\u0430 \u043f\u0456\u0434\u0441\u0443\u043c\u043e\u043a",
        "production and summary",
    }
    for section in plan.get("content_outline", []):
        section_title = section.get("section", "")
        if not section_title:
            continue
        en_match = re.search(r"\(([^)]+)\)", section_title)
        base = re.split(r"\s*[\(\u2014]", section_title)[0].strip()
        colon_parts = base.split(":", 1)
        if len(colon_parts) == 2 and colon_parts[0].strip().lower() in _generic:
            descriptive = colon_parts[1].strip()
            if descriptive:
                _add(descriptive)
        elif base.lower() not in _generic:
            _add(base)
        if en_match:
            en_text = en_match.group(1).strip()
            en_colon = en_text.split(":", 1)
            if len(en_colon) == 2 and en_colon[0].strip().lower() in _generic:
                descriptive = en_colon[1].strip()
                if descriptive:
                    _add(descriptive)
            elif en_text.lower() not in _generic:
                _add(en_text)

    for obj in plan.get("objectives", []):
        if not isinstance(obj, str):
            continue
        for phrase in _extract_noun_phrases(obj):
            _add(phrase)

    for gram in plan.get("grammar", []):
        if isinstance(gram, str) and gram.strip():
            _add(gram.strip())

    focus = plan.get("focus", "")
    if focus and isinstance(focus, str):
        _add(focus)

    vocab_hints = plan.get("vocabulary_hints", {})
    hints_list: list[str] = []
    if isinstance(vocab_hints, dict):
        hints_list = vocab_hints.get("required", [])[:10]
    elif isinstance(vocab_hints, list):
        hints_list = vocab_hints[:10]
    for lemma in extract_lemmas_from_hints(hints_list):
        _add(lemma)

    return keywords


def cap_query(keywords: list[str], max_len: int = 120) -> str:
    """Join keywords into a query string, capping total length."""
    query = ""
    for kw in keywords:
        candidate = f"{query} {kw}".strip() if query else kw
        if len(candidate) > max_len:
            break
        query = candidate
    return query or keywords[0][:max_len] if keywords else ""


# ---------------------------------------------------------------------------
# Blog discovery — static DB matching
# ---------------------------------------------------------------------------

_BLOG_STOPWORDS = {
    "ukrainian", "english", "language", "learn", "learning", "lesson",
    "introduce", "introduction", "explain", "practice", "identify",
    "demonstrate", "apply", "define", "understand", "review", "summary",
    "module", "section", "chapter", "guide", "rule", "rules", "self",
    "correctly", "fluently", "basic", "advanced", "common", "simple",
    "using", "about", "with", "from", "that", "this", "what", "where",
    "which", "have", "will", "they", "their", "your", "into", "also",
    "when", "more", "most", "some", "other", "each", "both", "than",
    "very", "only", "just", "make", "take", "give", "know", "help",
    "read", "write", "open", "leave", "never",
}


def _build_search_terms(topic_title, keywords):
    """Build search phrases and words from keywords, filtering stopwords."""
    search_phrases: list[str] = [topic_title.lower()]
    search_words: set[str] = set()
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if not kw_lower or kw_lower in _BLOG_STOPWORDS:
            continue
        if " " in kw_lower:
            search_phrases.append(kw_lower)
        else:
            search_words.add(kw_lower)
    for word in topic_title.lower().split():
        if len(word) > 3 and word not in _BLOG_STOPWORDS:
            search_words.add(word)
    return search_phrases, search_words


def _score_article(article, search_phrases, search_words, level_base):
    """Score a single article against search terms. Returns score or None if below threshold."""
    article_topics = {t.lower() for t in article.get("topics", [])}
    article_title = article.get("title", "").lower()
    article_title_words = set(article_title.split())
    article_level = article.get("suggested_level", "").upper()
    desc = article.get("description", "").lower()
    desc_words = set(desc.split())

    phrase_score = 0.0
    for phrase in search_phrases:
        if phrase in article_title or phrase in desc:
            phrase_score += 0.5
        elif any(phrase in t for t in article_topics):
            phrase_score += 0.4

    topic_overlap = len(search_words & article_topics)
    title_overlap = len(search_words & article_title_words)
    desc_overlap = len(search_words & desc_words)
    level_match = 1 if article_level == level_base else 0

    if phrase_score == 0 and topic_overlap == 0 and (title_overlap + desc_overlap) < 2:
        return None

    score = phrase_score + topic_overlap * 0.25 + title_overlap * 0.1 + desc_overlap * 0.05 + level_match * 0.1

    content_type = article.get("content_type", "")
    if content_type in ("podcast_episode", "podcast_episode_short"):
        score += 0.1

    return score if score >= 0.3 else None


def _search_blog_dbs(level, topic_title, keywords, results, seen_urls, load_blog_dbs_fn):
    """Layer 2: Keyword matching against blog/podcast DBs."""
    all_articles = load_blog_dbs_fn()
    if not all_articles:
        return

    search_phrases, search_words = _build_search_terms(topic_title, keywords)
    level_base = level.split("-")[0].upper()

    for article in all_articles:
        url = article.get("url", "")
        if url in seen_urls:
            continue

        score = _score_article(article, search_phrases, search_words, level_base)
        if score is None:
            continue

        seen_urls.add(url)
        source = article.get("source", "ukrainianlessons.com")
        if "dobraforma" in url or "opentext.ku.edu" in url:
            source = "dobraforma"

        entry: dict[str, Any] = {
            "url": url,
            "title": article.get("title", ""),
            "source": source,
            "relevance_score": min(score, 1.0),
            "topics": article.get("topics", []),
        }
        content_type = article.get("content_type", "")
        if content_type.startswith("podcast_episode"):
            entry["content_type"] = content_type
            entry["series"] = article.get("series", "")
            entry["season"] = article.get("season", 0)
            entry["episode"] = article.get("episode", 0)
        results.append(entry)


# ---------------------------------------------------------------------------
# Blog/RAG formatting
# ---------------------------------------------------------------------------

def format_blog_discovery(blogs: list[dict]) -> str:
    """Format blog results as markdown for {BLOG_DISCOVERY} placeholder."""
    if not blogs:
        return "(No blog articles found)"

    podcasts = [b for b in blogs if b.get("content_type", "").startswith("podcast_episode")]
    articles = [b for b in blogs if not b.get("content_type", "").startswith("podcast_episode")]

    lines: list[str] = []

    if podcasts:
        lines.append("### Podcast Episodes")
        lines.append("*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*")
        lines.append("")
        for b in podcasts:
            series = b.get("series", "ULP")
            season = b.get("season", 0)
            ep = b.get("episode", 0)
            label = f"{series} S{season} Ep{ep}" if season else f"{series} Ep{ep}"
            lines.append(f"- **{label}: {b['title']}**")
            lines.append(f"  URL: {b['url']}")
            lines.append(f"  Relevance: {b.get('relevance_score', 0):.1f}")
            if b.get("topics"):
                lines.append(f"  Topics: {', '.join(b['topics'][:5])}")
            lines.append("")

    if articles:
        lines.append("### Blog Articles & Guides")
        for b in articles:
            lines.append(f"- **{b['title']}** ({b.get('source', 'unknown')})")
            lines.append(f"  URL: {b['url']}")
            lines.append(f"  Relevance: {b.get('relevance_score', 0):.1f}")
            if b.get("topics"):
                lines.append(f"  Topics: {', '.join(b['topics'][:5])}")
            lines.append("")

    return "\n".join(lines)


def format_rag_discovery(
    text_chunks: list[dict],
    images: list[dict],
    literary: list[dict],
) -> str:
    """Format RAG results as markdown for the content prompt."""
    sections: list[str] = []

    if text_chunks:
        lines = ["### Textbook References"]
        for ch in text_chunks:
            section = ch.get("section_title", "")
            grade = ch.get("grade", 0)
            text = ch.get("text", "")[:200]
            header = f"Grade {grade}" if grade else "Textbook"
            if section:
                header += f", {section}"
            lines.append(f"- **{header}**")
            lines.append(f"  {text}...")
            lines.append("")
        sections.append("\n".join(lines))

    if images:
        lines = ["### Textbook Images"]
        for img in images:
            desc = img.get("description_uk", "")
            assoc = img.get("associated_text_uk", "")
            tv = img.get("teaching_value", "")
            grade = img.get("grade", 0)
            path = img.get("image_path", "")
            label = desc or assoc or "(no description)"
            lines.append(f"- **Grade {grade}** [{tv}]: {label}")
            if path:
                lines.append(f"  Path: {path}")
            lines.append("")
        sections.append("\n".join(lines))

    if literary:
        lines = ["### Literary Primary Sources"]
        for lit in literary:
            work = lit.get("work", "")
            year = lit.get("year", "")
            genre = lit.get("genre", "")
            text = lit.get("text", "")[:200]
            lines.append(f"- **{work}** ({year}, {genre})")
            lines.append(f"  {text}...")
            lines.append("")
        sections.append("\n".join(lines))

    if not sections:
        return "(No RAG content found)"
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# RAG discovery
# ---------------------------------------------------------------------------

_SEMINAR_TRACKS = {"hist", "istorio", "bio", "lit", "oes", "ruth"}

_LEVEL_GRADE_RANGES: dict[str, tuple[int, int]] = {
    "A1": (1, 4),
    "A2": (2, 6),
    "B1": (4, 8),
    "B2": (6, 11),
    "C1": (7, 11),
    "C2": (8, 11),
}


def search_rag(
    keywords: list[str],
    track: str,
    level: str = "",
    limit_text: int = 5,
    limit_images: int = 3,
    limit_literary: int = 3,
    is_qdrant_available_fn=None,
) -> dict[str, list[dict]]:
    """Search RAG collections for relevant content."""
    result: dict[str, list[dict]] = {
        "text_chunks": [],
        "images": [],
        "literary": [],
    }

    check_fn = is_qdrant_available_fn or _default_qdrant_check
    if not check_fn():
        logger.debug("RAG: Qdrant not available, skipping")
        return result

    try:
        from rag.query import search_images, search_literary, search_text
    except ImportError:
        logger.debug("RAG: rag.query not importable, skipping")
        return result

    query = cap_query(keywords)
    if not query:
        return result

    base_track = track.split("-")[0].lower()
    level_base = level.split("-")[0].upper() if level else ""

    # 1. Textbook chunks
    try:
        grade_range = _LEVEL_GRADE_RANGES.get(level_base)
        text_hits = search_text(query, limit=limit_text * 2)
        _PRIORITY_AUTHORS = {"bolshakova", "vashulenko", "zabolotnyi", "avramenko"}
        if grade_range:
            lo, hi = grade_range
            is_beginner = level_base in ("A1", "A2")
            scored = []
            for h in text_hits:
                g = h.get("grade", 0)
                source = h.get("source", "")
                if lo <= g <= hi:
                    grade_bonus = 0.3 if is_beginner else 0.1
                elif g > 0 and is_beginner:
                    distance = max(0, g - hi, lo - g)
                    grade_bonus = -0.05 * distance
                else:
                    grade_bonus = 0.0
                author_bonus = 0.15 if any(a in source for a in _PRIORITY_AUTHORS) else 0.0
                scored.append((h["score"] + grade_bonus + author_bonus, h))
            scored.sort(key=lambda x: x[0], reverse=True)
            result["text_chunks"] = [h for _, h in scored[:limit_text]]
        else:
            result["text_chunks"] = text_hits[:limit_text]
    except Exception as e:
        logger.debug("RAG text search failed: %s", e)

    # 2. Textbook images
    if limit_images > 0:
        try:
            img_hits = search_images(query, teaching_value="high", limit=limit_images)
            if len(img_hits) < limit_images:
                img_hits += search_images(
                    query, teaching_value="medium",
                    limit=limit_images - len(img_hits),
                )
            result["images"] = img_hits[:limit_images]
        except Exception as e:
            logger.debug("RAG image search failed: %s", e)

    # 3. Literary sources — seminar tracks only
    if base_track in _SEMINAR_TRACKS:
        try:
            lit_hits = search_literary(query, limit=limit_literary)
            result["literary"] = lit_hits
        except Exception as e:
            logger.debug("RAG literary search failed: %s", e)

    return result


def _default_qdrant_check() -> bool:
    """Default Qdrant availability check."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(
            host="localhost", grpc_port=6334,
            prefer_grpc=True, check_compatibility=False,
            timeout=3,
        )
        client.get_collections()
        return True
    except Exception:
        return False
