"""Canonical filesystem paths for Open Model Data components and datasets (#6321).

Centralizes path resolution to prevent hardcoded directory drift, obsolete dataset
poisoning, and fragmented component layouts.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Base Open Model Data directory
OPEN_MODEL_DATA_DIR = REPO_ROOT / "data" / "projects" / "open_model_data"

# Modular components (active curation)
COMPONENTS_DIR = OPEN_MODEL_DATA_DIR / "components"
DECOLONIZATION_DIR = COMPONENTS_DIR / "decolonization"
IDIOMS_DIR = COMPONENTS_DIR / "idioms"
GRAMMAR_DIR = COMPONENTS_DIR / "grammar"
TEXTBOOKS_DIR = COMPONENTS_DIR / "textbooks"
DIALECTS_DIR = COMPONENTS_DIR / "dialects"

# Verified releases (production-grade)
RELEASE_DIR = OPEN_MODEL_DATA_DIR / "release"
CORRECTION_PROTECTION_DIR = RELEASE_DIR / "correction_protection_v1"

# Archived and quarantined datasets (DO NOT USE for active training/replay)
ARCHIVE_DIR = OPEN_MODEL_DATA_DIR / "archive"
ARCHIVED_ULDR_V1_DIR = ARCHIVE_DIR / "uldr_v1_production"
QUARANTINED_HISTORICAL_DIR = ARCHIVE_DIR / "quarantined_historical"

# Contracts & Schemas
CONTRACTS_DIR = OPEN_MODEL_DATA_DIR / "contracts"


def ensure_component_directories() -> None:
    """Ensure all modular component directories exist."""
    for path in (
        DECOLONIZATION_DIR,
        IDIOMS_DIR,
        GRAMMAR_DIR,
        TEXTBOOKS_DIR,
        DIALECTS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def is_archived_or_quarantined_path(path: Path | str | None) -> bool:
    """Return True if path is within the archive or quarantined directories."""
    if path is None:
        return False
    try:
        resolved = Path(path).resolve()
        resolved.relative_to(ARCHIVE_DIR.resolve())
        return True
    except (ValueError, RuntimeError):
        return False


def assert_not_archived_path(path: Path | str | None, context: str = "dataset operation") -> None:
    """Raise ValueError if path is within the archive or quarantined directory."""
    if is_archived_or_quarantined_path(path):
        raise ValueError(
            f"Prohibited {context} on archived/quarantined path: {path}. "
            "Archived datasets in open_model_data/archive/ are quarantined and strictly prohibited "
            "from replay ingestion, active training, or overwritten generation outputs (#6321)."
        )
