#!/usr/bin/env python3
"""Vendor a pinned Atlas runtime-shard tree into the Pages dist (PR3 D1 / R1 / R7).

Downloads a GitHub Release asset pinned by **immutable asset id + sha256** (never a
mutable tag name), verifies archive checksum + internal packaging manifest, enforces
generation retention (CURRENT + PRIOR version dirs), applies scale gates, then
byte-preserves the tree into ``<dist>/atlas/``.

Feature flag: when ``ATLAS_TREE_ASSET_ID`` / ``ATLAS_TREE_SHA256`` are unset (and no
``--archive`` is supplied), the script logs a skip message and exits 0 so deploys
stay green until the 20k publish arc supplies the first real pin.

Usage::

    # Offline / tests (local archive + digest pin)
    ATLAS_TREE_SHA256=<hex> .venv/bin/python scripts/deploy/vendor_atlas_tree.py \\
        site/dist --archive /tmp/atlas-tree.zip

    # CI (asset id pin + digest; requires network + token)
    ATLAS_TREE_ASSET_ID=123 ATLAS_TREE_SHA256=<hex> \\
      .venv/bin/python scripts/deploy/vendor_atlas_tree.py site/dist
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Scale gates (R7) — fail before the 1 GiB GitHub Pages hard cap is at risk.
# Overridable via env; defaults are constants.
# ---------------------------------------------------------------------------
MIB = 1024 * 1024
DEFAULT_WARN_EXTRACTED_BYTES = 512 * MIB  # 512 MiB
DEFAULT_FAIL_EXTRACTED_BYTES = 800 * MIB  # 800 MiB
DEFAULT_FAIL_ARCHIVE_BYTES = 900 * MIB
DEFAULT_FAIL_OBJECT_COUNT = 200_000

TREE_MANIFEST_SCHEMA = "atlas-tree-archive-manifest"
TREE_MANIFEST_SCHEMA_VERSION = 1
TREE_MANIFEST_REL = "atlas/tree-manifest.json"
CURRENT_REL = "atlas/current.json"
VERSIONS_REL = "atlas/versions"

SKIP_MESSAGE = "atlas vendoring: no pin configured, skipping"

DEFAULT_REPO = "learn-ukrainian/learn-ukrainian.github.io"


class VendorError(RuntimeError):
    """Hard vendoring failure — deploy must abort (old site stays live)."""


@dataclass
class VendorMetrics:
    """R7 metrics emitted to stdout + optional JSON file."""

    archive_bytes: int
    extracted_bytes: int
    object_count: int
    vendor_duration_ms: int
    data_version: str
    prior_versions: list[str] = field(default_factory=list)
    archive_sha256: str = ""
    asset_id: str | None = None
    warnings: list[str] = field(default_factory=list)
    skipped: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(str(raw).strip(), 10)
    except ValueError as exc:
        raise VendorError(f"{name} must be an integer, got {raw!r}") from exc
    if value < 0:
        raise VendorError(f"{name} must be non-negative, got {value}")
    return value


def resolve_thresholds() -> dict[str, int]:
    """Return warn/fail thresholds (env overrides constants)."""
    return {
        "warn_extracted_bytes": _env_int(
            "ATLAS_TREE_WARN_EXTRACTED_BYTES", DEFAULT_WARN_EXTRACTED_BYTES
        ),
        "fail_extracted_bytes": _env_int(
            "ATLAS_TREE_FAIL_EXTRACTED_BYTES", DEFAULT_FAIL_EXTRACTED_BYTES
        ),
        "fail_archive_bytes": _env_int(
            "ATLAS_TREE_FAIL_ARCHIVE_BYTES", DEFAULT_FAIL_ARCHIVE_BYTES
        ),
        "fail_object_count": _env_int(
            "ATLAS_TREE_FAIL_OBJECT_COUNT", DEFAULT_FAIL_OBJECT_COUNT
        ),
    }


def pin_configured(
    *,
    asset_id: str | None,
    sha256: str | None,
    archive_path: Path | None,
) -> bool:
    """True when enough pin inputs exist to attempt vendoring (not skip)."""
    has_digest = bool(sha256 and str(sha256).strip())
    has_source = bool(archive_path) or bool(asset_id and str(asset_id).strip())
    return has_digest and has_source


def download_release_asset(
    asset_id: str,
    *,
    repo: str,
    token: str | None = None,
) -> bytes:
    """Download a release asset by immutable numeric id (GitHub API).

    Uses ``gh api`` when available (inherits ``GH_TOKEN`` / ``GITHUB_TOKEN``),
    otherwise falls back to ``urllib`` with an Authorization header.
    """
    asset_id = str(asset_id).strip()
    if not asset_id.isdigit():
        raise VendorError(
            f"ATLAS_TREE_ASSET_ID must be a numeric GitHub asset id, got {asset_id!r}"
        )

    # Prefer gh: handles redirects + auth for private/public assets uniformly.
    gh = shutil.which("gh")
    if gh:
        cmd = [
            gh,
            "api",
            f"repos/{repo}/releases/assets/{asset_id}",
            "-H",
            "Accept: application/octet-stream",
        ]
        try:
            result = subprocess.run(
                cmd, check=False, capture_output=True, timeout=300
            )
        except subprocess.TimeoutExpired as exc:
            raise VendorError(
                f"gh api timed out downloading release asset {asset_id} "
                f"from {repo}: {exc}"
            ) from exc
        except OSError as exc:
            raise VendorError(f"failed to invoke gh for asset {asset_id}: {exc}") from exc
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace").strip()
            raise VendorError(
                f"gh api failed downloading release asset {asset_id} "
                f"from {repo}: {err or f'exit {result.returncode}'}"
            )
        return result.stdout

    url = f"https://api.github.com/repos/{repo}/releases/assets/{asset_id}"
    headers = {
        "Accept": "application/octet-stream",
        "User-Agent": "learn-ukrainian-atlas-tree-vendor/1.0",
    }
    tok = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.read()
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise VendorError(
            f"failed to download release asset {asset_id} from {repo}: {exc}"
        ) from exc


def verify_archive_digest(archive_bytes: bytes, expected_sha256: str) -> str:
    """Return digest if it matches; raise VendorError on mismatch (fail closed)."""
    expected = expected_sha256.strip().lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise VendorError(
            f"ATLAS_TREE_SHA256 must be a 64-char hex digest, got {expected_sha256!r}"
        )
    actual = sha256_hex(archive_bytes)
    if actual != expected:
        raise VendorError(
            f"archive sha256 mismatch: expected {expected}, got {actual}"
        )
    return actual


def _safe_member_path(name: str) -> Path:
    """Reject absolute paths and ``..`` traversal in zip members."""
    # Zip members use forward slashes; normalize without resolving against host FS.
    cleaned = name.replace("\\", "/").lstrip("/")
    if not cleaned or cleaned.endswith("/"):
        raise VendorError(f"unsafe or empty zip member path: {name!r}")
    parts = Path(cleaned).parts
    if any(part in ("", ".", "..") for part in parts):
        raise VendorError(f"unsafe zip member path: {name!r}")
    if parts[0] != "atlas":
        raise VendorError(
            f"archive member must be under atlas/: got {name!r}"
        )
    return Path(*parts)


def extract_zip(archive_bytes: bytes, dest: Path) -> None:
    """Extract a zip archive into ``dest`` with path-safety checks."""
    dest.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(io_bytes_zip(archive_bytes)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                rel = _safe_member_path(info.filename)
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                # Byte-preserving copy (R10) — write raw member bytes as-is.
                with zf.open(info, "r") as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
    except zipfile.BadZipFile as exc:
        raise VendorError(f"archive is not a valid zip: {exc}") from exc


def io_bytes_zip(archive_bytes: bytes) -> Any:
    """Return a BytesIO suitable for ZipFile (kept as function for tests/mocks)."""
    import io

    return io.BytesIO(archive_bytes)


def load_tree_manifest(extract_root: Path) -> dict[str, Any]:
    """Load and schema-check the internal packaging manifest."""
    path = extract_root / TREE_MANIFEST_REL
    if not path.is_file():
        raise VendorError(f"internal manifest missing: {TREE_MANIFEST_REL}")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VendorError(f"internal manifest unreadable: {exc}") from exc
    if not isinstance(manifest, dict):
        raise VendorError("internal manifest must be a JSON object")
    if manifest.get("schema") != TREE_MANIFEST_SCHEMA:
        raise VendorError(
            f"internal manifest schema must be {TREE_MANIFEST_SCHEMA!r}, "
            f"got {manifest.get('schema')!r}"
        )
    if manifest.get("schemaVersion") != TREE_MANIFEST_SCHEMA_VERSION:
        raise VendorError(
            f"internal manifest schemaVersion must be {TREE_MANIFEST_SCHEMA_VERSION}, "
            f"got {manifest.get('schemaVersion')!r}"
        )
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise VendorError("internal manifest.files must be a non-empty list")
    return manifest


def verify_tree_manifest(extract_root: Path, manifest: Mapping[str, Any]) -> int:
    """Ensure every listed file exists and sizes match. Return listed file count."""
    seen: set[str] = set()
    for index, entry in enumerate(manifest["files"]):
        if not isinstance(entry, dict):
            raise VendorError(f"internal manifest.files[{index}] must be an object")
        rel = entry.get("path")
        size = entry.get("bytes")
        if not isinstance(rel, str) or not rel:
            raise VendorError(f"internal manifest.files[{index}].path must be a string")
        if not isinstance(size, int) or size < 0:
            raise VendorError(
                f"internal manifest.files[{index}].bytes must be a non-negative int"
            )
        # Paths in the packaging manifest are archive-relative (atlas/...).
        try:
            safe = _safe_member_path(rel)
        except VendorError:
            # _safe_member_path rejects trailing slashes; re-raise with context.
            raise
        if rel in seen:
            raise VendorError(f"internal manifest lists duplicate path: {rel}")
        seen.add(rel)
        path = extract_root / safe
        if not path.is_file():
            raise VendorError(f"manifest lists missing file: {rel}")
        actual = path.stat().st_size
        if actual != size:
            raise VendorError(
                f"size mismatch for {rel}: manifest={size}, actual={actual}"
            )
    return len(seen)


def list_version_dirs(extract_root: Path) -> list[str]:
    """Return sorted dataVersion directory names under atlas/versions/."""
    versions_root = extract_root / VERSIONS_REL
    if not versions_root.is_dir():
        raise VendorError(f"missing version tree: {VERSIONS_REL}/")
    names: list[str] = []
    for child in versions_root.iterdir():
        if child.is_dir() and not child.name.startswith("."):
            names.append(child.name)
    return sorted(names)


def verify_generation_retention(extract_root: Path) -> tuple[str, list[str]]:
    """R1: CURRENT + ≥1 PRIOR generation; current.json must point at a vendored dir.

    Returns ``(current_data_version, prior_versions)``.
    """
    current_path = extract_root / CURRENT_REL
    if not current_path.is_file():
        raise VendorError(f"missing {CURRENT_REL}")
    try:
        current = json.loads(current_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VendorError(f"current.json unreadable: {exc}") from exc
    if not isinstance(current, dict):
        raise VendorError("current.json must be a JSON object")
    if current.get("schema") != "atlas-current" or current.get("schemaVersion") != 1:
        raise VendorError("current.json has unsupported schema")
    data_version = current.get("dataVersion")
    if not isinstance(data_version, str) or not data_version.strip():
        raise VendorError("current.json missing dataVersion")
    manifest_url = current.get("manifestUrl")
    if not isinstance(manifest_url, str) or not manifest_url.startswith("versions/"):
        raise VendorError("current.json.manifestUrl must start with versions/")

    version_dirs = list_version_dirs(extract_root)
    if data_version not in version_dirs:
        raise VendorError(
            f"current.json points at non-vendored generation {data_version!r}; "
            f"vendored: {version_dirs}"
        )
    expected_manifest = extract_root / "atlas" / manifest_url
    if not expected_manifest.is_file():
        raise VendorError(f"current.json manifestUrl missing on disk: {manifest_url}")

    # Path inside versions/<dataVersion>/ must match the pointer's dataVersion.
    # manifestUrl form: versions/<dataVersion>/manifest.json
    parts = Path(manifest_url).parts
    if len(parts) < 3 or parts[0] != "versions" or parts[1] != data_version:
        raise VendorError(
            f"current.json manifestUrl {manifest_url!r} does not match "
            f"dataVersion {data_version!r}"
        )

    priors = [name for name in version_dirs if name != data_version]
    if not priors:
        raise VendorError(
            "generation retention failed: archive must vendor CURRENT and at least "
            f"one PRIOR generation under {VERSIONS_REL}/; only found {version_dirs}"
        )
    return data_version, priors


def measure_tree(extract_root: Path) -> tuple[int, int]:
    """Return ``(extracted_bytes, object_count)`` for files under extract_root."""
    total = 0
    count = 0
    atlas_root = extract_root / "atlas"
    if not atlas_root.is_dir():
        raise VendorError("extracted tree missing atlas/ root")
    for path in atlas_root.rglob("*"):
        if path.is_file():
            count += 1
            total += path.stat().st_size
    return total, count


def apply_scale_gates(
    *,
    archive_bytes: int,
    extracted_bytes: int,
    object_count: int,
    thresholds: Mapping[str, int],
) -> list[str]:
    """Return warnings; raise VendorError when a fail threshold is crossed."""
    warnings: list[str] = []
    warn_ex = thresholds["warn_extracted_bytes"]
    fail_ex = thresholds["fail_extracted_bytes"]
    fail_arch = thresholds["fail_archive_bytes"]
    fail_obj = thresholds["fail_object_count"]

    if extracted_bytes >= warn_ex and extracted_bytes < fail_ex:
        warnings.append(
            f"extracted size {extracted_bytes:,} bytes ≥ warn {warn_ex:,}"
        )
    if extracted_bytes >= fail_ex:
        raise VendorError(
            f"scale gate: extracted size {extracted_bytes:,} bytes ≥ fail "
            f"{fail_ex:,} (Pages hard-cap headroom)"
        )
    if archive_bytes >= fail_arch:
        raise VendorError(
            f"scale gate: archive size {archive_bytes:,} bytes ≥ fail {fail_arch:,}"
        )
    if object_count >= fail_obj:
        raise VendorError(
            f"scale gate: object count {object_count:,} ≥ fail {fail_obj:,}"
        )
    return warnings


def install_atlas_tree(extract_root: Path, dist: Path) -> Path:
    """Byte-preserve ``extract_root/atlas`` into ``dist/atlas`` (R10).

    Replaces any previous ``dist/atlas`` entirely so a pin flip is atomic from
    the deploy job's perspective (failure before this leaves the old artifact
    unuploaded).
    """
    src = extract_root / "atlas"
    if not src.is_dir():
        raise VendorError("nothing to install: extracted atlas/ missing")
    dest = dist / "atlas"
    if dest.exists():
        shutil.rmtree(dest)
    # copytree preserves file bytes; no rewrite/rename inside versions/.
    shutil.copytree(src, dest)
    return dest


def _serialize_tree_manifest(files: list[dict[str, Any]]) -> bytes:
    """Serialize packaging manifest JSON (UTF-8, trailing newline)."""
    body = {
        "schema": TREE_MANIFEST_SCHEMA,
        "schemaVersion": TREE_MANIFEST_SCHEMA_VERSION,
        "files": files,
    }
    return (json.dumps(body, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def build_archive_from_tree(tree_root: Path, archive_path: Path) -> str:
    """Test helper: zip an on-disk ``atlas/`` tree + write tree-manifest, return sha256.

    ``tree_root`` must contain an ``atlas/`` directory (e.g. a mini runtime tree).
    The packaging manifest lists every file under ``atlas/`` with sizes.
    """
    atlas = tree_root / "atlas"
    if not atlas.is_dir():
        raise VendorError(f"build_archive_from_tree: missing {atlas}")

    files: list[dict[str, Any]] = []
    for path in sorted(atlas.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(tree_root).as_posix()
        if rel == TREE_MANIFEST_REL:
            continue  # rewritten below
        files.append({"path": rel, "bytes": path.stat().st_size})

    # Self-size fixed-point: listed bytes for tree-manifest must match payload.
    self_entry: dict[str, Any] = {"path": TREE_MANIFEST_REL, "bytes": 0}
    files_with_self = [*files, self_entry]
    manifest_bytes = b""
    for _ in range(8):
        manifest_bytes = _serialize_tree_manifest(files_with_self)
        if self_entry["bytes"] == len(manifest_bytes):
            break
        self_entry["bytes"] = len(manifest_bytes)
    else:
        raise VendorError("failed to stabilize tree-manifest self size")

    manifest_path = tree_root / TREE_MANIFEST_REL
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(manifest_bytes)

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(atlas.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(tree_root).as_posix()
            # write stores exact file bytes (R10 source side).
            zf.write(path, arcname=rel)
    return sha256_hex(archive_path.read_bytes())


def vendor_atlas_tree(
    dist: Path,
    *,
    asset_id: str | None = None,
    sha256: str | None = None,
    archive_path: Path | None = None,
    repo: str | None = None,
    token: str | None = None,
    metrics_path: Path | None = None,
    thresholds: Mapping[str, int] | None = None,
) -> VendorMetrics:
    """Download (or load), verify, and install the atlas tree into ``dist``.

    Raises :class:`VendorError` on any integrity / retention / scale failure.
    When no pin is configured, returns a skipped metrics object (exit 0 path).
    """
    started = time.perf_counter()
    asset_id = (asset_id if asset_id is not None else os.environ.get("ATLAS_TREE_ASSET_ID") or "").strip() or None
    sha256 = (sha256 if sha256 is not None else os.environ.get("ATLAS_TREE_SHA256") or "").strip() or None
    if archive_path is None:
        env_archive = os.environ.get("ATLAS_TREE_ARCHIVE_PATH")
        if env_archive and str(env_archive).strip():
            archive_path = Path(str(env_archive).strip())

    if not pin_configured(asset_id=asset_id, sha256=sha256, archive_path=archive_path):
        metrics = VendorMetrics(
            archive_bytes=0,
            extracted_bytes=0,
            object_count=0,
            vendor_duration_ms=int((time.perf_counter() - started) * 1000),
            data_version="",
            skipped=True,
        )
        print(SKIP_MESSAGE)
        _write_metrics(metrics, metrics_path)
        return metrics

    if not sha256:
        raise VendorError("ATLAS_TREE_SHA256 is required when vendoring is enabled")

    if archive_path is not None:
        try:
            archive_bytes = archive_path.read_bytes()
        except OSError as exc:
            raise VendorError(f"failed to read archive {archive_path}: {exc}") from exc
    else:
        if not asset_id:
            raise VendorError("ATLAS_TREE_ASSET_ID is required when --archive is omitted")
        resolved_repo = (
            repo
            or os.environ.get("ATLAS_TREE_REPO")
            or os.environ.get("GITHUB_REPOSITORY")
            or DEFAULT_REPO
        )
        archive_bytes = download_release_asset(
            asset_id, repo=resolved_repo, token=token
        )

    digest = verify_archive_digest(archive_bytes, sha256)
    thr = dict(thresholds) if thresholds is not None else resolve_thresholds()

    with tempfile.TemporaryDirectory(prefix="atlas-vendor-") as tmp:
        extract_root = Path(tmp)
        extract_zip(archive_bytes, extract_root)
        packaging_manifest = load_tree_manifest(extract_root)
        listed_file_count = verify_tree_manifest(extract_root, packaging_manifest)
        data_version, priors = verify_generation_retention(extract_root)
        extracted_bytes, object_count = measure_tree(extract_root)
        # Fail closed: packaging manifest is the allowlist. Extra archive members
        # (not listed in atlas/tree-manifest.json) would otherwise install unverified.
        # The packaging manifest lists itself, so object_count must equal listed count.
        if object_count != listed_file_count:
            raise VendorError(
                f"archive contains files not listed in packaging manifest: "
                f"object_count={object_count} != listed_file_count={listed_file_count}"
            )
        warnings = apply_scale_gates(
            archive_bytes=len(archive_bytes),
            extracted_bytes=extracted_bytes,
            object_count=object_count,
            thresholds=thr,
        )
        dist.mkdir(parents=True, exist_ok=True)
        install_atlas_tree(extract_root, dist)

    duration_ms = int((time.perf_counter() - started) * 1000)
    metrics = VendorMetrics(
        archive_bytes=len(archive_bytes),
        extracted_bytes=extracted_bytes,
        object_count=object_count,
        vendor_duration_ms=duration_ms,
        data_version=data_version,
        prior_versions=priors,
        archive_sha256=digest,
        asset_id=asset_id,
        warnings=warnings,
        skipped=False,
    )
    _emit_metrics(metrics)
    _write_metrics(metrics, metrics_path)
    return metrics


def _emit_metrics(metrics: VendorMetrics) -> None:
    print("## Atlas tree vendoring metrics (R7)")
    print(f"archive_bytes={metrics.archive_bytes}")
    print(f"extracted_bytes={metrics.extracted_bytes}")
    print(f"object_count={metrics.object_count}")
    print(f"vendor_duration_ms={metrics.vendor_duration_ms}")
    print(f"data_version={metrics.data_version}")
    print(f"prior_versions={','.join(metrics.prior_versions)}")
    print(f"archive_sha256={metrics.archive_sha256}")
    if metrics.asset_id:
        print(f"asset_id={metrics.asset_id}")
    for warning in metrics.warnings:
        print(f"::warning title=Atlas tree scale::{warning}")
        print(f"WARNING: {warning}")
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        lines = [
            "## Atlas tree vendoring (R1/R7)",
            "",
            f"- archive_bytes: **{metrics.archive_bytes:,}**",
            f"- extracted_bytes: **{metrics.extracted_bytes:,}**",
            f"- object_count: **{metrics.object_count:,}**",
            f"- vendor_duration_ms: **{metrics.vendor_duration_ms}**",
            f"- data_version: `{metrics.data_version}`",
            f"- prior_versions: `{', '.join(metrics.prior_versions)}`",
            f"- archive_sha256: `{metrics.archive_sha256}`",
            "",
        ]
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))


def _write_metrics(metrics: VendorMetrics, metrics_path: Path | None) -> None:
    if metrics_path is None:
        return
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dist",
        type=Path,
        nargs="?",
        default=Path("site/dist"),
        help="Site dist directory (default: site/dist); installs into <dist>/atlas/",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=None,
        help="Local zip path (skips GitHub download; still requires ATLAS_TREE_SHA256)",
    )
    parser.add_argument(
        "--asset-id",
        default=None,
        help="Immutable GitHub release asset id (default: $ATLAS_TREE_ASSET_ID)",
    )
    parser.add_argument(
        "--sha256",
        default=None,
        help="Expected archive sha256 hex digest (default: $ATLAS_TREE_SHA256)",
    )
    parser.add_argument(
        "--repo",
        default=None,
        help="owner/repo for the release asset (default: $ATLAS_TREE_REPO / $GITHUB_REPOSITORY)",
    )
    parser.add_argument(
        "--metrics-out",
        type=Path,
        default=None,
        help="Write JSON metrics to this path (also set via ATLAS_TREE_METRICS_PATH)",
    )
    args = parser.parse_args(argv)

    metrics_path = args.metrics_out
    if metrics_path is None:
        env_metrics = os.environ.get("ATLAS_TREE_METRICS_PATH")
        if env_metrics and str(env_metrics).strip():
            metrics_path = Path(str(env_metrics).strip())
    # Metrics are opt-in via --metrics-out / ATLAS_TREE_METRICS_PATH so they
    # never land inside the Pages artifact by accident.

    try:
        vendor_atlas_tree(
            args.dist,
            asset_id=args.asset_id,
            sha256=args.sha256,
            archive_path=args.archive,
            repo=args.repo,
            metrics_path=metrics_path,
        )
    except VendorError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"::error title=Atlas tree vendoring::{exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
