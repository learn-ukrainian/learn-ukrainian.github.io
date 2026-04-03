"""Configuration for the wiki compiler."""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WIKI_DIR = PROJECT_ROOT / "wiki"
WIKI_STATE_DIR = WIKI_DIR / ".state"
PROMPTS_DIR = Path(__file__).parent / "prompts"

# Source data on Google Drive
GDRIVE_DATA = Path.home() / (
    "Library/CloudStorage/GoogleDrive-krisztian.koos@gmail.com"
    "/My Drive/Projects/learn-ukrainian-data"
)
LITERARY_DIR = GDRIVE_DATA / "literary_texts"
TEXTBOOK_CHUNKS_DIR = GDRIVE_DATA / "textbook_chunks"
TEXTBOOK_PDFS_DIR = GDRIVE_DATA / "textbooks"
DICT_DIR = GDRIVE_DATA  # grinchenko/, sum11/, frazeolohichnyi/ etc.

# Curriculum data (local repo)
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"

# ── Gemini ─────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-pro"

# ── Wiki structure ─────────────────────────────────────────────────
WIKI_DOMAINS = [
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

# Track → which wiki domains it reads
TRACK_DOMAINS: dict[str, list[str]] = {
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
    "lit-doc": ["literature/works", "figures"],
    "lit-crimea": ["literature/works", "figures", "periods"],
    "oes": ["linguistics/oes", "periods"],
    "ruth": ["linguistics/ruthenian", "periods"],
}

# Seminar tracks (ordered by build priority)
SEMINAR_TRACKS = [
    "folk", "hist", "bio", "istorio",
    "lit", "lit-essay", "lit-war", "lit-hist-fic", "lit-youth",
    "lit-fantastika", "lit-humor", "lit-drama", "lit-doc", "lit-crimea",
    "oes", "ruth",
]
