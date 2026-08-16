"""Configuration for the wiki compiler.

Supports ALL tracks: core levels (A1-C2) and seminar tracks.
Each track maps to wiki domains where its articles live.
"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WIKI_DIR = PROJECT_ROOT / "wiki"
WIKI_STATE_DIR = WIKI_DIR / ".state"
PROMPTS_DIR = Path(__file__).parent / "prompts"


def _import_resolve_bulk_root():
    """Load the shared bulk-root resolver (project root or scripts/ on path)."""
    try:
        from scripts.storage.topology import (
            resolve_bulk_root,
            unresolved_bulk_placeholder,
        )
    except ImportError:  # pragma: no cover - legacy ``scripts/``-on-path imports
        from storage.topology import (  # type: ignore
            resolve_bulk_root,
            unresolved_bulk_placeholder,
        )
    return resolve_bulk_root, unresolved_bulk_placeholder


def _resolve_gdrive_data_dir() -> Path:
    """Resolve the bulk raw-source root for rebuild consumers.

    Name retained as ``GDRIVE_DATA`` for call-site compatibility. The single
    source of truth is ``scripts.storage.topology.resolve_bulk_root``:

    1. ``LU_BULK_ROOT`` when marker-valid
    2. Marker-valid Windows ``UkrainianData`` SMB mirror
       (``…/raw-sources/learn-ukrainian-data``)
    3. Marker-valid Google Drive File Provider path
       (``LU_GDRIVE_DATA`` or CloudStorage glob)
    4. Non-existent placeholder so imports still succeed when neither root is
       present (tests/CI without mounts)

    Required markers: ``literary_texts/`` and ``textbook_chunks/``.
    See ``docs/runbooks/storage-topology.md``.
    """
    resolve_bulk_root, unresolved_bulk_placeholder = _import_resolve_bulk_root()
    result = resolve_bulk_root()
    if result.available and result.path is not None:
        return result.path
    # Import-safe placeholder — never a real path.
    return unresolved_bulk_placeholder()


# Bulk raw-source root (SMB preferred, Drive fallback). Legacy name GDRIVE_DATA.
GDRIVE_DATA = _resolve_gdrive_data_dir()
LITERARY_DIR = GDRIVE_DATA / "literary_texts"
TEXTBOOK_CHUNKS_DIR = GDRIVE_DATA / "textbook_chunks"
TEXTBOOK_PDFS_DIR = GDRIVE_DATA / "textbooks"
DICT_DIR = GDRIVE_DATA  # grinchenko/, sum11/, frazeolohichnyi/ etc.

# Curriculum data (local repo)
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"

# ── Gemini ─────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-3.1-pro-preview"

# ── Wiki structure ─────────────────────────────────────────────────
WIKI_DOMAINS = [
    # Core level domains
    "pedagogy/a1",
    "grammar/a2",
    "grammar/b1",
    "grammar/b2",
    "academic/c1",
    "mastery/c2",
    # Seminar domains
    "periods",
    "figures",
    "literature/movements",
    "literature/works",
    "literature/teaching",
    "linguistics/oes",
    "linguistics/ruthenian",
    "historiography",
    "folk",
]

# Track → which wiki domains it READS (for context injection)
TRACK_DOMAINS: dict[str, list[str]] = {
    # Core levels — each reads its own domain
    "a1": ["pedagogy/a1"],
    "a2": ["grammar/a2", "pedagogy/a1"],  # A2 can also read A1 pedagogy
    "b1": ["grammar/b1", "grammar/a2"],
    "b2": ["grammar/b2", "grammar/b1"],
    "c1": ["academic/c1", "grammar/b2"],
    "c2": ["mastery/c2", "academic/c1"],
    # Seminar tracks
    "folk": ["folk"],
    "hist": ["periods", "figures", "historiography"],
    "bio": ["figures", "periods"],
    "istorio": ["historiography", "periods"],
    "lit": ["literature/movements", "literature/works", "literature/teaching", "figures"],
    "lit-essay": ["literature/movements", "literature/works", "figures"],
    "lit-war": ["literature/works", "figures", "periods"],
    "lit-hist-fic": ["literature/works", "figures", "periods"],
    "lit-youth": ["literature/works", "figures"],
    "lit-fantastika": ["literature/works", "figures"],
    "lit-humor": ["literature/works", "figures"],
    "lit-drama": ["literature/works", "figures"],
    # lit-doc and lit-crimea were merged into other lit-* tracks; not in curriculum.yaml.
    "oes": ["linguistics/oes", "periods"],
    "ruth": ["linguistics/ruthenian", "periods"],
}

# Track → which wiki domain it WRITES TO (for compilation)
TRACK_WRITE_DOMAIN: dict[str, str] = {
    # Core levels
    "a1": "pedagogy/a1",
    "a2": "grammar/a2",
    "b1": "grammar/b1",
    "b2": "grammar/b2",
    "c1": "academic/c1",
    "c2": "mastery/c2",
    # Seminars use _get_domain() logic in compile.py (per-slug mapping)
}

# Track → which compilation prompt to use
TRACK_PROMPT: dict[str, str] = {
    "a1": "compile_pedagogy_brief.md",
    "a2": "compile_grammar_brief.md",
    "b1": "compile_grammar_brief.md",
    "b2": "compile_grammar_brief.md",
    "c1": "compile_academic.md",
    "c2": "compile_academic.md",
    # All seminar tracks use the default
}
DEFAULT_PROMPT = "compile_article.md"

# All supported tracks (ordered by build priority)
# Source of truth: curriculum/l2-uk-en/curriculum.yaml
# Only tracks that exist in curriculum.yaml belong here.
ALL_TRACKS = [
    # Core (priority: A1 first, then A2, then B1+)
    "a1", "a2", "b1", "b2", "c1", "c2",
    # Seminar (priority: FOLK first, then HIST+BIO, then rest)
    "folk", "hist", "bio", "istorio",
    "lit", "lit-essay", "lit-war", "lit-hist-fic", "lit-youth",
    "lit-fantastika", "lit-humor", "lit-drama",
    "oes", "ruth",
    # NOT included: lit-doc, lit-crimea (merged into other lit-* tracks; no longer
    #   in curriculum.yaml). Stale discovery dirs may still exist on disk.
    # NOT included: archived professional tracks, which do not need wiki.
]

# Legacy alias
SEMINAR_TRACKS = ALL_TRACKS[6:]  # Everything after c2
