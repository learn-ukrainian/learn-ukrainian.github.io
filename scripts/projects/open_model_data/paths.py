"""Canonical registry and managed-artifact bases for Open Model Data (#8809)."""

from __future__ import annotations

import csv
import hashlib
import json
import posixpath
from functools import lru_cache
from pathlib import Path
from typing import Any

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

# Quarantine of every old-plan trainable artifact (#9607, plan v3.4.3 PA1).
TOMBSTONE_NAME = "TOMBSTONE.md"
QUARANTINE_INVENTORY_RELATIVE = "quarantine/inventory_v1.json"
QUARANTINE_INVENTORY_PATH = REGISTRY_OPEN_MODEL_DATA_DIR / QUARANTINE_INVENTORY_RELATIVE
QUARANTINE_INVENTORY_SCHEMA = "open_model_quarantine_inventory_v1"
# Inventory storage of sealed files that lie outside the open-model tree.
STRAY_STORAGE = "stray"
# Successor of the pre-migration gemma probe runner. Filled after the routed
# file is frozen for this commit; tests require these to match the file bytes.
GEMMA_PROBE_RUNNER_BYTES = 63112
GEMMA_PROBE_RUNNER_SHA256 = "7d3e12dfb114ce96f14a195c8d8515964c77e125df4b649b9b31989b2e5c8ab6"


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


class QuarantinedArtifactError(ValueError):
    """A loader, packager or uploader was handed a quarantined old-plan artifact (#9607)."""


@lru_cache(maxsize=1)
def quarantine_inventory() -> dict[str, Any]:
    """Load the sealed inventory; when the guard needs it and it is missing, the guard refuses."""
    if not QUARANTINE_INVENTORY_PATH.is_file():
        raise QuarantinedArtifactError(
            f"quarantine inventory missing at {QUARANTINE_INVENTORY_PATH}; refusing every open-model input "
            "(materialize registry/projects with `git sparse-checkout add registry/projects`)"
        )
    inventory = json.loads(QUARANTINE_INVENTORY_PATH.read_text(encoding="utf-8"))
    if inventory.get("schema") != QUARANTINE_INVENTORY_SCHEMA:
        raise QuarantinedArtifactError(f"unexpected quarantine inventory schema in {QUARANTINE_INVENTORY_PATH}")
    return inventory


@lru_cache(maxsize=1)
def _quarantined_tails() -> frozenset[str]:
    """Open-model relative paths of every inventoried artifact inside the open-model tree."""
    tails = set()
    for entry in quarantine_inventory()["artifacts"]:
        if entry["storage"] == STRAY_STORAGE:
            continue
        tail = _open_model_tail(entry["path"])
        if tail is None:
            raise QuarantinedArtifactError(f"inventory path outside the open-model tree: {entry['path']}")
        tails.add(tail)
    return frozenset(tails)


@lru_cache(maxsize=1)
def _quarantined_stray_paths() -> frozenset[str]:
    """Repo-relative paths of inventoried files outside the open-model tree."""
    return frozenset(
        entry["path"] for entry in quarantine_inventory()["artifacts"] if entry["storage"] == STRAY_STORAGE
    )


@lru_cache(maxsize=1)
def _quarantined_hashes() -> dict[str, str]:
    """Content digest of every inventoried artifact mapped to its inventory path."""
    return {entry["sha256"]: entry["path"] for entry in quarantine_inventory()["artifacts"] if entry["bytes"] > 0}


def _open_model_tail(path: Path | str) -> str | None:
    """Return the path relative to either open-model base, or None outside both trees."""
    text = Path(path).as_posix()
    for marker in (LOGICAL_OPEN_MODEL_PREFIX, REGISTRY_OPEN_MODEL_PREFIX):
        token = marker + "/"
        index = text.find(token)
        if index != -1:
            return text[index + len(token) :].strip("/")
        if text == marker or text.endswith("/" + marker):
            return ""
    return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def _path_forms(candidate: Path, resolved: Path) -> tuple[str, ...]:
    """The lexically normalized and the resolved form of a path; ``..`` and symlinks cannot hide a seal."""
    forms = (posixpath.normpath(candidate.as_posix()), resolved.as_posix())
    return tuple(dict.fromkeys(forms))


def _tail_rule_reason(tail: str) -> str | None:
    """Apply the archive, tombstone and inventory-path rules to one open-model relative path."""
    parts = [part for part in tail.split("/") if part]
    if parts[:1] == ["archive"]:
        return "archived"
    for depth in range(1, len(parts) + 1):
        prefix = "/".join(parts[:depth])
        for base, label in (
            (REGISTRY_OPEN_MODEL_DATA_DIR, REGISTRY_OPEN_MODEL_PREFIX),
            (ARTIFACT_OPEN_MODEL_DATA_DIR, LOGICAL_OPEN_MODEL_PREFIX),
        ):
            if (base / prefix / TOMBSTONE_NAME).is_file():
                return f"sealed by {label}/{prefix}/{TOMBSTONE_NAME}"
    tails = _quarantined_tails()
    if tail in tails:
        return f"inventoried at {LOGICAL_OPEN_MODEL_PREFIX}/{tail}"
    prefix = tail + "/" if tail else ""
    if any(item.startswith(prefix) for item in tails):
        return f"directory holds inventoried artifacts: {tail or '.'}"
    return None


def _path_rule_reason(candidate: Path, resolved: Path) -> str | None:
    """Apply the archive, tombstone and inventory-path rules to every form of a path, without reading bytes."""
    for base in (REGISTRY_ARCHIVE_DIR, ARTIFACT_ARCHIVE_DIR):
        if resolved == base.resolve() or base.resolve() in resolved.parents:
            return "archived"
    for form in _path_forms(candidate, resolved):
        tail = _open_model_tail(form)
        if tail is not None:
            reason = _tail_rule_reason(tail)
            if reason is not None:
                return reason
    return None


def _stray_rule_reason(candidate: Path, resolved: Path) -> str | None:
    """Match inventoried files outside the open-model tree by their repo-relative path in any checkout."""
    for form in _path_forms(candidate, resolved):
        for stray in _quarantined_stray_paths():
            if form == stray or form.endswith("/" + stray):
                return f"inventoried at {stray}"
    return None


def _resolved(candidate: Path) -> Path:
    try:
        return candidate.resolve()
    except (OSError, RuntimeError):
        return candidate


def quarantine_reason(path: Path | str | None) -> str | None:
    """Return why a path is quarantined, or None when it may be read.

    A path is quarantined when it lies in either archive base, under a directory
    sealed by a ``TOMBSTONE.md`` in either storage base, at or above an inventoried
    artifact (outside-tree inventoried files included), or when it is a file whose
    bytes match an inventoried artifact (a copy outside the tree). Each rule is
    applied to the lexically normalized and to the resolved path. The inventory is
    loaded first for every path, so a missing inventory raises whatever the input
    is: the guard fails closed rather than open.
    """
    if path is None:
        return None
    quarantine_inventory()
    candidate = Path(path)
    resolved = _resolved(candidate)
    reason = _path_rule_reason(candidate, resolved) or _stray_rule_reason(candidate, resolved)
    if reason is not None:
        return reason
    if resolved.is_file() and resolved.stat().st_size > 0:
        match = _quarantined_hashes().get(_sha256_file(resolved))
        if match is not None:
            return f"bytes match quarantined {match}"
    return None


def refuse_quarantined(path: Path | str | None, context: str) -> None:
    """Raise before a loader opens a quarantined artifact; see ``quarantine_reason``."""
    reason = quarantine_reason(path)
    if reason is not None:
        raise QuarantinedArtifactError(
            f"Refusing {context} on quarantined path {path}: {reason}. Old-plan trainable artifacts are sealed "
            f"(#9607, plan PA1); see {REGISTRY_OPEN_MODEL_PREFIX}/{QUARANTINE_INVENTORY_RELATIVE}."
        )


def is_archived_or_quarantined_path(path: Path | str | None) -> bool:
    """Return whether a path is archived, tombstoned or inventoried (path rules only, no hashing)."""
    if path is None:
        return False
    candidate = Path(path)
    return _path_rule_reason(candidate, _resolved(candidate)) is not None


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


def _classified_child_classes(relative: str) -> set[str]:
    """Return the classes of rows under a relative directory, if any."""
    classes = open_model_classes()
    normalized = relative.strip("/")
    if not normalized:
        return set(classes.values())
    prefix = normalized + "/"
    return {classes[item] for item in classes if item.startswith(prefix)}


def open_model_class(relative: str) -> str | None:
    """Return K or A when the relative path, or a single-class directory, is classified."""
    classes = open_model_classes()
    normalized = relative.strip("/")
    if not normalized:
        return None
    found = classes.get(normalized)
    if found is not None:
        return found
    child_classes = _classified_child_classes(normalized)
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
    A single-class directory follows that class. A mixed directory, including
    the tree root, keeps the caller's prefix. A file path that is not a
    classification-table row raises ``ValueError`` instead of staying on the
    caller's prefix. Paths outside the tree join ``repo`` when they are relative.
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
    elif not relative.strip("/") or _classified_child_classes(relative):
        chosen = marker
    else:
        raise ValueError(f"unclassified open-model file path {relative.strip('/')!r} is not in classification-v1.tsv")
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
