"""Judge call planning: every in-contract claim fits the 32-call Sources budget.

The plan is deliberately pessimistic. One ``check_text`` call covers the whole
output's forms. Batchable claims (forms and senses in writer outputs) share
``verify_words`` and ``query_ulif_records`` calls of at most 200 words each.
Every other claim costs its facet's worst case in dedicated calls, even when
its label already carries a sealed receipt. Claims bound to pack or label
receipts cost nothing. The no-paid proof runs this plan at every family's caps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .contract import FAMILIES, SOURCES_CALLS_PER_PASS

BATCHED_FACETS = frozenset({"form", "meaning"})
BATCH_WORDS = 200  # the hard cap of query_ulif_records; verify_words is held to the same
BATCH_TOOL = {"form": "verify_words", "meaning": "query_ulif_records"}
# Dedicated calls per claim, worst case: a form accusation checks the underlying dictionary
# and corpus after the batched VESUM/ULIF lookups; spelling and style need both the
# structured Правопис lookup and the Антоненко-Давидович search (authority table).
INDIVIDUAL_COST = {
    "form": 2,
    "stress": 1,
    "meaning": 1,
    "historical": 1,
    "naturalness": 1,
    "pedagogy": 1,
    "spelling_style": 2,
    "exercise": 1,
}
WORST_INDIVIDUAL_COST = max(INDIVIDUAL_COST.values())
PREPAID_SOURCES = frozenset({"pack", "label"})


@dataclass(frozen=True)
class Claim:
    claim_id: str
    facet: str
    evidence: str = "judge"  # "judge" (needs calls) or a prepaid "pack" / "label" receipt


@dataclass(frozen=True)
class CallPlan:
    calls: tuple[tuple[str, tuple[str, ...]], ...]  # (tool, claim ids it covers)
    uncovered: tuple[str, ...]

    @property
    def total(self) -> int:
        return len(self.calls)

    @property
    def fits(self) -> bool:
        return self.total <= SOURCES_CALLS_PER_PASS and not self.uncovered


def cost_class(family: str, facet: str) -> str:
    """``batched`` for forms and senses where the family's cap allows batching, else ``individual``."""
    return "batched" if FAMILIES[family].cap.batched and facet in BATCHED_FACETS else "individual"


def plan_calls(family: str, claims: list[Claim]) -> CallPlan:
    calls: list[tuple[str, tuple[str, ...]]] = [("check_text", ())]
    batches: dict[str, list[str]] = {facet: [] for facet in BATCHED_FACETS}
    uncovered: list[str] = []
    for claim in claims:
        if claim.evidence in PREPAID_SOURCES:
            continue
        if claim.facet not in INDIVIDUAL_COST:
            uncovered.append(claim.claim_id)
        elif cost_class(family, claim.facet) == "batched":
            batches[claim.facet].append(claim.claim_id)
        else:
            calls += [("dedicated", (claim.claim_id,))] * INDIVIDUAL_COST[claim.facet]
    for facet in sorted(batches):
        ids = batches[facet]
        for start in range(0, len(ids), BATCH_WORDS):
            calls.append((BATCH_TOOL[facet], tuple(ids[start : start + BATCH_WORDS])))
    return CallPlan(tuple(calls), tuple(uncovered))


def worst_case_calls(family: str) -> int:
    """Calls for a maximum-size output whose claims are all off-label and of the costliest facet."""
    cap = FAMILIES[family].cap
    batched = sum(math.ceil(share / BATCH_WORDS) for share in (cap.batched // 2, cap.batched - cap.batched // 2))
    return 1 + batched + cap.max_claims * WORST_INDIVIDUAL_COST
