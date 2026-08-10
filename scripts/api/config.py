"""Configuration for the playground API."""

import os
from pathlib import Path
from typing import Any

import yaml

# Project root is the immutable code snapshot when the API is release-served.
# Mutable data remains reachable through the release's explicit symlinks.
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _live_repo_root() -> Path:
    """Return the checkout Git operations and child tools must target."""
    configured = os.environ.get("LEARN_UK_REPO_ROOT")
    if not configured:
        return PROJECT_ROOT
    supplied = Path(configured).expanduser()
    if not supplied.is_absolute():
        raise RuntimeError("LEARN_UK_REPO_ROOT must be an absolute path")
    candidate = supplied.resolve()
    if not candidate.is_dir() or not (candidate / ".git").exists():
        raise RuntimeError(f"LEARN_UK_REPO_ROOT is not a Git checkout: {candidate}")
    return candidate


LIVE_REPO_ROOT = _live_repo_root()

# Curriculum paths
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"

# Message broker database
MESSAGE_DB = Path(
    os.environ.get(
        "AB_DB_PATH",
        str(PROJECT_ROOT / ".mcp" / "servers" / "message-broker" / "messages.db"),
    )
)

# Dashboards directory (for static file serving)
DASHBOARDS_DIR = PROJECT_ROOT / "dashboards"

_KNOWN_LEVEL_NAMES = {
    "a1": "A1 - Beginner",
    "a2": "A2 - Elementary",
    "b1": "B1 - Intermediate",
    "b2": "B2 - Upper Intermediate",
    "c1": "C1 - Advanced",
    "c2": "C2 - Mastery",
    "hist": "HIST - History Track",
    "istorio": "ISTORIO - History Track",
    "bio": "BIO - Biography Track",
    "lit": "LIT - Literature Track",
    "lit-essay": "LIT-ESSAY - Essays",
    "lit-hist-fic": "LIT-HIST-FIC - Historical Fiction",
    "lit-fantastika": "LIT-FANTASTIKA - Fantasy/Sci-Fi",
    "lit-war": "LIT-WAR - War Literature",
    "lit-humor": "LIT-HUMOR - Humor",
    "lit-youth": "LIT-YOUTH - Youth & YA",
    "lit-doc": "LIT-DOC - Fact & Testimony",
    "lit-drama": "LIT-DRAMA - Modern Stage",
    "lit-crimea": "LIT-CRIMEA - Voices of Crimea",
    "oes": "OES - Old East Slavic",
    "ruth": "RUTH - Ruthenian",
    "folk": "FOLK - Folk Culture",
}


def _read_manifest_levels(repo_root: Path | None = None) -> dict[str, Any] | None:
    """Read levels mapping directly from curriculum.yaml manifest."""
    root = repo_root or LIVE_REPO_ROOT
    manifest_path = root / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    if not manifest_path.exists():
        manifest_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    if manifest_path.exists():
        try:
            data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("levels"), dict):
                return data["levels"]
        except Exception:
            pass
    return None


def load_seminar_track_ids(repo_root: Path | None = None) -> set[str]:
    """Derive active seminar track IDs from curriculum.yaml manifest."""
    levels = _read_manifest_levels(repo_root)
    if levels is not None:
        return {
            track_id
            for track_id, cfg in levels.items()
            if isinstance(cfg, dict) and cfg.get("type") == "track"
        }
    # Fallback if manifest fails to load
    return {
        "hist", "istorio", "bio", "lit", "lit-essay", "lit-hist-fic",
        "lit-fantastika", "lit-war", "lit-humor", "lit-youth", "lit-drama",
        "oes", "ruth", "folk",
    }


def load_levels(repo_root: Path | None = None) -> list[dict[str, str]]:
    """Derive active levels and tracks list from curriculum.yaml manifest."""
    levels = _read_manifest_levels(repo_root)
    if levels is not None:
        return [
            {
                "id": track_id,
                "name": _KNOWN_LEVEL_NAMES.get(track_id, f"{track_id.upper()} - {track_id}"),
                "path": track_id,
            }
            for track_id in levels
        ]
    return [
        {"id": k, "name": v, "path": k}
        for k, v in _KNOWN_LEVEL_NAMES.items()
    ]



# Levels configuration — derived from curriculum.yaml
LEVELS = load_levels()

# Seminar tracks (require Phase 0 research) — derived from curriculum.yaml
SEMINAR_TRACK_IDS = load_seminar_track_ids()

# Batch state directory
BATCH_STATE_DIR = PROJECT_ROOT / "batch_state"

# Server settings
API_HOST = "127.0.0.1"  # nosec B104 — bind to localhost only
API_PORT = 8765

