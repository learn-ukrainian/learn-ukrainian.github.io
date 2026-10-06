"""Preserve ignored task output before automatic worktree removal (#9645)."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from scripts.fleet.regenerable_output import is_regenerable_ignored_path
from scripts.orchestration import worktree_artifacts as artifacts
from scripts.orchestration.task_record_store import task_record_path

# Bound automatic disk duplication. Larger outputs require owner disposition;
# the complete source checkout survives rather than receiving a partial copy.
MAX_PRESERVED_BYTES = 256 * 1024 * 1024

_IDENTITY_KEYS = ("worktree_path", "cwd", "acp_runtime_paths", "keep_worktree", "worktree_reused")
_IDENTITY_CACHE_SCHEMA = "worktree-record-identities.v1"


def _identity_cache_path(tasks_dir: Path) -> Path:
    # Not *.json: the cache must never become part of the task inventory.
    return tasks_dir / ".worktree-record-identities.cache"


def _identity_decoder_context() -> dict[str, Any]:
    # A previously valid record may become corrupt under a different int limit.
    return {
        "python": list(sys.version_info[:3]),
        "int_max_str_digits": getattr(sys, "get_int_max_str_digits", lambda: 0)(),
    }


def _read_identity_cache(path: Path) -> dict[str, Any]:
    """A missing, stale-format or damaged accelerator supplies no evidence."""
    try:
        cache = json.loads(path.read_bytes())
        entries = cache["entries"]
        if (
            cache["schema"] == _IDENTITY_CACHE_SCHEMA
            and cache.get("decoder") == _identity_decoder_context()
            and isinstance(entries, dict)
            and cache["sha256"] == hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
        ):
            return entries
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        pass
    return {}


def _write_identity_cache(path: Path, entries: dict[str, Any]) -> None:
    """Publish atomically without another lock; concurrent stale writers are safe.

    Every hit is checked against the current source bytes. Losing a cache update
    only causes another parse, so neither a cache lock nor task-writer changes
    are needed. Cache I/O failure never changes task-inventory semantics.
    """
    temporary = None
    try:
        encoded = json.dumps(entries, sort_keys=True).encode()
        cache = {
            "schema": _IDENTITY_CACHE_SCHEMA,
            "decoder": _identity_decoder_context(),
            "entries": entries,
            "sha256": hashlib.sha256(encoded).hexdigest(),
        }
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".record-identities-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(cache).encode())
        os.replace(temporary, path)
    except (OSError, ValueError, TypeError, RecursionError):
        pass
    finally:
        if temporary is not None:
            with contextlib.suppress(OSError):
                temporary.unlink()


class _InventoryReadError(ValueError):
    def __init__(self, path: Path, *, missing: bool = False):
        super().__init__("task identity inventory unreadable")
        self.path = path
        self.missing = missing


def resolve_worktree_record(
    worktree: Path, tasks_dir: Path, *, repo_root: Path, publish_cache: bool = True
) -> tuple[Path | None, dict[str, Any]]:
    """Retry one complete inventory after a concurrent record move or rewrite.

    Atomic replacement at the same name does not expose partial JSON, but
    delegate's redispatch archive and stale_task_records' staging move can
    remove a filename between glob and open. Never simply omit a failed read.
    A vanished name needs a visible archive counterpart before retrying.
    ``publish_cache=False`` suppresses publication on both inventory attempts.
    """
    try:
        return _resolve_worktree_record_once(worktree, tasks_dir, repo_root=repo_root, publish_cache=publish_cache)
    except _InventoryReadError as exc:
        print("Task identity inventory read failed; retrying complete inventory once", file=sys.stderr)
        return _resolve_worktree_record_once(
            worktree,
            tasks_dir,
            repo_root=repo_root,
            publish_cache=publish_cache,
            missing_path=exc.path if exc.missing else None,
        )


def _resolve_worktree_record_once(
    worktree: Path,
    tasks_dir: Path,
    *,
    repo_root: Path,
    publish_cache: bool = True,
    missing_path: Path | None = None,
) -> tuple[Path | None, dict[str, Any]]:
    """Resolve identity from canonical records, never from a caller's hint.

    Inspect hot and archived records: a different filename, renamed tree, or
    optional task argument cannot hide a retention claim. Ambiguity fails closed.
    A sole force-new archived creator may bind a same-task canonical reused run.
    A content-verified cache bounds JSON decoding to changed/candidate records;
    all source files are still read, and filesystem aliases are resolved anew.
    ``publish_cache=False`` keeps cache reads but never creates or updates it.
    """
    from scripts.orchestration.worktree_claims import (
        is_superseded_record,
        record_may_claim_worktree,
        worktree_claim_needles,
    )

    matches = []
    needles = worktree_claim_needles(worktree, worktree.resolve())
    try:
        resolved_worktree = worktree.resolve(strict=True)
    except (OSError, ValueError, RuntimeError):
        resolved_worktree = None
    claim_paths: dict[str, Path] = {}
    cache_path = _identity_cache_path(tasks_dir)
    cached = _read_identity_cache(cache_path)
    identities = {}
    changed = False
    inventory = [("", path) for path in sorted(tasks_dir.glob("*.json"))] + [
        ("archive/", path) for path in sorted((tasks_dir / "archive").glob("*.json"))
    ]
    if missing_path is not None and not any(
        path == missing_path
        or (prefix == "archive/" and path.name == missing_path.name)
        or (
            prefix == ""
            and re.fullmatch(
                re.escape(missing_path.stem) + r"\.\d{8}T\d{6}\d*Z(?:\.\d+)?\.archived\.json", path.name
            )
        )
        for prefix, path in inventory
    ):
        raise _InventoryReadError(missing_path, missing=True)
    for prefix, path in inventory:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise _InventoryReadError(path, missing=isinstance(exc, FileNotFoundError)) from None
        digest = hashlib.sha256(raw).hexdigest()
        name = prefix + path.name
        entry = cached.get(name)
        hit = (
            isinstance(entry, dict)
            and entry.get("source_sha256") == digest
            and isinstance(entry.get("identity"), dict)
            and set(entry["identity"]) == set(_IDENTITY_KEYS)
        )
        try:
            record = entry["identity"] if hit else json.loads(raw)
        except ValueError:
            # Reuse the claim owner's existing released-record proof only for
            # corrupt records with no possible retention key. Valid records,
            # including released symlink aliases, are always resolved below.
            if record_may_claim_worktree(raw, needles) or b'"keep_worktree"' in raw:
                raise _InventoryReadError(path) from None
            continue
        identity = (
            {key: record.get(key) for key in _IDENTITY_KEYS}
            if isinstance(record, dict)
            else dict.fromkeys(_IDENTITY_KEYS)
        )
        identities[name] = {"source_sha256": digest, "identity": identity}
        changed |= not hit
        if isinstance(record, dict):
            if resolved_worktree is not None and _record_matches_worktree(
                record, worktree, repo_root=repo_root, resolved_worktree=resolved_worktree, claim_paths=claim_paths
            ):
                if hit:
                    record = json.loads(raw)  # Return the complete canonical record, never its projection.
                matches.append((path, record))
            elif (
                resolved_worktree is not None
                and record.get("keep_worktree")
                and _record_matches_worktree(
                    {"cwd": record.get("cwd")},
                    worktree,
                    repo_root=repo_root,
                    resolved_worktree=resolved_worktree,
                    claim_paths=claim_paths,
                )
            ):
                raise ValueError("ambiguous retention task binding")
    if publish_cache and (changed or cached.keys() != identities.keys()):
        _write_identity_cache(cache_path, identities)
    if len(matches) > 1:
        kept = [match for match in matches if match[1].get("keep_worktree")]
        if len(kept) == 1:
            return kept[0]
        if kept:
            raise ValueError("ambiguous worktree task attribution with retention intent")
        # Finished references alone are not ownership. Without one creator,
        # output retains unknown attribution; empty trees remain removable.
        creators = [match for match in matches if match[1].get("worktree_reused") is False]
        if len(creators) == 1 and is_superseded_record(creators[0][0]):
            identity = creators[0][1].get("task_id")
            if isinstance(identity, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", identity):
                canonical = task_record_path(tasks_dir, identity)
                current = [match for match in matches if match[0] == canonical]
                if (
                    len(current) == 1
                    and current[0][1].get("worktree_reused") is True
                    and all(match[1].get("task_id") == identity for match in matches)
                    and creators[0][0].parent == tasks_dir
                    and re.fullmatch(
                        re.escape(identity) + r"\.\d{8}T\d{6}\d*Z(?:\.\d+)?\.archived\.json", creators[0][0].name
                    )
                ):
                    return current[0]
        return creators[0] if len(creators) == 1 else (None, {})
    return matches[0] if matches else (None, {})


def creation_inventory(worktree: Path, *, primary: Path, task_id: str, run_nonce: str) -> dict[str, Any]:
    """Capture under delegate's existing per-worktree lock before worker spawn."""
    try:
        files = _ignored_output_files(worktree, primary, {})
        status = worktree.stat()
        paths = _path_inventory(worktree, files)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        raise ValueError(f"creation inventory unavailable ({type(exc).__name__}); worker not started") from exc
    return {
        "schema": "ignored-baseline.v1",
        "task_id": task_id,
        "run_nonce": run_nonce,
        "directory_identity": [status.st_dev, status.st_ino],
        "paths": paths,
    }


def _record_absence(root: Path, name: str, absent: list[dict[str, str]]) -> None:
    """Only a fresh lstat ENOENT licenses omission, under the remover's lock."""
    try:
        (root / name).lstat()
    except FileNotFoundError:
        proof = {"path": name, "proof": "lstat_enoent"}
        if proof not in absent:
            absent.append(proof)
        return
    raise ValueError("ignored output changed during preservation")


def _baseline_entry_ok(entry: Mapping[str, Any]) -> bool:
    """Accept a regular-file fingerprint or a symlink link record."""
    if not isinstance(entry, Mapping):
        return False
    keys = set(entry)
    size = entry.get("size")
    digest = entry.get("sha256")
    if (
        not isinstance(entry.get("path"), str)
        or not isinstance(size, int)
        or size < 0
        or not isinstance(digest, str)
        or re.fullmatch(r"[a-f0-9]{64}", digest) is None
    ):
        return False
    if keys == {"path", "size", "sha256"}:
        return True
    return (
        keys == {"path", "type", "target", "size", "sha256"}
        and entry.get("type") == "symlink"
        and isinstance(entry.get("target"), str)
    )


def _path_inventory(
    root: Path, files: list[str], *, absent: list[dict[str, str]] | None = None
) -> list[dict[str, Any]]:
    """Fingerprint each path. A symlink records its raw target and is not opened."""
    entries = []
    for name in files:
        path = root / name
        try:
            is_link = path.is_symlink()
        except FileNotFoundError:
            if absent is None:
                raise
            _record_absence(root, name, absent)
            continue
        try:
            size, digest = artifacts._fingerprint(path, root=root)
        except FileNotFoundError:
            if absent is None:
                raise
            _record_absence(root, name, absent)
            continue
        entry: dict[str, Any] = {"path": name, "size": size, "sha256": digest}
        if is_link:
            entry["type"] = "symlink"
            entry["target"] = os.readlink(path)
        entries.append(entry)
    return entries


def _classified_inventory(
    worktree: Path, files: list[str], record: Mapping[str, Any], *, absent: list[dict[str, str]] | None = None
) -> list[dict[str, Any]]:
    baseline = record.get("ignored_output_baseline")
    status = worktree.stat()
    trusted = (
        isinstance(baseline, dict)
        and baseline.get("schema") == "ignored-baseline.v1"
        and record.get("worktree_reused") is False
        and baseline.get("task_id") == record.get("task_id")
        and bool(record.get("run_nonce"))
        and baseline.get("run_nonce") == record.get("run_nonce")
        and baseline.get("directory_identity") == [status.st_dev, status.st_ino]
        and isinstance(baseline.get("paths"), list)
    )
    before = {}
    if trusted:
        try:
            before = {entry["path"]: entry for entry in baseline["paths"]}
            if len(before) != len(baseline["paths"]) or any(
                not _baseline_entry_ok(entry) for entry in before.values()
            ):
                trusted = False
        except (KeyError, TypeError):
            trusted = False
    entries = _path_inventory(worktree, files, absent=absent)
    for entry in entries:
        entry["class"] = (
            ("pre_existing" if before.get(entry["path"]) == entry else "task_created")
            if trusted
            else "unknown_baseline"
        )
    return entries


def verify_retrieval(primary: Path, receipt: Mapping[str, Any]) -> str:
    """Retrieve every preserved file and independently verify names, sizes, bytes."""
    relative = Path(receipt["location"])
    if relative.is_absolute() or ".." in relative.parts or not relative.is_relative_to("batch_state/preserved"):
        raise ValueError("invalid retrieval location")
    location = primary / relative
    if location.resolve(strict=True) != location.absolute():
        raise ValueError("linked retrieval location")
    paths = receipt["paths"]
    names = [entry["path"] for entry in paths]
    if any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
        raise ValueError("invalid retrieval path")
    entries = list(location.rglob("*"))
    if any(entry.is_symlink() for entry in entries):
        raise ValueError("linked retrieval entry")
    if sorted(entry.relative_to(location).as_posix() for entry in entries if not entry.is_dir()) != names:
        raise ValueError("retrieval inventory mismatch")
    if _path_inventory(location, names) != [{key: entry[key] for key in ("path", "size", "sha256")} for entry in paths]:
        raise ValueError("retrieval bytes mismatch")
    digest = _content_digest(location, names)
    if digest != receipt["content_sha256"]:
        raise ValueError("retrieval digest mismatch")
    return digest


def _ignored_output_files(
    worktree: Path, primary: Path, record: Mapping[str, Any], *, absent: list[dict[str, str]] | None = None
) -> list[str]:
    """Inventory output, including unignored files when no index was checked out."""
    # Retain the existing named-link safety checks and nested-repository gates.
    named = artifacts._named_artifact_files(worktree, record, primary=primary)
    names = artifacts._git_paths(worktree, "--others", "--ignored", "--exclude-standard")
    tracked = set(artifacts._git_paths(worktree, "--cached"))
    if not tracked:
        # --no-checkout leaves an empty index and no on-disk .gitignore.
        # Unignored scratch can be task output too; inventory both classes.
        names += artifacts._git_paths(worktree, "--others", "--exclude-standard")
    files: set[str] = set()
    for name in names:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("ignored output inventory escaped worktree")
        if artifacts.is_disposable_path(relative, worktree=worktree, primary=primary):
            continue
        source = worktree / relative
        try:
            if is_regenerable_ignored_path(name, worktree=worktree, tracked=tracked):
                continue
            status = source.lstat()
            if stat.S_ISLNK(status.st_mode):
                # The link is the output. Resolving it follows the target: an
                # internal link was dropped, and a dangling link raised
                # FileNotFoundError that _record_absence then contradicted with
                # lstat ("changed during preservation").
                files.add(name)
                continue
            if source.resolve(strict=True) != source.absolute():
                raise ValueError("ignored output is not a local regular file")
            if stat.S_ISDIR(status.st_mode):
                files.update(artifacts._inspect_directory_artifact(source, name, worktree=worktree))
                source.lstat()
            elif stat.S_ISREG(status.st_mode):
                files.add(name)
            else:
                raise ValueError("ignored output is not a regular file")
        except FileNotFoundError:
            if absent is None:
                raise
            _record_absence(worktree, name, absent)
    files.update(named)
    return sorted(
        name
        for name in files
        if not artifacts.is_disposable_path(Path(name), worktree=worktree, primary=primary)
        and not is_regenerable_ignored_path(name, worktree=worktree, tracked=tracked)
    )


def _record_matches_worktree(
    record: Mapping[str, Any],
    worktree: Path,
    *,
    repo_root: Path,
    resolved_worktree: Path | None = None,
    claim_paths: dict[str, Path] | None = None,
) -> bool:
    """Task names are hints; only resolved filesystem identity binds a record."""
    from scripts.orchestration.worktree_claims import resolve_claim_path

    if resolved_worktree is None:
        try:
            resolved_worktree = worktree.resolve(strict=True)
        except (OSError, ValueError, RuntimeError):
            return False
    locations = [record.get("worktree_path") or record.get("cwd")]
    runtime_paths = record.get("acp_runtime_paths")
    if isinstance(runtime_paths, list):
        locations.extend(runtime_paths)
    for location in locations:
        if not isinstance(location, str) or not location:
            continue
        try:
            claimed = claim_paths.get(location) if claim_paths is not None else None
            if claimed is None:
                claimed = resolve_claim_path(location, repo_root=repo_root)
                if claim_paths is not None:
                    claim_paths[location] = claimed
            if claimed == resolved_worktree:
                return True
        except (OSError, ValueError, RuntimeError):
            continue
    return False


def _update_bound_task_record(
    path: Path,
    worktree: Path,
    updates: Mapping[str, Any],
    *,
    repo_root: Path,
    clear: tuple[str, ...] = (),
    expected_record: Mapping[str, Any] | None = None,
) -> bool:
    """Recheck binding under the writer lock, including re-dispatch during copying."""
    with artifacts.task_state_lock(path):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return False
        if not isinstance(record, dict):
            raise ValueError("task record is not an object")
        if not _record_matches_worktree(record, worktree, repo_root=repo_root):
            return False
        if expected_record is not None and any(
            record.get(key) != expected_record.get(key) for key in ("task_id", "run_nonce")
        ):
            return False
        record.update(updates)
        for key in clear:
            record.pop(key, None)
        artifacts.reaper_lifecycle._atomic_write(path, record)
        return True


def _content_digest(root: Path, files: list[str]) -> str:
    """Hash ordered names, sizes and bytes. A symlink contributes its link record only."""
    entries = []
    for name in files:
        source = root / name
        status = source.lstat()
        if not stat.S_ISLNK(status.st_mode) and (
            source.resolve(strict=True) != source.absolute() or not stat.S_ISREG(status.st_mode)
        ):
            raise ValueError("preserved artifact is not a local regular file")
        entries.append((name, *artifacts._fingerprint(source, root=root)))
    return hashlib.sha256(json.dumps(entries, ensure_ascii=True).encode()).hexdigest()


def _reusable_copy(parent: Path, worktree: Path, files: list[str], digest: str) -> Path | None:
    """A manifest is a locator; verify the complete copy's names and bytes again."""
    for manifest in sorted(parent.glob("*.manifest.json")):
        try:
            saved = json.loads(manifest.read_text(encoding="utf-8"))
            if (
                not isinstance(saved, dict)
                or saved.get("worktree_sha256") != hashlib.sha256(str(worktree).encode()).hexdigest()
            ):
                continue
            if saved.get("content_sha256") != digest:
                continue
            location = manifest.with_name(manifest.name.removesuffix(".manifest.json"))
            if location.resolve(strict=True) != location.absolute():
                continue
            entries = list(location.rglob("*"))
            if any(entry.is_symlink() for entry in entries):
                continue
            names = sorted(entry.relative_to(location).as_posix() for entry in entries if not entry.is_dir())
            if names == files and _content_digest(location, files) == digest:
                return location
        except (OSError, ValueError, RuntimeError):
            continue  # Invalid or incomplete attempts never license removal.
    return None


def preserve_worktree_artifacts(
    worktree: Path,
    *,
    primary: Path,
    task_id: str | None,
    tasks_dir: Path,
    task_record: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Mandatory preservation and retention gate, under the remover's lock.

    Decision B inventories everything without a clock cutoff. Baselines only
    label provenance; they never reduce the copied set. No canonical attribution,
    oversized output, failed retrieval, or explicit retention refuses removal.
    Vanished paths require fresh lstat absence proof; byte changes still refuse.
    Caller records and task IDs are hints, never retention authority.
    """
    from scripts.orchestration.worktree_claims import identity_cache_publication_allowed

    repo_root = primary if repo_root is None else repo_root
    record_path = None
    record: dict[str, Any] = {}
    metadata: dict[str, Any] = {
        "retention_disposition": "retained",
        "owner": "infra lane",
        "next_condition": "establish canonical task attribution and verified retrieval",
    }
    absent: list[dict[str, str]] = []
    try:
        worktree = worktree.resolve(strict=True)
        primary = primary.resolve(strict=True)
        record_path, record = resolve_worktree_record(
            worktree,
            tasks_dir,
            repo_root=repo_root,
            publish_cache=identity_cache_publication_allowed(worktree, tasks_dir),
        )
        files = _ignored_output_files(worktree, primary, record, absent=absent)
        if not files and not absent and not record.get("keep_worktree"):
            return True, "", None
        identity = record.get("task_id")
        paths = _classified_inventory(worktree, files, record, absent=absent)
        files = [entry["path"] for entry in paths]
        metadata.update(
            {
                "count": len(files),
                "bytes": sum(entry["size"] for entry in paths),
                "paths": paths,
                "absent_paths": absent,
            }
        )
        if (
            not isinstance(identity, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", identity)
            or record_path
            not in (task_record_path(tasks_dir, identity), task_record_path(tasks_dir / "archive", identity))
        ):
            raise ValueError("missing canonical task attribution")
        metadata.update(
            {
                "owner": identity,
                "task_id": identity,
                "run_nonce": record.get("run_nonce"),
                "worktree_sha256": hashlib.sha256(str(worktree).encode()).hexdigest(),
            }
        )
        total_bytes = metadata["bytes"]
        if total_bytes > MAX_PRESERVED_BYTES:
            metadata["next_condition"] = "owner retrieves output exceeding the preservation cap"
            raise ValueError(f"ignored output exceeds preservation cap ({total_bytes} > {MAX_PRESERVED_BYTES} bytes)")
        if files or absent or record.get("keep_worktree"):
            parent = primary / "batch_state" / "preserved" / identity
            if parent.is_relative_to(worktree):
                raise ValueError("preservation destination is inside the worktree")
            # Bind copying to the original inventory, including mutations before
            # _copy_verified takes its own source fingerprint.
            digest = hashlib.sha256(
                json.dumps([(entry["path"], entry["size"], entry["sha256"]) for entry in paths]).encode()
            ).hexdigest()
            location = _reusable_copy(parent, worktree, files, digest)
            reused = location is not None
            if location is None:
                location = parent / uuid.uuid4().hex
                metadata["next_condition"] = "owner completes verified copy and retrieval"
                location.mkdir(parents=True, exist_ok=False)
                for name in files:
                    destination = location / name
                    if destination.resolve() != destination.absolute():
                        raise ValueError("preserved artifact destination contains a symlink")
                    try:
                        artifacts._copy_verified(
                            worktree / name,
                            destination,
                            source_root=worktree,
                            destination_root=location,
                        )
                    except FileNotFoundError:
                        _record_absence(worktree, name, absent)
                        # A destination-side failure is not source absence proof.
                        if destination.exists() or destination.is_symlink():
                            raise
                        continue
                paths = [entry for entry in paths if entry["path"] not in {proof["path"] for proof in absent}]
                files = [entry["path"] for entry in paths]
                metadata.update(count=len(files), bytes=sum(entry["size"] for entry in paths), paths=paths)
                digest = _content_digest(location, files)
                if _path_inventory(location, files) != [
                    {key: entry[key] for key in ("path", "size", "sha256")} for entry in paths
                ]:
                    raise ValueError("ignored output changed during preservation")
            metadata.update(
                {"location": location.relative_to(primary).as_posix(), "content_sha256": digest, "reused": reused}
            )
            metadata["next_condition"] = "owner repairs failed retrieval and verifies all bytes"
            metadata["retrieval_proof_sha256"] = verify_retrieval(primary, metadata)
            if (
                files != _ignored_output_files(worktree, primary, record, absent=absent)
                or _content_digest(worktree, files) != digest
            ):
                raise ValueError("ignored output changed during preservation")
            for proof in list(absent):
                _record_absence(worktree, proof["path"], absent)
            # The manifest is only a locator; retries independently read all bytes.
            if not reused:
                with location.with_suffix(".manifest.json").open("x", encoding="utf-8") as manifest:
                    json.dump(metadata, manifest, sort_keys=True)
                    manifest.write("\n")
        if record.get("keep_worktree"):
            metadata["next_condition"] = (
                "existing owner releases retention after proven retrieval via post_task_reap --release-retention"
            )
        else:
            metadata.update({"retention_disposition": "retrieved", "next_condition": "none"})
        if metadata["retention_disposition"] != "retained":
            metadata["next_condition"] = "owner repairs task receipt publication"
        # Recheck intent under the task writer lock. A concurrent record update
        # cannot have its keep flag overwritten by this gate's earlier snapshot.
        with artifacts.task_state_lock(record_path):
            current = json.loads(record_path.read_text(encoding="utf-8"))
            if (
                not _record_matches_worktree(current, worktree, repo_root=repo_root)
                or current.get("task_id") != identity
                or current.get("run_nonce") != record.get("run_nonce")
            ):
                raise ValueError("task attribution changed during preservation")
            if current.get("keep_worktree"):
                metadata.update(
                    {
                        "retention_disposition": "retained",
                        "next_condition": "existing owner releases retention after proven retrieval via post_task_reap --release-retention",
                    }
                )
            prior_release = current.get("preserved_artifacts", {}).get("retention_release")
            if prior_release:
                metadata["retention_release"] = prior_release
            if metadata["retention_disposition"] != "retained":
                metadata["next_condition"] = "none"
            current["preserved_artifacts"] = metadata
            current.pop("artifact_preservation_error", None)
            artifacts.reaper_lifecycle._atomic_write(record_path, current)
        if isinstance(task_record, dict) and _record_matches_worktree(task_record, worktree, repo_root=repo_root):
            task_record["preserved_artifacts"] = metadata
            task_record.pop("artifact_preservation_error", None)
        if metadata["retention_disposition"] == "retained":
            return False, "artifact preservation failed: keep_worktree intent set; refusing worktree removal", metadata
        print(
            f"Preserved {len(files)} files ({metadata['bytes']} bytes); retrieval SHA-256: {metadata.get('retrieval_proof_sha256')}",
            file=sys.stderr,
        )
        return True, "", metadata
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        # Never place filesystem exception paths in receipts.
        detail = str(exc).replace(str(worktree), "<worktree>").replace(str(primary), "<primary>")
        detail = re.sub(r"/(?:home|Users)/[^\s'\"]+", "<private-path>", detail)
        reason = f"artifact preservation failed: {detail}; refusing worktree removal"
        metadata["retention_disposition"] = "retained"
        if metadata["next_condition"] == "none":
            metadata["next_condition"] = "owner repairs task receipt publication and proves retrieval"
        if isinstance(task_record, dict) and _record_matches_worktree(task_record, worktree, repo_root=repo_root):
            task_record["artifact_preservation_error"] = reason
        if record_path is not None:
            with contextlib.suppress(OSError, ValueError):
                _update_bound_task_record(
                    record_path,
                    worktree,
                    {"artifact_preservation_error": reason, "preserved_artifacts": metadata},
                    repo_root=repo_root,
                    expected_record=record,
                )
        return False, reason, metadata
