"""
Configuration for Gemini Batch Runner.
Defines tracks, phases, templates, and validation rules.

Module numbering source of truth: curriculum/l2-uk-en/curriculum.yaml
Module N = levels.{track}.modules[N-1] (1-indexed position in the array).
"""

import re
from pathlib import Path

import yaml

from slug_utils import to_bare_slug, review_path as _review_path, status_path as _status_path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"
CURRICULUM_YAML = CURRICULUM_DIR / "curriculum.yaml"
PLANS_DIR = CURRICULUM_DIR / "plans"
PHASES_DIR = PROJECT_ROOT / "claude_extensions" / "phases" / "gemini"
QUICK_REF_DIR = PROJECT_ROOT / "claude_extensions" / "quick-ref"

# Model Tiering — Gemini
FLASH_MODEL = "gemini-3-flash-preview"
PRO_MODEL = "gemini-3-pro-preview"

# Model Tiering — Claude (used by build_module_v3.py --use-claude phases)
# Change these to switch models across the entire pipeline without touching CLI flags.
# Phase A (research):      seminar tracks → Opus, core tracks → Sonnet
# Phase C (activities):    seminar tracks → Opus, core tracks → Sonnet
# Phase F (final review):  always Opus (deep semantic QA)
CLAUDE_SONNET = "claude-sonnet-4-6"
CLAUDE_OPUS   = "claude-opus-4-6"

CLAUDE_MODEL_CORE_RESEARCH    = CLAUDE_SONNET   # Phase A, core tracks
CLAUDE_MODEL_CORE_ACTIVITIES  = CLAUDE_SONNET   # Phase C, core tracks
CLAUDE_MODEL_SEMINAR_RESEARCH   = CLAUDE_OPUS   # Phase A, seminar tracks
CLAUDE_MODEL_SEMINAR_ACTIVITIES = CLAUDE_OPUS   # Phase C, seminar tracks
CLAUDE_MODEL_FINAL_REVIEW       = CLAUDE_OPUS   # Phase F, all tracks

# Seminar tracks get research (phase 0) + review (phase 5)
SEMINAR_TRACKS = {
    "c1-bio", "hist", "c1-hist", "lit", "oes", "ruth",
    "lit-essay", "lit-hist-fic", "lit-fantastika", "lit-war", "lit-humor", "lit-youth",
}

# Professional tracks: need external research (not covered by State Standard)
# Use phase-A-pro.md (terminology, ДСТУ norms, authentic examples) not phase-A-seminar.md
PRO_TRACKS = {"b2-pro", "c1-pro"}

# Track definitions
TRACK_CONFIGS = {
    # --- Seminar tracks (Pro Model MANDATORY) ---
    "c1-bio": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "C1-BIO.md",
        "validation_phases": [2, 3],
    },
    "hist": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "HIST.md",
        "validation_phases": [2, 3],
    },
    "c1-hist": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "C1-HIST.md",
        "validation_phases": [2, 3],
    },
    "lit": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "LIT.md",
        "validation_phases": [2, 3],
    },
    "lit-essay": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "LIT.md",
        "validation_phases": [2, 3],
    },
    "lit-hist-fic": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "LIT.md",
        "validation_phases": [2, 3],
    },
    "lit-fantastika": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "LIT.md",
        "validation_phases": [2, 3],
    },
    "lit-war": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "LIT.md",
        "validation_phases": [2, 3],
    },
    "lit-humor": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "LIT.md",
        "validation_phases": [2, 3],
    },
    "lit-youth": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "LIT.md",
        "validation_phases": [2, 3],
    },
    "oes": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "OES.md",
        "validation_phases": [2, 3],
    },
    "ruth": {
        "type": "seminar",
        "model": PRO_MODEL,
        "phases": [0, 2, 3, 5],
        "templates": {
            0: PHASES_DIR / "phase-0-research-seminar.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "RUTH.md",
        "validation_phases": [2, 3],
    },
    # --- Core tracks (all Pro — flash too weak for quality content) ---
    "a1": {
        "type": "core",
        "model": PRO_MODEL,
        "phases": [1, 2, 3, 5],
        "templates": {
            1: PHASES_DIR / "phase-1-research-core.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "A1.md",
        "validation_phases": [2, 3],
    },
    "a2": {
        "type": "core",
        "model": PRO_MODEL,
        "phases": [1, 2, 3, 5],
        "templates": {
            1: PHASES_DIR / "phase-1-research-core.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "A2.md",
        "validation_phases": [2, 3],
    },
    "b1": {
        "type": "core",
        "model": PRO_MODEL,
        "phases": [1, 2, 3, 5],
        "templates": {
            1: PHASES_DIR / "phase-1-research-core.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "B1.md",
        "validation_phases": [2, 3],
    },
    "b2": {
        "type": "core",
        "model": PRO_MODEL,
        "phases": [1, 2, 3, 5],
        "templates": {
            1: PHASES_DIR / "phase-1-research-core.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "B2.md",
        "validation_phases": [2, 3],
    },
    "c1": {
        "type": "core",
        "model": PRO_MODEL,
        "phases": [1, 2, 3, 5],
        "templates": {
            1: PHASES_DIR / "phase-1-research-core.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "C1.md",
        "validation_phases": [2, 3],
    },
    "c2": {
        "type": "core",
        "model": PRO_MODEL,
        "phases": [1, 2, 3, 5],
        "templates": {
            1: PHASES_DIR / "phase-1-research-core.md",
            2: PHASES_DIR / "phase-2-content.md",
            3: PHASES_DIR / "phase-3-activities.md",
            5: PHASES_DIR / "phase-5-review.md",
            "fix": PHASES_DIR / "phase-fix.md",
            "fix-content": PHASES_DIR / "phase-fix-content.md",
            "fix-activities": PHASES_DIR / "phase-fix-activities.md",
        },
        "quick_ref": QUICK_REF_DIR / "C2.md",
        "validation_phases": [2, 3],
    },
}

# Default for unlisted tracks
DEFAULT_CONFIG = {
    "type": "core",
    "model": FLASH_MODEL,
    "phases": [2, 3, 5],
    "templates": {
        2: PHASES_DIR / "phase-2-content.md",
        3: PHASES_DIR / "phase-3-activities.md",
        5: PHASES_DIR / "phase-5-review.md",
        "fix": PHASES_DIR / "phase-fix.md",
        "fix-content": PHASES_DIR / "phase-fix-content.md",
        "fix-activities": PHASES_DIR / "phase-fix-activities.md",
    },
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
