"""Publish a changed, already bound open-model K companion through its A group."""

from __future__ import annotations

import hashlib
from pathlib import Path

from scripts.storage.artifacts import write_artifact_set
from scripts.storage.paths import artifact_set, manifest_path


def publish_bound_companion(repo: Path, group: str, producer: str, target: Path, payload: bytes) -> bool:
    """Assert unchanged bytes or publish one changed K file with the verified group."""
    repo = repo.resolve()
    target = target if target.is_absolute() else repo / target
    registry = repo / "registry/projects/open_model_data"
    if target.is_symlink() or not target.is_relative_to(registry) or not target.resolve().is_relative_to(registry):
        raise ValueError(f"unbound managed companion: {target}")
    relative = target.relative_to(repo).as_posix()
    snapshot = artifact_set(group, repo=repo)
    descriptor = snapshot.manifest["set_descriptor"]
    if relative not in descriptor["companions"]:
        raise ValueError(f"unbound managed companion: {relative}")
    if snapshot.companions[relative] == payload:
        return False
    expected_manifest = hashlib.sha256(manifest_path(group, repo).read_bytes()).hexdigest()
    write_artifact_set(
        repo,
        group,
        producer,
        {},
        expected_hashes={},
        expected_members=set(snapshot.artifacts),
        companions={relative: (descriptor["companions"][relative], lambda staged: staged.write_bytes(payload))},
        expected_manifest=expected_manifest,
    )
    return True
