"""Fake-transport proofs for #9898; no GitHub network is used."""

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from scripts.common import github_client as gh


def response(value, *, status=200, remaining=100, reset=2000, etag='"one"'):
    return gh.Response(
        status,
        {"ETag": etag, "X-RateLimit-Remaining": str(remaining), "X-RateLimit-Reset": str(reset)},
        json.dumps(value).encode(),
    )


def client(tmp_path, script, *, now=1000, env=None):
    calls = []

    def transport(method, endpoint, headers, body, timeout):
        calls.append((method, endpoint, headers, body))
        return script[len(calls) - 1]

    return gh.GitHubClient(cache_dir=tmp_path, transport=transport, clock=lambda: now, env=env or {}), calls


def test_conditional_cache_survives_new_client(tmp_path):
    first, calls = client(tmp_path, [response({"state": "open"})])
    assert first.request("GET", "repos/o/r/issues/1").value == {"state": "open"}
    second, calls = client(tmp_path, [response(None, status=304, remaining=100)], now=1010)
    result = second.request("GET", "repos/o/r/issues/1")
    assert result.value == {"state": "open"} and result.status == 304 and not result.stale
    assert calls[0][2]["If-None-Match"] == '"one"'
    with second._db() as db:
        assert db.execute("SELECT remaining FROM budget").fetchone() == (100,)


def test_low_budget_cached_stale_and_no_cache_typed(tmp_path):
    store, calls = client(tmp_path, [response([1], remaining=0)])
    store.request("GET", "repos/o/r/issues")
    stale = store.request("GET", "repos/o/r/issues", allow_stale=True)
    assert stale.value == [1] and stale.stale and stale.reset_at == 2000
    missing = store.request("GET", "repos/o/r/pulls")
    assert missing.error == "github_rate_limited" and missing.reset_at == 2000
    assert len(calls) == 1
    with pytest.raises(gh.GitHubRateLimited):
        stale.require_fresh()


def test_stale_age_is_explicit(tmp_path):
    store, _ = client(tmp_path, [response({"number": 1}, remaining=2)])
    store.request("GET", "repos/o/r/issues/1")
    store.clock = lambda: 1065
    assert store.request("GET", "repos/o/r/issues/1", allow_stale=True).age_seconds == 65


def test_write_exhaustion_is_single_attempt_then_no_attempt(tmp_path):
    store, calls = client(tmp_path, [response({"message": "rate limited"}, status=403, remaining=0)])
    for _ in range(2):
        limited = store.request("POST", "repos/o/r/issues", payload={"title": "x"})
        assert limited.error == "github_rate_limited" and limited.reset_at == 2000
    assert len(calls) == 1


def test_cached_status_cannot_prove_merge_or_cleanup(tmp_path):
    store, calls = client(tmp_path, [response({"state": "closed"}, remaining=0)])
    store.request("GET", "repos/o/r/pulls/1")
    assert store.request("GET", "repos/o/r/pulls/1", fresh=True).error == "github_rate_limited"
    assert len(calls) == 1


def test_reset_allows_next_request_without_waiting(tmp_path):
    store, calls = client(tmp_path, [response(1, remaining=0), response(2, remaining=99, reset=4000)])
    store.request("GET", "repos/o/r/issues")
    store.clock = lambda: 2001
    assert store.request("GET", "repos/o/r/issues").value == 2
    assert len(calls) == 2


def test_graphql_has_separate_budget_and_no_retry(tmp_path):
    store, calls = client(
        tmp_path, [response({"errors": [{"type": "RATE_LIMIT"}]}, remaining=0), response({"number": 1})]
    )
    result = store.request("POST", "graphql", payload={"query": "query { viewer { login } }"})
    assert result.error == "github_rate_limited"
    assert store.request("GET", "repos/o/r/issues/1").value == {"number": 1}
    assert len(calls) == 2


def test_colour_forcing_removed_and_json_parsed(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(tmp_path))
    calls = []

    def transport(args, **kw):
        calls.append((args, kw))
        assert "FORCE_COLOR" not in kw["env"] and "CLICOLOR_FORCE" not in kw["env"]
        return subprocess.CompletedProcess(
            args,
            0,
            b'HTTP/2.0 200 OK\r\nX-RateLimit-Remaining: 100\r\nX-RateLimit-Reset: 2000\r\n\r\n{"number":1}',
            b"",
        )

    result = gh.run(
        ["gh", "api", "repos/o/r/issues/1"],
        runner=transport,
        env={"FORCE_COLOR": "1", "CLICOLOR_FORCE": "1"},
        text=True,
        capture_output=True,
    )
    assert json.loads(result.stdout) == {"number": 1}
    assert "--include" in calls[0][0]


def test_rest_pr_state_and_head_projection(tmp_path):
    store, calls = client(
        tmp_path,
        [
            response(
                {
                    "number": 1,
                    "state": "open",
                    "draft": False,
                    "head": {"sha": "a" * 40, "ref": "fix"},
                    "base": {"ref": "main"},
                }
            )
        ],
    )
    result = gh.run(
        ["gh", "pr", "view", "1", "--repo", "o/r", "--json", "number,state,headRefOid"],
        client=store,
        text=True,
        capture_output=True,
    )
    assert json.loads(result.stdout) == {"number": 1, "state": "OPEN", "headRefOid": "a" * 40}
    assert calls[0][1] == "repos/o/r/pulls/1"


def test_pr_comment_uses_rest_once(tmp_path):
    store, calls = client(tmp_path, [response({"id": 1}, status=201)])
    result = gh.run(
        ["gh", "pr", "comment", "1", "--repo", "o/r", "--body=example"], client=store, text=True, capture_output=True
    )
    assert result.returncode == 0
    assert calls[0][:2] == ("POST", "repos/o/r/issues/1/comments")
    assert json.loads(calls[0][3]) == {"body": "example"}


def test_credential_cache_isolation(tmp_path):
    first, _ = client(tmp_path, [response(1, remaining=0)], env={"GH_TOKEN": "synthetic-one"})
    first.request("GET", "user")
    second, calls = client(tmp_path, [response(2)], env={"GH_TOKEN": "synthetic-two"})
    assert second.request("GET", "user").value == 2 and len(calls) == 1
    assert b"synthetic" not in (tmp_path / "cache.sqlite3").read_bytes()


def test_secondary_limit_defers_both_budgets(tmp_path):
    store, calls = client(tmp_path, [gh.Response(429, {"Retry-After": "120"}, b"{}")])
    assert store.request("GET", "repos/o/r/issues").reset_at == 1120
    assert (
        store.request("POST", "graphql", payload={"query": "query { viewer { login } }"}).error == "github_rate_limited"
    )
    assert len(calls) == 1


def test_rest_default_head_preserves_named_read_shape(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(tmp_path))
    calls = []

    def send(args, **kwargs):
        calls.append(args)
        endpoint = args[4]
        value = {"default_branch": "trunk", "full_name": "o/r"} if endpoint == "repos/o/r" else {"sha": "b" * 40}
        return subprocess.CompletedProcess(args, 0, json.dumps(value), "")

    result = gh.rest_read("default-head", "o/r", {}, runner=send, text=True, capture_output=True)
    assert json.loads(result.stdout) == {
        "data": {
            "repository": {"nameWithOwner": "o/r", "defaultBranchRef": {"name": "trunk", "target": {"oid": "b" * 40}}}
        }
    }
    assert [args[4] for args in calls] == ["repos/o/r", "repos/o/r/commits/trunk"]


def test_named_budget_uses_graphql_resource_not_core(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(tmp_path))
    calls = []

    def send(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(
            args,
            0,
            json.dumps(
                {
                    "resources": {
                        "core": {"remaining": 4999},
                        "graphql": {"limit": 5000, "remaining": 0, "used": 5000, "reset": 2000},
                    }
                }
            ),
            "",
        )

    result = gh.rest_read("budget", "o/r", {}, runner=send, text=True, capture_output=True)
    assert json.loads(result.stdout)["data"]["rateLimit"]["remaining"] == 0
    assert calls == [["gh", "api", "--method", "GET", "rate_limit"]]


def test_api_pagination_tracks_budget_and_stale_page(tmp_path):
    first = response([1])
    first.headers["Link"] = '<https://api.github.com/repos/o/r/issues?page=2>; rel="next"'
    store, calls = client(tmp_path, [first, response([2])])
    result = gh.run(
        ["gh", "api", "repos/o/r/issues", "--paginate", "--slurp"], client=store, text=True, capture_output=True
    )
    assert json.loads(result.stdout) == [[1], [2]] and len(calls) == 2


@pytest.mark.parametrize(
    "endpoint", ["repos/o/r/releases/assets/1", "repos/o/r/actions/artifacts/1/zip", "repos/o/r/pulls/1"]
)
@pytest.mark.parametrize("mode", [{}, {"raw_response": True}, {"headers": {"Accept": "application/octet-stream"}}])
def test_binary_downloads_are_not_cached(tmp_path, endpoint, mode):
    store, calls = client(tmp_path, [gh.Response(200, {"etag": '"zip"'}, b"\x00\xffzip")] * 2)
    for _ in range(2):
        assert store.request("GET", endpoint, **mode).value == b"\x00\xffzip"
    assert "If-None-Match" not in calls[1][2]
    with store._db() as db:
        assert db.execute("SELECT count(*) FROM cache").fetchone() == (0,)


def test_error_does_not_replace_cached_value(tmp_path):
    store, calls = client(
        tmp_path, [response({"number": 1}), response({"message": "bad"}, status=500), response({}, status=304)]
    )
    store.request("GET", "repos/o/r/issues/1")
    assert store.request("GET", "repos/o/r/issues/1").error == "github_http_error"
    assert store.request("GET", "repos/o/r/issues/1").value == {"number": 1}
    assert len(calls) == 3


def test_304_without_cache_is_explicit_error(tmp_path):
    store, _ = client(tmp_path, [response(None, status=304)])
    assert store.request("GET", "repos/o/r/issues/1").error == "github_cache_miss"


def test_unrelated_forbidden_is_not_a_rate_limit(tmp_path):
    store, _ = client(tmp_path, [response({"message": "permission denied"}, status=403)])
    assert store.request("GET", "repos/o/r/issues/1").error == "github_http_error"


def test_secondary_limit_without_headers_has_bounded_reset(tmp_path):
    store, calls = client(tmp_path, [gh.Response(403, {}, b'{"message":"You have exceeded a secondary rate limit."}')])
    result = store.request("POST", "repos/o/r/issues", payload={"title": "x"})
    assert result.error == "github_rate_limited" and result.reset_at == 1060 and len(calls) == 1


def test_foreign_endpoint_cannot_receive_credentials(tmp_path):
    store, calls = client(tmp_path, [])
    with pytest.raises(ValueError, match="host mismatch"):
        store.request("GET", "https://example.invalid/repos/o/r/issues")
    assert calls == []


def test_out_of_order_budget_does_not_restore_spent_budget(tmp_path):
    store, _ = client(tmp_path, [])
    with store._db() as db:
        gh._store_budget(db, store.scope, "core", 0, 2000)
        gh._store_budget(db, store.scope, "core", 100, 2000)
        gh._store_budget(db, store.scope, "core", 100, 1500)
        assert db.execute("SELECT remaining,reset FROM budget").fetchone() == (0, 2000)
        gh._store_budget(db, store.scope, "core", 100, 3000)
        assert db.execute("SELECT remaining,reset FROM budget").fetchone() == (100, 3000)


def test_out_of_order_body_cannot_replace_newer_cache(tmp_path):
    store, _ = client(tmp_path, [])
    with store._db() as db:
        gh._store_cache(db, store.scope, "key", b'{"state":"closed"}', {}, 1010)
        gh._store_cache(db, store.scope, "key", b'{"state":"open"}', {}, 1000)
        assert json.loads(db.execute("SELECT body FROM cache").fetchone()[0]) == {"state": "closed"}


def test_timer_skips_and_logs_reset(capsys):
    @gh.timer
    def scheduled():
        raise gh.GitHubRateLimited(2000)

    assert scheduled() == 0
    assert "skipped github_rate_limited reset_at=2000" in capsys.readouterr().out


def test_timer_does_not_hide_unrelated_failure():
    @gh.timer
    def scheduled():
        raise subprocess.CalledProcessError(1, ["gh"])

    with pytest.raises(subprocess.CalledProcessError):
        scheduled()


def test_rest_repository_selector_is_not_replaced_by_cwd(tmp_path):
    store, calls = client(
        tmp_path,
        [response({"full_name": "private/recall", "private": True, "permissions": {"push": True}})],
        env={"GH_REPO": "public/project"},
    )
    result = gh.run(
        ["gh", "repo", "view", "private/recall", "--json", "nameWithOwner,isPrivate,viewerPermission"],
        client=store,
        text=True,
        capture_output=True,
    )
    assert json.loads(result.stdout) == {
        "nameWithOwner": "private/recall",
        "isPrivate": True,
        "viewerPermission": "WRITE",
    }
    assert calls[0][1] == "repos/private/recall"


@pytest.mark.parametrize("conclusion,bucket", [("SUCCESS", "pass"), ("CANCELLED", "cancel"), ("SKIPPED", "skipping")])
def test_checks_preserve_native_buckets_and_fields(tmp_path, conclusion, bucket):
    expected = [
        {"name": "CI Gate", "state": conclusion, "bucket": bucket, "workflowName": "CI", "appSlug": "github-actions"}
    ]
    store, calls = client(tmp_path, [])
    native_calls = []

    def native(args, **kw):
        native_calls.append(args)
        return subprocess.CompletedProcess(args, 0, json.dumps(expected).encode(), b"")

    args = ["gh", "pr", "checks", "1", "--repo", "o/r", "--json", "name,bucket,state,workflowName,appSlug"]
    result = gh.run(args, client=store, runner=native, text=True, capture_output=True)
    assert json.loads(result.stdout) == expected
    assert native_calls == [args] and calls == []


def test_checks_native_failure_is_not_success(tmp_path):
    store, calls = client(tmp_path, [])

    def native(args, **kw):
        return subprocess.CompletedProcess(args, 1, b"[]", b"checks unavailable")

    args = ["gh", "pr", "checks", "1", "--repo", "o/r", "--json", "name,bucket,state"]
    result = gh.run(args, client=store, runner=native, text=True, capture_output=True)
    assert result.returncode == 1 and result.stderr == "checks unavailable" and calls == []


def test_pr_merge_uses_queue_mutation_and_preserves_head_guard(tmp_path):
    store, calls = client(
        tmp_path,
        [
            response({"data": {"repository": {"pullRequest": {"id": "PR_1", "isMergeQueueEnabled": True}}}}),
            response({"data": {"enqueuePullRequest": {"clientMutationId": None}}}),
        ],
    )
    result = gh.run(
        ["gh", "pr", "merge", "1", "--repo", "o/r", "--squash", "--match-head-commit=" + "a" * 40],
        client=store,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    payload = json.loads(calls[1][3])
    assert "enqueuePullRequest" in payload["query"] and payload["variables"]["input"] == {
        "pullRequestId": "PR_1",
        "expectedHeadOid": "a" * 40,
    }
    assert len(calls) == 2


def test_pr_merge_without_queue_uses_rest_and_pins_head(tmp_path):
    store, calls = client(
        tmp_path,
        [
            response({"data": {"repository": {"pullRequest": {"id": "PR_1", "isMergeQueueEnabled": False}}}}),
            response({"merged": True}),
        ],
    )
    result = gh.run(
        ["gh", "pr", "merge", "1", "--repo", "o/r", "--squash", "--match-head-commit=" + "a" * 40, "--subject=clean"],
        client=store,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert calls[1][:2] == ("PUT", "repos/o/r/pulls/1/merge")
    assert json.loads(calls[1][3]) == {"merge_method": "squash", "sha": "a" * 40, "commit_title": "clean"}


def test_worker_cannot_approve_or_merge(tmp_path):
    store, calls = client(tmp_path, [], env={"AGENT_NO_MERGE": "1"})
    for args in (
        ["gh", "pr", "review", "1", "--repo", "o/r", "--approve"],
        ["gh", "pr", "merge", "1", "--repo", "o/r", "--squash"],
    ):
        result = gh.run(args, client=store, text=True, capture_output=True)
        assert result.returncode == 1
    assert calls == []


def test_graphql_primary_http_limit_does_not_block_rest(tmp_path):
    limited = gh.Response(
        403,
        {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "2000", "x-ratelimit-resource": "graphql"},
        b'{"message":"API rate limit exceeded"}',
    )
    store, calls = client(tmp_path, [limited, response({"number": 1})])
    assert (
        store.request("POST", "graphql", payload={"query": "query { viewer { login } }"}).error == "github_rate_limited"
    )
    assert store.request("GET", "repos/o/r/issues/1").value == {"number": 1}
    assert len(calls) == 2


def test_asset_json_and_ansi_bytes_remain_exact(tmp_path):
    body = b'{ "name": "asset" }\n\x1b[31m'
    store, calls = client(tmp_path, [gh.Response(200, {"etag": '"asset"'}, body)] * 2)
    for _ in range(2):
        assert (
            store.request("GET", "repos/o/r/releases/assets/1", headers={"Accept": "application/octet-stream"}).value
            == body
        )
    assert gh.parse_http(b'\x1b[31mHTTP/2 200\x1b[0m\nETag: "asset"\n\n' + body).body == body
    assert len(calls) == 2


def test_http_adapter_preserves_body_headers_and_request(tmp_path, monkeypatch):
    import io
    from urllib.request import Request

    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(tmp_path))
    body = b'{  "token" : "synthetic-secret" }\n'
    request = Request(
        "https://api.github.com/app/installations/1/access_tokens", data=b'{"repositories":["r"]}', method="POST"
    )

    def opener(received, **kwargs):
        assert received is request and received.data == b'{"repositories":["r"]}'
        result = io.BytesIO(body)
        result.status = 201
        result.headers = {"X-RateLimit-Remaining": "100", "X-RateLimit-Reset": "2000"}
        return result

    with gh.http_open(request, opener=opener) as received:
        assert received.status == 201 and received.read() == body
    assert b"synthetic-secret" not in (tmp_path / "cache.sqlite3").read_bytes()


def test_http_adapter_retains_http_error_contract(tmp_path, monkeypatch):
    import io
    import urllib.error
    from urllib.request import Request

    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(tmp_path))

    def opener(request, **kwargs):
        raise urllib.error.HTTPError(request.full_url, 404, "missing", {}, io.BytesIO(b'{"message":"missing"}'))

    with pytest.raises(urllib.error.HTTPError) as exc:
        gh.http_open(Request("https://api.github.com/repos/o/r/releases/1"), opener=opener)
    assert exc.value.code == 404


def test_stale_pr_files_propagate_age_and_reset(tmp_path):
    store, calls = client(
        tmp_path,
        [
            response({"number": 1, "state": "open", "head": {}, "base": {}}),
            response([{"filename": "file.py"}], remaining=0),
        ],
    )
    args = ["gh", "pr", "view", "1", "--repo", "o/r", "--json", "number,files"]
    gh.run(args, client=store, capture_output=True, text=True)
    store.clock = lambda: 1060
    result = gh.run(args, client=store, allow_stale=True, capture_output=True, text=True)
    assert result.github_result.stale and result.github_result.age_seconds == 60
    assert json.loads(result.stderr) == {"stale": True, "age_seconds": 60, "reset_at": 2000}
    assert len(calls) == 2


def test_parent_read_uses_rest_and_preserves_cross_repository_identity(tmp_path, monkeypatch):
    from scripts.publish import github as pub

    issue = {"number": 1, "state": "open", "html_url": "https://github.com/o/r/issues/1", "repository_url": "https://api.github.com/repos/o/r"}
    parent = {
        "number": 7,
        "html_url": "https://github.com/other/stream/issues/7",
        "repository_url": "https://api.github.com/repos/other/stream",
    }
    store, calls = client(tmp_path, [response(issue), response(parent)])
    monkeypatch.setattr(gh, "GitHubClient", lambda **kw: store)
    result = pub.read("issue-parent", repo="o/r", number=1, capture_output=True, text=True)
    assert (
        json.loads(result.stdout)["data"]["repository"]["issue"]["parent"]["repository"]["nameWithOwner"]
        == "other/stream"
    )
    assert [c[1] for c in calls] == ["repos/o/r/issues/1", "repos/o/r/issues/1/parent"]


def test_missing_parent_is_rest_absence_not_transport_success(tmp_path, monkeypatch):
    store, calls = client(
        tmp_path,
        [
            response({"number": 1, "state": "open", "html_url": "https://github.com/o/r/issues/1", "repository_url": "https://api.github.com/repos/o/r"}),
            response({"message": "missing"}, status=404),
        ],
    )
    monkeypatch.setattr(gh, "GitHubClient", lambda **kw: store)
    result = gh.rest_read("issue-parent", "o/r", {"number": 1}, capture_output=True, text=True)
    assert json.loads(result.stdout)["data"]["repository"]["issue"]["parent"] is None
    assert len(calls) == 2


def test_subissue_batch_rest_paginates_without_graphql(tmp_path, monkeypatch):
    first = response(
        [{"number": 2, "repository_url": "https://api.github.com/repos/o/r", "sub_issues_summary": {"total": 1}}]
    )
    first.headers["Link"] = '<https://api.github.com/repos/o/r/issues/1/sub_issues?page=2>; rel="next"'
    store, calls = client(
        tmp_path,
        [
            response({"body": "root"}),
            first,
            response(
                [
                    {
                        "number": 3,
                        "repository_url": "https://api.github.com/repos/o/r",
                        "sub_issues_summary": {"total": 0},
                    }
                ]
            ),
        ],
    )
    monkeypatch.setattr(gh, "GitHubClient", lambda **kw: store)
    result = gh.rest_read(
        "subissue-batch", "o/r", {"cursors": {1: None}, "body_roots": {1}}, capture_output=True, text=True
    )
    row = json.loads(result.stdout)["data"]["repository"]["i1"]
    assert row["body"] == "root" and [n["number"] for n in row["subIssues"]["nodes"]] == [2, 3]
    assert row["subIssues"]["pageInfo"] == {"hasNextPage": False, "endCursor": None}
    assert all(c[0] == "GET" and c[1] != "graphql" for c in calls)


def test_auto_merge_timestamp_is_not_invented_from_rest(tmp_path):
    store, calls = client(
        tmp_path,
        [
            response({"number": 1, "state": "open", "head": {}, "base": {}, "auto_merge": {"merge_method": "squash"}}),
            response(
                {"data": {"repository": {"pullRequest": {"autoMergeRequest": {"enabledAt": "2026-10-06T00:00:00Z"}}}}}
            ),
        ],
    )
    result = gh.run(
        ["gh", "pr", "view", "1", "--repo", "o/r", "--json", "autoMergeRequest"],
        client=store,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout)["autoMergeRequest"]["enabledAt"] == "2026-10-06T00:00:00Z"
    query = json.loads(calls[1][3])["query"]
    assert "autoMergeRequest{enabledAt}" in query and "headRefOid" not in query


def test_publishing_preflight_returns_typed_limit_without_write(tmp_path, monkeypatch):
    from scripts.publish import github as pub

    store, calls = client(tmp_path, [])
    with store._db() as db:
        gh._store_budget(db, store.scope, "core", 0, 2000)
    monkeypatch.setattr(gh, "GitHubClient", lambda **kw: store)
    monkeypatch.setattr(pub.gate, "real_gh", lambda env: "gh")
    result = pub.publish("pr-merge", repo="o/r", number=1, env={"AGENT_NO_MERGE": "0"}, capture_output=True, text=True)
    assert result.returncode == 75
    assert json.loads(result.stdout) == {"error": "github_rate_limited", "reset_at": 2000}
    assert calls == []


def test_keeper_timer_skips_before_actions_and_logs_reset(tmp_path, monkeypatch, capsys):
    from scripts.orchestration import merge_queue_keeper as keeper

    def deferred(*args, **kwargs):
        raise gh.GitHubRateLimited(2000)

    monkeypatch.setattr(keeper, "run", deferred)
    assert keeper.main(["--repo", "o/r", "--repo-root", str(tmp_path)]) == 0
    assert "skipped reset_at=2000" in capsys.readouterr().out
    assert not (tmp_path / "batch_state/merge_queue_keeper.json").exists()


def test_data_timer_skips_stale_observation(tmp_path, monkeypatch, capsys):
    from scripts.ci import data_tier

    def deferred(*args, **kwargs):
        raise gh.GitHubRateLimited(2000)

    monkeypatch.setattr(data_tier, "run", deferred)
    assert data_tier.main(["run"]) == 0
    assert "skipped github_rate_limited reset_at=2000" in capsys.readouterr().out


def test_partial_graphql_error_is_not_success_or_cached(tmp_path):
    store, calls = client(
        tmp_path, [response({"data": {"repository": {"pullRequest": {"id": "PR"}}}, "errors": [{"type": "FORBIDDEN"}]})]
    )
    result = store.request("POST", "graphql", payload={"query": "mutation { example { id } }"})
    assert result.error == "github_graphql_error" and len(calls) == 1
    with store._db() as db:
        assert db.execute("SELECT count(*) FROM cache").fetchone()[0] == 0
    with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
        db.execute("SELECT 1")


def test_cli_timeout_reaps_a_real_descendant(tmp_path):
    import os
    import sys

    import psutil

    pid_file = tmp_path / "child.pid"
    executable = tmp_path / "gh"
    executable.write_text(
        f'#!{sys.executable}\nimport subprocess,sys,time,os\nchild=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"])\nopen(os.environ["CHILD_PID_PATH"],"w").write(str(child.pid))\ntime.sleep(30)\n'
    )
    executable.chmod(0o700)
    store = gh.GitHubClient(
        cache_dir=tmp_path / "cache",
        env={**os.environ, "AGENT_REAL_GH": str(executable), "CHILD_PID_PATH": str(pid_file)},
    )
    with pytest.raises(subprocess.TimeoutExpired):
        store.request("GET", "repos/o/r/issues", timeout=1)
    child = psutil.Process(int(pid_file.read_text())) if psutil.pid_exists(int(pid_file.read_text())) else None
    if child is not None:
        child.wait(timeout=5)


def test_low_keeper_budget_skips_identity_checks_and_state_write(tmp_path):
    from scripts.orchestration import merge_queue_keeper as keeper

    class BudgetOnly:
        def branch_names(self):
            return {"main"}

        def snapshot(self, branches):
            return {"remaining": 490, "cost": 1, "reset_at": 2000}

        def identity(self):
            pytest.fail("budget was already low")

    lines, failed = keeper.run(BudgetOnly(), tmp_path / "state.json", apply=True)
    assert not failed and "skipped" in lines[0] and "reset_at=2000" in lines[0]
    assert not (tmp_path / "state.json").exists()


def test_asset_limit_does_not_fall_back_to_another_http_request(monkeypatch):
    from scripts.open_dataset import hydrate

    def limited(args, **kwargs):
        result = subprocess.CompletedProcess(args, 75, b"", b"")
        result.github_result = gh.Result(error="github_rate_limited", reset_at=2000)
        return result

    monkeypatch.setattr(gh, "run", limited)
    monkeypatch.setattr(gh, "http_open", lambda *args, **kwargs: pytest.fail("unexpected fallback"))
    with pytest.raises(gh.GitHubRateLimited):
        hydrate.download_asset(
            {"release_tag": "tag", "asset_url": "https://github.com/o/r/releases/download/tag/a"}, repo="o/r"
        )


def test_frozen_json_payload_is_sent_byte_for_byte(tmp_path):
    body = b'{ "body" : "\\u2603" }\n'
    source = tmp_path / "payload.json"
    source.write_bytes(body)
    store, calls = client(tmp_path / "cache", [response({"id": 1}, status=201)])
    result = gh.run(
        ["gh", "api", "--method", "POST", "repos/o/r/issues/1/comments", "--input", str(source)],
        client=store,
        capture_output=True,
    )
    assert result.returncode == 0 and calls[0][3] == body


def test_frozen_graphql_read_still_uses_read_cache(tmp_path):
    body = b'{"query":"query { viewer { login } }"}'
    store, calls = client(tmp_path, [response({"data": {"viewer": {"login": "fixture"}}}, remaining=0)])
    first = store.request("POST", "graphql", payload=body)
    second = store.request("POST", "graphql", payload=body, allow_stale=True)
    assert second.stale and second.value == first.value and len(calls) == 1


def test_real_cli_transport_uses_conditional_headers_and_preserves_frozen_body(tmp_path):
    import os
    import sys

    executable = tmp_path / "gh"
    executable.write_text(
        f'#!{sys.executable}\nimport sys,os,json\nassert not any(k in os.environ for k in ("FORCE_COLOR","CLICOLOR_FORCE","GH_FORCE_TTY"))\nbody=sys.stdin.buffer.read()\nconditional=any("If-None-Match:" in arg for arg in sys.argv)\nprint("HTTP/2 304" if conditional else "HTTP/2 200")\nprint("X-RateLimit-Remaining: 100")\nprint("X-RateLimit-Reset: 2000")\nprint("ETag: \\"one\\"")\nprint()\nif not conditional: print(json.dumps({{"body":body.decode(),"no_colour":os.environ["NO_COLOR"]}}))\n'
    )
    executable.chmod(0o700)
    store = gh.GitHubClient(
        cache_dir=tmp_path / "cache",
        env={
            **os.environ,
            "AGENT_REAL_GH": str(executable),
            "FORCE_COLOR": "1",
            "CLICOLOR_FORCE": "1",
            "GH_FORCE_TTY": "1",
        },
        clock=lambda: 1000,
    )
    first = store.request("GET", "repos/o/r/issues/1")
    second = store.request("GET", "repos/o/r/issues/1")
    assert first.value == second.value == {"body": "", "no_colour": "1"} and second.status == 304
    body = b'{ "body": "\\u2603" }\n'
    assert store.request("POST", "repos/o/r/issues/1/comments", payload=body).value["body"].encode() == body


@pytest.fixture
def module_repository(tmp_path, monkeypatch):
    """A real module-owned repository, independent of the caller's repository."""
    monkeypatch.delenv("LU_GITHUB_CACHE_DIR")
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key)
    canonical = tmp_path / "canonical"
    subprocess.run(["git", "init", str(canonical)], check=True, capture_output=True, timeout=30)
    module = canonical / "scripts/common/github_client.py"
    module.parent.mkdir(parents=True)
    module.write_text("# fixture module location\n")
    monkeypatch.setattr(gh, "__file__", str(module))
    return canonical, module


@pytest.mark.parametrize("layout", ["primary", "linked", "linked-relative"])
def test_disk_cache_uses_runtime_state_of_module_git_common_root(module_repository, tmp_path, monkeypatch, layout):
    canonical, module = module_repository
    if layout != "primary":
        subprocess.run(
            ["git", "-C", str(canonical), "-c", "user.name=fixture", "-c", "user.email=fixture@example.com",
             "commit", "--allow-empty", "-m", "fixture"],
            check=True, capture_output=True, timeout=30,
        )
        worktree = tmp_path / "worktree"
        subprocess.run(
            ["git", "-C", str(canonical), "worktree", "add", "--detach", str(worktree)],
            check=True, capture_output=True, timeout=30,
        )
        module = worktree / module.relative_to(canonical)
        module.parent.mkdir(parents=True)
        module.write_text("# fixture module location\n")
        monkeypatch.setattr(gh, "__file__", str(module))
        if layout == "linked-relative":
            marker = worktree / ".git"
            gitdir = Path(marker.read_text().strip()[8:])
            marker.write_text(f"gitdir: {os.path.relpath(gitdir, worktree)}\n")
            (gitdir / "commondir").write_text(str(canonical / ".git"))
    assert gh._cache_directory() == canonical / "batch_state/github-client"


@pytest.mark.parametrize("explicit_cwd", [False, True])
def test_client_from_fixture_repository_leaves_its_status_clean(module_repository, tmp_path, monkeypatch, explicit_cwd):
    canonical, _ = module_repository
    caller = tmp_path / "caller"
    subprocess.run(["git", "init", str(caller)], check=True, capture_output=True, timeout=30)
    monkeypatch.chdir(caller)
    # Push hooks export repository-local Git variables for the caller.
    monkeypatch.setenv("GIT_DIR", str(caller / ".git"))
    monkeypatch.setenv("GIT_COMMON_DIR", str(caller / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(caller))
    store = gh.GitHubClient(cwd=caller if explicit_cwd else None, transport=lambda *_: response({"number": 1}), env={})
    assert store.request("GET", "repos/o/r/issues/1").value == {"number": 1}
    assert store.cache_dir == canonical / "batch_state/github-client"
    assert (store.cache_dir / "cache.sqlite3").is_file()
    status = subprocess.run(["git", "status", "--porcelain"], check=True, capture_output=True, text=True, timeout=30)
    assert status.stdout == ""
    assert not (caller / "batch_state").exists()


def test_cache_directory_override_wins_without_module_repository(tmp_path, monkeypatch):
    override = tmp_path / "override"
    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(override))
    monkeypatch.setattr(gh, "__file__", str(tmp_path / "plain/scripts/common/github_client.py"))
    store = gh.GitHubClient(transport=lambda *_: response(1), env={})
    assert store.request("GET", "user").value == 1
    assert store.cache_dir == override
    assert (override / "cache.sqlite3").is_file()


@pytest.mark.parametrize("layout", ["plain", "empty-git-dir", "invalid-gitfile", "missing-gitdir", "empty-commondir", "unreadable"])
def test_unresolved_module_repository_keeps_cache_and_budget_in_memory(tmp_path, monkeypatch, layout):
    monkeypatch.delenv("LU_GITHUB_CACHE_DIR")
    root = tmp_path / "plain"
    module = root / "scripts/common/github_client.py"
    module.parent.mkdir(parents=True)
    module.write_text("# fixture module location\n")
    monkeypatch.setattr(gh, "__file__", str(module))
    marker = root / ".git"
    if layout == "empty-git-dir":
        marker.mkdir()
    elif layout in {"invalid-gitfile", "unreadable"}:
        marker.write_text("invalid gitfile\n")
        if layout == "unreadable":
            read_text = Path.read_text

            def unreadable(path, *args, **kwargs):
                if path == marker:
                    raise PermissionError("fixture")
                return read_text(path, *args, **kwargs)

            monkeypatch.setattr(Path, "read_text", unreadable)
    elif layout in {"missing-gitdir", "empty-commondir"}:
        gitdir = root / "missing"
        marker.write_text(f"gitdir: {gitdir}\n")
        if layout == "empty-commondir":
            gitdir.mkdir()
            (gitdir / "commondir").write_text("")
    monkeypatch.chdir(tmp_path)
    calls = []
    replies = [response({"number": 1}), response(None, status=304, remaining=0)]

    def transport(*args):
        calls.append(args)
        return replies[len(calls) - 1]

    store = gh.GitHubClient(transport=transport, env={}, clock=lambda: 1000)
    assert store.cache_dir is None
    assert store.request("GET", "repos/o/r/issues/1").value == {"number": 1}
    assert store.request("GET", "repos/o/r/issues/1").status == 304
    assert calls[1][2]["If-None-Match"] == '"one"'
    assert store.request("GET", "repos/o/r/issues/1", allow_stale=True).stale
    assert store.request("GET", "user").error == "github_rate_limited"
    assert len(calls) == 2
    assert not list(tmp_path.rglob("cache.sqlite3"))


def test_absolute_search_url_observes_search_budget(tmp_path):
    limited = response({"items": []}, remaining=0)
    limited.headers["X-RateLimit-Resource"] = "search"
    store, calls = client(tmp_path, [limited, response({"login": "synthetic"})])
    endpoint = "https://api.github.com/search/issues?q=repo:o/r"
    store.request("GET", endpoint)
    assert store.request("GET", endpoint, allow_stale=True).stale
    assert store.request("GET", "search/issues?q=other").error == "github_rate_limited"
    assert store.request("GET", "user").value == {"login": "synthetic"}
    assert len(calls) == 2


def test_authorization_prefix_uses_same_credential_budget(tmp_path):
    first, _ = client(tmp_path, [response({}, remaining=0)], env={"GH_TOKEN": "synthetic"})
    first.request("GET", "user")
    second, calls = client(tmp_path, [], env={"GH_TOKEN": "Bearer synthetic"})
    assert second.request("POST", "repos/o/r/issues", payload={"title": "test"}).error == "github_rate_limited"
    assert calls == []


def test_enterprise_credentials_have_distinct_budget_scopes(tmp_path):
    first, _ = client(
        tmp_path, [response({}, remaining=0)], env={"GH_HOST": "unit.invalid", "GH_ENTERPRISE_TOKEN": "one"}
    )
    first.request("GET", "user")
    second, calls = client(tmp_path, [response({})], env={"GH_HOST": "unit.invalid", "GH_ENTERPRISE_TOKEN": "two"})
    assert second.request("GET", "user").error is None
    assert len(calls) == 1 and first.scope != second.scope


def test_asset_hydration_cli_reports_typed_limit(monkeypatch, capsys):
    from scripts.open_dataset import hydrate

    monkeypatch.setattr("sys.argv", ["hydrate"])

    def unavailable(**kwargs):
        raise gh.GitHubRateLimited(2000)

    monkeypatch.setattr(hydrate, "hydrate_open_dataset", unavailable)
    assert hydrate.main() == 75
    assert json.loads(capsys.readouterr().out) == {"error": "github_rate_limited", "reset_at": 2000}


@pytest.mark.parametrize(
    "module_name,function_name",
    [("scripts.lexicon.manifest_io", "_download_verified_json"), ("scripts.practice_deck.io", "_download_gzip")],
)
def test_release_pointer_limit_never_retries(module_name, function_name, monkeypatch):
    import importlib

    module = importlib.import_module(module_name)
    calls = []

    def unavailable(request, **kwargs):
        calls.append(request)
        raise gh.GitHubRateLimited(2000)

    monkeypatch.setattr(module.github_client, "http_open", unavailable)
    with pytest.raises(gh.GitHubRateLimited):
        getattr(module, function_name)(
            {
                "asset_url": "https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/v/asset",
                "gz_sha256": "a" * 64,
            }
        )
    assert len(calls) == 1


def test_cli_transport_skips_runtime_shim(tmp_path):
    import os
    import sys

    shim = tmp_path / "scripts/agent_runtime/shims/gh"
    shim.parent.mkdir(parents=True)
    shim.write_text("#!/bin/sh\nexit 99\n")
    shim.chmod(0o755)
    binary = tmp_path / "bin/gh"
    binary.parent.mkdir()
    binary.write_text(
        f"#!{sys.executable}\nprint('HTTP/1.1 200 OK\\nX-RateLimit-Remaining: 100\\nX-RateLimit-Reset: 2000\\n\\n{{}}')\n"
    )
    binary.chmod(0o755)
    store = gh.GitHubClient(
        cache_dir=tmp_path / "cache",
        env={"PATH": os.pathsep.join([str(shim.parent), str(binary.parent)])},
        clock=lambda: 1000,
    )
    assert store.request("GET", "user").value == {}


def test_cli_transport_missing_real_binary_is_typed(tmp_path, monkeypatch):
    monkeypatch.setattr(gh, "_transport_process", lambda *a, **kw: pytest.fail("no executable may run"))
    store = gh.GitHubClient(cache_dir=tmp_path, env={"PATH": str(tmp_path / "missing")})
    result = store.request("GET", "user")
    assert result.status == 599 and result.error == "github_http_error"


def test_subissue_parent_404_preserves_other_batch_nodes(tmp_path, monkeypatch):
    store, calls = client(
        tmp_path, [response({"body": "root"}), response([]), response({"message": "Not Found"}, status=404)]
    )
    monkeypatch.setattr(gh, "GitHubClient", lambda **kw: store)
    result = gh.rest_read(
        "subissue-batch", "o/r", {"cursors": {1: None, 999: None}, "body_roots": {1}}, capture_output=True, text=True
    )
    assert result.returncode == 0
    nodes = json.loads(result.stdout)["data"]["repository"]
    assert nodes["i1"]["body"] == "root" and nodes["i999"] is None
    assert len(calls) == 3


def test_subissue_connection_404_with_present_parent_is_failure(tmp_path, monkeypatch):
    store, calls = client(tmp_path, [response({"body": "root"}), response({}, status=404)])
    monkeypatch.setattr(gh, "GitHubClient", lambda **kw: store)
    result = gh.rest_read(
        "subissue-batch", "o/r", {"cursors": {1: None}, "body_roots": {1}}, capture_output=True, text=True
    )
    assert result.returncode == 1 and json.loads(result.stdout)["error"] == "github_read_failed"
    assert len(calls) == 2


def test_issue_create_resolves_milestone_before_one_write(tmp_path):
    store, calls = client(
        tmp_path,
        [response([{"title": "Ship", "number": 7}]), response({"html_url": "https://github.com/o/r/issues/1"})],
    )
    proc = gh.run(
        ["gh", "issue", "create", "--repo", "o/r", "--title", "test", "--body", "body", "--milestone", "Ship"],
        client=store,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert [r[0] for r in calls] == ["GET", "POST"]
    assert json.loads(calls[1][3]) == {"title": "test", "body": "body", "milestone": 7}


@pytest.mark.parametrize(
    "path",
    [
        "scripts/audit/lint_word_atlas.py",
        "scripts/audit/refresh_opsec_tracking_issues.py",
        "scripts/ci/cache_hygiene.py",
        "scripts/ci/check_issue_task_quality.py",
        "scripts/ci/ci_timings.py",
        "scripts/ci/reuse_green_run.py",
        "scripts/ci/split_tests.py",
        "scripts/deploy/vendor_atlas_tree.py",
        "scripts/entire/private_mode_preflight.py",
        "scripts/open_dataset/hydrate.py",
    ],
)
def test_direct_file_import_resolves_shared_client(path, tmp_path):
    import sys
    from pathlib import Path

    target = Path(__file__).resolve().parents[1] / path
    proc = subprocess.run(
        [sys.executable, "-c", "import runpy,sys; runpy.run_path(sys.argv[1], run_name='import_smoke')", str(target)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr


def test_later_page_stale_reset_is_preserved(tmp_path):
    first = response([{"number": 1, "state": "open"}])
    first.headers["Link"] = '<https://api.github.com/repos/o/r/pulls?page=2>; rel="next"'
    low = response([{"number": 1, "state": "open"}], remaining=5)
    low.headers["Link"] = first.headers["Link"]
    store, calls = client(tmp_path, [first, response([{"number": 2, "state": "open"}]), low])
    args = ["gh", "pr", "list", "--repo", "o/r", "--json", "number", "--limit", "200"]
    assert gh.run(args, client=store, capture_output=True, text=True).returncode == 0
    store.clock = lambda: 1020
    result = gh.run(args, client=store, allow_stale=True, capture_output=True, text=True)
    assert result.github_result.stale and result.github_result.age_seconds == 20
    assert json.loads(result.stderr) == {"stale": True, "age_seconds": 20, "reset_at": 2000}
    assert len(calls) == 3


def test_auth_status_falls_through_without_losing_flags(tmp_path):
    store, calls = client(tmp_path, [])
    seen = []

    def native(args, **kw):
        seen.append(args)
        return subprocess.CompletedProcess(args, 0, b"authenticated", b"")

    args = ["gh", "auth", "status", "--active"]
    result = gh.run(args, client=store, runner=native, capture_output=True, text=True)
    assert result.stdout == "authenticated" and seen == [args] and not calls


def test_local_cli_version_skips_shim(tmp_path, monkeypatch):
    binary = tmp_path / "real-gh"
    binary.write_text("#!/bin/sh\nprintf 'gh synthetic\\n'\n")
    binary.chmod(0o755)
    monkeypatch.setenv("AGENT_REAL_GH", str(binary))
    proc = gh.run(["gh", "--version"], capture_output=True, text=True, timeout=5)
    assert proc.returncode == 0 and proc.stdout == "gh synthetic\n"


@pytest.mark.parametrize("items", [[], [{"number": 1}]])
def test_pr_snapshot_preserves_cached_age_and_stale_marker(items, monkeypatch):
    import time
    from datetime import UTC, datetime, timedelta

    from scripts import github_rest_cache as rest
    from scripts.work import sources_public as sources

    now = datetime(2026, 10, 6, tzinfo=UTC)
    page = rest.RestPage(items, truncated=False, stale=True, age_seconds=90)
    monkeypatch.setattr(rest, "list_open_prs", lambda *a, **kw: page)
    monkeypatch.setattr(sources, "_utc_now", lambda: now + timedelta(seconds=5))
    snapshot = sources._PRSnapshot(sources.DEFAULT_PUBLIC_REPOSITORY, 1000)
    snapshot._refresh(now.isoformat())
    snapshot._started_at = time.monotonic()
    result = snapshot.read()
    assert result.status == "stale" and result.age_s == 95
    assert datetime.fromisoformat(result.observed_at) == now - timedelta(seconds=90)
    assert result.count == len(items)


@pytest.mark.parametrize("kind", ["issues", "prs"])
def test_empty_cached_lists_keep_stale_metadata(tmp_path, monkeypatch, kind):
    from scripts import github_rest_cache as rest
    from scripts.work import sources_public as sources

    repo = sources.DEFAULT_PUBLIC_REPOSITORY
    endpoint = (
        f"repos/{repo}/{'pulls' if kind == 'prs' else 'issues'}?state=open&per_page=100&sort=created&direction=desc"
    )
    store, calls = client(tmp_path, [response([], remaining=0)])
    store.request("GET", endpoint)
    store.clock = lambda: 1043
    store.allow_stale = True
    monkeypatch.setattr(gh, "GitHubClient", lambda **kw: store)
    cache = rest.GitHubRestCache(identity="fixture")
    page = getattr(rest, "list_open_" + kind)(repo, limit=10, timeout=2, cache=cache)
    assert page == [] and page.stale and page.age_seconds == 43
    assert len(calls) == 1
    if kind == "issues":
        monkeypatch.setattr(rest, "shared_cache", lambda: cache)
        section = sources._fetch_open_issues_rest(repo, 10)
        assert section.status == "stale" and section.age_s == 43 and section.count == 0


def test_cached_empty_review_list_is_incomplete(monkeypatch):
    import time

    from scripts import github_rest_cache as rest

    cache = rest.GitHubRestCache(
        identity="fixture", transport=lambda *a: (200, {"x-github-stale": "true", "x-github-age": "43"}, b"[]")
    )
    rows, complete = rest._list_body(cache, "repos/o/r/pulls/1/reviews", deadline=time.monotonic() + 2, timeout=2)
    assert rows == [] and rows.stale and not complete


def test_pr_snapshot_rate_failure_does_not_leave_warm_data_current(monkeypatch):
    import time

    from scripts import github_rest_cache as rest
    from scripts.work import sources_public as sources

    snapshot = sources._PRSnapshot(sources.DEFAULT_PUBLIC_REPOSITORY, 1000)
    observed = sources._iso_now()
    snapshot._snapshot = sources.SectionResult("prs", "ok", payload=[], observed_at=observed)

    def limited(*a, **kw):
        raise rest.GitHubRestError("github_rate_limited", status=429)

    monkeypatch.setattr(rest, "list_open_prs", limited)
    snapshot._refresh(sources._iso_now())
    snapshot._started_at = time.monotonic()
    result = snapshot.read()
    assert result.status == "stale" and result.reason == "github_rate_limited"
    assert result.observed_at == observed and result.payload == []


def test_timer_refuses_unattributed_exit_75():
    @gh.timer
    def unrelated():
        raise subprocess.CalledProcessError(75, ["local"], stderr='{"error":"github_rate_limited","reset_at":2000}')

    with pytest.raises(subprocess.CalledProcessError):
        unrelated()


def test_timer_skips_client_owned_limit_receipt(capsys):
    @gh.timer
    def limited():
        gh._result_process(
            ["gh", "api", "user"],
            gh.Result(error="github_rate_limited", reset_at=2000, status=429),
            {},
            {"capture_output": True, "text": True, "check": True},
        )

    assert limited() == 0
    assert "skipped github_rate_limited reset_at=2000" in capsys.readouterr().out


def test_bounded_cli_body_is_spooled_and_budget_headers_retained(tmp_path):
    import sys

    binary = tmp_path / "gh"
    binary.write_text(
        f"#!{sys.executable}\nprint('HTTP/2 200\\nX-RateLimit-Remaining: 100\\nX-RateLimit-Reset: 2000\\n\\n' + 'x' * 4096)\n"
    )
    binary.chmod(0o755)
    store = gh.GitHubClient(
        cache_dir=tmp_path / "cache", env={"AGENT_REAL_GH": str(binary)}, max_response_bytes=1024, clock=lambda: 1000
    )
    result = store.request("GET", "repos/o/r/actions/artifacts/1/zip")
    assert result.status == 413 and result.value["message"] == "github_response_too_large"
    with store._db() as db:
        assert db.execute("select remaining from budget").fetchone()[0] == 100
        assert db.execute("select count(*) from cache").fetchone()[0] == 0


@pytest.mark.parametrize("raw", [b"missing status headers", b"HTTP/2 200\r\nX-Test: " + b"x" * 65536 + b"\r\n\r\n{}"])
def test_bounded_cli_rejects_missing_or_oversized_headers(tmp_path, raw):
    import sys

    binary = tmp_path / "gh"
    binary.write_text(f"#!{sys.executable}\nimport sys\nsys.stdout.buffer.write({raw!r})\n")
    binary.chmod(0o755)
    store = gh.GitHubClient(cache_dir=tmp_path / "cache", env={"AGENT_REAL_GH": str(binary)}, max_response_bytes=1024)
    result = store.request("GET", "repos/o/r/actions/artifacts/1/zip")
    assert result.status == 599 and result.error == "github_http_error"
    with store._db() as db:
        assert db.execute("select count(*) from cache").fetchone()[0] == 0


def test_per_command_body_bound_does_not_mutate_shared_client(tmp_path):
    store, calls = client(tmp_path, [gh.Response(200, {}, b"x" * 2048)])
    result = gh.run(
        ["gh", "api", "repos/o/r/actions/artifacts/1/zip"],
        client=store,
        max_response_bytes=1024,
        capture_output=True,
        text=True,
    )
    assert result.github_result.status == 413 and len(calls) == 1
    assert store.max_response_bytes is None


def test_oversized_cached_body_is_not_materialized_for_bounded_read(tmp_path):
    store, calls = client(
        tmp_path, [gh.Response(200, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "2000"}, b"x" * 2048)]
    )
    store.request("GET", "repos/o/r/actions/artifacts/1/zip")
    store.max_response_bytes = 1024
    result = store.request("GET", "repos/o/r/actions/artifacts/1/zip")
    assert result.error == "github_rate_limited" and len(calls) == 1


def linked_response(value, endpoint):
    item = response(value)
    item.headers["Link"] = f'<https://api.github.com/{endpoint}>; rel="next"'
    return item


def test_run_list_reads_250_runs_up_to_limit_1000(tmp_path):
    rows = [{"id": i, "created_at": "2026-10-05T00:00:00Z"} for i in range(250)]
    store, calls = client(
        tmp_path,
        [
            linked_response({"workflow_runs": rows[:100]}, "repos/o/r/actions/runs?page=2"),
            linked_response({"workflow_runs": rows[100:200]}, "repos/o/r/actions/runs?page=3"),
            response({"workflow_runs": rows[200:]}),
        ],
    )
    result = gh.run(
        ["gh", "run", "list", "-R", "o/r", "--limit", "1000", "--json", "databaseId"],
        client=store,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == [{"databaseId": i} for i in range(250)]
    assert len(calls) == 3


@pytest.mark.parametrize("short", [False, True])
def test_run_list_filter_aliases_are_exact(tmp_path, short):
    from urllib.parse import parse_qs, urlparse

    store, calls = client(tmp_path, [response({"workflow_runs": []})])
    flags = ["-w", "-b", "-e", "-s", "-c"] if short else ["--workflow", "--branch", "--event", "--status", "--commit"]
    args = ["gh", "run", "list", "-R", "o/r", "--json", "databaseId"]
    for flag, value in zip(flags, ["ci.yml", "main", "merge_group", "completed", "a" * 40], strict=True):
        args += [flag, value]
    assert gh.run(args, client=store, text=True, capture_output=True).returncode == 0
    endpoint = urlparse(calls[0][1])
    assert endpoint.path == "repos/o/r/actions/workflows/ci.yml/runs"
    assert parse_qs(endpoint.query) == {
        "per_page": ["30"],
        "branch": ["main"],
        "event": ["merge_group"],
        "status": ["completed"],
        "head_sha": ["a" * 40],
    }


@pytest.mark.parametrize("kind,state", [("pr", "merged"), ("pr", "open"), ("issue", "closed")])
def test_list_limit_five_stops_after_one_page(tmp_path, kind, state):
    rows = [{"number": i, "state": "closed", "merged_at": "2026-10-05T00:00:00Z"} for i in range(5)]
    store, calls = client(
        tmp_path, [linked_response(rows, f"repos/o/r/{'pulls' if kind == 'pr' else 'issues'}?page=2")]
    )
    args = ["gh", kind, "list", "-R", "o/r", "--state", state, "--limit", "5", "--json", "number"]
    result = gh.run(args, client=store, text=True, capture_output=True)
    assert json.loads(result.stdout) == [{"number": i} for i in range(5)]
    assert len(calls) == 1 and "per_page=5" in calls[0][1]


@pytest.mark.parametrize("kind", ["pr", "issue"])
def test_list_limit_counts_matching_rows(tmp_path, kind):
    ignored = {"number": 99, "state": "closed"}
    if kind == "issue":
        ignored["pull_request"] = {}
    store, calls = client(
        tmp_path,
        [
            linked_response([ignored], "repos/o/r/list?page=2"),
            response([{"number": 1, "merged_at": "2026-10-05T00:00:00Z"}]),
        ],
    )
    args = ["gh", kind, "list", "-R", "o/r", "--limit", "1", "--json", "number"]
    if kind == "pr":
        args += ["--state", "merged"]
    result = gh.run(args, client=store, text=True, capture_output=True)
    assert json.loads(result.stdout) == [{"number": 1}] and len(calls) == 2


@pytest.mark.parametrize(
    "command",
    [
        ["api", "repos/o/r/issues", "--paginate"],
        ["pr", "list", "--json", "number", "--limit", "1000"],
        ["issue", "list", "--json", "number", "--limit", "1000"],
        ["run", "list", "--json", "databaseId", "--limit", "1000"],
    ],
)
def test_page_cap_returns_typed_error(tmp_path, command):
    value = {"workflow_runs": []} if command[0] == "run" else []
    store, calls = client(tmp_path, [linked_response(value, "repos/o/r/list?page=2")] * 100, env={"GH_REPO": "o/r"})
    result = gh.run(["gh", *command], client=store, text=True, capture_output=True)
    assert result.returncode == 1 and result.github_result.error == "github_pagination_limit"
    assert len(calls) == 100


@pytest.mark.parametrize(
    "flags",
    [
        ["-H", "x"],
        ["--head=x"],
        ["--author", "alice"],
        ["--assignee", "alice"],
        ["--draft"],
        ["--label", "bug"],
        ["--base", "main"],
        ["--search", "is:merged"],
        ["--unknown-flag", "x"],
        ["--json", "unmodelledField"],
        ["--template", "{{.number}}"],
    ],
)
def test_pr_filters_and_unmodelled_fields_fall_through_intact(tmp_path, flags):
    store, calls = client(tmp_path, [])
    seen = []

    def native(args, **kw):
        assert kw["env"]["NO_COLOR"] == "1"
        assert "FORCE_COLOR" not in kw["env"]
        assert kw["timeout"] == 7
        seen.append(args)
        return subprocess.CompletedProcess(args, 0, b'[{"number":1,"headRefName":"x"}]', b"")

    args = ["gh", "pr", "list", "-R", "o/r", "--json", "number,headRefName", *flags]
    result = gh.run(args, client=store, runner=native, capture_output=True, text=True, timeout=7)
    assert json.loads(result.stdout) == [{"number": 1, "headRefName": "x"}]
    assert seen == [args] and calls == []


def admitted_read_cases():
    from scripts.opsec.gh_snapshot import READ_GRAMMARS

    cases = []
    for (kind, action), (minimum, _maximum, flags) in READ_GRAMMARS.items():
        positional = ["x"] * minimum
        if kind in {"pr", "issue", "run"}:
            positional = ["1"] * minimum
        base = ["gh", kind, action, *positional]
        cases.append(base)
        for flag, valued in flags.items():
            value = "o/r" if flag in {"--repo", "-R"} else "number" if flag == "--json" else "x"
            cases.append([*base, flag, *([value] if valued else [])])
    return cases


@pytest.mark.parametrize("args", admitted_read_cases())
def test_every_shim_admitted_read_translates_or_falls_through(tmp_path, args):
    from pathlib import Path

    from scripts.opsec.gh_snapshot import READ_GRAMMARS, parse

    root = Path(__file__).resolve().parents[1]
    # These are the live entry chain: bash shim -> admission -> client.
    assert "scripts/opsec/gh_entry.py" in (root / "scripts/agent_runtime/shims/gh").read_text()
    entry = (root / "scripts/opsec/gh_entry.py").read_text()
    assert "frozen = admit(" in entry and 'run(["gh", *frozen.argv]' in entry
    parse(args[3:], READ_GRAMMARS[tuple(args[1:3])])
    translated, native = [], []

    def transport(method, endpoint, headers, body, timeout):
        translated.append(endpoint)
        if args[1] == "run" and args[2] == "list":
            return response({"workflow_runs": []})
        if "/pulls?" in endpoint:
            return response([{"number": 1}])
        return response([] if args[2] == "list" else {"number": 1, "head": {}, "base": {}})

    def fallback(command, **kw):
        native.append(command)
        return subprocess.CompletedProcess(command, 0, b"native", b"")

    store = gh.GitHubClient(cache_dir=tmp_path, env={"GH_REPO": "o/r"}, transport=transport)
    result = gh.run(args, client=store, runner=fallback, capture_output=True, text=True)
    assert result.returncode == 0
    assert bool(translated) != bool(native)
    if native:
        assert native == [args]
    else:
        assert gh._translation_options(args) is not None


@pytest.mark.parametrize("entry", ["request", "run", "request_run"])
def test_stale_requires_opt_in_for_gate_readers(tmp_path, monkeypatch, entry):
    store, calls = client(tmp_path, [response({"number": 1, "head": {"sha": "a" * 40}}, remaining=0)])
    endpoint = "repos/o/r/pulls/1"
    store.request("GET", endpoint)
    args = ["gh", "pr", "view", "1", "-R", "o/r", "--json", "headRefOid"]
    if entry == "request":
        assert store.request("GET", endpoint).error == "github_rate_limited"
    elif entry == "run":
        result = gh.run(args, client=store, capture_output=True, text=True)
        assert result.returncode == 75 and result.github_result.error == "github_rate_limited"
    else:
        from scripts.publish import github as publisher

        monkeypatch.setattr(gh, "GitHubClient", lambda **kw: store)
        monkeypatch.setattr(publisher.gate, "real_gh", lambda env: "gh")
        result = publisher.request_run(args, capture_output=True, text=True)
        assert result.returncode == 75 and result.github_result.error == "github_rate_limited"
    assert len(calls) == 1
    assert store.request("GET", endpoint, allow_stale=True).stale
    assert store.request("GET", endpoint, allow_stale=True, fresh=True).error == "github_rate_limited"


def test_native_fallback_honours_budget_and_never_retries(tmp_path):
    store, calls = client(tmp_path, [response([], remaining=0)])
    store.request("GET", "repos/o/r/issues")

    def native(*a, **kw):
        raise AssertionError("exhausted budget reached gh")

    result = gh.run(["gh", "search", "prs", "head:x"], client=store, runner=native, capture_output=True)
    assert result.returncode == 75 and result.github_result.error == "github_rate_limited"
    assert len(calls) == 1


def test_native_fallback_rate_limit_is_typed_and_stops_next_call(tmp_path):
    store, calls = client(tmp_path, [])
    seen = []

    def native(args, **kw):
        seen.append(args)
        return subprocess.CompletedProcess(args, 1, b"", b"HTTP 429: secondary rate limit")

    for _ in range(2):
        result = gh.run(["gh", "pr", "status"], client=store, runner=native, capture_output=True)
        assert result.returncode == 75 and result.github_result.error == "github_rate_limited"
    assert len(seen) == 1 and not calls


@pytest.mark.parametrize("total,limited", [(250, False), (1000, True)])
def test_flake_ledger_1000_run_read_and_denominator_guard(tmp_path, monkeypatch, total, limited):
    from datetime import date

    from scripts.ci import flake_ledger

    rows = [{"id": i + 1, "created_at": "2026-10-05T00:00:00Z"} for i in range(total)]
    pages = []
    for start in range(0, total, 100):
        page = {"workflow_runs": rows[start : start + 100]}
        pages.append(
            linked_response(page, f"repos/o/r/actions/runs?page={start // 100 + 2}")
            if start + 100 < total
            else response(page)
        )
    store, calls = client(tmp_path, pages, env={"GH_REPO": "o/r"})
    original = flake_ledger._gh
    monkeypatch.setattr(gh, "GitHubClient", lambda **kw: store)

    def ledger_command(*args):
        if args[:2] == ("run", "download"):
            raise subprocess.CalledProcessError(1, ["gh", *args])
        return original(*args)

    monkeypatch.setattr(flake_ledger, "_gh", ledger_command)
    monkeypatch.setattr(flake_ledger, "_reused_pytest", lambda _: False)
    if limited:
        with pytest.raises(ValueError, match="reached the 1000-run limit"):
            flake_ledger.fetch_queue_junit(tmp_path, since=date(2026, 10, 1))
    else:
        artifacts, missing = flake_ledger.fetch_queue_junit(tmp_path, since=date(2026, 10, 1))
        assert artifacts == {} and missing == list(range(1, 251))
    assert len(calls) == (total + 99) // 100


@pytest.mark.parametrize(
    "suffix",
    [
        ["--field", "nested[value]=1"],
        ["--field", "value=-1"],
        ["--field", "value=01"],
        ["--field", "value={branch}"],
        ["--field", "value=1", "-f", "value=text"],
        ["--field", "body=@input.json"],
        ["--include"],
        ["--cache", "1h"],
        ["--hostname", "other.invalid"],
        ["--input", "input.json", "--field", "x=y"],
        ["--method", "POST", "--paginate"],
        ["--slurp"],
        ["--paginate=false"],
        ["-X", "GET", "--method", "POST"],
    ],
)
def test_unmodelled_api_flag_semantics_fall_through(tmp_path, suffix):
    store, calls = client(tmp_path, [])
    args = ["gh", "api", "repos/o/r/issues", *suffix]
    seen = []

    def native(command, **kw):
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, b"[]", b"")

    assert gh.run(args, client=store, runner=native, capture_output=True).returncode == 0
    assert seen == [args] and not calls


@pytest.mark.parametrize("flag", ["-a", "--approve", "--approve=true"])
def test_worker_cannot_bypass_approval_guard_via_native_fallback(tmp_path, flag):
    store, calls = client(tmp_path, [], env={"AGENT_NO_MERGE": "1"})

    def native(*args, **kw):
        raise AssertionError("forbidden approval reached real gh")

    result = gh.run(["gh", "pr", "review", "1", flag, "--unmodelled"], client=store, runner=native, capture_output=True)
    assert result.github_result.error == "github_worker_write_forbidden" and not calls


def test_native_fallback_resolves_real_binary_and_preserves_exit(tmp_path, monkeypatch):
    binary = tmp_path / "gh"
    binary.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"; printf 'native error' >&2; exit 4\n")
    binary.chmod(0o755)
    store = gh.GitHubClient(cache_dir=tmp_path / "cache", env={"AGENT_REAL_GH": str(binary), "FORCE_COLOR": "1"})
    args = ["gh", "pr", "list", "-H", "x"]
    result = gh.run(args, client=store, capture_output=True, text=True)
    assert result.returncode == 4 and result.stdout.splitlines() == args[1:] and result.stderr == "native error"
    with pytest.raises(subprocess.CalledProcessError) as error:
        gh.run(args, client=store, capture_output=True, text=True, check=True)
    assert error.value.returncode == 4 and error.value.stderr == "native error"


def test_native_fallback_response_ceiling_is_bounded(tmp_path):
    binary = tmp_path / "gh"
    binary.write_text("#!/bin/sh\nprintf '01234567890123456789'\n")
    binary.chmod(0o755)
    store = gh.GitHubClient(cache_dir=tmp_path / "cache", env={"AGENT_REAL_GH": str(binary)}, max_response_bytes=10)
    result = gh.run(["gh", "pr", "status"], client=store, capture_output=True)
    assert result.github_result.error == "github_response_too_large"


@pytest.mark.parametrize("kind", ["pr", "issue"])
def test_label_projection_preserves_gh_field_names(tmp_path, kind):
    row = {
        "id": 1,
        "node_id": "NODE",
        "number": 1,
        "state": "open",
        "labels": [
            {"id": 123, "node_id": "LABEL", "name": "bug", "description": None, "color": "ff0000", "url": "ignored"}
        ],
    }
    store, calls = client(tmp_path, [response(row)])
    result = gh.run(
        ["gh", kind, "view", "1", "-R", "o/r", "--json", "id,labels"], client=store, capture_output=True, text=True
    )
    assert json.loads(result.stdout) == {
        "id": "NODE",
        "labels": [{"id": "LABEL", "name": "bug", "description": "", "color": "ff0000"}],
    }
    assert len(calls) == 1


@pytest.mark.parametrize(
    "operation,fields", [("queue-status", {"number": 1, "branch": "main"}), ("queue-snapshot", {"branches": {"main"}})]
)
def test_queue_reads_use_fresh_typed_rest_facts(tmp_path, monkeypatch, operation, fields):
    row = {
        "id": 1,
        "node_id": "NODE",
        "number": 1,
        "state": "open",
        "head": {"sha": "a" * 40, "ref": "feature"},
        "base": {"ref": "main"},
        "labels": [],
    }
    data = (
        {"repository": {"pullRequest": {"isInMergeQueue": False}}}
        if operation == "queue-status"
        else {"repository": {"p1": {"isInMergeQueue": False}, "q0": {"url": "queue"}}}
    )
    replies = [response(row)] if operation == "queue-status" else [response([row]), response(row)]
    store, calls = client(tmp_path, [*replies, response({"data": data})])
    monkeypatch.setattr(gh, "GitHubClient", lambda **kw: store)

    def reject(*a, **kw):
        raise AssertionError("typed queue facts went through command translation")

    monkeypatch.setattr(gh, "run", reject)
    result = gh.queue_read(operation, "o/r", fields, capture_output=True, text=True)
    assert result.returncode == 0
    repository = json.loads(result.stdout)["data"]["repository"]
    if operation == "queue-status":
        assert repository["pullRequest"]["merged"] is False
    else:
        assert repository["pullRequests"]["nodes"][0]["id"] == "NODE"
    expected = ["repos/o/r/pulls/1"] if operation == "queue-status" else ["repos/o/r/pulls", "repos/o/r/pulls/1"]
    assert [c[1].split("?")[0] for c in calls] == [*expected, "graphql"]


def _api_pages():
    """Two issues pages. Native ``gh api --paginate`` concatenates the arrays."""
    first = response([{"number": 1}, {"number": 2}])
    first.headers["Link"] = '<https://api.github.com/repos/o/r/issues?page=2>; rel="next"'
    return [first, response([{"number": 3}])]


def _native_api_shape(args):
    """Stdout native gh prints for the api reads this client still translates."""
    if "--jq" in args or "-q" in args:
        # One page: jq runs on that document. ``length`` of the first page is 2.
        return "2\n"
    if "--paginate" in args:
        return json.dumps([{"number": 1}, {"number": 2}, {"number": 3}], ensure_ascii=False)
    return json.dumps([{"number": 1}, {"number": 2}], ensure_ascii=False)


def admitted_api_read_cases():
    from scripts.opsec.gh_snapshot import REST_GET

    endpoint = "repos/o/r/issues"
    base = ["gh", "api", endpoint]
    cases = [base]
    _minimum, _maximum, flags = REST_GET
    for flag, valued in flags.items():
        if flag in {"--method", "-X"}:
            value = "GET"
        elif flag in {"--header", "-H"}:
            value = "Accept: application/vnd.github+json"
        elif flag in {"--jq", "-q"}:
            value = "length"
        elif flag == "--cache":
            value = "1h"
        else:
            value = None
        cases.append([*base, flag, *([value] if valued else [])])
    return cases


@pytest.mark.parametrize("args", admitted_api_read_cases())
def test_every_admitted_api_read_translates_exactly_or_falls_through(tmp_path, args):
    from pathlib import Path

    from scripts.opsec.gh_snapshot import REST_GET, admit, parse

    root = Path(__file__).resolve().parents[1]
    assert "scripts/opsec/gh_entry.py" in (root / "scripts/agent_runtime/shims/gh").read_text()
    entry = (root / "scripts/opsec/gh_entry.py").read_text()
    assert "frozen = admit(" in entry and 'run(["gh", *frozen.argv]' in entry
    parse(args[2:], REST_GET)
    frozen = admit(args[1:], cwd=tmp_path, environment={"GH_REPO": "o/r"})
    assert frozen.write is False and frozen.argv == args[1:]

    translated, native = [], []

    def transport(method, endpoint, headers, body, timeout):
        translated.append(endpoint)
        return _api_pages()[len(translated) - 1]

    def fallback(command, **kw):
        native.append(command)
        return subprocess.CompletedProcess(command, 0, b"native", b"")

    store = gh.GitHubClient(cache_dir=tmp_path, env={"GH_REPO": "o/r"}, transport=transport)
    result = gh.run(args, client=store, runner=fallback, capture_output=True, text=True)
    assert result.returncode == 0
    assert bool(translated) != bool(native)
    if native:
        assert native == [args]
    else:
        assert gh._translation_options(args) is not None
        assert result.stdout == _native_api_shape(args)
        if "--paginate" in args:
            assert len(translated) == 2


def test_api_paginate_object_pages_fall_through(tmp_path):
    first = response({"total_count": 2, "workflow_runs": [1]})
    first.headers["Link"] = '<https://api.github.com/repos/o/r/actions/runs?page=2>; rel="next"'
    store, calls = client(tmp_path, [first, response({"total_count": 2, "workflow_runs": [2]})])
    args = ["gh", "api", "repos/o/r/actions/runs", "--paginate"]
    seen = []

    def native(command, **kw):
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, b'{"page":1}{"page":2}', b"")

    result = gh.run(args, client=store, runner=native, capture_output=True)
    assert seen == [args]
    assert result.stdout == b'{"page":1}{"page":2}'
    assert calls and all(call[0] == "GET" for call in calls)


def test_api_paginate_jq_falls_through_without_merging_pages(tmp_path):
    store, calls = client(tmp_path, [])
    args = ["gh", "api", "repos/o/r/issues", "--paginate", "--jq", "length"]
    seen = []

    def native(command, **kw):
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, b"2\n2\n", b"")

    result = gh.run(args, client=store, runner=native, capture_output=True)
    assert seen == [args] and result.stdout == b"2\n2\n" and calls == []


def test_api_paginate_slurp_wraps_object_pages(tmp_path):
    first = response({"workflow_runs": [1]})
    first.headers["Link"] = '<https://api.github.com/repos/o/r/actions/runs?page=2>; rel="next"'
    store, calls = client(tmp_path, [first, response({"workflow_runs": [2]})])
    result = gh.run(
        ["gh", "api", "repos/o/r/actions/runs", "--paginate", "--slurp"],
        client=store,
        text=True,
        capture_output=True,
    )
    assert json.loads(result.stdout) == [{"workflow_runs": [1]}, {"workflow_runs": [2]}]
    assert len(calls) == 2


def test_pr_view_404_falls_through_with_native_message(tmp_path):
    store, calls = client(tmp_path, [response({"message": "Not Found"}, status=404)])
    args = ["gh", "pr", "view", "8183", "--repo", "o/r", "--json", "number,state,headRefOid"]
    seen = []

    def native(command, **kw):
        seen.append(command)
        return subprocess.CompletedProcess(
            command,
            1,
            b"",
            b"GraphQL: Could not resolve to a PullRequest with the number of 8183. (repository.pullRequest)\n",
        )

    result = gh.run(args, client=store, runner=native, capture_output=True, text=True)
    assert calls[0][1] == "repos/o/r/pulls/8183"
    assert seen == [args]
    assert result.returncode == 1
    assert "Could not resolve to a PullRequest" in result.stderr


def test_pr_view_non_404_stays_typed(tmp_path):
    store, calls = client(tmp_path, [response({"message": "boom"}, status=500)])

    def native(*args, **kw):
        raise AssertionError("non-404 pr view reached native gh")

    result = gh.run(
        ["gh", "pr", "view", "1", "--repo", "o/r", "--json", "number"],
        client=store,
        runner=native,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1 and json.loads(result.stdout)["status"] == 500 and calls



def test_substituted_subprocess_does_not_skip_rest_or_worker_guard(tmp_path, monkeypatch):
    store, calls = client(tmp_path, [response({"number": 1, "state": "open"})], env={"GH_REPO": "o/r", "AGENT_NO_MERGE": "1"})
    monkeypatch.setattr(subprocess, "run", lambda *args, **kw: pytest.fail("subprocess spy is not a client seam"))
    result = gh.run(["gh", "issue", "view", "1", "--json", "number,state"], client=store, capture_output=True, text=True)
    assert json.loads(result.stdout) == {"number": 1, "state": "OPEN"}
    denied = gh.run(["gh", "pr", "merge", "1"], client=store, capture_output=True, text=True)
    assert denied.github_result.error == "github_worker_write_forbidden"
    assert [(call[0], call[1]) for call in calls] == [("GET", "repos/o/r/issues/1")]



def test_publisher_write_live_limit_records_headers_without_replay(tmp_path):
    import os
    import sys

    from scripts.publish import github as publisher

    binary = tmp_path / "gh"
    calls = tmp_path / "calls"
    binary.write_text(
        f"#!{sys.executable}\nfrom pathlib import Path\n"
        f"with Path({str(calls)!r}).open('a') as stream: stream.write('call\\n')\n"
        "print('HTTP/1.1 403 Forbidden\\nRetry-After: 120\\nX-RateLimit-Remaining: 77\\nX-RateLimit-Reset: 4000000000\\n\\n'"
        ' + \'{"message":"You have exceeded a secondary rate limit."}\')\n'
        "raise SystemExit(1)\n"
    )
    binary.chmod(0o755)
    environment = {"GH_REPO": "o/r", "AGENT_REAL_GH": str(binary), "PATH": os.environ["PATH"]}
    command = ["gh", "pr", "comment", "1", "--repo", "o/r", "--body", "clean"]
    result = publisher._run_transport(command, env=environment, capture_output=True, text=True)
    assert result.returncode == 75
    assert result.github_result.error == "github_rate_limited"
    assert calls.read_text().splitlines() == ["call"]
    store = gh.GitHubClient(env=environment)
    with store._db() as db:
        budgets = {resource: (remaining, reset) for resource, remaining, reset in db.execute(
            "SELECT resource,remaining,reset FROM budget WHERE scope=?", (store.scope,)
        )}
    assert budgets["core"] == (77, 4000000000)
    assert budgets["secondary"] == (0, result.github_result.reset_at)
    deferred = publisher._run_transport(command, env=environment, capture_output=True, text=True)
    assert deferred.github_result.error == "github_rate_limited"
    assert calls.read_text().splitlines() == ["call"]
