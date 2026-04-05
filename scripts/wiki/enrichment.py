"""Source enrichment — supplements discovery data with track-specific sources.

Core tracks (A1-C2): enriched via RAG textbook search (23K chunks, Grades 1-11).
Seminar tracks (FOLK, HIST, etc.): enriched via literary JSONL files on Google Drive.

Discovery files often have thin source refs (just a few textbook page fragments).
This module adds relevant textbook chunks, literary texts, local data files,
and cross-references to build a rich context for wiki article compilation.
"""

import yaml

from .config import LITERARY_DIR, PROJECT_ROOT
from .sources import load_literary_jsonl

# ── Core track grade mapping ──────────────────────────────────
# Which school grades teach the grammar concepts at each CEFR level.
# Based on Ukrainian State Standard 2024 + textbook analysis.
# Multiple grades searched to capture progression (intro → mastery).
CORE_TRACK_GRADES: dict[str, list[int]] = {
    "a1": [1, 2, 3],       # Alphabet, basic sounds, simple sentences
    "a2": [4, 5, 6],       # Cases, verb aspects, basic grammar
    "b1": [5, 6, 7],       # Complex grammar, syntax, advanced cases
    "b2": [7, 8, 9],       # Stylistics, complex syntax, literary analysis
    "c1": [9, 10, 11],     # Academic writing, advanced stylistics
    "c2": [10, 11],        # Mastery, literary criticism, professional
}

# ── Track-specific literary source mappings ──────────────────────
# Maps tracks to literary JSONL files known to contain relevant content.
# These supplement whatever the discovery file already found.

FOLK_LITERARY_SOURCES = [
    "wave7-kostomarov-slovyanska-mifolohiia.jsonl",
    "wave4-chyzhevsky-istoriia-lit.jsonl",        # Folk traditions section
    "wave7-popovych-narys-kultury.jsonl",          # Cultural overview
    "wave8-ukr-lit-entsyklopediia.jsonl",          # Genre entries
]

HIST_LITERARY_SOURCES = [
    "грушевський-історія-україни-руси-т4.jsonl",
    "грушевський-історія-україни-руси-т5.jsonl",
    "wave7-hrushevsky-vybrani-statti.jsonl",
    "wave7-krypyakevych-gvk.jsonl",
    "wave7-krypyakevych-istkult.jsonl",
    "wave7-holobutsky-zaporizhzhia.jsonl",
    "wave7-shcherbak-kozatstvo.jsonl",
    "wave7-antonovych-vybrani.jsonl",
]

OES_LITERARY_SOURCES = [
    "wave9-shevelov-fonolohiia.jsonl",
    "wave9-rusanivsky-ist-lit-movy.jsonl",
    "wave9-pivtorak-pokhodzhennia.jsonl",
    "wave8-hensiorsky-gvl-mova.jsonl",
    "wave8-hensiorsky-gvl-process.jsonl",
    "wave0-slovo-o-polku.jsonl",
    "wave5-yushkov-ruska-pravda.jsonl",
    "wave8-biletsky-ruska-pravda-tekst.jsonl",
]

RUTH_LITERARY_SOURCES = [
    "wave9-ohiyenko-ist-lit-movy.jsonl",
    "wave7-statut-1566.jsonl",
    "wave9-uzhevych-hramatyka.jsonl",
    "wave9-uzhevych-paryzky.jsonl",
    "wave9-fedorovych-azbuka-1578.jsonl",
    "wave9-verbytsky-bukvar-1627.jsonl",
    "wave9-synonima-slavenoroskaia.jsonl",
    "wave8-isaievych-knyhovydannia.jsonl",
    "wave8-ohdruk-istoriia-drukarstva.jsonl",
    "wave8-masliuk-poetyky-rytoryky.jsonl",
]

ISTORIO_LITERARY_SOURCES = [
    "wave7-kohut-tsentralizm.jsonl",
    "wave7-nalyvaiko-ochyma-zakhodu.jsonl",
    "wave7-dzyuba-internatsionalizm.jsonl",
    "wave7-shevchenko-ukraina-skhid-zakhid.jsonl",
    "wave7-entsyklopediia-ukrainoznavstva.jsonl",
    "wave7-hrushevsky-vybrani-statti.jsonl",
]

TRACK_LITERARY_MAP: dict[str, list[str]] = {
    "folk": FOLK_LITERARY_SOURCES,
    "hist": HIST_LITERARY_SOURCES,
    "oes": OES_LITERARY_SOURCES,
    "ruth": RUTH_LITERARY_SOURCES,
    "istorio": ISTORIO_LITERARY_SOURCES,
}

# Keyword → literary file mappings for cross-track searches
KEYWORD_SOURCE_MAP: dict[str, list[str]] = {
    "kobzar": ["ukrlib-shevchenko.jsonl"],
    "shevchenko": ["ukrlib-shevchenko.jsonl"],
    "franko": ["ukrlib-franko.jsonl"],
    "lesya": ["ukrlib-lesya.jsonl"],
    "kotsyubynsky": ["ukrlib-kotsyubynsky.jsonl"],
    "skovoroda": ["wave5-skovoroda-tvory.jsonl", "wave8-chyzhevsky-skovoroda.jsonl"],
    "baroko": ["wave3-poeziya-baroko.jsonl", "wave8-chyzhevsky-baroko.jsonl"],
    "kozak": ["wave7-holobutsky-zaporizhzhia.jsonl", "wave7-shcherbak-kozatstvo.jsonl"],
    "mazepa": ["wave7-matskiv-mazepa-dzherela.jsonl"],
    "khmelnytsky": ["wave7-gvozdyk-pritsak-khmelnytsky.jsonl"],
}


def _search_textbook_rag(ukr_keywords: set[str], grades: list[int],
                         max_results: int = 20) -> list[dict]:
    """Search textbook RAG for relevant chunks using Ukrainian keywords.

    Runs multiple queries (one per top keyword) across the specified grades,
    deduplicates by chunk_id, and returns the best results.
    """
    try:
        from rag.query import search_text
    except ImportError:
        print("  ⚠️  RAG search unavailable (qdrant not running?)")
        return []

    if not ukr_keywords:
        return []

    seen_ids: set[str] = set()
    all_hits: list[dict] = []

    # Build search queries from keywords — group related keywords for better recall
    # Take the most specific keywords (longer = more specific)
    sorted_kw = sorted(ukr_keywords, key=len, reverse=True)

    # Run 2-3 searches: first with the topic phrase, then individual keywords
    queries = []

    # Query 1: Combine top 3 keywords into a phrase (most semantic coverage)
    if len(sorted_kw) >= 2:
        queries.append(" ".join(sorted_kw[:3]))

    # Query 2-3: Individual top keywords (catch different textbook formulations)
    for kw in sorted_kw[:2]:
        if kw not in queries:
            queries.append(kw)

    for query in queries[:3]:
        for grade in grades:
            try:
                results = search_text(
                    query, grade=grade,
                    limit=max_results // len(grades),
                )
            except Exception as e:
                print(f"  ⚠️  RAG search error for grade {grade}: {e}")
                continue

            for hit in results:
                cid = hit.get("chunk_id", "")
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    all_hits.append(hit)

    # Sort by score (if available) and cap
    all_hits.sort(key=lambda h: h.get("score", 0), reverse=True)
    return all_hits[:max_results]


def enrich_sources(track: str, slug: str, sources_info: dict) -> list[dict]:
    """Enrich source chunks for a module with track-specific data.

    Core tracks (A1-C2): search textbook RAG with Ukrainian keywords.
    Seminar tracks: search literary JSONL files on Google Drive.

    Combines:
    1. Discovery inline chunks (rag_literary, rag_chunks)
    2. Core tracks: RAG textbook search (Grades 1-11 Ukrainian language textbooks)
    3. Seminar tracks: literary JSONL files + keyword-matched sources
    4. Local data files (e.g., folk_micro_genres.yaml)

    Returns a list of chunk dicts ready for the compiler.
    """
    all_chunks: list[dict] = []

    # 1. Discovery inline chunks
    all_chunks.extend(sources_info.get("literary_chunks", []))
    all_chunks.extend(sources_info.get("textbook_chunks", []))
    discovery_count = len(all_chunks)

    # Extract Ukrainian keywords from discovery for searching
    # (the slug is Latin transliteration — useless for searching Ukrainian text)
    ukr_keywords = _extract_ukrainian_keywords(sources_info)

    # 2. Core tracks: search textbook RAG
    if track in CORE_TRACK_GRADES:
        grades = CORE_TRACK_GRADES[track]
        rag_chunks = _search_textbook_rag(ukr_keywords, grades, max_results=20)
        if rag_chunks:
            print(f"  📖 +{len(rag_chunks)} chunks from textbook RAG "
                  f"(grades {grades}, {len(ukr_keywords)} keywords)")
            all_chunks.extend(rag_chunks)

    # 3. Seminar tracks: literary JSONL files
    track_files = TRACK_LITERARY_MAP.get(track, [])
    if track_files:
        track_chunks = _load_relevant_chunks(
            track_files, slug, max_per_file=15, ukr_keywords=ukr_keywords,
        )
        if track_chunks:
            print(f"  📚 +{len(track_chunks)} chunks from track literary sources")
            all_chunks.extend(track_chunks)

    # 4. Keyword-matched sources from the slug
    slug_words = slug.replace("-", " ").lower().split()
    for keyword, files in KEYWORD_SOURCE_MAP.items():
        if keyword in slug_words or keyword in slug:
            kw_chunks = _load_relevant_chunks(
                files, slug, max_per_file=10, ukr_keywords=ukr_keywords,
            )
            if kw_chunks:
                print(f"  🔑 +{len(kw_chunks)} chunks from keyword '{keyword}'")
                all_chunks.extend(kw_chunks)

    # 5. Local data enrichment
    local_chunks = _load_local_data(track, slug)
    if local_chunks:
        print(f"  📄 +{len(local_chunks)} chunks from local data")
        all_chunks.extend(local_chunks)

    # 6. Literary files found by keyword search in sources.py
    if len(all_chunks) < 10 and sources_info.get("literary_files"):
        for lit_path in sources_info["literary_files"][:3]:
            chunks = load_literary_jsonl(lit_path)
            sampled = chunks[:20]
            print(f"  📖 +{len(sampled)} chunks from {lit_path.name}")
            all_chunks.extend(sampled)

    if not all_chunks:
        print(f"  ⚠️  No source material found for {track}/{slug}")
        all_chunks = [{"text": f"Topic: {slug.replace('-', ' ')}", "chunk_id": "no-source"}]
    else:
        # Cap total source material at ~80K chars to fit Gemini context
        # (prompt template adds ~5K, so 80K source + 5K template ≈ 85K total)
        total_chars = sum(len(c.get("text", "")) for c in all_chunks)
        if total_chars > 80_000:
            capped = []
            char_count = 0
            for chunk in all_chunks:
                chunk_len = len(chunk.get("text", ""))
                if char_count + chunk_len > 80_000:
                    break
                capped.append(chunk)
                char_count += chunk_len
            print(f"  ✂️  Capped from {len(all_chunks)} to {len(capped)} chunks "
                  f"({total_chars:,} → {char_count:,} chars)")
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


def _load_relevant_chunks(filenames: list[str], slug: str,
                          max_per_file: int = 15,
                          ukr_keywords: set[str] | None = None) -> list[dict]:
    """Load chunks from literary files, filtering for relevance.

    Uses both Latin slug words AND Ukrainian keywords from discovery
    to score chunks. Ukrainian keywords are weighted higher (x2) since
    they match the actual text language.
    """
    slug_words = set(slug.replace("-", " ").lower().split())
    slug_words = {w for w in slug_words if len(w) > 3}
    ukr_kw = ukr_keywords or set()

    all_relevant: list[dict] = []
    for filename in filenames:
        filepath = LITERARY_DIR / filename
        if not filepath.exists():
            continue

        try:
            chunks = load_literary_jsonl(filepath)
        except Exception as e:
            print(f"  ⚠️  Error loading {filename}: {e}")
            continue

        # Score each chunk by keyword overlap
        scored = []
        for chunk in chunks:
            text_lower = chunk.get("text", "").lower()
            # Ukrainian keywords score 2x (they actually match the text)
            score = sum(2 for w in ukr_kw if w in text_lower)
            score += sum(1 for w in slug_words if w in text_lower)
            if score > 0:
                scored.append((score, chunk))

        # Take top N by score
        scored.sort(key=lambda x: -x[0])
        for _score, chunk in scored[:max_per_file]:
            all_relevant.append(chunk)

    return all_relevant


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
                })

    return chunks
