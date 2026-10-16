"""One request normalizer for every GitHub transport (#10730 slice 1); no network.

A table-driven matrix: each representation of a request (``GitHubClient.request`` payloads,
``urllib`` ``Request.data``, native and translated ``gh api`` argv), each GraphQL semantic
case and each hold kind, crossed with the call's pool at remaining 0, unknown and 500. The
expected class is a literal in each row, never computed by the code under test. Admitted
rows assert one send of the exact request; refused rows assert zero sends and the exact
typed reason and reset. The gh contract is verified against the installed gh 2.98.0 binary
through a local recording proxy when it is present.
"""

from __future__ import annotations

import email.utils
import http.server
import io
import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request

import pytest

from scripts.common import github_client as gh

NOW = int(time.time())
OPEN = NOW + 3600  # a reset in the future: the window is open
TOKEN = "synthetic-token"
AUTH = {"Authorization": "Bearer " + TOKEN}
REASON = {"core": "core_below_landing_reserve", "graphql": "pool_exhausted"}

M = 'mutation { enqueuePullRequest(input: {pullRequestId: "PR_1"}) { clientMutationId } }'
LAND = 'mutation Land { enqueuePullRequest(input: {pullRequestId: "PR_1"}) { clientMutationId } }'
R = "query Read { viewer { login } }"
SEVERAL = LAND + ' mutation Comment { addComment(input: {subjectId: "X", body: "x"}) { clientMutationId } } ' + R
# The comment executes unless the typed variable skips it.
CONDITIONAL = (
    "mutation($skip: Boolean!) { enqueuePullRequest(input: {}) { clientMutationId } "
    "addComment(input: {}) @skip(if: $skip) { clientMutationId } }"
)
COUNTED = "mutation($n: Int!) { enqueuePullRequest(input: {pullRequestId: $n}) { clientMutationId } }"
FRAGMENT = "fragment Landing on Mutation { enqueuePullRequest(input: {}) { clientMutationId } }"


def envelope(document=M, **fields):
    return json.dumps({"query": document, **fields}).encode()


# --- the wire -------------------------------------------------------------------------------


class Wire:
    """What reached GitHub: the HTTP transport, the urllib opener and the native ``gh`` runner."""

    def __init__(self, reply=None):
        self.sent = []
        self.reply = reply or (lambda: gh.Response(200, {}, b'{"data":{}}'))

    def transport(self, method, endpoint, headers, body, timeout):
        self.sent.append(("http", method, endpoint, body))
        return self.reply()

    def runner(self, command, **kwargs):
        self.sent.append(("native", tuple(command[1:]), kwargs.get("input")))
        return subprocess.CompletedProcess(command, 0, b"{}", b"")

    def opener(self, request, **kwargs):
        """Send as Python 3.12 urllib does: it refuses str data before any connection."""
        data = request.data
        if isinstance(data, str):
            raise TypeError("POST data should be bytes, an iterable of bytes, or a file object.")
        if hasattr(data, "read"):
            sent = data.read()
            sent = sent.encode("iso-8859-1") if isinstance(sent, str) else sent
        elif data is None or isinstance(data, (bytes, bytearray, memoryview)):
            sent = None if data is None else bytes(data)
        else:
            sent = b"".join(bytes(chunk) for chunk in data)
        self.sent.append(("http_open", request.get_method(), request.full_url, sent))
        response = io.BytesIO(b'{"data":{}}')
        response.status, response.headers = 200, {}
        return response


@dataclass
class Context:
    client: Any
    wire: Wire
    tmp: Path
    now: int


@pytest.fixture
def context(tmp_path, monkeypatch):
    """The real client over the wire at the current time; ``http_open`` shares its cache, scope and budgets."""
    monkeypatch.setenv("LU_GITHUB_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)
    wire, now = Wire(), int(time.time())
    client = gh.GitHubClient(
        cache_dir=tmp_path / "cache",
        transport=wire.transport,
        runner=wire.runner,
        clock=lambda: now,
        env={"GH_TOKEN": TOKEN},
    )
    client.cwd = tmp_path
    return Context(client, wire, tmp_path, now)


def seed(context, rows):
    with context.client._db() as db:
        for resource, remaining, reset in rows:
            gh._store_budget(db, context.client.scope, resource, remaining, reset)


BUDGETS = {"0": 0, "unknown": None, "500": 500}


def budget_rows(pool, value):
    return [] if BUDGETS[value] is None else [(pool, BUDGETS[value], OPEN)]


def outcome(call, context):
    """Run a call: ``("ok", result)``, ``("limited", reason, reset)`` or ``("unprepared", reason)``."""
    try:
        result = call(context)
    except gh.GitHubRateLimited as limited:
        return ("limited", limited.reason, limited.reset_at)
    except gh.GitHubUnpreparedRequest as unprepared:
        return ("unprepared", unprepared.reason)
    except TypeError:
        return ("opener_type_error",)
    observation = getattr(result, "github_result", result)
    if isinstance(observation, gh.Result) and observation.error == "github_rate_limited":
        if isinstance(result, subprocess.CompletedProcess):
            assert result.returncode == 75
            detail = {"error": "github_rate_limited", "reset_at": observation.reset_at, "reason": observation.reason}
            assert json.loads(result.stdout) == detail
        return ("limited", observation.reason, observation.reset_at)
    if isinstance(observation, gh.Result) and observation.error == "github_invalid_request":
        if isinstance(result, subprocess.CompletedProcess):
            assert result.returncode == 1
            assert json.loads(result.stdout) == {
                "error": "github_invalid_request",
                "reset_at": None,
                "reason": observation.reason,
            }
        return ("unprepared", observation.reason)
    if isinstance(result, subprocess.CompletedProcess):
        assert result.returncode == 0, result.stderr
    elif isinstance(observation, gh.Result):
        assert observation.error is None, observation.error
    return ("ok", result)


# --- representations ------------------------------------------------------------------------


def request(method, endpoint, payload=None):
    return lambda context: context.client.request(method, endpoint, payload=payload)


def opened(method, path, data):
    url = "https://api.github.com/" + path

    def call(context):
        body = data() if callable(data) else data
        context.last_body = body
        return gh.http_open(Request(url, data=body, method=method, headers=AUTH), opener=context.wire.opener)

    return call


def native(*argv, input=None, files=None):
    """``gh api`` through the native transport (``--template`` keeps it out of translation)."""

    def call(context):
        for name, content in (files or {}).items():
            path = context.tmp / name
            if content == "fifo":
                os.mkfifo(path)
            else:
                path.write_bytes(content.encode() if isinstance(content, str) else content)
        return gh.run(["gh", *argv], client=context.client, capture_output=True, input=input)

    return call


def translated(*argv, input=None, files=None):
    return native(*argv, input=input, files=files)


class Unseekable(io.RawIOBase):
    """A stream urllib can send once (a socket or pipe): reading it consumes it."""

    def __init__(self, data):
        self.inner, self.consumed = io.BytesIO(data), 0

    def readable(self):
        return True

    def seekable(self):
        return False

    def readinto(self, buffer):
        chunk = self.inner.read(len(buffer))
        self.consumed += len(chunk)
        buffer[: len(chunk)] = chunk
        return len(chunk)


def chunks(data):
    def generate():
        yield data[:10]
        yield b""
        yield data[10:]

    return generate()


TEMPLATE = ("--template", "{{.}}")


@dataclass
class Row:
    id: str
    pool: str
    expected: str  # "L" landing, "N" ordinary, "P:<reason>" refused unread when admission needs the body
    call: Any
    sent: Any = None  # the exact body bytes the admitted request carries, when the row pins them


ROWS = [
    # GitHubClient.request payloads
    Row("request-mapping", "graphql", "L", request("POST", "graphql", {"query": M}), envelope()),
    Row("request-bytes", "graphql", "L", request("POST", "graphql", envelope()), envelope()),
    Row("request-bytearray", "graphql", "L", request("POST", "graphql", bytearray(envelope())), envelope()),
    Row("request-memoryview", "graphql", "L", request("POST", "graphql", memoryview(envelope())), envelope()),
    Row("request-bytes-read", "graphql", "N", request("POST", "graphql", envelope(R))),
    # A str payload is sent as a JSON string: it executes nothing, so it is never landing.
    Row("request-str-is-a-json-string", "graphql", "N", request("POST", "graphql", envelope().decode())),
    Row("rest-put-merge", "core", "L", request("PUT", "repos/o/r/pulls/1/merge", {"merge_method": "squash"})),
    Row("rest-get-merge-shaped-url", "core", "N", request("GET", "repos/o/r/pulls/1/merge")),
    # urllib Request.data, through http_open
    Row("data-bytes", "graphql", "L", opened("POST", "graphql", envelope()), envelope()),
    Row("data-bytes-read", "graphql", "N", opened("POST", "graphql", envelope(R))),
    Row("data-str", "graphql", "P:invalid_body_type", opened("POST", "graphql", envelope().decode())),
    Row("data-seekable-file", "graphql", "L", opened("POST", "graphql", lambda: io.BytesIO(envelope())), envelope()),
    Row("data-seekable-file-read", "graphql", "N", opened("POST", "graphql", lambda: io.BytesIO(envelope(R)))),
    Row(
        "data-text-file",
        "graphql",
        "L",
        opened("POST", "graphql", lambda: io.StringIO(envelope().decode())),
        envelope(),
    ),
    Row(
        "data-non-seekable-reader",
        "graphql",
        "P:body_not_replayable",
        opened("POST", "graphql", lambda: Unseekable(envelope())),
    ),
    Row(
        "data-generator-chunks",
        "graphql",
        "P:body_not_replayable",
        opened("POST", "graphql", lambda: chunks(envelope())),
    ),
    Row(
        "data-list-chunks",
        "graphql",
        "L",
        opened("POST", "graphql", lambda: [envelope()[:10], b"", envelope()[10:]]),
        envelope(),
    ),
    Row("data-list-chunks-read", "graphql", "N", opened("POST", "graphql", lambda: [envelope(R)[:5], envelope(R)[5:]])),
    # A landing REST write is landing by its shape: its streamed body is never read.
    Row(
        "data-generator-put-merge",
        "core",
        "L",
        opened("PUT", "repos/o/r/pulls/1/merge", lambda: chunks(b'{"merge_method":"squash"}')),
        b'{"merge_method":"squash"}',
    ),
    # native gh api: typed and raw fields (gh 2.98.0 magicFieldValue)
    Row(
        "native-F-operationName-null",
        "graphql",
        "L",
        native("api", "graphql", "-f", "query=" + M, "-F", "operationName=null", *TEMPLATE),
    ),
    Row(
        "native-f-operationName-null-is-a-string",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + M, "-f", "operationName=null", *TEMPLATE),
    ),
    Row(
        "native-operation-named-null",
        "graphql",
        "L",
        native(
            "api",
            "graphql",
            "-f",
            "query=" + M.replace("mutation", "mutation null"),
            "-f",
            "operationName=null",
            *TEMPLATE,
        ),
    ),
    Row(
        "native-F-operationName-true",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + M, "-F", "operationName=true", *TEMPLATE),
    ),
    Row(
        "native-F-operationName-int",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + M, "-F", "operationName=7", *TEMPLATE),
    ),
    Row(
        "native-F-true-skips",
        "graphql",
        "L",
        native("api", "graphql", "-f", "query=" + CONDITIONAL, "-F", "skip=true", *TEMPLATE),
    ),
    Row(
        "native-F-false-keeps",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + CONDITIONAL, "-F", "skip=false", *TEMPLATE),
    ),
    Row(
        "native-f-true-is-a-string",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + CONDITIONAL, "-f", "skip=true", *TEMPLATE),
    ),
    Row(
        "native-F-positive-int",
        "graphql",
        "L",
        native("api", "graphql", "-f", "query=" + COUNTED, "-F", "n=5", *TEMPLATE),
    ),
    Row(
        "native-F-negative-int",
        "graphql",
        "L",
        native("api", "graphql", "-f", "query=" + COUNTED, "-F", "n=-5", *TEMPLATE),
    ),
    Row(
        "native-F-at-file",
        "graphql",
        "L",
        native("api", "graphql", "-F", "query=@q.graphql", *TEMPLATE, files={"q.graphql": M}),
    ),
    Row(
        "native-F-at-file-read",
        "graphql",
        "N",
        native("api", "graphql", "-F", "query=@q.graphql", *TEMPLATE, files={"q.graphql": R}),
    ),
    Row("native-F-at-stdin", "graphql", "L", native("api", "graphql", "-F", "query=@-", *TEMPLATE, input=M.encode())),
    Row(
        "native-F-at-missing",
        "graphql",
        "P:body_unreadable",
        native("api", "graphql", "-F", "query=@missing", *TEMPLATE),
    ),
    Row(
        "native-f-at-is-literal",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=@q.graphql", *TEMPLATE, files={"q.graphql": M}),
    ),
    Row(
        "native-F-placeholder-unresolved",
        "graphql",
        "N",
        native("api", "graphql", "-F", "query=" + M.replace("PR_1", "{owner}"), *TEMPLATE),
    ),
    Row("native-attached-short-flag", "graphql", "L", native("api", "graphql", "-fquery=" + M, *TEMPLATE)),
    Row("native-combined-short-flags", "graphql", "L", native("api", "-iXPOST", "graphql", "-fquery=" + M, *TEMPLATE)),
    Row(
        "native-input-file",
        "graphql",
        "L",
        native("api", "graphql", "--input", "e.json", *TEMPLATE, files={"e.json": envelope()}),
    ),
    Row(
        "native-input-stdin-bytes",
        "graphql",
        "L",
        native("api", "graphql", "--input", "-", *TEMPLATE, input=envelope()),
    ),
    Row(
        "native-input-stdin-text",
        "graphql",
        "L",
        native("api", "graphql", "--input", "-", *TEMPLATE, input=envelope().decode()),
    ),
    Row(
        "native-input-fifo",
        "graphql",
        "P:body_not_replayable",
        native("api", "graphql", "--input", "pipe", *TEMPLATE, files={"pipe": "fifo"}),
    ),
    Row(
        "native-input-read-field-to-url",
        "graphql",
        "N",
        native("api", "graphql", "--input", "r.json", "-f", "query=" + M, *TEMPLATE, files={"r.json": envelope(R)}),
    ),
    Row(
        "native-stdin-taken-by-field",
        "graphql",
        "N",
        native("api", "graphql", "-F", "x=@-", "--input", "-", *TEMPLATE, input=envelope()),
    ),
    Row(
        "native-explicit-get-mutation",
        "graphql",
        "N",
        native("api", "graphql", "-X", "GET", "-f", "query=" + M, *TEMPLATE),
    ),
    Row(
        "native-explicit-post-read",
        "graphql",
        "N",
        native("api", "graphql", "-X", "POST", "-f", "query=" + R, *TEMPLATE),
    ),
    Row(
        "native-duplicate-field-gh-refuses",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + M, "-F", "query=" + M, *TEMPLATE),
    ),
    Row(
        "native-fake-landing-headers",
        "core",
        "N",
        native("api", "repos/o/r/pulls/1/reviews", "-H", "X-Landing-Flow: merge-queue-keeper", *TEMPLATE),
    ),
    Row("native-put-merge", "core", "L", native("api", "-X", "PUT", "repos/o/r/pulls/1/merge", *TEMPLATE)),
    # -F is a body file outside gh api: never read for admission, whatever it holds.
    Row(
        "native-issue-comment-F-body-file",
        "core",
        "N",
        native("issue", "comment", "1", "--repo", "o/r", "-F", "e.json", files={"e.json": envelope()}),
    ),
    Row(
        "native-pr-review-F-body-file",
        "core",
        "L",
        native("pr", "review", "1", "--repo", "o/r", "--comment", "-F", "body.md", files={"body.md": "x"}),
    ),
    # translated gh api: what is sent is what gh would send
    Row(
        "translated-f-query",
        "graphql",
        "L",
        translated("api", "graphql", "-f", "query=" + M),
        b'{"query":"mutation { enqueuePullRequest(input: {pullRequestId: \\"PR_1\\"}) { clientMutationId } }"}',
    ),
    Row(
        "translated-f-variables-grouped",
        "graphql",
        "L",
        translated("api", "graphql", "-f", "query=" + LAND, "-f", "operationName=Land", "-f", "x=1"),
        b'{"operationName":"Land","query":"mutation Land { enqueuePullRequest(input: {pullRequestId: \\"PR_1\\"}) { clientMutationId } }","variables":{"x":"1"}}',
    ),
    Row(
        "translated-input-file",
        "graphql",
        "L",
        translated("api", "graphql", "--input", "e.json", files={"e.json": envelope()}),
        envelope(),
    ),
    Row("translated-get-reads-merge-url", "core", "N", translated("api", "repos/o/r/pulls/1/merge")),
    # GraphQL semantics (GitHubClient.request mappings)
    Row(
        "gql-alias-of-landing-field",
        "graphql",
        "L",
        request("POST", "graphql", {"query": "mutation { a: enqueuePullRequest(input: {}) { clientMutationId } }"}),
    ),
    Row(
        "gql-landing-alias-on-comment",
        "graphql",
        "N",
        request(
            "POST", "graphql", {"query": "mutation { enqueuePullRequest: addComment(input: {}) { clientMutationId } }"}
        ),
    ),
    Row(
        "gql-inline-fragment",
        "graphql",
        "L",
        request(
            "POST",
            "graphql",
            {"query": "mutation { ... on Mutation { enqueuePullRequest(input: {}) { clientMutationId } } }"},
        ),
    ),
    Row(
        "gql-named-fragment",
        "graphql",
        "L",
        request("POST", "graphql", {"query": "mutation { ...Landing } " + FRAGMENT}),
    ),
    Row(
        "gql-document-in-variables", "graphql", "N", request("POST", "graphql", {"query": R, "variables": {"query": M}})
    ),
    Row(
        "gql-operationName-null-sole",
        "graphql",
        "L",
        request("POST", "graphql", {"query": LAND, "operationName": None}),
    ),
    Row(
        "gql-operationName-selects-landing",
        "graphql",
        "L",
        request("POST", "graphql", {"query": SEVERAL, "operationName": "Land"}),
    ),
    Row(
        "gql-operationName-selects-read",
        "graphql",
        "N",
        request("POST", "graphql", {"query": SEVERAL, "operationName": "Read"}),
    ),
    Row("gql-several-without-name", "graphql", "N", request("POST", "graphql", {"query": SEVERAL})),
    Row(
        "gql-operationName-not-a-string",
        "graphql",
        "N",
        request("POST", "graphql", {"query": LAND, "operationName": True}),
    ),
    Row(
        "gql-mutation-nested-in-query",
        "graphql",
        "N",
        request(
            "POST", "graphql", {"query": "query { viewer { enqueuePullRequest(input: {}) { clientMutationId } } }"}
        ),
    ),
    Row(
        "gql-subscription",
        "graphql",
        "N",
        request("POST", "graphql", {"query": "subscription { enqueuePullRequest(input: {}) { clientMutationId } }"}),
    ),
    Row("gql-batch", "graphql", "N", request("POST", "graphql", [{"query": M}])),
    Row(
        "gql-persisted-query",
        "graphql",
        "N",
        request(
            "POST",
            "graphql",
            {"operationName": "Land", "extensions": {"persistedQuery": {"version": 1, "sha256Hash": "0" * 64}}},
        ),
    ),
    Row(
        "gql-skip-literal-drops-comment",
        "graphql",
        "L",
        request("POST", "graphql", {"query": CONDITIONAL.replace("($skip: Boolean!) ", "").replace("$skip", "true")}),
    ),
    Row(
        "gql-include-false-drops-landing",
        "graphql",
        "N",
        request(
            "POST",
            "graphql",
            {"query": "mutation { enqueuePullRequest(input: {}) @include(if: false) { clientMutationId } }"},
        ),
    ),
    Row(
        "gql-skip-variable-default",
        "graphql",
        "L",
        request("POST", "graphql", {"query": CONDITIONAL.replace("Boolean!", "Boolean = true")}),
    ),
    Row(
        "gql-skip-undeclared-variable",
        "graphql",
        "N",
        request(
            "POST", "graphql", {"query": CONDITIONAL.replace("($skip: Boolean!) ", ""), "variables": {"skip": True}}
        ),
    ),
    Row(
        "gql-skip-variable-not-boolean",
        "graphql",
        "N",
        request("POST", "graphql", {"query": CONDITIONAL, "variables": {"skip": "true"}}),
    ),
    Row("gql-introspection", "graphql", "N", request("POST", "graphql", {"query": "{ __schema { types { name } } }"})),
    Row(
        "gql-root-typename",
        "graphql",
        "N",
        request(
            "POST", "graphql", {"query": "mutation { __typename enqueuePullRequest(input: {}) { clientMutationId } }"}
        ),
    ),
]


def assert_sent(context, row, before):
    sends = context.wire.sent[before:]
    assert len(sends) == 1, sends
    if row.sent is not None:
        kind = sends[0][0]
        body = sends[0][3] if kind in {"http", "http_open"} else None
        assert body == row.sent


@pytest.mark.parametrize("remaining", list(BUDGETS))
@pytest.mark.parametrize("row", ROWS, ids=[row.id for row in ROWS])
def test_request_matrix(context, row, remaining):
    seed(context, budget_rows(row.pool, remaining))
    result = outcome(row.call, context)
    if row.expected == "P:invalid_body_type" and remaining != "0":
        # Admission did not need the body; urllib itself refuses str data (Python 3.12), so nothing is sent.
        assert result == ("opener_type_error",) and context.wire.sent == []
        return
    if row.expected == "L" or remaining != "0":
        assert result[0] == "ok", result
        assert_sent(context, row, 0)
        return
    if row.expected == "N":
        assert result == ("limited", REASON[row.pool], OPEN)
    else:
        assert result == ("unprepared", row.expected.removeprefix("P:"))
    assert context.wire.sent == []


def test_matrix_has_the_required_denominator():
    ids = {row.id for row in ROWS}
    assert len(ROWS) >= 40 and len(ids) == len(ROWS)
    kinds = {row.expected.split(":")[0] for row in ROWS}
    assert kinds == {"L", "N", "P"}


# --- streams are never consumed to make a check possible -------------------------------------


@pytest.mark.parametrize("remaining", list(BUDGETS))
def test_non_replayable_stream_is_never_read_by_admission(context, remaining):
    seed(context, budget_rows("graphql", remaining))
    stream = Unseekable(envelope())
    result = outcome(opened("POST", "graphql", stream), context)
    if remaining == "0":
        assert result == ("unprepared", "body_not_replayable")
        assert stream.consumed == 0 and context.wire.sent == []
    else:
        # Admission did not need it: the opener alone read it, once and whole.
        assert result[0] == "ok" and stream.consumed == len(envelope())
        assert context.wire.sent[0][3] == envelope()


def test_seekable_body_is_restored_and_sent_whole(context):
    seed(context, budget_rows("graphql", "0"))
    stream = io.BytesIO(b"prefix" + envelope())
    stream.seek(6)
    assert outcome(opened("POST", "graphql", stream), context)[0] == "ok"
    assert context.wire.sent[0][3] == envelope()


class Counting(io.BytesIO):
    def __init__(self, data):
        super().__init__(data)
        self.read_bytes = 0

    def read(self, size=-1):
        chunk = super().read(size)
        self.read_bytes += len(chunk)
        return chunk


@pytest.mark.parametrize("remaining", list(BUDGETS))
def test_body_over_the_request_cap_is_refused_without_reading_the_rest(context, monkeypatch, remaining):
    monkeypatch.setattr(gh, "MAX_REQUEST_BYTES", 64)
    seed(context, budget_rows("graphql", remaining))
    big = envelope("query { " + "viewer { login } " * 20 + "}")
    stream = Counting(big)
    paths = [
        opened("POST", "graphql", stream),
        request("POST", "graphql", big),
        native("api", "graphql", "--input", "big.json", *TEMPLATE, files={"big.json": big}),
    ]
    for call in paths:
        result = outcome(call, context)
        assert result == ("unprepared", "body_too_large") if remaining == "0" else result[0] == "ok"
    if remaining == "0":
        assert stream.read_bytes <= 65 and stream.tell() == 0 and context.wire.sent == []
    else:
        assert len(context.wire.sent) == 3


def test_landing_flow_never_reads_a_body(context):
    """Inside a vetted landing flow the class is landing: a non-replayable body is sent unread."""
    from scripts.orchestration import merge_queue_keeper as keeper

    seed(context, budget_rows("graphql", "0"))
    stream = Unseekable(envelope(R))

    class Done(Exception):
        pass

    class Keeper:
        def branch_names(self):
            raise Done(outcome(opened("POST", "graphql", stream), context))

    with pytest.raises(Done) as done:
        keeper.run(Keeper(), Path("unused-state.json"), apply=False)
    assert done.value.args[0][0] == "ok" and context.wire.sent[0][3] == envelope(R)


# --- hold kinds -------------------------------------------------------------------------------

POOL_TRIGGERS = {
    "core": lambda client: client.request("GET", "repos/o/r/issues/1/comments"),
    "graphql": lambda client: client.request("POST", "graphql", payload={"query": R}),
}
CALLS = {
    ("core", "L", "request"): request("PUT", "repos/o/r/pulls/1/merge", {}),
    ("core", "N", "request"): request("GET", "repos/o/r/issues/1/timeline"),
    ("core", "L", "native"): native("pr", "merge", "1", "--repo", "o/r", "--auto"),
    ("core", "N", "native"): native("pr", "status"),
    ("core", "L", "http_open"): opened("PUT", "repos/o/r/pulls/1/merge", b"{}"),
    ("core", "N", "http_open"): opened("GET", "repos/o/r/issues/1", None),
    ("graphql", "L", "request"): request("POST", "graphql", {"query": M}),
    ("graphql", "N", "request"): request("POST", "graphql", {"query": R}),
    ("graphql", "L", "native"): native("api", "graphql", "-f", "query=" + M, "-F", "operationName=null", *TEMPLATE),
    ("graphql", "N", "native"): native("api", "graphql", "-f", "query=" + R, *TEMPLATE),
    ("graphql", "L", "http_open"): opened("POST", "graphql", envelope()),
    ("graphql", "N", "http_open"): opened("POST", "graphql", envelope(R)),
}


def hold_response(kind, pool, now):
    if kind == "retry_after_seconds":
        return gh.Response(429, {"retry-after": "120"}, b'{"message":"slow down"}')
    if kind == "retry_after_http_date":
        return gh.Response(403, {"retry-after": email.utils.formatdate(now + 120, usegmt=True)}, b"{}")
    if kind == "primary_reset":
        headers = {"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(OPEN), "x-ratelimit-resource": pool}
        return gh.Response(403, headers, b'{"message":"API rate limit exceeded"}')
    return gh.Response(403, {}, b'{"message":"You have exceeded a secondary rate limit."}')


def hold_expectations(hold, pool, now):
    """(what the call meeting GitHub's limit returns, what a landing call then gets, what an ordinary call gets)."""
    retry = ("retry_after", now + 120)
    return {
        "retry_after_seconds": (retry, retry, retry),
        "retry_after_http_date": (retry, retry, retry),
        "primary_reset": (("pool_exhausted", OPEN), None, (REASON[pool], OPEN)),
        "secondary_no_retry_after": (("secondary_hold", now + 60), None, ("secondary_hold", now + 60)),
    }[hold]


HOLDS = ["retry_after_seconds", "retry_after_http_date", "primary_reset", "secondary_no_retry_after"]


@pytest.mark.parametrize("remaining", list(BUDGETS))
@pytest.mark.parametrize("path", ["request", "native", "http_open"])
@pytest.mark.parametrize("kind", ["L", "N"])
@pytest.mark.parametrize("pool", ["core", "graphql"])
@pytest.mark.parametrize("hold", HOLDS)
def test_hold_matrix(context, hold, pool, kind, path, remaining):
    trigger = gh.GitHubClient(
        cache_dir=context.tmp / "cache",
        transport=lambda *args: hold_response(hold, pool, context.now),
        clock=lambda: context.now,
        env={"GH_TOKEN": TOKEN},
    )
    triggered, landing, ordinary = hold_expectations(hold, pool, context.now)
    first = POOL_TRIGGERS[pool](trigger)
    assert (first.error, first.reason, first.reset_at) == ("github_rate_limited", *triggered)
    seed(context, budget_rows(pool, remaining))
    expected = landing if kind == "L" else ordinary
    result = outcome(CALLS[(pool, kind, path)], context)
    if expected is None:
        assert result[0] == "ok", result
        assert len(context.wire.sent) == 1
    else:
        assert result == ("limited", *expected)
        assert context.wire.sent == []


@pytest.mark.parametrize("remaining", list(BUDGETS))
def test_host_rejection_sends_nothing(context, remaining):
    seed(context, budget_rows("graphql", remaining))
    with pytest.raises(ValueError, match="host mismatch"):
        context.client.request("POST", "https://example.invalid/graphql", payload={"query": M})
    for argv in (
        ["gh", "api", "https://example.invalid/graphql", "-f", "query=" + M],
        ["gh", "api", "https://example.invalid/graphql", "-f", "query=" + M, *TEMPLATE],
    ):
        result = gh.run(argv, client=context.client, capture_output=True)
        assert result.returncode == 1 and result.github_result.error == "github_invalid_command"
    assert context.wire.sent == []


@pytest.mark.parametrize("remaining", list(BUDGETS))
def test_agent_no_merge_refuses_the_merge_before_admission(context, remaining):
    seed(context, budget_rows("core", remaining))
    context.client.env = {**context.client.env, "AGENT_NO_MERGE": "1"}
    result = gh.run(["gh", "pr", "merge", "1", "--repo", "o/r", "--auto"], client=context.client, capture_output=True)
    assert result.returncode == 1 and result.github_result.error == "github_worker_write_forbidden"
    assert context.wire.sent == []


@pytest.mark.parametrize("remaining", list(BUDGETS))
def test_response_ceiling_applies_after_one_landing_send(context, remaining):
    seed(context, budget_rows("core", remaining))
    context.client.max_response_bytes = 4
    context.wire.reply = lambda: gh.Response(200, {}, b'{"merged":true}')
    result = context.client.request("PUT", "repos/o/r/pulls/1/merge", payload={})
    assert (result.status, result.value) == (413, {"message": "github_response_too_large"})
    assert len(context.wire.sent) == 1


@pytest.mark.parametrize(("remaining", "native_sends"), [("0", 0), ("4000", 1)])
def test_pr_view_404_falls_through_inside_the_guard(context, remaining, native_sends):
    """The native fall-through is admitted like any request: GitHub's 404 reported core at ``remaining``."""
    headers = {"X-RateLimit-Remaining": remaining, "X-RateLimit-Reset": str(OPEN), "X-RateLimit-Resource": "core"}
    context.wire.reply = lambda: gh.Response(404, headers, b'{"message":"Not Found"}')
    argv = ["gh", "pr", "view", "8183", "--repo", "o/r", "--json", "number"]
    result = gh.run(argv, client=context.client, capture_output=True)
    natives = [send for send in context.wire.sent if send[0] == "native"]
    assert len(natives) == native_sends
    if native_sends == 0:
        assert result.returncode == 75 and result.github_result.reason == "core_below_landing_reserve"


# --- normalization: one reading, typed provenance ------------------------------------------------


def test_one_gh_api_reading_feeds_admission_and_translation(context):
    seed(context, budget_rows("graphql", "0"))
    typed = ["api", "graphql", "-f", "query=" + CONDITIONAL, "-F", "skip=true"]
    call = gh._gh_api_call(typed[1:], stdin=None, cwd=context.tmp)
    url, body = call.build()
    assert (call.method, url) == ("POST", "graphql")
    assert json.loads(body) == {"query": CONDITIONAL, "variables": {"skip": True}}
    assert outcome(native(*typed, *TEMPLATE), context)[0] == "ok"
    # Translated: admitted from the same reading, and the wire carries exactly its body.
    raw = ["api", "graphql", "-f", "query=" + LAND, "-f", "operationName=Land", "-f", "x=1"]
    assert gh._translation_options(["gh", *raw]) is not None
    assert outcome(translated(*raw), context)[0] == "ok"
    assert context.wire.sent[-1][3] == gh._gh_api_call(raw[1:], stdin=None, cwd=None).build()[1]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("null", None),
        ("true", True),
        ("false", False),
        ("5", 5),
        ("-5", -5),
        ("+5", 5),
        ("007", 7),
        ("9223372036854775807", 9223372036854775807),
        ("9223372036854775808", "9223372036854775808"),
        ("-9223372036854775808", -9223372036854775808),
        ("0" * 30 + "1", 1),
        ("-", "-"),
        ("1.5", "1.5"),
        ("1e3", "1e3"),
        ("1_000", "1_000"),
        ("١", "١"),
        ("True", "True"),
        ("", ""),
    ],
)
def test_typed_field_values_follow_gh(value, expected):
    assert gh._gh_typed(value, lambda source: None) == expected


def test_typed_file_and_stdin_are_text_and_stdin_is_read_once(tmp_path):
    (tmp_path / "null.txt").write_text("null")
    call = gh._gh_api_call(["repos/o/r/issues", "-F", "a=@null.txt", "-F", "b=@-"], stdin=b"text", cwd=tmp_path)
    # A file holding "null" is the string "null"; raw fields never read a source.
    assert json.loads(call.build()[1]) == {"a": "null", "b": "text"}
    raw = gh._gh_api_call(["repos/o/r/issues", "-f", "a=@-", "-F", "b=@-"], stdin=b"text", cwd=tmp_path)
    assert json.loads(raw.build()[1]) == {"a": "@-", "b": "text"}
    # gh closes standard input after the first read: a second reader makes gh send nothing.
    for argv in (["-F", "b=@-", "-F", "c=@-"], ["-F", "b=@-", "--input", "-"]):
        assert gh._gh_api_call(["repos/o/r/issues", *argv], stdin=b"text", cwd=tmp_path) is None


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["-F", "a[b]=1", "-F", "a[c]=x"], {"a": {"b": 1, "c": "x"}}),
        (["-f", "l[]=1", "-f", "l[]=2"], {"l": ["1", "2"]}),
        (["-f", "l[]"], {"l": []}),
        (["-F", "l[][k]=1", "-F", "l[][k]=2"], {"l": [{"k": 1}, {"k": 2}]}),
        (["-f", "a=1", "-f", "a=2"], None),
        (["-f", "a=1", "-F", "a[b]=2"], None),
        (["-f", "novalue"], None),
    ],
)
def test_nested_fields_and_gh_refusals(argv, expected):
    call = gh._gh_api_call(["repos/o/r/issues", *argv], stdin=None, cwd=None)
    assert (None if call is None else json.loads(call.build()[1])) == expected


@pytest.mark.parametrize(
    ("argv", "method", "url"),
    [
        (["repos/o/r/issues"], "GET", "repos/o/r/issues"),
        (["repos/o/r/issues", "-f", "a=1"], "POST", "repos/o/r/issues"),
        (
            ["-X", "GET", "search/issues", "-F", "q=x y", "-F", "flag=true", "-F", "none=null"],
            "GET",
            "search/issues?flag=true&none=&q=x+y",
        ),
        (["-Xget", "search/issues?a=1", "-f", "b=2"], "GET", "search/issues?a=1&b=2"),
        (["repos/o/r/issues", "--input", "-", "-f", "a=1"], "POST", "repos/o/r/issues?a=1"),
    ],
)
def test_method_defaults_and_query_parameters_follow_gh(argv, method, url):
    call = gh._gh_api_call(argv, stdin=b"{}", cwd=None)
    assert (call.method, call.build()[0]) == (method, url)


@pytest.mark.parametrize(
    "argv",
    [
        ["repos/o/r", "--paginate", "-X", "POST"],
        ["repos/o/r", "--paginate", "--input", "x"],
        ["repos/o/r", "--slurp"],
        ["repos/o/r", "--paginate", "--slurp", "--jq", "."],
        ["repos/o/r", "--jq", ".", "--template", "x"],
        ["repos/o/r", "--unknown"],
        ["repos/o/r", "-X"],
        ["repos/o/r", "--help"],
        ["repos/o/r", "repos/o/s"],
        [],
    ],
)
def test_argv_gh_refuses_makes_no_request(argv):
    assert gh._gh_api_call(argv, stdin=None, cwd=None) is None


def test_go_json_matches_encoding_json():
    assert gh._go_json({"b": "<a&b> ", "a": [1, None, True]}) == (
        b'{"a":[1,null,true],"b":"\\u003ca\\u0026b\\u003e\\u2028"}'
    )


def test_provenance_holds_only_a_classification_length_digest_and_refusal(context):
    secret = "ghp_" + "x" * 36
    body = envelope(M.replace("PR_1", secret))
    normalized = gh._normalize("POST", "graphql", ("graphql",), body)
    record = normalized.provenance
    assert [field for field in record.__dataclass_fields__] == ["classification", "length", "digest", "refusal"]
    assert record.classification == "graphql_landing" and record.length == len(body) and secret not in repr(record)
    with pytest.raises(AssertionError, match="untyped"):
        gh._Provenance("graphql_landing; " + secret)
    with pytest.raises(AssertionError, match="untyped"):
        gh._Provenance("unprepared", refusal="github_rate_limited")
    deferred = gh._normalize("POST", "graphql", ("graphql",), gh._DeferredBody(iter([body])).capture)
    with pytest.raises(gh.GitHubUnpreparedRequest):
        deferred.inspect()
    assert deferred.provenance == gh._Provenance("unprepared", refusal="body_not_replayable")


def test_preparation_errors_are_a_closed_set():
    assert {
        "body_unreadable",
        "body_not_replayable",
        "body_too_large",
        "invalid_body_type",
    } == gh.PREPARATION_ERRORS
    assert gh.PREPARATION_ERRORS.isdisjoint(gh.REFUSAL_REASONS)
    with pytest.raises(AssertionError, match="untyped"):
        gh.GitHubUnpreparedRequest("retry_after")
    assert gh.MAX_REQUEST_BYTES == 8 * 1024 * 1024


def test_graphql_queries_are_cached_and_nothing_else_is(context):
    for payload, cacheable in (
        ({"query": R}, True),
        ({"query": "{ __schema { types { name } } }"}, True),
        ({"query": "subscription { x }"}, False),
        ({"query": M}, False),
        ({"query": "mutation { enqueuePullRequest(input: {}) @skip(if: true) { x } }"}, False),
        ([{"query": R}], False),
        ({"extensions": {"persistedQuery": {}}}, False),
    ):
        assert gh._normalize("POST", "graphql", ("graphql",), json.dumps(payload).encode()).read is cacheable
    assert gh._normalize("GET", "graphql", ("graphql",), None).read is False


# --- the installed gh 2.98.0 binary through a local recording proxy ---------------------------------


def _real_gh():
    """The installed gh executable (an ELF binary, never a shim), when it is gh 2.98."""
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / "gh"
        try:
            if not (candidate.is_file() and os.access(candidate, os.X_OK)):
                continue
            with candidate.open("rb") as handle:
                if handle.read(4) != b"\x7fELF":
                    continue
            version = subprocess.run([str(candidate), "--version"], capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            continue
        if version.stdout.startswith("gh version 2.98."):
            return str(candidate)
    return None


REAL_GH = _real_gh()


def needs_gh(test):
    """The installed gh binary, against a local proxy only: no request leaves this host."""
    return pytest.mark.live_github(pytest.mark.skipif(REAL_GH is None, reason="gh 2.98 binary not installed")(test))


class Proxy:
    """A local HTTP proxy that records each request and answers with ``reply``."""

    def __init__(self, reply=(200, {}, b'{"data":{}}')):
        self.requests, self.reply = [], reply
        proxy = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def handle_one(self):
                length = self.headers.get("Content-Length")
                if length is not None:
                    body = self.rfile.read(int(length))
                elif self.headers.get("Transfer-Encoding") == "chunked":
                    body = b""
                    while size := int(self.rfile.readline().strip(), 16):
                        body += self.rfile.read(size)
                        self.rfile.readline()
                    self.rfile.readline()
                else:
                    body = b""
                proxy.requests.append((self.command, self.path, body))
                status, headers, content = proxy.reply
                self.send_response(status)
                for name, value in headers.items():
                    self.send_header(name, value)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = handle_one

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def env(self, home):
        (home / "config").mkdir(exist_ok=True)
        address = f"http://127.0.0.1:{self.server.server_address[1]}"
        return {
            "PATH": "/usr/bin:/bin",
            "HOME": str(home),
            "GH_CONFIG_DIR": str(home / "config"),
            "GH_HOST": "github.localhost",
            "GH_ENTERPRISE_TOKEN": "synthetic",
            "GH_TOKEN": "synthetic",
            "GH_NO_UPDATE_NOTIFIER": "1",
            "HTTP_PROXY": address,
            "http_proxy": address,
        }

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def proxy():
    server = Proxy()
    yield server
    server.close()


DIFFERENTIAL = [
    (["graphql", "-f", "query=" + M, "-F", "operationName=null"], None),
    (["graphql", "-f", "query=" + M, "-f", "operationName=null"], None),
    (
        [
            "graphql",
            "-f",
            "query=" + COUNTED,
            "-F",
            "n=-5",
            "-F",
            "z=007",
            "-F",
            "long=" + "0" * 30 + "1",
            "-F",
            "big=99999999999999999999",
            "-F",
            "f=1.5",
            "-F",
            "t=true",
            "-F",
            "nil=null",
            "-f",
            "raw=null",
        ],
        None,
    ),
    (["graphql", "-F", "query=@q.graphql", "-F", "s=@-"], b"standard input"),
    (["graphql", "--input", "e.json"], None),
    (["graphql", "--input", "-"], envelope()),
    (["graphql", "-F", "x=@-", "--input", "-"], envelope()),
    (["repos/o/r/issues", "-F", "b=@-", "-F", "c=@-"], b"text"),
    (["repos/o/r/issues", "-f", "a=@-", "-F", "b=@-"], b"text"),
    (["repos/o/r/issues", "-f", "title=x", "-F", "labels[]=bug", "-F", "labels[]=ci", "-F", "meta[a]=1"], None),
    (["graphql", "-f", "query=" + M, "-F", "input[id]=X", "-f", "list[]"], None),
    (["-X", "GET", "search/issues", "-f", "q=x y", "-F", "per_page=5", "-F", "flag=true"], None),
    (["/graphql", "-f", "query=" + M, "-F", "x=1"], None),
    (["graphql", "-f", "query=<a&b> "], None),
    (["-fquery=" + M, "-iXPOST", "graphql"], None),
]


@needs_gh
@pytest.mark.parametrize(("argv", "stdin"), DIFFERENTIAL)
def test_gh_sends_exactly_what_the_normalizer_reads(tmp_path, proxy, argv, stdin):
    (tmp_path / "q.graphql").write_text(M)
    (tmp_path / "e.json").write_bytes(envelope(LAND, operationName="Land"))
    completed = subprocess.run(
        [REAL_GH, "api", *argv], input=stdin, cwd=tmp_path, env=proxy.env(tmp_path), capture_output=True, timeout=30
    )
    call = gh._gh_api_call(argv, stdin=stdin, cwd=tmp_path)
    if call is None:
        # The normalizer reads no request where gh sends none.
        assert completed.returncode != 0 and proxy.requests == []
        return
    assert completed.returncode == 0, completed.stderr
    url, body = call.build()
    [(method, path, sent)] = proxy.requests
    assert method == call.method
    assert path == "http://api.github.localhost/" + url.lstrip("/")
    assert sent == (body or b"")


@needs_gh
@pytest.mark.parametrize(
    ("argv", "landing"),
    [
        (["api", "graphql", "-f", "query=" + M, "-F", "operationName=null", *TEMPLATE], True),
        (["api", "graphql", "-f", "query=" + M, "-f", "operationName=null", *TEMPLATE], False),
        (["api", "graphql", "-f", "query=" + CONDITIONAL, "-F", "skip=true", *TEMPLATE], True),
        (["api", "graphql", "-f", "query=" + CONDITIONAL, "-F", "skip=false", *TEMPLATE], False),
    ],
)
def test_real_gh_typed_fields_end_to_end(tmp_path, proxy, argv, landing):
    """Blocker (1) with the real binary: gh's typed null and booleans decide the class."""
    environment = {**proxy.env(tmp_path), "AGENT_REAL_GH": REAL_GH}
    client = gh.GitHubClient(cache_dir=tmp_path / "cache", env=environment, clock=lambda: NOW)
    with client._db() as db:
        gh._store_budget(db, client.scope, "graphql", 0, OPEN)
    result = gh.run(["gh", *argv], client=client, runner=subprocess.run, capture_output=True)
    if landing:
        assert result.returncode == 0, result.stderr
        assert len(proxy.requests) == 1
    else:
        assert result.returncode == 75 and result.github_result.reason == "pool_exhausted"
        assert proxy.requests == []


@needs_gh
def test_real_gh_include_retry_after_is_an_authentic_hold(tmp_path):
    server = Proxy(reply=(429, {"Retry-After": "120"}, b'{"message":"slow down"}'))
    try:
        environment = {**server.env(tmp_path), "AGENT_REAL_GH": REAL_GH}
        client = gh.GitHubClient(cache_dir=tmp_path / "cache", env=environment, clock=lambda: NOW)
        argv = ["gh", "api", "--include", "graphql", "-f", "query=" + R, *TEMPLATE]
        first = gh.run(argv, client=client, runner=subprocess.run, capture_output=True)
        assert first.returncode == 75 and (first.github_result.reason, first.github_result.reset_at) == (
            "retry_after",
            NOW + 120,
        )
        landing = ["gh", "api", "graphql", "-f", "query=" + M, *TEMPLATE]
        second = gh.run(landing, client=client, runner=subprocess.run, capture_output=True)
        assert second.returncode == 75 and second.github_result.reason == "retry_after"
        assert len(server.requests) == 1
    finally:
        server.close()


@needs_gh
@pytest.mark.parametrize(
    ("command", "meaning"),
    [
        (["api"], "--field"),
        (["issue", "comment"], "--body-file"),
        (["issue", "create"], "--body-file"),
        (["issue", "edit"], "--body-file"),
        (["pr", "comment"], "--body-file"),
        (["pr", "create"], "--body-file"),
        (["pr", "edit"], "--body-file"),
        (["pr", "review"], "--body-file"),
        (["pr", "merge"], "--body-file"),
        (["release", "create"], "--notes-file"),
        (["release", "edit"], "--notes-file"),
    ],
)
def test_dash_f_has_one_meaning_per_command_family(tmp_path, command, meaning):
    assert gh._DASH_F[command[0]] == meaning
    help_text = subprocess.run(
        [REAL_GH, *command, "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        env={"PATH": "/usr/bin:/bin", "HOME": str(tmp_path)},
    ).stdout
    assert f"-F, {meaning}" in help_text
