"""Resolve tracked registry and untracked artifact paths for every checkout."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_ROOT = ROOT / "registry"
DATA_ROOT = ROOT / "data"
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class MissingArtifactError(FileNotFoundError):
    """A required artifact is absent or disagrees with its manifest."""

    def __init__(self, group: str, rel: str, how_to_get: str, detail: str = "missing") -> None:
        self.group = group
        self.rel = rel
        self.how_to_get = how_to_get
        self.detail = detail
        super().__init__(f"{group}/{rel}: {detail}; run: {how_to_get}")


def checked_group(group: str) -> str:
    if not _NAME.fullmatch(group) or group in {".", ".."}:
        raise ValueError(f"invalid artifact group: {group!r}")
    return group


def checked_rel(rel: str) -> Path:
    path = Path(rel)
    if not rel or path.is_absolute() or any(part in {".", ".."} for part in path.parts) or str(path) != rel:
        raise ValueError(f"invalid artifact relative path: {rel!r}")
    return path


def artifact_store_root(repo: Path = ROOT) -> Path:
    """Return the host store, shared by all worktrees of this checkout."""
    return _cached_store_root(repo.resolve(), os.environ.get("LU_ARTIFACT_STORE"))


@lru_cache(maxsize=64)
def _cached_store_root(repo: Path, override: str | None) -> Path:
    common = subprocess.check_output(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=repo, text=True, timeout=30
    ).strip()
    primary = Path(common).resolve().parent
    store = Path(override).expanduser().resolve() if override else primary / "data/.artifact-store"
    # A dispatch checkout can be short-lived. Never make it the only owner of bytes.
    resolved_repo = repo.resolve()
    if store.is_relative_to(primary / ".worktrees/dispatch") or (
        resolved_repo != primary and store.is_relative_to(resolved_repo)
    ):
        raise ValueError("artifact store must not live under a dispatch worktree")
    return store


def manifest_path(group: str, repo: Path = ROOT) -> Path:
    return repo / "registry" / "artifacts" / f"{checked_group(group)}.manifest.json"


def load_manifest(group: str, repo: Path = ROOT) -> dict:
    path = manifest_path(group, repo)
    if not path.is_file():
        raise MissingArtifactError(
            group,
            "*",
            f"/home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts manifest build --group {group} --pre <commit>",
            "manifest missing",
        )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("group") != group or not isinstance(manifest.get("entries"), list):
        raise ValueError(f"invalid manifest: {path}")
    seen: set[str] = set()
    for entry in manifest["entries"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError(f"invalid manifest entry in {path}")
        entry_path = entry["path"]
        if not entry_path.startswith("data/"):
            raise ValueError(f"invalid manifest artifact path: {entry_path}")
        checked_rel(entry_path[5:])
        sha = entry.get("sha256")
        size = entry.get("size")
        if (
            entry_path in seen
            or not isinstance(sha, str)
            or not _SHA256.fullmatch(sha)
            or entry.get("store") != sha
            or type(size) is not int
            or size < 0
        ):
            raise ValueError(f"invalid manifest artifact entry: {entry_path}")
        seen.add(entry_path)
    return manifest


def find_entry(group: str, rel: str, repo: Path = ROOT) -> dict:
    checked_rel(rel)
    manifest = load_manifest(group, repo)
    matches = [entry for entry in manifest["entries"] if entry.get("path") == f"data/{rel}"]
    if len(matches) != 1:
        raise MissingArtifactError(
            group,
            rel,
            f"/home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts hydrate --group {group}",
            "no unique manifest entry",
        )
    return matches[0]


@lru_cache(maxsize=256)
def _cached_manifest(group: str, repo: Path, mtime_ns: int, size: int) -> dict:
    return load_manifest(group, repo)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_file(path: Path, entry: dict, *, group: str, rel: str) -> None:
    command = f"/home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts hydrate --group {group}"
    if not path.is_file() or path.is_symlink():
        raise MissingArtifactError(group, rel, command)
    size = path.stat().st_size
    if size != entry.get("size"):
        raise MissingArtifactError(group, rel, command, f"size {size} != {entry.get('size')}")
    actual = hash_file(path)
    if actual != entry.get("sha256"):
        raise MissingArtifactError(group, rel, command, f"sha256 {actual} != {entry.get('sha256')}")


def artifact_path(group: str, rel: str, *, repo: Path = ROOT) -> Path:
    """Return a verified runtime artifact; only this read may use the local stat cache."""
    checked_rel(rel)
    manifest_file = manifest_path(group, repo)
    stamp = manifest_file.stat()
    manifest = _cached_manifest(group, repo.resolve(), stamp.st_mtime_ns, stamp.st_size)
    matches = [entry for entry in manifest["entries"] if entry["path"] == f"data/{rel}"]
    if len(matches) != 1:
        raise MissingArtifactError(group, rel, "hydrate the artifact group", "no unique manifest entry")
    entry = matches[0]
    path = repo / "data" / checked_rel(rel)
    command = f"/home/ops/learn-ukrainian/.venv/bin/python -m scripts.storage.artifacts hydrate --group {group}"
    if not path.is_file() or path.is_symlink():
        raise MissingArtifactError(group, rel, command)
    stat = path.stat()
    if stat.st_size != entry.get("size"):
        raise MissingArtifactError(group, rel, command, f"size {stat.st_size} != {entry.get('size')}")
    cache_path = artifact_store_root(repo) / ".verification-cache.json"
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    key = f"{repo.resolve()}:{group}:{rel}"
    fingerprint = [entry["sha256"], stat.st_size, stat.st_mtime_ns]
    if cache.get(key) != fingerprint:
        verify_file(path, entry, group=group, rel=rel)
        cache[key] = fingerprint
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=cache_path.parent, delete=False) as target:
            json.dump(cache, target, sort_keys=True)
            temp = Path(target.name)
        os.replace(temp, cache_path)
    return path
