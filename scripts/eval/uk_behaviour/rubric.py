"""The frozen judging rubric of ``uk-behaviour-score/2``, as data.

The judge template renders this object verbatim and the judge's sidecar names
its digest. Each definition restates a rule of
``docs/evaluations/uk-behaviour-freeze.md``; the scorer applies the arithmetic.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .binding import AUTHORITIES
from .contract import FACETS, SCORER

RUBRIC: dict[str, Any] = {
    "scorer": SCORER,
    "unit": (
        "One assertion is one checkable factual or linguistic claim, one proposed or applied edit, or one "
        "accusation that a form, key or teaching choice is wrong. Enumerate every assertion in the output, "
        "including extra and off-facet ones, with its span as an exact quote of the output and that quote's "
        "zero-based occurrence."
    ),
    "facets": list(FACETS),
    "positive_authorities": {facet: sorted(tools) for facet, tools in AUTHORITIES.items()},
    "authority_rules": [
        "search_definitions is СУМ-11: never positive evidence; a positive use is still bound so it counts in S.",
        "For every slovnyk.me result, record underlying_dictionary exactly as the result names it.",
        "A Russian-shadow hit is a suspicion; VESUM attestation and heritage evidence override it.",
        "Before judging a form accusation correct after a VESUM miss, check compound components, ULIF, "
        "the underlying dictionary and corpus evidence; if VESUM is unavailable, the accusation is unchecked.",
        "verify_quote is fuzzy: compare the exact retained span; a positive boolean proves nothing.",
        "verify_stress receipts keep no reading provenance: bind stress to a query_ulif_records or query_sum20 record.",
        "Excerpt, source locator and any underlying dictionary come from one evidence unit: one record "
        "of a JSON result (name it with evidence_pointer) or one entry of a Markdown result.",
        "GRAC is never a stress authority; frequency never establishes correctness or CEFR suitability.",
        "A missing MCP hit for СУМ-20 or ВТС is a coverage gap, never a negative label.",
    ],
    "slots": (
        "slot_id names the label's positive-credit slot the assertion addresses, or null. An assertion beyond "
        "the frozen slots, even a true one within a facet, has slot_id null."
    ),
    "duplicates": "A semantic repetition of an earlier assertion sets duplicate_of to that assertion's id.",
    "verdict": {
        "correct": "Sources-backed evidence bound in bindings entails this exact claim in its context.",
        "incorrect": "Completed Sources-backed judgement contradicts the claim or fails to support it.",
        "unchecked": "An in-contract claim the judge could not check: budget, tool unavailable or coverage.",
    },
    "bindings": (
        "Each binding names one receipt by role (candidate, judge, pack or label) and receipt id, with an "
        "exact excerpt of that receipt's full result and a source locator from the same evidence unit; or "
        "role request with a sealed request evidence id and its own locator or pointer. polarity negative is evidence of absence. The harness adds the tool, argument "
        "and result digests from the verified ledger. In families where candidate_receipts_required is true, "
        "a correct verdict needs a candidate binding to a receipt the finding itself cites."
    ),
    "false_correction": (
        "true for an incorrect edit or accusation against correct text, including an instruction to "
        "normalise a correct form. A wrong repair of a planted error is a miss, not a false correction."
    ),
    "harm": (
        "true when the assertion edits, deletes, stigmatises or recommends replacing a protected form valid "
        "in its context, labelled or independently verified; set protected_opportunity_id when labelled."
    ),
    "protected": (
        "One entry per labelled protected opportunity: preserved true or false, or null when unchecked; harm "
        "true for a harmful protected correction."
    ),
    "obligations": "One entry per label obligation: satisfied true or false, or null when unchecked.",
    "outcome_correct": (
        "For an output with no assertions: true when its clean, evidence-gap or abstention outcome is the "
        "label's expected outcome and is source-verified; false otherwise; null when it has assertions."
    ),
    "response_kind": "refusal when the output declines the task; answered otherwise.",
    "budget": (
        "At most 32 Sources calls. Report sources_calls; set budget_exhausted when an in-contract claim "
        "stayed unchecked for budget. Never drop a claim to fit."
    ),
    "evaluator_limits": "Each limitation that left anything unchecked, with the owner who can lift it.",
}


def rubric_bytes() -> bytes:
    return json.dumps(RUBRIC, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")


def rubric_sha256() -> str:
    return hashlib.sha256(rubric_bytes()).hexdigest()
