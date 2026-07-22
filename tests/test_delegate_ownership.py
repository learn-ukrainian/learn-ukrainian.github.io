"""Tests for scripts/delegate_ownership.py (#5643 Δ2-A WARN)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.delegate_ownership import (
    ClaimKind,
    GuardMode,
    OwnershipLedger,
    admit_write_paths,
    claims_conflict,
    normalize_claim,
)


def test_normalize_file_subtree_unknown():
    assert normalize_claim("scripts/delegate.py").kind == ClaimKind.FILE
    assert normalize_claim("scripts/").kind == ClaimKind.SUBTREE
    assert normalize_claim("scripts/**").kind == ClaimKind.SUBTREE
    assert normalize_claim("scripts/**/*.py").kind == ClaimKind.UNKNOWN
    assert normalize_claim("../escape").kind == ClaimKind.UNKNOWN


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
    result = admit_write_paths(
        task_id="solo",
        mode="workspace-write",
        owned_paths=[],
        ledger_path=ledger,
        task_state_dir=tmp_path,
    )
    assert result.admitted is True
    assert result.would_refuse is False


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


def test_file_subtree_and_sibling_disjoint(tmp_path: Path):
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    (state_dir / "h.json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )
    admit_write_paths(
        task_id="h",
        mode="danger",
        owned_paths=["pkg/"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    # file inside subtree conflicts
    inside = admit_write_paths(
        task_id="in",
        mode="danger",
        owned_paths=["pkg/mod.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert inside.would_refuse is True
    # sibling disjoint
    sib = admit_write_paths(
        task_id="sib",
        mode="danger",
        owned_paths=["other/"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    assert sib.would_refuse is False


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


def test_simultaneous_admission_one_conflict_visible(tmp_path: Path):
    """Under BEGIN IMMEDIATE, sequential contenders see each other's claims."""
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    for tid in ("a", "b"):
        (state_dir / f"{tid}.json").write_text(
            json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
        )
    r1 = admit_write_paths(
        task_id="a",
        mode="workspace-write",
        owned_paths=["race.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.REFUSE,
    )
    r2 = admit_write_paths(
        task_id="b",
        mode="workspace-write",
        owned_paths=["race.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.REFUSE,
    )
    assert r1.admitted is True
    assert r2.admitted is False


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


def test_active_unknown_claim_makes_later_concrete_unprovable(tmp_path: Path):
    """Active wildcard claim blocks proof of disjointness for later writers (CF r2)."""
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    (state_dir / "wild.json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )
    admit_write_paths(
        task_id="wild",
        mode="workspace-write",
        owned_paths=["scripts/**/*.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    later = admit_write_paths(
        task_id="concrete",
        mode="workspace-write",
        owned_paths=["scripts/delegate.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.WARN,
    )
    assert later.admitted is True
    assert later.would_refuse is True


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
