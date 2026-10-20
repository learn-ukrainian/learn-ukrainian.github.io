"""Exact-head security approval, separate from ordinary cross-family review."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from scripts.orchestration.integration_sweep import (
    MARKER_PREFIX as CF_MARKER_PREFIX,
)
from scripts.orchestration.integration_sweep import (
    TRUSTED_ASSOCIATIONS,
    _author_login,
    _edited,
    _field,
    parse_marker,
)
from scripts.review.security_paths import is_security_sensitive_change

MARKER_PREFIX = "<!-- security-signoff"
SIGNOFF_MODELS = frozenset({"claude-opus-5-5", "gpt-6.1-sol"})
_MARKER = re.compile(
    r"<!-- security-signoff v1 sha=(?P<sha>[0-9a-fA-F]{40}) "
    r"task=(?P<task>[A-Za-z0-9_./-]+) verdict=PASS "
    r"model=(?P<model>[A-Za-z0-9_.-]+) -->"
)


class SecuritySignoffError(ValueError):
    """Security evidence is missing or cannot be established."""


def parse_security_signoff(body: str) -> dict[str, str] | None:
    """Accept exactly one standalone, qualified PASS marker in a comment."""
    if body.count(MARKER_PREFIX) != 1:
        return None
    for line in body.splitlines():
        match = _MARKER.fullmatch(line)
        if match and match["model"] in SIGNOFF_MODELS:
            return match.groupdict()
    return None


def _independent_review(body: str, signoff: Mapping[str, str]) -> bool:
    """A marker beside a cf-verdict needs that verdict's cross-family, known-history APPROVE.

    Red-team mode and unknown history are ordinary-CF waivers, never independent sign-off.
    A body without a cf-verdict keeps the bare-marker handling unchanged.
    """
    if CF_MARKER_PREFIX not in body:
        return True
    verdict = parse_marker(body)
    return bool(
        verdict
        and verdict["verdict"] == "APPROVED"
        and verdict["sha"] == signoff["sha"].lower()
        and verdict["task"] == signoff["task"]
        and verdict["model"] == signoff["model"]
        and "review_mode" not in verdict
        and not verdict.get("unknown_history")
    )


def require_security_signoff(
    head: str,
    *,
    read_files: Callable[[], Sequence[Mapping[str, Any]]],
    read_comments: Callable[[], Sequence[Mapping[str, Any]]],
    read_login: Callable[[], str],
) -> None:
    """Refuse unreadable paths or sensitive changes without trusted exact-head approval.

    The file reader must establish completeness. Both names of a rename count.
    Evidence readers are lazy so non-sensitive changes keep their existing gates.
    """
    try:
        files = read_files()
        if not isinstance(files, (list, tuple)):
            raise ValueError
        paths = []
        for row in files:
            if not isinstance(row, Mapping) or not isinstance(row.get("filename"), str) or not row["filename"]:
                raise ValueError
            paths.append(row["filename"])
            if row.get("status") == "renamed" and "previous_filename" not in row:
                raise ValueError
            if "previous_filename" in row:
                previous = row["previous_filename"]
                if not isinstance(previous, str) or not previous:
                    raise ValueError
                paths.append(previous)
    except Exception as exc:
        raise SecuritySignoffError("security-signoff paths unreadable") from exc
    if not is_security_sensitive_change(paths):
        return
    if not isinstance(head, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", head):
        raise SecuritySignoffError("security-signoff head invalid")
    try:
        comments, login = read_comments(), read_login()
        if not isinstance(comments, (list, tuple)) or not isinstance(login, str) or not login:
            raise ValueError
        for comment in comments:
            if not isinstance(comment, Mapping) or not isinstance(comment.get("body"), str):
                raise ValueError
            marker = parse_security_signoff(comment["body"])
            if (
                marker
                and marker["sha"].lower() == head.lower()
                and _author_login(comment) == login
                and _field(comment, "author_association", "authorAssociation") in TRUSTED_ASSOCIATIONS
                and not _edited(comment)
                and _independent_review(comment["body"], marker)
            ):
                return
    except Exception as exc:
        raise SecuritySignoffError("security-signoff evidence unreadable") from exc
    raise SecuritySignoffError("security-signoff required for current head")
