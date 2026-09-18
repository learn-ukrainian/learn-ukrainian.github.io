"""Cheap TypeSafe/Jev triage of a PR/merge_group diff for the CI Gate.

Fleet best practice: docs/best-practices/typesafe-jev.md
Skill: agents_extensions/shared/skills/typesafe-ai/SKILL.md

One batched ``system_one`` call per run: a Choice on overall readiness and a
Noul on whether the diff smells like it touches a security/policy boundary.
Code composes the two answers into a pass/fail; TypeSafe never becomes CF or
merge authority (docs/best-practices/typesafe-jev.md § 6).

Missing ``TYPESAFE_API_KEY`` (no secret configured, or a fork PR that cannot
see repo secrets) skips with exit 0 — this job is advisory, not required.
A live API/network failure also skips rather than blocking merges on a
third-party dependency (docs/best-practices/typesafe-jev.md § 6 hard rail 4:
TypeSafe never replaces merge gates).
"""

from __future__ import annotations

import http.client
import json
import math
import os
import subprocess
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

API_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
MAX_DIFF_CHARS = 20_000

# readiness==broken fails the job only when the Choice is confident, or the
# high_risk Noul independently clears this bar (best-practices § 4: "High
# stakes... require very high conf").
CHOICE_FAIL_CONFIDENCE = 0.8
HIGH_RISK_FAIL_THRESHOLD = 0.8

QUESTIONS: dict[str, Any] = {
    "readiness": {
        "type": "choice",
        "instructions": (
            "Given this change's changed file paths and unified diff, is it ready to "
            "merge, does it need human review, or is it broken? `broken` means a "
            "concrete smell: an apparent syntax error, an unresolved TODO/placeholder "
            "left in place of real code, or a claim of tests/proof that the diff does "
            "not actually contain."
        ),
        "criteria": {
            "ready": "The diff looks complete and internally consistent; nothing obviously broken.",
            "needs_human": "Ambiguous, large, or unusual enough to warrant a human look, but nothing concretely broken.",
            "broken": "Contains an apparent syntax error, a placeholder/TODO standing in for real code, or an unsupported test/proof claim.",
        },
    },
    "high_risk": {
        "type": "noul",
        "instructions": (
            "Does this diff touch a security or policy boundary — authentication, "
            "secrets, credentials, permissions, access control, or CI/CD trust "
            "boundaries — in a way a reviewer should specifically flag?"
        ),
    },
}


def resolve_changed_paths(base: str, head: str, *, cwd: Path | None = None) -> list[str]:
    raw = subprocess.check_output(["git", "diff", "--name-only", base, head], text=True, cwd=cwd, timeout=60)
    return [line for line in raw.splitlines() if line]


def resolve_diff(base: str, head: str, *, cwd: Path | None = None) -> str:
    return subprocess.check_output(["git", "diff", base, head], text=True, cwd=cwd, timeout=60)


def truncate_diff(diff: str, limit: int = MAX_DIFF_CHARS) -> str:
    if len(diff) <= limit:
        return diff
    dropped = len(diff) - limit
    return f"{diff[:limit]}\n...[truncated {dropped} more chars]"


def build_state(paths: list[str], diff: str, event: str, test_log: str | None = None) -> dict[str, Any]:
    state: dict[str, Any] = {"event": event, "changed_paths": paths, "diff": truncate_diff(diff)}
    if test_log is not None:
        state["test_log"] = test_log
    return state


def call_system_one(
    state: dict[str, Any],
    questions: dict[str, Any],
    api_key: str,
    *,
    model: str = DEFAULT_MODEL,
    timeout: int = 30,
) -> dict[str, Any]:
    payload = json.dumps({"model": model, "state": state, "questions": questions}).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "learn-ukrainian-ci-typesafe-triage/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class MalformedResponse(ValueError):
    """The API answered, but not in the shape ``evaluate`` needs."""


def _unit_float(value: Any, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MalformedResponse(f"{what} is not a number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise MalformedResponse(f"{what} is too large to convert") from exc
    if not math.isfinite(number) or not 0.0 <= number <= 1.0:
        raise MalformedResponse(f"{what} is outside [0, 1]")
    return number


def parse_answers(answers: Any) -> tuple[str, float, float]:
    """Validate the raw answers; return ``(choice, confidence, high_risk)``.

    Raises ``MalformedResponse`` on an unexpected shape (null answers, invalid
    confidence).
    """
    if not isinstance(answers, dict):
        raise MalformedResponse("answers is not an object")
    readiness = answers.get("readiness")
    high_risk_answer = answers.get("high_risk")
    if not isinstance(readiness, dict) or not isinstance(high_risk_answer, dict):
        raise MalformedResponse("missing readiness/high_risk answer")
    choice = readiness.get("choice")
    if not isinstance(choice, str):
        raise MalformedResponse("readiness choice is not a string")
    confidence = _unit_float(readiness.get("confidence"), "confidence")
    high_risk = _unit_float(high_risk_answer.get("noul"), "high_risk")
    return choice, confidence, high_risk


def is_confident_break(choice: str, confidence: float, high_risk: float) -> bool:
    return choice == "broken" and (confidence >= CHOICE_FAIL_CONFIDENCE or high_risk >= HIGH_RISK_FAIL_THRESHOLD)


def evaluate(answers: Any) -> tuple[bool, str]:
    """Compose the two raw answers into a pass/fail. Never logs secrets.

    Callers treat ``MalformedResponse`` as an advisory skip.
    """
    choice, confidence, high_risk = parse_answers(answers)
    should_fail = is_confident_break(choice, confidence, high_risk)
    verdict = "FAIL" if should_fail else "pass"
    summary = (
        f"typesafe-jev triage: readiness={choice!r} confidence={confidence:.2f} high_risk={high_risk:.2f} -> {verdict}"
    )
    return should_fail, summary


def triage(
    paths: list[str],
    diff: str,
    event: str,
    api_key: str,
    *,
    system_one: Callable[[dict[str, Any], dict[str, Any], str], dict[str, Any]] = call_system_one,
) -> tuple[int, str]:
    if not paths:
        return 0, "typesafe-jev triage: no changed files — skipping."

    state = build_state(paths, diff, event)
    try:
        response = system_one(state, QUESTIONS, api_key)
    except (OSError, ValueError, http.client.HTTPException) as exc:
        # Class name only: str(exc) may echo the Authorization header value.
        return 0, f"typesafe-jev triage: API call failed ({type(exc).__name__}) — advisory, not blocking."

    try:
        if not isinstance(response, dict):
            raise MalformedResponse("response is not an object")
        should_fail, summary = evaluate(response.get("answers"))
    except MalformedResponse:
        return 0, "typesafe-jev triage: unexpected API response shape — advisory, not blocking."
    return (1 if should_fail else 0), summary


def main() -> int:
    api_key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not api_key:
        print("typesafe-jev triage: TYPESAFE_API_KEY not set — skipping (advisory job).")
        return 0

    event = os.environ.get("EVENT_NAME", "")
    base = os.environ.get("BASE_SHA", "").strip()
    head = os.environ.get("HEAD_SHA", "").strip() or "HEAD"
    if not base or set(base) == {"0"}:
        print("typesafe-jev triage: no base SHA for this event — skipping.")
        return 0

    try:
        paths = resolve_changed_paths(base, head)
        diff = resolve_diff(base, head)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"typesafe-jev triage: could not resolve git diff ({exc}) — skipping.")
        return 0

    exit_code, summary = triage(paths, diff, event, api_key)
    print(summary)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
