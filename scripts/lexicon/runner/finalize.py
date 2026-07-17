"""PR4 — leaf sealing handoff, streaming finalization, publication gate (#5230).

Implements ENRICH-RUNNER-SPEC-v2.md §Phase 8 + PR4-SPEC v2 (V1–V9):

1. Completion gate over current leaf chunks + constituent lemmas (V4)
2. Streaming assembly of sealed lemma artifacts into ``atlas/versions/<dataVersion>/``
3. Deterministic ZIP with fully normalized metadata (V3)
4. Publication handoff shape matching ``scripts/deploy/vendor_atlas_tree.py``
5. ``runFingerprint`` recorded in ``manifest.json`` (V6)
6. Temp-dir + atomic rename promotion (V7); single-writer finalize lock
7. ``finalize --dry-run`` operator report (V8/Q3)
8. One-time publication-gated first-run escape (V5)
9. Aggregate ledger queries only; bounded open FDs; scale pre-check (V9)

Out of scope (criterion 8): real release-asset upload / pin flip (#5138 class).
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import gzip
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
from collections.abc import Iterator, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scripts.deploy.vendor_atlas_tree import (
    DEFAULT_FAIL_EXTRACTED_BYTES,
    DEFAULT_WARN_EXTRACTED_BYTES,
    TREE_MANIFEST_REL,
    TREE_MANIFEST_SCHEMA,
    TREE_MANIFEST_SCHEMA_VERSION,
    VendorError,
    vendor_atlas_tree,
)
from scripts.lexicon.runner.contracts import (
    ENGINE_VERSION,
    SERIALIZATION_VERSION,
    canonical_json,
)
from scripts.lexicon.runner.deterministic_zip import (
    ZIP_WRITER_PIN,
    write_deterministic_zip,
)
from scripts.lexicon.runner.ledger import (
    CasStatus,
    DuplicateRunnerError,
    Ledger,
)

# Peak RSS ceiling for streaming assembly (PR4 criterion 2 / V2).
ASSEMBLY_RSS_CEILING_BYTES = 200 * 1024 * 1024  # 200 MiB


def _safe_rss_bytes() -> int | None:
    """Best-effort RSS for the 200 MiB assembly ceiling (telemetry + test assertion).

    Avoids the Darwin ctypes ``getrusage`` path in ``memory.current_rss_bytes``
    (incorrect timeval layout → SIGSEGV under load). Uses stdlib
    ``resource.getrusage`` only, with Linux KB→bytes conversion.
    """
    import platform
    import resource

    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss = int(usage.ru_maxrss)
    except (OSError, ValueError, AttributeError):
        return None
    if rss <= 0:
        return None
    # Linux reports KiB; macOS/BSD report bytes.
    if platform.system() == "Linux":
        return rss * 1024
    return rss

# Bounded concurrent open handles while writing shards (V9).
MAX_OPEN_SHARD_FDS = 8

# Entry-shard packing: keep shards small enough to stream; not the full 1 MiB
# runtime band — finalizer emits a runner-assembly tree, not a full atlas.db
# export. Vendor script only checks packaging/retention/scale, not entry schema.
DEFAULT_ENTRIES_PER_SHARD = 64

BOOTSTRAP_PRIOR_VERSION = "atlas-bootstrap-empty"
GENERATED_AT_PIN = "1970-01-01T00:00:00+00:00"

MANIFEST_SCHEMA = "atlas-runtime-manifest"
CURRENT_SCHEMA = "atlas-current"
ENTRY_SHARD_SCHEMA = "atlas-entry-shard"


class FinalizeError(RuntimeError):
    """Hard finalization failure — no partial tree is promoted."""


@dataclass(slots=True)
class DryRunReport:
    """Operator surface for ``finalize --dry-run`` (V8/Q3)."""

    run_id: str
    fingerprint: str | None
    gate_ok: bool
    gate_reasons: list[str] = field(default_factory=list)
    leaf_chunk_count: int = 0
    sealed_leaf_count: int = 0
    unsealed_leaf_count: int = 0
    unsealed_leaf_ids: list[str] = field(default_factory=list)
    constituent_lemma_count: int = 0
    unresolved_lemma_count: int = 0
    failed_terminal_count: int = 0
    non_terminal_count: int = 0
    estimated_payload_bytes: int = 0
    estimated_object_count: int = 0
    scale_warn_bytes: int = DEFAULT_WARN_EXTRACTED_BYTES
    scale_fail_bytes: int = DEFAULT_FAIL_EXTRACTED_BYTES
    scale_verdict: str = "unknown"
    prior_version_dir: str | None = None
    first_run_escape_required: bool = False
    first_run_escape_available: bool = False
    data_version_preview: str | None = None
    zip_writer_pin: dict[str, Any] = field(default_factory=lambda: dict(ZIP_WRITER_PIN))
    peak_rss_bytes: int | None = None
    rss_ceiling_bytes: int = ASSEMBLY_RSS_CEILING_BYTES

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FinalizeResult:
    ok: bool
    run_id: str
    fingerprint: str | None = None
    data_version: str | None = None
    archive_path: str | None = None
    archive_sha256: str | None = None
    tree_root: str | None = None
    detail: str = ""
    dry_run: DryRunReport | None = None
    peak_rss_bytes: int | None = None
    vendor_ok: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        if self.dry_run is not None:
            body["dry_run"] = self.dry_run.to_dict()
        return body


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _gzip_bytes(data: bytes, *, compression_level: int = 9) -> bytes:
    # mtime=0 — same discipline as export_runtime_shards.gzip_bytes.
    return gzip.compress(data, compresslevel=compression_level, mtime=0)


def _canonical_json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _atomic_replace_dir(src: Path, dest: Path) -> None:
    """Promote ``src`` directory to ``dest`` via same-partition rename (V7).

    Never leaves a partial ``dest`` visible: build fully under ``src``, then
    swap. If ``dest`` exists, it is moved aside and removed after success.
    """
    dest = Path(dest)
    src = Path(src)
    dest.parent.mkdir(parents=True, exist_ok=True)
    backup: Path | None = None
    if dest.exists():
        backup = dest.with_name(f".{dest.name}.bak-{os.getpid()}")
        if backup.exists():
            shutil.rmtree(backup)
        dest.rename(backup)
    try:
        src.rename(dest)
    except Exception:
        if backup is not None and backup.exists() and not dest.exists():
            backup.rename(dest)
        raise
    if backup is not None and backup.exists():
        shutil.rmtree(backup, ignore_errors=True)


class FinalizeLock:
    """Single-writer OS lock for the finalizer (criterion 7)."""

    def __init__(self, lock_path: Path, *, owner_id: str) -> None:
        self.lock_path = Path(lock_path)
        self.owner_id = owner_id
        self._fh: Any | None = None

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(self.lock_path, "a+", encoding="utf-8")  # noqa: SIM115
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            fh.close()
            raise DuplicateRunnerError(
                f"duplicate finalizer refused: lock held on {self.lock_path}"
            ) from exc
        fh.seek(0)
        fh.truncate()
        fh.write(f"{self.owner_id}\n{time.time():.6f}\n")
        fh.flush()
        self._fh = fh

    def release(self) -> None:
        if self._fh is not None:
            with contextlib.suppress(OSError):
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            self._fh.close()
            self._fh = None

    def __enter__(self) -> FinalizeLock:
        self.acquire()
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()


def resolve_artifact_path(
    artifacts_dir: Path,
    *,
    chunk_id: str,
    lemma_id: str,
) -> Path | None:
    """Locate a sealed lemma artifact (chunk-scoped or flat layout)."""
    candidates = (
        artifacts_dir / chunk_id / f"{lemma_id}.json",
        artifacts_dir / f"{lemma_id}.json",
        artifacts_dir / "lemmas" / f"{lemma_id}.json",
    )
    for path in candidates:
        if path.is_file():
            return path
    return None


def stream_lemma_payloads(
    ledger: Ledger,
    run_id: str,
    artifacts_dir: Path,
    *,
    phase: str = "offline_enrich",
) -> Iterator[tuple[str, dict[str, Any], str]]:
    """Yield ``(lemma_id, entry, content_sha256)`` in deterministic order.

    Streams one lemma at a time — never accumulates the full cohort (criterion 2).
    """
    rows = ledger.iter_sealed_leaf_lemmas(run_id, phase=phase)
    for row in rows:
        lemma_id = str(row["lemma_id"])
        chunk_id = str(row["chunk_id"])
        path = resolve_artifact_path(artifacts_dir, chunk_id=chunk_id, lemma_id=lemma_id)
        if path is None:
            raise FinalizeError(
                f"missing sealed lemma artifact for {lemma_id!r} (chunk={chunk_id})"
            )
        # Read + parse one file; do not retain prior entries.
        raw = path.read_bytes()
        digest = _sha256_bytes(raw)
        try:
            entry = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise FinalizeError(f"unreadable artifact {path}: {exc}") from exc
        if not isinstance(entry, dict):
            raise FinalizeError(f"artifact {path} must be a JSON object")
        yield lemma_id, entry, digest


def compute_data_version_from_digests(
    *,
    fingerprint: str,
    lemma_digests: Sequence[tuple[str, str]],
) -> str:
    """Content-addressed dataVersion from ordered (lemma_id, content_sha256)."""
    identity = {
        "engine_version": ENGINE_VERSION,
        "serialization_version": SERIALIZATION_VERSION,
        "run_fingerprint": fingerprint,
        "lemmas": [{"id": lid, "sha256": digest} for lid, digest in lemma_digests],
    }
    digest = _sha256_bytes(canonical_json(identity).encode("utf-8"))
    return f"atlas-v1-{digest[:16]}"


def estimate_artifacts_size(artifacts_dir: Path) -> tuple[int, int]:
    """Return ``(total_bytes, file_count)`` under artifacts_dir (for dry-run)."""
    total = 0
    count = 0
    if not artifacts_dir.is_dir():
        return 0, 0
    for path in artifacts_dir.rglob("*.json"):
        if path.is_file():
            count += 1
            total += path.stat().st_size
    return total, count


def build_dry_run_report(
    ledger: Ledger,
    run_id: str,
    *,
    artifacts_dir: Path,
    prior_version_dir: Path | None,
    grant_first_run_escape: bool,
    phase: str = "offline_enrich",
) -> DryRunReport:
    gate = ledger.assess_completion_gate(run_id, phase=phase)
    est_bytes, est_count = estimate_artifacts_size(artifacts_dir)
    # Prior generation (if any) adds to combined extracted size for scale check.
    prior_bytes = 0
    if prior_version_dir is not None and prior_version_dir.is_dir():
        for path in prior_version_dir.rglob("*"):
            if path.is_file():
                prior_bytes += path.stat().st_size
                est_count += 1
    combined = est_bytes + prior_bytes
    if combined >= DEFAULT_FAIL_EXTRACTED_BYTES:
        scale_verdict = "fail"
    elif combined >= DEFAULT_WARN_EXTRACTED_BYTES:
        scale_verdict = "warn"
    else:
        scale_verdict = "ok"

    first_run_required = prior_version_dir is None
    escape_consumed = ledger.first_run_escape_consumed()
    first_run_available = first_run_required and grant_first_run_escape and not escape_consumed

    # Preview dataVersion from sealed lemma digests without loading full bodies.
    data_version_preview: str | None = None
    fingerprint = gate.get("fingerprint")
    if gate["ok"] and fingerprint:
        digests: list[tuple[str, str]] = []
        for row in ledger.iter_sealed_leaf_lemmas(run_id, phase=phase):
            lemma_id = str(row["lemma_id"])
            chunk_id = str(row["chunk_id"])
            path = resolve_artifact_path(artifacts_dir, chunk_id=chunk_id, lemma_id=lemma_id)
            if path is None:
                digests = []
                break
            digests.append((lemma_id, _sha256_bytes(path.read_bytes())))
        if digests:
            data_version_preview = compute_data_version_from_digests(
                fingerprint=str(fingerprint),
                lemma_digests=digests,
            )

    return DryRunReport(
        run_id=run_id,
        fingerprint=None if fingerprint is None else str(fingerprint),
        gate_ok=bool(gate["ok"]),
        gate_reasons=list(gate.get("reasons") or []),
        leaf_chunk_count=int(gate.get("leaf_chunk_count") or 0),
        sealed_leaf_count=int(gate.get("sealed_leaf_count") or 0),
        unsealed_leaf_count=int(gate.get("unsealed_leaf_count") or 0),
        unsealed_leaf_ids=list(gate.get("unsealed_leaf_ids") or []),
        constituent_lemma_count=int(gate.get("constituent_lemma_count") or 0),
        unresolved_lemma_count=int(gate.get("unresolved_lemma_count") or 0),
        failed_terminal_count=int(gate.get("failed_terminal_count") or 0),
        non_terminal_count=int(gate.get("non_terminal_count") or 0),
        estimated_payload_bytes=combined,
        estimated_object_count=est_count,
        scale_verdict=scale_verdict,
        prior_version_dir=None if prior_version_dir is None else str(prior_version_dir),
        first_run_escape_required=first_run_required,
        first_run_escape_available=first_run_available,
        data_version_preview=data_version_preview,
        peak_rss_bytes=_safe_rss_bytes(),
    )


def _entry_shard_id(index: int) -> str:
    return f"p08-{index:02x}"


def _write_bootstrap_prior(versions_root: Path) -> str:
    """Minimal PRIOR generation so first-run archives satisfy vendor retention (V5)."""
    version = BOOTSTRAP_PRIOR_VERSION
    root = versions_root / version
    if root.exists():
        shutil.rmtree(root)
    shard_rel = "entries/p00-0.json.gz"
    payload = {
        "schema": ENTRY_SHARD_SCHEMA,
        "schemaVersion": 1,
        "dataVersion": version,
        "records": [],
        "note": "first-run bootstrap prior (publication-gated escape V5); not a real generation",
    }
    raw = _canonical_json_bytes(payload)
    compressed = _gzip_bytes(raw)
    shard_path = root / shard_rel
    shard_path.parent.mkdir(parents=True, exist_ok=True)
    shard_path.write_bytes(compressed)
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "schemaVersion": 1,
        "dataVersion": version,
        "generatedAt": GENERATED_AT_PIN,
        "runFingerprint": None,
        "bootstrap": True,
        "entries": {
            "tree": {"shardId": "p00-0"},
            "shards": {
                "p00-0": {
                    "id": "p00-0",
                    "url": shard_rel,
                    "count": 0,
                    "bytes": len(compressed),
                    "uncompressedBytes": len(raw),
                    "sha256": _sha256_bytes(compressed),
                    "jsonSha256": _sha256_bytes(raw),
                    "encoding": "gzip",
                }
            },
        },
        "search": {"articles": {"tree": {}, "shards": {}}, "aliases": {"tree": {}, "shards": {}}},
        "decks": {"levels": {}},
        "counts": {"entryShards": 1, "articles": 0, "publicRoutes": 0},
    }
    (root / "manifest.json").write_bytes(_canonical_json_bytes(manifest))
    return version


def _copy_prior_version(prior_dir: Path, versions_root: Path) -> str:
    """Copy a prior generation directory into versions/<name>/; return name."""
    prior_dir = Path(prior_dir)
    if not prior_dir.is_dir():
        raise FinalizeError(f"--prior-version-dir is not a directory: {prior_dir}")
    # Accept either .../versions/<name> or a dir that IS the version root.
    name = prior_dir.name
    if name in {".", ".."} or not name.strip():
        raise FinalizeError(f"invalid prior version dir name: {prior_dir}")
    dest = versions_root / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(prior_dir, dest)
    manifest = dest / "manifest.json"
    if not manifest.is_file():
        raise FinalizeError(
            f"prior version dir missing manifest.json: {prior_dir}"
        )
    return name


class BoundedShardWriter:
    """Write entry shards with a hard cap on open file descriptors (V9)."""

    def __init__(self, version_root: Path, *, max_open: int = MAX_OPEN_SHARD_FDS) -> None:
        self.version_root = version_root
        self.max_open = max(1, int(max_open))
        self._open: dict[str, Any] = {}
        self.descriptors: dict[str, dict[str, Any]] = {}
        self._buffers: dict[str, list[dict[str, Any]]] = {}
        self._raw_sizes: dict[str, int] = {}

    def add_record(self, shard_id: str, record: dict[str, Any]) -> None:
        if shard_id not in self._buffers:
            self._buffers[shard_id] = []
            self._raw_sizes[shard_id] = 0
        self._buffers[shard_id].append(record)

    def flush_all(self, *, data_version: str) -> None:
        # Sequential write — only one shard file open at a time (strict bound).
        for shard_id in sorted(self._buffers):
            records = self._buffers[shard_id]
            payload = {
                "schema": ENTRY_SHARD_SCHEMA,
                "schemaVersion": 1,
                "dataVersion": data_version,
                "records": records,
            }
            raw = _canonical_json_bytes(payload)
            compressed = _gzip_bytes(raw)
            rel = f"entries/{shard_id}.json.gz"
            path = self.version_root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            # open → write → close immediately (FD bound = 1 during write).
            with open(path, "wb") as fh:
                fh.write(compressed)
            self.descriptors[shard_id] = {
                "id": shard_id,
                "url": rel,
                "count": len(records),
                "bytes": len(compressed),
                "uncompressedBytes": len(raw),
                "sha256": _sha256_bytes(compressed),
                "jsonSha256": _sha256_bytes(raw),
                "encoding": "gzip",
            }
        self._buffers.clear()


def assemble_version_tree(
    *,
    ledger: Ledger,
    run_id: str,
    fingerprint: str,
    artifacts_dir: Path,
    tree_root: Path,
    prior_version_dir: Path | None,
    grant_first_run_escape: bool,
    first_run_escape_reason: str,
    entries_per_shard: int = DEFAULT_ENTRIES_PER_SHARD,
    phase: str = "offline_enrich",
    crash_mid_stream: bool = False,
    assert_rss_ceiling: bool = True,
) -> dict[str, Any]:
    """Stream sealed lemmas into a versioned atlas tree under ``tree_root/atlas``.

    Builds entirely under a temp dir sibling, then atomically renames into
    ``tree_root/atlas`` (V7). Never leaves a partial ``versions/<dataVersion>``
    at the final path.
    """
    artifacts_dir = Path(artifacts_dir)
    tree_root = Path(tree_root)
    tree_root.mkdir(parents=True, exist_ok=True)

    # Pre-scan digests for dataVersion (streaming — one file at a time).
    lemma_digests: list[tuple[str, str]] = []
    peak_rss = _safe_rss_bytes() or 0

    def _note_rss(*, force: bool = False, n: int = 0) -> None:
        nonlocal peak_rss
        if not force and n % 32 != 0:
            return
        rss = _safe_rss_bytes()
        if rss is None:
            return
        peak_rss = max(peak_rss, rss)
        if assert_rss_ceiling and rss > ASSEMBLY_RSS_CEILING_BYTES:
            raise FinalizeError(
                f"assembly RSS {rss} exceeded ceiling {ASSEMBLY_RSS_CEILING_BYTES} "
                f"({ASSEMBLY_RSS_CEILING_BYTES // (1024 * 1024)} MiB)"
            )

    for n, (lemma_id, _entry, digest) in enumerate(
        stream_lemma_payloads(ledger, run_id, artifacts_dir, phase=phase)
    ):
        lemma_digests.append((lemma_id, digest))
        _note_rss(n=n)

    if not lemma_digests:
        raise FinalizeError("no sealed lemma artifacts to assemble")

    data_version = compute_data_version_from_digests(
        fingerprint=fingerprint,
        lemma_digests=lemma_digests,
    )

    # Build into same-partition temp, promote via rename (V7).
    staging_parent = tree_root
    staging = Path(
        tempfile.mkdtemp(prefix=f".atlas-assemble-{data_version}-", dir=str(staging_parent))
    )
    try:
        atlas_staging = staging / "atlas"
        versions_root = atlas_staging / "versions"
        version_root = versions_root / data_version
        version_root.mkdir(parents=True, exist_ok=True)

        writer = BoundedShardWriter(version_root, max_open=MAX_OPEN_SHARD_FDS)
        shard_index = 0
        in_shard = 0
        current_shard = _entry_shard_id(shard_index)
        record_count = 0

        for lemma_id, entry, digest in stream_lemma_payloads(
            ledger, run_id, artifacts_dir, phase=phase
        ):
            if crash_mid_stream and record_count == max(1, len(lemma_digests) // 2):
                raise RuntimeError("injected crash: mid_stream_assembly")
            record = {
                "slug": lemma_id,
                "kind": "article",
                "entry": entry,
                "contentSha256": digest,
            }
            if in_shard >= entries_per_shard:
                shard_index += 1
                current_shard = _entry_shard_id(shard_index)
                in_shard = 0
            writer.add_record(current_shard, record)
            in_shard += 1
            record_count += 1
            _note_rss(n=record_count)

        writer.flush_all(data_version=data_version)
        _note_rss(force=True)

        # Prefix-free trivial tree: first shard as root pointer.
        shard_ids = sorted(writer.descriptors)
        tree_ptr = {"shardId": shard_ids[0]} if shard_ids else {}
        manifest: dict[str, Any] = {
            "schema": MANIFEST_SCHEMA,
            "schemaVersion": 1,
            "dataVersion": data_version,
            "generatedAt": GENERATED_AT_PIN,
            # V6: additive key; deploy schema must tolerate unknown keys.
            "runFingerprint": fingerprint,
            "engineVersion": ENGINE_VERSION,
            "serializationVersion": SERIALIZATION_VERSION,
            "counts": {
                "articles": record_count,
                "publicRoutes": record_count,
                "formRoutes": 0,
                "entryShards": len(shard_ids),
                "searchArticles": 0,
                "searchAliases": 0,
            },
            "entries": {
                "tree": tree_ptr,
                "shards": {sid: writer.descriptors[sid] for sid in shard_ids},
            },
            "search": {
                "articles": {"tree": {}, "shards": {}},
                "aliases": {"tree": {}, "shards": {}},
            },
            "decks": {"levels": {}},
            "zipWriter": ZIP_WRITER_PIN,
        }
        (version_root / "manifest.json").write_bytes(_canonical_json_bytes(manifest))

        # Prior generation retention (Q2 / V5).
        if prior_version_dir is not None:
            prior_name = _copy_prior_version(Path(prior_version_dir), versions_root)
            if prior_name == data_version:
                raise FinalizeError(
                    f"prior version name collides with current dataVersion {data_version}"
                )
        else:
            if not grant_first_run_escape:
                raise FinalizeError(
                    "no --prior-version-dir and no --grant-first-run-escape; "
                    "publish arc must supply prior or grant one-time first-run escape (V5)"
                )
            # Machine-checked: empty release history = no prior dir provided.
            escape = ledger.record_first_run_escape(
                run_id,
                first_run_escape_reason or "first-run publication gate (empty release history)",
                payload={
                    "proof": "no_prior_version_dir",
                    "data_version": data_version,
                },
            )
            if not escape.ok:
                raise FinalizeError(escape.detail)
            _write_bootstrap_prior(versions_root)

        current = {
            "schema": CURRENT_SCHEMA,
            "schemaVersion": 1,
            "dataVersion": data_version,
            "generatedAt": GENERATED_AT_PIN,
            "manifestUrl": f"versions/{data_version}/manifest.json",
            "runFingerprint": fingerprint,
        }
        (atlas_staging / "current.json").write_bytes(_canonical_json_bytes(current))

        # Scale pre-check on combined current+prior (V9) before promote.
        total_bytes = 0
        object_count = 0
        for path in atlas_staging.rglob("*"):
            if path.is_file():
                object_count += 1
                total_bytes += path.stat().st_size
        if total_bytes >= DEFAULT_FAIL_EXTRACTED_BYTES:
            raise FinalizeError(
                f"scale gate: combined tree {total_bytes} bytes ≥ fail "
                f"{DEFAULT_FAIL_EXTRACTED_BYTES} (vendor 800 MiB threshold)"
            )

        # Atomic promote of atlas/ into tree_root (V7).
        final_atlas = tree_root / "atlas"
        _atomic_replace_dir(atlas_staging, final_atlas)

        return {
            "data_version": data_version,
            "fingerprint": fingerprint,
            "record_count": record_count,
            "entry_shards": len(shard_ids),
            "tree_bytes": total_bytes,
            "object_count": object_count,
            "peak_rss_bytes": peak_rss,
            "atlas_root": str(final_atlas),
        }
    except Exception:
        # Discard staging; final tree_root/atlas untouched if promote never ran.
        shutil.rmtree(staging, ignore_errors=True)
        raise
    else:
        # Staging parent may still hold an empty temp dir shell after rename.
        shutil.rmtree(staging, ignore_errors=True)


def build_publication_archive(
    tree_root: Path,
    archive_path: Path,
) -> str:
    """Emit deterministic ZIP + self-listing ``tree-manifest.json`` (criterion 5).

    Shape matches ``vendor_atlas_tree.build_archive_from_tree`` / verify contract,
    but uses the V3-normalized zip writer for cross-platform byte equality.
    """
    tree_root = Path(tree_root)
    atlas = tree_root / "atlas"
    if not atlas.is_dir():
        raise FinalizeError(f"missing atlas tree at {atlas}")

    files: list[dict[str, Any]] = []
    for path in sorted(p for p in atlas.rglob("*") if p.is_file()):
        rel = path.relative_to(tree_root).as_posix()
        if rel == TREE_MANIFEST_REL:
            continue
        files.append({"path": rel, "bytes": path.stat().st_size})

    self_entry: dict[str, Any] = {"path": TREE_MANIFEST_REL, "bytes": 0}
    files_with_self = [*files, self_entry]
    manifest_bytes = b""
    for _ in range(8):
        body = {
            "schema": TREE_MANIFEST_SCHEMA,
            "schemaVersion": TREE_MANIFEST_SCHEMA_VERSION,
            "files": files_with_self,
        }
        manifest_bytes = (
            json.dumps(body, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")
        if self_entry["bytes"] == len(manifest_bytes):
            break
        self_entry["bytes"] = len(manifest_bytes)
    else:
        raise FinalizeError("failed to stabilize tree-manifest self size")

    manifest_path = tree_root / TREE_MANIFEST_REL
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(manifest_bytes)

    members: list[tuple[str, bytes]] = []
    for path in sorted(p for p in atlas.rglob("*") if p.is_file()):
        rel = path.relative_to(tree_root).as_posix()
        members.append((rel, path.read_bytes()))
    return write_deterministic_zip(archive_path, members)


def verify_fingerprint_in_tree(tree_root: Path, expected: str) -> None:
    """Refuse publication when manifest runFingerprint mismatches (criterion 6)."""
    current_path = tree_root / "atlas" / "current.json"
    if not current_path.is_file():
        raise FinalizeError("current.json missing after assembly")
    current = json.loads(current_path.read_text(encoding="utf-8"))
    manifest_url = current.get("manifestUrl")
    if not isinstance(manifest_url, str):
        raise FinalizeError("current.json missing manifestUrl")
    manifest_path = tree_root / "atlas" / manifest_url
    if not manifest_path.is_file():
        raise FinalizeError(f"manifest missing: {manifest_url}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    got = manifest.get("runFingerprint")
    if got != expected:
        raise FinalizeError(
            f"fingerprint mismatch refuses publication: "
            f"expected {expected}, got {got!r}"
        )
    current_fp = current.get("runFingerprint")
    if current_fp is not None and current_fp != expected:
        raise FinalizeError(
            f"current.json runFingerprint mismatch: expected {expected}, got {current_fp!r}"
        )


def finalize_run(
    *,
    ledger: Ledger,
    run_id: str,
    artifacts_dir: Path,
    out_dir: Path,
    archive_path: Path | None = None,
    prior_version_dir: Path | None = None,
    grant_first_run_escape: bool = False,
    first_run_escape_reason: str = "first-run publication gate (empty release history)",
    dry_run: bool = False,
    phase: str = "offline_enrich",
    entries_per_shard: int = DEFAULT_ENTRIES_PER_SHARD,
    verify_vendor: bool = True,
    crash_mid_stream: bool = False,
    assert_rss_ceiling: bool = True,
    expected_fingerprint: str | None = None,
) -> FinalizeResult:
    """Run completion gate + streaming assembly + publication archive.

    When ``dry_run`` is True, only the operator report is produced (no writes).
    """
    out_dir = Path(out_dir)
    artifacts_dir = Path(artifacts_dir)
    report = build_dry_run_report(
        ledger,
        run_id,
        artifacts_dir=artifacts_dir,
        prior_version_dir=prior_version_dir,
        grant_first_run_escape=grant_first_run_escape,
        phase=phase,
    )

    if dry_run:
        return FinalizeResult(
            ok=report.gate_ok and report.scale_verdict != "fail",
            run_id=run_id,
            fingerprint=report.fingerprint,
            detail="dry-run only",
            dry_run=report,
            peak_rss_bytes=report.peak_rss_bytes,
        )

    if not report.gate_ok:
        return FinalizeResult(
            ok=False,
            run_id=run_id,
            fingerprint=report.fingerprint,
            detail="completion gate refused: " + "; ".join(report.gate_reasons),
            dry_run=report,
        )

    if report.scale_verdict == "fail":
        return FinalizeResult(
            ok=False,
            run_id=run_id,
            fingerprint=report.fingerprint,
            detail=(
                f"scale gate fail: estimated {report.estimated_payload_bytes} bytes "
                f"≥ {report.scale_fail_bytes}"
            ),
            dry_run=report,
        )

    fingerprint = report.fingerprint
    if fingerprint is None:
        return FinalizeResult(
            ok=False, run_id=run_id, detail="run fingerprint missing", dry_run=report
        )
    if expected_fingerprint is not None and expected_fingerprint != fingerprint:
        return FinalizeResult(
            ok=False,
            run_id=run_id,
            fingerprint=fingerprint,
            detail=(
                f"fingerprint_mismatch_refused: expected {expected_fingerprint}, "
                f"ledger has {fingerprint}"
            ),
            dry_run=report,
        )

    lock = FinalizeLock(out_dir / ".finalize.lock", owner_id=ledger.owner_id)
    try:
        lock.acquire()
    except DuplicateRunnerError as exc:
        return FinalizeResult(
            ok=False,
            run_id=run_id,
            fingerprint=fingerprint,
            detail=str(exc),
            dry_run=report,
        )

    try:
        tree_root = out_dir / "tree"
        assembly = assemble_version_tree(
            ledger=ledger,
            run_id=run_id,
            fingerprint=fingerprint,
            artifacts_dir=artifacts_dir,
            tree_root=tree_root,
            prior_version_dir=prior_version_dir,
            grant_first_run_escape=grant_first_run_escape,
            first_run_escape_reason=first_run_escape_reason,
            entries_per_shard=entries_per_shard,
            phase=phase,
            crash_mid_stream=crash_mid_stream,
            assert_rss_ceiling=assert_rss_ceiling,
        )
        verify_fingerprint_in_tree(tree_root, fingerprint)

        if archive_path is None:
            archive_path = out_dir / "atlas-tree.zip"
        archive_path = Path(archive_path)
        digest = build_publication_archive(tree_root, archive_path)

        vendor_ok: bool | None = None
        if verify_vendor:
            # Integration happy path against the consumer contract (criterion 5).
            dist = out_dir / "vendor-dist"
            if dist.exists():
                shutil.rmtree(dist)
            dist.mkdir(parents=True)
            try:
                vendor_atlas_tree(
                    dist,
                    sha256=digest,
                    archive_path=archive_path,
                )
                vendor_ok = True
            except VendorError as exc:
                return FinalizeResult(
                    ok=False,
                    run_id=run_id,
                    fingerprint=fingerprint,
                    data_version=str(assembly["data_version"]),
                    archive_path=str(archive_path),
                    archive_sha256=digest,
                    tree_root=str(tree_root),
                    detail=f"vendor gate refused: {exc}",
                    dry_run=report,
                    peak_rss_bytes=int(assembly.get("peak_rss_bytes") or 0) or None,
                    vendor_ok=False,
                )

        ledger.record_finalize(
            run_id,
            data_version=str(assembly["data_version"]),
            archive_sha256=digest,
            fingerprint=fingerprint,
            payload={
                "record_count": assembly["record_count"],
                "entry_shards": assembly["entry_shards"],
                "tree_bytes": assembly["tree_bytes"],
            },
        )

        return FinalizeResult(
            ok=True,
            run_id=run_id,
            fingerprint=fingerprint,
            data_version=str(assembly["data_version"]),
            archive_path=str(archive_path),
            archive_sha256=digest,
            tree_root=str(tree_root),
            detail="finalized",
            dry_run=report,
            peak_rss_bytes=int(assembly.get("peak_rss_bytes") or 0) or None,
            vendor_ok=vendor_ok,
        )
    except Exception as exc:
        return FinalizeResult(
            ok=False,
            run_id=run_id,
            fingerprint=fingerprint,
            detail=f"{type(exc).__name__}: {exc}",
            dry_run=report,
            peak_rss_bytes=_safe_rss_bytes(),
        )
    finally:
        lock.release()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Runner PR4: completion gate + streaming finalization + publication archive",
    )
    parser.add_argument("--ledger", type=Path, required=True, help="Path to run ledger SQLite")
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        required=True,
        help="Directory of sealed lemma artifacts (chunk subdirs or flat)",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Output directory for tree/ + archive + lock",
    )
    parser.add_argument(
        "--archive-path",
        type=Path,
        default=None,
        help="Publication ZIP path (default: <out-dir>/atlas-tree.zip)",
    )
    parser.add_argument(
        "--prior-version-dir",
        type=Path,
        default=None,
        help="Prior generation dir supplied by publish arc (Q2); offline runner never downloads",
    )
    parser.add_argument(
        "--grant-first-run-escape",
        action="store_true",
        help=(
            "One-time publication-gated authorization for empty release history (V5). "
            "Not a reusable repo variable; consumed into the ledger on success."
        ),
    )
    parser.add_argument(
        "--first-run-escape-reason",
        default="first-run publication gate (empty release history)",
        help="Audited reason recorded with the one-time first-run escape",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Emit ledger health / gate / size / fingerprint report only (V8/Q3)",
    )
    parser.add_argument(
        "--expected-fingerprint",
        default=None,
        help="Refuse if ledger fingerprint does not match",
    )
    parser.add_argument(
        "--phase",
        default="offline_enrich",
        help="Work-unit phase for completion closure (default: offline_enrich)",
    )
    parser.add_argument(
        "--entries-per-shard",
        type=int,
        default=DEFAULT_ENTRIES_PER_SHARD,
    )
    parser.add_argument(
        "--skip-vendor-verify",
        action="store_true",
        help="Skip in-process vendor_atlas_tree round-trip (still emits archive)",
    )
    parser.add_argument(
        "--no-rss-ceiling",
        action="store_true",
        help="Disable 200 MiB RSS assertion (tests only)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    ledger = Ledger(args.ledger)
    try:
        ledger.open(create=False)
    except Exception:
        # Allow create for fresh test ledgers when file exists but was just made.
        ledger.open(create=True)

    try:
        result = finalize_run(
            ledger=ledger,
            run_id=args.run_id,
            artifacts_dir=args.artifacts_dir,
            out_dir=args.out_dir,
            archive_path=args.archive_path,
            prior_version_dir=args.prior_version_dir,
            grant_first_run_escape=args.grant_first_run_escape,
            first_run_escape_reason=args.first_run_escape_reason,
            dry_run=args.dry_run,
            phase=args.phase,
            entries_per_shard=args.entries_per_shard,
            verify_vendor=not args.skip_vendor_verify,
            assert_rss_ceiling=not args.no_rss_ceiling,
            expected_fingerprint=args.expected_fingerprint,
        )
    finally:
        ledger.close()

    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
