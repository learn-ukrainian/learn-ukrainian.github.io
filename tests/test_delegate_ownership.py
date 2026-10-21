"""Tests for scripts/guardrails/delegate_ownership.py (#5643 Δ2-A WARN)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts.guardrails.delegate_ownership import (
    ClaimKind,
    GuardMode,
    OwnershipLedger,
    PathClaim,
    admit_write_paths,
    claims_conflict,
    normalize_claim,
)


def test_normalize_literal_subtree_unknown():
    assert normalize_claim("scripts/delegate.py").kind == ClaimKind.SUBTREE
    assert normalize_claim("scripts/").kind == ClaimKind.SUBTREE
    assert normalize_claim("scripts/**").kind == ClaimKind.SUBTREE
    assert normalize_claim("scripts/**/*.py").kind == ClaimKind.UNKNOWN
    assert normalize_claim("../escape").kind == ClaimKind.UNKNOWN
    assert normalize_claim(r"C:\repo\scripts\delegate.py").kind == ClaimKind.UNKNOWN
    # Canonicalize equivalent spellings (CF r4 F001)
    a = normalize_claim("scripts/delegate.py")
    b = normalize_claim("scripts//delegate.py")
    c = normalize_claim("scripts/./delegate.py")
    assert a.norm == b.norm == c.norm
    assert claims_conflict(a, b) and claims_conflict(a, c)


def test_claims_conflict_matrix():
    f_a = normalize_claim("a/b.py")
    f_c = normalize_claim("a/c.py")
    sub = normalize_claim("a/")
    sib = normalize_claim("b/")
    assert claims_conflict(f_a, f_a)
    assert not claims_conflict(f_a, f_c)
    assert claims_conflict(f_a, sub)
    assert claims_conflict(sub, f_a)
    assert claims_conflict(normalize_claim("a/x/"), sub)
    assert not claims_conflict(sub, sib)
    assert not claims_conflict(f_a, normalize_claim("a/**/*.py"))


@pytest.mark.parametrize("legacy", [False, True])
@pytest.mark.parametrize(
    "held,incoming,refused,overlap",
    [
        ("scripts/agent_runtime", "scripts/agent_runtime/runner.py", True, True),
        ("scripts/agent_runtime/runner.py", "scripts/agent_runtime", True, True),
        ("scripts/agent_runtime", "scripts/agent_runtime/*.py", True, False),
        ("scripts/agent_runtime/*.py", "scripts/agent_runtime", True, False),
        ("scripts/agent_runtime", "scripts/agent_runtime_other", False, False),
    ],
)
def test_directory_admission_with_mixed_ledger(tmp_path, legacy, held, incoming, refused, overlap):
    ledger = OwnershipLedger(tmp_path / "ownership.sqlite3", task_state_dir=tmp_path, mode=GuardMode.REFUSE)
    pid = os.getpid()
    (tmp_path / "holder.json").write_text(json.dumps({"status": "running", "pid": pid}), encoding="utf-8")
    holder = ledger.admit(task_id="holder", mode="workspace-write", owned_paths=[held], pid=pid)
    assert holder.admitted
    if legacy:
        # Preserve the old row's key and shape, including FILE for a plain
        # directory, while admitting new SUBTREE rows alongside it.
        claim = normalize_claim(held)
        kind = ClaimKind.FILE if claim.kind is ClaimKind.SUBTREE else claim.kind
        with ledger._connect() as conn:
            conn.execute(
                "UPDATE write_claims SET claim_json = ? WHERE task_id = ?",
                (json.dumps(PathClaim(claim.raw, kind, claim.norm).as_dict()), "holder"),
            )
    result = ledger.admit(task_id="incoming", mode="workspace-write", owned_paths=[incoming], pid=pid)
    assert result.admitted is (not refused)
    assert bool(result.conflicts) is overlap
    if refused:
        assert "REFUSE" in result.reason
    if refused and not overlap:
        assert "--owned-path" in result.reason
        assert "--research-owned-path" not in result.reason


def test_read_only_exempt(tmp_path: Path):
    ledger = tmp_path / "own.sqlite3"
    result = admit_write_paths(
        task_id="t1",
        mode="read-only",
        owned_paths=["scripts/foo.py"],
        ledger_path=ledger,
        task_state_dir=tmp_path,
    )
    assert result.skipped is True
    assert result.admitted is True


def test_solo_no_claims_admitted(tmp_path: Path):
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    result = admit_write_paths(
        task_id="solo",
        mode="workspace-write",
        owned_paths=[],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert result.admitted is True
    assert result.would_refuse is False
    # Sentinel reserved so a later peer is unprovable (CF r8)
    later = admit_write_paths(
        task_id="later",
        mode="workspace-write",
        owned_paths=["scripts/a.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.WARN,
    )
    assert later.would_refuse is True


def test_exact_file_conflict_warn(tmp_path: Path):
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    # Active holder with live pid (this process)
    pid = os.getpid()
    (state_dir / "holder.json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )
    first = admit_write_paths(
        task_id="holder",
        mode="workspace-write",
        owned_paths=["scripts/a.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert first.admitted and not first.would_refuse

    second = admit_write_paths(
        task_id="challenger",
        mode="workspace-write",
        owned_paths=["scripts/a.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.WARN,
    )
    assert second.admitted is True
    assert second.would_refuse is True
    assert second.conflicts


def test_stale_claim_reconciled(tmp_path: Path):
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    # dead pid
    (state_dir / "dead.json").write_text(
        json.dumps({"status": "running", "pid": 99999999}), encoding="utf-8"
    )
    # plant claim via first admit then kill state
    own = OwnershipLedger(ledger, task_state_dir=state_dir, mode=GuardMode.WARN)
    # manually insert with dead pid after admit with fake live - use direct SQL after admit
    r = own.admit(
        task_id="dead",
        mode="workspace-write",
        owned_paths=["x.py"],
        pid=99999999,
    )
    assert r.admitted
    # now challenger should free the stale claim
    (state_dir / "dead.json").write_text(
        json.dumps({"status": "done", "pid": 99999999}), encoding="utf-8"
    )
    second = own.admit(
        task_id="live",
        mode="workspace-write",
        owned_paths=["x.py"],
        pid=os.getpid(),
    )
    assert second.admitted is True
    assert second.would_refuse is False


@pytest.mark.parametrize("block", ["admission_hold", "worktree_prep"])
@pytest.mark.parametrize("identity_case,kept", [("foreign", True), ("alive", True), ("dead", False), ("reused", False)])
def test_dispatcher_identity_protects_write_claim_after_grace(tmp_path, monkeypatch, block, identity_case, kept):
    import time

    from scripts.guardrails import delegate_ownership as ownership
    from scripts.orchestration import dead_worker_state as dead

    pid = 999_999_998
    namespace = dead.INITIAL_PID_NAMESPACE
    identity = {"pid": pid, "start_time": 100, "pid_namespace": "pid:[999999]" if identity_case == "foreign" else namespace}
    record = {
        "task_id": "dispatcher", "status": "spawning", "pid": None, "run_nonce": "run",
        block: {"run_nonce": "run", "owner_pid": pid, "owner_start": 100, "owner_identity": identity},
    }
    path = tmp_path / "dispatcher.json"
    path.write_text(json.dumps(record))
    before = path.read_bytes()
    monkeypatch.setattr(dead, "PROC_ROOT", tmp_path / "proc")
    monkeypatch.setattr(dead, "_pid_namespace", lambda process="self": namespace)
    monkeypatch.setattr(dead, "_proc_pid_namespace", lambda: namespace)

    def stat(process):
        if identity_case == "dead":
            raise FileNotFoundError
        return pid, 101 if identity_case == "reused" else 100

    monkeypatch.setattr(dead, "_process_stat", stat)
    assert ownership._task_still_active(
        "dispatcher", pid, tmp_path,
        created_at=time.time() - ownership.ADMISSION_PID_GRACE_S - 1,
        process_matches_task=lambda *_args, **_kwargs: False,
    ) is kept
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "case,remaining",
    [
        ("foreign", 1),
        ("foreign_crashed", 0),
        ("foreign_done", 0),
        ("foreign_failed", 0),
        ("dead", 0),
        ("reused", 0),
        ("reused_in_grace", 0),
        ("legacy_dead", 0),
        ("legacy_alive", 1),
        ("legacy_unknown", 1),
    ],
)
def test_namespace_claim_reconciliation(tmp_path, monkeypatch, case, remaining):
    """#10621: UNKNOWN protects ownership; proven death and PID reuse release it."""
    import sqlite3
    import time

    from scripts.guardrails import delegate_ownership as ownership
    from scripts.orchestration import dead_worker_state as dead

    pid = 999_999_998
    namespace = dead.INITIAL_PID_NAMESPACE
    status = case.removeprefix("foreign_") if case.startswith("foreign_") else "running"
    record = {"task_id": "worker", "status": status, "pid": pid}
    if not case.startswith("legacy"):
        record["worker_identity"] = {
            "pid": pid, "host_pid": None, "start_time": 100,
            "pid_namespace": "pid:[999999]" if case.startswith("foreign") else namespace,
            "recorder_pid_namespace": namespace,
        }
    (tmp_path / "worker.json").write_text(json.dumps(record))
    before = (tmp_path / "worker.json").read_bytes()
    monkeypatch.setattr(dead, "PROC_ROOT", tmp_path / "proc")
    monkeypatch.setattr(dead, "_pid_namespace", lambda process="self": None if case == "legacy_unknown" else namespace)
    monkeypatch.setattr(dead, "_proc_pid_namespace", lambda: namespace)
    monkeypatch.setattr(ownership, "_pid_alive", lambda candidate: case in ("reused", "reused_in_grace", "legacy_alive"))

    def stat(process):
        if case.startswith("reused"):
            return pid, 101
        raise FileNotFoundError

    def signal(candidate, signal):
        raise ProcessLookupError

    monkeypatch.setattr(dead, "_process_stat", stat)
    monkeypatch.setattr(dead.os, "kill", signal)
    ledger = OwnershipLedger(tmp_path / "claims.sqlite", task_state_dir=tmp_path, mode=GuardMode.WARN)
    with sqlite3.connect(":memory:") as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL)")
        created_at = time.time() if case == "reused_in_grace" else time.time() - ownership.ADMISSION_PID_GRACE_S - 1
        connection.execute("INSERT INTO write_claims VALUES (?, ?, ?, ?)", (
            "worker", '{"kind":"file","norm":"scripts/fixture.py"}', pid, created_at,
        ))
        released = ledger._reconcile_stale(connection)
        assert connection.execute("SELECT COUNT(*) FROM write_claims").fetchone()[0] == remaining
        assert released == ([] if remaining else ["worker"])
    assert (tmp_path / "worker.json").read_bytes() == before


@pytest.mark.parametrize("mode", [GuardMode.WARN, GuardMode.REFUSE])
@pytest.mark.parametrize("same_pid", [False, True])
@pytest.mark.parametrize("text_pid", [False, True])
def test_namespace_duplicate_admission_preserves_unknown_claim(tmp_path, mode, same_pid, text_pid):
    import time

    from scripts.guardrails.delegate_ownership import ADMISSION_PID_GRACE_S

    pid = os.getpid() if same_pid else 999_999_998
    record = {
        "task_id": "worker", "status": "running", "pid": str(pid) if text_pid else pid,
        "worker_identity": {"pid": pid, "host_pid": None, "start_time": 100,
                            "pid_namespace": "pid:[999999]", "recorder_pid_namespace": "pid:[999999]"},
    }
    path = tmp_path / "worker.json"
    path.write_text(json.dumps(record))
    before = path.read_bytes()
    ledger = OwnershipLedger(tmp_path / "claims.sqlite", task_state_dir=tmp_path, mode=mode)
    assert ledger.admit(task_id="worker", mode="workspace-write", owned_paths=["scripts/held.py"], pid=pid).admitted
    with ledger._connect() as connection:
        connection.execute("UPDATE write_claims SET created_at = ?", (time.time() - ADMISSION_PID_GRACE_S - 1,))
    incoming = ledger.admit(task_id="worker", mode="workspace-write", owned_paths=["scripts/replacement.py"], pid=os.getpid())
    assert incoming.admitted is (mode is GuardMode.WARN)
    assert incoming.would_refuse is True
    with ledger._connect(read_only=True) as connection:
        rows = connection.execute("SELECT claim_json, pid FROM write_claims").fetchall()
    assert [(json.loads(row["claim_json"])["norm"], row["pid"]) for row in rows] == [("scripts/held.py", pid)]
    assert path.read_bytes() == before


def test_override_records_reason(tmp_path: Path):
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    (state_dir / "h.json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )
    admit_write_paths(
        task_id="h",
        mode="workspace-write",
        owned_paths=["same.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    over = admit_write_paths(
        task_id="c",
        mode="workspace-write",
        owned_paths=["same.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        allow_path_overlap="coordinated dual-edit",
    )
    assert over.admitted is True
    assert over.would_refuse is False
    assert over.override_reason == "coordinated dual-edit"


def test_refuse_mode_blocks(tmp_path: Path):
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    (state_dir / "h.json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )
    admit_write_paths(
        task_id="h",
        mode="workspace-write",
        owned_paths=["same.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    refused = admit_write_paths(
        task_id="c",
        mode="workspace-write",
        owned_paths=["same.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.REFUSE,
    )
    assert refused.admitted is False
    assert refused.would_refuse is True


def test_slashful_task_id_state_file_sanitized(tmp_path: Path):
    """task_id with slashes must resolve to underscore state files (CF F001)."""
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    # delegate.py stores codex/5643 as codex_5643.json
    (state_dir / "codex_5643.json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )
    first = admit_write_paths(
        task_id="codex/5643",
        mode="workspace-write",
        owned_paths=["scripts/x.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert first.admitted is True
    second = admit_write_paths(
        task_id="other",
        mode="workspace-write",
        owned_paths=["scripts/x.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.WARN,
    )
    assert second.would_refuse is True
    assert second.conflicts


def test_no_claims_with_active_peer_is_unprovable(tmp_path: Path):
    """Write-capable dispatch without owned paths vs active peer (CF r3 F002)."""
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    (state_dir / "peer.json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )
    admit_write_paths(
        task_id="peer",
        mode="workspace-write",
        owned_paths=["scripts/a.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    blank = admit_write_paths(
        task_id="blank",
        mode="workspace-write",
        owned_paths=[],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.WARN,
    )
    assert blank.admitted is True
    assert blank.would_refuse is True


def test_duplicate_equivalent_claims_do_not_crash(tmp_path: Path):
    """Repeatable / equivalent owned paths must not hit PRIMARY KEY (CF r5)."""
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    result = admit_write_paths(
        task_id="dup",
        mode="workspace-write",
        owned_paths=["scripts/a.py", "scripts//a.py", "scripts/./a.py"],
        pid=os.getpid(),
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert result.admitted is True
    assert len(result.claims) == 1


def test_live_ledger_pid_keeps_claim_despite_terminal_state(tmp_path: Path):
    """Admission→state-write race: terminal state must not drop live PID claim (CF r6)."""
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    # Stale terminal file for reused task_id, but ledger PID is this live process.
    (state_dir / "reuse.json").write_text(
        json.dumps({"status": "done", "pid": 1}), encoding="utf-8"
    )
    first = admit_write_paths(
        task_id="reuse",
        mode="workspace-write",
        owned_paths=["scripts/x.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert first.admitted is True
    # Concurrent peer must still see the claim (would_refuse), not reconcile it away.
    peer = admit_write_paths(
        task_id="peer2",
        mode="workspace-write",
        owned_paths=["scripts/x.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.WARN,
    )
    assert peer.would_refuse is True


def test_same_task_id_live_pid_does_not_replace_claims(tmp_path: Path, monkeypatch):
    """Concurrent same task_id: second admission must not clobber first claims (CF r7)."""
    import scripts.guardrails.delegate_ownership as own_mod

    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    holder_pid = os.getpid()
    first = admit_write_paths(
        task_id="same",
        mode="workspace-write",
        owned_paths=["scripts/held.py"],
        pid=holder_pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert first.admitted is True

    real_alive = own_mod._pid_alive

    def fake_alive(pid: int) -> bool:
        if pid == 424242:
            return True
        return real_alive(pid)

    monkeypatch.setattr(own_mod, "_pid_alive", fake_alive)
    second = admit_write_paths(
        task_id="same",
        mode="workspace-write",
        owned_paths=["scripts/other.py"],
        pid=424242,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.WARN,
    )
    assert second.admitted is True
    assert second.would_refuse is True
    # Original claim retained
    import sqlite3

    rows = list(sqlite3.connect(ledger).execute("SELECT claim_json FROM write_claims"))
    assert any("held.py" in r[0] for r in rows)
    assert not any("other.py" in r[0] for r in rows)

    # Same-pid retry still allowed
    monkeypatch.setattr(own_mod, "_pid_alive", real_alive)
    retry = admit_write_paths(
        task_id="same",
        mode="workspace-write",
        owned_paths=["scripts/held.py", "scripts/extra.py"],
        pid=holder_pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert retry.admitted is True
    assert retry.would_refuse is False


def test_admit_write_paths_default_follows_env_refuse(
    tmp_path: Path, monkeypatch
) -> None:
    """Library default is env_guard_mode(), not hardcoded WARN (CF #5662 F001)."""
    monkeypatch.delenv("DELEGATE_OWNERSHIP_MODE", raising=False)
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    (state_dir / "h.json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )
    admit_write_paths(
        task_id="h",
        mode="workspace-write",
        owned_paths=["same.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    # No guard_mode kwarg → must refuse on conflict (default REFUSE).
    refused = admit_write_paths(
        task_id="c",
        mode="workspace-write",
        owned_paths=["same.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert refused.mode is GuardMode.REFUSE
    assert refused.admitted is False
    assert refused.would_refuse is True


def test_unprovable_refusal_names_peer_and_is_not_called_a_conflict(tmp_path: Path):
    """A refusal with zero overlaps must not masquerade as a path conflict.

    Regression: five live dispatches that were fired without
    ``--research-owned-path`` blocked every subsequent write dispatch fleet-wide,
    and the guard reported ``path ownership conflict ... (conflicts=0)`` — a
    message that names no peer, offers no fix, and reads as a guard bug.
    """
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    (state_dir / "undeclared.json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )
    # Peer runs write-capable without declaring any owned path.
    peer = admit_write_paths(
        task_id="undeclared",
        mode="workspace-write",
        owned_paths=[],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert peer.admitted is True

    # Our task declares one concrete file that overlaps nothing.
    blocked = admit_write_paths(
        task_id="mine",
        mode="workspace-write",
        owned_paths=["docs/plans/brand-new-file.md"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.REFUSE,
    )
    assert blocked.admitted is False
    assert blocked.conflicts == []
    reason = blocked.reason
    assert "path ownership conflict" not in reason, reason
    assert "cannot prove write-path disjointness" in reason, reason
    assert "undeclared" in reason, reason  # the blocking peer is named
    assert f"pid {pid}" in reason, reason
    assert "--owned-path" in reason and "--allow-path-overlap" in reason, reason
    assert "--research-owned-path" not in reason, reason


def test_ownership_ledger_release_pid_scoped_and_pidless_preserves_live(tmp_path: Path):
    """#8659: release(pid=None) must preserve claims of a live replacement run."""
    import sqlite3
    import time

    ledger_path = tmp_path / "own.sqlite3"
    ledger = OwnershipLedger(ledger_path)
    task_id = "test-task"

    conn = sqlite3.connect(ledger_path)
    conn.execute(
        "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
    )
    # Stale/dead PID claim
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/a.py"}', 999_999_999, time.time() - 100),
    )
    # Stale/NULL PID claim
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/b.py"}', None, time.time() - 100),
    )
    # Live PID replacement claim
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/c.py"}', os.getpid(), time.time()),
    )
    conn.commit()
    conn.close()

    # PID-less release cleans NULL and dead PIDs, preserves live PID
    ledger.release(task_id, pid=None)

    conn = sqlite3.connect(ledger_path)
    rows = conn.execute("SELECT pid, claim_json FROM write_claims WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    assert len(rows) == 1
    assert rows[0][0] == os.getpid()
    assert "scripts/c.py" in rows[0][1]

    # Explicit PID release cleans only matching PID
    ledger.release(task_id, pid=os.getpid())
    conn = sqlite3.connect(ledger_path)
    rows = conn.execute("SELECT pid, claim_json FROM write_claims WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    assert len(rows) == 0


def test_reconciliation_distinguishes_verified_replacement_from_recycled_pid(tmp_path: Path):
    """#8659 / CF r5 F1: Beyond-grace reconciliation preserves verified replacement runs and cleans recycled PIDs."""
    import sqlite3
    import time

    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    task_id = "test-task"
    (state_dir / f"{task_id}.json").write_text(
        json.dumps({"status": "failed", "pid": None}), encoding="utf-8"
    )

    # 1. Verified replacement run: matcher confirms process identity
    ledger_path_1 = tmp_path / "own1.sqlite3"
    ledger_1 = OwnershipLedger(
        ledger_path_1,
        task_state_dir=state_dir,
        process_matches_task=lambda p, tid: p == os.getpid() and tid == task_id,
    )
    conn = sqlite3.connect(ledger_path_1)
    conn.execute(
        "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
    )
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/c.py"}', os.getpid(), time.time() - 200),
    )
    conn.commit()
    conn.close()

    res1 = ledger_1.admit(
        task_id="challenger",
        mode="workspace-write",
        owned_paths=["scripts/c.py"],
        pid=os.getpid(),
    )
    assert res1.admitted is False
    assert res1.would_refuse is True

    conn = sqlite3.connect(ledger_path_1)
    rows1 = conn.execute("SELECT pid FROM write_claims WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    assert len(rows1) == 1

    # 2. Recycled PID: process is alive (e.g. os.getpid()) but matcher rejects (unrelated process)
    ledger_path_2 = tmp_path / "own2.sqlite3"
    ledger_2 = OwnershipLedger(
        ledger_path_2,
        task_state_dir=state_dir,
        process_matches_task=lambda _p, _tid: False,
    )
    conn = sqlite3.connect(ledger_path_2)
    conn.execute(
        "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
    )
    conn.execute(
        "INSERT INTO write_claims VALUES (?,?,?,?)",
        (task_id, '{"kind":"file","norm":"scripts/c.py"}', os.getpid(), time.time() - 200),
    )
    conn.commit()
    conn.close()

    res2 = ledger_2.admit(
        task_id="challenger",
        mode="workspace-write",
        owned_paths=["scripts/c.py"],
        pid=os.getpid(),
    )
    assert res2.admitted is True
    assert res2.would_refuse is False

    conn = sqlite3.connect(ledger_path_2)
    rows2 = conn.execute("SELECT pid FROM write_claims WHERE task_id = ?", (task_id,)).fetchall()
    conn.close()
    assert len(rows2) == 0


_EXEC_HANDSHAKE_TIMEOUT_S = 10.0


def _spawn_execd_sleeper(
    *,
    env: dict[str, str],
    cwd: str | None = None,
    timeout_s: float = _EXEC_HANDSHAKE_TIMEOUT_S,
):
    """Spawn a sleeper and return only after its new image is running.

    #9808: ``Popen`` returns only after its exec-status pipe closes. Linux
    closes that close-on-exec descriptor in ``begin_new_exec``, before the
    new image's argument and environment pointers are installed, so a live
    pid can have a readable but empty ``/proc/<pid>/environ`` and ``cmdline``.
    That window is unknown identity, not the parent image. The child writes
    one byte only after the new image is running; this blocks on that byte
    with a bounded ``select``.
    """
    import select
    import subprocess
    import sys
    import time

    read_fd, write_fd = os.pipe()
    proc = None
    try:
        os.set_inheritable(write_fd, True)
        script = f"import os, time\nos.write({write_fd}, b'1')\nos.close({write_fd})\ntime.sleep(30)\n"
        proc = subprocess.Popen(
            [sys.executable, "-c", script],
            env=env,
            cwd=cwd,
            pass_fds=(write_fd,),
        )
        os.close(write_fd)
        write_fd = -1
        deadline = time.monotonic() + timeout_s
        got = b""
        while b"1" not in got:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or proc.poll() is not None:
                raise AssertionError(
                    f"child pid {proc.pid} did not signal exec within {timeout_s}s (returncode={proc.poll()})"
                )
            readable, _, _ = select.select([read_fd], [], [], remaining)
            if not readable:
                raise AssertionError(f"child pid {proc.pid} did not signal exec within {timeout_s}s")
            chunk = os.read(read_fd, 16)
            if not chunk:
                raise AssertionError(f"child pid {proc.pid} closed the exec handshake (returncode={proc.poll()})")
            got += chunk
        return proc
    except BaseException:
        # KeyboardInterrupt and other BaseExceptions skip ``except Exception``
        # and used to leave the sleeper running.
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        raise
    finally:
        if write_fd >= 0:
            os.close(write_fd)
        os.close(read_fd)


def test_pid_matches_task_real_process_identity(tmp_path: Path):
    """#8659 / CF r5 F1: Verify _pid_matches_task using real subprocesses with environ/cmdline.

    #9808: both children are sampled only after the new image signals. The
    window after ``Popen`` returns can show empty ``environ`` and ``cmdline``;
    that is unknown identity, not a parent-image mismatch.
    """
    import sqlite3
    import time

    from scripts.guardrails.delegate_ownership import _pid_matches_task

    task_id = "real-worker-task"
    spawned: list = []
    try:
        # Register each child before the next spawn so a failed handshake
        # cannot leave the earlier child running.
        worker = _spawn_execd_sleeper(
            env={**os.environ, "LEARN_UKRAINIAN_DISPATCH_TASK_ID": task_id},
        )
        spawned.append(worker)
        dummy = _spawn_execd_sleeper(
            env={k: v for k, v in os.environ.items() if "TASK_ID" not in k},
        )
        spawned.append(dummy)

        assert _pid_matches_task(worker.pid, task_id) is True
        assert _pid_matches_task(worker.pid, "other-task") is False
        assert _pid_matches_task(dummy.pid, task_id) is False

        # Now test OwnershipLedger default matcher with real processes
        state_dir = tmp_path / "tasks"
        state_dir.mkdir()
        (state_dir / f"{task_id}.json").write_text(
            json.dumps({"status": "failed", "pid": None}), encoding="utf-8"
        )

        ledger_path = tmp_path / "own_real.sqlite3"
        ledger = OwnershipLedger(ledger_path, task_state_dir=state_dir)
        conn = sqlite3.connect(ledger_path)
        conn.execute(
            "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
        )
        # 1. Test recycled PID cleanup with dummy process
        conn.execute(
            "INSERT INTO write_claims VALUES (?,?,?,?)",
            (task_id, '{"kind":"file","norm":"scripts/c.py"}', dummy.pid, time.time() - 200),
        )
        conn.commit()

        challenger = ledger.admit(
            task_id="challenger-1",
            mode="workspace-write",
            owned_paths=["scripts/c.py"],
            pid=worker.pid,
        )
        assert challenger.admitted is True

        # 2. Test verified replacement worker preservation
        conn.execute(
            "INSERT INTO write_claims VALUES (?,?,?,?)",
            (task_id, '{"kind":"file","norm":"scripts/d.py"}', worker.pid, time.time() - 200),
        )
        conn.commit()
        conn.close()

        challenger_blocked = ledger.admit(
            task_id="challenger-2",
            mode="workspace-write",
            owned_paths=["scripts/d.py"],
            pid=dummy.pid,
        )
        assert challenger_blocked.admitted is False
        assert challenger_blocked.would_refuse is True
    finally:
        for proc in spawned:
            proc.terminate()
            proc.wait()


def _stub_task_proc(
    root: Path,
    pid: int,
    *,
    environ: bytes,
    cmdline: bytes,
    cwd: Path,
) -> Path:
    """A ``proc_root`` whose ``<pid>`` files are the supplied bytes and cwd symlink."""
    proc_dir = root / str(pid)
    proc_dir.mkdir(parents=True)
    (proc_dir / "environ").write_bytes(environ)
    (proc_dir / "cmdline").write_bytes(cmdline)
    (proc_dir / "cwd").symlink_to(cwd)
    return root


def test_pid_matches_task_empty_exec_window_is_unknown(tmp_path: Path):
    """#9808: readable but empty environ/cmdline are unknown identity, not a mismatch.

    Models the window ``Popen`` can observe. Linux closes the exec-status
    pipe in ``begin_new_exec`` before the new image's argument and
    environment pointers are installed, so a live pid's ``environ`` and
    ``cmdline`` read back empty. That is unavailable evidence (``None``)
    unless another probe matches. Populated non-matching evidence is still
    a confirmed mismatch (``False``).
    """
    from scripts.guardrails.delegate_ownership import _pid_matches_task

    task_id = "exec-window-9808"
    pid = os.getpid()
    neutral = tmp_path / "neutral-cwd"
    neutral.mkdir()
    matched = tmp_path / task_id
    matched.mkdir()
    assert task_id not in neutral.resolve().parts

    empty = _stub_task_proc(tmp_path / "empty-proc", pid, environ=b"", cmdline=b"", cwd=neutral)
    assert _pid_matches_task(pid, task_id, proc_root=empty) is None

    # A cmdline of only NULs has no non-empty parts: same unavailable evidence.
    nul_cmd = _stub_task_proc(tmp_path / "nul-cmd-proc", pid, environ=b"", cmdline=b"\0\0", cwd=neutral)
    assert _pid_matches_task(pid, task_id, proc_root=nul_cmd) is None

    # Each empty probe is unavailable on its own.
    empty_env = _stub_task_proc(
        tmp_path / "empty-env-proc",
        pid,
        environ=b"",
        cmdline=b"sleeper\0--idle\0",
        cwd=neutral,
    )
    assert _pid_matches_task(pid, task_id, proc_root=empty_env) is None
    empty_cmd = _stub_task_proc(
        tmp_path / "empty-cmd-proc",
        pid,
        environ=b"PATH=/usr/bin\0LANG=C\0",
        cmdline=b"",
        cwd=neutral,
    )
    assert _pid_matches_task(pid, task_id, proc_root=empty_cmd) is None

    populated = _stub_task_proc(
        tmp_path / "populated-proc",
        pid,
        environ=b"PATH=/usr/bin\0LANG=C\0",
        cmdline=b"sleeper\0--idle\0",
        cwd=neutral,
    )
    assert _pid_matches_task(pid, task_id, proc_root=populated) is False

    # Empty identity probes do not hide a positive match from another probe.
    by_cmd = _stub_task_proc(
        tmp_path / "cmd-match-proc",
        pid,
        environ=b"",
        cmdline=b"python\0--task-id\0" + task_id.encode() + b"\0",
        cwd=neutral,
    )
    assert _pid_matches_task(pid, task_id, proc_root=by_cmd) is True
    by_cwd = _stub_task_proc(tmp_path / "cwd-match-proc", pid, environ=b"", cmdline=b"", cwd=matched)
    assert _pid_matches_task(pid, task_id, proc_root=by_cwd) is True


def test_pid_matches_task_unknown_proc_preserves_claim(tmp_path: Path):
    """#8659 / CF r6 F1 & CF r7 F1: Unavailable evidence or denied /proc inspection preserves claims."""
    import sqlite3
    import time
    from unittest.mock import patch

    from scripts.guardrails.delegate_ownership import _pid_matches_task

    task_id = "unknown-proc-task"

    # Spawn live worker process carrying task marker
    worker = _spawn_execd_sleeper(
        env={**os.environ, "LEARN_UKRAINIAN_DISPATCH_TASK_ID": task_id},
    )

    try:
        # 1. Missing /proc root or PermissionError on proc_root -> returns None
        missing_proc = tmp_path / "nonexistent_proc"
        assert _pid_matches_task(worker.pid, task_id, proc_root=missing_proc) is None
        with patch.object(Path, "is_dir", side_effect=PermissionError("Permission denied on /proc")):
            assert _pid_matches_task(worker.pid, task_id) is None

        # 2. Denied inspection (PermissionError) -> returns None
        with patch("pathlib.Path.read_bytes", side_effect=PermissionError("Permission denied")):
            with patch("os.readlink", side_effect=PermissionError("Permission denied")):
                assert _pid_matches_task(worker.pid, task_id) is None

        # 3. Reviewer R7 probe: FileNotFoundError on environ while worker is alive -> returns None
        # and default OwnershipLedger matcher preserves claim and refuses challenger
        with patch.object(Path, "read_bytes", side_effect=FileNotFoundError("No such file: environ")):
            assert _pid_matches_task(worker.pid, task_id) is None

            state_dir = tmp_path / "tasks"
            state_dir.mkdir(exist_ok=True)
            (state_dir / f"{task_id}.json").write_text(
                json.dumps({"status": "failed", "pid": None}), encoding="utf-8"
            )

            ledger_path = tmp_path / "own_fnf.sqlite3"
            ledger = OwnershipLedger(ledger_path, task_state_dir=state_dir)
            conn = sqlite3.connect(ledger_path)
            conn.execute(
                "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
            )
            conn.execute(
                "INSERT INTO write_claims VALUES (?,?,?,?)",
                (task_id, '{"kind":"file","norm":"scripts/fnf.py"}', worker.pid, time.time() - 200),
            )
            conn.commit()

            challenger = ledger.admit(
                task_id="challenger-fnf",
                mode="workspace-write",
                owned_paths=["scripts/fnf.py"],
                pid=worker.pid,
            )
            assert challenger.admitted is False
            assert challenger.would_refuse is True
            # Claim remains in database
            rows = conn.execute("SELECT COUNT(*) FROM write_claims WHERE task_id = ?", (task_id,)).fetchone()
            assert rows[0] == 1
            conn.close()

        # 4. Unavailable cwd (e.g. /proc/<pid>/cwd vanishes or readlink fails with FileNotFoundError) -> returns None
        with patch("os.readlink", side_effect=FileNotFoundError("No such file: cwd")):
            with patch.object(Path, "read_bytes", side_effect=FileNotFoundError("No such file: environ")):
                assert _pid_matches_task(worker.pid, task_id) is None

        # 5. Cwd resolution failure (cwd_path.resolve() raises OSError) -> returns None
        with patch.object(Path, "resolve", side_effect=OSError("Resolution error")):
            assert _pid_matches_task(worker.pid, "other-task") is None

        # 6. Confirmed death: if process is dead, FileNotFoundError on probe returns False
        with patch("scripts.guardrails.delegate_ownership._pid_alive", return_value=False):
            assert _pid_matches_task(worker.pid, task_id) is False
    finally:
        worker.terminate()
        worker.wait()


def test_pid_matches_task_cwd_exact_component_negative_prefix_suffix(tmp_path: Path):
    """#8659 / CF r6 F2: Working-directory matching rejects prefix/suffix substrings and preserves genuine worktrees."""
    import sqlite3
    import time

    from scripts.guardrails.delegate_ownership import _pid_matches_task

    task_id = "target-task-8659"

    # Set up directories
    unrelated_dir = tmp_path / f"{task_id}-unrelated"
    unrelated_dir.mkdir()
    prefix_dir = tmp_path / f"prefix-{task_id}"
    prefix_dir.mkdir()
    genuine_dir = tmp_path / task_id
    genuine_dir.mkdir()

    clean_env = {k: v for k, v in os.environ.items() if "TASK_ID" not in k}

    # The handshake returns only after the new image is running, so cwd is
    # the requested directory. Register each child before the next spawn.
    spawned: list = []
    try:
        p_unrelated = _spawn_execd_sleeper(env=clean_env, cwd=str(unrelated_dir))
        spawned.append(p_unrelated)
        p_prefix = _spawn_execd_sleeper(env=clean_env, cwd=str(prefix_dir))
        spawned.append(p_prefix)
        p_genuine = _spawn_execd_sleeper(env=clean_env, cwd=str(genuine_dir))
        spawned.append(p_genuine)

        # Direct _pid_matches_task checks
        assert _pid_matches_task(p_unrelated.pid, task_id) is False
        assert _pid_matches_task(p_prefix.pid, task_id) is False
        assert _pid_matches_task(p_genuine.pid, task_id) is True

        # OwnershipLedger integration
        state_dir = tmp_path / "tasks"
        state_dir.mkdir()
        (state_dir / f"{task_id}.json").write_text(
            json.dumps({"status": "failed", "pid": None, "worktree_path": str(genuine_dir)}),
            encoding="utf-8",
        )

        ledger_path = tmp_path / "own_cwd.sqlite3"
        ledger = OwnershipLedger(ledger_path, task_state_dir=state_dir)
        conn = sqlite3.connect(ledger_path)
        conn.execute(
            "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
        )
        conn.commit()

        # 1. Negative suffix cwd (<task-id>-unrelated): stale claim cleaned up, challenger admitted
        conn.execute(
            "INSERT INTO write_claims VALUES (?,?,?,?)",
            (task_id, '{"kind":"file","norm":"scripts/suf.py"}', p_unrelated.pid, time.time() - 200),
        )
        conn.commit()
        ch_suf = ledger.admit(
            task_id="challenger-suf",
            mode="workspace-write",
            owned_paths=["scripts/suf.py"],
            pid=p_genuine.pid,
        )
        assert ch_suf.admitted is True

        # 2. Negative prefix cwd (prefix-<task-id>): stale claim cleaned up, challenger admitted
        conn.execute(
            "INSERT INTO write_claims VALUES (?,?,?,?)",
            (task_id, '{"kind":"file","norm":"scripts/pre.py"}', p_prefix.pid, time.time() - 200),
        )
        conn.commit()
        ch_pre = ledger.admit(
            task_id="challenger-pre",
            mode="workspace-write",
            owned_paths=["scripts/pre.py"],
            pid=p_genuine.pid,
        )
        assert ch_pre.admitted is True

        # 3. Genuine worktree cwd: claim preserved, challenger refused
        conn.execute(
            "INSERT INTO write_claims VALUES (?,?,?,?)",
            (task_id, '{"kind":"file","norm":"scripts/gen.py"}', p_genuine.pid, time.time() - 200),
        )
        conn.commit()
        conn.close()

        ch_gen = ledger.admit(
            task_id="challenger-gen",
            mode="workspace-write",
            owned_paths=["scripts/gen.py"],
            pid=p_unrelated.pid,
        )
        assert ch_gen.admitted is False
        assert ch_gen.would_refuse is True
    finally:
        for proc in spawned:
            proc.terminate()
            proc.wait()
