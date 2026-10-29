"""Bind judged claims to verified Sources receipts (protocol lines 362-384).

Receipts are the review ledgers of ``scripts/review/receipts``: each ledger is
read through ``ledger.records``, which verifies its ``.sha256`` sidecar, and
each call's outcome comes from the ``outcome_facts`` stored at record time
(``outcomes.search_outcome``). A claim binding names one receipt and repeats
the tool, the argument and result digests, an exact evidence excerpt and a
source locator; every term must match the ledger record. A successful call or
a hit count is never entailment: the judge's verdict decides entailment, and
this module only proves that the evidence it cites exists and says what it
quotes.

Ledger roles: ``candidate`` (the scored attempt's own calls), ``judge`` (the
judge's calls), ``pack`` (pack-builder receipts behind a fresh writer's inputs)
and ``label`` (receipts sealed with the G1 label). Pedagogy claims may also cite
the normative evidence sealed in the request itself (role ``request``: a
Standard excerpt with its line numbers, the video decision, the resource
inventory), which is checked against those exact bytes.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.review.receipts.ledger import REVIEW_TOOLS, LedgerError, dumps, records
from scripts.review.receipts.outcomes import search_outcome

ROLES = ("candidate", "judge", "pack", "label")
REQUEST_ROLE = "request"

# Positive authorities per facet (protocol authority table). ``search_definitions`` (СУМ-11)
# is absent everywhere: it can never support a claim, and a positive use of it counts in S.
_FORM = frozenset(
    {"verify_words", "verify_word", "verify_lemma", "inspect_word", "inspect_words", "query_ulif_records"}
)
_STRESS = frozenset({"verify_stress", "query_ulif_records", "query_sum20"})
_MEANING = frozenset({"query_sum20", "query_ulif_records", "search_slovnyk_me"})
AUTHORITIES: dict[str, frozenset[str]] = {
    "form": _FORM,
    "stress": _STRESS,
    "meaning": _MEANING,
    "historical": frozenset({"search_grinchenko_1907", "search_heritage"}),
    "naturalness": frozenset({"search_text", "query_grac", "search_heritage", "query_cefr_level"}),
    "pedagogy": frozenset({"search_text", "search_resources"}),
    "spelling_style": frozenset({"query_pravopys", "search_style_guide"}),
    "exercise": _FORM | _STRESS | _MEANING,
}
# Evidence of absence (a VESUM miss before a form accusation, a Sovietism signal) uses
# these tools with ``polarity: negative``; the judge still owns the accusation checks.
NEGATIVE_TOOLS = frozenset(REVIEW_TOOLS)
SUM11_TOOL = "search_definitions"
_SUM11_MARKERS = ("сум-11", "сум11", "сум 11", "11 томах")

VERIFIED = "verified"
FABRICATED = "fabricated"  # a candidate-cited receipt its own ledger does not hold
EVIDENCE_INVALID = "evidence_invalid"  # the record exists but the binding does not match it
EVIDENCE_MISSING = "evidence_missing"  # a judge, pack or label receipt that is not in its ledger
SUM11_POSITIVE = "sum11_positive"


class BindingError(Exception):
    """A ledger is unusable; the cell cannot be scored."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def arguments_sha256(arguments: Any) -> str:
    return sha256_text(dumps(arguments))


def _fold(text: str) -> str:
    return unicodedata.normalize("NFC", text)


@dataclass(frozen=True)
class LedgerRef:
    """One verified ledger and the attempt identity its records must carry."""

    role: str
    path: Path
    review_id: str
    attempt_id: str
    manifest_sha256: str


class LedgerIndex:
    """Receipts by role and id; every record must belong to its ledger's attempt."""

    def __init__(self, refs: list[LedgerRef], request_evidence: dict[str, str] | None = None) -> None:
        self.request_evidence = dict(request_evidence or {})
        self._by_role: dict[str, dict[str, dict[str, Any]]] = {role: {} for role in ROLES}
        self.counts: dict[str, int] = dict.fromkeys(ROLES, 0)
        for ref in refs:
            if ref.role not in ROLES:
                raise BindingError(f"unknown ledger role {ref.role!r}")
            try:
                found = records(ref.path)
            except (LedgerError, OSError, ValueError) as exc:
                raise BindingError(f"{ref.role} ledger is unusable: {type(exc).__name__}") from exc
            indexed = self._by_role[ref.role]
            for record in found:
                receipt_id = record.get("receipt_id")
                if not isinstance(receipt_id, str) or receipt_id in indexed:
                    raise BindingError(f"{ref.role} ledger has a duplicate or missing receipt id")
                identity = (record.get("review_id"), record.get("attempt_id"), record.get("manifest_sha256"))
                if identity != (ref.review_id, ref.attempt_id, ref.manifest_sha256):
                    raise BindingError(f"{ref.role} ledger holds a record of another attempt")
                indexed[receipt_id] = record
            self.counts[ref.role] += len(found)

    def get(self, role: str, receipt_id: str) -> dict[str, Any] | None:
        return self._by_role.get(role, {}).get(receipt_id)


@dataclass(frozen=True)
class BindingCheck:
    status: str
    reason: str
    sum11: bool = False


def is_sum11(dictionary: str) -> bool:
    folded = dictionary.casefold()
    return any(marker in folded for marker in _SUM11_MARKERS)


def check_binding(binding: dict[str, Any], facet: str, index: LedgerIndex) -> BindingCheck:
    """Whether ``binding`` is real evidence for a claim of ``facet`` (not whether it entails it)."""
    role, receipt_id = binding.get("role"), binding.get("receipt_id")
    if role == REQUEST_ROLE:
        return _check_request_evidence(binding, facet, index)
    record = index.get(str(role), str(receipt_id))
    if record is None:
        if role == "candidate":
            return BindingCheck(FABRICATED, "receipt is not in the candidate's verified ledger")
        return BindingCheck(EVIDENCE_MISSING, f"receipt is not in the {role} ledger")
    tool = record.get("tool")
    if binding.get("tool") != tool:
        return BindingCheck(EVIDENCE_INVALID, "tool differs from the receipt")
    if binding.get("arguments_sha256") != arguments_sha256(record.get("arguments")):
        return BindingCheck(EVIDENCE_INVALID, "arguments differ from the receipt")
    result = record.get("result")
    if not isinstance(result, str) or binding.get("result_sha256") != sha256_text(result):
        return BindingCheck(EVIDENCE_INVALID, "result differs from the receipt")
    excerpt = binding.get("evidence_excerpt")
    if not isinstance(excerpt, str) or not excerpt.strip() or _fold(excerpt) not in _fold(result):
        return BindingCheck(EVIDENCE_INVALID, "evidence excerpt is not in the full result")
    if not isinstance(binding.get("source_locator"), str) or not binding["source_locator"].strip():
        return BindingCheck(EVIDENCE_INVALID, "source locator is missing")
    outcome = search_outcome(str(record.get("status")), record.get("outcome_facts") or {})
    polarity = binding.get("polarity", "positive")
    if polarity == "negative":
        if tool not in NEGATIVE_TOOLS or outcome != "no_hits":
            return BindingCheck(EVIDENCE_INVALID, "evidence of absence needs a completed call with no hits")
        return BindingCheck(VERIFIED, "")
    if polarity != "positive":
        return BindingCheck(EVIDENCE_INVALID, f"unknown polarity {polarity!r}")
    if outcome != "hits_but_no_support":  # the ledger's name for a completed call with hits
        return BindingCheck(EVIDENCE_INVALID, f"positive evidence needs hits, the call shows {outcome!r}")
    if tool == SUM11_TOOL:
        return BindingCheck(SUM11_POSITIVE, "СУМ-11 is never a positive authority", sum11=True)
    if tool == "search_slovnyk_me":
        dictionary = binding.get("underlying_dictionary")
        if not isinstance(dictionary, str) or not dictionary.strip() or _fold(dictionary) not in _fold(result):
            return BindingCheck(EVIDENCE_INVALID, "slovnyk.me evidence must name its underlying dictionary")
        if is_sum11(dictionary):
            return BindingCheck(SUM11_POSITIVE, "slovnyk.me result is СУМ-11", sum11=True)
    if tool not in AUTHORITIES.get(facet, frozenset()):
        return BindingCheck(EVIDENCE_INVALID, f"{tool} is not a positive authority for {facet}")
    return BindingCheck(VERIFIED, "")


def _check_request_evidence(binding: dict[str, Any], facet: str, index: LedgerIndex) -> BindingCheck:
    if facet != "pedagogy":
        return BindingCheck(EVIDENCE_INVALID, "request evidence supports pedagogy claims only")
    text = index.request_evidence.get(str(binding.get("evidence_id")))
    if text is None:
        return BindingCheck(EVIDENCE_MISSING, "request evidence id is not sealed in the request")
    excerpt = binding.get("evidence_excerpt")
    if not isinstance(excerpt, str) or not excerpt.strip() or _fold(excerpt) not in _fold(text):
        return BindingCheck(EVIDENCE_INVALID, "evidence excerpt is not in the sealed request evidence")
    if not isinstance(binding.get("source_locator"), str) or not binding["source_locator"].strip():
        return BindingCheck(EVIDENCE_INVALID, "source locator is missing")
    return BindingCheck(VERIFIED, "")
