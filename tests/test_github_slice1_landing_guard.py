"""Landing guard and typed refusals in the shared GitHub client (#10730 slice 1); no network.

Every case drives the real client. A recording fake transport stands in for GitHub's HTTP
API and a recording runner for native ``gh``; assertions are on what reached that wire.
Contract (frozen brief): only an authentic GitHub ``Retry-After`` hold may refuse a landing
call; every local refusal is ``github_rate_limited``, exit 75, with a reason from a closed
set; reads are never landing by URL; only vetted in-repo entry points open landing flows.
"""

from __future__ import annotations

import ast
import email.utils
import json
import os
import subprocess
import time
from pathlib import Path

import pytest

from scripts.common import github_client as gh
from tests.opsec_fixtures import CATALOG

ROOT = Path(__file__).resolve().parents[1]
NOW = 1_000
OPEN = 2_000  # a reset in the future: the rate-limit window is open
EXPIRED = NOW - 1
HEAD = "a" * 40
REASONS = {"retry_after", "secondary_hold", "core_below_landing_reserve", "pool_exhausted"}
ENQUEUE = 'mutation { enqueuePullRequest(input: {pullRequestId: "PR_1"}) { clientMutationId } }'
VIEWER = "query { viewer { login } }"


class Wire:
    """Recording fake transport (HTTP) and native ``gh`` runner: what reached GitHub."""

    def __init__(self, reply=None, native=None):
        self.sent = []
        self._reply = reply or (lambda method, endpoint, body: gh.Response(200, {}, b"{}"))
        self._native = native or (lambda argv: subprocess.CompletedProcess(argv, 0, b"[]", b""))

    def transport(self, method, endpoint, headers, body, timeout):
        self.sent.append(("http", method, endpoint))
        return self._reply(method, endpoint, body)

    def runner(self, command, **kwargs):
        self.sent.append(("native", *command[1:]))
        return self._native(command)


def store(tmp_path, wire, budgets=(), *, env=None, now=NOW):
    """The real client over the recording wire, with ``(resource, remaining, reset)`` rows stored."""
    client = gh.GitHubClient(
        cache_dir=tmp_path, transport=wire.transport, runner=wire.runner, clock=lambda: now, env=env or {}
    )
    with client._db() as db:
        for resource, remaining, reset in budgets:
            gh._store_budget(db, client.scope, resource, remaining, reset)
    return client


def pool_rows(pool, value):
    if value == "unknown":
        return []
    if value == "expired":
        return [(pool, 0, EXPIRED)]
    return [(pool, value, OPEN)]


def admitted(result):
    if isinstance(result, subprocess.CompletedProcess):
        assert result.returncode == 0, result.stderr
    else:
        assert result.error is None, result.error


def refused(result, reason, reset=OPEN):
    observation = getattr(result, "github_result", result)
    assert observation.error == "github_rate_limited"
    assert observation.reason == reason and observation.reset_at == reset
    if isinstance(result, subprocess.CompletedProcess):
        assert result.returncode == 75
        detail = json.loads(result.stdout)
        assert detail == {"error": "github_rate_limited", "reset_at": reset, "reason": reason}


# --- decision table: every remaining value, every pool, landing and non-landing --------------

VALUES = [0, 1, 10, 11, 499, 500, "unknown", "expired"]
CORE_REFUSES = {0, 1, 10, 11, 499}
POOL_REFUSES = {0, 1, 10}


def _rest(method, endpoint, payload=None):
    return lambda client: client.request(method, endpoint, payload=payload)


def _native(*argv):
    return lambda client: gh.run(["gh", *argv], client=client, capture_output=True)


def _in_keeper_run(call):
    """Issue ``call`` from inside the merge-queue keeper's real ``run`` (a vetted landing flow)."""

    def issue(client):
        from scripts.orchestration import merge_queue_keeper as keeper

        class Done(Exception):
            pass

        class Keeper:
            def branch_names(self):
                raise Done(call(client))

        with pytest.raises(Done) as done:
            keeper.run(Keeper(), Path("unused-state.json"), apply=False)
        return done.value.args[0]

    return issue


CALLS = {
    # core: the landing write, and a read the incident's audits made (never landing by URL)
    ("core", "landing", "rest"): _rest("PUT", "repos/o/r/pulls/1/merge", {"merge_method": "squash"}),
    ("core", "other", "rest"): _rest("GET", "repos/o/r/issues/1/timeline"),
    ("core", "landing", "native"): _native("pr", "merge", "1", "--repo", "o/r", "--auto"),
    ("core", "other", "native"): _native("pr", "status"),
    # graphql: the merge-queue mutation, and an ordinary query
    ("graphql", "landing", "rest"): _rest("POST", "graphql", {"query": ENQUEUE}),
    ("graphql", "other", "rest"): _rest("POST", "graphql", {"query": VIEWER}),
    ("graphql", "landing", "native"): _native("api", "graphql", "-f", "query=" + ENQUEUE, "--template", "{{.}}"),
    ("graphql", "other", "native"): _native("api", "graphql", "-f", "query=" + VIEWER, "--template", "{{.}}"),
    # search: no landing verb spends search; a search inside a landing flow is landing traffic
    ("search", "landing", "rest"): _in_keeper_run(_rest("GET", "search/issues?q=repo:o/r")),
    ("search", "other", "rest"): _rest("GET", "search/issues?q=repo:o/r"),
    ("search", "landing", "native"): _in_keeper_run(_native("search", "prs", "x")),
    ("search", "other", "native"): _native("search", "prs", "x"),
}


@pytest.mark.parametrize("value", VALUES, ids=str)
@pytest.mark.parametrize(("pool", "kind", "path"), list(CALLS), ids="-".join)
def test_decision_table_over_every_remaining_value(tmp_path, pool, kind, path, value):
    wire = Wire()
    client = store(tmp_path, wire, pool_rows(pool, value))
    result = CALLS[(pool, kind, path)](client)
    expected = None
    if kind == "other" and value in (CORE_REFUSES if pool == "core" else POOL_REFUSES):
        expected = "core_below_landing_reserve" if pool == "core" else "pool_exhausted"
    if expected is None:
        admitted(result)
        assert len(wire.sent) == 1
    else:
        refused(result, expected)
        assert wire.sent == []


@pytest.mark.parametrize("value", VALUES, ids=str)
@pytest.mark.parametrize("pool", ["core", "graphql", "search", "code_search"])
@pytest.mark.parametrize("call_class", ["landing", "exempt", None])
def test_pure_decision_function_table(pool, value, call_class):
    rows = {resource: (remaining, reset) for resource, remaining, reset in pool_rows(pool, value)}
    decision = gh._refusal(rows, {pool}, call_class=call_class, now=NOW)
    if call_class is not None or value not in (CORE_REFUSES if pool == "core" else POOL_REFUSES):
        assert decision is None
    else:
        assert decision == ("core_below_landing_reserve" if pool == "core" else "pool_exhausted", OPEN)


def test_negative_core_remaining_is_not_a_budget_and_never_refuses():
    assert gh._refusal({"core": (-1, OPEN)}, {"core"}, call_class=None, now=NOW) is None


# --- holds: only an authentic GitHub hold refuses landing ------------------------------------

LANDING = {
    "rest": _rest("PUT", "repos/o/r/pulls/1/merge", {"merge_method": "squash"}),
    "graphql": _rest("POST", "graphql", {"query": ENQUEUE}),
    "native": _native("pr", "merge", "1", "--repo", "o/r", "--auto"),
    "review": _rest("POST", "repos/o/r/pulls/1/reviews", {"event": "APPROVE"}),
}


@pytest.mark.parametrize("call", list(LANDING))
def test_authentic_retry_after_hold_refuses_landing_then_expires(tmp_path, call):
    wire = Wire()
    client = store(tmp_path, wire, [("retry_after", 0, OPEN), ("core", 5000, 9000)])
    refused(LANDING[call](client), "retry_after")
    assert wire.sent == []
    client.clock = lambda: OPEN + 1
    admitted(LANDING[call](client))
    assert len(wire.sent) == 1


@pytest.mark.parametrize("call", list(LANDING))
@pytest.mark.parametrize("budgets", [[("secondary", 0, OPEN)], [("secondary", 0, OPEN), ("core", 0, OPEN)]])
def test_synthetic_hold_and_core_exhaustion_never_refuse_landing(tmp_path, call, budgets):
    wire = Wire()
    admitted(LANDING[call](store(tmp_path, wire, [*budgets, ("graphql", 0, OPEN)])))
    assert len(wire.sent) == 1


def test_primary_limit_hold_is_scoped_to_its_pool(tmp_path):
    wire = Wire()
    client = store(tmp_path, wire, [("retry_after:core", 0, OPEN)])
    refused(LANDING["rest"](client), "retry_after")
    admitted(LANDING["graphql"](client))
    assert wire.sent == [("http", "POST", "graphql")]


def test_refusal_precedence(tmp_path):
    rows = {"retry_after": (0, 1500), "secondary": (0, 1600), "core": (0, OPEN)}
    assert gh._refusal(rows, {"core"}, call_class="landing", now=NOW) == ("retry_after", 1500)
    assert gh._refusal(rows, {"core"}, call_class=None, now=NOW) == ("retry_after", 1500)
    del rows["retry_after"]
    assert gh._refusal(rows, {"core"}, call_class="landing", now=NOW) is None
    assert gh._refusal(rows, {"core"}, call_class=None, now=NOW) == ("secondary_hold", 1600)
    del rows["secondary"]
    assert gh._refusal(rows, {"core"}, call_class=None, now=NOW) == ("core_below_landing_reserve", OPEN)
    rows["graphql"] = (3, 1700)
    assert gh._refusal(rows, {"graphql"}, call_class=None, now=NOW) == ("pool_exhausted", 1700)
    assert gh._refusal({"retry_after": (0, EXPIRED)}, {"core"}, call_class="landing", now=NOW) is None


# --- how holds are created --------------------------------------------------------------------


def _limited_reply(status, headers, body=b'{"message":"You have exceeded a secondary rate limit."}'):
    replies = [gh.Response(status, headers, body)]
    return lambda method, endpoint, body: replies.pop(0) if replies else gh.Response(200, {}, b"{}")


def test_native_rate_limit_stderr_never_blocks_landing(tmp_path):
    """Root cause (b): gh stderr saying "rate limit" wrote a hold that landing calls honoured."""
    calls = []

    def native(argv):
        calls.append(argv)
        if len(calls) == 1:
            return subprocess.CompletedProcess(argv, 1, b"", b"HTTP 403: API rate limit exceeded")
        return subprocess.CompletedProcess(argv, 0, b"[]", b"")

    wire = Wire(native=native)
    client = store(tmp_path, wire)
    first = gh.run(["gh", "pr", "status"], client=client, capture_output=True)
    refused(first, "secondary_hold", NOW + 60)
    # Landing: native merge and the REST merge write both reach GitHub.
    assert (
        gh.run(["gh", "pr", "merge", "1", "--repo", "o/r", "--auto"], client=client, capture_output=True).returncode
        == 0
    )
    assert client.request("PUT", "repos/o/r/pulls/1/merge", payload={}).error is None
    # Non-landing calls keep the synthetic hold.
    refused(gh.run(["gh", "issue", "list"], client=client, capture_output=True), "secondary_hold", NOW + 60)
    refused(client.request("GET", "repos/o/r/issues/1/comments"), "secondary_hold", NOW + 60)
    assert wire.sent == [
        ("native", "pr", "status"),
        ("native", "pr", "merge", "1", "--repo", "o/r", "--auto"),
        ("http", "PUT", "repos/o/r/pulls/1/merge"),
    ]


@pytest.mark.parametrize(
    "retry_after",
    ["120", lambda: email.utils.formatdate(NOW + 120, usegmt=True)],
    ids=["delay-seconds", "http-date"],
)
def test_github_retry_after_creates_an_authentic_hold(tmp_path, retry_after):
    value = retry_after() if callable(retry_after) else retry_after
    wire = Wire(_limited_reply(403, {"Retry-After": value, "X-RateLimit-Remaining": "77", "X-RateLimit-Reset": "9000"}))
    client = store(tmp_path, wire)
    refused(client.request("POST", "repos/o/r/issues/1/comments", payload={"body": "x"}), "retry_after", NOW + 120)
    refused(LANDING["rest"](client), "retry_after", NOW + 120)
    refused(LANDING["native"](client), "retry_after", NOW + 120)
    assert len(wire.sent) == 1
    client.clock = lambda: NOW + 121
    admitted(LANDING["rest"](client))
    assert len(wire.sent) == 2


def test_primary_limit_403_with_github_reset_is_authentic_for_its_pool(tmp_path):
    headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(OPEN), "X-RateLimit-Resource": "core"}
    wire = Wire(_limited_reply(403, headers, b'{"message":"API rate limit exceeded"}'))
    client = store(tmp_path, wire)
    refused(client.request("GET", "repos/o/r/issues/1/timeline"), "retry_after")
    refused(LANDING["rest"](client), "retry_after")
    admitted(LANDING["graphql"](client))
    assert wire.sent == [("http", "GET", "repos/o/r/issues/1/timeline"), ("http", "POST", "graphql")]


@pytest.mark.parametrize(
    ("status", "headers"),
    [
        (403, {"X-RateLimit-Remaining": "50", "X-RateLimit-Reset": str(OPEN)}),
        (403, {}),
        (429, {}),
        (403, {"Retry-After": "soon"}),
    ],
    ids=["secondary-with-budget", "secondary-bare", "429-bare", "unparseable-retry-after"],
)
def test_limits_without_github_retry_after_are_synthetic(tmp_path, status, headers):
    wire = Wire(_limited_reply(status, headers))
    client = store(tmp_path, wire)
    first = client.request("POST", "repos/o/r/issues/1/comments", payload={"body": "x"})
    assert first.error == "github_rate_limited" and first.reason == "secondary_hold"
    for call in LANDING.values():
        admitted(call(client))
    assert len(wire.sent) == 1 + len(LANDING)
    second = client.request("GET", "repos/o/r/issues/1/comments")
    assert second.error == "github_rate_limited" and second.reason == "secondary_hold"
    assert len(wire.sent) == 1 + len(LANDING)


def test_graphql_rate_limited_body_is_a_typed_pool_refusal(tmp_path):
    reply = gh.Response(
        200,
        {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(OPEN)},
        json.dumps({"errors": [{"type": "RATE_LIMITED"}]}).encode(),
    )
    wire = Wire(lambda method, endpoint, body: reply)
    client = store(tmp_path, wire)
    refused(client.request("POST", "graphql", payload={"query": VIEWER}), "pool_exhausted")
    refused(client.request("POST", "graphql", payload={"query": "query { repository { id } }"}), "pool_exhausted")
    # The landing mutation still reaches GitHub; GitHub's own answer stays typed.
    assert LANDING["graphql"](client).reason == "pool_exhausted"
    assert len(wire.sent) == 2


# --- reads are never landing by URL -------------------------------------------------------------

READS = [
    ("GET", "repos/o/r/issues/1/timeline"),
    ("GET", "repos/o/r/issues/1/comments"),
    ("GET", "repos/o/r/issues/comments/1"),
    ("GET", "repos/o/r/pulls/1/reviews"),
    ("GET", "repos/o/r/pulls/1"),
    ("GET", "repos/o/r/commits/" + HEAD + "/check-runs"),
    ("GET", "repos/o/r/commits/" + HEAD + "/status"),
    ("GET", "repos/o/r/check-runs/1"),
    ("GET", "repos/o/r/actions/runs/1"),
    ("GET", "repos/o/r/actions/runs/1/jobs"),
    ("GET", "repos/o/r/actions/jobs/1"),
    ("GET", "repos/o/r/actions/runs?event=merge_group"),
    ("GET", "repos/o/r/pulls/1/merge"),
    ("POST", "repos/o/r/issues/1/comments"),
    ("POST", "repos/o/r/actions/runs/1/rerun"),
]


@pytest.mark.parametrize(("method", "endpoint"), READS)
def test_reads_and_other_calls_are_never_landing_by_url(tmp_path, method, endpoint):
    """Root cause (c): read shapes were classed as landing by URL and escaped the reserve."""
    wire = Wire()
    client = store(tmp_path, wire, [("core", 499, OPEN)])
    refused(
        client.request(method, endpoint, payload={"body": "x"} if method == "POST" else None),
        "core_below_landing_reserve",
    )
    refused(
        gh.run(["gh", "api", "--method", method, endpoint], client=client, capture_output=True),
        "core_below_landing_reserve",
    )
    assert wire.sent == []


@pytest.mark.parametrize(
    "query",
    [
        'query { repository(owner:"o", name:"r") { pullRequest(number:1) { isInMergeQueue isMergeQueueEnabled mergeQueueEntry { id } } } }',
        "query { enqueuePullRequest: viewer { login } }",
        'mutation { addComment(input: {subjectId: "X", body: "enqueuePullRequest"}) { clientMutationId } }',
        'mutation { enqueuePullRequest: addComment(input: {subjectId: "X", body: "x"}) { clientMutationId } }',
        ENQUEUE.replace("} }", '} addComment(input: {subjectId: "X", body: "x"}) { clientMutationId } }', 1),
        '# enqueuePullRequest\nmutation { addComment(input: {subjectId: "X", body: "x"}) { clientMutationId } }',
        "mutation { ...Landing } fragment Landing on Mutation { enqueuePullRequest(input: {}) { clientMutationId } }",
        "mutation A { enqueuePullRequest(input: {}) { clientMutationId } } mutation B { addComment(input: {}) { clientMutationId } }",
    ],
    ids=[
        "queue-read",
        "alias-query",
        "string-literal",
        "alias-mutation",
        "mixed-mutation",
        "comment",
        "root-spread",
        "two-operations",
    ],
)
def test_graphql_landing_needs_every_root_field_to_be_a_landing_mutation(tmp_path, query):
    wire = Wire()
    client = store(tmp_path, wire, [("graphql", 10, OPEN)])
    refused(client.request("POST", "graphql", payload={"query": query}), "pool_exhausted")
    assert wire.sent == []


@pytest.mark.parametrize(
    ("method", "endpoint", "payload"),
    [
        ("PUT", "repos/o/r/pulls/1/merge", {}),
        ("PUT", "repos/o/r/pulls/1/update-branch", {}),
        ("POST", "repos/o/r/pulls/1/reviews", {"event": "COMMENT"}),
        ("POST", "repos/o/r/pulls/1/reviews/7/events", {"event": "APPROVE"}),
        ("POST", "repos/o/r/actions/runs/1/rerun-failed-jobs", {}),
        ("POST", "repos/o/r/actions/jobs/1/rerun", {}),
        ("POST", "repos/o/r/check-runs/1/rerequest", {}),
        ("POST", "repos/o/r/statuses/" + HEAD, {"state": "success"}),
        ("POST", "graphql", {"query": ENQUEUE}),
        ("POST", "graphql", {"query": 'mutation { dequeuePullRequest(input: {id: "X"}) { clientMutationId } }'}),
        (
            "POST",
            "graphql",
            {
                "query": "mutation($i:EnablePullRequestAutoMergeInput!){enablePullRequestAutoMerge(input:$i){clientMutationId}}"
            },
        ),
        (
            "POST",
            "graphql",
            {"query": 'mutation { disablePullRequestAutoMerge(input: {pullRequestId: "X"}) { clientMutationId } }'},
        ),
        (
            "POST",
            "graphql",
            {"query": 'mutation { a: mergePullRequest(input: {pullRequestId: "X"}) { clientMutationId } }'},
        ),
    ],
)
def test_every_landing_verb_proceeds_at_zero(tmp_path, method, endpoint, payload):
    wire = Wire()
    client = store(tmp_path, wire, [("core", 0, OPEN), ("graphql", 0, OPEN), ("secondary", 0, OPEN)])
    assert client.request(method, endpoint, payload=payload).error is None
    assert wire.sent == [("http", method, endpoint)]


@pytest.mark.parametrize(
    "argv",
    [
        ["pr", "merge", "1", "--repo", "o/r", "--auto"],
        ["pr", "merge", "1", "--repo", "o/r", "--disable-auto", "--admin"],
        ["pr", "review", "1", "--repo", "o/r", "--comment", "-b", "x", "--unknown"],
        ["run", "rerun", "5", "--repo", "o/r", "--failed", "--debug"],
        ["run", "rerun", "--job", "6", "--repo", "o/r", "--debug"],
        ["pr", "checks", "1", "--repo", "o/r", "--json", "name,bucket,state,workflow"],
    ],
)
def test_native_landing_verbs_and_ci_status_proceed_at_zero(tmp_path, argv):
    wire = Wire()
    client = store(tmp_path, wire, [("core", 0, OPEN), ("graphql", 0, OPEN), ("secondary", 0, OPEN)])
    assert gh.run(["gh", *argv], client=client, capture_output=True).returncode == 0
    assert wire.sent == [("native", *argv)]


def test_full_run_rerun_is_not_landing(tmp_path):
    wire = Wire()
    client = store(tmp_path, wire, [("core", 0, OPEN)])
    refused(
        gh.run(["gh", "run", "rerun", "5", "--repo", "o/r", "--debug"], client=client, capture_output=True),
        "core_below_landing_reserve",
    )
    assert wire.sent == []


def test_ci_status_view_reads_proceed_but_a_plain_view_does_not(tmp_path):
    def reply(method, endpoint, body):
        if endpoint == "repos/o/r/pulls/1":
            return gh.Response(200, {}, json.dumps({"number": 1, "head": {"sha": HEAD}, "base": {}}).encode())
        if endpoint.endswith("/check-runs?per_page=100"):
            return gh.Response(200, {}, b'{"total_count":0,"check_runs":[]}')
        return gh.Response(200, {}, b'{"total_count":0,"statuses":[]}')

    wire = Wire(reply)
    client = store(tmp_path, wire, [("core", 0, OPEN)])
    view = ["gh", "pr", "view", "1", "--repo", "o/r", "--json", "headRefOid,statusCheckRollup"]
    assert gh.run(view, client=client, capture_output=True).returncode == 0
    assert [call[2].split("?")[0] for call in wire.sent] == [
        "repos/o/r/pulls/1",
        f"repos/o/r/commits/{HEAD}/check-runs",
        f"repos/o/r/commits/{HEAD}/status",
    ]
    refused(
        gh.run(["gh", "pr", "view", "1", "--repo", "o/r", "--json", "headRefOid"], client=client, capture_output=True),
        "core_below_landing_reserve",
    )
    assert len(wire.sent) == 3


# --- exempt calls --------------------------------------------------------------------------------


def test_rate_limit_read_is_exempt(tmp_path):
    reply = json.dumps({"resources": {"core": {"remaining": 0, "reset": OPEN}}}).encode()
    wire = Wire(lambda method, endpoint, body: gh.Response(200, {}, reply))
    client = store(tmp_path, wire, [("core", 0, OPEN), ("secondary", 0, OPEN)])
    assert client.request("GET", "rate_limit").error is None
    assert gh.run(["gh", "api", "rate_limit"], client=client, capture_output=True).returncode == 0
    assert len(wire.sent) == 2


@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("POST", "https://api.github.com/app/installations/1/access_tokens"),
        ("DELETE", "https://api.github.com/installation/token"),
    ],
)
def test_token_lifecycle_is_exempt_through_http_open(monkeypatch, method, url):
    from urllib.request import Request

    reset = int(time.time()) + 3600
    seeded = gh.GitHubClient(env={"GH_TOKEN": "Bearer synthetic-jwt"})
    with seeded._db() as db:
        gh._store_budget(db, seeded.scope, "core", 0, reset)
        gh._store_budget(db, seeded.scope, "secondary", 0, reset)
    opened = []

    def opener(request, **kwargs):
        import io

        opened.append(request.full_url)
        result = io.BytesIO(b'{"token":"synthetic"}')
        result.status, result.headers = 201, {}
        return result

    request = Request(
        url, data=b"{}" if method == "POST" else None, method=method, headers={"Authorization": "Bearer synthetic-jwt"}
    )
    with gh.http_open(request, opener=opener) as response:
        assert response.status == 201
    assert opened == [url]
    with pytest.raises(gh.GitHubRateLimited) as limited:
        gh.http_open(
            Request("https://api.github.com/repos/o/r/issues/1", headers={"Authorization": "Bearer synthetic-jwt"}),
            opener=opener,
        )
    assert limited.value.reason == "secondary_hold" and limited.value.reset_at == reset
    assert opened == [url]


# --- vetted landing entry points -----------------------------------------------------------------


def _pr_view(client):
    return gh.run(
        ["gh", "pr", "view", "1", "--repo", "o/r", "--json", "headRefOid"],
        client=client,
        capture_output=True,
        text=True,
    )


def _pull_reply(method, endpoint, body):
    return gh.Response(200, {}, json.dumps({"number": 1, "head": {"sha": HEAD}, "base": {}}).encode())


def test_verdict_publication_entry_point_is_landing_only_while_it_runs(tmp_path, monkeypatch):
    from scripts.fleet_comms import review_publisher

    wire = Wire(_pull_reply)
    client = store(tmp_path, wire, [("core", 0, OPEN), ("secondary", 0, OPEN)])
    monkeypatch.setattr(gh, "GitHubClient", lambda **kwargs: client)
    assert review_publisher.fetch_pr_head_sha(repository="o/r", pr_number=1) == HEAD
    assert wire.sent == [("http", "GET", "repos/o/r/pulls/1")]
    # The declaration ended with the call: the same read outside it is refused.
    refused(_pr_view(client), "secondary_hold")
    assert len(wire.sent) == 1


def test_merge_queue_keeper_entry_point_is_landing(tmp_path):
    wire = Wire(_pull_reply)
    client = store(tmp_path, wire, [("core", 0, OPEN)])
    assert _in_keeper_run(_pr_view)(client).returncode == 0
    refused(_pr_view(client), "core_below_landing_reserve")
    assert len(wire.sent) == 1


def test_lookalike_entry_points_never_exempt(tmp_path):
    """Same function names, other files: neither the name nor a path suffix is the vetting."""
    wire = Wire()
    client = store(tmp_path, wire, [("core", 0, OPEN)])
    for path, name in [*gh._LANDING_ENTRY_POINTS, ("scripts/publish/github.py", "publish")]:
        for filename in (str(tmp_path / path), path, "<string>"):
            namespace = {"call": _pr_view, "client": client}
            exec(compile(f"def {name}():\n    return call(client)\n", filename, "exec"), namespace)
            refused(namespace[name](), "core_below_landing_reserve")
    assert wire.sent == []


def test_caller_tags_flags_headers_and_environment_never_exempt(tmp_path, monkeypatch):
    tags = {
        "LU_GITHUB_LANDING": "1",
        "LU_GITHUB_OPERATION": "pr-merge",
        "GITHUB_LANDING_FLOW": "merge-queue-keeper",
        "LANDING_FLOW": "verdict-publication",
        "AGENT_GH_LANDING": "ci-status",
    }
    for key, value in tags.items():
        monkeypatch.setenv(key, value)
    wire = Wire()
    client = store(tmp_path, wire, [("core", 0, OPEN)], env=tags)
    headers = {"X-Landing-Flow": "merge-queue-keeper", "X-GitHub-Operation": "pr-merge", "X-Caller": "publish"}
    refused(client.request("GET", "repos/o/r/pulls/1/reviews", headers=headers), "core_below_landing_reserve")
    for argv in (
        ["api", "repos/o/r/pulls/1/reviews", "-H", "X-Landing-Flow: merge-queue-keeper"],
        ["api", "repos/o/r/pulls/1/reviews", "--template", "{{.}}", "-H", "X-Operation: pr-merge"],
        ["pr", "view", "1", "--repo", "o/r", "--json", "headRefOid", "--jq", ".landing"],
        ["issue", "comment", "1", "--repo", "o/r", "--body", "pr merge --failed"],
        ["run", "view", "1", "--repo", "o/r", "--json", "databaseId"],
    ):
        refused(gh.run(["gh", *argv], client=client, capture_output=True), "core_below_landing_reserve")

    @gh.rate_limited_command
    def publish(verb, **kwargs):
        return client.request("GET", "repos/o/r/pulls/1/reviews")

    refused(publish("pr-merge"), "core_below_landing_reserve")
    assert wire.sent == []


def test_frozen_landing_entry_points_exist_and_nothing_else_declares_them():
    assert gh._LANDING_ENTRY_POINTS == {
        ("scripts/orchestration/merge_queue_keeper.py", "run"): "merge-queue-keeper",
        ("scripts/fleet_comms/review_publisher.py", "fetch_pr_head_sha"): "verdict-publication",
        ("scripts/fleet_comms/review_publisher.py", "execute_publication"): "verdict-publication",
        ("scripts/fleet_comms/review_publisher.py", "publish_sealed_verdict"): "verdict-publication",
        ("scripts/review/record_cf_verdict.py", "record"): "verdict-publication",
    }
    assert gh._PUBLISHER_ENTRY_POINT == ("scripts/publish/github.py", "publish")
    assert {
        "pr-merge",
        "pr-update-branch",
        "pr-review",
        "run-rerun",
        "commit-status",
        "pr-dequeue",
        "pr-disarm",
    } == gh._PUBLISHER_LANDING_VERBS
    for path, name in [*gh._LANDING_ENTRY_POINTS, gh._PUBLISHER_ENTRY_POINT]:
        tree = ast.parse((ROOT / path).read_text())
        assert name in {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}, (path, name)
    # Only this module opens a landing operation, and only at these vetted sites.
    openers = []

    class Openers(ast.NodeVisitor):
        def __init__(self):
            self.scope = []

        def visit_FunctionDef(self, node):
            self.scope.append(node.name)
            self.generic_visit(node)
            self.scope.pop()

        def visit_Call(self, node):
            if getattr(node.func, "id", None) == "_landing_operation":
                openers.append(".".join(self.scope))
            self.generic_visit(node)

    Openers().visit(ast.parse((ROOT / "scripts/common/github_client.py").read_text()))
    assert sorted(openers) == ["queue_read", "rate_limited_command.wrapped", "rest_read", "run"]


def test_no_caller_outside_the_client_can_open_a_landing_operation(tmp_path):
    wire = Wire()
    client = store(tmp_path, wire, [("core", 0, OPEN)])
    with pytest.raises(PermissionError, match="only inside the GitHub client"):
        with gh._landing_operation("merge-queue-keeper"):
            client.request("GET", "repos/o/r/pulls/1/reviews")
    assert gh._LANDING_FLOW.get() is None and wire.sent == []


# --- publisher: a landing verb is one landing operation -------------------------------------------


@pytest.fixture
def publisher(tmp_path, monkeypatch, synthetic_opsec):
    from scripts.publish import github as pub

    monkeypatch.setattr(pub.gate, "catalog", lambda: CATALOG)
    monkeypatch.setattr(pub.gate, "real_gh", lambda env: "gh")
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)

    def reply(method, endpoint, body):
        if endpoint == "repos/unit/public/pulls/1":
            return gh.Response(
                200, {}, json.dumps({"number": 1, "draft": False, "head": {"sha": HEAD}, "base": {}}).encode()
            )
        pull = {
            "headRefOid": HEAD,
            "isMergeQueueEnabled": False,
            "viewerMergeHeadlineText": "clean (#1)",
            "viewerMergeBodyText": "* clean",
        }
        return gh.Response(200, {}, json.dumps({"data": {"repository": {"pullRequest": pull}}}).encode())

    def install(budgets):
        wire = Wire(reply)
        client = store(tmp_path / "cache", wire, budgets)
        monkeypatch.setattr(gh, "GitHubClient", lambda **kwargs: client)
        return pub, wire

    return install


def test_publisher_merge_proceeds_at_zero_with_every_readiness_read(publisher):
    pub, wire = publisher([("core", 0, OPEN), ("graphql", 0, OPEN), ("secondary", 0, OPEN)])
    result = pub.publish(
        "pr-merge",
        repo="unit/public",
        number=1,
        subject="clean",
        body="clean",
        env={"PATH": os.defpath},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert wire.sent[:3] == [
        ("http", "GET", "repos/unit/public/pulls/1"),
        ("native", "pr", "checks", "1", "--json", "name,bucket,state,workflow", "--repo", "unit/public"),
        ("http", "POST", "graphql"),
    ]
    assert wire.sent[3][:4] == ("native", "pr", "merge", "1") and len(wire.sent) == 4
    # The operation ended with the verb: a non-landing verb is refused with its typed reason.
    refused(
        pub.publish(
            "issue-comment",
            repo="unit/public",
            number=1,
            body="clean",
            env={"PATH": os.defpath},
            capture_output=True,
            text=True,
        ),
        "secondary_hold",
    )
    assert len(wire.sent) == 4


def test_publisher_merge_honours_only_an_authentic_hold_with_its_reason(publisher):
    pub, wire = publisher([("retry_after", 0, OPEN), ("core", 0, OPEN)])
    result = pub.publish(
        "pr-merge",
        repo="unit/public",
        number=1,
        subject="clean",
        body="clean",
        env={"PATH": os.defpath},
        capture_output=True,
        text=True,
    )
    refused(result, "retry_after")
    assert wire.sent == []


# --- typed reason propagation: REST, native and injected paths -------------------------------------


def _rest_client(tmp_path, budgets):
    """In-process REST transport (``gh api --include`` through an injected runner)."""
    sent = []

    def runner(command, **kwargs):
        sent.append(command)
        return subprocess.CompletedProcess(command, 0, b"HTTP/2 200\r\n\r\n{}", b"")

    client = gh.GitHubClient(cache_dir=tmp_path, runner=runner, clock=lambda: NOW, env={})
    with client._db() as db:
        for row in budgets:
            gh._store_budget(db, client.scope, *row)
    return client, sent


@pytest.mark.parametrize(
    ("budgets", "reason"),
    [
        ([("retry_after", 0, OPEN)], "retry_after"),
        ([("secondary", 0, OPEN)], "secondary_hold"),
        ([("core", 499, OPEN)], "core_below_landing_reserve"),
        ([("graphql", 10, OPEN), ("core", 0, EXPIRED)], "pool_exhausted"),
    ],
)
@pytest.mark.parametrize("path", ["rest", "injected", "native"])
def test_typed_reason_and_exit_75_on_every_path(tmp_path, budgets, reason, path):
    argv = ["gh", "api", "graphql", "-f", "query=" + VIEWER] if reason == "pool_exhausted" else ["gh", "api", "user"]
    if path == "rest":
        client, sent = _rest_client(tmp_path, budgets)
    else:
        wire = Wire()
        client, sent = store(tmp_path, wire, budgets), wire.sent
        if path == "native":
            argv = [*argv, "--template", "{{.}}"]
    result = gh.run(argv, client=client, capture_output=True, text=True)
    refused(result, reason)
    assert json.loads(result.stderr)["reason"] == reason
    with pytest.raises(subprocess.CalledProcessError) as raised:
        gh.run(argv, client=client, capture_output=True, check=True)
    assert raised.value.returncode == 75 and raised.value.github_result.reason == reason
    with pytest.raises(gh.GitHubRateLimited) as fresh:
        result.github_result.require_fresh()
    assert fresh.value.reason == reason
    assert sent == []


def test_adapters_keep_the_reason(tmp_path, monkeypatch, capsys):
    wire = Wire()
    client = store(tmp_path, wire, [("core", 0, OPEN)])
    monkeypatch.setattr(gh, "GitHubClient", lambda **kwargs: client)
    states = gh.rest_read("issue-states", "o/r", {"numbers": [1]}, capture_output=True, text=True)
    refused(states, "core_below_landing_reserve")

    # Existing adapters re-raise from an observation with its reset only; the reason survives.
    observation = gh.run(["gh", "api", "user"], client=client, capture_output=True).github_result
    reraised = gh.GitHubRateLimited(observation.reset_at)
    assert reraised.reason == "core_below_landing_reserve"

    @gh.timer
    def scheduled():
        raise gh.GitHubRateLimited(observation.reset_at)

    assert scheduled() == 0
    assert "reason=core_below_landing_reserve" in capsys.readouterr().out
    assert wire.sent == []


def test_landing_flow_adapters_admit_at_zero(tmp_path, monkeypatch):
    def reply(method, endpoint, body):
        if endpoint == "graphql":
            data = {"repository": {"pullRequest": {"isInMergeQueue": False}}}
            return gh.Response(200, {}, json.dumps({"data": data}).encode())
        return gh.Response(
            200,
            {},
            json.dumps({"number": 1, "state": "open", "head": {"sha": HEAD}, "base": {}, "merged_at": None}).encode(),
        )

    wire = Wire(reply)
    client = store(tmp_path, wire, [("core", 0, OPEN), ("graphql", 0, OPEN), ("secondary", 0, OPEN)])
    monkeypatch.setattr(gh, "GitHubClient", lambda **kwargs: client)
    status = gh.queue_read("queue-status", "o/r", {"number": 1, "branch": "main"}, capture_output=True, text=True)
    assert status.returncode == 0
    facts = gh.rest_read("merge-facts", "o/r", {"batch": [["o/r", 1]]}, capture_output=True, text=True)
    assert facts.returncode == 0
    assert [call[1:] for call in wire.sent] == [
        ("GET", "repos/o/r/pulls/1"),
        ("POST", "graphql"),
        ("GET", "repos/o/r/pulls/1"),
    ]


def test_every_refusal_reason_is_from_the_closed_set():
    assert gh.REFUSAL_REASONS == REASONS
    assert gh.LANDING_RESERVE == 500 and gh.RESERVE == 10
    # Every typed result goes through one constructor, which admits only the closed set.
    for reason in REASONS:
        assert gh._limited(reason, OPEN).reason == reason
    for untyped in (None, "", "github_rate_limited", "landing"):
        with pytest.raises(AssertionError, match="untyped"):
            gh._limited(untyped, OPEN)
