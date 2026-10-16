"""#10437: fixed consumer handling, with a census and behavior probes."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.fleet_comms import review_publication, review_publisher
from scripts.orchestration import integration_sweep as sweep
from scripts.orchestration import merge_queue_keeper as keeper
from scripts.review.record_cf_verdict import build_comment

# Publication and telemetry readers are included so a new reference cannot
# silently enter the approval path. These are handling labels, not endorsements.
HANDLING = {
    "scripts/orchestration/merge_queue_keeper.py": "accept-as-approval",
    "scripts/orchestration/integration_sweep.py": "accept-as-approval",
    "scripts/publish/github.py": "accept-as-approval",
    "scripts/fleet_comms/review_publisher.py": "accept-as-approval",
    "scripts/api/fleet_board/prs.py": "display-label",
    "scripts/fleet_comms/review_publication.py": "ignore",
    "scripts/lexicon/published_record_dispositions.py": "refuse",
    "scripts/orchestration/integration_sweep.py#CI-blocker-exclusion": "ignore",
    "scripts/review/record_cf_verdict.py": "accept-as-approval",
    "scripts/fleet_comms/cli.py": "ignore",
    "scripts/fleet_comms/efficiency_metrics.py": "ignore",
    "scripts/entire_context/resolvers.py": "ignore",
}


def _mentions_review_contract(tree: ast.AST) -> bool:
    names = {"DEFAULT_STATUS_CONTEXT", "lookup_verdict", "parse_marker", "MARKER_PREFIX"}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and ("cf-verdict" in node.value or "fleet/cross-family-review" in node.value)
        ):
            return True
        if (
            isinstance(node, (ast.Name, ast.Attribute))
            and (node.id if isinstance(node, ast.Name) else node.attr) in names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and any(alias.name in names for alias in node.names):
            return True
    return False


@pytest.mark.repo_wide
def test_every_marker_or_status_consumer_has_a_fixed_handling_row():
    root = Path(__file__).resolve().parents[1]
    consumers = {
        path.relative_to(root).as_posix()
        for path in (root / "scripts").rglob("*.py")
        if _mentions_review_contract(ast.parse(path.read_text(encoding="utf-8")))
    }
    assert consumers == {path.split("#", 1)[0] for path in HANDLING}
    assert set(HANDLING.values()) == {"accept-as-approval", "display-label", "refuse", "ignore"}


@pytest.mark.parametrize(
    "source",
    [
        "from scripts.orchestration.integration_sweep import lookup_verdict as renamed",
        "import scripts.orchestration.integration_sweep as review\nreview.lookup_verdict([], '', '')",
        "context = 'fleet/cross-family-review'",
        "marker = '<!-- cf-verdict v1'",
    ],
)
def test_consumer_census_detects_new_references(source):
    assert _mentions_review_contract(ast.parse(source))


def _comment(mode="red_team", *, login="fleet"):
    from tests.orchestration.test_integration_sweep import comment

    return comment(review_mode=mode, login=login)


def test_keeper_and_sweep_accept_red_team_approval(tmp_path):
    from tests.orchestration.test_integration_sweep import SHA, pr
    from tests.orchestration.test_merge_queue_keeper import FakeGitHub, mutations, recorded

    fake = FakeGitHub()
    fake.comments_rows = [recorded("APPROVED", "2026-09-23T12:00:00.000001+00:00", review_mode="red_team")]
    lines, failed = keeper.run(fake, tmp_path / "keeper.json", apply=True)
    assert failed is False and mutations(fake) == ["enqueue"]
    assert "reason=ready" in lines[0]
    verdict = sweep.lookup_verdict([_comment()], SHA, "fleet")
    assert sweep.classify_pr(pr(), verdict, queued=False, observed_at="2026-10-11T00:00:00Z").state == "ready"
    assert keeper._recorded_approval_for_head([_comment()], SHA, "fleet") is True
    assert HANDLING["scripts/orchestration/merge_queue_keeper.py"] == "accept-as-approval"
    assert HANDLING["scripts/orchestration/integration_sweep.py"] == "accept-as-approval"


def test_fleet_board_counts_red_team_as_ready():
    """#10452 AC-02: display the mode, and do not present it as an ordinary approval."""
    from scripts.api.fleet_board import prs
    from tests.api.test_fleet_board_prs import _mq, _pull, _view
    from tests.orchestration.test_integration_sweep import SHA

    pull = _pull(sha=SHA)
    comment = _comment(login="fleet")
    view = _view(pull, login="fleet", comments={pull.number: (comment,)})
    cf = prs._cf(pull, view)
    ordinary = prs._cf(
        pull,
        _view(pull, login="fleet", comments={pull.number: (_comment("cross_family"),)}),
    )
    assert cf == {"verdict": "APPROVED", "at_head": True, "review_mode": "red_team"}
    assert ordinary == {"verdict": "APPROVED", "at_head": True}
    assert cf.keys() - ordinary.keys() == {"review_mode"}
    assert prs._verdict_at((comment,), "fleet") is not None
    _, ready, minutes = prs._ready_minutes(
        pull,
        ci="green",
        cf=cf,
        mq_status="not_queued",
        hold=False,
        mq=_mq(since={f"{pull.number}:{SHA}": "2026-10-11T00:00:00Z"}),
        now=datetime(2026, 10, 11, 1, tzinfo=UTC),
        threshold=30,
    )
    assert ready is True and minutes == 60
    assert HANDLING["scripts/api/fleet_board/prs.py"] == "display-label"


def test_ci_blocker_exclusion_ignores_review_status():
    from tests.orchestration.test_integration_sweep import pr

    pull = pr()
    pull["statusCheckRollup"].append({"context": "fleet/cross-family-review", "state": "FAILURE"})
    assert sweep._check_blockers(pull) == []
    assert HANDLING["scripts/orchestration/integration_sweep.py#CI-blocker-exclusion"] == "ignore"


def test_publication_ignores_marker_and_publisher_accepts_sealed_approval(monkeypatch):
    from tests.test_fleet_comms_review_publication import _approved_evidence, _sealed

    sealed = review_publication.parse_sealed_verdict_payload(
        _sealed(
            review_evidence=_approved_evidence(),
            review_mode="red_team",
            marker="invalid marker",
        )
    )
    plan = review_publication.plan_publication(sealed, current_head_sha=sealed.head_sha, mutate=True)
    assert plan.status_state == "success"
    assert "review_mode=red_team" not in plan.comment_body
    assert review_publication.DEFAULT_STATUS_CONTEXT == "fleet/cross-family-review"
    statuses = []
    monkeypatch.setattr(review_publisher, "post_pr_comment", lambda **_kwargs: "https://example.com/comment")
    monkeypatch.setattr(review_publisher, "post_commit_status", lambda **kwargs: statuses.append(kwargs))
    assert review_publisher.execute_publication(plan).status_posted is True
    assert statuses[0]["context"] == "fleet/cross-family-review"
    assert statuses[0]["state"] == "success"
    assert "review_mode" not in statuses[0]["description"]
    assert HANDLING["scripts/fleet_comms/review_publication.py"] == "ignore"
    assert HANDLING["scripts/fleet_comms/review_publisher.py"] == "accept-as-approval"


def test_lexicon_dispositions_refuse_red_team(tmp_path):
    from scripts.lexicon import published_record_dispositions as dispositions
    from tests.test_published_record_dispositions import native_receipt

    row, hold_digest = {"row_id": "release-fixture"}, "b" * 64
    digest = dispositions.canonical_sha256(row)
    receipt = json.dumps(native_receipt())
    for mode in ("cross_family", "red_team"):
        body = build_comment(
            sha="a" * 40,
            task_id="review-fixture",
            started="2026-10-11T00:00:00.000001+00:00",
            verdict="APPROVED",
            model="claude-opus-5-5",
            family="anthropic",
            review_mode=mode,
            reply=f"release-row-sha256: {digest}\nsuperseded-hold-row-sha256: {hold_digest}",
        )
        bindings = [
            {
                "row_sha256": digest,
                "superseded_row_sha256": hold_digest,
                "receipt_json": receipt,
                "receipt_sha256": hashlib.sha256(receipt.encode()).hexdigest(),
                "verdict_body": body,
                "verdict_sha256": hashlib.sha256(body.encode()).hexdigest(),
            }
        ]
        if mode == "red_team":
            with pytest.raises(ValueError, match="cross-family APPROVED verdict"):
                dispositions._validate_release_review(tmp_path, row, hold_digest, bindings)
        else:
            dispositions._validate_release_review(tmp_path, row, hold_digest, bindings)
    assert HANDLING["scripts/lexicon/published_record_dispositions.py"] == "refuse"


def test_recovery_accepts_red_team_approval(tmp_path, monkeypatch):
    from scripts.publish import github
    from tests import test_ci_recovery

    monkeypatch.setattr(github.recovery, "ledger_path", lambda _cwd: tmp_path / "recovery.sqlite3")
    monkeypatch.setattr(
        test_ci_recovery, "build_comment", lambda **kwargs: build_comment(**kwargs, review_mode="red_team")
    )
    transport = test_ci_recovery.Transport()
    # Exercise recovery admission only, through an entirely local transport.
    record = github._prepare_recovery(
        "run-rerun",
        {"number": 123},
        "unit/public",
        tmp_path,
        {},
        transport,
    )
    assert record[2] == transport.head
    assert transport.writes == []
    assert HANDLING["scripts/publish/github.py"] == "accept-as-approval"
