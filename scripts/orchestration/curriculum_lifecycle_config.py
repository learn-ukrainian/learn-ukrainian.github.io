"""Manifest-derived profile selection shared by curriculum lifecycle contracts."""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from scripts.orchestration.preparation_evidence import (
    RegistryValidationError,
    load_yaml_mapping,
)

MANIFEST_PATH = Path("curriculum/l2-uk-en/curriculum.yaml")
MANIFEST_TYPE_FAMILIES = {"core": "core", "track": "seminar"}
_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class LifecycleConfigError(ValueError):
    """Raised when manifest authority and lifecycle selectors disagree."""


def _repo_file(repo_root: Path, relative: str | Path) -> Path:
    raw = str(relative)
    path = Path(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        raise LifecycleConfigError(f"manifest path must be repository-relative: {raw!r}")
    root = repo_root.resolve()
    candidate = (root / path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise LifecycleConfigError(f"manifest path escapes repository root: {raw!r}") from exc
    return candidate


def load_active_tracks(
    repo_root: Path,
    manifest_path: str | Path = MANIFEST_PATH,
) -> dict[str, str]:
    """Return the active ``track -> manifest type`` map from curriculum.yaml."""
    path = _repo_file(repo_root, manifest_path)
    try:
        manifest = load_yaml_mapping(path)
    except RegistryValidationError as exc:
        raise LifecycleConfigError(str(exc)) from exc
    levels = manifest.get("levels")
    if not isinstance(levels, Mapping) or not levels:
        raise LifecycleConfigError("curriculum manifest must contain a non-empty levels mapping")
    active: dict[str, str] = {}
    for raw_track, raw_record in levels.items():
        if not isinstance(raw_track, str) or not _IDENTIFIER_RE.fullmatch(raw_track):
            raise LifecycleConfigError(f"invalid active curriculum track: {raw_track!r}")
        if not isinstance(raw_record, Mapping):
            raise LifecycleConfigError(f"manifest levels.{raw_track} must be a mapping")
        manifest_type = raw_record.get("type")
        modules = raw_record.get("modules")
        if not isinstance(manifest_type, str) or not _IDENTIFIER_RE.fullmatch(manifest_type):
            raise LifecycleConfigError(f"manifest levels.{raw_track}.type is invalid")
        if not isinstance(modules, list) or not all(
            isinstance(slug, str) and _IDENTIFIER_RE.fullmatch(slug) for slug in modules
        ):
            raise LifecycleConfigError(
                f"manifest levels.{raw_track}.modules must be a list of repository slugs"
            )
        if len(modules) != len(set(modules)):
            raise LifecycleConfigError(f"manifest levels.{raw_track}.modules contains duplicates")
        active[raw_track] = manifest_type
    return active


def reject_stale_track_keys(
    keys: Mapping[str, Any] | set[str],
    active_tracks: Mapping[str, str],
    *,
    label: str,
) -> None:
    """Reject track-keyed config that names anything outside the active manifest."""
    configured = set(keys)
    stale = sorted(configured - set(active_tracks))
    if stale:
        raise LifecycleConfigError(f"{label} references inactive tracks: {', '.join(stale)}")


def resolve_profile_selectors(
    *,
    selectors: Mapping[str, Any],
    profile_families: Mapping[str, str],
    active_tracks: Mapping[str, str],
    label: str,
    manifest_type_families: Mapping[str, str] = MANIFEST_TYPE_FAMILIES,
) -> dict[str, str]:
    """Resolve every active track through strict overrides or manifest-type defaults."""
    track_selectors = selectors.get("tracks")
    type_selectors = selectors.get("manifest_types")
    if not isinstance(track_selectors, Mapping) or not isinstance(type_selectors, Mapping):
        raise LifecycleConfigError(f"{label} selectors must contain tracks and manifest_types mappings")
    reject_stale_track_keys(track_selectors, active_tracks, label=f"{label} track selector")

    resolved: dict[str, str] = {}
    for track, manifest_type in active_tracks.items():
        expected_family = manifest_type_families.get(manifest_type)
        if expected_family is None:
            raise LifecycleConfigError(
                f"{label} has no family contract for active manifest type {manifest_type!r}"
            )
        profile_id = track_selectors.get(track) or type_selectors.get(manifest_type)
        if not isinstance(profile_id, str):
            raise LifecycleConfigError(
                f"{label} has no profile for active track={track} type={manifest_type}"
            )
        profile_family = profile_families.get(profile_id)
        if profile_family is None:
            raise LifecycleConfigError(f"{label} selects unknown profile {profile_id!r} for {track}")
        if profile_family != expected_family:
            raise LifecycleConfigError(
                f"{label} profile {profile_id!r} has family {profile_family!r}; "
                f"active track {track!r} requires {expected_family!r}"
            )
        resolved[track] = profile_id
    return resolved
