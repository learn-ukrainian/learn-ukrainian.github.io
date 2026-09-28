"""Canonical registry and managed-artifact bases for Open Model Data (#8809)."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_OPEN_MODEL_DATA_DIR = REPO_ROOT / "registry" / "projects" / "open_model_data"
ARTIFACT_OPEN_MODEL_DATA_DIR = REPO_ROOT / "data" / "projects" / "open_model_data"
LOGICAL_OPEN_MODEL_PREFIX = "data/projects/open_model_data"
REGISTRY_OPEN_MODEL_PREFIX = "registry/projects/open_model_data"

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
# Successor of the pre-migration gemma probe runner. Filled after the routed
# file is frozen for this commit; tests require these to match the file bytes.
GEMMA_PROBE_RUNNER_BYTES = 62872
GEMMA_PROBE_RUNNER_SHA256 = "617daf6dadcbbd6831e019ade8e6393a85fbdf2d9ca6af7c7ec92cf5b763ff57"


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


@lru_cache(maxsize=1)
def open_model_classes() -> dict[str, str]:
    """Map each open-model relative path to its frozen K or A class."""
    table = REPO_ROOT / "registry/artifacts/classification-v1.tsv"
    classes: dict[str, str] = {}
    with table.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            logical = row.get("path", "")
            marker = LOGICAL_OPEN_MODEL_PREFIX + "/"
            if logical.startswith(marker) and row.get("class") in {"K", "A"}:
                classes[logical[len(marker) :]] = row["class"]
    if not classes:
        raise ValueError(f"open-model classification rows missing from {table}")
    return classes


def open_model_class(relative: str) -> str | None:
    """Return K or A when the relative path, or a single-class directory, is classified."""
    classes = open_model_classes()
    normalized = relative.strip("/")
    if not normalized:
        return None
    found = classes.get(normalized)
    if found is not None:
        return found
    prefix = normalized + "/"
    child_classes = {classes[item] for item in classes if item.startswith(prefix)}
    if child_classes == {"K"}:
        return "K"
    if child_classes == {"A"}:
        return "A"
    return None


def _open_model_split(text: str) -> tuple[str, str, str] | None:
    """Return the path head, matched prefix, and open-model relative tail."""
    for marker in (LOGICAL_OPEN_MODEL_PREFIX, REGISTRY_OPEN_MODEL_PREFIX):
        token = marker + "/"
        index = text.find(token)
        if index != -1:
            return text[:index], marker, text[index + len(token) :]
        if text == marker or text.endswith("/" + marker):
            start = text.rfind(marker)
            return text[:start], marker, ""
    return None


def resolve_open_model_path(path: str | Path, *, repo: Path | None = None) -> Path:
    """Resolve a logical or physical open-model path to its classified location.

    K members live under ``registry/projects/open_model_data``. A members stay
    under ``data/projects/open_model_data``. Logical ``data/`` strings recorded
    in frozen contracts are unchanged; only the filesystem location moves.
    Mixed directories keep the caller's prefix. Paths outside the tree join
    ``repo`` when they are relative.
    """
    raw = Path(path)
    split = _open_model_split(raw.as_posix())
    if split is None:
        if raw.is_absolute() or repo is None:
            return raw
        return repo / raw
    head, marker, relative = split
    klass = open_model_class(relative)
    if klass == "K":
        chosen = REGISTRY_OPEN_MODEL_PREFIX
    elif klass == "A":
        chosen = LOGICAL_OPEN_MODEL_PREFIX
    else:
        chosen = marker
    tail = f"{chosen}/{relative}" if relative else chosen
    if raw.is_absolute() or head not in {"", "."}:
        prefix = head
        if prefix and not prefix.endswith("/"):
            prefix = prefix + "/"
        return Path(f"{prefix}{tail}")
    return (repo if repo is not None else REPO_ROOT) / tail


def assert_not_archived_path(path: Path | str | None, context: str = "dataset operation") -> None:
    """Reject active work on archive paths in either storage base."""
    if is_archived_or_quarantined_path(path):
        raise ValueError(
            f"Prohibited {context} on archived/quarantined path: {path}. "
            "Archived datasets in open_model_data/archive/ are quarantined and strictly prohibited "
            "from replay ingestion, active training, or overwritten generation outputs (#6321)."
        )
