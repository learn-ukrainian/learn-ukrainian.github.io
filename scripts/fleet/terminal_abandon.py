"""Write creator-, stream-custody- or owner-attested terminal-abandon records using the existing validator."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agents_extensions.shared.session_streams.process_identity import (
    ProcessIdentityUnavailable,
    lineage_identity,
    validate_process_identity,
)
from scripts.agent_runtime.attribution import resolve_invocation_attribution
from scripts.common import task_store_paths
from scripts.fleet import ignored_task_output as output
from scripts.orchestration import reap_worktrees as rw
from scripts.orchestration import worktree_artifacts as artifacts
from scripts.orchestration import worktree_claims as claims
from scripts.orchestration.preparation_evidence import UniqueKeyLoader
from scripts.orchestration.task_record_store import locate_task_record, task_record_path

# Lane roster used to bind an attesting owner's seat to the task's lane (#10657).
AREA_ASSIGNMENTS = _ROOT / "scripts/config/area_assignments.yaml"


class Refusal(ValueError):
    """A stable, privacy-safe refusal suitable for the owner's receipt."""

    def __init__(self, code: str, reason: str, context: dict[str, Any] | None = None):
        super().__init__(reason)
        self.code = code
        self.context = context


RECOVERY = (
    "infra driver must recover authentic dispatch creator evidence from archived task state or a verified backup; "
    "if unavailable, a separate creator-recovery task is required; never synthesize a creator"
)


def _regular_bytes(path: Path, primary: Path) -> bytes:
    leaf = artifacts._read_preserved_bytes(path, root=primary / "batch_state")
    if leaf.file_type != "regular":
        raise Refusal("INVALID_INPUT", "input must be a regular file below batch_state, without symlink ancestors")
    return leaf.payload


def _activity(
    primary: Path,
    tree: Path,
    matches: list[tuple[Path, dict[str, Any]]],
    head: str,
    *,
    successor: bool = False,
    merged: bool = False,
) -> None:
    try:
        active = rw._active_task_ids()
        cwds = rw._live_cwd_paths(primary)
    except Exception:
        raise Refusal("ACTIVITY_UNKNOWN", "live task or process activity probe unavailable") from None
    if not isinstance(active, set) or cwds is None:
        raise Refusal("ACTIVITY_UNKNOWN", "live task or process activity probe unavailable")
    if any(member.get("task_id") in active for _, member in matches):
        raise Refusal("LIVE_OR_WANTED", "a bound task is active")
    if any(not output.abandon_task_is_terminal(member, successor=successor, merged=merged) for _, member in matches):
        raise Refusal("LIVE_OR_WANTED", "bound task status, PID, lease or retention does not permit abandonment")
    info = rw.WorktreeInfo(tree, claims.checked_out_branch(tree), head)
    if rw._activity_reason(repo_root=primary, info=info, active_ids=active, live_cwds=cwds) is not None:
        raise Refusal("LIVE_OR_WANTED", "tree has live process, review, rollover, ownership or reap activity")


def _caller_lease(caller: Any) -> Any:
    """The launcher-issued lease envelope this session was started with, if any."""
    from agents_extensions.shared.session_streams.hooks import lease_from_environment

    if caller.source == "unknown" or caller.initiator == "unknown":
        raise Refusal("NOT_CREATOR", "caller initiator does not match the dispatch creator-of-record")
    try:
        return lease_from_environment()
    except (ValueError, TypeError):
        raise Refusal(
            "NOT_CREATOR", "caller is neither the creator-of-record nor a holder of launcher-issued stream custody"
        ) from None


def _current_custody(lease: Any, stream: str) -> dict[str, Any]:
    """The authority ``_observed_custody`` proves, without its observation."""
    return _observed_custody(lease, stream)[0]


def _observed_custody(lease: Any, stream: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Prove with Monitor that ``lease`` is the stream's current active lease, held by this process tree.

    Membership in the succession map grants nothing; only this exact, unexpired
    lease does. A local PID never proves a remote lease expired, so Monitor is the
    sole authority and any unavailable or malformed answer refuses. The envelope
    from the environment (including its ``LU_MONITOR_HOST_ID`` host label) only
    names the lease and can only narrow the match: Monitor's stream view
    publishes every envelope field, so possession proves nothing until the kernel
    shows the caller running beneath Monitor's recorded holder process. The
    returned authority binds that generation's recorded holder process identity,
    so every later check compares against the same holder. Also returns the
    complete lease observation (``observe_custody``) for a later write's
    confirmation. Read only.
    """
    from scripts.session_supervisor.remote import RemoteEpicClient

    if lease.stream_id != stream:
        raise Refusal("CROSS_STREAM", "caller's stream custody is not the creator's canonical stream")
    identity, observation = observe_custody(RemoteEpicClient._lease_payload(lease), caller_holds=True)
    authority = {
        "stream_id": stream,
        "session_id": lease.session_id,
        "lease_id": lease.lease_id,
        "generation": lease.generation,
        "fencing_token": lease.fencing_token,
        "holder": {
            "agent": lease.holder.agent,
            "harness": lease.holder.harness,
            "instance_id": lease.holder.instance_id,
            "process_identity": identity,
        },
    }
    return authority, observation


def confirm_custody_after_write(
    path: Path, original: bytes, authority: dict[str, Any], before: Mapping[str, Any]
) -> None:
    """Bind a just-published record to the lease state it was checked against, or withdraw it (#10657).

    ``before`` is the complete lease observation (``observe_custody``) taken
    after every other slow probe and before the write. The record was written
    under the task-record locks every remover takes before its final check, so
    no remover has acted on it yet. Confirmation observes the lease again and
    requires both:

    - Monitor's own clock says the lease is active and unexpired now (its
      projection reports ``expired`` from ``expires_at`` on its clock), and it
      is held by this process tree;
    - the observation equals ``before`` in every field: generation, fencing
      token, the holder including its process identity, and the validity
      fields ``heartbeat_at``, ``expires_at``, ``version`` and states.

    Store triggers advance ``version`` on every change to the lease row, so
    equal observations mean the row was not touched in between, and an
    ``expires_at`` that is unchanged and still in the future now was in the
    future at the write. A renewal (including an expired holder reviving
    itself), a succession, an expiry reclaim or a force release in between
    therefore refuses ``STALE_AUTHORITY``: the record's exact prior bytes are
    restored before the locks are released, and the caller removes the
    preservation files it published. Any failure to confirm withdraws it.
    """
    try:
        _, after = observe_custody(authority, caller_holds=True)
        if _canonical(after) != _canonical(before):
            raise Refusal(
                "STALE_AUTHORITY",
                "stream custody was renewed, replaced or expired between the last check and the write",
            )
    except Exception:
        temporary = path.with_name(f".{path.name}.{os.getpid()}.restore")
        with temporary.open("wb") as handle:
            handle.write(original)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        raise


def _canonical(value: Any) -> str:
    """Canonical JSON keeps int, bool and null distinct and ignores key order."""
    return json.dumps(value, sort_keys=True)


def verify_current_custody(expected: dict[str, Any], *, caller_holds: bool = False) -> str | None:
    """``observe_custody`` without the observation."""
    return observe_custody(expected, caller_holds=caller_holds)[0]


def observe_custody(expected: dict[str, Any], *, caller_holds: bool = False) -> tuple[str | None, dict[str, Any]]:
    """Revalidate writer or receipt custody against Monitor without acquiring a lease.

    Only the canonical loopback Monitor is asked: an environment-selected
    endpoint could answer for any lease. Every field ``expected`` carries must
    equal Monitor's current lease, including a recorded ``holder.process_identity``.
    With ``caller_holds`` this process must also be Monitor's recorded holder
    process or one of its descendants, proven from the kernel by
    ``prove_holder_process`` against the identity read in the same response.
    Returns that generation's recorded holder process identity and the
    complete lease observation: every field Monitor returned except
    ``age_seconds``, which Monitor derives from its clock at each read.
    """
    from agents_extensions.shared.session_streams.model import parse_timestamp
    from scripts.session_supervisor.remote import DEFAULT_MONITOR, RemoteEpicClient, RemoteSupervisorError

    stream = expected["stream_id"]
    try:
        response = RemoteEpicClient(base=DEFAULT_MONITOR).stream(stream, digest_limit=1)
    except RemoteSupervisorError:
        raise Refusal("AUTHORITY_UNKNOWN", "Monitor stream custody probe unavailable") from None
    current = response.get("lease")
    observed = {key: current.get(key) for key in expected} if isinstance(current, dict) else {}
    # Receipts retain only the holder identity. Writer envelopes also bind the
    # process fields, so compare every holder field present in the expected proof.
    if isinstance(observed.get("holder"), dict) and isinstance(expected.get("holder"), dict):
        observed["holder"] = {key: observed["holder"].get(key) for key in expected["holder"]}
    if (
        response.get("stream_id") != stream
        or not isinstance(current, dict)
        or current.get("state") != "active"
        or current.get("session_state") not in ("open", "rolling")
        or _canonical(observed) != _canonical(expected)
    ):
        raise Refusal("STALE_AUTHORITY", "caller's lease is not the stream's current active custody")
    try:
        expired = datetime.now(UTC) >= parse_timestamp(current["expires_at"])
    except (KeyError, TypeError, ValueError):
        raise Refusal("AUTHORITY_UNKNOWN", "Monitor stream custody expiry unavailable") from None
    if expired:
        raise Refusal("STALE_AUTHORITY", "caller's stream custody has expired")
    observation = {key: value for key, value in current.items() if key != "age_seconds"}
    if caller_holds:
        return prove_holder_process(current), observation
    identity = current["holder"].get("process_identity") if isinstance(current.get("holder"), dict) else None
    return (identity if isinstance(identity, str) else None), observation


def prove_holder_process(lease: Mapping[str, Any]) -> str:
    """Prove this process is Monitor's recorded lease holder process or its descendant (#10657).

    The launcher records its own PID as the holder and starts the provider
    beneath it; the session supervisor records that launcher's kernel-derived
    ``holder.process_identity`` when it acquires the generation. A PID alone
    names a process only on one host, boot and PID namespace, and a host label
    is configuration any caller can set, so locality is proven from the kernel
    alone: this process derives the identity of its own ancestor with the
    recorded PID independently (``process_identity.lineage_identity``) and it
    must equal the recorded value. A lease that records no or a malformed
    identity (acquired before the field existed or by an older client), a lease
    held on another host, boot or namespace, a reused PID, an app-thread holder
    (no process), and a machine without ``/proc`` are all refused. No
    environment value is read. Returns the verified identity.
    """
    holder = lease.get("holder")
    pid = holder.get("process_id") if isinstance(holder, dict) else None
    if not isinstance(holder, dict) or holder.get("holder_kind") != "process" or type(pid) is not int or pid <= 0:
        raise Refusal("HOLDER_UNPROVEN", "stream custody is not held by a recorded local process")
    claimed = holder.get("process_identity")
    try:
        validate_process_identity(claimed)
    except ValueError:
        raise Refusal(
            "HOLDER_UNPROVEN",
            "stream custody records no valid kernel process identity for its holder; "
            "the holder's next launcher acquisition records one",
        ) from None
    try:
        derived = lineage_identity(pid)
    except ProcessIdentityUnavailable:
        raise Refusal("HOLDER_UNPROVEN", "process ancestry or kernel identity unavailable") from None
    except LookupError:
        raise Refusal(
            "HOLDER_UNPROVEN", "this process is neither the stream custody holder nor its descendant"
        ) from None
    if not hmac.compare_digest(derived, claimed):
        raise Refusal(
            "HOLDER_UNPROVEN",
            "stream custody is held by a process on another host, boot or namespace, "
            "or by an earlier process with this PID",
        )
    return claimed


def _succession_map() -> tuple[dict[str, str], str]:
    try:
        return output.succession_streams()
    except (OSError, ValueError):
        raise Refusal("STREAM_UNMAPPED", "reviewed succession map unavailable or invalid") from None


def _successor(caller: Any, creator: dict[str, Any]) -> tuple[Any, str, str, dict[str, Any]]:
    """Admit a non-creator only with current custody of the creator's mapped stream (#10617)."""
    lease = _caller_lease(caller)
    mapping, mapping_digest = _succession_map()
    initiator = creator.get("initiator")
    stream = mapping.get(initiator) if isinstance(initiator, str) else None
    if stream is None:
        raise Refusal("STREAM_UNMAPPED", "creator initiator has no reviewed stream mapping; creator recovery required")
    return lease, stream, mapping_digest, _current_custody(lease, stream)


def _recover_creator(
    primary: Path, tasks: Path, path: Path, record: dict[str, Any], tree: Path
) -> tuple[dict[str, Any], dict[str, str]]:
    """Separate opt-in recovery; archive evidence must bind the same attempt."""
    candidates = [
        tasks / "archive" / f"{record['task_id']}.json",
        *sorted(tasks.glob(f"{record['task_id']}.*.archived.json")),
    ]
    verified = []
    for source in candidates:
        if source == path or not output.recovery_source_path(tasks, record["task_id"], source):
            continue
        try:
            raw = _regular_bytes(source, primary)
            archived = json.loads(raw)
            if not isinstance(archived, dict):
                continue
            recovered = output.recovered_creator(archived, record, tree)
        except (OSError, ValueError, RuntimeError):
            continue
        verified.append(
            (recovered, {"path": source.relative_to(primary).as_posix(), "sha256": hashlib.sha256(raw).hexdigest()})
        )
    if len(verified) != 1:
        raise Refusal(
            "CREATOR_RECOVERY_REQUIRED",
            f"manual item {record['task_id']}: archived creator evidence missing, ambiguous or unverifiable; {RECOVERY}",
        )
    return verified[0]


def _reflog_gitdir(tree: Path, scratch: Path, head: str, reflog: list[str]) -> None:
    """Make ``scratch`` a bare gitdir borrowing the tree's objects, with HEAD and one ref per reflog-only commit.

    A bundle advertises only named refs, and the target's own refs must not
    change, so the names live here. Only admitted Git commands touch it.
    """
    common = artifacts.safe_git(
        ["rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=tree,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if common.returncode != 0 or not Path(common.stdout.strip()).is_absolute():
        raise Refusal("PRESERVATION_INVALID", "object store probe unavailable for the reflog bundle")
    (scratch / "objects/info").mkdir(parents=True)
    (scratch / "refs").mkdir()
    (scratch / "objects/info/alternates").write_text(f"{Path(common.stdout.strip()) / 'objects'}\n")
    (scratch / "HEAD").write_text(f"{head}\n")
    named = artifacts.safe_git(
        ["update-ref", "--stdin"],
        cwd=scratch,
        input="".join(f"create {output.REFLOG_BUNDLE_REF}{oid} {oid}\n" for oid in reflog),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if named.returncode != 0:
        raise Refusal("PRESERVATION_INVALID", "reflog-only commits could not be named for the bundle")


def _detached_bundle(
    tree: Path, parent: Path, primary: Path, head: str, base_sha: str, reflog: list[str] | None = None
) -> tuple[dict[str, str], Path | None]:
    """Preserve only post-base objects; reuse a digest-named copy without owning it.

    ``reflog`` names commits only the tree's HEAD reflog reaches; each becomes
    its own bundle ref so a restore gives every one of them back (#10657).
    """
    if (
        not isinstance(base_sha, str)
        or not re.fullmatch(r"[a-f0-9]{40}", base_sha)
        or not rw._sha_is_ancestor(tree, base_sha, head)
        or not rw._sha_is_ancestor(primary, base_sha, "refs/remotes/origin/main")
    ):
        raise Refusal("PRESERVATION_INVALID", "detached bundle base must be an ancestor of HEAD and origin/main")
    # Stage beside the preserved copy for validation under batch_state and
    # atomic publication; the finally block owns cleanup, not the scratch lease.
    with tempfile.NamedTemporaryFile(dir=parent, prefix=".head-bundle-", delete=False) as handle:
        temporary = Path(handle.name)
    scratch = None
    try:
        try:
            if reflog:
                try:
                    scratch = Path(tempfile.mkdtemp(dir=parent, prefix=".reflog-bundle-"))
                    _reflog_gitdir(tree, scratch, head, reflog)
                except OSError:
                    raise Refusal("PRESERVATION_INVALID", "reflog bundle scratch could not be prepared") from None
                # A HEAD already on main is the base itself, which Git would exclude.
                revisions = [
                    *(["HEAD"] if head != base_sha else []),
                    *(output.REFLOG_BUNDLE_REF + oid for oid in reflog),
                    f"^{base_sha}",
                ]
                probe = artifacts.safe_git(
                    ["bundle", "create", str(temporary), "--stdin"],
                    cwd=scratch,
                    input="".join(f"{revision}\n" for revision in revisions),
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )
            else:
                probe = artifacts.safe_git(
                    ["bundle", "create", str(temporary), "HEAD", "--not", base_sha],
                    cwd=tree,
                    capture_output=True,
                    check=False,
                    timeout=30,
                )
        except subprocess.TimeoutExpired:
            raise Refusal("PRESERVATION_INVALID", "detached HEAD bundle could not be created in time") from None
        if probe.returncode != 0:
            raise Refusal("PRESERVATION_INVALID", "detached HEAD bundle could not be created")
        _, digest = output._abandon_regular(
            primary, temporary, read_payload=False, max_bytes=output.MAX_DETACHED_BUNDLE_BYTES
        )
        destination = parent / f"head-{head}-{digest}.bundle"
        if destination.exists() or destination.is_symlink():
            output._abandon_file(
                primary,
                {"path": destination.relative_to(primary).as_posix(), "sha256": digest},
                read_payload=False,
                max_bytes=output.MAX_DETACHED_BUNDLE_BYTES,
            )
            created = None
        else:
            os.replace(temporary, destination)
            created = destination
        return {"path": destination.relative_to(primary).as_posix(), "sha256": digest}, created
    except output.PreservationLimit as exc:
        raise Refusal("PRESERVATION_LIMIT", str(exc)) from None
    finally:
        temporary.unlink(missing_ok=True)
        # Git's own lock beside the target survives an interrupted create.
        temporary.with_name(temporary.name + ".lock").unlink(missing_ok=True)
        if scratch is not None:
            shutil.rmtree(scratch, ignore_errors=True)


def record_abandon(
    *, task_id: str, head: str, reason: str, bundle: Path, recover_creator: bool = False
) -> dict[str, Any]:
    """Validate under dispatch's locks, then atomically publish the creator record.

    Caller identity uses the same initiator resolver as delegate's owner-only
    force-new path. It is attribution within the shared-UID control plane, not
    a security boundary against a writer already able to modify task state.
    A non-creator succeeds only while holding the Monitor-verified current lease
    of the creator's stream from the reviewed succession map, and only from
    beneath that lease's recorded holder process (#10657). That record keeps
    the creator identity and nonce, appends a succession receipt, and also
    preserves untracked and ignored output. This never acquires or moves a lease.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", task_id) or not re.fullmatch(r"[a-f0-9]{40}", head):
        raise Refusal("INVALID_INPUT", "task id must be canonical and head must be a full lowercase 40-hex SHA")
    if not reason.strip():
        raise Refusal("INVALID_INPUT", "reason must be nonempty")
    caller = resolve_invocation_attribution()
    primary = claims.control_plane_root(Path.cwd()).resolve(strict=True)
    tasks = task_store_paths.tasks_dir()
    if tasks.absolute() != primary / "batch_state/tasks" or tasks.resolve(strict=True) != tasks.absolute():
        raise Refusal("INVALID_INPUT", "task store must be the canonical control-plane store without symlinks")
    path = locate_task_record(tasks, task_id)
    recovery_reason = f"manual item {task_id}: {RECOVERY}" if recover_creator else RECOVERY
    if path is None:
        raise Refusal("CREATOR_RECOVERY_REQUIRED", recovery_reason)
    record = json.loads(_regular_bytes(path, primary))
    if not isinstance(record, dict) or (not recover_creator and not output.record_created_worktree(record)):
        raise Refusal("CREATOR_RECOVERY_REQUIRED", recovery_reason)
    if recover_creator and record.get("task_id") != task_id:
        raise Refusal(
            "CREATOR_RECOVERY_REQUIRED",
            f"manual item {task_id}: archived recovery requires a canonical task identity; {RECOVERY}",
        )
    raw_tree = record.get("worktree_path") or record.get("cwd")
    if not isinstance(raw_tree, str):
        raise Refusal("CREATOR_RECOVERY_REQUIRED", recovery_reason)
    tree = claims.resolve_claim_path(raw_tree, repo_root=primary)
    if tree is None or not tree.is_dir():
        raise Refusal("CREATOR_RECOVERY_REQUIRED", recovery_reason)
    if tree == primary or not tree.is_relative_to(primary / ".worktrees/dispatch"):
        raise Refusal("INVALID_INPUT", "target must be an existing dispatch worktree")
    branch = claims.checked_out_branch(tree)
    source_branch = branch
    if source_branch is None and caller.initiator != record.get("initiator"):
        source_branch = record.get("worktree_branch")
    prs, error = rw._query_pr_states(tree, source_branch)
    if error is not None:
        raise Refusal("ACTIVITY_UNKNOWN", "open PR probe unavailable")
    if any(pr.state == "OPEN" for pr in prs):
        raise Refusal("LIVE_OR_WANTED", "tree branch has an open PR")

    with contextlib.ExitStack() as locks:
        locks.enter_context(claims.worktree_lock(tree, lock_dir=claims.repository_lock_dir(primary)))
        matches = output.matching_worktree_records(tree, tasks, repo_root=primary, publish_cache=False)
        for member_path, _ in sorted(matches):
            _regular_bytes(member_path, primary)
            lock_path = member_path.with_suffix(member_path.suffix + ".lock")
            if lock_path.is_symlink():
                raise Refusal("INVALID_INPUT", "task lock must not be a symlink")
            locks.enter_context(artifacts.task_state_lock(member_path))
        current = output.matching_worktree_records(tree, tasks, repo_root=primary, publish_cache=False)
        if current != matches:
            raise Refusal("STATE_CHANGED", "task cohort changed while acquiring locks; retry after it settles")
        recovery = None
        recovered = None
        if recover_creator and not output.record_created_worktree(record):
            locked_record = next((member for member_path, member in matches if member_path == path), None)
            if locked_record != record:
                raise Refusal("STATE_CHANGED", "creator recovery task changed during lock acquisition")
            recovered, recovery = _recover_creator(primary, tasks, path, locked_record, tree)
            creators = [(path, recovered)]
            if any(output.record_created_worktree(r) and p != primary / recovery["path"] for p, r in matches):
                raise Refusal("CREATOR_RECOVERY_REQUIRED", RECOVERY)
        else:
            recovered_source = output._recovery_source(matches, tree, primary=primary, tasks=tasks)
            creators = [(p, r) for p, r in matches if p != recovered_source and output.record_created_worktree(r)]
        if len(creators) != 1:
            raise Refusal("CREATOR_RECOVERY_REQUIRED", RECOVERY)
        creator_path, creator = creators[0]
        if creator_path != path or creator.get("task_id") != task_id:
            raise Refusal("NOT_CREATOR", "requested task is not the sole creator-of-record")
        succession = None
        if caller.source == "unknown" or caller.initiator == "unknown" or creator.get("initiator") != caller.initiator:
            succession = _successor(caller, creator)
        probe = rw._run(["git", "rev-parse", "HEAD"], cwd=tree)
        if probe is None or probe.returncode != 0 or probe.stdout.strip() != head:
            raise Refusal("HEAD_MISMATCH", "checkout HEAD does not match the requested exact head")
        if claims.checked_out_branch(tree) != branch:
            raise Refusal("STATE_CHANGED", "checkout branch changed after PR probe; retry after it settles")
        merged_proof = None
        if succession is not None and any(
            r.get("keep_worktree") or r.get("status") == "needs_finalize" for _, r in matches
        ):
            try:
                merged_proof = output.merged_abandon_proof(tree, creator, head)
            except (OSError, ValueError, RuntimeError):
                raise Refusal(
                    "LIVE_OR_WANTED", "merged terminal proof unavailable or checkout HEAD is unmerged"
                ) from None
        _activity(primary, tree, matches, head, successor=succession is not None, merged=merged_proof is not None)
        if "worktree_abandon" in creator:
            output.terminal_abandon_creator(matches, tree, primary=primary, tasks_dir=tasks)
            old = creator["worktree_abandon"]
            recovery = old.get("creator_recovery")
            if old["head_sha"] != head or old["reason"] != reason:
                raise Refusal("ALREADY_RECORDED", "existing abandon differs; no overwrite is permitted")
        bundle = bundle if bundle.is_absolute() else primary / bundle
        supplied = json.loads(_regular_bytes(bundle, primary))
        if not isinstance(supplied, dict):
            raise Refusal("PRESERVATION_INVALID", "preservation bundle must be a JSON object")
        # Use an already trusted directory outside the target. A temporary
        # manifest lets the unmodified reader validate before either publication.
        parent = bundle.parent
        if (
            parent.is_relative_to(tree)
            or parent.is_relative_to(tasks)
            or parent.resolve(strict=True) != parent.absolute()
        ):
            raise Refusal(
                "INVALID_INPUT", "bundle must be outside the target and task store, without symlink ancestors"
            )
        manifest = {
            "schema": "terminal-abandon-preservation.v1",
            "owner": task_id,
            "run_nonce": creator.get("run_nonce"),
            "head_sha": head,
            **{key: supplied.get(key) for key in ("base_sha", "head_patch", "index_patch", "working_patch")},
        }
        captured = None
        created_bundle = None
        created_manifest = None
        temporary = None
        published = False
        try:
            if succession is not None:
                if branch is None:
                    manifest["detached_bundle"], created_bundle = _detached_bundle(
                        tree, parent, primary, head, manifest["base_sha"]
                    )
                # Git patches cannot carry untracked or ignored bytes; a successor
                # is not their author, so it preserves them before deciding.
                try:
                    locator, captured = output.capture_abandon_output(tree, primary=primary, record=creator)
                except output.PreservationLimit as exc:
                    raise Refusal("PRESERVATION_LIMIT", str(exc)) from None
                except (OSError, ValueError, RuntimeError):
                    raise Refusal(
                        "PRESERVATION_INVALID", "untracked or ignored output could not be preserved"
                    ) from None
                manifest["output"] = locator
            encoded = (json.dumps(manifest, sort_keys=True) + "\n").encode()
            digest = hashlib.sha256(encoded).hexdigest()
            destination = parent / f"terminal-abandon-{task_id}-{digest}.json"
            receipt = {
                "schema": "terminal-abandon.v1",
                "disposition": "ABANDON",
                "owner": task_id,
                "run_nonce": creator.get("run_nonce"),
                "head_sha": head,
                "reason": reason,
                "preservation": {"path": "", "sha256": digest},
            }
            if recovery is not None:
                receipt["creator_recovery"] = recovery
            if merged_proof is not None:
                receipt["merged_pr"] = merged_proof
            if succession is not None:
                lease, stream, mapping_digest, authority = succession
                receipt["succession"] = {
                    "schema": "terminal-abandon-succession.v1",
                    "task_id": task_id,
                    "creator_initiator": creator.get("initiator"),
                    "caller_initiator": caller.initiator,
                    "stream_id": stream,
                    "mapping_sha256": mapping_digest,
                    "authority": authority,
                    "tree": tree.relative_to(primary).as_posix(),
                    "branch": branch,
                    "head_sha": head,
                    "preservation_sha256": digest,
                }
            with tempfile.NamedTemporaryFile(dir=parent, prefix=".terminal-abandon-", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            receipt["preservation"]["path"] = temporary.relative_to(primary).as_posix()
            candidate = dict(creator, worktree_abandon=receipt)
            proposed = [(p, candidate if p == creator_path else r) for p, r in matches]
            # Local validation of the proposed record; the complete proof, with its
            # GitHub and Monitor probes first, runs again just before publication.
            try:
                output.terminal_abandon_local(proposed, tree, primary=primary, tasks_dir=tasks, on_disk=matches)
            except output.SuccessionRefusal as exc:
                raise Refusal(exc.code, str(exc)) from None
            except (OSError, ValueError, RuntimeError):
                raise Refusal(
                    "PRESERVATION_INVALID", "bundle hashes, identity, base or Git patches failed the existing validator"
                ) from None
            receipt["preservation"]["path"] = destination.relative_to(primary).as_posix()
            if "worktree_abandon" in creator:
                if creator["worktree_abandon"] != receipt:
                    raise Refusal("ALREADY_RECORDED", "existing abandon differs; no overwrite is permitted")
                return {"outcome": "already_recorded", "task_id": task_id, "head_sha": head}
            _activity(primary, tree, matches, head, successor=succession is not None, merged=merged_proof is not None)
            if output.matching_worktree_records(tree, tasks, repo_root=primary, publish_cache=False) != matches:
                raise Refusal("STATE_CHANGED", "task cohort changed during validation; retry after it settles")
            if succession is not None:
                # Custody, the reviewed map and the copied output can all move
                # while probes run; recheck each before publishing anything.
                rechecked, observation = _observed_custody(lease, stream)
                if rechecked != authority:
                    raise Refusal("STALE_AUTHORITY", "stream custody changed during validation")
                if _succession_map()[1] != mapping_digest:
                    raise Refusal("STATE_CHANGED", "succession map changed during validation; retry after review")
                current_prs, pr_error = rw._query_pr_states(tree, source_branch)
                if pr_error is not None:
                    raise Refusal("ACTIVITY_UNKNOWN", "source PR probe unavailable before publication")
                if any(pr.state == "OPEN" for pr in current_prs):
                    raise Refusal("LIVE_OR_WANTED", "source PR opened before publication")
                try:
                    output.verify_abandon_output(tree, primary=primary, record=creator, locator=locator)
                except (OSError, ValueError, RuntimeError):
                    raise Refusal(
                        "PRESERVATION_INVALID", "untracked or ignored output changed before publication"
                    ) from None
            # Activity and PR probes take time. The validator runs its own GitHub
            # and Monitor probes first, then re-reads the cohort, head, patches and
            # output, immediately before publishing either final artifact (#10657).
            receipt["preservation"]["path"] = temporary.relative_to(primary).as_posix()
            try:
                output.terminal_abandon_creator(proposed, tree, primary=primary, tasks_dir=tasks, on_disk=matches)
            except output.SuccessionRefusal as exc:
                raise Refusal(exc.code, str(exc)) from None
            except (OSError, ValueError, RuntimeError):
                raise Refusal("PRESERVATION_INVALID", "checkout or preservation changed before publication") from None
            receipt["preservation"]["path"] = destination.relative_to(primary).as_posix()
            if destination.exists() or destination.is_symlink():
                if _regular_bytes(destination, primary) != encoded:
                    raise Refusal("PRESERVATION_INVALID", "existing manifest differs; no overwrite is permitted")
            else:
                os.replace(temporary, destination)
                created_manifest = destination
            if captured is not None:
                output.publish_abandon_output(tree, primary=primary, record=creator, locator=locator)
            original = _regular_bytes(creator_path, primary)
            artifacts.reaper_lifecycle._atomic_write(creator_path, candidate)
            if succession is not None:
                confirm_custody_after_write(creator_path, original, authority, observation)
            published = True
            return {"outcome": "recorded", "task_id": task_id, "head_sha": head}
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            if not published:
                if created_bundle is not None:
                    created_bundle.unlink(missing_ok=True)
                if created_manifest is not None:
                    created_manifest.unlink(missing_ok=True)
                if captured is not None:
                    # Only this call's unpublished copy; the checkout holds the bytes.
                    shutil.rmtree(captured, ignore_errors=True)
                    captured.with_suffix(".tar").unlink(missing_ok=True)
                    captured.with_suffix(".manifest.json").unlink(missing_ok=True)


# --- Owner-attested abandonment (#10657) -----------------------------------


def _privacy_safe(text: str, *paths: Path) -> str:
    """Keep refusal text free of host paths, as the removal gate's receipts do."""
    for path in paths:
        text = text.replace(str(path), "<path>")
    return re.sub(r"/(?:home|Users|var|tmp)/[^\s'\"]+", "<private-path>", text)


def _attested_tree(raw: str | os.PathLike[str], primary: Path) -> Path:
    """The named dispatch checkout root itself: no link spelling and no subdirectory.

    The supplied spelling is validated before anything normalizes it, so no
    component can disappear first: ``jump/../task`` with ``jump`` a symlink
    must not become ``task``. Every component must be a plain name (no ``.``,
    ``..`` or empty component, so no trailing or repeated separator; a single
    leading ``/`` marks an absolute path) and no component may be a symlink.
    Only then is the path resolved, and it must resolve to itself.
    """
    text = os.fspath(raw)
    invalid = Refusal("INVALID_INPUT", "tree must be .worktrees/dispatch/<agent>/<task> without symlinks")
    if not isinstance(text, str) or not text or "\0" in text:
        raise invalid
    absolute = text.startswith("/")
    components = (text[1:] if absolute else text).split("/")
    if any(component in ("", ".", "..") for component in components):
        raise Refusal(
            "INVALID_INPUT", "tree must be spelled without '.', '..', empty, trailing or repeated path components"
        )
    candidate = Path("/") if absolute else primary
    for component in components:
        candidate = candidate / component
        try:
            if candidate.is_symlink():
                raise invalid
        except OSError:
            raise invalid from None
    try:
        tree = candidate.resolve(strict=True)
    except (OSError, RuntimeError):
        raise Refusal("INVALID_INPUT", "tree must be an existing dispatch worktree") from None
    dispatch = primary / ".worktrees/dispatch"
    if tree != candidate or not tree.is_dir() or not tree.is_relative_to(dispatch):
        raise Refusal("INVALID_INPUT", "tree must be .worktrees/dispatch/<agent>/<task> without symlinks")
    if len(tree.relative_to(dispatch).parts) != 2:
        raise Refusal("INVALID_INPUT", "tree must be .worktrees/dispatch/<agent>/<task> without symlinks")
    top = artifacts.safe_git(
        ["rev-parse", "--show-toplevel"], cwd=tree, capture_output=True, text=True, check=False, timeout=30
    )
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != tree:
        raise Refusal("INVALID_INPUT", "tree must be the root of a Git checkout")
    return tree


def _attested_host(primary: Path, tasks: Path, task_id: str, tree: Path) -> tuple[Path, dict[str, Any]]:
    """The canonical task record that hosts the attestation; it must bind the named tree."""
    path = task_record_path(tasks, task_id)
    try:
        record = json.loads(_regular_bytes(path, primary))
    except OSError:
        raise Refusal("INVALID_INPUT", "task record must exist at its canonical task-store path") from None
    if not isinstance(record, dict) or record.get("task_id") != task_id:
        raise Refusal("INVALID_INPUT", "task record identity does not match the requested task")
    if not isinstance(record.get("run_nonce"), str) or not record["run_nonce"].strip():
        raise Refusal("INVALID_INPUT", "task record has no run nonce to bind")
    location = record.get("worktree_path") or record.get("cwd")
    if not isinstance(location, str) or claims.resolve_claim_path(location, repo_root=primary) != tree:
        raise Refusal("INVALID_INPUT", "task record does not bind the named tree")
    return path, record


def _attested_branch(tree: Path) -> str | None:
    branch = claims.checked_out_branch(tree)
    if branch is None and not output.detached_head(tree):
        raise Refusal("ACTIVITY_UNKNOWN", "checkout branch probe unavailable")
    return branch


def _replaced(matches: list[tuple[Path, dict[str, Any]]], host_path: Path, tasks: Path) -> list[dict[str, str]]:
    """The strict writer's refusals this attestation stands in for, from record state alone."""
    creators = [path for path, member in matches if output.record_created_worktree(member)]
    if len(creators) == 1 and creators[0] != host_path:
        creator = dict(matches)[creators[0]]
        if creators[0] == task_record_path(tasks, str(creator.get("task_id"))):
            raise Refusal("INVALID_INPUT", f"attest on the tree's sole creator-of-record task {creator.get('task_id')}")
    replaced = []
    if creators != [host_path]:
        replaced.append(
            {
                "code": "CREATOR_RECOVERY_REQUIRED",
                "reason": "no sole authentic creator-of-record binds this attempt; the owner attests "
                "instead of a synthesized creator",
            }
        )
    if any(member.get("status") == "needs_finalize" or member.get("keep_worktree") for _, member in matches):
        replaced.append(
            {
                "code": "LIVE_OR_WANTED",
                "reason": "unsettled status or retention intent (needs_finalize or keep_worktree) "
                "with no live activity",
            }
        )
    return replaced


def _attested_prs(tree: Path, branch: str | None, matches: list[tuple[Path, dict[str, Any]]]) -> None:
    """Every branch the tree is bound to, checked out or recorded, so detaching hides no PR.

    The removal reader runs the same check again before deleting the tree.
    """
    try:
        output.bound_branches_unclaimed(tree, branch, matches)
    except output.AttestationRefusal as exc:
        raise Refusal(exc.code, exc.reason) from None


def _attested_activity(
    primary: Path, tasks: Path, tree: Path, matches: list[tuple[Path, dict[str, Any]]], head: str
) -> None:
    """The same liveness proof as ``_activity``, naming each bound record that blocks.

    Only unsettled status and retention are waived (the reader's ``attested``
    predicate). An active task, an in-flight status, an active worker lease, a
    PID that is live or was never recorded, and every tree-level activity
    (live cwd, rollover, review, ownership, reap reservation) still refuse.
    """
    try:
        active = rw._active_task_ids()
        cwds = rw._live_cwd_paths(primary)
    except Exception:
        raise Refusal("ACTIVITY_UNKNOWN", "live task or process activity probe unavailable") from None
    if not isinstance(active, set) or cwds is None:
        raise Refusal("ACTIVITY_UNKNOWN", "live task or process activity probe unavailable")
    blockers = []
    for path, member in sorted(matches):
        name = path.relative_to(tasks).as_posix()
        pid = member.get("pid")
        lease = member.get("lease")
        if member.get("task_id") in active:
            blockers.append(f"{name} is an active task")
        elif member.get("status") not in rw._TERMINAL_DISPATCH_STATUSES:
            blockers.append(f"{name} status {member.get('status')!r} is not terminal")
        elif member.get("lease_state") == "active" or (isinstance(lease, dict) and lease.get("state") == "active"):
            blockers.append(f"{name} holds an active worker lease")
        elif not rw._pid_proven_absent(member):
            if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
                blockers.append(f"{name} has no valid recorded PID, so its worker's exit cannot be proven")
            else:
                blockers.append(f"{name} PID {pid} is held by a live process")
        elif not output.abandon_task_is_terminal(member, successor=False, merged=False, attested=True):
            blockers.append(f"{name} does not prove a settled worker")
    if blockers:
        raise Refusal(
            "LIVE_OR_WANTED", "bound record " + "; ".join(blockers) + "; an attestation never replaces liveness"
        )
    info = rw.WorktreeInfo(tree, claims.checked_out_branch(tree), head)
    reason = rw._activity_reason(repo_root=primary, info=info, active_ids=active, live_cwds=cwds)
    if reason is not None:
        raise Refusal("LIVE_OR_WANTED", f"tree activity: {_privacy_safe(reason, tree, primary)}")


def _attested_clean(tree: Path, head: str) -> None:
    try:
        output.index_settled(tree)
        output.tracked_clean(tree, head, label="attested")
    except ValueError as exc:
        raise Refusal("DIRTY_TREE", f"{exc}; an attestation never replaces a dirty tree") from None
    except (OSError, RuntimeError, subprocess.SubprocessError):
        raise Refusal(
            "DIRTY_TREE", "tracked state probe unavailable; an attestation never replaces a dirty tree"
        ) from None


def _git_bytes(tree: Path, args: list[str]) -> bytes:
    probe = artifacts.safe_git(
        args, cwd=tree, env=artifacts._safe_git_env(), capture_output=True, text=False, check=False, timeout=30
    )
    if probe.returncode != 0:
        raise Refusal("PRESERVATION_INVALID", f"git {args[0]} failed while planning preservation")
    return probe.stdout


def _preservation_plan(primary: Path, tree: Path, host: dict[str, Any], head: str) -> dict[str, Any]:
    """What the tool will preserve; any part it cannot preserve is the named blocker."""
    try:
        base = _git_bytes(tree, ["merge-base", head, "refs/remotes/origin/main"]).decode().strip()
    except Refusal:
        raise Refusal(
            "PRESERVATION_INVALID", "HEAD shares no history with origin/main; there is no bundle base"
        ) from None
    commits = int(_git_bytes(tree, ["rev-list", "--count", f"{base}..{head}"]).decode().strip())
    reflog = _reflog_commits(tree, head, primary)
    try:
        inventory = output._abandon_output_inventory(tree, primary=primary, record=host)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        raise Refusal(
            "PRESERVATION_INVALID",
            f"untracked or ignored output cannot be preserved: {_privacy_safe(str(exc), tree, primary)}",
        ) from None
    total = sum(entry["size"] for entry in inventory)
    if total > output.MAX_PRESERVED_BYTES:
        raise Refusal(
            "PRESERVATION_LIMIT",
            f"ignored output exceeds preservation cap ({total} > {output.MAX_PRESERVED_BYTES} bytes)",
        )
    return {
        "base_sha": base,
        "commits": commits,
        "reflog_commits": len(reflog),
        "commit_bundle": commits > 0 or bool(reflog),
        "output_files": len(inventory),
        "output_bytes": total,
    }


def _reflog_commits(tree: Path, head: str, primary: Path) -> list[str]:
    """Commits only the tree's own HEAD reflog reaches, or the named blocker when completeness is unknown."""
    try:
        return output.unreachable_reflog_commits(tree, head)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise Refusal("PRESERVATION_INVALID", _privacy_safe(str(exc), tree, primary)) from None


def _area_roster() -> tuple[dict[str, str], frozenset[str], str]:
    """Exact seat -> area roster from area_assignments.yaml; a seat in two areas refuses."""
    raw = AREA_ASSIGNMENTS.read_bytes()
    data = yaml.load(raw.decode("utf-8"), Loader=UniqueKeyLoader)  # SafeLoader subclass
    if not isinstance(data, dict) or not isinstance(data.get("assignments"), dict):
        raise ValueError("area assignment map invalid")
    roster: dict[str, str] = {}
    for area, entry in data["assignments"].items():
        if not isinstance(area, str) or not isinstance(entry, dict) or not isinstance(entry.get("slots"), list):
            raise ValueError("area assignment map invalid")
        for seat in entry["slots"]:
            if not isinstance(seat, str) or seat in roster:
                raise ValueError("area assignment map invalid")
            roster[seat] = area
    return roster, frozenset(data["assignments"]), hashlib.sha256(raw).hexdigest()


def _seat_area(seat: str, roster: dict[str, str], areas: frozenset[str]) -> str | None:
    """A roster seat's area, or the area of a launcher seat the bridge registers as an alias (#7597)."""
    if seat in roster:
        return roster[seat]
    from scripts.orchestration import handoff_slot_registry

    provider, separator, area = seat.partition("-")
    if (
        separator
        and provider
        and area in areas
        and handoff_slot_registry.is_registered_slot(seat, assignments_path=AREA_ASSIGNMENTS)
    ):
        return area
    return None


def owner_lane(seat: Any, holder_agent: Any, initiator: Any, initiators: list[Any]) -> dict[str, str]:
    """The lane that owns every bound task and the seat's standing in it, from the reviewed maps alone.

    The task initiator names the lane through the reviewed succession map; every
    bound task must belong to that lane. The seat must be a registered seat of
    the same area (area_assignments.yaml), of the provider holding the lease,
    mapped to that lane's stream. The writer records this and the removal
    reader recomputes it, trusting a recorded owner only where the two agree.
    """
    mapping, mapping_digest = _succession_map()
    try:
        roster, areas, assignments_digest = _area_roster()
    except (OSError, ValueError, UnicodeDecodeError, yaml.YAMLError):
        raise Refusal("OWNER_UNMAPPED", "area assignment map unavailable or invalid") from None
    stream = mapping.get(initiator) if isinstance(initiator, str) else None
    if stream is None:
        raise Refusal("OWNER_UNMAPPED", "task initiator has no reviewed lane stream; its owner cannot be verified")
    for member_initiator in initiators:
        lane = mapping.get(member_initiator) if isinstance(member_initiator, str) else None
        if lane is None:
            raise Refusal("OWNER_UNMAPPED", "a task bound to the tree has no reviewed lane stream")
        if lane != stream:
            raise Refusal("FOREIGN_OWNER", "a task bound to the tree belongs to another lane")
    seat_area = _seat_area(seat, roster, areas) if isinstance(seat, str) else None
    task_area = _seat_area(initiator, roster, areas)
    if (
        seat_area is None
        or seat.partition("-")[0] != holder_agent
        or mapping.get(seat) != stream
        or (task_area is not None and task_area != seat_area)
    ):
        raise Refusal("FOREIGN_OWNER", "caller's seat and stream custody are not the lane that owns the task")
    return {
        "seat": seat,
        "area": seat_area,
        "stream_id": stream,
        "task_initiator": initiator,
        "mapping_sha256": mapping_digest,
        "assignments_sha256": assignments_digest,
    }


def _attested_owner(caller: Any, host: dict[str, Any], matches: list[tuple[Path, dict[str, Any]]]) -> dict[str, Any]:
    """Authenticate the lane owner from this session's launcher custody, never from an argument.

    The environment's lease only names which custody the caller claims; it must
    equal Monitor's current lease of the owning lane's stream, and this process
    must run beneath that lease's recorded holder process. Neither the envelope
    nor the attributed seat can widen authority.
    """
    from agents_extensions.shared.session_streams.hooks import lease_from_environment

    try:
        lease = lease_from_environment()
    except (ValueError, TypeError):
        raise Refusal(
            "OWNER_UNAUTHENTICATED",
            "no launcher-issued stream lease in this session; an owner is never taken from an argument",
        ) from None
    if caller.source == "unknown" or caller.initiator == "unknown":
        raise Refusal("OWNER_UNAUTHENTICATED", "session seat attribution unavailable")
    owner: dict[str, Any] = owner_lane(
        caller.initiator,
        lease.holder.agent,
        host.get("initiator"),
        [member.get("initiator") for _, member in matches],
    )
    if lease.stream_id != owner["stream_id"]:
        raise Refusal("FOREIGN_OWNER", "caller's seat and stream custody are not the lane that owns the task")
    owner["authority"] = _current_custody(lease, owner["stream_id"])
    return owner


def _content_file(primary: Path, parent: Path, key: str, payload: bytes) -> tuple[dict[str, str], Path | None]:
    """Publish a digest-named preservation file once; reuse an identical existing copy."""
    digest = hashlib.sha256(payload).hexdigest()
    destination = parent / f"{key}-{digest}.patch"
    locator = {"path": destination.relative_to(primary).as_posix(), "sha256": digest}
    if destination.exists() or destination.is_symlink():
        try:
            output._abandon_file(primary, locator)
        except (OSError, ValueError):
            raise Refusal("PRESERVATION_INVALID", f"existing {key} copy differs; no overwrite is permitted") from None
        return locator, None
    with tempfile.NamedTemporaryFile(dir=parent, prefix=f".{key}-", delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return locator, destination


def record_attested_abandon(
    *, tree: str | os.PathLike[str], task_id: str, head: str, reason: str, apply: bool = False
) -> dict[str, Any]:
    """Owner-attested terminal abandonment of one dispatch tree; dry-run unless ``apply`` (#10657).

    The attestation replaces only missing creator evidence and unsettled status
    or retention intent. Liveness, open PRs, a dirty tree and preservation are
    checked exactly as for every other abandonment and are never replaced. The
    tool produces all preservation itself (commit bundle, Git patches and the
    untracked/ignored output copy); no caller bundle is read. An existing
    attestation of the same decision that no longer verifies is re-issued;
    any other existing record refuses overwrite.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", task_id) or not re.fullmatch(r"[a-f0-9]{40}", head):
        raise Refusal("INVALID_INPUT", "task id must be canonical and head must be a full lowercase 40-hex SHA")
    if not reason.strip():
        raise Refusal("INVALID_INPUT", "reason must be nonempty")
    caller = resolve_invocation_attribution()
    primary = claims.control_plane_root(Path.cwd()).resolve(strict=True)
    tasks = task_store_paths.tasks_dir()
    if tasks.absolute() != primary / "batch_state/tasks" or tasks.resolve(strict=True) != tasks.absolute():
        raise Refusal("INVALID_INPUT", "task store must be the canonical control-plane store without symlinks")
    target = _attested_tree(tree, primary)
    host_path, _ = _attested_host(primary, tasks, task_id, target)
    if not apply:
        matches = output.matching_worktree_records(target, tasks, repo_root=primary, publish_cache=False)
        return _attest(primary, tasks, target, host_path, matches, task_id, head, reason, caller, write=False)
    with contextlib.ExitStack() as locks:
        locks.enter_context(claims.worktree_lock(target, lock_dir=claims.repository_lock_dir(primary)))
        matches = output.matching_worktree_records(target, tasks, repo_root=primary, publish_cache=False)
        for member_path, _ in sorted(matches):
            _regular_bytes(member_path, primary)
            lock_path = member_path.with_suffix(member_path.suffix + ".lock")
            if lock_path.is_symlink():
                raise Refusal("INVALID_INPUT", "task lock must not be a symlink")
            locks.enter_context(artifacts.task_state_lock(member_path))
        if output.matching_worktree_records(target, tasks, repo_root=primary, publish_cache=False) != matches:
            raise Refusal("STATE_CHANGED", "task cohort changed while acquiring locks; retry after it settles")
        return _attest(primary, tasks, target, host_path, matches, task_id, head, reason, caller, write=True)


def _attest(
    primary: Path,
    tasks: Path,
    tree: Path,
    host_path: Path,
    matches: list[tuple[Path, dict[str, Any]]],
    task_id: str,
    head: str,
    reason: str,
    caller: Any,
    *,
    write: bool,
) -> dict[str, Any]:
    host = dict(matches).get(host_path)
    if host is None:
        raise Refusal("INVALID_INPUT", "task record does not bind the named tree")
    if host.get("task_id") != task_id or not isinstance(host.get("run_nonce"), str) or not host["run_nonce"].strip():
        raise Refusal("STATE_CHANGED", "task record identity or run nonce changed; retry after it settles")
    probe = rw._run(["git", "rev-parse", "HEAD"], cwd=tree)
    if probe is None or probe.returncode != 0 or probe.stdout.strip() != head:
        raise Refusal("HEAD_MISMATCH", "checkout HEAD does not match the requested exact head")
    branch = _attested_branch(tree)
    status = tree.stat()
    identity = {
        "task_id": task_id,
        "tree": tree.relative_to(primary).as_posix(),
        "directory_identity": [status.st_dev, status.st_ino],
        "branch": branch,
        "head_sha": head,
        "reason": reason,
        "cohort": output.attestation_cohort(matches, tasks),
    }
    summary: dict[str, Any] = {"task_id": task_id, "tree": identity["tree"], "head_sha": head, "branch": branch}
    replaces = None
    try:
        recorded = [(path, member) for path, member in matches if "worktree_abandon" in member]
        if recorded:
            existing = recorded[0][1]["worktree_abandon"]
            attestation = existing.get("attestation") if isinstance(existing, dict) else None
            if (
                len(recorded) != 1
                or recorded[0][0] != host_path
                or not isinstance(attestation, dict)
                or any(attestation.get(key) != value for key, value in identity.items())
            ):
                raise Refusal(
                    "ALREADY_RECORDED", "the tree already carries a terminal-abandon record; no overwrite is permitted"
                )
            try:
                output.terminal_abandon_creator(matches, tree, primary=primary, tasks_dir=tasks)
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                # The same decision on the same tree, cohort and HEAD, whose custody
                # rolled over or whose evidence went stale: it authorizes nothing,
                # so the lane's authenticated owner re-issues it after every check.
                summary["reissues"] = _privacy_safe(str(exc), tree, primary)
            else:
                return {"outcome": "already_recorded", **summary}
        replaces = _replaced(matches, host_path, tasks)
        # Slow and external probes (GitHub, Monitor, process scan) come before the
        # local tree checks, so the tree they describe is the one just read.
        _attested_prs(tree, branch, matches)
        _attested_activity(primary, tasks, tree, matches, head)
        owner = _attested_owner(caller, host, matches)
        _attested_clean(tree, head)
        plan = _preservation_plan(primary, tree, host, head)
        if not write:
            return {
                "outcome": "would_record",
                **summary,
                "replaces": replaces,
                "owner": {key: owner[key] for key in ("seat", "area", "stream_id")},
                "preservation_plan": plan,
            }
        return _publish_attestation(
            primary, tasks, tree, host_path, host, matches, identity, summary, replaces, plan, owner
        )
    except Refusal as exc:
        if replaces is not None and exc.context is None:
            exc.context = {"replaces": replaces}
        raise


def _publish_attestation(
    primary: Path,
    tasks: Path,
    tree: Path,
    host_path: Path,
    host: dict[str, Any],
    matches: list[tuple[Path, dict[str, Any]]],
    identity: dict[str, Any],
    summary: dict[str, Any],
    replaces: list[dict[str, str]],
    plan: dict[str, Any],
    owner: dict[str, Any],
) -> dict[str, Any]:
    """Produce and verify all preservation, then publish manifest, output locator and record."""
    task_id, head, base = identity["task_id"], identity["head_sha"], plan["base_sha"]
    parent = primary / "batch_state" / "abandon" / task_id
    created: list[Path] = []
    captured = None
    temporary = None
    published = False
    try:
        parent.mkdir(parents=True, exist_ok=True)
        if (
            parent.resolve(strict=True) != parent.absolute()
            or parent.is_relative_to(tree)
            or parent.is_relative_to(tasks)
        ):
            raise Refusal("INVALID_INPUT", "preservation directory must be below batch_state without symlinks")
        manifest: dict[str, Any] = {
            "schema": "terminal-abandon-preservation.v1",
            "owner": task_id,
            "run_nonce": host["run_nonce"],
            "head_sha": head,
            "base_sha": base,
        }
        for key, revisions in (
            ("head_patch", [base, head]),
            ("index_patch", ["--cached", head]),
            ("working_patch", []),
        ):
            payload = _git_bytes(
                tree, ["diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", *revisions, "--"]
            )
            manifest[key], made = _content_file(primary, parent, key, payload)
            if made is not None:
                created.append(made)
        # Recompute: the reflog can grow between the plan and publication, and
        # the reader rechecks that every reflog-only commit is in the bundle.
        reflog = _reflog_commits(tree, head, primary)
        if plan["commits"] > 0 or reflog:
            manifest["commit_bundle"], made = _detached_bundle(tree, parent, primary, head, base, reflog)
            if made is not None:
                created.append(made)
        try:
            locator, captured = output.capture_abandon_output(tree, primary=primary, record=host)
        except output.PreservationLimit as exc:
            raise Refusal("PRESERVATION_LIMIT", str(exc)) from None
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            raise Refusal(
                "PRESERVATION_INVALID",
                f"untracked or ignored output could not be preserved: {_privacy_safe(str(exc), tree, primary)}",
            ) from None
        manifest["output"] = locator
        encoded = (json.dumps(manifest, sort_keys=True) + "\n").encode()
        digest = hashlib.sha256(encoded).hexdigest()
        destination = parent / f"terminal-abandon-{task_id}-{digest}.json"
        receipt = {
            "schema": "terminal-abandon.v1",
            "disposition": "ABANDON",
            "owner": task_id,
            "run_nonce": host["run_nonce"],
            "head_sha": head,
            "reason": identity["reason"],
            "preservation": {"path": "", "sha256": digest},
            "attestation": {
                "schema": output.ATTESTATION_SCHEMA,
                **identity,
                "attested_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "owner": owner,
                "replaces": replaces,
                "preservation_sha256": digest,
            },
        }
        with tempfile.NamedTemporaryFile(dir=parent, prefix=".terminal-abandon-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        candidate = dict(host, worktree_abandon=receipt)
        proposed = [(path, candidate if path == host_path else member) for path, member in matches]

        # The unmodified removal reader validates the temporary manifest. Every
        # slow probe runs first: the reader's GitHub and Monitor probes, then
        # liveness (Monitor, process scan). Only then does the reader re-read the
        # cohort and every local fact, immediately before publication (#10657).
        receipt["preservation"]["path"] = temporary.relative_to(primary).as_posix()
        try:
            output.terminal_abandon_external(proposed, tree, primary=primary, tasks_dir=tasks)
            _attested_activity(primary, tasks, tree, matches, head)
            # The lease state the write is confirmed against: the last slow probe.
            _, observation = observe_custody(owner["authority"], caller_holds=True)
            output.terminal_abandon_local(proposed, tree, primary=primary, tasks_dir=tasks, on_disk=matches)
        except Refusal:
            raise
        except output.AttestationRefusal as exc:
            raise Refusal(exc.code, exc.reason) from None
        except output.CohortChanged as exc:
            raise Refusal("STATE_CHANGED", str(exc)) from None
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            raise Refusal(
                "PRESERVATION_INVALID",
                f"checkout or preservation changed before publication: {_privacy_safe(str(exc), tree, primary)}",
            ) from None
        receipt["preservation"]["path"] = destination.relative_to(primary).as_posix()
        if destination.exists() or destination.is_symlink():
            if _regular_bytes(destination, primary) != encoded:
                raise Refusal("PRESERVATION_INVALID", "existing manifest differs; no overwrite is permitted")
        else:
            os.replace(temporary, destination)
            created.append(destination)
        if captured is not None:
            output.publish_abandon_output(tree, primary=primary, record=host, locator=locator)
        original = _regular_bytes(host_path, primary)
        artifacts.reaper_lifecycle._atomic_write(host_path, candidate)
        confirm_custody_after_write(host_path, original, owner["authority"], observation)
        published = True
        return {
            "outcome": "recorded",
            **summary,
            "replaces": replaces,
            "owner": {key: owner[key] for key in ("seat", "area", "stream_id")},
            "preservation": {"path": destination.relative_to(primary).as_posix(), "sha256": digest},
        }
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        if not published:
            for path in created:
                path.unlink(missing_ok=True)
            if captured is not None:
                shutil.rmtree(captured, ignore_errors=True)
                captured.with_suffix(".tar").unlink(missing_ok=True)
                captured.with_suffix(".manifest.json").unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Record terminal abandonment of a settled worktree by its dispatch creator, its lane\n"
            "successor, or (--owner-attest) the lane owner. Live, PR-bound or dirty trees are refused."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n  .venv/bin/python -m scripts.fleet.terminal_abandon --task-id owner-task "
            "--head <40-hex-sha> --reason 'superseded implementation' "
            "--preservation-bundle batch_state/abandon/owner-task/bundle.json\n"
            "  .venv/bin/python -m scripts.fleet.terminal_abandon --owner-attest "
            "--tree .worktrees/dispatch/<agent>/<task> --task-id <task> --head <40-hex-sha> "
            "--reason 'owner retired superseded work'            # dry-run\n"
            "  (same command) --apply                                 # write the record\n\n"
            "Owner attestation (#10657): for a tree the creator and succession paths refuse.\n"
            "Dry-run by default; --apply writes one record per tree; a rerun is already_recorded.\n"
            "The owner is never an argument: it is this session's launcher lease, verified as the\n"
            "current custody in the canonical loopback Monitor, with this process running beneath\n"
            "the lease's recorded holder process, proven from the kernel alone: the lease generation\n"
            "must record holder.process_identity (Monitor derives it at claim from the kernel's view\n"
            "of the claim connection: the claim command's parent, the launcher; a claim carrying the\n"
            "field is refused; v1:SHA-256 of boot id, PID namespace, PID and start ticks),\n"
            "and this process must derive the same value for one of its own ancestors\n"
            "(HOLDER_UNPROVEN otherwise; a lease acquired before the field existed, an environment\n"
            "copy of a lease or a host label proves nothing; no environment value is read for this;\n"
            "the identity is a public identifier, not a credential). After writing, the tool\n"
            "observes the lease again: it must be unexpired on Monitor's clock and identical to the\n"
            "observation before the write, validity fields included; a renewal, replacement or\n"
            "expiry in between restores the record and refuses STALE_AUTHORITY. --tree is checked\n"
            "as spelled: '.', '..', empty components and symlink components refuse INVALID_INPUT.\n"
            "Its attributed seat must be registered\n"
            "in scripts/config/area_assignments.yaml for the provider holding the lease, and its\n"
            "stream must be the lane that scripts/config/terminal_abandon_succession.yaml maps\n"
            "every bound task's initiator to. It replaces only missing creator evidence\n"
            "(CREATOR_RECOVERY_REQUIRED) and unsettled status or retention intent with no live\n"
            "activity (needs_finalize or keep_worktree; LIVE_OR_WANTED). It never replaces a live\n"
            "process, an active task, a worker or rollover lease, an in-flight status, an open PR\n"
            "on any bound branch, a dirty tracked tree (DIRTY_TREE) or preservation. The tool\n"
            "itself writes a Git bundle of the commits not on origin/main, including every commit\n"
            "only the tree's own HEAD reflog still reaches (one refs/abandon/reflog/<sha> ref\n"
            "each), the three Git patches and a verified copy plus tar of untracked and ignored\n"
            "output; a caller bundle is refused. A detached tree is bound by its exact HEAD. The\n"
            "record binds tree path, directory identity, branch, HEAD, reason, owner, time and the\n"
            "complete task cohort including each initiator; any later change refuses removal.\n"
            "Removal recomputes the owning lane from the reviewed maps, rechecks every bound\n"
            "branch's PR, and requires the attested lease to still be current custody with the\n"
            "remover beneath its holder process. Writer and remover run every GitHub and Monitor\n"
            "probe first, then re-read the cohort and the checkout, immediately before acting.\n"
            "Run the reaper from the attesting session,\n"
            "  scripts/orchestration/reap_worktrees.py --legacy-classes --preserve-then-reap\n"
            "  --worktree <tree> --apply\n"
            "After a session rollover or a map change the lane's current owner reruns the same\n"
            "--owner-attest command, which re-issues the record (reissues: <why>).\n\n"
            "Bundle JSON: base_sha (40 hex), head_patch, index_patch, working_patch. Each patch is\n"
            "{path: 'batch_state/...', sha256: '<64-hex-digest>'}. Patches must equal git diff\n"
            "--binary --full-index --no-ext-diff --no-textconv for base..HEAD, --cached HEAD,\n"
            "and the working tree. The base must be an ancestor of HEAD and origin/main.\n"
            "Run from the owner's session in another checkout. Caller comes from the existing\n"
            "runtime/session attribution resolver and must match the creator's initiator.\n"
            "Lane succession: a non-creator is admitted only while its launcher session holds, and\n"
            "this process runs beneath the holder of, the Monitor-verified current lease of the\n"
            "stream that scripts/config/\n"
            "terminal_abandon_succession.yaml maps the creator's initiator to. It keeps the\n"
            "creator identity and nonce, appends a succession receipt and copies untracked and\n"
            "ignored output below batch_state/preserved/<task> before publishing, with a hash-bound\n"
            "tar archive and a 256 MiB payload cap. Detached HEAD also requires clean tracked\n"
            "bytes and a thin Git bundle excluding base_sha, separately capped at 256 MiB\n"
            "(MAX_DETACHED_BUNDLE_BYTES). Restore by fetching into a repository containing the base.\n"
            "Retention or needs_finalize requires a MERGED\n"
            "source PR containing HEAD; live processes and leases still refuse.\n"
            "Creator recovery: add --recover-creator only for missing creation evidence. It\n"
            "requires exactly one archived creator for the same task, nonce, initiator, tree,\n"
            "branch and directory inode; otherwise CREATOR_RECOVERY_REQUIRED names a manual item.\n"
            "Outputs: hashed terminal-abandon-preservation.v1 beside the bundle (attested: below\n"
            "batch_state/abandon/<task>), atomic worktree_abandon in the existing task record, and\n"
            "one JSON receipt. No retention release, tree removal, lease change or creator invention.\n"
            "Monitor must be available.\n"
            "Exit codes: 0 recorded/already_recorded/would_record (dry-run); 2 typed refusal with no\n"
            "abandon record written (NOT_CREATOR, STREAM_UNMAPPED, CROSS_STREAM, STALE_AUTHORITY,\n"
            "AUTHORITY_UNKNOWN, HOLDER_UNPROVEN, OWNER_UNAUTHENTICATED, OWNER_UNMAPPED,\n"
            "FOREIGN_OWNER, DIRTY_TREE, LIVE_OR_WANTED, PRESERVATION_INVALID, PRESERVATION_LIMIT, ...).\n"
            "Related: #10594, #10617, #10657; scripts/fleet/ignored_task_output.py;\n"
            "docs/runbooks/worktree-cleanup.md"
        ),
    )
    parser.add_argument("--task-id", required=True, help="Canonical task id whose record hosts it, e.g. owner-task")
    parser.add_argument("--head", required=True, help="Exact checkout HEAD, full lowercase 40-hex SHA")
    parser.add_argument(
        "--reason", required=True, help="Nonempty owner abandonment reason, e.g. 'superseded implementation'"
    )
    parser.add_argument(
        "--preservation-bundle",
        type=Path,
        default=None,
        help=(
            "JSON bundle below control-plane batch_state, e.g. batch_state/abandon/owner-task/bundle.json; "
            "required without --owner-attest, refused with it"
        ),
    )
    parser.add_argument(
        "--recover-creator",
        action="store_true",
        default=False,
        help="Verify archived creator evidence before abandonment (default: off); e.g. --recover-creator",
    )
    parser.add_argument(
        "--owner-attest",
        action="store_true",
        default=False,
        help="Owner-attested mode for a tree the other paths refuse (default: off; dry-run unless --apply)",
    )
    parser.add_argument(
        "--tree",
        # The raw spelling: Path() would already drop '.', repeated and trailing separators.
        type=str,
        default=None,
        help="With --owner-attest: the dispatch checkout to retire, e.g. .worktrees/dispatch/codex/owner-task",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="With --owner-attest: write the record (default: off, a read-only dry-run)",
    )
    args = parser.parse_args(argv)
    try:
        if args.owner_attest:
            if args.preservation_bundle is not None:
                raise Refusal(
                    "INVALID_INPUT",
                    "--owner-attest regenerates preservation from the tree; omit --preservation-bundle",
                )
            if args.recover_creator or args.tree is None:
                raise Refusal("INVALID_INPUT", "--owner-attest requires --tree and excludes --recover-creator")
            result = record_attested_abandon(
                tree=args.tree, task_id=args.task_id, head=args.head, reason=args.reason, apply=args.apply
            )
        else:
            if args.apply or args.tree is not None:
                raise Refusal("INVALID_INPUT", "--apply and --tree belong to --owner-attest")
            if args.preservation_bundle is None:
                raise Refusal("INVALID_INPUT", "--preservation-bundle is required without --owner-attest")
            result = record_abandon(
                task_id=args.task_id,
                head=args.head,
                reason=args.reason,
                bundle=args.preservation_bundle,
                recover_creator=args.recover_creator,
            )
    except Refusal as exc:
        result = {"outcome": "refused", "code": exc.code, "reason": str(exc), **(exc.context or {})}
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        result = {
            "outcome": "refused",
            "code": "INVALID_INPUT",
            "reason": "input, task state or required probe is unavailable or invalid",
        }
    print(json.dumps(result, sort_keys=True))
    return 2 if result["outcome"] == "refused" else 0


if __name__ == "__main__":
    raise SystemExit(main())
