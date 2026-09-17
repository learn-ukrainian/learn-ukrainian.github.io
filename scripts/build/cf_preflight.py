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
from pathlib import Path
from typing import Any

_SHA40 = re.compile(r"^[0-9a-f]{40}$", re.I)
# Accept formal COMMENT fallbacks and sealed publication wording.
_APPROVE = re.compile(
    r"(?im)(?:reviewer\s+)?verdict\s*:\s*(?:approve|approved)\b"
    r"|\bVERDICT\s*:\s*(?:APPROVE|APPROVED)\b"
)
_REQUEST_CHANGES = re.compile(
    r"(?im)(?:reviewer\s+)?verdict\s*:\s*request[_ -]?changes\b"
    r"|\bVERDICT\s*:\s*(?:CHANGES_REQUESTED|REQUEST_CHANGES)\b"
)
_HEAD_IN_BODY = re.compile(
    r"(?im)\b(?:exact\s+)?head(?:\s+sha)?\s*[:=]\s*`?([0-9a-f]{40})`?"
    r"|\b([0-9a-f]{40})\b"
)


@dataclass(frozen=True)
class CfPreflightResult:
    """Outcome of a CF-before-build check."""

    clear: bool
    reason: str
    head: str | None = None
    source: str | None = None


class CfPreflightError(RuntimeError):
    """Paid build blocked because CF is not clear on the exact head."""

    exit_code = 3


def normalize_head(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    head = value.strip().lower()
    return head if _SHA40.fullmatch(head) else None


def verdict_kind(body: str) -> str | None:
    """Return ``approve``, ``request_changes``, or None for one comment/review body."""
    if not isinstance(body, str) or not body.strip():
        return None
    # Prefer the more specific REQUEST_CHANGES when both appear (reviewer quotes).
    req = _REQUEST_CHANGES.search(body)
    appr = _APPROVE.search(body)
    if req and appr:
        return "request_changes" if req.start() <= appr.start() else "approve"
    if req:
        return "request_changes"
    if appr:
        return "approve"
    return None


def head_mentioned(body: str, head: str) -> bool:
    if not isinstance(body, str):
        return False
    target = head.lower()
    for match in _HEAD_IN_BODY.finditer(body):
        for group in match.groups():
            if isinstance(group, str) and group.lower() == target:
                return True
    return target in body.lower()


def evaluate_comment_bodies(
    bodies: Sequence[str],
    *,
    head: str,
) -> CfPreflightResult:
    """CF is clear only when an APPROVE for ``head`` is not superseded by REQUEST_CHANGES."""
    head_n = normalize_head(head)
    if head_n is None:
        return CfPreflightResult(False, "cf_preflight: head must be a 40-char hex SHA", head=None)

    last_for_head: str | None = None
    for body in bodies:
        if not head_mentioned(body, head_n):
            continue
        kind = verdict_kind(body)
        if kind is not None:
            last_for_head = kind

    if last_for_head == "approve":
        return CfPreflightResult(True, "cf_preflight: APPROVE on exact head", head=head_n, source="comments")
    if last_for_head == "request_changes":
        return CfPreflightResult(
            False,
            "cf_preflight: REQUEST_CHANGES still open on exact head — fix and re-CF before build",
            head=head_n,
            source="comments",
        )
    return CfPreflightResult(
        False,
        "cf_preflight: no exact-head CF APPROVE found — do not start a paid build",
        head=head_n,
        source="comments",
    )


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


def git_head(repo_root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
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
        )
    except OSError:
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def github_pr_comment_bodies(*, repo: str | None = None) -> list[str]:
    """Best-effort: bodies from the open PR for the current branch."""
    view_args = ["pr", "view", "--json", "number,url"]
    if repo:
        view_args.extend(["-R", repo])
    viewed = _gh_json(view_args)
    if not isinstance(viewed, Mapping) or not viewed.get("number"):
        return []
    number = int(viewed["number"])
    comment_args = [
        "api",
        f"repos/{{owner}}/{{repo}}/issues/{number}/comments",
        "--paginate",
    ]
    if repo:
        # Explicit repo form for api
        owner_repo = repo
        comment_args = [
            "api",
            f"repos/{owner_repo}/issues/{number}/comments",
            "--paginate",
        ]
    payload = _gh_json(comment_args)
    # Also pull review bodies (APPROVE events + COMMENT fallbacks).
    review_args = ["api", f"repos/{repo}/pulls/{number}/reviews", "--paginate"] if repo else [
        "api",
        f"repos/{{owner}}/{{repo}}/pulls/{number}/reviews",
        "--paginate",
    ]
    reviews = _gh_json(review_args)
    bodies: list[str] = []
    if isinstance(payload, list):
        for row in payload:
            if isinstance(row, Mapping) and isinstance(row.get("body"), str):
                bodies.append(row["body"])
    if isinstance(reviews, list):
        for row in reviews:
            if isinstance(row, Mapping) and isinstance(row.get("body"), str):
                bodies.append(row["body"])
    return bodies


def check_cf_preflight(
    *,
    repo_root: Path,
    head: str | None = None,
    clearance_path: Path | None = None,
    module_dir: Path | None = None,
    allow_github: bool = True,
    github_repo: str | None = None,
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
        bodies = github_pr_comment_bodies(repo=github_repo)
        if bodies:
            return evaluate_comment_bodies(bodies, head=resolved_head)

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
