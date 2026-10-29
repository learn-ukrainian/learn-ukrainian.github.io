"""Detached supervision, client waits and process-group cancellation."""

import contextlib
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from scripts.agent_runtime import bounded_advisory
from scripts.agent_runtime.read_only_tmp import create_dispatch_lease, discard_dispatch_lease
from scripts.common.repo_root import project_interpreter
from scripts.common.scratch import ensure_scratch_root
from scripts.common.task_scratch import TaskScratchError
from scripts.dispatcher import admission, agy_sandbox, git, headroom, providers, runtime_context, store
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.types import TaskSpec
from scripts.dispatcher.watchdog import DeadlineExpired, communicate, deadlines, liveness_paths
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


def start(spec: TaskSpec, record: dict, prompt: bytes, hard_timeout: float) -> None:
    from scripts.orchestration.dispatch_admission import new_admission_hold

    if spec.agent == "cursor":
        record.update(resolved_model="unknown", resolved_model_known=False, resolved_model_source="pending")
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
    )


def _outside_cause(paths, owned) -> str | None:
    from scripts.guardrails.delegate_ownership import path_is_owned, sanitize_for_display
    from scripts.secret_redactor import redact_text

    outside = sorted(path for path in set(paths) if path and not path_is_owned(path, owned))
    if not outside:
        return None
    cause = "outside_owned_paths: " + ", ".join(sanitize_for_display(redact_text(path)) for path in outside)
    return cause if len(cause) <= 1024 else cause[:1009] + "... (truncated)"


def _verification_cause(exc: Exception) -> str:
    """Name what stopped the ownership check: the failing Git step, or the check's own refusal."""
    if isinstance(exc, subprocess.TimeoutExpired):
        detail = f"git {exc.cmd[1]} timed out"
    elif isinstance(exc, subprocess.CalledProcessError):
        detail = f"git {exc.cmd[1]} failed"
    elif isinstance(exc, ValueError):
        detail = str(exc)
    elif isinstance(exc, KeyError):
        detail = f"record field {exc} missing"
    else:
        detail = type(exc).__name__
    return f"owned_paths_verification_failed: {detail}"[:200]


def _enforce_delivery(record: dict) -> None:
    if record["mode"] == "read-only" or record["status"] != "done":
        return
    cause = None
    owned = record.get("owned_paths")
    # With no commits ahead there is nothing to verify, and the remote branch may never have existed.
    if owned and (record.get("commits_ahead") or 0) > 0:
        try:
            with git.ownership_git(record) as run:
                base_sha = run("rev-parse", "--verify", "refs/heads/base^{commit}")
                merge_base = run("merge-base", record["head_sha"], base_sha)
                start_sha = record.get("worktree_start_sha", record["worktree_base_sha"])
                revision_range = (record["head_sha"], "--not", merge_base, start_sha)
                if (record["commits_ahead"] or 0) > 0 and not run("rev-list", "--max-count=1", *revision_range):
                    raise ValueError("empty ownership range with recorded commits ahead")
                version = tuple(int(part) for part in run("version").split()[2].split(".")[:2])
                remerge = version >= (2, 36)
                # Remerge diffs isolate edits made during a merge from clean upstream changes.
                # Older Git and octopus merges cannot prove the absence of resolution edits.
                paths = run(
                    "log", "--format=", "--name-only", "-z", "-r", "--no-renames", "--root",
                    "--remerge-diff" if remerge else "--cc", *revision_range, strip=False,
                ).split("\0")
                if run("rev-list", "--min-parents=3" if remerge else "--min-parents=2", *revision_range):
                    raise ValueError("merge resolution paths cannot be verified")
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
        cause = _outside_cause(merged["paths"], owned) if owned else None
        record["delivery_pr"] = f"{merged['repo']}#{merged['number']}"
    if cause:
        record.update(status="no_deliverable", error=cause, no_deliverable_reason=cause)


# Refusals that a merged pull request answers: the local branch could not show the delivery.
MERGE_RESCUABLE = frozenset({"owned_paths_verification_failed", "no_commits_or_unknown", "work_not_pushed_or_unknown"})


def _cgroup(pid: int) -> str | None:
    with contextlib.suppress(OSError):
        return next((line[3:] for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines()
                     if line.startswith("0::")), None)
    return None


def _provider_alive(record: dict) -> bool | None:
    """Whether the provider's process tree still runs, from the identity recorded for it; None when unknown."""
    if record.get("launch_mode") == "scope":
        # The scope holds every descendant, including ones that left the provider's process group.
        if not (cgroup := record.get("launch_cgroup")):
            return None
        try:
            procs = Path("/sys/fs/cgroup" + cgroup, "cgroup.procs").read_text().split()
        except FileNotFoundError:
            # The kernel refuses to remove a cgroup that still holds processes, so a gone scope is empty.
            return False if Path("/sys/fs/cgroup/cgroup.controllers").exists() else None
        except OSError:
            return None
        return any(int(pid) != os.getpid() for pid in procs)
    if "provider_pgid" not in record:
        return None  # the supervisor ended before recording whether it started a provider
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


# Dispositions that can change once other processes end, the tree is committed or reverted, the work is
# published (pushed or merged after the task ended), or a transient Git, lock, claim or removal failure
# clears; the next dispatch's crash recovery settles these again, in a fresh process, and still removes
# only with the proof. A tree that is still dirty is kept again, so only a changed tree is removed.
RETRY_REASONS = frozenset({"dirty", "provider_processes_alive", "provider_liveness_unknown", "borrowed_by_live_task",
                           "unpublished", "remote_mismatch", "unknown", "removal_refused",
                           "worktree_remove_failed", "settlement_failed"})
# Seconds settlement waits for a provider's lingering processes to exit before it retains the tree.
SETTLE_PATIENCE = 10


def _reap_settled(record: dict, patience: float = 0) -> None:
    """Record the task worktree's disposition; never changes the task's execution status.

    The worktree goes only once the provider's whole process tree is proven gone; liveness that
    cannot be proven either way keeps it.
    """
    deadline = time.monotonic() + patience
    record.pop("worktree_disposition_detail", None)  # a retry replaces an earlier attempt's detail
    while (alive := _provider_alive(record)) and time.monotonic() < deadline:
        time.sleep(0.05)
    if alive is not False:
        reason = "provider_processes_alive" if alive else "provider_liveness_unknown"
        record.update(worktree_disposition="retained", worktree_disposition_reason=reason)
        return
    try:
        record.update(git.settle_worktree(record, borrowed=lambda: _borrowed(record)))
    except Exception:
        record.update(worktree_disposition="error", worktree_disposition_reason="settlement_failed")


def _unsettled(record: dict) -> bool:
    return record.get("status") not in store.ACTIVE and (
        "worktree_disposition" not in record or record.get("worktree_disposition_reason") in RETRY_REASONS)


def settle_left_worktrees() -> None:
    """Settle worktrees of finished tasks whose supervisor ended before settling them."""
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
                _reap_settled(current)
                store.replace(current, path)


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
    resolved_model = sources_calls = None
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
        with tempfile.TemporaryFile(dir=ensure_scratch_root()) as stdin, stdout_path.open("wb") as out, stderr_path.open("ab") as err:
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
            store.replace(record, path)
            terminal_observer = getattr(provider, "terminal_result_observer", None)
            communicate(child, invocation, stdout_path, stderr_path, hard_timeout, silence_timeout,
                        initial_response_timeout, liveness_paths(spec, invocation), output_sizes,
                        terminal_observer(stdout_path) if terminal_observer else None, checkpoint)
        returncode = child.returncode
        final = invocation.final_file
        final_text = final.read_text(errors="replace") if final and final.exists() else None
        parsed = provider.parse(
            stdout_path.read_text(errors="replace"), stderr_path.read_text(errors="replace"), returncode, final_text
        )
        text, usage, sources_calls = parsed.text, parsed.usage, parsed.sources_mcp_call_count
        if spec.agent == "agy" and spec.mode == "read-only":
            # Only the boundary's receipt, written outside the sandbox, proves the run read-only and
            # supplies its Sources count (C-3027); without a verified one the run fails.
            boundary, sources_calls, refusal = agy_sandbox.verify(spec.final_file, spec.task_id, record)
            record["read_only_boundary"] = boundary
            if refusal:
                status, error = "failed", refusal
                return
        if parsed.rate_limited and returncode >= 0:
            # Before the schema check, which would record the same terminal failure as invalid output.
            status, error = "rate_limited", parsed.error
            return
        if schema is not None:
            from scripts.agent_runtime.adapters._output_schema import json_value, structured_result

            result = structured_result(json_value(text), schema, returncode=returncode, terminal_ok=not parsed.error)
            text = result.response
            if not result.ok:
                error = f"{result.failure_code}: {result.stderr_excerpt}"
                status = "failed"
                return
        resolved_model = parsed.resolved_model
        status = "done" if returncode == 0 and not parsed.error and text and text.strip() else "failed"
        if returncode < 0:
            status = "crashed"
        if status != "done":
            error = parsed.error or (
                "provider exited unsuccessfully" if returncode else "provider returned no successful final response"
            )
        if status == "done" and record.get("schema_version") == 2 and record.get("require_review_verdict") is True:
            try:
                from scripts.review.verdict_parser import recognized_verdicts

                verdicts = set(recognized_verdicts(text))
                if not verdicts:
                    status, error = "failed", "review_missing_verdict_line"
                elif len(verdicts) > 1:
                    status, error = "failed", "review_ambiguous_verdict"
            except Exception:
                status, error = "failed", "review_gate_error"
    except _Cancelled:
        status, error = "cancelled", "cancelled by client"
    except DeadlineExpired as exc:
        status, error = "timeout", exc.diagnostic
        record.update(kill_reason=exc.kind, stderr_excerpt=exc.diagnostic)
    except subprocess.TimeoutExpired:
        status, error = "timeout", "process deadline exceeded"
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
            _enforce_delivery(record)
            if spec.agent == "cursor":
                record.update(
                    resolved_model=resolved_model if resolved_model is not None else "unknown",
                    resolved_model_known=resolved_model is not None,
                    resolved_model_source="cursor-stream-json" if resolved_model is not None else "pending",
                )
            record["provider_pgid"] = child.pid if child else None
            # The removal chokepoint releases a tree only to a finished owner record, so publish it, then
            # settle; wait() reads a terminal record under this lock and never sees the tree mid-removal.
            with store.task_state_lock(path):
                store.replace(record, path)
                _reap_settled(record, patience=SETTLE_PATIENCE)
                store.replace(record, path)
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
