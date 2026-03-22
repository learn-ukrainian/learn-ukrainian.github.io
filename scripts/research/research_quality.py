"""
Research quality assessment engine with pluggable rubrics.

Rubrics are defined per-track. Tracks without a rubric get coverage-only reporting.
New rubrics are added to RUBRIC_REGISTRY when a track completes research coverage.

Extensibility:
  1. Read 3-5 research files for the new track to identify section structure
  2. Define dimensions + scoring in RUBRIC_REGISTRY
  3. Add track ID to the rubric's "tracks" set
  4. CLI + dashboard automatically apply the new rubric — no other changes needed
"""

import re
from pathlib import Path

# ==================== RUBRIC REGISTRY ====================

RUBRIC_REGISTRY = {
    "core": {
        "tracks": {"a1", "a2", "b1", "b2", "c1", "c2"},
        "max_score": 17,
        "dimensions": ["state_standard", "vocabulary", "cultural_hooks",
                        "learner_errors", "cross_references", "pedagogy_notes",
                        "source_verification", "claim_grounding",
                        "discovery_integration", "specificity"],
    },
    "history": {
        "tracks": {"hist", "bio", "istorio", "oes", "ruth",
                    "lit", "lit-essay", "lit-fantastika", "lit-hist-fic",
                    "lit-humor", "lit-youth", "lit-war",
                    "lit-drama", "folk"},
        "max_score": 17,
        "dimensions": ["sources", "chronology", "primary_quotes",
                        "engagement_hooks", "decolonization", "section_notes",
                        "source_verification", "claim_grounding",
                        "discovery_integration", "specificity"],
    },
    "professional": {
        "tracks": {"b2-pro", "c1-pro"},
        "max_score": 17,
        "dimensions": ["sources", "terminology", "language_norms",
                        "authentic_examples", "engagement_hooks", "section_notes",
                        "source_verification", "claim_grounding",
                        "discovery_integration", "specificity"],
    },
}

# Short labels for CLI column headers
DIMENSION_SHORT_LABELS = {
    # Core
    "state_standard": "Std",
    "vocabulary": "Voc",
    "cultural_hooks": "Cul",
    "learner_errors": "Err",
    "cross_references": "Xrf",
    "pedagogy_notes": "Not",
    # History
    "sources": "Src",
    "chronology": "Chr",
    "primary_quotes": "Qot",
    "engagement_hooks": "Hok",
    "decolonization": "Dec",
    "section_notes": "Not",
    # Professional
    "terminology": "Trm",
    "language_norms": "Nrm",
    "authentic_examples": "Aut",
    # Substance (shared across rubrics)
    "source_verification": "Src✓",
    "claim_grounding": "Clm",
    "discovery_integration": "Dis",
    "specificity": "Spc",
}


# ==================== HELPERS ====================


import contextlib

from research.research_markdown_utils import (
    count_blockquotes as _count_blockquotes,
)
from research.research_markdown_utils import (
    count_dated_entries as _count_dated_entries,
)
from research.research_markdown_utils import (
    count_guillemet_quotes as _count_guillemet_quotes,
)
from research.research_markdown_utils import (
    count_h3_subsections as _count_h3_subsections,
)
from research.research_markdown_utils import (
    count_numbered_items as _count_numbered_items,
)
from research.research_markdown_utils import (
    count_urls as _count_urls,
)
from research.research_markdown_utils import (
    extract_section as _extract_section,
)

# ==================== SUBSTANCE SCORING ====================

# Substance thresholds by tier.
# Tier is derived from track: beginner (A1/A2), core (B1/B2/C1/C2), advanced (history/professional).
# A1 research naturally has fewer sources and simpler examples — calibrate accordingly.
SUBSTANCE_TIERS = {
    "beginner": {
        "source_domains_full": 1,   # 1 known-good domain → 2/2
        "source_domains_partial": 1, # same (any known domain → full score)
        "examples_full": 5,          # 5 cited examples → 2/2
        "examples_partial": 3,       # 3 → 1/2
        "specifics_full": 5,         # 5 specific markers → 2/2
        "specifics_partial": 2,      # 2 → 1/2
    },
    "core": {
        "source_domains_full": 2,
        "source_domains_partial": 1,
        "examples_full": 10,
        "examples_partial": 5,
        "specifics_full": 10,
        "specifics_partial": 5,
    },
    "advanced": {
        "source_domains_full": 3,
        "source_domains_partial": 1,
        "examples_full": 15,
        "examples_partial": 5,
        "specifics_full": 15,
        "specifics_partial": 5,
    },
}

_TRACK_TO_TIER = {
    "a1": "beginner", "a2": "beginner",
    "b1": "core", "b2": "core", "c1": "core", "c2": "core",
    # History/professional → advanced
}


def _get_substance_tier(track_id: str) -> str:
    """Map track ID to substance scoring tier."""
    return _TRACK_TO_TIER.get(track_id, "advanced")


# Known good domains for Ukrainian language resources
KNOWN_GOOD_DOMAINS = {
    # Official / institutional
    "mon.gov.ua", "zakon.rada.gov.ua",
    "nbuv.gov.ua", "irbis-nbuv.gov.ua",
    # Academic / encyclopedic
    "uk.wikipedia.org", "uk.wikisource.org", "uk.wiktionary.org",
    "litopys.org.ua", "izbornyk.org.ua",
    # Language resources
    "sum.in.ua", "goroh.pp.ua", "r2u.org.ua", "lcorp.ulif.org.ua",
    "pravopys.net", "slovnyk.ua", "ukrlit.org",
    # Educational
    "ukrainianlessons.com", "osvita.ua", "zno.osvita.ua",
    # Cultural
    "namu.kiev.ua", "museum.if.ua",
    # Scholarly
    "doi.org", "jstor.org", "scholar.google.com",
}


def _extract_domains(text: str) -> list[str]:
    """Extract unique domains from URLs in text."""
    urls = re.findall(r"https?://([^\s/\)>]+)", text)
    domains = set()
    for raw in urls:
        # Strip port and trailing punctuation
        domain = raw.split(":")[0].rstrip(".,;")
        # Get base domain (last 2 or 3 parts)
        parts = domain.split(".")
        if len(parts) >= 2:
            domains.add(".".join(parts[-2:]) if len(parts[-1]) > 2 else ".".join(parts[-3:]))
    return list(domains)


def _extract_ukrainian_words(text: str) -> list[str]:
    """Extract Ukrainian words (Cyrillic) from text, deduped."""
    # Match words of 3+ Cyrillic chars (skip short prepositions etc)
    words = re.findall(r"\b[а-яіїєґА-ЯІЇЄҐ][а-яіїєґ'ʼ]{2,}\b", text)
    return list(set(w.lower() for w in words))


def _parse_discovery(discovery_path: "Path | None") -> dict:
    """Parse discovery.yaml once, returning normalised data.

    Returns a dict with keys: blogs, videos, rag_chunks, rag_literary (each a list).
    Returns empty lists on missing/invalid file.
    """
    empty = {"blogs": [], "videos": [], "rag_chunks": [], "rag_literary": []}
    if discovery_path is None or not discovery_path.exists():
        return empty
    try:
        import yaml
        data = yaml.safe_load(discovery_path.read_text("utf-8"))
    except Exception:
        return empty
    if not isinstance(data, dict):
        return empty
    return {
        "blogs": data.get("blogs") or [],
        "videos": data.get("videos") or [],
        "rag_chunks": data.get("rag_chunks") or [],
        "rag_literary": data.get("rag_literary") or [],
    }


def _score_source_verification(text: str, tier: str = "advanced",
                               discovery: dict | None = None) -> dict:
    """Score source quality: known-good domains, URL count, RAG textbook chunks.

    Sources are counted from both the research markdown AND discovery data.
    RAG textbook chunks count as verified sources (they come from real
    Ukrainian school textbooks via the VESUM-backed RAG pipeline).
    """
    thresholds = SUBSTANCE_TIERS[tier]
    urls = set(re.findall(r"https?://[^\s\)>]+", text))
    domains = _extract_domains(text)
    known = [d for d in domains if any(d.endswith(k) or k.endswith(d) for k in KNOWN_GOOD_DOMAINS)]

    # Also count sources from discovery (blogs, videos, RAG chunks)
    rag_chunk_count = 0
    if discovery:
        # Collect discovery URLs
        discovery_urls: set[str] = set()
        for item in discovery["blogs"]:
            url = item.get("url", "") if isinstance(item, dict) else ""
            if url:
                discovery_urls.add(url)
        for item in discovery["videos"]:
            url = item.get("url", "") if isinstance(item, dict) else ""
            if url:
                discovery_urls.add(url)
        urls.update(discovery_urls)
        # Extract domains only from new discovery URLs
        for d in _extract_domains(" ".join(discovery_urls)):
            if d not in domains:
                domains.append(d)
                if any(d.endswith(k) or k.endswith(d) for k in KNOWN_GOOD_DOMAINS):
                    known.append(d)
        rag_chunk_count = len(discovery["rag_chunks"])

    total_sources = len(urls) + rag_chunk_count
    source_parts = []
    if urls:
        source_parts.append(f"{len(urls)} URLs")
    if rag_chunk_count:
        source_parts.append(f"{rag_chunk_count} RAG chunks")
    source_detail = ", ".join(source_parts) if source_parts else "no sources"

    if total_sources == 0:
        return {"score": 0, "max": 2, "detail": "no sources found"}
    # RAG chunks count as known-good sources (verified textbook content).
    # Multiple RAG chunks from different grades/subjects count as distinct sources
    # (capped at 2 to avoid inflating the score from a single search).
    rag_source_credit = min(rag_chunk_count, 2) if rag_chunk_count > 0 else 0
    known_count = len(known) + rag_source_credit
    if known_count >= thresholds["source_domains_full"]:
        return {"score": 2, "max": 2, "detail": f"{known_count} known-good sources, {source_detail}"}
    if known_count >= thresholds["source_domains_partial"]:
        return {"score": 1, "max": 2, "detail": f"{known_count} known-good source(s), {source_detail}"}
    return {"score": 0, "max": 2, "detail": f"{source_detail} but 0 known-good sources"}


def _score_claim_grounding(text: str, tier: str = "advanced") -> dict:
    """Score claim grounding: concrete Ukrainian examples in the research.

    Counts Ukrainian words that appear in structured contexts: quoted, bold,
    italic, table cells, or bullet-list items. These indicate the research
    contains real linguistic examples rather than vague generalizations.
    """
    thresholds = SUBSTANCE_TIERS[tier]
    uk_words = _extract_ukrainian_words(text)
    total_words = len(text.split())
    if total_words == 0:
        return {"score": 0, "max": 2, "detail": "empty text"}

    cited = set()
    # Words in quotes, bold, or italic delimiters
    cited.update(re.findall(r"[«\"*_]([а-яіїєґА-ЯІЇЄҐ][а-яіїєґ'ʼ]+)[»\"*_]", text))
    # Ukrainian words in markdown table cells (| word |)
    cited.update(re.findall(r"\|\s*([а-яіїєґА-ЯІЇЄҐ][а-яіїєґ'ʼ]{2,})", text))
    # Ukrainian words after bullet points (- word or * word)
    cited.update(re.findall(r"^[-*]\s+([а-яіїєґА-ЯІЇЄҐ][а-яіїєґ'ʼ]{2,})", text, re.MULTILINE))
    example_count = len(cited)

    if example_count >= thresholds["examples_full"]:
        return {"score": 2, "max": 2, "detail": f"{example_count} cited examples, {len(uk_words)} Ukrainian terms"}
    if example_count >= thresholds["examples_partial"]:
        return {"score": 1, "max": 2, "detail": f"{example_count} cited examples, {len(uk_words)} Ukrainian terms"}
    return {"score": 0, "max": 2, "detail": f"{example_count} cited examples (need {thresholds['examples_partial']}+)"}


def _score_discovery_integration(discovery: dict | None) -> dict:
    """Score discover phase integration: external resources found.

    Counts all discovery resource types: videos, blogs, RAG chunks, and
    literary sources. A module with RAG textbook hits is still well-researched
    even without YouTube videos.
    """
    if not discovery:
        return {"score": 0, "max": 1, "detail": "no discovery file"}

    videos = discovery["videos"]
    blogs = discovery["blogs"]
    rag_chunks = discovery["rag_chunks"]
    rag_literary = discovery["rag_literary"]
    total = len(videos) + len(blogs) + len(rag_chunks) + len(rag_literary)

    parts = []
    if videos:
        parts.append(f"{len(videos)} videos")
    if blogs:
        parts.append(f"{len(blogs)} blogs")
    if rag_chunks:
        parts.append(f"{len(rag_chunks)} RAG")
    if rag_literary:
        parts.append(f"{len(rag_literary)} literary")
    detail = ", ".join(parts) if parts else "0 resources"

    if total >= 1:
        return {"score": 1, "max": 1, "detail": detail}
    return {"score": 0, "max": 1, "detail": detail}


def _score_specificity(text: str, tier: str = "advanced") -> dict:
    """Score specificity: are claims concrete (dates, names, numbers) vs vague generalizations?"""
    thresholds = SUBSTANCE_TIERS[tier]
    # Count specific markers
    dates = len(re.findall(r"\b\d{4}\b", text))
    section_refs = len(re.findall(r"§\d+|розділ\s+\d+|частина\s+\d+", text, re.IGNORECASE))
    page_refs = len(re.findall(r"\bс\.\s*\d+|\bp\.\s*\d+|стор\.\s*\d+", text))
    table_rows = len(re.findall(r"^\|.+\|$", text, re.MULTILINE))

    specifics = dates + section_refs + page_refs + table_rows

    if specifics >= thresholds["specifics_full"]:
        return {"score": 2, "max": 2, "detail": f"{dates} dates, {section_refs} §refs, {page_refs} pages, {table_rows} table rows"}
    if specifics >= thresholds["specifics_partial"]:
        return {"score": 1, "max": 2, "detail": f"{specifics} specific markers (need {thresholds['specifics_full']}+)"}
    return {"score": 0, "max": 2, "detail": f"{specifics} specific markers (need {thresholds['specifics_partial']}+)"}


def _count_table_rows(text: str) -> int:
    """Count Markdown table data rows (exclude header and separator)."""
    count = 0
    header_seen = False
    for line in text.strip().splitlines():
        stripped = line.strip()
        if "|" in stripped:
            if not header_seen:
                header_seen = True
                continue
            if re.match(r"^\|[\s\-:|]+\|$", stripped):
                continue
            count += 1
    return count


def _count_hooks(text: str) -> int:
    """Count [!type] callout tags."""
    return len(re.findall(r"\[![a-z_-]+\]", text, re.IGNORECASE))


# ==================== RUBRIC LOOKUP ====================


def get_rubric(track_id: str) -> str | None:
    """Return rubric name for a track, or None if no rubric defined."""
    for rubric_name, rubric in RUBRIC_REGISTRY.items():
        if track_id in rubric["tracks"]:
            return rubric_name
    return None


def get_dimensions(rubric_name: str) -> list[str]:
    """Return ordered dimension names for a rubric."""
    rubric = RUBRIC_REGISTRY.get(rubric_name)
    return rubric["dimensions"] if rubric else []


# ==================== CORE RUBRIC SCORING ====================


def _is_v6_knowledge_packet(text: str) -> bool:
    """Detect if text is a V6 knowledge packet (vs V5 research file)."""
    return bool(re.search(r"^## .*\n\n> \*\*Source:\*\*", text, re.MULTILINE))


def _score_v6_knowledge_packet(text: str) -> dict:
    """Score a V6 knowledge packet based on its actual structure.

    V6 packets have: ## Section blocks with textbook excerpts.
    Scoring dimensions adapted from core rubric but checking V6 markers.
    """
    dims = {}

    # Count section blocks (## headings)
    sections = re.findall(r"^## .+", text, re.MULTILINE)
    section_count = len(sections)

    # Count textbook sources (> **Source:** citations)
    sources = re.findall(r"> \*\*Source:\*\*", text)
    source_count = len(sources)

    # Count unique authors
    authors = set(re.findall(r"> \*\*Source:\*\*\s*(.+?)(?:,|Grade)", text))
    author_count = len(authors)

    # Word count
    words = len(text.split())

    # state_standard → section coverage (max 2)
    if section_count >= 5:
        dims["state_standard"] = {"score": 2, "max": 2, "detail": f"{section_count} sections covered"}
    elif section_count >= 3:
        dims["state_standard"] = {"score": 1, "max": 2, "detail": f"{section_count} sections (need 5+)"}
    else:
        dims["state_standard"] = {"score": 0, "max": 2, "detail": f"only {section_count} sections"}

    # vocabulary → textbook excerpts richness (max 2)
    if source_count >= 20:
        dims["vocabulary"] = {"score": 2, "max": 2, "detail": f"{source_count} textbook excerpts"}
    elif source_count >= 10:
        dims["vocabulary"] = {"score": 1, "max": 2, "detail": f"{source_count} excerpts (need 20+)"}
    else:
        dims["vocabulary"] = {"score": 0, "max": 2, "detail": f"only {source_count} excerpts"}

    # cultural_hooks → embedded in excerpts (max 2)
    hooks = len(re.findall(r"(?i)(культур|традиц|звича|свят|народн)", text))
    if hooks >= 3:
        dims["cultural_hooks"] = {"score": 2, "max": 2, "detail": f"{hooks} cultural references"}
    elif hooks >= 1:
        dims["cultural_hooks"] = {"score": 1, "max": 2, "detail": f"{hooks} cultural reference(s)"}
    else:
        dims["cultural_hooks"] = {"score": 0, "max": 2, "detail": "no cultural references found"}

    # learner_errors → not in V6 packets, give full score (max 2)
    dims["learner_errors"] = {"score": 2, "max": 2, "detail": "N/A for V6 packets"}

    # cross_references → author diversity (max 1)
    if author_count >= 3:
        dims["cross_references"] = {"score": 1, "max": 1, "detail": f"{author_count} authors"}
    else:
        dims["cross_references"] = {"score": 0, "max": 1, "detail": f"only {author_count} author(s)"}

    # pedagogy_notes → textbook methodology in excerpts (max 1)
    pedagogy = len(re.findall(r"(?i)(вправ|завдання|робота|метод|підручник)", text))
    dims["pedagogy_notes"] = {"score": 1 if pedagogy >= 2 else 0, "max": 1,
                              "detail": f"{pedagogy} pedagogy references"}

    # source_verification → all sources are textbook citations (max 2)
    if source_count >= 10 and author_count >= 2:
        dims["source_verification"] = {"score": 2, "max": 2, "detail": f"{source_count} cited sources"}
    elif source_count >= 5:
        dims["source_verification"] = {"score": 1, "max": 2, "detail": f"{source_count} sources"}
    else:
        dims["source_verification"] = {"score": 0, "max": 2, "detail": f"only {source_count} sources"}

    # claim_grounding → Ukrainian terms in text (max 2)
    uk_terms = len(re.findall(r"[а-яіїєґ]{3,}", text))
    if uk_terms >= 500:
        dims["claim_grounding"] = {"score": 2, "max": 2, "detail": f"{uk_terms} Ukrainian terms"}
    elif uk_terms >= 100:
        dims["claim_grounding"] = {"score": 1, "max": 2, "detail": f"{uk_terms} terms"}
    else:
        dims["claim_grounding"] = {"score": 0, "max": 2, "detail": f"only {uk_terms} terms"}

    # discovery_integration → N/A for V6 (max 1)
    dims["discovery_integration"] = {"score": 1, "max": 1, "detail": "N/A for V6"}

    # specificity → word count richness (max 2)
    if words >= 3000:
        dims["specificity"] = {"score": 2, "max": 2, "detail": f"{words} words"}
    elif words >= 1500:
        dims["specificity"] = {"score": 1, "max": 2, "detail": f"{words} words (need 3000+)"}
    else:
        dims["specificity"] = {"score": 0, "max": 2, "detail": f"only {words} words"}

    return dims


def _score_core(text: str) -> dict:
    """Score a research file using the core rubric (A1, A2).

    Auto-detects V6 knowledge packets and uses adapted scoring.
    """
    # V6 knowledge packets have different structure — use adapted scoring
    if _is_v6_knowledge_packet(text):
        return _score_v6_knowledge_packet(text)

    dims = {}

    # V5 scoring below — looks for specific section headings
    # state_standard (max 2)
    section = _extract_section(text, [r"##\s*State Standard Reference"])
    if section is None:
        dims["state_standard"] = {"score": 0, "max": 2, "detail": "missing"}
    elif re.search(r"\u00a7\d+", section) and re.search(r"(?i)alignment", section):
        dims["state_standard"] = {"score": 2, "max": 2, "detail": "\u00a7codes + alignment"}
    else:
        dims["state_standard"] = {"score": 1, "max": 2, "detail": "exists, incomplete"}

    # vocabulary (max 2)
    section = _extract_section(text, [r"##\s*Vocabulary Frequency"])
    if section is None:
        dims["vocabulary"] = {"score": 0, "max": 2, "detail": "missing"}
    else:
        rows = _count_table_rows(section)
        if rows >= 3:
            dims["vocabulary"] = {"score": 2, "max": 2, "detail": f"{rows} table rows"}
        else:
            dims["vocabulary"] = {"score": 1, "max": 2, "detail": f"{rows} rows (need 3+)"}

    # cultural_hooks (max 2)
    section = _extract_section(text, [r"##\s*Cultural Hooks"])
    if section is None:
        dims["cultural_hooks"] = {"score": 0, "max": 2, "detail": "missing"}
    else:
        hooks = _count_numbered_items(section)
        if hooks >= 2:
            dims["cultural_hooks"] = {"score": 2, "max": 2, "detail": f"{hooks} hooks"}
        elif hooks >= 1:
            dims["cultural_hooks"] = {"score": 1, "max": 2, "detail": f"{hooks} hook"}
        else:
            dims["cultural_hooks"] = {"score": 1, "max": 2, "detail": "section exists, no numbered hooks"}

    # learner_errors (max 2)
    section = _extract_section(text, [r"##\s*Common Learner Errors"])
    if section is None:
        dims["learner_errors"] = {"score": 0, "max": 2, "detail": "missing"}
    else:
        errors = _count_numbered_items(section)
        if errors >= 3:
            dims["learner_errors"] = {"score": 2, "max": 2, "detail": f"{errors} errors"}
        elif errors >= 1:
            dims["learner_errors"] = {"score": 1, "max": 2, "detail": f"{errors} errors (need 3+)"}
        else:
            dims["learner_errors"] = {"score": 1, "max": 2, "detail": "section exists, no numbered errors"}

    # cross_references (max 1)
    section = _extract_section(text, [r"##\s*Cross-References"])
    if section is None:
        dims["cross_references"] = {"score": 0, "max": 1, "detail": "missing"}
    else:
        has_upstream = bool(re.search(r"(?i)(builds?\s+on|upstream|prerequisite)", section))
        has_downstream = bool(re.search(r"(?i)(prepares?\s+for|downstream|leads?\s+to)", section))
        if has_upstream and has_downstream:
            dims["cross_references"] = {"score": 1, "max": 1, "detail": "upstream + downstream"}
        else:
            dims["cross_references"] = {"score": 1, "max": 1, "detail": "present"}

    # pedagogy_notes (max 1)
    section = _extract_section(text, [r"##\s*Notes for Content Writing"])
    if section is None:
        dims["pedagogy_notes"] = {"score": 0, "max": 1, "detail": "missing"}
    else:
        dims["pedagogy_notes"] = {"score": 1, "max": 1, "detail": "present"}

    return dims


# ==================== HISTORY RUBRIC SCORING ====================


def _score_history(text: str) -> dict:
    """Score a research file using the history rubric (HIST)."""
    dims = {}

    # sources (max 3)
    section = _extract_section(text, [r"##\s*\u0412\u0438\u043a\u043e\u0440\u0438\u0441\u0442\u0430\u043d\u0456 \u0434\u0436\u0435\u0440\u0435\u043b\u0430"])
    if section is None:
        dims["sources"] = {"score": 0, "max": 3, "detail": "missing"}
    else:
        urls = _count_urls(section)
        items = _count_numbered_items(section)
        count = max(urls, items)
        if count >= 4:
            dims["sources"] = {"score": 3, "max": 3, "detail": f"{count} sources"}
        elif count >= 3:
            dims["sources"] = {"score": 2, "max": 3, "detail": f"{count} sources"}
        elif count >= 1:
            dims["sources"] = {"score": 1, "max": 3, "detail": f"{count} sources"}
        else:
            dims["sources"] = {"score": 1, "max": 3, "detail": "section exists, few items"}

    # chronology (max 2)
    section = _extract_section(text, [r"##\s*\u0425\u0440\u043e\u043d\u043e\u043b\u043e\u0433\u0456\u044f"])
    if section is None:
        dims["chronology"] = {"score": 0, "max": 2, "detail": "missing"}
    else:
        entries = _count_dated_entries(section)
        if entries == 0:
            entries = len(re.findall(r"\b\d{3,4}\b", section))
        if entries >= 2:
            dims["chronology"] = {"score": 2, "max": 2, "detail": f"{entries} dated entries"}
        elif entries >= 1:
            dims["chronology"] = {"score": 1, "max": 2, "detail": f"{entries} dated entries"}
        else:
            dims["chronology"] = {"score": 1, "max": 2, "detail": "section exists, no dates"}

    # primary_quotes (max 2) — blockquotes + guillemet quotes across entire text
    bq = _count_blockquotes(text)
    gq = _count_guillemet_quotes(text)
    total_quotes = bq + gq
    if total_quotes >= 3:
        dims["primary_quotes"] = {"score": 2, "max": 2, "detail": f"{total_quotes} quotes ({bq}>, {gq}\u00ab\u00bb)"}
    elif total_quotes >= 1:
        dims["primary_quotes"] = {"score": 1, "max": 2, "detail": f"{total_quotes} quotes"}
    else:
        dims["primary_quotes"] = {"score": 0, "max": 2, "detail": "no quotes found"}

    # engagement_hooks (max 1)
    section = _extract_section(text, [r"##\s*Engagement Hooks"])
    if section is None:
        dims["engagement_hooks"] = {"score": 0, "max": 1, "detail": "missing"}
    else:
        hooks = _count_hooks(section)
        if hooks >= 3:
            dims["engagement_hooks"] = {"score": 1, "max": 1, "detail": f"{hooks} [!type] hooks"}
        else:
            dims["engagement_hooks"] = {"score": 0, "max": 1, "detail": f"{hooks} hooks (need 3+)"}

    # decolonization (max 1)
    section = _extract_section(text, [
        r"##\s*\u0414\u0435\u043a\u043e\u043b\u043e\u043d\u0456\u0437\u0430\u0446\u0456\u0439\u043d\u0438\u0439",
        r"##\s*Decoloni[sz]ation",
    ])
    if section is None:
        dims["decolonization"] = {"score": 0, "max": 1, "detail": "missing"}
    else:
        wc = len(section.split())
        if wc >= 30:
            dims["decolonization"] = {"score": 1, "max": 1, "detail": f"{wc} words"}
        else:
            dims["decolonization"] = {"score": 0, "max": 1, "detail": f"{wc} words (need 30+)"}

    # section_notes (max 1)
    section = _extract_section(text, [r"##\s*Section-Mapped Research Notes"])
    if section is None:
        dims["section_notes"] = {"score": 0, "max": 1, "detail": "missing"}
    else:
        subsections = _count_h3_subsections(section)
        if subsections >= 3:
            dims["section_notes"] = {"score": 1, "max": 1, "detail": f"{subsections} H3 subsections"}
        else:
            dims["section_notes"] = {"score": 0, "max": 1, "detail": f"{subsections} subsections (need 3+)"}

    return dims


# ==================== PROFESSIONAL RUBRIC SCORING ====================


def _score_professional(text: str) -> dict:
    """Score a research file using the professional rubric (B2-PRO, C1-PRO)."""
    dims = {}

    # sources (max 2): Ukrainian professional/official sources
    section = _extract_section(text, [r"##\s*Використані джерела"])
    if section is None:
        dims["sources"] = {"score": 0, "max": 2, "detail": "missing"}
    else:
        urls = _count_urls(section)
        items = _count_numbered_items(section)
        count = max(urls, items)
        if count >= 3:
            dims["sources"] = {"score": 2, "max": 2, "detail": f"{count} sources"}
        elif count >= 1:
            dims["sources"] = {"score": 1, "max": 2, "detail": f"{count} sources (need 3+)"}
        else:
            dims["sources"] = {"score": 1, "max": 2, "detail": "section exists, few items"}

    # terminology (max 3): Ukrainian professional term inventory
    section = _extract_section(text, [r"##\s*Термінологічна база", r"##\s*Terminology"])
    if section is None:
        dims["terminology"] = {"score": 0, "max": 3, "detail": "missing"}
    else:
        rows = _count_table_rows(section)
        if rows >= 8:
            dims["terminology"] = {"score": 3, "max": 3, "detail": f"{rows} terms"}
        elif rows >= 5:
            dims["terminology"] = {"score": 2, "max": 3, "detail": f"{rows} terms (need 8+)"}
        elif rows >= 2:
            dims["terminology"] = {"score": 1, "max": 3, "detail": f"{rows} terms (need 5+)"}
        else:
            dims["terminology"] = {"score": 1, "max": 3, "detail": "section exists, few terms"}

    # language_norms (max 2): ДСТУ/official language standards + common errors
    section_norms = _extract_section(text, [r"##\s*Мовні норми", r"##\s*Language Norms"])
    section_errors = _extract_section(text, [r"##\s*Типові помилки", r"##\s*Common Errors"])
    has_norms = section_norms is not None and len(section_norms.split()) >= 20
    errors_count = _count_numbered_items(section_errors or "") if section_errors else 0
    if has_norms and errors_count >= 3:
        dims["language_norms"] = {"score": 2, "max": 2, "detail": f"norms + {errors_count} errors"}
    elif has_norms or errors_count >= 3:
        dims["language_norms"] = {"score": 1, "max": 2, "detail": "partial (norms or errors, not both)"}
    else:
        dims["language_norms"] = {"score": 0, "max": 2, "detail": "missing norms + errors"}

    # authentic_examples (max 1): real Ukrainian professional text fragments
    section = _extract_section(text, [r"##\s*Аутентичні приклади", r"##\s*Authentic Examples"])
    if section is None:
        dims["authentic_examples"] = {"score": 0, "max": 1, "detail": "missing"}
    else:
        items = _count_numbered_items(section)
        gq = _count_guillemet_quotes(section)
        count = max(items, gq)
        if count >= 3:
            dims["authentic_examples"] = {"score": 1, "max": 1, "detail": f"{count} examples"}
        else:
            dims["authentic_examples"] = {"score": 0, "max": 1, "detail": f"{count} examples (need 3+)"}

    # engagement_hooks (max 1)
    section = _extract_section(text, [r"##\s*Engagement Hooks"])
    if section is None:
        dims["engagement_hooks"] = {"score": 0, "max": 1, "detail": "missing"}
    else:
        hooks = _count_hooks(section)
        if hooks >= 3:
            dims["engagement_hooks"] = {"score": 1, "max": 1, "detail": f"{hooks} [!type] hooks"}
        else:
            dims["engagement_hooks"] = {"score": 0, "max": 1, "detail": f"{hooks} hooks (need 3+)"}

    # section_notes (max 1)
    section = _extract_section(text, [r"##\s*Section-Mapped Research Notes"])
    if section is None:
        dims["section_notes"] = {"score": 0, "max": 1, "detail": "missing"}
    else:
        subsections = _count_h3_subsections(section)
        if subsections >= 3:
            dims["section_notes"] = {"score": 1, "max": 1, "detail": f"{subsections} H3 subsections"}
        else:
            dims["section_notes"] = {"score": 0, "max": 1, "detail": f"{subsections} subsections (need 3+)"}

    return dims


# ==================== CONTENT ALIGNMENT ====================


def _check_content_alignment_history(dims: dict, content_text: str) -> dict:
    """Check if content uses what the research provides (history rubric)."""
    reasons = []

    hooks_dim = dims.get("engagement_hooks", {})
    if hooks_dim.get("score", 0) >= 1:
        content_hooks = len(re.findall(r"\[![a-z_-]+\]", content_text, re.IGNORECASE))
        if content_hooks == 0:
            reasons.append("Research has engagement hooks but content has 0 [!type] callouts")

    decol_dim = dims.get("decolonization", {})
    if decol_dim.get("score", 0) >= 1:
        has_decol = bool(re.search(
            r"(?i)##.*(\u0434\u0435\u043a\u043e\u043b\u043e\u043d\u0456\u0437|decoloni)", content_text
        ))
        if not has_decol:
            reasons.append("Research has decolonization section but content lacks it")

    quotes_dim = dims.get("primary_quotes", {})
    if quotes_dim.get("score", 0) >= 2:
        content_bq = _count_blockquotes(content_text)
        content_gq = _count_guillemet_quotes(content_text)
        if content_bq + content_gq < 2:
            reasons.append(f"Research has 3+ quotes but content has {content_bq + content_gq}")

    sources_dim = dims.get("sources", {})
    if sources_dim.get("score", 0) >= 3 and _count_urls(content_text) == 0:
        reasons.append("Research has 5+ sources but content cites 0")

    return {
        "content_exists": True,
        "refresh_recommended": len(reasons) > 0,
        "reasons": reasons,
    }


def _check_content_alignment_core(dims: dict, content_text: str) -> dict:
    """Check if content uses what the research provides (core rubric)."""
    reasons = []

    hooks_dim = dims.get("cultural_hooks", {})
    if hooks_dim.get("score", 0) >= 2:
        has_cultural = bool(re.search(
            r"(?i)(##.*cultur|##.*\u043a\u0443\u043b\u044c\u0442\u0443\u0440|\[!culture\]|\[!context\])", content_text
        ))
        if not has_cultural:
            reasons.append("Research has 2+ cultural hooks but content has no cultural section")

    errors_dim = dims.get("learner_errors", {})
    if errors_dim.get("score", 0) >= 2:
        has_errors = bool(re.search(
            r"(?i)(common\s+mistake|\u043f\u043e\u043c\u0438\u043b\u043a|\u0442\u0438\u043f\u043e\u0432|\u043f\u043e\u0448\u0438\u0440\u0435\u043d|\[!warning\]|\[!caution\]|\[!tip\])",
            content_text,
        ))
        if not has_errors:
            reasons.append("Research has 3+ learner errors but content doesn't address common mistakes")

    return {
        "content_exists": True,
        "refresh_recommended": len(reasons) > 0,
        "reasons": reasons,
    }


def _check_content_alignment_professional(dims: dict, content_text: str) -> dict:
    """Check if content uses what the research provides (professional rubric)."""
    reasons = []

    hooks_dim = dims.get("engagement_hooks", {})
    if hooks_dim.get("score", 0) >= 1:
        content_hooks = len(re.findall(r"\[![a-z_-]+\]", content_text, re.IGNORECASE))
        if content_hooks == 0:
            reasons.append("Research has engagement hooks but content has 0 [!type] callouts")

    errors_dim = dims.get("language_norms", {})
    if errors_dim.get("score", 0) >= 2:
        has_errors = bool(re.search(
            r"(?i)(типов|помилк|русизм|\[!language-note\]|\[!common-error\]|\[!warning\])",
            content_text,
        ))
        if not has_errors:
            reasons.append("Research has language norms/errors but content doesn't address them")

    examples_dim = dims.get("authentic_examples", {})
    if examples_dim.get("score", 0) >= 1:
        gq = _count_guillemet_quotes(content_text)
        bq = _count_blockquotes(content_text)
        if gq + bq == 0:
            reasons.append("Research has authentic examples but content has no quoted examples")

    return {
        "content_exists": True,
        "refresh_recommended": len(reasons) > 0,
        "reasons": reasons,
    }


# ==================== QUALITY LABELS ====================


def quality_label(score: int) -> str:
    """Map score (0-10) to quality label."""
    if score >= 9:
        return "exemplary"
    elif score >= 7:
        return "solid"
    elif score >= 5:
        return "adequate"
    elif score >= 2:
        return "thin"
    else:
        return "stub"


def _compute_gaps(dims: dict) -> list[str]:
    """Generate actionable gap descriptions from dimension scores."""
    gaps = []
    for dim_name, dim_data in dims.items():
        if dim_data["score"] < dim_data["max"]:
            gaps.append(f"{dim_name}: {dim_data['detail']}")
    return gaps


# ==================== FILE DISCOVERY ====================


def find_research_path(track_dir: Path, slug: str) -> Path | None:
    """Find the research file path for a module.

    Checks V5 format ({slug}-research.md) and V6 format ({slug}-knowledge-packet.md).
    """
    research_dir = track_dir / "research"
    for candidate in [
        f"{slug}-research.md",
        f"{slug.lstrip('0123456789-')}-research.md",
        f"{slug}-knowledge-packet.md",
    ]:
        rp = research_dir / candidate
        if rp.exists():
            return rp
    return None


# ==================== PUBLIC API ====================


def assess_research(
    text: str,
    track_id: str,
    content_text: str | None = None,
    discovery_path: "Path | None" = None,
) -> dict:
    """
    Assess research file quality.

    Args:
        text: Research file content.
        track_id: Track identifier (e.g. "a1", "hist").
        content_text: Optional module content for alignment checking.
        discovery_path: Optional path to discovery.yaml for resource scoring.

    Returns:
        Assessment dict with score, quality, dimensions, gaps, content_alignment.
        Scores are normalized to 0-10 scale (raw score / max * 10).
    """
    words = len(text.split())
    rubric_name = get_rubric(track_id)

    if rubric_name is None:
        result = {
            "exists": True,
            "words": words,
            "quality": None,
            "score": None,
            "markers": None,
            "profile": None,
            "dimensions": None,
            "gaps": None,
        }
        if content_text is not None:
            result["content_alignment"] = {
                "content_exists": True,
                "refresh_recommended": False,
                "reasons": [],
            }
        return result

    # Score using appropriate rubric (format dimensions)
    if rubric_name == "core":
        dims = _score_core(text)
    elif rubric_name == "history":
        dims = _score_history(text)
    elif rubric_name == "professional":
        dims = _score_professional(text)
    else:
        dims = {}

    # Add substance dimensions (shared across all rubrics, level-aware thresholds)
    # Skip for V6 knowledge packets — they already have these dimensions scored
    if not _is_v6_knowledge_packet(text):
        tier = _get_substance_tier(track_id)
        discovery = _parse_discovery(discovery_path)
        dims["source_verification"] = _score_source_verification(text, tier, discovery)
        dims["claim_grounding"] = _score_claim_grounding(text, tier)
        dims["discovery_integration"] = _score_discovery_integration(discovery)
        dims["specificity"] = _score_specificity(text, tier)

    raw_score = sum(d["score"] for d in dims.values())
    max_possible = sum(d["max"] for d in dims.values())
    # Normalize to 0-10 scale for backward compatibility
    total_score = round(raw_score / max_possible * 10) if max_possible > 0 else 0
    quality = quality_label(total_score)
    gaps = _compute_gaps(dims)

    result = {
        "exists": True,
        "words": words,
        "quality": quality,
        "score": total_score,
        "score_raw": raw_score,
        "score_max": max_possible,
        "markers": total_score,  # backward compat
        "profile": rubric_name,
        "dimensions": dims,
        "gaps": gaps,
    }

    if content_text is not None:
        if rubric_name == "core":
            result["content_alignment"] = _check_content_alignment_core(dims, content_text)
        elif rubric_name == "history":
            result["content_alignment"] = _check_content_alignment_history(dims, content_text)
        elif rubric_name == "professional":
            result["content_alignment"] = _check_content_alignment_professional(dims, content_text)

    return result


def assess_research_compat(
    path: "Path | str",
    track_id: str,
    content_path: "Path | str | None" = None,
    discovery_path: "Path | str | None" = None,
) -> dict | None:
    """
    Compatibility wrapper that reads files and calls assess_research.

    Returns None if research file doesn't exist.
    If discovery_path is None, attempts to auto-discover it from the research path.
    """
    path = Path(path)
    if not path.exists():
        return None

    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None

    if len(text.strip()) < 10:
        rubric_name = get_rubric(track_id)
        return {
            "exists": True,
            "words": len(text.split()),
            "quality": "stub" if rubric_name else None,
            "score": 0 if rubric_name else None,
            "markers": 0 if rubric_name else None,
            "profile": rubric_name,
            "dimensions": None,
            "gaps": None,
        }

    content_text = None
    if content_path:
        content_path = Path(content_path)
        if content_path.exists():
            with contextlib.suppress(Exception):
                content_text = content_path.read_text(encoding="utf-8")

    # Auto-discover discovery.yaml from research path if not provided
    disc_path = Path(discovery_path) if discovery_path else None
    if disc_path is None:
        # research/ is sibling to orchestration/
        # research/{slug}-research.md → orchestration/{slug}/discovery.yaml
        slug = path.stem.replace("-research", "")
        orch_dir = path.parent.parent / "orchestration" / slug
        candidate = orch_dir / "discovery.yaml"
        if candidate.exists():
            disc_path = candidate

    result = assess_research(text, track_id, content_text, discovery_path=disc_path)

    # Mtime check: if research is newer than content, content wasn't written from it
    if content_path and content_text is not None and result.get("content_alignment"):
        try:
            research_mtime = path.stat().st_mtime
            content_mtime = Path(content_path).stat().st_mtime
            if research_mtime > content_mtime:
                alignment = result["content_alignment"]
                alignment["refresh_recommended"] = True
                if "Content predates research" not in str(alignment.get("reasons", [])):
                    alignment.setdefault("reasons", []).insert(
                        0, "Content predates research (research file is newer)"
                    )
        except OSError:
            pass

    return result
