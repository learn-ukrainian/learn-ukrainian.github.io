"""Task instructions, output schemas, prompt assembly and response validation.

Every variant of a task kind gets byte-identical instructions, schema and input
block; the only difference is the optional preamble placed first.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import jsonschema

from .common import ERROR_TYPES, sha256_text
from .dataset import ReviewItem, WritingTask

_SPAN_FIELDS = {
    "span": {"type": "string"},
    "start": {"type": "integer", "minimum": 0},
    "end": {"type": "integer", "minimum": 0},
}

REVIEW_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "corrected_text", "corrections", "style_suggestions"],
    "properties": {
        "id": {"type": "string"},
        "corrected_text": {"type": "string"},
        "corrections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["span", "start", "end", "correction", "error_type", "evidence"],
                "properties": {
                    **_SPAN_FIELDS,
                    "correction": {"type": "string"},
                    "error_type": {"type": "string"},
                    "evidence": {"type": "string"},
                },
            },
        },
        "style_suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["span", "start", "end", "suggestion", "reason"],
                "properties": {**_SPAN_FIELDS, "suggestion": {"type": "string"}, "reason": {"type": "string"}},
            },
        },
    },
}

WRITING_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "text"],
    "properties": {"id": {"type": "string"}, "text": {"type": "string", "minLength": 1}},
}

JUDGE_CRITERIA = ("naturalness", "correctness", "task_fit", "level_fit")
_SCORE = {"type": "integer", "minimum": 1, "maximum": 5}
_CRITERIA_OBJECT = {
    "type": "object",
    "additionalProperties": False,
    "required": list(JUDGE_CRITERIA),
    "properties": dict.fromkeys(JUDGE_CRITERIA, _SCORE),
}
JUDGE_ITEM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "scores", "winner", "rationale"],
    "properties": {
        "id": {"type": "string"},
        "scores": {
            "type": "object",
            "additionalProperties": False,
            "required": ["A", "B"],
            "properties": {"A": _CRITERIA_OBJECT, "B": _CRITERIA_OBJECT},
        },
        "winner": {"enum": ["A", "B", "tie"]},
        "rationale": {"type": "string"},
    },
}

ITEM_SCHEMAS = {"review": REVIEW_ITEM_SCHEMA, "writing": WRITING_ITEM_SCHEMA, "judge": JUDGE_ITEM_SCHEMA}


def response_schema(kind: str) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["items"],
        "properties": {"items": {"type": "array", "items": ITEM_SCHEMAS[kind]}},
    }


REVIEW_INSTRUCTIONS = f"""# Task: proofreading Ukrainian paragraphs

The JSON input block below holds Ukrainian paragraphs. For every paragraph, find its genuine errors \
and return the corrected paragraph.

Requirements for the answer:
- Each error is one entry in `corrections`. `span` is the exact erroneous substring of the ORIGINAL \
paragraph; `start` and `end` are its 0-based character offsets in the original paragraph (end exclusive, \
as in Python slicing); `correction` is the replacement text for that span; `error_type` is one label \
from the list below; `evidence` names the rule or source that proves the error.
- `corrected_text` is the original paragraph with exactly the listed corrections applied and nothing else changed.
- Optional stylistic improvements that are not errors belong only in `style_suggestions`, never in `corrections`.
- A paragraph without errors gets an empty `corrections` list and a `corrected_text` identical to the original.
- Every input paragraph appears exactly once in `items`, with its `id`.
- The answer is one JSON object that matches the output schema below and nothing else: no prose, no Markdown fence.

Error type labels: {", ".join(ERROR_TYPES)}.
"""

WRITING_INSTRUCTIONS = """# Task: Ukrainian writing

Each task in the JSON input block below gives a CEFR level, an instruction and, when present, a word range. \
For every task, produce the requested Ukrainian text at that level.

Requirements for the answer:
- Every input task appears exactly once in `items`, with its `id`; `text` holds only the requested text.
- The answer is one JSON object that matches the output schema below and nothing else: no prose, no Markdown fence.
"""

JUDGE_INSTRUCTIONS = f"""# Task: blind pairwise judgement of Ukrainian texts

Each comparison in the JSON input block below gives a writing task (CEFR level, instruction, word range) and \
two anonymous texts, A and B, written for it. Judge them on these criteria, each scored 1 (poor) to 5 (excellent):
- naturalness: idiomatic, native-like Ukrainian without calques, Russianisms or surzhyk;
- correctness: grammar, agreement, case government and spelling by Правопис 2019;
- task_fit: does what the instruction asks, within the word range when one is given;
- level_fit: vocabulary and structures suit the stated CEFR level.

Requirements for the judgement:
- Judge quality, not length: a longer or shorter text earns nothing for its length alone.
- The order of A and B is random and carries no information.
- `winner` is "A", "B" or "tie"; `rationale` is at most three sentences.
- Every comparison appears exactly once in `items`, with its `id`.
- The answer is one JSON object that matches the output schema below and nothing else: no prose, no Markdown fence.

Criteria keys: {", ".join(JUDGE_CRITERIA)}.
"""

INSTRUCTIONS = {"review": REVIEW_INSTRUCTIONS, "writing": WRITING_INSTRUCTIONS, "judge": JUDGE_INSTRUCTIONS}


def template_fingerprint() -> str:
    """Hash of every instruction text and schema; frozen in the run manifest."""
    payload = {kind: [INSTRUCTIONS[kind], response_schema(kind)] for kind in INSTRUCTIONS}
    return sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def review_payload(items: Sequence[ReviewItem]) -> list[dict[str, Any]]:
    return [{"id": item.id, "text": item.text} for item in items]


def writing_payload(tasks: Sequence[WritingTask]) -> list[dict[str, Any]]:
    payload = []
    for task in tasks:
        entry: dict[str, Any] = {"id": task.id, "level": task.level, "instruction": task.instruction}
        if task.min_words is not None:
            entry["min_words"] = task.min_words
        if task.max_words is not None:
            entry["max_words"] = task.max_words
        payload.append(entry)
    return payload


def build_prompt(kind: str, payload: list[dict[str, Any]], preamble: str | None = None) -> str:
    """Preamble (when any) first, then the kind's fixed instructions, schema and input."""
    parts = [preamble.strip()] if preamble else []
    parts.append(INSTRUCTIONS[kind].strip())
    schema = json.dumps(response_schema(kind), ensure_ascii=False, indent=2)
    parts.append(f"Output schema:\n```json\n{schema}\n```")
    body = json.dumps({"items": payload}, ensure_ascii=False, indent=2)
    parts.append(f"Input:\n```json\n{body}\n```")
    return "\n\n".join(parts) + "\n"


_FENCE = re.compile(r"```(?:json)?[ \t]*\n(.*?)```", re.DOTALL)


def extract_json(text: str) -> Any:
    """The answer's JSON object: the whole text, else the last parseable fence, else the outer braces."""
    stripped = text.strip()
    candidates = [stripped, *reversed(_FENCE.findall(stripped))]
    first, last = stripped.find("{"), stripped.rfind("}")
    if 0 <= first < last:
        candidates.append(stripped[first : last + 1])
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("no JSON object found in the response")


@dataclass(frozen=True)
class ItemResult:
    """One requested item's validated answer, or the reason it failed (never dropped)."""

    item_id: str
    entry: dict[str, Any] | None
    error: str | None


def validate_response(kind: str, response_text: str | None, expected_ids: Sequence[str]) -> list[ItemResult]:
    """Validate a chunk answer item by item; every expected id yields exactly one result."""
    if response_text is None:
        return [ItemResult(item_id, None, "no response") for item_id in expected_ids]
    try:
        document = extract_json(response_text)
    except ValueError as exc:
        return [ItemResult(item_id, None, f"unparseable response: {exc}") for item_id in expected_ids]
    entries = document.get("items")
    if not isinstance(entries, list):
        return [ItemResult(item_id, None, "response has no 'items' array") for item_id in expected_ids]
    by_id: dict[str, list[Any]] = {}
    for entry in entries:
        key = entry.get("id") if isinstance(entry, dict) else None
        by_id.setdefault(key if isinstance(key, str) else "", []).append(entry)
    validator = jsonschema.Draft202012Validator(ITEM_SCHEMAS[kind])
    results = []
    for item_id in expected_ids:
        matches = by_id.get(item_id, [])
        if not matches:
            results.append(ItemResult(item_id, None, "item missing from response"))
            continue
        if len(matches) > 1:
            results.append(ItemResult(item_id, None, f"item answered {len(matches)} times"))
            continue
        errors = sorted(validator.iter_errors(matches[0]), key=lambda err: list(err.absolute_path))
        if errors:
            where = "/".join(str(part) for part in errors[0].absolute_path) or "<item>"
            results.append(ItemResult(item_id, None, f"schema violation at {where}: {errors[0].message}"))
            continue
        results.append(ItemResult(item_id, matches[0], None))
    return results
