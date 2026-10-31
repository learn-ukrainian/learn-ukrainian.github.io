"""Detached supervision, client waits and process-group cancellation."""

import contextlib
import hashlib
import json
import os
import re
import signal
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
        store.create(record, prompt)
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
        never_ran = record.get("returncode_reason") in {"spawn_process_missing", "dispatch_died_after_admission"}
        return False if never_ran and record.get("pid") is None and record.get("process_start") is None else None
    if record["provider_pgid"] is None:
        return False
    try:
        os.killpg(record["provider_pgid"], 0)
    except ProcessLookupError:
        return False
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
# clears; every later dispatch and every settlement settles these again, and still removes
# only with the proof. A tree that is still dirty is kept again, so only a changed tree is removed.
# The hourly hygiene run's salvage reasons retry the same way.
RETRY_REASONS = frozenset({"dirty", "provider_processes_alive", "provider_liveness_unknown", "borrowed_by_live_task",
                           "unpublished", "remote_mismatch", "unknown", "removal_refused",
                           "worktree_remove_failed", "settlement_failed",
                           "salvage_failed", "salvage_unverified", "large_ignored_output",
                           "nested_repository_unpushed", "github_deferred"})
# Seconds settlement waits for a provider's lingering processes to exit before it retains the tree.
SETTLE_PATIENCE = 10


def _reap_settled(record: dict, patience: float = 0, salvage: bool = False) -> None:
    """Record the task worktree's disposition; never changes the task's execution status.

    The worktree goes only once the provider's whole process tree is proven gone; liveness that
    cannot be proven either way keeps it. With salvage (git.settle_worktree), that proof is taken
    again with the borrower check, before the salvage push and under the removal lock.
    """
    deadline = time.monotonic() + patience
    record.pop("worktree_disposition_detail", None)  # a retry replaces an earlier attempt's detail
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
    except Exception:
        record.update(worktree_disposition="error", worktree_disposition_reason="settlement_failed")


def _unsettled(record: dict) -> bool:
    return record.get("status") not in store.ACTIVE and (
        "worktree_disposition" not in record or record.get("worktree_disposition_reason") in RETRY_REASONS)


def settle_left_worktrees(salvage: bool = False) -> None:
    """Settle worktrees of finished tasks whose supervisor ended before settling them.

    The hourly hygiene run passes salvage (git.settle_worktree) for the trees settlement keeps.
    """
    records = []
    for record in store.list_tasks():
        if record.get("schema_version") == 2:
            with contextlib.suppress(OSError, ValueError, KeyError, TypeError):
                record = _observe(record)
            records.append(record)
    for record in records:
        if not _unsettled(record) or not Path(record.get("worktree_path") or "").is_dir():
            continue
        path = store.record_path(record["task_id"])
        # wait() takes this lock before it reports a terminal task, so it never returns mid-removal.
        with contextlib.suppress(OSError, ValueError, KeyError), store.task_state_lock(path):
            current = json.loads(path.read_text())
            if _unsettled(current):
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
        return "review_missing_verdict_line"
    return "review_ambiguous_verdict" if len(verdicts) > 1 else None


def supervise(path: Path, options: dict | None = None, hard_timeout: float | None = None) -> None:
    os.umask(0o077)
    record = json.loads(path.read_text())
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
        try:
            headroom.check_plan(spec.agent, spec.model, record, review=admission.review_typed(record))
            headroom.check_runtime(spec.agent, spec.model)
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
            if pending_conversation:
                from scripts.dispatcher.providers.agy import continuation

                invocation = continuation(runtime_context.build(spec, child_env(spec)), pending_conversation)
            # The first launch keeps the timeout the caller passed. Only a continuation
            # spends what remains of that same deadline, and a spent deadline does not
            # become the unlimited timeout a zero means.
            launch_hard = hard_timeout
            if pending_conversation and hard_timeout > 0:
                launch_hard = max(0.0, hard_timeout - (time.monotonic() - started))
                if launch_hard <= 0 and parsed is not None:
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
            parse_options = {"output_schema": schema} if spec.agent == "agy" else {}
            parsed = provider.parse(stdout, stderr_path.read_text(errors="replace"), exit_code, final_text, **parse_options)
            text, usage, sources_calls = parsed.text, parsed.usage, parsed.sources_mcp_call_count
            # Once parsed, the whole stream decides the model, whatever settlement follows (not the running value).
            resolved_model = parsed.resolved_model
            conversation, parsed = _agy_follow_up(
                spec, record, parsed, started, hard_timeout, continuations, checkpoint)
            if conversation is None:
                text = parsed.text
                break
            pending_conversation = conversation
            continuations += 1
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
        if schema is not None and spec.agent != "agy":
            from scripts.agent_runtime.adapters._output_schema import json_value, structured_result

            result = structured_result(json_value(text), schema, returncode=exit_code, terminal_ok=not parsed.error)
            text = result.response
            if not result.ok:
                error = f"{result.failure_code}: {result.stderr_excerpt}"
                status = "failed"
                return
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
            if spec.agent == "agy" and spec.mode == "read-only" and (residue := agy_sandbox.discard(spec.task_id)):
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
            # Settling a task first retries the trees earlier settlements kept for a cause that may have
            # cleared, under the same proofs. It runs before this task's record turns terminal, holding no
            # record lock, so the supervisor exits as soon as its own tree is settled.
            with contextlib.suppress(Exception):
                settle_left_worktrees()
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
