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
* The GitHub user who authored the comment/review is not the PR author

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
from datetime import UTC, datetime
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
# #7593-r2: hidden marker on the evaluator's own gap comment. The evaluator
# never answers a body carrying it, and at most one gap comment is posted per
# (PR, head SHA) — the on-comment workflow must never loop on its own output.
GAP_COMMENT_TAG = "cf-attest:gap"
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
    # Filled from GitHub metadata, never from the attestation body. A missing
    # author is not evidence of independence and is rejected when the
    # evaluator has PR-author identity available.
    author_login: str = ""
    # GitHub's stable numeric user id, when supplied by the API. Login is
    # retained as a compatibility fallback for old fixtures/API payloads.
    author_id: str = ""


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


def _normalize_login(value: Any) -> str:
    """Normalize a GitHub login for case-insensitive identity comparison."""
    if not isinstance(value, str):
        return ""
    return value.strip().casefold()


def _normalize_user_id(value: Any) -> str:
    """Normalize GitHub's numeric user id without treating booleans as ids."""
    if isinstance(value, bool):
        return ""
    if isinstance(value, int):
        return str(value) if value > 0 else ""
    if isinstance(value, str):
        normalized = value.strip()
        return normalized if normalized.isdigit() and int(normalized) > 0 else ""
    return ""


def _user_identity(item: Mapping[str, Any]) -> tuple[str, str]:
    """Return ``(login, id)`` from one GitHub API item's user object."""
    user = item.get("user")
    if not isinstance(user, Mapping):
        return "", ""
    return _normalize_login(user.get("login")), _normalize_user_id(user.get("id"))


def _identity_matches(
    *,
    author_login: str,
    author_id: str,
    candidate_login: str,
    candidate_id: str,
) -> bool:
    """Compare GitHub identities, preferring the stable user id."""
    if author_id and candidate_id:
        return author_id == candidate_id
    if author_login and candidate_login:
        return author_login == candidate_login
    return False


def _identity_is_comparable(
    *,
    author_login: str,
    author_id: str,
    candidate_login: str,
    candidate_id: str,
) -> bool:
    """Return whether the two API identities share a comparable signal."""
    return bool((author_id and candidate_id) or (author_login and candidate_login))


def _timestamp_sort_key(value: str) -> tuple[int, datetime]:
    """Sort RFC3339 timestamps chronologically, retaining fixture stability."""
    raw = value.strip() if isinstance(value, str) else ""
    if raw:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is not None:
                return 1, parsed.astimezone(UTC)
        except ValueError:
            pass
    return 0, datetime.min.replace(tzinfo=UTC)


def _timestamp_is_valid(value: str) -> bool:
    """Return whether a collected API timestamp is usable for ordering."""
    return _timestamp_sort_key(value)[0] == 1


def parse_attestation(
    body: str,
    *,
    source: str = "comment",
    created_at: str = "",
    author_login: str = "",
    author_id: str | int | None = "",
) -> ParsedAttestation | None:
    """Parse one existing CF comment shape, or None if it is not CF of record.

    #7487: a body whose verdict is a block/changes-request is parsed as a
    REVOCATION (verdict="BLOCK") instead of being dropped — evaluation is
    latest-wins across current-head records, so an earlier APPROVE cannot
    survive a later block at the same head.
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
        author_login=_normalize_login(author_login),
        author_id=_normalize_user_id(author_id),
    )


def diagnose_attest_comment(body: str, *, expected_head: str = "") -> str | None:
    """Explain why a VERDICT-bearing comment cannot attest, else ``None``.

    The on-comment workflow posts this as ONE short gap comment so a verdict
    that misses the contract is never skipped silently (#M-4, 2026-09-01: a
    ``**VERDICT: APPROVE**`` + ``resolved_model:`` comment with no
    ``Reviewer family:`` line was dropped without any feedback).

    #7593-r2: a body carrying our own gap-comment marker is never diagnosed —
    answering it would retrigger the workflow in a loop.
    """
    if not isinstance(body, str) or not body.strip():
        return None
    if GAP_COMMENT_TAG in body:
        return None
    if not VERDICT_PRESENT_RE.search(body):
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
    # #7593-r2: these notes are embedded verbatim in the gap comment, so they
    # must not carry the literal gate trigger tokens. The expected-shape
    # tokens use HTML entities (VERDICT&#58;) which render as colons on
    # GitHub but fail ``contains(body, 'VERDICT:')`` and VERDICT_PRESENT_RE.
    if not CF_MARKER_RE.search(body):
        gaps.append(
            "a cross-family marker (e.g. a `Cross-family review of record` "
            "line naming the reviewer seat)"
        )
    if not VERDICT_APPROVE_RE.search(body) and not VERDICT_BLOCK_RE.search(body):
        gaps.append(
            "a recognized verdict (e.g. VERDICT&#58; APPROVE or VERDICT&#58; CHANGES_REQUESTED)"
        )
    if _first_labeled_sha(body) is None:
        found = {match.group(1).lower() for match in SHA_RE.finditer(body)}
        if len(found) != 1:
            gaps.append("the exact head SHA (e.g. `At exact head `<40-char-sha>``)")
    if normalize_family(_family_text(body)) not in CONCRETE_FAMILIES:
        gaps.append(
            "a resolvable reviewer family — add a Reviewer family&#58; <family> line "
            "or a resolved_model&#58; <model-id> line (e.g. resolved_model&#58; claude-sonnet-5)"
        )
    if not gaps:
        return None
    return "missing " + "; ".join(gaps)


def build_attest_feedback(note: str, *, head: str = "", trigger_id: str = "") -> str:
    """The one short bot comment for an unattestable verdict comment.

    #7593-r2: this comment must never retrigger the on-comment workflow. It
    carries a hidden dedupe marker (``cf-attest:gap`` plus the head SHA and
    triggering comment id), and the expected-shape tokens are written with
    HTML entities (``VERDICT&#58;``) so neither ``contains(body, 'VERDICT:')``
    nor VERDICT_PRESENT_RE matches it. Entities sit OUTSIDE code spans so
    GitHub renders them as the literal tokens for the reader.
    """
    marker = f"<!-- {GAP_COMMENT_TAG}"
    normalized_head = (head or "").strip().lower()
    if SHA_RE.fullmatch(normalized_head):
        marker += f" head={normalized_head}"
    normalized_trigger = (trigger_id or "").strip()
    if normalized_trigger.isdigit():
        marker += f" trigger={normalized_trigger}"
    marker += " -->"
    return (
        marker + "\n"
        "CF attest: your verdict comment could not be recorded — " + note + ".\n\n"
        "Expected shape (markdown emphasis around the verdict is fine):\n"
        "- **VERDICT&#58; APPROVE**\n"
        "- Cross-family review of record — <seat>\n"
        "- Reviewer family&#58; <family>   (or a line like: resolved_model&#58; <model-id>)\n"
        "- At exact head `<40-char-sha>`"
    )


def _is_gap_comment(body: str, *, head: str = "") -> bool:
    """True for our own gap comments; with ``head`` set, only at that head."""
    if GAP_COMMENT_TAG not in body:
        return False
    normalized = (head or "").strip().lower()
    if normalized and SHA_RE.fullmatch(normalized):
        return f"head={normalized}" in body
    return True


def _comment_author_is_bot() -> bool:
    """True when the triggering comment author is automation.

    ``COMMENT_AUTHOR_TYPE``/``COMMENT_AUTHOR_LOGIN`` arrive via env from the
    issue_comment event (never shell-interpolated). Absent values mean the
    caller did not supply identity — the marker and trigger-token guards
    still apply — but alone they do not block feedback.
    """
    if os.environ.get("COMMENT_AUTHOR_TYPE", "").strip() == "Bot":
        return True
    login = os.environ.get("COMMENT_AUTHOR_LOGIN", "").strip().casefold()
    return login.endswith("[bot]")


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
    pr_author_login: str | None = None,
    pr_author_id: str | int | None = None,
) -> AttestResult:
    """Return pass/fail for supplied comment/review bodies against one SHA.

    ``pr_author_login``/``pr_author_id`` are sourced from the PR object, while
    each body entry's fourth/fifth fields are sourced from that
    comment/review's ``user.login``/``user.id``. When PR identity is available,
    both are required for an attestation to be eligible: a self-authored or
    identity-less body fails closed. The shorter two/three-field form remains
    accepted for pure parser fixtures that do not model GitHub metadata.
    """
    head = (expected_head or "").strip().lower()
    if not SHA_RE.fullmatch(head):
        return AttestResult(False, "unparseable attestation: invalid expected PR head SHA")
    if author_family in {FAMILY_UNKNOWN, ""}:
        return AttestResult(False, "unparseable attestation: author family", expected_head=head)

    normalized_pr_author_login = _normalize_login(pr_author_login)
    normalized_pr_author_id = _normalize_user_id(pr_author_id)
    identity_context = pr_author_login is not None or pr_author_id is not None
    if identity_context and not (normalized_pr_author_login or normalized_pr_author_id):
        return AttestResult(
            False,
            "unparseable attestation: missing PR author identity",
            expected_head=head,
            author_family=author_family,
        )

    parsed: list[ParsedAttestation] = []
    self_authored = False
    for entry in bodies:
        if len(entry) == 5:
            source, body, created_at, author_login, author_id = entry
        elif len(entry) == 4:
            source, body, created_at, author = entry
            if _normalize_user_id(author):
                author_login = ""
                author_id = author
            else:
                author_login = author
                author_id = ""
        elif len(entry) == 3:
            source, body, created_at = entry
            author_login = ""
            author_id = ""
        elif len(entry) == 2:
            source, body = entry
            created_at = ""
            author_login = ""
            author_id = ""
        else:
            continue
        item = parse_attestation(
            body,
            source=source,
            created_at=created_at,
            author_login=author_login,
            author_id=author_id,
        )
        if item is not None:
            comparable = _identity_is_comparable(
                author_login=normalized_pr_author_login,
                author_id=normalized_pr_author_id,
                candidate_login=item.author_login,
                candidate_id=item.author_id,
            )
            if identity_context and comparable and _identity_matches(
                author_login=normalized_pr_author_login,
                author_id=normalized_pr_author_id,
                candidate_login=item.author_login,
                candidate_id=item.author_id,
            ):
                self_authored = True
                continue
            parsed.append(item)
    # Chronological latest-wins across SOURCES (#7502 CF r1): comments and
    # reviews are fetched as separate lists, so list order alone let an older
    # review outrank a newer comment. Sort by created_at when present; the
    # sort is stable, so timestamp-less fixtures keep their list order.
    # Tie-break (#7502 CF r2): on EQUAL timestamps a BLOCK sorts after an
    # APPROVE so the latest verdict fails closed — a same-second approve
    # can never bury a same-second revocation.
    parsed.sort(
        key=lambda item: (*_timestamp_sort_key(item.created_at), item.verdict == "BLOCK")
    )
    if not parsed:
        if self_authored:
            reason = "self-authored CF rejected: attestation author matches PR author"
        else:
            reason = "missing CF: no independent exact-head APPROVE"
        return AttestResult(
            False,
            reason,
            expected_head=head,
            author_family=author_family,
        )

    matching = [item for item in parsed if item.head_sha == head]
    if not matching:
        attested = parsed[-1].head_sha
        return AttestResult(
            False,
            f"stale CF: attested {attested} != PR head {head}",
            expected_head=head,
            attested_head=attested,
            author_family=author_family,
            reviewer_family=parsed[-1].reviewer_family,
        )

    if identity_context:
        invalid_metadata = next(
            (
                item
                for item in matching
                if not _identity_is_comparable(
                    author_login=normalized_pr_author_login,
                    author_id=normalized_pr_author_id,
                    candidate_login=item.author_login,
                    candidate_id=item.author_id,
                )
                or not _timestamp_is_valid(item.created_at)
            ),
            None,
        )
        if invalid_metadata is not None:
            reason = (
                "unparseable attestation: missing attestation author identity"
                if not _identity_is_comparable(
                    author_login=normalized_pr_author_login,
                    author_id=normalized_pr_author_id,
                    candidate_login=invalid_metadata.author_login,
                    candidate_id=invalid_metadata.author_id,
                )
                else "unparseable attestation: invalid attestation timestamp"
            )
            return AttestResult(
                False,
                reason,
                expected_head=head,
                attested_head=head,
                author_family=author_family,
                reviewer_family=invalid_metadata.reviewer_family,
            )

    # Latest-wins across all parseable current-head comments/reviews (#7487):
    # a later block cannot leave an earlier approval standing merely because
    # the body claims a different reviewer family. Equal timestamps already
    # sort BLOCK after APPROVE so conflicts fail closed.
    latest = matching[-1]
    if latest.verdict == "APPROVE" and families_independent(
        author_family, latest.reviewer_family
    ):
        return AttestResult(
            True,
            "independent exact-head CF APPROVE",
            expected_head=head,
            attested_head=head,
            author_family=author_family,
            reviewer_family=latest.reviewer_family,
        )
    if latest.verdict == "BLOCK":
        return AttestResult(
            False,
            f"revoked CF: latest verdict from {latest.reviewer_family} "
            "is a block at this head",
            expected_head=head,
            attested_head=head,
            author_family=author_family,
            reviewer_family=latest.reviewer_family,
        )
    return AttestResult(
        False,
        f"same-family review: author={author_family} reviewer={latest.reviewer_family}",
        expected_head=head,
        attested_head=latest.head_sha,
        author_family=author_family,
        reviewer_family=latest.reviewer_family,
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
JOB_ID_RE = re.compile(r"/actions/runs/[1-9][0-9]*/jobs?/([1-9][0-9]*)")
STALE_CHECK_CONCLUSIONS = frozenset({"FAILURE", "STALE", "TIMED_OUT"})
STALE_RUN_CONCLUSIONS = frozenset({"failure", "timed_out"})


def rerun_stale_failed_cf_attest(
    *,
    repository: str,
    head_sha: str,
    api_get: ApiGet,
    api_post: Callable[[str, Mapping[str, Any]], Any],
) -> str:
    """Re-run the CF attest job of the initial failed CI run at ``head_sha``.

    #7548 built whole-run rerun for the scheduled auto-arm scanner; #7593
    scopes this on-comment companion strictly to the single ``CF attest`` job
    (never whole-run) and enforces rate-limiting (at most one rerun attempt
    per head SHA).
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
    candidates: list[tuple[int, int]] = []
    for check in check_runs:
        if not isinstance(check, Mapping):
            continue
        if str(check.get("name") or "") != "CF attest":
            continue
        if str(check.get("status") or "").upper() != "COMPLETED":
            continue
        if str(check.get("conclusion") or "").upper() not in STALE_CHECK_CONCLUSIONS:
            continue
        details = str(check.get("details_url") or "")
        run_match = RUN_ID_RE.search(details)
        job_match = JOB_ID_RE.search(details)
        check_id = check.get("id")
        job_id: int | None = None
        if job_match is not None:
            job_id = int(job_match.group(1))
        elif isinstance(check_id, int):
            job_id = check_id
        elif isinstance(check_id, str) and check_id.isdigit():
            job_id = int(check_id)
        if run_match is not None and job_id is not None:
            candidates.append((int(run_match.group(1)), job_id))
    if not candidates:
        return "no failed/stale CF attest check run at this head; nothing to rerun"
    run_id, job_id = candidates[-1]
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
    api_post(f"repos/{quoted}/actions/jobs/{job_id}/rerun", {})
    return f"requested rerun of CF attest job {job_id} for run {run_id}"


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
) -> tuple[list[tuple[str, str, str, str, str]], tuple[str, ...], str, str]:
    """Load PR comments, review bodies, and X-Agent seats.

    Pure Dependabot PRs have no ``X-Agent`` trailers. Resolve the PR author
    login when it is Dependabot so ``author_family_from_agents`` can map them
    to the fixture family (universal independence) as designed for #7487.
    Comment/review author identities travel with their bodies so self-authored
    attestations can be rejected without trusting body prose.
    """
    repo = quote(repository, safe="/")
    pull = api_get(f"repos/{repo}/pulls/{pr_number}")
    pr_author_login, pr_author_id = (
        _user_identity(pull) if isinstance(pull, Mapping) else ("", "")
    )
    if not (pr_author_login or pr_author_id):
        raise ValueError("unparseable attestation: missing PR author identity")
    comments = fetch_paginated(f"repos/{repo}/issues/{pr_number}/comments", api_get=api_get)
    reviews = fetch_paginated(f"repos/{repo}/pulls/{pr_number}/reviews", api_get=api_get)
    commits = fetch_paginated(f"repos/{repo}/pulls/{pr_number}/commits", api_get=api_get)

    bodies: list[tuple[str, str, str, str, str]] = []
    for comment in comments:
        body = comment.get("body")
        stamp = comment.get("created_at")
        author_login, author_id = _user_identity(comment)
        if isinstance(body, str) and body.strip():
            bodies.append(
                (
                    "comment",
                    body,
                    stamp if isinstance(stamp, str) else "",
                    author_login,
                    author_id,
                )
            )
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
        author_login, author_id = _user_identity(review)
        if isinstance(body, str) and body.strip():
            bodies.append(("review", body, stamp, author_login, author_id))

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
    return bodies, tuple(seats), pr_author_login, pr_author_id


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
    pr_author_login: str | None = None,
    pr_author_id: str | int | None = None,
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
    resolved_pr_author_login = pr_author_login
    resolved_pr_author_id = pr_author_id
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
            (
                fetched_bodies,
                fetched_agents,
                fetched_pr_author_login,
                fetched_pr_author_id,
            ) = collect_bodies_and_agents(
                repository=repo, pr_number=number, api_get=get
            )
        except (ValueError, HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            return AttestResult(False, f"unparseable attestation: {exc}")
        if resolved_bodies is None:
            resolved_bodies = fetched_bodies
        if resolved_agents is None:
            resolved_agents = fetched_agents
        resolved_pr_author_login = fetched_pr_author_login
        resolved_pr_author_id = fetched_pr_author_id

    author_family = author_family_from_agents(resolved_agents or ())
    return evaluate_attestation(
        expected_head=expected_head,
        author_family=author_family,
        bodies=resolved_bodies,
        pr_author_login=resolved_pr_author_login,
        pr_author_id=resolved_pr_author_id,
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
    """Best-effort gap comment; never changes the fail-closed exit code.

    #7593-r2 loop guards: never answer a bot-authored trigger or our own
    marker-tagged gap comment, and post at most one gap comment per
    (PR, head SHA) — an existing marker+head comment suppresses a repost. If
    the dedupe check itself fails, skip posting rather than risk a loop.
    """
    if _comment_author_is_bot():
        print("CF attest feedback skipped: triggering comment author is a bot")
        return
    body = os.environ.get("COMMENT_BODY", "")
    if GAP_COMMENT_TAG in body:
        print("CF attest feedback skipped: trigger carries the gap-comment marker")
        return
    note = diagnose_attest_comment(body, expected_head=result.expected_head)
    if note is None:
        return
    repo = (args.repository or "").strip()
    number = (args.pr_number or "").strip()
    if "/" not in repo or not number.isdigit():
        print("::warning::CF attest feedback skipped: missing repo or PR number", file=sys.stderr)
        return
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    quoted = quote(repo, safe="/")
    head = (result.expected_head or "").strip().lower()
    try:
        existing = fetch_paginated(
            f"repos/{quoted}/issues/{number}/comments",
            api_get=lambda path: github_api_get(path, token=token),
        )
    except Exception as exc:
        print(
            f"::warning::CF attest feedback skipped: dedupe check failed: {exc}",
            file=sys.stderr,
        )
        return
    if any(
        isinstance(comment.get("body"), str)
        and _is_gap_comment(comment["body"], head=head)
        for comment in existing
    ):
        print("CF attest feedback skipped: gap comment already posted at this head")
        return
    trigger_id = os.environ.get("COMMENT_ID", "").strip()
    try:
        github_api_post(
            f"repos/{quoted}/issues/{number}/comments",
            {"body": build_attest_feedback(note, head=head, trigger_id=trigger_id)},
            token=token,
        )
    except Exception as exc:  # best-effort: feedback must not mask the verdict
        print(f"::warning::CF attest feedback comment failed: {exc}", file=sys.stderr)
        return
    print("posted attest-format feedback comment")


if __name__ == "__main__":
    raise SystemExit(main())
