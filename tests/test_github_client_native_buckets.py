"""Native ``gh`` fall-through gates only on the buckets the command can spend (#10497); no network."""

import subprocess

import pytest

from scripts.common import github_client as gh

NOW = 1000
FUTURE = 2000


def seeded(tmp_path, exhausted):
    """Client whose named buckets are at remaining=0 with a future reset, plus call recorders."""
    translated, native = [], []

    def transport(method, endpoint, headers, body, timeout):
        translated.append(endpoint)
        return gh.Response(200, {"X-RateLimit-Remaining": "100", "X-RateLimit-Reset": "9000"}, b"[]")

    def runner(command, **kw):
        native.append(command)
        return subprocess.CompletedProcess(command, 0, b"[]", b"")

    store = gh.GitHubClient(cache_dir=tmp_path, transport=transport, clock=lambda: NOW, env={})
    with store._db() as db:
        for name in exhausted:
            gh._store_budget(db, store.scope, name, 0, FUTURE)
    return store, runner, translated, native


def blocked(result):
    return result.returncode == 75 and result.github_result.error == "github_rate_limited"


def spent(result, translated, native):
    return not blocked(result) and result.returncode == 0 and bool(translated or native)


UNRELATED = ["code_search", "code_scanning_autofix"]


@pytest.mark.parametrize(
    "args",
    [
        ["gh", "repo", "view", "--json", "owner,name"],
        ["gh", "pr", "view", "1"],
        ["gh", "issue", "list"],
        ["gh", "api", "repos/o/r/issues"],
        ["gh", "api", "--paginate", "--jq", ".x", "repos/o/r/issues"],
    ],
)
def test_unrelated_exhausted_buckets_do_not_block(tmp_path, args):
    store, runner, translated, native = seeded(tmp_path, UNRELATED)
    result = gh.run(args, client=store, runner=runner, capture_output=True)
    assert spent(result, translated, native)


@pytest.mark.parametrize(
    ("bucket", "args"),
    [
        ("core", ["gh", "api", "repos/o/r"]),
        ("graphql", ["gh", "api", "graphql"]),
        ("search", ["gh", "search", "prs", "x"]),
        ("code_search", ["gh", "search", "code", "x"]),
        ("code_search", ["gh", "api", "search/code"]),
        ("secondary", ["gh", "pr", "status"]),
        ("core", ["gh", "api", "--paginate", "--jq", ".x", "repos/o/r/issues"]),
        ("graphql", ["gh", "api", "--paginate", "--jq", ".x", "graphql"]),
        ("search", ["gh", "api", "--paginate", "--jq", ".x", "search/issues?q=x"]),
        ("code_search", ["gh", "api", "--paginate", "--jq", ".x", "search/code?q=x"]),
        ("secondary", ["gh", "api", "--paginate", "--jq", ".x", "repos/o/r/issues"]),
    ],
)
def test_own_exhausted_bucket_blocks_with_typed_result(tmp_path, bucket, args):
    store, runner, translated, native = seeded(tmp_path, [bucket])
    result = gh.run(args, client=store, runner=runner, capture_output=True)
    assert blocked(result) and result.github_result.reset_at == FUTURE
    assert not translated and not native


def test_exhausted_search_does_not_block_pr_status(tmp_path):
    store, runner, translated, native = seeded(tmp_path, ["search"])
    result = gh.run(["gh", "pr", "status"], client=store, runner=runner, capture_output=True)
    assert spent(result, translated, native) and native == [["gh", "pr", "status"]]


@pytest.mark.parametrize("bucket", ["core", "graphql"])
@pytest.mark.parametrize(
    "args",
    [
        ["gh", "pr", "view", "1"],
        ["gh", "pr", "status"],
        ["gh", "issue", "list"],
        ["gh", "repo", "view", "--json", "owner,name"],
        ["gh", "run", "list"],
        ["gh", "workflow", "list"],
        ["gh", "release", "list"],
        ["gh", "label", "list"],
        ["gh", "frobnicate", "x"],
    ],
)
def test_high_level_subcommands_blocked_by_core_or_graphql(tmp_path, bucket, args):
    store, runner, translated, native = seeded(tmp_path, [bucket])
    result = gh.run(args, client=store, runner=runner, capture_output=True)
    assert blocked(result) and not translated and not native


@pytest.mark.parametrize(
    "args",
    [
        ["gh", "pr", "status"],
        ["gh", "search", "prs", "x"],
        ["gh", "api", "--paginate", "--jq", ".x", "repos/o/r/issues"],
    ],
)
def test_unknown_bucket_never_blocks(tmp_path, args):
    store, runner, translated, native = seeded(tmp_path, ["some_future_bucket"])
    result = gh.run(args, client=store, runner=runner, capture_output=True)
    assert spent(result, translated, native)


def test_native_rate_limit_stderr_still_stores_secondary_and_exits_75(tmp_path):
    store, runner, _translated, native = seeded(tmp_path, [])
    seen = []

    def limited(command, **kw):
        seen.append(command)
        return subprocess.CompletedProcess(command, 1, b"", b"HTTP 429: secondary rate limit")

    first = gh.run(["gh", "pr", "status"], client=store, runner=limited, capture_output=True)
    assert blocked(first) and first.github_result.reset_at == NOW + 60
    with store._db() as db:
        assert db.execute(
            "SELECT remaining,reset FROM budget WHERE scope=? AND resource='secondary'", (store.scope,)
        ).fetchone() == (0, NOW + 60)
    again = gh.run(["gh", "issue", "list"], client=store, runner=runner, capture_output=True)
    assert blocked(again) and len(seen) == 1 and not native


def test_translated_search_code_uses_code_search_bucket(tmp_path):
    store, runner, translated, native = seeded(tmp_path, ["search"])
    assert spent(
        gh.run(["gh", "api", "search/code"], client=store, runner=runner, capture_output=True), translated, native
    )
    store, runner, translated, native = seeded(tmp_path / "other", ["code_search"])
    assert blocked(gh.run(["gh", "api", "search/code"], client=store, runner=runner, capture_output=True))
    assert not translated
    # other search endpoints keep the ``search`` bucket and are not blocked by code_search
    assert spent(
        gh.run(["gh", "api", "search/issues?q=x"], client=store, runner=runner, capture_output=True), translated, native
    )


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["gh", "api", "repos/o/r"], {"core"}),
        (["gh", "api", "--jq", ".x", "repos/o/r/issues"], {"core"}),
        (["gh", "api", "-X", "GET", "-f", "q=search/x", "repos/o/r"], {"core"}),
        (["gh", "api", "graphql", "-f", "query={viewer{login}}"], {"graphql"}),
        (["gh", "api", "https://api.github.com/graphql"], {"graphql"}),
        (["gh", "api", "search/code?q=x"], {"code_search"}),
        (["gh", "api", "/search/code"], {"code_search"}),
        (["gh", "api", "search/issues", "-f", "q=x"], {"search"}),
        (["gh", "api", "https://api.github.com/search/issues?q=x"], {"search"}),
        (["gh", "api", "https://api.github.com/search/code?q=x"], {"code_search"}),
        (["gh", "search", "code", "x"], {"code_search"}),
        (["gh", "search", "prs", "x"], {"search"}),
        (["gh", "pr", "view", "1"], {"core", "graphql"}),
        (["gh", "frobnicate"], {"core", "graphql"}),
        (["gh"], {"core", "graphql"}),
    ],
)
def test_native_buckets_over_the_denominator(args, expected):
    assert gh._native_buckets(args) == frozenset(expected | {"secondary"})
