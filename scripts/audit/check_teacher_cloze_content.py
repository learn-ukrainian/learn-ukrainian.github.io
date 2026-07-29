#!/usr/bin/env python3
"""Fail closed when a shipped teacher-cloze answer is not Ukrainian content."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLOZE_REL_PATH = Path("site/src/data/lexicon-teacher-cloze.json")
OVERRIDES_REL_PATH = Path("site/src/data/lexicon-teacher-cloze-overrides.json")

_CYRILLIC_LETTER_RE = re.compile(r"[\u0400-\u04ff]")
_ASCII_WORD_RE = re.compile(r"[A-Za-z]+")
_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)


def _load_json_object(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    """Load a JSON object, returning a user-actionable failure instead of crashing."""
    if not path.is_file():
        return None, [f"{label} is missing: {path}"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{label} is invalid JSON: {path}: {exc.msg}"]
    if not isinstance(value, dict):
        return None, [f"{label} must contain a JSON object: {path}"]
    return value, []


def _load_excluded_cloze_ids(path: Path, known_ids: set[str]) -> tuple[set[str], list[str]]:
    """Load optional exclusions and reject malformed or stale sidecars."""
    if not path.exists():
        return set(), []

    payload, errors = _load_json_object(path, "teacher-cloze overrides")
    if payload is None:
        return set(), errors

    excluded_ids = payload.get("excludedClozeIds")
    if not isinstance(excluded_ids, list) or not all(
        isinstance(cloze_id, str) and cloze_id for cloze_id in excluded_ids
    ):
        return set(), [f"teacher-cloze overrides require a non-empty-string excludedClozeIds list: {path}"]

    duplicates = sorted({cloze_id for cloze_id in excluded_ids if excluded_ids.count(cloze_id) > 1})
    if duplicates:
        errors.append(f"teacher-cloze overrides duplicate excludedClozeIds: {duplicates}")

    unknown = sorted(set(excluded_ids) - known_ids)
    if unknown:
        errors.append(f"teacher-cloze overrides reference unknown cloze IDs: {unknown}")
    return set(excluded_ids), errors


def _answer_fields(card: dict[str, Any]) -> Iterable[tuple[str, Any]]:
    """Yield the Ukrainian fields which can become learner-visible answers."""
    for field in ("lemmaId", "lemma", "form"):
        yield field, card.get(field)

    options = card.get("options")
    if not isinstance(options, list):
        return
    for option_index, option in enumerate(options):
        if not isinstance(option, dict) or option.get("kind") != "answer":
            continue
        for field in ("lemmaId", "label"):
            yield f"options[{option_index}].{field}", option.get(field)


def _is_non_linguistic(value: str) -> bool:
    """Allow a numeric/symbol cloze answer; those are not word-form claims."""
    return not _LETTER_RE.search(value)


def _validate_answer_value(value: Any) -> str | None:
    """Return a reason for invalid input or multiple ASCII words in an answer."""
    if not isinstance(value, str) or not value.strip():
        return "must be a non-empty string"
    if _is_non_linguistic(value):
        return None
    if len(_ASCII_WORD_RE.findall(value)) >= 2:
        return "must not be an English multi-word descriptive phrase"
    if _CYRILLIC_LETTER_RE.search(value):
        return None
    return None


def validate_teacher_cloze_content(
    cloze_path: Path,
    overrides_path: Path,
) -> list[str]:
    """Validate effective teacher-cloze answers after optional exclusions apply."""
    payload, errors = _load_json_object(cloze_path, "teacher-cloze data")
    if payload is None:
        return errors

    cards = payload.get("cloze")
    if not isinstance(cards, list):
        return [*errors, f"teacher-cloze data requires a cloze list: {cloze_path}"]

    card_ids: set[str] = set()
    for index, card in enumerate(cards):
        if not isinstance(card, dict) or not isinstance(card.get("clozeId"), str) or not card["clozeId"]:
            errors.append(f"teacher-cloze card {index} requires a non-empty string clozeId")
            continue
        if card["clozeId"] in card_ids:
            errors.append(f"teacher-cloze data duplicates clozeId: {card['clozeId']}")
        card_ids.add(card["clozeId"])

    excluded_ids, override_errors = _load_excluded_cloze_ids(overrides_path, card_ids)
    errors.extend(override_errors)

    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            errors.append(f"teacher-cloze card {index} must be an object")
            continue
        cloze_id = card.get("clozeId")
        if not isinstance(cloze_id, str) or cloze_id in excluded_ids:
            continue
        for field, value in _answer_fields(card):
            reason = _validate_answer_value(value)
            if reason:
                errors.append(f"teacher-cloze {cloze_id} {field}: {reason}; got {value!r}")
    return errors


def main(argv: list[str] | None = None) -> int:
    """Run the teacher-cloze content gate from the repository root or a fixture root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root (default: current repository)")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    errors = validate_teacher_cloze_content(root / CLOZE_REL_PATH, root / OVERRIDES_REL_PATH)
    if errors:
        print("Teacher cloze content gate failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Teacher cloze content gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
