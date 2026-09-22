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
