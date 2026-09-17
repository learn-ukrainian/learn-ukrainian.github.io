"""Block paid V7 content builds until exact-head cross-family CF is clear.

Policy: ``agents_extensions/shared/rules/pipeline.md`` § CF before build.
Gemini self-adjust is not this gate. CF-attest CI was retired; this preflight
reads local clearance files and optional GitHub PR evidence instead.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

_SHA40 = re.compile(r"^[0-9a-f]{40}$", re.I)
_APPROVE = re.compile(
    r"(?im)(?:reviewer\s+)?verdict\s*:\s*(?:approve|approved)\b"
    r"|\bVERDICT\s*:\s*(?:APPROVE|APPROVED)\b"
)
_REQUEST_CHANGES = re.compile(
    r"(?im)(?:reviewer\s+)?verdict\s*:\s*request[_ -]?changes\b"
    r"|\bVERDICT\s*:\s*(?:CHANGES_REQUESTED|REQUEST_CHANGES)\b"
)
# Dedicated head field only (line-anchored). Rejects historical prose such as
# "Previously reviewed head:" which embeds the word "head" mid-line.
_EXPLICIT_HEAD = re.compile(
    r"(?im)^[ \t]*(?:exact[ \t]+)?head(?:[ \t]+sha)?[ \t]*[:=][ \t]*`?([0-9a-f]{40})`?"
)
_REVIEW_STATE_APPROVED = frozenset({"APPROVED"})
_REVIEW_STATE_CHANGES = frozenset({"CHANGES_REQUESTED"})
_REVIEW_STATE_DISMISSED = frozenset({"DISMISSED"})
_REVIEW_STATE_COMMENT = frozenset({"COMMENTED", "PENDING", ""})


@dataclass(frozen=True)
class CfPreflightResult:
    """Outcome of a CF-before-build check."""

    clear: bool
    reason: str
    head: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class CfEvidenceEvent:
    """One ordered CF evidence event from GitHub (comment or review)."""

    kind: str  # approve | request_changes
    head: str
    when: datetime
    source: str  # comment | review
    state: str | None = None


class CfPreflightError(RuntimeError):
    """Paid build blocked because CF is not clear on the exact head."""

    exit_code = 3


def normalize_head(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    head = value.strip().lower()
    return head if _SHA40.fullmatch(head) else None


def verdict_kind(body: str) -> str | None:
    """Return ``approve``, ``request_changes``, or None for one body."""
    if not isinstance(body, str) or not body.strip():
        return None
    req = _REQUEST_CHANGES.search(body)
    appr = _APPROVE.search(body)
    if req and appr:
        return "request_changes" if req.start() <= appr.start() else "approve"
    if req:
        return "request_changes"
    if appr:
        return "approve"
    return None


def explicit_heads_in_body(body: str) -> list[str]:
    """Return explicitly bound head SHAs (``Exact head:`` / ``head:`` only)."""
    if not isinstance(body, str):
        return []
    out: list[str] = []
    for match in _EXPLICIT_HEAD.finditer(body):
        head = normalize_head(match.group(1))
        if head and head not in out:
            out.append(head)
    return out


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed


def evaluate_evidence_events(
    events: Sequence[CfEvidenceEvent],
    *,
    head: str,
) -> CfPreflightResult:
    """CF is clear only when the latest event for ``head`` is APPROVE."""
    head_n = normalize_head(head)
    if head_n is None:
        return CfPreflightResult(False, "cf_preflight: head must be a 40-char hex SHA", head=None)

    relevant = [event for event in events if event.head == head_n]
    if not relevant:
        return CfPreflightResult(
            False,
            "cf_preflight: no exact-head CF APPROVE found — do not start a paid build",
            head=head_n,
            source="events",
        )
    # Later wins. Equal timestamps fail closed: request_changes beats approve.
    def _rank(event: CfEvidenceEvent) -> tuple[datetime, int]:
        kind_rank = 1 if event.kind == "request_changes" else 0
        return (event.when, kind_rank)

    latest = max(relevant, key=_rank)
    if latest.kind == "approve":
        return CfPreflightResult(
            True,
            f"cf_preflight: APPROVE on exact head ({latest.source})",
            head=head_n,
            source=latest.source,
        )
    return CfPreflightResult(
        False,
        "cf_preflight: REQUEST_CHANGES still open on exact head — fix and re-CF before build",
        head=head_n,
        source=latest.source,
    )


def evaluate_comment_bodies(
    bodies: Sequence[str],
    *,
    head: str,
) -> CfPreflightResult:
    """Backward-compatible helper for tests: bodies alone, synthetic chronology."""
    events: list[CfEvidenceEvent] = []
    base = datetime.fromisoformat("2000-01-01T00:00:00+00:00")
    for index, body in enumerate(bodies):
        kind = verdict_kind(body)
        heads = explicit_heads_in_body(body)
        if kind is None or not heads:
            continue
        # Ambiguous multi-head prose is not clearance for any mentioned SHA.
        if len(heads) != 1:
            continue
        events.append(
            CfEvidenceEvent(
                kind=kind,
                head=heads[0],
                when=base.replace(microsecond=index),
                source="comment",
            )
        )
    return evaluate_evidence_events(events, head=head)


def load_clearance_file(path: Path) -> CfPreflightResult:
    """Accept ``{"head": "<sha>", "verdict": "APPROVE"|"APPROVED"}`` clearance JSON."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return CfPreflightResult(False, f"cf_preflight: clearance unreadable: {path}: {exc}")
    if not isinstance(raw, Mapping):
        return CfPreflightResult(False, f"cf_preflight: clearance must be a JSON object: {path}")
    head = normalize_head(raw.get("head") or raw.get("head_sha") or raw.get("sha"))
    verdict = str(raw.get("verdict") or raw.get("VERDICT") or "").strip().upper()
    if head is None:
        return CfPreflightResult(False, f"cf_preflight: clearance missing 40-char head: {path}")
    if verdict not in {"APPROVE", "APPROVED"}:
        return CfPreflightResult(
            False,
            f"cf_preflight: clearance verdict must be APPROVE/APPROVED (got {verdict or 'empty'}): {path}",
            head=head,
            source=str(path),
        )
    return CfPreflightResult(True, f"cf_preflight: clearance file OK ({path})", head=head, source=str(path))


def write_clearance_file(path: Path, *, head: str, verdict: str = "APPROVE") -> None:
    """Write a clearance file for fixtures / post-CF handoff."""
    head_n = normalize_head(head)
    if head_n is None:
        raise ValueError("head must be a 40-char hex SHA")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"head": head_n, "verdict": verdict.upper()}, indent=2) + "\n",
        encoding="utf-8",
    )


def git_head(repo_root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return normalize_head(proc.stdout.strip())


def _gh_json(args: list[str]) -> Any | None:
    try:
        proc = subprocess.run(
            ["gh", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def events_from_github_payloads(
    *,
    comments: Sequence[Mapping[str, Any]] | None,
    reviews: Sequence[Mapping[str, Any]] | None,
) -> list[CfEvidenceEvent]:
    """Build ordered CF events from GitHub comment + review payloads."""
    events: list[CfEvidenceEvent] = []

    for row in comments or ():
        if not isinstance(row, Mapping):
            continue
        body = row.get("body")
        # Prefer updated_at so an edited REQUEST_CHANGES is not stuck at create time.
        when = _parse_timestamp(row.get("updated_at")) or _parse_timestamp(row.get("created_at"))
        if when is None or not isinstance(body, str):
            continue
        kind = verdict_kind(body)
        heads = explicit_heads_in_body(body)
        if kind is None or len(heads) != 1:
            continue
        events.append(
            CfEvidenceEvent(kind=kind, head=heads[0], when=when, source="comment")
        )

    for row in reviews or ():
        if not isinstance(row, Mapping):
            continue
        state = str(row.get("state") or "").upper()
        if state in _REVIEW_STATE_DISMISSED:
            continue
        when = _parse_timestamp(
            row.get("submitted_at") or row.get("submittedAt") or row.get("created_at")
        )
        if when is None:
            continue
        commit_id = normalize_head(row.get("commit_id") or row.get("commitId"))
        body = row.get("body") if isinstance(row.get("body"), str) else ""

        if state in _REVIEW_STATE_APPROVED:
            if commit_id is None:
                continue
            events.append(
                CfEvidenceEvent(
                    kind="approve",
                    head=commit_id,
                    when=when,
                    source="review",
                    state=state,
                )
            )
            continue

        if state in _REVIEW_STATE_CHANGES:
            if commit_id is None:
                continue
            events.append(
                CfEvidenceEvent(
                    kind="request_changes",
                    head=commit_id,
                    when=when,
                    source="review",
                    state=state,
                )
            )
            continue

        # COMMENT / PENDING fallbacks: textual verdict + explicit head (or commit_id).
        if state not in _REVIEW_STATE_COMMENT and state:
            continue
        kind = verdict_kind(body)
        if kind is None:
            continue
        heads = explicit_heads_in_body(body)
        if len(heads) == 1:
            bound = heads[0]
        elif commit_id is not None and not heads:
            bound = commit_id
        else:
            continue
        if commit_id is not None and heads and commit_id not in heads:
            # Body claims a different head than the review binding — reject.
            continue
        events.append(
            CfEvidenceEvent(
                kind=kind,
                head=bound,
                when=when,
                source="review",
                state=state or "COMMENTED",
            )
        )

    return events


def github_pr_evidence_events(*, repo: str | None = None) -> list[CfEvidenceEvent] | None:
    """Ordered CF events from the open PR, or ``None`` if a channel fetch failed.

    Empty successful channels return ``[]``. A ``None`` from either comments or
    reviews means incomplete evidence — callers must not clear a paid build.
    """
    view_args = ["pr", "view", "--json", "number,url"]
    if repo:
        view_args.extend(["-R", repo])
    viewed = _gh_json(view_args)
    if not isinstance(viewed, Mapping) or not viewed.get("number"):
        return []
    number = int(viewed["number"])
    if repo:
        comments = _gh_json(
            ["api", f"repos/{repo}/issues/{number}/comments", "--paginate"]
        )
        reviews = _gh_json(
            ["api", f"repos/{repo}/pulls/{number}/reviews", "--paginate"]
        )
    else:
        comments = _gh_json(
            ["api", f"repos/{{owner}}/{{repo}}/issues/{number}/comments", "--paginate"]
        )
        reviews = _gh_json(
            ["api", f"repos/{{owner}}/{{repo}}/pulls/{number}/reviews", "--paginate"]
        )
    if not isinstance(comments, list) or not isinstance(reviews, list):
        return None
    return events_from_github_payloads(comments=comments, reviews=reviews)


def check_cf_preflight(
    *,
    repo_root: Path,
    head: str | None = None,
    clearance_path: Path | None = None,
    module_dir: Path | None = None,
    allow_github: bool = True,
    github_repo: str | None = None,
    github_events: Sequence[CfEvidenceEvent] | None = None,
) -> CfPreflightResult:
    """Return whether a paid content build may start for ``head``."""
    resolved_head = normalize_head(head) or git_head(repo_root)
    if resolved_head is None:
        return CfPreflightResult(False, "cf_preflight: cannot resolve HEAD SHA")

    candidates: list[Path] = []
    if clearance_path is not None:
        candidates.append(clearance_path)
    env_path = os.environ.get("LU_CF_CLEARANCE_FILE", "").strip()
    if env_path:
        candidates.append(Path(env_path))
    if module_dir is not None:
        candidates.append(module_dir / "cf_clearance.json")
    candidates.append(repo_root / "cf_clearance.json")

    for path in candidates:
        if path.is_file():
            result = load_clearance_file(path)
            if not result.clear:
                return result
            if result.head != resolved_head:
                return CfPreflightResult(
                    False,
                    f"cf_preflight: clearance head {result.head} != build HEAD {resolved_head}",
                    head=resolved_head,
                    source=str(path),
                )
            return result

    if allow_github and os.environ.get("LU_CF_PREFLIGHT_SKIP_GITHUB", "").strip() not in {
        "1",
        "true",
        "yes",
    }:
        if github_events is not None:
            events: list[CfEvidenceEvent] | None = list(github_events)
        else:
            events = github_pr_evidence_events(repo=github_repo)
        if events is None:
            return CfPreflightResult(
                False,
                "cf_preflight: incomplete GitHub CF evidence "
                "(comments or reviews API failed) — do not start a paid build",
                head=resolved_head,
                source="github",
            )
        if events:
            return evaluate_evidence_events(events, head=resolved_head)

    return CfPreflightResult(
        False,
        "cf_preflight: no clearance file and no GitHub exact-head APPROVE — "
        "write cf_clearance.json after CF APPROVE, or pass --cf-clearance PATH",
        head=resolved_head,
    )


def require_cf_preflight(**kwargs: Any) -> CfPreflightResult:
    """Raise ``CfPreflightError`` when CF is not clear."""
    result = check_cf_preflight(**kwargs)
    if not result.clear:
        raise CfPreflightError(result.reason)
    return result
