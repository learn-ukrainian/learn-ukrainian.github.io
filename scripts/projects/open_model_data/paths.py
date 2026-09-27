"""Canonical registry and managed-artifact bases for Open Model Data (#8809)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_OPEN_MODEL_DATA_DIR = REPO_ROOT / "registry" / "projects" / "open_model_data"
ARTIFACT_OPEN_MODEL_DATA_DIR = REPO_ROOT / "data" / "projects" / "open_model_data"

REGISTRY_COMPONENTS_DIR = REGISTRY_OPEN_MODEL_DATA_DIR / "components"
ARTIFACT_COMPONENTS_DIR = ARTIFACT_OPEN_MODEL_DATA_DIR / "components"
REGISTRY_DECOLONIZATION_DIR = REGISTRY_COMPONENTS_DIR / "decolonization"
ARTIFACT_DECOLONIZATION_DIR = ARTIFACT_COMPONENTS_DIR / "decolonization"
REGISTRY_IDIOMS_DIR = REGISTRY_COMPONENTS_DIR / "idioms"
ARTIFACT_IDIOMS_DIR = ARTIFACT_COMPONENTS_DIR / "idioms"
REGISTRY_GRAMMAR_DIR = REGISTRY_COMPONENTS_DIR / "grammar"
ARTIFACT_GRAMMAR_DIR = ARTIFACT_COMPONENTS_DIR / "grammar"
REGISTRY_TEXTBOOKS_DIR = REGISTRY_COMPONENTS_DIR / "textbooks"
ARTIFACT_TEXTBOOKS_DIR = ARTIFACT_COMPONENTS_DIR / "textbooks"
REGISTRY_DIALECTS_DIR = REGISTRY_COMPONENTS_DIR / "dialects"
ARTIFACT_DIALECTS_DIR = ARTIFACT_COMPONENTS_DIR / "dialects"

REGISTRY_RELEASE_DIR = REGISTRY_OPEN_MODEL_DATA_DIR / "release"
ARTIFACT_RELEASE_DIR = ARTIFACT_OPEN_MODEL_DATA_DIR / "release"
REGISTRY_CORRECTION_PROTECTION_DIR = REGISTRY_RELEASE_DIR / "correction_protection_v1"
ARTIFACT_CORRECTION_PROTECTION_DIR = ARTIFACT_RELEASE_DIR / "correction_protection_v1"

REGISTRY_ARCHIVE_DIR = REGISTRY_OPEN_MODEL_DATA_DIR / "archive"
ARTIFACT_ARCHIVE_DIR = ARTIFACT_OPEN_MODEL_DATA_DIR / "archive"
REGISTRY_ARCHIVED_ULDR_V1_DIR = REGISTRY_ARCHIVE_DIR / "uldr_v1_production"
ARTIFACT_ARCHIVED_ULDR_V1_DIR = ARTIFACT_ARCHIVE_DIR / "uldr_v1_production"
REGISTRY_QUARANTINED_HISTORICAL_DIR = REGISTRY_ARCHIVE_DIR / "quarantined_historical"
ARTIFACT_QUARANTINED_HISTORICAL_DIR = ARTIFACT_ARCHIVE_DIR / "quarantined_historical"

CONTRACTS_DIR = REGISTRY_OPEN_MODEL_DATA_DIR / "contracts"


def ensure_component_directories() -> None:
    """Ensure registry-side component directories exist."""
    for path in (
        REGISTRY_DECOLONIZATION_DIR,
        REGISTRY_IDIOMS_DIR,
        REGISTRY_GRAMMAR_DIR,
        REGISTRY_TEXTBOOKS_DIR,
        REGISTRY_DIALECTS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def is_archived_or_quarantined_path(path: Path | str | None) -> bool:
    """Return whether a path is inside either archive base."""
    if path is None:
        return False
    try:
        resolved = Path(path).resolve()
        return any(
            resolved == base.resolve() or base.resolve() in resolved.parents
            for base in (REGISTRY_ARCHIVE_DIR, ARTIFACT_ARCHIVE_DIR)
        )
    except (ValueError, RuntimeError):
        return False


def assert_not_archived_path(path: Path | str | None, context: str = "dataset operation") -> None:
    """Reject active work on archive paths in either storage base."""
    if is_archived_or_quarantined_path(path):
        raise ValueError(
            f"Prohibited {context} on archived/quarantined path: {path}. "
            "Archived datasets in open_model_data/archive/ are quarantined and strictly prohibited "
            "from replay ingestion, active training, or overwritten generation outputs (#6321)."
        )
