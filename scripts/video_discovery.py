"""Video/blog discovery for the build pipeline.

Searches curated YouTube channels for relevant content, downloads transcripts,
and scores relevance using Gemini Flash. Also matches blog articles from
ukrainianlessons.com and Dobra Forma against module topics.

Non-blocking: all exceptions caught, returns empty/default results on failure.

Used by phase_discover_v4() in build_module.py.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

logger = logging.getLogger(__name__)

TRANSCRIPT_CAP = 50_000
MAX_QUERY_LENGTH = 120  # yt-dlp search breaks with very long queries

# Paths to blog databases (relative to project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
BLOG_DB_PATHS: list[Path] = [
    _PROJECT_ROOT / "docs" / "resources" / "ukrainianlessons" / "blog_db.json",
    _PROJECT_ROOT / "docs" / "resources" / "dobraforma" / "dobraforma_db.json",
    _PROJECT_ROOT / "docs" / "resources" / "talkukrainian" / "talkukrainian_db.json",
    _PROJECT_ROOT / "docs" / "resources" / "verba" / "verba_db.json",
]
PODCAST_DB_PATH = _PROJECT_ROOT / "docs" / "resources" / "podcasts" / "podcast_db.json"
CURATED_RESOURCES_PATH = _PROJECT_ROOT / "docs" / "resources" / "external_resources.yaml"
SCORE_DB_PATH = _PROJECT_ROOT / "docs" / "resources" / "ukrainianlessons" / "resource_module_scores_final.json"


# ---------------------------------------------------------------------------
# Keyword cleaning — extract clean lemmas from vocab hint strings
# ---------------------------------------------------------------------------

def extract_lemmas_from_hints(hints: list[str]) -> list[str]:
    """Extract clean lemmas from vocabulary hint strings.

    Input examples:
        "цей / ця / це / ці (this) — High frequency"  → ["цей", "ця", "це", "ці"]
        "книга (book)"  → ["книга"]
        "ходити / йти (to walk/go)"  → ["ходити", "йти"]

    Returns a flat list of individual Ukrainian words (lemmas).
    """
    lemmas: list[str] = []
    for hint in hints:
        if not hint or not isinstance(hint, str):
            continue
        # Strip everything after ( or — or - (when preceded by space)
        clean = re.split(r'\s*[\(—]', hint)[0].strip()
        # Also strip trailing " - description" patterns
        clean = re.split(r'\s+[-–]\s+', clean)[0].strip()
        # Split on / to get individual forms
        parts = [p.strip() for p in clean.split("/")]
        for part in parts:
            # Only keep Ukrainian words (Cyrillic), skip English
            words = part.split()
            for w in words:
                w = w.strip(",;.")
                if w and re.match(r"^[а-яіїєґА-ЯІЇЄҐ''ʼ-]+$", w):
                    lemmas.append(w)
    return lemmas


def build_search_keywords(
    topic_title: str,
    vocab_hints: list[str] | dict,
    max_keywords: int = 8,
) -> list[str]:
    """Build clean keyword list for video/blog search.

    Combines topic title with clean lemmas extracted from vocabulary hints.
    Caps total keyword count and total query length.
    """
    keywords = [topic_title]

    # Extract hints list
    hints_list: list[str] = []
    if isinstance(vocab_hints, dict):
        hints_list = vocab_hints.get("required", [])[:10]
    elif isinstance(vocab_hints, list):
        hints_list = vocab_hints[:10]

    lemmas = extract_lemmas_from_hints(hints_list)
    # Deduplicate while preserving order
    seen: set[str] = {topic_title.lower()}
    for lemma in lemmas:
        if lemma.lower() not in seen:
            seen.add(lemma.lower())
            keywords.append(lemma)
        if len(keywords) >= max_keywords:
            break

    return keywords


def _extract_noun_phrases(text: str) -> list[str]:
    """Extract key noun phrases from objective strings.

    Strips leading verb phrases like "Learner can recognize..." to get
    the object, e.g., "6 Ukrainian letters" → "Ukrainian letters".
    Also handles Ukrainian-language objectives.
    """
    phrases: list[str] = []
    if not text:
        return phrases
    # Strip common objective prefixes (English)
    cleaned = re.sub(
        r"^(Learner\s+)?can\s+\w+\s+(and\s+\w+\s+)?",
        "", text, flags=re.IGNORECASE,
    ).strip()
    # Strip Ukrainian prefixes: "Учень може..." / "Здатний..."
    cleaned = re.sub(
        r"^(Учень|Студент)\s+(може|здатний|вміє)\s+\w+\s+",
        "", cleaned, flags=re.IGNORECASE,
    ).strip()
    if cleaned and len(cleaned) > 3:
        # Remove leading numbers like "6 " or "40 "
        cleaned = re.sub(r"^\d+\s+", "", cleaned)
        phrases.append(cleaned)
    return phrases


def build_discovery_keywords(
    plan: dict,
    max_keywords: int = 12,
) -> list[str]:
    """Build keyword list for discovery from full plan metadata.

    Extracts semantic keywords from multiple plan fields (title, content
    outline, objectives, grammar, focus) to produce better search terms
    than vocabulary lemmas alone.

    Falls back to build_search_keywords() behavior if plan is empty.
    """
    if not plan:
        return []

    keywords: list[str] = []
    seen: set[str] = set()

    def _add(term: str) -> bool:
        """Add term if not duplicate and under cap. Returns True if added."""
        if len(keywords) >= max_keywords:
            return False
        key = term.lower().strip()
        if not key or key in seen:
            return False
        seen.add(key)
        keywords.append(term.strip())
        return True

    # 1. Topic title (always first)
    title = plan.get("title", "")
    if title:
        _add(title)

    # 2. Content outline section titles
    # Generic PPP/structural labels that don't help discovery
    _generic = {
        "вступ", "підсумок", "introduction", "summary", "conclusion",
        "презентація", "presentation", "практика", "practice",
        "продукція", "production",
        "продукція та підсумок", "production and summary",
    }
    for section in plan.get("content_outline", []):
        section_title = section.get("section", "")
        if not section_title:
            continue
        # Extract English part from parentheses if present
        en_match = re.search(r"\(([^)]+)\)", section_title)
        # Get the base (before parenthetical)
        base = re.split(r"\s*[\(—]", section_title)[0].strip()
        # Handle "Generic: Descriptive subtitle" pattern (e.g., "Презентація: Близька родина")
        colon_parts = base.split(":", 1)
        if len(colon_parts) == 2 and colon_parts[0].strip().lower() in _generic:
            # Use the descriptive part after the colon
            descriptive = colon_parts[1].strip()
            if descriptive:
                _add(descriptive)
        elif base.lower() not in _generic:
            _add(base)
        # Also add English label from parens if descriptive
        if en_match:
            en_text = en_match.group(1).strip()
            en_colon = en_text.split(":", 1)
            if len(en_colon) == 2 and en_colon[0].strip().lower() in _generic:
                descriptive = en_colon[1].strip()
                if descriptive:
                    _add(descriptive)
            elif en_text.lower() not in _generic:
                _add(en_text)

    # 3. Objectives → extract noun phrases
    for obj in plan.get("objectives", []):
        if not isinstance(obj, str):
            continue
        for phrase in _extract_noun_phrases(obj):
            _add(phrase)

    # 4. Grammar topics
    for gram in plan.get("grammar", []):
        if isinstance(gram, str) and gram.strip():
            _add(gram.strip())

    # 5. Focus field
    focus = plan.get("focus", "")
    if focus and isinstance(focus, str):
        _add(focus)

    # 6. Vocabulary hints (lower priority — lemmas are specific words)
    vocab_hints = plan.get("vocabulary_hints", {})
    hints_list: list[str] = []
    if isinstance(vocab_hints, dict):
        hints_list = vocab_hints.get("required", [])[:10]
    elif isinstance(vocab_hints, list):
        hints_list = vocab_hints[:10]
    for lemma in extract_lemmas_from_hints(hints_list):
        _add(lemma)

    return keywords


def cap_query(keywords: list[str], max_len: int = MAX_QUERY_LENGTH) -> str:
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

_blog_db_cache: list[dict] | None = None
_score_db_cache: dict | None = None
_curated_cache: dict | None = None


def _load_blog_dbs() -> list[dict]:
    """Load all blog + podcast database files. Returns flat list of article dicts."""
    global _blog_db_cache
    if _blog_db_cache is not None:
        return _blog_db_cache
    articles: list[dict] = []
    for db_path in BLOG_DB_PATHS:
        if not db_path.exists():
            continue
        try:
            data = json.loads(db_path.read_text("utf-8"))
            articles.extend(data.get("articles", []))
        except Exception as e:
            logger.debug("Failed to load blog DB %s: %s", db_path, e)

    # Podcast episodes (normalize to article format)
    if PODCAST_DB_PATH.exists():
        try:
            pod_data = json.loads(PODCAST_DB_PATH.read_text("utf-8"))
            episodes = pod_data if isinstance(pod_data, list) else pod_data.get("episodes", [])
            for ep in episodes:
                articles.append({
                    "id": ep.get("id", ""),
                    "url": ep.get("url", ""),
                    "title": ep.get("title", ""),
                    "topics": ep.get("tags", []),
                    "description": ep.get("summary", ""),
                    "suggested_level": "",
                    "content_type": "podcast_episode",
                    "source": "ukrainianlessons.com",
                    "series": ep.get("season", ""),
                    "season": ep.get("season", 0),
                    "episode": ep.get("episode_number", 0),
                })
        except Exception as e:
            logger.debug("Failed to load podcast DB: %s", e)
    _blog_db_cache = articles
    return articles


def _load_score_db() -> dict:
    """Load pre-computed module→resource score mappings."""
    global _score_db_cache
    if _score_db_cache is not None:
        return _score_db_cache
    if not SCORE_DB_PATH.exists():
        _score_db_cache = {}
        return _score_db_cache
    try:
        _score_db_cache = json.loads(SCORE_DB_PATH.read_text("utf-8"))
    except Exception:
        _score_db_cache = {}
    return _score_db_cache


def _load_curated_resources() -> dict:
    """Load curated per-module resources from external_resources.yaml."""
    global _curated_cache
    if _curated_cache is not None:
        return _curated_cache
    if not CURATED_RESOURCES_PATH.exists():
        _curated_cache = {}
        return _curated_cache
    try:
        data = yaml.safe_load(CURATED_RESOURCES_PATH.read_text("utf-8"))
        _curated_cache = data.get("resources", {})
    except Exception as e:
        logger.debug("Failed to load curated resources: %s", e)
        _curated_cache = {}
    return _curated_cache


def search_blogs(
    module_slug: str,
    level: str,
    topic_title: str,
    keywords: list[str],
    max_results: int = 5,
) -> list[dict]:
    """Find relevant blog/podcast articles for a module.

    Three-layer approach:
    0. Curated per-module resources (external_resources.yaml) — guaranteed matches
    1. Pre-computed score DB (resource_module_scores_final.json)
    2. Keyword + topic matching against blog/podcast DBs

    Returns list of dicts with: url, title, source, relevance_score, topics.
    """
    results: list[dict] = []
    seen_urls: set[str] = set()

    # Layer 0: Curated per-module resources (highest priority)
    curated = _load_curated_resources()
    # external_resources.yaml uses "a1-01-slug" format; match by slug suffix
    matching_keys = [k for k in curated if k == module_slug or k.endswith(f"-{module_slug}")]
    for key in matching_keys:
        module_resources = curated.get(key, {})
        if not module_resources:
            continue
        for cat, score in [("articles", 1.0), ("websites", 0.95)]:
            for item in module_resources.get(cat, []):
                url = item.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append({
                        "url": url,
                        "title": item.get("title", ""),
                        "source": item.get("source", "curated"),
                        "relevance_score": score,
                        "topics": [],
                    })

    # Layer 1: Pre-computed scores
    score_db = _load_score_db()
    # Try multiple slug formats
    slug_variants = [
        f"{level.lower()}-{module_slug}",
        module_slug,
    ]
    for slug_key in slug_variants:
        if slug_key in score_db:
            for entry in score_db[slug_key]:
                url = entry.get("resource_url", "")
                if url and url not in seen_urls and entry.get("score", 0) >= 60:
                    seen_urls.add(url)
                    results.append({
                        "url": url,
                        "title": entry.get("resource_title", ""),
                        "source": "ukrainianlessons.com",
                        "relevance_score": entry.get("score", 0) / 100.0,
                        "topics": [],
                    })

    # Layer 2: Keyword matching against blog DBs
    all_articles = _load_blog_dbs()
    if not all_articles:
        return results[:max_results]

    # Build search terms (lowercased), filtering stopwords
    _stopwords = {
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
    # Separate phrase-level terms (multi-word) from single-word terms
    search_phrases: list[str] = []  # e.g. "past tense", "reflexive verbs"
    search_words: set[str] = set()  # single domain-specific words
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if not kw_lower or kw_lower in _stopwords:
            continue
        if " " in kw_lower:
            search_phrases.append(kw_lower)
        else:
            search_words.add(kw_lower)
    # Add topic title as a phrase
    search_phrases.insert(0, topic_title.lower())
    # Add individual topic words (only domain-specific ones)
    for word in topic_title.lower().split():
        if len(word) > 3 and word not in _stopwords:
            search_words.add(word)

    level_base = level.split("-")[0].upper()

    for article in all_articles:
        url = article.get("url", "")
        if url in seen_urls:
            continue

        article_topics = {t.lower() for t in article.get("topics", [])}
        article_title = article.get("title", "").lower()
        article_title_words = set(article_title.split())
        article_level = article.get("suggested_level", "").upper()
        desc = article.get("description", "").lower()
        desc_words = set(desc.split())

        # Phrase matching — much stronger signal than single words
        phrase_score = 0.0
        for phrase in search_phrases:
            if phrase in article_title or phrase in desc:
                phrase_score += 0.5
            elif any(phrase in t for t in article_topics):
                phrase_score += 0.4

        # Word-level matching
        topic_overlap = len(search_words & article_topics)
        title_overlap = len(search_words & article_title_words)
        desc_overlap = len(search_words & desc_words)
        level_match = 1 if article_level == level_base else 0

        # Gate: require a phrase match, or a topic tag match, or 2+ title/desc word matches
        if phrase_score == 0 and topic_overlap == 0 and (title_overlap + desc_overlap) < 2:
            continue

        score = phrase_score + topic_overlap * 0.25 + title_overlap * 0.1 + desc_overlap * 0.05 + level_match * 0.1

        # Podcast episodes get a priority boost — structured content
        content_type = article.get("content_type", "")
        if content_type in ("podcast_episode", "podcast_episode_short"):
            score += 0.1

        if score < 0.3:
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
        # Podcast metadata for richer discovery output
        if content_type.startswith("podcast_episode"):
            entry["content_type"] = content_type
            entry["series"] = article.get("series", "")
            entry["season"] = article.get("season", 0)
            entry["episode"] = article.get("episode", 0)
        results.append(entry)

    # Sort by relevance, cap results
    results.sort(key=lambda r: r["relevance_score"], reverse=True)
    return results[:max_results]


def format_blog_discovery(blogs: list[dict]) -> str:
    """Format blog results as markdown for {BLOG_DISCOVERY} placeholder."""
    if not blogs:
        return "(No blog articles found)"

    # Separate podcasts from blog articles for clearer presentation
    podcasts = [b for b in blogs if b.get("content_type", "").startswith("podcast_episode")]
    articles = [b for b in blogs if not b.get("content_type", "").startswith("podcast_episode")]

    lines: list[str] = []

    if podcasts:
        lines.append("### Podcast Episodes")
        lines.append("*Each episode has audio + transcript + vocabulary list — recommend to students as supplementary listening.*")
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


# ---------------------------------------------------------------------------
# RAG discovery — textbook chunks, literary sources, and images
# ---------------------------------------------------------------------------

# Seminar tracks that benefit from literary primary source search
_SEMINAR_TRACKS = {"hist", "istorio", "bio", "lit", "oes", "ruth"}

# Rough mapping: learner level → school grade range for textbook search
_LEVEL_GRADE_RANGES: dict[str, tuple[int, int]] = {
    "A1": (1, 4),
    "A2": (2, 6),
    "B1": (4, 8),
    "B2": (6, 11),
    "C1": (7, 11),
    "C2": (8, 11),
}


def _is_qdrant_available() -> bool:
    """Check if Qdrant is reachable without loading heavy models."""
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


def search_rag(
    keywords: list[str],
    track: str,
    level: str = "",
    limit_text: int = 5,
    limit_images: int = 3,
    limit_literary: int = 3,
) -> dict[str, list[dict]]:
    """Search RAG collections for relevant content.

    Returns dict with keys: text_chunks, images, literary.
    Gracefully degrades if Qdrant is unavailable.
    """
    result: dict[str, list[dict]] = {
        "text_chunks": [],
        "images": [],
        "literary": [],
    }

    if not _is_qdrant_available():
        logger.debug("RAG: Qdrant not available, skipping")
        return result

    try:
        from rag.query import search_text, search_images, search_literary
    except ImportError:
        logger.debug("RAG: rag.query not importable, skipping")
        return result

    query = cap_query(keywords)
    if not query:
        return result

    base_track = track.split("-")[0].lower()
    level_base = level.split("-")[0].upper() if level else ""

    # 1. Textbook chunks — relevant for all tracks
    try:
        grade_range = _LEVEL_GRADE_RANGES.get(level_base)
        # Search without grade filter to cast wide net, then prefer matching grades
        text_hits = search_text(query, limit=limit_text * 2)
        # Prefer chunks from appropriate grade levels
        if grade_range:
            lo, hi = grade_range
            # A1/A2 need stronger grade preference — otherwise grade 11
            # literature outscores grade 1-4 bukvar content on semantic score alone
            is_beginner = level_base in ("A1", "A2")
            scored = []
            for h in text_hits:
                g = h.get("grade", 0)
                if lo <= g <= hi:
                    grade_bonus = 0.3 if is_beginner else 0.1
                elif g > 0 and is_beginner:
                    # Penalty for out-of-range grades at beginner levels
                    distance = max(0, g - hi, lo - g)
                    grade_bonus = -0.05 * distance
                else:
                    grade_bonus = 0.0
                scored.append((h["score"] + grade_bonus, h))
            scored.sort(key=lambda x: x[0], reverse=True)
            result["text_chunks"] = [h for _, h in scored[:limit_text]]
        else:
            result["text_chunks"] = text_hits[:limit_text]
    except Exception as e:
        logger.debug("RAG text search failed: %s", e)

    # 2. Textbook images — high/medium teaching value only
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


# Channel allowlist — categorized by track relevance.
# tracks: ["*"] = all tracks, or specific track IDs.
DEFAULT_CHANNELS: list[dict[str, Any]] = [
    # Language learning (core A1-C2)
    {"name": "Ukrainian Lessons", "handle": "@UkrainianLessons", "tracks": ["*"]},
    {"name": "Anna Ohoiko", "handle": "@annaohoiko", "tracks": ["*"]},
    {"name": "Ukrainian with Olha", "handle": "@ukrainianwitholha", "tracks": ["*"]},
    {"name": "Let's Learn Ukrainian", "handle": "@LetsLearnUkrainian", "tracks": ["*"]},
    {"name": "Speak Ukrainian", "handle": "@SpeakUkrainian", "tracks": ["*"]},
    {"name": "Learn Ukrainian Language", "handle": "@LearnUkrainianLanguage", "tracks": ["*"]},
    {"name": "Learn Ukrainian with Vakulenko", "handle": "@learnukrainianwithvakulenko", "tracks": ["*"]},
    {"name": "VERBA SCHOOL", "handle": "@verbaschool", "tracks": ["*"]},
    {"name": "Red Purple Ukrainian", "handle": "@RedPurpleUkrainian", "tracks": ["*"]},
    {"name": "Ukrainian Guy", "handle": "@ukrainianguy", "tracks": ["*"]},
    {"name": "Bright Kids Ukrainian", "handle": "@BrightKidsUkrainianOnlineSchool", "tracks": ["a1", "a2"]},
    {"name": "Listen & Read", "handle": "@listen-read", "tracks": ["*"]},
    {"name": "UkrainerNet", "handle": "@ukrainernet", "tracks": ["*"]},
    # History (HIST, ISTORIO, BIO)
    {"name": "Реальна Історія", "handle": "@realhistoryua", "tracks": ["hist", "istorio", "bio"]},
    {"name": "Harvard Ukrainian Research Institute", "handle": "@ukrainianresearchinstitute1041", "tracks": ["hist", "istorio", "bio", "lit"]},
    {"name": "Комік Історик", "handle": "@komikistoryk", "tracks": ["hist", "istorio", "bio"]},
    {"name": "ІМТГШ", "handle": "@imtgsh", "tracks": ["hist", "istorio"]},
    # Historical linguistics (OES, RUTH)
    {"name": "Історія Мови", "handle": "@Istoria-Movy", "tracks": ["oes", "ruth"]},
    # Culture & documentary (B2+, LIT, cultural modules)
    {"name": "Суспільне Культура", "handle": "@SuspilneKultura", "tracks": ["lit", "b2", "c1", "c2"]},
    {"name": "Суспільне Док", "handle": "@SuspilneDoc", "tracks": ["hist", "bio", "lit", "b2", "c1"]},
    {"name": "Repainted Fox", "handle": "@repaintedfox", "tracks": ["b1", "b2", "c1"]},
    {"name": "Klopotenko", "handle": "@klopotenko", "tracks": ["a2", "b1", "b2"]},
    {"name": "Radio Khartia", "handle": "@RadioKhartia", "tracks": ["lit", "c1", "c2"]},
]


@dataclass
class VideoCandidate:
    url: str
    channel: str
    title: str
    transcript: str = ""
    relevance_score: float = 0.0
    relevance_note: str = ""
    transcript_excerpt: str = ""
    embed_suggestion: str = ""


@dataclass
class DiscoveryResult:
    discovered_at: str = ""
    query_keywords: list[str] = field(default_factory=list)
    videos: list[VideoCandidate] = field(default_factory=list)
    blogs: list[dict] = field(default_factory=list)
    rag_chunks: list[dict] = field(default_factory=list)
    rag_images: list[dict] = field(default_factory=list)
    rag_literary: list[dict] = field(default_factory=list)
    error: str | None = None
    warning: str | None = None


# ---------------------------------------------------------------------------
# SRT cleaning
# ---------------------------------------------------------------------------

def clean_srt(text: str) -> str:
    """Strip SRT metadata (timestamps, sequence numbers), dedup consecutive lines."""
    lines = text.splitlines()
    final: list[str] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r"^\d+$", line):
            continue
        if "-->" in line:
            continue
        line = re.sub(r"<[^>]+>", "", line)
        if not line:
            continue
        if not final or final[-1] != line:
            final.append(line)
    return " ".join(final)


# ---------------------------------------------------------------------------
# Transcript download
# ---------------------------------------------------------------------------

def download_transcript(url: str) -> str:
    """Download Ukrainian auto-subs via yt-dlp. Returns plain text or empty string."""
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir) / "subs"
            cmd = [
                "yt-dlp", url,
                "--write-subs", "--write-auto-subs",
                "--sub-langs", "uk",
                "--convert-subs", "srt",
                "--skip-download",
                "--output", f"{tmp_path}.%(ext)s",
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
            srt_file = None
            for f in Path(tmp_dir).glob("*.uk.srt"):
                srt_file = f
                break
            if srt_file is None or not srt_file.exists():
                return ""
            srt_text = srt_file.read_text(encoding="utf-8", errors="replace")
            text = clean_srt(srt_text)
            return text[:TRANSCRIPT_CAP] if len(text) > TRANSCRIPT_CAP else text
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.debug("Transcript download failed for %s: %s", url, e)
        return ""
    except Exception as e:
        logger.debug("Unexpected error downloading transcript for %s: %s", url, e)
        return ""


# ---------------------------------------------------------------------------
# Channel filtering & search
# ---------------------------------------------------------------------------

def filter_channels(channels: list[dict], track: str) -> list[dict]:
    """Filter channel allowlist by track relevance."""
    base_track = track.split("-")[0].lower()
    return [
        ch for ch in channels
        if "*" in ch.get("tracks", [])
        or base_track in ch.get("tracks", [])
        or track.lower() in ch.get("tracks", [])
    ]


def search_channel(keywords: list[str], channel_handle: str, max_results: int = 3) -> list[dict]:
    """Search YouTube via yt-dlp for videos matching keywords on a channel."""
    query = cap_query(keywords)
    search_term = f"ytsearch{max_results}:{query} {channel_handle}"
    try:
        result = subprocess.run(
            ["yt-dlp", search_term, "--get-id", "--get-title"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return []
        lines = [ln.strip() for ln in result.stdout.strip().splitlines() if ln.strip()]
        # yt-dlp outputs title then id alternating
        videos = []
        for i in range(0, len(lines) - 1, 2):
            videos.append({
                "url": f"https://www.youtube.com/watch?v={lines[i + 1]}",
                "title": lines[i],
            })
        return videos
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Gemini scoring
# ---------------------------------------------------------------------------

def score_candidates(
    candidates: list[VideoCandidate],
    topic: str,
    outline: list[dict],
    vocab: list[str],
    dispatch_fn: Callable[..., tuple[bool, str]],
    model: str = "gemini-2.5-flash",
) -> list[VideoCandidate]:
    """Score candidates for relevance using Gemini Flash. Modifies in-place."""
    if not candidates:
        return candidates

    sections_str = ", ".join(
        s.get("section", s.get("title", ""))
        for s in outline if s.get("section") or s.get("title")
    ) or "(no outline)"
    vocab_str = ", ".join(vocab[:20]) if vocab else "(no vocab)"

    candidate_blocks = []
    for i, c in enumerate(candidates):
        excerpt = c.transcript[:2000] if c.transcript else "(no transcript)"
        candidate_blocks.append(
            f"### Candidate {i + 1}\n"
            f"- URL: {c.url}\n"
            f"- Title: {c.title}\n"
            f"- Channel: {c.channel}\n"
            f"- Transcript excerpt:\n{excerpt}\n"
        )

    prompt = (
        "# Video Discovery: Relevance Scoring\n\n"
        "## Module Context\n"
        f"Topic: {topic}\n"
        f"Sections: {sections_str}\n"
        f"Vocabulary: {vocab_str}\n\n"
        "## Candidates\n\n"
        + "\n".join(candidate_blocks)
        + "\n## Instructions\n\n"
        "Rate each candidate's relevance to this module (0.0-1.0).\n"
        "For each, suggest where it could be embedded (after which section).\n"
        "Extract a short transcript excerpt (1-2 sentences) that's most relevant.\n\n"
        "## Output (between delimiters)\n\n"
        "===DISCOVERY_SCORES_START===\n"
        "- video_url: \"...\"\n"
        "  relevance_score: 0.0-1.0\n"
        "  relevance_note: \"...\"\n"
        "  embed_suggestion: \"After section X — reason\"\n"
        "  transcript_excerpt: \"...\"\n"
        "===DISCOVERY_SCORES_END===\n"
    )

    try:
        ok, response = dispatch_fn(
            prompt,
            task_id="video-discovery-score",
            model=model,
            stdout_only=True,
            timeout=120,
        )
        if not ok:
            logger.warning("Gemini scoring failed")
            return candidates

        match = re.search(
            r"===DISCOVERY_SCORES_START===\s*(.*?)\s*===DISCOVERY_SCORES_END===",
            response,
            re.DOTALL,
        )
        if not match:
            logger.warning("Could not parse scoring response delimiters")
            return candidates

        try:
            scores = yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            logger.warning("Could not parse YAML in scoring response")
            return candidates

        if not isinstance(scores, list):
            return candidates

        url_to_score = {
            entry.get("video_url", ""): entry
            for entry in scores if isinstance(entry, dict)
        }
        for c in candidates:
            entry = url_to_score.get(c.url, {})
            c.relevance_score = float(entry.get("relevance_score", 0.0))
            c.relevance_note = str(entry.get("relevance_note", ""))
            c.embed_suggestion = str(entry.get("embed_suggestion", ""))
            c.transcript_excerpt = str(entry.get("transcript_excerpt", ""))

    except Exception as e:
        logger.warning("Scoring failed: %s", e)

    return candidates


# ---------------------------------------------------------------------------
# Full discovery pipeline
# ---------------------------------------------------------------------------

def run_discovery(
    topic: str,
    keywords: list[str],
    outline: list[dict],
    vocab: list[str],
    dispatch_fn: Callable[..., tuple[bool, str]],
    track: str = "",
    channels: list[dict[str, Any]] | None = None,
    max_per_channel: int = 2,
) -> DiscoveryResult:
    """Search → transcript → score → rank. Non-blocking: always returns a result."""
    result = DiscoveryResult(
        discovered_at=datetime.now(timezone.utc).isoformat(),
        query_keywords=keywords,
    )

    try:
        channel_list = channels if channels is not None else DEFAULT_CHANNELS
        if track:
            channel_list = filter_channels(channel_list, track)
        if not channel_list:
            result.error = f"No channels match track '{track}'"
            return result

        all_candidates: list[VideoCandidate] = []
        seen_urls: set[str] = set()
        for ch in channel_list:
            videos = search_channel(keywords, ch["handle"], max_results=max_per_channel)
            for v in videos:
                if v["url"] not in seen_urls:
                    seen_urls.add(v["url"])
                    all_candidates.append(VideoCandidate(
                        url=v["url"],
                        channel=ch["name"],
                        title=v["title"],
                    ))

        if not all_candidates:
            result.warning = "No videos found across channels"
            return result

        # Download transcripts (cap at 8 to limit network time)
        for c in all_candidates[:8]:
            c.transcript = download_transcript(c.url)

        # Score candidates that have transcripts
        with_text = [c for c in all_candidates if c.transcript]
        if with_text:
            score_candidates(with_text, topic, outline, vocab, dispatch_fn)

        all_candidates.sort(key=lambda c: c.relevance_score, reverse=True)
        result.videos = all_candidates

    except Exception as e:
        result.error = str(e)
        logger.warning("Discovery failed: %s", e)

    return result


# ---------------------------------------------------------------------------
# YAML serialization
# ---------------------------------------------------------------------------

def write_discovery_yaml(result: DiscoveryResult, path: Path) -> None:
    """Serialize DiscoveryResult to YAML."""
    data: dict[str, Any] = {
        "discovered_at": result.discovered_at,
        "query_keywords": result.query_keywords,
        "error": result.error,
        "warning": result.warning,
        "videos": [
            {
                "url": v.url,
                "channel": v.channel,
                "title": v.title,
                "relevance_score": v.relevance_score,
                "relevance_note": v.relevance_note,
                "transcript_excerpt": v.transcript_excerpt,
                "embed_suggestion": v.embed_suggestion,
            }
            for v in result.videos
        ],
        "blogs": result.blogs,
        "rag_chunks": result.rag_chunks,
        "rag_images": result.rag_images,
        "rag_literary": result.rag_literary,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def read_discovery_yaml(path: Path) -> DiscoveryResult:
    """Deserialize DiscoveryResult from YAML."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data:
        return DiscoveryResult()
    result = DiscoveryResult(
        discovered_at=data.get("discovered_at", ""),
        query_keywords=data.get("query_keywords", []),
        error=data.get("error"),
        blogs=data.get("blogs", []),
        rag_chunks=data.get("rag_chunks", []),
        rag_images=data.get("rag_images", []),
        rag_literary=data.get("rag_literary", []),
    )
    for v in data.get("videos", []):
        result.videos.append(VideoCandidate(
            url=v.get("url", ""),
            channel=v.get("channel", ""),
            title=v.get("title", ""),
            relevance_score=float(v.get("relevance_score", 0.0)),
            relevance_note=v.get("relevance_note", ""),
            transcript_excerpt=v.get("transcript_excerpt", ""),
            embed_suggestion=v.get("embed_suggestion", ""),
        ))
    return result


# ---------------------------------------------------------------------------
# Template formatting
# ---------------------------------------------------------------------------

def format_discovery_for_template(result: DiscoveryResult) -> str:
    """Format as markdown for {VIDEO_DISCOVERY} placeholder."""
    sections: list[str] = []

    # Videos
    relevant = [v for v in result.videos if v.relevance_score >= 0.5]
    if relevant:
        lines: list[str] = ["### Videos"]
        for v in relevant:
            lines.append(f"- **{v.title}** ({v.channel})")
            lines.append(f"  URL: {v.url}")
            lines.append(f"  Score: {v.relevance_score:.1f} — {v.relevance_note}")
            if v.embed_suggestion:
                lines.append(f"  Suggested placement: {v.embed_suggestion}")
            if v.transcript_excerpt:
                lines.append(f"  Key excerpt: {v.transcript_excerpt}")
            lines.append("")
        sections.append("\n".join(lines))

    # Blogs
    if result.blogs:
        sections.append(format_blog_discovery(result.blogs))

    # RAG content
    if result.rag_chunks or result.rag_images or result.rag_literary:
        rag_text = format_rag_discovery(
            result.rag_chunks, result.rag_images, result.rag_literary,
        )
        if "(No RAG content found)" not in rag_text:
            sections.append(rag_text)

    if not sections:
        if result.error:
            return "(No discoveries available)"
        return "(No relevant resources found)"

    return "\n\n".join(sections)
