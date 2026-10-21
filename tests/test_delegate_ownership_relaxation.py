"""Write-path ownership relaxation (#11281, R7).

One row per conflict class the ledger refused before #11281, with its new
decision: disjoint concrete files in a shared directory admit; a same-file or
directory-prefix overlap queues behind the holder (bounded, typed timeout); a
literal bracket file name is comparable; a glob the ledger cannot compare still
refuses. A claim is released only when its author stops writing (terminal task
or explicit release), never by PR creation alone.
"""

from __future__ import annotations

import fnmatch
import json
import os
import sqlite3
import time
from pathlib import Path

import pytest

from scripts.guardrails import delegate_ownership as ownership
from scripts.guardrails.delegate_ownership import (
    AdmissionOutcome,
    ClaimKind,
    GuardMode,
    OwnershipLedger,
    PathClaim,
    claims_conflict,
    env_queue_wait_s,
    expand_claim,
    normalize_claim,
    owned_path_matcher,
)

PID = os.getpid()
DEAD_PID = 99999999


class FakeTime:
    """A clock and a sleep that advances it; ``hooks`` run on successive sleeps."""

    def __init__(self, limit: float = ownership.MAX_QUEUE_WAIT_S) -> None:
        self.now = self.start = time.time()
        self.limit = limit
        self.sleeps: list[float] = []
        self.hooks: list = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds
        assert self.now - self.start <= self.limit, "queue waited past its bound"
        assert len(self.sleeps) <= 1000, "queue kept polling without a bound"
        if self.hooks:
            self.hooks.pop(0)()


@pytest.fixture
def env(tmp_path: Path):
    state_dir = tmp_path / "tasks"
    state_dir.mkdir()
    ledger = OwnershipLedger(tmp_path / "own.sqlite3", task_state_dir=state_dir, mode=GuardMode.REFUSE)
    return ledger, state_dir


def _state(state_dir: Path, task_id: str, status: str = "running", pid: int = PID, **extra) -> None:
    (state_dir / f"{task_id}.json").write_text(json.dumps({"status": status, "pid": pid, **extra}), encoding="utf-8")


def _hold(ledger: OwnershipLedger, state_dir: Path, task_id: str, paths: list[str]) -> None:
    _state(state_dir, task_id)
    held = ledger.admit(task_id=task_id, mode="workspace-write", owned_paths=paths, pid=PID)
    assert held.admitted, held.reason


def _rows(ledger: OwnershipLedger, sql: str, *params) -> list[tuple]:
    with sqlite3.connect(ledger.path) as conn:
        return conn.execute(sql, params).fetchall()


def _events(ledger: OwnershipLedger, task_id: str) -> list[str]:
    return [r[0] for r in _rows(ledger, "SELECT event FROM admission_events WHERE task_id = ? ORDER BY id", task_id)]


def _claims(ledger: OwnershipLedger, task_id: str) -> list[str]:
    return sorted(
        json.loads(r[0])["norm"]
        for r in _rows(ledger, "SELECT claim_json FROM write_claims WHERE task_id = ?", task_id)
    )


def _waiters(ledger: OwnershipLedger) -> list[tuple]:
    return _rows(ledger, "SELECT task_id FROM write_waiters")


def _queued_admit(ledger, fake, task_id, paths, *, wait_s=60.0, poll_s=5.0, notices=None):
    return ledger.admit(
        task_id=task_id,
        mode="workspace-write",
        owned_paths=paths,
        pid=PID,
        wait_s=wait_s,
        poll_s=poll_s,
        sleep=fake.sleep,
        clock=fake.clock,
        monotonic=fake.clock,
        on_queued=(notices.append if notices is not None else None),
    )


# --- AC-01: shared directory, disjoint concrete files -------------------------


def test_disjoint_concrete_files_in_one_directory_are_both_admitted(env):
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["scripts/pkg/a.py"])

    second = ledger.admit(task_id="sibling", mode="workspace-write", owned_paths=["scripts/pkg/b.py"], pid=PID)

    assert second.admitted and not second.would_refuse and second.outcome is AdmissionOutcome.ADMITTED
    assert _claims(ledger, "holder") == ["scripts/pkg/a.py"]
    assert _claims(ledger, "sibling") == ["scripts/pkg/b.py"]


# --- AC-02: same-file and directory-prefix writers queue ----------------------


def test_same_file_writer_queues_then_is_admitted_when_holder_terminates(env):
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["scripts/pkg/a.py"])
    fake = FakeTime()
    fake.hooks.append(lambda: _state(state_dir, "holder", status="done"))
    notices: list[str] = []

    result = _queued_admit(ledger, fake, "waiter", ["scripts/pkg/a.py"], notices=notices)

    assert result.admitted and result.outcome is AdmissionOutcome.ADMITTED, result.reason
    assert result.waited_s == pytest.approx(5.0)
    assert fake.sleeps == [5.0]
    assert len(notices) == 1 and "holder" in notices[0] and "scripts/pkg/a.py" in notices[0]
    assert _events(ledger, "waiter") == ["queued", "admitted"]
    assert _claims(ledger, "waiter") == ["scripts/pkg/a.py"]
    assert _claims(ledger, "holder") == []
    assert _waiters(ledger) == []


def test_same_file_queue_is_bounded_and_times_out_typed(env):
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["scripts/pkg/a.py"])
    fake = FakeTime(limit=30.0)

    result = _queued_admit(ledger, fake, "waiter", ["scripts/pkg/a.py"], wait_s=30.0, poll_s=5.0)

    assert not result.admitted
    assert result.outcome is AdmissionOutcome.QUEUE_TIMEOUT
    assert result.queue_timeout and result.would_refuse
    assert sum(fake.sleeps) == pytest.approx(30.0)
    assert "timed out" in result.reason and "holder" in result.reason
    assert result.conflicts and result.conflicts[0]["other_task_id"] == "holder"
    assert _events(ledger, "waiter") == ["queued", "queue_timeout"]
    assert _claims(ledger, "waiter") == []
    assert _waiters(ledger) == []


def test_queue_bound_survives_a_backward_wall_clock_step(env, monkeypatch):
    """The bound is elapsed monotonic time: stepping the wall clock back cannot extend the wait."""
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["scripts/pkg/a.py"])
    fake = FakeTime(limit=30.0)
    wall = [time.time()]

    def stepping_wall_clock() -> float:
        wall[0] -= 3600.0  # an hour back on every read, as a clock correction might
        return wall[0]

    monkeypatch.setattr(ownership, "_sleep", fake.sleep)
    monkeypatch.setattr(ownership, "_monotonic", fake.clock, raising=False)
    monkeypatch.setattr(ownership, "_clock", stepping_wall_clock)
    rows: list[tuple] = []
    fake.hooks.append(lambda: rows.extend(_rows(ledger, "SELECT enqueued_at, deadline FROM write_waiters")))

    result = ledger.admit(
        task_id="waiter", mode="workspace-write", owned_paths=["scripts/pkg/a.py"], pid=PID, wait_s=30.0, poll_s=5.0
    )

    assert result.outcome is AdmissionOutcome.QUEUE_TIMEOUT, result.reason
    assert result.waited_s == pytest.approx(30.0)
    assert sum(fake.sleeps) == pytest.approx(30.0)
    # Peers expire the row on wall time: its deadline is the monotonic budget left at the write.
    assert len(rows) == 1 and rows[0][1] - rows[0][0] == pytest.approx(30.0)
    assert _events(ledger, "waiter") == ["queued", "queue_timeout"]
    assert _waiters(ledger) == []


def test_requested_wait_is_capped(env):
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["a.py"])
    fake = FakeTime()

    result = _queued_admit(ledger, fake, "waiter", ["a.py"], wait_s=10**9, poll_s=ownership.MAX_QUEUE_WAIT_S / 4)

    assert result.outcome is AdmissionOutcome.QUEUE_TIMEOUT
    assert sum(fake.sleeps) == pytest.approx(ownership.MAX_QUEUE_WAIT_S)


@pytest.mark.parametrize("poll_s", [0.0, -1.0])
def test_non_positive_poll_does_not_spin(env, poll_s):
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["a.py"])
    fake = FakeTime(limit=10.0)

    result = _queued_admit(ledger, fake, "waiter", ["a.py"], wait_s=10.0, poll_s=poll_s)

    assert result.outcome is AdmissionOutcome.QUEUE_TIMEOUT
    assert fake.sleeps == [ownership.DEFAULT_QUEUE_POLL_S, ownership.DEFAULT_QUEUE_POLL_S]


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, ownership.DEFAULT_QUEUE_WAIT_S),
        ("", ownership.DEFAULT_QUEUE_WAIT_S),
        ("not-a-number", ownership.DEFAULT_QUEUE_WAIT_S),
        ("nan", ownership.DEFAULT_QUEUE_WAIT_S),
        ("0", 0.0),
        ("-5", 0.0),
        ("90", 90.0),
        ("1e12", ownership.MAX_QUEUE_WAIT_S),
        ("inf", ownership.MAX_QUEUE_WAIT_S),
    ],
)
def test_env_queue_wait_is_bounded(monkeypatch, raw, expected):
    if raw is None:
        monkeypatch.delenv(ownership.QUEUE_WAIT_ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(ownership.QUEUE_WAIT_ENV_VAR, raw)
    assert env_queue_wait_s() == expected


@pytest.mark.parametrize(
    "held,incoming",
    [("pkg", "pkg/mod.py"), ("pkg/mod.py", "pkg/"), ("pkg/**", "pkg/sub/x.py")],
)
def test_directory_prefix_overlap_queues_and_is_never_admitted_while_held(env, held, incoming):
    """A directory claim covers the concrete file, so it is an overlap, not a shared directory."""
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", [held])

    immediate = ledger.admit(task_id="now", mode="workspace-write", owned_paths=[incoming], pid=PID)
    assert not immediate.admitted and immediate.conflicts
    assert immediate.outcome is AdmissionOutcome.REFUSED

    fake = FakeTime()
    queued = _queued_admit(ledger, fake, "waiter", [incoming], wait_s=10.0, poll_s=5.0)
    assert queued.outcome is AdmissionOutcome.QUEUE_TIMEOUT
    assert _claims(ledger, "waiter") == []


def test_newcomer_does_not_jump_a_queued_waiter(env):
    """FIFO: a later writer for the same file waits behind the earlier waiter, not beside it."""
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["shared.py"])
    fake = FakeTime()
    seen = {}

    def holder_finishes_and_newcomer_arrives():
        _state(state_dir, "holder", status="done")
        seen["late"] = ledger.admit(
            task_id="late", mode="workspace-write", owned_paths=["shared.py"], pid=PID, clock=fake.clock
        )

    fake.hooks.append(holder_finishes_and_newcomer_arrives)

    first = _queued_admit(ledger, fake, "first", ["shared.py"])

    late = seen["late"]
    assert not late.admitted and late.conflicts[0]["other_task_id"] == "first"
    assert late.conflicts[0].get("queued") is True
    assert first.admitted
    assert _claims(ledger, "first") == ["shared.py"]


def test_waiter_ahead_on_a_disjoint_file_does_not_block(env):
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["a.py"])
    fake = FakeTime()
    seen = {}
    fake.hooks.append(
        lambda: seen.setdefault(
            "other",
            ledger.admit(task_id="other", mode="workspace-write", owned_paths=["b.py"], pid=PID, clock=fake.clock),
        )
    )

    result = _queued_admit(ledger, fake, "waiter", ["a.py"], wait_s=5.0, poll_s=5.0)

    assert seen["other"].admitted
    assert result.outcome is AdmissionOutcome.QUEUE_TIMEOUT


@pytest.mark.parametrize("stale", ["dead_pid", "past_deadline"])
def test_abandoned_waiter_rows_are_reconciled(env, stale):
    ledger, _state_dir = env
    with ledger._connect() as conn:
        pass  # create the schema
    pid, deadline = (DEAD_PID, time.time() + 600) if stale == "dead_pid" else (PID, time.time() - 1)
    with sqlite3.connect(ledger.path) as conn:
        conn.execute(
            "INSERT INTO write_waiters (task_id, claims_json, pid, enqueued_at, deadline) VALUES (?,?,?,?,?)",
            ("ghost", json.dumps([normalize_claim("x.py").as_dict()]), pid, time.time() - 10, deadline),
        )

    result = ledger.admit(task_id="live", mode="workspace-write", owned_paths=["x.py"], pid=PID)

    assert result.admitted, result.reason
    assert _waiters(ledger) == []


def test_unprovable_peer_still_refuses_without_queueing(env):
    ledger, state_dir = env
    _hold(ledger, state_dir, "globber", ["tests/test_*.py"])
    fake = FakeTime()

    result = _queued_admit(ledger, fake, "waiter", ["scripts/a.py"])

    assert result.outcome is AdmissionOutcome.REFUSED
    assert "cannot prove write-path disjointness" in result.reason
    assert fake.sleeps == []
    assert _waiters(ledger) == []


def test_warn_mode_and_override_still_admit_without_queueing(env):
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["a.py"])
    fake = FakeTime()
    overridden = ledger.admit(
        task_id="o",
        mode="workspace-write",
        owned_paths=["a.py"],
        pid=PID,
        allow_path_overlap="reviewed: disjoint hunks",
        wait_s=60,
        sleep=fake.sleep,
        clock=fake.clock,
    )
    warn = OwnershipLedger(ledger.path, task_state_dir=state_dir, mode=GuardMode.WARN).admit(
        task_id="w",
        mode="workspace-write",
        owned_paths=["a.py"],
        pid=PID,
        wait_s=60,
        sleep=fake.sleep,
        clock=fake.clock,
    )
    assert overridden.admitted and overridden.override_reason
    assert warn.admitted and warn.would_refuse
    assert fake.sleeps == []


# --- AC-03: release on quiescence only ---------------------------------------


@pytest.mark.parametrize(
    "pr_fields",
    [
        {"pr_url": "https://example.invalid/pull/1"},
        {"auto_finalize": {"ok": True, "pr_url": "https://example.invalid/pull/1", "commit_sha": "a" * 40}},
    ],
    ids=["pr_url", "auto_finalize_pr"],
)
def test_pr_creation_alone_does_not_release_the_claim(env, pr_fields):
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["site/x.ts"])
    fake = FakeTime()
    fake.hooks.append(lambda: _state(state_dir, "holder", **pr_fields))

    result = _queued_admit(ledger, fake, "waiter", ["site/x.ts"], wait_s=10.0, poll_s=5.0)

    assert result.outcome is AdmissionOutcome.QUEUE_TIMEOUT
    assert _claims(ledger, "holder") == ["site/x.ts"]
    assert _claims(ledger, "waiter") == []


def test_explicit_release_admits_the_waiter(env):
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["a.py"])
    fake = FakeTime()
    fake.hooks.append(lambda: ledger.release("holder", pid=PID))

    result = _queued_admit(ledger, fake, "waiter", ["a.py"])

    assert result.admitted
    assert _claims(ledger, "waiter") == ["a.py"]


def test_review_fix_dispatch_reacquires_the_claim(env):
    """The author's next writing run (review fixes) holds the file again before it writes."""
    ledger, state_dir = env
    _hold(ledger, state_dir, "author", ["a.py"])
    _state(state_dir, "author", status="done")

    fix = ledger.admit(task_id="author-fix", mode="workspace-write", owned_paths=["a.py"], pid=PID)
    _state(state_dir, "author-fix")
    other = ledger.admit(task_id="other", mode="workspace-write", owned_paths=["a.py"], pid=PID)

    assert fix.admitted and _claims(ledger, "author-fix") == ["a.py"]
    assert not other.admitted and other.conflicts[0]["other_task_id"] == "author-fix"


# --- AC-04: literal bracket file names ---------------------------------------

BRACKET_NAMES = [
    "site/src/pages/[...path].astro",
    "site/src/pages/lexicon-v2/[...path].astro",
    "site/src/pages/lexicon/[lemma].astro",
    "site/src/pages/[[...slug]].astro",
    "site/src/pages/[[]...slug].astro",
    "site/src/pages/[lang]/index.astro",
]


@pytest.mark.parametrize("raw", BRACKET_NAMES)
def test_literal_bracket_name_is_comparable_and_admitted_beside_a_peer(env, raw):
    ledger, state_dir = env
    _hold(ledger, state_dir, "peer", ["site/src/components/Card.tsx"])

    result = ledger.admit(task_id="route", mode="workspace-write", owned_paths=[raw], pid=PID)

    assert result.admitted, result.reason
    assert "comparable" not in result.reason
    assert not result.unknown_claims


def test_literal_bracket_name_same_file_queues(env):
    ledger, state_dir = env
    _hold(ledger, state_dir, "holder", ["site/src/pages/[...path].astro"])

    same = ledger.admit(task_id="same", mode="workspace-write", owned_paths=["site/src/pages/[...path].astro"], pid=PID)
    escaped = ledger.admit(
        task_id="escaped", mode="workspace-write", owned_paths=["site/src/pages/[[]...path].astro"], pid=PID
    )

    for result in (same, escaped):
        assert not result.admitted and result.conflicts, result.reason
        assert "comparable" not in result.reason


@pytest.mark.parametrize("raw", BRACKET_NAMES)
def test_commit_scope_owns_the_literal_bracket_file(raw):
    """Like a git pathspec, the claim names its literal file as well as its glob matches."""
    matcher = owned_path_matcher(raw)
    assert matcher is not None and matcher(raw)
    assert all(c.kind is ClaimKind.SUBTREE for c in expand_claim(raw))


def test_escaped_bracket_spelling_still_owns_the_bracket_file():
    matcher = owned_path_matcher("site/src/pages/[[]...slug].astro")
    assert matcher is not None and matcher("site/src/pages/[...slug].astro")
    reserved = expand_claim("site/src/pages/[[]...slug].astro")
    assert any(c.norm == "site/src/pages/[...slug].astro" for c in reserved)


SOUNDNESS_PROBES = [
    "site/src/pages/[...path].astro",
    "site/src/pages/p.astro",
    "site/src/pages/..astro",
    "site/src/pages/[...slug].astro",
    "site/src/pages/[.astro",
    "site/src/pages/s].astro",
    "site/src/pages/l/index.astro",
    "site/src/pages/[lang]/index.astro",
    "site/src/pages/x/index.astro",
    "site/src/pages/lexicon/[lemma].astro",
    "site/src/pages/lexicon/m.astro",
    "site/src/pages/lexicon-v2/[...path].astro",
    "site/src/pages/lexicon-v2/t.astro",
]


@pytest.mark.parametrize("raw", BRACKET_NAMES)
def test_every_path_commit_scope_owns_is_reserved(raw):
    """Fail closed: admission reserves at least every path the commit-scope matcher lets the worker write."""
    matcher = owned_path_matcher(raw)
    reserved = expand_claim(raw)
    owned = [path for path in SOUNDNESS_PROBES if matcher(path)]
    assert owned
    for path in owned:
        # A changed path is a literal file name, never a pattern.
        written = PathClaim(path, ClaimKind.SUBTREE, path)
        assert any(claims_conflict(written, claim) for claim in reserved), (raw, path)


@pytest.mark.parametrize("members", ["...path", "lemma", "[", "]ab", "^ab", "&|~", "aab"])
def test_bracket_expansion_is_exactly_what_fnmatch_matches(members):
    """Enumerated members equal fnmatch's own set over printable ASCII, so nothing a glob owns is missed."""
    pattern = f"x/[{members}].y"
    alphabet = [chr(c) for c in range(32, 127) if chr(c) != "/"]
    expected = sorted(f"x/{ch}.y" for ch in alphabet if fnmatch.fnmatchcase(f"x/{ch}.y", pattern))
    assert sorted(ownership._bracket_expansions(pattern)) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "tests/test_*.py",
        "tests/test_[abd-qs-z]*.py",
        "site/src/pages/[a-z].astro",
        "site/src/pages/[!x].astro",
        "site/src/pages/?.astro",
        "site/src/pages/[a/b].astro",
        "site/[.]/x.astro",
        "site/" + "[abcdefgh]" * 3 + ".astro",
    ],
)
def test_globs_the_ledger_cannot_compare_still_refuse(env, raw):
    ledger, state_dir = env
    _hold(ledger, state_dir, "peer", ["docs/unrelated.md"])

    result = ledger.admit(task_id="glob", mode="workspace-write", owned_paths=[raw], pid=PID)

    assert not result.admitted
    assert result.outcome is AdmissionOutcome.REFUSED
    assert "declared no comparable --owned-path" in result.reason
    assert [c.kind for c in expand_claim(raw)] == [ClaimKind.UNKNOWN]
