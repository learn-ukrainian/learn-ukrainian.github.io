"""Hydrate release-pinned Atlas practice deck shards."""

from __future__ import annotations

import gzip
import hashlib
import http.client
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from contextlib import suppress
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRACTICE_DIR = ROOT / "site" / "public" / "lexicon"
DEFAULT_POINTER = ROOT / "site" / "src" / "data" / "lexicon-practice-deck.pointer.json"
RECOVERY_COMMAND = ".venv/bin/python -m scripts.practice_deck.io"

REQUIRED_POINTER_KEYS = (
    "asset_url",
    "release_tag",
    "deck_version",
    "package_schema_version",
    "gz_sha256",
    "package_sha256",
    "gz_bytes",
    "package_bytes",
    "file_count",
    "files",
)
DOWNLOAD_ATTEMPTS = 3
FORCE_HYDRATE_ENV = "ATLAS_MANIFEST_FORCE_HYDRATE"
ALLOWED_RELEASE_PATH_PREFIX = "/learn-ukrainian/learn-ukrainian.github.io/releases/download/"
PRACTICE_DECK_BUILDER_VERSION = 4  # 3→4: #4691 rationaleUk passthrough into heritage deck items
STALE_POINTER_HINT = (
    "If your branch predates the latest practice deck publish, its committed pointer is stale — "
    "update the branch from origin/main (gh pr update-branch <N> / git merge origin/main). "
    "Re-downloading cannot fix a stale pointer."
)


class PracticeDeckHydrationError(RuntimeError):
    """Raised when the practice deck cannot be safely hydrated."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_deck_inputs_fingerprint(
    entries: list[dict[str, Any]] | None,
    heritage_pairs: list[dict[str, Any]] | None,
    paronym_pairs: list[dict[str, Any]] | None,
    synonym_verdicts: dict[str, Any] | None,
    cloze_sources: list[dict[str, Any]] | None,
    schema_version: int,
) -> str:
    """Canonical hash of the deck DATA inputs only (no builder version).

    Seeds deterministic generation randomness: identical inputs must produce
    identical rolls regardless of code revision, so builder-version bumps
    never reshuffle seeded content (and seed-sensitive fixture tests stay
    stable across semantics releases).
    """
    payload = {
        "schema_version": schema_version,
        "entries": entries or [],
        "heritage_pairs": heritage_pairs or [],
        "paronym_pairs": paronym_pairs or [],
        "synonym_verdicts": synonym_verdicts or {},
        "cloze_sources": cloze_sources or [],
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def compute_deck_version(
    entries: list[dict[str, Any]] | None,
    heritage_pairs: list[dict[str, Any]] | None,
    paronym_pairs: list[dict[str, Any]] | None,
    synonym_verdicts: dict[str, Any] | None,
    cloze_sources: list[dict[str, Any]] | None,
    schema_version: int,
) -> str:
    payload = {
        "builder_version": PRACTICE_DECK_BUILDER_VERSION,
        "schema_version": schema_version,
        "entries": entries or [],
        "heritage_pairs": heritage_pairs or [],
        "paronym_pairs": paronym_pairs or [],
        "synonym_verdicts": synonym_verdicts or {},
        "cloze_sources": cloze_sources or [],
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"atlas-practice-v{schema_version}-{fingerprint}"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PracticeDeckHydrationError(f"{path} must contain a JSON object")
    return payload


def _validate_pointer(pointer: dict[str, Any], pointer_path: Path) -> None:
    missing = [key for key in REQUIRED_POINTER_KEYS if key not in pointer]
    if missing:
        raise PracticeDeckHydrationError(f"{pointer_path} missing required keys: {', '.join(missing)}")
    if pointer.get("package_schema_version") != 1:
        raise PracticeDeckHydrationError(f"{pointer_path} package_schema_version must be 1")
    if not isinstance(pointer.get("files"), list):
        raise PracticeDeckHydrationError(f"{pointer_path} files must be a list")
    if len(pointer["files"]) != pointer.get("file_count"):
        raise PracticeDeckHydrationError(f"{pointer_path} file_count does not match files")


def _safe_shard_name(name: object) -> str:
    if not isinstance(name, str) or not name:
        raise PracticeDeckHydrationError("practice deck file path must be a non-empty string")
    if "/" in name or "\\" in name or name.startswith("."):
        raise PracticeDeckHydrationError(f"unsafe practice deck file path: {name!r}")
    allowed_prefixes = (
        "practice-index.",
        "practice-lexemes.",
        "practice-cloze.",
        "practice-stress.",
        "practice-classify.",
        "practice-paradigm.",
        "practice-synonym.",
        "practice-heritage.",
        "practice-paronym.",
    )
    if not name.endswith(".json") or not name.startswith(allowed_prefixes):
        raise PracticeDeckHydrationError(f"unexpected practice deck file path: {name!r}")
    return name


def _pointer_file_map(pointer: dict[str, Any]) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for raw_file in pointer["files"]:
        if not isinstance(raw_file, dict):
            raise PracticeDeckHydrationError("practice deck pointer files entries must be objects")
        name = _safe_shard_name(raw_file.get("path"))
        if name in files:
            raise PracticeDeckHydrationError(f"duplicate practice deck file in pointer: {name}")
        for key in ("sha256", "bytes", "level", "kind"):
            if key not in raw_file:
                raise PracticeDeckHydrationError(f"practice deck pointer file {name} missing {key}")
        files[name] = raw_file
    return files


def _assert_allowed_download_url(raw_url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(raw_url)
    except ValueError as exc:
        raise PracticeDeckHydrationError(f"practice deck asset_url is not valid URL: {raw_url}") from exc
    if parsed.scheme != "https":
        raise PracticeDeckHydrationError(f"practice deck asset_url must use https: {raw_url}")
    host = parsed.hostname.lower() if parsed.hostname else ""
    from_repo_release = host == "github.com" and parsed.path.startswith(ALLOWED_RELEASE_PATH_PREFIX)
    from_github_cdn = host.endswith(".githubusercontent.com")
    if not (from_repo_release or from_github_cdn):
        raise PracticeDeckHydrationError(f"practice deck asset_url is not allowlisted: {raw_url}")
    return raw_url


def _download_url(pointer: dict[str, Any], attempt: int) -> str:
    if attempt == 0:
        return _assert_allowed_download_url(str(pointer["asset_url"]))
    split = urllib.parse.urlsplit(str(pointer["asset_url"]))
    query = urllib.parse.parse_qsl(split.query, keep_blank_values=True)
    query.extend(
        [
            ("atlas_practice_deck_sha256", str(pointer["gz_sha256"])),
            ("atlas_practice_deck_attempt", str(attempt)),
        ]
    )
    return _assert_allowed_download_url(
        urllib.parse.urlunsplit(split._replace(query=urllib.parse.urlencode(query)))
    )


def _download(pointer: dict[str, Any], *, attempt: int = 0) -> bytes:
    request = urllib.request.Request(
        _download_url(pointer, attempt),
        headers={
            "Accept": "application/gzip, application/octet-stream;q=0.9, */*;q=0.1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "learn-ukrainian-atlas-practice-deck-hydrate/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _download_gzip(pointer: dict[str, Any]) -> bytes:
    gz_bytes: bytes | None = None
    actual_gz_sha = ""
    last_error: BaseException | None = None
    last_failure = ""
    for attempt in range(DOWNLOAD_ATTEMPTS):
        try:
            gz_bytes = _download(pointer, attempt=attempt)
        except (OSError, urllib.error.URLError, http.client.HTTPException) as exc:
            last_error = exc
            last_failure = "error"
            continue
        actual_gz_sha = _sha256(gz_bytes)
        if actual_gz_sha == pointer["gz_sha256"]:
            return gz_bytes
        last_failure = "mismatch"

    if last_error is not None and last_failure == "error":
        raise PracticeDeckHydrationError(
            "failed to download Atlas practice deck release asset "
            f"after {DOWNLOAD_ATTEMPTS} attempts: {last_error}. "
            f"Manual recovery command: {RECOVERY_COMMAND}"
        ) from last_error
    raise PracticeDeckHydrationError(
        "gz sha256 mismatch: "
        f"expected {pointer['gz_sha256']}, got {actual_gz_sha} "
        f"after {DOWNLOAD_ATTEMPTS} download attempts. "
        f"{STALE_POINTER_HINT} "
        f"Manual recovery command: {RECOVERY_COMMAND}"
    )


def _already_hydrated(practice_dir: Path, pointer: dict[str, Any]) -> bool:
    for name, metadata in _pointer_file_map(pointer).items():
        path = practice_dir / name
        if not path.exists():
            return False
        data = path.read_bytes()
        if len(data) != metadata["bytes"] or _sha256(data) != metadata["sha256"]:
            return False
    return True


def _refuse_richer_local(practice_dir: Path, pointer: dict[str, Any]) -> None:
    if os.environ.get(FORCE_HYDRATE_ENV) == "1":
        return

    local_lexemes = 0
    release_lexemes = 0
    try:
        for name, metadata in _pointer_file_map(pointer).items():
            if metadata["kind"] != "index":
                continue
            release_count = metadata.get("counts", {}).get("lexemes")
            local_count = _read_json(practice_dir / name).get("counts", {}).get("lexemes")
            if (
                not isinstance(release_count, int)
                or isinstance(release_count, bool)
                or not isinstance(local_count, int)
                or isinstance(local_count, bool)
            ):
                return
            release_lexemes += release_count
            local_lexemes += local_count
    except (OSError, ValueError):
        return

    if local_lexemes > release_lexemes:
        raise PracticeDeckHydrationError(
            f"refusing to overwrite local practice deck with {local_lexemes} lexemes using the "
            f"published release with only {release_lexemes}. Publish it with make "
            f"practice-deck-publish, or force the restore with {FORCE_HYDRATE_ENV}=1."
        )


def _package_files(package: dict[str, Any], pointer: dict[str, Any]) -> list[tuple[str, bytes]]:
    if package.get("schema") != "atlas-practice-deck-package":
        raise PracticeDeckHydrationError("practice deck package schema mismatch")
    if package.get("schemaVersion") != pointer["package_schema_version"]:
        raise PracticeDeckHydrationError("practice deck package schemaVersion mismatch")
    if package.get("deckVersion") != pointer["deck_version"]:
        raise PracticeDeckHydrationError("practice deck package deckVersion mismatch")
    raw_files = package.get("files")
    if not isinstance(raw_files, list) or len(raw_files) != pointer["file_count"]:
        raise PracticeDeckHydrationError("practice deck package file count mismatch")

    pointer_files = _pointer_file_map(pointer)
    hydrated: list[tuple[str, bytes]] = []
    seen: set[str] = set()
    for raw_file in raw_files:
        if not isinstance(raw_file, dict):
            raise PracticeDeckHydrationError("practice deck package files entries must be objects")
        name = _safe_shard_name(raw_file.get("path"))
        if name in seen:
            raise PracticeDeckHydrationError(f"duplicate practice deck file in package: {name}")
        seen.add(name)
        if name not in pointer_files:
            raise PracticeDeckHydrationError(f"practice deck package file not pinned by pointer: {name}")
        content = raw_file.get("content")
        if not isinstance(content, str):
            raise PracticeDeckHydrationError(f"practice deck package file {name} missing string content")
        data = content.encode("utf-8")
        metadata = pointer_files[name]
        if len(data) != metadata["bytes"] or _sha256(data) != metadata["sha256"]:
            raise PracticeDeckHydrationError(f"practice deck package file hash mismatch: {name}")
        hydrated.append((name, data))
    if seen != set(pointer_files):
        missing = sorted(set(pointer_files) - seen)
        raise PracticeDeckHydrationError(f"practice deck package missing files: {', '.join(missing)}")
    return hydrated


def _decode_package(data: bytes, pointer: dict[str, Any]) -> list[tuple[str, bytes]]:
    if len(data) != pointer["package_bytes"]:
        raise PracticeDeckHydrationError(
            f"package size mismatch: expected {pointer['package_bytes']}, got {len(data)}"
        )
    actual_sha = _sha256(data)
    if actual_sha != pointer["package_sha256"]:
        raise PracticeDeckHydrationError(
            f"package sha mismatch: expected {pointer['package_sha256']}, got {actual_sha}. "
            f"{STALE_POINTER_HINT}"
        )
    package = json.loads(data.decode("utf-8"))
    if not isinstance(package, dict):
        raise PracticeDeckHydrationError("practice deck package must contain a JSON object")
    return _package_files(package, pointer)


def _write_files(practice_dir: Path, files: list[tuple[str, bytes]]) -> None:
    practice_dir.mkdir(parents=True, exist_ok=True)
    temp_paths: list[Path] = []
    try:
        for name, data in files:
            path = practice_dir / name
            temp_path = path.with_name(f"{path.name}.tmp")
            temp_path.write_bytes(data)
            temp_paths.append(temp_path)
        for temp_path in temp_paths:
            os.replace(temp_path, temp_path.with_name(temp_path.name.removesuffix(".tmp")))
    finally:
        for temp_path in temp_paths:
            with suppress(FileNotFoundError):
                temp_path.unlink()


def ensure_practice_deck_hydrated(
    practice_dir: Path = DEFAULT_PRACTICE_DIR,
    pointer_path: Path = DEFAULT_POINTER,
) -> dict[str, Any]:
    pointer = _read_json(pointer_path)
    _validate_pointer(pointer, pointer_path)
    if _already_hydrated(practice_dir, pointer):
        return pointer

    gz_bytes = _download_gzip(pointer)
    if len(gz_bytes) != pointer["gz_bytes"]:
        raise PracticeDeckHydrationError(f"gz size mismatch: expected {pointer['gz_bytes']}, got {len(gz_bytes)}")
    package_bytes = gzip.decompress(gz_bytes)
    files = _decode_package(package_bytes, pointer)
    _refuse_richer_local(practice_dir, pointer)
    _write_files(practice_dir, files)
    return pointer


def main() -> int:
    pointer = ensure_practice_deck_hydrated()
    print(f"Hydrated Atlas practice deck {pointer['deck_version']} ({pointer['file_count']} shards).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
