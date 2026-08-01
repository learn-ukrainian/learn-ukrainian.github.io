"""Canonical thin ``review-pr`` entrypoint (Sol fleet-comms Phase 0–3).

Pointer-only: no embedded diffs or inventory YAML. Prefer sealed Codex
``--review --pr`` isolation (#5285). Claude-dark local default for
opencode-family reviewers is GLM-5.2 (LOCAL-ONLY — never CI).

Formal CF model + effort pins (operator 2026-07-21): practical seats @ high
— Terra / Sonnet 5 / GLM — not Sol/Fable on routine PRs. Authority seats
remain on the critical review ladder only (see model_catalog.yaml).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
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

# Practical formal CF pins — keep in sync with model_catalog formal_cf_defaults.
FORMAL_CF_MODEL: dict[str, str] = {
    REVIEWER_CODEX: "gpt-5.6-terra",
    REVIEWER_CLAUDE: "claude-sonnet-5",
    REVIEWER_GLM: "glm-5.2",
}
FORMAL_CF_EFFORT: dict[str, str] = {
    REVIEWER_CODEX: "high",
    REVIEWER_CLAUDE: "high",
    REVIEWER_GLM: "high",
}


def _formal_review_authority_key(
    repository: str,
    pr_number: int,
    head_sha: str,
    patch_sha256: str,
) -> str:
    """Return a bounded opaque key for one exact-head sealed review."""
    identity = json.dumps(
        {
            "repository": repository,
            "pr_number": pr_number,
            "head_sha": head_sha,
            "patch_sha256": patch_sha256,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "formal-review:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


class _ReviewPrLifecycle:
    """Attach formal-run terminal evidence to its bridge ask without changing asks."""

    def __init__(self, *, background: bool):
        self.background = background
        self.message_id: int | None = None
        self._terminal: Any = None

    def message_created(self, message_id: int) -> None:
        """Write launch evidence before the adapter enters its run/spawn path."""
        from ._ask_lifecycle import _AskTerminalRecorder, _write_ask_launch_record

        self.message_id = message_id
        _write_ask_launch_record(message_id, pid=os.getpid(), target="review-pr")
        self._terminal = _AskTerminalRecorder(message_id)

    def record_terminal(self) -> None:
        """Write the synchronous formal review's terminal state from its ask status."""
        if self.background or self.message_id is None or self._terminal is None:
            return
        from ._ask_lifecycle import _ask_status

        status = _ask_status(self.message_id)
        if status and status.startswith("replied:"):
            self._terminal.write(0, "success")
        elif status and (status.startswith("timed-out:") or "timeout" in status.lower()):
            self._terminal.write(1, "timeout", cause=status)
        else:
            self._terminal.write(1, "failed", cause=status or "review-pr ended without a reply")

    def record_spawn_failure(self, exc: BaseException) -> None:
        """Leave the dispatch failure reason durable after an ask id exists."""
        if self.message_id is None or self._terminal is None:
            return
        from ._ask_lifecycle import record_ask_failure

        cause = f"{type(exc).__name__}: {exc}"
        record_ask_failure(self.message_id, cause)
        self._terminal.write(1, "spawn-failure" if self.background else "exception", cause=cause)

_DEFAULT_CHECKLIST = """\
## Formal cross-family PR review (pointer-only)

**PR:** https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/{pr}
**Reviewer seat:** {reviewer_model} @ effort={reviewer_effort} (transport={reviewer})
**Expected:** pull the PR evidence yourself (sealed snapshot / gh). Do not request
the operator to paste the diff.

### Required output
Emit exactly one canonical `code-review-findings.v1` JSON object — no markdown
or trailing `VERDICT:` line. It must contain `overall`
(`correctness`, `explanation`, `confidence`) and every finding with its
canonical location and evidence fields. Publication derives the GitHub gate
verdict from this evidence and preserves the review body in the PR comment.
"""


def parse_pr_number(raw: str) -> int:
    text = raw.strip()
    match = _PR_REF_RE.match(text)
    if not match:
        raise ReviewSafetyError(f"invalid_pr_ref: {raw!r} (expected digits or #N)")
    return int(match.group("num"))


def build_review_pr_prompt(
    pr: int,
    *,
    reviewer: str,
    model: str,
    effort: str,
    extra: str | None = None,
) -> str:
    body = _DEFAULT_CHECKLIST.format(
        pr=pr,
        reviewer=reviewer,
        reviewer_model=model,
        reviewer_effort=effort,
    )
    if extra and extra.strip():
        body = f"{body}\n\n## Additional scope\n{extra.strip()}\n"
    body = prepend_read_only_contract(body)
    assert_content_size(body, limit=MAX_REVIEW_REQUEST_BYTES, label="review_pr_prompt")
    return body


def resolve_reviewer(selection: str, *, claude_available: bool | None = None) -> str:
    """Return concrete reviewer transport; GLM is the preferred ACP CF seat."""
    choice = (selection or REVIEWER_AUTO).strip().lower()
    if choice == REVIEWER_AUTO:
        _ = claude_available  # retained as a compatibility-only CLI hint
        return REVIEWER_GLM
    if choice in {REVIEWER_CODEX, REVIEWER_GLM, REVIEWER_CLAUDE}:
        return choice
    raise ReviewSafetyError(
        f"unsupported_reviewer: {selection!r} "
        f"(choose auto|codex|glm|claude)"
    )


def formal_cf_pin(reviewer: str) -> tuple[str, str]:
    """Return (model_id, effort) for a formal CF transport."""
    model = FORMAL_CF_MODEL[reviewer]
    effort = FORMAL_CF_EFFORT[reviewer]
    return model, effort


def handle_review_pr(args: argparse.Namespace) -> int:
    """CLI handler for ``review-pr``."""
    try:
        pr = parse_pr_number(str(args.pr))
        reviewer = resolve_reviewer(args.reviewer, claude_available=args.claude_available)
        model, effort = formal_cf_pin(reviewer)
        if getattr(args, "model", None):
            model = str(args.model).strip()
        if getattr(args, "effort", None):
            effort = str(args.effort).strip()
        prompt = build_review_pr_prompt(
            pr,
            reviewer=reviewer,
            model=model,
            effort=effort,
            extra=args.extra,
        )
    except ReviewSafetyError as exc:
        print(f"review-pr: {exc}", file=sys.stderr)
        return 2

    task_id = args.task_id or f"review-pr-{pr}"
    if args.dry_run:
        print(
            f"review-pr dry-run pr={pr} reviewer={reviewer} "
            f"model={model} effort={effort} task_id={task_id}"
        )
        print(f"prompt_bytes={len(prompt.encode('utf-8'))}")
        print("--- prompt ---")
        print(prompt)
        return 0
    if args.background:
        print(
            "review-pr: background bridge workers are retired; enqueue the formal job "
            "through fleet-comms or run this sealed ACP review synchronously",
            file=sys.stderr,
        )
        return 2

    from_llm = (
        getattr(args, "from_llm", None)
        or os.environ.get("SESSION_HANDOFF_AGENT")
        or os.environ.get("LEARN_UKRAINIAN_AGENT_NAME")
        or "gemini"
    )
    from agent_runtime.runner import invoke_inter_agent

    from scripts.fleet_comms.authority import AuthorityService
    from scripts.fleet_comms.review_publication import (
        SealedVerdict,
        parse_review_evidence,
        verdict_from_review_evidence,
    )
    from scripts.orchestration.task_identity import DEFAULT_REPOSITORY

    from ._config import REPO_ROOT
    from ._review_worktree import (
        ReviewTarget,
        provision_review_worktree,
        validate_code_review_response,
    )

    participant = {
        REVIEWER_CODEX: "codex",
        REVIEWER_CLAUDE: "claude",
        REVIEWER_GLM: "glm",
    }[reviewer]
    family = {
        REVIEWER_CODEX: "openai",
        REVIEWER_CLAUDE: "anthropic",
        REVIEWER_GLM: "zhipu",
    }[reviewer]
    target = ReviewTarget(pr_number=pr)
    with provision_review_worktree(
        target,
        repo_root=REPO_ROOT,
        acceptance_mode="acp-inline",
    ) as checkout:
        if checkout is None:  # pragma: no cover - target above is mandatory
            raise RuntimeError("sealed review snapshot was not provisioned")
        evidence = checkout.review_prompt_evidence("acp")
        sealed_prompt = prompt + evidence
        timeout = 86400 if args.no_timeout else 1800
        worker_id = f"review-pr-acp:{os.getpid()}"
        authority_key = _formal_review_authority_key(
            DEFAULT_REPOSITORY,
            pr,
            checkout.sha,
            checkout.patch_digest,
        )
        with AuthorityService() as authority:
            authority_job = authority.enqueue_formal_review(
                repository=DEFAULT_REPOSITORY,
                pr_number=pr,
                head_sha=checkout.sha,
                gate_kind="cross-family-review",
                snapshot=evidence.encode("utf-8"),
                idempotency_key=authority_key,
            )
            formal_job = authority.require_publishable_formal_review(
                authority_job.subject_id,
                current_head_sha=checkout.sha,
            )
            if authority_job.state in {"complete", "failed", "expired", "dead_lettered"}:
                replay = authority.read_job_result(authority_job.job_id)
                if authority_job.state != "complete" or replay is None:
                    print("review-pr: prior ACP attempt is terminal and not publishable", file=sys.stderr)
                    return 1
                raw_response = replay.decode("utf-8")
            else:
                lease = authority.claim_job(
                    authority_job.job_id,
                    worker_id,
                    lease_seconds=timeout + 30,
                )
                previous_transport = os.environ.get("LU_ACPX_TRANSPORT")
                os.environ["LU_ACPX_TRANSPORT"] = "active"
                try:
                    result = invoke_inter_agent(
                        participant,
                        sealed_prompt,
                        cwd=Path(REPO_ROOT),
                        task_id=task_id,
                        correlation_id=formal_job.review_id,
                        idempotency_key=authority_key,
                        source=from_llm,
                        model=model,
                        effort=effort,
                        hard_timeout=timeout,
                    )
                except BaseException as exc:
                    authority.finish_job(
                        authority_job.job_id,
                        worker_id=worker_id,
                        fence_token=lease.fence_token,
                        state="failed",
                        result=json.dumps(
                            {"error": type(exc).__name__, "transport": "acp"},
                            sort_keys=True,
                        ).encode("utf-8"),
                    )
                    raise
                finally:
                    if previous_transport is None:
                        os.environ.pop("LU_ACPX_TRANSPORT", None)
                    else:
                        os.environ["LU_ACPX_TRANSPORT"] = previous_transport
                raw_response = str(getattr(result, "response", ""))
                authority.finish_job(
                    authority_job.job_id,
                    worker_id=worker_id,
                    fence_token=lease.fence_token,
                    state="complete" if getattr(result, "ok", False) else "failed",
                    result=raw_response.encode("utf-8"),
                )
                if not getattr(result, "ok", False):
                    print("review-pr: ACP reviewer failed without bridge retry", file=sys.stderr)
                    return 1

            if not raw_response:
                print("review-pr: ACP reviewer failed without bridge retry", file=sys.stderr)
                return 1
            validate_code_review_response(
                raw_response,
                base_sha=checkout.base_sha,
                head_sha=checkout.sha,
                patch_sha256=checkout.patch_digest,
                changed_paths=checkout.changed_paths,
                evidence_root=checkout.path,
                changed_lines=checkout.changed_line_numbers,
            )
            canonical = json.loads(raw_response)
            review_evidence = parse_review_evidence(canonical)
            verdict = (
                "BLOCKED"
                if review_evidence is None
                else verdict_from_review_evidence(review_evidence)
            )
            sealed = SealedVerdict(
                review_id=formal_job.review_id,
                repository=DEFAULT_REPOSITORY,
                pr_number=pr,
                head_sha=checkout.sha,
                gate_kind="cross-family-review",
                verdict=verdict,
                model=model,
                family=family,
                harness="acp",
                review_evidence=review_evidence,
            )
            authority.accept_formal_review_verdict(formal_job.review_id, sealed)
            print(
                json.dumps(
                    {
                        "review_id": formal_job.review_id,
                        "pr": pr,
                        "head_sha": checkout.sha,
                        "snapshot_artifact_id": formal_job.snapshot_artifact_id,
                        "authority_job_id": authority_job.job_id,
                        "verdict": verdict,
                        "reviewer": reviewer,
                        "model": model,
                        "effort": effort,
                        "transport": "acp",
                    },
                    sort_keys=True,
                )
            )
            return 0 if verdict == "APPROVED" else 1


def register_review_pr_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "review-pr",
        help="Pointer-only formal PR review (sealed isolation preferred)",
        description=(
            "Canonical formal code-review entrypoint. Builds a thin pointer-only "
            "prompt with a mandatory read-only contract. Default transport is "
            "ACP with GLM-5.2 @ high over an immutable exact-head inline snapshot. "
            "Codex and Claude selections are accepted only when their ACP route "
            "implements the requested exact model pin."
        ),
    )
    parser.add_argument("pr", help="PR number (e.g. 5443 or #5443)")
    parser.add_argument(
        "--reviewer",
        default=REVIEWER_AUTO,
        help="auto|codex|glm|claude (default: auto → GLM sealed ACP path)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Override formal CF model pin "
            "(default: codex→gpt-5.6-terra, claude→claude-sonnet-5, glm→glm-5.2; "
            "authority escalate: gpt-5.6-sol / claude-fable-5)"
        ),
    )
    parser.add_argument(
        "--effort",
        default=None,
        help=(
            "Override formal CF effort pin (default: high; authority escalate: xhigh)"
        ),
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
