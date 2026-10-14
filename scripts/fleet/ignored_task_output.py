"""Preserve ignored task output before automatic worktree removal (#9645).

Creation evidence requires ``worktree_reused is False`` and a dictionary-valued
``ignored_output_baseline`` captured by dispatch before worker spawn. Cohort
attribution also requires one such creator and the common checkout/branch proof.
A path or canonical-leaf match, the flag alone, or a prep-failure record without
the creation inventory never proves creation, including in historical cohorts.
"""

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

_IDENTITY_KEYS = (
    "worktree_path",
    "cwd",
    "acp_runtime_paths",
    "keep_worktree",
    "worktree_reused",
    "status",
    "worktree_branch",
)
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


def matching_worktree_records(
    worktree: Path, tasks_dir: Path, *, repo_root: Path, publish_cache: bool = True
) -> list[tuple[Path, dict[str, Any]]]:
    """Retry one complete inventory after a concurrent record move or rewrite.

    Atomic replacement at the same name does not expose partial JSON, but
    delegate's redispatch archive and stale_task_records' staging move can
    remove a filename between glob and open. Never simply omit a failed read.
    A vanished name needs a visible archive counterpart before retrying.
    ``publish_cache=False`` suppresses publication on both inventory attempts.
    """
    try:
        matches = _matching_worktree_records_once(worktree, tasks_dir, repo_root=repo_root, publish_cache=publish_cache)
    except _InventoryReadError as exc:
        print("Task identity inventory read failed; retrying complete inventory once", file=sys.stderr)
        matches = _matching_worktree_records_once(
            worktree,
            tasks_dir,
            repo_root=repo_root,
            publish_cache=publish_cache,
            missing_path=exc.path if exc.missing else None,
        )
    # Retention and record-change checks need every claim, including history.
    # Only creator attribution may disregard proven force-new attempts.
    return matches


def _current_reuse_records(
    matches: list[tuple[Path, dict[str, Any]]], tasks_dir: Path
) -> list[tuple[Path, dict[str, Any]]]:
    """Exclude proven force-new history, never an ordinary archived creator.

    Both attempts already match the checkout. Require the exact delegate archive
    name, a terminal prior run, a distinct canonical replacement nonce, and a
    current creator. A sole historical creator of a same-task reused run remains
    available to the existing receipt attribution path.
    """
    from scripts.orchestration.worktree_claims import RELEASED_TASK_STATUSES

    current = {
        record.get("task_id"): (path, record)
        for path, record in matches
        if isinstance(record.get("task_id"), str) and path == task_record_path(tasks_dir, record["task_id"])
    }
    has_creator = any(record_created_worktree(record) for _, record in current.values())
    result = []
    for path, record in matches:
        identity, nonce = record.get("task_id"), record.get("run_nonce")
        replacement = current.get(identity) if isinstance(identity, str) else None
        if (
            has_creator
            and replacement is not None
            and path.parent == tasks_dir
            and re.fullmatch(re.escape(identity) + r"\.\d{8}T\d{6}\d*Z(?:\.\d+)?\.archived\.json", path.name)
            and isinstance(record.get("status"), str)
            and record["status"] in RELEASED_TASK_STATUSES
            and isinstance(nonce, str)
            and bool(nonce.strip())
            and isinstance(replacement[1].get("run_nonce"), str)
            and bool(replacement[1]["run_nonce"].strip())
            and nonce != replacement[1]["run_nonce"]
        ):
            continue
        result.append((path, record))
    return result


def _matching_worktree_records_once(
    worktree: Path,
    tasks_dir: Path,
    *,
    repo_root: Path,
    publish_cache: bool = True,
    missing_path: Path | None = None,
) -> list[tuple[Path, dict[str, Any]]]:
    """Resolve identity from canonical records, never from a caller's hint.

    Inspect hot and archived records: a different filename, renamed tree, or
    optional task argument cannot hide a retention claim. Ambiguity fails closed.
    A sole force-new archived creator may bind a same-task canonical reused run.
    A content-verified cache bounds JSON decoding to changed/candidate records;
    all source files are still read, and filesystem aliases are resolved anew.
    ``publish_cache=False`` keeps cache reads but never creates or updates it.
    """
    from scripts.orchestration.worktree_claims import (
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
            and re.fullmatch(re.escape(missing_path.stem) + r"\.\d{8}T\d{6}\d*Z(?:\.\d+)?\.archived\.json", path.name)
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
    return matches


def record_created_worktree(record: Mapping[str, Any]) -> bool:
    """Require both the explicit creation flag and dispatch's creation inventory."""
    return record.get("worktree_reused") is False and isinstance(record.get("ignored_output_baseline"), dict)


def reused_worktree_creator(
    matches: list[tuple[Path, dict[str, Any]]], worktree: Path, *, repo_root: Path, tasks_dir: Path
) -> tuple[Path, dict[str, Any]]:
    """Accept one creator and settled successors with a common checkout/branch binding."""
    from scripts.orchestration.worktree_claims import RELEASED_TASK_STATUSES, checked_out_branch, resolve_claim_path

    retained = any(record.get("keep_worktree") for _, record in matches)
    matches = _current_reuse_records(matches, tasks_dir)
    creators = [match for match in matches if record_created_worktree(match[1])]
    branch = checked_out_branch(worktree)
    if branch is None and not retained and len(creators) == 1:
        # None also means a failed probe. Only a positive detached HEAD result
        # permits using the records' common branch instead of a checked-out one.
        from scripts.orchestration.worktree_claims import _git_probe

        probe = _git_probe(["rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree)
        if probe is not None and probe.returncode == 0 and probe.stdout.strip() == "HEAD":
            recorded = creators[0][1].get("worktree_branch")
            if isinstance(recorded, str) and recorded.strip():
                branch = recorded
    if len(creators) != 1 or not branch:
        raise ValueError("ambiguous worktree task attribution with retention intent")
    target = worktree.resolve(strict=True)
    for _, record in matches:
        location = record.get("worktree_path") or record.get("cwd")
        if (
            not isinstance(location, str)
            or resolve_claim_path(location, repo_root=repo_root) != target
            or record.get("worktree_branch") != branch
            or (
                record is not creators[0][1]
                and (
                    record.get("worktree_reused") is not True
                    or not isinstance(record.get("status"), str)
                    or record["status"] not in RELEASED_TASK_STATUSES
                )
            )
        ):
            raise ValueError("ambiguous worktree task attribution with retention intent")
    return creators[0]


def resolve_worktree_record(
    worktree: Path, tasks_dir: Path, *, repo_root: Path, publish_cache: bool = True
) -> tuple[Path | None, dict[str, Any]]:
    """Resolve the creator; multiple retention claims require a proven reuse cohort."""
    from scripts.orchestration.worktree_claims import is_superseded_record

    matches = _current_reuse_records(
        matching_worktree_records(worktree, tasks_dir, repo_root=repo_root, publish_cache=publish_cache), tasks_dir
    )
    if len(matches) > 1:
        kept = [match for match in matches if match[1].get("keep_worktree")]
        if kept:
            return reused_worktree_creator(matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir)
        # Finished references alone are not ownership. Without one creator,
        # output retains unknown attribution; empty trees remain removable.
        creators = [match for match in matches if record_created_worktree(match[1])]
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
        if creators:
            return reused_worktree_creator(matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir)
        return None, {}
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


def _abandon_file(primary: Path, entry: Mapping[str, Any]) -> bytes:
    """Read a hash-bound regular receipt below batch_state without following links."""
    if not isinstance(entry, Mapping):
        raise ValueError("terminal-abandon preservation locator invalid")
    name, digest = entry.get("path"), entry.get("sha256")
    if not isinstance(name, str) or not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("terminal-abandon preservation locator invalid")
    root = primary / "batch_state"
    parts = artifacts._relative_parts(primary / name, root)
    if not parts:
        raise ValueError("terminal-abandon preservation locator invalid")
    leaf = artifacts._read_preserved_bytes(root.joinpath(*parts), root=root)
    if leaf.file_type != "regular" or hashlib.sha256(leaf.payload).hexdigest() != digest:
        raise ValueError("terminal-abandon preservation digest invalid")
    return leaf.payload


def terminal_abandon_creator(
    matches: list[tuple[Path, dict[str, Any]]], worktree: Path, *, primary: Path, tasks_dir: Path
) -> tuple[Path, dict[str, Any]]:
    """Prove explicit owner abandonment and exact Git patches, never infer it from CLOSED.

    The creator's ``worktree_abandon`` record is terminal-abandon.v1: ABANDON,
    owner, run_nonce, head_sha, reason and a preservation {path, sha256} locator.
    That hashed terminal-abandon-preservation.v1 manifest repeats the identity,
    names base_sha and hash-bound head_patch, index_patch and working_patch.
    All three patches must equal Git's binary, full-index diff for this checkout.
    Untracked and ignored bytes still require the ordinary verified-copy gate.
    """
    from scripts.orchestration import reap_worktrees as rw

    creators = [item for item in matches if record_created_worktree(item[1])]
    if len(creators) != 1 or not matches:
        raise ValueError("terminal-abandon owner attribution unavailable")
    path, creator = creators[0]
    identity, nonce = creator.get("task_id"), creator.get("run_nonce")
    if (
        not isinstance(identity, str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", identity)
        or not isinstance(nonce, str)
        or not nonce.strip()
        or path not in (task_record_path(tasks_dir, identity), task_record_path(tasks_dir / "archive", identity))
    ):
        raise ValueError("terminal-abandon owner identity unavailable")
    if any(
        member.get("status") not in rw._TERMINAL_DISPATCH_STATUSES
        or member.get("keep_worktree")
        or member.get("lease_state") == "active"
        or (isinstance(member.get("lease"), dict) and member["lease"].get("state") == "active")
        or not rw._pid_proven_absent(member)
        or not isinstance(member.get("run_nonce"), str)
        or not member["run_nonce"].strip()
        or (member is not creator and member.get("worktree_reused") is not True)
        or not _record_matches_worktree(member, worktree, repo_root=primary)
        for _, member in matches
    ):
        raise ValueError("terminal-abandon task, PID, lease or retention proof unavailable")
    receipt = creator.get("worktree_abandon")
    if not isinstance(receipt, dict):
        raise ValueError("terminal-abandon owner ABANDON record missing")
    head = receipt.get("head_sha")
    if (
        receipt.get("schema") != "terminal-abandon.v1"
        or receipt.get("disposition") != "ABANDON"
        or receipt.get("owner") != identity
        or receipt.get("run_nonce") != nonce
        or not isinstance(receipt.get("reason"), str)
        or not receipt["reason"].strip()
        or not isinstance(head, str)
        or not re.fullmatch(r"[a-f0-9]{40}", head)
    ):
        raise ValueError("terminal-abandon owner ABANDON record invalid")
    current = rw._run(["git", "rev-parse", "HEAD"], cwd=worktree)
    if current is None or current.returncode != 0 or current.stdout.strip() != head:
        raise ValueError("terminal-abandon checkout HEAD differs from receipt")
    index_lock = rw._run(["git", "rev-parse", "--path-format=absolute", "--git-path", "index.lock"], cwd=worktree)
    if index_lock.returncode != 0 or not Path(index_lock.stdout.strip()).is_absolute():
        raise ValueError("terminal-abandon index lock probe unavailable")
    try:
        Path(index_lock.stdout.strip()).lstat()
    except FileNotFoundError:
        pass
    else:
        raise ValueError("terminal-abandon index.lock present; existing lock must be settled")
    if artifacts._git_paths(worktree, "--unmerged"):
        raise ValueError("terminal-abandon unmerged index cannot be preserved by ordinary patches")
    manifest = json.loads(_abandon_file(primary, receipt.get("preservation")))
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != "terminal-abandon-preservation.v1"
        or manifest.get("owner") != identity
        or manifest.get("run_nonce") != nonce
        or manifest.get("head_sha") != head
        or not isinstance(manifest.get("base_sha"), str)
        or not re.fullmatch(r"[a-f0-9]{40}", manifest["base_sha"])
        or not rw._sha_is_ancestor(worktree, manifest["base_sha"], head)
        or not rw._sha_is_ancestor(worktree, manifest["base_sha"], "refs/remotes/origin/main")
    ):
        raise ValueError("terminal-abandon preservation manifest identity invalid")
    for key, revisions in (
        ("head_patch", [manifest["base_sha"], head]),
        ("index_patch", ["--cached", head]),
        ("working_patch", []),
    ):
        stored = _abandon_file(primary, manifest.get(key))
        probe = artifacts.safe_git(
            ["diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", *revisions, "--"],
            cwd=worktree,
            env=artifacts._safe_git_env(),
            capture_output=True,
            text=False,
            check=False,
            timeout=30,
        )
        if probe.returncode != 0 or probe.stdout != stored:
            raise ValueError(f"terminal-abandon {key} does not preserve current Git bytes")
    return path, creator


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


def _byte_identity(entries: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Name, size and hash.

    Preservation and retrieval compare these fields only. The symlink label
    and its target are not part of that decision.
    """
    return [{key: entry[key] for key in ("path", "size", "sha256")} for entry in entries]


def _path_inventory(
    root: Path, files: list[str], *, absent: list[dict[str, str]] | None = None
) -> list[dict[str, Any]]:
    """Fingerprint each path from one descriptor walk.

    The file type is the walk's ``fstat`` result. A real symlink records that
    type and its target. A regular file records neither, including when its
    bytes begin with the link-record prefix. This inventory does not stat the
    path or parse the prefix out of the bytes.
    """
    entries = []
    for name in files:
        path = root / name
        try:
            walked = artifacts._read_preserved_bytes(path, root=root)
        except FileNotFoundError:
            if absent is None:
                raise
            _record_absence(root, name, absent)
            continue
        entry: dict[str, Any] = {
            "path": name,
            "size": len(walked.payload),
            "sha256": hashlib.sha256(walked.payload).hexdigest(),
        }
        if walked.file_type == "symlink":
            if not isinstance(walked.target, str):
                raise ValueError("symlink target is missing")
            entry["type"] = "symlink"
            entry["target"] = walked.target
        elif walked.file_type != "regular":
            raise ValueError("artifact is not a regular file")
        entries.append(entry)
    return entries


def _classified_inventory(
    worktree: Path, files: list[str], record: Mapping[str, Any], *, absent: list[dict[str, str]] | None = None
) -> list[dict[str, Any]]:
    baseline = record.get("ignored_output_baseline")
    status = worktree.stat()
    trusted = (
        record_created_worktree(record)
        and baseline.get("schema") == "ignored-baseline.v1"
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
            if len(before) != len(baseline["paths"]) or any(not _baseline_entry_ok(entry) for entry in before.values()):
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
    if _byte_identity(_path_inventory(location, names)) != _byte_identity(paths):
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
    extra_files: list[str] | None = None,
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
    disposition = None
    disposition_members = None

    def output_files() -> list[str]:
        names = _ignored_output_files(worktree, primary, record, absent=absent)
        if disposition == "abandon":
            # Ordinary tracked changes are already bound to verified patches.
            # Copy untracked bytes and present hidden index entries, whose local
            # changes Git can omit from those patches. Never copy the whole index.
            candidates = artifacts._git_paths(worktree, "--others", "--exclude-standard")
            for tagged in artifacts._git_paths(worktree, "-v", "--cached"):
                if len(tagged) < 3 or tagged[1] != " ":
                    raise ValueError("terminal-abandon tagged index inventory malformed")
                if tagged[0].islower() or tagged[0] == "S":
                    candidates.append(tagged[2:])
            for name in candidates:
                try:
                    (worktree / name).lstat()
                except FileNotFoundError:
                    _record_absence(worktree, name, absent)
                else:
                    names.append(name)
        for name in extra_files or []:
            artifacts._relative_parts(worktree / name, worktree)
        return sorted(set(names + (extra_files or [])))

    try:
        worktree = worktree.resolve(strict=True)
        primary = primary.resolve(strict=True)
        matches = matching_worktree_records(worktree, tasks_dir, repo_root=repo_root, publish_cache=False)
        if any("worktree_abandon" in member for _, member in matches):
            record_path, record = terminal_abandon_creator(matches, worktree, primary=primary, tasks_dir=tasks_dir)
            disposition = "abandon"
            disposition_members = matches
        try:
            if disposition is None:
                record_path, record = resolve_worktree_record(
                    worktree,
                    tasks_dir,
                    repo_root=repo_root,
                    publish_cache=identity_cache_publication_allowed(worktree, tasks_dir),
                )
        except ValueError:
            # A continuation that switched branch still names the dispatch-time
            # branch, so strict attribution refuses. Preservation may use that
            # creator only after the merged-head proof; resolve itself stays strict
            # so branch-holder release and retention release do not (#10548).
            from scripts.orchestration.reap_worktrees import (
                _preservation_merged_creator,
                _switched_branch_merge_proven,
                _switched_branch_structural_cohort,
            )

            matches = matching_worktree_records(worktree, tasks_dir, repo_root=repo_root, publish_cache=False)
            structural = _switched_branch_structural_cohort(matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir)
            if structural is not None:
                cohort = _current_reuse_records(matches, tasks_dir)
                if not _switched_branch_merge_proven(repo_root, worktree, cohort):
                    raise
                record_path, record = structural
            elif any(member.get("worktree_reap_proof") for _, member in matches):
                record_path, record = _preservation_merged_creator(
                    matches, worktree, repo_root=repo_root, tasks_dir=tasks_dir
                )
                disposition = "merged"
                disposition_members = matches
            else:
                raise
        members = matching_worktree_records(worktree, tasks_dir, repo_root=repo_root, publish_cache=False)
        kept = any(member.get("keep_worktree") for _, member in members)

        files = output_files()
        if not files and not absent and not kept:
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
        if files or absent or kept:
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
                if _byte_identity(_path_inventory(location, files)) != _byte_identity(paths):
                    raise ValueError("ignored output changed during preservation")
            metadata.update(
                {"location": location.relative_to(primary).as_posix(), "content_sha256": digest, "reused": reused}
            )
            metadata["next_condition"] = "owner repairs failed retrieval and verifies all bytes"
            metadata["retrieval_proof_sha256"] = verify_retrieval(primary, metadata)
            if files != output_files() or _content_digest(worktree, files) != digest:
                raise ValueError("ignored output changed during preservation")
            for proof in list(absent):
                _record_absence(worktree, proof["path"], absent)
            # The manifest is only a locator; retries independently read all bytes.
            if not reused:
                with location.with_suffix(".manifest.json").open("x", encoding="utf-8") as manifest:
                    json.dump(metadata, manifest, sort_keys=True)
                    manifest.write("\n")
            metadata["manifest_path"] = location.with_suffix(".manifest.json").relative_to(primary).as_posix()
        if kept:
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
            if disposition is not None:
                current_members = matching_worktree_records(
                    worktree, tasks_dir, repo_root=repo_root, publish_cache=False
                )
                if current_members != disposition_members:
                    raise ValueError("disposition task records changed during preservation")
                if disposition == "abandon":
                    terminal_abandon_creator(current_members, worktree, primary=primary, tasks_dir=tasks_dir)
                    metadata["abandon_proof"] = record["worktree_abandon"]
                else:
                    _preservation_merged_creator(current_members, worktree, repo_root=repo_root, tasks_dir=tasks_dir)
            if (
                not _record_matches_worktree(current, worktree, repo_root=repo_root)
                or current.get("task_id") != identity
                or current.get("run_nonce") != record.get("run_nonce")
            ):
                raise ValueError("task attribution changed during preservation")
            if current.get("keep_worktree") or kept:
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
            if extra_files is not None:
                current["branch_holder_archive"] = metadata
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
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
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
