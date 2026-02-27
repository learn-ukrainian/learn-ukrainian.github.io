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
        "max_score": 10,
        "dimensions": ["state_standard", "vocabulary", "cultural_hooks",
                        "learner_errors", "cross_references", "pedagogy_notes"],
    },
    "history": {
        "tracks": {"hist", "c1-bio", "c1-hist", "oes", "ruth",
                    "lit", "lit-essay", "lit-fantastika", "lit-hist-fic",
                    "lit-humor", "lit-youth", "lit-war", "lit-doc",
                    "lit-drama", "lit-crimea"},
        "max_score": 10,
        "dimensions": ["sources", "chronology", "primary_quotes",
                        "engagement_hooks", "decolonization", "section_notes"],
    },
    "professional": {
        "tracks": {"b2-pro", "c1-pro"},
        "max_score": 10,
        "dimensions": ["sources", "terminology", "language_norms",
                        "authentic_examples", "engagement_hooks", "section_notes"],
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
}


# ==================== HELPERS ====================


def _extract_section(text: str, header_patterns: list[str]) -> str | None:
    """Extract text under a section header until the next ## header or EOF."""
    for pattern in header_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = match.end()
            next_header = re.search(r"\n##\s", text[start:])
            end = start + next_header.start() if next_header else len(text)
            section = text[start:end].strip()
            return section if section else None
    return None


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


def _count_blockquotes(text: str) -> int:
    """Count blockquote lines (lines starting with >)."""
    return sum(1 for line in text.splitlines() if line.strip().startswith(">"))


def _count_guillemet_quotes(text: str) -> int:
    """Count guillemet-style quotes."""
    return len(re.findall(r"\u00ab[^\u00bb]+\u00bb", text))


def _count_urls(text: str) -> int:
    """Count unique URLs in text."""
    return len(set(re.findall(r"https?://[^\s\)>]+", text)))


def _count_dated_entries(text: str) -> int:
    """Count list entries with year or century references.

    Matches any bullet-point line containing either:
    - A 3-4 digit year (e.g., 1654, 882)
    - A Roman or Arabic century reference with 'ст.' (e.g., IX ст., 12 ст.)
    In a chronology section, these are always dated entries.
    """
    # Year-based entries (3-4 digit number) — match full line to avoid dedup issues
    year_entries = set(re.findall(
        r"^[\s]*[-*]\s+.*\b\d{3,4}\b.*$",
        text, re.MULTILINE,
    ))
    # Century-based entries (Roman numeral + ст. or Arabic + ст.)
    century_entries = set(re.findall(
        r"^[\s]*[-*]\s+.*(?:[IVXLC]+|[0-9]{1,2})\s*ст\..*$",
        text, re.MULTILINE,
    ))
    return len(year_entries | century_entries)


def _count_numbered_items(text: str) -> int:
    """Count numbered list items (1. 2. 3. etc.)."""
    return len(re.findall(r"^\s*\d+\.\s+", text, re.MULTILINE))


def _count_h3_subsections(text: str) -> int:
    """Count ### sub-headers."""
    return len(re.findall(r"^###\s", text, re.MULTILINE))


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


def _score_core(text: str) -> dict:
    """Score a research file using the core rubric (A1, A2)."""
    dims = {}

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
        if count >= 5:
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
        if entries >= 5:
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
    if sources_dim.get("score", 0) >= 3:
        if _count_urls(content_text) == 0:
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
    """Find the research file path for a module."""
    research_dir = track_dir / "research"
    for candidate in [f"{slug}-research.md", f"{slug.lstrip('0123456789-')}-research.md"]:
        rp = research_dir / candidate
        if rp.exists():
            return rp
    return None


# ==================== PUBLIC API ====================


def assess_research(text: str, track_id: str, content_text: str | None = None) -> dict:
    """
    Assess research file quality.

    Args:
        text: Research file content.
        track_id: Track identifier (e.g. "a1", "hist").
        content_text: Optional module content for alignment checking.

    Returns:
        Assessment dict with score, quality, dimensions, gaps, content_alignment.
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

    # Score using appropriate rubric
    if rubric_name == "core":
        dims = _score_core(text)
    elif rubric_name == "history":
        dims = _score_history(text)
    elif rubric_name == "professional":
        dims = _score_professional(text)
    else:
        dims = {}

    total_score = sum(d["score"] for d in dims.values())
    quality = quality_label(total_score)
    gaps = _compute_gaps(dims)

    result = {
        "exists": True,
        "words": words,
        "quality": quality,
        "score": total_score,
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
) -> dict | None:
    """
    Compatibility wrapper that reads files and calls assess_research.

    Returns None if research file doesn't exist.
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
            try:
                content_text = content_path.read_text(encoding="utf-8")
            except Exception:
                pass

    result = assess_research(text, track_id, content_text)

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
