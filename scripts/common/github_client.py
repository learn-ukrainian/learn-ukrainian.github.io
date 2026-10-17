"""GitHub transport: REST-first, conditional disk cache, and bounded budgets.

All GitHub I/O belongs here. Publishing admission still belongs to
``scripts.publish``; this module does not grant permission to publish.
Conditional GETs follow GitHub's documented ETag protocol. No request is retried.
Only fully modelled argv/JSON fields translate; other commands retain their
native gh semantics through the same bounded, colour-safe process transport.
Stale JSON reads require allow_stale=True; binary responses are never cached.

Every request path (REST, injected transports and native gh) is normalized once
(``_normalize``) and admitted by one decision, ``_refusal``. Only GitHub's own
Retry-After hold refuses a call that lands a PR; every local refusal is
``github_rate_limited`` (exit 75) with a typed reason. A body is read only when that
decision depends on it, whatever its size: it is captured once and exactly those bytes
are sent. One that cannot be captured is refused before any send as
``github_invalid_request`` with a typed reason, never classified by guess.
"""

from __future__ import annotations

import contextvars
import email.utils
import hashlib
import io
import json
import logging
import math
import os
import re
import sqlite3
import stat
import subprocess
import sys
import time
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from datetime import UTC
from pathlib import Path
from typing import Any
from urllib.parse import quote, quote_plus, urlencode, urlsplit

RESERVE = 10
"""GraphQL and search pools: a non-landing call is refused at or below this many remaining."""
LANDING_RESERVE = 500
"""Core pool: below this many remaining, what is left is kept for calls that land a PR."""
BUDGET_RESET_HORIZON_SECONDS = 2 * 60 * 60
"""GitHub resets a primary window within an hour. A stored primary reset further ahead than this is not a budget.

Retry-After expiries are not primary windows. :func:`_observation_reset_ignored` keeps them.
"""
MAX_BUDGET_REMAINING = 15_000
"""Inclusive ceiling for a plausible remaining count. GitHub's highest published primary limit is 15_000."""
_IMPLAUSIBLE_RESET_LOGGED = False
REFUSAL_REASONS = frozenset({"retry_after", "secondary_hold", "core_below_landing_reserve", "pool_exhausted"})
"""The closed set of reasons; every local refusal names exactly one."""
SPILL_BYTES = 8 * 1024 * 1024
"""Most bytes a spool (:func:`_spool`) keeps in memory before it moves to a private temporary file.

It never limits a request: a body of any size is captured and sent whole.
"""
PREPARATION_ERRORS = frozenset({"body_unreadable", "body_not_replayable", "invalid_body_type"})
"""The closed set of reasons a request whose admission needs its body is refused before any send."""
ANSI = re.compile(rb"\x1b\[[0-?]*[ -/]*[@-~]")
# One response's status line and headers as ``gh api --include`` frames them, within the
# limits ``http.client`` reads headers with: lines of at most 65536 bytes, at most 100 headers.
_FRAME_LINE, _FRAME_HEADERS = 65536, 100
_FRAME_BYTES = (_FRAME_HEADERS + 2) * (_FRAME_LINE + 2)


class GitHubInvalidHost(ValueError):
    """A host cannot safely identify a GitHub credential or budget scope."""


def canonical_host(value: str) -> str:
    """Canonical ASCII authority from a host or URL, without userinfo/default port.

    Reject parser/browser ambiguities before parsing can discard characters.
    Non-default ports remain part of the authority, including for GHES.
    """
    if not isinstance(value, str) or not value or "\\" in value or any(ord(c) <= 32 or ord(c) == 127 for c in value):
        raise GitHubInvalidHost("invalid GitHub host")
    try:
        parsed = urlsplit(value if "://" in value or value.startswith("//") else "//" + value)
        if not parsed.netloc.isascii():
            raise ValueError
        host = (parsed.hostname or "").lower().removesuffix(".")
        if not host or host.endswith(".") or "%" in host or any(label.startswith("xn--") for label in host.split(".")):
            raise ValueError
        port = parsed.port
    except ValueError:
        raise GitHubInvalidHost("invalid GitHub host") from None
    if ":" in host:
        host = "[" + host + "]"
    default_port = 80 if parsed.scheme == "http" else 443
    return host if port is None or port == default_port else f"{host}:{port}"


def colour_safe_environment(env=None):
    result = dict(os.environ if env is None else env)
    for key in ("FORCE_COLOR", "CLICOLOR_FORCE", "GH_FORCE_TTY"):
        result.pop(key, None)
    result.update(NO_COLOR="1", GH_PAGER="cat", GH_PROMPT_DISABLED="1")
    return result


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes


@dataclass
class Result:
    value: Any = None
    status: int = 200
    stale: bool = False
    age_seconds: float = 0
    error: str | None = None
    reset_at: int | None = None
    headers: dict[str, str] = field(default_factory=dict)
    reason: str | None = None

    def require_fresh(self):
        if self.error == "github_rate_limited" or self.stale:
            raise GitHubRateLimited(self.reset_at, self.reason)
        if self.error:
            raise RuntimeError(self.error)
        return self.value


# The most recent refusal in this context, as (reset_at, reason).
_LAST_REFUSAL = contextvars.ContextVar("github_last_refusal", default=None)


class GitHubRateLimited(RuntimeError):
    code = "github_rate_limited"

    def __init__(self, reset_at, reason=None):
        if reason is None:
            # Adapters re-raise a refusal from its reset alone; keep that refusal's reason.
            last = _LAST_REFUSAL.get()
            reason = last[1] if last is not None and last[0] == reset_at else None
        self.reset_at, self.reason = reset_at, reason
        super().__init__(f"github_rate_limited reset_at={reset_at}" + (f" reason={reason}" if reason else ""))


def _limited(reason, reset_at, **observation):
    """Build every rate-limit result this client originates; remember its reason for re-raising adapters."""
    if reason not in REFUSAL_REASONS:
        raise AssertionError(f"untyped GitHub refusal reason: {reason!r}")
    _LAST_REFUSAL.set((reset_at, reason))
    if observation.get("stale"):
        return Result(reset_at=reset_at, reason=reason, **observation)
    return Result(status=429, error="github_rate_limited", reset_at=reset_at, reason=reason)


class GitHubUnpreparedRequest(RuntimeError):
    """Admission needed a request body this client cannot read exactly; nothing was sent."""

    code = "github_invalid_request"

    def __init__(self, reason):
        if reason not in PREPARATION_ERRORS:
            raise AssertionError(f"untyped GitHub preparation error: {reason!r}")
        self.reason = reason
        super().__init__(f"github_invalid_request reason={reason}")


def _unprepared(reason):
    """The result of a request refused before any send because admission could not read its body."""
    if reason not in PREPARATION_ERRORS:
        raise AssertionError(f"untyped GitHub preparation error: {reason!r}")
    return Result(status=400, error=GitHubUnpreparedRequest.code, reason=reason)


def refusal_of(observed, *, injected=False):
    """The typed refusal a client result, completed process or process error carries, else ``None``.

    Adapters re-raise this instead of a generic failure. A command runner the caller
    injected in place of the client may only serialize the refusal (exit 75, the detail on
    stdout or stderr); that is read only when ``injected``, so an unrelated process's exit
    75 is never taken for the client's refusal.
    """
    result = observed if isinstance(observed, Result) else getattr(observed, "github_result", None)
    if isinstance(result, Result):
        return GitHubRateLimited(result.reset_at, result.reason) if result.error == "github_rate_limited" else None
    if not injected or getattr(observed, "returncode", None) != 75:
        return None
    for stream in (getattr(observed, "stdout", None), getattr(observed, "stderr", None)):
        try:
            detail = json.loads(stream)
        except (TypeError, ValueError):
            continue
        if isinstance(detail, dict) and detail.get("error") == "github_rate_limited":
            reason = detail.get("reason")
            return GitHubRateLimited(detail.get("reset_at"), reason if reason in REFUSAL_REASONS else None)
    return None


# --- admission: one decision for every request path ---------------------------------------
#
# Holds share the budget table with GitHub's pool observations. Only GitHub's own Retry-After
# holds, every pool of a credential ("retry_after"). A primary-limit 403 or 429 is a pool
# observation (remaining 0 until GitHub's reset), never a hold: ordinary calls honour it and
# landing calls do not. "secondary" is this client's own inference (gh stderr, a limit response
# without Retry-After); it never refuses a landing call.
_AUTHENTIC_HOLD = "retry_after"
_SYNTHETIC_HOLD = "secondary"
_FLOORED_POOLS = frozenset({"graphql", "search", "code_search"})


def _refusal(budgets, pools, *, call_class, now):
    """The single local admission decision of every request path; ``None`` admits.

    ``budgets`` maps one credential scope's stored resources to ``(remaining, reset)``,
    ``pools`` are the rate-limit buckets the call can spend and ``call_class`` is
    ``"landing"``, ``"exempt"`` or ``None``. The first match wins:

    1. GitHub's own Retry-After hold refuses every class: ``retry_after``;
    2. a landing or exempt call is admitted;
    3. a live synthetic or secondary hold: ``secondary_hold``;
    4. core with its window open and ``0 <= remaining < LANDING_RESERVE``: ``core_below_landing_reserve``;
    5. graphql or search with its window open and ``remaining <= RESERVE``: ``pool_exhausted``.

    An unknown or expired budget never refuses. A refusal is ``(reason, reset_at)``, the
    latest reset among the rows that refuse.
    """

    def latest(names, refuses):
        resets = [
            budgets[name][1]
            for name in names
            if name in budgets and budgets[name][1] > now and refuses(budgets[name][0])
        ]
        return max(resets, default=None)

    checks = [("retry_after", [_AUTHENTIC_HOLD], lambda _: True)]
    if call_class is None:
        checks += [
            ("secondary_hold", [_SYNTHETIC_HOLD], lambda remaining: remaining <= RESERVE),
            (
                "core_below_landing_reserve",
                ["core"] if "core" in pools else [],
                lambda remaining: 0 <= remaining < LANDING_RESERVE,
            ),
            ("pool_exhausted", sorted(_FLOORED_POOLS & set(pools)), lambda remaining: remaining <= RESERVE),
        ]
    for reason, names, refuses in checks:
        reset = latest(names, refuses)
        if reset is not None:
            return reason, reset
    return None


def _budget_reset_implausible(reset, now):
    """True when ``reset`` cannot be a live GitHub primary window relative to ``now``.

    A window lasts at most an hour. Non-finite, non-integer, non-positive, and
    far-future values are not budgets: a year-2096 reset would otherwise refuse
    until that date because an expired row is the only one admission skips.
    """
    if type(reset) is not int or reset <= 0:
        return True
    return reset > now + BUDGET_RESET_HORIZON_SECONDS


def _budget_remaining_implausible(remaining, limit):
    """True when ``remaining`` is outside the closed interval ``[0, limit]``."""
    return type(remaining) is not int or remaining < 0 or remaining > limit


def _observation_reset_ignored(resource, reset, now):
    """True when a stored or incoming reset must not act as this resource's budget.

    The primary-window horizon applies to pool observations only. GitHub's
    Retry-After expiry is the duration it named, which can outlast that window,
    so a long authentic hold is kept. A non-positive or non-integer expiry is
    still not a hold.
    """
    if resource == _AUTHENTIC_HOLD:
        return type(reset) is not int or reset <= 0
    return _budget_reset_implausible(reset, now)


def _log_implausible_reset_once(reset):
    """Debug-log the first implausible reset in this process and stay quiet after that."""
    global _IMPLAUSIBLE_RESET_LOGGED
    if _IMPLAUSIBLE_RESET_LOGGED:
        return
    _IMPLAUSIBLE_RESET_LOGGED = True
    logging.getLogger(__name__).debug("ignoring implausible GitHub budget reset: %s", reset)


def implausible_budget_rows(connection, *, now, remaining_limit=MAX_BUDGET_REMAINING):
    """Budget rows that cannot be a live GitHub observation.

    ``connection`` is only read. A row is listed when its reset is ignored
    (:func:`_observation_reset_ignored`) or its remaining falls outside
    ``[0, remaining_limit]``. A Retry-After expiry beyond the primary-window
    horizon is a live hold, not a poisoned reset.
    """
    found = []
    query = "SELECT scope, resource, remaining, reset FROM budget ORDER BY resource"
    for scope, resource, remaining, reset in connection.execute(query):
        reasons = []
        if _observation_reset_ignored(resource, reset, now):
            reasons.append("reset")
        if _budget_remaining_implausible(remaining, remaining_limit):
            reasons.append("remaining")
        if reasons:
            found.append(
                {
                    "table": "budget",
                    "scope": scope,
                    "resource": resource,
                    "remaining": remaining,
                    "reset": reset,
                    "reasons": tuple(reasons),
                }
            )
    return found


def _admission(db, scope, pools, call_class, now):
    """Apply :func:`_refusal` to the scope's stored budgets and holds."""
    names = [*pools, _SYNTHETIC_HOLD, _AUTHENTIC_HOLD]
    rows = db.execute(
        "SELECT resource,remaining,reset FROM budget WHERE scope=? AND resource IN ("
        + ",".join("?" * len(names))
        + ")",
        (scope, *names),
    ).fetchall()
    budgets = {}
    for resource, remaining, reset in rows:
        if _observation_reset_ignored(resource, reset, now):
            _log_implausible_reset_once(reset)
            continue
        budgets[resource] = (remaining, reset)
    return _refusal(budgets, pools, call_class=call_class, now=now)


def _admit(db, scope, request, now):
    """Admit one normalized request (:func:`_normalize`): ``None`` or a ``(reason, reset)`` refusal.

    The decision is :func:`_refusal`'s. A body is read only when that decision depends on it:
    an ordinary call would be refused (steps 3-5) where a landing one would not, and neither
    the request's own shape nor a vetted landing flow has decided its class. A body that cannot
    then be read exactly raises :class:`GitHubUnpreparedRequest`; it is never guessed ordinary.
    """
    if request.inspect is None:
        return _admission(db, scope, request.pools, request.call_class, now)
    refusal = _admission(db, scope, request.pools, None, now)
    if refusal is None or refusal[0] == "retry_after":
        return refusal
    return None if request.inspect() else refusal


def _retry_after_expiry(value, now):
    """Expiry of GitHub's ``Retry-After`` (delay-seconds or HTTP-date, RFC 9110 §10.2.3), else ``None``."""
    if value is None:
        return None
    try:
        seconds = float(value)
    except ValueError:
        try:
            when = email.utils.parsedate_to_datetime(value)
        except (TypeError, ValueError, IndexError):
            return None
        return int((when if when.tzinfo else when.replace(tzinfo=UTC)).timestamp())
    return int(now + seconds) if math.isfinite(seconds) and seconds >= 0 else None


def _budget_headers(headers):
    """GitHub's ``(remaining, reset)`` from lower-cased response headers, else ``None``."""
    try:
        return int(headers["x-ratelimit-remaining"]), int(headers["x-ratelimit-reset"])
    except (KeyError, TypeError, ValueError):
        return None


def _limit_hold(response, now):
    """The hold GitHub's limit response asks for: ``(holds, reset, reason)``, else ``None``.

    Every request path that sees GitHub's status and headers decides through this. Only its
    ``Retry-After`` is a hold, on every pool of the credential. A primary-limit 403 or 429
    (remaining ``0`` with GitHub's reset) holds nothing: the caller stores that remaining and
    reset as the pool's budget, which ordinary calls honour and landing calls do not. Any other
    limit response is this client's inference: a synthetic hold that never refuses landing.
    """
    h = {key.lower(): value for key, value in response.headers.items()}
    if not (
        response.status == 429
        or (
            response.status == 403
            and (h.get("x-ratelimit-remaining") == "0" or "retry-after" in h or b"rate limit" in response.body.lower())
        )
    ):
        return None
    retry = _retry_after_expiry(h.get("retry-after"), now)
    if retry is not None:
        return [_AUTHENTIC_HOLD], retry, "retry_after"
    budget = _budget_headers(h)
    if budget is not None and budget[0] == 0:
        return [], budget[1], "pool_exhausted"
    return [_SYNTHETIC_HOLD], (budget[1] if budget is not None else None) or int(now + 60), "secondary_hold"


# --- landing classification -----------------------------------------------------------------

_REPOSITORY_PATH = r"repos/[^/]+/[^/]+/"
# Writes that land a PR, and the budget and credential calls that are exempt. A read is
# never landing by its URL: it is landing only inside a vetted landing operation.
_CLASSIFIED_REST = tuple(
    (method, re.compile(pattern), call_class)
    for method, pattern, call_class in (
        ("PUT", _REPOSITORY_PATH + r"pulls/\d+/merge", "landing"),
        ("PUT", _REPOSITORY_PATH + r"pulls/\d+/update-branch", "landing"),
        ("POST", _REPOSITORY_PATH + r"pulls/\d+/reviews", "landing"),
        ("POST", _REPOSITORY_PATH + r"pulls/\d+/reviews/\d+/events", "landing"),
        ("POST", _REPOSITORY_PATH + r"actions/runs/\d+/rerun-failed-jobs", "landing"),
        ("POST", _REPOSITORY_PATH + r"actions/jobs/\d+/rerun", "landing"),
        ("POST", _REPOSITORY_PATH + r"check-runs/\d+/rerequest", "landing"),
        ("POST", _REPOSITORY_PATH + r"statuses/[^/]+", "landing"),
        ("GET", r"rate_limit", "exempt"),
        ("POST", r"app/installations/\d+/access_tokens", "exempt"),
        ("DELETE", r"installation/token", "exempt"),
    )
)
# Merge, update-branch, review, merge-queue and auto-merge mutations.
_LANDING_MUTATIONS = frozenset(
    {
        "mergePullRequest",
        "updatePullRequestBranch",
        "addPullRequestReview",
        "submitPullRequestReview",
        "enqueuePullRequest",
        "dequeuePullRequest",
        "enablePullRequestAutoMerge",
        "disablePullRequestAutoMerge",
    }
)
_ROOT_TYPES = {"query": "Query", "mutation": "Mutation", "subscription": "Subscription"}
_CONDITIONS = frozenset({"skip", "include"})
# Every GraphQL validation rule (September 2025, §5) that needs no schema, as graphql-core
# implements it. Operation selection and root field collection rely on them; a document they
# reject executes nothing on GitHub, so it is never landing.
_DOCUMENT_RULES = (
    "ExecutableDefinitionsRule",
    "LoneAnonymousOperationRule",
    "UniqueOperationNamesRule",
    "UniqueFragmentNamesRule",
    "KnownFragmentNamesRule",
    "NoUnusedFragmentsRule",
    "NoFragmentCyclesRule",
    "UniqueArgumentNamesRule",
    "UniqueInputFieldNamesRule",
    "UniqueVariableNamesRule",
    "NoUndefinedVariablesRule",
    "NoUnusedVariablesRule",
    "UniqueDirectivesPerLocationRule",
)
_GRAPHQL = {}


class _Undecided(ValueError):
    """Which root fields of the selected GraphQL operation execute cannot be decided."""


def _graphql():
    """graphql-core's language and validation API, imported once on first use (it is not cheap to import)."""
    if not _GRAPHQL:
        import graphql
        from graphql import language, validation
        from graphql.utilities import get_operation_ast

        # Only schema-free rules run, so a schema with nothing in it suffices.
        schema = graphql.GraphQLSchema(
            query=graphql.GraphQLObjectType("Query", {"_": graphql.GraphQLField(graphql.GraphQLBoolean)})
        )
        _GRAPHQL.update(
            language=language,
            error=graphql.GraphQLError,
            select=get_operation_ast,
            validate=lambda document: validation.validate(
                schema, document, [getattr(validation, rule) for rule in _DOCUMENT_RULES]
            ),
        )
    return _GRAPHQL


def _graphql_operation(query, operation_name=None, variables=None):
    """``(operation type, root fields)`` of the operation a GraphQL request executes, else ``None``.

    graphql-core parses the document. The operation is selected as the specification's
    GetOperation does (``operationName``, else the sole operation) once every schema-free
    validation rule holds (``_DOCUMENT_RULES``); its root fields are then collected as
    CollectFields does: fragment spreads and inline fragments on the root type expand, and
    ``@skip``/``@include`` resolve from literals, ``variables`` and the operation's defaults.
    Aliases, arguments, strings and comments never name a field. The fields are ``None`` when
    which ones execute cannot be decided (a fragment on another type, or a condition that is not
    a declared ``Boolean`` value). A document that does not parse or validate, or selects no
    operation, is ``None``. One that never spells ``mutation`` or ``subscription`` can execute
    nothing but a query, so it is a query without being parsed.
    """
    if not isinstance(query, str) or not (operation_name is None or isinstance(operation_name, str)):
        return None
    if "mutation" not in query and "subscription" not in query:
        return "query", None
    graphql = _graphql()
    ast = graphql["language"]
    try:
        document = ast.parse(query, no_location=True)
        if graphql["validate"](document):
            return None
    except (graphql["error"], RecursionError):
        return None
    operation = graphql["select"](document, operation_name)
    if operation is None:
        return None
    kind = operation.operation.value
    root, fields = _ROOT_TYPES[kind], []
    fragments = {
        definition.name.value: definition
        for definition in document.definitions
        if isinstance(definition, ast.FragmentDefinitionNode)
    }
    declared = {definition.variable.name.value: definition for definition in operation.variable_definitions or ()}
    supplied = variables if isinstance(variables, dict) else {}

    def condition(value):
        """The Boolean an ``if:`` argument coerces to: a literal, or a declared Boolean variable's value."""
        if isinstance(value, ast.BooleanValueNode):
            return value.value
        definition = declared.get(value.name.value) if isinstance(value, ast.VariableNode) else None
        if definition is None:
            raise _Undecided
        # A variable in a Boolean! position: declared Boolean!, or Boolean with a default.
        non_null = isinstance(definition.type, ast.NonNullTypeNode)
        named = definition.type.type if non_null else definition.type
        default = definition.default_value
        if (
            not isinstance(named, ast.NamedTypeNode)
            or named.name.value != "Boolean"
            or not (non_null or default is not None)
        ):
            raise _Undecided
        name = value.name.value
        if name in supplied:
            flag = supplied[name]
        elif isinstance(default, ast.BooleanValueNode):
            flag = default.value
        else:
            raise _Undecided
        if not isinstance(flag, bool):
            raise _Undecided
        return flag

    def executes(directives):
        """Whether a selection with these directives executes (CollectFields' @skip and @include)."""
        result = True
        for directive in directives or ():
            name = directive.name.value
            if name in _CONDITIONS:
                arguments = {argument.name.value: argument.value for argument in directive.arguments or ()}
                if set(arguments) != {"if"}:
                    raise _Undecided
                flag = condition(arguments["if"])
                result = result and flag is (name == "include")
        return result

    def collect(selection_set, visited):
        for selection in selection_set.selections:
            if not executes(selection.directives):
                continue
            if isinstance(selection, ast.FieldNode):
                fields.append(selection.name.value)
            elif isinstance(selection, ast.InlineFragmentNode):
                if selection.type_condition is not None and selection.type_condition.name.value != root:
                    raise _Undecided
                collect(selection.selection_set, visited)
            elif selection.name.value not in visited:
                visited.add(selection.name.value)
                fragment = fragments[selection.name.value]
                # @skip and @include never apply to a fragment definition: GitHub rejects the document.
                if fragment.type_condition.name.value != root or any(
                    directive.name.value in _CONDITIONS for directive in fragment.directives or ()
                ):
                    raise _Undecided
                collect(fragment.selection_set, visited)

    try:
        # Nor to an operation.
        if any(directive.name.value in _CONDITIONS for directive in operation.directives or ()):
            raise _Undecided
        collect(operation.selection_set, set())
    except (_Undecided, RecursionError):
        return kind, None
    return kind, fields


def _graphql_request(document):
    """``(kind, landing)`` of the GraphQL request a decoded JSON body makes.

    GraphQL over HTTP: an object whose ``query`` is the one executable document, an optional
    ``operationName`` (absent or null selects a sole operation) and ``variables`` (an object).
    kind is the selected operation's type; ``"batch"`` for a JSON array of requests;
    ``"persisted"`` for an object with no document whose extensions name a persisted query;
    ``"opaque"`` for anything else no operation can be selected from. A document inside
    variables, extensions or a string never executes. Only a selected mutation whose every
    executing root field is a landing mutation is landing; the root ``__typename`` meta-field
    writes nothing, so beside landing mutations it changes nothing.
    """
    if isinstance(document, list):
        return "batch", False
    if not isinstance(document, dict):
        return "opaque", False
    query, variables = document.get("query"), document.get("variables")
    if query is None:
        extensions = document.get("extensions")
        return ("persisted" if isinstance(extensions, dict) and "persistedQuery" in extensions else "opaque"), False
    if not (variables is None or isinstance(variables, dict)):
        return "opaque", False
    operation = _graphql_operation(query, document.get("operationName"), variables)
    if operation is None:
        return "opaque", False
    kind, fields = operation
    writes = {field for field in fields or () if field != "__typename"}
    return kind, kind == "mutation" and bool(writes) and writes <= _LANDING_MUTATIONS


def _reject_constant(name):
    raise ValueError(f"not JSON: {name}")


def _json_body(data):
    """The JSON value a request body's exact bytes encode (strict UTF-8, no NaN or Infinity), else ``None``."""
    try:
        return json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None


def _rest_class(method, path):
    """``"landing"`` for a REST write that lands a PR, ``"exempt"`` for a budget or credential call, else ``None``."""
    return next(
        (
            call_class
            for verb, pattern, call_class in _CLASSIFIED_REST
            if method == verb and isinstance(path, str) and pattern.fullmatch(path)
        ),
        None,
    )


# --- the request normalizer: one interpretation of a request for every transport ------------

_CLASSIFICATIONS = frozenset(
    {
        "rest",
        "rest_landing",
        "rest_exempt",
        "graphql_get",
        "graphql_query",
        "graphql_mutation",
        "graphql_landing",
        "graphql_subscription",
        "graphql_batch",
        "graphql_persisted",
        "graphql_opaque",
        "uninspected",
        "unprepared",
        "command",
        "invalid",
    }
)
# A body gh fills from repository context (a placeholder in a typed field): its bytes are
# gh's to compute, so it can never establish landing.
_UNRESOLVED_BODY = object()


@dataclass(frozen=True)
class _Provenance:
    """How a request was classified. Only these four fields: never a header, token, body,
    document, variable, path or argv, so the record can neither leak nor correlate them."""

    classification: str
    length: int | None = None
    digest: str | None = None
    refusal: str | None = None

    def __post_init__(self):
        if self.classification not in _CLASSIFICATIONS or not (
            self.refusal is None or self.refusal in PREPARATION_ERRORS
        ):
            raise AssertionError("untyped GitHub request provenance")


@dataclass(eq=False)
class _Request:
    """One request as admission sees it, whatever transport sends it (see :func:`_normalize`).

    ``call_class`` is ``"landing"``, ``"exempt"`` or ``None``; ``read`` marks a cacheable read;
    ``inspect`` is set only while the class still depends on an unread body: it reads the body
    and answers whether it lands a PR, or raises :class:`GitHubUnpreparedRequest`.
    """

    method: str
    path: str | None
    pools: tuple
    call_class: str | None
    read: bool = False
    inspect: Any = None
    provenance: _Provenance = _Provenance("uninspected")

    def classify(self, body):
        """Classify a GraphQL POST body: whether it lands a PR.

        ``body`` is the exact bytes sent, ``None`` for none, or a zero-argument capture of them. A
        capture that fails raises :class:`GitHubUnpreparedRequest`: the request is then neither
        landing nor ordinary, and its provenance records the typed reason.
        """
        try:
            data = body() if callable(body) else body
        except GitHubUnpreparedRequest as refused:
            self.provenance = _Provenance("unprepared", refusal=refused.reason)
            raise
        known = isinstance(data, bytes)
        kind, landing = _graphql_request(_json_body(data) if known else None)
        self.provenance = _Provenance(
            "graphql_landing" if landing else "graphql_" + kind,
            len(data) if known else None,
            hashlib.sha256(data).hexdigest() if known else None,
        )
        return landing


def _normalize(method, path, pools, body=None):
    """The one interpretation of a request that admission, caching and every transport share.

    ``path`` is the canonical resource path (:func:`_canonical_endpoint`). ``body`` is the
    exact bytes sent, ``None`` for none, or a zero-argument capture of them that admission calls
    only if its decision depends on the body (:func:`_admit`). The class comes from the
    request's own shape (a REST landing or exempt call, or a GraphQL POST whose selected
    operation is a landing mutation), else from a vetted landing flow; a read is never landing
    by its URL. A GraphQL request is a cacheable read only when it selects a query.
    """
    method = method.upper()
    flow = "landing" if _landing_flow() else None
    if path != "graphql":
        shape = _rest_class(method, path)
        provenance = _Provenance("rest_" + shape if shape else "rest")
        return _Request(method, path, tuple(pools), shape or flow, method == "GET", provenance=provenance)
    if method != "POST":
        # GraphQL over GET never executes a mutation (GraphQL over HTTP); it is never cached.
        return _Request(method, path, tuple(pools), flow, provenance=_Provenance("graphql_get"))
    request = _Request(method, path, tuple(pools), flow)
    if callable(body):
        if flow is None:
            request.inspect = lambda: request.classify(body)
        return request
    request.call_class = "landing" if request.classify(body) else flow
    request.read = request.provenance.classification == "graphql_query"
    return request


def _payload_bytes(payload):
    """The exact bytes :meth:`GitHubClient.request` sends for ``payload``: bytes-like data as given, else its JSON."""
    if payload is None:
        return None
    if isinstance(payload, (bytes, bytearray, memoryview)):
        return bytes(payload)
    return json.dumps(payload, ensure_ascii=False).encode()


def _spool():
    """A private spool: up to ``SPILL_BYTES`` in memory, then a temporary file no other process can open.

    ``tempfile`` creates that file with mode 0600 and never names it (or unlinks it at once), in
    the fleet scratch root (:func:`scripts.common.scratch.ensure_scratch_root`), never the cache:
    closing the spool, on any path, removes every byte.
    """
    import tempfile

    from scripts.common.scratch import ensure_scratch_root

    return tempfile.SpooledTemporaryFile(max_size=SPILL_BYTES, mode="w+b", dir=ensure_scratch_root())


def _http_client_blocks(data):
    """The byte blocks Python's ``http.client`` sends for urllib ``data`` that is not bytes-like.

    As Python 3.12 to 3.14 send them: a file object from its current position, block by block
    until a block is empty (a text file encoded ISO-8859-1); any other iterable chunk by chunk,
    empty chunks skipped. Each block must then be bytes-like. ``str`` and other values urllib
    rejects are ``invalid_body_type``; a read or iteration that fails is ``body_unreadable``.
    """
    if hasattr(data, "read"):
        text = isinstance(data, io.TextIOBase)

        def reads():
            while block := data.read(8192):
                yield block.encode("iso-8859-1") if text else block

        source = reads()
    elif isinstance(data, str):
        raise GitHubUnpreparedRequest("invalid_body_type")
    else:
        try:
            source = iter(data)
        except TypeError:
            raise GitHubUnpreparedRequest("invalid_body_type") from None
    while True:
        try:
            block = next(source)
            if not block:
                continue
        except StopIteration:
            return
        except UnicodeEncodeError:
            raise GitHubUnpreparedRequest("invalid_body_type") from None
        except Exception:
            raise GitHubUnpreparedRequest("body_unreadable") from None
        try:
            yield memoryview(block).tobytes()
        except TypeError:
            raise GitHubUnpreparedRequest("invalid_body_type") from None


class _DeferredBody:
    """A ``urllib.request.Request`` body: its opener sends it, unless admission needed its bytes.

    Admission reads it only through :meth:`capture`, exactly once, into a spool (:func:`_spool`);
    the opener is then given those bytes (:meth:`request_for`), never the consumed original.
    Whatever its size or representation, what is sent is what was classified.
    """

    def __init__(self, data):
        self.data, self.spool = data, None

    def capture(self):
        """The exact bytes urllib sends for this body (bytes-like data whole, else :func:`_http_client_blocks`)."""
        if self.spool is None:
            if not hasattr(self.data, "read") and not isinstance(self.data, str):
                with suppress(TypeError):
                    # Sent as it is: there is nothing to replay.
                    return memoryview(self.data).tobytes()
            spool = _spool()
            try:
                for block in _http_client_blocks(self.data):
                    spool.write(block)
            except BaseException:
                spool.close()
                raise
            self.spool = spool
        self.spool.seek(0)
        return self.spool.read()

    def request_for(self, request):
        """The request the opener sends: ``request`` itself, or a copy whose body is the captured bytes.

        The copy keeps every attribute and header of ``request``, a caller's ``Content-Length``
        included, and leaves ``request`` unchanged.
        """
        if self.spool is None:
            return request
        import copy

        outgoing = copy.copy(request)
        outgoing.headers, outgoing.unredirected_hdrs = dict(request.headers), dict(request.unredirected_hdrs)
        lengths = [
            (headers, headers["Content-length"])
            for headers in (outgoing.headers, outgoing.unredirected_hdrs)
            if "Content-length" in headers
        ]
        self.spool.seek(0)
        outgoing.data = self.spool  # the setter drops a Content-Length: restore the caller's
        for headers, value in lengths:
            headers["Content-length"] = value
        return outgoing

    def close(self):
        if self.spool is not None:
            self.spool.close()


# The current landing operation, opened only by this module's vetted sites.
_LANDING_FLOW = contextvars.ContextVar("github_landing_flow", default=None)
_THIS_MODULE = os.path.realpath(__file__)
_REPOSITORY = Path(__file__).resolve().parents[2]
# Vetted landing entry points outside this module, by repository file and function. Every
# request made while one runs on the current thread belongs to its landing flow, and the
# declaration ends when the function returns. No tag, flag, header or environment value a
# caller passes can add to this list; only an edit here can.
_LANDING_ENTRY_POINTS = {
    ("scripts/orchestration/merge_queue_keeper.py", "run"): "merge-queue-keeper",
    ("scripts/fleet_comms/review_publisher.py", "fetch_pr_head_sha"): "verdict-publication",
    ("scripts/fleet_comms/review_publisher.py", "execute_publication"): "verdict-publication",
    ("scripts/fleet_comms/review_publisher.py", "publish_sealed_verdict"): "verdict-publication",
    ("scripts/review/record_cf_verdict.py", "record"): "verdict-publication",
}
# The publisher's ``publish`` (wrapped by rate_limited_command) and its verbs that land a PR:
# such a verb's readiness and recovery reads belong to it.
_PUBLISHER_ENTRY_POINT = ("scripts/publish/github.py", "publish")
_PUBLISHER_LANDING_VERBS = frozenset(
    {"pr-merge", "pr-update-branch", "pr-review", "run-rerun", "commit-status", "pr-dequeue", "pr-disarm"}
)
_ENTRY_POINT_CODE = {
    (os.path.realpath(_REPOSITORY / path), name): flow for (path, name), flow in _LANDING_ENTRY_POINTS.items()
}
_ENTRY_POINT_NAMES = frozenset(name for _, name in _LANDING_ENTRY_POINTS)
_VETTED_CODE = {}


def _code_identity(code):
    """``(real absolute file, function name)`` of a code object; relative files have none."""
    filename = code.co_filename
    return (os.path.realpath(filename), code.co_qualname) if os.path.isabs(filename) else None


def _landing_flow():
    """The vetted landing operation the current call belongs to, else ``None``.

    This module opened one, or a vetted entry point's frame is executing on this thread.
    Work handed to another thread is not landing.
    """
    flow = _LANDING_FLOW.get()
    frame = sys._getframe(1)
    while flow is None and frame is not None:
        code = frame.f_code
        if code.co_qualname in _ENTRY_POINT_NAMES:
            if code not in _VETTED_CODE:
                _VETTED_CODE[code] = _ENTRY_POINT_CODE.get(_code_identity(code))
            flow = _VETTED_CODE[code]
        frame = frame.f_back
    return flow


def _landing_operation(flow):
    """Run a block as landing flow ``flow``; ``None`` opens nothing and an outer flow stays.

    Only this module's vetted sites open one; a caller anywhere else is refused.
    """
    if (_code_identity(sys._getframe(1).f_code) or ("",))[0] != _THIS_MODULE:
        raise PermissionError("landing operations open only inside the GitHub client")

    @contextmanager
    def opened():
        token = _LANDING_FLOW.set(flow) if flow is not None and _LANDING_FLOW.get() is None else None
        try:
            yield
        finally:
            if token is not None:
                _LANDING_FLOW.reset(token)

    return opened()


def _cache_directory():
    """Use this module's primary checkout, or no disk cache when unresolved.

    Read the checkout's own Git markers so a caller's cwd and repository-local
    Git environment (including a push hook's GIT_DIR) cannot redirect writes.
    """
    override = os.environ.get("LU_GITHUB_CACHE_DIR")
    if override:
        path = Path(override)
        if path.exists() and not os.access(path, os.W_OK):
            return None
        return path
    try:
        root = Path(__file__).resolve().parents[2]
        marker = root / ".git"
        if marker.is_file():
            content = marker.read_text().strip()
            if not content.startswith("gitdir: ") or not content[8:]:
                return None
            marker = (root / content[8:]).resolve()
            common = marker / "commondir"
            if common.is_file():
                content = common.read_text().strip()
                if not content:
                    return None
                marker = (marker / content).resolve()
        if marker.name == ".git" and marker.is_dir() and (marker / "HEAD").is_file():
            candidate = marker.parent / "batch_state" / "github-client"
            if candidate.exists():
                if not os.access(candidate, os.W_OK):
                    return None
            elif not os.access(marker.parent, os.W_OK):
                return None
            return candidate
    except (OSError, ValueError, RuntimeError):
        pass
    return None


_STATUS_LINE = re.compile(rb"HTTP/[0-9]+(?:\.[0-9]+)? ([0-9]{3})(?: .*)?")
_HEADER_NAME = re.compile(rb"[!#$%&'*+.^_`|~0-9A-Za-z-]+")


def _frame(raw, start=0):
    """``(response, end)`` of the one response ``gh api --include`` frames at ``start``, else ``None``.

    gh 2.98.0 writes the status line (``<proto> <status>``) and a newline, each header as
    ``Name: value`` and CRLF, then an empty line; the body follows. A line that is not a header,
    a line over ``_FRAME_LINE`` bytes or more than ``_FRAME_HEADERS`` headers is not gh's frame.
    Colour codes are ignored. The response's body is everything after the frame.
    """
    position, status, headers, count = start, None, {}, 0
    while True:
        newline = raw.find(b"\n", position, position + _FRAME_LINE + 1)
        if newline < 0 or count > _FRAME_HEADERS:
            return None
        line = ANSI.sub(b"", raw[position:newline]).removesuffix(b"\r")
        position = newline + 1
        if status is None:
            match = _STATUS_LINE.fullmatch(line)
            if match is None:
                return None
            status = int(match[1])
        elif not line:
            return Response(status, headers, raw[position:]), position
        else:
            name, colon, value = line.partition(b":")
            if not colon or not _HEADER_NAME.fullmatch(name):
                return None
            headers[name.decode().lower()] = value.strip().decode("latin-1")
            count += 1


def parse_http(raw):
    """The response ``gh api --include`` printed for one request: the frame at its start (:func:`_frame`)."""
    framed = _frame(raw)
    if framed is None:
        raise RuntimeError("GitHub transport omitted response headers")
    return framed[0]


def _cached_value(cached):
    return cached[0] if json.loads(cached[1]).get("_github_binary") else json.loads(cached[0])


def _store_budget(db, scope, resource, remaining, reset, now=None):
    """Record one observation.

    An implausible primary-window reset is not written. GitHub's Retry-After
    expiry is not that window, so a hold longer than it is kept. A stored row
    the reader ignores loses to a later plausible observation: the upsert used
    to require ``excluded.reset >= budget.reset``, and a year-2096 reset then
    blocked every healthy write. The extra ``WHERE`` terms are that ignore
    rule (:func:`_observation_reset_ignored`) applied to the stored row.
    """
    if now is None:
        now = time.time()
    if _observation_reset_ignored(resource, reset, now):
        _log_implausible_reset_once(reset)
        return
    db.execute(
        """INSERT INTO budget VALUES(?,?,?,?)
        ON CONFLICT(scope,resource) DO UPDATE SET
        remaining=CASE WHEN excluded.reset=budget.reset THEN min(budget.remaining,excluded.remaining) ELSE excluded.remaining END,
        reset=excluded.reset
        WHERE excluded.reset>=budget.reset
           OR typeof(budget.reset)!='integer'
           OR budget.reset<=0
           OR (budget.resource!=? AND budget.reset>?)""",
        (scope, resource, remaining, reset, _AUTHENTIC_HOLD, now + BUDGET_RESET_HORIZON_SECONDS),
    )


def _store_cache(db, scope, key, body, headers, at):
    db.execute(
        """INSERT INTO cache VALUES(?,?,?,?,?)
        ON CONFLICT(scope,key) DO UPDATE SET body=excluded.body,headers=excluded.headers,at=excluded.at
        WHERE excluded.at>=cache.at""",
        (scope, key, body, json.dumps(headers), at),
    )


class _Kept:
    """Standard output kept in a spool: with a ``limit``, at most ``limit + 1`` bytes of body.

    When the output is ``framed`` (``gh api --include``), its frame is kept whole up to its empty
    line (at most ``_FRAME_BYTES``) and the limit counts the body after it. The rest is dropped.
    """

    def __init__(self, output, limit, framed):
        self.output, self.room = output, None if limit is None else limit + 1
        self.frame = bytearray() if framed and limit is not None else None

    def write(self, data):
        if self.frame is not None:
            start = max(0, len(self.frame) - 2)
            self.frame += data
            ends = [
                found + size
                for found, size in ((self.frame.find(b"\n\n", start), 2), (self.frame.find(b"\n\r\n", start), 3))
                if found >= 0
            ]
            if not ends and len(self.frame) <= _FRAME_BYTES:
                self.output.write(data)
                return
            # The frame ends in this block; with no end within the frame limit, it is not gh's frame.
            head = len(data) - (len(self.frame) - min(ends, default=len(self.frame)))
            self.output.write(data[:head])
            data, self.frame = data[head:], None
        if self.room is None:
            self.output.write(data)
        elif self.room:
            self.output.write(data[: self.room])
            self.room -= min(len(data), self.room)


def _exchange(child, input, kept, deadline, timeout):
    """``communicate()``, with standard output written through ``kept`` (:class:`_Kept`): its standard error.

    Output past what ``kept`` keeps is still read, so the process never blocks on a full pipe.
    """
    import select
    import selectors

    errors, pending = [], memoryview(input or b"")
    with selectors.DefaultSelector() as selector:
        if child.stdin is not None:
            if pending:
                selector.register(child.stdin, selectors.EVENT_WRITE)
            else:
                child.stdin.close()
        selector.register(child.stdout, selectors.EVENT_READ)
        selector.register(child.stderr, selectors.EVENT_READ)
        while selector.get_map():
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                raise subprocess.TimeoutExpired(child.args, timeout)
            for key, _events in selector.select(remaining):
                if key.fileobj is child.stdin:
                    try:
                        pending = pending[os.write(key.fd, pending[: select.PIPE_BUF]) :]
                    except BrokenPipeError:
                        pending = pending[:0]
                    if not pending:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                    continue
                data = os.read(key.fd, 32768)
                if not data:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                elif key.fileobj is child.stderr:
                    errors.append(data)
                else:
                    kept.write(data)
    return b"".join(errors)


def _transport_process(command, *, input, env, cwd, timeout, limit=None, framed=False, **_kwargs):
    """Bound one CLI process and its descendants without polling or retrying.

    Standard output passes through one spool (:func:`_spool`); with a response ``limit`` at
    most ``limit + 1`` bytes of body are kept (:class:`_Kept`), and under the limit they are
    exactly what the process wrote. Signals are forwarded to the process group, which is killed
    only on a timeout or an exception, never after a completed wait.
    """
    import signal
    import threading

    deadline = None if timeout is None else time.monotonic() + timeout
    with (
        _spool() as output,
        subprocess.Popen(
            command,
            stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=cwd,
            start_new_session=True,
        ) as child,
    ):
        previous = {}

        def forward(signum, _frame):
            with suppress(ProcessLookupError):
                os.killpg(child.pid, signum)

        if threading.current_thread() is threading.main_thread():
            previous = {
                signum: signal.signal(signum, forward) for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
            }
        try:
            try:
                error = _exchange(child, input, _Kept(output, limit, framed), deadline, timeout)
                try:
                    child.wait(None if deadline is None else max(0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired:
                    raise subprocess.TimeoutExpired(command, timeout) from None
            except BaseException:
                # The process is not yet reaped, so its group cannot have been reused.
                with suppress(ProcessLookupError):
                    os.killpg(child.pid, signal.SIGKILL)
                child.wait()
                raise
            output.seek(0)
            return subprocess.CompletedProcess(command, child.returncode, output.read(), error)
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)


class GitHubClient:
    def __init__(
        self,
        *,
        cache_dir=None,
        env=None,
        cwd=None,
        transport=None,
        runner=None,
        clock=time.time,
        max_response_bytes=None,
        allow_stale=False,
    ):
        self.env = colour_safe_environment(env)
        self.cwd = cwd
        self.transport = transport
        self.runner = runner
        self.clock = clock
        self.allow_stale = allow_stale
        if max_response_bytes is not None and (type(max_response_bytes) is not int or max_response_bytes < 0):
            raise ValueError("invalid GitHub response byte limit")
        self.max_response_bytes = max_response_bytes
        self._configure_host(canonical_host(self.env.get("GH_HOST", "github.com")))
        self.cache_dir = Path(cache_dir) if cache_dir is not None else _cache_directory()
        self._memory_db = None

    def _configure_host(self, host):
        """Select credentials and scope from an authority already canonicalised at entry."""
        self.host = host
        self.env = {**self.env, "GH_HOST": host}
        # A digest isolates credentials without storing credentials or account IDs.
        credential = (
            self.env.get("GH_TOKEN") or self.env.get("GITHUB_TOKEN")
            if self.host == "github.com" or self.host.endswith(".ghe.com")
            else self.env.get("GH_ENTERPRISE_TOKEN") or self.env.get("GITHUB_ENTERPRISE_TOKEN")
        )
        if credential:
            credential = re.sub(r"^(?:Bearer|token)\s+", "", credential, flags=re.IGNORECASE)
        if not credential:
            config = Path(
                self.env.get("GH_CONFIG_DIR")
                or str(Path(self.env.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")) / "gh")
            )
            try:
                credential = hashlib.sha256((config / "hosts.yml").read_bytes()).hexdigest()
            except OSError:
                credential = "unconfigured-cli"
        self.scope = hashlib.sha256((self.host + "\0" + credential).encode()).hexdigest()

    @contextmanager
    def _db(self):
        for attempt in range(2):
            path = ":memory:"
            if self.cache_dir is not None:
                try:
                    self.cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
                    candidate = self.cache_dir / "cache.sqlite3"
                    if candidate.exists() and not os.access(candidate, os.W_OK):
                        raise OSError("cache database is read-only")
                    path = candidate
                except OSError:
                    self.cache_dir = None
                    path = ":memory:"
            try:
                db = self._memory_db if self._memory_db is not None else sqlite3.connect(path, timeout=5)
                if self.cache_dir is None:
                    self._memory_db = db
                else:
                    with suppress(OSError):
                        os.chmod(path, 0o600)
                db.execute(
                    "CREATE TABLE IF NOT EXISTS cache (scope TEXT, key TEXT, body BLOB, headers TEXT, at REAL, PRIMARY KEY(scope,key))"
                )
                db.execute(
                    "CREATE TABLE IF NOT EXISTS budget (scope TEXT, resource TEXT, remaining INTEGER, reset INTEGER, PRIMARY KEY(scope,resource))"
                )
                if self.cache_dir is not None:
                    db.execute(
                        "INSERT OR REPLACE INTO budget (scope, resource, remaining, reset) VALUES ('__probe__', '__probe__', 0, 0)"
                    )
                    db.execute("DELETE FROM budget WHERE scope='__probe__'")
                break
            except (sqlite3.OperationalError, sqlite3.DatabaseError, OSError):
                if self.cache_dir is not None:
                    if "db" in locals() and db is not self._memory_db:
                        with suppress(Exception):
                            db.close()
                    self.cache_dir = None
                    if attempt == 0:
                        continue
                raise
        try:
            with db:
                yield db
        finally:
            if self.cache_dir is not None:
                db.close()

    def _send(self, method, endpoint, headers, body, timeout):
        if self.transport:
            response = self.transport(method, endpoint, headers, body, timeout)
            return self._bounded_response(response)
        executable = self.env.get("AGENT_REAL_GH", "gh")
        if self.runner is None:
            from scripts.opsec.prepublish import PublishBlocked, real_gh

            try:
                executable = real_gh({**self.env, "AGENT_ORIGINAL_PATH": self.env.get("PATH", os.defpath)})
            except PublishBlocked:
                return Response(599, {}, b'{"message":"github_transport_unavailable"}')
        command = [executable, "api", "--include", "--method", method, endpoint]
        if self.host != "github.com":
            command.extend(["--hostname", self.host])
        for name, value in headers.items():
            command.extend(["-H", f"{name}: {value}"])
        if body is not None:
            command.extend(["--input", "-"])
        executor = self.runner or _transport_process
        # The response ceiling bounds the body; its frame comes first (:func:`_frame`).
        bounds = {"limit": self.max_response_bytes, "framed": True} if executor is _transport_process else {}
        proc = executor(
            command,
            **bounds,
            input=body,
            capture_output=True,
            env=self.env,
            cwd=self.cwd,
            timeout=timeout,
            check=False,
        )
        raw = proc.stdout.encode() if isinstance(proc.stdout, str) else proc.stdout or b""
        # Injected existing runners can supply plain JSON; real transports must
        # provide the HTTP status and budget headers.
        if self.runner and not ANSI.sub(b"", raw).startswith(b"HTTP/"):
            return self._bounded_response(Response(200 if proc.returncode == 0 else 500, {}, raw))
        framed = _frame(raw)
        if framed is None:
            return Response(599, {}, b'{"message":"github_transport_unavailable"}')
        return self._bounded_response(framed[0])

    def _bounded_response(self, response):
        if self.max_response_bytes is not None and len(response.body) > self.max_response_bytes:
            return Response(413, response.headers, b'{"message":"github_response_too_large"}')
        return response

    def request(
        self,
        method,
        endpoint,
        *,
        payload=None,
        timeout=30,
        fresh=False,
        allow_stale=None,
        headers=None,
        raw_response=False,
    ):
        method = method.upper()
        allow_stale = self.allow_stale if allow_stale is None else allow_stale
        host_class, resource_path = _canonical_endpoint(endpoint, self.host)
        if host_class == "rejected":
            raise ValueError("GitHub endpoint host mismatch")
        # A body the opener sends itself (http_open) is read only if admission needs it.
        deferred_body = payload.capture if isinstance(payload, _DeferredBody) else None
        raw = None if deferred_body else _payload_bytes(payload)
        graphql = resource_path == "graphql"
        resource = _endpoint_bucket(resource_path)
        normalized = _normalize(method, resource_path, (resource,), deferred_body or raw)
        key = hashlib.sha256(
            (
                method
                + "\0"
                + endpoint
                + "\0"
                + json.dumps(headers or {}, sort_keys=True)
                + ("raw" if raw_response else "json")
            ).encode()
            + (raw or b"")
        ).hexdigest()
        cacheable = (
            normalized.read
            and not raw_response
            and not any(
                name.lower() == "accept" and value == "application/octet-stream"
                for name, value in (headers or {}).items()
            )
            and not re.search(r"/(?:releases/assets/\d+|artifacts/\d+/zip)$", resource_path)
        )
        now = self.clock()
        try:
            with self._db() as db:
                cached = (
                    db.execute(
                        "SELECT body,headers,at FROM cache WHERE scope=? AND key=? AND (? IS NULL OR length(body)<=?)",
                        (self.scope, key, self.max_response_bytes, self.max_response_bytes),
                    ).fetchone()
                    if cacheable
                    else None
                )
                if not cacheable or (cached and json.loads(cached[1]).get("_github_binary")):
                    cached = None
                refusal = _admit(db, self.scope, normalized, now)
        except GitHubUnpreparedRequest as refused:
            return _unprepared(refused.reason)

        def deferred(reason, reset):
            if allow_stale and cached and not fresh:
                return _limited(
                    reason,
                    reset,
                    value=_cached_value(cached),
                    stale=True,
                    age_seconds=max(0, now - cached[2]),
                    headers=json.loads(cached[1]),
                )
            return _limited(reason, reset)

        if refusal is not None:
            return deferred(*refusal)
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", **(headers or {})}
        if cached and method == "GET":
            old_headers = json.loads(cached[1])
            if old_headers.get("etag"):
                headers["If-None-Match"] = old_headers["etag"]
        response = self._send(method, endpoint, headers, raw, timeout)
        h = {k.lower(): v for k, v in response.headers.items()}
        reset = None
        for persist_attempt in range(2):
            try:
                with self._db() as db:
                    budget = _budget_headers(h)
                    if budget is not None:
                        remaining, reset = budget
                        _store_budget(
                            db, self.scope, h.get("x-ratelimit-resource", resource), remaining, reset, now=now
                        )
                    limit = _limit_hold(response, now)
                    if limit is not None:
                        holds, reset, reason = limit
                        for hold in holds:
                            _store_budget(db, self.scope, hold, 0, reset, now=now)
                        return deferred(reason, reset)
                    if response.status == 304:
                        if not cached:
                            return Result(status=304, error="github_cache_miss", headers=h)
                        # 304 is authoritative freshness; its remaining header is used,
                        # never decremented locally.
                        h = {**json.loads(cached[1]), **h}
                        db.execute(
                            "UPDATE cache SET at=?,headers=? WHERE scope=? AND key=? AND at<=?",
                            (now, json.dumps(h), self.scope, key, now),
                        )
                        return Result(_cached_value(cached), status=304, headers=h)
                    if 200 <= response.status < 300 and (
                        raw_response or headers.get("Accept") == "application/octet-stream"
                    ):
                        return Result(response.body, status=response.status, headers=h)
                    try:
                        value = json.loads(response.body) if response.body else None
                    except ValueError:
                        return Result(
                            response.body,
                            status=response.status,
                            error=None if 200 <= response.status < 300 else "github_http_error",
                            headers=h,
                        )
                    if (
                        graphql
                        and isinstance(value, dict)
                        and any(
                            e.get("type") in {"RATE_LIMIT", "RATE_LIMITED"}
                            for e in _graphql_errors(value)
                            if isinstance(e, dict)
                        )
                    ):
                        reset = reset or int(now + 60)
                        _store_budget(db, self.scope, resource, 0, reset, now=now)
                        return deferred("pool_exhausted", reset)
                    if graphql and isinstance(value, dict) and value.get("errors"):
                        return Result(value, status=response.status, error="github_graphql_error", headers=h)
                    if not 200 <= response.status < 300:
                        return Result(
                            value, status=response.status, error="github_http_error", reset_at=reset, headers=h
                        )
                    if resource_path == "rate_limit" and isinstance(value, dict):
                        for name, rate in value.get("resources", {}).items():
                            if (
                                isinstance(rate, dict)
                                and type(rate.get("remaining")) is int
                                and type(rate.get("reset")) is int
                            ):
                                _store_budget(db, self.scope, name, rate["remaining"], rate["reset"], now=now)
                    if cacheable:
                        _store_cache(db, self.scope, key, response.body, h, now)
                    else:
                        # Any write can affect list/detail cache entries. Retain them
                        # for stale status, but never treat them as fresh without GET.
                        pass
                break
            except (sqlite3.OperationalError, sqlite3.DatabaseError, OSError):
                if self.cache_dir is not None:
                    self.cache_dir = None
                    if persist_attempt == 0:
                        continue
                try:
                    value = json.loads(response.body) if response.body else None
                except ValueError:
                    value = response.body
                return Result(
                    value,
                    status=response.status,
                    error=None if 200 <= response.status < 300 else "github_http_error",
                    reset_at=reset,
                    headers=h,
                )
        return Result(value, status=response.status, headers=h)


def _api_hosts(host):
    """Hosts whose absolute URLs are this client's own API endpoints."""
    host = canonical_host(host)
    return {"api.github.com", "uploads.github.com", "github.com"} if host == "github.com" else {host}


def _canonical_endpoint(endpoint, host="github.com"):
    """Return host admission class and normalised path; only ``None`` is unknown.

    Both transports refuse foreign or ambiguous absolute URLs. API host
    identity uses the same boundary as credentials and budget scopes.
    """
    if endpoint is None:
        return "unknown", None
    # Reject controls before splitting queries/fragments or URL parsing can discard them.
    # Keep the existing leading-space refusal; query-value spaces remain valid.
    if any(ord(char) < 32 or ord(char) == 127 for char in endpoint) or endpoint.startswith(" "):
        return "rejected", endpoint
    # gh accepts leading slashes and bare x:y as relative endpoint paths.
    # Only an initial scheme selects a host; query and fragment text never do.
    absolute = re.match(r"[A-Za-z][A-Za-z0-9+.-]*://", endpoint) is not None
    endpoint_path = re.split(r"[?#]", endpoint, maxsplit=1)[0]
    if not absolute:
        return "relative", endpoint_path.lstrip("/")
    try:
        parsed = urlsplit(endpoint_path)
        hostname = canonical_host(endpoint_path)
        if parsed.scheme not in {"http", "https"} or hostname not in _api_hosts(host):
            return "rejected", endpoint
    except ValueError:
        return "rejected", endpoint
    path = parsed.path.lstrip("/")
    # gh sends absolute URLs unchanged; GHES uses /api/v3/ for REST
    # and /api/graphql for GraphQL. Never strip these on public hosts.
    if hostname not in _api_hosts("github.com"):
        if path.startswith("api/v3/"):
            path = path.removeprefix("api/v3/")
        elif path == "api/graphql":
            path = "graphql"
    return "api", path


def _resource_path(endpoint, host="github.com"):
    """Compatibility view of the shared endpoint canonicalizer's resource path."""
    return _canonical_endpoint(endpoint, host)[1]


def _endpoint_bucket(resource_path):
    """Rate-limit bucket of a normalised path; interior and trailing segments never select one."""
    if resource_path == "graphql":
        return "graphql"
    if resource_path == "search/code":
        return "code_search"
    return "search" if resource_path.startswith("search/") else "core"


def _options(args, *, valued_flags=None, canonicalize_hosts=False):
    options, positional = {}, []
    valued = {
        "--repo",
        "-R",
        "--json",
        "--jq",
        "-q",
        "--template",
        "--state",
        "--head",
        "--base",
        "--limit",
        "-L",
        "--search",
        "--label",
        "--author",
        "--assignee",
        "--branch",
        "--event",
        "--workflow",
        "--status",
        "--created",
        "--commit",
        "--job",
        "--pattern",
        "-p",
        "--output",
        "-O",
        "--dir",
        "-D",
        "--method",
        "-X",
        "--input",
        "--header",
        "-H",
        "--field",
        "-F",
        "--raw-field",
        "-f",
        "--hostname",
        "-t",
        "--cache",
        "--preview",
        "--title",
        "--body",
        "--body-file",
        "--match-head-commit",
        "--subject",
        "--comment",
        "--reason",
        "--ref",
        "--name",
        "--color",
        "--description",
        "--milestone",
        "--add-label",
        "--remove-label",
        "--target",
        "--notes-file",
        "-s",
        "-B",
        "-l",
        "-S",
        "-A",
        "-a",
        "-w",
        "-b",
        "-e",
        "-c",
    }
    if valued_flags is not None:
        valued = valued_flags
    iterator = iter(enumerate(args))
    for index, arg in iterator:
        if arg == "--":
            positional.extend(value for _, value in iterator)
            break
        if arg.startswith("-"):
            flag, eq, value = arg.partition("=")
            if not eq and len(flag) > 2 and flag[:2] in valued:
                flag, value = flag[:2], flag[2:]
            elif not eq and flag in valued:
                value_index, value = next(iterator, (None, True))
            elif not eq:
                value = True
            if canonicalize_hosts and flag == "--hostname":
                value = canonical_host(value)
                if eq:
                    args[index] = flag + "=" + value
                else:
                    args[value_index] = value
            options.setdefault(flag, []).append(value)
        else:
            positional.append(arg)
    return options, positional


def _opt(options, *keys, default=None):
    return next((options[k][-1] for k in keys if k in options), default)


def _repo(options, client):
    repo = _opt(options, "--repo", "-R") or client.env.get("GH_REPO") or client.env.get("GITHUB_REPOSITORY")
    if repo:
        return repo.removeprefix("github.com/")
    from scripts.opsec.gh_snapshot import repository

    value = repository(Path(client.cwd or Path.cwd()), client.env)
    if value == "unknown":
        raise ValueError("GitHub repository unresolved")
    return value.split("/", 1)[1]


def _next_link(headers):
    return next((m.group(1) for m in re.finditer(r'<([^>]+)>;\s*rel="next"', headers.get("link", ""))), None)


def _pages(client, endpoint, *, timeout, fresh, paginate, limit=None, items=lambda value: value):
    pages = []
    count = 0
    for _ in range(100):
        result = client.request("GET", endpoint, timeout=timeout, fresh=fresh)
        if result.error:
            return result
        pages.append(result)
        if limit is not None:
            count += len(items(result.value))
            if count >= limit:
                return pages
        endpoint = _next_link(result.headers) if paginate else None
        if not endpoint:
            return pages
    return Result(error="github_pagination_limit")


def _merge_observation(result, *observations):
    for other in observations:
        result.stale |= other.stale
        result.age_seconds = max(result.age_seconds, other.age_seconds)
        if other.reset_at is not None:
            result.reset_at = other.reset_at
        if other.reason is not None:
            result.reason = other.reason
    return result


def _project(row, kind):
    value = dict(row)
    for old, new in {
        "html_url": "url",
        "node_id": "id",
        "created_at": "createdAt",
        "updated_at": "updatedAt",
        "closed_at": "closedAt",
        "merged_at": "mergedAt",
        "head_sha": "headSha",
        "head_branch": "headBranch",
        "display_title": "displayTitle",
        "run_number": "number",
        "database_id": "databaseId",
        "tag_name": "tagName",
        "target_commitish": "targetCommitish",
    }.items():
        if old in row:
            value[new] = row[old]
    value["databaseId"] = row.get("id")
    if "changed_files" in row:
        value["changedFiles"] = row["changed_files"]
    if kind == "comment":
        value.update(author=row.get("user"), authorAssociation=row.get("author_association"))
    if kind in {"pr", "issue"}:
        value["state"] = "MERGED" if row.get("merged_at") else str(row.get("state", "")).upper()
        value["author"] = row.get("user")
        value["labels"] = [
            {
                "id": label.get("node_id", ""),
                "name": label.get("name", ""),
                "description": label.get("description") or "",
                "color": label.get("color", ""),
            }
            for label in row.get("labels", [])
        ]
    if kind == "pr":
        head, base = row.get("head") or {}, row.get("base") or {}
        value.update(
            isDraft=row.get("draft"),
            headRefOid=head.get("sha"),
            headRefName=head.get("ref"),
            baseRefOid=base.get("sha"),
            baseRefName=base.get("ref"),
            merged=bool(row.get("merged_at")),
            isCrossRepository=(head.get("repo") or {}).get("full_name") != (base.get("repo") or {}).get("full_name"),
            autoMergeRequest=row.get("auto_merge"),
            mergeable="MERGEABLE"
            if row.get("mergeable") is True
            else "CONFLICTING"
            if row.get("mergeable") is False
            else "UNKNOWN",
        )
        value["mergeCommit"] = (
            {"oid": row["merge_commit_sha"]} if row.get("merged_at") and row.get("merge_commit_sha") else None
        )
        value["mergeStateStatus"] = {
            "clean": "CLEAN",
            "blocked": "BLOCKED",
            "behind": "BEHIND",
            "dirty": "DIRTY",
            "unstable": "UNSTABLE",
            "draft": "DRAFT",
        }.get(row.get("mergeable_state"), "UNKNOWN")
    if kind == "run":
        value["workflowName"] = row.get("name")
        value["workflowDatabaseId"] = row.get("workflow_id")
        value["startedAt"] = row.get("run_started_at")
        value["attempt"] = row.get("run_attempt")
    if kind == "release":
        value["assets"] = [
            {**asset, "url": asset.get("browser_download_url"), "size": asset.get("size")}
            for asset in row.get("assets", [])
        ]
    return value


def _read_command(client, kind, action, options, positional, *, timeout, fresh):
    repo = (
        positional[0].removeprefix("https://github.com/").removeprefix("github.com/").rstrip("/")
        if kind == "repo" and positional
        else _repo(options, client)
    )
    root = f"repos/{repo}"
    fields = str(_opt(options, "--json", default="")).split(",")
    number = positional[0] if positional else None
    if number and "/" in number and re.search(r"/(pull|issues)/\d+", number):
        number = number.rstrip("/").split("/")[-1]
    query = {"per_page": 100}
    for flag, parameter in {
        "--state": "state",
        "--base": "base",
        "--event": "event",
        "--branch": "branch",
        "--commit": "head_sha",
        "--status": "status",
        "--created": "created",
    }.items():
        if flag in options:
            query[parameter] = _opt(options, flag)
    if query.get("state") == "merged":
        query["state"] = "closed"
    if "--head" in options:
        head = _opt(options, "--head")
        query["head"] = head if ":" in head else repo.split("/")[0] + ":" + head
    limit = int(_opt(options, "--limit", "-L", default=30))
    if limit <= 0:
        raise ValueError("invalid GitHub list limit")
    if action == "list":
        query["per_page"] = min(limit, 100)
    if kind == "pr" and action in {"view", "checks", "diff"}:
        if not number or not str(number).isdigit():
            head = (
                number
                or subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=client.cwd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=True,
                ).stdout.strip()
            )
            found = client.request(
                "GET",
                root + "/pulls?" + urlencode({"state": "all", "head": repo.split("/")[0] + ":" + head}),
                timeout=timeout,
                fresh=fresh,
            )
            if found.error or not found.value:
                return found if found.error else Result(status=404, error="github_pr_not_found")
            number = str(found.value[0]["number"])
        result = client.request("GET", f"{root}/pulls/{number}", timeout=timeout, fresh=fresh)
        if result.error:
            return result
        value = _project(result.value, "pr")
        if action == "diff":
            pages = _pages(
                client, f"{root}/pulls/{number}/files?per_page=100", timeout=timeout, fresh=fresh, paginate=True
            )
            if isinstance(pages, Result):
                return pages
            files = [f for page in pages for f in page.value]
            if "--name-only" in options:
                value = "\n".join(f["filename"] for f in files)
            else:
                diff = client.request(
                    "GET",
                    f"{root}/pulls/{number}",
                    headers={"Accept": "application/vnd.github.diff"},
                    timeout=timeout,
                    fresh=fresh,
                )
                if diff.error:
                    return diff
                pages.append(diff)
                value = diff.value
            _merge_observation(result, *pages)
        if action == "checks" or "statusCheckRollup" in fields:
            checks = client.request(
                "GET", f"{root}/commits/{value['headRefOid']}/check-runs?per_page=100", timeout=timeout, fresh=fresh
            )
            if checks.error:
                return checks
            rows = checks.value.get("check_runs", [])
            if checks.value.get("total_count", 0) > len(rows):
                return Result(error="github_checks_incomplete")
            status = client.request(
                "GET", f"{root}/commits/{value['headRefOid']}/status?per_page=100", timeout=timeout, fresh=fresh
            )
            if status.error:
                return status
            if status.value.get("total_count", 0) > len(status.value.get("statuses", [])):
                return Result(error="github_statuses_incomplete")
            rollup = [
                {
                    "__typename": "CheckRun",
                    "name": r.get("name"),
                    "status": str(r.get("status", "")).upper(),
                    "conclusion": str(r.get("conclusion") or "").upper(),
                    "detailsUrl": r.get("html_url"),
                    "startedAt": r.get("started_at"),
                    "completedAt": r.get("completed_at"),
                }
                for r in rows
            ]
            rollup.extend(
                {
                    "__typename": "StatusContext",
                    "context": r.get("context"),
                    "state": str(r.get("state", "")).upper(),
                    "targetUrl": r.get("target_url"),
                }
                for r in status.value.get("statuses", [])
            )
            value["statusCheckRollup"] = rollup
            _merge_observation(result, checks, status)
            if action == "checks":
                value = [
                    {
                        "name": r.get("name") or r.get("context"),
                        "state": r.get("conclusion") or r.get("state") or r.get("status"),
                        "bucket": "pass"
                        if (r.get("conclusion") or r.get("state")) in {"SUCCESS", "NEUTRAL", "SKIPPED"}
                        else "pending"
                        if (r.get("status") != "COMPLETED" and r.get("state") in {None, "PENDING"})
                        else "fail",
                    }
                    for r in rollup
                ]
    elif kind in {"pr", "issue"} and action in {"view", "list"}:
        endpoint = root + ("/pulls" if kind == "pr" else "/issues")
        endpoint += "/" + str(number) if action == "view" else "?" + urlencode(query)
        searching = action == "list" and "--search" in options
        if searching:
            terms = [f"repo:{repo}", "is:pr" if kind == "pr" else "is:issue", _opt(options, "--search")]
            state = _opt(options, "--state", default="open")
            if state != "all":
                terms.append("is:merged" if state == "merged" else f"state:{state}")
            terms.extend("label:" + json.dumps(label) for label in options.get("--label", []))
            endpoint = "search/issues?" + urlencode({"q": " ".join(terms), "per_page": 100})

        def matching(value):
            rows = value["items"] if searching else value
            if kind == "issue":
                rows = [r for r in rows if "pull_request" not in r]
            if _opt(options, "--state") == "merged" and not searching:
                rows = [r for r in rows if r.get("merged_at")]
            return rows

        pages = _pages(
            client,
            endpoint,
            timeout=timeout,
            fresh=fresh,
            paginate=action == "list",
            limit=limit if action == "list" else None,
            items=matching,
        )
        if isinstance(pages, Result):
            return pages
        result = pages[0]
        if action == "list":
            if searching:
                if any(p.value.get("incomplete_results") for p in pages):
                    return Result(error="github_search_incomplete")
                rows = [r for page in pages for r in page.value["items"]][:limit]
                if kind == "pr":
                    details = []
                    for row in rows:
                        detail = client.request("GET", f"{root}/pulls/{row['number']}", timeout=timeout, fresh=fresh)
                        if detail.error:
                            return detail
                        pages.append(detail)
                        details.append(detail.value)
                    rows = details
            else:
                rows = [r for p in pages for r in p.value if kind == "pr" or "pull_request" not in r]
            if _opt(options, "--state") == "merged":
                rows = [r for r in rows if r.get("merged_at")]
            _merge_observation(result, *pages)
            if "--label" in options:
                wanted = set(options["--label"])
                rows = [r for r in rows if wanted <= {x["name"] for x in r.get("labels", [])}]
            value = [_project(r, kind) for r in rows[:limit]]
            if kind == "pr" and set(fields) & {
                "mergeable",
                "mergeStateStatus",
                "statusCheckRollup",
                "reviewDecision",
                "files",
                "reviews",
                "additions",
                "deletions",
                "changedFiles",
                "closingIssuesReferences",
            }:
                enriched = []
                for row in rows[:limit]:
                    detail = _read_command(
                        client, "pr", "view", options, [str(row["number"])], timeout=timeout, fresh=fresh
                    )
                    if detail.error:
                        return detail
                    _merge_observation(result, detail)
                    enriched.append(detail.value)
                value = enriched
        else:
            value = _project(result.value, kind)
    elif kind == "repo" and action == "view":
        result = client.request("GET", root, timeout=timeout, fresh=fresh)
        if result.error:
            return result
        value = _project(result.value, "repo")
        permissions = value.get("permissions") or {}
        value.update(
            nameWithOwner=value.get("full_name"),
            isPrivate=value.get("private"),
            visibility=str(value.get("visibility") or ("private" if value.get("private") else "public")).upper(),
            viewerPermission=next(
                (
                    name
                    for flag, name in (
                        ("admin", "ADMIN"),
                        ("maintain", "MAINTAIN"),
                        ("push", "WRITE"),
                        ("triage", "TRIAGE"),
                        ("pull", "READ"),
                    )
                    if permissions.get(flag)
                ),
                None,
            ),
            defaultBranchRef={"name": value.get("default_branch")},
        )
    elif kind == "run" and action in {"list", "view"}:
        if "--job" in options:
            endpoint = f"{root}/actions/jobs/{_opt(options, '--job')}" + ("/logs" if "--log" in options else "")
        else:
            runs_root = (
                f"{root}/actions/workflows/{quote(_opt(options, '--workflow'), safe='')}/runs"
                if "--workflow" in options
                else f"{root}/actions/runs"
            )
            endpoint = runs_root + ("/" + str(number) if action == "view" else "?" + urlencode(query))
        if action == "list":
            pages = _pages(
                client,
                endpoint,
                timeout=timeout,
                fresh=fresh,
                paginate=True,
                limit=limit,
                items=lambda value: value["workflow_runs"],
            )
            if isinstance(pages, Result):
                return pages
            result = pages[0]
            rows = [r for page in pages for r in page.value["workflow_runs"]]
            _merge_observation(result, *pages)
        else:
            result = client.request("GET", endpoint, timeout=timeout, fresh=fresh)
            if result.error:
                return result
        value = (
            [_project(r, "run") for r in rows[:limit]]
            if action == "list"
            else _project(result.value, "run")
            if isinstance(result.value, dict)
            else result.value
        )
        if action == "view" and "jobs" in fields and "--job" not in options:
            jobs = _pages(
                client, f"{root}/actions/runs/{number}/jobs?per_page=100", timeout=timeout, fresh=fresh, paginate=True
            )
            if isinstance(jobs, Result):
                return jobs
            value["jobs"] = [
                {
                    **r,
                    "databaseId": r.get("id"),
                    "startedAt": r.get("started_at"),
                    "completedAt": r.get("completed_at"),
                    "status": r.get("status"),
                    "conclusion": r.get("conclusion"),
                }
                for p in jobs
                for r in p.value["jobs"]
            ]
            _merge_observation(result, *jobs)
    elif kind == "release" and action == "view":
        result = client.request(
            "GET",
            root + "/releases/" + ("tags/" + quote(number, safe="") if number else "latest"),
            timeout=timeout,
            fresh=fresh,
        )
        if result.error:
            return result
        value = _project(result.value, "release")
    else:
        return Result(error="github_unsupported_command")
    if kind in {"pr", "issue"} and action == "view" and isinstance(value, dict) and "comments" in fields:
        pages = _pages(
            client, f"{root}/issues/{number}/comments?per_page=100", timeout=timeout, fresh=fresh, paginate=True
        )
        if isinstance(pages, Result):
            return pages
        value["comments"] = [_project(r, "comment") for p in pages for r in p.value]
        _merge_observation(result, *pages)
    if kind == "pr" and action == "view" and isinstance(value, dict):
        for field_name, path in (("files", "files"), ("reviews", "reviews")):
            if field_name in fields:
                pages = _pages(
                    client, f"{root}/pulls/{number}/{path}?per_page=100", timeout=timeout, fresh=fresh, paginate=True
                )
                if isinstance(pages, Result):
                    return pages
                rows = [r for page in pages for r in page.value]
                value[field_name] = (
                    [
                        {
                            "path": r.get("filename"),
                            "additions": r.get("additions"),
                            "deletions": r.get("deletions"),
                            "changeType": {
                                "added": "ADDED",
                                "removed": "DELETED",
                                "modified": "MODIFIED",
                                "renamed": "RENAMED",
                                "copied": "COPIED",
                                "changed": "CHANGED",
                                "unchanged": "UNCHANGED",
                            }.get(r.get("status"), "UNKNOWN"),
                        }
                        for r in rows
                    ]
                    if path == "files"
                    else [_project(r, "comment") for r in rows]
                )
                _merge_observation(result, *pages)
    if (
        kind == "pr"
        and action == "view"
        and isinstance(value, dict)
        and set(fields) & {"reviewDecision", "closingIssuesReferences", "autoMergeRequest"}
    ):
        selections = []
        if "reviewDecision" in fields:
            selections.append("reviewDecision")
        # REST auto_merge has no enabledAt timestamp used by closeout readers.
        if "autoMergeRequest" in fields:
            selections.append("autoMergeRequest{enabledAt}")
        if "closingIssuesReferences" in fields:
            selections.append("closingIssuesReferences(first:100){totalCount pageInfo{hasNextPage} nodes{number url}}")
        owner, name = repo.split("/", 1)
        query = (
            "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){"
            + " ".join(selections)
            + "}}}"
        )
        aggregate = client.request(
            "POST",
            "graphql",
            payload={"query": query, "variables": {"owner": owner, "name": name, "number": int(number)}},
            timeout=timeout,
            fresh=fresh,
        )
        if aggregate.error:
            return aggregate
        pull = (aggregate.value.get("data") or {}).get("repository", {}).get("pullRequest")
        if not isinstance(pull, dict):
            return Result(error="github_pr_aggregate_unknown")
        if "closingIssuesReferences" in fields:
            references = pull.get("closingIssuesReferences")
            if (
                not isinstance(references, dict)
                or references.get("pageInfo", {}).get("hasNextPage")
                or references.get("totalCount") != len(references.get("nodes", []))
            ):
                return Result(error="github_closing_references_incomplete")
            pull["closingIssuesReferences"] = references["nodes"]
        value.update(pull)
        _merge_observation(result, aggregate)
    if fields != [""]:
        if isinstance(value, list):
            value = [{f: row.get(f) for f in fields} for row in value]
        elif isinstance(value, dict):
            value = {f: value.get(f) for f in fields}
    result.value = value
    return result


def _write_command(client, kind, action, options, positional, *, timeout, input=None):
    if (
        client.env.get("AGENT_NO_MERGE") == "1"
        and kind == "pr"
        and (action == "merge" or (action == "review" and "--approve" in options))
    ):
        return Result(error="github_worker_write_forbidden")
    repo = _repo(options, client) if kind != "gist" else ""
    root = f"repos/{repo}"
    number = positional[0] if positional else None
    payload = {}
    for key in ("title", "body", "head", "base", "color", "description", "ref", "name"):
        if "--" + key in options:
            payload[key] = _opt(options, "--" + key)
    if "--body-file" in options:
        source = _opt(options, "--body-file")
        payload["body"] = (
            (input.decode() if isinstance(input, bytes) else input) if source == "-" else Path(source).read_text()
        )
    if kind in {"pr", "issue"}:
        endpoint = root + ("/pulls" if kind == "pr" else "/issues")
        if action == "create":
            if kind == "pr":
                payload["draft"] = "--draft" in options
            if "--label" in options:
                payload["labels"] = options["--label"]
            method = "POST"
        else:
            endpoint += "/" + str(number)
            method = "PATCH"
            if action == "comment":
                endpoint, method = f"{root}/issues/{number}/comments", "POST"
            elif action in {"close", "reopen"}:
                payload["state"] = "closed" if action == "close" else "open"
                if "--reason" in options:
                    payload["state_reason"] = "completed" if _opt(options, "--reason") == "completed" else "not_planned"
            elif action == "review":
                endpoint += "/reviews"
                method = "POST"
                payload["event"] = (
                    "APPROVE"
                    if "--approve" in options
                    else "REQUEST_CHANGES"
                    if "--request-changes" in options
                    else "COMMENT"
                )
            elif action == "update-branch":
                endpoint += "/update-branch"
                method = "PUT"
            elif action in {"ready", "merge"}:
                owner, name = repo.split("/", 1)
                query = "query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){id isMergeQueueEnabled}}}"
                queue = client.request(
                    "POST",
                    "graphql",
                    payload={"query": query, "variables": {"owner": owner, "name": name, "number": int(number)}},
                    timeout=timeout,
                    fresh=True,
                )
                if queue.error:
                    return queue
                pull = queue.value.get("data", {}).get("repository", {}).get("pullRequest")
                if not isinstance(pull, dict) or not pull.get("id"):
                    return Result(error="github_queue_unknown")
                if action == "ready" or "--disable-auto" in options or pull.get("isMergeQueueEnabled"):
                    mutation = (
                        "markPullRequestReadyForReview"
                        if action == "ready"
                        else "disablePullRequestAutoMerge"
                        if "--disable-auto" in options
                        else "enqueuePullRequest"
                    )
                    input_payload = {"pullRequestId": pull["id"]}
                    if action == "merge" and "--disable-auto" not in options and _opt(options, "--match-head-commit"):
                        input_payload["expectedHeadOid"] = _opt(options, "--match-head-commit")
                    return client.request(
                        "POST",
                        "graphql",
                        payload={
                            "query": f"mutation($input:{mutation[0].upper() + mutation[1:]}Input!){{{mutation}(input:$input){{clientMutationId}}}}",
                            "variables": {"input": input_payload},
                        },
                        timeout=timeout,
                        fresh=True,
                    )
                if pull.get("isMergeQueueEnabled") is not False:
                    return Result(error="github_queue_unknown")
                endpoint += "/merge"
                method = "PUT"
                payload = {
                    "merge_method": "squash",
                    "sha": _opt(options, "--match-head-commit"),
                    "commit_title": _opt(options, "--subject"),
                    "commit_message": payload.get("body"),
                }
                payload = {k: v for k, v in payload.items() if v is not None}
            elif action != "edit":
                return Result(error="github_unsupported_command")
            if action == "close" and "--comment" in options:
                comment = client.request(
                    "POST",
                    f"{root}/issues/{number}/comments",
                    payload={"body": _opt(options, "--comment")},
                    timeout=timeout,
                    fresh=True,
                )
                if comment.error:
                    return comment
        if action in {"create", "edit"} and (
            "--add-label" in options
            or "--remove-label" in options
            or "--label" in options
            or "--milestone" in options
            or "--remove-milestone" in options
        ):
            if kind == "pr" and action == "edit":
                endpoint = f"{root}/issues/{number}"
            if "--add-label" in options or "--remove-label" in options:
                labels = client.request("GET", f"{root}/issues/{number}/labels", timeout=timeout, fresh=True)
                if labels.error:
                    return labels
                payload["labels"] = sorted(
                    ({r["name"] for r in labels.value} | set(options.get("--add-label", [])))
                    - set(options.get("--remove-label", []))
                )
            if "--remove-milestone" in options:
                payload["milestone"] = None
            elif "--milestone" in options:
                milestones = _pages(
                    client, f"{root}/milestones?state=all&per_page=100", timeout=timeout, fresh=True, paginate=True
                )
                if isinstance(milestones, Result):
                    return milestones
                target = _opt(options, "--milestone")
                matched = next((r["number"] for page in milestones for r in page.value if r["title"] == target), None)
                if matched is None:
                    return Result(error="github_milestone_not_found")
                payload["milestone"] = matched
    elif kind == "run" and action == "rerun":
        endpoint, method = (
            f"{root}/actions/runs/{number}/rerun" + ("-failed-jobs" if "--failed" in options else ""),
            "POST",
        )
    elif kind == "workflow" and action == "run":
        endpoint, method = f"{root}/actions/workflows/{quote(number, safe='')}/dispatches", "POST"
    elif kind == "gist" and action == "create":
        endpoint, method = "gists", "POST"
        payload["public"] = "--public" in options
        payload["files"] = {Path(path).name: {"content": Path(path).read_text()} for path in positional}
    elif kind == "release" and action in {"create", "edit", "upload"}:
        tag, *assets = positional
        if action == "create":
            payload = {
                "tag_name": tag,
                "name": payload.pop("title", tag),
                "body": Path(_opt(options, "--notes-file")).read_text() if "--notes-file" in options else "",
                "target_commitish": _opt(options, "--target"),
            }
            payload = {k: v for k, v in payload.items() if v is not None}
            for flag in ("draft", "prerelease"):
                if "--" + flag in options:
                    payload[flag] = _opt(options, "--" + flag) in {True, "true"}
            result = client.request("POST", f"{root}/releases", payload=payload, timeout=timeout, fresh=True)
        else:
            result = client.request("GET", f"{root}/releases/tags/{quote(tag, safe='')}", timeout=timeout, fresh=True)
        if result.error:
            return result
        release = result.value
        if action == "edit":
            payload = {"name": payload["title"]} if "title" in payload else {}
            if "--notes-file" in options:
                payload["body"] = Path(_opt(options, "--notes-file")).read_text()
            for flag in ("draft", "prerelease"):
                if "--" + flag in options:
                    payload[flag] = _opt(options, "--" + flag) in {True, "true"}
            return client.request(
                "PATCH", f"{root}/releases/{release['id']}", payload=payload, timeout=timeout, fresh=True
            )
        for asset in assets:
            name = Path(asset).name
            if "--clobber" in options:
                for existing in release.get("assets", []):
                    if existing.get("name") == name:
                        removed = client.request(
                            "DELETE", f"{root}/releases/assets/{existing['id']}", timeout=timeout, fresh=True
                        )
                        if removed.error:
                            return removed
            upload = release["upload_url"].split("{", 1)[0] + "?" + urlencode({"name": name})
            result = client.request(
                "POST",
                upload,
                payload=Path(asset).read_bytes(),
                headers={"Content-Type": "application/octet-stream"},
                timeout=timeout,
                fresh=True,
            )
            if result.error:
                return result
        return result
    elif kind == "label" and action in {"create", "edit"}:
        endpoint, method = (
            f"{root}/labels" + ("/" + quote(number, safe="") if action == "edit" else ""),
            "POST" if action == "create" else "PATCH",
        )
        payload["name"] = payload.get("name", number)
    else:
        return Result(error="github_unsupported_command")
    return client.request(method, endpoint, payload=payload, timeout=timeout, fresh=True)


def _format_value(value, options, *, api=False):
    expression = _opt(options, "--jq", "-q")
    if expression:
        # jq stays local: gh must not fetch again to format a cached response.
        p = subprocess.run(
            ["jq", "-r", expression], input=json.dumps(value), text=True, capture_output=True, check=True, timeout=5
        )
        return p.stdout.encode()
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode()
    if not api and "--json" not in options and isinstance(value, dict) and value.get("html_url"):
        return (value["html_url"] + "\n").encode()
    return json.dumps(value, ensure_ascii=False).encode()


def _translation_options(args):
    """Closed translation shapes; all other argv stays intact for real gh.

    Admission is separate. In particular -H means head in pr list, while
    -s means status in run list. Never guess at flags or requested fields.
    """
    repo = {"--repo", "-R"}
    formatting = {"--json", "--jq", "-q"}
    listing = formatting | repo | {"--limit", "-L"}
    basic = {"id", "number", "title", "body", "url", "state", "createdAt", "updatedAt", "closedAt", "labels"}
    pr = basic | {
        "headRefOid",
        "headRefName",
        "baseRefOid",
        "baseRefName",
        "isDraft",
        "mergedAt",
        "mergeCommit",
        "mergeable",
        "mergeStateStatus",
        "isCrossRepository",
        "additions",
        "deletions",
        "changedFiles",
        "files",
        "autoMergeRequest",
        "reviewDecision",
        "closingIssuesReferences",
        "statusCheckRollup",
        "reviews",
    }
    run = {
        "databaseId",
        "number",
        "displayTitle",
        "headSha",
        "headBranch",
        "status",
        "conclusion",
        "event",
        "url",
        "createdAt",
        "updatedAt",
        "workflowName",
        "workflowDatabaseId",
        "startedAt",
        "attempt",
    }
    shapes = {
        ("pr", "list"): (
            listing | {"--state", "-s"},
            pr - {"autoMergeRequest", "reviewDecision", "closingIssuesReferences"},
            0,
            0,
        ),
        ("pr", "view"): (formatting | repo, pr, 0, 1),
        ("issue", "list"): (listing | {"--state", "-s"}, basic, 0, 0),
        ("issue", "view"): (formatting | repo, basic, 1, 1),
        ("repo", "view"): (
            formatting,
            {"nameWithOwner", "isPrivate", "viewerPermission", "visibility", "defaultBranchRef"},
            0,
            1,
        ),
        ("run", "list"): (
            listing
            | {"--workflow", "-w", "--branch", "-b", "--event", "-e", "--status", "-s", "--commit", "-c", "--created"},
            run,
            0,
            0,
        ),
        ("run", "view"): (formatting | repo, run | {"jobs"}, 1, 1),
    }
    # Only these publishing flags have exact implementations. Unknown write
    # shapes also use the admitted native transport, without granting admission.
    text = {"--title", "--body", "--body-file"}
    for kind in ("pr", "issue"):
        shapes[(kind, "comment")] = (repo | {"--body", "--body-file"}, None, 1, 1)
        shapes[(kind, "create")] = (
            repo | text | {"--label", "--milestone"} | ({"--head", "--base", "--draft"} if kind == "pr" else set()),
            None,
            0,
            0,
        )
        shapes[(kind, "edit")] = (
            repo
            | text
            | {"--add-label", "--remove-label", "--milestone", "--remove-milestone"}
            | ({"--base"} if kind == "pr" else set()),
            None,
            1,
            1,
        )
        shapes[(kind, "close")] = (repo | {"--comment"} | ({"--reason"} if kind == "issue" else set()), None, 1, 1)
        shapes[(kind, "reopen")] = (repo, None, 1, 1)
    shapes[("pr", "merge")] = (
        repo | {"--squash", "--match-head-commit", "--subject", "--body", "--disable-auto"},
        None,
        1,
        1,
    )
    shapes[("pr", "ready")] = (repo, None, 1, 1)
    shapes[("pr", "update-branch")] = (repo, None, 1, 1)
    shapes[("run", "rerun")] = (repo | {"--failed"}, None, 1, 1)
    if len(args) < 3:
        return None
    api = args[1] == "api"
    tokens = args[2:] if api else args[3:]
    shape = (
        (
            {
                "--method",
                "-X",
                "--input",
                "--header",
                "-H",
                "--field",
                "-F",
                "--raw-field",
                "-f",
                "--paginate",
                "--slurp",
                "--jq",
                "-q",
            },
            None,
            1,
            1,
        )
        if api
        else shapes.get(tuple(args[1:3]))
    )
    if shape is None:
        return None
    allowed, fields, minimum, maximum = shape
    # Preflight before parsing: an unknown valued flag must not steal a
    # positional argument or be silently treated as a boolean.
    iterator = iter(tokens)
    for token in iterator:
        if token == "--":
            break
        if token.startswith("-"):
            flag, eq, value = token.partition("=")
            if flag not in allowed:
                return None
            boolean = flag in {
                "--draft",
                "--remove-milestone",
                "--squash",
                "--disable-auto",
                "--failed",
                "--paginate",
                "--slurp",
            }
            if boolean and eq:
                return None
            if not eq and not boolean and next(iterator, None) is None:
                return None
    options, positional = _options(tokens)
    if any(
        short in options and long in options
        for short, long in {
            "-R": "--repo",
            "-L": "--limit",
            "-q": "--jq",
            "-X": "--method",
            "-s": "--status" if args[1] == "run" else "--state",
            "-w": "--workflow",
            "-b": "--branch",
            "-e": "--event",
            "-c": "--commit",
            "-f": "--raw-field",
            "-F": "--field",
            "-H": "--header",
        }.items()
    ):
        return None
    if not minimum <= len(positional) <= maximum:
        return None
    if any(
        len(values) > 1
        for flag, values in options.items()
        if flag
        not in {"--label", "--add-label", "--remove-label", "-H", "--header", "-f", "--raw-field", "-F", "--field"}
    ):
        return None
    if fields is not None:
        requested = set(str(_opt(options, "--json", default="")).split(","))
        if "--json" not in options or not requested <= fields:
            return None
    if api:
        if set(options) & {"--field", "-F"} and set(options) & {"--raw-field", "-f"}:
            return None
        if "--input" in options and set(options) & {"--field", "-F", "--raw-field", "-f"}:
            return None
        if "{" in positional[0] or "}" in positional[0]:
            return None
        if "--slurp" in options and "--paginate" not in options:
            return None
        if "--paginate" in options and _opt(options, "--method", "-X", default="GET").upper() != "GET":
            return None
        if "--paginate" in options and (
            set(options) & {"--header", "-H", "--input", "--field", "-F", "--raw-field", "-f"}
        ):
            return None
        for flag in ("--field", "-F", "--raw-field", "-f"):
            for entry in options.get(flag, []):
                key, eq, value = entry.partition("=")
                if not eq or "[" in key or (flag in {"--field", "-F"} and value.startswith("@")):
                    return None
                if flag in {"--field", "-F"} and (re.fullmatch(r"[+-]\d+|0\d+", value) or "{" in value or "}" in value):
                    return None
    return options, positional


def _native_buckets(args, host="github.com"):
    """Rate-limit buckets a native ``gh`` argv can spend, ``secondary`` always included.

    ``gh api`` is classified from its one positional endpoint, normalised as
    ``GitHubClient.request`` does; ``gh search`` from its subcommand. Every
    other command, and a ``gh api`` whose endpoint cannot be determined, may
    spend ``core`` or ``graphql``. An unrelated exhausted bucket must not block
    the command.
    """
    buckets = {"secondary"}
    command = args[1] if len(args) > 1 else ""
    if command == "search":
        # Search's valued flags include child-specific filters accepted before
        # the subcommand. Its -w is boolean, unlike workflow commands' -w.
        _, positional = _options(
            args[2:],
            valued_flags={
                "--app",
                "--assignee",
                "--author",
                "--author-date",
                "--author-email",
                "--author-name",
                "--base",
                "--checks",
                "--closed",
                "--commenter",
                "--comments",
                "--committer",
                "--committer-date",
                "--committer-email",
                "--committer-name",
                "--created",
                "--extension",
                "--filename",
                "--followers",
                "--forks",
                "--good-first-issues",
                "--hash",
                "--head",
                "--help-wanted-issues",
                "--include-forks",
                "--interactions",
                "--involves",
                "--jq",
                "--json",
                "--label",
                "--language",
                "--license",
                "--limit",
                "--match",
                "--mentions",
                "--merged-at",
                "--milestone",
                "--number-topics",
                "--order",
                "--owner",
                "--parent",
                "--project",
                "--reactions",
                "--repo",
                "--review",
                "--review-requested",
                "--reviewed-by",
                "--search-type",
                "--size",
                "--sort",
                "--stars",
                "--state",
                "--team-mentions",
                "--template",
                "--topic",
                "--tree",
                "--updated",
                "--visibility",
                "-L",
                "-R",
                "-q",
                "-t",
            },
        )
        buckets.update(
            {"code_search" if positional[0] == "code" else "search"} if positional else {"search", "code_search"}
        )
    elif command == "api":
        options, positional = _options(args[2:])
        # Exactly one positional is the endpoint. Zero, or a second one (a
        # flag this parser does not model took a value), is undeterminable.
        hostname = _opt(options, "--hostname")
        host_class, path = _canonical_endpoint(
            positional[0] if len(positional) == 1 else None,
            hostname if isinstance(hostname, str) else host,
        )
        if host_class == "rejected":
            raise ValueError("GitHub endpoint host mismatch")
        buckets.update({_endpoint_bucket(path)} if path is not None else {"core", "graphql"})
    else:
        buckets.update({"core", "graphql"})
    return frozenset(buckets)


# --- gh api: the request a native command line makes, as gh 2.98.0 builds it -----------------
#
# ``-F`` has one meaning per gh 2.98.0 command family (``gh <family> <command> --help``): a typed
# ``gh api`` field, the release notes file of ``gh release create|edit``, the body file of
# ``gh issue|pr comment|create|edit`` and ``gh pr review|merge``. Only ``gh api`` fields shape a
# request this client classifies; a body or notes file is never read for admission.
_DASH_F = {"api": "--field", "release": "--notes-file", "issue": "--body-file", "pr": "--body-file"}
# gh 2.98.0 ``gh api`` flags (pkg/cmd/api/api.go) by pflag spelling: (name, takes a value).
_GH_API_FLAGS = {
    "--hostname": ("hostname", True),
    "--method": ("method", True),
    "-X": ("method", True),
    "--field": ("field", True),
    "-F": ("field", True),
    "--raw-field": ("raw-field", True),
    "-f": ("raw-field", True),
    "--header": ("header", True),
    "-H": ("header", True),
    "--preview": ("preview", True),
    "-p": ("preview", True),
    "--input": ("input", True),
    "--template": ("template", True),
    "-t": ("template", True),
    "--jq": ("jq", True),
    "-q": ("jq", True),
    "--cache": ("cache", True),
    "--include": ("include", False),
    "-i": ("include", False),
    "--slurp": ("slurp", False),
    "--paginate": ("paginate", False),
    "--silent": ("silent", False),
    "--verbose": ("verbose", False),
    "--allow-escape-sequences": ("allow-escape-sequences", False),
}
# gh fills these from the current repository (fillPlaceholders); this client does not.
_GH_PLACEHOLDER = re.compile(r":(?:owner|repo|branch)\b|\{(?:owner|repo|branch)\}", re.ASCII)
_GO_TRUE, _GO_FALSE = {"1", "t", "T", "TRUE", "true", "True"}, {"0", "f", "F", "FALSE", "false", "False"}
_UNRESOLVED = object()


def _gh_api_argv(tokens):
    """``(flags, positional, end)`` of ``gh api`` arguments as gh 2.98.0's pflag parser reads them, else ``None``.

    ``flags`` maps a flag's name to its values in order; ``end`` is the index of the ``--`` that
    ends the flags, else ``len(tokens)``. A long flag takes ``--name=value`` or the next
    argument; shorthands combine (``-iXPOST``), attach (``-Fkey=value``) or take ``-F=value``;
    ``-`` is positional. An unknown flag, a missing value or help is ``None``: gh sends no request.
    """
    flags, positional, queue = {}, [], [str(token) for token in tokens]
    end = len(queue)
    while queue:
        token = queue.pop(0)
        if token == "--":
            end -= len(queue) + 1
            positional.extend(queue)
            break
        if not token.startswith("-") or token == "-":
            positional.append(token)
            continue
        if token.startswith("--"):
            spelling, eq, value = token.partition("=")
            if spelling not in _GH_API_FLAGS:
                return None
            name, valued = _GH_API_FLAGS[spelling]
            if valued and not eq:
                if not queue:
                    return None
                value = queue.pop(0)
            elif not valued:
                value = True if not eq else True if value in _GO_TRUE else False if value in _GO_FALSE else None
                if value is None:
                    return None
            flags.setdefault(name, []).append(value)
            continue
        shorthands = token[1:]
        while shorthands:
            if "-" + shorthands[0] not in _GH_API_FLAGS:
                return None
            name, valued = _GH_API_FLAGS["-" + shorthands[0]]
            if len(shorthands) > 2 and shorthands[1] == "=":
                value, shorthands = shorthands[2:], ""
                if not valued:
                    value = True if value in _GO_TRUE else False if value in _GO_FALSE else None
                    if value is None:
                        return None
            elif not valued:
                value, shorthands = True, shorthands[1:]
            elif len(shorthands) > 1:
                value, shorthands = shorthands[1:], ""
            elif queue:
                value, shorthands = queue.pop(0), ""
            else:
                return None
            flags.setdefault(name, []).append(value)
    return flags, positional, end


def _go_atoi(text):
    """Go's ``strconv.Atoi``: an optionally signed ASCII decimal within int64, else ``None``."""
    match = re.fullmatch(r"([+-]?)0*([0-9]+)", text, re.ASCII)
    if match is None or len(match[2]) > 19:
        return None
    number = int(match[1] + match[2])
    return number if -(2**63) <= number < 2**63 else None


def _gh_typed(text, read):
    """gh 2.98.0 ``magicFieldValue`` of a ``-F`` value (pkg/cmd/api/fields.go).

    ``@path`` and ``@-`` are a file's or standard input's text (``read``); then an int, a
    boolean or null; any other value is the string, unless gh would fill a repository
    placeholder into it.
    """
    if text.startswith("@"):
        return read(text[1:])
    number = _go_atoi(text)
    if number is not None:
        return number
    if text in ("true", "false"):
        return text == "true"
    if text == "null":
        return None
    return _UNRESOLVED if _GH_PLACEHOLDER.search(text) else text


def _gh_fields(raw, typed, value_of):
    """gh 2.98.0 ``parseFields``: raw fields, then typed ones, into nested parameters, else ``None``.

    Bracketed keys nest objects (``a[b]=1``) and append to arrays (``a[]=1``); a key without
    ``=`` is an empty array only when it ends in ``[]``. Overriding a field, or a type
    conflict, is gh's error: no request.
    """
    params = {}
    for entry, magic in [*((entry, False) for entry in raw), *((entry, True) for entry in typed)]:
        value_index, keystack, key_start = 0, [], 0
        for position, char in enumerate(entry):
            if char == "[":
                if key_start == 0:
                    keystack.append(entry[:position])
                key_start = position + 1
            elif char == "]":
                keystack.append(entry[key_start:position])
            elif char == "=":
                if key_start == 0:
                    keystack.append(entry[:position])
                value_index = position + 1
                break
        if not keystack:
            return None
        if value_index == 0:
            if keystack[-1] != "":
                return None
            value = None
        else:
            value = entry[value_index:]
            if magic:
                value = value_of(value)
        target, is_array, subkey = params, False, ""
        for key in keystack:
            if key == "":
                is_array = True
                continue
            if subkey != "":
                target = _gh_slice(target, subkey, key) if is_array else _gh_map(target, subkey)
                is_array = False
                if target is None:
                    return None
            subkey = key
        if is_array:
            if value is None:
                target[subkey] = []
            elif subkey not in target:
                target[subkey] = [value]
            elif isinstance(target[subkey], list):
                target[subkey].append(value)
            else:
                return None
        elif subkey in target:
            return None
        else:
            target[subkey] = value
    return params


def _gh_map(params, key):
    if key not in params:
        params[key] = {}
    return params[key] if isinstance(params[key], dict) else None


def _gh_slice(params, previous, key):
    if previous not in params:
        params[previous] = [{}]
        return params[previous][0]
    existing = params[previous]
    if not isinstance(existing, list):
        return None
    if existing and isinstance(existing[-1], dict):
        if key not in existing[-1]:
            return existing[-1]
        if existing[-1][key] is None:
            return None  # gh's reflect.TypeOf(nil).Kind() panics: no request
        if isinstance(existing[-1][key], list):
            return existing[-1]
    existing.append({})
    return existing[-1]


def _gh_contains_unresolved(value):
    if value is _UNRESOLVED:
        return True
    if isinstance(value, dict):
        return any(_gh_contains_unresolved(item) for item in value.values())
    return isinstance(value, list) and any(_gh_contains_unresolved(item) for item in value)


def _gh_group(params):
    """gh 2.98.0 ``groupGraphQLVariables``: ``query`` and ``operationName`` stay top-level, every other field is a variable."""
    top = {key: value for key, value in params.items() if key in ("query", "operationName")}
    variables = {key: value for key, value in params.items() if key not in top}
    return {**top, "variables": variables} if variables else top


def _go_json(value):
    """The bytes Go's ``encoding/json.Marshal`` writes for gh's parameters: sorted keys, compact, HTML-safe."""
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    for char, escape in (("<", "\\u003c"), (">", "\\u003e"), ("&", "\\u0026"), (" ", "\\u2028"), (" ", "\\u2029")):
        text = text.replace(char, escape)
    return text.encode()


def _gh_add_query(path, params):
    """gh 2.98.0 ``addQuery`` (pkg/cmd/api/http.go): parameters as ``url.Values``, keys sorted."""
    if not params:
        return path
    pairs = []

    def add(key, value):
        if isinstance(value, str):
            pairs.append((key, value))
        elif value is None:
            pairs.append((key, ""))
        elif isinstance(value, bool):
            pairs.append((key, "true" if value else "false"))
        elif isinstance(value, int):
            pairs.append((key, str(value)))
        elif isinstance(value, dict):
            for subkey, item in value.items():
                add(subkey, item)
        elif isinstance(value, list):
            for item in value:
                add(key + "[]", item)

    add("", params)
    pairs.sort(key=lambda pair: pair[0])
    query = "&".join(quote_plus(key, safe="") + "=" + quote_plus(value, safe="") for key, value in pairs)
    return path + ("&" if "?" in path else "?") + query


class _Stdin:
    """A command's standard input as gh reads it: once, whole (:func:`_gh_api_call` refuses a second reader)."""

    def __init__(self, data):
        self.data = (
            b""
            if data is None
            else data.encode()
            if isinstance(data, str)
            else bytes(data)
            if isinstance(data, (bytes, bytearray, memoryview))
            else None
        )

    def take(self):
        data, self.data = self.data, b""
        if data is None:
            raise GitHubUnpreparedRequest("invalid_body_type")
        return data


def _source_bytes(source, stdin, cwd):
    """The exact bytes gh reads from a ``--input`` or ``@`` source, whatever its size.

    ``-`` is the command's standard input (:class:`_Stdin`), which gh is given unchanged. A
    path, relative to the command's working directory, is opened without blocking and read only
    if it is a regular file, which gh then reads itself. A pipe or device is refused unread: what
    this client read from it could not be what gh reads, and it can neither block nor be consumed.
    """
    if source == "-":
        return stdin.take()
    path = Path(source)
    path = path if path.is_absolute() else Path(cwd or ".") / path
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    except (OSError, ValueError):
        raise GitHubUnpreparedRequest("body_unreadable") from None
    with open(descriptor, "rb", closefd=True) as handle:
        mode = os.fstat(descriptor).st_mode
        if not stat.S_ISREG(mode):
            raise GitHubUnpreparedRequest("body_unreadable" if stat.S_ISDIR(mode) else "body_not_replayable")
        try:
            return handle.read()
        except OSError:
            raise GitHubUnpreparedRequest("body_unreadable") from None


@dataclass
class _GhApiCall:
    """The request one ``gh api`` command line makes, as gh 2.98.0 builds it (pkg/cmd/api)."""

    method: str
    endpoint: str
    host: str | None
    flags: dict
    unresolved: bool
    build: Any

    def body(self):
        """The exact body bytes, ``None`` for none, or ``_UNRESOLVED_BODY``; raises when gh's sources cannot be read."""
        return self.build()[1]


def _gh_api_call(tokens, *, stdin, cwd):
    """The request ``gh api <tokens>`` sends, else ``None`` when gh 2.98.0 would send none.

    One reading for admission and translation: pflag argv (:func:`_gh_api_argv`), gh's own
    argument checks, fields (:func:`_gh_fields`, raw before typed) and the method gh defaults
    to (POST once there are fields or ``--input``). ``build()`` reads every source gh reads,
    in gh's order, and returns ``(url, body)``: ``--input`` is the body verbatim and the fields
    become query parameters; otherwise a GET carries the fields as query parameters and any
    other method as gh's JSON (``graphql`` keeps ``query`` and ``operationName`` top-level and
    groups every other field under ``variables``).
    """
    parsed = _gh_api_argv(tokens)
    if parsed is None:
        return None
    flags, positional, _ = parsed

    def last(name, default=None):
        return flags[name][-1] if name in flags else default

    if len(positional) != 1:
        return None
    endpoint, given_method, input_file = positional[0], last("method", "GET"), last("input") or None
    paginate, slurp = last("paginate") is True, last("slurp") is True
    outputs = [last("verbose") is True, last("silent") is True, bool(last("jq")), bool(last("template"))]
    if (
        (paginate and given_method.upper() != "GET" and endpoint != "graphql")
        or (paginate and input_file)
        or (slurp and (last("jq") or last("template") or not paginate))
        or sum(outputs) > 1
    ):
        return None
    raw, typed = flags.get("raw-field", []), flags.get("field", [])
    shape = _gh_fields(raw, typed, lambda text: _gh_typed(text, lambda _source: ""))
    # gh reads standard input once and closes it: a second reader fails before any request.
    stdin_readers = sum(entry.partition("=")[2] == "@-" for entry in typed if "=" in entry) + (input_file == "-")
    if shape is None or stdin_readers > 1:
        return None
    method = given_method if "method" in flags else "POST" if shape or input_file else "GET"
    method = method.upper() or "GET"
    fields_unresolved = _gh_contains_unresolved(shape)

    def build():
        if fields_unresolved and not input_file and method != "GET":
            return endpoint, _UNRESOLVED_BODY
        stream = _Stdin(stdin)

        def text_of(source):
            return _source_bytes(source, stream, cwd).decode(errors="replace")

        # gh reads the fields' sources first (``@-`` takes standard input), then ``--input``.
        params = _gh_fields(raw, typed, lambda text: _gh_typed(text, text_of))
        if input_file:
            return _gh_add_query(endpoint, params), _source_bytes(input_file, stream, cwd)
        if not params:
            return endpoint, None
        if method == "GET":
            return _gh_add_query(endpoint, params), None
        return endpoint, _go_json(_gh_group(params) if endpoint == "graphql" else params)

    unresolved = fields_unresolved or _GH_PLACEHOLDER.search(endpoint) is not None
    return _GhApiCall(method, endpoint, last("hostname"), flags, unresolved, build)


def _normalize_native(args, host, pools, *, stdin=None, cwd=None):
    """:func:`_normalize` of a native ``gh`` command line.

    A ``gh api`` request is what gh builds (:func:`_gh_api_call`); its body is read only if
    admission needs it. Any other command, and argv gh would refuse, is classified by its vetted
    landing flow alone (:data:`_DASH_F`: its ``-F`` names a body or notes file, never a field).
    """
    call = (
        _gh_api_call(args[2:], stdin=stdin, cwd=cwd)
        if len(args) > 2 and _DASH_F.get(str(args[1])) == "--field"
        else None
    )
    if call is not None:
        host_class, path = _canonical_endpoint(call.endpoint, call.host or host)
        if host_class not in {"unknown", "rejected"}:
            return _normalize(call.method, path, pools, call.body)
    flow = "landing" if _landing_flow() else None
    classification = "invalid" if len(args) > 1 and args[1] == "api" else "command"
    return _Request("", None, tuple(pools), flow, provenance=_Provenance(classification))


def _argv_landing_flow(args):
    """The landing flow a ``gh`` command line opens: a landing verb or a CI status read."""
    if len(args) < 3 or Path(str(args[0])).name not in {"gh", "gh.real"}:
        return None
    command = (str(args[1]), str(args[2]))
    if command in {("pr", "merge"), ("pr", "review")}:
        return "landing-verb"
    options, _ = _options([str(arg) for arg in args[3:]])
    if command == ("run", "rerun") and (True in options.get("--failed", []) or {"--job", "-j"} & set(options)):
        return "landing-verb"
    rollup = command == ("pr", "view") and "statusCheckRollup" in str(_opt(options, "--json", default="")).split(",")
    return "ci-status" if command == ("pr", "checks") or rollup else None


@dataclass(frozen=True)
class _Presentation:
    """How a ``gh api`` command line presents GitHub's response, read by :func:`_gh_api_argv`.

    ``end`` is where its flags end among the arguments after ``api``.
    """

    include: bool
    paginate: bool
    verbose: bool
    end: int


def _gh_api_presentation(args):
    """The response-presentation flags of a ``gh api`` command line, else ``None`` (gh sends no request)."""
    if len(args) < 2 or str(args[1]) != "api":
        return None
    parsed = _gh_api_argv(args[2:])
    if parsed is None:
        return None
    flags, _, end = parsed

    def given(name):
        return flags.get(name, [False])[-1] is True

    return _Presentation(given("include"), given("paginate"), given("verbose"), end)


# gh's report of a failing response on standard error (pkg/cmd/api): its message and HTTP status.
_GH_HTTP_ERROR = re.compile(rb"^gh: (?:(.*) \(HTTP ([0-9]{3})\)|HTTP ([0-9]{3}))\r?$", re.MULTILINE)


def _gh_reported(response, report):
    """Whether ``report`` (a :data:`_GH_HTTP_ERROR` match) is gh's report of ``response``.

    gh names the status, after the error body's ``message`` when it has one.
    """
    message, status = report[0], int(report[1] or report[2])
    try:
        body = json.loads(response.body)
    except (ValueError, RecursionError):
        body = None
    stated = body.get("message") if isinstance(body, dict) and isinstance(body.get("message"), str) else ""
    return response.status == status and stated.encode() == message


def _native_response(output, error, *, paginate, complete):
    """GitHub's response to a ``gh api --include`` run, from gh's own framing: ``(response, end)``, else ``None``.

    gh writes each response's frame (:func:`_frame`) before its body, on success and on HTTP
    errors alike, so the first frame starts standard output. Without ``--paginate`` it is the
    only response. A paginated run repeats a frame per page, each after a newline, and stops at
    the first page that fails: a first page that failed is the first frame. Otherwise the
    failing page's frame is the last one, followed only by GitHub's own error body, and gh
    reports its status (after that body's message) on standard error; it is read only when that
    report matches it and the output is ``complete`` (not cut short by the response ceiling).
    Frame-like text anywhere else is a body (what ``--jq`` or ``--template`` rendered from
    GitHub's data) and is never read as GitHub's headers.
    """
    first = _frame(output)
    if first is None or not paginate or not 200 <= first[0].status < 300:
        return first
    reports = _GH_HTTP_ERROR.findall(error)
    start = output.rfind(b"\nHTTP/")
    while complete and reports and start > 0:
        framed = _frame(output, start + 1)
        if framed is not None:
            return framed if _gh_reported(framed[0], reports[-1]) else None
        start = output.rfind(b"\nHTTP/", 0, start)
    return None


def _native_command(args, client, runner, kwargs):
    """Fall through once using the bounded, colour-safe native transport, inside the same admission.

    A ``gh api`` command line that is neither paginated nor verbose, and does not print
    GitHub's headers itself, runs with ``--include`` after its last flag, so GitHub's status and
    headers (a Retry-After included) come from gh's own framing (:func:`_native_response`).
    That frame is then removed: the caller's output is exactly what gh prints without it.
    """
    pools = sorted(_native_buckets(args, client.host) - {_SYNTHETIC_HOLD})
    request = _normalize_native(args, client.host, pools, stdin=kwargs.get("input"), cwd=client.cwd)
    try:
        with client._db() as db:
            refusal = _admit(db, client.scope, request, client.clock())
    except GitHubUnpreparedRequest as refused:
        return _result_process(args, _unprepared(refused.reason), {}, kwargs)
    if refusal is not None:
        return _result_process(args, _limited(*refusal), {}, kwargs)
    executable = client.env.get("AGENT_REAL_GH", "gh")
    executor = runner or client.runner
    if executor is None:
        from scripts.opsec.prepublish import PublishBlocked, real_gh

        try:
            executable = real_gh({**client.env, "AGENT_ORIGINAL_PATH": client.env.get("PATH", os.defpath)})
        except PublishBlocked:
            return _result_process(args, Result(error="github_transport_unavailable"), {}, kwargs)
    presentation = _gh_api_presentation(args)
    # gh merges paginated JSON pages only without --include, and --verbose prints no frame.
    injected = presentation is not None and not (presentation.include or presentation.paginate or presentation.verbose)
    command = [executable, *args[1:]]
    if injected:
        flags_end = 2 + presentation.end
        command = [executable, *args[1:flags_end], "--include", *args[flags_end:]]
    call = dict(
        input=kwargs.get("input").encode() if isinstance(kwargs.get("input"), str) else kwargs.get("input"),
        env=client.env,
        cwd=client.cwd,
        timeout=kwargs.get("timeout") or 30,
        capture_output=True,
        check=False,
    )
    if executor is None:
        # An added frame is removed again: the ceiling bounds what the caller gets.
        native = _transport_process(command, limit=client.max_response_bytes, framed=injected, **call)
    else:
        native = executor(command, **call)
    output, error = (
        value.encode() if isinstance(value, str) else value or b"" for value in (native.stdout, native.stderr)
    )
    framed = (
        _native_response(
            output,
            error,
            paginate=presentation.paginate,
            complete=client.max_response_bytes is None or len(output) <= client.max_response_bytes,
        )
        if presentation is not None and (presentation.include or injected)
        else None
    )
    response = framed[0] if framed is not None else None
    if injected and framed is not None:
        output = output[framed[1] :]
    if native.returncode:
        now = client.clock()
        if response is not None:
            # GitHub's own status and headers: decide as request() does.
            limit = _limit_hold(response, now)
        elif b"rate limit" in error.lower():
            # gh's stderr carries no Retry-After: a synthetic hold, never binding on landing.
            limit = [_SYNTHETIC_HOLD], int(now + 60), "secondary_hold"
        else:
            limit = None
        if limit is not None:
            holds, reset, reason = limit
            budget = _budget_headers(response.headers) if response is not None else None
            # GitHub's pool observation: the resource it names, else the one pool the command spends.
            resource = (
                (response.headers.get("x-ratelimit-resource") or (pools[0] if len(pools) == 1 else None))
                if budget is not None
                else None
            )
            with client._db() as db:
                if resource is not None:
                    _store_budget(db, client.scope, resource, *budget, now=now)
                for hold in holds:
                    _store_budget(db, client.scope, hold, 0, reset, now=now)
            return _result_process(args, _limited(reason, reset), {}, kwargs)
    if client.max_response_bytes is not None and len(output) > client.max_response_bytes:
        return _result_process(args, Result(error="github_response_too_large"), {}, kwargs)
    text = kwargs.get("text") or kwargs.get("universal_newlines") or kwargs.get("encoding")
    for key, value in (("stdout", output), ("stderr", error)):
        value = (
            value.decode(kwargs.get("encoding") or "utf-8", errors=kwargs.get("errors") or "strict") if text else value
        )
        setattr(native, key, value)
        target = kwargs.get(key)
        if target not in (None, subprocess.PIPE, subprocess.DEVNULL, subprocess.STDOUT):
            target.write(value)
        elif target is None and not kwargs.get("capture_output"):
            import sys

            stream = getattr(sys, key)
            (stream.buffer if isinstance(value, bytes) else stream).write(value)
    native.args = args
    if kwargs.get("check") and native.returncode:
        raise subprocess.CalledProcessError(native.returncode, args, output=native.stdout, stderr=native.stderr)
    return native


def _run_command(args, *, runner=None, client=None, fresh=False, allow_stale=False, **kwargs):
    """subprocess.run-compatible seam; non-GitHub commands pass through.

    A CompletedProcess carries ``github_result``. Stale reads also emit a
    typed diagnostic to stderr, never a silently fresh status. Admission of
    public writes remains the caller's responsibility.
    """
    if not args or Path(str(args[0])).name not in {"gh", "gh.real"}:
        return (runner or subprocess.run)(args, **kwargs)
    if args[1:] in (["--version"], ["version"]):
        environment = colour_safe_environment(kwargs.get("env"))
        kwargs["env"] = environment
        if runner is None:
            from scripts.opsec.prepublish import PublishBlocked, real_gh

            try:
                executable = real_gh({**environment, "AGENT_ORIGINAL_PATH": environment.get("PATH", os.defpath)})
            except PublishBlocked:
                return _result_process(args, Result(error="github_transport_unavailable"), {}, kwargs)
            args = [executable, *args[1:]]
        return (runner or subprocess.run)(args, **kwargs)
    limit = kwargs.pop("max_response_bytes", None)
    if limit is not None and (type(limit) is not int or limit < 0):
        raise ValueError("invalid GitHub response byte limit")
    host_args = list(args[2:])
    host_options, _ = _options(host_args, canonicalize_hosts=True)
    if client is not None and (limit is not None or allow_stale or "--hostname" in host_options):
        from copy import copy

        # Per-call host and read options must never retarget the caller's client.
        client = copy(client)
        client.env = dict(client.env)
        if limit is not None:
            client.max_response_bytes = (
                min(client.max_response_bytes, limit) if client.max_response_bytes is not None else limit
            )
    if client is None:
        client = GitHubClient(env=kwargs.get("env"), cwd=kwargs.get("cwd"), runner=runner, max_response_bytes=limit)
    if allow_stale:
        client.allow_stale = True
    timeout = kwargs.get("timeout") or 30
    if (
        client.env.get("AGENT_NO_MERGE") == "1"
        and args[1:3] in (["pr", "merge"], ["pr", "review"])
        and (args[2] == "merge" or any(a.split("=", 1)[0] in {"--approve", "-a"} for a in args[3:]))
    ):
        return _result_process(args, Result(error="github_worker_write_forbidden"), {}, kwargs)
    if "--hostname" in host_options:
        client._configure_host(_opt(host_options, "--hostname"))
        args = [*args[:2], *host_args]
    translation = _translation_options(args)
    if translation is None:
        return _native_command(args, client, runner, kwargs)
    options, positional = translation
    aliases = {
        "-s": "--status" if args[1] == "run" else "--state",
        "-B": "--base",
        "-l": "--label",
        "-S": "--search",
        "-A": "--author",
        "-a": "--assignee",
    }
    if args[1] == "run":
        aliases.update({"-w": "--workflow", "-b": "--branch", "-e": "--event", "-c": "--commit"})
    for short, long in aliases.items():
        if short in options and long not in options:
            options[long] = options[short]
    if args[1] == "api":
        request_headers = {}
        for raw_header in options.get("-H", []) + options.get("--header", []):
            name, _, value = raw_header.partition(":")
            request_headers[name.strip()] = value.strip()
        # What is sent is what gh would send: the one reading admission also uses.
        call = _gh_api_call(args[2:], stdin=kwargs.get("input"), cwd=client.cwd)
        if call is None or call.unresolved:
            return _native_command(args, client, runner, kwargs)
        try:
            endpoint, payload = call.build()
        except GitHubUnpreparedRequest:
            # A source this client will not read stays gh's own, inside the same admission.
            return _native_command(args, client, runner, kwargs)
        if "--input" in options:
            json.loads(payload)
        method = call.method
        if "--paginate" in options and method == "GET":
            # gh applies --jq to each page, and prints a non-list page as its
            # own document. A merged value is a different result, so those
            # shapes keep the native command. List pages concatenate; --slurp
            # wraps every page.
            if "--slurp" not in options and ("--jq" in options or "-q" in options):
                return _native_command(args, client, runner, kwargs)
            pages = _pages(client, endpoint, timeout=timeout, fresh=fresh, paginate=True)
            if isinstance(pages, Result):
                result = pages
            elif "--slurp" not in options and any(not isinstance(page.value, list) for page in pages):
                return _native_command(args, client, runner, kwargs)
            else:
                result = pages[0]
                result.value = (
                    [page.value for page in pages]
                    if "--slurp" in options
                    else [item for page in pages for item in page.value]
                )
                _merge_observation(result, *pages)
        else:
            result = client.request(
                method, endpoint, payload=payload, timeout=timeout, fresh=fresh, headers=request_headers
            )
    else:
        kind, action = args[1:3]
        if action == "download":
            result = _download_command(client, kind, options, positional, timeout=timeout)
        elif action in {"view", "list", "checks", "diff"}:
            result = _read_command(client, kind, action, options, positional, timeout=timeout, fresh=fresh)
        else:
            result = _write_command(
                client, kind, action, options, positional, timeout=timeout, input=kwargs.get("input")
            )
    # REST 404 is not gh's "Could not resolve to a PullRequest". Review
    # checkouts encode issue numbers, and only native gh distinguishes that
    # absence from an unreadable guard.
    if (
        args[1:3] == ["pr", "view"]
        and result.status == 404
        and result.error in {"github_http_error", "github_pr_not_found"}
    ):
        return _native_command(args, client, runner, kwargs)
    return _result_process(args, result, options, kwargs, api=args[1] == "api")


def run(args, *, runner=None, client=None, fresh=False, allow_stale=False, **kwargs):
    """Return command/configuration errors through the subprocess contract.

    A landing verb or CI status read is one landing operation: the reads it makes (the
    merge's queue lookup, the pull request behind a check rollup) share its landing class.
    """
    try:
        with _landing_operation(_argv_landing_flow(args) if args else None):
            return _run_command(args, runner=runner, client=client, fresh=fresh, allow_stale=allow_stale, **kwargs)
    except ValueError:
        return _result_process(args, Result(error="github_invalid_command"), {}, kwargs)


def check_output(args, **kwargs):
    kwargs.pop("check", None)
    return run(args, check=True, stdout=subprocess.PIPE, **kwargs).stdout


def http_open(request, *, timeout=30, opener=None, **kwargs):
    """HTTP seam for existing TLS/redirect-constrained GitHub integrations.

    The supplied opener keeps its security policy. Credential lifecycle
    responses are never cached; only budget headers are persisted.
    """
    import io
    import urllib.error
    import urllib.request

    client = GitHubClient(
        env={
            "GH_HOST": request.full_url,
            "GH_TOKEN": request.get_header("Authorization") or "http-unauthenticated",
            "GH_ENTERPRISE_TOKEN": request.get_header("Authorization") or "http-unauthenticated",
        }
    )
    if client.host in _api_hosts("github.com"):
        client._configure_host("github.com")
    method = request.get_method()
    # The opener sends ``request`` itself. Admission reads its body only if the decision needs
    # it, capturing it once (:class:`_DeferredBody`); the opener then sends exactly those bytes.
    body = _DeferredBody(request.data) if request.data is not None else None

    def transport(_method, endpoint, headers, _body, request_timeout):
        outgoing = body.request_for(request) if body is not None else request
        for key, value in headers.items():
            if key.lower() not in {k.lower() for k in outgoing.headers}:
                outgoing.add_header(key, value)
        try:
            opened = (opener or urllib.request.urlopen)(outgoing, timeout=request_timeout, **kwargs)
        except urllib.error.HTTPError as exc:
            opened = exc
        with opened as response:
            return Response(response.status, dict(response.headers.items()), response.read())

    client.transport = transport
    try:
        # POST/DELETE token endpoints contain sensitive responses and have no read cache.
        result = client.request(
            method,
            request.full_url,
            payload=body,
            timeout=timeout,
            fresh=True,
            raw_response=True,
            headers=dict(request.header_items()),
        )
    finally:
        if body is not None:
            body.close()
    if result.error == GitHubUnpreparedRequest.code:
        raise GitHubUnpreparedRequest(result.reason)
    if result.error and result.error != "github_rate_limited":
        encoded = json.dumps(result.value).encode()
        raise urllib.error.HTTPError(
            request.full_url, result.status, "GitHub HTTP request failed", result.headers, io.BytesIO(encoded)
        )
    value = result.require_fresh()
    stream = io.BytesIO(value if isinstance(value, bytes) else json.dumps(value).encode() if value is not None else b"")
    stream.status = result.status
    stream.headers = result.headers
    return stream


def command(args, *, runner=None, **kwargs):
    """Preserve the publisher's injectable whole-command test seam.

    Production uses ``run``; injected command executors replace the entire
    client, rather than pretending to be an HTTP transport. HTTP-level tests
    inject GitHubClient.transport instead.
    """
    if runner is None:
        return run(args, **kwargs)
    kwargs["env"] = colour_safe_environment(kwargs.get("env"))
    return runner(args, **kwargs)


def rest_read(operation, repo, fields, *, runner=None, env=None, cwd=None, **kwargs):
    """REST equivalents of former named GraphQL reads, with legacy shapes; merge facts are a landing flow."""
    with _landing_operation("merge-facts" if operation == "merge-facts" else None):
        return _rest_read(operation, repo, fields, runner=runner, env=env, cwd=cwd, **kwargs)


def _rest_read(operation, repo, fields, *, runner=None, env=None, cwd=None, **kwargs):
    client = GitHubClient(env=env, cwd=cwd)
    observed = []

    def get(endpoint, *, paginate=False, optional=False):
        args = ["gh", "api", "--method", "GET", endpoint]
        if paginate:
            args += ["--paginate"]
        proc = (
            command(
                args,
                runner=runner,
                client=client,
                fresh=operation != "budget",
                capture_output=True,
                text=True,
                cwd=cwd,
                env=env,
                timeout=kwargs.get("timeout"),
            )
            if runner is None
            else command(
                args, runner=runner, capture_output=True, text=True, cwd=cwd, env=env, timeout=kwargs.get("timeout")
            )
        )
        observed.append(getattr(proc, "github_result", None))
        if proc.returncode:
            observation = getattr(proc, "github_result", None)
            if optional and observation and observation.status == 404:
                return None
            if optional and runner is not None:
                # Command adapters may serialize the client's typed result.
                with suppress(ValueError, TypeError):
                    detail = json.loads(proc.stdout)
                    if detail.get("error") == "github_http_error" and detail.get("status") == 404:
                        return None
            refusal = refusal_of(proc, injected=runner is not None)
            if refusal is not None:
                raise refusal
            raise RuntimeError("GitHub REST read failed")
        return json.loads(proc.stdout)

    root = f"repos/{repo}"
    try:
        if operation == "budget":
            rate = get("rate_limit")["resources"]["graphql"]
            from datetime import UTC, datetime

            value = {
                "data": {
                    "rateLimit": {
                        **{k: rate[k] for k in ("limit", "remaining", "used")},
                        "resetAt": datetime.fromtimestamp(rate["reset"], UTC).isoformat().replace("+00:00", "Z"),
                    }
                }
            }
        elif operation == "default-head":
            repository = get(root)
            branch = repository["default_branch"]
            head = get(root + "/commits/" + quote(branch, safe=""))
            value = {
                "data": {
                    "repository": {
                        "nameWithOwner": repository["full_name"],
                        "defaultBranchRef": {"name": branch, "target": {"oid": head["sha"]}},
                    }
                }
            }
        elif operation == "pr-bases":
            rows = get(root + "/pulls?state=open&per_page=100", paginate=True)
            count = get("search/issues?" + urlencode({"q": f"repo:{repo} is:pr is:open", "per_page": 1}))
            if count.get("incomplete_results") is not False or type(count.get("total_count")) is not int:
                raise ValueError("incomplete GitHub search")
            value = {
                "data": {
                    "repository": {
                        "pullRequests": {
                            "totalCount": count["total_count"],
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [{"number": r["number"], "baseRefOid": r["base"]["sha"]} for r in rows],
                        }
                    }
                }
            }
        elif operation == "issue-states":
            states = {}
            for number in fields["numbers"]:
                issue = get(root + f"/issues/{number}", optional=True)
                states[f"i{number}"] = {"number": number, "state": str(issue["state"]).upper()} if issue else None
            value = {"data": {"repository": states}}
        elif operation in {"issue-parent", "issue-scope", "subissues", "subissues-next", "subissue-batch"}:

            def connection(number, cursor=None):
                if cursor is not None:
                    # This client returns complete REST collections. An opaque
                    # GraphQL cursor cannot safely be reinterpreted as a page.
                    raise ValueError("obsolete GitHub pagination cursor")
                rows = get(root + f"/issues/{number}/sub_issues?per_page=100", paginate=True)
                nodes = [
                    {
                        "number": r["number"],
                        "repository": {"nameWithOwner": r["repository_url"].split("/repos/", 1)[1]},
                        "subIssuesSummary": {"total": (r.get("sub_issues_summary") or {}).get("total")},
                    }
                    for r in rows
                ]
                return {"nodes": nodes, "pageInfo": {"hasNextPage": False, "endCursor": None}}

            if operation == "subissue-batch":
                issues = {}
                for number, cursor in fields["cursors"].items():
                    parent = get(root + f"/issues/{number}", optional=True)
                    if parent is None:
                        issues[f"i{number}"] = None
                        continue
                    issue = {"subIssues": connection(number, cursor)}
                    if number in fields["body_roots"] and cursor is None:
                        issue["body"] = parent["body"]
                    issues[f"i{number}"] = issue
                value = {"data": {"repository": issues}}
            else:
                number = fields["number"]
                issue = get(root + f"/issues/{number}")
                if operation in {"issue-parent", "issue-scope"}:
                    parent = get(root + f"/issues/{number}/parent", optional=True)
                    parent = (
                        {
                            "number": parent["number"],
                            "url": parent["html_url"],
                            "repository": {"nameWithOwner": parent["repository_url"].split("/repos/", 1)[1]},
                        }
                        if parent
                        else None
                    )
                    row = {
                        "number": issue["number"],
                        "state": str(issue["state"]).upper(),
                        "url": issue["html_url"],
                        "parent": parent,
                    }
                    if operation == "issue-scope":
                        row.update(body=issue["body"], labels={"nodes": [{"name": r["name"]} for r in issue["labels"]]})
                else:
                    row = {"body": issue["body"], "subIssues": connection(number, fields.get("cursor"))}
                value = {
                    "data": {
                        "repository": {"nameWithOwner": issue["repository_url"].split("/repos/", 1)[1], "issue": row}
                    }
                }
        elif operation == "merge-facts":
            groups = {}
            for slug, number in fields["batch"]:
                groups.setdefault(slug, []).append(number)
            data, errors = {}, []
            for i, (slug, numbers) in enumerate(groups.items()):
                alias = f"r{i}"
                data[alias] = {}
                for number in numbers:
                    pull_alias = f"p{number}"
                    try:
                        pull = get(f"repos/{slug}/pulls/{number}")
                        data[alias][pull_alias] = {"mergedAt": pull["merged_at"]}
                    except GitHubRateLimited:
                        raise
                    except (RuntimeError, ValueError, KeyError, TypeError):
                        errors.append({"message": "GitHub pull request lookup failed", "path": [alias, pull_alias]})
            value = {"data": data}
            if errors:
                value["errors"] = errors
        else:
            raise ValueError("unknown REST read")
    except GitHubRateLimited as exc:
        result = Result(error=exc.code, reset_at=exc.reset_at, status=429, reason=exc.reason)
    except (ValueError, KeyError, TypeError):
        result = Result(error="github_invalid_read")
    except RuntimeError:
        result = Result(error="github_read_failed", status=502)
    else:
        result = Result(
            value,
            stale=any(r.stale for r in observed if r),
            age_seconds=max((r.age_seconds for r in observed if r), default=0),
            reset_at=next((r.reset_at for r in observed if r and r.reset_at), None),
            reason=next((r.reason for r in observed if r and r.reason), None),
        )
    return _result_process(["github", operation], result, {}, kwargs)


def queue_read(operation, repo, fields, *, env=None, cwd=None, **kwargs):
    """Queue-only GraphQL fields joined to ordinary conditional REST reads; a landing flow."""
    with _landing_operation("queue-read"):
        return _queue_read(operation, repo, fields, env=env, cwd=cwd, **kwargs)


def _queue_read(operation, repo, fields, *, env=None, cwd=None, **kwargs):
    client = GitHubClient(env=env, cwd=cwd)
    timeout = kwargs.get("timeout") or 30
    owner, name = repo.split("/", 1)
    observations = []
    if operation == "queue-snapshot":
        ordinary = _read_command(
            client,
            "pr",
            "list",
            {
                "--repo": [repo],
                "--state": ["open"],
                "--limit": ["1000"],
                "--json": ["id,number,title,isDraft,headRefOid,baseRefName,mergeStateStatus,labels"],
            },
            [],
            timeout=timeout,
            fresh=True,
        )
        observations.append(ordinary)
        if ordinary.error:
            return _result_process(["github", operation], ordinary, {}, kwargs)
        rows = ordinary.value
        selections = " ".join(
            f"p{r['number']}:pullRequest(number:{r['number']}){{isInMergeQueue autoMergeRequest{{enabledAt}}}}"
            for r in rows
        )
        selections += " " + " ".join(
            f"q{i}:mergeQueue(branch:{json.dumps(branch)}){{url}}"
            for i, branch in enumerate(sorted(fields["branches"]))
        )
        query = (
            "query($owner:String!,$name:String!){rateLimit{remaining cost resetAt} repository(owner:$owner,name:$name){"
            + selections
            + "}}"
        )
        response = client.request(
            "POST", "graphql", payload={"query": query, "variables": {"owner": owner, "name": name}}, timeout=timeout
        )
        if response.error:
            return _result_process(["github", operation], response, {}, kwargs)
        observations.append(response)
        data = response.value.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("repository"), dict):
            return _result_process(["github", operation], Result(error="github_queue_unknown"), {}, kwargs)
        repository = data["repository"]
        for row in rows:
            membership = repository.pop(f"p{row['number']}", None)
            row["isInMergeQueue"] = membership.get("isInMergeQueue") if isinstance(membership, dict) else None
            row["autoMergeRequest"] = membership.get("autoMergeRequest") if isinstance(membership, dict) else None
        repository["pullRequests"] = {"totalCount": len(rows), "pageInfo": {"hasNextPage": False}, "nodes": rows}
        value = response.value
    elif operation == "queue-status":
        # These are internal REST facts, including the derived merged
        # boolean; they are not a gh --json command vocabulary.
        ordinary = _read_command(
            client,
            "pr",
            "view",
            {
                "--repo": [repo],
                "--json": ["number,title,state,merged,mergeable,mergeStateStatus,headRefName,headRefOid,baseRefName"],
            },
            [str(fields["number"])],
            timeout=timeout,
            fresh=True,
        )
        if ordinary.error:
            return _result_process(["github", operation], ordinary, {}, kwargs)
        observations.append(ordinary)
        query = "query($owner:String!,$name:String!,$number:Int!,$branch:String!){repository(owner:$owner,name:$name){pullRequest(number:$number){isInMergeQueue isMergeQueueEnabled mergeQueueEntry{id position state enqueuedAt estimatedTimeToMerge jump solo headCommit{oid}}} mergeQueue(branch:$branch){url nextEntryEstimatedTimeToMerge entries(first:50){totalCount nodes{position state enqueuedAt estimatedTimeToMerge pullRequest{number}}}}}}"
        response = client.request(
            "POST",
            "graphql",
            payload={"query": query, "variables": {"owner": owner, "name": name, **fields}},
            timeout=timeout,
        )
        if response.error:
            return _result_process(["github", operation], response, {}, kwargs)
        observations.append(response)
        value = response.value
        repository = (value.get("data") or {}).get("repository")
        if isinstance(repository, dict) and isinstance(repository.get("pullRequest"), dict):
            repository["pullRequest"] = {**ordinary.value, **repository["pullRequest"]}
    else:
        raise ValueError("unknown queue operation")
    result = Result(
        value,
        stale=any(r.stale for r in observations),
        age_seconds=max(r.age_seconds for r in observations),
        reset_at=next((r.reset_at for r in observations if r.reset_at), None),
        reason=next((r.reason for r in observations if r.reason), None),
    )
    return _result_process(["github", operation], result, {}, kwargs)


def _graphql_errors(value):
    """Return the response's ``errors`` entries; any other shape has none."""
    errors = value.get("errors") if isinstance(value, dict) else None
    return errors if isinstance(errors, list) else []


def _graphql_error_detail(value):
    """Redacted ``type`` and ``message`` of each object error; other entries are dropped."""
    from scripts.opsec.prepublish import CREDENTIAL_TOKEN_PATTERN

    def text(field):
        return CREDENTIAL_TOKEN_PATTERN.sub("[REDACTED]", field)[:500] if isinstance(field, str) else None

    return [
        {"type": text(entry.get("type")), "message": text(entry.get("message"))}
        for entry in _graphql_errors(value)
        if isinstance(entry, dict)
    ]


def _result_process(args, result, options, kwargs, *, api=True):
    if result.error:
        detail = {"error": result.error, "reset_at": result.reset_at}
        if result.error == "github_rate_limited":
            detail["reason"] = result.reason
        elif result.error == "github_http_error":
            detail["status"] = result.status
        elif result.error == GitHubUnpreparedRequest.code:
            detail["reason"] = result.reason
        elif result.error == "github_graphql_error":
            detail["errors"] = _graphql_error_detail(result.value)
        output = json.dumps(detail).encode()
        error = output
        code = 75 if result.error == "github_rate_limited" else 1
    else:
        output = _format_value(result.value, options, api=api)
        error = (
            json.dumps({"stale": True, "age_seconds": result.age_seconds, "reset_at": result.reset_at}).encode()
            if result.stale
            else b""
        )
        code = 0
    if kwargs.get("text") or kwargs.get("universal_newlines") or kwargs.get("encoding"):
        output, error = output.decode(kwargs.get("encoding") or "utf-8"), error.decode()
    completed = subprocess.CompletedProcess(args, code, output, error)
    completed.github_result = result
    for key, content in (("stdout", output), ("stderr", error)):
        target = kwargs.get(key)
        if target not in (None, subprocess.PIPE, subprocess.DEVNULL, subprocess.STDOUT):
            target.write(content)
        elif target is None and not kwargs.get("capture_output"):
            import sys

            stream = getattr(sys, key)
            if isinstance(content, bytes):
                stream.buffer.write(content)
            else:
                stream.write(content)
    if kwargs.get("check") and code:
        failure = subprocess.CalledProcessError(code, args, output=output, stderr=error)
        failure.github_result = result
        raise failure
    return completed


def _download_command(client, kind, options, positional, *, timeout):
    import fnmatch
    import io
    import stat
    import zipfile

    repo = _repo(options, client)
    root = f"repos/{repo}"
    pattern = _opt(options, "--pattern", "-p", default="*")
    if kind == "release":
        tag = positional[0] if positional else None
        release = client.request(
            "GET",
            root + "/releases/" + ("tags/" + quote(tag, safe="") if tag else "latest"),
            timeout=timeout,
            fresh=True,
        )
        if release.error:
            return release
        selected = [r for r in release.value.get("assets", []) if fnmatch.fnmatchcase(r["name"], pattern)]
    elif kind == "run":
        pages = _pages(
            client,
            f"{root}/actions/runs/{positional[0]}/artifacts?per_page=100",
            timeout=timeout,
            fresh=True,
            paginate=True,
        )
        if isinstance(pages, Result):
            return pages
        selected = [
            r
            for page in pages
            for r in page.value["artifacts"]
            if fnmatch.fnmatchcase(r["name"], pattern) and not r.get("expired")
        ]
    else:
        return Result(error="github_unsupported_command")
    if not selected:
        return Result(error="github_asset_not_found")
    output = _opt(options, "--output", "-O")
    if output and len(selected) != 1:
        return Result(error="github_asset_ambiguous")
    directory = Path(_opt(options, "--dir", "-D", default=client.cwd or Path.cwd()))
    for row in selected:
        endpoint = f"{root}/releases/assets/{row['id']}" if kind == "release" else row["archive_download_url"]
        downloaded = client.request(
            "GET", endpoint, headers={"Accept": "application/octet-stream"}, timeout=timeout, fresh=True
        )
        if downloaded.error:
            return downloaded
        if not isinstance(downloaded.value, bytes):
            return Result(error="github_asset_invalid")
        if output == "-":
            return downloaded
        if kind == "release":
            destination = Path(output) if output else directory / row["name"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(downloaded.value)
        else:
            destination = directory if len(selected) == 1 else directory / row["name"]
            destination.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(downloaded.value)) as archive:
                for member in archive.infolist():
                    path = Path(member.filename)
                    if path.is_absolute() or ".." in path.parts or stat.S_ISLNK(member.external_attr >> 16):
                        return Result(error="github_archive_unsafe")
                    target = (destination / path).resolve()
                    if not target.is_relative_to(destination.resolve()):
                        return Result(error="github_archive_unsafe")
                archive.extractall(destination)
    return Result("")


def timer(function):
    """A timer skips one run on a typed limit; it does not wait or retry."""
    from functools import wraps

    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except GitHubRateLimited as exc:
            print(f"GitHub timer: skipped github_rate_limited reset_at={exc.reset_at} reason={exc.reason}")
            return 0
        except subprocess.CalledProcessError as exc:
            observation = getattr(exc, "github_result", None)
            if (
                exc.returncode != 75
                or not isinstance(observation, Result)
                or observation.error != "github_rate_limited"
            ):
                raise
            reset = observation.reset_at
            print(f"GitHub timer: skipped github_rate_limited reset_at={reset} reason={observation.reason}")
            return 0

    return wrapped


def rate_limited_command(function):
    """Keep an exhausted publishing preflight in the typed command contract.

    On the publisher's vetted ``publish`` entry point, a verb that lands a PR runs as one
    landing operation, so its readiness and recovery reads share the verb's landing class.
    """
    from functools import wraps

    code = getattr(function, "__code__", None)
    vetted = code is not None and _code_identity(code) == (
        os.path.realpath(_REPOSITORY / _PUBLISHER_ENTRY_POINT[0]),
        _PUBLISHER_ENTRY_POINT[1],
    )

    @wraps(function)
    def wrapped(*args, **kwargs):
        verb = args[0] if args else kwargs.get("verb")
        landing = vetted and isinstance(verb, str) and verb in _PUBLISHER_LANDING_VERBS
        try:
            with _landing_operation("publisher-landing-verb" if landing else None):
                return function(*args, **kwargs)
        except GitHubRateLimited as exc:
            result = Result(error=exc.code, reset_at=exc.reset_at, status=429, reason=exc.reason)
            return _result_process(["github", "publish"], result, {}, kwargs)

    return wrapped
