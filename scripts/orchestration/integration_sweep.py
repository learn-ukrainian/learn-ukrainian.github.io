#!/usr/bin/env python3
"""Read-only, exact-head PR landing report. The local keeper owns mutations (#8564).

Verdict-marker threat model (#11127)
------------------------------------
Anyone with a GitHub account can comment on a public PR, but only comments by the
authenticated fleet login with a trusted author association are evidence; every
other marker is listed in ``untrusted_markers`` and never counts. The fleet login
is shared by every agent, so the remaining risk is a trusted comment carrying a
``<!-- cf-verdict`` marker that ``record_cf_verdict`` did not write: hand-written,
edited or malformed. The publisher refuses that prefix in comment verbs unless the
body is the recorder's typed record (``scripts.publish.github.CfVerdictRecord``).
That record is an in-process type, not a secret: it stops hand-written CLI and file
bodies, not reviewed code, and the OPSEC ``gh`` guard refuses raw public writes. The
reader rules below therefore never rely on the publisher check.

A marker the parser rejects can still be read one of three ways:

* It cannot be attributed to exactly one head (several markers, no ``-->``, no or
  several ``sha=`` keys, a malformed SHA): the current head is ``unknown``. Such a
  marker could be a rejection of any head, including this one.
* It names the current head: ``unknown``. The parser is never relaxed for the head
  being landed, so a malformed rejection keeps blocking it.
* It names a different head: superseded. Valid markers for other heads never decide
  this head either, so a forged or malformed one cannot revoke an approval of the
  current head, nor can it approve anything. A body that mentions the current head
  (its seven-character abbreviation or longer) is treated as naming it, so a marker
  aimed at an old SHA cannot smuggle a current-head rejection past this rule.

A forger with the fleet identity can therefore still hold a PR (fail closed), but
can no longer revoke one through an unrelated malformed marker, and every
``unknown`` verdict names a typed reason from ``UNKNOWN_REASONS`` and the comment.
Every valid current-head rejection stands regardless of later same-head approvals.
A different head requires its own review; old-head rejections do not decide it.

A marker may also name the artifact items it covers and the review brief's item
denominator (#12257). A head that declares one is approved only when every
required Ukrainian seat's non-void APPROVE coverage equals that denominator and
no non-void rejection stands. A voided chunk does not count. Markers that
disagree on the denominator make the head ``unknown`` (``denominator-mismatch``).
A head with no denominator is unchanged.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.ci.advisory_checks import is_advisory, load_advisory_checks
from scripts.common.github_client import GitHubRateLimited, timer
from scripts.deploy.auto_deploy_eligibility import CONTENT_PATH_PREFIXES, SITE_CODE_PATH_EXCEPTIONS
from scripts.github_check_rollup import group_collapsed_by_name
from scripts.publish.github import CF_VERDICT_MARKER_PREFIX, Request, request_run
from scripts.review.language_lane import is_ukrainian_review
from scripts.review.ukrainian_seats import (
    UKRAINIAN_SEAT_FAMILIES,
    UKRAINIAN_SEAT_ROUTES,
    attested_author_families,
    required_ukrainian_seats,
)

Runner = Callable[[list[str]], str]
SHA = re.compile(r"[0-9a-f]{40}\Z")
# Item ids on a coverage marker. One token, no spaces; the recorder uses ITEM_ID_RE.
_ITEM_ID = r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}"
ITEM_ID_RE = re.compile(_ITEM_ID + r"\Z")
_ITEM_LIST = rf"{_ITEM_ID}(?:,{_ITEM_ID})*"
# A chunk voided before its coverage counts (#12257). The reason is the marker token.
VOID_QUOTE_MISMATCH = "quote-mismatch"
VOID_REVIEWER_BOOKKEEPING = "reviewer-bookkeeping"
CHUNK_VOIDS = frozenset({VOID_QUOTE_MISMATCH, VOID_REVIEWER_BOOKKEEPING})
MARKER = re.compile(
    r"<!-- cf-verdict v1 sha=(?P<sha>[0-9a-f]{40}) task=(?P<task>[^\s]+) "
    r"started=(?P<started>[^\s]+) verdict=(?P<verdict>APPROVED|APPROVE|CHANGES_REQUESTED|BLOCKED) "
    r"model=(?P<model>[^\s]+) family=(?P<family>[^\s]+)(?: review_mode=(?P<review_mode>red_team))?"
    r"(?: unknown_history=(?P<unknown_history>[0-9a-f]{40}(?:,[0-9a-f]{40})*))?"
    r"(?: authorship=(?P<authorship>verified_app_bot))?"
    r"(?: review_profile=(?P<review_profile>ukrainian))?(?: sources_calls=(?P<sources_calls>[0-9]+))?"
    rf"(?: denominator=(?P<denominator>{_ITEM_LIST}))?(?: coverage=(?P<coverage>-|{_ITEM_LIST}))?"
    rf"(?: void=(?P<void>{VOID_QUOTE_MISMATCH}|{VOID_REVIEWER_BOOKKEEPING}))? -->\Z"
)
MARKER_PREFIX = CF_VERDICT_MARKER_PREFIX
# Stable reason codes for an ``unknown`` verdict (#11127); consumers may match on them.
COMMENTS_UNAVAILABLE = "comments-unavailable"  # lookup failed, partial, or not a comment list
HEAD_INVALID = "head-invalid"  # the head is not a full 40-hex SHA
IDENTITY_UNAVAILABLE = "identity-unavailable"  # no authenticated login to trust markers from
COMMENT_MALFORMED = "comment-malformed"  # a comment row or its body has the wrong type
MARKER_UNATTRIBUTABLE = "marker-unattributable"  # a malformed marker names no single head
MARKER_MALFORMED_CURRENT_HEAD = "marker-malformed-current-head"  # a malformed marker names this head
MARKER_MENTIONS_CURRENT_HEAD = "marker-mentions-current-head"  # a malformed old-head marker cites this head
MARKER_EDITED = "marker-edited"  # a marker for this head was edited after posting
REVIEWER_UNATTESTED = "reviewer-unattested"  # a marker for this head has no attested reviewer family
# Chunks of one review named different item denominators (#12257).
DENOMINATOR_MISMATCH = "denominator-mismatch"
UNKNOWN_REASONS = (
    COMMENTS_UNAVAILABLE,
    HEAD_INVALID,
    IDENTITY_UNAVAILABLE,
    COMMENT_MALFORMED,
    MARKER_UNATTRIBUTABLE,
    MARKER_MALFORMED_CURRENT_HEAD,
    MARKER_MENTIONS_CURRENT_HEAD,
    MARKER_EDITED,
    REVIEWER_UNATTESTED,
    DENOMINATOR_MISMATCH,
)
# Git's default abbreviation; a body citing this much of the current head names it.
HEAD_MENTION_LENGTH = 7
TRUSTED_ASSOCIATIONS = frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
REJECTED = frozenset({"CHANGES_REQUESTED", "BLOCKED"})
# The recorder normalizes APPROVE to APPROVED, but older trailers carry the reviewer's raw token (#10119).
VERDICT_ALIASES = {"APPROVE": "APPROVED"}
SUCCESSFUL = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
# A Ukrainian-profile head whose recorded seats do not cover the author rule; never approval.
NEEDS_SEAT = "needs-seat"
# A head whose review brief declared an item denominator that APPROVE coverage has not filled.
NEEDS_COVERAGE = "needs-coverage"
# Recorder headings; a body that opens with one is a verdict record, never informal prose.
RECORD_HEADINGS = ("### Cross-family review\n", "### Adversarial red-team review\n")
# Every recorder opens the reviewer's reply with this line, right after the record's lines.
REPLY_OPENER = "<details><summary>Reviewer's reply</summary>\n\n"
# Since #11127 the publisher posts only the recorder's typed record, which never carries a
# raw APPROVE trailer, so only a comment GitHub created before then can be such a legacy record.
LEGACY_TRAILER_CUTOFF = datetime(2026, 10, 20, 6, 0, 20, tzinfo=UTC)
# Readable record lines whose value the trailer does not carry.
FREE_RECORD_LINES = re.compile(
    r"Review score: (?:\d+/10|absent)|Authored by: [^\s,]+(?:, [^\s,]+)*|Withheld findings: (?:\d+|unknown)"
)
REQUIRED_CHECKS = ("CI Gate",)
DEFAULT_GH_TIMEOUT_SECONDS = 60.0
# GitHub lists at most this many files of a pull request; a list this long may be cut short.
PR_FILES_LIMIT = 3000


class SweepError(RuntimeError):
    """An authoritative lookup failed; no landing decision can follow."""


@dataclass(frozen=True)
class Verdict:
    state: str
    task: str | None = None
    model: str | None = None
    family: str | None = None
    started: datetime | None = None
    untrusted_markers: tuple[str, ...] = ()
    review_mode: str = "cross_family"
    unknown_history: tuple[str, ...] = ()
    # Set only for ``unknown``: the typed cause and, when one comment caused it, its id.
    reason: str | None = None
    comment_id: str | None = None
    # Trusted malformed markers that name another head; they neither poison nor approve.
    superseded_markers: tuple[str, ...] = ()
    # Reviewer families of the Ukrainian seats that approved this head, sorted.
    ukrainian_seats: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if (self.state == "unknown") != (self.reason is not None):
            raise ValueError("an unknown verdict, and only one, carries a reason")
        if self.reason is not None and self.reason not in UNKNOWN_REASONS:
            raise ValueError(f"unregistered unknown-verdict reason: {self.reason}")


def verdict_detail(reason: str | None, comment_id: str | None, superseded: Sequence[str] = ()) -> str:
    """Report suffix naming an unknown verdict's cause and comment; never comment text."""
    detail = f" cf-unknown={reason} comment={comment_id or 'none'}" if reason else ""
    return detail + (f" superseded-marker={','.join(superseded)}" if superseded else "")


@dataclass(frozen=True)
class PRReport:
    number: int
    head: str
    observed_at: str
    state: str
    blockers: tuple[str, ...]
    untrusted_markers: tuple[str, ...] = ()
    verdict_reason: str | None = None
    verdict_comment: str | None = None
    superseded_markers: tuple[str, ...] = ()


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else None


def _field(comment: Mapping[str, Any], *keys: str) -> Any:
    return next((comment[key] for key in keys if key in comment), None)


def _author_login(comment: Mapping[str, Any]) -> str | None:
    author = _field(comment, "user", "author")
    if isinstance(author, Mapping):
        login = author.get("login")
        return login if isinstance(login, str) else None
    return None


def _terminal_marker(body: str) -> re.Match[str] | None:
    """Return the well-formed trailer when it is the body's only marker and its last line."""
    if body.count(MARKER_PREFIX) != 1:
        return None
    return MARKER.fullmatch(body.rstrip("\n").split("\n")[-1])


def _comment_ref(comment: Mapping[str, Any], index: int) -> str:
    """A GitHub comment id, or the list position when the row carries no integer id."""
    value = _field(comment, "id", "databaseId")
    return str(value) if isinstance(value, int) and not isinstance(value, bool) else f"index-{index}"


def _attributed_head(body: str) -> str | None:
    """The one head a single, closed marker names through one ``sha=`` key, else None."""
    if body.count(MARKER_PREFIX) != 1:
        return None
    start = body.index(MARKER_PREFIX) + len(MARKER_PREFIX)
    end = body.find("-->", start)
    if end < 0:
        return None
    values = [token[4:] for token in body[start:end].split() if token.startswith("sha=")]
    return values[0] if len(values) == 1 and SHA.fullmatch(values[0]) else None


def _edited(comment: Mapping[str, Any]) -> bool:
    created = _timestamp(_field(comment, "created_at", "createdAt"))
    updated = _timestamp(_field(comment, "updated_at", "updatedAt"))
    return created is None or updated is None or created != updated


def parse_marker(body: str) -> dict[str, Any] | None:
    """Accept an intact terminal marker; Ukrainian reviews need positive Sources calls."""
    match = _terminal_marker(body)
    if match is None:
        return None
    item: dict[str, Any] = match.groupdict()
    sources = item["sources_calls"]
    try:
        item["sources_calls"] = int(sources) if sources is not None else None
    except ValueError:
        return None
    profile = item.pop("review_profile")
    if profile is not None:
        item["review_profile"] = profile
    raw_denominator = item.pop("denominator")
    raw_coverage = item.pop("coverage")
    raw_void = item.pop("void")
    if (raw_denominator is None) != (raw_coverage is None) or (raw_void is not None and raw_denominator is None):
        return None
    denominator = _item_ids(raw_denominator, empty=False)
    coverage = _item_ids(raw_coverage, empty=True)
    if raw_denominator is not None and (
        denominator is None or coverage is None or not set(coverage) <= set(denominator)
    ):
        return None
    if raw_void is not None and raw_void not in CHUNK_VOIDS:
        return None
    # The record's own lines end where the recorder opens the reply, or, in a record
    # without a reply, at the trailer; nothing else in the body can end them early (#12020).
    prefix, opened, _ = body.partition(REPLY_OPENER)
    if not opened:
        prefix = body.rstrip("\n").rsplit("\n", 1)[0]
    # These readable statements must agree with the terminal marker exactly,
    # once each. Substrings also admit negation, prefixed labels and conflicts.
    authorship = item.pop("authorship")
    history = item.pop("unknown_history")
    statements = {
        "Authorship:": f"Authorship: {authorship}" if authorship else None,
        "Historical authorship:": "Historical authorship: unknown_historical" if history else None,
        "Unknown history:": f"Unknown history: {history}" if history else None,
        "author model": "No author model assumed." if history or authorship else None,
    }
    for label, expected in statements.items():
        lines = [
            line
            for line in prefix.split("\n")
            if label.casefold() in line.casefold()
            and not (label == "Authorship:" and "historical authorship:" in line.casefold())
        ]
        if lines != ([expected] if expected is not None else []):
            return None
    if is_ukrainian_review(item) and (item["sources_calls"] is None or item["sources_calls"] <= 0):
        return None
    if sources is not None and f"Sources MCP calls: {item['sources_calls']}\n" not in prefix:
        return None
    mode = item.pop("review_mode")
    if history is not None:
        shas = history.split(",")
        if mode != "red_team" or shas != sorted(set(shas)):
            return None
        item["unknown_history"] = shas
    # A verified app bot author (#10531) is stated in the readable prefix too.
    if authorship is not None:
        item["authorship"] = authorship
    if mode is not None:
        item["review_mode"] = mode
        if not body.startswith("### Adversarial red-team review\nReview mode: red_team\n"):
            return None
    elif not body.startswith("### Cross-family review\n") or "Review mode:" in prefix:
        return None
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}(?:Z|\+00:00)", item["started"]):
        return None
    if _timestamp(item["started"]) is None:
        return None
    readable = prefix.split("\n")
    identity = [
        f"head: {item['sha']}",
        f"Reviewer family: {item['family']}",
        f"VERDICT: {item['verdict']}",
        f"Reviewer model: {item['model']}",
        f"Task id: {item['task']}",
    ]
    if raw_denominator is not None:
        identity.append(f"Denominator: {','.join(denominator or ())}")
        identity.append("Coverage: " + (",".join(coverage or ()) if coverage else "-"))
    if raw_void is not None:
        identity.append(f"Chunk void: {raw_void}")
    if any(line not in readable for line in identity):
        return None
    # Every readable line is one the recorder writes for these trailer fields, so an
    # altered or added statement, such as a review profile in any spelling, refuses the
    # marker instead of downgrading a Ukrainian seat to code (#12020).
    fixed = {
        "",
        "Findings are held privately.",
        # The withheld-findings wording of earlier recorders, still on open PRs.
        "Findings are held privately on the host in CF run output files (`out/<task>.final` and `out/<task>.md`).",
        RECORD_HEADINGS[mode is not None].rstrip("\n"),
        *identity,
        *(statement for statement in statements.values() if statement),
        *(["Review mode: red_team"] if mode else []),
        *([f"Review profile: {profile}"] if profile else []),
        *([f"Sources MCP calls: {item['sources_calls']}"] if sources is not None else []),
    }
    if any(line not in fixed and not FREE_RECORD_LINES.fullmatch(line) for line in readable):
        return None
    authored = [line for line in readable if line.startswith("Authored by: ")]
    if len(authored) > 1:
        return None
    item["author_models"] = tuple(authored[0].removeprefix("Authored by: ").split(", ")) if authored else ()
    item["verdict"] = VERDICT_ALIASES.get(item["verdict"], item["verdict"])
    if raw_denominator is not None:
        item["denominator"] = denominator
        item["coverage"] = coverage
    if raw_void is not None:
        item["void"] = raw_void
    return item


def _item_ids(value: str | None, *, empty: bool) -> list[str] | None:
    """Sorted unique item ids from a marker token, ``[]`` for ``-``, or None when the token is illegal.

    ``None`` as ``value`` means the token is absent. An absent token returns an empty list only so
    the caller can tell a missing pair from a bad token by checking the raw string first.
    """
    if value is None:
        return []
    if value == "-":
        return [] if empty else None
    ids = value.split(",")
    if ids != sorted(set(ids)) or any(ITEM_ID_RE.fullmatch(item) is None for item in ids):
        return None
    return ids


def pr_file_paths(rows: object) -> list[str]:
    """Every path a pull request's file list names, the old path of a rename included.

    Raises ``ValueError`` when the list is malformed (a rename without its old path
    included) or may be cut short.
    """
    if not isinstance(rows, list) or len(rows) >= PR_FILES_LIMIT:
        raise ValueError("PR file list partial or malformed")
    paths: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("filename"), str) or not row["filename"]:
            raise ValueError("PR file list malformed")
        paths.append(row["filename"])
        # A rename names its old path, which may be learner content; a rename that does not is unknown.
        previous = row.get("previous_filename")
        if isinstance(previous, str) and previous:
            paths.append(previous)
        elif previous is not None or row.get("status") == "renamed":
            raise ValueError("PR file list malformed")
    return paths


def changes_learner_content(paths: Iterable[str]) -> bool:
    """Whether a change to ``paths`` changes learner content, which takes the Ukrainian seats.

    The content surfaces are the auto-deploy ones, the repository's one list of
    paths that can change published learner content (#12181).
    """
    return any(path not in SITE_CODE_PATH_EXCEPTIONS and path.startswith(CONTENT_PATH_PREFIXES) for path in paths)


def ukrainian_seat_families(markers: Iterable[Mapping[str, Any]]) -> set[str]:
    """Families of the eligible cross-family Ukrainian seats among ``markers``."""
    return {
        marker["family"]
        for marker in markers
        if is_ukrainian_review(marker)
        and marker["family"] in UKRAINIAN_SEAT_FAMILIES
        and marker.get("review_mode", "cross_family") == "cross_family"
    }


def _coverage_decision(
    candidates: list[tuple[Any, tuple[Any, int], dict[str, Any]]],
    *,
    learner_content: bool,
) -> tuple[str, dict[str, Any], tuple[str, ...], str | None, int, datetime | None] | None:
    """Gate a head that declares an item denominator. None when none of its markers do.

    The tuple is ``(state, marker, seats, reason, comment_index, started)``. ``reason``
    is set only when chunks disagree on the denominator. A voided chunk counts as
    neither coverage nor a rejection. An APPROVE that names no denominator adds no items.
    """
    declared = [item for item in candidates if item[2].get("denominator")]
    if not declared:
        return None
    denominators = {tuple(item[2]["denominator"]) for item in declared}
    if len(denominators) != 1:
        first = min(declared, key=lambda item: item[1][1])
        return ("unknown", first[2], (), DENOMINATOR_MISMATCH, first[1][1], first[0])
    denominator = set(denominators.pop())
    active = [item for item in candidates if not item[2].get("void")]
    standing = [item for item in active if item[2]["verdict"] in REJECTED]
    if standing:
        winner = max(standing, key=lambda item: (item[0], item[1]))
        return (winner[2]["verdict"], winner[2], (), None, winner[1][1], winner[0])
    approvals = [item for item in active if item[2]["verdict"] not in REJECTED]
    by_family: dict[str, set[str]] = {}
    for _, _, marker in approvals:
        # A code-profile chunk of the same family must not finish a Ukrainian seat (#12257).
        if (
            not marker.get("denominator")
            or marker.get("review_mode", "cross_family") != "cross_family"
            or not is_ukrainian_review(marker)
        ):
            continue
        by_family.setdefault(marker["family"], set()).update(marker.get("coverage") or ())
    union: set[str] = set().union(*by_family.values()) if by_family else set()
    seats = tuple(
        sorted(family for family, ids in by_family.items() if ids == denominator and family in UKRAINIAN_SEAT_FAMILIES)
    )
    profiled = [marker for _, _, marker in approvals if is_ukrainian_review(marker)]
    pool = approvals or active or candidates
    latest = max(item[0] for item in pool)
    winner = next(item for item in pool if item[0] == latest)
    if union != denominator:
        state = NEEDS_COVERAGE
    elif (bool(profiled) or learner_content) and not required_ukrainian_seats(
        attested_author_families(profiled)
    ) <= set(seats):
        state = NEEDS_SEAT
    else:
        state = "APPROVED"
    return (state, winner[2], seats, None, winner[1][1], winner[0])


def lookup_verdict(
    comments: Sequence[Mapping[str, Any]] | None,
    sha: str,
    authenticated_login: str | None,
    *,
    complete: bool = True,
    learner_content: bool = False,
) -> Verdict:
    """Resolve one SHA's verdict; malformed or edited evidence for it poisons it.

    A valid rejection stands for this exact SHA regardless of later approvals.
    A head is approved only once its Ukrainian seats have approved it when it
    carries a Ukrainian-profile approval or, by ``learner_content``, changes
    learner content (``changes_learner_content``), even with no Ukrainian verdict yet.
    When a marker declares an item denominator, approval also needs each required
    seat's non-void Ukrainian-profile APPROVE coverage to equal it (#12257). A
    voided chunk, a code-profile chunk and a marker that names no denominator add
    no items.
    A malformed marker poisons this SHA unless it is attributable to another head; see
    the module docstring for the threat model (#11127).
    """
    if not complete or not isinstance(comments, Sequence) or isinstance(comments, (str, bytes)):
        return Verdict("unknown", reason=COMMENTS_UNAVAILABLE)
    if not SHA.fullmatch(sha):
        return Verdict("unknown", reason=HEAD_INVALID)
    if not authenticated_login:
        return Verdict("unknown", reason=IDENTITY_UNAVAILABLE)
    candidates: list[tuple[datetime, tuple[datetime, int], dict[str, Any]]] = []
    untrusted: list[str] = []
    superseded: list[str] = []
    legacy = False
    other_head = False

    def unknown(reason: str, index: int, comment: Mapping[str, Any] | None = None) -> Verdict:
        ref = _comment_ref(comment, index) if comment is not None else f"index-{index}"
        return Verdict(
            "unknown",
            untrusted_markers=tuple(untrusted),
            reason=reason,
            comment_id=ref,
            superseded_markers=tuple(superseded),
        )

    for index, comment in enumerate(comments):
        if not isinstance(comment, Mapping):
            return unknown(COMMENT_MALFORMED, index)
        body = comment.get("body")
        if not isinstance(body, str):
            return unknown(COMMENT_MALFORMED, index, comment)
        if MARKER_PREFIX not in body:
            if re.search(r"(?im)^\s*VERDICT:", body):
                legacy = True
            continue
        marker = parse_marker(body)
        login = _author_login(comment)
        association = _field(comment, "author_association", "authorAssociation")
        if login != authenticated_login or association not in TRUSTED_ASSOCIATIONS:
            untrusted.append(str(_field(comment, "id", "databaseId") or index))
            continue
        if marker is None:
            trailer = _terminal_marker(body)
            if (
                trailer is not None
                and trailer["verdict"] == "APPROVE"
                and not is_ukrainian_review(trailer.groupdict())
                and not body.startswith(RECORD_HEADINGS)
                and (created := _timestamp(_field(comment, "created_at", "createdAt"))) is not None
                and created < LEGACY_TRAILER_CUTOFF
            ):
                # A legacy approval trailer outside the keeper format cannot hide a rejection, so it
                # neither poisons the head nor counts as approval; an edited one still poisons it
                # (#10119). A newer one is no legacy record and poisons the head like any malformed
                # marker, so it cannot hide a Ukrainian seat however it is spelled (#12020).
                if trailer["sha"] == sha and _edited(comment):
                    return unknown(MARKER_EDITED, index, comment)
                if re.search(r"(?im)^\s*VERDICT:", body):
                    legacy = True
                continue
            head = _attributed_head(body)
            if head is None:
                return unknown(MARKER_UNATTRIBUTABLE, index, comment)
            if head == sha:
                return unknown(MARKER_MALFORMED_CURRENT_HEAD, index, comment)
            if sha[:HEAD_MENTION_LENGTH] in body.casefold():
                return unknown(MARKER_MENTIONS_CURRENT_HEAD, index, comment)
            # Named another head: like a valid marker for that head, it cannot decide this one.
            superseded.append(_comment_ref(comment, index))
            other_head = True
            continue
        if marker["sha"] != sha:
            other_head = True
            continue
        if marker["family"] in {"unknown", "unattested", "ambiguous", "conflicting"}:
            return unknown(REVIEWER_UNATTESTED, index, comment)
        if _edited(comment):
            return unknown(MARKER_EDITED, index, comment)
        # An unedited comment has a parseable creation time; list order breaks same-second ties.
        posted = (_timestamp(_field(comment, "created_at", "createdAt")), index)
        candidates.append((_timestamp(marker["started"]), posted, marker))
    if not candidates:
        state = "CF-unrecorded" if legacy else "CF-stale" if other_head else "needs-CF"
        return Verdict(state, untrusted_markers=tuple(untrusted), superseded_markers=tuple(superseded))
    covered = _coverage_decision(candidates, learner_content=learner_content)
    if covered is not None:
        state, marker, seats, reason, index, started = covered
        if reason is not None:
            return unknown(reason, index, comments[index])
        return Verdict(
            state,
            marker["task"],
            marker["model"],
            marker["family"],
            started,
            tuple(untrusted),
            marker.get("review_mode", "cross_family"),
            tuple(marker.get("unknown_history", ())),
            superseded_markers=tuple(superseded),
            ukrainian_seats=seats,
        )
    approvals = [item for item in candidates if item[2]["verdict"] not in REJECTED]
    # Same-head approvals cannot clear a rejection, including when started and posted later.
    # Keep the latest rejection by review start, then posting time for stalled-work reporting.
    standing = [item for item in candidates if item[2]["verdict"] in REJECTED]
    if standing:
        winner = max(standing, key=lambda item: (item[0], item[1]))
    else:
        latest_start = max(item[0] for item in approvals)
        winner = next(item for item in approvals if item[0] == latest_start)
    marker = winner[2]
    state = marker["verdict"]
    profiled = [item[2] for item in approvals if is_ukrainian_review(item[2])]
    seats = () if standing else tuple(sorted(ukrainian_seat_families(profiled)))
    needs_seats = bool(profiled) or learner_content
    if not standing and needs_seats and not required_ukrainian_seats(attested_author_families(profiled)) <= set(seats):
        # A Ukrainian head is approved only once every required seat has approved it. With no
        # Ukrainian verdict the authors are unattested, so both seats are required (#12181).
        state = NEEDS_SEAT
    return Verdict(
        state,
        marker["task"],
        marker["model"],
        marker["family"],
        winner[0],
        tuple(untrusted),
        marker.get("review_mode", "cross_family"),
        tuple(marker.get("unknown_history", ())),
        superseded_markers=tuple(superseded),
        ukrainian_seats=seats,
    )


def _comment_page_url(comment: Mapping[str, Any]) -> str:
    for key in ("url", "html_url"):
        value = comment.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _seat_harness(family: str) -> str | None:
    matches = sorted({harness for harness, seat_family in UKRAINIAN_SEAT_ROUTES if seat_family == family})
    if len(matches) != 1:
        return None
    return matches[0]


def contributing_ukrainian_chunks(
    comments: Sequence[Mapping[str, Any]] | None,
    sha: str,
    authenticated_login: str | None,
    *,
    learner_content: bool = True,
) -> dict[str, Any]:
    """Every non-void chunk that makes this head an APPROVED Ukrainian quorum.

    ``lookup_verdict`` stays the keeper's one-winner result. This reader admits
    candidates with that same function, then keeps each contributing comment.
    A partial chunk does not complete a seat. One seat is enough only when
    ``required_ukrainian_seats`` names that family alone.
    """
    verdict = lookup_verdict(
        comments,
        sha,
        authenticated_login,
        learner_content=learner_content,
    )
    if verdict.state != "APPROVED":
        return {"refused": verdict.state, "author_models": (), "author_families": (), "seats": ()}
    if not isinstance(comments, Sequence) or isinstance(comments, (str, bytes)):
        return {"refused": COMMENTS_UNAVAILABLE, "author_models": (), "author_families": (), "seats": ()}

    admitted: list[dict[str, Any]] = []
    for comment in comments:
        if not isinstance(comment, Mapping):
            continue
        body = comment.get("body")
        if not isinstance(body, str) or MARKER_PREFIX not in body:
            continue
        marker = parse_marker(body)
        if marker is None or marker.get("sha") != sha or marker.get("void"):
            continue
        if not is_ukrainian_review(marker) or marker.get("verdict") in REJECTED:
            continue
        login = _author_login(comment)
        association = _field(comment, "author_association", "authorAssociation")
        if login != authenticated_login or association not in TRUSTED_ASSOCIATIONS or _edited(comment):
            continue
        # The keeper counts only cross-family chunks. A red-team marker of the
        # same family must not appear as a contributing chunk.
        if marker.get("review_mode", "cross_family") != "cross_family":
            continue
        if marker.get("family") not in set(verdict.ukrainian_seats):
            continue
        url = _comment_page_url(comment)
        if not url:
            return {"refused": "chunk-url-missing", "author_models": (), "author_families": (), "seats": ()}
        admitted.append({**marker, "comment_url": url})

    if not admitted:
        return {"refused": "chunks-missing", "author_models": (), "author_families": (), "seats": ()}

    model_sets = {tuple(sorted(marker.get("author_models") or ())) for marker in admitted}
    if len(model_sets) != 1:
        return {"refused": "author-models-conflict", "author_models": (), "author_families": (), "seats": ()}
    author_models = model_sets.pop()
    if not author_models or not all(isinstance(model, str) and model for model in author_models):
        return {"refused": "author-models-unresolved", "author_models": (), "author_families": (), "seats": ()}
    families = attested_author_families(admitted)
    from learn_ukrainian_v4_runtime.identity import (
        UNKNOWN_AUTHOR_FAMILY,
        UNRESOLVED_AUTHOR_FAMILIES,
    )

    if not families or not families.isdisjoint(UNRESOLVED_AUTHOR_FAMILIES | {UNKNOWN_AUTHOR_FAMILY}):
        return {"refused": "author-models-unresolved", "author_models": (), "author_families": (), "seats": ()}
    required = required_ukrainian_seats(families)
    if not required <= set(verdict.ukrainian_seats):
        return {"refused": "seat-quorum", "author_models": (), "author_families": (), "seats": ()}

    seats: list[dict[str, Any]] = []
    for family in sorted(required):
        family_chunks = [marker for marker in admitted if marker.get("family") == family]
        if not family_chunks:
            return {"refused": "seat-quorum", "author_models": (), "author_families": (), "seats": ()}
        harness = _seat_harness(family)
        if harness is None:
            return {"refused": "seat-harness", "author_models": (), "author_families": (), "seats": ()}
        denominators = {tuple(marker.get("denominator") or ()) for marker in family_chunks}
        if len(denominators) != 1:
            return {
                "refused": DENOMINATOR_MISMATCH,
                "author_models": (),
                "author_families": (),
                "seats": (),
            }
        coverage: list[str] = sorted({item for marker in family_chunks for item in (marker.get("coverage") or ())})
        raw_denominator = denominators.pop()
        denominator = sorted(raw_denominator) if raw_denominator else []
        if denominator and set(coverage) != set(denominator):
            return {"refused": NEEDS_COVERAGE, "author_models": (), "author_families": (), "seats": ()}
        chunks = [
            {
                "comment_url": marker["comment_url"],
                "task": marker.get("task"),
                "model": marker.get("model"),
                "sha": marker.get("sha"),
                "verdict": marker.get("verdict"),
                "coverage": list(marker.get("coverage") or ()),
                "started": marker.get("started"),
            }
            for marker in sorted(family_chunks, key=lambda item: (str(item.get("task")), item["comment_url"]))
        ]
        seats.append(
            {
                "family": family,
                "harness": harness,
                "harness_source": "ukrainian-seat-route",
                "selection_reason": "required-ukrainian-seat",
                "selection_reason_source": "required-ukrainian-seat",
                "denominator": denominator,
                "coverage": coverage,
                "chunks": chunks,
            }
        )
    return {
        "refused": None,
        "author_models": tuple(sorted(author_models)),
        "author_families": tuple(sorted(families)),
        "seats": tuple(seats),
    }


# Only the CTO seat applies this label, to a machinery fix that should land first (#12019).
PRIORITY_LABEL = "merge-priority"


def priority_jump(labels, timeline, comments, head, login) -> bool:
    """Whether an enqueue of ``head`` goes to the front of the merge queue.

    The priority label must be on the PR, its latest application must come from the
    fleet login, and it must postdate a recorded approval of exactly ``head`` that
    still stands. A label applied before that approval, including at an earlier
    head, does not jump: the CTO re-applies it once the head to land is approved.
    """
    if not login or PRIORITY_LABEL not in {row.get("name") for row in labels if isinstance(row, dict)}:
        return False
    if lookup_verdict(comments, head, login).state != "APPROVED":
        return False
    approved = [
        _timestamp(row.get("created_at"))
        for row in comments
        if isinstance(row, dict)
        and isinstance(row.get("body"), str)
        and (marker := parse_marker(row["body"])) is not None
        and marker["sha"] == head
        and lookup_verdict([row], head, login).state == "APPROVED"
    ]
    events = [
        (_timestamp(row.get("created_at")), row)
        for row in timeline
        if isinstance(row, dict)
        and row.get("event") in {"labeled", "unlabeled"}
        and isinstance(row.get("label"), dict)
        and row["label"].get("name") == PRIORITY_LABEL
    ]
    if not events or not approved or None in approved or any(at is None for at, _ in events):
        return False
    # A stable sort keeps the timeline's own order for same-second events.
    labeled_at, last = sorted(events, key=lambda item: item[0])[-1]
    actor = last.get("actor")
    return (
        last["event"] == "labeled"
        and isinstance(actor, dict)
        and actor.get("login") == login
        and labeled_at > min(approved)
    )


def _check_row_kind(row: Mapping[str, Any]) -> str:
    """Return ``red``, ``pending``, ``unknown``, or ``green`` for one surviving row."""
    status = str(row.get("status") or row.get("state") or "").upper()
    outcome = str(row.get("conclusion") or row.get("state") or "").upper()
    if not status and not outcome:
        return "unknown"
    if status not in {"COMPLETED", "SUCCESS", "FAILURE", "ERROR"}:
        return "pending"
    if outcome not in SUCCESSFUL:
        return "red" if outcome else "pending"
    return "green"


def _check_blockers(pr: Mapping[str, Any], required: Sequence[str] = REQUIRED_CHECKS) -> list[str]:
    """Block when any non-advisory row surviving the shared collapse is red or pending.

    A missing rollup or a non-check value is still ``CI unknown``. Timestamp
    ties and same-named jobs from different workflows are not collapsed to one
    winner: one red or pending survivor fails that name.
    """
    checks = pr.get("statusCheckRollup")
    if not isinstance(checks, list):
        return ["CI unknown"]
    if any(not isinstance(check, Mapping) for check in checks):
        return ["CI unknown"]
    named, _other = group_collapsed_by_name(list(checks))
    policy = load_advisory_checks()
    grouped = {
        name: blocking_rows
        for name, rows in named.items()
        if name != "fleet/cross-family-review"
        if (
            blocking_rows := [
                row
                for row in rows
                if not is_advisory(name, workflow=row.get("workflowName") or row.get("workflow"), policy=policy)
            ]
        )
    }
    blockers = []
    for name in set(required) | set(grouped):
        versions = grouped.get(name, [])
        if not versions:
            blockers.append(f"CI pending {name}")
            continue
        kinds = {_check_row_kind(row) for row in versions}
        if "red" in kinds:
            blockers.append(f"CI red {name}")
        elif "pending" in kinds:
            blockers.append(f"CI pending {name}")
        elif "unknown" in kinds:
            blockers.append(f"CI unknown {name}")
    return sorted(blockers)


def classify_pr(pr: Mapping[str, Any], verdict: Verdict, *, queued: bool | None, observed_at: str) -> PRReport:
    """Expose a deterministic, importable state classifier for the queue keeper."""
    number = pr.get("number")
    head = pr.get("headRefOid")
    if not isinstance(number, int) or number < 1 or not isinstance(head, str) or not SHA.fullmatch(head):
        return PRReport(
            int(number or 0),
            str(head or "")[:12],
            observed_at,
            "unknown",
            ("invalid PR identity",),
            verdict.untrusted_markers,
            verdict.reason,
            verdict.comment_id,
            verdict.superseded_markers,
        )
    blockers: list[str] = []
    if pr.get("isDraft") is True:
        blockers.append("draft")
    if verdict.state != "APPROVED":
        blockers.append(verdict.state)
    blockers.extend(_check_blockers(pr))
    mergeable = str(pr.get("mergeable") or "").upper()
    if mergeable in {"CONFLICTING", "DIRTY"}:
        blockers.append("merge conflict")
    if queued is None:
        blockers.append("queue lookup unknown")
    if pr.get("isDraft") is True:
        state = "blocked draft"
    elif queued is True:
        state = "queued"
    elif pr.get("autoMergeRequest"):
        state = "armed"
    elif verdict.state == "unknown" or queued is None or "CI unknown" in " ".join(blockers):
        state = "CF-unknown" if verdict.state == "unknown" else "unknown"
    elif verdict.state in {"needs-CF", "CF-unrecorded", "CF-stale", NEEDS_SEAT, NEEDS_COVERAGE}:
        state = verdict.state
    elif verdict.state in REJECTED:
        state = "CF-rejected"
    elif any(item.startswith("CI red") for item in blockers):
        state = "CI-red " + ", ".join(item.removeprefix("CI red ") for item in blockers if item.startswith("CI red"))
    elif any(item.startswith("CI pending") for item in blockers):
        state = "CI-pending"
    elif "merge conflict" in blockers:
        state = "blocked merge conflict"
    else:
        state = "ready"
    return PRReport(
        number,
        head[:12],
        observed_at,
        state,
        tuple(blockers),
        verdict.untrusted_markers,
        verdict.reason,
        verdict.comment_id,
        verdict.superseded_markers,
    )


class GitHubAdapter:
    """Read-only GitHub CLI boundary. Paged lookups use --slurp and reject malformed pages."""

    def __init__(self, repo_root: Path, *, runner: Runner | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self._runner = runner or self._default_runner

    def _default_runner(self, args: list[str]) -> str:
        try:
            result = request_run(
                args,
                cwd=self.repo_root,
                text=True,
                capture_output=True,
                timeout=DEFAULT_GH_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SweepError(
                f"{args.verb if isinstance(args, Request) else ' '.join(args[:4])} timed out after {DEFAULT_GH_TIMEOUT_SECONDS}s"
            ) from exc
        observation = getattr(result, "github_result", None)
        if observation is not None and (observation.stale or observation.error == "github_rate_limited"):
            raise GitHubRateLimited(observation.reset_at)
        if result.returncode:
            raise SweepError((result.stderr or result.stdout or "GitHub lookup failed")[:1000])
        return result.stdout

    def _json(self, args: list[str]) -> Any:
        try:
            return json.loads(self._runner(args))
        except (ValueError, TypeError) as exc:
            raise SweepError("GitHub returned invalid JSON") from exc

    def identity(self) -> str:
        login = self._json(Request("read-identity")).get("login", "").strip()
        if not login:
            raise SweepError("authenticated gh identity unavailable")
        return login

    def list_open_prs(self, repository: str) -> list[dict[str, Any]]:
        payload = self._json(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repository,
                "--state",
                "open",
                "--limit",
                "1000",
                "--json",
                "number,isDraft,headRefOid,headRefName,baseRefName,autoMergeRequest,statusCheckRollup,mergeable",
            ]
        )
        if not isinstance(payload, list) or len(payload) >= 1000 or not all(isinstance(item, dict) for item in payload):
            raise SweepError("open PR list partial or malformed")
        return payload

    def comments(self, repository: str, number: int) -> list[dict[str, Any]]:
        pages = self._json(Request("read-comments", repo=repository, number=number, paginate=True, slurp=True))
        if not isinstance(pages, list) or not all(isinstance(page, list) for page in pages):
            raise SweepError("PR comments pagination incomplete")
        comments = [item for page in pages for item in page]
        if not all(isinstance(item, dict) for item in comments):
            raise SweepError("PR comments malformed")
        return comments

    def pr_files(self, repository: str, number: int) -> list[str]:
        pages = self._json(Request("read-pr-files", repo=repository, number=number, paginate=True, slurp=True))
        if not isinstance(pages, list) or not all(isinstance(page, list) for page in pages):
            raise SweepError("PR files pagination incomplete")
        try:
            return pr_file_paths([item for page in pages for item in page])
        except ValueError as exc:
            raise SweepError(str(exc)) from exc

    def queue_membership(self, repository: str, pr: Mapping[str, Any]) -> bool:
        data = self._json(
            Request(
                "read-membership-head", repo=repository, number=pr["number"], branch=pr.get("baseRefName") or "main"
            )
        )
        if not isinstance(data, dict) or data.get("errors"):
            raise SweepError("merge queue GraphQL lookup incomplete")
        repo = (data.get("data") or {}).get("repository")
        node = repo.get("pullRequest") if isinstance(repo, dict) else None
        if (
            not isinstance(node, dict)
            or node.get("headRefOid") != pr.get("headRefOid")
            or not isinstance(node.get("isInMergeQueue"), bool)
        ):
            raise SweepError("merge queue head moved or membership unavailable")
        return node["isInMergeQueue"]


def run(adapter: GitHubAdapter, repository: str, *, now: datetime | None = None) -> list[PRReport]:
    observed = (now or datetime.now(UTC)).isoformat(timespec="microseconds")
    prs = adapter.list_open_prs(repository)
    try:
        login = adapter.identity()
    except SweepError:
        login = None
    rows = []
    for pr in prs:
        number, head = pr.get("number"), pr.get("headRefOid")
        if not isinstance(number, int) or number < 1 or not isinstance(head, str) or not SHA.fullmatch(head):
            rows.append(classify_pr(pr, Verdict("unknown", reason=HEAD_INVALID), queued=None, observed_at=observed))
            continue
        try:
            comments = adapter.comments(repository, number)
            content = changes_learner_content(adapter.pr_files(repository, number))
            verdict = lookup_verdict(comments, head, login, learner_content=content)
        except SweepError:
            verdict = Verdict("unknown", reason=COMMENTS_UNAVAILABLE)
        try:
            queued = adapter.queue_membership(repository, pr)
        except (SweepError, ValueError, KeyError):
            queued = None
        rows.append(classify_pr(pr, verdict, queued=queued, observed_at=observed))
    return rows


@timer
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report exact-head PR review, CI and queue state without mutations.\n"
        "Use for landing evidence; the local keeper owns queue changes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python -m scripts.orchestration.integration_sweep --repo owner/repo --report\n"
        "  .venv/bin/python -m scripts.orchestration.integration_sweep --repo owner/repo --json\n"
        "Outputs: Read-only GitHub PR state report on stdout; no writes.\n"
        "Exit codes: 0: report complete; 1: lookup failed; 2: retired --apply refused.\n"
        "Related: scripts/review/record_cf_verdict.py, scripts/orchestration/merge_queue_keeper.py; #9951",
    )
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument("--report", action="store_true", help="Print the read-only PR state report (default behavior)")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text (default: text)")
    parser.add_argument(
        "--apply", action="store_true", help="Retired and refused; landing is keeper-owned (default: false)"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Checkout used for GitHub commands, e.g. . (default: current working directory)",
    )
    args = parser.parse_args(argv)
    if args.apply:
        print("integration sweep refused: --apply is retired; this sweep is report-only")
        return 2
    try:
        rows = run(GitHubAdapter(args.repo_root), args.repo)
    except SweepError as exc:
        print(f"integration sweep refused: {exc}")
        return 1
    if args.json:
        print(json.dumps([asdict(row) for row in rows], sort_keys=True))
    else:
        for row in rows:
            blockers = ", ".join(row.blockers) or "none"
            untrusted = f" untrusted-marker={','.join(row.untrusted_markers)}" if row.untrusted_markers else ""
            print(
                f"#{row.number} head={row.head} observed_at={row.observed_at} state={row.state} blockers={blockers}"
                f"{untrusted}{verdict_detail(row.verdict_reason, row.verdict_comment, row.superseded_markers)}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
