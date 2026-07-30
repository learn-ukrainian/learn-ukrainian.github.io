#!/usr/bin/env python3
"""Durable local mirror for the Atlas 20k runner work-dir (#5884, sibling of #6014).

The fetch/enrich runners write their durable state (``ledger.sqlite``,
``network-cache.sqlite``, reduce/enrich candidates) under a work-dir on the
remote runner host (default ``/home/ops/atlas-runner/run-20k``), which has no
backup of its own. ``scripts/backup-data.sh`` (#6014) already makes encrypted,
versioned restic snapshots of everything under this repo's local ``data/`` —
so the fix is to mirror the runner work-dir into a checksummed copy under
``data/lexicon/runner-mirror/`` and let the existing backup bus pick it up,
not to build a second backup mechanism.

Three operations:

- ``snapshot``: rsync a source (local path or ``user@host:/path``) into a
  local mirror directory, then write a checksummed ``manifest.json`` over the
  mirror contents.
- ``verify``: recompute checksums for a mirror directory and compare against
  its manifest.
- ``require``: fail closed (nonzero exit / raised error) unless a mirror
  manifest exists, is internally verified, and is newer than
  ``--max-age-hours``. Callers that would otherwise wipe runner state should
  gate on this first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

MANIFEST_NAME = "manifest.json"
MANIFEST_SCHEMA_VERSION = 1
RESTIC_GATE_RECEIPT_NAME = "RESTIC-GATE-RECEIPT.json"
RESTIC_GATE_RECEIPT_SCHEMA = "atlas-runner-restic-gate-receipt"
RESTIC_GATE_RECEIPT_SCHEMA_VERSION = 1
IGNORED_DIR_NAMES = {"__pycache__"}
IGNORED_FILE_NAMES = {".DS_Store"}
IGNORED_SUFFIXES = {".pid", ".lock"}
DEFAULT_MAX_AGE_HOURS = 24.0


class DurableMirrorError(RuntimeError):
    """Raised when a durable mirror is missing, stale, or fails verification."""


@dataclass(frozen=True, slots=True)
class VerifyResult:
    ok: bool
    missing: list[str] = field(default_factory=list)
    mismatched: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        # Fail closed: symlinks can hide state or escape the tree after restore.
        if path.is_symlink():
            raise DurableMirrorError(f"symlink not allowed in durable mirror tree: {path}")
        if path.is_dir():
            continue
        if path.name in IGNORED_FILE_NAMES or path.suffix in IGNORED_SUFFIXES:
            continue
        if any(part in IGNORED_DIR_NAMES for part in path.relative_to(root).parts):
            continue
        if path.name == MANIFEST_NAME and path.parent == root:
            continue
        files.append(path)
    return files


def build_manifest(root: Path) -> dict[str, Any]:
    """Walk ``root`` and return a checksummed manifest (excludes ``manifest.json`` itself)."""
    entries: list[dict[str, Any]] = []
    total_bytes = 0
    for path in _iter_files(root):
        data_bytes = path.stat().st_size
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": data_bytes,
                "sha256": _sha256_file(path),
            }
        )
        total_bytes += data_bytes
    return {
        "schema": "atlas-runner-mirror-manifest",
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generated_at": time.time(),
        "file_count": len(entries),
        "total_bytes": total_bytes,
        "files": entries,
    }


def write_manifest(manifest: dict[str, Any], mirror_dir: Path) -> Path:
    manifest_path = mirror_dir / MANIFEST_NAME
    temp_path = manifest_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_path.replace(manifest_path)
    return manifest_path


def read_manifest(mirror_dir: Path) -> dict[str, Any]:
    manifest_path = mirror_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        raise DurableMirrorError(f"no durable mirror manifest at {manifest_path}")
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DurableMirrorError(f"unreadable durable mirror manifest at {manifest_path}: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema") != "atlas-runner-mirror-manifest":
        raise DurableMirrorError(f"{manifest_path} is not a runner-mirror manifest")
    if payload.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise DurableMirrorError(f"{manifest_path} has unsupported schema_version {payload.get('schema_version')!r}")
    return payload


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_utc_timestamp(value: Any, *, field_name: str) -> float:
    if not isinstance(value, str):
        raise DurableMirrorError(f"restic gate receipt has invalid {field_name}={value!r}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DurableMirrorError(f"restic gate receipt has invalid {field_name}={value!r}") from exc
    if parsed.tzinfo is None:
        raise DurableMirrorError(f"restic gate receipt has invalid {field_name}={value!r}")
    timestamp = parsed.timestamp()
    if not math.isfinite(timestamp):
        raise DurableMirrorError(f"restic gate receipt has non-finite {field_name}={value!r}")
    return timestamp


def _manifest_fingerprint(mirror_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Return the stable fields a restic receipt binds for one mirror."""
    manifest_path = mirror_dir / MANIFEST_NAME
    try:
        file_count = int(manifest["file_count"])
        generated_at = float(manifest["generated_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DurableMirrorError(f"cannot fingerprint invalid mirror manifest at {manifest_path}") from exc
    if file_count < 0 or not math.isfinite(generated_at):
        raise DurableMirrorError(f"cannot fingerprint invalid mirror manifest at {manifest_path}")
    return {
        "manifest_sha256": _sha256_file(manifest_path),
        "generated_at": generated_at,
        "file_count": file_count,
    }


def _fingerprint_mirrors(mirror_root: Path) -> dict[str, dict[str, Any]]:
    """Fingerprint every manifest-bearing mirror below a real mirror root."""
    if mirror_root.is_symlink() or not mirror_root.is_dir():
        raise DurableMirrorError(f"restic gate mirror root must be a real directory: {mirror_root}")

    mirrors: dict[str, dict[str, Any]] = {}
    for candidate in sorted(mirror_root.iterdir()):
        if candidate.is_symlink():
            raise DurableMirrorError(f"symlink not allowed in restic gate mirror root: {candidate}")
        if not candidate.is_dir() or not (candidate / MANIFEST_NAME).is_file():
            continue
        mirrors[candidate.name] = _manifest_fingerprint(candidate, read_manifest(candidate))
    return mirrors


def write_restic_gate_receipt(
    mirror_root: Path,
    *,
    restic_snapshot_id: str,
    host: str,
    git_sha: str,
    mirror_root_relative_to_data: str = "lexicon/runner-mirror",
    receipt_root: Path | None = None,
) -> Path:
    """Record manifests covered by a completed restic snapshot, atomically.

    This receipt is deliberately local. It lets a pre-wipe gate prove that a
    current mirror was included in a successful restic backup without access
    to restic credentials or its remote repository. ``mirror_root`` is the
    tree included in restic; when ``receipt_root`` is distinct, it must still
    have exactly the same manifest fingerprints before the receipt is written.
    """
    if not restic_snapshot_id or not isinstance(restic_snapshot_id, str):
        raise DurableMirrorError("restic gate receipt requires a restic snapshot id")
    if not host or not isinstance(host, str):
        raise DurableMirrorError("restic gate receipt requires a host label")
    if not git_sha or not isinstance(git_sha, str):
        raise DurableMirrorError("restic gate receipt requires a git sha")
    mirrors = _fingerprint_mirrors(mirror_root)
    receipt_root = receipt_root or mirror_root
    if receipt_root.resolve() != mirror_root.resolve():
        receipt_mirrors = _fingerprint_mirrors(receipt_root)
        if receipt_mirrors != mirrors:
            raise DurableMirrorError(
                "live runner mirrors changed after staging; refusing to write a receipt for content not backed up"
            )

    receipt = {
        "schema": RESTIC_GATE_RECEIPT_SCHEMA,
        "schema_version": RESTIC_GATE_RECEIPT_SCHEMA_VERSION,
        "created_at_utc": _utc_now(),
        "restic_snapshot_id": restic_snapshot_id,
        "host": host,
        "git_sha": git_sha,
        "mirror_root_relative_to_data": mirror_root_relative_to_data,
        "mirrors": mirrors,
    }
    receipt_path = receipt_root / RESTIC_GATE_RECEIPT_NAME
    temp_path = receipt_path.with_suffix(".json.tmp")
    temp_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_path.replace(receipt_path)
    return receipt_path


def _require_restic_gate_receipt(mirror_dir: Path, manifest: dict[str, Any]) -> None:
    receipt_path = mirror_dir.parent / RESTIC_GATE_RECEIPT_NAME
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise DurableMirrorError(
            f"no restic gate receipt for durable mirror at {mirror_dir}; "
            "run `./scripts/backup-data.sh backup --execute` after snapshot"
        )
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DurableMirrorError(f"unreadable restic gate receipt at {receipt_path}: {exc}") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != RESTIC_GATE_RECEIPT_SCHEMA:
        raise DurableMirrorError(f"{receipt_path} is not a restic gate receipt")
    if receipt.get("schema_version") != RESTIC_GATE_RECEIPT_SCHEMA_VERSION:
        raise DurableMirrorError(f"{receipt_path} has unsupported schema_version {receipt.get('schema_version')!r}")
    created_at = _parse_utc_timestamp(receipt.get("created_at_utc"), field_name="created_at_utc")
    snapshot_id = receipt.get("restic_snapshot_id")
    if (
        not isinstance(snapshot_id, str)
        or len(snapshot_id) != 64
        or any(c not in "0123456789abcdef" for c in snapshot_id)
    ):
        raise DurableMirrorError(f"{receipt_path} has invalid restic_snapshot_id")
    mirrors = receipt.get("mirrors")
    if not isinstance(mirrors, dict):
        raise DurableMirrorError(f"{receipt_path} has invalid mirrors map")
    recorded = mirrors.get(mirror_dir.name)
    if not isinstance(recorded, dict):
        raise DurableMirrorError(f"{receipt_path} does not cover mirror {mirror_dir.name!r}")

    current = _manifest_fingerprint(mirror_dir, manifest)
    if created_at < current["generated_at"]:
        raise DurableMirrorError(
            f"{receipt_path} predates the current mirror manifest; "
            "run `./scripts/backup-data.sh backup --execute` after snapshot"
        )
    for fingerprint_field, value in current.items():
        if recorded.get(fingerprint_field) != value:
            raise DurableMirrorError(
                f"{receipt_path} does not cover the current mirror manifest ({fingerprint_field} mismatch); "
                "run `./scripts/backup-data.sh backup --execute` after snapshot"
            )


def _safe_mirror_rel_path(mirror_dir: Path, rel_path: str) -> Path:
    """Resolve a manifest path only if it stays inside ``mirror_dir``."""
    if not isinstance(rel_path, str) or not rel_path or rel_path.startswith("/"):
        raise DurableMirrorError(f"unsafe manifest path: {rel_path!r}")
    parts = Path(rel_path).parts
    if any(part in ("", ".", "..") for part in parts):
        raise DurableMirrorError(f"unsafe manifest path: {rel_path!r}")
    disk_path = (mirror_dir / rel_path).resolve()
    mirror_real = mirror_dir.resolve()
    try:
        disk_path.relative_to(mirror_real)
    except ValueError as exc:
        raise DurableMirrorError(f"manifest path escapes mirror: {rel_path!r}") from exc
    return disk_path


def verify_manifest(manifest: dict[str, Any], mirror_dir: Path) -> VerifyResult:
    """Recompute checksums for every manifest entry and compare against disk."""
    missing: list[str] = []
    mismatched: list[str] = []
    expected_paths: set[str] = set()
    for entry in manifest.get("files", []):
        if not isinstance(entry, dict) or "path" not in entry:
            raise DurableMirrorError("manifest entry missing path")
        if "bytes" not in entry or "sha256" not in entry:
            raise DurableMirrorError(f"manifest entry missing bytes/sha256: {entry.get('path')!r}")
        rel_path = str(entry["path"])
        expected_paths.add(rel_path)
        disk_path = _safe_mirror_rel_path(mirror_dir, rel_path)
        if not disk_path.is_file():
            missing.append(rel_path)
            continue
        if disk_path.stat().st_size != entry["bytes"] or _sha256_file(disk_path) != entry["sha256"]:
            mismatched.append(rel_path)
    on_disk = {path.relative_to(mirror_dir).as_posix() for path in _iter_files(mirror_dir)}
    extra = sorted(on_disk - expected_paths)
    return VerifyResult(
        ok=not missing and not mismatched and not extra, missing=missing, mismatched=mismatched, extra=extra
    )


def sync_source_to_mirror(source: str, mirror_dir: Path, *, dry_run: bool = False) -> None:
    """rsync ``source`` (local path or ``user@host:/path``) into ``mirror_dir``.

    Trailing slash on both sides: sync contents, not a nested directory.
    ``--delete`` keeps the mirror an exact reflection of the current runner
    state, since versioning/history is the downstream restic bus's job, not
    this mirror's.
    """
    mirror_dir.mkdir(parents=True, exist_ok=True)
    source_arg = source if source.endswith("/") else f"{source}/"
    dest_arg = f"{mirror_dir}/"
    cmd = ["rsync", "-az", "--delete", "--exclude", f"/{MANIFEST_NAME}"]
    for dir_name in IGNORED_DIR_NAMES:
        cmd.extend(["--exclude", dir_name])
    for file_name in IGNORED_FILE_NAMES:
        cmd.extend(["--exclude", file_name])
    for suffix in IGNORED_SUFFIXES:
        cmd.extend(["--exclude", f"*{suffix}"])
    if dry_run:
        cmd.append("--dry-run")
    cmd.extend([source_arg, dest_arg])
    subprocess.run(cmd, check=True)


def _is_remote_rsync_source(source: str) -> bool:
    """True for rsync remote forms ``host:path`` / ``user@host:path`` (not Windows drive)."""
    if source.startswith("/"):
        return False
    # Windows-style local drive: C:\...
    if len(source) >= 2 and source[1] == ":" and source[0].isalpha():
        return False
    return ":" in source


def _remote_host_and_path(source: str) -> tuple[str, str]:
    host, _, remote_path = source.partition(":")
    if not host or not remote_path:
        raise DurableMirrorError(f"invalid remote source: {source!r}")
    return host, remote_path


def snapshot(source: str, mirror_dir: Path, *, dry_run: bool = False, allow_live: bool = False) -> dict[str, Any]:
    """rsync ``source`` into ``mirror_dir`` and (re)write its checksummed manifest."""
    # Fail closed when the source still looks live (local or remote): pid file means
    # SQLite may still be mutating. Remote check is best-effort via ssh test -f.
    if not allow_live:
        if _is_remote_rsync_source(source):
            host, remote_path = _remote_host_and_path(source)
            remote_pid = f"{remote_path.rstrip('/')}/enrich-driver.pid"
            probe = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host, "test", "-f", remote_pid],
                check=False,
                capture_output=True,
            )
            if probe.returncode == 0:
                raise DurableMirrorError(
                    f"refusing to snapshot live remote runner at {source} (found enrich-driver.pid); "
                    "stop the runner or pass --allow-live for an emergency best-effort copy"
                )
            if probe.returncode != 1:
                # ssh failure / remote error — fail closed (not "pid absent")
                detail = (probe.stderr or probe.stdout or b"").decode("utf-8", errors="replace").strip()
                raise DurableMirrorError(
                    f"could not probe remote runner liveness at {source} "
                    f"(ssh exit {probe.returncode}): {detail or 'no detail'}"
                )
        else:
            pid = Path(source) / "enrich-driver.pid"
            if pid.is_file():
                raise DurableMirrorError(
                    f"refusing to snapshot live runner at {source} (found enrich-driver.pid); "
                    "stop the runner or pass --allow-live for an emergency best-effort copy"
                )
    sync_source_to_mirror(source, mirror_dir, dry_run=dry_run)
    if dry_run:
        # Preview prospective payload from a local source; remote sources get a
        # dry-run rsync only (no meaningful local manifest without a transfer).
        local = Path(source)
        if "@" not in source and local.is_dir():
            preview = build_manifest(local)
            preview["dry_run"] = True
            preview["source"] = source
            return preview
        return {
            "schema": "atlas-runner-mirror-manifest",
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "generated_at": time.time(),
            "file_count": 0,
            "total_bytes": 0,
            "files": [],
            "dry_run": True,
            "source": source,
            "note": "remote dry-run; counts not computed locally",
        }
    manifest = build_manifest(mirror_dir)
    write_manifest(manifest, mirror_dir)
    return manifest


def require_durable(mirror_dir: Path, *, max_age_hours: float = DEFAULT_MAX_AGE_HOURS) -> dict[str, Any]:
    """Fail closed unless ``mirror_dir`` holds a fresh, internally-consistent manifest.

    Returns the manifest on success. Callers about to clean up runner state
    (VPS work-dir wipe, local cache purge) must call this first and abort on
    :class:`DurableMirrorError`.
    """
    if not math.isfinite(max_age_hours) or max_age_hours < 0:
        raise DurableMirrorError(f"invalid max_age_hours={max_age_hours!r} (must be finite and >= 0)")
    manifest = read_manifest(mirror_dir)
    files = manifest.get("files")
    if not isinstance(files, list):
        raise DurableMirrorError(f"durable mirror at {mirror_dir} has invalid files list")
    try:
        file_count = int(manifest.get("file_count") or 0)
    except (TypeError, ValueError) as exc:
        raise DurableMirrorError(
            f"durable mirror at {mirror_dir} has invalid file_count={manifest.get('file_count')!r}"
        ) from exc
    if len(files) == 0 or file_count == 0:
        raise DurableMirrorError(f"durable mirror at {mirror_dir} is empty")
    if file_count != len(files):
        raise DurableMirrorError(f"durable mirror at {mirror_dir} file_count mismatch ({file_count} != {len(files)})")
    try:
        generated_at = float(manifest["generated_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise DurableMirrorError(
            f"durable mirror at {mirror_dir} has invalid generated_at={manifest.get('generated_at')!r}"
        ) from exc
    if not math.isfinite(generated_at):
        raise DurableMirrorError(
            f"durable mirror at {mirror_dir} has non-finite generated_at={manifest.get('generated_at')!r}"
        )
    now = time.time()
    # Reject future-dated manifests (clock skew / corruption); small 5m skew tolerance.
    if generated_at > now + 300:
        raise DurableMirrorError(f"durable mirror at {mirror_dir} has future generated_at={generated_at} (now={now})")
    age_hours = max(0.0, now - generated_at) / 3600.0
    if age_hours > max_age_hours:
        raise DurableMirrorError(
            f"durable mirror at {mirror_dir} is {age_hours:.1f}h old (max {max_age_hours}h) — refresh with `snapshot` first"
        )
    result = verify_manifest(manifest, mirror_dir)
    if not result.ok:
        raise DurableMirrorError(
            f"durable mirror at {mirror_dir} failed verification: missing={result.missing} mismatched={result.mismatched}"
        )
    if manifest["file_count"] == 0:
        raise DurableMirrorError(
            f"durable mirror at {mirror_dir} is empty — refusing to treat an empty mirror as durable"
        )
    _require_restic_gate_receipt(mirror_dir, manifest)
    return manifest


def _cmd_snapshot(args: argparse.Namespace) -> int:
    manifest = snapshot(args.source, args.mirror_dir, dry_run=args.dry_run, allow_live=args.allow_live)
    print(
        f"{'would snapshot' if args.dry_run else 'snapshotted'} {args.source} -> {args.mirror_dir}: "
        f"{manifest['file_count']} files, {manifest['total_bytes']} bytes"
    )
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    try:
        manifest = read_manifest(args.mirror_dir)
        result = verify_manifest(manifest, args.mirror_dir)
    except DurableMirrorError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    if result.ok:
        print(f"OK: {args.mirror_dir} matches its manifest ({manifest['file_count']} files)")
        return 0
    print(f"FAILED: missing={result.missing} mismatched={result.mismatched} extra={result.extra}", file=sys.stderr)
    return 2


def _cmd_require(args: argparse.Namespace) -> int:
    try:
        manifest = require_durable(args.mirror_dir, max_age_hours=args.max_age_hours)
    except DurableMirrorError as exc:
        print(f"NOT DURABLE: {exc}", file=sys.stderr)
        return 2
    print(f"durable: {args.mirror_dir} ({manifest['file_count']} files, generated_at={manifest['generated_at']})")
    return 0


def _cmd_write_restic_gate_receipt(args: argparse.Namespace) -> int:
    try:
        receipt_path = write_restic_gate_receipt(
            args.mirror_root,
            restic_snapshot_id=args.restic_snapshot_id,
            host=args.host,
            git_sha=args.git_sha,
            mirror_root_relative_to_data=args.mirror_root_relative_to_data,
            receipt_root=args.receipt_root,
        )
    except DurableMirrorError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2
    print(f"wrote restic gate receipt: {receipt_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", required=True)

    snap = subparsers.add_parser("snapshot", help="rsync a source into a local mirror and write its manifest")
    snap.add_argument("--source", required=True, help="Local path or user@host:/path to mirror from")
    snap.add_argument("--mirror-dir", type=Path, required=True)
    snap.add_argument("--dry-run", action="store_true", help="rsync --dry-run; do not write a manifest")
    snap.add_argument(
        "--allow-live", action="store_true", help="allow snapshot while enrich-driver.pid is present (best-effort)"
    )
    snap.set_defaults(func=_cmd_snapshot)

    verify = subparsers.add_parser("verify", help="recompute checksums and compare against manifest.json")
    verify.add_argument("--mirror-dir", type=Path, required=True)
    verify.set_defaults(func=_cmd_verify)

    require = subparsers.add_parser("require", help="fail closed unless the mirror is fresh and verified")
    require.add_argument("--mirror-dir", type=Path, required=True)
    require.add_argument("--max-age-hours", type=float, default=DEFAULT_MAX_AGE_HOURS)
    require.set_defaults(func=_cmd_require)

    receipt = subparsers.add_parser(
        "write-restic-gate-receipt",
        help="write a local receipt binding runner manifests to a completed restic snapshot",
    )
    receipt.add_argument("--mirror-root", type=Path, required=True)
    receipt.add_argument("--restic-snapshot-id", required=True)
    receipt.add_argument("--host", required=True)
    receipt.add_argument("--git-sha", required=True)
    receipt.add_argument("--mirror-root-relative-to-data", default="lexicon/runner-mirror")
    receipt.add_argument(
        "--receipt-root",
        type=Path,
        help="live mirror root where the receipt is written; must match --mirror-root",
    )
    receipt.set_defaults(func=_cmd_write_restic_gate_receipt)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
