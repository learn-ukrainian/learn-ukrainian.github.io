"""Bounded merged-PR history is qualified independently from open PRs (#10667 D04)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from scripts.work.normalize import build_projection, qualify_pr_snapshot_age
from scripts.work.schema import validate_projection
from scripts.work.sources_public import SectionResult

REPO = "learn-ukrainian/learn-ukrainian.github.io"


def _sections(*, history: SectionResult | None = None, prs: SectionResult | None = None) -> dict[str, SectionResult]:
    sections = {
        "issues": SectionResult("issues", "ok", payload=[]),
        "prs": prs or SectionResult("prs", "ok", payload=[]),
        "streams": SectionResult("streams", "ok", payload={"streams": {}}),
        "delegate_active": SectionResult("delegate_active", "ok", payload={"tasks": []}),
        "delegate_tasks": SectionResult("delegate_tasks", "ok", payload={"tasks": []}),
        "fleet_reviews": SectionResult("fleet_reviews", "ok", payload={"reviews": []}),
    }
    if history is not None:
        sections["prs_merged"] = history
    return sections


def _merged_row(number: int = 71) -> dict:
    return {
        "number": number,
        "state": "MERGED",
        "mergedAt": "2026-10-14T12:00:00Z",
        "mergeCommit": {"oid": "b" * 40},
        "title": "Merged fixture",
        "labels": [],
        "assignees": [],
        "detailReadComplete": False,
    }


def test_merged_history_is_a_real_merge_fact_not_an_open_row() -> None:
    projection = build_projection(
        _sections(history=SectionResult("prs_merged", "ok", payload=[_merged_row()], count=1)),
        lifecycle_ledgers=[],
    )
    validate_projection(projection)
    [row] = projection["items"]
    assert row["remote_id"] == "71"
    assert row["lifecycle"] == "merged"
    assert row["projections"]["verification"]["merged_at"] == "2026-10-14T12:00:00Z"
    assert row["projections"]["verification"]["merge_commit_sha"] == "b" * 40
    assert row["flags"]["pr_history"] is True
    assert row["safe_next_action"] == {
        "code": "NONE",
        "reason_codes": ["pr_terminal_historical"],
        "state": "none",
    }
    assert row["flags"]["attention"] is False
    assert projection["denominator"]["prs_open"] == 0
    assert projection["sources"][0]["sections"]["prs_merged"]["count"] == 1


def test_closed_pull_without_merge_timestamp_is_not_merged() -> None:
    row = {"number": 72, "state": "CLOSED", "mergedAt": None, "title": "Rejected"}
    projection = build_projection(
        _sections(history=SectionResult("prs_merged", "ok", payload=[row], count=1)),
        lifecycle_ledgers=[],
    )
    # The collector filters these rows; the normalizer also refuses the badge.
    assert all(item["lifecycle"] != "merged" for item in projection["items"])


def test_merged_history_missing_is_an_explicit_omission_not_an_empty_success() -> None:
    projection = build_projection(_sections(), lifecycle_ledgers=[])
    assert not any(item["resource_kind"] == "pr" for item in projection["items"])
    # A manually assembled projection without the history section stays compatible.
    assert not any(o["class"] == "prs_merged" for o in projection["denominator"]["omissions"])

    omitted = build_projection(
        _sections(
            history=SectionResult(
                "prs_merged",
                "unavailable",
                reason="gh_pr_snapshot_missing",
                age_s=None,
                observed_at=None,
            )
        ),
        lifecycle_ledgers=[],
    )
    assert any(o["class"] == "prs_merged" for o in omitted["denominator"]["omissions"])


def test_stale_history_section_marks_history_rows_unknown() -> None:
    observed = (datetime.now(UTC) - timedelta(seconds=90)).isoformat()
    payload = build_projection(
        _sections(
            history=SectionResult(
                "prs_merged",
                "ok",
                payload=[_merged_row()],
                count=1,
                observed_at=observed,
                age_s=90,
            )
        ),
        lifecycle_ledgers=[],
    )
    qualified = qualify_pr_snapshot_age(payload)
    [row] = qualified["items"]
    assert row["lifecycle"] == "merged"
    assert row["health"] == "UNKNOWN"
    assert row["safe_next_action"]["code"] == "INSPECT_UNKNOWN"
    assert row["projections"]["verification"]["merge_evidence"]["state"] == "unknown"


def test_merged_runner_keeps_only_github_merge_evidence() -> None:
    from scripts.work.sources_public import fetch_merged_prs

    calls: list[list[str]] = []

    def runner(args: list[str], _timeout: float) -> tuple[int, str, str]:
        calls.append(args)
        return (
            0,
            '[{"number": 1, "mergedAt": "2026-10-14T12:00:00Z", "state": "MERGED"},'
            ' {"number": 2, "mergedAt": null, "state": "CLOSED"}]',
            "",
        )

    section = fetch_merged_prs(runner=runner)
    assert section.name == "prs_merged"
    assert section.status == "ok"
    assert [row["number"] for row in section.payload] == [1]
    assert calls and calls[0][calls[0].index("--state") + 1] == "merged"
    assert "mergedAt" in calls[0][calls[0].index("--json") + 1]


def test_merged_runner_failure_is_typed_and_never_an_empty_success() -> None:
    from scripts.work.sources_public import fetch_merged_prs

    section = fetch_merged_prs(runner=lambda _args, _timeout: (124, "", "timeout"))
    assert section.name == "prs_merged"
    assert section.status == "timeout"
    assert section.reason == "gh_pr_list_timeout"
    assert section.payload is None
