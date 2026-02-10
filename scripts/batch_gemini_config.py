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

# Seminar tracks get research (phase 0) + review (phase 5)
SEMINAR_TRACKS = {
    "c1-bio", "b2-hist", "c1-hist", "lit", "oes", "ruth",
    "lit-essay", "lit-hist-fic", "lit-fantastika", "lit-war", "lit-humor", "lit-juvenile",
}

# Track definitions
TRACK_CONFIGS = {
    # --- Seminar tracks (6 phases) ---
    "c1-bio": {
        "type": "seminar",
        "phases": [0, 2, 3, 5],  # Research, Content, Activities, Review
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
        "validation_phases": [2, 3],  # Phases that trigger audit
    },
    "b2-hist": {
        "type": "seminar",
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
        "quick_ref": QUICK_REF_DIR / "B2-HIST.md",
        "validation_phases": [2, 3],
    },
    "c1-hist": {
        "type": "seminar",
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
    # --- Literature variant tracks (seminar, inherit LIT config) ---
    "lit-essay": {
        "type": "seminar",
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
    "lit-juvenile": {
        "type": "seminar",
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
    # --- Core tracks (4 phases) ---
    "a1": {
        "type": "core",
        "phases": [2, 3, 5],  # Content, Activities, Review
        "templates": {
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
        "phases": [2, 3, 5],
        "templates": {
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
}

# Default for unlisted tracks
DEFAULT_CONFIG = {
    "type": "core",
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
    """Resolve all file paths for a module, handling numeric prefixes."""
    track_dir = CURRICULUM_DIR / track

    # Try direct match first, then glob for numeric prefix
    md_path = track_dir / f"{slug}.md"
    file_slug = slug  # slug used in filenames

    if not md_path.exists():
        matches = list(track_dir.glob(f"*-{slug}.md"))
        if matches:
            md_path = matches[0]
            file_slug = md_path.stem  # e.g., "01-the-cyrillic-code-i"

    # Plans: core tracks use numbered prefix, seminar tracks use bare slug
    is_seminar = track in SEMINAR_TRACKS
    plan_slug = slug if is_seminar else file_slug
    plan_path = PLANS_DIR / track / f"{plan_slug}.yaml"

    # Seminar tracks: meta/activities/vocabulary use bare slug
    # Core tracks with numeric prefix: use file_slug
    yaml_slug = slug if is_seminar else file_slug

    return {
        "md": md_path,
        "meta": track_dir / "meta" / f"{yaml_slug}.yaml",
        "activities": track_dir / "activities" / f"{yaml_slug}.yaml",
        "vocabulary": track_dir / "vocabulary" / f"{yaml_slug}.yaml",
        "plan": plan_path,
        "research": track_dir / "research" / f"{slug}-research.md",
        "orchestration": track_dir / "orchestration" / slug,
        "review": _review_path(track_dir, slug),
        "status": _status_path(track_dir, slug),
    }
