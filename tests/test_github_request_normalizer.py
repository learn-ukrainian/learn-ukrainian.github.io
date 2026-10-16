"""One request normalizer for every GitHub transport (#10730 slice 1); no network.

A table-driven matrix: each representation of a request (``GitHubClient.request`` payloads,
``urllib`` ``Request.data``, native and translated ``gh api`` argv), each GraphQL semantic
case and each hold kind, crossed with the call's pool at remaining 0, unknown and 500. The
expected class is a literal in each row, never computed by the code under test. Admitted
rows assert one send carrying exactly the caller's bytes; refused rows assert zero sends and
the exact typed reason and reset. The gh contract is verified against the installed gh 2.98.0
binary through a local recording proxy when it is present.
"""

from __future__ import annotations

import email.utils
import hashlib
import http.server
import io
import json
import os
import subprocess
import sys
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
TYPENAME = 'mutation { __typename enqueuePullRequest(input: {pullRequestId: "PR_1"}) { clientMutationId } }'


def envelope(document=M, **fields):
    return json.dumps({"query": document, **fields}).encode()


def wire_json(payload):
    """The bytes ``GitHubClient.request`` sends for a JSON payload (its documented serialization)."""
    return json.dumps(payload, ensure_ascii=False).encode()


def go_json(value):
    """The bytes gh 2.98.0 sends for its parameters (Go ``encoding/json``: sorted, compact, HTML-safe)."""
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    for char, escape in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), (" ", "\\u2028"), (" ", "\\u2029")):
        text = text.replace(char, escape)
    return text.encode()


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
        """Send as Python's http.client does: str data is refused, a file is read block by block until empty."""
        data = request.data
        if isinstance(data, str):
            raise TypeError("POST data should be bytes, an iterable of bytes, or a file object.")
        if hasattr(data, "read"):
            blocks = []
            while block := data.read(8192):
                blocks.append(block.encode("iso-8859-1") if isinstance(block, str) else bytes(block))
            sent = b"".join(blocks)
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


@dataclass
class Native:
    """``gh <argv>`` through ``gh.run`` (``--template`` keeps a ``gh api`` out of translation)."""

    argv: tuple
    input: Any = None
    files: dict | None = None

    def __call__(self, context):
        for name, content in (self.files or {}).items():
            path = context.tmp / name
            if content == "fifo":
                os.mkfifo(path)
            else:
                path.write_bytes(content.encode() if isinstance(content, str) else content)
        return gh.run(["gh", *self.argv], client=context.client, capture_output=True, input=self.input)


def native(*argv, input=None, files=None):
    return Native(argv, input, files)


translated = native


def runs(argv):
    """The argv the native transport gives gh (#10730): a ``gh api`` command line that is neither
    paginated, verbose nor already ``--include``d (``-iXPOST``) gets ``--include`` after its last
    flag, so GitHub's status and headers come from gh's own framing; any other command is unchanged."""
    if argv[0] != "api" or {"--paginate", "--verbose", "--include", "-iXPOST"} & set(argv):
        return tuple(argv)
    return (*argv, "--include")


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
# gh reads this body itself from a source this client does not model (a pipe, a missing file, a
# repository placeholder): only the command line and standard input are what the client passes on.
GH_READS = object()


@dataclass
class Row:
    id: str
    pool: str
    expected: str  # "L" landing, "N" ordinary, "P:<reason>" refused unread when admission needs the body
    call: Any
    sent: Any  # the exact body bytes an admitted request carries (None: no body; native: what gh sends)


ROWS = [
    # GitHubClient.request payloads
    Row("request-mapping", "graphql", "L", request("POST", "graphql", {"query": M}), envelope()),
    Row("request-bytes", "graphql", "L", request("POST", "graphql", envelope()), envelope()),
    Row("request-bytearray", "graphql", "L", request("POST", "graphql", bytearray(envelope())), envelope()),
    Row("request-memoryview", "graphql", "L", request("POST", "graphql", memoryview(envelope())), envelope()),
    Row("request-bytes-read", "graphql", "N", request("POST", "graphql", envelope(R)), envelope(R)),
    # A str payload is sent as a JSON string: it executes nothing, so it is never landing.
    Row(
        "request-str-is-a-json-string",
        "graphql",
        "N",
        request("POST", "graphql", envelope().decode()),
        wire_json(envelope().decode()),
    ),
    Row(
        "rest-put-merge",
        "core",
        "L",
        request("PUT", "repos/o/r/pulls/1/merge", {"merge_method": "squash"}),
        wire_json({"merge_method": "squash"}),
    ),
    Row("rest-get-merge-shaped-url", "core", "N", request("GET", "repos/o/r/pulls/1/merge"), None),
    # urllib Request.data, through http_open
    Row("data-bytes", "graphql", "L", opened("POST", "graphql", envelope()), envelope()),
    Row("data-bytes-read", "graphql", "N", opened("POST", "graphql", envelope(R)), envelope(R)),
    Row("data-str", "graphql", "P:invalid_body_type", opened("POST", "graphql", envelope().decode()), None),
    Row("data-seekable-file", "graphql", "L", opened("POST", "graphql", lambda: io.BytesIO(envelope())), envelope()),
    Row(
        "data-seekable-file-read",
        "graphql",
        "N",
        opened("POST", "graphql", lambda: io.BytesIO(envelope(R))),
        envelope(R),
    ),
    Row(
        "data-text-file",
        "graphql",
        "L",
        opened("POST", "graphql", lambda: io.StringIO(envelope().decode())),
        envelope(),
    ),
    # A stream that reading consumes is captured once and those bytes are sent.
    Row(
        "data-non-seekable-reader",
        "graphql",
        "L",
        opened("POST", "graphql", lambda: Unseekable(envelope())),
        envelope(),
    ),
    Row("data-generator-chunks", "graphql", "L", opened("POST", "graphql", lambda: chunks(envelope())), envelope()),
    Row(
        "data-generator-chunks-read",
        "graphql",
        "N",
        opened("POST", "graphql", lambda: chunks(envelope(R))),
        envelope(R),
    ),
    Row(
        "data-list-chunks",
        "graphql",
        "L",
        opened("POST", "graphql", lambda: [envelope()[:10], b"", envelope()[10:]]),
        envelope(),
    ),
    Row(
        "data-list-chunks-read",
        "graphql",
        "N",
        opened("POST", "graphql", lambda: [envelope(R)[:5], envelope(R)[5:]]),
        envelope(R),
    ),
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
        go_json({"operationName": None, "query": M}),
    ),
    Row(
        "native-f-operationName-null-is-a-string",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + M, "-f", "operationName=null", *TEMPLATE),
        go_json({"operationName": "null", "query": M}),
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
        go_json({"operationName": "null", "query": M.replace("mutation", "mutation null")}),
    ),
    Row(
        "native-F-operationName-true",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + M, "-F", "operationName=true", *TEMPLATE),
        go_json({"operationName": True, "query": M}),
    ),
    Row(
        "native-F-operationName-int",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + M, "-F", "operationName=7", *TEMPLATE),
        go_json({"operationName": 7, "query": M}),
    ),
    Row(
        "native-F-true-skips",
        "graphql",
        "L",
        native("api", "graphql", "-f", "query=" + CONDITIONAL, "-F", "skip=true", *TEMPLATE),
        go_json({"query": CONDITIONAL, "variables": {"skip": True}}),
    ),
    Row(
        "native-F-false-keeps",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + CONDITIONAL, "-F", "skip=false", *TEMPLATE),
        go_json({"query": CONDITIONAL, "variables": {"skip": False}}),
    ),
    Row(
        "native-f-true-is-a-string",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + CONDITIONAL, "-f", "skip=true", *TEMPLATE),
        go_json({"query": CONDITIONAL, "variables": {"skip": "true"}}),
    ),
    Row(
        "native-F-positive-int",
        "graphql",
        "L",
        native("api", "graphql", "-f", "query=" + COUNTED, "-F", "n=5", *TEMPLATE),
        go_json({"query": COUNTED, "variables": {"n": 5}}),
    ),
    Row(
        "native-F-negative-int",
        "graphql",
        "L",
        native("api", "graphql", "-f", "query=" + COUNTED, "-F", "n=-5", *TEMPLATE),
        go_json({"query": COUNTED, "variables": {"n": -5}}),
    ),
    Row(
        "native-F-at-file",
        "graphql",
        "L",
        native("api", "graphql", "-F", "query=@q.graphql", *TEMPLATE, files={"q.graphql": M}),
        go_json({"query": M}),
    ),
    Row(
        "native-F-at-file-read",
        "graphql",
        "N",
        native("api", "graphql", "-F", "query=@q.graphql", *TEMPLATE, files={"q.graphql": R}),
        go_json({"query": R}),
    ),
    Row(
        "native-F-at-stdin",
        "graphql",
        "L",
        native("api", "graphql", "-F", "query=@-", *TEMPLATE, input=M.encode()),
        go_json({"query": M}),
    ),
    Row(
        "native-F-at-missing",
        "graphql",
        "P:body_unreadable",
        native("api", "graphql", "-F", "query=@missing", *TEMPLATE),
        GH_READS,
    ),
    Row(
        "native-f-at-is-literal",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=@q.graphql", *TEMPLATE, files={"q.graphql": M}),
        go_json({"query": "@q.graphql"}),
    ),
    Row(
        "native-F-placeholder-unresolved",
        "graphql",
        "N",
        native("api", "graphql", "-F", "query=" + M.replace("PR_1", "{owner}"), *TEMPLATE),
        GH_READS,
    ),
    Row(
        "native-attached-short-flag",
        "graphql",
        "L",
        native("api", "graphql", "-fquery=" + M, *TEMPLATE),
        go_json({"query": M}),
    ),
    Row(
        "native-combined-short-flags",
        "graphql",
        "L",
        native("api", "-iXPOST", "graphql", "-fquery=" + M, *TEMPLATE),
        go_json({"query": M}),
    ),
    Row(
        "native-input-file",
        "graphql",
        "L",
        native("api", "graphql", "--input", "e.json", *TEMPLATE, files={"e.json": envelope()}),
        envelope(),
    ),
    Row(
        "native-input-stdin-bytes",
        "graphql",
        "L",
        native("api", "graphql", "--input", "-", *TEMPLATE, input=envelope()),
        envelope(),
    ),
    Row(
        "native-input-stdin-text",
        "graphql",
        "L",
        native("api", "graphql", "--input", "-", *TEMPLATE, input=envelope().decode()),
        envelope(),
    ),
    # A pipe gh reads itself: what this client read from it could not be what gh reads.
    Row(
        "native-input-fifo",
        "graphql",
        "P:body_not_replayable",
        native("api", "graphql", "--input", "pipe", *TEMPLATE, files={"pipe": "fifo"}),
        GH_READS,
    ),
    Row(
        "native-input-read-field-to-url",
        "graphql",
        "N",
        native("api", "graphql", "--input", "r.json", "-f", "query=" + M, *TEMPLATE, files={"r.json": envelope(R)}),
        envelope(R),
    ),
    Row(
        "native-stdin-taken-by-field",
        "graphql",
        "N",
        native("api", "graphql", "-F", "x=@-", "--input", "-", *TEMPLATE, input=envelope()),
        None,
    ),
    Row(
        "native-explicit-get-mutation",
        "graphql",
        "N",
        native("api", "graphql", "-X", "GET", "-f", "query=" + M, *TEMPLATE),
        None,
    ),
    Row(
        "native-explicit-post-read",
        "graphql",
        "N",
        native("api", "graphql", "-X", "POST", "-f", "query=" + R, *TEMPLATE),
        go_json({"query": R}),
    ),
    Row(
        "native-duplicate-field-gh-refuses",
        "graphql",
        "N",
        native("api", "graphql", "-f", "query=" + M, "-F", "query=" + M, *TEMPLATE),
        None,
    ),
    Row(
        "native-fake-landing-headers",
        "core",
        "N",
        native("api", "repos/o/r/pulls/1/reviews", "-H", "X-Landing-Flow: merge-queue-keeper", *TEMPLATE),
        None,
    ),
    Row("native-put-merge", "core", "L", native("api", "-X", "PUT", "repos/o/r/pulls/1/merge", *TEMPLATE), None),
    # -F is a body file outside gh api: never read for admission, whatever it holds.
    Row(
        "native-issue-comment-F-body-file",
        "core",
        "N",
        native("issue", "comment", "1", "--repo", "o/r", "-F", "e.json", files={"e.json": envelope()}),
        None,
    ),
    Row(
        "native-pr-review-F-body-file",
        "core",
        "L",
        native("pr", "review", "1", "--repo", "o/r", "--comment", "-F", "body.md", files={"body.md": "x"}),
        None,
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
    Row("translated-get-reads-merge-url", "core", "N", translated("api", "repos/o/r/pulls/1/merge"), None),
]


def _semantic(row_id, expected, payload):
    """A GraphQL semantic case sent as a ``GitHubClient.request`` mapping."""
    return Row(row_id, "graphql", expected, request("POST", "graphql", payload), wire_json(payload))


ROWS += [
    _semantic(
        "gql-alias-of-landing-field",
        "L",
        {"query": "mutation { a: enqueuePullRequest(input: {}) { clientMutationId } }"},
    ),
    _semantic(
        "gql-landing-alias-on-comment",
        "N",
        {"query": "mutation { enqueuePullRequest: addComment(input: {}) { clientMutationId } }"},
    ),
    _semantic(
        "gql-inline-fragment",
        "L",
        {"query": "mutation { ... on Mutation { enqueuePullRequest(input: {}) { clientMutationId } } }"},
    ),
    _semantic("gql-named-fragment", "L", {"query": "mutation { ...Landing } " + FRAGMENT}),
    _semantic("gql-document-in-variables", "N", {"query": R, "variables": {"query": M}}),
    _semantic("gql-operationName-null-sole", "L", {"query": LAND, "operationName": None}),
    _semantic("gql-operationName-selects-landing", "L", {"query": SEVERAL, "operationName": "Land"}),
    _semantic("gql-operationName-selects-read", "N", {"query": SEVERAL, "operationName": "Read"}),
    _semantic("gql-several-without-name", "N", {"query": SEVERAL}),
    _semantic("gql-operationName-not-a-string", "N", {"query": LAND, "operationName": True}),
    _semantic(
        "gql-mutation-nested-in-query",
        "N",
        {"query": "query { viewer { enqueuePullRequest(input: {}) { clientMutationId } } }"},
    ),
    _semantic(
        "gql-subscription",
        "N",
        {"query": "subscription { enqueuePullRequest(input: {}) { clientMutationId } }"},
    ),
    Row("gql-batch", "graphql", "N", request("POST", "graphql", [{"query": M}]), wire_json([{"query": M}])),
    _semantic(
        "gql-persisted-query",
        "N",
        {"operationName": "Land", "extensions": {"persistedQuery": {"version": 1, "sha256Hash": "0" * 64}}},
    ),
    _semantic(
        "gql-skip-literal-drops-comment",
        "L",
        {"query": CONDITIONAL.replace("($skip: Boolean!) ", "").replace("$skip", "true")},
    ),
    _semantic(
        "gql-include-false-drops-landing",
        "N",
        {"query": "mutation { enqueuePullRequest(input: {}) @include(if: false) { clientMutationId } }"},
    ),
    _semantic("gql-skip-variable-default", "L", {"query": CONDITIONAL.replace("Boolean!", "Boolean = true")}),
    _semantic(
        "gql-skip-undeclared-variable",
        "N",
        {"query": CONDITIONAL.replace("($skip: Boolean!) ", ""), "variables": {"skip": True}},
    ),
    _semantic("gql-skip-variable-not-boolean", "N", {"query": CONDITIONAL, "variables": {"skip": "true"}}),
    _semantic("gql-introspection", "N", {"query": "{ __schema { types { name } } }"}),
    # The root __typename meta-field writes nothing: beside a landing mutation it changes nothing.
    _semantic("gql-root-typename", "L", {"query": TYPENAME}),
    _semantic("gql-root-typename-aliased", "L", {"query": TYPENAME.replace("__typename", "kind: __typename")}),
    _semantic("gql-root-typename-alone", "N", {"query": "mutation { __typename }"}),
    _semantic(
        "gql-typename-beside-comment",
        "N",
        {"query": 'mutation { __typename addComment(input: {subjectId: "X", body: "x"}) { clientMutationId } }'},
    ),
    # A document GitHub rejects executes nothing, so it is never landing.
    _semantic("gql-unused-variable", "N", {"query": M.replace("mutation", "mutation($x: Int)")}),
    _semantic("gql-unused-fragment", "N", {"query": M + " " + FRAGMENT}),
    _semantic("gql-undefined-variable", "N", {"query": M.replace('"PR_1"', "$x")}),
    _semantic("gql-duplicate-input-field", "N", {"query": M.replace('"PR_1"', '"PR_1", pullRequestId: "PR_2"')}),
    _semantic("gql-unparsable", "N", {"query": M[:-1]}),
]


def assert_sent(context, row):
    """One send, carrying exactly the bytes the caller's request means."""
    [send] = context.wire.sent
    if send[0] in {"http", "http_open"}:
        assert send[3] == row.sent
        return
    call = row.call
    _, argv, stdin = send
    assert argv == runs(call.argv)
    # Standard input reaches gh unchanged; gh builds the request from it and the argv.
    assert stdin == (call.input.encode() if isinstance(call.input, str) else call.input)
    if call.argv[0] == "api" and row.sent is not GH_READS:
        model = gh._gh_api_call(list(call.argv[1:]), stdin=stdin, cwd=context.tmp)
        assert (None if model is None else model.build()[1]) == row.sent


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
        assert_sent(context, row)
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
    # Every row pins what it sends: bytes, no body, or a body gh reads itself.
    assert all(row.sent is None or row.sent is GH_READS or isinstance(row.sent, bytes) for row in ROWS)


# --- bodies: captured once, whatever their size, and sent exactly --------------------------------


@pytest.mark.parametrize("remaining", list(BUDGETS))
def test_a_stream_is_read_once_and_exactly_its_bytes_are_sent(context, remaining):
    seed(context, budget_rows("graphql", remaining))
    stream = Unseekable(envelope())
    result = outcome(opened("POST", "graphql", stream), context)
    # At remaining 0 admission captures it and the opener is given the captured bytes; otherwise
    # the opener alone reads it. Either way it is read once and sent whole.
    assert result[0] == "ok" and stream.consumed == len(envelope())
    assert [send[3] for send in context.wire.sent] == [envelope()]


def test_seekable_body_is_sent_from_its_position(context):
    seed(context, budget_rows("graphql", "0"))
    stream = io.BytesIO(b"prefix" + envelope())
    stream.seek(6)
    assert outcome(opened("POST", "graphql", stream), context)[0] == "ok"
    assert context.wire.sent[0][3] == envelope()


def test_a_captured_body_goes_only_to_the_copy_the_opener_sends(context):
    """The caller's Request keeps its data and headers; the opener's copy keeps the caller's Content-Length."""
    seed(context, budget_rows("graphql", "0"))
    data, received = chunks(envelope()), []

    def opener(outgoing, **kwargs):
        received.append((outgoing, outgoing.data.read(), dict(outgoing.headers)))
        response = io.BytesIO(b'{"data":{}}')
        response.status, response.headers = 200, {}
        return response

    headers = {**AUTH, "Content-Length": str(len(envelope()))}
    original = Request("https://api.github.com/graphql", data=data, method="POST", headers=headers)
    before = dict(original.headers)
    with gh.http_open(original, opener=opener) as response:
        assert response.status == 200
    [(outgoing, body, sent_headers)] = received
    assert outgoing is not original and body == envelope()
    assert sent_headers["Content-length"] == str(len(envelope()))
    assert original.data is data and dict(original.headers) == before


class Recorded:
    """Every spool the client opens, to prove each is closed on every path."""

    def __init__(self, monkeypatch):
        self.spools, spool = [], gh._spool

        def recording():
            self.spools.append(spool())
            return self.spools[-1]

        monkeypatch.setattr(gh, "_spool", recording)


@pytest.mark.parametrize("remaining", list(BUDGETS))
def test_bodies_beyond_the_spill_threshold_are_sent_whole(context, monkeypatch, remaining):
    """The spill threshold moves a captured body to a private file; it never refuses one (#10730 blocker 1)."""
    monkeypatch.setattr(gh, "SPILL_BYTES", 64)
    recorded = Recorded(monkeypatch)
    seed(context, budget_rows("graphql", remaining))
    big = envelope(M + " " * 200)
    calls = {
        "direct": request("POST", "graphql", big),
        "urllib-bytes": opened("POST", "graphql", big),
        "urllib-seekable": opened("POST", "graphql", lambda: io.BytesIO(big)),
        "urllib-reader": opened("POST", "graphql", lambda: Unseekable(big)),
        "urllib-iterator": opened("POST", "graphql", lambda: chunks(big)),
        "native-file": native("api", "graphql", "--input", "big.json", *TEMPLATE, files={"big.json": big}),
        "native-stdin": native("api", "graphql", "--input", "-", *TEMPLATE, input=big),
    }
    for path, call in calls.items():
        before = len(context.wire.sent)
        assert outcome(call, context)[0] == "ok", path
        [send] = context.wire.sent[before:]
        if send[0] == "native":
            assert send[1] == runs(call.argv) and send[2] == call.input
        else:
            assert send[3] == big, path
    # Streams were captured only where admission needed them, then spilled, and every spool is closed.
    captured = 3 if remaining == "0" else 0
    assert len(recorded.spools) == captured and all(spool._rolled and spool.closed for spool in recorded.spools)


CAP = 8 * 1024 * 1024  # the former admission cap: a landing body one byte over it was refused (review of 55881a20)


def padded(document, size):
    """A valid request body of exactly ``size`` bytes: GraphQL whitespace pads the document."""
    return envelope(document + " " * (size - len(envelope(document))))


@pytest.mark.parametrize(
    "path", ["direct", "urllib-bytes", "urllib-reader", "urllib-iterator", "native-stdin", "native-file"]
)
def test_a_landing_body_one_byte_over_the_former_cap_is_sent_intact(context, path):
    seed(context, budget_rows("graphql", "0"))
    body = padded(M, CAP + 1)
    assert len(body) == CAP + 1
    calls = {
        "direct": request("POST", "graphql", body),
        "urllib-bytes": opened("POST", "graphql", body),
        "urllib-reader": opened("POST", "graphql", lambda: Unseekable(body)),
        "urllib-iterator": opened("POST", "graphql", lambda: chunks(body)),
        "native-stdin": native("api", "graphql", "--input", "-", *TEMPLATE, input=body),
        "native-file": native("api", "graphql", "--input", "big.json", *TEMPLATE, files={"big.json": body}),
    }
    assert outcome(calls[path], context)[0] == "ok"
    [send] = context.wire.sent
    if send[0] == "native":
        assert send[1] == runs(calls[path].argv)
        sent = send[2] if path == "native-stdin" else (context.tmp / "big.json").read_bytes()
    else:
        sent = send[3]
    assert hashlib.sha256(sent).hexdigest() == hashlib.sha256(body).hexdigest()


@pytest.mark.parametrize("path", ["direct", "urllib-reader", "native-stdin"])
def test_an_ordinary_body_over_the_former_cap_keeps_its_typed_refusal(context, path):
    seed(context, budget_rows("graphql", "0"))
    body = padded(R, CAP + 1)
    calls = {
        "direct": request("POST", "graphql", body),
        "urllib-reader": opened("POST", "graphql", lambda: Unseekable(body)),
        "native-stdin": native("api", "graphql", "--input", "-", *TEMPLATE, input=body),
    }
    assert outcome(calls[path], context) == ("limited", "pool_exhausted", OPEN)
    assert context.wire.sent == []


class Failing(io.RawIOBase):
    """A stream whose device fails after its first block."""

    def __init__(self, data):
        self.data, self.reads = data, 0

    def readable(self):
        return True

    def readinto(self, buffer):
        self.reads += 1
        if self.reads > 1:
            raise OSError("device gone")
        buffer[:10] = self.data[:10]
        return 10


def broken_producer():
    yield envelope()[:10]
    raise RuntimeError("producer failed")


@pytest.mark.parametrize(
    ("data", "reason"),
    [
        (lambda: Failing(envelope()), "body_unreadable"),
        (broken_producer, "body_unreadable"),
        (lambda: [envelope(), "text chunk"], "invalid_body_type"),
        (lambda: io.StringIO(M.replace("PR_1", "PR_☃")), "invalid_body_type"),
        (lambda: 42, "invalid_body_type"),
    ],
    ids=["read-fails", "iteration-fails", "str-chunk", "text-beyond-latin-1", "not-a-body"],
)
def test_a_body_that_cannot_be_captured_is_typed_and_sends_nothing(context, monkeypatch, data, reason):
    """Capture failure is its own outcome: never classified landing or ordinary, never sent."""
    recorded = Recorded(monkeypatch)
    seed(context, budget_rows("graphql", "0"))
    assert outcome(opened("POST", "graphql", data), context) == ("unprepared", reason)
    assert context.wire.sent == [] and all(spool.closed for spool in recorded.spools)
    normalized = gh._normalize("POST", "graphql", ("graphql",), gh._DeferredBody(data()).capture)
    with pytest.raises(gh.GitHubUnpreparedRequest):
        normalized.inspect()
    assert normalized.provenance == gh._Provenance("unprepared", refusal=reason) and normalized.call_class is None


def test_a_spool_is_closed_when_the_send_fails(context, monkeypatch):
    recorded = Recorded(monkeypatch)
    seed(context, budget_rows("graphql", "0"))

    def opener(outgoing, **kwargs):
        raise ConnectionResetError("network down")

    with pytest.raises(ConnectionResetError):
        gh.http_open(
            Request("https://api.github.com/graphql", data=chunks(envelope()), method="POST", headers=AUTH),
            opener=opener,
        )
    assert len(recorded.spools) == 1 and recorded.spools[0].closed


def test_the_spool_spills_into_an_unnamed_file_only_this_process_can_open(monkeypatch):
    import stat

    monkeypatch.setattr(gh, "SPILL_BYTES", 16)
    with gh._spool() as spool:
        spool.write(b"x" * 16)
        assert not spool._rolled
        spool.write(b"x")
        status = os.fstat(spool.fileno())
        assert spool._rolled and stat.S_IMODE(status.st_mode) == 0o600 and status.st_nlink == 0
    assert spool.closed


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
    # A one-shot iterator is captured once; its provenance is that of the captured bytes, never the bytes.
    deferred = gh._normalize("POST", "graphql", ("graphql",), gh._DeferredBody(iter([body])).capture)
    assert deferred.inspect() is True
    assert deferred.provenance == gh._Provenance(
        "graphql_landing", len(body), hashlib.sha256(body).hexdigest()
    ) and secret not in repr(deferred.provenance)
    with pytest.raises(gh.GitHubUnpreparedRequest) as refused:
        gh._DeferredBody([body, secret]).capture()
    assert secret not in str(refused.value) and secret not in repr(refused.value)


def test_preparation_errors_are_a_closed_set():
    # Size is no reason: a body is captured whatever its size (the former cap is the spill threshold).
    assert {"body_unreadable", "body_not_replayable", "invalid_body_type"} == gh.PREPARATION_ERRORS
    assert gh.PREPARATION_ERRORS.isdisjoint(gh.REFUSAL_REASONS)
    with pytest.raises(AssertionError, match="untyped"):
        gh.GitHubUnpreparedRequest("body_too_large")
    assert gh.SPILL_BYTES == 8 * 1024 * 1024 and not hasattr(gh, "MAX_REQUEST_BYTES")


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
    """A local HTTP proxy that records each request and answers with ``reply``.

    ``reply`` is ``(status, headers, body)``, or a function of the request path returning one,
    or ``None`` to drop the connection without an answer.
    """

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
                reply = proxy.reply(self.path) if callable(proxy.reply) else proxy.reply
                if reply is None:
                    self.close_connection = True
                    return
                status, headers, content = reply
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


@needs_gh
@pytest.mark.parametrize(
    "row",
    [row for row in ROWS if isinstance(row.call, Native) and row.call.argv[0] == "api" and isinstance(row.sent, bytes)],
    ids=lambda row: row.id,
)
def test_real_gh_sends_exactly_each_native_rows_bytes(tmp_path, proxy, row):
    """Every native row's pinned bytes are what the installed gh sends for that command line."""
    for name, content in (row.call.files or {}).items():
        (tmp_path / name).write_bytes(content.encode() if isinstance(content, str) else content)
    stdin = row.call.input.encode() if isinstance(row.call.input, str) else row.call.input
    completed = subprocess.run(
        [REAL_GH, *runs(row.call.argv)],
        input=stdin,
        cwd=tmp_path,
        env=proxy.env(tmp_path),
        capture_output=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    [(_, _, sent)] = proxy.requests
    assert sent == row.sent


# --- GraphQL: one parsed document, the same class for every spelling of it ------------------------

ADD_SUB_ISSUE = 'mutation { addSubIssue(input: {issueId: "I_1", subIssueId: "I_2"}) { clientMutationId } }'


@pytest.mark.parametrize(
    ("document", "landing", "read"),
    [
        ({"query": M}, True, False),
        ({"query": "\n\t" + M.replace(" ", "\n  ") + "\n"}, True, False),
        ({"variables": {}, "query": M}, True, False),
        ({"query": "# mutation\n" + R}, False, True),
        ({"query": 'query { search(query: "mutation enqueuePullRequest") { issueCount } }'}, False, True),
        ({"query": R + " " + LAND, "operationName": "Land"}, True, False),
        ({"query": R + " " + LAND, "operationName": "Read"}, False, True),
        # Spelling no keyword that writes, it can execute no write; GitHub's error answer is never cached.
        ({"query": "", "extensions": {"persistedQuery": {"version": 1}}}, False, True),
        ({"query": ADD_SUB_ISSUE}, False, False),
        ({"query": ADD_SUB_ISSUE.replace("addSubIssue", "removeSubIssue")}, False, False),
        (
            {"query": "mutation { ...F } fragment F on Mutation { a: enqueuePullRequest(input: {}) { x } __typename }"},
            True,
            False,
        ),
        (
            {
                "query": "mutation($go: Boolean = false) { enqueuePullRequest(input: {}) { x } "
                "addComment(input: {}) @include(if: $go) { x } }",
            },
            True,
            False,
        ),
        (
            {
                "query": "mutation($go: Boolean = false) { enqueuePullRequest(input: {}) { x } "
                "addComment(input: {}) @include(if: $go) { x } }",
                "variables": {"go": True},
            },
            False,
            False,
        ),
        (
            {"query": "mutation { ...F ...F } fragment F on Mutation { enqueuePullRequest(input: {}) { x } }"},
            True,
            False,
        ),
        ({"query": M + " " + M.replace("mutation", "mutation Other")}, False, False),
        ({"query": 7}, False, False),
        ({"query": M, "variables": "{}"}, False, False),
    ],
    ids=[
        "compact",
        "whitespace-variant",
        "key-order-variant",
        "keyword-in-comment",
        "keyword-in-string",
        "operationName-selects-the-mutation",
        "operationName-selects-the-read",
        "empty-query-with-extensions",
        "add-sub-issue",
        "remove-sub-issue",
        "fragment-alias-and-typename",
        "directive-default-skips-the-comment",
        "supplied-variable-overrides-the-default",
        "fragment-spread-twice",
        "anonymous-beside-named",
        "query-not-a-string",
        "variables-not-an-object",
    ],
)
def test_graphql_class_follows_the_parsed_document_only(document, landing, read):
    normalized = gh._normalize("POST", "graphql", ("graphql",), json.dumps(document).encode())
    assert (normalized.call_class == "landing", normalized.read) == (landing, read)


def test_graphql_core_is_imported_only_to_parse_a_document_that_could_write():
    """graphql-core costs about 0.1 s to import: the shim's other GitHub calls never pay it."""
    code = (
        "import sys\n"
        "from scripts.common import github_client as gh\n"
        "assert 'graphql' not in sys.modules\n"
        "assert gh._normalize('POST', 'graphql', ('graphql',), b'{\"query\":\"query { viewer { login } }\"}').read\n"
        "assert 'graphql' not in sys.modules\n"
        "gh._normalize('POST', 'graphql', ('graphql',), b'{\"query\":\"mutation { x }\"}')\n"
        "assert 'graphql' in sys.modules\n"
    )
    subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[1], check=True, timeout=60)


# --- paired requests: one operation, every representation, the same admission --------------------

GRAPHQL_OPERATIONS = {
    "enqueue": (M, True),
    "enqueue-beside-typename": (TYPENAME, True),
    "bulk-query": ('query { repository(owner: "o", name: "r") { issues(first: 100) { nodes { number } } } }', False),
    "add-sub-issue": (ADD_SUB_ISSUE, False),
    "enqueue-beside-comment": (
        M.replace("} }", '} addComment(input: {subjectId: "X", body: "x"}) { clientMutationId } }', 1),
        False,
    ),
}


def graphql_representations(document):
    body = envelope(document)
    respelled = json.dumps({"variables": {}, "query": document}, indent=2).encode()
    fields = go_json({"query": document})
    return {
        "request-mapping": (request("POST", "graphql", {"query": document}), wire_json({"query": document})),
        "request-bytes": (request("POST", "graphql", body), body),
        "request-respelled": (request("POST", "graphql", respelled), respelled),
        "urllib-bytes": (opened("POST", "graphql", body), body),
        "urllib-seekable": (opened("POST", "graphql", lambda: io.BytesIO(body)), body),
        "urllib-text": (opened("POST", "graphql", lambda: io.StringIO(body.decode())), body),
        "urllib-reader": (opened("POST", "graphql", lambda: Unseekable(body)), body),
        "urllib-iterator": (opened("POST", "graphql", lambda: chunks(body)), body),
        "urllib-list": (opened("POST", "graphql", lambda: [body[:7], body[7:]]), body),
        "native-stdin": (native("api", "graphql", "--input", "-", *TEMPLATE, input=body), body),
        "native-file": (native("api", "graphql", "--input", "op.json", *TEMPLATE, files={"op.json": body}), body),
        "native-field": (native("api", "graphql", "-f", "query=" + document, *TEMPLATE), fields),
        "native-field-file": (
            native("api", "graphql", "-F", "query=@op.graphql", *TEMPLATE, files={"op.graphql": document}),
            fields,
        ),
        "translated-field": (translated("api", "graphql", "-f", "query=" + document), fields),
        "translated-input": (translated("api", "graphql", "--input", "op.json", files={"op.json": body}), body),
    }


REST_OPERATIONS = {
    "merge": ("PUT", "repos/o/r/pulls/1/merge", ("merge_method", "squash"), True),
    "comment-write": ("POST", "repos/o/r/issues/1/comments", ("body", "x"), False),
    "issue-list": ("GET", "repos/o/r/issues?per_page=100", None, False),
}


def rest_representations(method, path, field):
    payload = None if field is None else dict([field])
    body = None if payload is None else go_json(payload)
    flags = () if field is None else ("-f", "=".join(field))
    representations = {
        "request": (request(method, path, payload), None if payload is None else wire_json(payload)),
        "urllib": (opened(method, path, body), body),
        "native": (native("api", "-X", method, path, *flags, *TEMPLATE), body),
        "translated": (translated("api", "-X", method, path, *flags), body),
    }
    if body is not None:
        representations["urllib-iterator"] = (opened(method, path, lambda: chunks(body)), body)
        representations["native-stdin"] = (
            native("api", "-X", method, path, "--input", "-", *TEMPLATE, input=body),
            body,
        )
    return representations


PAIRED = {
    (name, representation): ("graphql", landing, call, sent)
    for name, (document, landing) in GRAPHQL_OPERATIONS.items()
    for representation, (call, sent) in graphql_representations(document).items()
} | {
    (name, representation): ("core", landing, call, sent)
    for name, (method, path, field, landing) in REST_OPERATIONS.items()
    for representation, (call, sent) in rest_representations(method, path, field).items()
}
# Ordinary calls refused below each pool's reserve: core keeps 500 for landing, GraphQL 10.
REFUSES = {"core": {0, 10, 11, 499}, "graphql": {0, 10}}


def in_keeper_run(call):
    """Make ``call`` from inside the merge-queue keeper's real ``run``: a vetted landing flow."""

    def run(context):
        from scripts.orchestration import merge_queue_keeper as keeper

        class Done(Exception):
            pass

        class Keeper:
            def branch_names(self):
                raise Done(call(context))

        with pytest.raises(Done) as done:
            keeper.run(Keeper(), Path("unused-state.json"), apply=False)
        return done.value.args[0]

    return run


@pytest.mark.parametrize("remaining", [0, 10, 11, 499, 500, "unknown"], ids=str)
@pytest.mark.parametrize("flow", ["outside", "keeper-run"])
@pytest.mark.parametrize(("operation", "representation"), list(PAIRED), ids=[f"{op}:{rep}" for op, rep in PAIRED])
def test_paired_requests_admit_alike_across_representations(context, operation, representation, flow, remaining):
    """The same operation is admitted or refused alike however it is spelled, inside and outside a vetted flow."""
    pool, landing, call, sent = PAIRED[(operation, representation)]
    if remaining != "unknown":
        seed(context, [(pool, remaining, OPEN)])
    result = outcome(call if flow == "outside" else in_keeper_run(call), context)
    if landing or flow != "outside" or remaining not in REFUSES[pool]:
        assert result[0] == "ok", result
        assert_sent(context, Row(operation, pool, "L" if landing else "N", call, sent))
    else:
        assert result == ("limited", REASON[pool], OPEN)
        assert context.wire.sent == []


def test_paired_matrix_spans_every_body_representation():
    representations = {representation for _, representation in PAIRED}
    assert {"urllib-reader", "urllib-iterator", "native-stdin", "native-file", "request-respelled"} <= representations
    assert {landing for _, landing, _, _ in PAIRED.values()} == {True, False}


# --- native transport: GitHub's headers from gh's own framing ----------------------------------------

SECONDARY_LIMIT = (403, {"Retry-After": "120"}, b'{"message":"You have exceeded a secondary rate limit."}')
LANDING_ARGV = ["gh", "api", "graphql", "-f", "query=" + M, *TEMPLATE]


@needs_gh
@pytest.mark.parametrize(
    "argv",
    [
        ["api", "repos/o/r/issues", *TEMPLATE],
        ["api", "--include", "repos/o/r/issues", *TEMPLATE],
        ["api", "-i", "repos/o/r/issues", *TEMPLATE],
        ["api", "--include=true", "repos/o/r/issues", *TEMPLATE],
        ["api", "--include=false", "repos/o/r/issues", *TEMPLATE],
        ["api", "-iXGET", "repos/o/r/issues", *TEMPLATE],
        ["api", "-iXPOST", "graphql", "-fquery=" + R, *TEMPLATE],
        ["api", "repos/o/r/issues", "--jq", ".[]", "--cache", "1h"],
        ["api", "-X", "POST", "repos/o/r/issues", "-f", "title=x", "--silent", "--cache", "1h"],
    ],
    ids=["plain", "include", "i", "include-true", "include-false", "combined-iXGET", "combined-iXPOST", "jq", "silent"],
)
def test_real_gh_retry_after_holds_landing_until_it_expires(tmp_path, argv):
    """Blocker (2): the authentic Retry-After of a native run holds landing whatever the presentation flags."""
    server = Proxy(reply=SECONDARY_LIMIT)
    try:
        now = [NOW]
        environment = {**server.env(tmp_path), "AGENT_REAL_GH": REAL_GH}
        client = gh.GitHubClient(cache_dir=tmp_path / "cache", env=environment, clock=lambda: now[0])
        first = gh.run(["gh", *argv], client=client, runner=subprocess.run, capture_output=True)
        assert first.returncode == 75
        assert (first.github_result.reason, first.github_result.reset_at) == ("retry_after", NOW + 120)
        server.reply = (200, {}, b'{"data":{}}')
        now[0] = NOW + 119
        held = gh.run(LANDING_ARGV, client=client, runner=subprocess.run, capture_output=True)
        assert held.returncode == 75 and held.github_result.reason == "retry_after"
        assert len(server.requests) == 1
        now[0] = NOW + 120
        assert gh.run(LANDING_ARGV, client=client, runner=subprocess.run, capture_output=True).returncode == 0
        assert len(server.requests) == 2
    finally:
        server.close()


@needs_gh
@pytest.mark.parametrize("status", [200, 404, 204])
@pytest.mark.parametrize(
    "flags",
    [
        ("--template", "{{range .}}{{.title}}{{end}}"),
        ("--jq", ".[].title", "--cache", "1h"),
        ("--cache", "1h"),
        ("--silent", "--cache", "1h"),
        ("-X", "POST", "-f", "a=1", "--cache", "1h"),
    ],
    ids=["template", "jq", "json", "silent", "post"],
)
def test_real_gh_output_is_unchanged_by_the_added_include(tmp_path, status, flags):
    """The frame the transport adds is removed again: the caller gets gh's own output, byte for byte."""
    body = {200: b'[{"title":"HTTP/2.0 429 x\\r\\nRetry-After: 9"}]', 404: b'{"message":"Not Found"}', 204: b""}[status]
    server = Proxy(reply=(status, {"X-Ratelimit-Remaining": "4000"}, body))
    try:
        argv = ["api", "repos/o/r/issues", *flags]
        ours_home, theirs_home = tmp_path / "ours", tmp_path / "theirs"
        ours_home.mkdir()
        theirs_home.mkdir()
        environment = {**server.env(ours_home), "AGENT_REAL_GH": REAL_GH}
        client = gh.GitHubClient(cache_dir=tmp_path / "cache", env=environment, clock=lambda: NOW)
        ours = gh.run(["gh", *argv], client=client, runner=subprocess.run, capture_output=True)
        assert ours.args == ["gh", *argv] and not hasattr(ours, "github_result")
        theirs = subprocess.run([REAL_GH, *argv], env=server.env(theirs_home), capture_output=True, timeout=30)
        assert (ours.returncode, ours.stdout, ours.stderr) == (theirs.returncode, theirs.stdout, theirs.stderr)
        assert [path for _, path, _ in server.requests] == ["http://api.github.localhost/repos/o/r/issues"] * 2
    finally:
        server.close()


def _pages(final):
    """Two GitHub pages: page 1 lists an issue whose title looks like a limit response; page 2 is ``final``."""
    first = (
        200,
        {"Link": '<http://api.github.localhost/repos/o/r/issues?page=2>; rel="next"', "X-Ratelimit-Remaining": "4000"},
        b'[{"title":"HTTP/2.0 429 Spoofed\\r\\nRetry-After: 99999\\r\\n\\r\\n{}"}]',
    )
    return lambda path: final if "page=2" in path else first


@needs_gh
@pytest.mark.parametrize("render", [("--jq", ".[].title"), ("--template", "{{range .}}{{.title}}{{end}}")])
def test_real_gh_paginated_include_reads_the_failing_pages_frame(tmp_path, render):
    """gh stops at the failing page: its frame, after the rendered page text that imitates one, holds landing."""
    server = Proxy(reply=_pages((429, {"Retry-After": "30"}, b'{"message":"slow down"}')))
    try:
        environment = {**server.env(tmp_path), "AGENT_REAL_GH": REAL_GH}
        client = gh.GitHubClient(cache_dir=tmp_path / "cache", env=environment, clock=lambda: NOW)
        argv = ["gh", "api", "-i", "--paginate", "repos/o/r/issues", *render]
        result = gh.run(argv, client=client, runner=subprocess.run, capture_output=True)
        assert (result.returncode, result.github_result.reason, result.github_result.reset_at) == (
            75,
            "retry_after",
            NOW + 30,
        )
        assert gh.run(LANDING_ARGV, client=client, runner=subprocess.run, capture_output=True).returncode == 75
        assert len(server.requests) == 2
    finally:
        server.close()


@needs_gh
def test_real_gh_page_text_imitating_a_limit_never_holds_landing(tmp_path):
    """A failure with no GitHub response (the connection drops) leaves page text that imitates one unread."""
    server = Proxy(reply=_pages(None))
    try:
        environment = {**server.env(tmp_path), "AGENT_REAL_GH": REAL_GH}
        client = gh.GitHubClient(cache_dir=tmp_path / "cache", env=environment, clock=lambda: NOW)
        argv = ["gh", "api", "-i", "--paginate", "repos/o/r/issues", "--jq", ".[].title"]
        result = gh.run(argv, client=client, runner=subprocess.run, capture_output=True)
        assert result.returncode == 1 and b"Retry-After: 99999" in result.stdout
        server.reply = (200, {}, b'{"data":{}}')
        assert gh.run(LANDING_ARGV, client=client, runner=subprocess.run, capture_output=True).returncode == 0
        ordinary = ["gh", "api", "graphql", "-f", "query=" + R, *TEMPLATE]
        assert gh.run(ordinary, client=client, runner=subprocess.run, capture_output=True).returncode == 0
    finally:
        server.close()


@needs_gh
def test_real_gh_paginated_run_without_include_observes_no_headers(tmp_path):
    """Boundary (#10730 residual): gh renders paginated JSON differently with --include, so none is added.

    Its limit is then known only from gh's stderr: a synthetic hold, which never holds landing,
    and never a Retry-After this client could not see.
    """
    server = Proxy(reply=_pages((429, {"Retry-After": "30"}, b'{"message":"API rate limit exceeded"}')))
    try:
        environment = {**server.env(tmp_path), "AGENT_REAL_GH": REAL_GH}
        client = gh.GitHubClient(cache_dir=tmp_path / "cache", env=environment, clock=lambda: NOW)
        argv = ["gh", "api", "--paginate", "repos/o/r/issues", "--jq", ".[].title"]
        result = gh.run(argv, client=client, runner=subprocess.run, capture_output=True)
        assert len(server.requests) == 2 and server.requests[1][1].endswith("issues?page=2")
        assert (result.returncode, result.github_result.reason) == (75, "secondary_hold")
        server.reply = (200, {}, b'{"data":{}}')
        assert gh.run(LANDING_ARGV, client=client, runner=subprocess.run, capture_output=True).returncode == 0
    finally:
        server.close()
