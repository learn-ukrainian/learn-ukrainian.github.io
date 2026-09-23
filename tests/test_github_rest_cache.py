"""REST ETag cache and the Monitor/Work poller contracts (#8535)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

import scripts.api.main as api_main
import scripts.api.state_helpers as state_helpers
import scripts.github_rest_cache as github_rest
from scripts.api.main import app
from scripts.api.state_helpers import cache_invalidate
from scripts.work.attention import _pr_check_state
from scripts.work.normalize import _assignee_logins, _label_names
from scripts.work.sources_public import (
    SectionResult,
    fetch_issue_states_batched,
    fetch_open_issues,
)

REPO = "learn-ukrainian/learn-ukrainian.github.io"
SHA = "a" * 40
client = TestClient(app, raise_server_exceptions=False)


def _transport_from(script):
    calls: list[tuple[str, str | None]] = []

    def transport(path: str, headers: dict[str, str], timeout: float):
        calls.append((path, headers.get("If-None-Match")))
        return script(path, headers, timeout, len(calls))

    return calls, transport


def test_etag_is_stored_and_sent_on_the_next_request():
    calls, transport = _transport_from(
        lambda path, headers, timeout, n: (
            (200, {"etag": '"v1"'}, b'[{"number": 1}]') if n == 1 else (304, {"etag": '"v1"'}, b"")
        )
    )
    cache = github_rest.GitHubRestCache(transport=transport)

    first = cache.get_json("repos/o/r/issues?state=open", timeout=1.0)
    second = cache.get_json("repos/o/r/issues?state=open", timeout=1.0)

    assert first.status == 200
    assert calls[0][1] is None
    assert calls[1][1] == '"v1"'
    assert second.status == 304
    assert second.not_modified is True
    assert second.body == [{"number": 1}]
    assert second.body == first.body


def test_304_serves_cached_body_and_ignores_a_replacement_payload():
    calls, transport = _transport_from(
        lambda path, headers, timeout, n: (
            (200, {"etag": 'W/"one"', "link": '<https://api.github.com/next>; rel="next"'}, b"[1]")
            if n == 1
            else (304, {"etag": '"two"'}, b"[999]")
        )
    )
    cache = github_rest.GitHubRestCache(transport=transport)

    first = cache.get_json("repos/o/r/issues?state=open", timeout=1.0)
    second = cache.get_json("repos/o/r/issues?state=open", timeout=1.0)

    assert first.body == [1]
    assert second.body == [1]
    assert second.link_next == "https://api.github.com/next"
    assert calls[1][1] == 'W/"one"'
    assert cache.cached_body("repos/o/r/issues?state=open") == [1]


def test_non_304_replaces_the_cached_body_and_etag():
    payloads = [b'[{"n": 1}]', b'[{"n": 2}]']
    etags = ['"a"', '"b"']

    def script(path, headers, timeout, n):
        if n == 3:
            return 304, {"etag": '"b"'}, b""
        index = n - 1
        return 200, {"etag": etags[index]}, payloads[index]

    calls, transport = _transport_from(script)
    cache = github_rest.GitHubRestCache(transport=transport)

    first = cache.get_json("repos/o/r/pulls?state=open", timeout=1.0)
    second = cache.get_json("repos/o/r/pulls?state=open", timeout=1.0)
    cache.get_json("repos/o/r/pulls?state=open", timeout=1.0)

    assert first.body == [{"n": 1}]
    assert second.body == [{"n": 2}]
    assert calls[1][1] == '"a"'
    assert calls[2][1] == '"b"'


def test_error_is_not_cached_and_the_previous_etag_is_replayed():
    def script(path, headers, timeout, n):
        if n == 1:
            return 200, {"etag": '"v1"'}, b'[{"ok": 1}]'
        if n == 2:
            return 500, {"etag": '"err"'}, b'{"message": "boom"}'
        return 304, {"etag": '"v1"'}, b'[{"ok": 999}]'

    calls, transport = _transport_from(script)
    cache = github_rest.GitHubRestCache(transport=transport)

    first = cache.get_json("repos/o/r/issues?state=open", timeout=1.0)
    with pytest.raises(github_rest.GitHubRestError):
        cache.get_json("repos/o/r/issues?state=open", timeout=1.0)
    third = cache.get_json("repos/o/r/issues?state=open", timeout=1.0)

    assert first.body == [{"ok": 1}]
    assert third.body == [{"ok": 1}]
    assert calls[1][1] == '"v1"'
    assert calls[2][1] == '"v1"'
    assert cache.cached_body("repos/o/r/issues?state=open") == [{"ok": 1}]


def test_issue_projection_keeps_only_fields_consumers_read():
    projected = github_rest.project_issue(
        {
            "number": 9,
            "title": "Public issue",
            "state": "open",
            "body": "blocked by #1",
            "created_at": "2026-08-01T00:00:00Z",
            "updated_at": "2026-08-02T00:00:00Z",
            "html_url": f"https://github.com/{REPO}/issues/9",
            "labels": [{"name": "bug", "color": "red"}],
            "assignees": [{"login": "octocat", "id": 1}],
            "node_id": "I_kw",
            "user": {"login": "someone"},
        }
    )

    assert set(projected) == {
        "number",
        "title",
        "labels",
        "body",
        "createdAt",
        "updatedAt",
        "assignees",
        "url",
        "state",
    }
    assert projected["state"] == "OPEN"
    assert projected["labels"] == [{"name": "bug"}]
    assert _label_names(projected["labels"]) == ["bug"]
    assert _assignee_logins(projected["assignees"]) == ["octocat"]
    assert "node_id" not in projected
    assert projected["body"] == "blocked by #1"


def test_pull_projection_matches_work_and_idle_consumers():
    updated = "2026-08-13T08:00:00Z"
    now = datetime(2026, 8, 13, 12, tzinfo=UTC)
    projected = github_rest.project_pull_request(
        {
            "number": 77,
            "title": "Ship it",
            "state": "open",
            "draft": False,
            "head": {"ref": "cursor/example", "sha": SHA},
            "updated_at": updated,
            "created_at": "2026-08-01T00:00:00Z",
            "html_url": f"https://github.com/{REPO}/pull/77",
            "labels": [{"name": "area:infra", "color": "ededed"}],
            "assignees": [{"login": "octocat"}],
            "body": "not a consumer field",
            "node_id": "PR_kw",
        },
        pull={"mergeable_state": "clean", "requested_reviewers": []},
        check_runs=[
            {
                "name": "CI Gate",
                "status": "completed",
                "conclusion": "success",
                "started_at": updated,
                "completed_at": "2026-08-13T08:10:00Z",
            }
        ],
        statuses=[{"context": "lint", "state": "success", "created_at": updated, "updated_at": updated}],
        reviews=[{"user": {"login": "reviewer"}, "state": "APPROVED", "commit_id": SHA}],
        comments=[{"body": "note", "created_at": updated, "user": {"login": "reviewer"}}],
    )

    assert set(projected) == {
        "number",
        "title",
        "state",
        "isDraft",
        "headRefName",
        "headRefOid",
        "updatedAt",
        "createdAt",
        "reviewDecision",
        "reviews",
        "comments",
        "statusCheckRollup",
        "mergeStateStatus",
        "labels",
        "assignees",
        "url",
    }
    assert "body" not in projected
    assert projected["reviewDecision"] == "APPROVED"
    assert projected["reviews"] == [{"state": "APPROVED", "commit": {"oid": SHA}}]
    assert projected["comments"] == [{"body": "note", "createdAt": updated}]
    assert projected["mergeStateStatus"] == "CLEAN"
    assert _pr_check_state(projected) == "passing"
    eligible = api_main._eligible_idle_pr(projected, now=now)
    assert eligible == {"number": 77, "branch": "cursor/example", "minutes_idle": 240}


def test_changes_requested_beats_a_later_approval_from_someone_else():
    reviews = [
        {"user": {"login": "a"}, "state": "APPROVED"},
        {"user": {"login": "b"}, "state": "CHANGES_REQUESTED"},
    ]
    assert github_rest.derive_review_decision(reviews, []) == "CHANGES_REQUESTED"
    assert github_rest.derive_review_decision(reviews[:1], [{"login": "c"}]) == "REVIEW_REQUIRED"


def _scripted_repo():
    updated = (datetime.now(UTC) - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pulls_path = f"repos/{REPO}/pulls?state=open&per_page=100&sort=created&direction=desc"
    issues_path = f"repos/{REPO}/issues?state=open&per_page=100&sort=created&direction=desc"
    resources = {
        pulls_path: (
            '"pulls"',
            [
                {
                    "number": 77,
                    "title": "Ship it",
                    "state": "open",
                    "draft": False,
                    "head": {"ref": "cursor/example", "sha": SHA},
                    "updated_at": updated,
                    "created_at": "2026-08-01T00:00:00Z",
                    "html_url": f"https://github.com/{REPO}/pull/77",
                    "labels": [],
                    "assignees": [],
                }
            ],
        ),
        issues_path: (
            '"issues"',
            [
                {
                    "number": 77,
                    "title": "The pull request",
                    "state": "open",
                    "pull_request": {"url": "https://api.github.com/pulls/77"},
                    "body": "not an issue",
                    "created_at": updated,
                    "updated_at": updated,
                    "html_url": f"https://github.com/{REPO}/pull/77",
                    "labels": [],
                    "assignees": [],
                },
                {
                    "number": 9,
                    "title": "Public issue",
                    "state": "open",
                    "body": "blocked by #1",
                    "created_at": "2026-08-01T00:00:00Z",
                    "updated_at": "2026-08-02T00:00:00Z",
                    "html_url": f"https://github.com/{REPO}/issues/9",
                    "labels": [{"name": "bug"}],
                    "assignees": [{"login": "octocat"}],
                },
            ],
        ),
        f"repos/{REPO}/pulls/77": ('"pull"', {"mergeable_state": "unstable", "requested_reviewers": []}),
        f"repos/{REPO}/commits/{SHA}/check-runs?per_page=100&page=1": (
            '"checks"',
            {
                "total_count": 1,
                "check_runs": [
                    {
                        "name": "CI Gate",
                        "status": "completed",
                        "conclusion": "success",
                        "started_at": updated,
                        "completed_at": updated,
                    }
                ],
            },
        ),
        f"repos/{REPO}/commits/{SHA}/status": ('"status"', {"statuses": [], "total_count": 0}),
        f"repos/{REPO}/pulls/77/reviews?per_page=100": (
            '"reviews"',
            [{"user": {"login": "reviewer"}, "state": "APPROVED", "commit_id": SHA}],
        ),
        f"repos/{REPO}/issues/77/comments?per_page=100": ('"comments"', []),
        f"repos/{REPO}/issues/9": ('"issue9"', {"number": 9, "state": "open"}),
        f"repos/{REPO}/issues/1": ('"issue1"', {"number": 1, "state": "closed"}),
    }
    return resources


def test_open_pr_detail_is_conditional_and_bounded_to_open_pulls():
    resources = _scripted_repo()
    calls: list[tuple[str, str | None]] = []

    def transport(path, headers, timeout):
        calls.append((path, headers.get("If-None-Match")))
        etag, body = resources[path]
        if headers.get("If-None-Match") == etag:
            return 304, {"etag": etag}, b""
        return 200, {"etag": etag}, json.dumps(body).encode()

    cache = github_rest.GitHubRestCache(transport=transport)
    first = github_rest.list_open_prs(REPO, limit=1000, timeout=2.0, cache=cache, include_comments=True)
    second = github_rest.list_open_prs(REPO, limit=1000, timeout=2.0, cache=cache, include_comments=True)

    assert not any("/pulls/78" in path or "/issues/9" in path for path, _ in calls)
    assert first == second
    assert first[0]["number"] == 77
    assert first[0]["reviewDecision"] == "APPROVED"
    assert _pr_check_state(first[0]) == "passing"
    assert len(calls) == 12
    assert calls[0][1] is None
    assert all(etag for _, etag in calls[6:])


def test_check_run_error_is_not_cached_as_a_successful_pr_list():
    resources = _scripted_repo()

    def transport(path, headers, timeout):
        if "check-runs" in path:
            return 500, {}, b"unavailable"
        etag, body = resources[path]
        return 200, {"etag": etag}, json.dumps(body).encode()

    cache = github_rest.GitHubRestCache(transport=transport)
    with pytest.raises(github_rest.GitHubRestError):
        github_rest.list_open_prs(REPO, limit=10, timeout=2.0, cache=cache)
    check_path = f"repos/{REPO}/commits/{SHA}/check-runs?per_page=100&page=1"
    assert cache.cached_body(check_path) is None


def test_fetch_open_issues_rest_timeout_is_not_a_successful_section(monkeypatch):
    def boom(repo, *, limit, timeout, cache=None):
        raise github_rest.GitHubRestTimeout(timeout)

    monkeypatch.setattr(github_rest, "list_open_issues", boom)
    section = fetch_open_issues(REPO)
    assert section.status == "timeout"
    assert section.reason == "gh_issue_list_timeout"
    assert section.payload is None


def test_issue_state_rest_omits_404_and_does_not_cache_it():
    resources = _scripted_repo()

    def transport(path, headers, timeout):
        if path.endswith("/issues/404"):
            return 404, {}, b""
        if path.endswith("/issues/500"):
            return 500, {"etag": '"nope"'}, b"boom"
        etag, body = resources[path]
        if headers.get("If-None-Match") == etag:
            return 304, {"etag": etag}, b""
        return 200, {"etag": etag}, json.dumps(body).encode()

    cache = github_rest.GitHubRestCache(transport=transport)
    found = github_rest.issue_states(REPO, [9, 1, 404, 500], timeout=1.0, cache=cache)
    assert found == {9: "open", 1: "closed"}
    assert cache.cached_body(f"repos/{REPO}/issues/404") is None
    assert cache.cached_body(f"repos/{REPO}/issues/500") is None
    again = github_rest.issue_states(REPO, [1], timeout=1.0, cache=cache)
    assert again == {1: "closed"}


def test_fetch_issue_states_rest_contract(monkeypatch):
    resources = _scripted_repo()
    cache = github_rest.GitHubRestCache(
        transport=lambda path, headers, timeout: (
            200,
            {"etag": resources[path][0]},
            json.dumps(resources[path][1]).encode(),
        )
    )
    monkeypatch.setattr(github_rest, "shared_cache", lambda: cache)

    states = fetch_issue_states_batched([9, 1], repository_id=REPO)

    from scripts.work.relations import issue_work_id

    assert states[issue_work_id(REPO, 9)] == "open"
    assert states[issue_work_id(REPO, 1)] == "closed"
    assert states["1"] == "closed"


def test_orient_issues_endpoint_contract(monkeypatch):
    monkeypatch.setattr(
        github_rest,
        "list_open_issues",
        lambda *args, **kwargs: [
            {
                "number": 42,
                "title": "Hello",
                "labels": [{"name": "priority:high"}],
                "createdAt": "2026-09-01T00:00:00Z",
            }
        ],
    )
    for key in [key for key in list(state_helpers._ttl_cache) if str(key).startswith("orient_")]:
        state_helpers._ttl_cache.pop(key, None)

    response = client.get("/api/orient?sections=issues")

    assert response.status_code == 200
    issue = response.json()["issues"][0]
    assert set(issue) == {"number", "title", "labels", "age_days"}
    assert issue["number"] == 42
    assert issue["title"] == "Hello"
    assert issue["labels"] == ["priority:high"]
    assert isinstance(issue["age_days"], int)


def test_orient_idle_prs_endpoint_contract(monkeypatch):
    updated = (datetime.now(UTC) - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    monkeypatch.setattr(
        github_rest,
        "list_open_prs",
        lambda *args, **kwargs: [
            {
                "number": 77,
                "state": "OPEN",
                "isDraft": False,
                "headRefName": "cursor/example",
                "headRefOid": SHA,
                "updatedAt": updated,
                "reviewDecision": "APPROVED",
                "reviews": [],
                "comments": [],
                "mergeStateStatus": "CLEAN",
                "statusCheckRollup": [
                    {
                        "name": "CI Gate",
                        "status": "COMPLETED",
                        "conclusion": "SUCCESS",
                        "startedAt": updated,
                        "completedAt": updated,
                    }
                ],
            }
        ],
    )

    def inline(collector, scope):
        api_main._run_idle_pr_refresh(collector, scope)

    monkeypatch.setattr(api_main, "_schedule_idle_pr_refresh", inline)
    for thread in list(api_main._idle_pr_refresh_threads.values()):
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)
    api_main._idle_pr_refresh_threads.clear()
    api_main._idle_pr_last_good.clear()
    api_main._idle_pr_last_error.clear()
    api_main._idle_pr_next_retry_at.clear()
    for key in [key for key in list(state_helpers._ttl_cache) if "idle_pr" in str(key)]:
        state_helpers._ttl_cache.pop(key, None)

    response = client.get("/api/orient?sections=idle_prs")

    assert response.status_code == 200
    row = response.json()["idle_prs"][0]
    assert set(row) == {"number", "branch", "minutes_idle"}
    assert row["number"] == 77
    assert row["branch"] == "cursor/example"
    assert row["minutes_idle"] >= 60


def test_work_projection_endpoint_contract(monkeypatch):
    monkeypatch.setattr(
        github_rest,
        "list_open_issues",
        lambda *args, **kwargs: [
            github_rest.project_issue(
                _scripted_repo()[f"repos/{REPO}/issues?state=open&per_page=100&sort=created&direction=desc"][1][1]
            )
        ],
    )
    projected_pr = github_rest.project_pull_request(
        _scripted_repo()[f"repos/{REPO}/pulls?state=open&per_page=100&sort=created&direction=desc"][1][0],
        pull={"mergeable_state": "clean", "requested_reviewers": []},
        check_runs=[
            {
                "name": "CI Gate",
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-08-13T08:00:00Z",
                "completed_at": "2026-08-13T08:10:00Z",
            }
        ],
        statuses=[],
        reviews=[{"user": {"login": "reviewer"}, "state": "APPROVED", "commit_id": SHA}],
        comments=[],
    )
    monkeypatch.setattr(github_rest, "list_open_prs", lambda *args, **kwargs: [projected_pr])
    monkeypatch.setattr(
        github_rest,
        "issue_states",
        lambda *args, **kwargs: {1: "closed"},
    )

    from scripts.work import sources_public

    monkeypatch.setattr(
        sources_public,
        "fetch_streams_projection",
        lambda loader=None: SectionResult(
            "streams",
            "ok",
            payload={
                "orphans": [],
                "multi_homed": [],
                "pending_native_link": [],
                "open_total": 1,
                "open_issue_numbers": [9],
            },
            count=1,
        ),
    )
    monkeypatch.setattr(
        sources_public,
        "fetch_delegate_active",
        lambda loader=None, repository_id=None: SectionResult(
            "delegate_active", "ok", payload={"total": 0, "tasks": []}, count=0
        ),
    )
    monkeypatch.setattr(
        sources_public,
        "fetch_delegate_tasks",
        lambda loader=None, repository_id=None: SectionResult(
            "delegate_tasks", "ok", payload={"total": 0, "tasks": []}, count=0
        ),
    )
    monkeypatch.setattr(
        sources_public,
        "fetch_fleet_reviews",
        lambda loader=None, repository_id=None: SectionResult(
            "fleet_reviews", "ok", payload={"total": 0, "reviews": []}, count=0
        ),
    )
    cache_invalidate("work:v1:projection")

    response = client.get("/api/work/v1/projection?fresh=true")

    assert response.status_code == 200
    items = response.json()["items"]
    issue = next(item for item in items if item["resource_kind"] == "issue")
    pull = next(item for item in items if item["resource_kind"] == "pr")
    assert issue["title"] == "Public issue"
    assert issue["lifecycle"] == "open"
    assert issue["labels"] == ["bug"]
    assert issue["urls"]["html"].endswith("/issues/9")
    assert "body" not in issue
    assert pull["lifecycle"] == "open"
    assert pull["flags"]["is_draft"] is False
    assert pull["projections"]["verification"]["ci_state"] == "passing"
    assert pull["projections"]["verification"]["merge_state_status"] == "CLEAN"
    assert pull["projections"]["verification"]["head_sha"] == SHA
    assert pull["projections"]["review"]["review_decision"] == "APPROVED"
