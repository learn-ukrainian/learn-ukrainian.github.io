"""Canonical thin ``review-pr`` entrypoint (Sol fleet-comms Phase 0–3).

Pointer-only: no embedded diffs or inventory YAML. Prefer sealed Codex
``--review --pr`` isolation (#5285). Claude-dark local default for
opencode-family reviewers is GLM-5.2 (LOCAL-ONLY — never CI).
"""

from __future__ import annotations

import argparse
import re
import sys
from typing import Any

from ._review_safety import (
    MAX_REVIEW_REQUEST_BYTES,
    ReviewSafetyError,
    assert_content_size,
    prepend_read_only_contract,
)

_PR_REF_RE = re.compile(r"^(?:#|pr-)?(?P<num>\d+)$", re.IGNORECASE)

# Reviewer transport ids (not harness marketing names).
REVIEWER_CODEX = "codex"
REVIEWER_GLM = "glm"
REVIEWER_CLAUDE = "claude"
REVIEWER_AUTO = "auto"

_DEFAULT_CHECKLIST = """\
## Formal cross-family PR review (pointer-only)

**PR:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/{pr}
**Expected:** pull the PR evidence yourself (sealed snapshot / gh). Do not request
the operator to paste the diff.

### Required output
End with exactly one line:
`VERDICT: APPROVED` or `VERDICT: CHANGES_REQUESTED` or `VERDICT: BLOCKED`

If CHANGES_REQUESTED/BLOCKED, list blockers with paths.
"""


def parse_pr_number(raw: str) -> int:
    text = raw.strip()
    match = _PR_REF_RE.match(text)
    if not match:
        raise ReviewSafetyError(f"invalid_pr_ref: {raw!r} (expected digits or #N)")
    return int(match.group("num"))


def build_review_pr_prompt(pr: int, *, extra: str | None = None) -> str:
    body = _DEFAULT_CHECKLIST.format(pr=pr)
    if extra and extra.strip():
        body = f"{body}\n\n## Additional scope\n{extra.strip()}\n"
    body = prepend_read_only_contract(body)
    assert_content_size(body, limit=MAX_REVIEW_REQUEST_BYTES, label="review_pr_prompt")
    return body


def resolve_reviewer(selection: str, *, claude_available: bool | None = None) -> str:
    """Return concrete reviewer transport. Claude dark → glm (local)."""
    choice = (selection or REVIEWER_AUTO).strip().lower()
    if choice == REVIEWER_AUTO:
        if claude_available is False:
            return REVIEWER_GLM
        # Prefer sealed codex path when auto and Claude not forced — isolation-first.
        return REVIEWER_CODEX
    if choice in {REVIEWER_CODEX, REVIEWER_GLM, REVIEWER_CLAUDE}:
        return choice
    raise ReviewSafetyError(
        f"unsupported_reviewer: {selection!r} "
        f"(choose auto|codex|glm|claude)"
    )


def handle_review_pr(args: argparse.Namespace) -> int:
    """CLI handler for ``review-pr``."""
    try:
        pr = parse_pr_number(str(args.pr))
        reviewer = resolve_reviewer(args.reviewer, claude_available=args.claude_available)
        prompt = build_review_pr_prompt(pr, extra=args.extra)
    except ReviewSafetyError as exc:
        print(f"review-pr: {exc}", file=sys.stderr)
        return 2

    task_id = args.task_id or f"review-pr-{pr}"
    if args.dry_run:
        print(f"review-pr dry-run pr={pr} reviewer={reviewer} task_id={task_id}")
        print(f"prompt_bytes={len(prompt.encode('utf-8'))}")
        print("--- prompt ---")
        print(prompt)
        return 0

    from_llm = getattr(args, "from_llm", None) or "grok"
    if reviewer == REVIEWER_CODEX:
        from ._codex import ask_codex

        ask_codex(
            prompt,
            task_id=task_id,
            msg_type="review",
            from_llm=from_llm,
            review=True,
            review_pr_number=pr,
            background=bool(args.background),
            no_timeout=bool(args.no_timeout),
        )
        return 0
    if reviewer == REVIEWER_CLAUDE:
        from ._claude import ask_claude

        ask_claude(
            prompt,
            task_id=task_id,
            msg_type="review",
            from_llm=from_llm,
            review=True,
            review_pr_number=pr,
            background=bool(args.background),
        )
        return 0
    if reviewer == REVIEWER_GLM:
        from ._opencode import ask_glm

        # GLM is LOCAL-ONLY — interactive/local bridge only; never CI.
        # Isolation: GLM/opencode path still gets RO contract + size caps via prompt;
        # sealed worktree for opencode is a follow-up (Phase 0b). Prefer --reviewer codex
        # for full #5285 sealing today.
        ask_glm(
            prompt,
            task_id=task_id,
            msg_type="review",
            from_llm=from_llm,
            background=bool(args.background),
            no_timeout=bool(args.no_timeout),
        )
        return 0
    print(f"review-pr: unhandled reviewer {reviewer}", file=sys.stderr)
    return 2


def register_review_pr_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "review-pr",
        help="Pointer-only formal PR review (sealed isolation preferred)",
        description=(
            "Canonical formal code-review entrypoint. Builds a thin pointer-only "
            "prompt with a mandatory read-only contract. Default transport is "
            "Codex sealed --review --pr. When Claude is unavailable, use "
            "--reviewer glm (LOCAL-ONLY) or --reviewer auto with "
            "--claude-available false."
        ),
    )
    parser.add_argument("pr", help="PR number (e.g. 5443 or #5443)")
    parser.add_argument(
        "--reviewer",
        default=REVIEWER_AUTO,
        help="auto|codex|glm|claude (default: auto → codex sealed path)",
    )
    parser.add_argument(
        "--claude-available",
        dest="claude_available",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Hint for --reviewer auto (false selects glm local)",
    )
    parser.add_argument("--task-id", help="Bridge task id (default: review-pr-<N>)")
    parser.add_argument("--extra", help="Optional extra scope text (kept under size cap)")
    parser.add_argument("--from", dest="from_llm", help="Sender agent family")
    parser.add_argument("--background", action="store_true")
    parser.add_argument("--no-timeout", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    # Post-reply finalize is a separate CLI so review-pr stays pointer-only:
    #   .venv/bin/python -m scripts.fleet_comms formal-job accept \
    #       --pr N --verdict APPROVED --model M --family F --harness H [--publish]
