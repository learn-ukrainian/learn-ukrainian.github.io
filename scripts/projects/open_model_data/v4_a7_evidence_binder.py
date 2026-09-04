#!/usr/bin/env python3
"""V4 A7 evidence/reconstruction binder: deterministic, expression-free
checks that a candidate independently-authored row (a) carries verified,
resolved-or-bounded linguistic evidence bound to project-authoritative
identifiers, and (b) passes all five reconstruction gates
(``v4_original_row_admission.RECONSTRUCTION_GATES``) against every
candidate-family reference text -- never just the one bound unit.

No live corpus or model call happens here. Real VESUM/``sources`` MCP
identifier resolution is a documented follow-up (it requires the
``mcp__sources__*`` tool surface, unavailable to an offline validator or a
CI run); this binder enforces the *shape* a genuine identifier must have
and the *disposition* evidence must carry (verified, resolved/bounded) --
exactly the fields ``v4_original_row_admission.evaluate_row`` already
requires -- and is exercised in this PR only against synthetic,
caller-supplied identifiers and reference texts, never real corpus text.

The five reconstruction gates reuse (never reimplement) the sealed
near-duplicate policy and its deterministic implementation
(``phase3_near_duplicate.py``) at different comparison granularities:

* ``exact`` / ``fuzzy`` -- the candidate must not classify as an exact or
  near duplicate of any single reference text.
* ``structural`` -- a stricter, lower-threshold band on the same
  similarity features, catching a near-miss the near-duplicate policy's
  own 0.9 minimum would let through (a shorter shared skeleton is still a
  reconstruction risk even if it clears the near-duplicate bar).
* ``cumulative`` -- the candidate is also compared against the
  concatenation of every reference text, catching a row assembled by
  stitching fragments across multiple sources (which no single pairwise
  comparison would catch).
* ``reconstruction`` -- the final aggregate: passes only if all four
  gates above pass *and* the candidate is not a verbatim substring or
  superstring of any single reference text.

This is a deterministic firewall, not a linguistic judgement -- exactly
the posture the near-duplicate policy itself declares.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from scripts.projects.open_model_data import phase3_near_duplicate as near_duplicate

RECONSTRUCTION_GATES = ("exact", "fuzzy", "structural", "cumulative", "reconstruction")

# A stricter band than the near-duplicate policy's own 0.9 near-duplicate
# minimum -- deliberately lower, so "structural" catches shorter shared
# skeletons the near-duplicate check alone would pass.
STRUCTURAL_SIMILARITY_THRESHOLD = 0.6

# Deterministic, offline identifier-shape check only -- real VESUM/`sources`
# resolution is a documented follow-up (see module docstring). Accepts
# "vesum:<id>" and "sources:<id>" forms.
VESUM_IDENTIFIER_RE = re.compile(r"^(vesum|sources):[a-z0-9][a-z0-9_.:-]*$")


class EvidenceBinderError(ValueError):
    """Evidence or a reconstruction gate cannot be recorded safely."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceBinderError(message)


def verify_identifier_shape(identifier: str) -> bool:
    return isinstance(identifier, str) and bool(VESUM_IDENTIFIER_RE.match(identifier))


def build_evidence_receipt(row_content_sha256: str, vesum_ids: list[str], *, uncertainty: str = "resolved") -> dict[str, Any]:
    """A text-free evidence receipt satisfying
    ``v4_original_row_admission.evaluate_row``'s own requirements (grade
    "verified", uncertainty resolved/bounded, disposition
    supported/admitted, a nonempty receipt_id). Refuses any identifier that
    does not match the pinned VESUM/``sources`` shape, and refuses an empty
    identifier list -- evidence with no bound identifier is not evidence."""
    require(isinstance(vesum_ids, list) and vesum_ids, "vesum_ids must be a nonempty list")
    require(len(vesum_ids) == len(set(vesum_ids)), "vesum_ids must not contain duplicates")
    for identifier in vesum_ids:
        require(verify_identifier_shape(identifier), f"identifier does not match the pinned VESUM/sources shape: {identifier!r}")
    require(uncertainty in {"resolved", "bounded"}, "uncertainty must be resolved or bounded")

    payload = f"v4-a7-evidence-v1\x00{row_content_sha256}\x00{','.join(sorted(vesum_ids))}\x00{uncertainty}"
    receipt_id = f"evidence:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
    return {
        "receipt_id": receipt_id,
        "grade": "verified",
        "uncertainty": uncertainty,
        "disposition": "supported",
        "vesum_ids": sorted(vesum_ids),
        "row_content_sha256": row_content_sha256,
    }


def _gate_receipt_id(gate: str, candidate_fingerprint: str, policy_fingerprint: str) -> str:
    payload = f"v4-a7-reconstruction-gate-v1\x00{gate}\x00{candidate_fingerprint}\x00{policy_fingerprint}"
    return f"reconstruction-gate:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def _structural_pass(candidate: str, reference_texts: list[str], policy: dict[str, Any]) -> bool:
    for reference in reference_texts:
        result = near_duplicate.classify_texts(candidate, reference, scope="span", policy=policy)
        if result.token_jaccard >= STRUCTURAL_SIMILARITY_THRESHOLD or result.normalized_edit_similarity >= STRUCTURAL_SIMILARITY_THRESHOLD:
            return False
    return True


def run_reconstruction_gates(
    candidate_text: str,
    reference_texts: dict[str, str],
    *,
    policy: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Run all five reconstruction gates against *every* reference text --
    never just the one candidate-ledger-bound unit. Fails closed on an
    empty reference set (see ``check_split_duplicate_safety`` for the
    identical rationale)."""
    require(isinstance(candidate_text, str) and candidate_text, "candidate_text must be a nonempty string")
    require(isinstance(reference_texts, dict) and reference_texts, "reference_texts must be a nonempty mapping")
    active_policy = policy if policy is not None else near_duplicate.load_policy()
    require(
        active_policy.get("policy_fingerprint_sha256") == near_duplicate.policy_fingerprint(active_policy),
        "near-duplicate policy fingerprint drift -- refusing",
    )
    policy_fingerprint = active_policy["policy_fingerprint_sha256"]
    references = list(reference_texts.values())

    exact_pass = all(
        near_duplicate.classify_texts(candidate_text, reference, scope="span", policy=active_policy).classification != "exact"
        for reference in references
    )
    fuzzy_pass = all(
        not near_duplicate.classify_texts(candidate_text, reference, scope="span", policy=active_policy).duplicate
        for reference in references
    )
    structural_pass = _structural_pass(candidate_text, references, active_policy)
    cumulative_reference = "\n".join(references)
    cumulative_pass = not near_duplicate.classify_texts(candidate_text, cumulative_reference, scope="span", policy=active_policy).duplicate
    normalized_candidate = near_duplicate.normalize(candidate_text)
    no_verbatim_containment = all(
        normalized_candidate not in near_duplicate.normalize(reference) and near_duplicate.normalize(reference) not in normalized_candidate
        for reference in references
    )
    reconstruction_pass = exact_pass and fuzzy_pass and structural_pass and cumulative_pass and no_verbatim_containment

    candidate_fingerprint = near_duplicate.fingerprint(candidate_text).exact_fingerprint
    results = {
        "exact": exact_pass,
        "fuzzy": fuzzy_pass,
        "structural": structural_pass,
        "cumulative": cumulative_pass,
        "reconstruction": reconstruction_pass,
    }
    return {
        gate: {"passed": passed, "receipt_id": _gate_receipt_id(gate, candidate_fingerprint, policy_fingerprint)}
        for gate, passed in results.items()
    }
