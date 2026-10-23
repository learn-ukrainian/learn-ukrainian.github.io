"""Work ownership, membership and blocker provenance stay explicit (#10667 D04/D05)."""

from __future__ import annotations

from scripts.work.normalize import build_projection
from scripts.work.schema import validate_projection
from scripts.work.sources_public import SectionResult

REPO = "learn-ukrainian/learn-ukrainian.github.io"


def _sections(*, issues: list[dict] | None = None, prs: list[dict] | None = None) -> dict[str, SectionResult]:
    return {
        "issues": SectionResult("issues", "ok", payload=issues or []),
        "prs": SectionResult("prs", "ok", payload=prs or []),
        "streams": SectionResult(
            "streams",
            "ok",
            payload={
                "streams": {"infra-harness": [10]},
                "orphans": [],
                "open_stream_membership": {"10": ["infra-harness"]},
            },
        ),
        "delegate_active": SectionResult("delegate_active", "ok", payload={"tasks": []}),
        "delegate_tasks": SectionResult("delegate_tasks", "ok", payload={"tasks": []}),
        "fleet_reviews": SectionResult("fleet_reviews", "ok", payload={"reviews": []}),
    }


def _pr() -> dict:
    return {
        "number": 100,
        "title": "PR without a canonical task association",
        "state": "OPEN",
        "isDraft": False,
        "reviewDecision": "REVIEW_REQUIRED",
        "statusCheckRollup": [{"state": "SUCCESS"}],
        "mergeStateStatus": "BLOCKED",
        "labels": [],
        "assignees": [{"login": "operator"}],
        "url": f"https://github.com/{REPO}/pull/100",
        "createdAt": "2026-10-01T00:00:00Z",
        "updatedAt": "2026-10-02T00:00:00Z",
        "headRefOid": "deadbeef",
        "headRefName": "codex/impl-10667-b0-sol",
    }


def test_pr_owner_and_stream_stay_unknown_without_a_canonical_association() -> None:
    projection = build_projection(_sections(prs=[_pr()]), lifecycle_ledgers=[])
    validate_projection(projection)
    [row] = projection["items"]
    assert row["projections"]["dispatch"]["accountable_owner"] == "unknown"
    assert row["projections"]["dispatch"]["owner_reason"] == "owner_unknown"
    assert row["projections"]["stream"]["status"] == "n/a"
    # A branch prefix is not an accountable-owner or stream claim.
    assert "accountable_owner" not in row["projections"]["stream"]


def test_derived_blocker_is_not_a_posted_blocker_report() -> None:
    issue = {
        "number": 10,
        "title": "Blocked issue",
        "state": "OPEN",
        "labels": [],
        "assignees": [],
        "body": "Blocked by #11",
        "url": f"https://github.com/{REPO}/issues/10",
        "createdAt": "2026-10-01T00:00:00Z",
        "updatedAt": "2026-10-02T00:00:00Z",
    }
    projection = build_projection(_sections(issues=[issue]), lifecycle_ledgers=[])
    [row] = projection["items"]
    assert row["flags"]["has_blocker"] is True
    assert "posted_blocker" not in row
    assert "posted_blocker" not in row["flags"]
