"""An unpublished verdict that a later verdict of its own seat superseded (``review_lineage.superseded_runs``)."""

from __future__ import annotations

import pytest

from scripts.review import record_cf_verdict as recorder
from scripts.review.review_lineage import LineageRefused, ReviewRun, check_lineage, superseded_runs

EARLY = "1" * 40
APPROVED = "2" * 40
CANDIDATE = "3" * 40
SEATS = {"openai": ("gpt-6.1-sol", "codex"), "anthropic": ("claude-opus-5-5", "claude")}


def started(minute):
    return f"2026-10-28T20:{minute:02d}:00.000001+00:00"


def review(task, sha, reply, *, minute, family="openai", profile="code", status="done", publish=True, **marker):
    """A review run and, when ``publish``, the verdict comment the recorder would post for it."""
    model, agent = SEATS[family]
    record = {
        "task_id": task,
        "worktree_base_sha": sha,
        "pinned_head": sha,
        "model": model,
        "agent": agent,
        "started_at": started(minute),
        "status": status,
        "review_profile": profile,
    }
    if profile == "ukrainian":
        record["sources_mcp_call_count"] = 3
    run = ReviewRun(task, record, reply)
    if not publish:
        return run, None
    fields = dict(
        sha=sha,
        task_id=task,
        started=started(minute),
        verdict=recorder.normalize_verdict(reply),
        model=model,
        family=family,
        reply=reply,
        review_profile=profile,
        sources_mcp_call_count=3 if profile == "ukrainian" else None,
    )
    fields.update(marker)
    stamp = f"2026-10-28T21:{minute:02d}:00Z"
    comment = {
        "id": minute,
        "body": recorder.build_comment(**fields),
        "user": {"login": "fleet"},
        "author_association": "MEMBER",
        "created_at": stamp,
        "updated_at": stamp,
    }
    return run, comment


def lineage(*pairs, approved=APPROVED, exclude_head=None):
    runs = [run for run, _ in pairs]
    comments = sorted((comment for _, comment in pairs if comment), key=lambda item: item["created_at"])
    seats = check_lineage(runs=runs, comments=comments, login="fleet", approved=approved, exclude_head=exclude_head)
    return seats, superseded_runs(runs=runs, comments=comments, login="fleet", exclude_head=exclude_head)


def report(*pairs, exclude_head=None):
    comments = sorted((comment for _, comment in pairs if comment), key=lambda item: item["created_at"])
    return superseded_runs(runs=[run for run, _ in pairs], comments=comments, login="fleet", exclude_head=exclude_head)


ORPHAN_REJECTION = "VERDICT: REQUEST_CHANGES\nF1 [P1] scripts/unit.py:1 the guard drops a case."


def test_a_later_same_seat_approve_supersedes_an_unpublished_rejection_and_keeps_it_listed():
    orphan = review("sol-r1", EARLY, ORPHAN_REJECTION, minute=1, publish=False)
    witness = review("sol-r2", APPROVED, "VERDICT: APPROVE", minute=2)
    with pytest.raises(LineageRefused, match="review task sol-r1 finished but its verdict is unpublished"):
        lineage(orphan)
    seats, superseded = lineage(orphan, witness)
    assert seats == ["openai"]
    assert superseded == [
        {
            "task": "sol-r1",
            "started": started(1),
            "head": EARLY,
            "verdict": "CHANGES_REQUESTED",
            "findings": recorder._review_verdict_and_count(ORPHAN_REJECTION)[1],
            "model": "gpt-6.1-sol",
            "family": "openai",
            "profile": "code",
            "superseded_by": {
                "task": "sol-r2",
                "started": started(2),
                "head": APPROVED,
                "verdict": "APPROVED",
                "model": "gpt-6.1-sol",
            },
        }
    ]


@pytest.mark.parametrize(
    "seat", [{"family": "anthropic"}, {"profile": "ukrainian"}], ids=["other-family", "other-profile"]
)
def test_another_seats_verdict_supersedes_nothing(seat):
    orphan = review("sol-r1", EARLY, "VERDICT: APPROVE", minute=1, publish=False)
    witness = review("other-r2", APPROVED, "VERDICT: APPROVE", minute=2, **seat)
    assert report(orphan, witness) == []
    with pytest.raises(LineageRefused, match="review task sol-r1 finished but its verdict is unpublished"):
        lineage(orphan, witness)


@pytest.mark.parametrize("orphan_head,orphan_minute", [(APPROVED, 1), (EARLY, 3)], ids=["same-head", "older-witness"])
def test_a_same_head_or_older_witness_supersedes_nothing(orphan_head, orphan_minute):
    witness = review("sol-r2", APPROVED, "VERDICT: APPROVE", minute=2)
    orphan = review("sol-late", orphan_head, "VERDICT: APPROVE", minute=orphan_minute, publish=False)
    assert report(orphan, witness) == []
    with pytest.raises(LineageRefused, match="review task sol-late finished but its verdict is unpublished"):
        lineage(orphan, witness)


def test_an_approval_at_the_candidate_head_never_supersedes_to_prove_the_approved_head():
    opus = review("opus-r2", APPROVED, "VERDICT: APPROVE", minute=2, family="anthropic")
    orphan = review("sol-r2", APPROVED, "VERDICT: APPROVE", minute=2, publish=False)
    at_candidate = review("sol-r3", CANDIDATE, "VERDICT: APPROVE", minute=3)
    assert report(opus, orphan, at_candidate, exclude_head=CANDIDATE) == []
    with pytest.raises(LineageRefused, match="review task sol-r2 finished but its verdict is unpublished"):
        lineage(opus, orphan, at_candidate, exclude_head=CANDIDATE)


def _edited(pair):
    run, comment = pair
    return run, {**comment, "updated_at": "2026-10-28T23:59:00Z"}


def _unattested(pair):
    run, comment = pair
    return ReviewRun(run.task_id, {**run.record, "model": "unknown-model"}, run.reply), comment


def _pinned(pair, pin):
    run, comment = pair
    return ReviewRun(run.task_id, {**run.record, "pinned_head": pin}, run.reply), comment


UNSUPERSEDED = "review task sol-r1 finished but its verdict is unpublished"


@pytest.mark.parametrize(
    "damage,refusal",
    [
        (
            lambda: review("sol-r2", APPROVED, "VERDICT: APPROVE", minute=2, verdict="CHANGES_REQUESTED"),
            "published verdict of sol-r2 conflicts with its task record",
        ),
        (lambda: _edited(review("sol-r2", APPROVED, "VERDICT: APPROVE", minute=2)), "was edited"),
        (
            lambda: _unattested(review("sol-r2", APPROVED, "VERDICT: APPROVE", minute=2)),
            "review task sol-r2 evidence refused",
        ),
        (
            lambda: review("sol-r2", APPROVED, "VERDICT: APPROVE", minute=2, status="failed"),
            r"review task sol-r2 \(failed\) carries an unpublished verdict",
        ),
        # A witness pinned to another head, or to no valid head, is evidence the recorder refuses.
        (lambda: _pinned(review("sol-r2", APPROVED, "VERDICT: APPROVE", minute=2), CANDIDATE), UNSUPERSEDED),
        (lambda: _pinned(review("sol-r2", APPROVED, "VERDICT: APPROVE", minute=2), "invalid-sha"), UNSUPERSEDED),
        (lambda: _pinned(review("sol-r2", APPROVED, "VERDICT: APPROVE", minute=2), []), UNSUPERSEDED),
    ],
    ids=[
        "conflicting-marker",
        "edited-marker",
        "unattested-reviewer",
        "unfinished-run",
        "pinned-elsewhere",
        "pinned-invalid",
        "pinned-malformed",
    ],
)
def test_a_malformed_witness_supersedes_nothing_and_the_lineage_still_refuses(damage, refusal):
    orphan = review("sol-r1", EARLY, "VERDICT: APPROVE", minute=1, publish=False)
    witness = damage()
    assert report(witness, orphan) == []
    # The witness is read first, so its own defect is the refusal.
    with pytest.raises(LineageRefused, match=refusal):
        lineage(witness, orphan)


def _crashed(task, *, provider_pgid=None, result_sha256=None, include_provider=True, status="crashed"):
    """A terminal run with no reply. Provider fields are omitted when ``include_provider`` is false."""
    record = {
        "task_id": task,
        "worktree_base_sha": EARLY,
        "pinned_head": EARLY,
        "model": "gpt-6.1-sol",
        "agent": "codex",
        "started_at": started(4),
        "status": status,
        "review_profile": "code",
    }
    if include_provider:
        record["provider_pgid"] = provider_pgid
        record["result_sha256"] = result_sha256
    return ReviewRun(task, record, None)


def test_a_crashed_run_with_no_provider_pgid_and_no_reply_is_admitted():
    """Defect class: a supervisor crash before any provider starts leaves no reply and blocks the lineage forever.

    A terminal non-done run is admitted as carrying no verdict when ``provider_pgid`` is null or
    absent and there is no result digest, which is the PR #12894 shape (status crashed, both null).
    """
    approve = review("sol-ok", APPROVED, "VERDICT: APPROVE", minute=1)
    for name, run in (
        ("null", _crashed("crashed-null")),
        ("absent", _crashed("crashed-absent", include_provider=False)),
    ):
        seats, superseded = lineage(approve, (run, None))
        assert seats == ["openai"], name
        assert superseded == [], name


def test_a_crashed_run_with_a_provider_pgid_and_no_reply_is_still_refused():
    """Defect class: a crashed review that started a provider and left no reply is not proof of no verdict.

    ``provider_pgid`` on the task record means a provider may have run, so the missing reply still refuses.
    """
    approve = review("sol-ok", APPROVED, "VERDICT: APPROVE", minute=1)
    crashed = _crashed("crashed-ran", provider_pgid=370101)
    with pytest.raises(LineageRefused, match=r"review task crashed-ran \(crashed\) has no reply on record"):
        lineage(approve, (crashed, None))


def test_a_published_verdict_naming_a_never_started_run_is_refused():
    """Defect class: a published verdict cannot belong to a review run that never started a provider.

    Admitting the missing reply must not claim the run, so a marker that names it has no finished review.
    """
    run, comment = review("never-ran", APPROVED, "VERDICT: APPROVE", minute=1, status="crashed")
    never = ReviewRun(run.task_id, {**run.record, "provider_pgid": None, "result_sha256": None}, None)
    with pytest.raises(LineageRefused, match="published verdict of task never-ran has no review run on record"):
        lineage((never, comment))


@pytest.mark.parametrize(
    "status,provider_pgid,result_sha256",
    [("crashed", None, "ab" * 32), ("done", None, None)],
    ids=["result-digest", "done-run"],
)
def test_a_missing_reply_without_proof_the_provider_never_ran_is_still_refused(status, provider_pgid, result_sha256):
    """Defect class: a missing reply is admitted only for a non-done run whose record proves no provider ran.

    A result digest means a provider may have produced a verdict, and a ``done`` run is unchanged.
    """
    approve = review("sol-ok", APPROVED, "VERDICT: APPROVE", minute=1)
    missing = _crashed("missing-reply", provider_pgid=provider_pgid, result_sha256=result_sha256, status=status)
    with pytest.raises(LineageRefused, match=rf"review task missing-reply \({status}\) has no reply on record"):
        lineage(approve, (missing, None))
