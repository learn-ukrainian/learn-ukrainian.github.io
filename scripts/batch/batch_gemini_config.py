"""
Configuration for Gemini Batch Runner.
Defines tracks, phases, templates, and validation rules.

Module numbering source of truth: curriculum/l2-uk-en/curriculum.yaml
Module N = levels.{track}.modules[N-1] (1-indexed position in the array).
"""

from pathlib import Path

import yaml
from slug_utils import review_path as _review_path
from slug_utils import status_path as _status_path
from slug_utils import to_bare_slug

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"
CURRICULUM_YAML = CURRICULUM_DIR / "curriculum.yaml"
PLANS_DIR = CURRICULUM_DIR / "plans"
PHASES_DIR = PROJECT_ROOT / "claude_extensions" / "phases" / "gemini"
QUICK_REF_DIR = PROJECT_ROOT / "claude_extensions" / "quick-ref"

# Model Tiering — Gemini
FLASH_MODEL = "gemini-3-flash-preview"
PRO_MODEL = "gemini-3.1-pro-preview"

# Model Tiering — Claude (used by build_module_v5.py --use-claude phases)
# Change these to switch models across the entire pipeline without touching CLI flags.
# Research:      seminar tracks → Opus, core tracks → Sonnet
# Content:       always Opus (quality content generation)
# Activities:    seminar tracks → Opus, core tracks → Sonnet
# Final review:  always Opus (deep semantic QA)
CLAUDE_SONNET = "claude-sonnet-4-6"
CLAUDE_OPUS   = "claude-opus-4-6"

CLAUDE_MODEL_CORE_RESEARCH    = CLAUDE_SONNET   # Research, core tracks
CLAUDE_MODEL_CORE_CONTENT     = CLAUDE_OPUS     # Content, core tracks
CLAUDE_MODEL_CORE_ACTIVITIES  = CLAUDE_SONNET   # Activities, core tracks
CLAUDE_MODEL_SEMINAR_RESEARCH   = CLAUDE_OPUS   # Research, seminar tracks
CLAUDE_MODEL_SEMINAR_CONTENT    = CLAUDE_OPUS   # Content, seminar tracks
CLAUDE_MODEL_SEMINAR_ACTIVITIES = CLAUDE_OPUS   # Activities, seminar tracks
CLAUDE_MODEL_FINAL_REVIEW       = CLAUDE_OPUS   # Final review, all tracks

# Seminar tracks get research (phase 0) + review (phase 5)
SEMINAR_TRACKS = {
    "bio", "hist", "istorio", "lit", "oes", "ruth",
    "lit-essay", "lit-hist-fic", "lit-fantastika", "lit-war", "lit-humor", "lit-youth",
}

# Professional tracks: need external research (not covered by State Standard)
# Use research-pro.md (terminology, ДСТУ norms, authentic examples) not research-seminar.md
PRO_TRACKS = {"b2-pro", "c1-pro"}

# --- Shared template sets (DRY: defined once, reused across all track configs) ---
_COMMON_TEMPLATES = {
    2: PHASES_DIR / "content.md",
    3: PHASES_DIR / "activities.md",
    5: PHASES_DIR / "review-legacy.md",
    "fix": PHASES_DIR / "fix.md",
    "fix-content": PHASES_DIR / "fix-content.md",
    "fix-activities": PHASES_DIR / "fix-activities.md",
}
SEMINAR_TEMPLATES = {0: PHASES_DIR / "research-seminar-v0.md", **_COMMON_TEMPLATES}
CORE_TEMPLATES = {1: PHASES_DIR / "research-core.md", **_COMMON_TEMPLATES}


def _seminar(quick_ref_name: str) -> dict:
    """Build a seminar track config. Only quick_ref differs between tracks."""
    return {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": SEMINAR_TEMPLATES,
        "quick_ref": QUICK_REF_DIR / f"{quick_ref_name}.md",
        "validation_phases": [2, 3],
    }


def _core(quick_ref_name: str) -> dict:
    """Build a core track config. Only quick_ref differs between tracks."""
    return {
        "type": "core",
        "model": PRO_MODEL,
        "phases": [1, 2, 3, 5],
        "templates": CORE_TEMPLATES,
        "quick_ref": QUICK_REF_DIR / f"{quick_ref_name}.md",
        "validation_phases": [2, 3],
    }


# Track definitions
TRACK_CONFIGS = {
    # --- Seminar tracks (Pro Model MANDATORY) ---
    "bio":            _seminar("BIO"),
    "hist":           _seminar("HIST"),
    "istorio":        _seminar("ISTORIO"),
    "lit":            _seminar("LIT"),
    "lit-essay":      _seminar("LIT"),
    "lit-hist-fic":   _seminar("LIT"),
    "lit-fantastika": _seminar("LIT"),
    "lit-war":        _seminar("LIT"),
    "lit-humor":      _seminar("LIT"),
    "lit-youth":      _seminar("LIT"),
    "oes":            _seminar("OES"),
    "ruth":           _seminar("RUTH"),
    # --- Core tracks (all Pro — flash too weak for quality content) ---
    "a1": _core("A1"),
    "a2": _core("A2"),
    "b1": _core("B1"),
    "b2": _core("B2"),
    "c1": _core("C1"),
    "c2": _core("C2"),
}

# Default for unlisted tracks
DEFAULT_CONFIG = {
    "type": "core",
    "model": FLASH_MODEL,
    "phases": [2, 3, 5],
    "templates": _COMMON_TEMPLATES,
    "quick_ref": None,
    "validation_phases": [2, 3],
}

# --- Module Index (loaded once from curriculum.yaml) ---

_module_index_cache = {}


def _load_curriculum():
    """Load curriculum.yaml once, cache the result."""
    if not _module_index_cache:
        data = yaml.safe_load(CURRICULUM_YAML.read_text(encoding="utf-8"))
        for level, info in data.get("levels", {}).items():
            modules = info.get("modules", [])
            # num_to_slug: 1-indexed position → slug
            # slug_to_num: slug → 1-indexed position
            num_to_slug = {}
            slug_to_num = {}
            for i, entry in enumerate(modules):
                num = i + 1
                # Core tracks have "39-buying-tickets" format, extract bare slug
                slug = to_bare_slug(entry)
                num_to_slug[num] = slug
                slug_to_num[slug] = num
            _module_index_cache[level] = {
                "num_to_slug": num_to_slug,
                "slug_to_num": slug_to_num,
                "total": len(modules),
                "raw_entries": modules,
            }
    return _module_index_cache


def get_module_index(track: str) -> dict:
    """Get the module index for a track.

    Returns dict with:
      num_to_slug: {1: 'knyahynia-olha', 2: 'kniaz-sviatoslav', ...}
      slug_to_num: {'knyahynia-olha': 1, 'kniaz-sviatoslav': 2, ...}
      total: int
      raw_entries: ['knyahynia-olha', 'kniaz-sviatoslav', ...] (as in curriculum.yaml)
    """
    idx = _load_curriculum()
    if track not in idx:
        raise ValueError(
            f"Track '{track}' not found in curriculum.yaml. "
            f"Available: {sorted(idx.keys())}"
        )
    return idx[track]


def slug_for_num(track: str, num: int) -> str:
    """Get slug for a module number. Raises ValueError if not found."""
    idx = get_module_index(track)
    if num not in idx["num_to_slug"]:
        raise ValueError(
            f"Module {num} not found in {track} "
            f"(has {idx['total']} modules, range 1-{idx['total']})"
        )
    return idx["num_to_slug"][num]


def num_for_slug(track: str, slug: str) -> int:
    """Get module number for a slug. Raises ValueError if not found."""
    idx = get_module_index(track)
    if slug not in idx["slug_to_num"]:
        raise ValueError(f"Slug '{slug}' not found in {track}")
    return idx["slug_to_num"][slug]


def get_track_config(track_name: str) -> dict:
    """Get config for a track, with quick_ref auto-detection."""
    config = TRACK_CONFIGS.get(track_name, DEFAULT_CONFIG).copy()

    # Auto-detect quick_ref if not set or file missing
    if not config.get("quick_ref") or not config["quick_ref"].exists():
        for variant in [track_name.upper(), track_name, track_name.lower()]:
            qr_path = QUICK_REF_DIR / f"{variant}.md"
            if qr_path.exists():
                config["quick_ref"] = qr_path
                break

    return config


def get_module_paths(track: str, slug: str) -> dict:
    """Resolve all file paths for a module. All tracks use bare slugs."""
    bare_slug = to_bare_slug(slug)
    track_dir = CURRICULUM_DIR / track
    plans_track_dir = PLANS_DIR / track

    return {
        "md": track_dir / f"{bare_slug}.md",
        "meta": track_dir / "meta" / f"{bare_slug}.yaml",
        "activities": track_dir / "activities" / f"{bare_slug}.yaml",
        "vocabulary": track_dir / "vocabulary" / f"{bare_slug}.yaml",
        "plan": plans_track_dir / f"{bare_slug}.yaml",
        "research": track_dir / "research" / f"{bare_slug}-research.md",
        "orchestration": track_dir / "orchestration" / bare_slug,
        "review": _review_path(track_dir, bare_slug),
        "status": _status_path(track_dir, bare_slug),
    }
