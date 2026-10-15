"""Landing-first budget guard and the optional per-caller soft cap (#10730, #10660). No network."""

from __future__ import annotations

import json

import pytest

from scripts.common import github_budget_counters as counters
from scripts.common import github_client as gh

NOW = 10 * 3600 + 120
RESET = NOW + 1800
NON_LANDING = ("GET", "repos/o/r/issues")
LANDING = ("PUT", "repos/o/r/pulls/7/merge")


def ok():
    return gh.Response(200, {"X-RateLimit-Remaining": "5000", "X-RateLimit-Reset": str(RESET)}, b"{}")


def make(tmp_path, *, caller="drv", now=NOW, env=None):
    calls = []

    def transport(method, endpoint, headers, body, timeout):
        calls.append((method, endpoint))
        return ok()

    return gh.GitHubClient(
        cache_dir=tmp_path, transport=transport, clock=lambda: now, env=env or {}, caller=caller
    ), calls


def seed(client, remaining, *, resource="core", reset=RESET):
    with client._db() as db:
        gh._store_budget(db, client.scope, resource, remaining, reset)


def count(tmp_path):
    """Requests counted this hour, every pool, as the Ops API report serves them."""
    pools = counters.report_for(tmp_path, NOW, limit=50)["windows"]["current"]["resources"]
    return sum(row["count"] for rows in pools.values() for row in rows)


@pytest.mark.parametrize(("remaining", "non_landing_refused"), [(499, True), (500, False), (501, False), (11, True)])
def test_boundary_at_the_500_reserve(tmp_path, remaining, non_landing_refused):
    client, calls = make(tmp_path)
    seed(client, remaining)
    if non_landing_refused:
        with pytest.raises(gh.GitHubBudgetRefused) as refusal:
            client.request(*NON_LANDING)
        assert refusal.value.reason == counters.REASON_CORE_RESERVE and refusal.value.reset_at == RESET
        assert calls == []
    else:
        assert client.request(*NON_LANDING).status == 200
        assert len(calls) == 1
    # A landing call proceeds at every level.
    assert client.request(*LANDING).status == 200


@pytest.mark.parametrize("remaining", [499, 500, 501])
def test_landing_proceeds_on_both_sides_of_the_boundary(tmp_path, remaining):
    client, calls = make(tmp_path)
    seed(client, remaining)
    assert client.request(*LANDING).status == 200
    assert calls == [LANDING]


def test_unknown_budget_never_refuses(tmp_path):
    client, calls = make(tmp_path)
    assert client.request(*NON_LANDING).status == 200
    other, _ = make(tmp_path, env={"GH_TOKEN": "another-scope"})
    seed(other, 3)  # another credential's pool says nothing about this one
    assert client.request(*NON_LANDING).status == 200
    assert len(calls) == 2


def test_an_expired_window_is_an_unknown_budget(tmp_path):
    client, _ = make(tmp_path)
    seed(client, 3, reset=NOW)  # reset == now: the window has rolled over
    assert client.request(*NON_LANDING).status == 200


def test_a_refused_call_is_typed_value_free_and_counts_nothing(tmp_path):
    client, calls = make(tmp_path, caller="orphan-triage")
    seed(client, 77)
    with pytest.raises(gh.GitHubRateLimited) as refusal:  # existing handlers already catch this base
        client.request("POST", "repos/secret-owner/secret-repo/issues/9/labels", payload={"labels": ["private-body"]})
    exc = refusal.value
    assert isinstance(exc, gh.GitHubBudgetRefused) and exc.code == "github_budget_refused"
    assert "secret" not in str(exc) and "private" not in str(exc)
    assert str(exc) == f"github_budget_refused reason=core_below_landing_reserve reset_at={RESET}"
    assert calls == [] and count(tmp_path) == 0


def test_the_guard_never_sleeps_or_retries(tmp_path, monkeypatch):
    import time

    monkeypatch.setattr(time, "sleep", lambda *_: pytest.fail("the client must not sleep"))
    client, calls = make(tmp_path)
    seed(client, 100)
    with pytest.raises(gh.GitHubBudgetRefused):
        client.request(*NON_LANDING)
    assert calls == []


def test_only_the_core_pool_is_guarded(tmp_path):
    client, calls = make(tmp_path)
    seed(client, 0)
    assert client.request("POST", "graphql", payload={"query": "query { viewer { login } }"}).status == 200
    assert client.request("GET", "search/issues?q=x").status == 200
    assert len(calls) == 2


@pytest.mark.parametrize(
    ("method", "path", "query", "landing"),
    [
        ("PUT", "repos/o/r/pulls/7/merge", None, True),
        ("POST", "repos/o/r/pulls/7/reviews", None, True),
        ("GET", "repos/o/r/pulls/7/reviews", None, True),
        ("PUT", "repos/o/r/pulls/7/update-branch", None, True),
        ("GET", "repos/o/r/commits/abc123/check-runs", None, True),
        ("GET", "repos/o/r/commits/abc123/status", None, True),
        ("GET", "repos/o/r/commits/abc123/statuses", None, True),
        ("GET", "repos/o/r/actions/runs/55", None, True),
        ("GET", "repos/o/r/actions/runs/55/jobs", None, True),
        ("POST", "repos/o/r/actions/runs/55/rerun-failed-jobs", None, True),
        ("POST", "repos/o/r/actions/jobs/66/rerun", None, True),
        # verdict publication, its readback and the commit status line (F1)
        ("POST", "repos/o/r/issues/7/comments", None, True),
        ("GET", "repos/o/r/issues/7/comments", None, True),
        ("GET", "repos/o/r/issues/comments/9", None, True),
        ("GET", "repos/o/r/issues/7/timeline", None, True),
        ("POST", "repos/o/r/statuses/0123abc", None, True),
        ("GET", "rate_limit", None, True),
        ("POST", "app/installations/12/access_tokens", None, True),
        ("DELETE", "installation/token", None, True),
        (
            "POST",
            "graphql",
            "mutation($i:EnqueuePullRequestInput!){enqueuePullRequest(input:$i){clientMutationId}}",
            True,
        ),
        ("POST", "graphql", "mutation{ enablePullRequestAutoMerge(input:{}){clientMutationId} }", True),
        ("POST", "graphql", 'query{repository(owner:"o",name:"r"){mergeQueue(branch:"main"){url}}}', True),
        # not landing: wrong verb, a full rerun, bulk reads, writes unrelated to landing, unknown shapes
        ("DELETE", "repos/o/r/pulls/7/merge", None, False),
        ("POST", "repos/o/r/actions/runs/55/rerun", None, False),
        ("GET", "repos/o/r/actions/runs", None, False),
        ("GET", "repos/o/r/pulls", None, False),
        # A plain pull-request read is not landing; CI status reads of it are (``ci-status``).
        ("GET", "repos/o/r/pulls/7", None, False),
        ("GET", "repos/o/r/issues", None, False),
        ("PATCH", "repos/o/r/issues/comments/9", None, False),
        ("DELETE", "repos/o/r/issues/comments/9", None, False),
        ("POST", "repos/o/r/issues/7/labels", None, False),
        ("GET", "repos/o/r/issues/7/events", None, False),
        ("POST", "repos/o/r/commits/abc123/comments", None, False),
        ("GET", "repos/o/r/statuses/abc123", None, False),
        ("PATCH", "repos/o/r/issues/7", None, False),
        ("GET", "repos/o/r/pulls/7/files", None, False),
        ("GET", "search/issues", None, False),
        ("POST", "graphql", "query{viewer{login}}", False),
        ("POST", "graphql", None, False),
        ("GET", None, None, False),
        ("GET", "repos/o/r/pulls/7/merge/extra", None, False),
    ],
)
def test_landing_allowlist(method, path, query, landing):
    assert counters.is_landing(method, path, query) is landing


def test_named_publisher_operations_are_landing_only_inside_their_scope():
    assert not counters.is_landing("GET", "repos/o/r/pulls")
    with counters.operation("queue-snapshot"):
        assert counters.is_landing("GET", "repos/o/r/pulls")
    with counters.operation("pr-bases"):
        assert not counters.is_landing("GET", "repos/o/r/pulls")
    assert not counters.is_landing("GET", "repos/o/r/pulls")


def test_a_named_read_inside_a_landing_verb_stays_landing():
    with counters.operation("pr-merge"):
        with counters.operation("pr-bases"):
            assert counters.is_landing("GET", "repos/o/r/pulls/7")
        assert counters.native_is_landing(["gh", "pr", "view", "7", "--json", "headRefOid"])
    assert not counters.is_landing("GET", "repos/o/r/pulls/7")


@pytest.mark.parametrize(
    ("args", "landing"),
    [
        (["gh", "pr", "merge", "7"], True),
        (["gh", "pr", "review", "7", "--approve"], True),
        (["gh", "pr", "checks", "7"], True),
        (["gh", "pr", "view", "7", "--json", "statusCheckRollup"], True),
        (["gh", "pr", "view", "7", "--json", "headRefOid"], False),
        (["gh", "run", "view", "55"], True),
        (["gh", "run", "rerun", "55", "--failed"], True),
        (["gh", "run", "rerun", "55"], False),
        (["gh", "issue", "comment", "7"], False),
        (["gh", "repo", "view"], False),
    ],
)
def test_native_landing_allowlist(args, landing):
    assert counters.native_is_landing(args) is landing


def test_native_api_shapes_are_classified_by_endpoint_and_method():
    assert gh._native_landing(["gh", "api", "--method", "PUT", "repos/o/r/pulls/7/merge"], "github.com")
    assert gh._native_landing(["gh", "api", "repos/o/r/commits/abc/check-runs"], "github.com")
    assert gh._native_landing(
        ["gh", "api", "graphql", "-f", "query=mutation{enqueuePullRequest(input:{}){x}}"], "github.com"
    )
    assert not gh._native_landing(["gh", "api", "repos/o/r/issues"], "github.com")
    assert not gh._native_landing(["gh", "api", "graphql", "-f", "query=query{viewer{login}}"], "github.com")


def test_run_returns_the_refusal_as_a_retryable_typed_result(tmp_path):
    client, calls = make(tmp_path)
    seed(client, 12)
    result = gh.run(["gh", "api", "repos/o/r/issues"], client=client, capture_output=True, text=True)
    assert result.returncode == 75 and calls == []
    assert result.github_result.error == "github_budget_refused"
    assert result.github_result.reason == counters.REASON_CORE_RESERVE
    assert json.loads(result.stderr) == {
        "error": "github_budget_refused",
        "reset_at": RESET,
        "reason": "core_below_landing_reserve",
    }
    landing = gh.run(["gh", "api", "--method", "PUT", "repos/o/r/pulls/7/merge"], client=client, capture_output=True)
    assert landing.returncode == 0 and calls == [LANDING]


def test_check_true_raises_a_called_process_error_the_timer_skips(tmp_path, capsys):
    client, _ = make(tmp_path)
    seed(client, 12)

    @gh.timer
    def job():
        return gh.run(["gh", "api", "repos/o/r/issues"], client=client, capture_output=True, check=True)

    assert job() == 0
    assert "skipped github_budget_refused" in capsys.readouterr().out


def test_native_fall_through_is_guarded_and_counted(tmp_path):
    client, _ = make(tmp_path)
    seed(client, 12)
    native = []

    def runner(command, **kwargs):
        native.append(command)
        return gh.subprocess.CompletedProcess(command, 0, b"{}", b"")

    shape = ["gh", "api", "--paginate", "--jq", ".x", "repos/o/r/issues"]  # keeps the native command
    with pytest.raises(gh.GitHubBudgetRefused):
        gh._run_command(shape, client=client, runner=runner, capture_output=True)
    assert native == [] and count(tmp_path) == 0
    seed(client, 900, reset=RESET + 1)
    gh._run_command(shape, client=client, runner=runner, capture_output=True)
    assert len(native) == 1 and count(tmp_path) == 1
    seed(client, 12, reset=RESET + 2)
    landing = ["gh", "api", "--paginate", "--jq", ".x", "repos/o/r/pulls/7/reviews"]  # native, and a landing read
    gh._run_command(landing, client=client, runner=runner, capture_output=True)
    assert len(native) == 2 and count(tmp_path) == 2


def write_caps(tmp_path, document):
    path = tmp_path / counters.SOFT_CAP_FILE
    path.write_text(json.dumps(document) if not isinstance(document, str) else document)
    return path


def test_soft_cap_ships_disabled(tmp_path):
    assert counters.load_soft_caps(tmp_path) == {}
    client, calls = make(tmp_path, caller="greedy")
    for _ in range(5):
        client.request(*NON_LANDING)
    assert len(calls) == 5


def test_soft_cap_refuses_only_the_capped_caller_when_enabled(tmp_path):
    write_caps(tmp_path, {"enabled": True, "hourly_caps": {"greedy": {"core": 2}}})
    greedy, greedy_calls = make(tmp_path, caller="greedy")
    polite, polite_calls = make(tmp_path, caller="polite")
    greedy.request(*NON_LANDING)
    greedy.request(*NON_LANDING)
    with pytest.raises(gh.GitHubBudgetRefused) as refusal:
        greedy.request(*NON_LANDING)
    assert refusal.value.reason == counters.REASON_SOFT_CAP and refusal.value.reset_at == 10 * 3600 + 3600
    for _ in range(5):
        polite.request(*NON_LANDING)
    assert len(greedy_calls) == 2 and len(polite_calls) == 5
    # Landing is never capped; another pool without a cap is untouched.
    assert greedy.request(*LANDING).status == 200
    assert greedy.request("GET", "search/issues?q=x").status == 200


def test_soft_cap_resets_with_the_hour(tmp_path):
    write_caps(tmp_path, {"enabled": True, "hourly_caps": {"greedy": {"core": 1}}})
    first, _ = make(tmp_path, caller="greedy")
    first.request(*NON_LANDING)
    with pytest.raises(gh.GitHubBudgetRefused):
        first.request(*NON_LANDING)
    next_hour, _ = make(tmp_path, caller="greedy", now=NOW + 3600)
    assert next_hour.request(*NON_LANDING).status == 200


@pytest.mark.parametrize(
    "document",
    [
        {"enabled": False, "hourly_caps": {"greedy": {"core": 0}}},
        {"hourly_caps": {"greedy": {"core": 0}}},
        {"enabled": "yes", "hourly_caps": {"greedy": {"core": 0}}},
        {"enabled": True, "hourly_caps": {"greedy": {"core": -1}}},
        {"enabled": True, "hourly_caps": {"greedy": {"core": "2"}}},
        {"enabled": True, "hourly_caps": {"Bad Caller": {"core": 0}}},
        {"enabled": True, "hourly_caps": ["greedy"]},
        "not json",
        [],
    ],
)
def test_a_disabled_or_malformed_soft_cap_file_caps_nobody(tmp_path, document):
    write_caps(tmp_path, document)
    assert counters.load_soft_caps(tmp_path) == {}
    client, calls = make(tmp_path, caller="greedy")
    for _ in range(3):
        client.request(*NON_LANDING)
    assert len(calls) == 3


def test_soft_cap_file_is_reread_when_it_changes(tmp_path):
    path = write_caps(tmp_path, {"enabled": True, "hourly_caps": {"greedy": {"core": 1}}})
    assert counters.load_soft_caps(tmp_path) == {"greedy": {"core": 1}}
    path.write_text(json.dumps({"enabled": True, "hourly_caps": {"greedy": {"core": 100, "graphql": 5}}}))
    assert counters.load_soft_caps(tmp_path) == {"greedy": {"core": 100, "graphql": 5}}
    path.unlink()
    assert counters.load_soft_caps(tmp_path) == {}


def test_soft_cap_path_can_be_overridden_by_environment(tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text(json.dumps({"enabled": True, "hourly_caps": {"greedy": {"core": 4}}}))
    monkeypatch.setenv(counters.SOFT_CAP_ENV, str(elsewhere))
    assert counters.load_soft_caps(tmp_path / "unrelated") == {"greedy": {"core": 4}}


def test_simulated_exhaustion_names_the_top_three_callers(tmp_path):
    # Real traffic from five callers; the last response says the pool is nearly gone (77 left).
    plan = {"orphan-triage": 9, "issue-audit": 7, "workflow-reads": 5, "keeper": 3, "review-trigger": 1}
    remaining = {"left": 5000}

    def transport(method, endpoint, headers, body, timeout):
        remaining["left"] -= 1
        return gh.Response(
            200, {"X-RateLimit-Remaining": str(remaining["left"]), "X-RateLimit-Reset": str(RESET)}, b"{}"
        )

    order = [name for name, n in plan.items() for _ in range(n)]
    for index, name in enumerate(order):
        client = gh.GitHubClient(cache_dir=tmp_path, transport=transport, clock=lambda: NOW, env={}, caller=name)
        if index == len(order) - 1:
            remaining["left"] = 78
        client.request(*NON_LANDING)
    report = counters.report_for(tmp_path, NOW, limit=3)
    assert report["budget"]["core"]["remaining"] == 77
    assert report["windows"]["current"]["resources"]["core"] == [
        {"caller": "orphan-triage", "count": 9},
        {"caller": "issue-audit", "count": 7},
        {"caller": "workflow-reads", "count": 5},
    ]
    # And from here only landing calls get through.
    late, calls = make(tmp_path, caller="orphan-triage")
    with pytest.raises(gh.GitHubBudgetRefused):
        late.request(*NON_LANDING)
    assert late.request(*LANDING).status == 200 and calls == [LANDING]


REAL_CLIENT = gh.GitHubClient


def route_client_builder(tmp_path, monkeypatch, answers):
    """Make the publisher-facing read helpers build their client on a fake transport in ``tmp_path``."""
    calls = []

    def transport(method, endpoint, headers, body, timeout):
        calls.append((method, endpoint))
        return answers(method, endpoint)

    def build(**kwargs):
        return REAL_CLIENT(cache_dir=tmp_path, transport=transport, clock=lambda: NOW, **kwargs)

    monkeypatch.setattr(gh, "GitHubClient", build)
    return calls


def test_rest_read_tags_the_caller_and_lets_landing_operations_through(tmp_path, monkeypatch):
    calls = route_client_builder(tmp_path, monkeypatch, lambda m, e: gh.Response(200, {}, b'{"merged_at": null}'))
    seed(gh.GitHubClient(env=None), 77)
    landing = gh.rest_read(
        "merge-facts", "o/r", {"batch": [("o/r", 7)]}, caller="lander", capture_output=True, text=True
    )
    assert landing.returncode == 0 and json.loads(landing.stdout) == {"data": {"r0": {"p7": {"mergedAt": None}}}}
    assert calls == [("GET", "repos/o/r/pulls/7")]
    assert counters.report_for(tmp_path, NOW)["windows"]["current"]["resources"]["core"] == [
        {"caller": "lander", "count": 1}
    ]
    reader = gh.rest_read("pr-bases", "o/r", {}, caller="reader", capture_output=True, text=True)
    assert reader.returncode == 75 and len(calls) == 1
    assert json.loads(reader.stderr) == {
        "error": "github_budget_refused",
        "reset_at": RESET,
        "reason": "core_below_landing_reserve",
    }


def test_queue_read_is_a_landing_operation(tmp_path, monkeypatch):
    def answer(method, endpoint):
        body = b'{"data": {"repository": {"q0": {"url": "u"}}}}' if endpoint == "graphql" else b"[]"
        return gh.Response(200, {}, body)

    calls = route_client_builder(tmp_path, monkeypatch, answer)
    seed(gh.GitHubClient(env=None), 77)
    result = gh.queue_read(
        "queue-snapshot", "o/r", {"branches": ["main"]}, caller="keeper", capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert [endpoint.split("?")[0] for _, endpoint in calls] == ["repos/o/r/pulls", "graphql"]
    resources = counters.report_for(tmp_path, NOW)["windows"]["current"]["resources"]
    assert resources["core"] == [{"caller": "keeper", "count": 1}] and resources["graphql"] == [
        {"caller": "keeper", "count": 1}
    ]


def test_publisher_tags_its_traffic(monkeypatch):
    from scripts.publish import github as publisher

    seen = []
    monkeypatch.setattr(publisher.github_client, "run", lambda command, **kwargs: seen.append(kwargs.get("caller")))
    monkeypatch.setattr(counters, "_process_caller", None)
    publisher._run_transport(["gh", "api", "user"], env={})
    counters.set_process_caller("keeper")
    publisher._run_transport(["gh", "api", "user"], env={})
    assert seen == ["publish", "keeper"]


# --- landing calls proceed at every remaining value, zero and unknown included (review round 2: F1) ---

VERDICT_TRAFFIC = {
    "verdict-comment": ("POST", "repos/o/r/issues/7/comments", {"body": "VERDICT: APPROVE"}),
    "comment-readback": ("GET", "repos/o/r/issues/7/comments?per_page=100", None),
    "single-comment-readback": ("GET", "repos/o/r/issues/comments/9", None),
    "timeline-readback": ("GET", "repos/o/r/issues/7/timeline", None),
    "commit-status": ("POST", "repos/o/r/statuses/0123abcd", {"state": "success", "context": "cf"}),
}
LANDING_WRITES = {
    "merge": ("PUT", "repos/o/r/pulls/7/merge", {"merge_method": "squash"}),
    "enqueue": (
        "POST",
        "graphql",
        {"query": "mutation($i:EnqueuePullRequestInput!){enqueuePullRequest(input:$i){clientMutationId}}"},
    ),
    "update-branch": ("PUT", "repos/o/r/pulls/7/update-branch", None),
    "rerun-failed": ("POST", "repos/o/r/actions/runs/55/rerun-failed-jobs", None),
}


def send(client, shape):
    method, path, payload = shape
    return client.request(method, path, payload=payload, fresh=True)


@pytest.mark.parametrize("name", sorted(VERDICT_TRAFFIC))
@pytest.mark.parametrize("remaining", [499, 500, 501])
def test_verdict_traffic_is_landing_class_around_the_reserve(tmp_path, name, remaining):
    client, calls = make(tmp_path)
    seed(client, remaining)
    assert send(client, VERDICT_TRAFFIC[name]).status == 200
    assert len(calls) == 1


@pytest.mark.parametrize("name", sorted(VERDICT_TRAFFIC))
def test_verdict_traffic_proceeds_at_a_zero_budget(tmp_path, name):
    client, calls = make(tmp_path)
    seed(client, 0)
    assert send(client, VERDICT_TRAFFIC[name]).status == 200
    assert len(calls) == 1 and count(tmp_path) == 1


def test_a_verdict_after_a_reserve_refusal_still_goes_out_at_zero(tmp_path):
    client, calls = make(tmp_path)
    seed(client, 499)
    with pytest.raises(gh.GitHubBudgetRefused):
        client.request(*NON_LANDING)
    seed(client, 0, reset=RESET + 1)
    assert send(client, VERDICT_TRAFFIC["verdict-comment"]).status == 200 and len(calls) == 1


@pytest.mark.parametrize("name", sorted(VERDICT_TRAFFIC))
def test_verdict_traffic_is_never_starved_by_an_unknown_or_expired_budget(tmp_path, name):
    client, calls = make(tmp_path)
    assert send(client, VERDICT_TRAFFIC[name]).status == 200  # no budget row at all
    seed(client, 0, reset=NOW)  # the window has rolled over
    assert send(client, VERDICT_TRAFFIC[name]).status == 200 and len(calls) == 2


@pytest.mark.parametrize("name", sorted(LANDING_WRITES))
@pytest.mark.parametrize("remaining", [499, 10, 1, 0])
def test_landing_writes_are_not_held_back_by_any_budget(tmp_path, name, remaining):
    client, calls = make(tmp_path)
    seed(client, remaining, resource="graphql" if name == "enqueue" else "core")
    assert send(client, LANDING_WRITES[name]).status == 200
    assert len(calls) == 1 and count(tmp_path) == 1


@pytest.mark.parametrize("name", sorted(LANDING_WRITES))
def test_landing_writes_go_out_with_no_budget_known(tmp_path, name):
    client, calls = make(tmp_path)
    assert send(client, LANDING_WRITES[name]).status == 200 and len(calls) == 1


@pytest.mark.parametrize(
    "shape", [LANDING_WRITES["merge"], VERDICT_TRAFFIC["verdict-comment"]], ids=["merge", "verdict"]
)
def test_only_githubs_own_retry_after_holds_a_landing_call(tmp_path, shape):
    # GitHub asks clients to wait out a secondary limit; requests during it extend it.
    client, calls = make(tmp_path)
    seed(client, 0, resource="secondary")
    result = send(client, shape)
    assert result.error == "github_rate_limited" and result.reset_at == RESET and result.reason is None
    assert calls == [] and count(tmp_path) == 0


def test_non_landing_below_the_client_reserve_keeps_its_untyped_deferral(tmp_path):
    client, calls = make(tmp_path)
    seed(client, 0)
    result = client.request(*NON_LANDING)
    assert result.error == "github_rate_limited" and result.reason is None and calls == []


@pytest.mark.parametrize("remaining", [499, 1, 0])
def test_run_rerun_failed_and_update_branch_through_the_cli_seam(tmp_path, remaining):
    client, calls = make(tmp_path)
    seed(client, remaining)
    update = gh.run(
        ["gh", "api", "--method", "PUT", "repos/o/r/pulls/7/update-branch"], client=client, capture_output=True
    )
    rerun = gh.run(
        ["gh", "api", "--method", "POST", "repos/o/r/actions/runs/55/rerun-failed-jobs"],
        client=client,
        capture_output=True,
    )
    assert update.returncode == 0 and rerun.returncode == 0 and len(calls) == 2


@pytest.mark.parametrize("remaining", [499, 1, 0])
@pytest.mark.parametrize(
    "shape",
    [
        ["gh", "api", "--paginate", "--jq", ".x", "repos/o/r/pulls/7/reviews"],
        ["gh", "run", "rerun", "55", "--failed"],
        ["gh", "pr", "checks", "7", "--json", "name,bucket,state,workflow", "--repo", "o/r"],
        ["gh", "pr", "merge", "7", "--squash", "--auto"],
    ],
    ids=["review-read", "rerun-failed", "checks", "merge"],
)
def test_landing_commands_reach_github_at_every_budget(tmp_path, remaining, shape):
    # Native or translated, a landing command is sent once whatever the budget says.
    client, calls = make(tmp_path)
    seed(client, remaining)
    seed(client, remaining, resource="graphql")
    native = []

    def runner(command, **kwargs):
        native.append(command)
        return gh.subprocess.CompletedProcess(command, 0, b"{}", b"")

    result = gh._run_command(shape, client=client, runner=runner, capture_output=True)
    assert result.returncode != 75 and len(native) + len(calls) >= 1


@pytest.mark.parametrize("remaining", [499, 0])
def test_a_native_non_landing_command_keeps_both_gates(tmp_path, remaining):
    client, _ = make(tmp_path)
    seed(client, remaining)
    runner = lambda command, **kwargs: pytest.fail("a gated command reached gh")  # noqa: E731
    shape = ["gh", "api", "--paginate", "--jq", ".x", "repos/o/r/issues"]
    if remaining:
        with pytest.raises(gh.GitHubBudgetRefused):
            gh._run_command(shape, client=client, runner=runner, capture_output=True)
    else:
        result = gh._run_command(shape, client=client, runner=runner, capture_output=True)
        assert result.returncode == 75 and json.loads(result.stderr)["error"] == "github_rate_limited"


def pull_and_checks(method, endpoint):
    if endpoint.startswith("repos/o/r/pulls/7"):
        return gh.Response(200, {}, json.dumps({"number": 7, "state": "open", "head": {"sha": "a" * 40}}).encode())
    if "check-runs" in endpoint:
        return gh.Response(200, {}, b'{"total_count": 0, "check_runs": []}')
    return gh.Response(200, {}, b'{"state": "success", "statuses": []}')


@pytest.mark.parametrize("remaining", [499, 0])
def test_a_ci_status_read_proceeds_but_a_plain_pull_request_read_does_not(tmp_path, monkeypatch, remaining):
    calls = route_client_builder(tmp_path, monkeypatch, pull_and_checks)
    client = gh.GitHubClient(env=None)
    seed(client, remaining)
    rollup = gh.run(
        ["gh", "pr", "view", "7", "--repo", "o/r", "--json", "statusCheckRollup"],
        client=client,
        capture_output=True,
        text=True,
    )
    assert rollup.returncode == 0, rollup.stderr
    assert calls[0] == ("GET", "repos/o/r/pulls/7") and len(calls) > 1  # the lookup, then the CI status
    sent = len(calls)
    plain = gh.run(
        ["gh", "pr", "view", "7", "--repo", "o/r", "--json", "headRefOid"],
        client=client,
        capture_output=True,
        text=True,
    )
    assert plain.returncode == 75 and len(calls) == sent


def test_the_publisher_merge_flow_reaches_github_at_a_zero_budget(tmp_path, monkeypatch):
    # Review round 2 (F1): the merge's own readiness read was refused before anything was sent.
    from scripts.publish import github as pub

    calls = route_client_builder(tmp_path, monkeypatch, lambda method, endpoint: gh.Response(500, {}, b"{}"))
    seed(gh.GitHubClient(env=None), 0)
    monkeypatch.setattr(pub.gate, "real_gh", lambda env: "gh")
    with pytest.raises(pub.gate.PublishBlocked, match="merge readiness unverifiable"):
        pub.publish("pr-merge", repo="o/r", number=7, env={"AGENT_NO_MERGE": "0"}, capture_output=True, text=True)
    assert calls[0] == ("GET", "repos/o/r/pulls/7")
