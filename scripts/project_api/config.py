"""Curriculum configuration for the product half of the Monitor API.

Levels and seminar tracks come from ``curriculum/l2-uk-en/curriculum.yaml``.
Roots, stores and the server address stay in the machinery
``scripts.api.config``.
"""

from pathlib import Path
from typing import Any, cast

import yaml
from lu_machinery.api.config import LIVE_REPO_ROOT, PROJECT_ROOT

# Textbook PDFs live under the resolved bulk raw-source root, never a
# repository symlink (#8803; docs/runbooks/storage-topology.md).
# Resolved on first use: curriculum_state imports this module before it has
# finished loading the product wrapper.


def __getattr__(name: str) -> Path:
    if name != "TEXTBOOKS_DIR":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .curriculum_state import monitor_surface  # noqa: PLC0415

    value = cast(Path, monitor_surface.textbook_pdfs_dir())
    globals()["TEXTBOOKS_DIR"] = value
    return value


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
                return cast("dict[str, Any] | None", data["levels"])
        except Exception:
            pass
    return None


def load_seminar_track_ids(repo_root: Path | None = None) -> set[str]:
    """Derive active seminar track IDs from curriculum.yaml manifest."""
    return _seminar_track_ids_from_levels(_read_manifest_levels(repo_root))


def _seminar_track_ids_from_levels(levels: dict[str, Any] | None) -> set[str]:
    if levels is not None:
        return {track_id for track_id, cfg in levels.items() if isinstance(cfg, dict) and cfg.get("type") == "track"}
    # Fallback if manifest fails to load
    return {
        "hist",
        "istorio",
        "bio",
        "lit",
        "lit-essay",
        "lit-hist-fic",
        "lit-fantastika",
        "lit-war",
        "lit-humor",
        "lit-youth",
        "lit-drama",
        "oes",
        "ruth",
        "folk",
    }


def load_levels(repo_root: Path | None = None) -> list[dict[str, str]]:
    """Derive active levels and tracks list from curriculum.yaml manifest."""
    return _levels_from_manifest(_read_manifest_levels(repo_root))


def _levels_from_manifest(levels: dict[str, Any] | None) -> list[dict[str, str]]:
    if levels is not None:
        return [
            {
                "id": track_id,
                "name": _KNOWN_LEVEL_NAMES.get(track_id, f"{track_id.upper()} - {track_id}"),
                "path": track_id,
            }
            for track_id in levels
        ]
    return [{"id": k, "name": v, "path": k} for k, v in _KNOWN_LEVEL_NAMES.items()]


# Share one manifest read during import; explicit helper calls stay fresh.
_manifest_levels = _read_manifest_levels()
LEVELS = _levels_from_manifest(_manifest_levels)

# Seminar tracks (require Phase 0 research) — derived from curriculum.yaml
SEMINAR_TRACK_IDS = _seminar_track_ids_from_levels(_manifest_levels)
del _manifest_levels
