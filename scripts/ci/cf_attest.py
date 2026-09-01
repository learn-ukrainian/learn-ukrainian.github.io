#!/usr/bin/env python3
"""Fail-closed exact-head cross-family review lock for CI Gate.

``cf-attest`` is a needs-job that CI Gate aggregates. It passes only when the
PR has an independent CF of record (comment or review body) whose attested
head SHA matches the **PR head**, not a merge_group merge commit.

Stdlib only so the job can sparse-checkout ``scripts/ci`` and run with system
``python3``. It never calls OpenRouter and does not invent a new CF protocol:
it accepts comment shapes already used on this repo.

CF of record contract (durable seat path under a shared GitHub identity,
issue #7472 — do **not** invent a second GitHub login; native
``gh pr review --approve`` cannot satisfy required-review forge controls when
author == approver, and AGENT_NO_MERGE keeps merge/--approve blocked):

Post with ``gh pr comment <N> --body ...`` a body that ``parse_attestation``
accepts:

* CF marker: ``cross-family`` / ``cf of record`` / ``reviewer provenance``
* ``Verdict: APPROVE`` (or approved / pass / passed; markdown emphasis like
  ``**VERDICT: APPROVE**`` or ``VERDICT: **APPROVE**`` is fine)
* Exact head SHA (labeled ``head`` / ``exact-head``, or the sole 40-char SHA)
* Reviewer family resolving to a concrete family in ``CONCRETE_FAMILIES``,
  from a ``Reviewer family:`` line OR a ``resolved_model:`` model id mapped
  through the same ``normalize_family`` resolver the Gate uses

Example shape already in use on this repo::

    **VERDICT: APPROVE**

    Cross-family review of record (Codex)
    Reviewer family: OpenAI
    At exact head ``<40-char-sha>``
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

SHA_RE = re.compile(r"\b([0-9a-f]{40})\b", re.IGNORECASE)
X_AGENT_RE = re.compile(
    r"^X-Agent:\s+(?P<agent>[A-Za-z0-9._:-]+)/(?P<task>[A-Za-z0-9._-]+)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
PR_NUMBER_RE = re.compile(r"(?:^|/)pr-([1-9][0-9]*)(?:/|-|_|\b)", re.IGNORECASE)
CF_MARKER_RE = re.compile(
    r"\b(?:cross[- ]family|cf of record|reviewer provenance)\b",
    re.IGNORECASE,
)
VERDICT_APPROVE_RE = re.compile(
    # Markdown emphasis around the token or the value is fine:
    # ``**VERDICT: APPROVE**`` and ``VERDICT: **APPROVE**`` both attest.
    r"\bverdict\s*:\s*\**\s*(?:approve[d]?|pass(?:ed)?)\b",
    re.IGNORECASE,
)
VERDICT_BLOCK_RE = re.compile(
    r"\bverdict\s*:\s*\**\s*(?:"
    r"changes?[-_ ]requested|request(?:ed)?[-_ ]changes?|needs?[-_ ]work|"
    r"blocked|reject(?:ed)?|fail(?:ed|ure)?|revise"
    r")\b",
    re.IGNORECASE,
)
HEAD_LABELED_RE = re.compile(
    r"(?:"
    r"(?:\bat\s+(?:exact\s+)?)?head(?:\s+sha)?\b|"
    r"exact[- ]head"
    r")\s*[:=]?\s*`?([0-9a-f]{40})`?",
    re.IGNORECASE,
)
FAMILY_LABELED_RE = re.compile(
    r"(?:reviewer\s+family|family)\s*[:=]\s*([^\n;]+)",
    re.IGNORECASE,
)
# #M-4 (2026-09-01): reviewers increasingly record their model instead of a
# family line (``resolved_model: claude-sonnet-5``). It resolves through the
# same normalize_family resolver the Gate uses; unresolvable still fails
# closed.
RESOLVED_MODEL_RE = re.compile(
    r"\bresolved_model\s*[:=]\s*([^\n;]+)",
    re.IGNORECASE,
)
VERDICT_PRESENT_RE = re.compile(r"\bverdict\s*:", re.IGNORECASE)
CF_PAREN_RE = re.compile(
    r"\b(?:cross[- ]family(?:\s+(?:review|cf))?|cf of record)\b[^\n(]{0,40}\(([^)]+)\)",
    re.IGNORECASE,
)

FAMILY_UNKNOWN = "unknown"
FAMILY_FIXTURE = "fixture"
FAMILY_CURSOR_AUTO_UNION = "cursor-auto-union"
CURSOR_AUTO_UNION_FAMILIES = frozenset({"xai", "moonshot"})
CONCRETE_FAMILIES = frozenset(
    {
        "google",
        "anthropic",
        "openai",
        "deepseek",
        "xai",
        "moonshot",
        "zhipu",
        "poolside",
        "qwen",
    }
)

# Mirrors scripts/audit/model_families.py token rules plus X-Agent seat names
# from lint_agent_trailer.py. Kept local so this job stays stdlib-only.
_FAMILY_TOKEN_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("deepseek",), "deepseek"),
    (("gemma", "gemini", "agy", "antigravity", "google"), "google"),
    (("codex", "openai", "gpt"), "openai"),
    (("anthropic", "claude", "fable", "opus", "sonnet"), "anthropic"),
    (("grok", "xai"), "xai"),
    (("composer-2.5", "kimi"), "moonshot"),
    (("glm", "zhipu"), "zhipu"),
    (("poolside", "laguna"), "poolside"),
    (("qwen",), "qwen"),
    (("dependabot",), FAMILY_FIXTURE),
)

_CURSOR_SEATS = frozenset({"cursor", "cursor-tools", "cursor-auto"})
NOOP_EVENTS = frozenset({"push", "schedule", "workflow_dispatch"})
PR_EVENTS = frozenset({"pull_request", "merge_group"})
GITHUB_API_TIMEOUT_SECONDS = 10
ApiGet = Callable[[str], Any]


@dataclass(frozen=True, slots=True)
class ParsedAttestation:
    """One parsed CF comment/review body."""

    head_sha: str
    reviewer_family: str
    verdict: str
    source: str
    # Attestation binds to the FIRST labeled SHA — the "At exact head" header
    # line per the posting contract. History-recap lines later in the body
    # neither bind nor stale-reject (CF r1 on this PR rejected match-any:
    # it let one body attest several heads).
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class AttestResult:
    """Pass/fail of the mechanical CF lock."""

    ok: bool
    reason: str
    expected_head: str = ""
    attested_head: str = ""
    author_family: str = ""
    reviewer_family: str = ""


def _compile_family_patterns() -> tuple[tuple[re.Pattern[str], str], ...]:
    compiled: list[tuple[re.Pattern[str], str]] = []
    for markers, family in _FAMILY_TOKEN_RULES:
        alternation = "|".join(re.escape(marker) for marker in markers)
        compiled.append(
            (re.compile(rf"(?:^|[^a-z0-9])(?:{alternation})(?:$|[^a-z0-9])"), family)
        )
    return tuple(compiled)


_FAMILY_PATTERNS = _compile_family_patterns()


def normalize_family(value: str) -> str:
    """Normalize a seat, model id, or prose token to a family."""
    text = (value or "").strip().casefold()
    if not text:
        return FAMILY_UNKNOWN
    if text in {FAMILY_FIXTURE, "adversarial-fixture"}:
        return FAMILY_FIXTURE
    if text == FAMILY_CURSOR_AUTO_UNION:
        return FAMILY_CURSOR_AUTO_UNION
    if text in _CURSOR_SEATS or text in {"auto", "composer"}:
        return FAMILY_CURSOR_AUTO_UNION
    for pattern, family in _FAMILY_PATTERNS:
        if pattern.search(text):
            return family
    if text in CONCRETE_FAMILIES:
        return text
    return FAMILY_UNKNOWN


def author_family_from_agents(agents: Iterable[str]) -> str:
    """Resolve X-Agent seats to the author family, or a '+'-joined union.

    Unparseable seats still fail closed to UNKNOWN; multiple concrete
    families resolve to a canonical sorted union token whose independence
    check is stricter (reviewer outside every member).
    """
    families: set[str] = set()
    saw_cursor = False
    for raw in agents:
        family = normalize_family(raw)
        if family == FAMILY_CURSOR_AUTO_UNION:
            saw_cursor = True
            continue
        if family == FAMILY_UNKNOWN:
            return FAMILY_UNKNOWN
        families.add(family)
    # #7487: the dependabot token maps to the fixture family (universal
    # independence — legitimate for pure dependabot PRs). One smuggled
    # ``X-Agent: dependabot/x`` trailer must not neutralize a mixed PR's
    # real author family, so fixture is ignored whenever any concrete
    # family is present.
    if FAMILY_FIXTURE in families and (len(families) > 1 or saw_cursor):
        families.discard(FAMILY_FIXTURE)
    if len(families) > 1:
        # Multi-family authorship (e.g. a driver landing a reviewer-prescribed
        # fix on a worker's PR) is legitimate and STRICTER, not looser: the
        # reviewer must be independent of EVERY author family. Encode the set
        # as a canonical '+'-joined token; families_independent() enforces
        # union independence. (Previously fail-closed to UNKNOWN, which made
        # every co-authored PR permanently unattestable — 2026-09-01, #7571.)
        return "+".join(sorted(families))
    if len(families) == 1:
        return next(iter(families))
    if saw_cursor:
        return FAMILY_CURSOR_AUTO_UNION
    return FAMILY_UNKNOWN


def x_agent_seats_from_messages(messages: Iterable[str]) -> tuple[str, ...]:
    seats: list[str] = []
    for message in messages:
        if not isinstance(message, str):
            continue
        for match in X_AGENT_RE.finditer(message):
            seats.append(match.group("agent").strip().casefold())
    return tuple(seats)


def parse_pr_number(head_ref: str) -> int | None:
    """Parse the grouped PR number from a merge_group head_ref."""
    match = PR_NUMBER_RE.search(head_ref or "")
    if match is None:
        return None
    return int(match.group(1))


def _first_labeled_sha(text: str) -> str | None:
    match = HEAD_LABELED_RE.search(text)
    if match is None:
        return None
    return match.group(1).lower()


def _labeled_shas(text: str) -> tuple[str, ...]:
    return tuple(match.group(1).lower() for match in HEAD_LABELED_RE.finditer(text))


def _family_text(body: str) -> str:
    """Family evidence: ``Reviewer family:`` line, ``resolved_model:`` line,
    or the CF parenthetical — in that order of precedence."""
    labeled = FAMILY_LABELED_RE.search(body)
    if labeled is not None:
        return labeled.group(1)
    model = RESOLVED_MODEL_RE.search(body)
    if model is not None:
        return model.group(1)
    paren = CF_PAREN_RE.search(body)
    if paren is not None:
        return paren.group(1)
    return ""


def parse_attestation(
    body: str, *, source: str = "comment", created_at: str = ""
) -> ParsedAttestation | None:
    """Parse one existing CF comment shape, or None if it is not CF of record.

    #7487: a body whose verdict is a block/changes-request is parsed as a
    REVOCATION (verdict="BLOCK") instead of being dropped — evaluation is
    latest-wins per reviewer family, so an earlier APPROVE cannot survive a
    later block at the same head.
    """
    if not isinstance(body, str) or not body.strip():
        return None
    if not CF_MARKER_RE.search(body):
        return None
    blocked = VERDICT_BLOCK_RE.search(body) is not None
    if not blocked and not VERDICT_APPROVE_RE.search(body):
        return None

    labeled_heads = _labeled_shas(body)
    sha = labeled_heads[0] if labeled_heads else None
    if sha is None:
        found = {match.group(1).lower() for match in SHA_RE.finditer(body)}
        if len(found) != 1:
            return None
        sha = next(iter(found))

    family_text = _family_text(body)
    reviewer_family = normalize_family(family_text)
    if reviewer_family not in CONCRETE_FAMILIES:
        return None
    return ParsedAttestation(
        head_sha=sha,
        reviewer_family=reviewer_family,
        verdict="BLOCK" if blocked else "APPROVE",
        source=source,
        created_at=created_at,
    )


def diagnose_attest_comment(body: str, *, expected_head: str = "") -> str | None:
    """Explain why a VERDICT-bearing comment cannot attest, else ``None``.

    The on-comment workflow posts this as ONE short gap comment so a verdict
    that misses the contract is never skipped silently (#M-4, 2026-09-01: a
    ``**VERDICT: APPROVE**`` + ``resolved_model:`` comment with no
    ``Reviewer family:`` line was dropped without any feedback).
    """
    if not isinstance(body, str) or not VERDICT_PRESENT_RE.search(body):
        return None
    parsed = parse_attestation(body)
    if parsed is not None:
        head = (expected_head or "").strip().lower()
        if head and SHA_RE.fullmatch(head) and parsed.head_sha != head:
            return (
                f"it attests `{parsed.head_sha}` but the current PR head is "
                f"`{head}` — repost the verdict against the current head"
            )
        return None
    gaps: list[str] = []
    if not CF_MARKER_RE.search(body):
        gaps.append("a cross-family marker (e.g. `Cross-family review of record (<seat>)`)")
    if not VERDICT_APPROVE_RE.search(body) and not VERDICT_BLOCK_RE.search(body):
        gaps.append("a recognized verdict (`VERDICT: APPROVE` or `VERDICT: CHANGES_REQUESTED`)")
    if _first_labeled_sha(body) is None:
        found = {match.group(1).lower() for match in SHA_RE.finditer(body)}
        if len(found) != 1:
            gaps.append("the exact head SHA (e.g. `At exact head `<40-char-sha>``)")
    if normalize_family(_family_text(body)) not in CONCRETE_FAMILIES:
        gaps.append(
            "a resolvable reviewer family — add `Reviewer family: <family>` "
            "or `resolved_model: <model-id>` (e.g. `resolved_model: claude-sonnet-5`)"
        )
    if not gaps:
        return None
    return "missing " + "; ".join(gaps)


def build_attest_feedback(note: str) -> str:
    """The one short bot comment for an unattestable VERDICT comment."""
    return (
        "CF attest: your `VERDICT:` comment could not be recorded — " + note + ".\n\n"
        "Expected shape (markdown emphasis around the verdict is fine):\n"
        "```\n"
        "**VERDICT: APPROVE**\n"
        "Cross-family review of record (<seat>)\n"
        "Reviewer family: <family>   # or a line like: resolved_model: <model-id>\n"
        "At exact head `<40-char-sha>`\n"
        "```"
    )


def families_independent(author_family: str, reviewer_family: str) -> bool:
    """True when the reviewer is a different concrete family from the author."""
    if reviewer_family not in CONCRETE_FAMILIES:
        return False
    if author_family == FAMILY_CURSOR_AUTO_UNION:
        return reviewer_family not in CURSOR_AUTO_UNION_FAMILIES
    if author_family == FAMILY_FIXTURE:
        return True
    if "+" in author_family:
        parts = set(author_family.split("+"))
        # Union independence: reviewer outside EVERY author family; any
        # non-concrete part fails closed.
        if not parts <= CONCRETE_FAMILIES:
            return False
        return reviewer_family not in parts
    if author_family not in CONCRETE_FAMILIES:
        return False
    return reviewer_family != author_family


def evaluate_attestation(
    *,
    expected_head: str,
    author_family: str,
    bodies: Sequence[tuple[str, ...]],
) -> AttestResult:
    """Return pass/fail for the supplied comment/review bodies against one SHA."""
    head = (expected_head or "").strip().lower()
    if not SHA_RE.fullmatch(head):
        return AttestResult(False, "unparseable attestation: invalid expected PR head SHA")
    if author_family in {FAMILY_UNKNOWN, ""}:
        return AttestResult(False, "unparseable attestation: author family", expected_head=head)

    parsed: list[ParsedAttestation] = []
    for entry in bodies:
        if len(entry) == 3:
            source, body, created_at = entry
        else:
            source, body = entry
            created_at = ""
        item = parse_attestation(body, source=source, created_at=created_at)
        if item is not None:
            parsed.append(item)
    # Chronological latest-wins across SOURCES (#7502 CF r1): comments and
    # reviews are fetched as separate lists, so list order alone let an older
    # review outrank a newer comment. Sort by created_at when present; the
    # sort is stable, so timestamp-less fixtures keep their list order.
    # Tie-break (#7502 CF r2): on EQUAL timestamps a BLOCK sorts after an
    # APPROVE so the standing verdict fails closed — a same-second approve
    # can never bury a same-second revocation.
    parsed.sort(key=lambda item: (item.created_at, item.verdict == "BLOCK"))
    if not parsed:
        return AttestResult(
            False,
            "missing CF: no independent exact-head APPROVE",
            expected_head=head,
            author_family=author_family,
        )

    matching = [item for item in parsed if item.head_sha == head]
    if not matching:
        attested = parsed[0].head_sha
        return AttestResult(
            False,
            f"stale CF: attested {attested} != PR head {head}",
            expected_head=head,
            attested_head=attested,
            author_family=author_family,
            reviewer_family=parsed[0].reviewer_family,
        )

    # Latest-wins per reviewer family (#7487): bodies arrive in API order
    # (chronological within comments, then reviews), so the LAST parsed item
    # for a family is its standing verdict at this head. An earlier APPROVE
    # must not survive a later block from the same family.
    standing: dict[str, ParsedAttestation] = {}
    for item in matching:
        standing[item.reviewer_family] = item

    approving = [
        item
        for item in standing.values()
        if item.verdict == "APPROVE"
        and families_independent(author_family, item.reviewer_family)
    ]
    if approving:
        item = approving[0]
        return AttestResult(
            True,
            "independent exact-head CF APPROVE",
            expected_head=head,
            attested_head=head,
            author_family=author_family,
            reviewer_family=item.reviewer_family,
        )
    revoked = [item for item in standing.values() if item.verdict == "BLOCK"]
    if revoked:
        return AttestResult(
            False,
            f"revoked CF: latest verdict from {revoked[0].reviewer_family} "
            "is a block at this head",
            expected_head=head,
            attested_head=head,
            author_family=author_family,
            reviewer_family=revoked[0].reviewer_family,
        )
    first = next(iter(standing.values()))
    return AttestResult(
        False,
        f"same-family review: author={author_family} reviewer={first.reviewer_family}",
        expected_head=head,
        attested_head=first.head_sha,
        author_family=author_family,
        reviewer_family=first.reviewer_family,
    )


def github_api_get(
    path: str,
    *,
    token: str | None = None,
    api_url: str | None = None,
    timeout: int = GITHUB_API_TIMEOUT_SECONDS,
) -> Any:
    """Read one GitHub REST resource with a bounded request."""
    base_url = (api_url or os.environ.get("GITHUB_API_URL") or "https://api.github.com").rstrip(
        "/"
    )
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{base_url}/{path.lstrip('/')}", headers=headers)
    # #7487: one transient 5xx / connection blip must not fail the Gate and
    # force a full re-run — bounded retries with short backoff, fail closed
    # after the budget. 4xx (auth, not-found, rate-limit-as-403) never retry.
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code < 500 or attempt == attempts:
                raise
        except (URLError, TimeoutError):
            if attempt == attempts:
                raise
        time.sleep(2 * attempt)
    raise ValueError("unreachable: retry loop exhausted")  # pragma: no cover


def github_api_post(
    path: str,
    payload: Mapping[str, Any] | None = None,
    *,
    token: str | None = None,
    api_url: str | None = None,
    timeout: int = GITHUB_API_TIMEOUT_SECONDS,
) -> Any:
    """POST one GitHub REST resource (gap comment, failed-jobs rerun).

    Single attempt: both callers are best-effort side effects layered on a
    fail-closed verdict, so a transient failure must surface as a warning,
    not hide behind retries.
    """
    base_url = (api_url or os.environ.get("GITHUB_API_URL") or "https://api.github.com").rstrip(
        "/"
    )
    headers = {"Accept": "application/vnd.github+json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(payload or {}).encode("utf-8")
    request = Request(f"{base_url}/{path.lstrip('/')}", data=data, headers=headers, method="POST")
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
    if not body.strip():
        return {}
    return json.loads(body)


RUN_ID_RE = re.compile(r"/actions/runs/([1-9][0-9]*)")
STALE_CHECK_CONCLUSIONS = frozenset({"FAILURE", "STALE", "TIMED_OUT"})
STALE_RUN_CONCLUSIONS = frozenset({"failure", "timed_out"})


def rerun_stale_failed_cf_attest(
    *,
    repository: str,
    head_sha: str,
    api_get: ApiGet,
    api_post: Callable[[str, Mapping[str, Any]], Any],
) -> str:
    """Re-run failed jobs of the initial failed CF attest run at ``head_sha``.

    #7548 built this path for the scheduled auto-arm scanner; the on-comment
    workflow could not reach it, so a freshly accepted verdict left the PR's
    ``CF attest`` check red until a human ran ``gh run rerun --failed``
    (#M-4, 2026-09-01). Idempotent: only a first-attempt completed failure
    at this exact head is rerun.
    """
    repo = (repository or "").strip()
    if "/" not in repo:
        raise ValueError("rerun-stale-failed: GITHUB_REPOSITORY missing")
    head = (head_sha or "").strip().lower()
    if not SHA_RE.fullmatch(head):
        raise ValueError("rerun-stale-failed: missing or malformed PR head SHA")
    quoted = quote(repo, safe="/")
    query = urlencode({"check_name": "CF attest", "filter": "latest"})
    payload = api_get(f"repos/{quoted}/commits/{head}/check-runs?{query}")
    check_runs = payload.get("check_runs") if isinstance(payload, Mapping) else None
    if not isinstance(check_runs, list):
        raise ValueError("rerun-stale-failed: check-runs payload malformed")
    candidates: list[int] = []
    for check in check_runs:
        if not isinstance(check, Mapping):
            continue
        if str(check.get("name") or "") != "CF attest":
            continue
        if str(check.get("status") or "").upper() != "COMPLETED":
            continue
        if str(check.get("conclusion") or "").upper() not in STALE_CHECK_CONCLUSIONS:
            continue
        match = RUN_ID_RE.search(str(check.get("details_url") or ""))
        if match is not None:
            candidates.append(int(match.group(1)))
    if not candidates:
        return "no failed/stale CF attest check run at this head; nothing to rerun"
    run_id = candidates[-1]
    run = api_get(f"repos/{quoted}/actions/runs/{run_id}")
    if not isinstance(run, Mapping):
        raise ValueError("rerun-stale-failed: workflow run payload malformed")
    if str(run.get("head_sha") or "").strip().lower() != head:
        return f"run {run_id} head SHA mismatch; not rerunning"
    if run.get("run_attempt") != 1:
        return f"run {run_id} already on attempt {run.get('run_attempt')}; not rerunning again"
    if (
        str(run.get("status") or "").upper() != "COMPLETED"
        or str(run.get("conclusion") or "").strip().lower() not in STALE_RUN_CONCLUSIONS
    ):
        return f"run {run_id} is not a completed failure; not rerunning"
    api_post(f"repos/{quoted}/actions/runs/{run_id}/rerun-failed-jobs", {})
    return f"requested rerun of failed jobs for run {run_id}"


def _api_items(payload: Any, key: str) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, Mapping)]
    if isinstance(payload, Mapping):
        items = payload.get(key)
        if isinstance(items, list):
            return [item for item in items if isinstance(item, Mapping)]
    return []


def fetch_paginated(
    path: str,
    *,
    api_get: ApiGet,
    per_page: int = 100,
    max_pages: int = 10,
) -> list[Mapping[str, Any]]:
    """Fetch a list endpoint; fail closed if the page budget is exhausted."""
    items: list[Mapping[str, Any]] = []
    separator = "&" if "?" in path else "?"
    for page in range(1, max_pages + 1):
        query = urlencode({"per_page": per_page, "page": page})
        payload = api_get(f"{path}{separator}{query}")
        batch = _api_items(payload, "items") if isinstance(payload, Mapping) else _api_items(
            payload, ""
        )
        if isinstance(payload, list):
            batch = [item for item in payload if isinstance(item, Mapping)]
        items.extend(batch)
        if len(batch) < per_page:
            return items
    raise ValueError(f"unparseable attestation: {path} exceeded page budget")


def resolve_pr_head_sha(
    *,
    event_name: str,
    event_sha: str,
    pr_head_sha: str,
    pr_number: str,
    merge_group_head_ref: str,
    repository: str,
    api_get: ApiGet | None = None,
) -> str:
    """Return the PR head SHA that CF must attest.

    ``pull_request`` uses ``pull_request.head.sha`` (not the test-merge
    ``github.sha``). ``merge_group`` resolves the grouped PR and uses that
    PR's current head — never ``github.sha`` / the merge commit.
    """
    if event_name == "pull_request":
        head = (pr_head_sha or "").strip().lower()
        if SHA_RE.fullmatch(head):
            return head
        raise ValueError("unparseable attestation: missing pull_request.head.sha")
    if event_name == "merge_group":
        number = parse_pr_number(merge_group_head_ref)
        if number is None and (pr_number or "").strip().isdigit():
            number = int(pr_number.strip())
        if number is None:
            raise ValueError("unparseable attestation: cannot parse merge_group PR number")
        repo = (repository or "").strip()
        if not repo or "/" not in repo:
            raise ValueError("unparseable attestation: GITHUB_REPOSITORY missing")
        get = api_get or (
            lambda path: github_api_get(path, token=os.environ.get("GITHUB_TOKEN"))
        )
        payload = get(f"repos/{repo}/pulls/{number}")
        if not isinstance(payload, Mapping):
            raise ValueError("unparseable attestation: merge_group PR payload")
        head_obj = payload.get("head")
        sha = head_obj.get("sha") if isinstance(head_obj, Mapping) else None
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha.strip()):
            raise ValueError("unparseable attestation: merge_group PR head SHA")
        # event_sha is the merge commit; it must not be returned.
        if event_sha and sha.strip().lower() == event_sha.strip().lower():
            # Possible only if GitHub reused the SHA; still treat as PR head
            # after the API said so. Never *prefer* event_sha when they differ.
            pass
        return sha.strip().lower()
    raise ValueError(f"unparseable attestation: CF not defined for event {event_name!r}")


def collect_bodies_and_agents(
    *,
    repository: str,
    pr_number: int,
    api_get: ApiGet,
) -> tuple[list[tuple[str, str]], tuple[str, ...]]:
    """Load PR comments, review bodies, and X-Agent seats.

    Pure Dependabot PRs have no ``X-Agent`` trailers. Resolve the PR author
    login when it is Dependabot so ``author_family_from_agents`` can map them
    to the fixture family (universal independence) as designed for #7487.
    """
    repo = quote(repository, safe="/")
    pull = api_get(f"repos/{repo}/pulls/{pr_number}")
    comments = fetch_paginated(f"repos/{repo}/issues/{pr_number}/comments", api_get=api_get)
    reviews = fetch_paginated(f"repos/{repo}/pulls/{pr_number}/reviews", api_get=api_get)
    commits = fetch_paginated(f"repos/{repo}/pulls/{pr_number}/commits", api_get=api_get)

    bodies: list[tuple[str, str, str]] = []
    for comment in comments:
        body = comment.get("body")
        if isinstance(body, str) and body.strip():
            stamp = comment.get("created_at")
            bodies.append(("comment", body, stamp if isinstance(stamp, str) else ""))
    for review in reviews:
        # #7502 CF r2/r3: a PENDING review is an unsubmitted draft and a
        # DISMISSED review is a voided one — neither may attest. Only
        # positively-submitted states count; a missing submitted_at also
        # fails closed (every submitted review carries one).
        state = review.get("state")
        stamp = review.get("submitted_at")
        if state not in {"APPROVED", "CHANGES_REQUESTED", "COMMENTED"}:
            continue
        if not isinstance(stamp, str) or not stamp:
            continue
        body = review.get("body")
        if isinstance(body, str) and body.strip():
            bodies.append(("review", body, stamp))

    messages: list[str] = []
    for commit in commits:
        inner = commit.get("commit") if isinstance(commit.get("commit"), Mapping) else commit
        if isinstance(inner, Mapping):
            message = inner.get("message")
            if isinstance(message, str):
                messages.append(message)
    seats = list(x_agent_seats_from_messages(messages))
    if isinstance(pull, Mapping):
        user = pull.get("user")
        login = user.get("login") if isinstance(user, Mapping) else None
        if isinstance(login, str) and "dependabot" in login.casefold():
            seats.append("dependabot")
    return bodies, tuple(seats)


def run_event(
    *,
    event_name: str,
    event_sha: str,
    pr_head_sha: str,
    pr_number: str,
    merge_group_head_ref: str,
    repository: str,
    api_get: ApiGet | None = None,
    bodies: Sequence[tuple[str, ...]] | None = None,
    author_agents: Sequence[str] | None = None,
) -> AttestResult:
    """Evaluate CF for one GitHub event. Non-PR events no-op succeed."""
    name = (event_name or "").strip()
    if name in NOOP_EVENTS:
        return AttestResult(True, f"no PR on {name}; CF attest no-op")
    if name not in PR_EVENTS:
        return AttestResult(False, f"unparseable attestation: unknown event {name!r}")

    try:
        expected_head = resolve_pr_head_sha(
            event_name=name,
            event_sha=event_sha,
            pr_head_sha=pr_head_sha,
            pr_number=pr_number,
            merge_group_head_ref=merge_group_head_ref,
            repository=repository,
            api_get=api_get,
        )
    except ValueError as exc:
        return AttestResult(False, str(exc))

    number = parse_pr_number(merge_group_head_ref) if name == "merge_group" else None
    if number is None and (pr_number or "").strip().isdigit():
        number = int(pr_number.strip())

    resolved_bodies = list(bodies) if bodies is not None else None
    resolved_agents = tuple(author_agents) if author_agents is not None else None
    if resolved_bodies is None or resolved_agents is None:
        if number is None:
            return AttestResult(False, "unparseable attestation: missing PR number")
        repo = (repository or "").strip()
        if not repo or "/" not in repo:
            return AttestResult(False, "unparseable attestation: GITHUB_REPOSITORY missing")
        get = api_get or (
            lambda path: github_api_get(path, token=os.environ.get("GITHUB_TOKEN"))
        )
        try:
            fetched_bodies, fetched_agents = collect_bodies_and_agents(
                repository=repo, pr_number=number, api_get=get
            )
        except (ValueError, HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            return AttestResult(False, f"unparseable attestation: {exc}")
        if resolved_bodies is None:
            resolved_bodies = fetched_bodies
        if resolved_agents is None:
            resolved_agents = fetched_agents

    author_family = author_family_from_agents(resolved_agents or ())
    return evaluate_attestation(
        expected_head=expected_head,
        author_family=author_family,
        bodies=resolved_bodies,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", default=os.environ.get("EVENT_NAME", ""))
    parser.add_argument("--event-sha", default=os.environ.get("EVENT_SHA", ""))
    parser.add_argument("--pr-head-sha", default=os.environ.get("PR_HEAD_SHA", ""))
    parser.add_argument("--pr-number", default=os.environ.get("PR_NUMBER", ""))
    parser.add_argument(
        "--merge-group-head-ref",
        default=os.environ.get("MERGE_GROUP_HEAD_REF", ""),
    )
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
    )
    parser.add_argument(
        "--feedback-comment",
        action="store_true",
        help=(
            "when evaluation fails and the triggering comment (env COMMENT_BODY) "
            "carries a VERDICT that cannot be attested, post ONE short gap comment"
        ),
    )
    parser.add_argument(
        "--rerun-stale-failed",
        action="store_true",
        help=(
            "re-run failed jobs of the initial failed CF attest run at "
            "--pr-head-sha, then exit (post-accept companion)"
        ),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.rerun_stale_failed:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

        def _get(path: str) -> Any:
            return github_api_get(path, token=token)

        def _post(path: str, payload: Mapping[str, Any]) -> Any:
            return github_api_post(path, payload, token=token)

        try:
            summary = rerun_stale_failed_cf_attest(
                repository=args.repository,
                head_sha=args.pr_head_sha,
                api_get=_get,
                api_post=_post,
            )
        except Exception as exc:
            print(f"::error::CF attest rerun-stale-failed: {exc}", file=sys.stderr)
            return 1
        print(f"rerun-stale-failed: {summary}")
        return 0

    try:
        result = run_event(
            event_name=args.event,
            event_sha=args.event_sha,
            pr_head_sha=args.pr_head_sha,
            pr_number=args.pr_number,
            merge_group_head_ref=args.merge_group_head_ref,
            repository=args.repository,
        )
    except Exception as exc:
        print(f"::error::CF attest fail-closed: {exc}", file=sys.stderr)
        return 1

    print(f"event={args.event}")
    print(f"expected_head={result.expected_head}")
    print(f"attested_head={result.attested_head}")
    print(f"author_family={result.author_family}")
    print(f"reviewer_family={result.reviewer_family}")
    print(f"reason={result.reason}")
    if not result.ok:
        if args.feedback_comment:
            _maybe_post_feedback(args, result)
        print(f"::error::CF attest fail-closed: {result.reason}", file=sys.stderr)
        return 1
    print("CF attest: independent exact-head cross-family APPROVE")
    return 0


def _maybe_post_feedback(args: argparse.Namespace, result: AttestResult) -> None:
    """Best-effort gap comment; never changes the fail-closed exit code."""
    body = os.environ.get("COMMENT_BODY", "")
    note = diagnose_attest_comment(body, expected_head=result.expected_head)
    if note is None:
        return
    repo = (args.repository or "").strip()
    number = (args.pr_number or "").strip()
    if "/" not in repo or not number.isdigit():
        print("::warning::CF attest feedback skipped: missing repo or PR number", file=sys.stderr)
        return
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    try:
        github_api_post(
            f"repos/{quote(repo, safe='/')}/issues/{number}/comments",
            {"body": build_attest_feedback(note)},
            token=token,
        )
    except Exception as exc:  # best-effort: feedback must not mask the verdict
        print(f"::warning::CF attest feedback comment failed: {exc}", file=sys.stderr)
        return
    print("posted attest-format feedback comment")


if __name__ == "__main__":
    raise SystemExit(main())
