"""Native ``gh`` fall-through gates only on the buckets the command can spend (#10497); no network."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from scripts.common import github_client as gh
from tests.common.github_cache_isolation import isolate_github_client_cache

NOW = 1000
FUTURE = 2000


@pytest.fixture(autouse=True)
def _isolate_github_client_cache(tmp_path, monkeypatch):
    yield from isolate_github_client_cache(tmp_path, monkeypatch)


def natively_runs(args):
    """The command line the native transport runs for ``args`` (#10730): a ``gh api`` that is neither
    paginated, verbose nor already ``--include``d gets ``--include`` after its last flag, so GitHub's
    status and headers come from gh's own framing; any other command line is unchanged."""
    tokens = list(args)
    if tokens[1:2] != ["api"] or {"--paginate", "--verbose", "--include", "-i"} & set(tokens):
        return tokens
    return [*tokens, "--include"]


def seeded(tmp_path, exhausted, remaining=0, *, host="github.com"):
    """Client whose named buckets are at ``remaining`` with a future reset, plus call recorders."""
    translated, native = [], []

    def transport(method, endpoint, headers, body, timeout):
        translated.append(endpoint)
        return gh.Response(200, {"X-RateLimit-Remaining": "100", "X-RateLimit-Reset": "9000"}, b"[]")

    def runner(command, **kw):
        native.append(command)
        return subprocess.CompletedProcess(command, 0, b"[]", b"")

    store = gh.GitHubClient(cache_dir=tmp_path, transport=transport, clock=lambda: NOW, env={"GH_HOST": host})
    with store._db() as db:
        for name in exhausted:
            gh._store_budget(db, store.scope, name, remaining, FUTURE)
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


ALL_BUCKETS = ["core", "graphql", "code_search", "search", "secondary"]
CORE, GRAPHQL, CODE, SEARCH, UNDETERMINED = (
    {"core"},
    {"graphql"},
    {"code_search"},
    {"search"},
    {"core", "graphql"},
)


def api(*tokens):
    return ["gh", "api", *tokens]


@pytest.mark.parametrize(
    "endpoint,path,bucket",
    [
        ("//graphql", "graphql", "graphql"),
        ("//search/code", "search/code", "code_search"),
        ("///graphql", "graphql", "graphql"),
        ("//", "", "core"),
        ("//github.com/x", "github.com/x", "core"),
        ("./graphql", "./graphql", "core"),
        ("user:1", "user:1", "core"),
        ("x:y", "x:y", "core"),
        ("search/code?q=https://x/y", "search/code", "code_search"),
        ("/search/code?q=https://x/y", "search/code", "code_search"),
        ("search/code#https://x/y", "search/code", "code_search"),
        ("user?next=https://x", "user", "core"),
        ("graphql#https://x", "graphql", "graphql"),
        ("//search/code?q=https://x/y", "search/code", "code_search"),
        ("//graphql?x=http://y", "graphql", "graphql"),
        ("search/code?q=x", "search/code", "code_search"),
        ("search/code#frag", "search/code", "code_search"),
        ("x:y?next=https://x", "x:y", "core"),
        ("repos/o/https://x", "repos/o/https://x", "core"),
        ("1https://x", "1https://x", "core"),
    ],
)
def test_relative_endpoint_spellings_never_select_a_host(tmp_path, endpoint, path, bucket):
    """Only a scheme at the start introduces an absolute URL."""
    assert gh._canonical_endpoint(endpoint) == ("relative", path)
    assert gh._native_buckets(api(endpoint)) == frozenset({bucket, "secondary"})
    store, runner, translated, native = seeded(tmp_path, [])
    assert gh.run(api(endpoint), client=store, runner=runner, capture_output=True).returncode == 0
    assert translated == [endpoint] and not native
    store, runner, translated, native = seeded(tmp_path / "native", [])
    args = api(endpoint, "--template", "{{.}}")
    assert gh.run(args, client=store, runner=runner, capture_output=True).returncode == 0
    assert native == [natively_runs(args)] and not translated
    store, runner, translated, native = seeded(tmp_path / "limited", [bucket])
    assert blocked(gh.run(args, client=store, runner=runner, capture_output=True))
    assert not translated and not native


@pytest.mark.parametrize(
    "endpoint,path,bucket",
    [
        ("https://api.github.com/search/code?q=https://x", "search/code", "code_search"),
        ("HTTPS://api.github.com/user", "user", "core"),
    ],
)
def test_absolute_scheme_position_preserves_native_admission(tmp_path, endpoint, path, bucket):
    assert gh._canonical_endpoint(endpoint) == ("api", path)
    assert gh._native_buckets(api(endpoint)) == frozenset({bucket, "secondary"})
    store, runner, translated, native = seeded(tmp_path, [])
    args = api(endpoint, "--template", "{{.}}")
    assert gh.run(args, client=store, runner=runner, capture_output=True).returncode == 0
    assert native == [natively_runs(args)] and not translated


@pytest.mark.parametrize("native", [False, True])
@pytest.mark.parametrize(
    "host,endpoint",
    [
        ("github.com", "http://api.github.com:443/user"),
        ("ghe.example:8443", "https://ghe.example:9443/api/v3/user"),
    ],
)
def test_absolute_endpoint_port_mismatch_is_refused(tmp_path, native, host, endpoint):
    """HTTP port 443 is non-default; a GHES URL must match the selected authority's port."""
    assert gh._canonical_endpoint(endpoint, host)[0] == "rejected"
    args = api("--hostname", host, endpoint, *(["--paginate"] if native else []))
    with pytest.raises(ValueError, match="host mismatch"):
        gh._native_buckets(args)
    store, runner, translated, calls = seeded(tmp_path, [], host=host)
    result = gh.run(args, client=store, runner=runner, capture_output=True)
    assert result.github_result.error == "github_invalid_command"
    assert not translated and not calls


ROOT_ENDPOINTS = [
    api("--paginate", "--jq", ".x", "/"),
    api("--paginate", "--jq", ".x", "https://api.github.com"),
    api("--paginate", "--jq", ".x", "https://api.github.com/"),
    api("--hostname", "ghe.example", "--paginate", "--jq", ".x", "https://ghe.example/api/v3/"),
]


@pytest.mark.parametrize("args", ROOT_ENDPOINTS, ids=["relative", "absolute", "absolute-slash", "enterprise"])
def test_root_endpoint_is_determinable_core(args):
    assert gh._native_buckets(args) == frozenset({"core", "secondary"})


@pytest.mark.parametrize("args", ROOT_ENDPOINTS, ids=["relative", "absolute", "absolute-slash", "enterprise"])
@pytest.mark.parametrize("bucket", ALL_BUCKETS)
def test_root_endpoint_gates_only_core_and_secondary(tmp_path, args, bucket):
    options, _ = gh._options(args[2:])
    host = gh._opt(options, "--hostname", default="github.com")
    store, runner, translated, native = seeded(tmp_path, [bucket], host=host)
    result = gh.run(args, client=store, runner=runner, capture_output=True)
    assert not translated
    if bucket in {"core", "secondary"}:
        assert blocked(result) and not native
    else:
        assert result.returncode == 0 and native == [args]


HOST_SHAPES = [
    ("https://api.github.com./search/code", "code_search", True),
    ("HTTPS://api.github.com./search/code", "code_search", True),
    ("https://api.github.com:443/search/code", "code_search", True),
    ("https://probe@api.github.com/search/code", "code_search", True),
    ("https://API.GITHUB.COM/search/code", "code_search", True),
    ("https://api.github.c\u043em/search/code", "core", False),
    ("https:///search/code", "core", False),
    ("http://api.github.com/search/code", "code_search", True),
]


@pytest.mark.parametrize(("endpoint", "bucket", "accepted"), HOST_SHAPES)
def test_host_shape_admission_and_classification_agree(tmp_path, endpoint, bucket, accepted):
    if accepted:
        assert gh._native_buckets(api(endpoint)) == frozenset({bucket, "secondary"})
    else:
        with pytest.raises(ValueError, match="host mismatch"):
            gh._native_buckets(api(endpoint))
    store, runner, translated, native = seeded(tmp_path, [])
    result = gh.run(api(endpoint), client=store, runner=runner, capture_output=True)
    assert not native
    if accepted:
        assert result.returncode == 0 and translated == [endpoint]
        store, runner, translated, native = seeded(tmp_path / "limited", [bucket])
        result = gh.run(api(endpoint), client=store, runner=runner, capture_output=True)
        assert blocked(result) and not translated and not native
    else:
        assert result.github_result.error == "github_invalid_command" and not translated


@pytest.fixture
def no_jq(monkeypatch):
    """Output formatting is orthogonal to the gate; ``--jq search/code`` is not a valid jq program."""
    monkeypatch.setattr(gh, "_format_value", lambda value, options, *, api=False: b"[]")


# (argv, buckets the command can spend). A flag value, a path suffix or an
# interior segment must never select a bucket; only the whole endpoint does.
ENDPOINT_SHAPES = [
    # flag values that look like a search/graphql endpoint, before and after a core endpoint
    *[
        (api(*flag, "repos/o/r/issues"), CORE)
        for flag in (
            ["--jq", "search/code"],
            ["-q", "search/code"],
            ["--template", "search/code"],
            ["-t", "search/code"],
            ["-H", "X: search/code"],
            ["--hostname", "search/code"],
            ["-f", "q=search/code"],
            ["--jq=search/code"],
            ["--template=search/code"],
            ["--jq", "graphql"],
            ["--paginate", "--jq", "search/code"],
            ["--paginate", "--template", "search/code"],
        )
    ],
    *[
        (api("repos/o/r/issues", *flag), CORE)
        for flag in (
            ["--jq", "search/code"],
            ["-q", "search/code"],
            ["--template", "search/code"],
            ["-t", "search/code"],
            ["-H", "X: search/code"],
            ["--hostname", "search/code"],
            ["-f", "q=search/code"],
            ["--jq=search/code"],
            ["--template=search/code"],
        )
    ],
    (api("--jq", "search/code", "--", "repos/o/r/issues"), CORE),
    (api("--jq=search/code", "--", "repos/o/r/issues"), CORE),
    (api("--", "repos/o/r/issues"), CORE),
    (api("--jq", ".x", "--", "search/code"), CODE),
    # the flag values of a search endpoint do not turn it into anything else
    (api("--jq", "repos/o/r/issues", "search/code"), CODE),
    (api("-t", "graphql", "search/issues?q=x"), SEARCH),
    (api("--cache", "1h", "graphql"), GRAPHQL),
    # REST reads whose interior or trailing segment merely resembles an endpoint
    (api("repos/o/graphql"), CORE),
    (api("repos/o/r/contents/graphql"), CORE),
    (api("https://api.github.com/repos/o/r/contents/search/code"), CORE),
    (api("repos/o/r/contents/search/issues"), CORE),
    (api("repos/o/r/search/code"), CORE),
    (api("graphql/extra"), CORE),
    (api("search"), CORE),
    (api("search/code/"), SEARCH),
    # real endpoints
    (api("graphql"), GRAPHQL),
    (api("/graphql"), GRAPHQL),
    (api("https://api.github.com/graphql"), GRAPHQL),
    (api("graphql", "-f", "query={viewer{login}}"), GRAPHQL),
    (api("search/code"), CODE),
    (api("/search/code"), CODE),
    (api("search/code?q=x"), CODE),
    (api("search/code#frag"), CODE),
    (api("https://api.github.com/search/code?q=x"), CODE),
    (api("search/issues"), SEARCH),
    (api("search/issues?q=x"), SEARCH),
    (api("https://api.github.com/search/issues?q=x"), SEARCH),
    (api("search/repositories", "-f", "q=x"), SEARCH),
    # no determinable endpoint: core and graphql, never every bucket, never a flag value
    (api("--paginate"), UNDETERMINED),
    (api(), UNDETERMINED),
    (api("--jq", "search/code"), UNDETERMINED),
    (api("repos/o/r", "--jq"), CORE),
    (api("repos/o/r", "repos/o/s"), UNDETERMINED),
]


@pytest.mark.parametrize(
    ("args", "expected"), [pytest.param(a, e, id=" ".join(a[2:]) or "no-args") for a, e in ENDPOINT_SHAPES]
)
def test_endpoint_classification_table(args, expected):
    assert gh._native_buckets(args) == frozenset(expected | {"secondary"})


@pytest.mark.parametrize("remaining", [0, gh.RESERVE])
@pytest.mark.parametrize("bucket", ALL_BUCKETS)
@pytest.mark.parametrize(
    ("args", "expected"), [pytest.param(a, e, id=" ".join(a[2:]) or "no-args") for a, e in ENDPOINT_SHAPES]
)
def test_exhausted_bucket_gates_exactly_the_classified_shapes(no_jq, tmp_path, args, expected, bucket, remaining):
    options, _ = gh._options(args[2:])
    host = gh._opt(options, "--hostname", default="github.com")
    store, runner, translated, native = seeded(tmp_path, [bucket], remaining, host=host)
    result = gh.run(args, client=store, runner=runner, capture_output=True)
    if bucket == "secondary" or bucket in expected:
        assert blocked(result) and result.github_result.reset_at == FUTURE
        assert not translated and not native
    else:
        assert not blocked(result)
        assert translated or native


@pytest.mark.parametrize("bucket", ALL_BUCKETS)
def test_budget_above_reserve_never_blocks(no_jq, tmp_path, bucket):
    # Core keeps a landing reserve (#10730); every other bucket refuses only at RESERVE or below.
    above = gh.LANDING_RESERVE if bucket == "core" else gh.RESERVE + 1
    store, runner, translated, native = seeded(tmp_path, [bucket], above)
    result = gh.run(api("--jq", "search/code", "repos/o/r/issues"), client=store, runner=runner, capture_output=True)
    assert not blocked(result) and (translated or native)


@pytest.mark.parametrize("remaining", [gh.RESERVE + 1, gh.LANDING_RESERVE - 1])
def test_core_below_landing_reserve_blocks_non_landing_with_typed_reason(no_jq, tmp_path, remaining):
    store, runner, translated, native = seeded(tmp_path, ["core"], remaining)
    result = gh.run(api("--jq", "search/code", "repos/o/r/issues"), client=store, runner=runner, capture_output=True)
    assert blocked(result) and result.github_result.reason == "core_below_landing_reserve"
    assert not translated and not native


@pytest.mark.parametrize(
    ("args", "host", "expected"),
    [
        (api("http://api.github.com/graphql"), "github.com", GRAPHQL),
        (api("https://uploads.github.com/repos/o/r/releases/1/assets"), "github.com", CORE),
        # an absolute URL for a host that is not the API host is never an API resource
        (api("https://example.com/graphql"), "github.com", None),
        (api("https://example.com/search/code"), "github.com", None),
        (api("https://api.github.com/graphql"), "ghe.example", None),
        (api("--hostname", "ghe.example", "https://api.github.com/graphql"), "github.com", None),
        (api("https://ghe.example/graphql"), "ghe.example", GRAPHQL),
        (api("--hostname", "ghe.example", "https://ghe.example/search/code"), "github.com", CODE),
        (api("-X", "search/code", "repos/o/r"), "github.com", CORE),
        (api("--input", "search/code", "repos/o/r"), "github.com", CORE),
        (api("--preview", "search/code", "repos/o/r"), "github.com", CORE),
    ],
)
def test_url_endpoints_honour_the_api_host(args, host, expected):
    if expected is None:
        with pytest.raises(ValueError, match="host mismatch"):
            gh._native_buckets(args, host)
    else:
        assert gh._native_buckets(args, host) == frozenset(expected | {"secondary"})


@pytest.mark.parametrize(
    ("endpoint", "bucket"),
    [
        ("search/code", "code_search"),
        ("/search/code?q=x", "code_search"),
        ("https://api.github.com/search/code?q=x", "code_search"),
        ("search/issues?q=x", "search"),
        ("graphql", "graphql"),
        ("search/code?q=https://x/y", "code_search"),
        ("/search/code?q=https://x/y", "code_search"),
        ("search/code#https://x/y", "code_search"),
        ("user?next=https://x", "core"),
        ("graphql#https://x", "graphql"),
        ("//graphql?x=http://y", "graphql"),
        ("https://api.github.com/search/code?q=https://x", "code_search"),
        ("HTTPS://api.github.com/user", "core"),
        ("repos/o/graphql", "core"),
        ("repos/o/r/contents/search/code", "core"),
        ("https://api.github.com/repos/o/r/contents/graphql", "core"),
    ],
)
def test_translated_request_uses_the_shared_classification(tmp_path, endpoint, bucket):
    """GitHubClient.request and the native gate classify through one function."""
    assert gh._endpoint_bucket(gh._resource_path(endpoint)) == bucket
    store, _runner, translated, _native = seeded(tmp_path / "own", [bucket])
    assert store.request("GET", endpoint).error == "github_rate_limited"
    assert not translated
    others = [name for name in ALL_BUCKETS if name not in {bucket, "secondary"}]
    store, _runner, translated, _native = seeded(tmp_path / "others", others)
    assert store.request("GET", endpoint).error is None
    assert translated


# Absolute URLs go to native gh unchanged. Force native fall-through with
# --paginate/--jq so these rows prove runner admission, not just path parsing.
NORMALIZED_NATIVE_SHAPES = [
    *[
        (api(f"{scheme}://{authority}/{path}?q=x#fragment", "--paginate", "--jq", ".x"), expected)
        for scheme, port in (("HTTP", 80), ("Http", 80), ("HTTPS", 443))
        for authority in (
            "API.GITHUB.COM",
            f"API.GITHUB.COM:{port}",
            "probe@API.GITHUB.COM",
            f"probe@API.GITHUB.COM.:{port}",
        )
        for path, expected in (("graphql", GRAPHQL), ("search/code", CODE))
    ],
    *[
        (api("--hostname", hostname, f"https://{authority}/api/graphql"), GRAPHQL)
        for hostname in ("GHE.EXAMPLE", "GhE.Example.", "probe@GHE.EXAMPLE.:443")
        for authority in ("ghe.example", "GHE.EXAMPLE.:443")
    ],
    *[
        (api("--hostname", "ghe.example", f"https://ghe.example/{path}?q=x#fragment"), expected)
        for path, expected in (
            ("api/graphql", GRAPHQL),
            ("api/v3/graphql", GRAPHQL),
            ("api/v3/search/code", CODE),
            ("api/v3/search/issues", SEARCH),
            ("api/v3/repos/o/r/issues", CORE),
            ("api/GraphQL", CORE),
            ("api/graphql/extra", CORE),
            ("api/search/code", CORE),
        )
    ],
    *[
        (api(endpoint, "--paginate", "--jq", ".x"), CORE)
        for endpoint in (
            "https://api.github.com/api/v3/search/code",
            "https://api.github.com/api/graphql",
            "HTTPS://API.GITHUB.COM/GraphQL",
        )
    ],
    (api("--hostname", "API.GITHUB.COM", "https://api.github.com/api/v3/search/code"), CORE),
    *[
        (["gh", "search", *flags, "code", "x"], CODE)
        for flags in (
            ["--repo", "o/r"],
            ["-R", "o/r"],
            ["-Ro/r"],
            ["--repo=o/r"],
            ["--owner", "issues"],
            ["--limit", "5"],
            ["-L5"],
            ["--json", "path"],
            ["-q", ".x"],
            ["--jq", ".x"],
            ["-q.x"],
            ["--template", "issues"],
            ["--language", "go"],
            ["--extension", "py"],
            ["--filename", "issues"],
            ["--match", "file"],
            ["--size", "5"],
            ["--web"],
            ["-w"],
        )
    ],
    (["gh", "search", "-R", "o/r", "--limit", "5", "issues", "x"], SEARCH),
    (["gh", "search", "--language", "code", "issues", "x"], SEARCH),
    (["gh", "search", "code", "--repo", "o/r", "x"], CODE),
    (["gh", "search"], {"search", "code_search"}),
    (["gh", "search", "--repo", "code"], {"search", "code_search"}),
    (["gh", "search", "--owner", "code"], {"search", "code_search"}),
    (["gh", "search", "--json", "code", "--"], {"search", "code_search"}),
]


@pytest.mark.parametrize("remaining", [0, gh.RESERVE])
@pytest.mark.parametrize("bucket", ALL_BUCKETS)
@pytest.mark.parametrize(
    ("args", "expected"),
    [pytest.param(a, e, id=" ".join(a[1:])) for a, e in NORMALIZED_NATIVE_SHAPES],
)
def test_normalized_native_shapes_gate_runner(no_jq, tmp_path, args, expected, bucket, remaining):
    options, _ = gh._options(args[2:])
    host = gh._opt(options, "--hostname", default="github.com")
    store, runner, translated, native = seeded(tmp_path, [bucket], remaining, host=host)
    result = gh.run(args, client=store, runner=runner, capture_output=True)
    assert not translated
    if bucket == "secondary" or bucket in expected:
        assert blocked(result) and result.github_result.reset_at == FUTURE
        assert not native
    else:
        expected_args = list(args)
        if "--hostname" in expected_args:
            expected_args[expected_args.index("--hostname") + 1] = gh.canonical_host(host)
        assert result.returncode == 0 and native == [natively_runs(expected_args)]


@pytest.mark.parametrize(
    "endpoint",
    [
        "HTTPS://foreign.example/search/code",
        "http://foreign.example/search/code",
        "HTTP://foreign.example/search/code",
        "ftp://foreign.example/search/code",
        "FTP://foreign.example/search/code",
        "ftp://evil.example/user",
        "http://api.github.com:443/user",
        " https://api.github.com/user",
        "\x00https://api.github.com/user",
        "\thttps://api.github.com/user",
        "\nhttps://api.github.com/user",
        "\x7fhttps://api.github.com/user",
        "https://evil.com\\@api.github.com/x",
    ],
)
@pytest.mark.parametrize("native", [False, True])
def test_host_boundary_refuses_before_either_transport(no_jq, tmp_path, endpoint, native):
    store, runner, translated, calls = seeded(tmp_path, [])
    args = api(endpoint, *(["--paginate", "--jq", ".x"] if native else []))
    result = gh.run(args, client=store, runner=runner, capture_output=True)
    assert result.github_result.error == "github_invalid_command"
    assert not translated and not calls


# Frozen from the exact parent blob, never imported or executed during tests.
# Each position's bit mask records admission for codepoints in the given order.
PARENT_ADMISSION = json.loads((Path(__file__).parent / "fixtures/github_endpoint_parent_admission.json").read_text())
SWEEP_ROWS = PARENT_ADMISSION["rows"]
SWEEP_CODEPOINTS = [*range(0x21), 0x7F]


def test_endpoint_sweep_denominator():
    assert PARENT_ADMISSION["parent_sha"] == "4b4696291a613436725ad1e1c5aa5249f4bb3da5"
    assert PARENT_ADMISSION["codepoints"] == SWEEP_CODEPOINTS
    assert len(SWEEP_ROWS) == 13
    assert sum(len(row["endpoint"]) + 1 for row in SWEEP_ROWS) == 311
    for row in SWEEP_ROWS:
        assert len(row["admission_masks"]) == len(row["endpoint"]) + 1
        assert len(row["space_outcomes"]) == len(row["endpoint"]) + 1


@pytest.mark.parametrize("row", SWEEP_ROWS, ids=[row["name"] for row in SWEEP_ROWS])
@pytest.mark.parametrize("codepoint", SWEEP_CODEPOINTS, ids=lambda value: f"byte-{value:02x}")
def test_endpoint_byte_insertion_sweep(monkeypatch, tmp_path, row, codepoint):
    """Every offset, including discarded query/fragment text, gets checked."""
    store = gh.GitHubClient(cache_dir=tmp_path, env={"GH_CONFIG_DIR": str(tmp_path)}, clock=lambda: NOW)
    send = Mock(return_value=gh.Response(200, {}, b"[]"))
    runner = Mock(return_value=subprocess.CompletedProcess([], 0, b"[]", b""))
    monkeypatch.setattr(store, "_send", send)
    endpoint = row["endpoint"]
    bit = SWEEP_CODEPOINTS.index(codepoint)
    for position in range(len(endpoint) + 1):
        mutated = endpoint[:position] + chr(codepoint) + endpoint[position:]
        host_class, path = gh._canonical_endpoint(mutated)
        parent_admitted = bool(int(row["admission_masks"][position], 16) & (1 << bit))
        # No historical exception is needed for this swept denominator.
        assert host_class == "rejected" or parent_admitted, (row["name"], codepoint, position)
        if codepoint != 0x20:
            assert (host_class, path) == ("rejected", mutated)
            with pytest.raises(ValueError, match="host mismatch"):
                store.request("GET", mutated)
            for flags in ([], ["--paginate"]):
                result = gh.run(api(mutated, *flags), client=store, runner=runner, capture_output=True)
                assert result.github_result.error == "github_invalid_command"
            send.assert_not_called()
            runner.assert_not_called()
        elif "?" in endpoint and position > endpoint.index("?"):
            # Query spaces retain the parent's admission and path. Existing
            # code_search bucket normalization is independent of query spaces.
            parent_class, parent_path = row["space_outcomes"][position]
            assert parent_class == "admitted"
            assert host_class in {"api", "relative"} and path == parent_path
            assert (host_class, path) == gh._canonical_endpoint(endpoint)
            assert store.request("GET", mutated).value == []
            assert send.call_args.args[1] == mutated


@pytest.mark.parametrize(
    "endpoint",
    [
        pytest.param("h\thttps://evil.example/user", id="tab-inside-scheme-token"),
        pytest.param("https:\t//evil.example/user", id="tab-before-foreign-authority"),
        pytest.param("https:\n//evil.example/user", id="newline-before-foreign-authority"),
        pytest.param("http:\t//api.github.com:443/user", id="tab-before-nondefault-port"),
    ],
)
def test_shifted_control_regressions(monkeypatch, tmp_path, endpoint):
    store = gh.GitHubClient(cache_dir=tmp_path, env={"GH_CONFIG_DIR": str(tmp_path)})
    send, runner = Mock(), Mock()
    monkeypatch.setattr(store, "_send", send)
    assert gh._canonical_endpoint(endpoint) == ("rejected", endpoint)
    with pytest.raises(ValueError, match="host mismatch"):
        store.request("GET", endpoint)
    for flags in ([], ["--paginate"]):
        result = gh.run(api(endpoint, *flags), client=store, runner=runner, capture_output=True)
        assert result.github_result.error == "github_invalid_command"
    send.assert_not_called()
    runner.assert_not_called()


@pytest.mark.parametrize(
    "endpoint,expected,bucket",
    [
        ("https://api.github.com/search/code?q=https://x", ("api", "search/code"), "code_search"),
        ("HTTPS://api.github.com/user", ("api", "user"), "core"),
        ("//host/x?u=http://y", ("relative", "host/x"), "core"),
        ("x:y", ("relative", "x:y"), "core"),
        ("javascript:alert(1)", ("relative", "javascript:alert(1)"), "core"),
        ("user:1", ("relative", "user:1"), "core"),
        ("javascript://evil.example", ("rejected", "javascript://evil.example"), None),
        ("", ("relative", ""), "core"),
        (" user", ("rejected", " user"), None),
        ("user ", ("relative", "user "), "core"),
        ("https://api.github.com/user ", ("rejected", "https://api.github.com/user "), None),
        ("https://api.github.com/user?q=a b ", ("api", "user"), "core"),
    ],
)
def test_control_fix_preserves_endpoint_and_space_contract(endpoint, expected, bucket):
    assert gh._canonical_endpoint(endpoint) == expected
    if bucket is not None:
        assert gh._endpoint_bucket(expected[1]) == bucket
