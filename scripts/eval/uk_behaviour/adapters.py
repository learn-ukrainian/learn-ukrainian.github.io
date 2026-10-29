"""Production adapters: one sealed request item to the exact bytes a candidate receives.

- Fresh lesson and fresh activities: the production lesson-writer renderer over the
  four prescribed inputs (plan entry, cited records, learner state with its immersion
  rule, the level's style card). No fifth input and no output field is added; the
  writer has no Sources tools. Writer requests are authoring by contract.
- V7 module: the pinned ``curriculum-writer.md`` contract followed by the sealed,
  production-rendered V7 writer prompt (plan, inventory, size policy).
- Passage review: the pinned ``content-review-prompt.md`` with a fixed inline-input
  frame whose envelope captures the corrected text and the findings.
- Card, exercise and pedagogy review: the advisor-accepted private prompt, verified
  against its pinned SHA-256, followed by the request JSON.

Only allowlisted, candidate-visible fields of an item reach a candidate; an item
carrying anything else is refused, so label fields cannot leak through an adapter.
The judging mode travels in the request JSON for review families and in the task
metadata for writer families, whose production prompts are the authoring contract.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from jsonschema import Draft202012Validator

from scripts.eval.uk_preamble.common import sha256_bytes, tokenize
from scripts.eval.uk_preamble.prompts import extract_json

from .contract import (
    ANCHOR_KINDS,
    CARD_FACETS,
    EXERCISE_DEFECTS,
    FAMILIES,
    PEDAGOGY_DEFECTS,
    PEDAGOGY_NORMS,
    REPO_ROOT,
    SOURCES_CALLS_PER_PASS,
)


class AdapterError(Exception):
    """A request item or prompt cannot be rendered under the frozen contract."""


# Candidate-visible top-level fields per family. Everything else is refused.
VISIBLE_FIELDS: dict[str, frozenset[str]] = {
    "fresh_lesson": frozenset({"item_id", "judging_mode", "level", "slug", "lesson_n", "inputs"}),
    "fresh_activities": frozenset({"item_id", "judging_mode", "level", "slug", "lesson_n", "inputs"}),
    "v7_module": frozenset({"item_id", "judging_mode", "level", "writer_prompt"}),
    "exercise_review": frozenset({"item_id", "judging_mode", "level", "exercise", "target", "learner_state"}),
    "card_review": frozenset({"item_id", "judging_mode", "level", "card", "context"}),
    "passage_review": frozenset({"item_id", "judging_mode", "level", "passage"}),
    "pedagogy_review": frozenset(
        {
            "item_id",
            "judging_mode",
            "level",
            "shape",
            "snippet",
            "target",
            "learner_state",
            "prerequisites",
            "resources",
            "norm_evidence",
        }
    ),
}
FRESH_INPUTS = frozenset({"plan_entry", "cited_records", "learner_state", "immersion"})

REQUEST_FRAME = "\n\n## Request\n\nThe request is this JSON object:\n\n```json\n{payload}\n```\n"

# Inline-input frame for content-review-prompt.md. The production prompt reads module files;
# here the text under review is supplied inline and the reply is a fixed JSON envelope.
PASSAGE_FRAME = """

## Evaluation input and reply

This review covers one passage, supplied inline in the request below instead of as module
files. Apply the Linguistic Accuracy checks and the binding review rules above to it at the
request's level and `judging_mode`; the plan, activity and engagement checks do not apply.
Repair only Ukrainian errors that the Sources tools prove, and keep every other character of
the passage exactly as it is. Preserve dialect, heritage and rare but valid forms in context.

Each Sources result ends with a line `receipt: rr-…`; cite those ids exactly, only from your
own calls in this session. You may make at most 32 Sources calls. Instead of the Markdown
report, return one JSON object and nothing else:

```json
{
  "item_id": "<the request's item_id>",
  "judging_mode": "<the request's judging_mode>",
  "outcome": "findings | clean | evidence_gap",
  "corrected_text": "<the whole passage after your supported repairs>",
  "findings": [
    {
      "id": "F1",
      "facet": "form | stress | meaning | historical | naturalness | spelling_style",
      "location": {"field": "/passage", "quote": "<exact original text>"},
      "claim": "<one checkable assertion in English, naming the source>",
      "proposed_edit": {"field": "/passage", "replacement": "<replacement text>"},
      "receipts": ["rr-…"]
    }
  ],
  "gaps": [
    {"facet": "<facet>", "location": {"field": "/passage", "quote": "<exact text>"},
     "reason": "<what the sources could not decide>", "receipts": ["rr-…"]}
  ]
}
```

A correct passage is returned unchanged with `"outcome": "clean"` and no findings."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _check_item(family: str, item: dict[str, Any]) -> None:
    if family not in FAMILIES:
        raise AdapterError(f"unknown family {family!r}")
    if not isinstance(item, dict):
        raise AdapterError("a request item is a JSON object")
    extra = sorted(set(item) - VISIBLE_FIELDS[family])
    if extra:
        raise AdapterError(f"{family} item carries fields a candidate may not see: {', '.join(extra)}")
    for key in ("item_id", "judging_mode", "level"):
        if not isinstance(item.get(key), str) or not item[key]:
            raise AdapterError(f"{family} item needs {key}")
    if item["judging_mode"] not in FAMILIES[family].modes:
        raise AdapterError(f"{family} items use {list(FAMILIES[family].modes)} mode, not {item['judging_mode']!r}")


def pinned_bytes(data: bytes, expected_sha256: str | None, what: str) -> bytes:
    """``data`` when it hashes to its pin; an unpinned or drifted prompt is refused."""
    if not expected_sha256:
        raise AdapterError(f"{what} has no pinned SHA-256; it cannot be used before G3 acceptance")
    if sha256_bytes(data) != expected_sha256:
        raise AdapterError(f"{what} differs from its pinned SHA-256")
    return data


def render_review(family: str, item: dict[str, Any], prompt: bytes) -> str:
    """Request bytes for exercise, card, pedagogy or passage review. ``prompt`` is already pin-checked."""
    _check_item(family, item)
    if FAMILIES[family].output not in ("review-envelope", "passage-envelope"):
        raise AdapterError(f"{family} is not a review family")
    text = prompt.decode("utf-8").rstrip("\n")
    if family == "passage_review":
        if not isinstance(item.get("passage"), str) or not item["passage"]:
            raise AdapterError("passage_review item needs the passage text")
        text += PASSAGE_FRAME
    return text + REQUEST_FRAME.format(payload=_canonical(item))


def render_v7(item: dict[str, Any], contract: bytes) -> str:
    _check_item("v7_module", item)
    if not isinstance(item.get("writer_prompt"), str) or not item["writer_prompt"].strip():
        raise AdapterError("v7_module item needs the production-rendered writer prompt")
    return contract.decode("utf-8").rstrip("\n") + "\n\n" + item["writer_prompt"]


Renderer = Callable[..., str]


def render_fresh(family: str, item: dict[str, Any], renderer: Renderer | None = None) -> str:
    """The production lesson prompt over exactly the four prescribed inputs."""
    _check_item(family, item)
    if family not in ("fresh_lesson", "fresh_activities"):
        raise AdapterError(f"{family} is not a fresh-writer family")
    inputs = item.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != FRESH_INPUTS:
        raise AdapterError("a fresh-writer item supplies exactly plan_entry, cited_records, learner_state, immersion")
    if not isinstance(item.get("slug"), str) or not isinstance(item.get("lesson_n"), int):
        raise AdapterError("a fresh-writer item needs slug and lesson_n")
    if renderer is None:
        from scripts.build.fresh.prompt import render_lesson_prompt as renderer
    # The style card is the fourth input: the level's fixed card, resolved by the renderer.
    return renderer(
        inputs["plan_entry"],
        inputs["cited_records"],
        inputs["learner_state"],
        inputs["immersion"],
        level=item["level"],
        slug=item["slug"],
        lesson_n=item["lesson_n"],
    )


def production_asset(family: str) -> bytes:
    """The pinned production prompt asset of a family that has one in the repository."""
    path = FAMILIES[family].prompt
    if path.startswith("private://"):
        raise AdapterError(f"{family} uses a private prompt slot")
    return (REPO_ROOT / path).read_bytes()


def tool_policy(family: str) -> dict[str, Any]:
    """The candidate's tool boundary: fresh writers get none; others the review Sources set, 32 calls."""
    tools = FAMILIES[family].sources_tools
    return {"sources": tools, "max_sources_calls": SOURCES_CALLS_PER_PASS if tools else 0}


# --------------------------------------------------------------------------- output acceptance

_LOCATION = {
    "type": "object",
    "required": ["field", "quote"],
    "additionalProperties": False,
    "properties": {"field": {"type": "string"}, "quote": {"type": "string"}},
}
_RECEIPTS = {"type": "array", "items": {"type": "string", "pattern": "^rr-[0-9a-f]{20}$"}}
_EDIT = {
    "oneOf": [
        {"type": "null"},
        {
            "type": "object",
            "required": ["field", "replacement"],
            "additionalProperties": False,
            "properties": {"field": {"type": "string"}, "replacement": {"type": "string"}},
        },
    ]
}
_ANCHOR = {
    "type": "object",
    "required": ["kind", "evidence", "receipt", "quote"],
    "additionalProperties": False,
    "properties": {
        "kind": {"enum": list(ANCHOR_KINDS)},
        "evidence": {"type": ["string", "null"]},
        "receipt": {"oneOf": [{"type": "null"}, {"type": "string", "pattern": "^rr-[0-9a-f]{20}$"}]},
        "quote": {"type": "string", "minLength": 1},
    },
}
_PASSAGE_FACETS = ("form", "stress", "meaning", "historical", "naturalness", "spelling_style")


def _finding_schema(family: str) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "id": {"type": "string", "minLength": 1},
        "location": _LOCATION,
        "claim": {"type": "string", "minLength": 1},
        "proposed_edit": _EDIT,
        "receipts": _RECEIPTS,
    }
    required = ["id", "location", "claim", "proposed_edit", "receipts"]
    if family == "exercise_review":
        properties["defect"] = {"enum": list(EXERCISE_DEFECTS)}
        properties["key_positions"] = {"type": "array", "items": {"type": "integer", "minimum": 0}}
        required.append("defect")
    elif family == "pedagogy_review":
        properties["defect"] = {"enum": list(PEDAGOGY_DEFECTS)}
        properties["norm"] = {"enum": list(PEDAGOGY_NORMS)}
        properties["anchors"] = {"type": "array", "minItems": 1, "items": _ANCHOR}
        properties["proposed_edit"] = {"type": "null"}
        required += ["defect", "norm", "anchors"]
    else:
        facets = CARD_FACETS if family == "card_review" else _PASSAGE_FACETS
        properties["facet"] = {"enum": list(facets)}
        required.append("facet")
    return {"type": "object", "required": required, "additionalProperties": False, "properties": properties}


def _gap_schema(family: str) -> dict[str, Any]:
    key = "defect" if family in ("exercise_review", "pedagogy_review") else "facet"
    return {
        "type": "object",
        "required": [key, "location", "reason", "receipts"],
        "additionalProperties": False,
        "properties": {
            key: {"type": "string", "minLength": 1},
            "location": _LOCATION,
            "reason": {"type": "string", "minLength": 1},
            "receipts": _RECEIPTS,
        },
    }


def envelope_schema(family: str) -> dict[str, Any]:
    properties: dict[str, Any] = {
        "item_id": {"type": "string"},
        "judging_mode": {"enum": ["repair", "authoring"]},
        "outcome": {"enum": ["findings", "clean", "evidence_gap"]},
        "findings": {"type": "array", "items": _finding_schema(family)},
        "gaps": {"type": "array", "items": _gap_schema(family)},
    }
    required = ["item_id", "judging_mode", "outcome", "findings", "gaps"]
    if family == "passage_review":
        properties["corrected_text"] = {"type": "string"}
        required.append("corrected_text")
    return {"type": "object", "required": required, "additionalProperties": False, "properties": properties}


@dataclass
class Acceptance:
    """Deterministic acceptance of one output; ``response`` is a ``reward.RESPONSES`` kind."""

    response: str
    reasons: list[str] = field(default_factory=list)
    parsed: Any = None
    cited_receipts: list[str] = field(default_factory=list)


def _envelope_problems(family: str, parsed: Any, item: dict[str, Any]) -> list[str]:
    errors = sorted(Draft202012Validator(envelope_schema(family)).iter_errors(parsed), key=lambda e: list(e.path))
    problems = [f"envelope: {error.message[:160]}" for error in errors[:5]]
    if problems:
        return problems
    if parsed["item_id"] != item["item_id"] or parsed["judging_mode"] != item["judging_mode"]:
        problems.append("envelope does not echo the request's item_id and judging_mode")
    if parsed["outcome"] == "findings" and not parsed["findings"]:
        problems.append("outcome findings without a finding")
    if parsed["outcome"] != "findings" and parsed["findings"]:
        problems.append(f"outcome {parsed['outcome']} with findings")
    if parsed["outcome"] == "evidence_gap" and not parsed["gaps"]:
        problems.append("outcome evidence_gap without a gap")
    ids = [finding["id"] for finding in parsed["findings"]]
    if len(ids) != len(set(ids)):
        problems.append("finding ids repeat")
    return problems


def accept(
    family: str,
    text: str | None,
    item: dict[str, Any],
    *,
    validate_draft: Callable[[str, str], Any] | None = None,
) -> Acceptance:
    """Whether an output is an accepted response of its production contract."""
    if text is None or not text.strip():
        return Acceptance("missing", ["no output"])
    output = FAMILIES[family].output
    if output in ("review-envelope", "passage-envelope"):
        try:
            parsed = extract_json(text)
        except ValueError:
            return Acceptance("malformed", ["no JSON object"])
        problems = _envelope_problems(family, parsed, item)
        if problems:
            return Acceptance("malformed", problems)
        cited = [rid for part in ("findings", "gaps") for entry in parsed[part] for rid in entry["receipts"]]
        cited += [a["receipt"] for f in parsed["findings"] for a in f.get("anchors", []) if a["receipt"]]
        return Acceptance("accepted", parsed=parsed, cited_receipts=cited)
    if output == "lesson-draft":
        if validate_draft is None:
            from scripts.build.fresh.writer import parse_and_validate_reply

            def validate_draft(reply: str, level: str) -> Any:
                return parse_and_validate_reply(reply, level)

        try:
            return Acceptance("accepted", parsed=validate_draft(text, item["level"]))
        except Exception as exc:  # the production validator raises its own error types
            return Acceptance("malformed", [f"lesson-draft-v1: {type(exc).__name__}"])
    # V7: the module's own audit gates are production checks; completion obligations are judged.
    return Acceptance("accepted", parsed=text)


def _pointer_token(key: Any) -> str:
    return str(key).replace("~", "~0").replace("/", "~1")


def request_evidence(item: dict[str, Any]) -> dict[str, str]:
    """Checkable request text by JSON pointer (scalars as text, subtrees as canonical JSON), and each
    ``norm_evidence`` entry by id.

    A finding's ``location`` and a pedagogy anchor's ``evidence`` resolve here; their quote must
    occur in the text found. ``norm_evidence`` is a list of ``{"id", "kind", "locator", "text"}``.
    """
    found: dict[str, str] = {}

    def walk(value: Any, pointer: str) -> None:
        if isinstance(value, dict | list) and pointer:  # a block-level finding quotes inside its subtree
            found[pointer] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, f"{pointer}/{_pointer_token(key)}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{pointer}/{index}")
        elif value is not None:
            found[pointer] = value if isinstance(value, str) else json.dumps(value)

    walk(item, "")
    for entry in item.get("norm_evidence") or []:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and isinstance(entry.get("text"), str):
            found[entry["id"]] = entry["text"]
    return found


def block_key_positions(item: dict[str, Any], pointer: str) -> list[int] | None:
    """Zero-based key positions of the ordered block at ``pointer`` (items with ``options`` and ``key``)."""
    node: Any = item
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(node, list) and token.isdigit() and int(token) < len(node):
            node = node[int(token)]
        elif isinstance(node, dict) and token in node:
            node = node[token]
        else:
            return None
    entries = node.get("items") if isinstance(node, dict) else node
    if not isinstance(entries, list):
        return None
    positions = []
    for entry in entries:
        options = entry.get("options") if isinstance(entry, dict) else None
        if not isinstance(options, list) or entry.get("key") not in options:
            return None
        positions.append(options.index(entry["key"]))
    return positions


def size_problems(family: str, text: str, *, individual: int, batched: int, edits: int) -> list[str]:
    """Where an output exceeds its family's presealed size or claim caps.

    Claims are counted with every repetition, split by ``coverage.cost_class``.
    """
    cap = FAMILIES[family].cap
    problems = []
    if len(text.encode("utf-8")) > cap.max_bytes:
        problems.append(f"output exceeds {cap.max_bytes} bytes")
    if len(tokenize(text)) > cap.max_tokens:
        problems.append(f"output exceeds {cap.max_tokens} scoring tokens")
    if individual > cap.max_claims:
        problems.append(f"output makes more than {cap.max_claims} individually checked claims")
    if batched > cap.batched:
        problems.append(f"output makes more than {cap.batched} batch-checked claims")
    if edits > cap.max_edits:
        problems.append(f"output makes more than {cap.max_edits} edits")
    return problems
