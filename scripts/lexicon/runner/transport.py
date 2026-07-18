"""Content-addressed packet/bundle transport (#5230 PR3).

Packets and return bundles are immutable ``.tar.zst`` objects named by SHA-256
(spec §9). Writes are rsync-resumable: content is staged to a ``.partial`` file
and atomically renamed only after the outer content hash verifies.

Host-agnostic: no VPS provisioning. Compression uses the ``zstandard`` module
when installed, otherwise the ``zstd`` CLI (same framing either way).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.lexicon.runner.contracts import (
    BUNDLE_SCHEMA_VERSION,
    PACKET_SCHEMA_VERSION,
    canonical_json,
)

# Soft bound so one changed item never requires retransmitting multi-GB archives.
DEFAULT_MAX_BUNDLE_ITEMS = 500
DEFAULT_MAX_BUNDLE_UNCOMPRESSED_BYTES = 64 * 1024 * 1024  # 64 MiB


class TransportError(RuntimeError):
    """Invalid packet/bundle construction or verification failure."""


class HashMismatchError(TransportError):
    """Outer or per-item content hash did not match."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def zstd_compress(data: bytes, *, level: int = 3) -> bytes:
    """Compress bytes to zstd framing."""
    try:
        import zstandard as zstd  # type: ignore[import-not-found]

        return zstd.ZstdCompressor(level=level).compress(data)
    except ImportError:
        pass
    if shutil.which("zstd") is None:
        raise TransportError(
            "zstd compression requires the 'zstandard' package or a 'zstd' binary on PATH"
        )
    proc = subprocess.run(
        ["zstd", f"-{int(level)}", "-c", "-"],
        input=data,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise TransportError(f"zstd compress failed: {proc.stderr[:200]!r}")
    return proc.stdout


def zstd_decompress(data: bytes) -> bytes:
    """Decompress zstd-framed bytes."""
    try:
        import zstandard as zstd  # type: ignore[import-not-found]

        return zstd.ZstdDecompressor().decompress(data)
    except ImportError:
        pass
    if shutil.which("zstd") is None:
        raise TransportError(
            "zstd decompression requires the 'zstandard' package or a 'zstd' binary on PATH"
        )
    proc = subprocess.run(
        ["zstd", "-d", "-c", "-"],
        input=data,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise TransportError(f"zstd decompress failed: {proc.stderr[:200]!r}")
    return proc.stdout


def item_content_hash(payload: Mapping[str, Any] | bytes | str) -> str:
    if isinstance(payload, bytes):
        return _sha256_bytes(payload)
    if isinstance(payload, str):
        return _sha256_bytes(payload.encode("utf-8"))
    return _sha256_bytes(canonical_json(dict(payload)).encode("utf-8"))


@dataclass(frozen=True, slots=True)
class PacketItem:
    lemma_id: str
    request_key: str
    request: dict[str, Any]
    item_hash: str

    @staticmethod
    def from_request(
        lemma_id: str,
        request_key: str,
        request: Mapping[str, Any],
    ) -> PacketItem:
        body = {
            "lemma_id": lemma_id,
            "request": dict(request),
            "request_key": request_key,
        }
        return PacketItem(
            lemma_id=lemma_id,
            request_key=request_key,
            request=dict(request),
            item_hash=item_content_hash(body),
        )


@dataclass(frozen=True, slots=True)
class BundleItem:
    lemma_id: str
    request_key: str
    result: dict[str, Any]
    result_hash: str

    @staticmethod
    def from_result(
        lemma_id: str,
        request_key: str,
        result: Mapping[str, Any],
    ) -> BundleItem:
        body = {
            "lemma_id": lemma_id,
            "request_key": request_key,
            "result": dict(result),
        }
        return BundleItem(
            lemma_id=lemma_id,
            request_key=request_key,
            result=dict(result),
            result_hash=item_content_hash(body),
        )


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """Content-addressed artifact on disk."""

    artifact_id: str
    path: Path
    kind: str  # "packet" | "bundle"
    item_count: int
    uncompressed_bytes: int


def _build_tar_bytes(members: Mapping[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name in sorted(members):
            data = members[name]
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _extract_tar_bytes(tar_bytes: bytes) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            handle = tar.extractfile(member)
            if handle is None:
                continue
            out[member.name] = handle.read()
    return out


def atomic_write_bytes(path: Path, data: bytes) -> None:
    """Rsync-resumable durable write: ``.partial`` then fsync + atomic rename."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".partial")
    # If a prior partial exists, overwrite from start (rsync-style resume at app layer
    # is: rewrite partial until final hash matches, then rename).
    fd = os.open(str(partial), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        # Leave partial for resume; re-raise.
        raise
    os.replace(partial, path)
    # Best-effort directory fsync for durability on crash after rename.
    try:
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass


def write_content_addressed(
    directory: Path,
    tar_bytes: bytes,
    *,
    kind: str,
    item_count: int,
) -> ArtifactRef:
    """Compress, hash, and write ``{sha256}.tar.zst`` under *directory*."""
    compressed = zstd_compress(tar_bytes)
    artifact_id = _sha256_bytes(compressed)
    path = Path(directory) / f"{artifact_id}.tar.zst"
    if path.is_file():
        # Idempotent retransmission: same object, same path.
        if _sha256_file(path) != artifact_id:
            raise HashMismatchError(f"existing artifact corrupted: {path}")
        return ArtifactRef(
            artifact_id=artifact_id,
            path=path,
            kind=kind,
            item_count=item_count,
            uncompressed_bytes=len(tar_bytes),
        )
    atomic_write_bytes(path, compressed)
    # Verify outer hash after write (receiving-side contract also uses this).
    if _sha256_file(path) != artifact_id:
        path.unlink(missing_ok=True)
        raise HashMismatchError(f"outer hash mismatch after write: {path}")
    return ArtifactRef(
        artifact_id=artifact_id,
        path=path,
        kind=kind,
        item_count=item_count,
        uncompressed_bytes=len(tar_bytes),
    )


def verify_artifact_file(path: Path, *, expected_id: str | None = None) -> str:
    """Verify outer content address before extraction. Returns artifact id."""
    path = Path(path)
    if not path.is_file():
        raise TransportError(f"artifact missing: {path}")
    # Ignore incomplete partials.
    if path.name.endswith(".partial"):
        raise TransportError(f"partial transfer not final: {path}")
    digest = _sha256_file(path)
    name_id = path.name.removesuffix(".tar.zst")
    if path.name.endswith(".tar.zst") and name_id != digest:
        raise HashMismatchError(
            f"filename content-address mismatch: name={name_id} file={digest}"
        )
    if expected_id is not None and digest != expected_id:
        raise HashMismatchError(
            f"expected artifact id {expected_id}, got {digest}"
        )
    return digest


def load_tar_zst(path: Path, *, expected_id: str | None = None) -> dict[str, bytes]:
    verify_artifact_file(path, expected_id=expected_id)
    compressed = Path(path).read_bytes()
    return _extract_tar_bytes(zstd_decompress(compressed))


def build_packet(
    *,
    run_id: str,
    fingerprint: str,
    generation: int,
    items: Sequence[PacketItem],
    output_dir: Path,
    extra_manifest: Mapping[str, Any] | None = None,
) -> ArtifactRef:
    """Build a content-addressed request packet (.tar.zst)."""
    if not items:
        raise TransportError("packet requires at least one item")
    item_entries = []
    members: dict[str, bytes] = {}
    for item in items:
        body = {
            "lemma_id": item.lemma_id,
            "request": item.request,
            "request_key": item.request_key,
        }
        raw = canonical_json(body).encode("utf-8")
        digest = _sha256_bytes(raw)
        if digest != item.item_hash:
            raise HashMismatchError(
                f"item hash mismatch for lemma {item.lemma_id}: "
                f"declared={item.item_hash} actual={digest}"
            )
        rel = f"items/{item.lemma_id}.json"
        members[rel] = raw
        item_entries.append(
            {
                "item_hash": item.item_hash,
                "lemma_id": item.lemma_id,
                "path": rel,
                "request_key": item.request_key,
            }
        )
    manifest = {
        "fingerprint": fingerprint,
        "generation": int(generation),
        "items": sorted(item_entries, key=lambda x: x["lemma_id"]),
        "kind": "packet",
        "run_id": run_id,
        "schema_version": PACKET_SCHEMA_VERSION,
        **dict(extra_manifest or {}),
    }
    members["manifest.json"] = canonical_json(manifest).encode("utf-8")
    tar_bytes = _build_tar_bytes(members)
    return write_content_addressed(
        output_dir, tar_bytes, kind="packet", item_count=len(items)
    )


def build_bundle(
    *,
    run_id: str,
    fingerprint: str,
    packet_id: str,
    packet_generation: int,
    items: Sequence[BundleItem],
    output_dir: Path,
    max_items: int = DEFAULT_MAX_BUNDLE_ITEMS,
    max_uncompressed_bytes: int = DEFAULT_MAX_BUNDLE_UNCOMPRESSED_BYTES,
    extra_manifest: Mapping[str, Any] | None = None,
) -> ArtifactRef:
    """Build a bounded content-addressed result bundle (.tar.zst)."""
    if not items:
        raise TransportError("bundle requires at least one item")
    if len(items) > int(max_items):
        raise TransportError(
            f"bundle item count {len(items)} exceeds bound {max_items}; split the bundle"
        )
    item_entries = []
    members: dict[str, bytes] = {}
    for item in items:
        body = {
            "lemma_id": item.lemma_id,
            "request_key": item.request_key,
            "result": item.result,
        }
        raw = canonical_json(body).encode("utf-8")
        digest = _sha256_bytes(raw)
        if digest != item.result_hash:
            raise HashMismatchError(
                f"result hash mismatch for lemma {item.lemma_id}: "
                f"declared={item.result_hash} actual={digest}"
            )
        rel = f"items/{item.lemma_id}.json"
        members[rel] = raw
        item_entries.append(
            {
                "lemma_id": item.lemma_id,
                "path": rel,
                "request_key": item.request_key,
                "result_hash": item.result_hash,
            }
        )
    manifest = {
        "fingerprint": fingerprint,
        "items": sorted(item_entries, key=lambda x: x["lemma_id"]),
        "kind": "bundle",
        "packet_generation": int(packet_generation),
        "packet_id": packet_id,
        "run_id": run_id,
        "schema_version": BUNDLE_SCHEMA_VERSION,
        **dict(extra_manifest or {}),
    }
    members["manifest.json"] = canonical_json(manifest).encode("utf-8")
    tar_bytes = _build_tar_bytes(members)
    if len(tar_bytes) > int(max_uncompressed_bytes):
        raise TransportError(
            f"bundle uncompressed size {len(tar_bytes)} exceeds bound "
            f"{max_uncompressed_bytes}; split the bundle"
        )
    return write_content_addressed(
        output_dir, tar_bytes, kind="bundle", item_count=len(items)
    )


def split_bundle_items(
    items: Sequence[BundleItem],
    *,
    max_items: int = DEFAULT_MAX_BUNDLE_ITEMS,
) -> list[list[BundleItem]]:
    """Split items into bounded groups (stable lemma order)."""
    ordered = sorted(items, key=lambda it: it.lemma_id)
    groups: list[list[BundleItem]] = []
    for i in range(0, len(ordered), int(max_items)):
        groups.append(list(ordered[i : i + int(max_items)]))
    return groups


@dataclass(frozen=True, slots=True)
class LoadedPacket:
    artifact_id: str
    path: Path
    manifest: dict[str, Any]
    items: list[dict[str, Any]]  # each has lemma_id, request_key, request, item_hash


@dataclass(frozen=True, slots=True)
class LoadedBundle:
    artifact_id: str
    path: Path
    manifest: dict[str, Any]
    items: list[dict[str, Any]]  # each has lemma_id, request_key, result, result_hash


def _load_json_member(members: Mapping[str, bytes], name: str) -> dict[str, Any]:
    if name not in members:
        raise TransportError(f"missing member {name!r}")
    data = json.loads(members[name].decode("utf-8"))
    if not isinstance(data, dict):
        raise TransportError(f"{name} must be a JSON object")
    return data


def read_packet(path: Path, *, expected_id: str | None = None) -> LoadedPacket:
    """Verify outer hash and every per-item hash; return loaded packet."""
    path = Path(path)
    artifact_id = verify_artifact_file(path, expected_id=expected_id)
    members = load_tar_zst(path, expected_id=artifact_id)
    manifest = _load_json_member(members, "manifest.json")
    if manifest.get("kind") != "packet":
        raise TransportError(f"not a packet artifact: kind={manifest.get('kind')!r}")
    items: list[dict[str, Any]] = []
    for entry in manifest.get("items") or []:
        rel = str(entry["path"])
        raw = members.get(rel)
        if raw is None:
            raise TransportError(f"missing packet item file {rel}")
        actual = _sha256_bytes(raw)
        declared = str(entry["item_hash"])
        if actual != declared:
            raise HashMismatchError(
                f"per-item hash mismatch for {entry.get('lemma_id')}: "
                f"declared={declared} actual={actual}"
            )
        body = json.loads(raw.decode("utf-8"))
        items.append(
            {
                "item_hash": declared,
                "lemma_id": str(body["lemma_id"]),
                "request": dict(body["request"]),
                "request_key": str(body["request_key"]),
            }
        )
    items.sort(key=lambda x: x["lemma_id"])
    return LoadedPacket(
        artifact_id=artifact_id,
        path=path,
        manifest=manifest,
        items=items,
    )


def read_bundle(path: Path, *, expected_id: str | None = None) -> LoadedBundle:
    """Verify outer hash and every per-item hash; return loaded bundle."""
    path = Path(path)
    artifact_id = verify_artifact_file(path, expected_id=expected_id)
    members = load_tar_zst(path, expected_id=artifact_id)
    manifest = _load_json_member(members, "manifest.json")
    if manifest.get("kind") != "bundle":
        raise TransportError(f"not a bundle artifact: kind={manifest.get('kind')!r}")
    items: list[dict[str, Any]] = []
    for entry in manifest.get("items") or []:
        rel = str(entry["path"])
        raw = members.get(rel)
        if raw is None:
            raise TransportError(f"missing bundle item file {rel}")
        actual = _sha256_bytes(raw)
        declared = str(entry["result_hash"])
        if actual != declared:
            raise HashMismatchError(
                f"per-item hash mismatch for {entry.get('lemma_id')}: "
                f"declared={declared} actual={actual}"
            )
        body = json.loads(raw.decode("utf-8"))
        items.append(
            {
                "lemma_id": str(body["lemma_id"]),
                "request_key": str(body["request_key"]),
                "result": dict(body["result"]),
                "result_hash": declared,
            }
        )
    items.sort(key=lambda x: x["lemma_id"])
    return LoadedBundle(
        artifact_id=artifact_id,
        path=path,
        manifest=manifest,
        items=items,
    )


def retransmit_copy(src: Path, dest_dir: Path) -> Path:
    """Idempotent retransmission of the same content-addressed object."""
    artifact_id = verify_artifact_file(src)
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{artifact_id}.tar.zst"
    if dest.is_file() and _sha256_file(dest) == artifact_id:
        return dest
    # Stage via partial then rename (same contract as initial write).
    atomic_write_bytes(dest, Path(src).read_bytes())
    if _sha256_file(dest) != artifact_id:
        dest.unlink(missing_ok=True)
        raise HashMismatchError(f"retransmit hash mismatch: {dest}")
    return dest


def stage_directory(prefix: str = "runner-transport-") -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


def iter_packet_paths(directory: Path) -> Iterable[Path]:
    for path in sorted(Path(directory).glob("*.tar.zst")):
        if path.name.endswith(".partial"):
            continue
        yield path
