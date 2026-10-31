"""Teaching-adequacy evidence and descriptive size reporting for build prompts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scripts.audit import module_size_policy_audit as audit


def build_size_policy_for_plan(
    plan: Mapping[str, Any],
    *,
    plan_path: Path | None = None,
    actual_words: int | None = None,
    module_text: str | None = None,
) -> audit.SizePolicyRecord:
    """Use the same evidence decisions as the post-build audit."""
    track = str(plan.get("level") or "").strip().lower()
    slug = str(plan.get("slug") or (plan_path.stem if plan_path else "")).strip()
    return audit.build_record_for_plan(
        track, plan_path or Path(f"{slug}.yaml"), plan,
        actual_words=actual_words, module_text=module_text,
    )


def size_policy_allows_auto_expansion(record: audit.SizePolicyRecord) -> bool:
    """A size report never authorizes automatic expansion of a short draft.

    Revisions need objective/content-point coverage and evidence of insufficient
    explanation, worked examples or aligned practice, not a word shortfall.
    """
    return False


def size_policy_padding_diagnostic(record: audit.SizePolicyRecord) -> dict[str, Any]:
    """Report repetition independently of all module and plan counts."""
    matches = len(record.repetition.matches) if record.repetition else 0
    return {
        "status": "repetitive_authored_prose" if matches else "clear",
        "review_action": (
            "revise exact/near-duplicate authored paragraphs; do not add more prose"
            if matches else "review objective coverage, explanation, source use and practice"
        ),
        "repetition_status": "revision_needed" if matches else "clear",
        "repetition_match_count": matches,
    }


def size_policy_summary(record: audit.SizePolicyRecord) -> dict[str, Any]:
    """Return evidence decisions with descriptive counts for diagnostics."""
    data = asdict(record)
    data["auto_expand_allowed"] = size_policy_allows_auto_expansion(record)
    data["padding_diagnostic"] = size_policy_padding_diagnostic(record)
    data["expansion_permission"] = (
        "evidence_gap_requires_research_or_plan_review" if record.evidence_gap
        else "coverage_and_teaching_evidence_required"
    )
    return data


def render_writer_size_policy(record: audit.SizePolicyRecord) -> str:
    """Render teaching requirements without legacy floors or ranges."""
    return "\n".join([
        f"- Status: {record.status}",
        "- Rule: teach every objective and content point accurately, with sufficient explanation for the intended learner, worked examples and aligned practice with feedback.",
        "- Rule: explain unfamiliar terms, steps, reasoning and connections between ideas; avoid dry lists and compressed under-explanation.",
        "- Rule: neither reward nor penalize word counts. Add material only when source-backed and pedagogically necessary.",
        "- Rule: for an unsupported objective, emit `<!-- EVIDENCE_GAP: objective=<objective>; missing evidence=<needed source support> -->` and route to research or versioned plan review.",
        "- Rule: preserve source fidelity, factual verification, practice requirements and level-appropriate comprehensibility.",
        "- Rule: reject repetitive padding, repeated framing, decorative digressions, generic exposition, uncited interpretation and inflated transitions.",
    ])


def render_reviewer_size_policy(record: audit.SizePolicyRecord) -> str:
    """Render teaching criteria and actionable repetition evidence."""
    padding = size_policy_padding_diagnostic(record)
    return "\n".join([
        render_writer_size_policy(record),
        "- Reviewer rule: verify source fidelity and factual claims independently; word counts never prove coverage or adequate explanation.",
        "- Reviewer rule: assess the teaching value of the actual passages throughout the module, including explanations, examples, practice and feedback.",
        f"- Repetition status: {padding['repetition_status']}",
        f"- Repetition matches: {padding['repetition_match_count']}",
        f"- Review action: {padding['review_action']}",
    ])
