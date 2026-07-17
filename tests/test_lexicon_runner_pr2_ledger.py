"""Injected-crash + fencing tests for runner PR2 (real-unit ledger / resume)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lexicon.runner.contracts import ErrorCode
from scripts.lexicon.runner.ledger import (
    CasStatus,
    ChunkLedgerState,
    DuplicateRunnerError,
    Ledger,
    OperatorActionKind,
    SchedulableState,
    UnitOutcome,
    compute_run_fingerprint,
)
from scripts.lexicon.runner.split import child_chunk_id

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "lexicon" / "runner_pr1"


def _ensure_fixture() -> None:
    needed = (
        FIXTURE / "baseline.sha256",
        FIXTURE / "baseline_enriched.json",
        FIXTURE / "sources_slice.sqlite",
        FIXTURE / "slice_input.json",
        FIXTURE / "grac_frequency_slice.json",
        FIXTURE / "kaikki_slice.json",
    )
    if not all(path.is_file() for path in needed):
        from scripts.lexicon.runner.generate_pr1_fixture import main as gen

        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("LEXICON_SLOVNYK_OFFLINE", "1")
            assert gen() == 0


@pytest.fixture
def ledger(tmp_path: Path) -> Ledger:
    lg = Ledger(tmp_path / "run.ledger.sqlite", max_attempts=3, lease_ttl_seconds=60.0)
    lg.open()
    yield lg
    lg.close()


def test_duplicate_runner_os_lock_refused(tmp_path: Path) -> None:
    path = tmp_path / "shared.ledger.sqlite"
    a = Ledger(path, owner_id="writer-a")
    a.open()
    b = Ledger(path, owner_id="writer-b")
    with pytest.raises(DuplicateRunnerError, match="duplicate runner refused"):
        b.open()
    a.close()
    # After release, a second writer may acquire.
    b.open()
    b.close()


def test_fingerprint_start_refuses_duplicate_incomplete(ledger: Ledger) -> None:
    fp = compute_run_fingerprint(cohort_digest="cohort-a")
    first = ledger.start_run(fp)
    assert first.ok and first.run_id
    second = ledger.start_run(fp)
    assert not second.ok
    assert second.resumable_run_id == first.run_id
    # force_new creates a separate run without attaching old results.
    forced = ledger.start_run(fp, force_new=True)
    assert forced.ok
    assert forced.run_id != first.run_id


def test_resume_fingerprint_mismatch_refused(ledger: Ledger) -> None:
    fp = compute_run_fingerprint(cohort_digest="cohort-b")
    started = ledger.start_run(fp)
    assert started.run_id
    bad = ledger.resume_run(started.run_id, compute_run_fingerprint(cohort_digest="OTHER"))
    assert bad.status is CasStatus.FINGERPRINT_MISMATCH_REFUSED
    assert bad.detail == ErrorCode.FINGERPRINT_MISMATCH_REFUSED.value
    events = ledger.list_events(started.run_id, event=ErrorCode.FINGERPRINT_MISMATCH_REFUSED.value)
    assert events
    good = ledger.resume_run(started.run_id, fp)
    assert good.ok


def test_claim_monotonic_generation_and_heartbeat_cas(ledger: Ledger) -> None:
    fp = compute_run_fingerprint(cohort_digest="claim")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_chunk_work_units(run, [("chunk-0", ["a", "b"])])
    c1 = ledger.claim_unit(run, "chunk-0", "owner-1", now=1000.0)
    assert c1.ok
    assert c1.lease_generation == 1
    hb_ok = ledger.heartbeat(run, "chunk-0", "owner-1", 1, now=1010.0)
    assert hb_ok.ok
    # Stale writer heartbeat rejected.
    hb_stale = ledger.heartbeat(run, "chunk-0", "owner-OLD", 1, now=1011.0)
    assert hb_stale.status is CasStatus.STALE_COMMIT_REJECTED
    hb_stale_gen = ledger.heartbeat(run, "chunk-0", "owner-1", 99, now=1012.0)
    assert hb_stale_gen.status is CasStatus.STALE_COMMIT_REJECTED


def test_stale_writer_result_commit_rejected(ledger: Ledger) -> None:
    """Injected-crash suite: stale writers cannot commit after claim loss."""
    fp = compute_run_fingerprint(cohort_digest="stale")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_chunk_work_units(run, [("chunk-0", ["x"])])
    c1 = ledger.claim_unit(run, "chunk-0", "owner-A", now=1000.0)
    assert c1.lease_generation == 1
    # Lease expires; reclaim; new owner claims (generation 2).
    reclaimed = ledger.reclaim_expired(run, now=2000.0)
    assert "chunk-0" in reclaimed
    events = ledger.list_events(run, event="lease_reclaimed")
    assert events
    c2 = ledger.claim_unit(run, "chunk-0", "owner-B", now=2001.0)
    assert c2.ok and c2.lease_generation == 2
    # Stale A commits with gen=1 → rejected; B commits with gen=2 → ok.
    stale = ledger.commit_result(run, "chunk-0", "owner-A", 1, "done", result_hash="hash-a", now=2002.0)
    assert stale.status is CasStatus.STALE_COMMIT_REJECTED
    assert stale.detail == ErrorCode.STALE_COMMIT_REJECTED.value
    good = ledger.commit_result(run, "chunk-0", "owner-B", 2, "done", result_hash="hash-b", now=2003.0)
    assert good.ok
    unit = ledger.get_work_unit(run, "chunk-0")
    assert unit is not None
    assert unit["result_hash"] == "hash-b"
    assert unit["state"] == UnitOutcome.DONE.value


def test_claim_loss_reclaim_increments_generation(ledger: Ledger) -> None:
    fp = compute_run_fingerprint(cohort_digest="claim-loss")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_work_unit(run, "lemma-1", unit_kind="lemma")
    c1 = ledger.claim_unit(run, "lemma-1", "w1", now=10.0)
    assert c1.lease_generation == 1
    ledger.reclaim_expired(run, now=9999.0)
    c2 = ledger.claim_unit(run, "lemma-1", "w2", now=10000.0)
    assert c2.lease_generation == 2
    assert c2.attempt_count == 2


def test_attempt_cap_exhaustion_and_operator_retry(ledger: Ledger) -> None:
    ledger.max_attempts = 2
    fp = compute_run_fingerprint(cohort_digest="cap")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_work_unit(run, "lemma-z", unit_kind="lemma")
    t = 100.0
    for owner in ("a", "b"):
        c = ledger.claim_unit(run, "lemma-z", owner, now=t)
        assert c.ok
        ledger.commit_result(
            run,
            "lemma-z",
            owner,
            int(c.lease_generation or 0),
            "retry_scheduled",
            error_code="transient",
            now=t + 1,
        )
        t += 10
    # Third claim hits cap → failed_terminal.
    exhausted = ledger.claim_unit(run, "lemma-z", "c", now=t)
    assert exhausted.status is CasStatus.ATTEMPT_CAP_EXHAUSTED
    unit = ledger.get_work_unit(run, "lemma-z")
    assert unit is not None
    assert unit["state"] == UnitOutcome.FAILED_TERMINAL.value
    # Operator retry is the only reopen path.
    bad = ledger.retry_failed(run, "lemma-z", "")
    assert not bad.ok
    ok = ledger.retry_failed(run, "lemma-z", "operator accepted transient exhaustion")
    assert ok.ok
    assert ledger.count_operator_actions(run, OperatorActionKind.RETRY_FAILED.value) == 1
    unit2 = ledger.get_work_unit(run, "lemma-z")
    assert unit2 is not None
    assert unit2["state"] == SchedulableState.PENDING.value
    assert int(unit2["attempt_count"]) == 0
    run_row = ledger.get_run(run)
    assert run_row is not None
    assert int(run_row["manual_retry_epoch"]) == 1


def test_attempt_cap_syncs_chunk_row(ledger: Ledger) -> None:
    """Attempt-cap terminal marking must update work_units AND chunks together."""
    ledger.max_attempts = 1
    fp = compute_run_fingerprint(cohort_digest="cap-chunk")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_chunk_work_units(run, [("chunk-cap", ["x", "y"])])
    c1 = ledger.claim_unit(run, "chunk-cap", "owner-1", now=10.0)
    assert c1.ok
    assert ledger.commit_result(
        run,
        "chunk-cap",
        "owner-1",
        int(c1.lease_generation or 0),
        "retry_scheduled",
        error_code="transient",
        now=11.0,
    ).ok
    exhausted = ledger.claim_unit(run, "chunk-cap", "owner-2", now=12.0)
    assert exhausted.status is CasStatus.ATTEMPT_CAP_EXHAUSTED
    unit = ledger.get_work_unit(run, "chunk-cap")
    chunk = ledger.get_chunk(run, "chunk-cap")
    assert unit is not None and chunk is not None
    assert unit["state"] == UnitOutcome.FAILED_TERMINAL.value
    assert chunk["state"] == ChunkLedgerState.FAILED_TERMINAL.value
    assert chunk["error_code"] == "attempt_cap_exhausted"


def test_claim_crash_mid_transaction_rolls_back_both_tables(ledger: Ledger) -> None:
    """crash_after_claim fires inside the write txn so neither table commits."""
    fp = compute_run_fingerprint(cohort_digest="claim-crash")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_chunk_work_units(run, [("chunk-c", ["a"])])
    ledger.crash_after_claim = True
    with pytest.raises(RuntimeError, match="injected crash: after_claim"):
        ledger.claim_unit(run, "chunk-c", "owner", now=1.0)
    ledger.crash_after_claim = False
    unit = ledger.get_work_unit(run, "chunk-c")
    chunk = ledger.get_chunk(run, "chunk-c")
    assert unit is not None and chunk is not None
    assert unit["state"] == SchedulableState.PENDING.value
    assert int(unit["lease_generation"]) == 0
    assert chunk["state"] == ChunkLedgerState.PENDING.value
    assert int(chunk["lease_generation"]) == 0
    # Retry claim succeeds after the crash flag is cleared.
    ok = ledger.claim_unit(run, "chunk-c", "owner", now=2.0)
    assert ok.ok and ok.lease_generation == 1


def test_result_crash_mid_transaction_rolls_back_both_tables(ledger: Ledger) -> None:
    """crash_after_result fires inside the write txn so neither table commits."""
    fp = compute_run_fingerprint(cohort_digest="result-crash")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_chunk_work_units(run, [("chunk-r", ["a"])])
    claim = ledger.claim_unit(run, "chunk-r", "owner", now=1.0)
    gen = int(claim.lease_generation or 0)
    ledger.crash_after_result = True
    with pytest.raises(RuntimeError, match="injected crash: after_result"):
        ledger.commit_result(run, "chunk-r", "owner", gen, "done", result_hash="h1", now=2.0)
    ledger.crash_after_result = False
    unit = ledger.get_work_unit(run, "chunk-r")
    chunk = ledger.get_chunk(run, "chunk-r")
    assert unit is not None and chunk is not None
    assert unit["state"] == SchedulableState.LEASED.value
    assert chunk["state"] == ChunkLedgerState.LEASED.value
    assert unit["result_hash"] is None
    # Retry commit succeeds.
    assert ledger.commit_result(run, "chunk-r", "owner", gen, "done", result_hash="h1", now=3.0).ok
    unit2 = ledger.get_work_unit(run, "chunk-r")
    assert unit2 is not None
    assert unit2["state"] == UnitOutcome.DONE.value
    assert unit2["result_hash"] == "h1"


def test_split_interruption_and_deterministic_children(ledger: Ledger) -> None:
    """Crash mid-split (inside txn): parent remains active; retry creates same child IDs."""
    fp = compute_run_fingerprint(cohort_digest="split")
    run = ledger.start_run(fp).run_id
    assert run
    parent_id = "parent"
    lemmas = ["a", "b", "c", "d"]
    ledger.register_chunk_work_units(run, [(parent_id, lemmas)])
    claim = ledger.claim_unit(run, parent_id, "coord", now=50.0)
    assert claim.ok
    gen = int(claim.lease_generation or 0)

    ledger.crash_mid_split = True
    with pytest.raises(RuntimeError, match="injected crash: mid_split"):
        ledger.commit_split(run, parent_id, "coord", gen, now=51.0)
    ledger.crash_mid_split = False

    # Parent still leased (no partial children) — crash rolled back mid-txn write.
    parent = ledger.get_chunk(run, parent_id)
    assert parent is not None
    assert parent["state"] == ChunkLedgerState.LEASED.value
    assert int(parent["is_leaf"]) == 1
    parent_wu = ledger.get_work_unit(run, parent_id)
    assert parent_wu is not None
    assert parent_wu["state"] == SchedulableState.LEASED.value

    # Retry completes deterministically.
    done = ledger.commit_split(run, parent_id, "coord", gen, now=52.0)
    assert done.ok
    parent2 = ledger.get_chunk(run, parent_id)
    assert parent2 is not None
    assert parent2["state"] == ChunkLedgerState.SUPERSEDED.value
    assert int(parent2["is_leaf"]) == 0
    left_id = child_chunk_id(parent_id, 1, ["a", "b"])
    right_id = child_chunk_id(parent_id, 1, ["c", "d"])
    left = ledger.get_chunk(run, left_id)
    right = ledger.get_chunk(run, right_id)
    assert left is not None and right is not None
    assert left["state"] == ChunkLedgerState.PENDING.value
    assert right["state"] == ChunkLedgerState.PENDING.value
    # Re-split of a superseded (non-leaf) parent is refused.
    again = ledger.commit_split(run, parent_id, "coord", gen, now=53.0)
    assert again.status is CasStatus.NOT_LEAF


def test_single_lemma_oom_failed_terminal_no_split(ledger: Ledger) -> None:
    """Single-lemma OOM marks chunks + work_units FAILED_TERMINAL atomically."""
    fp = compute_run_fingerprint(cohort_digest="oom1")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_chunk_work_units(run, [("leaf", ["only"])])
    claim = ledger.claim_unit(run, "leaf", "coord", now=1.0)
    assert claim.ok
    gen = int(claim.lease_generation or 0)

    # Mid-txn crash on single-lemma path: neither table advances.
    ledger.crash_mid_split = True
    with pytest.raises(RuntimeError, match="injected crash: mid_split"):
        ledger.commit_split(run, "leaf", "coord", gen, now=2.0)
    ledger.crash_mid_split = False
    leaf_mid = ledger.get_chunk(run, "leaf")
    wu_mid = ledger.get_work_unit(run, "leaf")
    assert leaf_mid is not None and wu_mid is not None
    assert leaf_mid["state"] == ChunkLedgerState.LEASED.value
    assert wu_mid["state"] == SchedulableState.LEASED.value

    res = ledger.commit_split(run, "leaf", "coord", gen, now=3.0)
    assert res.ok
    leaf = ledger.get_chunk(run, "leaf")
    wu = ledger.get_work_unit(run, "leaf")
    assert leaf is not None and wu is not None
    assert leaf["state"] == ChunkLedgerState.FAILED_TERMINAL.value
    assert leaf["error_code"] == ErrorCode.FAILED_OOM.value
    assert wu["state"] == UnitOutcome.FAILED_TERMINAL.value
    assert wu["error_code"] == ErrorCode.FAILED_OOM.value


def _mark_lemma_terminal(
    ledger: Ledger,
    run_id: str,
    lemma_id: str,
    *,
    owner: str = "coord",
    now: float = 1.0,
    outcome: str = "done",
) -> None:
    """Claim+commit a lemma work unit to a terminal-successful state."""
    claim = ledger.claim_unit(run_id, lemma_id, owner, now=now)
    assert claim.ok, claim.detail
    assert ledger.commit_result(
        run_id,
        lemma_id,
        owner,
        int(claim.lease_generation or 0),
        outcome,
        result_hash=f"h-{lemma_id}",
        now=now + 0.1,
    ).ok


def test_seal_interruption_and_leaf_only_rules(ledger: Ledger) -> None:
    """Seal crash leaves no seal row; superseded parents never seal."""
    fp = compute_run_fingerprint(cohort_digest="seal")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_chunk_work_units(run, [("parent", ["a", "b"])])
    claim = ledger.claim_unit(run, "parent", "coord", now=10.0)
    gen = int(claim.lease_generation or 0)
    assert ledger.commit_split(run, "parent", "coord", gen, now=11.0).ok
    left_id = child_chunk_id("parent", 1, ["a"])
    # Parent is superseded — not sealable.
    parent_seal = ledger.commit_seal(run, "parent", "coord", gen, seal_sha256="dead", now=12.0)
    assert parent_seal.status is CasStatus.NOT_LEAF

    # Claim leaf, mark done, then crash mid-seal.
    c_left = ledger.claim_unit(run, left_id, "coord", now=13.0)
    assert c_left.ok
    lgen = int(c_left.lease_generation or 0)
    assert ledger.commit_result(run, left_id, "coord", lgen, "done", result_hash="r1", now=14.0).ok
    # Constituent lemmas must be terminal-successful before seal (#5370).
    _mark_lemma_terminal(ledger, run, "a", now=14.5)
    # After result, owner released; seal uses matching generation on DONE leaf.
    leaf = ledger.get_chunk(run, left_id)
    assert leaf is not None
    assert int(leaf["lease_generation"]) == lgen

    ledger.crash_mid_seal = True
    with pytest.raises(RuntimeError, match="injected crash: mid_seal"):
        ledger.commit_seal(run, left_id, "coord", lgen, seal_sha256="seal-1", now=15.0)
    ledger.crash_mid_seal = False
    # No seal row after crash.
    seals = (
        ledger._require()
        .execute(
            "SELECT COUNT(*) AS n FROM seals WHERE run_id = ? AND chunk_id = ?",
            (run, left_id),
        )
        .fetchone()
    )
    assert int(seals["n"]) == 0
    # Retry seal succeeds.
    sealed = ledger.commit_seal(run, left_id, "coord", lgen, seal_sha256="seal-1", now=16.0)
    assert sealed.ok
    seals2 = (
        ledger._require()
        .execute(
            "SELECT seal_sha256 FROM seals WHERE run_id = ? AND chunk_id = ?",
            (run, left_id),
        )
        .fetchone()
    )
    assert seals2 is not None
    assert seals2["seal_sha256"] == "seal-1"
    # Stale generation seal rejected.
    stale = ledger.commit_seal(run, left_id, "coord", lgen - 1, seal_sha256="seal-x", now=17.0)
    assert stale.status in {CasStatus.STALE_COMMIT_REJECTED, CasStatus.INVALID_STATE}


def test_seal_blocked_by_failed_constituent(ledger: Ledger) -> None:
    """Seal refuses when any constituent lemma is failed_terminal (#5370)."""
    fp = compute_run_fingerprint(cohort_digest="seal-fail-const")
    run = ledger.start_run(fp).run_id
    assert run
    lemmas = ["good-a", "bad-b", "good-c"]
    ledger.register_chunk_work_units(run, [("chunk-x", lemmas)])
    claim = ledger.claim_unit(run, "chunk-x", "coord", now=1.0)
    gen = int(claim.lease_generation or 0)
    assert ledger.commit_result(run, "chunk-x", "coord", gen, "done", result_hash="chunk-h", now=2.0).ok
    _mark_lemma_terminal(ledger, run, "good-a", now=3.0)
    _mark_lemma_terminal(ledger, run, "good-c", now=4.0, outcome="no_data")
    # Force failed_terminal on the remaining constituent without claim dance.
    ledger._require().execute(
        "UPDATE work_units SET state = ?, error_code = ?, updated_at = ? "
        "WHERE run_id = ? AND unit_id = ? AND phase = ?",
        (
            UnitOutcome.FAILED_TERMINAL.value,
            "inject_fail",
            5.0,
            run,
            "bad-b",
            "offline_enrich",
        ),
    )

    blocked = ledger.commit_seal(run, "chunk-x", "coord", gen, seal_sha256="seal-blocked", now=6.0)
    assert blocked.status is CasStatus.INVALID_STATE
    assert "bad-b" in blocked.detail
    assert "failed_terminal" in blocked.detail
    assert "constituent lemmas not terminal-successful" in blocked.detail
    seals = (
        ledger._require()
        .execute(
            "SELECT COUNT(*) AS n FROM seals WHERE run_id = ? AND chunk_id = ?",
            (run, "chunk-x"),
        )
        .fetchone()
    )
    assert int(seals["n"]) == 0
    chunk = ledger.get_chunk(run, "chunk-x")
    assert chunk is not None
    assert chunk["state"] == ChunkLedgerState.DONE.value
    events = ledger.list_events(run, event="seal_blocked_constituent_lemmas")
    assert len(events) == 1


def test_seal_blocked_by_pending_constituent(ledger: Ledger) -> None:
    """Seal refuses when any constituent lemma is still pending (#5370)."""
    fp = compute_run_fingerprint(cohort_digest="seal-pend-const")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_chunk_work_units(run, [("chunk-y", ["done-1", "still-pending"])])
    claim = ledger.claim_unit(run, "chunk-y", "coord", now=1.0)
    gen = int(claim.lease_generation or 0)
    assert ledger.commit_result(run, "chunk-y", "coord", gen, "done", result_hash="cy", now=2.0).ok
    _mark_lemma_terminal(ledger, run, "done-1", now=3.0)
    # still-pending remains pending — seal must block.
    blocked = ledger.commit_seal(run, "chunk-y", "coord", gen, seal_sha256="nope", now=4.0)
    assert blocked.status is CasStatus.INVALID_STATE
    assert "still-pending" in blocked.detail
    assert "pending" in blocked.detail
    seals = (
        ledger._require()
        .execute(
            "SELECT COUNT(*) AS n FROM seals WHERE run_id = ? AND chunk_id = ?",
            (run, "chunk-y"),
        )
        .fetchone()
    )
    assert int(seals["n"]) == 0

    # Completing the last lemma unblocks seal; mid-seal crash still rolls back.
    _mark_lemma_terminal(ledger, run, "still-pending", now=5.0)
    ledger.crash_mid_seal = True
    with pytest.raises(RuntimeError, match="injected crash: mid_seal"):
        ledger.commit_seal(run, "chunk-y", "coord", gen, seal_sha256="seal-y", now=6.0)
    ledger.crash_mid_seal = False
    seals_mid = (
        ledger._require()
        .execute(
            "SELECT COUNT(*) AS n FROM seals WHERE run_id = ? AND chunk_id = ?",
            (run, "chunk-y"),
        )
        .fetchone()
    )
    assert int(seals_mid["n"]) == 0
    sealed = ledger.commit_seal(run, "chunk-y", "coord", gen, seal_sha256="seal-y", now=7.0)
    assert sealed.ok


def test_lemma_retry_reschedules_parent_chunk(ledger: Ledger) -> None:
    """retry_failed on a lemma CAS-resets the parent chunk to PENDING (#5370)."""
    ledger.max_attempts = 1
    fp = compute_run_fingerprint(cohort_digest="lemma-retry-parent")
    run = ledger.start_run(fp).run_id
    assert run
    lemmas = ["L1", "L2", "L3"]
    ledger.register_chunk_work_units(run, [("parent-chunk", lemmas)])

    # Exhaust the lemma so it is failed_terminal.
    c_lemma = ledger.claim_unit(run, "L2", "w1", now=10.0)
    assert c_lemma.ok
    assert ledger.commit_result(
        run,
        "L2",
        "w1",
        int(c_lemma.lease_generation or 0),
        "retry_scheduled",
        error_code="transient",
        now=11.0,
    ).ok
    exhausted = ledger.claim_unit(run, "L2", "w2", now=12.0)
    assert exhausted.status is CasStatus.ATTEMPT_CAP_EXHAUSTED
    unit = ledger.get_work_unit(run, "L2")
    assert unit is not None
    assert unit["state"] == UnitOutcome.FAILED_TERMINAL.value

    # Parent chunk completed while a constituent was still failing — the
    # pre-#5370 orphanage path left the chunk DONE forever.
    c_chunk = ledger.claim_unit(run, "parent-chunk", "coord", now=13.0)
    assert c_chunk.ok
    chunk_gen = int(c_chunk.lease_generation or 0)
    assert ledger.commit_result(
        run,
        "parent-chunk",
        "coord",
        chunk_gen,
        "done",
        result_hash="partial",
        now=14.0,
    ).ok
    parent_before = ledger.get_chunk(run, "parent-chunk")
    assert parent_before is not None
    assert parent_before["state"] == ChunkLedgerState.DONE.value
    assert int(parent_before["lease_generation"]) == chunk_gen

    ok = ledger.retry_failed(run, "L2", "operator reopening failed constituent lemma", now=15.0)
    assert ok.ok

    lemma_after = ledger.get_work_unit(run, "L2")
    assert lemma_after is not None
    assert lemma_after["state"] == SchedulableState.PENDING.value
    assert int(lemma_after["attempt_count"]) == 0

    parent_after = ledger.get_chunk(run, "parent-chunk")
    assert parent_after is not None
    assert parent_after["state"] == ChunkLedgerState.PENDING.value
    assert parent_after["owner"] is None
    assert parent_after["leased_until"] is None
    # Generation preserved (CAS guard), owner cleared for reschedule.
    assert int(parent_after["lease_generation"]) == chunk_gen

    chunk_unit = ledger.get_work_unit(run, "parent-chunk")
    assert chunk_unit is not None
    assert chunk_unit["state"] == SchedulableState.PENDING.value
    assert "parent-chunk" in ledger.list_pending_chunk_ids(run)

    actions = (
        ledger._require()
        .execute(
            "SELECT payload_json FROM operator_actions WHERE run_id = ? AND action = ? ORDER BY action_id DESC LIMIT 1",
            (run, OperatorActionKind.RETRY_FAILED.value),
        )
        .fetchone()
    )
    assert actions is not None
    payload = json.loads(str(actions["payload_json"]))
    assert payload["unit_kind"] == "lemma"
    assert payload["parent_chunk_id"] == "parent-chunk"


def test_seal_large_chunk_no_sqlite_variable_limit(ledger: Ledger) -> None:
    """1500-lemma chunk seals via json_each join (no IN-list var blowup) (#5370)."""
    n = 1500
    lemmas = [f"lem-{i:04d}" for i in range(n)]
    fp = compute_run_fingerprint(cohort_digest="seal-1500")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_chunk_work_units(run, [("big-chunk", lemmas)])
    claim = ledger.claim_unit(run, "big-chunk", "coord", now=1.0)
    gen = int(claim.lease_generation or 0)
    assert ledger.commit_result(run, "big-chunk", "coord", gen, "done", result_hash="big", now=2.0).ok
    # Bulk-mark constituents terminal-successful (setup only; seal uses join).
    conn = ledger._require()
    conn.execute(
        "UPDATE work_units SET state = ?, result_hash = 'bulk', updated_at = 3.0 "
        "WHERE run_id = ? AND unit_kind = 'lemma' AND phase = ?",
        (UnitOutcome.DONE.value, run, "offline_enrich"),
    )
    # Leave one pending to prove the aggregate still finds offenders at scale,
    # then fix and seal cleanly.
    conn.execute(
        "UPDATE work_units SET state = ? WHERE run_id = ? AND unit_id = ?",
        (SchedulableState.PENDING.value, run, lemmas[1234]),
    )
    blocked = ledger.commit_seal(run, "big-chunk", "coord", gen, seal_sha256="big-seal", now=4.0)
    assert blocked.status is CasStatus.INVALID_STATE
    assert lemmas[1234] in blocked.detail

    conn.execute(
        "UPDATE work_units SET state = ? WHERE run_id = ? AND unit_id = ?",
        (UnitOutcome.DONE.value, run, lemmas[1234]),
    )
    sealed = ledger.commit_seal(run, "big-chunk", "coord", gen, seal_sha256="big-seal", now=5.0)
    assert sealed.ok, sealed.detail
    seal_row = conn.execute(
        "SELECT seal_sha256 FROM seals WHERE run_id = ? AND chunk_id = ?",
        (run, "big-chunk"),
    ).fetchone()
    assert seal_row is not None
    assert seal_row["seal_sha256"] == "big-seal"
    # Bound-parameter count stays O(1): re-run the same aggregate shape that
    # seal uses and confirm SQLite accepts it (would raise if rewritten as IN).
    rows = conn.execute(
        "SELECT COUNT(*) AS n FROM chunks c "
        "JOIN json_each(c.lemma_ids_json) AS je "
        "LEFT JOIN work_units wu "
        "  ON wu.run_id = c.run_id "
        " AND wu.unit_id = CAST(je.value AS TEXT) "
        " AND wu.phase = 'offline_enrich' "
        " AND wu.unit_kind = 'lemma' "
        "WHERE c.run_id = ? AND c.chunk_id = ?",
        (run, "big-chunk"),
    ).fetchone()
    assert int(rows["n"]) == n


def test_import_cas_and_stale_generation(ledger: Ledger) -> None:
    fp = compute_run_fingerprint(cohort_digest="import")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_work_unit(run, "lemma-i", unit_kind="lemma", phase="network_import")
    claim = ledger.claim_unit(run, "lemma-i", "imp", phase="network_import", now=1.0)
    gen = int(claim.lease_generation or 0)
    ok = ledger.commit_import(
        run,
        "lemma-i",
        "imp",
        gen,
        packet_generation=1,
        result_hash="body-1",
        expected_fingerprint=fp,
        now=2.0,
    )
    assert ok.ok
    # Re-import matching hash is no-op success.
    again = ledger.commit_import(
        run,
        "lemma-i",
        "imp",
        gen,
        packet_generation=1,
        result_hash="body-1",
        expected_fingerprint=fp,
        now=3.0,
    )
    assert again.ok
    # Fingerprint mismatch refused.
    bad_fp = ledger.commit_import(
        run,
        "lemma-j",
        "imp",
        1,
        packet_generation=1,
        result_hash="x",
        expected_fingerprint="nope",
        now=4.0,
    )
    assert bad_fp.status is CasStatus.FINGERPRINT_MISMATCH_REFUSED

    # Stale owner/generation on a leased unit.
    ledger.register_work_unit(run, "lemma-k", unit_kind="lemma", phase="network_import")
    c2 = ledger.claim_unit(run, "lemma-k", "imp2", phase="network_import", now=5.0)
    stale = ledger.commit_import(
        run,
        "lemma-k",
        "wrong-owner",
        int(c2.lease_generation or 0),
        packet_generation=2,
        result_hash="body-k",
        expected_fingerprint=fp,
        phase="network_import",
        now=6.0,
    )
    assert stale.status is CasStatus.STALE_COMMIT_REJECTED


def test_import_reclaimed_lease_rejected(ledger: Ledger) -> None:
    """After reclaim to PENDING, stale importer cannot commit_import (CAS bypass fix)."""
    fp = compute_run_fingerprint(cohort_digest="import-reclaim")
    run = ledger.start_run(fp).run_id
    assert run
    ledger.register_work_unit(run, "lemma-r", unit_kind="lemma", phase="network_import")
    claim = ledger.claim_unit(run, "lemma-r", "imp-old", phase="network_import", now=100.0)
    gen = int(claim.lease_generation or 0)
    reclaimed = ledger.reclaim_expired(run, now=10_000.0)
    assert "lemma-r" in reclaimed
    unit = ledger.get_work_unit(run, "lemma-r", phase="network_import")
    assert unit is not None
    assert unit["state"] == SchedulableState.PENDING.value

    stale = ledger.commit_import(
        run,
        "lemma-r",
        "imp-old",
        gen,
        packet_generation=7,
        result_hash="stale-body",
        expected_fingerprint=fp,
        phase="network_import",
        now=10_001.0,
    )
    assert stale.status is CasStatus.STALE_COMMIT_REJECTED
    # Import row must not exist after rejected stale commit.
    imports = (
        ledger._require()
        .execute(
            "SELECT COUNT(*) AS n FROM imports WHERE run_id = ? AND lemma_id = ?",
            (run, "lemma-r"),
        )
        .fetchone()
    )
    assert int(imports["n"]) == 0
    unit2 = ledger.get_work_unit(run, "lemma-r", phase="network_import")
    assert unit2 is not None
    assert unit2["state"] == SchedulableState.PENDING.value

    # Fresh claim + import still succeeds.
    c2 = ledger.claim_unit(run, "lemma-r", "imp-new", phase="network_import", now=10_002.0)
    assert c2.ok
    ok = ledger.commit_import(
        run,
        "lemma-r",
        "imp-new",
        int(c2.lease_generation or 0),
        packet_generation=7,
        result_hash="fresh-body",
        expected_fingerprint=fp,
        phase="network_import",
        now=10_003.0,
    )
    assert ok.ok
    unit3 = ledger.get_work_unit(run, "lemma-r", phase="network_import")
    assert unit3 is not None
    assert unit3["state"] == UnitOutcome.DONE.value
    assert unit3["result_hash"] == "fresh-body"


def test_abandon_packet_operator_record(ledger: Ledger) -> None:
    fp = compute_run_fingerprint(cohort_digest="pkt")
    run = ledger.start_run(fp).run_id
    assert run
    res = ledger.abandon_packet(run, "pkt-1", 3, "operator abandoned stale transport")
    assert res.ok
    assert ledger.count_operator_actions(run, OperatorActionKind.ABANDON_PACKET.value) == 1


def test_500_lemma_slice_resume_from_interrupted_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Resume continues the frozen 500-lemma offline slice after interruption."""
    _ensure_fixture()
    from scripts.lexicon import enrich_manifest as em
    from scripts.lexicon.runner.memory import EnforcementProof
    from scripts.lexicon.runner.offline_engine import enrich_offline_slice

    monkeypatch.setattr(em, "_vesum_valid_synonym", lambda term: bool(term))
    monkeypatch.setattr(
        "scripts.lexicon.runner.offline_engine.run_startup_self_test",
        lambda **_kwargs: EnforcementProof(
            kind="rlimit_as",
            enforced=True,
            detail="test stub",
            max_bytes=64 * 1024 * 1024,
        ),
    )

    # In-process enrich stub: write tiny artifacts without full sources.
    def _fake_enrich(payload: dict) -> dict[str, str]:
        import hashlib

        entries = json.loads(Path(payload["entries_path"]).read_text(encoding="utf-8"))
        artifact_dir = Path(payload["artifact_dir"])
        artifact_dir.mkdir(parents=True, exist_ok=True)
        arts: dict[str, str] = {}
        for entry in entries:
            lemma_id = str(entry.get("url_slug") or entry.get("lemma") or "")
            body = {"lemma": entry.get("lemma"), "url_slug": lemma_id, "enriched": True}
            raw = json.dumps(body, ensure_ascii=False, sort_keys=True)
            (artifact_dir / f"{lemma_id}.json").write_text(raw + "\n", encoding="utf-8")
            arts[lemma_id] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return arts

    monkeypatch.setattr(
        "scripts.lexicon.runner.worker_enrich.enrich_chunk_payload",
        _fake_enrich,
    )

    grac = json.loads((FIXTURE / "grac_frequency_slice.json").read_text(encoding="utf-8"))
    work = tmp_path / "runner_work"
    out1 = tmp_path / "candidate1.json"
    ledger_path = work / "ledger.sqlite"

    first = enrich_offline_slice(
        manifest_path=FIXTURE / "slice_input.json",
        sources_db=FIXTURE / "sources_slice.sqlite",
        kaikki_json=FIXTURE / "kaikki_slice.json",
        work_dir=work,
        output_path=out1,
        grac_cache=dict(grac),
        require_memory_self_test=False,
        skip_workers=True,
        chunk_size=50,
        ledger_path=ledger_path,
        stop_after_chunks=3,
        owner_id="resume-test-1",
    )
    assert "error" not in first, first
    assert first["interrupted"] is True
    assert first["processed_this_invocation"] == 3
    assert first["run_id"]
    run_id = first["run_id"]
    fingerprint = first["fingerprint"]

    # Same fingerprint start must refuse and point at resumable run.
    refuse = enrich_offline_slice(
        manifest_path=FIXTURE / "slice_input.json",
        sources_db=FIXTURE / "sources_slice.sqlite",
        kaikki_json=FIXTURE / "kaikki_slice.json",
        work_dir=work,
        output_path=tmp_path / "should_refuse.json",
        grac_cache=dict(grac),
        require_memory_self_test=False,
        skip_workers=True,
        chunk_size=50,
        ledger_path=ledger_path,
        owner_id="resume-test-refuse",
    )
    assert refuse.get("error") == CasStatus.INVALID_STATE.value
    assert refuse.get("resumable_run_id") == run_id

    out2 = tmp_path / "candidate2.json"
    second = enrich_offline_slice(
        manifest_path=FIXTURE / "slice_input.json",
        sources_db=FIXTURE / "sources_slice.sqlite",
        kaikki_json=FIXTURE / "kaikki_slice.json",
        work_dir=work,
        output_path=out2,
        grac_cache=dict(grac),
        require_memory_self_test=False,
        skip_workers=True,
        chunk_size=50,
        ledger_path=ledger_path,
        run_id=run_id,
        owner_id="resume-test-2",
    )
    assert "error" not in second, second
    assert second["run_id"] == run_id
    assert second["fingerprint"] == fingerprint
    assert second["interrupted"] is False
    # Resume must process remaining chunks (500/50=10 total; first did 3).
    assert second["processed_this_invocation"] == 7
    assert second["completed"] == 500

    lg = Ledger(ledger_path, owner_id="verify")
    lg.open()
    try:
        done = lg.list_completed_chunk_ids(run_id)
        assert len(done) == 10
        pending = lg.list_pending_chunk_ids(run_id)
        assert pending == []
        run_row = lg.get_run(run_id)
        assert run_row is not None
        assert run_row["status"] == "completed"
    finally:
        lg.close()

    candidate = json.loads(out2.read_text(encoding="utf-8"))
    assert candidate["ledger_run_id"] == run_id
    assert len(candidate["entries"]) == 500


def test_issue_streams_registers_5331_under_atlas_practice() -> None:
    import yaml

    doc = yaml.safe_load(Path("scripts/config/issue_streams.yaml").read_text(encoding="utf-8"))
    epics = doc["streams"]["atlas-practice"]["epics"]
    assert 5331 in epics
    assert 4387 in epics
    # Do not claim infra's issue.
    infra = doc["streams"]["infra-harness"]["epics"]
    assert 5331 not in infra
