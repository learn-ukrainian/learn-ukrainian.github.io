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
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from scripts.fleet.regenerable_output import is_regenerable_ignored_path
from scripts.orchestration import worktree_artifacts as artifacts
from scripts.orchestration.preparation_evidence import UniqueKeyLoader
from scripts.orchestration.task_record_store import task_record_path

# Bound automatic disk duplication. Larger outputs require owner disposition;
# the complete source checkout survives rather than receiving a partial copy.
MAX_PRESERVED_BYTES = 256 * 1024 * 1024
# A detached bundle gets the same ceiling as the existing output payload budget.
# It is a separate artifact; neither budget permits a partial preservation.
MAX_DETACHED_BUNDLE_BYTES = MAX_PRESERVED_BYTES

# Reviewed creator-initiator -> canonical stream map for lane succession (#10617).
SUCCESSION_MAP = Path(__file__).resolve().parents[2] / "scripts/config/terminal_abandon_succession.yaml"
_SUCCESSION_STREAM = re.compile(r"epic:[1-9][0-9]*")
_SUCCESSION_INITIATOR = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

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


class SuccessionRefusal(ValueError):
    """Keep custody's typed refusal across script and module writer imports."""

    def __init__(self, code: str, reason: str):
        super().__init__(f"terminal-abandon succession {code}: {reason}")
        self.code = code


class AttestationRefusal(ValueError):
    """A typed owner-attestation refusal shared by the writer and the removal reader (#10657)."""

    def __init__(self, code: str, reason: str):
        super().__init__(f"terminal-abandon attestation {code}: {reason}")
        self.code = code
        self.reason = reason


class CohortChanged(ValueError):
    """The bound task records changed while an abandon proof was checked; retry after they settle (#10657)."""


class PreservationLimit(ValueError):
    """A complete snapshot exceeds the existing automatic preservation budget."""


def merged_abandon_proof(worktree: Path, creator: Mapping[str, Any], head: str) -> dict[str, Any]:
    """Require an authoritative MERGED PR containing every checkout commit."""
    from scripts.orchestration import reap_worktrees as rw
    from scripts.orchestration.worktree_claims import checked_out_branch

    branch = checked_out_branch(worktree) or creator.get("worktree_branch")
    if not isinstance(branch, str) or not branch:
        raise ValueError("merged terminal proof requires a recorded source branch")
    states, error = rw._query_pr_states(worktree, branch)
    if error is not None or any(pr.state == "OPEN" for pr in states):
        raise ValueError("merged terminal proof unavailable or source PR is open")
    info = rw.WorktreeInfo(worktree, branch, head)
    for pr in states:
        if (
            pr.state == "MERGED"
            and not pr.head_from_commit_search
            and type(pr.number) is int
            and pr.number > 0
            and (rw._pr_matches_worktree_head(info, pr) or _abandon_merged_equivalent(info, pr))
        ):
            return {
                "schema": "terminal-abandon-merged-pr.v1",
                "number": pr.number,
                "branch": branch,
                "head_sha": pr.head_sha,
                "tree_head_sha": head,
                "relation": rw._merged_head_relation(info, pr),
            }
    raise ValueError("merged terminal proof does not contain checkout HEAD")


def _abandon_merged_equivalent(info: Any, pr: Any) -> bool:
    """Committed patch equivalence, with dirty bytes separately bound to the abandon manifest."""
    from scripts.orchestration import reap_worktrees as rw

    if not info.head or not pr.head_sha:
        return False
    for sha in (info.head, pr.head_sha):
        obj = rw._run(["git", "cat-file", "-t", sha], cwd=info.path)
        if obj.returncode != 0 or obj.stdout.strip() != "commit":
            return False
    merges = rw._run(["git", "rev-list", "--min-parents=2", f"{pr.head_sha}..{info.head}"], cwd=info.path)
    if merges.returncode != 0 or merges.stdout.strip():
        return False
    cherry = rw._run(["git", "cherry", pr.head_sha, info.head], cwd=info.path)
    return bool(
        cherry.returncode == 0 and all(re.fullmatch(r"- [a-f0-9]{40}", line) for line in cherry.stdout.splitlines())
    )


def abandon_task_is_terminal(
    member: Mapping[str, Any], *, successor: bool, merged: bool, attested: bool = False
) -> bool:
    """Merge evidence or an owner attestation substitutes for status and retention, never liveness."""
    from scripts.orchestration import reap_worktrees as rw

    return bool(
        member.get("status") in rw._TERMINAL_DISPATCH_STATUSES
        and (not member.get("keep_worktree") or merged or attested)
        and (not successor or member.get("status") != "needs_finalize" or merged or attested)
        and member.get("lease_state") != "active"
        and not (isinstance(member.get("lease"), dict) and member["lease"].get("state") == "active")
        and rw._pid_proven_absent(member)
    )


def recovered_creator(source: Mapping[str, Any], current: Mapping[str, Any], worktree: Path) -> dict[str, Any]:
    """Restore creation evidence only from the same archived attempt and directory inode."""
    baseline = source.get("ignored_output_baseline")
    status = worktree.stat()
    if (
        not record_created_worktree(source)
        or not isinstance(baseline, dict)
        or baseline.get("schema") != "ignored-baseline.v1"
        or baseline.get("directory_identity") != [status.st_dev, status.st_ino]
        or baseline.get("task_id") != current.get("task_id")
        or baseline.get("run_nonce") != current.get("run_nonce")
        or not isinstance(baseline.get("paths"), list)
        or not all(_baseline_entry_ok(entry) for entry in baseline["paths"])
        or len({entry["path"] for entry in baseline["paths"]}) != len(baseline["paths"])
        or not isinstance(current.get("run_nonce"), str)
        or not current["run_nonce"].strip()
        or not isinstance(current.get("initiator"), str)
        or not current["initiator"].strip()
        or (current.get("worktree_reused") is not None and current.get("worktree_reused") is not False)
        or any(
            source.get(key) != current.get(key)
            for key in (
                "task_id",
                "run_nonce",
                "initiator",
                "worktree_path",
                "cwd",
                "worktree_branch",
            )
        )
    ):
        raise ValueError("creator recovery archived attempt or creation inventory unverifiable")
    return dict(current, worktree_reused=False, ignored_output_baseline=baseline)


def recovery_source_path(tasks: Path, task_id: str, path: Path) -> bool:
    """Only canonical archives or delegate's exact force-new archive names are evidence."""
    return path == task_record_path(tasks / "archive", task_id) or (
        path.parent == tasks
        and re.fullmatch(re.escape(task_id) + r"\.\d{8}T\d{6}\d*Z(?:\.\d+)?\.archived\.json", path.name) is not None
    )


def _recovery_source(
    matches: list[tuple[Path, dict[str, Any]]], worktree: Path, *, primary: Path, tasks: Path
) -> Path | None:
    hosts = [
        (path, member)
        for path, member in matches
        if isinstance(member.get("worktree_abandon"), dict) and "creator_recovery" in member["worktree_abandon"]
    ]
    if not hosts:
        return None
    if len(hosts) != 1:
        raise ValueError("creator recovery attribution ambiguous")
    host_path, host = hosts[0]
    locator = host["worktree_abandon"]["creator_recovery"]
    try:
        source = json.loads(_abandon_file(primary, locator))
    except (OSError, ValueError, RuntimeError):
        raise ValueError("creator recovery archived source digest invalid") from None
    source_path = primary / locator["path"]
    if (
        host_path != task_record_path(tasks, host.get("task_id", ""))
        or not recovery_source_path(tasks, host["task_id"], source_path)
        or not any(path == source_path and member == source for path, member in matches)
        or not isinstance(source, dict)
        or recovered_creator(source, host, worktree) != host
    ):
        raise ValueError("creator recovery source binding invalid")
    return source_path


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


def succession_streams(path: Path | None = None) -> tuple[dict[str, str], str]:
    """Load the reviewed initiator -> stream map and the SHA-256 of its exact bytes.

    Exact keys only; a malformed file, duplicate key or an initiator listed under
    two streams refuses the whole map rather than choosing one.
    """
    raw = (SUCCESSION_MAP if path is None else path).read_bytes()
    try:
        data = yaml.load(raw.decode("utf-8"), Loader=UniqueKeyLoader)  # SafeLoader subclass
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError("succession map unreadable") from exc
    if not isinstance(data, dict) or set(data) != {"schema", "streams"}:
        raise ValueError("succession map invalid")
    if data["schema"] != "terminal-abandon-succession-map.v1" or not isinstance(data["streams"], dict):
        raise ValueError("succession map invalid")
    mapping: dict[str, str] = {}
    for stream, entry in data["streams"].items():
        if (
            not isinstance(stream, str)
            or not _SUCCESSION_STREAM.fullmatch(stream)
            or not isinstance(entry, dict)
            or set(entry) != {"initiators"}
            or not isinstance(entry["initiators"], list)
        ):
            raise ValueError("succession map invalid")
        for initiator in entry["initiators"]:
            if not isinstance(initiator, str) or not _SUCCESSION_INITIATOR.fullmatch(initiator) or initiator in mapping:
                raise ValueError("succession map invalid")
            mapping[initiator] = stream
    return mapping, hashlib.sha256(raw).hexdigest()


def _succession_authority(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """The custody a successor's receipt names, shape-checked before Monitor is asked about it."""
    succession = receipt.get("succession")
    authority = succession.get("authority") if isinstance(succession, dict) else None
    if (
        not isinstance(authority, dict)
        or not isinstance(authority.get("stream_id"), str)
        or authority["stream_id"] != succession.get("stream_id")
        or any(type(authority.get(key)) is not int for key in ("generation", "fencing_token"))
        or any(not isinstance(authority.get(key), str) or not authority[key] for key in ("session_id", "lease_id"))
    ):
        raise ValueError("terminal-abandon succession receipt invalid")
    return authority


def _succession_custody(receipt: Mapping[str, Any]) -> None:
    """The external half of the succession proof: the recorded custody is still Monitor's current lease."""
    from scripts.fleet.terminal_abandon import Refusal, verify_current_custody

    try:
        verify_current_custody(_succession_authority(receipt))
    except Refusal as exc:
        raise SuccessionRefusal(exc.code, str(exc)) from None


def _verify_succession(
    receipt: Mapping[str, Any],
    manifest: Mapping[str, Any],
    creator: Mapping[str, Any],
    worktree: Path,
    *,
    primary: Path,
) -> None:
    """Prove a successor's receipt still binds this exact task, tree, head and map entry (#10617).

    The local half only: removal first rechecks live custody
    (``_succession_custody``), then exact map bytes, checkout identity, branch,
    preservation digest and current untracked/ignored output under its locks.
    """
    from scripts.orchestration.worktree_claims import checked_out_branch

    succession = receipt.get("succession")
    authority = succession.get("authority") if isinstance(succession, dict) else None
    try:
        tree = worktree.resolve(strict=True).relative_to(primary.resolve(strict=True)).as_posix()
    except (OSError, ValueError, RuntimeError):
        raise ValueError("terminal-abandon succession tree binding invalid") from None
    mapping, mapping_digest = succession_streams()
    initiator = creator.get("initiator")
    if (
        not isinstance(succession, dict)
        or not isinstance(authority, dict)
        or succession.get("schema") != "terminal-abandon-succession.v1"
        or succession.get("task_id") != creator.get("task_id")
        or succession.get("creator_initiator") != initiator
        or not isinstance(initiator, str)
        or mapping.get(initiator) != succession.get("stream_id")
        or not isinstance(succession.get("mapping_sha256"), str)
        or not re.fullmatch(r"[a-f0-9]{64}", succession["mapping_sha256"])
        or succession.get("tree") != tree
        or succession.get("head_sha") != receipt.get("head_sha")
        or succession.get("preservation_sha256") != (receipt.get("preservation") or {}).get("sha256")
        or authority.get("stream_id") != succession.get("stream_id")
        or any(type(authority.get(key)) is not int for key in ("generation", "fencing_token"))
        or any(not isinstance(authority.get(key), str) or not authority[key] for key in ("session_id", "lease_id"))
        or not isinstance(succession.get("caller_initiator"), str)
    ):
        raise ValueError("terminal-abandon succession receipt invalid")
    if mapping_digest != succession["mapping_sha256"]:
        raise ValueError("terminal-abandon succession MAPPING_CHANGED: reviewed mapping bytes changed")
    # The slowest local check first; the commit, tracked and branch checks last.
    located = manifest.get("output")
    if not isinstance(located, dict) or located.get("schema") != "terminal-abandon-output.v1":
        raise ValueError("terminal-abandon succession output preservation missing")
    try:
        verify_retrieval(primary, located)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        # Never echo filesystem detail into the receipt.
        raise ValueError("terminal-abandon succession output preservation not retrievable") from None
    try:
        verify_abandon_output(worktree, primary=primary, record=creator, locator=located)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        raise ValueError(
            "terminal-abandon succession OUTPUT_CHANGED: current output differs from authorized snapshot"
        ) from None
    branch = checked_out_branch(worktree)
    if branch is None:
        if not detached_head(worktree):
            raise ValueError("terminal-abandon detached HEAD proof unavailable")
        verify_commit_bundle(primary, manifest.get("detached_bundle"), receipt["head_sha"], label="detached")
        tracked_clean(worktree, receipt["head_sha"], label="detached")
    if succession.get("branch") != branch:
        raise ValueError("terminal-abandon succession receipt invalid")


def detached_head(worktree: Path) -> bool:
    """Positive detached-HEAD proof; a failed branch probe is not detachment."""
    probe = artifacts.safe_git(
        ["rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree, capture_output=True, text=True, check=False, timeout=30
    )
    return probe.returncode == 0 and probe.stdout.strip() == "HEAD"


def tracked_clean(worktree: Path, head: str, *, label: str) -> None:
    """Refuse tracked index or working-tree changes, including ones hidden by index flags."""
    for revisions in (["--cached", head], []):
        clean = artifacts.safe_git(
            ["diff", "--quiet", "--no-ext-diff", *revisions, "--"],
            cwd=worktree,
            capture_output=True,
            check=False,
            timeout=30,
        )
        if clean.returncode != 0:
            raise ValueError(f"terminal-abandon {label} tracked changes refuse")
    # Git diff honors hidden index flags. Present flagged files must also
    # equal the index blob; sparse absent skip-worktree entries are safe.
    for tagged in artifacts._git_paths(worktree, "-v", "--cached"):
        if len(tagged) < 3 or tagged[1] != " ":
            raise ValueError(f"terminal-abandon {label} index inventory invalid")
        flag, name = tagged[0], tagged[2:]
        if not (flag.islower() or flag == "S"):
            continue
        if flag.upper() == "S" and not os.path.lexists(worktree / name):
            continue
        leaf = artifacts._read_preserved_bytes(worktree / name, root=worktree)
        blob = artifacts.safe_git(
            ["cat-file", "blob", f":{name}"], cwd=worktree, capture_output=True, check=False, timeout=30
        )
        payload = os.fsencode(leaf.target) if leaf.file_type == "symlink" else leaf.payload
        if blob.returncode != 0 or payload != blob.stdout:
            raise ValueError(f"terminal-abandon {label} concealed tracked changes refuse")


def index_settled(worktree: Path) -> None:
    """No in-progress index write and no unmerged entries, which ordinary patches cannot carry."""
    from scripts.orchestration import reap_worktrees as rw

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


def verify_commit_bundle(primary: Path, locator: Any, head: str, *, label: str) -> None:
    """A hash-bound Git bundle below batch_state whose only head is the exact checkout HEAD."""
    _abandon_file(primary, locator, read_payload=False, max_bytes=MAX_DETACHED_BUNDLE_BYTES)
    bundle_path = primary / locator["path"]
    verify = artifacts.safe_git(
        ["bundle", "verify", str(bundle_path)], cwd=primary, capture_output=True, check=False, timeout=30
    )
    listed = artifacts.safe_git(
        ["bundle", "list-heads", str(bundle_path)],
        cwd=primary,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if verify.returncode != 0 or listed.returncode != 0 or listed.stdout.strip() != f"{head} HEAD":
        raise ValueError(f"terminal-abandon {label} bundle does not preserve HEAD")


# Bundle refs naming commits that only the tree's own HEAD reflog reaches (#10657).
REFLOG_BUNDLE_REF = "refs/abandon/reflog/"
_REFLOG_ENTRY = re.compile(rb"([0-9a-f]{40}) ([0-9a-f]{40}) [^\n]*")
_ZERO_OID = "0" * 40


def unreachable_reflog_commits(worktree: Path, head: str) -> list[str]:
    """Commits the tree's own HEAD reflog still reaches that neither HEAD nor origin/main contains.

    Removing a linked worktree deletes this per-worktree reflog, so such a
    commit (for example one left behind by a reset) survives only inside the
    preservation bundle. Both object ids of every entry count, as they do for
    Git's own reachability. Completeness that cannot be established refuses.
    """
    formats = artifacts.safe_git(
        ["rev-parse", "--show-ref-format", "--show-object-format"],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if formats.returncode != 0 or formats.stdout.split() != ["files", "sha1"]:
        raise ValueError("terminal-abandon reflog completeness cannot be established for this ref or object format")
    located = artifacts.safe_git(
        ["rev-parse", "--path-format=absolute", "--git-path", "logs/HEAD"],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if located.returncode != 0 or not Path(located.stdout.strip()).is_absolute():
        raise ValueError("terminal-abandon reflog probe unavailable")
    try:
        fd = os.open(located.stdout.strip(), artifacts._LEAF_FLAGS)
    except FileNotFoundError:
        return []
    except OSError:
        raise ValueError("terminal-abandon reflog unreadable") from None
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("terminal-abandon reflog must be a regular file")
        entries = handle.read().split(b"\n")
    if entries[-1] == b"":
        entries.pop()
    oids: set[str] = set()
    for line in entries:
        entry = _REFLOG_ENTRY.fullmatch(line)
        if entry is None:
            raise ValueError("terminal-abandon reflog entry unreadable; completeness cannot be established")
        oids.update(oid.decode() for oid in entry.groups())
    oids.discard(_ZERO_OID)
    if not oids:
        return []
    # Everything the reflog reaches minus what HEAD or origin/main already carries.
    probe = artifacts.safe_git(
        ["rev-list", "--stdin"],
        cwd=worktree,
        input="".join(f"{oid}\n" for oid in sorted(oids)) + f"^{head}\n^refs/remotes/origin/main\n",
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if probe.returncode != 0:
        raise ValueError(
            "terminal-abandon reflog names a commit the object store cannot walk; completeness cannot be established"
        )
    return sorted(oids & set(probe.stdout.split()))


def verify_attested_bundle(primary: Path, locator: Any, head: str, reflog: list[str], *, require_head: bool) -> None:
    """A hash-bound bundle whose heads are HEAD plus a named ref for every current reflog-only commit.

    ``require_head`` is false only when origin/main already contains HEAD.
    """
    _abandon_file(primary, locator, read_payload=False, max_bytes=MAX_DETACHED_BUNDLE_BYTES)
    bundle_path = primary / locator["path"]
    verify = artifacts.safe_git(
        ["bundle", "verify", str(bundle_path)], cwd=primary, capture_output=True, check=False, timeout=30
    )
    listed = artifacts.safe_git(
        ["bundle", "list-heads", str(bundle_path)],
        cwd=primary,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    heads = listed.stdout.splitlines() if listed.returncode == 0 else []
    if verify.returncode != 0 or listed.returncode != 0 or heads.count(f"{head} HEAD") != int(require_head):
        raise ValueError("terminal-abandon attestation commit bundle does not preserve HEAD")
    named = set()
    for line in heads:
        oid, _, ref = line.partition(" ")
        if line != f"{head} HEAD" and (not re.fullmatch(r"[a-f0-9]{40}", oid) or ref != REFLOG_BUNDLE_REF + oid):
            raise ValueError("terminal-abandon attestation commit bundle names an unexpected ref")
        named.add(oid)
    if not set(reflog) <= named:
        raise ValueError("terminal-abandon attestation REFLOG_UNPRESERVED: a reflog-only commit is not in the bundle")


def bound_branches_unclaimed(worktree: Path, branch: str | None, matches: list[tuple[Path, dict[str, Any]]]) -> None:
    """No branch bound to the tree, checked out or recorded, has an open PR; an unknown probe refuses."""
    from scripts.orchestration import reap_worktrees as rw

    names = {branch, *(member.get("worktree_branch") for _, member in matches)}
    for name in sorted(name for name in names if isinstance(name, str) and name):
        prs, error = rw._query_pr_states(worktree, name)
        if error is not None:
            raise AttestationRefusal("ACTIVITY_UNKNOWN", "open PR probe unavailable")
        if any(pr.state == "OPEN" for pr in prs):
            raise AttestationRefusal("LIVE_OR_WANTED", "a branch bound to the tree has an open PR")


def _preservation_manifest(
    primary: Path, receipt: Mapping[str, Any], worktree: Path, *, identity: str, nonce: str, head: str
) -> dict[str, Any]:
    """The hashed preservation manifest bound to this owner, run and HEAD; ``_verify_patches`` checks its bytes."""
    from scripts.orchestration import reap_worktrees as rw

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
    return manifest


def _verify_patches(primary: Path, manifest: Mapping[str, Any], worktree: Path, *, head: str) -> None:
    """The manifest's three hash-bound patches equal Git's current binary, full-index diffs."""
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


# Owner-attested abandonment (#10657). The attestation may stand in only for
# missing creator evidence and for unsettled status or retention intent.
ATTESTATION_SCHEMA = "terminal-abandon-attestation.v1"
ATTESTATION_REPLACEABLE = frozenset({"CREATOR_RECOVERY_REQUIRED", "LIVE_OR_WANTED"})
_ATTESTED_RECEIPT_KEYS = frozenset(
    {"schema", "disposition", "owner", "run_nonce", "head_sha", "reason", "preservation", "attestation"}
)
_ATTESTATION_KEYS = frozenset(
    {
        "schema",
        "task_id",
        "tree",
        "directory_identity",
        "branch",
        "head_sha",
        "reason",
        "attested_at",
        "owner",
        "replaces",
        "cohort",
        "preservation_sha256",
    }
)
_ATTESTATION_OWNER_KEYS = frozenset(
    {"seat", "area", "stream_id", "task_initiator", "mapping_sha256", "assignments_sha256", "authority"}
)
_ATTESTATION_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")


def attestation_cohort(matches: list[tuple[Path, dict[str, Any]]], tasks_dir: Path) -> list[dict[str, Any]]:
    """Every task record bound to the tree, by task-store path, task, run and initiator.

    The initiator decides the owning lane, so a changed initiator is a changed cohort.
    """
    return sorted(
        (
            {
                "record": path.relative_to(tasks_dir).as_posix(),
                "task_id": member.get("task_id"),
                "run_nonce": member.get("run_nonce"),
                "initiator": member.get("initiator"),
            }
            for path, member in matches
        ),
        key=lambda entry: entry["record"],
    )


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _attestation_well_formed(attestation: Mapping[str, Any]) -> bool:
    from agents_extensions.shared.session_streams.process_identity import PROCESS_IDENTITY_RE

    owner = attestation.get("owner")
    authority = owner.get("authority") if isinstance(owner, dict) else None
    holder = authority.get("holder") if isinstance(authority, dict) else None
    identity = attestation.get("directory_identity")
    replaces = attestation.get("replaces")
    return bool(
        set(attestation) == _ATTESTATION_KEYS
        and attestation["schema"] == ATTESTATION_SCHEMA
        and all(_nonempty(attestation[key]) for key in ("task_id", "tree", "head_sha", "reason"))
        and (attestation["branch"] is None or _nonempty(attestation["branch"]))
        and isinstance(attestation["attested_at"], str)
        and _ATTESTATION_TIME.fullmatch(attestation["attested_at"])
        and isinstance(identity, list)
        and len(identity) == 2
        and all(type(part) is int for part in identity)
        and isinstance(attestation["preservation_sha256"], str)
        and re.fullmatch(r"[a-f0-9]{64}", attestation["preservation_sha256"])
        and isinstance(owner, dict)
        and set(owner) == _ATTESTATION_OWNER_KEYS
        and all(_nonempty(owner[key]) for key in ("seat", "area", "stream_id", "task_initiator"))
        and all(
            isinstance(owner[key], str) and re.fullmatch(r"[a-f0-9]{64}", owner[key])
            for key in ("mapping_sha256", "assignments_sha256")
        )
        and isinstance(authority, dict)
        and set(authority) == {"stream_id", "session_id", "lease_id", "generation", "fencing_token", "holder"}
        and authority["stream_id"] == owner["stream_id"]
        and all(_nonempty(authority[key]) for key in ("session_id", "lease_id"))
        and all(type(authority[key]) is int for key in ("generation", "fencing_token"))
        and isinstance(holder, dict)
        # The attested generation's recorded holder process identity (#10657);
        # removal requires Monitor's current lease to record the same one.
        and set(holder) == {"agent", "harness", "instance_id", "process_identity"}
        and all(_nonempty(value) for value in holder.values())
        and PROCESS_IDENTITY_RE.fullmatch(holder["process_identity"])
        and owner["seat"].partition("-")[0] == holder["agent"]
        and isinstance(replaces, list)
        and all(
            isinstance(entry, dict)
            and set(entry) == {"code", "reason"}
            and entry["code"] in ATTESTATION_REPLACEABLE
            and _nonempty(entry["reason"])
            for entry in replaces
        )
        and len({entry["code"] for entry in replaces}) == len(replaces)
        and isinstance(attestation["cohort"], list)
    )


def _attestation_receipt(
    matches: list[tuple[Path, dict[str, Any]]], tasks_dir: Path
) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any]]:
    """The tree's single attested record and its receipt, shape-checked from record state alone."""
    hosts = [(path, member) for path, member in matches if "worktree_abandon" in member]
    if len(hosts) != 1:
        raise ValueError("terminal-abandon attestation must be the tree's only abandon record")
    path, host = hosts[0]
    identity, nonce = host.get("task_id"), host.get("run_nonce")
    if (
        not isinstance(identity, str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", identity)
        or not _nonempty(nonce)
        or path != task_record_path(tasks_dir, identity)
    ):
        raise ValueError("terminal-abandon attestation host identity unavailable")
    receipt = host["worktree_abandon"]
    attestation = receipt.get("attestation") if isinstance(receipt, dict) else None
    head = receipt.get("head_sha") if isinstance(receipt, dict) else None
    if (
        not isinstance(receipt, dict)
        or set(receipt) != _ATTESTED_RECEIPT_KEYS
        or receipt["schema"] != "terminal-abandon.v1"
        or receipt["disposition"] != "ABANDON"
        or receipt["owner"] != identity
        or receipt["run_nonce"] != nonce
        or not _nonempty(receipt["reason"])
        or not isinstance(head, str)
        or not re.fullmatch(r"[a-f0-9]{40}", head)
        or not isinstance(receipt["preservation"], dict)
        or not isinstance(attestation, dict)
        or not _attestation_well_formed(attestation)
        or attestation["task_id"] != identity
        or attestation["head_sha"] != head
        or attestation["reason"] != receipt["reason"]
        or attestation["preservation_sha256"] != receipt["preservation"].get("sha256")
    ):
        raise ValueError("terminal-abandon attestation receipt invalid")
    return path, host, receipt, attestation


def _attested_owner_lane(
    attestation: Mapping[str, Any], host: Mapping[str, Any], matches: list[tuple[Path, dict[str, Any]]]
) -> None:
    """The recorded owner must be the lane the reviewed maps assign every bound task to, from current map bytes."""
    from scripts.fleet.terminal_abandon import Refusal, owner_lane

    owner = attestation["owner"]
    try:
        lane = owner_lane(
            owner["seat"],
            owner["authority"]["holder"]["agent"],
            host.get("initiator"),
            [member.get("initiator") for _, member in matches],
        )
    except Refusal as exc:
        raise AttestationRefusal(exc.code, str(exc)) from None
    if any(owner[key] != lane[key] for key in ("mapping_sha256", "assignments_sha256")):
        raise AttestationRefusal("MAPPING_CHANGED", "reviewed lane or area map bytes changed; the owner re-attests")
    if any(owner[key] != value for key, value in lane.items()):
        raise AttestationRefusal("FOREIGN_OWNER", "recorded owner is not the lane that owns every bound task")


def _attestation_external(matches: list[tuple[Path, dict[str, Any]]], worktree: Path, *, tasks_dir: Path) -> None:
    """The slow half of an attestation proof: GitHub PR state and Monitor custody (#10657).

    A changed cohort or a record naming a foreign lane is refused from record
    state and the reviewed maps before any network probe; the local half checks
    both again afterwards. Every bound branch, the attested one and each
    recorded one, must have no open PR; the local half later proves the
    checkout is still on the attested branch. The attested custody must still
    be the stream's current Monitor lease, held by this process or one of its
    ancestors (kernel-proven).
    """
    from scripts.fleet.terminal_abandon import Refusal, verify_current_custody

    _, host, _, attestation = _attestation_receipt(matches, tasks_dir)
    if attestation["cohort"] != attestation_cohort(matches, tasks_dir):
        raise ValueError("terminal-abandon attestation cohort changed")
    _attested_owner_lane(attestation, host, matches)
    bound_branches_unclaimed(worktree, attestation["branch"], matches)
    try:
        verify_current_custody(attestation["owner"]["authority"], caller_holds=True)
    except Refusal as exc:
        raise AttestationRefusal(exc.code, str(exc)) from None


def _attestation_local(
    matches: list[tuple[Path, dict[str, Any]]], worktree: Path, *, primary: Path, tasks_dir: Path
) -> tuple[Path, dict[str, Any]]:
    """The local half of an attestation proof, run after every slow probe (#10657).

    The attestation replaces creator evidence and unsettled status or retention
    only. Liveness, checkout identity, tracked cleanliness, the Git patches, the
    commit bundle (including every commit only the tree's reflog reaches) and
    the untracked/ignored output copy are all rechecked here. No recorded owner
    field is trusted: the owning lane is recomputed from the reviewed maps and
    the bound records' initiators. Record and configuration checks come first,
    then the slowest tree check (output hashing), HEAD, branch and the commit
    bundle (every new reflog entry counts); the tracked and Git byte checks run
    last, immediately before the caller acts.
    """
    from scripts.orchestration import reap_worktrees as rw
    from scripts.orchestration.worktree_claims import checked_out_branch

    path, host, receipt, attestation = _attestation_receipt(matches, tasks_dir)
    identity, nonce, head = host["task_id"], host["run_nonce"], receipt["head_sha"]
    try:
        tree = worktree.resolve(strict=True).relative_to(primary.resolve(strict=True)).as_posix()
        status = worktree.stat()
    except (OSError, ValueError, RuntimeError):
        raise ValueError("terminal-abandon attestation tree binding invalid") from None
    if attestation["tree"] != tree:
        raise ValueError("terminal-abandon attestation tree binding invalid")
    if attestation["directory_identity"] != [status.st_dev, status.st_ino]:
        raise ValueError("terminal-abandon attestation directory identity changed")
    if attestation["cohort"] != attestation_cohort(matches, tasks_dir):
        raise ValueError("terminal-abandon attestation cohort changed")
    if any(
        not abandon_task_is_terminal(member, successor=False, merged=False, attested=True)
        or not _nonempty(member.get("run_nonce"))
        or not _record_matches_worktree(member, worktree, repo_root=primary)
        for _, member in matches
    ):
        raise ValueError("terminal-abandon attestation task, PID or lease proof unavailable")
    _attested_owner_lane(attestation, host, matches)
    manifest = _preservation_manifest(primary, receipt, worktree, identity=identity, nonce=nonce, head=head)
    located = manifest.get("output")
    if not isinstance(located, dict) or located.get("schema") != "terminal-abandon-output.v1":
        raise ValueError("terminal-abandon attestation output preservation missing")
    try:
        verify_retrieval(primary, located)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        raise ValueError("terminal-abandon attestation output preservation not retrievable") from None
    try:
        verify_abandon_output(worktree, primary=primary, record=host, locator=located)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError):
        raise ValueError(
            "terminal-abandon attestation OUTPUT_CHANGED: current output differs from attested snapshot"
        ) from None
    current = rw._run(["git", "rev-parse", "HEAD"], cwd=worktree)
    if current is None or current.returncode != 0 or current.stdout.strip() != head:
        raise ValueError("terminal-abandon checkout HEAD differs from receipt")
    branch = checked_out_branch(worktree)
    if branch is None and not detached_head(worktree):
        raise ValueError("terminal-abandon attestation branch probe unavailable")
    if branch != attestation["branch"]:
        raise ValueError("terminal-abandon attestation branch changed")
    reflog = unreachable_reflog_commits(worktree, head)
    head_on_main = rw._sha_is_ancestor(worktree, head, "refs/remotes/origin/main")
    bundle = manifest.get("commit_bundle")
    if bundle is not None:
        verify_attested_bundle(primary, bundle, head, reflog, require_head=not head_on_main)
    elif reflog or not head_on_main:
        raise ValueError("terminal-abandon attestation commit bundle missing for commits outside origin/main")
    index_settled(worktree)
    tracked_clean(worktree, head, label="attested")
    _verify_patches(primary, manifest, worktree, head=head)
    return path, host


def _abandon_candidates(worktree: Path, *, absent: list[dict[str, str]]) -> list[str]:
    """Untracked bytes and present hidden index entries, which Git patches can omit.

    Never the whole index: ordinary tracked changes are bound to verified patches.
    """
    names = []
    candidates = artifacts._git_paths(worktree, "--others", "--exclude-standard")
    for tagged in artifacts._git_paths(worktree, "-v", "--cached"):
        if len(tagged) < 3 or tagged[1] != " ":
            raise ValueError("terminal-abandon tagged index inventory malformed")
        if tagged[0].islower() or tagged[0] == "S":
            # Sparse checkout intentionally leaves skip-worktree entries
            # absent. Only present hidden entries are output. A present path
            # that vanishes later still changes the authorized inventory.
            if tagged[0].upper() == "S" and not os.path.lexists(worktree / tagged[2:]):
                continue
            candidates.append(tagged[2:])
    for name in candidates:
        try:
            (worktree / name).lstat()
        except FileNotFoundError:
            _record_absence(worktree, name, absent)
        else:
            names.append(name)
    return names


def _abandon_output_inventory(worktree: Path, *, primary: Path, record: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The removal gate's abandon-mode file set; any vanished path refuses here."""
    absent: list[dict[str, str]] = []
    names = _ignored_output_files(worktree, primary, record, absent=absent)
    files = sorted(set(names + _abandon_candidates(worktree, absent=absent)))
    if absent:
        raise ValueError("ignored output changed during preservation")
    return _path_inventory(worktree, files)


def capture_abandon_output(
    worktree: Path, *, primary: Path, record: Mapping[str, Any]
) -> tuple[dict[str, Any], Path | None]:
    """Copy untracked and ignored output before a successor's abandon record (#10617).

    Git patches cannot carry these bytes. Copy them below
    ``batch_state/preserved/<task>`` and verify retrieval independently. Return
    the hash-bound locator and the directory this call created, or ``None`` when
    an identical verified copy was reused. The removal gate later reuses the same
    copy while the bytes are unchanged; it never replaces the removal-time copy.
    """
    worktree = worktree.resolve(strict=True)
    primary = primary.resolve(strict=True)
    identity = record.get("task_id")
    if not isinstance(identity, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", identity):
        raise ValueError("missing canonical task attribution")
    paths = _abandon_output_inventory(worktree, primary=primary, record=record)
    files = [entry["path"] for entry in paths]
    total = sum(entry["size"] for entry in paths)
    if total > MAX_PRESERVED_BYTES:
        raise PreservationLimit(f"ignored output exceeds preservation cap ({total} > {MAX_PRESERVED_BYTES} bytes)")
    digest = hashlib.sha256(
        json.dumps([(entry["path"], entry["size"], entry["sha256"]) for entry in paths]).encode()
    ).hexdigest()
    parent = primary / "batch_state" / "preserved" / identity
    if parent.is_relative_to(worktree):
        raise ValueError("preservation destination is inside the worktree")
    location = _reusable_copy(parent, worktree, files, digest, require_archive=True)
    created = None
    try:
        if location is None:
            location = created = parent / uuid.uuid4().hex
            location.mkdir(parents=True, exist_ok=False)
            for name in files:
                destination = location / name
                if destination.resolve() != destination.absolute():
                    raise ValueError("preserved artifact destination contains a symlink")
                artifacts._copy_verified(worktree / name, destination, source_root=worktree, destination_root=location)
        locator = {
            "schema": "terminal-abandon-output.v1",
            "location": location.relative_to(primary).as_posix(),
            "content_sha256": digest,
            "paths": paths,
        }
        # Keep the ordinary retrieved copy for existing removers. The inert tar
        # independently carries every byte, including link records, without
        # extraction or following a link from an untrusted checkout.
        archive = location.with_suffix(".tar")
        if created is not None:
            with contextlib.ExitStack() as held:
                root_fd = artifacts._open_trusted_root(primary / "batch_state")
                held.callback(os.close, root_fd)
                parts = artifacts._relative_parts(archive, primary / "batch_state")
                parent_fd, owned = artifacts._walk_parent(root_fd, parts[:-1])
                if owned:
                    held.callback(os.close, parent_fd)
                fd = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent_fd)
                stream = held.enter_context(os.fdopen(fd, "wb"))
                tar = held.enter_context(tarfile.open(fileobj=stream, mode="w", format=tarfile.PAX_FORMAT))
                for entry in paths:
                    leaf = artifacts._read_preserved_bytes(location / entry["path"], root=location)
                    item = tarfile.TarInfo(entry["path"])
                    item.size = len(leaf.payload)
                    item.mode = 0o600
                    tar.addfile(item, io.BytesIO(leaf.payload))
                stream.flush()
            locator["archive"] = {
                "path": archive.relative_to(primary).as_posix(),
                "sha256": hashlib.sha256(
                    artifacts._read_preserved_bytes(archive, root=primary / "batch_state").payload
                ).hexdigest(),
            }
        else:
            saved = json.loads(location.with_suffix(".manifest.json").read_bytes())
            if "archive" in saved:
                locator["archive"] = saved["archive"]
        verify_retrieval(primary, locator)
        verify_abandon_output(worktree, primary=primary, record=record, locator=locator)
    except BaseException:
        if created is not None:
            shutil.rmtree(created, ignore_errors=True)
            created.with_suffix(".tar").unlink(missing_ok=True)
        raise
    return locator, created


def verify_abandon_output(
    worktree: Path, *, primary: Path, record: Mapping[str, Any], locator: Mapping[str, Any]
) -> None:
    """Refuse when the checkout's untracked or ignored bytes differ from the captured copy."""
    current = _abandon_output_inventory(worktree.resolve(strict=True), primary=primary, record=record)
    if _byte_identity(current) != _byte_identity(locator["paths"]):
        raise ValueError("ignored output changed during preservation")


def publish_abandon_output(
    worktree: Path, *, primary: Path, record: Mapping[str, Any], locator: Mapping[str, Any]
) -> None:
    """Write the locator manifest the removal gate's ``_reusable_copy`` recognizes."""
    location = primary / locator["location"]
    metadata = {
        **locator,
        "owner": record["task_id"],
        "task_id": record["task_id"],
        "run_nonce": record.get("run_nonce"),
        "count": len(locator["paths"]),
        "bytes": sum(entry["size"] for entry in locator["paths"]),
        "worktree_sha256": hashlib.sha256(str(worktree.resolve(strict=True)).encode()).hexdigest(),
    }
    with location.with_suffix(".manifest.json").open("x", encoding="utf-8") as manifest:
        json.dump(metadata, manifest, sort_keys=True)
        manifest.write("\n")


def _abandon_regular(
    primary: Path, path: Path, *, read_payload: bool, max_bytes: int | None = None
) -> tuple[bytes, str]:
    """Hash a regular file in bounded reads, walking descriptor-relative without links."""
    root = primary / "batch_state"
    parts = artifacts._relative_parts(path, root)
    with contextlib.ExitStack() as held:
        root_fd = artifacts._open_trusted_root(root)
        held.callback(os.close, root_fd)
        parent_fd, owned = artifacts._walk_parent(root_fd, parts[:-1])
        if owned:
            held.callback(os.close, parent_fd)
        fd = os.open(parts[-1], artifacts._LEAF_FLAGS, dir_fd=parent_fd)
        held.callback(os.close, fd)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("terminal-abandon preservation must be regular")
        if max_bytes is not None and before.st_size > max_bytes:
            raise PreservationLimit(
                f"detached bundle exceeds MAX_DETACHED_BUNDLE_BYTES ({before.st_size} > {max_bytes} bytes)"
            )
        digest = hashlib.sha256()
        payload = bytearray()
        remaining = before.st_size
        while remaining:
            chunk = os.read(fd, min(remaining, 1024 * 1024))
            if not chunk:
                raise ValueError("terminal-abandon preservation changed during hashing")
            digest.update(chunk)
            if read_payload:
                payload.extend(chunk)
            remaining -= len(chunk)
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("terminal-abandon preservation changed during hashing")
        return bytes(payload), digest.hexdigest()


def _abandon_file(
    primary: Path, entry: Mapping[str, Any], *, read_payload: bool = True, max_bytes: int | None = None
) -> bytes:
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
    payload, observed = _abandon_regular(primary, root.joinpath(*parts), read_payload=read_payload, max_bytes=max_bytes)
    if observed != digest:
        raise ValueError("terminal-abandon preservation digest invalid")
    return payload


def _abandon_attested(matches: list[tuple[Path, dict[str, Any]]]) -> bool:
    return any(
        isinstance(member.get("worktree_abandon"), dict) and "attestation" in member["worktree_abandon"]
        for _, member in matches
    )


def _creator_receipt(
    matches: list[tuple[Path, dict[str, Any]]], worktree: Path, *, primary: Path, tasks_dir: Path
) -> tuple[Path, dict[str, Any], Any, Path | None]:
    """The sole creator-of-record and its raw abandon receipt, identified from record state alone."""
    recovery = _recovery_source(matches, worktree, primary=primary, tasks=tasks_dir)
    creators = [item for item in matches if item[0] != recovery and record_created_worktree(item[1])]
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
    return path, creator, creator.get("worktree_abandon"), recovery


def _creator_external(
    matches: list[tuple[Path, dict[str, Any]]], worktree: Path, *, primary: Path, tasks_dir: Path
) -> None:
    """The slow half of a creator or successor proof: merged-PR evidence (GitHub) and custody (Monitor)."""
    _, creator, receipt, _ = _creator_receipt(matches, worktree, primary=primary, tasks_dir=tasks_dir)
    if not isinstance(receipt, dict):
        return  # The local half refuses a missing record.
    merged = receipt.get("merged_pr")
    if merged is not None and (
        not isinstance(receipt.get("succession"), dict)
        or merged != merged_abandon_proof(worktree, creator, receipt.get("head_sha"))
    ):
        raise ValueError("terminal-abandon merged terminal proof changed")
    if "succession" in receipt:
        _succession_custody(receipt)


def _creator_local(
    matches: list[tuple[Path, dict[str, Any]]], worktree: Path, *, primary: Path, tasks_dir: Path
) -> tuple[Path, dict[str, Any]]:
    """The local half of a creator or successor proof; HEAD, index and Git byte checks run last."""
    from scripts.orchestration import reap_worktrees as rw

    path, creator, receipt, recovery = _creator_receipt(matches, worktree, primary=primary, tasks_dir=tasks_dir)
    identity, nonce = creator["task_id"], creator["run_nonce"]
    merged = receipt.get("merged_pr") if isinstance(receipt, dict) else None
    if any(
        not abandon_task_is_terminal(
            member, successor=isinstance(receipt, dict) and "succession" in receipt, merged=merged is not None
        )
        or not isinstance(member.get("run_nonce"), str)
        or not member["run_nonce"].strip()
        or (member is not creator and member_path != recovery and member.get("worktree_reused") is not True)
        or not _record_matches_worktree(member, worktree, repo_root=primary)
        for member_path, member in matches
    ):
        raise ValueError("terminal-abandon task, PID, lease or retention proof unavailable")
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
    manifest = _preservation_manifest(primary, receipt, worktree, identity=identity, nonce=nonce, head=head)
    if "succession" in receipt:
        _verify_succession(receipt, manifest, creator, worktree, primary=primary)
    current = rw._run(["git", "rev-parse", "HEAD"], cwd=worktree)
    if current is None or current.returncode != 0 or current.stdout.strip() != head:
        raise ValueError("terminal-abandon checkout HEAD differs from receipt")
    index_settled(worktree)
    _verify_patches(primary, manifest, worktree, head=head)
    return path, creator


def terminal_abandon_external(
    matches: list[tuple[Path, dict[str, Any]]], worktree: Path, *, primary: Path, tasks_dir: Path
) -> None:
    """The slow half of the abandon proof: every GitHub and Monitor probe it needs (#10657).

    A caller that acts on the proof (publishing a record, deleting the tree)
    runs this first and ``terminal_abandon_local`` last, with nothing slow in
    between, so no tree or cohort change can land during a network wait and go
    unseen. Raises ``ValueError`` (or a typed subclass) on refusal.
    """
    if _abandon_attested(matches):
        _attestation_external(matches, worktree, tasks_dir=tasks_dir)
    else:
        _creator_external(matches, worktree, primary=primary, tasks_dir=tasks_dir)


def terminal_abandon_local(
    matches: list[tuple[Path, dict[str, Any]]],
    worktree: Path,
    *,
    primary: Path,
    tasks_dir: Path,
    on_disk: list[tuple[Path, dict[str, Any]]] | None = None,
) -> tuple[Path, dict[str, Any]]:
    """The local half of the abandon proof: re-read the bound cohort, then check the checkout itself (#10657).

    The cohort read now must equal ``on_disk`` (default ``matches``); a writer
    validating an unpublished record passes the proposed cohort as ``matches``
    and the locked on-disk cohort as ``on_disk``. Then every record, tree and
    preservation fact is read again, with the checkout's HEAD, branch, tracked
    and Git byte checks last. No network call is made here.
    """
    current = matching_worktree_records(worktree, tasks_dir, repo_root=primary, publish_cache=False)
    if current != (matches if on_disk is None else on_disk):
        raise CohortChanged("terminal-abandon task cohort changed during verification; retry after it settles")
    if _abandon_attested(matches):
        return _attestation_local(matches, worktree, primary=primary, tasks_dir=tasks_dir)
    return _creator_local(matches, worktree, primary=primary, tasks_dir=tasks_dir)


def terminal_abandon_creator(
    matches: list[tuple[Path, dict[str, Any]]],
    worktree: Path,
    *,
    primary: Path,
    tasks_dir: Path,
    on_disk: list[tuple[Path, dict[str, Any]]] | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Prove explicit owner abandonment and exact Git patches, never infer it from CLOSED.

    The creator's ``worktree_abandon`` record is terminal-abandon.v1: ABANDON,
    owner, run_nonce, head_sha, reason and a preservation {path, sha256} locator.
    That hashed terminal-abandon-preservation.v1 manifest repeats the identity,
    names base_sha and hash-bound head_patch, index_patch and working_patch.
    All three patches must equal Git's binary, full-index diff for this checkout.
    Untracked and ignored bytes still require the ordinary verified-copy gate.
    A successor's receipt adds ``succession`` and a manifest ``output`` copy;
    both are revalidated here, at removal (#10617). An owner attestation is a
    separate, complete proof that replaces creator evidence (#10657).
    Every slow probe runs before the cohort is re-read and the checkout is
    checked, so the last check precedes the caller's act with no wait between.
    """
    terminal_abandon_external(matches, worktree, primary=primary, tasks_dir=tasks_dir)
    return terminal_abandon_local(matches, worktree, primary=primary, tasks_dir=tasks_dir, on_disk=on_disk)


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
    if "archive" in receipt:
        _verify_output_archive(primary, receipt)
    return digest


def _verify_output_archive(primary: Path, receipt: Mapping[str, Any]) -> None:
    """Verify the tar's digest, exact members and bytes without extracting it."""
    locator = receipt["archive"]
    expected = Path(receipt["location"]).with_suffix(".tar").as_posix()
    if not isinstance(locator, dict) or locator.get("path") != expected:
        raise ValueError("output archive location invalid")
    raw = _abandon_file(primary, locator)
    try:
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as tar:
            members = tar.getmembers()
            paths = receipt["paths"]
            if [member.name for member in members] != [entry["path"] for entry in paths]:
                raise ValueError("output archive inventory mismatch")
            for member, entry in zip(members, paths, strict=True):
                if not member.isfile() or member.size != entry["size"]:
                    raise ValueError("output archive member invalid")
                stream = tar.extractfile(member)
                if stream is None or hashlib.sha256(stream.read()).hexdigest() != entry["sha256"]:
                    raise ValueError("output archive bytes mismatch")
    except tarfile.TarError:
        raise ValueError("output archive invalid") from None


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


def _reusable_copy(
    parent: Path, worktree: Path, files: list[str], digest: str, *, require_archive: bool = False
) -> Path | None:
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
            if require_archive and "archive" not in saved:
                continue
            location = manifest.with_name(manifest.name.removesuffix(".manifest.json"))
            if location.resolve(strict=True) != location.absolute():
                continue
            entries = list(location.rglob("*"))
            if any(entry.is_symlink() for entry in entries):
                continue
            names = sorted(entry.relative_to(location).as_posix() for entry in entries if not entry.is_dir())
            if names == files and _content_digest(location, files) == digest:
                verify_retrieval(parent.parents[2], saved)
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
            names += _abandon_candidates(worktree, absent=absent)
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
                if record_path is None and any(member.get("worktree_reap_proof") for _, member in matches):
                    # Zero creators resolve to no owner rather than raising.
                    # Reuse the same proof verifier as ambiguous creators below.
                    raise ValueError("merged cohort requires preservation proof attribution")
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
        # Merge proof or an owner attestation (#10657) releases retention intent.
        retention_released = disposition == "abandon" and (
            "merged_pr" in record["worktree_abandon"] or "attestation" in record["worktree_abandon"]
        )
        kept = any(member.get("keep_worktree") for _, member in members) and not retention_released

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
            if reused:
                saved = json.loads(location.with_suffix(".manifest.json").read_bytes())
                if "archive" in saved:
                    metadata["archive"] = saved["archive"]
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
                    # The last check before destructive Git: its GitHub and Monitor
                    # probes run first, then the cohort and checkout are read again.
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
            if (current.get("keep_worktree") or kept) and not retention_released:
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
