"""Source material loader — reads JSONLs and discovery files for wiki compilation.

Loads literary texts, textbook chunks, and discovery files from Google Drive
and the local curriculum directory. Groups source material by topic for
compilation into wiki articles.
"""

import json
from pathlib import Path

import yaml

from .config import CURRICULUM_DIR, LITERARY_DIR, TEXTBOOK_CHUNKS_DIR


def load_literary_jsonl(path: Path) -> list[dict]:
    """Load chunks from a single literary text JSONL file.

    Each chunk has: chunk_id, text, source_url, token_count,
    work, author, year, genre, language_period.
    """
    chunks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def load_textbook_jsonl(path: Path) -> list[dict]:
    """Load chunks from a single textbook JSONL file.

    Each chunk has: chunk_id, text, token_count, section_title,
    grade, author, year, subject, trust_tier, pdf_stem.
    """
    chunks = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunk = json.loads(line)
                # Skip garbled chunks
                if chunk.get("quality", {}).get("is_clean", True):
                    chunks.append(chunk)
    return chunks


def list_literary_sources() -> list[Path]:
    """List all literary text JSONL files on Google Drive."""
    if not LITERARY_DIR.exists():
        return []
    return sorted(LITERARY_DIR.glob("*.jsonl"))


def list_textbook_sources(*, grades: list[int] | None = None,
                          subjects: list[str] | None = None) -> list[Path]:
    """List textbook chunk JSONL files, optionally filtered by grade/subject.

    Args:
        grades: Filter to specific grades (e.g., [5, 6, 7]).
        subjects: Filter to subjects containing these strings (e.g., ["istoria", "ukrlit"]).
    """
    if not TEXTBOOK_CHUNKS_DIR.exists():
        return []

    files = []
    for grade_dir in sorted(TEXTBOOK_CHUNKS_DIR.iterdir()):
        if not grade_dir.is_dir():
            continue
        # Parse grade number from dir name "grade-05"
        grade_num = int(grade_dir.name.split("-")[-1])
        if grades and grade_num not in grades:
            continue

        for jsonl in sorted(grade_dir.glob("*.jsonl")):
            if subjects:
                stem = jsonl.stem.lower()
                if not any(s in stem for s in subjects):
                    continue
            files.append(jsonl)
    return files


def load_discovery(track: str, slug: str) -> dict | None:
    """Load a single discovery file for a track module.

    Returns the parsed YAML or None if not found.
    """
    path = CURRICULUM_DIR / track / "discovery" / f"{slug}.yaml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_discovery_slugs(track: str) -> list[str]:
    """List all module slugs that have discovery files for a track.

    If no discovery files exist but plans do, auto-generates discovery
    files from plan data (extracting keywords from title, sections, vocab).
    """
    discovery_dir = CURRICULUM_DIR / track / "discovery"
    plans_dir = CURRICULUM_DIR / "plans" / track

    # If discovery files exist, use them
    if discovery_dir.exists():
        slugs = sorted(p.stem for p in discovery_dir.glob("*.yaml"))
        if slugs:
            return slugs

    # Auto-generate from plans if no discovery files
    if plans_dir.exists():
        plan_files = sorted(
            p for p in plans_dir.glob("*.yaml")
            if not p.name.startswith(".") and not p.name.endswith(".bak")
        )
        if plan_files:
            _auto_generate_discovery(track, plan_files, discovery_dir)
            return sorted(p.stem for p in discovery_dir.glob("*.yaml"))

    return []


def _auto_generate_discovery(
    track: str, plan_files: list, discovery_dir: Path
) -> None:
    """Generate discovery files from plan data when none exist.

    Extracts keywords from plan title, section names, objectives,
    and vocabulary hints to create minimal discovery files.
    """
    from datetime import UTC, datetime

    from pipeline.vocab_helpers import extract_vocab_words

    discovery_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()
    count = 0

    for plan_path in plan_files:
        slug = plan_path.stem
        disc_path = discovery_dir / f"{slug}.yaml"
        if disc_path.exists():
            continue

        plan = yaml.safe_load(plan_path.read_text("utf-8"))
        if not plan or not isinstance(plan, dict):
            continue

        # Extract keywords
        keywords = []
        title = plan.get("title", "")
        if title:
            keywords.append(title)
        for section in (plan.get("content_outline") or []):
            if isinstance(section, dict):
                name = section.get("section", "")
                if name:
                    keywords.append(name)
        for obj in (plan.get("objectives") or []):
            if any("\u0400" <= c <= "\u04FF" for c in str(obj)):
                keywords.append(str(obj))
        for word in extract_vocab_words(plan.get("vocabulary_hints") or []):
            keywords.append(word)

        discovery = {
            "discovered_at": now,
            "query_keywords": keywords,
            "error": None,
            "warning": "Auto-generated from plan",
            "rag_chunks": [],
            "rag_literary": [],
        }

        with open(disc_path, "w", encoding="utf-8") as f:
            yaml.dump(discovery, f, allow_unicode=True, default_flow_style=False)
        count += 1

    if count:
        print(f"  📝 Auto-generated {count} discovery files for {track}")


def extract_source_refs(discovery: dict) -> dict[str, list[str]]:
    """Extract source references (chunk_ids) from a discovery file.

    Returns dict with keys: 'literary', 'textbook', 'image'.
    """
    refs: dict[str, list[str]] = {
        "literary": [],
        "textbook": [],
        "image": [],
    }
    for chunk in discovery.get("rag_literary", []):
        cid = chunk.get("chunk_id", "")
        if cid:
            refs["literary"].append(cid)
    for chunk in discovery.get("rag_chunks", []):
        cid = chunk.get("chunk_id", "")
        if cid:
            refs["textbook"].append(cid)
    for img in discovery.get("rag_images", []):
        iid = img.get("chunk_id", img.get("image_id", ""))
        if iid:
            refs["image"].append(iid)
    return refs


def find_literary_by_keywords(keywords: list[str]) -> list[Path]:
    """Find literary JSONL files whose names match any of the keywords.

    Uses fuzzy stem matching — e.g., keyword "shevchenko" matches
    "ukrlib-shevchenko.jsonl" and "wave7-shevchenko-ukraina-skhid-zakhid.jsonl".
    """
    all_files = list_literary_sources()
    matches = []
    for f in all_files:
        stem = f.stem.lower()
        for kw in keywords:
            if kw.lower() in stem:
                matches.append(f)
                break
    return matches


def find_literary_by_chunk_ids(chunk_ids: list[str]) -> dict[Path, list[str]]:
    """Map chunk IDs to their source JSONL files.

    Chunk IDs have a hash prefix (e.g., "04bf5f0f_c0000") that doesn't
    directly map to filenames. We need to scan files to find matches.

    For efficiency, builds an index on first call.

    Returns: {jsonl_path: [matching_chunk_ids]}
    """
    if not chunk_ids:
        return {}

    target_ids = set(chunk_ids)
    result: dict[Path, list[str]] = {}

    for jsonl_path in list_literary_sources():
        matched = []
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Quick check before full parse — chunk_id is near the start
                for cid in target_ids:
                    if cid in line:
                        chunk = json.loads(line)
                        if chunk.get("chunk_id") in target_ids:
                            matched.append(chunk["chunk_id"])
        if matched:
            result[jsonl_path] = matched
    return result


def gather_discovery_sources(track: str, slug: str) -> dict:
    """Gather all source material referenced by a discovery file.

    Returns:
        {
            "discovery": <parsed discovery dict>,
            "keywords": [query keywords],
            "literary_chunks": [chunk dicts from literary JSONLs],
            "textbook_chunks": [chunk dicts from textbook JSONLs],
            "literary_files": [Paths to matching literary JSONLs],
        }
    """
    discovery = load_discovery(track, slug)
    if not discovery:
        return {"error": f"No discovery file for {track}/{slug}"}

    keywords = discovery.get("query_keywords", [])

    # Gather inline chunks from discovery (already have text snippets)
    literary_chunks = discovery.get("rag_literary", [])
    textbook_chunks = discovery.get("rag_chunks", [])

    # Find full literary source files by keywords
    # Extract author/topic keywords from the query_keywords
    search_terms = []
    for kw in keywords[:3]:  # First few are usually topic-specific
        # Take individual words that look like names/topics
        for word in kw.split():
            if len(word) > 4 and word[0].isupper():
                search_terms.append(word.lower())

    literary_files = find_literary_by_keywords(search_terms) if search_terms else []

    return {
        "discovery": discovery,
        "keywords": keywords,
        "literary_chunks": literary_chunks,
        "textbook_chunks": textbook_chunks,
        "literary_files": literary_files,
    }


def get_track_source_summary(track: str) -> dict:
    """Summarize all source material available for a track.

    Returns:
        {
            "track": str,
            "module_count": int,
            "slugs": [str],
            "total_literary_refs": int,
            "total_textbook_refs": int,
            "unique_literary_files": [str],
        }
    """
    slugs = list_discovery_slugs(track)
    total_lit = 0
    total_text = 0
    lit_file_stems: set[str] = set()

    for slug in slugs:
        disc = load_discovery(track, slug)
        if not disc:
            continue
        refs = extract_source_refs(disc)
        total_lit += len(refs["literary"])
        total_text += len(refs["textbook"])

        # Track unique literary source files referenced
        for chunk in disc.get("rag_literary", []):
            cid = chunk.get("chunk_id", "")
            # chunk_id prefix is a hash, but text field might mention the source
            text = chunk.get("text", "")[:200]
            if text:
                lit_file_stems.add(cid.split("_")[0] if "_" in cid else cid)

    return {
        "track": track,
        "module_count": len(slugs),
        "slugs": slugs,
        "total_literary_refs": total_lit,
        "total_textbook_refs": total_text,
        "unique_source_hashes": sorted(lit_file_stems),
    }
