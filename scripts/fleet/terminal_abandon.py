"""Write creator- or stream-custody-authorized terminal-abandon records using the existing validator."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.agent_runtime.attribution import resolve_invocation_attribution
from scripts.common import task_store_paths
from scripts.fleet import ignored_task_output as output
from scripts.orchestration import reap_worktrees as rw
from scripts.orchestration import worktree_artifacts as artifacts
from scripts.orchestration import worktree_claims as claims
from scripts.orchestration.task_record_store import locate_task_record


class Refusal(ValueError):
    """A stable, privacy-safe refusal suitable for the owner's receipt."""

    def __init__(self, code: str, reason: str):
        super().__init__(reason)
        self.code = code


RECOVERY = (
    "infra driver must recover authentic dispatch creator evidence from archived task state or a verified backup; "
    "if unavailable, a separate creator-recovery task is required; never synthesize a creator"
)


def _regular_bytes(path: Path, primary: Path) -> bytes:
    leaf = artifacts._read_preserved_bytes(path, root=primary / "batch_state")
    if leaf.file_type != "regular":
        raise Refusal("INVALID_INPUT", "input must be a regular file below batch_state, without symlink ancestors")
    return leaf.payload


def _activity(primary: Path, tree: Path, matches: list[tuple[Path, dict[str, Any]]], head: str) -> None:
    try:
        active = rw._active_task_ids()
        cwds = rw._live_cwd_paths(primary)
    except Exception:
        raise Refusal("ACTIVITY_UNKNOWN", "live task or process activity probe unavailable") from None
    if not isinstance(active, set) or cwds is None:
        raise Refusal("ACTIVITY_UNKNOWN", "live task or process activity probe unavailable")
    if any(member.get("task_id") in active for _, member in matches):
        raise Refusal("LIVE_OR_WANTED", "a bound task is active")
    if any(
        member.get("status") not in rw._TERMINAL_DISPATCH_STATUSES
        or member.get("keep_worktree")
        or member.get("lease_state") == "active"
        or (isinstance(member.get("lease"), dict) and member["lease"].get("state") == "active")
        or not rw._pid_proven_absent(member)
        for _, member in matches
    ):
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
    """Prove with Monitor that ``lease`` is the stream's current active lease.

    Membership in the succession map grants nothing; only this exact, unexpired
    lease does. A local PID never proves a remote lease expired, so Monitor is the
    sole authority and any unavailable or malformed answer refuses. Read only.
    """
    from agents_extensions.shared.session_streams.model import parse_timestamp
    from scripts.session_supervisor.remote import RemoteEpicClient, RemoteSupervisorError

    if lease.stream_id != stream:
        raise Refusal("CROSS_STREAM", "caller's stream custody is not the creator's canonical stream")
    try:
        response = RemoteEpicClient().stream(stream, digest_limit=1)
    except RemoteSupervisorError:
        raise Refusal("AUTHORITY_UNKNOWN", "Monitor stream custody probe unavailable") from None
    current = response.get("lease")
    expected = RemoteEpicClient._lease_payload(lease)
    if (
        response.get("stream_id") != stream
        or not isinstance(current, dict)
        or current.get("state") != "active"
        or current.get("session_state") not in ("open", "rolling")
        # Canonical JSON keeps int, bool and null distinct.
        or json.dumps({key: current.get(key) for key in expected}, sort_keys=True)
        != json.dumps(expected, sort_keys=True)
    ):
        raise Refusal("STALE_AUTHORITY", "caller's lease is not the stream's current active custody")
    try:
        expired = datetime.now(UTC) >= parse_timestamp(current["expires_at"])
    except (KeyError, TypeError, ValueError):
        raise Refusal("AUTHORITY_UNKNOWN", "Monitor stream custody expiry unavailable") from None
    if expired:
        raise Refusal("STALE_AUTHORITY", "caller's stream custody has expired")
    return {
        "stream_id": stream,
        "session_id": lease.session_id,
        "lease_id": lease.lease_id,
        "generation": lease.generation,
        "fencing_token": lease.fencing_token,
        "holder": {
            "agent": lease.holder.agent,
            "harness": lease.holder.harness,
            "instance_id": lease.holder.instance_id,
        },
    }


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


def record_abandon(*, task_id: str, head: str, reason: str, bundle: Path) -> dict[str, Any]:
    """Validate under dispatch's locks, then atomically publish the creator record.

    Caller identity uses the same initiator resolver as delegate's owner-only
    force-new path. It is attribution within the shared-UID control plane, not
    a security boundary against a writer already able to modify task state.
    A non-creator succeeds only while holding the Monitor-verified current lease
    of the creator's stream from the reviewed succession map. That record keeps
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
    if path is None:
        raise Refusal("CREATOR_RECOVERY_REQUIRED", RECOVERY)
    record = json.loads(_regular_bytes(path, primary))
    if not isinstance(record, dict) or not output.record_created_worktree(record):
        raise Refusal("CREATOR_RECOVERY_REQUIRED", RECOVERY)
    raw_tree = record.get("worktree_path") or record.get("cwd")
    if not isinstance(raw_tree, str):
        raise Refusal("CREATOR_RECOVERY_REQUIRED", RECOVERY)
    tree = claims.resolve_claim_path(raw_tree, repo_root=primary)
    if tree is None or not tree.is_dir():
        raise Refusal("CREATOR_RECOVERY_REQUIRED", RECOVERY)
    if tree == primary or not tree.is_relative_to(primary / ".worktrees/dispatch"):
        raise Refusal("INVALID_INPUT", "target must be an existing dispatch worktree")
    branch = claims.checked_out_branch(tree)
    prs, error = rw._query_pr_states(tree, branch)
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
        creators = [(p, r) for p, r in matches if output.record_created_worktree(r)]
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
        if succession is not None and not isinstance(branch, str):
            raise Refusal("INVALID_INPUT", "succession requires a checked-out branch")
        _activity(primary, tree, matches, head)
        if "worktree_abandon" in creator:
            output.terminal_abandon_creator(matches, tree, primary=primary, tasks_dir=tasks)
            old = creator["worktree_abandon"]
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
        if succession is not None:
            # Git patches cannot carry untracked or ignored bytes; a successor
            # is not their author, so it preserves them before deciding.
            try:
                locator, captured = output.capture_abandon_output(tree, primary=primary, record=creator)
            except (OSError, ValueError, RuntimeError):
                raise Refusal("PRESERVATION_INVALID", "untracked or ignored output could not be preserved") from None
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
        published = False
        try:
            with tempfile.NamedTemporaryFile(dir=parent, prefix=".terminal-abandon-", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            if captured is not None:
                shutil.rmtree(captured, ignore_errors=True)
            raise
        try:
            receipt["preservation"]["path"] = temporary.relative_to(primary).as_posix()
            candidate = dict(creator, worktree_abandon=receipt)
            proposed = [(p, candidate if p == creator_path else r) for p, r in matches]
            try:
                output.terminal_abandon_creator(proposed, tree, primary=primary, tasks_dir=tasks)
            except (OSError, ValueError, RuntimeError):
                raise Refusal(
                    "PRESERVATION_INVALID", "bundle hashes, identity, base or Git patches failed the existing validator"
                ) from None
            receipt["preservation"]["path"] = destination.relative_to(primary).as_posix()
            if "worktree_abandon" in creator:
                if creator["worktree_abandon"] != receipt:
                    raise Refusal("ALREADY_RECORDED", "existing abandon differs; no overwrite is permitted")
                return {"outcome": "already_recorded", "task_id": task_id, "head_sha": head}
            _activity(primary, tree, matches, head)
            if output.matching_worktree_records(tree, tasks, repo_root=primary, publish_cache=False) != matches:
                raise Refusal("STATE_CHANGED", "task cohort changed during validation; retry after it settles")
            if succession is not None:
                # Custody, the reviewed map and the copied output can all move
                # while probes run; recheck each before publishing anything.
                if _current_custody(lease, stream) != authority:
                    raise Refusal("STALE_AUTHORITY", "stream custody changed during validation")
                if _succession_map()[1] != mapping_digest:
                    raise Refusal("STATE_CHANGED", "succession map changed during validation; retry after review")
                try:
                    output.verify_abandon_output(tree, primary=primary, record=creator, locator=locator)
                except (OSError, ValueError, RuntimeError):
                    raise Refusal(
                        "PRESERVATION_INVALID", "untracked or ignored output changed before publication"
                    ) from None
            # Activity probes can take time. Revalidate the head and every patch
            # after them, immediately before publishing either final artifact.
            receipt["preservation"]["path"] = temporary.relative_to(primary).as_posix()
            try:
                output.terminal_abandon_creator(proposed, tree, primary=primary, tasks_dir=tasks)
            except (OSError, ValueError, RuntimeError):
                raise Refusal("PRESERVATION_INVALID", "checkout or preservation changed before publication") from None
            receipt["preservation"]["path"] = destination.relative_to(primary).as_posix()
            if destination.exists() or destination.is_symlink():
                if _regular_bytes(destination, primary) != encoded:
                    raise Refusal("PRESERVATION_INVALID", "existing manifest differs; no overwrite is permitted")
            else:
                os.replace(temporary, destination)
            if captured is not None:
                output.publish_abandon_output(tree, primary=primary, record=creator, locator=locator)
            published = True
            artifacts.reaper_lifecycle._atomic_write(creator_path, candidate)
            return {"outcome": "recorded", "task_id": task_id, "head_sha": head}
        finally:
            temporary.unlink(missing_ok=True)
            if captured is not None and not published:
                # Only this call's unpublished copy; the checkout still holds the bytes.
                shutil.rmtree(captured, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Record terminal abandonment of a settled worktree by its dispatch creator.\n"
            "Use after preserving exact patches; live or wanted trees and unknown creators are refused."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n  .venv/bin/python -m scripts.fleet.terminal_abandon --task-id owner-task "
            "--head <40-hex-sha> --reason 'superseded implementation' "
            "--preservation-bundle batch_state/abandon/owner-task/bundle.json\n\n"
            "Bundle JSON: base_sha (40 hex), head_patch, index_patch, working_patch. Each patch is\n"
            "{path: 'batch_state/...', sha256: '<64-hex-digest>'}. Patches must equal git diff\n"
            "--binary --full-index --no-ext-diff --no-textconv for base..HEAD, --cached HEAD,\n"
            "and the working tree. The base must be an ancestor of HEAD and origin/main.\n"
            "Run from the owner's session in another checkout. Caller comes from the existing\n"
            "runtime/session attribution resolver and must match the creator's initiator.\n"
            "Lane succession: a non-creator is admitted only while its launcher session holds the\n"
            "Monitor-verified current lease of the stream that scripts/config/\n"
            "terminal_abandon_succession.yaml maps the creator's initiator to. It keeps the\n"
            "creator identity and nonce, appends a succession receipt and copies untracked and\n"
            "ignored output below batch_state/preserved/<task> before publishing.\n"
            "Outputs: hashed terminal-abandon-preservation.v1 beside the bundle, atomic\n"
            "worktree_abandon in the existing creator task record, and one JSON receipt.\n"
            "No retention release, tree removal, lease change or creator invention. Monitor must be available.\n"
            "Exit codes: 0 recorded/already_recorded; 2 typed refusal with no abandon record written\n"
            "(NOT_CREATOR, STREAM_UNMAPPED, CROSS_STREAM, STALE_AUTHORITY, AUTHORITY_UNKNOWN, ...).\n"
            "Related: #10594, #10617; scripts/fleet/ignored_task_output.py; docs/runbooks/worktree-cleanup.md"
        ),
    )
    parser.add_argument("--task-id", required=True, help="Creator's canonical owner task id, e.g. owner-task")
    parser.add_argument("--head", required=True, help="Exact checkout HEAD, full lowercase 40-hex SHA")
    parser.add_argument(
        "--reason", required=True, help="Nonempty owner abandonment reason, e.g. 'superseded implementation'"
    )
    parser.add_argument(
        "--preservation-bundle",
        required=True,
        type=Path,
        help="JSON bundle below control-plane batch_state, e.g. batch_state/abandon/owner-task/bundle.json",
    )
    args = parser.parse_args(argv)
    try:
        result = record_abandon(
            task_id=args.task_id, head=args.head, reason=args.reason, bundle=args.preservation_bundle
        )
    except Refusal as exc:
        result = {"outcome": "refused", "code": exc.code, "reason": str(exc)}
    except (OSError, ValueError, RuntimeError):
        result = {
            "outcome": "refused",
            "code": "INVALID_INPUT",
            "reason": "input, task state or required probe is unavailable or invalid",
        }
    print(json.dumps(result, sort_keys=True))
    return 2 if result["outcome"] == "refused" else 0


if __name__ == "__main__":
    raise SystemExit(main())
