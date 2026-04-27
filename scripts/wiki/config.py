"""Configuration for the wiki compiler.

Supports ALL tracks: core levels (A1-C2) and seminar tracks.
Each track maps to wiki domains where its articles live.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WIKI_DIR = PROJECT_ROOT / "wiki"
WIKI_STATE_DIR = WIKI_DIR / ".state"
PROMPTS_DIR = Path(__file__).parent / "prompts"


def _resolve_gdrive_data_dir() -> Path:
    """Resolve the Google Drive data directory path.

    Resolution order:

    1. ``LU_GDRIVE_DATA`` env var — explicit override. Set this in
       ``~/.bash_secrets`` (or wherever you keep per-machine env vars)
       so the path doesn't have to be hardcoded in committed code.
    2. Glob ``~/Library/CloudStorage/GoogleDrive-*/My Drive/Projects/learn-ukrainian-data``
       and return the first existing match. macOS Google Drive Desktop
       creates per-user mount points named ``GoogleDrive-<email>/``;
       globbing avoids hardcoding the email (#1577 Phase 1 Q4 —
       wartime contributor exposure risk).
    3. Fall through to a placeholder Path that does not exist on disk.
       Callers that hit the filesystem will get a clear
       ``FileNotFoundError``; setting ``LU_GDRIVE_DATA`` fixes it.
       Keeping this module-importable even when the mount is absent
       matters for tests / CI that don't have a real GDrive folder.
    """
    explicit = os.environ.get("LU_GDRIVE_DATA")
    if explicit:
        return Path(explicit)

    cloudstorage = Path.home() / "Library" / "CloudStorage"
    if cloudstorage.exists():
        for mount in sorted(cloudstorage.glob("GoogleDrive-*")):
            candidate = mount / "My Drive" / "Projects" / "learn-ukrainian-data"
            if candidate.exists():
                return candidate

    # Unresolved placeholder — never matches a real path. Module import
    # still succeeds; access errors only fire on actual filesystem ops.
    return (
        Path.home()
        / "Library" / "CloudStorage" / "GoogleDrive-UNSET"
        / "My Drive" / "Projects" / "learn-ukrainian-data"
    )


# Source data on Google Drive (resolved at import; override via LU_GDRIVE_DATA)
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
    # NOT included: b2-pro, c1-pro (professional tracks, no wiki needed)
]

# Legacy alias
SEMINAR_TRACKS = ALL_TRACKS[6:]  # Everything after c2
