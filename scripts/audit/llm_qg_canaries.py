#!/usr/bin/env python3
"""Deterministic LLM-QG canary definitions and pure evaluators."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.api.config import SEMINAR_TRACK_IDS

_NORMALIZE_RE = re.compile(r"[^A-Z0-9_]")


@dataclass(frozen=True, slots=True)
class LLMQGCanary:
    """One deterministic canary rule used by LLM-QG calibration tests."""

    canary_id: str
    level: str
    snippet: str
    required_issue_ids: frozenset[str]
    issue_family: str
    rationale: str
    forbidden_issue_ids: frozenset[str] = frozenset()


CANARIES: tuple[LLMQGCanary, ...] = (
    LLMQGCanary(
        canary_id="a1-english-scaffold-allowed",
        level="a1",
        snippet="Read the dialogue. **Я тут.** - I am here.",
        required_issue_ids=frozenset(),
        issue_family="policy",
        rationale="A1 can use concise English task support and glosses without being marked as English leakage.",
        forbidden_issue_ids=frozenset({"ENGLISH_LEAKAGE"}),
    ),
    LLMQGCanary(
        canary_id="a2-english-gloss-allowed",
        level="a2",
        snippet="Прочитайте: **прокидаюся** - I wake up. Повторіть речення українською.",
        required_issue_ids=frozenset(),
        issue_family="policy",
        rationale="A2 can still use concise English glosses while the default prose remains easy Ukrainian.",
        forbidden_issue_ids=frozenset({"ENGLISH_LEAKAGE"}),
    ),
    LLMQGCanary(
        canary_id="b1-passive-result-state",
        level="b1",
        snippet="застосунок має бути відкритий",
        required_issue_ids=frozenset({"AWKWARD_PASSIVE_RESULT_STATE"}),
        issue_family="grammar_register",
        rationale="Awkward passive/result-state phrasing should be flagged as grammar/register defect.",
    ),
    LLMQGCanary(
        canary_id="b1-anthropomorphic-pathos",
        level="b1",
        snippet="Застереження каже: будь обережний, щоб небажаний результат не стався.",
        required_issue_ids=frozenset({"UNNATURAL_ANTHROPOMORPHISM"}),
        issue_family="grammar_register",
        rationale=(
            "Metatranslated or anthropomorphic register should be flagged in B1 naturalness review."
        ),
    ),
    LLMQGCanary(
        canary_id="surface-ai-leakage",
        level="any",
        snippet="I will now think step-by-step and produce a corrected draft.",
        required_issue_ids=frozenset({"AI_LEAKAGE"}),
        issue_family="surface",
        rationale=(
            "LLM chain-of-thought / scratchpad wording should be blocked by the reviewer."
        ),
    ),
    LLMQGCanary(
        canary_id="policy-b1-english-led",
        level="b1",
        snippet="In this lesson we will cover the grammar before you can follow the Ukrainian meaning.",
        required_issue_ids=frozenset({"ENGLISH_LEAKAGE"}),
        issue_family="policy",
        rationale=(
            "B1 learner-facing prose should be Ukrainian-led; English-led narration should be flagged."
        ),
    ),
    LLMQGCanary(
        canary_id="policy-seminar-english-led",
        level="seminar",
        snippet="Students must understand this unit to improve English output in Ukrainian literature.",
        required_issue_ids=frozenset({"ENGLISH_LEAKAGE"}),
        issue_family="policy",
        rationale="Seminar prose should keep Ukrainian teaching voice; English scaffolding only."
    ),
    LLMQGCanary(
        canary_id="surface-path-leakage",
        level="any",
        snippet="Use /tmp/course-output/material.md for the next example before publishing.",
        required_issue_ids=frozenset({"PATH_LEAKAGE"}),
        issue_family="surface",
        rationale="Filesystem paths should not leak into learner-facing text.",
    ),
    LLMQGCanary(
        canary_id="surface-internal-leakage",
        level="any",
        snippet="See internal artifact: scripts/audit/llm_qg.json before final publish.",
        required_issue_ids=frozenset({"INTERNAL_LEAKAGE"}),
        issue_family="surface",
        rationale="Internal file names and debug artifacts should not leak into outputs.",
    ),
    LLMQGCanary(
        canary_id="seminar-register-pathos",
        level="seminar",
        snippet=(
            "Розповідь має надихнути учасників, пробудити гордість і об'єднати спільноту "
            "навколо правильної позиції наприкінці модуля."
        ),
        required_issue_ids=frozenset({"SEMINAR_REGISTER_PATHOS"}),
        issue_family="register_pathos",
        rationale="Seminar reviews should reject oversold motivational framing and pathos-heavy register.",
    ),
)


def _canonical_level(level: str | None) -> str | None:
    if level is None:
        return None
    wanted = level.strip().lower()
    if not wanted:
        return None
    if wanted in SEMINAR_TRACK_IDS:
        return "seminar"
    if wanted.startswith("b1"):
        return "b1"
    return wanted


def _selected_canary_ids(result: Any) -> frozenset[str] | None:
    if not isinstance(result, Mapping):
        return None
    raw = result.get("canary_id")
    if raw is None:
        raw = result.get("canary_ids")
    if isinstance(raw, str):
        return frozenset({raw})
    if isinstance(raw, list):
        return frozenset(item for item in raw if isinstance(item, str))
    return None


def list_canaries(
    level: str | None = None,
    *,
    canary_ids: frozenset[str] | None = None,
) -> tuple[LLMQGCanary, ...]:
    """Return canaries applicable to the requested level.

    ``level=None`` returns all canaries.
    """

    wanted = _canonical_level(level)
    if wanted is None:
        return CANARIES
    canaries = tuple(canary for canary in CANARIES if canary.level in {"any", wanted})
    if canary_ids is not None:
        canaries = tuple(canary for canary in canaries if canary.canary_id in canary_ids)
    return canaries


def required_issue_ids(
    level: str,
    *,
    canary_ids: frozenset[str] | None = None,
) -> frozenset[str]:
    """Return issue IDs required for this level's canaries."""

    return frozenset(
        issue_id
        for canary in list_canaries(level, canary_ids=canary_ids)
        for issue_id in canary.required_issue_ids
    )


def forbidden_issue_ids(
    level: str,
    *,
    canary_ids: frozenset[str] | None = None,
) -> frozenset[str]:
    """Return issue IDs forbidden for this level's allow-list canaries."""

    return frozenset(
        issue_id
        for canary in list_canaries(level, canary_ids=canary_ids)
        for issue_id in canary.forbidden_issue_ids
    )


def normalize_issue_id(raw: Any) -> str | None:
    """Normalize a raw issue identifier to canonical uppercase underscore form."""

    if not isinstance(raw, str):
        return None
    normalized = _NORMALIZE_RE.sub("_", raw.strip().upper())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or None


def _yield_issue_values(obj: Mapping[str, Any]) -> list[str]:
    fields = (
        "issue_id",
        "issue_ids",
        "issue_type",
        "issue_types",
        "type",
        "kind",
        "tag",
        "error_class",
        "issue",
        "flags",
        "flags_raised",
    )
    issue_values: list[str] = []
    for field in fields:
        value = obj.get(field)
        if isinstance(value, str):
            issue_values.append(value)
        elif isinstance(value, list):
            issue_values.extend(item for item in value if isinstance(item, str))
    return issue_values


def extract_issue_ids(result: Any) -> frozenset[str]:
    """Extract canonical issue IDs from a JSON-ish LLM result."""

    if not isinstance(result, Mapping):
        return frozenset()

    ids: set[str] = set()
    payload = dict(result)

    def add_values(value: Any) -> None:
        if isinstance(value, str):
            normalized = normalize_issue_id(value)
            if normalized:
                ids.add(normalized)
        elif isinstance(value, list):
            for item in value:
                add_values(item)
        elif isinstance(value, Mapping):
            for raw in _yield_issue_values(value):
                normalized = normalize_issue_id(raw)
                if normalized:
                    ids.add(normalized)

    def add_from_findings(value: Any) -> None:
        if not isinstance(value, list):
            return
        for finding in value:
            if isinstance(finding, (Mapping, str)):
                add_values(finding)

    add_values(payload.get("issue_ids"))
    add_values(payload.get("flags"))
    add_values(payload.get("flags_raised"))
    add_from_findings(payload.get("findings"))

    aggregate = payload.get("aggregate")
    if isinstance(aggregate, Mapping):
        add_values(aggregate.get("issue_ids"))
        add_values(aggregate.get("flags"))
        add_values(aggregate.get("flags_raised"))
        add_from_findings(aggregate.get("findings"))

    dimensions = payload.get("dimensions")
    if isinstance(dimensions, Mapping):
        for entry in dimensions.values():
            if isinstance(entry, Mapping):
                add_values(entry.get("issue_ids"))
                add_values(entry.get("flags"))
                add_values(entry.get("flags_raised"))
                add_from_findings(entry.get("findings"))

    return frozenset(ids)


def evaluate_canaries(result: Any, level: str) -> dict[str, Any]:
    """Match a JSON-ish LLM result to required issue IDs for one level."""

    selected_ids = _selected_canary_ids(result)
    applicable_canaries = list_canaries(level, canary_ids=selected_ids)
    required = required_issue_ids(level, canary_ids=selected_ids)
    forbidden = forbidden_issue_ids(level, canary_ids=selected_ids)
    found = extract_issue_ids(result)
    missing = required - found
    forbidden_found = forbidden & found

    matched_canaries: list[str] = []
    missed_canaries: list[str] = []
    for canary in applicable_canaries:
        required_pass = canary.required_issue_ids.issubset(found)
        forbidden_pass = not (canary.forbidden_issue_ids & found)
        if required_pass and forbidden_pass:
            matched_canaries.append(canary.canary_id)
        else:
            missed_canaries.append(canary.canary_id)

    return {
        "level": _canonical_level(level) or "",
        "canary_ids": tuple(sorted(canary.canary_id for canary in applicable_canaries)),
        "passed": len(missed_canaries) == 0,
        "required_issue_ids": tuple(sorted(required)),
        "forbidden_issue_ids": tuple(sorted(forbidden)),
        "found_issue_ids": tuple(sorted(found)),
        "missing_issue_ids": tuple(sorted(missing)),
        "forbidden_issue_ids_found": tuple(sorted(forbidden_found)),
        "matched_canaries": tuple(sorted(matched_canaries)),
        "missed_canaries": tuple(sorted(missed_canaries)),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", nargs="?", type=Path, help="Optional JSON reviewer result to evaluate.")
    parser.add_argument("--level", default="b1", help="Level/profile to evaluate, e.g. a1, a2, b1, seminar.")
    parser.add_argument("--list", action="store_true", help="Print applicable canaries instead of evaluating a result.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list:
        payload = [asdict(canary) for canary in list_canaries(args.level)]
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=sorted))
        return 0
    if args.result is None:
        raise SystemExit("error: result file is required unless --list is set")
    result = json.loads(args.result.read_text(encoding="utf-8"))
    report = evaluate_canaries(result, args.level)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
