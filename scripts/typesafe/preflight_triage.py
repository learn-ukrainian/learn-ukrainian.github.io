"""Pre-dispatch TypeSafe/Jev readiness triage for ``delegate.py dispatch`` (#8183).

Fleet best practice: docs/best-practices/typesafe-jev.md § 3.4

Reuses the CI triage primitives (one shared question set, thresholds and
answer parsing) so the pre-dispatch hook and the Gate job cannot drift. The CI
job keeps its own ``ready | needs_human | broken`` strings; this module adapts
them onto the issue's ``ready_for_review | insufficient_evidence |
broken_or_failing`` labels.

Advisory: a missing key, API failure or malformed response skips (dispatch
proceeds). TypeSafe is never CF-of-record or merge authority.
"""

from __future__ import annotations

import http.client
import json
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from scripts.ci.typesafe_pr_triage import (
    QUESTIONS,
    MalformedResponse,
    build_state,
    call_system_one,
    is_confident_break,
    parse_answers,
)

FAST_FAIL_EXIT_CODE = 3
MAX_TEST_LOG_CHARS = 8_000
NO_TEST_LOG = "(no local test log provided)"
SECRET_PATH = Path.home() / ".secrets" / "typesafe-ai.key"

# In-process counter (tests + same-process callers); the JSONL ledger below is
# the durable record across dispatches.
FAST_FAIL_COUNT = 0

SystemOne = Callable[[dict[str, Any], dict[str, Any], str], dict[str, Any]]


class PreflightLabel(StrEnum):
    READY_FOR_REVIEW = "ready_for_review"
    BROKEN_OR_FAILING = "broken_or_failing"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


_CI_TO_PREFLIGHT = {
    "ready": PreflightLabel.READY_FOR_REVIEW,
    "broken": PreflightLabel.BROKEN_OR_FAILING,
    "needs_human": PreflightLabel.INSUFFICIENT_EVIDENCE,
}


@dataclass(frozen=True)
class PreflightResult:
    fast_fail: bool
    message: str
    label: PreflightLabel | None = None
    confidence: float | None = None
    high_risk: float | None = None


def load_api_key(secret_path: Path | None = None) -> str:
    """Prefer the canonical key file, then ``TYPESAFE_API_KEY``; ``""`` if none."""
    path = secret_path or SECRET_PATH
    try:
        if path.is_file():
            lines = path.read_text(encoding="utf-8").splitlines()
            if lines and lines[0].strip():
                return lines[0].strip()
    except OSError:
        pass
    return os.environ.get("TYPESAFE_API_KEY", "").strip()


def truncate_test_log(text: str, limit: int = MAX_TEST_LOG_CHARS) -> str:
    """Keep the tail: pytest puts the verdict and failures at the end."""
    if len(text) <= limit:
        return text
    return f"[truncated {len(text) - limit} earlier chars]...\n{text[-limit:]}"


def read_test_log(path: Path | None) -> str:
    if path is None:
        return NO_TEST_LOG
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return NO_TEST_LOG
    return truncate_test_log(text) if text.strip() else NO_TEST_LOG


def collect_candidate(base: str, cwd: Path) -> tuple[list[str], str]:
    """Changed paths and unified diff of ``cwd`` against ``base`` (incl. uncommitted)."""
    paths = subprocess.check_output(["git", "diff", "--name-only", base], text=True, cwd=cwd, timeout=60).splitlines()
    diff = subprocess.check_output(["git", "diff", base], text=True, cwd=cwd, timeout=60)
    return [p for p in paths if p], diff


def run_preflight(
    paths: list[str],
    diff: str,
    test_log: str,
    api_key: str,
    *,
    system_one: SystemOne = call_system_one,
) -> PreflightResult:
    if not api_key:
        return PreflightResult(False, "preflight-triage: no TypeSafe key — skipping.")
    if not paths:
        return PreflightResult(False, "preflight-triage: no changed files — skipping.")

    state = build_state(paths, diff, "pre-dispatch", test_log=test_log)
    try:
        response = system_one(state, QUESTIONS, api_key)
    except (OSError, ValueError, http.client.HTTPException) as exc:
        # Class name only: str(exc) may echo the Authorization header value.
        return PreflightResult(False, f"preflight-triage: API call failed ({type(exc).__name__}) — skipping.")
    try:
        if not isinstance(response, dict):
            raise MalformedResponse("response is not an object")
        choice, confidence, high_risk = parse_answers(response.get("answers"))
    except MalformedResponse:
        return PreflightResult(False, "preflight-triage: unexpected API response shape — skipping.")

    label = _CI_TO_PREFLIGHT.get(choice, PreflightLabel.INSUFFICIENT_EVIDENCE)
    fast_fail = is_confident_break(choice, confidence, high_risk)
    verdict = "FAST-FAIL" if fast_fail else "pass"
    message = f"preflight-triage: {label.value} confidence={confidence:.2f} high_risk={high_risk:.2f} -> {verdict}"
    if fast_fail:
        message += (
            "\n  The candidate diff looks broken (syntax error, placeholder standing in for "
            "real code, or unsupported test/proof claim). Fix it and re-dispatch, or drop "
            "--preflight-triage to override."
        )
    return PreflightResult(fast_fail, message, label, confidence, high_risk)


def record_fast_fail(task_id: str, result: PreflightResult, ledger: Path | None) -> None:
    """Bump the counter and append one JSONL row to the ledger (best effort)."""
    global FAST_FAIL_COUNT
    FAST_FAIL_COUNT += 1
    if ledger is None:
        return
    row = {
        "ts": datetime.now(UTC).isoformat(),
        "task_id": task_id,
        "label": result.label.value if result.label else None,
        "confidence": result.confidence,
        "high_risk": result.high_risk,
    }
    try:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except OSError:
        pass
