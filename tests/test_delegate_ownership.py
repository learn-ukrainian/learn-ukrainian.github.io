"""Tests for scripts/guardrails/delegate_ownership.py (#5643 Δ2-A WARN)."""

from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path

from scripts.guardrails.delegate_ownership import (
    ClaimKind,
    GuardMode,
    OwnershipLedger,
    _safe_task_state_name,
    admit_write_paths,
    claims_conflict,
    env_guard_mode,
    normalize_claim,
    refusal_message,
    sanitize_for_display,
)


def test_normalize_file_subtree_unknown():
    assert normalize_claim("scripts/delegate.py").kind == ClaimKind.FILE
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


def test_env_guard_mode_defaults_to_refuse(monkeypatch):
    monkeypatch.delenv("DELEGATE_OWNERSHIP_MODE", raising=False)
    assert env_guard_mode() is GuardMode.REFUSE


def test_env_guard_mode_warn_opt_in(monkeypatch):
    monkeypatch.setenv("DELEGATE_OWNERSHIP_MODE", "warn")
    assert env_guard_mode() is GuardMode.WARN


def test_env_guard_mode_unknown_fails_closed_to_refuse(monkeypatch):
    monkeypatch.setenv("DELEGATE_OWNERSHIP_MODE", "maybe")
    assert env_guard_mode() is GuardMode.REFUSE


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


def test_ownership_ledger_default_mode_follows_env(
    tmp_path: Path, monkeypatch
) -> None:
    """Default mode follows env; paths must stay tmp-scoped (CF #5662 r4 P2)."""
    monkeypatch.delenv("DELEGATE_OWNERSHIP_MODE", raising=False)
    ledger = tmp_path / "own.sqlite3"
    state = tmp_path / "tasks"
    assert (
        OwnershipLedger(ledger, task_state_dir=state).mode is GuardMode.REFUSE
    )
    monkeypatch.setenv("DELEGATE_OWNERSHIP_MODE", "warn")
    assert OwnershipLedger(ledger, task_state_dir=state).mode is GuardMode.WARN
    assert (
        OwnershipLedger(ledger, task_state_dir=state, mode=GuardMode.REFUSE).mode
        is GuardMode.REFUSE
    )


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
    assert "--research-owned-path" in reason and "--allow-path-overlap" in reason, reason


def test_real_conflict_refusal_still_reads_as_a_conflict(tmp_path: Path):
    """The genuine-overlap message keeps its name and points at the shared path."""
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    (state_dir / "holder.json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )
    admit_write_paths(
        task_id="holder",
        mode="workspace-write",
        owned_paths=["scripts/shared.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
    )
    blocked = admit_write_paths(
        task_id="challenger",
        mode="workspace-write",
        owned_paths=["scripts/shared.py"],
        pid=pid,
        ledger_path=ledger,
        task_state_dir=state_dir,
        guard_mode=GuardMode.REFUSE,
    )
    assert blocked.admitted is False
    assert blocked.conflicts
    assert "path ownership conflict" in blocked.reason
    assert "scripts/shared.py" in blocked.reason
    assert "holder" in blocked.reason


def test_refusal_message_escapes_untrusted_task_ids_and_paths():
    """Ledger-sourced text is untrusted: it must not forge operator output.

    CF review of #5804: a task id containing a newline printed a second line that
    read as the guard itself speaking ("OPERATOR: override granted").
    """
    evil_task = "evil\n❌ OPERATOR: override granted"
    evil_path = "scripts/a.py\x1b[31m\rSAFE TO MERGE"

    unprovable = refusal_message(
        conflicts=[],
        unprovable_peers=[{"other_task_id": evil_task, "other_pid": 42}],
        self_unprovable=False,
        unknown=[],
    )
    conflict = refusal_message(
        conflicts=[
            {
                "other_task_id": "peer",
                "other_pid": 7,
                "other_claim": {"raw": evil_path, "kind": "file", "norm": evil_path},
            }
        ],
        unprovable_peers=[],
        self_unprovable=False,
        unknown=[],
    )
    for message in (unprovable, conflict):
        assert "\n" not in message and "\r" not in message, repr(message)
        assert "\x1b" not in message, repr(message)
    assert "\\x0a" in unprovable  # escaped, not silently dropped
    assert "\\x1b" in conflict and "\\x0d" in conflict

    # Length-bounded so one absurd claim cannot bury the message.
    assert len(sanitize_for_display("x" * 5000)) <= 120

    # Beyond ASCII: a bidi override would visually reverse the rest of the line
    # even though it is not a C0 control character.
    bidi = sanitize_for_display("safe\u202eevil")
    assert "\u202e" not in bidi and "\\u202e" in bidi, bidi
    assert sanitize_for_display("zero\u200bwidth").count("\\u200b") == 1
    # Ordinary non-ASCII text must survive untouched — Ukrainian paths are normal.
    assert sanitize_for_display("данні/слово.md") == "данні/слово.md"


def test_sanitizer_escapes_unicode_line_separators():
    """U+2028/U+2029 are not control CATEGORIES but do render as line breaks.

    CF re-review of #5804 (F001): escaping only Cc/Cf/Cs/Co left the forged-line
    hole open for a task id carrying a LINE SEPARATOR.
    """
    for sep, code in (("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        rendered = sanitize_for_display(f"before{sep}after")
        assert sep not in rendered, repr(rendered)
        assert code in rendered, repr(rendered)
        message = refusal_message(
            conflicts=[],
            unprovable_peers=[
                {"other_task_id": f"evil{sep}❌ OPERATOR: all clear", "other_pid": 9}
            ],
            self_unprovable=False,
            unknown=[],
        )
        assert sep not in message, repr(message)


def test_every_admission_reason_is_display_safe(tmp_path: Path):
    """INVARIANT: AdmissionResult.reason is safe to print, on every path.

    delegate.py prints `ownership.reason` directly, so a reason built anywhere in
    this module must never carry raw control or line-separator characters. Today
    the non-refusal reasons interpolate only pids and mode names, and the refusal
    reasons route through the sanitizer — this test is what keeps that true when
    someone later adds a reason string with a task id in it.

    (A cross-family reviewer suspected a hole here. There is none — the same-task
    race reasons interpolate `other_pid` only, and delegate.py prints task ids via
    `!r`, whose repr escapes LF/CR/NEL/U+2028/U+2029/ESC. This test pins both.)
    """
    hostile = "evil ❌ OPERATOR: all clearx\x1b[31m y\n"
    unsafe = {"Cc", "Cf", "Cs", "Co", "Zl", "Zp"}
    ledger = tmp_path / "own.sqlite3"
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    pid = os.getpid()
    (state_dir / _safe_task_state_name(hostile)).with_suffix(".json").write_text(
        json.dumps({"status": "running", "pid": pid}), encoding="utf-8"
    )

    results = [
        admit_write_paths(
            task_id=hostile, mode="read-only", owned_paths=[hostile],
            ledger_path=ledger, task_state_dir=state_dir,
        ),
        admit_write_paths(
            task_id=hostile, mode="workspace-write", owned_paths=[hostile],
            pid=pid, ledger_path=ledger, task_state_dir=state_dir,
        ),
        admit_write_paths(
            task_id="peer", mode="workspace-write", owned_paths=[hostile],
            pid=pid, ledger_path=ledger, task_state_dir=state_dir,
            guard_mode=GuardMode.REFUSE,
        ),
        admit_write_paths(
            task_id="peer2", mode="workspace-write", owned_paths=[],
            pid=pid, ledger_path=ledger, task_state_dir=state_dir,
            guard_mode=GuardMode.WARN,
        ),
    ]

    # The same-task/different-live-PID race branch needs a SECOND live pid, or it
    # is never entered — the reviewer noticed the first version of this test only
    # claimed to cover it. The parent process is live and is not us.
    other_live_pid = os.getppid()
    race_state = tmp_path / "race"
    race_state.mkdir()
    race_ledger = tmp_path / "race.sqlite3"
    (race_state / _safe_task_state_name(hostile)).with_suffix(".json").write_text(
        json.dumps({"status": "running", "pid": other_live_pid}), encoding="utf-8"
    )
    admit_write_paths(
        task_id=hostile, mode="workspace-write", owned_paths=[hostile],
        pid=other_live_pid, ledger_path=race_ledger, task_state_dir=race_state,
    )
    for mode in (GuardMode.REFUSE, GuardMode.WARN):
        raced = admit_write_paths(
            task_id=hostile, mode="workspace-write", owned_paths=[hostile],
            pid=pid, ledger_path=race_ledger, task_state_dir=race_state,
            guard_mode=mode,
        )
        assert "pid" in raced.reason  # proves we entered the same-task race branch
        assert str(other_live_pid) in raced.reason
        results.append(raced)
    for result in results:
        bad = [c for c in result.reason if unicodedata.category(c) in unsafe]
        assert not bad, (result.reason, [hex(ord(c)) for c in bad])

    # And the way delegate.py renders a task id is itself escaping.
    rendered = f"task_id={hostile!r}"
    assert "\n" not in rendered and " " not in rendered and "\x1b" not in rendered


def test_sanitizer_never_truncates_mid_escape():
    """The length bound must cut between escape units, not inside one.

    CF re-review of #5804 (F002): slicing the joined string turned a trailing
    "\\u202e" into a lone backslash — a value the operator cannot match against
    anything real.
    """
    limit = 20
    # A bidi override lands exactly on the boundary: its 6-char escape cannot fit.
    value = "x" * (limit - 2) + "\u202e" + "tail"
    rendered = sanitize_for_display(value, limit=limit)
    assert len(rendered) <= limit, (len(rendered), rendered)
    assert rendered.endswith("…")
    body = rendered[:-1]
    assert not body.endswith("\\"), rendered
    # Any backslash still present must head a COMPLETE escape unit.
    for idx, ch in enumerate(body):
        if ch == "\\":
            tail = body[idx:]
            assert re.match(r"\\x[0-9a-f]{2}|\\u[0-9a-f]{4}", tail), rendered

    # Degenerate budget: a single unit wider than the whole limit yields only
    # the ellipsis rather than a corrupted fragment.
    assert sanitize_for_display("\u202e", limit=3) == "…"


def test_refusal_message_counts_peers_not_claim_rows():
    """One agent holding four claims is ONE blocker (CF review of #5804)."""
    rows = [
        {"other_task_id": "busy", "other_pid": 333, "other_claim": {"norm": "*"}}
        for _ in range(4)
    ]
    message = refusal_message(
        conflicts=[], unprovable_peers=rows, self_unprovable=False, unknown=[]
    )
    assert message.count("busy(pid 333)") == 1, message
    assert "more" not in message.split("No actual path overlap")[0], message

    # Four DISTINCT peers still truncate honestly at three.
    distinct = [
        {"other_task_id": f"peer{i}", "other_pid": 100 + i, "other_claim": {"norm": "*"}}
        for i in range(4)
    ]
    many = refusal_message(
        conflicts=[], unprovable_peers=distinct, self_unprovable=False, unknown=[]
    )
    assert "(+1 more)" in many, many

    # Conflicts group paths under their peer instead of repeating the peer.
    overlaps = [
        {
            "other_task_id": "one",
            "other_pid": 777,
            "other_claim": {"norm": f"scripts/f{i}.py"},
        }
        for i in range(4)
    ]
    conflict = refusal_message(
        conflicts=overlaps, unprovable_peers=[], self_unprovable=False, unknown=[]
    )
    assert conflict.count("one(pid 777)") == 1, conflict
    assert "(+2 more paths)" in conflict, conflict


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


def test_pid_matches_task_real_process_identity(tmp_path: Path):
    """#8659 / CF r5 F1: Verify _pid_matches_task using real subprocesses with environ/cmdline."""
    import sqlite3
    import subprocess
    import sys
    import time

    from scripts.guardrails.delegate_ownership import _pid_matches_task

    task_id = "real-worker-task"

    # Spawn real worker subprocess carrying task identity in environ
    worker = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        env={**os.environ, "LEARN_UKRAINIAN_DISPATCH_TASK_ID": task_id},
    )
    # Spawn dummy subprocess carrying no task identity
    dummy = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        env={k: v for k, v in os.environ.items() if "TASK_ID" not in k},
    )

    try:
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
        worker.terminate()
        worker.wait()
        dummy.terminate()
        dummy.wait()


def test_pid_matches_task_unknown_proc_preserves_claim(tmp_path: Path):
    """#8659 / CF r6 F1 & CF r7 F1: Unavailable evidence or denied /proc inspection preserves claims."""
    import sqlite3
    import subprocess
    import sys
    import time
    from unittest.mock import patch

    from scripts.guardrails.delegate_ownership import _pid_matches_task

    task_id = "unknown-proc-task"

    # Spawn live worker process carrying task marker
    worker = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
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
    import subprocess
    import sys
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

    # Spawn processes in each directory without task marker in env or cmdline
    p_unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=str(unrelated_dir),
        env=clean_env,
    )
    p_prefix = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=str(prefix_dir),
        env=clean_env,
    )
    p_genuine = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=str(genuine_dir),
        env=clean_env,
    )

    try:
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
        for p in (p_unrelated, p_prefix, p_genuine):
            p.terminate()
            p.wait()


def test_pid_matches_task_deleted_cwd_preserves_claim(tmp_path: Path):
    """#8659 / CF r8 F1: Removed process cwd evidence is treated as unknown and preserves claims."""
    import sqlite3
    import subprocess
    import sys
    import time

    from scripts.guardrails.delegate_ownership import _pid_matches_task

    task_id = "deleted-cwd-task"

    # Directory for the process cwd
    target_dir = tmp_path / "worktrees" / task_id
    target_dir.mkdir(parents=True)

    # Spawn real process with marker-free environment and command line
    clean_env = {k: v for k, v in os.environ.items() if "TASK_ID" not in k}
    p = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=str(target_dir),
        env=clean_env,
    )

    try:
        # Before removal: cwd matches task_id exactly
        assert _pid_matches_task(p.pid, task_id) is True

        # Delete process cwd on disk while process remains alive
        target_dir.rmdir()

        # After removal: Linux /proc/<pid>/cwd is marked "(deleted)" or fails resolution strict
        # With marker-free env/cmdline, the matcher must return None (unknown identity), not False!
        assert _pid_matches_task(p.pid, task_id) is None

        # OwnershipLedger integration with claim older than admission grace period
        state_dir = tmp_path / "tasks"
        state_dir.mkdir(exist_ok=True)
        (state_dir / f"{task_id}.json").write_text(
            json.dumps({"status": "failed", "pid": None, "worktree_path": str(target_dir)}),
            encoding="utf-8",
        )

        ledger_path = tmp_path / "own_del_cwd.sqlite3"
        ledger = OwnershipLedger(ledger_path, task_state_dir=state_dir)
        conn = sqlite3.connect(ledger_path)
        conn.execute(
            "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
        )
        conn.execute(
            "INSERT INTO write_claims VALUES (?,?,?,?)",
            (task_id, '{"kind":"file","norm":"scripts/del.py"}', p.pid, time.time() - 200),
        )
        conn.commit()

        # Challenger must be refused because unknown process identity preserves protection
        challenger = ledger.admit(
            task_id="challenger-del",
            mode="workspace-write",
            owned_paths=["scripts/del.py"],
            pid=os.getpid(),
        )
        assert challenger.admitted is False
        assert challenger.would_refuse is True

        # Claim remains in database
        rows = conn.execute("SELECT COUNT(*) FROM write_claims WHERE task_id = ?", (task_id,)).fetchone()
        assert rows[0] == 1
        conn.close()
    finally:
        p.terminate()
        p.wait()


def test_pid_matches_task_worktree_resolution_error_preserves_claim(tmp_path: Path):
    """#8659 / CF r9 F1: Unavailable worktree_path resolution (FileNotFoundError/PermissionError) preserves claims."""
    import sqlite3
    import subprocess
    import sys
    import time
    from unittest.mock import patch

    from scripts.guardrails.delegate_ownership import _pid_matches_task

    task_id = "wt-res-task"
    cwd_dir = tmp_path / "generic_cwd"
    cwd_dir.mkdir()

    # Marker-free environment and command line: environ and cmdline read cleanly without matching
    clean_env = {k: v for k, v in os.environ.items() if "TASK_ID" not in k}
    p = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=str(cwd_dir),
        env=clean_env,
    )

    try:
        # 1. worktree_path resolution raises FileNotFoundError
        missing_wt = tmp_path / "missing_worktree"
        assert _pid_matches_task(p.pid, task_id, worktree_path=missing_wt) is None

        # 2. worktree_path resolution raises PermissionError
        with patch.object(Path, "resolve", side_effect=PermissionError("Permission denied on worktree")):
            assert _pid_matches_task(p.pid, task_id, worktree_path=tmp_path / "denied_wt") is None

        # 3. OwnershipLedger integration with FileNotFoundError on worktree_path
        state_dir = tmp_path / "tasks"
        state_dir.mkdir(exist_ok=True)
        (state_dir / f"{task_id}.json").write_text(
            json.dumps({"status": "failed", "pid": None, "worktree_path": str(missing_wt)}),
            encoding="utf-8",
        )

        ledger_path_fnf = tmp_path / "own_wt_fnf.sqlite3"
        ledger_fnf = OwnershipLedger(ledger_path_fnf, task_state_dir=state_dir)
        conn_fnf = sqlite3.connect(ledger_path_fnf)
        conn_fnf.execute(
            "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
        )
        conn_fnf.execute(
            "INSERT INTO write_claims VALUES (?,?,?,?)",
            (task_id, '{"kind":"file","norm":"scripts/wt_fnf.py"}', p.pid, time.time() - 200),
        )
        conn_fnf.commit()

        ch_fnf = ledger_fnf.admit(
            task_id="challenger-wt-fnf",
            mode="workspace-write",
            owned_paths=["scripts/wt_fnf.py"],
            pid=os.getpid(),
        )
        assert ch_fnf.admitted is False
        assert ch_fnf.would_refuse is True
        rows_fnf = conn_fnf.execute("SELECT COUNT(*) FROM write_claims WHERE task_id = ?", (task_id,)).fetchone()
        assert rows_fnf[0] == 1
        conn_fnf.close()

        # 4. OwnershipLedger integration with PermissionError on worktree_path
        state_dir_perm = tmp_path / "tasks_perm"
        state_dir_perm.mkdir(exist_ok=True)
        denied_wt = tmp_path / "denied_worktree"
        (state_dir_perm / f"{task_id}.json").write_text(
            json.dumps({"status": "failed", "pid": None, "worktree_path": str(denied_wt)}),
            encoding="utf-8",
        )

        ledger_path_perm = tmp_path / "own_wt_perm.sqlite3"
        ledger_perm = OwnershipLedger(ledger_path_perm, task_state_dir=state_dir_perm)
        conn_perm = sqlite3.connect(ledger_path_perm)
        conn_perm.execute(
            "CREATE TABLE write_claims (task_id TEXT, claim_json TEXT, pid INTEGER, created_at REAL, PRIMARY KEY (task_id, claim_json))"
        )
        conn_perm.execute(
            "INSERT INTO write_claims VALUES (?,?,?,?)",
            (task_id, '{"kind":"file","norm":"scripts/wt_perm.py"}', p.pid, time.time() - 200),
        )
        conn_perm.commit()

        orig_resolve = Path.resolve

        def mock_resolve_perm(self: Path, strict: bool = False) -> Path:
            if "denied_worktree" in str(self) or "denied_wt" in str(self):
                raise PermissionError(f"Permission denied: {self}")
            return orig_resolve(self, strict=strict)

        with patch.object(Path, "resolve", autospec=True, side_effect=mock_resolve_perm):
            ch_perm = ledger_perm.admit(
                task_id="challenger-wt-perm",
                mode="workspace-write",
                owned_paths=["scripts/wt_perm.py"],
                pid=os.getpid(),
            )
            assert ch_perm.admitted is False
            assert ch_perm.would_refuse is True
            rows_perm = conn_perm.execute("SELECT COUNT(*) FROM write_claims WHERE task_id = ?", (task_id,)).fetchone()
            assert rows_perm[0] == 1
            conn_perm.close()
    finally:
        p.terminate()
        p.wait()
