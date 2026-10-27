"""Legacy host/credit admission and the atomic pre-launch write-slot hold.

Mirrors delegate.py:5128-5192, 15385-15406, 15812-15882 and 19369-19386.
The retained admission scanner and ownership ledger read the same hold format.
"""

import contextlib
import subprocess
import sys
import uuid

from scripts.common.task_store_paths import tasks_dir
from scripts.dispatcher import store
from scripts.orchestration import dispatch_admission as legacy
from scripts.orchestration import worktree_prep
from scripts.orchestration.dead_worker_state import (
    mark_dead_worker_terminal,
    mark_orphaned_admission_hold_crashed,
    mark_orphaned_worktree_prep_crashed,
    worker_liveness,
)
from scripts.orchestration.task_record_store import task_state_lock


class Refused(ValueError):
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code


def _write(path, record):
    # Shared healers recheck the nonce/status/identity under task_state_lock.
    if record.get("schema_version") == 2:
        store.replace(record, path)
    else:
        from scripts.orchestration.task_record_store import write_record_unlocked

        write_record_unlocked(path, record)


def heal_dead(path, state):
    """Adapter for legacy _heal_dead_task: only proven death permits a write."""
    if state.get("status") not in legacy.ACTIVE_STATUSES:
        return
    if state.get("pid"):
        mark_dead_worker_terminal(
            path, state, source="admission", terminal_status="crashed",
            allowed_statuses=("running", "spawning"), pid_alive=legacy.process_alive,
            resolve_head=_head, write=_write,
        )
    elif worktree_prep.is_orphaned_prep_record(state):
        mark_orphaned_worktree_prep_crashed(
            path, state, source="admission", is_orphaned=worktree_prep.is_orphaned_prep_record, write=_write,
        )
    elif legacy.is_orphaned_admission_hold(state):
        mark_orphaned_admission_hold_crashed(
            path, state, source="admission", is_orphaned=legacy.is_orphaned_admission_hold,
            reason=legacy.ORPHANED_HOLD_REASON, write=_write,
        )


def _head(root):
    from scripts.dispatcher.git import _git

    try:
        return _git(root, "rev-parse", "HEAD")
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def evaluate(mode, *, sweep, thresholds=None, reap_disk=False, disk_guard=True):
    """Copy-adapted from delegate._evaluate_dispatch_admission, including v2 liveness."""
    return legacy.evaluate(
        mode, tasks_dir(), pid_alive=legacy.process_alive,
        record_liveness=lambda record: worker_liveness(record, pid_alive=legacy.process_alive),
        on_dead=heal_dead if sweep else None, thresholds=thresholds,
        reaper=legacy.run_disk_reaper if reap_disk else None, disk_guard=disk_guard,
    )


def allows(decision, force_reason):
    """delegate.py:5155: force may override host checks, never disk refusal."""
    return decision.exempt or decision.admitted or (force_reason is not None and not decision.disk_refused)


def report(decision, *, force_reason=None):
    """Legacy refusal/admit/override text and exits."""
    if decision.exempt:
        return
    if decision.admitted:
        print(f"🚦 dispatch admission: admitted — {decision.summary()}", file=sys.stderr)
    elif allows(decision, force_reason):
        print(
            f"⚠️  dispatch admission overridden by --force-admission ({force_reason!r}): {'; '.join(decision.failures)}",
            file=sys.stderr,
        )
    else:
        raise Refused(f"❌ {decision.refusal_line()}", 4 if decision.disk_refused else 3)


def precheck(mode, *, force_reason=None):
    if force_reason is not None:
        return
    try:
        decision = legacy.precheck(mode)
    except ValueError as exc:
        raise Refused(f"❌ invalid dispatch admission threshold: {exc}", 2) from exc
    if decision is not None:
        report(decision)


def check(mode, *, dry_run, disk_guard, force_reason=None):
    try:
        decision = evaluate(mode, sweep=not dry_run, reap_disk=not dry_run and disk_guard, disk_guard=disk_guard)
    except ValueError as exc:
        raise Refused(f"❌ invalid dispatch admission threshold: {exc}", 2) from exc
    report(decision, force_reason=force_reason)
    return decision


def credit_period_refusal(agent, model):
    """delegate.py:19369: import errors propagate; only the reader owns unknown-state policy."""
    from scripts.fleet import credit_lane

    if not model:
        from scripts.agent_runtime.telemetry import _default_model_for
        from scripts.review.model_catalog import substitution_default_model

        model = substitution_default_model(agent) or _default_model_for(agent)
    return credit_lane.dispatch_refusal(agent, model)


def check_credit(agent, model):
    if refusal := credit_period_refusal(agent, model):
        raise Refused(f"❌ dispatch refused: {refusal}", 2)


@contextlib.contextmanager
def reserve(task_id, mode, decision, *, agent, disk_guard, force_reason=None):
    """Legacy locked recheck -> publish hold -> setup; release on every unwound path."""
    hold = None
    try:
        if not decision.exempt:
            refusal = None
            try:
                with legacy.admission_lock(tasks_dir()):
                    current = evaluate(mode, sweep=True, thresholds=decision.thresholds, disk_guard=disk_guard())
                    if allows(current, force_reason):
                        nonce = uuid.uuid4().hex
                        owner = legacy.new_admission_hold(nonce)
                        hold = dict(schema_version=2, task_id=task_id, agent=agent, run_nonce=nonce, status="spawning", pid=None,
                                    mode=mode, started_at=owner["admitted_at"], finished_at=None,
                                    admission=current.to_record(force_reason=force_reason), admission_hold=owner)
                        path = store.record_path(task_id)
                        with task_state_lock(path):
                            if store.read(task_id, missing_ok=True) is not None:
                                raise RuntimeError(f"task record for {task_id!r} exists; refusing to overwrite it")
                            store._write(path, hold, exclusive=True)
                    else:
                        refusal = Refused(f"❌ {current.refusal_line()}", 4 if current.disk_refused else 3)
            except legacy.AdmissionLockTimeout as exc:
                raise Refused(f"❌ dispatch admission lock unavailable: {exc}; retry the dispatch", 3) from exc
            except (OSError, RuntimeError) as exc:
                raise Refused(f"❌ could not publish the admission hold for {task_id!r}: {exc}", 1) from exc
            if refusal is not None:
                raise refusal
        yield hold
    finally:
        if hold is not None:
            path = store.record_path(task_id)
            with contextlib.suppress(OSError), task_state_lock(path):
                current = store.read(task_id, missing_ok=True)
                if (current is not None and current.get("run_nonce") == hold["run_nonce"]
                        and current.get("status") in store.ACTIVE and legacy.is_admission_hold_record(current)):
                    path.unlink(missing_ok=True)
