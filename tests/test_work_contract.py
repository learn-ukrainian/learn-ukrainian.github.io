"""Contract and deterministic unit tests for the Work projection foundation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.work.attention import derive_health, derive_safe_next_action
from scripts.work.normalize import _match_dispatch, build_projection
from scripts.work.relations import (
    detect_dependency_cycles,
    extract_body_relations,
    issue_work_id,
    make_work_id,
)
from scripts.work.schema import (
    SCHEMA_VERSION,
    SchemaValidationError,
    load_schema,
    parse_saved_view_params,
    validate_projection,
)
from scripts.work.sources_public import SectionResult

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "work" / "projection_public_min.json"
REPO = "learn-ukrainian/learn-ukrainian.github.io"


def test_schema_loads_and_fixture_validates():
    schema = load_schema()
    assert schema["properties"]["schema_version"]["const"] == SCHEMA_VERSION
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    validate_projection(payload)
    assert payload["foundation_status"] == "FOUNDATION_COMPLETE"
    assert payload["foundation_status"] != "COMPLETE"
    assert payload["capabilities"]["mutation"] is False


def test_identity_serialization_is_collision_safe():
    a = make_work_id("public-monitor", REPO, "issue", "1")
    b = make_work_id("private-local-adapter", REPO, "issue", "1")
    assert a != b
    assert a.startswith("wp1:")
    assert a == issue_work_id(REPO, 1)


def test_saved_view_rejects_free_text_and_private_keys():
    with pytest.raises(SchemaValidationError):
        parse_saved_view_params({"q": "secret search"})
    with pytest.raises(SchemaValidationError):
        parse_saved_view_params({"private_endpoint": "http://127.0.0.1:9999"})
    with pytest.raises(SchemaValidationError):
        parse_saved_view_params({"health": "kinda-bad"})
    ok = parse_saved_view_params(
        {"health": "AT_RISK", "kind": "issue", "orphan": "true", "repository_id": REPO}
    )
    assert ok["health"] == ["AT_RISK"]
    assert ok["orphan"] is True


def test_saved_view_lifecycle_allowlist():
    ok = parse_saved_view_params({"lifecycle": "open"})
    assert ok["lifecycle"] == ["open"]
    with pytest.raises(SchemaValidationError, match="invalid lifecycle filter"):
        parse_saved_view_params({"lifecycle": "nonce-xyz-not-a-lifecycle"})


def test_relations_and_cycle_detection():
    body = "This blocks #2 and is blocked by #3. Duplicate of #4. Superseded-by: #5"
    rels = extract_body_relations(body, repository_id=REPO, self_number=1)
    types = {r["type"] for r in rels}
    assert "blocks" in types
    assert "blocked_by" in types
    assert "duplicate_of" in types
    assert "superseded_by" in types

    items = [
        {
            "work_id": issue_work_id(REPO, 1),
            "relationships": [
                {"type": "blocks", "target_id": issue_work_id(REPO, 2), "evidence": "t"}
            ],
        },
        {
            "work_id": issue_work_id(REPO, 2),
            "relationships": [
                {"type": "blocks", "target_id": issue_work_id(REPO, 1), "evidence": "t"}
            ],
        },
    ]
    cycles = detect_dependency_cycles(items)
    assert cycles
    assert issue_work_id(REPO, 1) in cycles[0]


def test_match_dispatch_requires_boundary_safe_issue_and_pr_ids():
    """Substring prefixes must not attach unrelated dispatch state.

    Regression: unanchored ``#1`` matched ``#19``; ``pr-10`` matched ``pr-100``.
    """
    tasks = [
        {"task_id": "codex-#19-fix", "status": "running", "agent": "codex"},
        {"task_id": "codex-issue-19", "status": "running", "agent": "codex"},
        {"task_id": "codex-issue_19", "status": "running", "agent": "codex"},
        {"task_id": "codex/19/work", "status": "running", "agent": "codex"},
        {"task_id": "worker-19", "status": "running", "agent": "codex"},
        {"task_id": "codex-#1-fix", "status": "running", "agent": "claude"},
        {"task_id": "codex-issue-1", "status": "running", "agent": "claude"},
        {"task_id": "codex-issue_1", "status": "running", "agent": "claude"},
        {"task_id": "codex/1/work", "status": "running", "agent": "claude"},
        {"task_id": "worker-1", "status": "running", "agent": "claude"},
        {"task_id": "agy-pr-100", "status": "running", "agent": "agy"},
        {"task_id": "agy-pr_100", "status": "running", "agent": "agy"},
        {"task_id": "agy-pr/100", "status": "running", "agent": "agy"},
        {"task_id": "review-pr100", "status": "running", "agent": "agy"},
        {"task_id": "agy-pr-10", "status": "running", "agent": "kimi"},
        {"task_id": "agy-pr_10", "status": "running", "agent": "kimi"},
        {"task_id": "agy-pr/10", "status": "running", "agent": "kimi"},
        {"task_id": "review-pr10", "status": "running", "agent": "kimi"},
        # Unrelated numeric text must not become authority for a match.
        {"task_id": "retrycount1of19", "status": "running", "agent": "cursor"},
        {"task_id": "shard10of100", "status": "running", "agent": "cursor"},
        {"task_id": "build100timeout", "status": "running", "agent": "cursor"},
        {"task_id": "page1", "status": "running", "agent": "cursor"},
        {"task_id": "v10-release", "status": "running", "agent": "cursor"},
    ]

    issue_1 = _match_dispatch(tasks, issue_number=1, pr_number=None)
    assert set(issue_1["task_ids"]) == {
        "codex-#1-fix",
        "codex-issue-1",
        "codex-issue_1",
        "codex/1/work",
        "worker-1",
    }
    assert "codex-#19-fix" not in issue_1["task_ids"]
    assert "codex-issue-19" not in issue_1["task_ids"]
    assert "retrycount1of19" not in issue_1["task_ids"]
    assert "page1" not in issue_1["task_ids"]

    issue_19 = _match_dispatch(tasks, issue_number=19, pr_number=None)
    assert set(issue_19["task_ids"]) == {
        "codex-#19-fix",
        "codex-issue-19",
        "codex-issue_19",
        "codex/19/work",
        "worker-19",
    }
    assert "codex-#1-fix" not in issue_19["task_ids"]
    assert "codex-issue-1" not in issue_19["task_ids"]
    assert "retrycount1of19" not in issue_19["task_ids"]

    pr_10 = _match_dispatch(tasks, issue_number=None, pr_number=10)
    assert set(pr_10["task_ids"]) == {
        "agy-pr-10",
        "agy-pr_10",
        "agy-pr/10",
        "review-pr10",
    }
    assert "agy-pr-100" not in pr_10["task_ids"]
    assert "review-pr100" not in pr_10["task_ids"]
    assert "shard10of100" not in pr_10["task_ids"]
    assert "v10-release" not in pr_10["task_ids"]

    pr_100 = _match_dispatch(tasks, issue_number=None, pr_number=100)
    assert set(pr_100["task_ids"]) == {
        "agy-pr-100",
        "agy-pr_100",
        "agy-pr/100",
        "review-pr100",
    }
    assert "agy-pr-10" not in pr_100["task_ids"]
    assert "review-pr10" not in pr_100["task_ids"]
    assert "build100timeout" not in pr_100["task_ids"]
    assert "shard10of100" not in pr_100["task_ids"]


def test_health_never_uses_activity_and_pr_rules():
    pr_fail = {
        "resource_kind": "pr",
        "lifecycle": "open",
        "flags": {},
        "projections": {
            "stream": {},
            "dispatch": {},
            "review": {"review_decision": "APPROVED"},
            "verification": {"ci_state": "failing"},
        },
    }
    assert derive_health(pr_fail, source_ok=True) == "OFF_TRACK"
    assert derive_safe_next_action(pr_fail)["code"] == "FIX_CI"

    orphan = {
        "resource_kind": "issue",
        "flags": {},
        "projections": {
            "stream": {"status": "orphan", "fresh": True},
            "dispatch": {"statuses": []},
            "review": {},
            "verification": {},
        },
    }
    assert derive_health(orphan, source_ok=True) == "AT_RISK"
    assert derive_safe_next_action(orphan)["code"] == "TRIAGE_ORPHAN"

    assert derive_health(orphan, source_ok=False) == "UNKNOWN"


def test_build_projection_joins_sources_deterministically():
    sections = {
        "issues": SectionResult(
            "issues",
            "ok",
            payload=[
                {
                    "number": 10,
                    "title": "Orphan issue",
                    "labels": [{"name": "agent"}],
                    "assignees": [],
                    "body": "blocked by #11",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "url": "https://example.test/issues/10",
                    "state": "OPEN",
                },
                {
                    "number": 11,
                    "title": "Blocker",
                    "labels": [],
                    "assignees": [],
                    "body": "blocks #10",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "url": "https://example.test/issues/11",
                    "state": "OPEN",
                },
            ],
            count=2,
        ),
        "prs": SectionResult(
            "prs",
            "ok",
            payload=[
                {
                    "number": 99,
                    "title": "Draft PR",
                    "state": "OPEN",
                    "isDraft": True,
                    "reviewDecision": "",
                    "statusCheckRollup": [{"state": "PENDING"}],
                    "mergeStateStatus": "BLOCKED",
                    "labels": [],
                    "assignees": [],
                    "url": "https://example.test/pull/99",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "headRefOid": "abc",
                    "headRefName": "feat/x",
                }
            ],
            count=1,
        ),
        "streams": SectionResult(
            "streams",
            "ok",
            payload={
                "generated_at": 1,
                "open_total": 2,
                "orphans": [{"number": 10, "title": "Orphan issue"}],
                "multi_homed": [],
                "pending_native_link": [],
                "ok": False,
            },
            count=2,
        ),
        "delegate_active": SectionResult(
            "delegate_active",
            "ok",
            payload={"total": 0, "tasks": []},
            count=0,
        ),
        "delegate_tasks": SectionResult(
            "delegate_tasks",
            "ok",
            payload={
                "total": 1,
                "tasks": [
                    {
                        "task_id": "unlinked-task-1",
                        "agent": "codex",
                        "status": "running",
                        "started_at": "2026-08-16T00:00:00Z",
                    }
                ],
            },
            count=1,
        ),
        "fleet_reviews": SectionResult(
            "fleet_reviews",
            "ok",
            payload={
                "total": 1,
                "reviews": [
                    {
                        "review_id": "rev-1",
                        "repository": REPO,
                        "pr_number": 99,
                        "head_sha": "abc",
                        "gate_kind": "code",
                        "state": "running",
                        "sealed_verdict_available": False,
                    }
                ],
            },
            count=1,
        ),
    }
    projection = build_projection(sections, repository_id=REPO)
    validate_projection(projection)
    assert projection["foundation_status"] == "FOUNDATION_COMPLETE"
    assert projection["capabilities"]["mutation"] is False
    assert projection["capabilities"]["private_source"]["available"] is False
    assert projection["denominator"]["issues_open"] == 2
    assert projection["denominator"]["prs_open"] == 1
    assert projection["denominator"]["class4"]["delegate_tasks"] is True

    ids = {item["work_id"] for item in projection["items"]}
    assert issue_work_id(REPO, 10) in ids
    assert any(i["resource_kind"] == "pr" for i in projection["items"])
    assert any(i["resource_kind"] == "task" for i in projection["items"])

    # Body text must not leak into the projection payload.
    blob = json.dumps(projection)
    assert "blocked by #11" not in blob
    assert "blocks #10" not in blob

    ranks = [a["attention_rank"] for a in projection["attention"]]
    assert ranks == sorted(ranks)
    # Deterministic: same inputs → same first attention id
    again = build_projection(sections, repository_id=REPO)
    assert again["attention"][0]["work_id"] == projection["attention"][0]["work_id"]
