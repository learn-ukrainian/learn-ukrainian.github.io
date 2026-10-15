"""Terminal-abandon publication across a writer crash (#10657 round 6).

A custody-bound record must never become consumable unless its publication was
confirmed. Each crash test forks the actual writer (owner attestation or lane
succession) and ends the child with ``os._exit`` at one boundary, the technique
of ``tests/test_teacher_deck_refresh.py``: no ``except``, ``finally`` or cleanup
runs, so the parent sees exactly what a killed writer leaves on disk. The lease
lives in the real store behind the production Monitor router on loopback, held
by this test process, as in the round-5 review's reproducer; the real reaper
then decides.

The hooks are black-box: the lease lapses when the writer makes the record's
payload durable in the task store (its ``fsync``), and the child dies at its
next Monitor probe, the confirmation's observation, or at the rename onto a
task record.
"""

import contextlib
import io
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import LeaseHolder, utc_now
from agents_extensions.shared.session_streams.store import SessionStreamStore
from scripts.api import epics_router
from scripts.fleet import ignored_task_output as output
from scripts.fleet import terminal_abandon
from scripts.orchestration import reap_worktrees as rw
from scripts.session_supervisor import remote
from tests.epics_monitor_stub import epics_monitor_stub
from tests.fleet.test_terminal_abandon import (
    HOLDER_HOST,
    MONITOR,
    _files,
    _refused_removal,
    _set_lease_env,
    invoke,
    kernel_identity,
)
from tests.fleet.test_terminal_abandon import succession as succession
from tests.fleet.test_terminal_abandon import writer_fixture as writer_fixture
from tests.fleet.test_terminal_abandon_attest import attest as attest
from tests.fleet.test_terminal_abandon_attest import attest_cli
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_continuation_worktree_reap import abandon_cohort as abandon_cohort
from tests.test_continuation_worktree_reap import same_branch_pending_cohort as same_branch_pending_cohort
from tests.test_reused_worktree_retention import cohort as cohort
from tests.test_reused_worktree_retention import save

CRASHED = 73
TTL = 900
# The production stream probe; the shape fixtures replace it with an in-memory Monitor.
REAL_STREAM = remote.RemoteEpicClient.stream
WRITERS = ["attested", "succession"]


def _shape(path, request):
    """The writer's fixture as one mapping: repo, tree, task store and the call that writes."""
    if path == "attested":
        fx = request.getfixturevalue("attest")
        return {**fx, "write": lambda: attest_cli(fx, apply=True)}
    fixture, monitor = request.getfixturevalue("succession")
    repo, tree, tasks, *_ = fixture
    return {
        "repo": repo,
        "tree": tree,
        "tasks": tasks,
        "fixture": fixture,
        "monitor": monitor,
        "write": lambda: invoke(fixture),
    }


@pytest.fixture(params=WRITERS)
def real(request, monkeypatch, tmp_path):
    """One writer's tree, with its lease in the real store behind the real Monitor router.

    This test process is the lease's recorded holder, as a launcher is for the
    commands run beneath it. Monitor's clock runs ``clock`` seconds ahead of
    the host's: a forked child moves it (it cannot share memory with the
    parent, which serves Monitor on a thread).
    """
    fx = _shape(request.param, request)
    store = SessionStreamStore(SessionStreamDatabase(tmp_path / "streams.sqlite3"))
    store.database.connect().close()
    holder = LeaseHolder(
        agent="muse",
        harness="muse-cli",
        instance_id="muse-monitor-1",
        process_id=os.getpid(),
        host_id=HOLDER_HOST,
        process_identity=kernel_identity(os.getpid()),
    )
    lease, _ = store.claim_remote_session(
        stream_id=MONITOR,
        holder=holder,
        lineage_id="lineage-10657-r6",
        ttl_seconds=TTL,
        session_id="session-current",
        lease_id="lease-current",
    )
    clock = tmp_path / "monitor-clock-offset"
    clock.write_text("0")
    real_now = epics_router.utc_now
    monkeypatch.setattr(epics_router, "utc_now", lambda: real_now() + timedelta(seconds=float(clock.read_text())))
    _set_lease_env(monkeypatch, GENERATION=str(lease.generation), FENCING_TOKEN=str(lease.fencing_token))
    monkeypatch.setattr(remote.RemoteEpicClient, "stream", REAL_STREAM)
    with epics_monitor_stub(store) as base:
        monkeypatch.setattr(remote, "DEFAULT_MONITOR", base)
        yield {**fx, "path": request.param, "store": store, "lease": lease, "clock": clock, "base": base}


def _monitor_lease(fx):
    return remote.RemoteEpicClient(base=fx["base"]).stream(MONITOR, digest_limit=1)["lease"]


def _in_store(path, tasks):
    return Path(path).parent.resolve() == Path(tasks).resolve()


def _in_child(fx, hooks) -> int:
    """Run the writer in a forked child with ``hooks(state)`` installed; return its exit code."""
    pid = os.fork()
    if pid == 0:  # pragma: no cover - child
        try:
            hooks({"lapsed": False})
            with contextlib.redirect_stdout(io.StringIO()):
                fx["write"]()
            os._exit(0)
        except BaseException:
            os._exit(1)
    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)


def _lapse_at_the_record_write_then_die_at_confirmation(fx):
    """The review's reproducer: the lease lapses as the record is written; the writer dies before confirming."""
    tasks, clock = fx["tasks"], fx["clock"]

    def hooks(state):
        fsync, stream = os.fsync, remote.RemoteEpicClient.stream

        def lapsing_fsync(fd):
            if not state["lapsed"] and _in_store(os.readlink(f"/proc/self/fd/{fd}"), tasks):
                clock.write_text(str(TTL + 60))  # Monitor's clock passes expires_at
                state["lapsed"] = True
            return fsync(fd)

        def dying_stream(self, *args, **kwargs):
            if state["lapsed"]:
                os._exit(CRASHED)  # the confirmation's observation never runs
            return stream(self, *args, **kwargs)

        os.fsync = lapsing_fsync
        remote.RemoteEpicClient.stream = dying_stream

    return hooks


def _die_at_the_rename(fx, *, after):
    """Die at the rename onto a task record: before the kernel performs it, or just after."""
    tasks = fx["tasks"]

    def hooks(state):
        replace = os.replace

        def dying_replace(source, destination, *args, **kwargs):
            if _in_store(destination, tasks) and Path(destination).suffix == ".json":
                if after:
                    replace(source, destination, *args, **kwargs)
                os._exit(CRASHED)
            return replace(source, destination, *args, **kwargs)

        os.replace = dying_replace

    return hooks


def _record(fx):
    """The task record that carries the tree's abandon record, and its receipt."""
    (record,) = [
        record
        for record in (json.loads(path.read_bytes()) for path in fx["tasks"].glob("*.json"))
        if "worktree_abandon" in record
    ]
    return record, record["worktree_abandon"]


def _consumable(fx):
    return any("worktree_abandon" in json.loads(path.read_bytes()) for path in fx["tasks"].glob("*.json"))


def _pending(fx):
    """Files beside the task records that no task-store reader opens (``*.json`` only)."""
    return sorted(path.name for path in fx["tasks"].iterdir() if path.name.startswith(".") and path.suffix != ".lock")


def _reap(fx):
    return next(
        row
        for row in rw.reap_worktrees(
            repo_root=fx["repo"], apply=True, live_cwds=set(), preserve_then_reap=True, merged_pr_only=False
        )
        if row.path == str(fx["tree"])
    )


def _write(fx):
    with contextlib.redirect_stdout(io.StringIO()) as stdout:
        code = fx["write"]()
    return code, json.loads(stdout.getvalue())


def _revive(fx):
    """The holder renews its lapsed lease: same generation, holder and identity; new validity and version."""
    lapsed = _monitor_lease(fx)
    monitor_now = utc_now() + timedelta(seconds=float(fx["clock"].read_text()))
    revived = fx["store"].heartbeat(fx["lease"], now=monitor_now)
    current = _monitor_lease(fx)
    assert (revived.generation, revived.fencing_token) == (fx["lease"].generation, fx["lease"].fencing_token)
    assert current["state"] == "active" and current["version"] > lapsed["version"]
    return lapsed


def test_crash_before_confirmation_is_never_consumed(real):
    """Expire at the record write, die before confirmation, renew the same generation: nothing is consumable.

    Round 5 published the task record first and confirmed afterwards, so this
    left a record the reaper consumed (``preserved_then_removed``) with the
    tree deleted. A pending publication is inert; the writer's next run for
    the tree discards it and publishes through confirmation.
    """
    assert _in_child(real, _lapse_at_the_record_write_then_die_at_confirmation(real)) == CRASHED
    assert _revive(real)["state"] == "expired", "the record write must have happened outside the validity interval"
    assert not _consumable(real), "an unconfirmed publication must never reach a task record"
    row = _reap(real)
    assert row.action not in {"removed", "preserved_then_removed"}, row
    assert real["tree"].exists()
    leftover = _pending(real)
    assert leftover, "the crashed writer's pending publication stays inert on disk"
    # The writer's next run for the same tree discards it and confirms its own publication.
    code, result = _write(real)
    assert (code, result["outcome"]) == (0, "recorded"), result
    assert not _pending(real)
    assert _record(real)[1]["publication"] == {
        "schema": "terminal-abandon-publication.v1",
        "state": "confirmed",
        "lease_version": _monitor_lease(real)["version"],
    }
    assert _reap(real).action == "preserved_then_removed"
    assert not real["tree"].exists()


@pytest.mark.parametrize("after", [False, True], ids=["before_rename", "after_rename"])
def test_crash_at_the_commit_rename(real, after):
    """The rename is the only step that makes a publication consumable, and it is atomic.

    Dying before the kernel performs it leaves only the inert pending record,
    which the next run discards; dying just after it leaves a confirmed
    record that the reaper consumes as usual.
    """
    assert _in_child(real, _die_at_the_rename(real, after=after)) == CRASHED
    if after:
        assert _consumable(real) and not _pending(real)
        assert _reap(real).action == "preserved_then_removed"
        assert not real["tree"].exists()
        return
    assert not _consumable(real)
    assert _pending(real)
    row = _reap(real)
    assert row.action not in {"removed", "preserved_then_removed"}, row
    assert real["tree"].exists()
    code, result = _write(real)
    assert (code, result["outcome"]) == (0, "recorded"), result
    assert not _pending(real)
    assert _reap(real).action == "preserved_then_removed"


def test_pending_publication_is_invisible_to_task_store_readers(real):
    """No reader of the task store opens a pending record: the cohort and the abandon proof ignore it."""
    assert _in_child(real, _die_at_the_rename(real, after=False)) == CRASHED
    pending = [real["tasks"] / name for name in _pending(real)]
    assert pending and all("worktree_abandon" in json.loads(path.read_bytes()) for path in pending)
    matches = output.matching_worktree_records(real["tree"], real["tasks"], repo_root=real["repo"], publish_cache=False)
    assert all(path.parent == real["tasks"] and path.suffix == ".json" for path, _ in matches)
    assert not any("worktree_abandon" in member for _, member in matches)
    assert rw._terminal_abandon_matches(real["repo"], real["tree"]) is None


@pytest.mark.parametrize("real", ["attested"], indirect=True)
def test_dry_run_leaves_a_pending_publication_alone(real):
    """Discarding a leftover is a write: only an applying run for the tree does it, under the record locks."""
    assert _in_child(real, _die_at_the_rename(real, after=False)) == CRASHED
    leftover = _pending(real)
    with contextlib.redirect_stdout(io.StringIO()):
        assert attest_cli(real) == 0
    assert _pending(real) == leftover


# --- The reader consumes only the confirmed form, against the current lease ---


@pytest.mark.parametrize("path", WRITERS)
@pytest.mark.parametrize(
    "tamper,attested_reason,succession_reason",
    [
        # The attested receipt's exact key set already refuses a record without the marker.
        ("missing", "receipt invalid", "PUBLICATION_UNCONFIRMED"),
        ("pending", "PUBLICATION_UNCONFIRMED", "PUBLICATION_UNCONFIRMED"),
        ("untyped_version", "PUBLICATION_UNCONFIRMED", "PUBLICATION_UNCONFIRMED"),
        ("extra_field", "PUBLICATION_UNCONFIRMED", "PUBLICATION_UNCONFIRMED"),
        ("newer_than_current_lease", "STALE_AUTHORITY", "STALE_AUTHORITY"),
    ],
)
def test_reader_requires_the_confirmed_publication(request, path, tamper, attested_reason, succession_reason):
    """A record without the confirmed marker, or confirmed against a lease state the current lease predates, refuses."""
    fx = _shape(path, request)
    code, result = _write(fx)
    assert (code, result["outcome"]) == (0, "recorded"), result
    record, receipt = _record(fx)
    marker = receipt["publication"]
    if tamper == "missing":
        receipt.pop("publication")
    elif tamper == "pending":
        marker["state"] = "pending"
    elif tamper == "untyped_version":
        marker["lease_version"] = str(marker["lease_version"])
    elif tamper == "extra_field":
        marker["confirmed_at"] = "2026-10-15T00:00:00Z"
    else:
        marker["lease_version"] = fx["monitor"]["streams"][MONITOR]["version"] + 1
    save(fx["tasks"], record)
    _refused_removal(fx["fixture"], attested_reason if path == "attested" else succession_reason)


@pytest.mark.parametrize("path", WRITERS)
def test_rename_happens_only_before_the_confirmed_expiry(request, monkeypatch, path):
    """The lease must still be valid on this host's clock when the confirmed record is renamed into place.

    Monitor is loopback, so it shares the clock. The local recheck after the
    confirmation outlasts the lease here; the rename is refused and the
    pending record and the call's preservation are removed.
    """
    fx = _shape(path, request)
    lease = fx["monitor"]["streams"][MONITOR]
    lease["expires_at"] = (datetime.now(UTC) + timedelta(seconds=600)).strftime("%Y-%m-%dT%H:%M:%SZ")

    class Clock(datetime):
        offset = timedelta(0)

        @classmethod
        def now(cls, tz=None):
            return datetime.now(tz) + cls.offset

    local = output.terminal_abandon_local

    def outlasting_recheck(*args, **kwargs):
        checked = local(*args, **kwargs)
        if _pending(fx):
            Clock.offset = timedelta(seconds=601)
        return checked

    monkeypatch.setattr(terminal_abandon, "datetime", Clock)
    monkeypatch.setattr(output, "terminal_abandon_local", outlasting_recheck)
    before = _files(fx["repo"])
    code, result = _write(fx)
    assert (code, result["outcome"], result["code"]) == (2, "refused", "STALE_AUTHORITY"), result
    assert Clock.offset, "the recheck after confirmation must have run"
    assert _files(fx["repo"]) == before and not _consumable(fx) and not _pending(fx)
