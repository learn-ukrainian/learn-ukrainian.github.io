"""Detached supervision, client waits and process-group cancellation."""

import contextlib
import ctypes
import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import psutil

from scripts.agent_runtime import bounded_advisory
from scripts.agent_runtime.read_only_tmp import create_dispatch_lease, discard_dispatch_lease
from scripts.common import task_scratch
from scripts.common.repo_root import project_interpreter
from scripts.common.scratch import ensure_scratch_root
from scripts.common.task_scratch import TaskScratchError
from scripts.dispatcher import admission, agy_sandbox, git, headroom, ownership, providers, runtime_context, store
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.types import ParsedResult, TaskSpec
from scripts.dispatcher.watchdog import (
    TERMINAL_EXIT_GRACE_S,
    DeadlineExpired,
    communicate,
    deadlines,
    liveness_paths,
)
from scripts.review.model_catalog import advisory_role_policy
from scripts.review.product_hooks import attempt_hooks


def _seal_advisory_result(record: dict, result: Path) -> None:
    """Seal an advisory decision's result as written (``bounded_advisory.seal_advisor_result``).

    A seal that cannot be computed is left out, so every consumer refuses the
    result as unsealed; it never stops the record from settling.
    """
    try:
        fence = advisory_role_policy(record["advisory_role"]).fence
        response = result.read_bytes().decode("utf-8")
    except (KeyError, OSError, UnicodeDecodeError, ValueError) as exc:
        record["advisory_seal_error"] = f"{type(exc).__name__}: {exc}"[:300]
        return
    record[bounded_advisory.SEAL_FIELD] = bounded_advisory.seal_advisor_result(
        response, model=record.get("model"), run_nonce=record.get("run_nonce"), fence=fence
    )


# Re-creatable caches a worker leaves in its own task output directories. Settlement removes these directories
# and keeps every log, result, receipt and hand-off beside them (C-4946(a)).
TASK_CACHE_DIRS = frozenset({"venv", ".venv", "buildvenv", "npm-cache", ".npm", "node_modules", "pip-cache", ".cache",
                             "__pycache__"})


def _remove_cache_entry(dir_fd: int, name: str) -> None:
    """Unlink a cache-named link, or remove one cache directory, relative to ``dir_fd``.

    A link is unlinked and never followed. A directory is removed by the same remover
    ``_remove_task_scratch`` uses: this directory gets owner rwx when it lacks it, children
    are repaired on descent, and another device or a mount point is refused before anything
    is unlinked. The chmod and the deletion stay inside ``name``.
    """
    info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
    if stat.S_ISLNK(info.st_mode):
        os.unlink(name, dir_fd=dir_fd)
        return
    if not stat.S_ISDIR(info.st_mode):
        return
    parent = os.fstat(dir_fd)
    mount_id = task_scratch.fd_mount_id(dir_fd)
    if info.st_dev != parent.st_dev:
        raise task_scratch.ContainmentError(f"cache {name!r} is on another filesystem")
    if mount_id is None:
        raise task_scratch.ContainmentError("mount information unavailable")
    if stat.S_IMODE(info.st_mode) & stat.S_IRWXU != stat.S_IRWXU:
        # A read-only top directory would refuse to give up its entries; children are repaired on descent.
        task_scratch.grant_owner_rwx(dir_fd, name, info, device=parent.st_dev, mount_id=mount_id)
    # The held descriptor's path is what mountinfo names. The scratch remover refuses a mount
    # below this directory before it unlinks anything, and it never chmods outside the directory.
    task_scratch._remove_invocation_dir(
        dir_fd,
        name,
        namespace=Path(os.readlink(f"/proc/self/fd/{dir_fd}")),
        expected_dev=info.st_dev,
        expected_ino=info.st_ino,
    )


def _task_caches(task_id: str, *, remove: bool) -> tuple[list[str], list[str]]:
    """The cache directories in ``<task_id>.artifacts`` and ``<task_id>.evidence``, and what could not be walked or removed.

    os.fwalk holds each directory open and checks it with lstat, open and fstat before it descends, so neither a
    link nor an ancestor swapped during the walk takes it outside the task's outputs. Removal acts relative to the
    held parent. ``DirEntry.is_dir`` follows links, so a dangling cache link or a link to a file is listed in
    ``files``; those names are unlinked too. A real directory goes through the scratch remover.
    """
    tasks = store.record_path(task_id).parent  # refuses an invalid task id before any path is built from it
    found: list[str] = []
    failed: list[str] = []

    def refused(error: OSError) -> None:
        failed.append(f"{error.filename}: {type(error).__name__}")

    def drop(directory: str, dir_fd: int, name: str) -> None:
        found.append(f"{directory}/{name}")
        if not remove:
            return
        try:
            _remove_cache_entry(dir_fd, name)
        except (OSError, task_scratch.ContainmentError) as exc:
            failed.append(f"{directory}/{name}: {type(exc).__name__}")

    tasks_fd = os.open(tasks, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for root in (f"{task_id}.artifacts", f"{task_id}.evidence"):
            try:
                os.stat(root, dir_fd=tasks_fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            try:
                for directory, names, files, dir_fd in os.fwalk(root, onerror=refused, dir_fd=tasks_fd):
                    for name in [name for name in names if name in TASK_CACHE_DIRS]:
                        names.remove(name)  # do not descend into a directory this pass is removing
                        drop(directory, dir_fd, name)
                    for name in files:
                        if name not in TASK_CACHE_DIRS:
                            continue
                        try:
                            linked = stat.S_ISLNK(os.stat(name, dir_fd=dir_fd, follow_symlinks=False).st_mode)
                        except OSError as exc:
                            failed.append(f"{directory}/{name}: {type(exc).__name__}")
                            continue
                        if linked:
                            drop(directory, dir_fd, name)
            except OSError as exc:  # the root, or a listing os.fwalk does not pass to onerror
                failed.append(f"{root}: {type(exc).__name__}")
    finally:
        os.close(tasks_fd)
    return found, failed


def _clear_task_caches(record: dict) -> bool:
    """Remove a finished task's re-creatable caches from its own output directories; True when the record changed.

    The caller holds the task state lock. Whatever could not be walked or removed is recorded in
    ``task_cache_residue`` and retried by the scheduled settlement sweep.
    """
    if record.get("status") in store.ACTIVE:
        return False
    try:
        residue = _task_caches(record["task_id"], remove=True)[1]
    except Exception as exc:  # cache removal never stops the worktree settlement that follows it
        residue = [f"scan: {type(exc).__name__}"]
    if residue == record.get("task_cache_residue", []):
        return False
    if residue:
        record["task_cache_residue"] = residue
    else:
        record.pop("task_cache_residue")
    return True


def _identity(pid: int | None) -> str | None:
    if not pid:
        return None
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        return None if fields[0] == "Z" else f"{boot}:{fields[19]}"
    except (OSError, IndexError):
        return None


def _observe(record: dict) -> dict:
    if _spawn_expired(record):
        path = store.record_path(record["task_id"])
        with store.task_state_lock(path):
            current = store.read(record["task_id"], record["run_nonce"])
            if current.get("started_at") == record.get("started_at") and _spawn_expired(current):
                current.update(status="crashed", finished_at=store.now(),
                               returncode_reason="spawn_process_missing", error="spawn never produced a supervisor")
                store.replace(current, path)
            record = current
    if (record.get("schema_version") == 2 and record.get("status") in store.ACTIVE
            and record.get("pid") is None and record.get("admission_hold")):
        from scripts.dispatcher.host_admission import heal_dead

        heal_dead(store.record_path(record["task_id"]), record)
        return store.read(record["task_id"], record["run_nonce"])
    if (
        record.get("schema_version") == 2
        and record["status"] in store.ACTIVE
        and record.get("pid")
        and _identity(record["pid"]) != record.get("process_start")
    ):
        current = store.read(record["task_id"], record["run_nonce"])
        if current["status"] not in store.ACTIVE:
            return current
        record.update(status="crashed", finished_at=store.now(), error="supervisor exited without a result")
        _discard_read_only_scratch(record)  # a killed supervisor never reached its own cleanup
        record["duration_s"] = (
            datetime.fromisoformat(record["finished_at"]) - datetime.fromisoformat(record["started_at"])
        ).total_seconds()
        record.update(git.snapshot_delivery(_spec(record, {}), record))
        store.replace(record)
    return record


def _dispatcher_code() -> dict:
    """The checkout whose dispatcher supervises this task: its HEAD and whether its code is unmodified.

    Recorded when the supervisor starts and again when it settles. A review-contract canary
    needs both to be the same clean checkout at the head it reviewed (#12399). An unreadable
    checkout records ``head`` None, which no canary accepts.
    """
    from scripts.common.git_context import sanitized_git_env

    root = Path(__file__).resolve().parents[2]

    def git_out(*args: str) -> str | None:
        try:
            return subprocess.run(["git", *args], cwd=root, env=sanitized_git_env(), capture_output=True,
                                  text=True, check=True, timeout=30).stdout
        except (OSError, subprocess.SubprocessError):
            return None

    head = (git_out("rev-parse", "HEAD") or "").strip() or None
    package = Path(os.path.abspath(__file__)).parents[1].name  # the machinery package directory
    status = git_out("status", "--porcelain", "--", package, "schemas")
    return {"root": str(root), "head": head, "clean": status == ""}


def _discard_read_only_scratch(record: dict) -> None:
    """Remove a dispatched Codex read-only task's scratch; residue is recorded, never raised."""
    if record["agent"] == "codex" and record["mode"] == "read-only" and (
        residue := discard_dispatch_lease(record["task_id"])
    ):
        record["read_only_scratch_cleanup"] = residue


def _spawn_expired(record: dict) -> bool:
    """Recover old pid-less launches, preserving a live or unprovable setup owner."""
    from scripts.orchestration import dispatch_admission

    if (record.get("schema_version") != 2 or record.get("status") != "spawning"
            or record.get("pid") is not None or record.get("admission_hold") or record.get("worktree_prep")
            or any(name.startswith("launch_") for name in record)):
        return False
    try:
        started = datetime.fromisoformat(record["started_at"].replace("Z", "+00:00"))
        age = (datetime.now(UTC) - started.replace(tzinfo=started.tzinfo or UTC)).total_seconds()
    except (KeyError, TypeError, ValueError, AttributeError):
        return False
    return age > dispatch_admission.PIDLESS_SPAWNING_GRACE_S


def _stream_attestation(source: str, model: str | None) -> dict:
    """A record's model attestation from that provider's own stream-json, pending until the stream names one."""
    return dict(resolved_model=model if model is not None else "unknown", resolved_model_known=model is not None,
                resolved_model_source=source if model is not None else "pending")


def _submitted_prompt_already_published(record: dict, prompt: bytes, failed: str | None) -> bool:
    """True when exclusive prompt publication collided with the submitted bytes.

    ``store.create`` writes ``record["prompt_file"]`` with ``"xb"`` (``store.py``). A review
    brief is often already that path: ``--prompt-file batch_state/tasks/<task_id>.prompt``.
    The exclusive create then raises ``FileExistsError`` before any supervisor exists, and
    ``start`` records ``spawn_setup_failed``. The same bytes are the prompt this launch
    would publish, so the collision is the source file, not a foreign occupant. A different
    file, a symlink, or a ``FileExistsError`` from another path still fails closed.
    """
    expected = record.get("prompt_file")
    if not isinstance(failed, str) or not isinstance(expected, str) or not expected:
        return False
    if os.path.normpath(failed) != os.path.normpath(expected):
        return False
    path = Path(expected)
    try:
        info = path.lstat()
        held = path.read_bytes() if stat.S_ISREG(info.st_mode) else None
    except OSError:
        return False
    return held == prompt


def start(spec: TaskSpec, record: dict, prompt: bytes, hard_timeout: float) -> None:
    from scripts.orchestration.dispatch_admission import new_admission_hold

    source = getattr(providers.load(spec.agent), "MODEL_SOURCE", None)
    if source:
        record.update(_stream_attestation(source, None))
    if not record.get("admission_hold"):
        record["admission_hold"] = new_admission_hold(record["run_nonce"])
    path = store.record_path(spec.task_id)
    logs = path.parent / "logs"
    try:
        try:
            store.create(record, prompt)
        except FileExistsError as exc:
            if not _submitted_prompt_already_published(record, prompt, exc.filename):
                raise
        logs.mkdir(exist_ok=True, mode=0o700)
        with open(logs / f"{spec.task_id}.stderr.log", "ab", opener=lambda p, f: os.open(p, f, 0o600)) as err:
            mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM, signal.SIGINT})
            try:
                process, launch = admission.spawn_supervisor(
                    [str(project_interpreter()), "-m", "scripts.dispatcher.worker", str(path)],
                    task_id=spec.task_id, run_nonce=record["run_nonce"], cwd=Path(__file__).resolve().parents[2],
                    stderr=err, stderr_log=logs / f"{spec.task_id}.stderr.log",
                    env={**os.environ,
                         "LEARN_UKRAINIAN_DISPATCH_TASK_ID": spec.task_id,
                         "LEARN_UKRAINIAN_DISPATCH_AGENT": spec.agent},
                )
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, mask)
        record.update(pid=process.pid, process_start=_identity(process.pid), **launch)
        if record.get("launch_mode") == "scope":
            # Crash recovery reads the scope's members to prove the whole task tree has exited.
            record["launch_cgroup"] = _cgroup(process.pid)
        store.replace(record, path)
        payload = json.dumps({"options": spec.options, "hard_timeout": hard_timeout}).encode()
        process.stdin.write(payload)
        process.stdin.close()
    except BaseException as exc:
        # create() can publish the record before prompt/log setup fails. Never
        # overwrite another run, or a supervisor that has already settled.
        with store.task_state_lock(path):
            current = store.read(spec.task_id, missing_ok=True)
            if (current is not None and current.get("run_nonce") == record["run_nonce"]
                    and current.get("status") in store.ACTIVE):
                fields = (exc.fields if isinstance(exc, admission.LaunchRefused) else
                          dict(status="failed" if current.get("pid") is None else "crashed",
                               error="supervisor launch failed"))
                reason = (fields["error"].split(":", 1)[0] if isinstance(exc, admission.LaunchRefused) else
                          "spawn_setup_failed" if current.get("pid") is None else "supervisor_launch_failed")
                if not isinstance(exc, admission.LaunchRefused):
                    fields["error"] = f"{reason}: {type(exc).__name__}"
                current.update(fields, finished_at=store.now(), returncode_reason=reason)
                store.replace(current, path)
        raise


class _Cancelled(Exception):
    pass


def _spec(record: dict, options: dict) -> TaskSpec:
    return TaskSpec(
        record["task_id"],
        record["agent"],
        record["model"],
        record["effort"],
        record["mode"],
        Path(record["worktree_path"]),
        Path(record["prompt_file"]),
        Path(record["result_file"]),
        record["claude_account"],
        record["provider"],
        {**record.get("options", {}), **options},
        codex_account=record.get("codex_account"),
    )


def _outside_cause(paths, owned) -> str | None:
    from scripts.guardrails.delegate_ownership import sanitize_for_display
    from scripts.secret_redactor import redact_text

    outside = ownership.outside_owned(paths, owned)
    if not outside:
        return None
    cause = "outside_owned_paths: " + ", ".join(sanitize_for_display(redact_text(path)) for path in outside)
    return cause if len(cause) <= 1024 else cause[:1009] + "... (truncated)"


def _verification_cause(exc: Exception) -> str:
    """Name what stopped the ownership check: the failing Git step, or the check's own refusal."""
    return f"owned_paths_verification_failed: {ownership.failure_detail(exc)}"[:200]


def _enforce_delivery(record: dict) -> None:
    if record["mode"] == "read-only" or record["status"] != "done":
        return
    cause = None
    paths = []
    try:
        owned = ownership.effective_scope(record)
    except (ValueError, TypeError) as exc:
        record.update(status="no_deliverable", error=_verification_cause(exc),
                      no_deliverable_reason=_verification_cause(exc))
        return
    # With no commits ahead there is nothing to verify, and the remote branch may never have existed.
    if owned and (record.get("commits_ahead") or 0) > 0:
        try:
            with git.ownership_git(record) as run:
                base_sha = run("rev-parse", "--verify", "refs/heads/base^{commit}")
                start_sha = record.get("worktree_start_sha", record["worktree_base_sha"])
                paths = ownership.delivered_paths(run, record["head_sha"], base_sha, start_sha,
                                                  commits_expected=True)
            cause = _outside_cause(paths, owned)
        except (OSError, ValueError, TypeError, IndexError, KeyError, TaskScratchError, subprocess.SubprocessError) as exc:
            cause = _verification_cause(exc)
    if cause is None:
        if record.get("worktree_dirty_on_exit") is not False:
            cause = "worktree_dirty_or_unknown"
        elif not record.get("commits_ahead"):
            cause = "no_commits_or_unknown"
        elif record.get("push_state") != "pushed":
            cause = "work_not_pushed_or_unknown"
    # Merged work leaves nothing on the task branch to inspect (it may be reset or deleted), so the
    # merged pull request is the evidence; it refuses an outside-owned path the same way.
    if cause and cause.split(":", 1)[0] in MERGE_RESCUABLE and record.get("worktree_dirty_on_exit") is False and (
            merged := git.merged_delivery(record)):
        paths = merged["paths"]
        cause = _outside_cause(paths, owned) if owned else None
        record["delivery_pr"] = f"{merged['repo']}#{merged['number']}"
    record["owned_path_grants_used"] = ownership.grants_used(record, paths)
    if cause:
        record.update(status="no_deliverable", error=cause, no_deliverable_reason=cause)


# Refusals that a merged pull request answers: the local branch could not show the delivery.
MERGE_RESCUABLE = frozenset({"owned_paths_verification_failed", "no_commits_or_unknown", "work_not_pushed_or_unknown"})


def _cgroup(pid: int) -> str | None:
    with contextlib.suppress(OSError):
        return next((line[3:] for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines()
                     if line.startswith("0::")), None)
    return None


def _scope_cgroups(unit: str) -> list[str] | None:
    """Every cgroup the tree holds for ``unit``'s scope; None when the traversal was not complete."""
    root, failed, found = "/sys/fs/cgroup", [], []

    def refused(error: OSError) -> None:
        failed.append(error)

    for directory, _names, _files in os.walk(root, onerror=refused):
        if os.path.basename(directory) == f"{unit}.scope":
            found.append(directory.removeprefix(root))
    return None if failed else found


def _provider_alive(record: dict) -> bool | None:
    """Whether the provider's process tree still runs, from the identity recorded for it; None when unknown."""
    if record.get("launch_mode") == "scope":
        # The scope holds every descendant, including ones that left the provider's process group.
        unit = record.get("launch_unit")
        if cgroup := record.get("launch_cgroup"):
            cgroups = [cgroup]
        elif isinstance(unit, str) and re.fullmatch(r"lu-worker-[A-Za-z0-9._-]+", unit):
            # A supervisor that ended before it read the provider's cgroup still named the scope's unit,
            # which is found wherever it was placed.
            cgroups = _scope_cgroups(unit)
            if cgroups is None:
                return None
        else:
            return None
        controllers = Path("/sys/fs/cgroup/cgroup.controllers").exists()
        alive = False
        for cgroup in cgroups:
            try:
                procs = Path("/sys/fs/cgroup" + cgroup, "cgroup.procs").read_text().split()
            except FileNotFoundError:
                # The kernel refuses to remove a cgroup that still holds processes, so a gone scope is empty.
                if not controllers:
                    return None
                continue
            except OSError:
                return None
            alive = alive or any(int(pid) != os.getpid() for pid in procs)
        # No scope under the unit's name is a gone scope, which held nothing, on a cgroup v2 host.
        return alive if cgroups or controllers else None
    if "provider_pgid" not in record:
        # The supervisor ended before recording whether it started a provider. A launch that the
        # dispatcher itself recorded as never having produced a supervisor started none.
        # spawn_setup_failed is that record: start() settled with no pid before a provider existed.
        never_ran = record.get("returncode_reason") in {
            "spawn_process_missing", "dispatch_died_after_admission", "spawn_setup_failed",
        }
        return False if never_ran and record.get("pid") is None and record.get("process_start") is None else None
    if record["provider_pgid"] is None:
        return False
    try:
        os.killpg(record["provider_pgid"], 0)
    except ProcessLookupError:
        # A descendant that left the group is named by the stop that could not end it (#12520).
        return any(_identity(int(pid)) == identity for pid, identity in record.get("fallback_survivors", {}).items())
    except PermissionError:
        pass
    return True


def _same_tree(left: str | None, right: str | None) -> bool:
    """Whether two recorded paths name one directory: by inode while both exist, else by resolved path."""
    if not left or not right:
        return False
    with contextlib.suppress(OSError):
        return os.path.samefile(left, right)
    return os.path.realpath(left) == os.path.realpath(right)


def _borrowed(record: dict) -> bool:
    """Whether another task may still work in this task's worktree (dispatched there with --cwd).

    Liveness outranks status: a terminal borrower (a crashed supervisor) holds the tree until its
    provider is proven gone. A borrower whose supervisor never started (no pid) never ran a provider.
    """
    return any(
        other.get("task_id") != record["task_id"] and _same_tree(other.get("worktree_path"), record.get("worktree_path"))
        and (other.get("status") in store.ACTIVE or (other.get("pid") is not None and _provider_alive(other) is not False))
        for other in store.list_tasks())


def _running_children(record: dict) -> list[str]:
    """Tasks this run dispatched that are still running as it settles: no one is left to read their results.

    A child whose status is not a string is not running: no record may stop this settlement.
    """
    with contextlib.suppress(OSError, ValueError):
        return sorted(other["task_id"] for other in store.list_tasks()
                      if other.get("parent_task_id") == record["task_id"]
                      and isinstance(other.get("status"), str) and other["status"] in store.ACTIVE)
    return []


def _children_at(record: dict, deadline: float, checkpoint) -> list[str]:
    """Child tasks still running at ``deadline``.

    Polls until they leave the active states or the deadline passes. A hard
    timeout of zero does not wait: the caller is already out of time. Cancel
    is checked on each poll, the same way the provider wait checks it.
    """
    children = _running_children(record)
    while children and time.monotonic() < deadline:
        checkpoint()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(1.0, remaining))
        children = _running_children(record)
    return children


def _agy_follow_up(spec: TaskSpec, record: dict, parsed: ParsedResult, started: float,
                   hard_timeout: float, resumes: int, checkpoint) -> tuple[str | None, ParsedResult]:
    """Resume an AGY workspace-write turn that closed while its work was still open.

    Returns ``(conversation id, parsed)`` to launch again, or ``(None, parsed)``
    to settle ``parsed``. A child still active at the task deadline becomes a
    typed failure naming that child. The resume flag is the adapter's
    ``--conversation``.
    """
    from scripts.dispatcher.providers.agy import CONTINUATION_LIMIT, conversation_id

    if spec.agent != "agy" or spec.mode != "workspace-write":
        return None, parsed
    incomplete = parsed.error == "agy: incomplete run"
    children = _running_children(record)
    if not incomplete and not children:
        return None, parsed
    deadline = started + hard_timeout if hard_timeout > 0 else time.monotonic()
    saw_children = bool(children)
    if children:
        children = _children_at(record, deadline, checkpoint)
    if children:
        named = ", ".join(children)
        return None, replace(parsed, error=f"agy_child_still_running: {named}")
    if resumes >= CONTINUATION_LIMIT or time.monotonic() >= deadline:
        return None, _agy_unfinished(parsed)
    if not incomplete and not saw_children:
        return None, parsed
    log = spec.final_file.with_suffix(".log")
    conversation = conversation_id(log) if log.is_file() else None
    if not conversation:
        return None, _agy_unfinished(parsed)
    return conversation, parsed


def _agy_unfinished(parsed: ParsedResult) -> ParsedResult:
    """An interim success is not final when no continuation produced a later result."""
    if parsed.error:
        return parsed
    return replace(parsed, error="agy: incomplete run")


# Dispositions that can change once other processes end, the tree is committed or reverted, the work is
# published (pushed or merged after the task ended), or a transient Git, lock, claim or removal failure
# clears; the scheduled cleanup retries these under the same removal proofs.
# Admission and worker exit never retry unrelated tasks. A public-push refusal
# (opsec_refused) and an owner retention hold (retention_hold) are absent on purpose:
# automation must not retry either.
RETRY_REASONS = frozenset({"dirty", "provider_processes_alive", "provider_liveness_unknown", "borrowed_by_live_task",
                           "unpublished", "remote_mismatch", "unknown", "removal_refused",
                           "worktree_remove_failed", "settlement_failed",
                           "salvage_failed", "salvage_unverified", "large_ignored_output",
                           "nested_repository_unpushed", "github_deferred", git.CODE_UNAVAILABLE})


def _load_bound_review_code() -> None:
    """Import what a bound formal review attempt (``review_attempt.run``) imports on demand.

    Only that kind of run needs the build engine's manifest, the evidence sources, the review prompt checks and the agent runner with
    its ``ai_llm`` package. The manifest import reaches ``scripts.wiki.dense_rerank``, which imports numpy, and numpy starts an
    OpenBLAS thread pool in this process. The pool shares the file table. A supervisor that then holds review slots keeps those
    flocks in the same table; SIGKILL makes the leader a zombie, which ``_identity`` treats as gone, while the pool still holds
    the flocks, so the hold stays live. A bound attempt does not take review slots (``hold_review_test_slots`` returns immediately
    when ``review_attempt`` is set), so only that run loads this code. The runner imports ``ai_llm`` from ``scripts/``, which
    ``review_attempt.run`` puts on ``sys.path`` just before it imports the runner; do the same, and leave ``sys.path`` as it was.
    """
    scripts_dir = str(Path(__file__).resolve().parents[1])
    added = scripts_dir not in sys.path
    if added:
        sys.path.insert(0, scripts_dir)
    try:
        with contextlib.suppress(Exception):
            attempt_hooks().bind_bound_review_modules()
        with contextlib.suppress(Exception):
            from scripts.agent_runtime import runner  # noqa: F401
    finally:
        if added:
            sys.path.remove(scripts_dir)


def _load_provider_modules() -> None:
    """Import the provider modules in their own scope.

    ``load_post_start_code`` also imports ``scripts.agent_runtime.adapters`` under the names ``agy``, ``claude``, ``codex``,
    ``cursor`` and ``muse``. Binding those names twice in one function is a mypy ``no-redef`` error. The imports stay
    literal, and each module still lands in ``sys.modules``.
    """
    with contextlib.suppress(Exception):
        from scripts.dispatcher.providers import agy, claude, codex, cursor, muse, opencode, stream_json  # noqa: F401


def load_post_start_code(bound_review: bool = False) -> None:
    """Import, as the worker starts, the modules its later steps import inside functions.

    Settlement and the other steps after the provider runs import part of their code on demand, from the
    primary checkout. A dispatcher change that merged while the worker ran gave them new modules next to
    the old ones loaded at start, and removal failed on the mix (#12634). Loading them now makes the whole
    run use the version it started with. The list holds the deferred imports of the modules a worker runs
    after start (this one, ``git``, the provider registry, the settlement chain, review attempts and
    their helpers) and the modules the dispatcher tests loaded after start. A new deferred import in
    those steps belongs here; ``bound_review`` adds what only a bound review attempt imports. Each group is skipped whole when any module in it fails to import, whatever
    the error, so the worker still starts; a step that then cannot load its code records
    ``git.CODE_UNAVAILABLE`` and the scheduled cleanup completes it from a fresh process.
    """
    with contextlib.suppress(Exception):
        from scripts.agent_runtime import (  # noqa: F401
            agy_hook_config,
            attempt_boundary,
            attempt_network,
            binary_resolve,
            codex_accounts,
            env_sanitize,
            failure_codes,
            jsonl,
            review_mcp,
            sources_read_only,
            telemetry,
            tool_calls,
        )
        from scripts.agent_runtime.adapters import (  # noqa: F401
            _output_schema,
            agy,
            base,
            claude,
            codex,
            codex_events,
            cursor,
            muse,
        )
    if bound_review:
        _load_bound_review_code()
    with contextlib.suppress(Exception):
        from scripts.common import fallback_substitutions, nofollow_walk, release_layout, safe_open  # noqa: F401

        attempt_hooks().bind_evidence_modules()
        from scripts.guardrails import delegate_ownership  # noqa: F401
        from scripts.lib import git_identity  # noqa: F401
        from scripts.opsec import git_push  # noqa: F401
        from scripts.session_supervisor import remote  # noqa: F401
        from scripts.utils import claude_version  # noqa: F401
    with contextlib.suppress(Exception):
        from scripts.review import (  # noqa: F401
            capacity,
            isolation,
            record_cf_verdict,
            render_contract,
            repair_round,
            review_contract,
            reviewer_resolver,
            role_resolution,
            subject_seat,
            verdict_parser,
        )

        attempt_hooks().bind_receipt_modules()
    with contextlib.suppress(Exception):
        from scripts.dispatcher import checks, host_admission, output_schema, review_attempt, scope  # noqa: F401
    _load_provider_modules()
    with contextlib.suppress(Exception):
        from scripts.fleet import (  # noqa: F401
            credit_lane,
            ignored_task_output,
            pr_owner_check,
            regenerable_output,
            reset_reserve,
            terminal_abandon,
        )
    with contextlib.suppress(Exception):
        from scripts.orchestration import (  # noqa: F401
            admission_shadow,
            dead_worker_state,
            dispatch_admission,
            pool_headroom,
            pr_ownership,
            preparation_evidence,
            reaper_lifecycle,
            slot_routing,
            task_record_causes,
            worker_leftovers,
            worktree_artifacts,
            worktree_claims,
            worktree_git,
            worktree_prep,
        )


# Seconds settlement waits for a provider's lingering processes to exit before it retains the tree.
SETTLE_PATIENCE = 10
# Extra fallback scans, 0.2 s apart, before an unreadable one keeps the worktree.
FALLBACK_SCAN_RETRIES = 10
# Ancestry walks of one candidate, restarted when an ancestor exits during the walk.
ANCESTRY_ATTEMPTS = 5
# Parents followed from one candidate; a deeper chain is unknown, never a stranger.
ANCESTRY_DEPTH = 64


def _cgroup_holds_other_active_task(record: dict, cgroup: str) -> bool:
    """Whether another still-active task has its supervisor or provider in ``cgroup``.

    A fallback child started from inside this scope stays in it. Stopping the
    scope would cancel that task. Membership that cannot be read counts too,
    and so does a task record or task directory that cannot be read, so the
    stop is skipped and the liveness check keeps the tree. A child that has
    its own scope is not a member here and does not block the stop.
    """
    from scripts.orchestration import worker_leftovers

    try:
        members = worker_leftovers.ProcFsReader().cgroup_procs(cgroup)
    except worker_leftovers.ScanUnknown:
        return True
    if not members:
        return False
    task_id = record.get("task_id")
    try:
        root = store.tasks_dir()
        if not root.is_dir():
            return True
        next(root.iterdir(), None)
        others = store.list_tasks(strict=True)
    except (OSError, ValueError):
        return True
    protected: set[int] = set()
    for other in others:
        if other.get("task_id") == task_id or other.get("status") not in store.ACTIVE:
            continue
        for key in ("pid", "provider_pgid"):
            value = other.get(key)
            if type(value) is int and value > 0:
                protected.add(value)
    return any(pid in protected for pid in members)


def _own_tree() -> set[int]:
    """Every process the supervisor started, whatever group or session it moved to (it adopts orphans)."""
    return {child.pid for child in psutil.Process().children(recursive=True)}


def _is_own_descendant(pid: int) -> bool:
    """Whether ``pid`` is in the supervisor's process tree now, which the marker alone does not prove.

    A client that inherited the task's marker, or a task this one dispatched, is not the task's descendant.
    ``stop_leftovers`` asks this of each candidate as it is listed and again after its pidfd is open, so a
    process that appears mid-stop is judged at that moment. An ancestor that exits during the walk has just
    reparented the candidate to the supervisor, so the walk starts again; ancestry that stays unresolved or
    unreadable raises ``ScanUnknown`` (the stop is then not ok) and is never read as "not a descendant".
    """
    from scripts.orchestration import worker_leftovers

    me = os.getpid()
    for _ in range(ANCESTRY_ATTEMPTS):
        current, settled = pid, True
        for _ in range(ANCESTRY_DEPTH):
            try:
                parent = psutil.Process(current).ppid()
            except psutil.NoSuchProcess:
                if current == pid:
                    return False  # the candidate itself has exited
                settled = False
                break
            except psutil.Error as exc:
                raise worker_leftovers.ScanUnknown(f"ancestry of {pid} unreadable: {exc}") from None
            if parent == me:
                return True
            if parent <= 1:
                return False
            current = parent
        if settled:
            raise worker_leftovers.ScanUnknown(f"ancestry of {pid} is deeper than {ANCESTRY_DEPTH} processes")
    raise worker_leftovers.ScanUnknown(f"ancestry of {pid} kept changing")


def _stop_fallback_tree(task_id: str, nonce: str):
    """Stop the processes a Popen-fallback supervisor started, once; a scan that cannot be read is not ok."""
    from scripts.orchestration import worker_leftovers

    reader = worker_leftovers.ProcFsReader()
    try:
        scope = worker_leftovers.worker_scope_at_exit(
            task_id=task_id, launch_mode="popen-fallback", launch_unit=None, run_nonce=nonce, reader=reader)
        stopped = worker_leftovers.stop_leftovers(scope, reader=reader, owned=_is_own_descendant)
        for pid in _own_tree():
            # An adopted descendant stays a zombie in its old process group until reaped, which the group
            # liveness check would read as a live provider.
            with contextlib.suppress(ChildProcessError, OSError):
                os.waitpid(pid, os.WNOHANG)
        return stopped
    except (OSError, ValueError, psutil.Error, worker_leftovers.ScanUnknown):
        return worker_leftovers.StopResult(ok=False, error="fallback boundary unreadable")


def _end_own_scope(record: dict):
    """End processes left in this finished task's own boundary; return the stop result, None when none ran.

    A scope stays alive while any member remains. Settlement used to read those
    members as a live provider and keep the worktree. A scope launch stops only
    the unit ``dispatch_isolation`` derives for this task and nonce: a recorded
    cgroup that is not that unit's scope is left alone, another active task's
    supervisor or provider in this cgroup is left alone, and the caller and its
    ancestors are not signalled. A Popen-fallback launch has no cgroup to stop, and
    ``killpg`` misses a descendant in another process group (GNU ``timeout``
    puts its child in one) or session, so the marked processes of the supervisor's
    own tree are stopped instead (#12520). A stop that cannot be proven
    leaves the processes for the liveness check, which keeps a scope's tree; the
    caller keeps a fallback tree from a failed stop. Only the supervisor sweeps a
    fallback launch (None otherwise): it alone knows the cgroup its jobs keep and the tree it adopted.
    """
    launch_mode = record.get("launch_mode")
    task_id, unit, nonce = record.get("task_id"), record.get("launch_unit"), record.get("run_nonce")
    if launch_mode == "popen-fallback":
        if not (isinstance(task_id, str) and task_id and isinstance(nonce, str) and nonce):
            return None
        if record.get("pid") != os.getpid():
            # Only the supervisor knows the cgroup its jobs keep, which a closed environment is judged by (#9514);
            # a later sweep from another process cannot bound the scan, so it leaves the task's processes alone.
            return None
        # A process that is mid-exec on a busy host reads as closed for an instant; only a scan that stays
        # unreadable keeps the tree.
        stopped = _stop_fallback_tree(task_id, nonce)
        for _ in range(FALLBACK_SCAN_RETRIES):
            if stopped.ok or stopped.survivors:
                break
            time.sleep(0.2)
            stopped = _stop_fallback_tree(task_id, nonce)
        return stopped
    if launch_mode != "scope":
        return None
    if not all(isinstance(value, str) and value for value in (task_id, unit, nonce)):
        return None
    from scripts.orchestration import dispatch_isolation, worker_leftovers

    if not dispatch_isolation.scope_unit_matches(unit, task_id=task_id, run_nonce=nonce):
        return None
    cgroup = dispatch_isolation.scope_cgroup(unit, uid=os.getuid())
    recorded = record.get("launch_cgroup")
    # A recorded boundary that is not this unit's scope is not ours to stop.
    if isinstance(recorded, str) and recorded and recorded != cgroup:
        return None
    if _cgroup_holds_other_active_task(record, cgroup):
        return None
    scope = worker_leftovers.WorkerScope(
        task_id=task_id, launch_mode=dispatch_isolation.LAUNCH_SCOPE, unit=unit, cgroup=cgroup, run_nonce=nonce)
    try:
        return worker_leftovers.stop_leftovers(scope, reader=worker_leftovers.ProcFsReader())
    except (OSError, ValueError, worker_leftovers.ScanUnknown):
        return None


def _reap_settled(record: dict, patience: float = 0, salvage: bool = False) -> None:
    """Record the task worktree's disposition and remove the task's caches; never changes its execution status.

    The worktree goes only once the provider's whole process tree is proven gone; liveness that
    cannot be proven either way keeps it. A finished scope launch first ends whatever that scope
    still holds, so a stray descendant cannot keep a published tree. With salvage
    (git.settle_worktree), that proof is taken again with the borrower check, before the salvage
    push and under the removal lock.
    """
    deadline = time.monotonic() + patience
    record.pop("worktree_disposition_detail", None)  # a retry replaces an earlier attempt's detail
    stopped = _end_own_scope(record)
    _clear_task_caches(record)
    if record.get("launch_mode") == "popen-fallback" and stopped is not None and not stopped.ok:
        # Only the process group's id is recorded for a fallback launch, so a descendant that left it is
        # invisible to the liveness check below. Name each survivor so a later retry still sees it.
        survivors = {str(proc.pid): identity for proc in stopped.survivors if (identity := _identity(proc.pid))}
        record["fallback_survivors"] = survivors
        record.update(worktree_disposition="retained",
                      worktree_disposition_reason="provider_processes_alive" if survivors else "provider_liveness_unknown")
        return
    while (alive := _provider_alive(record)) and time.monotonic() < deadline:
        time.sleep(0.05)
    if alive is not False:
        reason = "provider_processes_alive" if alive else "provider_liveness_unknown"
        record.update(worktree_disposition="retained", worktree_disposition_reason=reason)
        return

    def borrowed() -> bool:
        return (salvage and _provider_alive(record) is not False) or _borrowed(record)

    try:
        record.update(git.settle_worktree(record, borrowed=borrowed, salvage=salvage))
    except ImportError as exc:
        # Settlement's code could not be loaded: keep the tree and let the scheduled cleanup, a fresh process, finish.
        record.update(worktree_disposition="retained", worktree_disposition_reason=git.CODE_UNAVAILABLE,
                      worktree_disposition_detail=f"{type(exc).__name__}: {exc}")
    except Exception:
        record.update(worktree_disposition="error", worktree_disposition_reason="settlement_failed")


def _holds_task_caches(record: dict) -> bool:
    """Whether a finished task still has caches to remove, or a walk or removal failure to retry."""
    if record.get("status") in store.ACTIVE:
        return False
    try:
        found, failed = _task_caches(record["task_id"], remove=False)
    except (KeyError, TypeError, ValueError):
        return False  # no valid task identity, so no output directories of its own
    except OSError:
        return True
    return bool(found or failed or "task_cache_residue" in record)


def _unsettled(record: dict) -> bool:
    return record.get("status") not in store.ACTIVE and (
        "worktree_disposition" not in record or record.get("worktree_disposition_reason") in RETRY_REASONS)


def settle_left_worktrees(salvage: bool = False) -> None:
    """Retry finished tasks' worktrees and remove their caches during scheduled cleanup, including crash recovery.

    Admission and worker exit do not call this store-wide sweep. Each worker settles only
    its own task. The hourly hygiene run passes salvage for the trees settlement keeps.
    """
    records = []
    for record in store.list_tasks():
        if record.get("schema_version") == 2:
            with contextlib.suppress(OSError, ValueError, KeyError, TypeError):
                record = _observe(record)
            records.append(record)
    for record in records:
        reap = _unsettled(record) and Path(record.get("worktree_path") or "").is_dir()
        if not reap and not _holds_task_caches(record):
            continue
        try:
            path = store.record_path(record["task_id"])
        except (KeyError, TypeError, ValueError):
            continue  # a damaged identity never ends the sweep for the records after it
        # wait() takes this lock before it reports a terminal task, so it never returns mid-removal.
        with contextlib.suppress(OSError, ValueError, KeyError), store.task_state_lock(path):
            current = json.loads(path.read_text())
            if not reap or not _unsettled(current):
                # A task settled without a worktree, or by an earlier pass, still sheds its caches.
                if _clear_task_caches(current):
                    store.replace(current, path)
            else:
                _reap_settled(current, salvage=salvage)
                store.replace(current, path)


def _end_lingering(child: subprocess.Popen, spec: TaskSpec) -> None:
    """End a provider that outlived its terminal result, keeping what its launcher still has to write.

    The read-only AGY launcher records its boundary receipt once AGY exits, so only AGY's own tree is
    killed and the launcher is given time to finish; anything still alive after that is killed whole.
    """
    if spec.agent == "agy" and spec.mode == "read-only":
        with contextlib.suppress(psutil.Error):
            for process in psutil.Process(child.pid).children():
                process.kill()
        with contextlib.suppress(subprocess.TimeoutExpired):
            child.wait(timeout=TERMINAL_EXIT_GRACE_S)
    if child.returncode is None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(child.pid, signal.SIGKILL)
        child.wait()


def _verdict_failure(record: dict, text: str | None) -> str | None:
    """Why a successful review must fail its requested verdict gate (``--require-review-verdict``), or None."""
    if record.get("schema_version") != 2 or record.get("require_review_verdict") is not True:
        return None
    try:
        from scripts.review.verdict_parser import recognized_verdicts

        verdicts = set(recognized_verdicts(text))
    except Exception:
        return "review_gate_error"
    if not verdicts:
        return None if _item_judgments_verdict(record, text) else "review_missing_verdict_line"
    return "review_ambiguous_verdict" if len(verdicts) > 1 else None


def _item_judgments_verdict(record: dict, text: str | None) -> str | None:
    """The verdict a valid ``ukrainian-item-judgments`` block carries, or None.

    The Ukrainian contract with an item denominator has the reviewer return only that
    block (``review-loop/references/ukrainian.md``). The recorder's own parser judges it
    against the brief's frozen packet, as the recorder does.
    """
    if record.get("review_profile") != "ukrainian" or not text:
        return None
    from scripts.review.review_contract import ContractError, item_judgments_verdict, load_frozen_item_packet

    try:
        packet = load_frozen_item_packet(record)
        return item_judgments_verdict(packet, text) if packet is not None else None
    except ContractError:
        return None


def _correction_stdin(prior: str) -> bytes:
    """One format repair. The verdict, findings, and their meaning stay as they were."""
    return (
        "The previous reply is not a recordable review.\n"
        "Return only one JSON object matching schemas/code-review-findings.v1.schema.json.\n"
        "Keep the same verdict, the same findings, and the same meaning.\n"
        "Include confidence and verbatim where the schema requires them.\n\n"
        "Previous reply:\n"
        f"{prior}\n"
    ).encode()


def _format_correction(record: dict, schema: dict | None, text: str | None, launches: int) -> tuple[bytes, dict] | None:
    """A second launch when a code review cannot bind a schema and the reply cannot be a receipt.

    Schema-capable providers fail closed on their own schema check. An ambiguous
    reply is not rewritten into one verdict. One launch is the limit.
    """
    if schema is not None or launches >= 1 or record.get("require_review_verdict") is not True:
        return None
    if not text or not text.strip():
        return None
    from scripts.review.review_contract import (
        ContractError,
        canonical_receipt_payload,
        decision_lock,
        schema_path,
    )

    if schema_path(profile=record.get("review_profile"), task=record) is None:
        return None
    try:
        canonical_receipt_payload(text)
    except ContractError:
        pass
    else:
        return None
    lock = decision_lock(text)
    # A correction is accepted only when this reply already states one decision.
    # With nothing to lock, a second reply would be a new verdict.
    if lock["ambiguous"] or (lock.get("payload") is None and len(lock.get("verdicts") or []) != 1):
        return None
    return _correction_stdin(text), lock


def _receipt_failure(record: dict, text: str | None) -> str | None:
    """A code review settles only when the reply is a canonical receipt.

    A verdict line alone is not a receipt. Ukrainian reviews do not use this
    object, so they keep the verdict gate.
    """
    if record.get("schema_version") != 2 or record.get("require_review_verdict") is not True:
        return None
    from scripts.review.review_contract import ContractError, canonical_receipt_payload, schema_path

    if schema_path(profile=record.get("review_profile"), task=record) is None:
        return None
    try:
        canonical_receipt_payload(text or "")
    except ContractError:
        return _verdict_failure(record, text) or "review_gate_error"
    return None


def _corrected_reply_refusal(lock: dict, text: str | None) -> str | None:
    """Refuse a correction that is still not a receipt, or that changes the locked decision."""
    from scripts.review.review_contract import ContractError, canonical_receipt_payload, same_decision

    try:
        payload = canonical_receipt_payload(text or "")
    except ContractError:
        return _verdict_failure({"schema_version": 2, "require_review_verdict": True}, text) or "review_gate_error"
    if not same_decision(lock, payload):
        return "review_ambiguous_verdict"
    return None


def _adopt_orphans() -> bool:
    """Make this supervisor the parent of every orphaned descendant (``PR_SET_CHILD_SUBREAPER``).

    A Popen-fallback launch has no cgroup. A double-forked descendant would otherwise reparent to init or the
    user manager, out of the supervisor's process tree, and settlement could not tell it from an unrelated process.
    False when the kernel or a confinement policy refuses.
    """
    try:
        return ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0
    except (AttributeError, OSError):
        return False


def supervise(path: Path, options: dict | None = None, hard_timeout: float | None = None) -> None:
    os.umask(0o077)
    record = json.loads(path.read_text())
    load_post_start_code(bool(record.get("review_attempt")))
    if record.get("require_review_verdict") is True:
        # The code this supervisor loaded; settlement records it again (#12399).
        record["dispatcher_code_start"] = _dispatcher_code()
    spec = _spec(record, options or {})
    options = spec.options
    hard_timeout, silence_timeout, initial_response_timeout = deadlines({
        **options, **{key: record[key] for key in ("hard_timeout", "silence_timeout", "initial_response_timeout")
                     if key in record},
        **({"hard_timeout": hard_timeout} if hard_timeout is not None else {}),
    })
    child, status, returncode, error, usage, text = None, "crashed", None, None, None, None
    slots = None
    resolved_model = sources_calls = source = None
    started = time.monotonic()
    cancel_requested = interruptible = False

    def cancelled(_signum, _frame):
        # A handler's exception lands at an arbitrary bytecode, where Python can drop it (a weakref
        # callback) or a caller can convert it (#11994). Record the request; checkpoint() raises it,
        # settlement honours it, and only a wait marked interruptible, built to unwind there, is
        # stopped in place.
        nonlocal cancel_requested, interruptible
        cancel_requested = True
        if interruptible:
            interruptible = False  # one raise per run: a later signal cannot interrupt cleanup
            raise _Cancelled()

    def checkpoint():
        if cancel_requested:
            raise _Cancelled()

    def terminate():
        # Only an unreaped leader still pins its group id; a reaped one's id may name another group.
        if child and child.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(child.pid, signal.SIGKILL)
            child.wait()

    previous_term = signal.signal(signal.SIGTERM, cancelled)
    previous_int = signal.signal(signal.SIGINT, cancelled)
    stdout_path = path.parent / "logs" / f"{spec.task_id}.stdout.log"
    stderr_path = path.parent / "logs" / f"{spec.task_id}.stderr.log"
    try:
        signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM, signal.SIGINT})
        if record.get("launch_mode") == "popen-fallback" and not _adopt_orphans():
            # Without it a double-forked descendant would escape settlement's sweep unseen.
            status, error = "failed", "fallback_adoption_unavailable: PR_SET_CHILD_SUBREAPER was refused"
            return
        try:
            headroom.check_plan(spec.agent, spec.model, record, review=admission.review_typed(record))
            headroom.check_runtime(spec.agent, spec.model, codex_account=record.get("codex_account"))
        except ValueError as exc:
            status, error = "failed", str(exc)
            return
        except headroom.RateLimitedError as exc:
            status, error = "rate_limited", str(exc)
            return
        if record.get("review_attempt"):
            # A bound formal attempt runs only inside the agent runtime's attempt boundary, with the rendered
            # prompt's exact bytes: no dispatch context, no task-store grant, no ordinary launch (#12114).
            from scripts.dispatcher import review_attempt

            prompt = spec.prompt_file.read_bytes()
            record.update(status="running", runtime_input_sha256=hashlib.sha256(prompt).hexdigest())
            store.replace(record, path, require_existing=True)
            interruptible = True  # cancel unwinds the runtime, which kills the seat and tears the boundary down
            try:
                checkpoint()
                outcome = review_attempt.run(spec, record, prompt.decode("utf-8"),
                                             (hard_timeout, silence_timeout, initial_response_timeout))
            finally:
                interruptible = False
            status, error, text, sources_calls = outcome.status, outcome.error, outcome.text, outcome.sources_calls
            record.update(outcome.identity)
            if outcome.trace:
                # The runtime keeps the seat's stream to itself; its redacted tool-call trace takes the stream's
                # place in the task's private stdout log.
                with stdout_path.open("w", encoding="utf-8") as trace:
                    trace.writelines(json.dumps(call, ensure_ascii=False) + "\n" for call in outcome.trace)
            if status == "done" and (refusal := _verdict_failure(record, text)):
                status, error = "failed", refusal
            return
        schema = None
        if options.get("output_schema_path") is not None:
            from scripts.dispatcher.output_schema import load

            try:
                schema = load(options)
            except (OSError, ValueError):
                status, error = "failed", "output schema binding invalid"
                return
        provider = providers.load(spec.agent)
        invocation = runtime_context.build(spec, child_env(spec))
        record["runtime_input_sha256"] = hashlib.sha256(invocation.stdin or b"").hexdigest()
        pending_conversation = None
        pending_correction = None
        correction_launches = 0
        locked = None
        continuations = 0
        parsed = None
        try:
            invocation = admission.claude_launch(spec, invocation)
            if spec.agent == "claude" and spec.claude_account not in (None, "a"):
                from scripts.agent_runtime.attempt_boundary import claude_account_auth_receipt

                # Value-free: label, source and the verified method (``api_key_helper`` bills that key).
                record["claude_account_auth"] = claude_account_auth_receipt(
                    spec.claude_account, source=record.get("claude_account_source")
                )
            # Checked again with the launch's own environment: a managed policy may appear after dispatch.
            if spec.mode == "read-only" and (refusal := providers.read_only_refusal(spec.agent, invocation.env)):
                raise ValueError(refusal)
        except ValueError as exc:
            status, error = "failed", str(exc)
            return
        if spec.agent == "codex" and spec.mode == "read-only":
            try:
                create_dispatch_lease(spec.task_id, spec.worktree)
            except (OSError, ValueError) as exc:
                status, error = "failed", f"read_only_scratch_unavailable: {exc}"
                return
        # The slot queue can wait for an hour and discards its ticket on any exception, so cancel stops it in place.
        interruptible = True
        try:
            checkpoint()  # after the region opens: a request from before it cannot wait out the queue
            slots, slots_record = admission.hold_review_test_slots(
                agent=spec.agent, mode=spec.mode, review_typed=admission.review_typed(record),
                sealed_attempt=bool(record.get("review_attempt")), task_id=spec.task_id,
            )
        finally:
            interruptible = False
        if slots_record is not None:
            record["review_test_slots"] = slots_record
        while True:
            correcting = pending_correction is not None
            if pending_conversation:
                invocation = runtime_context.build(spec, child_env(spec), conversation=pending_conversation)
            elif correcting:
                invocation = runtime_context.build(spec, child_env(spec), launch_prompt=pending_correction)
                pending_correction = None
            # The first launch keeps the timeout the caller passed. Only a continuation
            # spends what remains of that same deadline, and a spent deadline does not
            # become the unlimited timeout a zero means.
            launch_hard = hard_timeout
            if (pending_conversation or correcting) and hard_timeout > 0:
                launch_hard = max(0.0, hard_timeout - (time.monotonic() - started))
                if launch_hard <= 0 and parsed is not None:
                    if pending_conversation:
                        parsed = _agy_unfinished(parsed)
                    text = parsed.text
                    break
            with tempfile.TemporaryFile(dir=ensure_scratch_root()) as stdin, stdout_path.open("wb") as out, stderr_path.open(
                "wb" if pending_conversation else "ab"
            ) as err:
                stdin.write(invocation.stdin or b"")
                stdin.seek(0)
                output_sizes = out.tell(), err.tell()
                checkpoint()  # the last one before the provider starts: a cancelled run launches nothing
                child = subprocess.Popen(
                    invocation.argv,
                    stdin=stdin,
                    stdout=out,
                    stderr=err,
                    cwd=spec.worktree,
                    # The CLI's governed test runs join this hold through its marker (#11230).
                    env={**invocation.env, **slots.environment()} if slots else invocation.env,
                    start_new_session=True,
                )
                record.update(status="running", provider_pgid=child.pid)
                store.replace(record, path, require_existing=True)
                terminal_observer = getattr(provider, "terminal_result_observer", None)
                source = getattr(provider, "MODEL_SOURCE", None)
                observe_model = provider.model_observer(stdout_path) if source else None

                def watch(observe_model=observe_model, source=source):
                    # A running author's commits are reviewable only once its record attests the model (#12014).
                    nonlocal resolved_model
                    checkpoint()
                    if observe_model is None or source is None:
                        return
                    resolved_model = observe_model()
                    fields = _stream_attestation(source, resolved_model)
                    if any(record.get(key) != value for key, value in fields.items()):
                        record.update(fields)
                        store.replace(record, path, require_existing=True)

                lingered = communicate(child, invocation, stdout_path, stderr_path, launch_hard, silence_timeout,
                                       initial_response_timeout, liveness_paths(spec, invocation), output_sizes,
                                       terminal_observer(stdout_path) if terminal_observer else None, watch)
            if lingered:
                _end_lingering(child, spec)
            returncode = child.returncode
            # A provider ended after its terminal result is judged by that result, not by how it was ended.
            exit_code = 0 if lingered else returncode
            final = invocation.final_file
            final_text = final.read_text(errors="replace") if final and final.exists() else None
            stdout = stdout_path.read_text(errors="replace")
            parse_options = (
                {"output_schema": schema} if spec.agent in {"agy", "claude"} and schema is not None else {}
            )
            parsed = provider.parse(stdout, stderr_path.read_text(errors="replace"), exit_code, final_text, **parse_options)
            text, usage, sources_calls = parsed.text, parsed.usage, parsed.sources_mcp_call_count
            # Once parsed, the whole stream decides the model, whatever settlement follows (not the running value).
            resolved_model = parsed.resolved_model
            conversation, parsed = _agy_follow_up(
                spec, record, parsed, started, hard_timeout, continuations, checkpoint)
            if conversation is not None:
                pending_conversation = conversation
                continuations += 1
                continue
            text = parsed.text
            if parsed.error is None and (
                correction := _format_correction(record, schema, text, correction_launches)
            ):
                pending_correction, locked = correction
                correction_launches += 1
                continue
            break
        store.begin_settlement(record)
        if spec.agent == "agy" and spec.mode == "read-only":
            # Only the boundary's receipt, written outside the sandbox, proves the run read-only and
            # supplies its Sources count (C-3027); without a verified one the run fails.
            boundary, sources_calls, refusal = agy_sandbox.verify(spec.final_file, spec.task_id, record)
            record["read_only_boundary"] = boundary
            if refusal:
                status, error = "failed", refusal
                return
        if parsed.rate_limited and exit_code >= 0:
            # Before the schema check, which would record the same terminal failure as invalid output.
            status, error = "rate_limited", parsed.error
            return
        if schema is not None and spec.agent != "agy" and exit_code == 0 and not parsed.error:
            from scripts.agent_runtime.adapters._output_schema import json_value, structured_result

            result = structured_result(json_value(text), schema, returncode=exit_code, terminal_ok=True)
            if not result.ok:
                error = f"{result.failure_code}: {result.stderr_excerpt}"
                status = "failed"
                return
            text = result.response
        status = "done" if exit_code == 0 and not parsed.error and text and text.strip() else "failed"
        if exit_code < 0:
            status = "crashed"
        if status != "done":
            error = parsed.error or (
                "provider exited unsuccessfully" if exit_code else "provider returned no successful final response"
            )
        if status == "done" and source == "agy-stream-json":
            from scripts.dispatcher.providers.agy import identity_failure

            if refusal := identity_failure(spec.model, resolved_model):
                status, error = "failed", refusal
        if status == "done" and spec.agent == "claude":
            # An advised run attests its executor from its own result; another model never settles done (#12094).
            from scripts.dispatcher.providers.claude import MODEL_USAGE_SOURCE, executor_failure

            if (attested := executor_failure(spec, stdout)) is not None:
                record.update(_stream_attestation(MODEL_USAGE_SOURCE, attested[0]))
                if attested[1]:
                    status, error = "failed", attested[1]
        if status == "done" and locked is not None and (refusal := _corrected_reply_refusal(locked, text)):
            status, error = "failed", refusal
        if status == "done" and (refusal := _receipt_failure(record, text)):
            status, error = "failed", refusal
        if status == "done" and (refusal := _verdict_failure(record, text)):
            status, error = "failed", refusal
    except _Cancelled:
        status, error = "cancelled", "cancelled by client"
    except DeadlineExpired as exc:
        status, error = "timeout", exc.diagnostic
        record.update(kill_reason=exc.kind, stderr_excerpt=exc.diagnostic)
    except subprocess.TimeoutExpired:
        status, error = "timeout", "process deadline exceeded"
    except store.TaskRecordError as exc:
        status, error = "crashed", exc.code
    except Exception:
        status, error = "crashed", "supervisor or provider processing failed"
    finally:
        if cancel_requested:
            # A cancel requested before settlement decides the run, whatever exit the work took after it.
            status, error = "cancelled", "cancelled by client"
        try:
            if child and (child.returncode is None or status in {"cancelled", "timeout", "crashed"}):
                terminate()
                returncode = child.returncode
            if not record.get("settling_at"):
                try:
                    store.begin_settlement(record)
                except store.TaskRecordError as exc:
                    status, error = "crashed", exc.code
            # A killed launcher leaves its scratch and token copy; residue is recorded, never raised.
            if spec.agent == "agy" and spec.mode == "read-only":
                # A bound attempt already counted its Sources bodies and replaced the stream with
                # that trace. The stream merger only understands step updates, so running it here
                # would replace the attempt's counts with zeros.
                if not record.get("review_attempt"):
                    # The launcher exports saved tool bodies before it deletes the scratch. Fold them
                    # into the retained stream first; discard then removes whatever scratch remains.
                    try:
                        retained, missing = agy_sandbox.apply_tool_results(stdout_path, spec.final_file, spec.task_id)
                        record["sources_bodies_retained"] = retained
                        record["sources_bodies_missing"] = missing
                    except (OSError, ValueError):
                        record["sources_bodies_missing"] = None
                if residue := agy_sandbox.discard(spec.task_id):
                    record["read_only_boundary_cleanup"] = residue
            _discard_read_only_scratch(record)
            if slots is not None:
                # The hold is the supervisor's: a killed supervisor ends it, and the governed runs in flight
                # keep their slots shared until they exit (test_slots).
                slots.release()
            if text is not None:
                spec.final_file.write_text(text)
                spec.final_file.chmod(0o600)
                if record.get("advisory_role") is not None:
                    _seal_advisory_result(record, spec.final_file)
            record.update(
                status=status,
                returncode=returncode,
                error=error,
                usage=usage,
                finished_at=store.now(),
                duration_s=round(time.monotonic() - started, 3),
                result_sha256=store.digest(spec.final_file.read_bytes()) if spec.final_file.exists() else None,
            )
            if sources_calls is not None:
                record["sources_mcp_call_count"] = sources_calls
            if record.get("require_review_verdict") is True:
                record["dispatcher_code"] = _dispatcher_code()
            record.update(git.snapshot_delivery(spec, record))
            if error and error.startswith("TASK_RECORD_"):
                record.update(worktree_disposition="retained", worktree_disposition_reason="task_record_damaged")
            else:
                _enforce_delivery(record)
            if children := _running_children(record):
                # A run that ends while a task it dispatched still runs left that result unconsumed (#12156).
                record["orphaned_child_tasks"] = children
            if source:
                record.update(_stream_attestation(source, resolved_model))
            record["provider_pgid"] = child.pid if child else None
            # The removal chokepoint releases a tree only to a finished owner record, so publish it, then
            # settle; wait() reads a terminal record under this lock and never sees the tree mid-removal.
            with store.task_state_lock(path):
                # A cancel arriving during cleanup still decides the run until publication, never after: a
                # published terminal record is never rewritten, and cancel() returns one unchanged. Signals
                # held across the check and the write make publication that exact cutoff (the mask is this
                # thread's; the supervisor runs no other).
                mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM, signal.SIGINT})
                try:
                    if cancel_requested and record["status"] != "cancelled":
                        record.pop("no_deliverable_reason", None)
                        record.update(status="cancelled", error="cancelled by client")
                    if (children := record.get("orphaned_child_tasks")) and record["status"] != "done":
                        record["error"] = f"orphaned_child_tasks: {', '.join(children)}; {record['error']}"
                    try:
                        store.replace(record, path, require_existing=True)
                    except store.TaskRecordError:
                        store.publish_failed_record(record, path)
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, mask)
                if record.get("worktree_disposition_reason") != "task_record_damaged":
                    _reap_settled(record, patience=SETTLE_PATIENCE)
                try:
                    store.replace(record, path, require_existing=True)
                except store.TaskRecordError:
                    store.publish_failed_record(record, path)
        finally:
            signal.signal(signal.SIGTERM, previous_term)
            signal.signal(signal.SIGINT, previous_int)


def wait(task_id: str, nonce: str | None = None, timeout: float = 0, poll_interval: float = 1) -> tuple[dict, int]:
    deadline = time.monotonic() + timeout if timeout else None
    while True:
        record = _observe(store.read(task_id, nonce))
        if record["status"] not in store.ACTIVE:
            if record.get("schema_version") == 2:
                # Crash recovery settles a terminal task under this lock; report it only after that ends.
                with store.task_state_lock(store.record_path(task_id)):
                    record = store.read(task_id, nonce)
            return record, 0 if record["status"] == "done" else 1
        remaining = deadline - time.monotonic() if deadline else None
        if remaining is not None and remaining <= 0:
            return record, 124
        time.sleep(min(poll_interval, remaining) if remaining is not None else poll_interval)


def cancel(task_id: str, nonce: str | None = None) -> dict:
    record = _observe(store.read(task_id, nonce))
    if record.get("schema_version") != 2:
        raise ValueError("legacy task cancellation belongs to its original supervisor")
    if record["status"] in store.ACTIVE:
        if not record.get("pid") or not record.get("process_start"):
            raise ValueError("supervisor identity is unavailable; cancellation refused")
        try:
            pidfd = os.pidfd_open(record["pid"])
            try:
                if _identity(record["pid"]) != record["process_start"]:
                    raise ValueError("supervisor identity changed; cancellation refused")
                signal.pidfd_send_signal(pidfd, signal.SIGTERM)
            finally:
                os.close(pidfd)
        except ProcessLookupError:
            return _observe(record)
        return wait(task_id, nonce, timeout=10, poll_interval=0.05)[0]
    return record


if __name__ == "__main__":
    # Run as -m, this module is __main__; a later `import scripts.dispatcher.worker` (the removal chokepoint's
    # liveness proof) must get this running copy, not a second one loaded from a checkout that has moved since.
    sys.modules.setdefault("scripts.dispatcher.worker", sys.modules[__name__])
    settings = json.load(sys.stdin)
    supervise(Path(sys.argv[1]), **settings)
