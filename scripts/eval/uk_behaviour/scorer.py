"""Semantic sidecar scorer: one cell's components, status and reward.

Inputs are the family, the private G1 label, the request item, the candidate's
output text, the judge's sidecar (``judge.parse_sidecar``) and the verified
ledgers (``binding.LedgerIndex``). The judge decides each assertion's slot,
verdict, false-correction and harm; this module checks that every judgement is
bound to the exact output bytes and to real evidence, then applies the frozen
arithmetic. A passage cell also runs the inherited ``uk-preamble-scoring/2``
counts on its corrected text: a seed earns credit only when that scorer counts
it a hit, and its false alarms enter ``F``.

The label interface (private, sealed under G1)::

    {"item_id", "family", "judging_mode", "answerable": bool,
     "expected_outcome": "findings" | "clean" | "evidence_gap" | "abstention",
     "O": int, "required_slots": [{"slot_id", "facet"}],
     "positive_slots": [{"slot_id", "facet"}],  # every positive-credit slot, required ones included
     "protected": [{"opportunity_id", "stratum"}], "obligations": [str],
     "passage": {...}}  # passage review only: the uk-preamble review item (seeds are its errors)
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any
from unicodedata import normalize

from scripts.eval.uk_preamble.common import sha256_text
from scripts.eval.uk_preamble.dataset import ReviewItem, _review_item
from scripts.eval.uk_preamble.scoring import review_counts

from . import adapters
from .binding import SUM11_POSITIVE, VERIFIED, LedgerIndex, check_binding
from .contract import (
    EXERCISE_REQUEST_DEFECTS,
    FAMILIES,
    INVALID_FABRICATED_RECEIPT,
    INVALID_OVERPRODUCTION,
    PEDAGOGY_ANCHORS,
    SOURCES_CALLS_PER_PASS,
    STRATA,
    UNRESOLVED_EVALUATOR,
    answer_position_pattern,
)
from .coverage import cost_class
from .reward import Components, quality, resolve_status, reward

GAP_OUTCOMES = ("clean", "evidence_gap", "abstention")


class ScoringError(Exception):
    """The inputs do not describe one judged cell; nothing is scored."""


@dataclass
class _Tally:
    flags: set[str] = field(default_factory=set)
    limits: list[dict[str, str]] = field(default_factory=list)

    def unresolved(self, reason: str, owner: str = "primary-judge") -> None:
        self.flags.add(UNRESOLVED_EVALUATOR)
        self.limits.append({"reason": reason, "owner": owner})


def _passage_item(label: dict[str, Any]) -> ReviewItem:
    raw = label.get("passage")
    if not isinstance(raw, dict):
        raise ScoringError("a passage label carries its uk-preamble review item")
    try:
        return _review_item(raw, 0)
    except Exception as exc:
        raise ScoringError(f"passage label is not a valid review item: {exc}") from exc


def _check_label(family: str, label: dict[str, Any]) -> None:
    if label.get("family") != family:
        raise ScoringError("label belongs to another family")
    if not isinstance(label.get("O"), int) or label["O"] < 1:
        raise ScoringError("label needs a positive presealed O")
    if label.get("expected_outcome") not in ("findings", *GAP_OUTCOMES):
        raise ScoringError("label expected_outcome is unknown")
    required = {slot["slot_id"] for slot in label.get("required_slots", [])}
    positive = {slot["slot_id"] for slot in label.get("positive_slots", [])}
    if not required <= positive:
        raise ScoringError("every required slot is a positive-credit slot")
    strata = [entry.get("stratum") for entry in label.get("protected", [])]
    if any(stratum not in STRATA for stratum in strata):
        raise ScoringError("protected opportunities use the three strata")


def _quoted(quote: str, text: str | None) -> bool:
    return text is not None and bool(quote) and normalize("NFC", quote) in normalize("NFC", text)


def _candidate_evidence(
    family: str,
    finding: dict[str, Any],
    verified: list[dict[str, Any]],
    item: dict[str, Any],
    evidence: dict[str, str],
    index: LedgerIndex,
) -> bool:
    """Whether the finding carries its own checkable evidence (protocol lines 362-378).

    Card and passage findings need a verified receipt they cite. Exercise and pedagogy
    findings must also quote the request exactly at their location. A request-only exercise
    defect rests on that quote (an answer-position finding also on key positions recomputed
    from the block); a pedagogy finding needs every anchor its defect requires.
    """
    own = any(b["role"] == "candidate" and b.get("receipt_id") in finding["receipts"] for b in verified)
    if family in ("card_review", "passage_review"):
        return own
    location = finding["location"]
    if not _quoted(location["quote"], evidence.get(location["field"])):
        return False
    if family == "exercise_review":
        if finding["defect"] == "answer_position_pattern":
            derived = adapters.block_key_positions(item, location["field"])
            return derived is not None and finding.get("key_positions") == derived and answer_position_pattern(derived)
        return finding["defect"] in EXERCISE_REQUEST_DEFECTS or own
    satisfied = set()
    for anchor in finding["anchors"]:
        if anchor["receipt"] is not None:
            record = index.get("candidate", anchor["receipt"])
            ok = (
                anchor["kind"] == "textbook_page"
                and anchor["receipt"] in finding["receipts"]
                and record is not None
                and _quoted(anchor["quote"], record.get("result"))
            )
        else:
            ok = anchor["evidence"] is not None and _quoted(anchor["quote"], evidence.get(anchor["evidence"]))
        if ok:
            satisfied.add(anchor["kind"])
    return all(any(kind in satisfied for kind in part) for part in PEDAGOGY_ANCHORS[finding["defect"]])


def score_cell(
    family: str,
    *,
    label: dict[str, Any],
    item: dict[str, Any],
    output: str | None,
    sidecar: dict[str, Any] | None,
    index: LedgerIndex,
    validate_draft: Any = None,
) -> dict[str, Any]:
    """Score one item-repeat. Every status but ``COMPLETE`` leaves the reward provisional."""
    if family not in FAMILIES:
        raise ScoringError(f"unknown family {family!r}")
    _check_label(family, label)
    contract = FAMILIES[family]
    tally = _Tally()
    acceptance = adapters.accept(family, output, item, validate_draft=validate_draft)
    response = acceptance.response
    text = output or ""

    if not contract.sources_tools and index.counts["candidate"]:
        tally.unresolved("a fresh writer reached Sources tools; the tool boundary was broken", "baseline-runner")
    fabricated = [rid for rid in acceptance.cited_receipts if index.get("candidate", rid) is None]
    if fabricated:
        tally.flags.add(INVALID_FABRICATED_RECEIPT)

    assertions: list[dict[str, Any]] = []
    if sidecar is not None:
        if sidecar["item_id"] != label["item_id"]:
            raise ScoringError("sidecar judges another item")
        if output is not None and sidecar["output_sha256"] != sha256_text(text):
            raise ScoringError("sidecar does not bind these output bytes")
        assertions = sidecar["assertions"]
        if sidecar["response_kind"] == "refusal" and response in ("accepted", "malformed"):
            response = "refusal"
        if sidecar["sources_calls"] > SOURCES_CALLS_PER_PASS:
            tally.unresolved("judge exceeded its 32 Sources calls")
        for limit in sidecar["evaluator_limits"]:
            tally.unresolved(limit["reason"], limit["owner"])
    elif response == "accepted":
        tally.unresolved("accepted output has no judgement")

    findings: dict[str, dict[str, Any]] = {}
    if isinstance(acceptance.parsed, dict):
        findings = {entry["id"]: entry for entry in acceptance.parsed.get("findings", [])}
    evidence = adapters.request_evidence(item)
    index.request_evidence = {**evidence, **index.request_evidence}
    positive = {slot["slot_id"] for slot in label.get("positive_slots", [])}
    required = {slot["slot_id"] for slot in label.get("required_slots", [])}
    protected_ids = {entry["opportunity_id"] for entry in label.get("protected", [])}

    ids = [a["id"] for a in assertions]
    if len(ids) != len(set(ids)):
        raise ScoringError("sidecar assertion ids repeat")
    size = Counter()
    supported_slots: set[str] = set()
    refuted_slots: set[str] = set()
    emitted_slots: set[str] = set()
    extras = unsupported_extras = 0
    false_corrections = accusation_false_corrections = 0
    s_count = missing_receipts = bound = 0
    harmed: set[str] = set()
    extra_harms = 0
    facets: dict[str, Counter] = {}
    seen: set[str] = set()
    for a in assertions:
        size[cost_class(family, a["facet"])] += 1
        if a["kind"] == "edit":
            size["edits"] += 1
        span = a["span"]
        if not (span["start"] < span["end"] <= len(text)) or text[span["start"] : span["end"]] != span["quote"]:
            tally.unresolved(f"assertion {a['id']} span does not quote the output")
            continue
        if a["duplicate_of"] is not None:
            if a["duplicate_of"] not in seen:
                tally.unresolved(f"assertion {a['id']} duplicates an unknown assertion")
            continue
        seen.add(a["id"])
        facet_count = facets.setdefault(a["facet"], Counter())
        facet_count["emitted"] += 1
        slot = a["slot_id"]
        if slot is not None and slot not in positive:
            tally.unresolved(f"assertion {a['id']} names a slot outside the label")
            continue
        if a["protected_opportunity_id"] is not None and a["protected_opportunity_id"] not in protected_ids:
            tally.unresolved(f"assertion {a['id']} names an unlabelled protected opportunity")
            continue
        if a["false_correction"] and (a["kind"] == "assertion" or a["verdict"] != "incorrect"):
            tally.unresolved(f"assertion {a['id']}: a false correction is an incorrect edit or accusation")
            continue

        # A harmful correction of a labelled protected opportunity is verified by its sealed label;
        # no evidence error below can erase it.
        if a["harm"] and a["protected_opportunity_id"] is not None:
            harmed.add(a["protected_opportunity_id"])

        checks = [check_binding(b, a["facet"], index) for b in a["bindings"]]
        if any(check.status == SUM11_POSITIVE for check in checks):
            s_count += 1
        # Candidate fabrication is decided from the receipts the output itself cites (above);
        # a judge binding to a receipt no ledger holds is an evaluator error.
        broken = [c.reason for c in checks if c.status not in (VERIFIED, SUM11_POSITIVE)]
        if broken and a["verdict"] != "unchecked":
            tally.unresolved(f"assertion {a['id']} evidence does not verify: {broken[0]}")
            continue
        verified = [b for b, c in zip(a["bindings"], checks, strict=True) if c.status == VERIFIED]
        if (a["false_correction"] or a["harm"]) and not verified:
            tally.unresolved(f"assertion {a['id']}: a false correction or harm needs bound evidence")
            continue
        if contract.candidate_receipts_required:
            finding = findings.get(a["finding_id"])
            has_receipt = finding is not None and _candidate_evidence(family, finding, verified, item, evidence, index)
        else:
            has_receipt = bool(verified)
        if a["verdict"] == "unchecked":
            tally.unresolved(f"assertion {a['id']} unchecked: {a['unchecked_reason'] or 'unstated'}")
        supported = a["verdict"] == "correct" and has_receipt
        if a["verdict"] == "correct" and not has_receipt:
            missing_receipts += 1
        if verified:
            bound += 1
        if supported:
            facet_count["supported"] += 1
        if a["harm"] and a["protected_opportunity_id"] is None:
            extra_harms += 1
        if a["false_correction"]:
            false_corrections += 1
            if a["kind"] == "accusation":
                accusation_false_corrections += 1
        if slot is not None:
            emitted_slots.add(slot)
            if supported:
                supported_slots.add(slot)
            elif a["verdict"] == "incorrect":
                refuted_slots.add(slot)
        else:
            if not a["false_correction"]:
                extras += 1
            if not supported:
                unsupported_extras += 1

    passage = None
    if family == "passage_review" and response == "accepted" and isinstance(acceptance.parsed, dict):
        passage = review_counts(_passage_item(label), acceptance.parsed["corrected_text"])
    credited = supported_slots - refuted_slots
    if passage is not None:
        credited &= set(passage.hits) | (positive - {span.id for span in _passage_item(label).errors})

    # Protected opportunities: preserved only when the judge says so and, for a passage, the
    # inherited scorer left the span untouched. Missing or unchecked entries fail closed.
    abstention = response == "refusal" and not label["answerable"] and label["expected_outcome"] == "abstention"
    entries = {entry["opportunity_id"]: entry for entry in (sidecar or {}).get("protected", [])}
    preserved_ids: set[str] = set()
    by_stratum = {stratum: [0, 0] for stratum in STRATA}
    for opportunity in label.get("protected", []):
        oid = opportunity["opportunity_id"]
        entry = entries.get(oid)
        by_stratum[opportunity["stratum"]][1] += 1
        if entry is not None and entry["harm"]:
            harmed.add(oid)
        if response != "accepted" and not abstention:
            continue
        if entry is None or entry["preserved"] is None:
            tally.unresolved(f"protected opportunity {oid} unchecked")
            continue
        if entry["preserved"] and oid not in harmed and not (passage and oid in passage.protected):
            preserved_ids.add(oid)
            by_stratum[opportunity["stratum"]][0] += 1

    obligations = {entry["id"]: entry["satisfied"] for entry in (sidecar or {}).get("obligations", [])}
    unmet = []
    for obligation in label.get("obligations", []):
        state = obligations.get(obligation)
        if state is None and response == "accepted":
            tally.unresolved(f"obligation {obligation} unchecked")
        if state is not True:
            unmet.append(obligation)

    edits = size["edits"]
    if passage is not None:  # the corrected text is the edit record; the judge's edit entries restate it
        edits = sum(len(units) for units in (passage.hits, passage.wrong, passage.tokens, passage.insertions))
        edits += len(passage.protected)
    overproduction = adapters.size_problems(
        family, text, individual=size["individual"], batched=size["batched"], edits=edits
    )
    if response == "accepted" and overproduction:
        tally.flags.add(INVALID_OVERPRODUCTION)
    if sidecar is not None and sidecar["budget_exhausted"]:
        if extras:  # off-contract padding consumed the judge's budget
            tally.flags.add(INVALID_OVERPRODUCTION)
        else:
            tally.unresolved("judge budget exhausted on in-contract claims")

    H = len(harmed) + extra_harms
    F = false_corrections
    if passage is not None:
        F = passage.false_alarms + accusation_false_corrections
    emitted = len(seen)
    P = len(preserved_ids) / len(protected_ids) if protected_ids else 1.0
    gap_ok = label["expected_outcome"] in GAP_OUTCOMES and (sidecar or {}).get("outcome_correct") is True
    if response == "accepted":
        coverage = len(credited & required) / len(required) if required else 1.0
        if emitted == 0:
            correctness = 1.0 if gap_ok else 0.0
        else:
            correctness = len(credited) / (len(emitted_slots) + unsupported_extras)
        C = coverage * correctness
        T = 1 if not unmet else 0
    elif abstention and gap_ok:
        T, C = 1, 1.0  # the correct abstention on a prelabelled impossible item
    else:
        T, C, P = 0, 0.0, 0.0
    components = Components(T=T, C=C, P=P, F=F, S=s_count, X=extras, H=H, O=label["O"])
    status = resolve_status(tally.flags)
    value = reward(components, status=status, response=response, answerable=label["answerable"])
    return {
        "item_id": label["item_id"],
        "family": family,
        "judging_mode": label.get("judging_mode"),
        "status": status,
        "provisional": status != "COMPLETE",
        "safety_failed": H > 0,
        "response": response,
        "acceptance_problems": acceptance.reasons,
        "components": components.as_dict(),
        "Q": round(quality(components), 6),
        "R": value,
        "counts": {
            "required_slots": len(required),
            "credited_slots": len(credited),
            "emitted_slots": len(emitted_slots),
            "extra_assertions": extras,
            "unsupported_extras": unsupported_extras,
            "missing_receipts": missing_receipts,
            "fabricated_receipts": len(fabricated),
            "receipt_bound_assertions": bound,
            "assertions": emitted,
            "inherited_false_alarms": passage.false_alarms if passage else None,
            "protected_by_stratum": by_stratum,
            "facets": {facet: dict(count) for facet, count in sorted(facets.items())},
            "unmet_obligations": unmet,
            "size": dict(size),
        },
        "receipt_coverage": round(bound / emitted, 6) if emitted else None,
        "overproduction": overproduction if response == "accepted" else [],
        "evaluator_limits": tally.limits,
    }
