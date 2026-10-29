"""Blind absolute-rubric judging: the judge request, its sidecar schema, shuffle and audit sample.

The judge template is private bytes pinned by SHA-256 (``JUDGE_SLOT``). It holds
the placeholders in ``PLACEHOLDERS``; ``render_judge_request`` fills each exactly
once. The judge sees the candidate's request, the opaque output, the private
label and the candidate's receipts, never the candidate's identity, variant,
repeat, timing, claimed reward or another judgement. Its reply is the sidecar
that ``scorer.score_cell`` reads.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Sequence
from itertools import zip_longest
from typing import Any

from jsonschema import Draft202012Validator

from scripts.eval.uk_preamble.prompts import extract_json

from .binding import LedgerIndex, arguments_sha256, sha256_text
from .contract import AUDIT_SELECTION_SEED, FACETS, FAMILIES, OUTPUT_SHUFFLE_SEED, SOURCES_CALLS_PER_PASS
from .rubric import RUBRIC, rubric_sha256

PLACEHOLDERS = (
    "{{RUBRIC}}",
    "{{FAMILY}}",
    "{{REQUEST}}",
    "{{OUTPUT_ID}}",
    "{{OUTPUT}}",
    "{{LABEL}}",
    "{{CANDIDATE_RECEIPTS}}",
    "{{REPLY_SCHEMA}}",
)
# Fields a judge may never see: they identify or rank the candidate.
BLIND_FORBIDDEN = frozenset(
    {"seat", "model", "family", "variant", "repeat", "task_id", "timing", "reward", "judgement"}
)


class JudgeError(Exception):
    """A judge request or sidecar breaks the frozen judging contract."""


_NULLABLE_ID = {"type": ["string", "null"]}


def _schema(bound: bool) -> dict[str, Any]:
    """The judge's reply (``bound=False``) or the stored sidecar the harness binds from it.

    A judge names evidence by receipt id, excerpt and locator, and spans by quote and
    occurrence; it computes no digest or offset. ``bind_reply`` adds the output and rubric
    digests, the span offsets and each receipt's tool, argument and result digests from the
    verified ledger, and ``check_binding`` re-verifies every one of them when scoring.
    """
    span = {
        "type": "object",
        "required": ["quote", "occurrence"] + (["start", "end"] if bound else []),
        "additionalProperties": False,
        "properties": {
            "quote": {"type": "string", "minLength": 1},
            "occurrence": {"type": "integer", "minimum": 0},
            **({"start": {"type": "integer", "minimum": 0}, "end": {"type": "integer", "minimum": 0}} if bound else {}),
        },
    }
    binding_properties: dict[str, Any] = {
        "role": {"enum": ["candidate", "judge", "pack", "label", "request"]},
        "receipt_id": {"type": "string", "pattern": "^rr-[0-9a-f]{20}$"},
        "evidence_id": {"type": "string", "minLength": 1},
        "polarity": {"enum": ["positive", "negative"]},
        "evidence_excerpt": {"type": "string", "minLength": 1},
        "source_locator": {"type": "string", "minLength": 1},
        "underlying_dictionary": {"type": "string"},
    }
    if bound:
        binding_properties |= {
            "tool": {"type": "string"},
            "arguments_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "result_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        }
    binding = {
        "type": "object",
        "required": ["role", "evidence_excerpt", "source_locator"],
        "additionalProperties": False,
        "properties": binding_properties,
        "if": {"properties": {"role": {"const": "request"}}},
        "then": {"required": ["evidence_id"]},
        "else": {"required": ["receipt_id"]},
    }
    assertion_fields = {
        "id": {"type": "string", "minLength": 1},
        "span": span,
        "finding_id": _NULLABLE_ID,
        "facet": {"enum": list(FACETS)},
        "kind": {"enum": ["assertion", "edit", "accusation"]},
        "slot_id": _NULLABLE_ID,
        "duplicate_of": _NULLABLE_ID,
        "verdict": {"enum": ["correct", "incorrect", "unchecked"]},
        "unchecked_reason": {"enum": [None, "budget", "tool_unavailable", "coverage"]},
        "false_correction": {"type": "boolean"},
        "protected_opportunity_id": _NULLABLE_ID,
        "harm": {"type": "boolean"},
        "bindings": {"type": "array", "items": binding},
    }
    top: dict[str, Any] = {
        "item_id": {"type": "string"},
        "output_id": {"type": "string"},
        "response_kind": {"enum": ["answered", "refusal"]},
        "outcome_correct": {"type": ["boolean", "null"]},
        "assertions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": list(assertion_fields),
                "additionalProperties": False,
                "properties": assertion_fields,
            },
        },
        "protected": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["opportunity_id", "preserved", "harm"],
                "additionalProperties": False,
                "properties": {
                    "opportunity_id": {"type": "string"},
                    "preserved": {"type": ["boolean", "null"]},
                    "harm": {"type": "boolean"},
                },
            },
        },
        "obligations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "satisfied"],
                "additionalProperties": False,
                "properties": {"id": {"type": "string"}, "satisfied": {"type": ["boolean", "null"]}},
            },
        },
        "sources_calls": {"type": "integer", "minimum": 0},
        "budget_exhausted": {"type": "boolean"},
        "evaluator_limits": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["reason", "owner"],
                "additionalProperties": False,
                "properties": {"reason": {"type": "string"}, "owner": {"type": "string"}},
            },
        },
    }
    if bound:
        top |= {
            "output_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "rubric_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": list(top),
        "additionalProperties": False,
        "properties": top,
    }


REPLY_SCHEMA = _schema(bound=False)
SIDECAR_SCHEMA = _schema(bound=True)


def opaque_output_id(task_id: str) -> str:
    """A stable identifier that reveals nothing about the candidate behind it."""
    return "out-" + hashlib.sha256(f"{OUTPUT_SHUFFLE_SEED}:{task_id}".encode()).hexdigest()[:16]


def shuffled(task_ids: Sequence[str]) -> list[str]:
    """The fixed judging order of the outputs (seed 10453)."""
    order = sorted(task_ids)
    random.Random(OUTPUT_SHUFFLE_SEED).shuffle(order)
    return order


def audit_sample(cells: Sequence[dict[str, Any]], size: int) -> list[str]:
    """The presealed second-judge sample (seed 10454), stratified by model and family.

    ``cells`` are planned cells with ``task_id``, ``model``, ``family`` and ``judging_mode``.
    Every model x family stratum contributes one cell before any stratum contributes a
    second, and pedagogy cells cover both judging modes for each model when ``size``
    allows. Drawn before any output exists; the returned task ids are frozen.
    """
    rng = random.Random(AUDIT_SELECTION_SEED)
    strata: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for cell in sorted(cells, key=lambda c: c["task_id"]):
        strata.setdefault((cell["model"], cell["family"]), []).append(cell)
    for members in strata.values():
        rng.shuffle(members)
        if members and members[0]["family"] == "pedagogy_review":
            # Alternate judging modes so both appear in each model's first two draws.
            authoring = [c for c in members if c["judging_mode"] == "authoring"]
            repair = [c for c in members if c["judging_mode"] == "repair"]
            members[:] = [c for pair in zip_longest(authoring, repair) for c in pair if c is not None]
    keys = sorted(strata)
    chosen: list[str] = []
    depth = 0
    while len(chosen) < size and any(depth < len(strata[key]) for key in keys):
        for key in keys:
            if depth < len(strata[key]) and len(chosen) < size:
                chosen.append(strata[key][depth]["task_id"])
        depth += 1
    return chosen


def _blind(label: dict[str, Any]) -> dict[str, Any]:
    leaked = sorted(BLIND_FORBIDDEN & set(label))
    if leaked:
        raise JudgeError(f"label carries candidate-identifying fields: {', '.join(leaked)}")
    return label


def render_judge_request(
    template: bytes,
    *,
    family: str,
    request: str,
    output_id: str,
    output: str,
    label: dict[str, Any],
    candidate_receipts: list[dict[str, Any]],
) -> str:
    """One judge prompt; ``template`` is already pin-checked by the caller."""
    text = template.decode("utf-8")
    for placeholder in PLACEHOLDERS:
        if text.count(placeholder) != 1:
            raise JudgeError(f"judge template must hold {placeholder} exactly once")
    if family not in FAMILIES:
        raise JudgeError(f"unknown family {family!r}")
    contract = FAMILIES[family]
    values = {
        "{{RUBRIC}}": json.dumps(RUBRIC, ensure_ascii=False, indent=2, sort_keys=True),
        "{{FAMILY}}": json.dumps(
            {
                "family": family,
                "candidate_receipts_required": contract.candidate_receipts_required,
                "cap": contract.cap.__dict__,
                "judge_sources_calls_max": SOURCES_CALLS_PER_PASS,
                "rubric_sha256": rubric_sha256(),
            },
            sort_keys=True,
        ),
        "{{REQUEST}}": request,
        "{{OUTPUT_ID}}": output_id,
        "{{OUTPUT}}": output,
        "{{LABEL}}": json.dumps(_blind(label), ensure_ascii=False, indent=2, sort_keys=True),
        "{{CANDIDATE_RECEIPTS}}": json.dumps(candidate_receipts, ensure_ascii=False, indent=2, sort_keys=True),
        "{{REPLY_SCHEMA}}": json.dumps(REPLY_SCHEMA, indent=2, sort_keys=True),
    }
    # Fill in one pass so a value that contains a placeholder string is never re-expanded.
    pieces = [text]
    for placeholder in PLACEHOLDERS:
        pieces = [part for piece in pieces for part in _split_keep(piece, placeholder)]
    return "".join(values.get(piece, piece) for piece in pieces)


def _split_keep(text: str, token: str) -> list[str]:
    if text in PLACEHOLDERS:
        return [text]
    parts = text.split(token)
    out: list[str] = []
    for index, part in enumerate(parts):
        if index:
            out.append(token)
        out.append(part)
    return out


def _validated(value: Any, schema: dict[str, Any], what: str) -> dict[str, Any]:
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path))
    if errors:
        raise JudgeError(f"{what} breaks its schema: {errors[0].message[:200]}")
    return value


def _offsets(output: str, quote: str, occurrence: int) -> tuple[int, int]:
    """The code-point span of the ``occurrence``-th ``quote`` in ``output``; (0, 0) when absent."""
    at = -1
    for _ in range(occurrence + 1):
        at = output.find(quote, at + 1)
        if at < 0:
            return 0, 0
    return at, at + len(quote)


def bind_reply(reply: str, *, item_id: str, output_id: str, output: str, index: LedgerIndex) -> dict[str, Any]:
    """The stored sidecar: the judge's reply bound to the output bytes, rubric and ledgers."""
    try:
        parsed = extract_json(reply)
    except ValueError as exc:
        raise JudgeError("judge reply holds no JSON object") from exc
    sidecar = _validated(parsed, REPLY_SCHEMA, "judge reply")
    if sidecar["item_id"] != item_id or sidecar["output_id"] != output_id:
        raise JudgeError("judge reply names another item or output")
    for assertion in sidecar["assertions"]:
        span = assertion["span"]
        span["start"], span["end"] = _offsets(output, span["quote"], span["occurrence"])
        for binding in assertion["bindings"]:
            if binding["role"] == "request":
                continue
            record = index.get(binding["role"], binding["receipt_id"])
            if record is not None:  # an absent record stays unbound; scoring types it
                binding["tool"] = record["tool"]
                binding["arguments_sha256"] = arguments_sha256(record.get("arguments"))
                binding["result_sha256"] = sha256_text(str(record.get("result")))
    sidecar["output_sha256"] = sha256_text(output)
    sidecar["rubric_sha256"] = rubric_sha256()
    return _validated(sidecar, SIDECAR_SCHEMA, "bound sidecar")


def parse_sidecar(stored: str) -> dict[str, Any]:
    """A stored, bound sidecar; anything else is refused."""
    try:
        sidecar = json.loads(stored)
    except ValueError as exc:
        raise JudgeError("stored sidecar is not JSON") from exc
    _validated(sidecar, SIDECAR_SCHEMA, "stored sidecar")
    if sidecar["rubric_sha256"] != rubric_sha256():
        raise JudgeError("sidecar names another rubric")
    return sidecar
