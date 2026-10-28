#!/usr/bin/env python3
"""Vendor a pinned Atlas runtime-shard tree into the Pages dist (PR3 D1 / R1 / R7).

Downloads a GitHub Release asset pinned by **immutable asset id + sha256** (never a
mutable tag name), verifies archive checksum + internal packaging manifest, enforces
generation retention (CURRENT + PRIOR version dirs), applies scale gates, then
byte-preserves the tree into ``<dist>/atlas/``. Public article search, aliases,
and typeahead shards are then projected from that same verified immutable pin;
entry/search set drift aborts before installation. The Pages entrypoint also
checks independent browse, daily and practice advertisements against CURRENT
before installing either the runtime or its search projection.

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
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
import zlib
from collections.abc import Iterator, Mapping
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.atlas.normalization import normalize_atlas_text
from scripts.audit.generate_search_index import (
    _gerund_parent,
    _sanitize_typeahead_gloss,
    _search_gloss,
    _uk_sort_key,
    build_search_shards,
    classification_code,
    display_gloss,
    write_aliases,
    write_index,
    write_search_shards,
)
from scripts.common import github_client

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
# The exporter re-publishes a byte-different tree for an already-published
# dataVersion beside the canonical one at ``<dataVersion>-transport-<tree sha256>``.
TRANSPORT_MARKER = "-transport-"
TRANSPORT_SUFFIX_RE = re.compile(r"-transport-[0-9a-f]{64}")
TRANSPORT_DIR_RE = re.compile(r"(?P<data_version>.+)-transport-[0-9a-f]{64}")

SKIP_MESSAGE = "atlas vendoring: no pin configured, skipping"

DEFAULT_REPO = "learn-ukrainian/learn-ukrainian.github.io"
DISCOVERY_EXCLUSIONS = Path(__file__).resolve().parents[2] / "registry/lexicon/atlas-discovery-exclusions.json"


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
    search_parity: dict[str, Any] = field(default_factory=dict)

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
            result = github_client.run(
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
        with github_client.http_open(request, timeout=300) as response:
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


def _data_version_problem(data_version: str) -> str | None:
    """Why ``data_version`` is not one safe path component free of the transport marker."""
    if (
        not data_version
        or data_version in {".", ".."}
        or data_version != data_version.strip()
        or any(ch in data_version for ch in "/\\")
        or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in data_version)
    ):
        return "is not a safe path component"
    if TRANSPORT_MARKER in data_version:
        return "must not carry a transport suffix"
    return None


def _validate_data_version(data_version: str) -> None:
    problem = _data_version_problem(data_version)
    if problem:
        raise VendorError(f"current.json dataVersion {problem}: {data_version!r}")


def _generation_version(extract_root: Path, dir_name: str) -> str:
    """Logical dataVersion of a vendored ``versions/`` directory, proven by its manifest.

    The directory must be exactly ``<dataVersion>`` or the exporter's
    ``<dataVersion>-transport-<64 lowercase hex>``, and its ``manifest.json`` must
    carry that dataVersion. Anything else — a truncated or otherwise malformed
    suffix, a missing or foreign manifest — fails closed rather than being counted
    as (or hidden inside) a generation.
    """
    match = TRANSPORT_DIR_RE.fullmatch(dir_name)
    data_version = match.group("data_version") if match else dir_name
    problem = _data_version_problem(data_version)
    if problem:
        raise VendorError(
            f"malformed generation directory {VERSIONS_REL}/{dir_name!r}: its dataVersion "
            f"{data_version!r} {problem} (expected <dataVersion> or "
            "<dataVersion>-transport-<64 lowercase hex>)"
        )
    manifest_path = extract_root / VERSIONS_REL / dir_name / "manifest.json"
    if not manifest_path.is_file():
        raise VendorError(f"generation {VERSIONS_REL}/{dir_name} has no manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VendorError(f"generation {VERSIONS_REL}/{dir_name} manifest unreadable: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("dataVersion") != data_version:
        found = manifest.get("dataVersion") if isinstance(manifest, dict) else None
        raise VendorError(
            f"generation {VERSIONS_REL}/{dir_name} manifest carries dataVersion {found!r}, "
            f"not {data_version!r}"
        )
    return data_version


def _pointed_version_dir(manifest_url: str, data_version: str) -> str:
    """Return the ``versions/`` directory named by ``manifestUrl``.

    Accepts exactly ``versions/<dataVersion>/manifest.json`` or the exporter's
    ``versions/<dataVersion>-transport-<64 lowercase hex>/manifest.json``.
    """
    parts = manifest_url.split("/")
    if len(parts) == 3 and parts[0] == "versions" and parts[2] == "manifest.json":
        dir_name = parts[1]
        suffix = dir_name[len(data_version) :]
        if dir_name == data_version or (
            dir_name.startswith(data_version) and TRANSPORT_SUFFIX_RE.fullmatch(suffix)
        ):
            return dir_name
    raise VendorError(
        f"current.json manifestUrl {manifest_url!r} does not match dataVersion "
        f"{data_version!r} (expected versions/{data_version}[-transport-<sha256>]/manifest.json)"
    )


def verify_generation_retention(extract_root: Path) -> tuple[str, list[str]]:
    """R1: CURRENT + ≥1 PRIOR generation; current.json must point at a vendored dir.

    A transport-suffixed current tree and its canonical same-dataVersion tree are
    one logical generation; only a distinct dataVersion counts as PRIOR. Every
    vendored generation directory is validated (name shape + manifest identity)
    before it is counted, so a malformed sibling can never pose as a PRIOR.

    Returns ``(current_data_version, prior_versions)`` (prior directory names).
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
    _validate_data_version(data_version)
    manifest_url = current.get("manifestUrl")
    if not isinstance(manifest_url, str) or not manifest_url.startswith("versions/"):
        raise VendorError("current.json.manifestUrl must start with versions/")
    current_dir = _pointed_version_dir(manifest_url, data_version)

    version_dirs = list_version_dirs(extract_root)
    if current_dir not in version_dirs:
        raise VendorError(
            f"current.json points at non-vendored generation {data_version!r}; "
            f"vendored: {version_dirs}"
        )
    expected_manifest = extract_root / "atlas" / manifest_url
    if not expected_manifest.is_file():
        raise VendorError(f"current.json manifestUrl missing on disk: {manifest_url}")
    try:
        pointed = json.loads(expected_manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VendorError(f"current.json manifestUrl target unreadable: {exc}") from exc
    if not isinstance(pointed, dict) or pointed.get("dataVersion") != data_version:
        raise VendorError(
            f"manifest at {manifest_url!r} does not carry dataVersion {data_version!r}"
        )

    priors = [name for name in version_dirs if _generation_version(extract_root, name) != data_version]
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


def _runtime_shard_records(
    version_root: Path,
    index: Mapping[str, Any],
    *,
    schema: str,
    data_version: str,
) -> Iterator[list[dict[str, Any]]]:
    """Read each pinned shard after checking its path, hashes and envelope.

    Search prefix shards replicate rows, so retain shard boundaries for duplicate
    detection. Entry shards partition routes and never replicate them.
    """
    for descriptor in index["shards"].values():
        rel = descriptor["url"]
        if (
            not isinstance(rel, str)
            or not rel
            or "\\" in rel
            or any(part in {"", ".", ".."} for part in rel.split("/"))
        ):
            raise VendorError("unsafe runtime shard path")
        path = version_root / rel
        blob = path.read_bytes()
        if (
            descriptor["encoding"] != "gzip"
            or len(blob) != descriptor["bytes"]
            or sha256_hex(blob) != descriptor["sha256"]
        ):
            raise VendorError(f"runtime shard compressed integrity mismatch: {rel}")
        size = descriptor["uncompressedBytes"]
        if not isinstance(size, int) or size < 0:
            raise VendorError(f"invalid runtime shard uncompressedBytes: {rel}")
        with gzip.GzipFile(fileobj=io_bytes_zip(blob)) as stream:
            raw = stream.read(size + 1)
        if len(raw) != size or sha256_hex(raw) != descriptor["jsonSha256"]:
            raise VendorError(f"runtime shard JSON integrity mismatch: {rel}")
        payload = json.loads(raw)
        if payload["schema"] != schema or payload["schemaVersion"] != 1 or payload["dataVersion"] != data_version:
            raise VendorError(f"runtime shard identity mismatch: {rel}")
        rows = payload["records"]
        if (
            not isinstance(rows, list)
            or len(rows) != descriptor["count"]
            or any(not isinstance(row, dict) for row in rows)
        ):
            raise VendorError(f"runtime shard records/count mismatch: {rel}")
        yield rows


def _discovery_exclusions(article_rows: list[dict[str, Any]]) -> tuple[set[str], list[str]]:
    """Apply reviewed holds to discovery without altering immutable routes."""
    policy = json.loads(DISCOVERY_EXCLUSIONS.read_bytes())
    if policy["schema"] != "atlas-discovery-exclusions" or policy["schemaVersion"] != 1:
        raise VendorError("invalid Atlas discovery exclusion schema")
    heads = {row["s"]: row["l"] for row in article_rows}
    withheld: set[str] = set()
    absent: list[str] = []
    seen: set[str] = set()
    for record in policy["exclusions"]:
        slug = record["slug"]
        if slug in seen or not record["headword"] or not record["reason"] or not record["evidence"]:
            raise VendorError("duplicate or incomplete Atlas discovery exclusion")
        seen.add(slug)
        if slug not in heads:
            absent.append(slug)
        elif heads[slug] != record["headword"]:
            raise VendorError(f"Atlas discovery exclusion headword changed: {slug}")
        else:
            withheld.add(slug)
    return withheld, sorted(absent)


def build_pinned_search(extract_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Project search from the installed pin, refusing full-set or alias drift.

    The immutable runtime owns routes. After full parity validation, reviewed
    discovery exclusions may withhold listings, never rewrite the pinned tree.
    """
    try:
        current = json.loads((extract_root / CURRENT_REL).read_bytes())
        data_version = current["dataVersion"]
        _validate_data_version(data_version)
        directory = _pointed_version_dir(current["manifestUrl"], data_version)
        version_root = extract_root / VERSIONS_REL / directory
        manifest_bytes = (version_root / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        if (
            manifest["schema"] != "atlas-runtime-manifest"
            or manifest["schemaVersion"] != 1
            or manifest["dataVersion"] != data_version
        ):
            raise VendorError("runtime manifest identity mismatch")
        routes: set[str] = set()
        articles: set[str] = set()
        forms: set[str] = set()
        public_fields: dict[str, tuple[str | None, str | None, str | None]] = {}
        for rows in _runtime_shard_records(
            version_root, manifest["entries"], schema="atlas-entry-shard", data_version=data_version
        ):
            for row in rows:
                slug = row["slug"]
                if not isinstance(slug, str) or not slug or slug in routes:
                    raise VendorError("invalid or duplicate runtime route slug")
                routes.add(slug)
                if row["kind"] == "article":
                    articles.add(slug)
                    entry = row.get("entry") or {}
                    public_fields[slug] = (classification_code(entry), _gerund_parent(entry), _search_gloss(entry))
                elif row["kind"] == "form_route":
                    forms.add(slug)
                else:
                    raise VendorError("unknown runtime route kind")

        families: dict[str, list[dict[str, Any]]] = {}
        replicas: dict[str, int] = {}
        for family, schema in (("articles", "atlas-search-article-shard"), ("aliases", "atlas-search-alias-shard")):
            unique: dict[Any, dict[str, Any]] = {}
            replicas[family] = 0
            for rows in _runtime_shard_records(
                version_root, manifest["search"][family], schema=schema, data_version=data_version
            ):
                local: set[Any] = set()
                for row in rows:
                    slug = row["s"]
                    fields = ("l", "r", "t") if family == "articles" else ("a", "h", "k")
                    if not isinstance(slug, str) or not slug or any(not isinstance(row[key], str) for key in fields):
                        raise VendorError(f"invalid runtime search {family} row")
                    key = slug if family == "articles" else (normalize_atlas_text(row["a"]), slug)
                    if key in local:
                        raise VendorError(f"duplicate runtime search {family} row within shard")
                    local.add(key)
                    if key in unique:
                        if unique[key] != row:
                            raise VendorError(f"conflicting runtime search {family} replicas")
                        replicas[family] += 1
                    else:
                        unique[key] = row
            families[family] = list(unique.values())
        search_slugs = {row["s"] for row in families["articles"]}
        advertised_only = sorted(search_slugs - articles)
        runtime_only = sorted(articles - search_slugs)
        if advertised_only or runtime_only:
            raise VendorError(
                "article search/runtime set mismatch: "
                + json.dumps(
                    {
                        "advertisedOnly": advertised_only,
                        "runtimeOnly": runtime_only,
                    },
                    ensure_ascii=False,
                )
            )
        if any(row["s"] not in articles for row in families["aliases"]):
            raise VendorError("runtime search alias target is not a runtime article")
        counts = manifest["counts"]
        for name, actual in (
            ("articles", len(articles)),
            ("formRoutes", len(forms)),
            ("publicRoutes", len(routes)),
            ("searchArticles", len(search_slugs)),
            ("searchAliases", len(families["aliases"])),
        ):
            if counts[name] != actual:
                raise VendorError(f"runtime {name} count mismatch: {counts[name]} != {actual}")
        article_rows = []
        for runtime_row in families["articles"]:
            row = dict(runtime_row)
            cls, parent, gloss = public_fields[row["s"]]
            # Use the raw payload's public gloss when present. New runtimes may
            # already qualify editorial notes; sanitizing those a second time
            # can truncate the qualification. Old pins still need projection.
            row["g"] = display_gloss(gloss or _sanitize_typeahead_gloss(row.get("g")), cls)
            row.pop("cls", None)
            row.pop("p", None)
            if cls:
                row["cls"] = cls
            if parent:
                row["p"] = parent
            article_rows.append(row)
        article_rows.sort(key=lambda row: (_uk_sort_key(row["l"]), row["s"]))
        aliases = sorted(families["aliases"], key=lambda row: (_uk_sort_key(row["a"]), row["s"], row["k"]))
        withheld, absent_exclusions = _discovery_exclusions(article_rows)
        projected_articles = [row for row in article_rows if row["s"] not in withheld]
        projected_aliases = [row for row in aliases if row["s"] not in withheld]
        return (
            projected_articles,
            projected_aliases,
            {
                "dataVersion": data_version,
                "runtimeManifestSha256": sha256_hex(manifest_bytes),
                "articles": len(articles),
                "formRoutes": len(forms),
                "aliases": len(aliases),
                "projectedArticles": len(projected_articles),
                "projectedAliases": len(projected_aliases),
                "withheldArticles": sorted(withheld),
                "withheldAliases": len(aliases) - len(projected_aliases),
                "absentExclusions": absent_exclusions,
                "advertisedOnly": advertised_only,
                "runtimeOnly": runtime_only,
                "articleDuplicates": 0,
                "runtimeDuplicates": 0,
                "aliasDuplicates": 0,
                "replicatedArticleRows": replicas["articles"],
                "replicatedAliasRows": replicas["aliases"],
            },
        )
    except (OSError, EOFError, ValueError, KeyError, TypeError, AttributeError, zlib.error) as exc:
        raise VendorError(f"pinned runtime search unreadable: {exc}") from exc



class AdvertisementParityError(VendorError):
    """Built advertisements contain links absent from the selected runtime."""

    def __init__(self, message: str, missing: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.missing = missing


def _read_advertisement(path: Path) -> Any:
    try:
        return json.loads(path.read_bytes())
    except (OSError, UnicodeError, ValueError) as exc:
        raise VendorError(f"advertised artifact {path.name} unreadable: {exc}") from exc


def _advertised_rows(doc: Any, key: str, name: str) -> set[str]:
    if not isinstance(doc, list) or any(
        not isinstance(row, dict) or not isinstance(row.get(key), str) or not row[key]
        for row in doc
    ):
        raise VendorError(f"advertised artifact {name} must list rows carrying {key!r}")
    return {row[key] for row in doc}


def _advertised_daily_rows(doc: Any, name: str) -> set[str]:
    _advertised_rows(doc, "slug", name)
    # daily-card and PracticeDailyDeck suppress links only for explicit false.
    return {row["slug"] for row in doc if row.get("hasAtlasEntry") is not False}


class _BrowseAdvertisements(HTMLParser):
    """Read the same embedded browse metadata and flagged rows as the browser."""

    def __init__(self) -> None:
        super().__init__()
        self.scopes: list[tuple[Any, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if "data-atlas-index" in attributes:
            try:
                self.scopes.append((json.loads(attributes["data-browse-meta"]),
                                    json.loads(attributes["data-flagged-rows"])))
            except (KeyError, TypeError, ValueError) as exc:
                raise VendorError("advertised browse metadata unreadable") from exc


def collect_advertised_slugs(lexicon_dir: Path) -> dict[str, set[str]]:
    """Collect independent built advertisements; search is replaced from the pin.

    Browse metadata advertises shard URLs/counts, not word slugs. Check those
    bindings and its embedded flagged rows, including a genuinely empty browse.
    Practice remains optional because its artifact is separately pinned.
    """
    advertised = {"daily-pool.json": _advertised_daily_rows(
        _read_advertisement(lexicon_dir / "daily-pool.json"), "daily-pool.json"
    )}
    for directory, prefix in ((lexicon_dir, ""), (lexicon_dir.parent / "api/lexicon", "api/")):
        for path in sorted(directory.glob("practice-lexemes.*.json")):
            doc = _read_advertisement(path)
            advertised[prefix + path.name] = _advertised_rows(
                doc.get("lexemes") if isinstance(doc, dict) else None, "lemmaId", prefix + path.name
            )
    api_daily = lexicon_dir.parent / "api/lexicon/daily-pool.json"
    if api_daily.exists():
        advertised["api/daily-pool.json"] = _advertised_daily_rows(
            _read_advertisement(api_daily), "api/daily-pool.json"
        )
    parser = _BrowseAdvertisements()
    try:
        parser.feed((lexicon_dir / "browse/index.html").read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise VendorError(f"advertised browse page unreadable: {exc}") from exc
    if not parser.scopes:
        raise VendorError("advertised browse metadata missing")
    browse: dict[str, tuple[bytes, int]] = {}
    for path in sorted(lexicon_dir.glob("browse/*.json")):
        blob = path.read_bytes()
        rows = _read_advertisement(path)
        advertised[f"browse/{path.name}"] = _advertised_rows(rows, "s", path.name)
        browse[f"/lexicon/browse/{path.name}"] = (blob, len(rows))
    for meta, flagged in parser.scopes:
        advertised.setdefault("browse-flagged", set()).update(
            _advertised_rows(flagged, "s", "browse-flagged")
        )
        try:
            if meta["schema"] != "atlas-browse-meta" or meta["schemaVersion"] != 1:
                raise VendorError("advertised browse metadata identity mismatch")
            descriptors = meta["browseShards"]
            if not isinstance(descriptors, dict):
                raise VendorError("advertised browseShards must be an object")
            expected: set[str] = set()
            for letter, descriptor in descriptors.items():
                url = f"/lexicon/browse/{letter}.json"
                if descriptor["path"] != url or url not in browse:
                    raise VendorError("advertised browse shard missing or mismatched")
                expected.add(url)
                blob, count = browse[url]
                if (descriptor["count"] != count or descriptor["bytes"] != len(blob)
                        or descriptor["sha256"] != sha256_hex(blob)
                        or meta["letterCounts"][letter] != count):
                    raise VendorError("advertised browse shard metadata mismatch")
            if (expected != set(browse) or meta["browseShardCount"] != len(browse)
                    or meta["total"] != sum(count for _, count in browse.values())
                    or any(count != (browse.get(f"/lexicon/browse/{letter}.json", (b"", 0))[1])
                           for letter, count in meta["letterCounts"].items())):
                raise VendorError("advertised browse metadata scope mismatch")
        except (KeyError, TypeError, AttributeError) as exc:
            raise VendorError("advertised browse metadata malformed") from exc
    return advertised


def verify_advertised_links_resolve(
    extract_root: Path, lexicon_dir: Path,
    articles: list[dict[str, Any]], aliases: list[dict[str, Any]],
) -> None:
    """Restore the full advertisement invariant before installing any output.

    Search/index/shards and alias targets use the already verified projection
    that will replace those endpoints. Independent advertisements must resolve
    in CURRENT, never merely in PRIOR. Alias text is not a route.
    """
    current = _read_advertisement(extract_root / CURRENT_REL)
    version_root = extract_root / VERSIONS_REL / _pointed_version_dir(
        current["manifestUrl"], current["dataVersion"]
    )
    manifest = _read_advertisement(version_root / "manifest.json")
    routes = {row["slug"] for rows in _runtime_shard_records(
        version_root, manifest["entries"], schema="atlas-entry-shard", data_version=current["dataVersion"]
    ) for row in rows}
    advertised = collect_advertised_slugs(lexicon_dir)
    advertised["search-index"] = {row["s"] for row in articles}
    advertised["search-aliases"] = {row["s"] for row in aliases}
    union = set().union(*advertised.values())
    missing = tuple(sorted(union - routes))
    if missing:
        by_artifact = ", ".join(f"{name}={len(slugs - routes)}" for name, slugs in sorted(advertised.items())
                                if slugs - routes)
        raise AdvertisementParityError(
            f"{len(missing)} of {len(union)} advertised Atlas slugs do not resolve in the pinned "
            f"runtime ({len(routes)} routes; per artifact: {by_artifact}); "
            "unresolvable advertised slugs:\n" + "\n".join(missing), missing,
        )
    print(f"advertisement parity: {len(union)} advertised slugs resolve in {len(routes)} runtime routes")


def install_pinned_search(dist: Path, articles: list[dict[str, Any]], aliases: list[dict[str, Any]]) -> None:
    """Replace built public search endpoints using the existing shard contract."""
    index = dist / "lexicon/search-index.json"
    write_index(articles, index)
    write_index(articles, dist / "api/lexicon/search-index.json")
    write_aliases(aliases, dist / "lexicon/search-aliases.json")
    manifest, shards = build_search_shards(articles)
    write_search_shards(manifest, shards, dist / "lexicon/search-shards.json", dist / "lexicon/search")


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
    advertised_links_dir: Path | None = None,
) -> VendorMetrics:
    """Download (or load), verify, and install the atlas tree into ``dist``.

    Raises :class:`VendorError` on any integrity / retention / scale failure.
    When no pin is configured, returns a skipped metrics object (exit 0 path).
    The Pages entrypoint supplies advertised_links_dir; library callers without
    a built site retain their runtime-only verification round-trip.
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
        resolved_repo = repo or os.environ.get("ATLAS_TREE_REPO") or os.environ.get("GITHUB_REPOSITORY") or DEFAULT_REPO
        archive_bytes = download_release_asset(asset_id, repo=resolved_repo, token=token)

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
        articles, aliases, search_parity = build_pinned_search(extract_root)
        if advertised_links_dir is not None:
            verify_advertised_links_resolve(extract_root, advertised_links_dir, articles, aliases)
        dist.mkdir(parents=True, exist_ok=True)
        install_atlas_tree(extract_root, dist)
        install_pinned_search(dist, articles, aliases)

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
        search_parity=search_parity,
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
    print(f"search_parity={json.dumps(metrics.search_parity, sort_keys=True)}")
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
            advertised_links_dir=args.dist / "lexicon",
        )
    except VendorError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"::error title=Atlas tree vendoring::{exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
