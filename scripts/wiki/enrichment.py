"""Source enrichment — supplements discovery data with track-specific sources.

Core tracks (A1-C2): enriched via RAG textbook search (23K chunks, Grades 1-11).
Seminar tracks (FOLK, HIST, etc.): enriched via literary JSONL files on Google Drive.

Discovery files often have thin source refs (just a few textbook page fragments).
This module adds relevant textbook chunks, literary texts, local data files,
and cross-references to build a rich context for wiki article compilation.
"""

import yaml

from .channels import rank_external_hits as apply_channel_ranking
from .config import CURRICULUM_DIR, PROJECT_ROOT

SOURCE_CHAR_CAPS = {
    # A1 bumped 45_000 → 60_000 on 2026-04-18 after smoke-test showed
    # 62 chunks → 33 chunks trimming (117k → 45k chars) correlated with
    # source_grounding REJECT (5 MISATTRIBUTION findings). With 2k-char
    # post-#1324 chunks, 60k ≈ 30 chunks — still bounded, more headroom
    # for the writer to find a supporting chunk per claim.
    "a1": 60_000,
    "a2": 60_000,
    "b1": 80_000,
    "b2": 90_000,
    "c1": 110_000,
    "c2": 120_000,
}

_BACKGROUND_SOURCE_TYPES = {"wikipedia", "external", "external_article"}
#: `dict[str, float]` (not int) so callers with float-typed parameter
#: signatures — e.g. `rank_external_hits(..., source_type_priority=...)` —
#: type-check without dict invariance warnings.
_SOURCE_TYPE_PRIORITY: dict[str, float] = {
    "discovery": 120.0,
    "local": 110.0,
    "textbook": 100.0,
    "literary": 95.0,
    "external_article": 60.0,
    "external": 55.0,
    "wikipedia": 40.0,
    "external_video": 0.0,
}


def _chunk_source_type(chunk: dict) -> str:
    """Infer a normalized source type for budgeting and formatting."""
    source_type = str(chunk.get("source_type", "")).strip()
    if source_type:
        return source_type
    if chunk.get("grade") or chunk.get("section_title"):
        return "textbook"
    if chunk.get("work") or chunk.get("author"):
        return "literary"
    if chunk.get("genre") and str(chunk.get("chunk_id", "")).startswith("folk-micro-"):
        return "local"
    return "discovery"


def _strip_prefixed_metadata(text: str) -> str:
    """Remove verbose metadata lines duplicated in the compiler header."""
    lines = text.splitlines()
    while lines:
        head = lines[0].strip()
        if head.startswith((
            "External article:",
            "External pedagogical article:",
            "External pedagogical reference:",
            "External video reference:",
            "Wikipedia:",
            "Source:",
            "Channel:",
            "URL:",
            "Note:",
        )):
            lines.pop(0)
            continue
        break
    return "\n".join(lines).strip()


def _chunk_body_length(chunk: dict) -> int:
    """Estimate useful prompt budget consumed by a chunk body."""
    return len(_strip_prefixed_metadata(str(chunk.get("text", "")).strip()))


def _dedupe_chunks(chunks: list[dict]) -> list[dict]:
    """Drop exact duplicates by chunk_id or normalized text body."""
    seen_chunk_ids: set[str] = set()
    seen_bodies: set[str] = set()
    deduped: list[dict] = []
    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id", "")).strip()
        body = _strip_prefixed_metadata(str(chunk.get("text", "")).strip())
        if chunk_id:
            if chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(chunk_id)
        elif body:
            body_key = " ".join(body.split())
            if body_key in seen_bodies:
                continue
            seen_bodies.add(body_key)
        deduped.append(chunk)
    return deduped


def _cap_source_chunks(track: str, chunks: list[dict]) -> tuple[list[dict], int, int]:
    """Cap useful source material with background-source guards."""
    char_cap = SOURCE_CHAR_CAPS.get(track, 110_000)
    background_cap = int(char_cap * 0.2)
    background_max_chunks = 3

    scored = sorted(
        chunks,
        key=lambda c: (
            c.get("_kw_score", 0),
            _SOURCE_TYPE_PRIORITY.get(_chunk_source_type(c), 50),
            -float(c.get("adjusted_score", c.get("rank", 0.0)) or 0.0),
        ),
        reverse=True,
    )

    selected: list[dict] = []
    total_chars = 0
    background_chars = 0
    background_count = 0

    for chunk in scored:
        body_len = _chunk_body_length(chunk)
        if body_len <= 0:
            continue

        source_type = _chunk_source_type(chunk)
        is_background = source_type in _BACKGROUND_SOURCE_TYPES
        if is_background:
            if background_count >= background_max_chunks:
                continue
            if background_chars + body_len > background_cap:
                continue

        if total_chars + body_len > char_cap:
            continue

        selected.append(chunk)
        total_chars += body_len
        if is_background:
            background_chars += body_len
            background_count += 1

    return selected, char_cap, total_chars


def rank_external_hits(hits: list[dict], track: str | None = None) -> list[dict]:
    """Apply channel-aware ordering on top of source-type priority."""
    return apply_channel_ranking(
        hits,
        track=track,
        source_type_priority=_SOURCE_TYPE_PRIORITY,
    )


def enrich_sources(track: str, slug: str, sources_info: dict) -> list[dict]:
    """Enrich source chunks for a module with track-specific data.

    Core tracks (A1-C2): load textbook JSONL files directly, score by keyword.
    Seminar tracks: load literary JSONL files from Google Drive.
    Same approach for both — no RAG, direct JSONL keyword matching.

    Combines:
    1. Discovery inline chunks (rag_literary, rag_chunks)
    2. Core tracks: textbook JSONL files (40 ukrmova + bukvar + ukrlit for C1/C2)
    3. Seminar tracks: literary JSONL files + keyword-matched sources
    4. Local data files (e.g., folk_micro_genres.yaml)

    Returns a list of chunk dicts ready for the compiler.
    """
    all_chunks: list[dict] = []

    # 1. Discovery inline chunks — these are the original plan sources,
    # give them a high base score so they survive capping.
    # Shallow-copy to avoid mutating the caller's data.
    for chunk in sources_info.get("literary_chunks", []):
        all_chunks.append({**chunk, "_kw_score": 100, "source_type": _chunk_source_type(chunk)})
    for chunk in sources_info.get("textbook_chunks", []):
        all_chunks.append({**chunk, "_kw_score": 100, "source_type": _chunk_source_type(chunk)})
    discovery_count = len(all_chunks)

    # 2. Unified dense retrieval across all dense-indexed corpora.
    discovery_path = CURRICULUM_DIR / track / "discovery" / f"{slug}.yaml"
    if discovery_path.exists():
        from .sources_db import search_sources

        unified_hits = search_sources(
            discovery_path,
            track=track,
            strategy="unified_dense",
            limit=10,
        )
        if unified_hits:
            print(f"  🔎 +{len(unified_hits)} unified dense sources ({track})")
            all_chunks.extend(unified_hits)

    # 3. Local data enrichment
    local_chunks = _load_local_data(track, slug)
    if local_chunks:
        print(f"  📄 +{len(local_chunks)} chunks from local data")
        all_chunks.extend(local_chunks)

    # 4. External resources — explicit YAML mappings (URL-matched)
    ext_chunks = _load_external_resources(track, slug)
    if ext_chunks:
        print(f"  🌐 +{len(ext_chunks)} external reference sources (mapped)")
        all_chunks.extend(ext_chunks)

    if not all_chunks:
        print(f"  ⚠️  No source material found for {track}/{slug}")
        all_chunks = [{"text": f"Topic: {slug.replace('-', ' ')}", "chunk_id": "no-source"}]
    else:
        all_chunks = _dedupe_chunks(all_chunks)
        total_chars = sum(_chunk_body_length(c) for c in all_chunks)
        capped, char_cap, kept_chars = _cap_source_chunks(track, all_chunks)
        if kept_chars < total_chars:
            print(f"  ✂️  Capped from {len(all_chunks)} to {len(capped)} chunks "
                  f"({total_chars:,} → {kept_chars:,} useful chars, cap: {char_cap:,})")
            all_chunks = capped

        print(f"  📊 Total: {len(all_chunks)} chunks "
              f"(discovery: {discovery_count}, enriched: {len(all_chunks) - discovery_count})")

    return all_chunks


def _extract_ukrainian_keywords(sources_info: dict) -> set[str]:
    """Extract Ukrainian keywords from discovery data for searching.

    The discovery file's query_keywords contain Ukrainian terms that are
    far more useful than the Latin slug for searching Ukrainian literary texts.
    """
    keywords: set[str] = set()
    discovery = sources_info.get("discovery", {})
    if not discovery:
        return keywords

    for kw in discovery.get("query_keywords", []):
        # Skip English-only keywords
        if all(ord(c) < 256 for c in kw.replace(" ", "")):
            continue
        # Extract individual Ukrainian words (4+ chars)
        for word in kw.split():
            # Check if word has Cyrillic characters
            if any("\u0400" <= c <= "\u04FF" for c in word) and len(word) >= 4:
                # Strip punctuation and markdown formatting
                clean = word.strip(".,;:!?\"'«»()—–-`*_")
                if len(clean) >= 4:
                    keywords.add(clean.lower())

    return keywords



# Cached external_resources.yaml (loaded once per process)
_EXT_RESOURCES: dict | None = None


def _get_external_resources() -> dict:
    """Load and cache external_resources.yaml."""
    global _EXT_RESOURCES
    if _EXT_RESOURCES is None:
        ext_path = PROJECT_ROOT / "docs" / "resources" / "external_resources.yaml"
        if ext_path.exists():
            with open(ext_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            _EXT_RESOURCES = data.get("resources", {}) if data else {}
        else:
            _EXT_RESOURCES = {}
    assert _EXT_RESOURCES is not None
    return _EXT_RESOURCES


def _load_external_resources(track: str, slug: str) -> list[dict]:
    """Load external resources for a module — fetched content when available.

    Reads docs/resources/external_resources.yaml to find which articles/videos
    are relevant for this module. Then looks up the cached JSONL files for
    actual content. Falls back to reference metadata if not cached.

    Keys in the YAML are formatted as "{level}-{slug}" (e.g. "a1-sounds-letters-and-hello").

    Note: slug may include level prefix (e.g. "a2-bridge") or not (e.g. "around-the-city").
    This function normalizes both formats.
    """
    resources = _get_external_resources()

    # Normalize slug: if it starts with "{track}-", strip that prefix
    # This handles both "a2-bridge" and "bridge" style slugs
    normalized_slug = slug
    if slug.startswith(f"{track}-"):
        normalized_slug = slug[len(track) + 1:]  # Remove "{track}-"

    key = f"{track}-{normalized_slug}"
    entry = resources.get(key)
    if not entry:
        return []

    from .sources_db import lookup_by_url

    chunks = []
    skipped_reference_only = 0

    # Articles — inject full cached content when available
    for article in entry.get("articles", []):
        if article.get("relevance") != "high":
            continue
        url = article.get("url", "")
        title = article.get("title", "")
        source = article.get("source", "")

        cached = lookup_by_url(url)
        if cached and cached.get("text"):
            text = cached["text"][:6000]
        else:
            skipped_reference_only += 1
            continue

        chunks.append({
            "text": text,
            "chunk_id": f"ext-article-{len(chunks)}",
            "source_type": "external_article",
            "title": cached.get("title", title) if cached else title,
            "url": url,
            "source_name": cached.get("domain", source) if cached else source,
        })

    # Bare YouTube references are intentionally excluded: without subtitles or
    # transcripts they consume prompt budget but provide no citable evidence.
    skipped_reference_only += sum(
        1 for video in entry.get("youtube", []) if video.get("relevance") == "high"
    )

    if skipped_reference_only:
        print(f"  ℹ️  Skipped {skipped_reference_only} external references without cached content")

    return chunks


def _load_local_data(track: str, slug: str) -> list[dict]:
    """Load local data files relevant to the track/slug.

    Returns chunks formatted for the compiler.
    """
    chunks: list[dict] = []

    if track == "folk":
        chunks.extend(_load_folk_micro_genres(slug))

    return chunks


def _load_folk_micro_genres(slug: str) -> list[dict]:
    """Load folk micro-genre examples from data/folk_micro_genres.yaml.

    Matches slug keywords to genre categories in the YAML.
    """
    yaml_path = PROJECT_ROOT / "data" / "folk_micro_genres.yaml"
    if not yaml_path.exists():
        return []

    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data:
        return []

    # Map slug keywords to YAML genre keys
    slug_genre_map: dict[str, list[str]] = {
        "zahadky": ["загадки"],
        "prykazky": ["прислів'я"],
        "pryslivia": ["прислів'я"],
        "koliadky": ["колядки"],
        "shchedrivky": ["щедрівки"],
        "vesnianky": ["веснянки"],
        "hayivky": ["гаївки"],
        "lichilky": ["лічилки"],
        "myrilky": ["мирилки"],
        "skоromovky": ["скоромовки"],
    }

    # Find matching genres (deduplicate)
    target_genres_set: set[str] = set()
    for key, genres in slug_genre_map.items():
        if key in slug:
            target_genres_set.update(genres)
    target_genres: list[str] = sorted(target_genres_set)

    # If no specific match, try to match any genre key in the YAML
    if not target_genres:
        slug_lower = slug.replace("-", " ").lower()
        for genre_key in data:
            if isinstance(genre_key, str) and genre_key.lower() in slug_lower:
                target_genres.append(genre_key)

    chunks = []
    for genre in target_genres:
        entries = data.get(genre, [])
        if not isinstance(entries, list):
            continue
        # Take up to 10 examples
        for entry in entries[:10]:
            if isinstance(entry, dict):
                text_parts = []
                if entry.get("text"):
                    text_parts.append(entry["text"])
                if entry.get("answer"):
                    text_parts.append(f"Відповідь: {entry['answer']}")
                if entry.get("source"):
                    text_parts.append(f"Джерело: {entry['source']}")
                chunks.append({
                    "text": " | ".join(text_parts),
                    "chunk_id": f"folk-micro-{genre}-{len(chunks)}",
                    "genre": genre,
                    "source_type": "local",
                })

    return chunks
