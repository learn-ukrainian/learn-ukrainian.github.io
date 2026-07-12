"""Effective module size policy for writer prompts and build prechecks.

The read-only classifier lives in ``scripts.audit.module_size_policy_audit``.
This module adapts that classifier for already-loaded plans so build code can
inject a stable policy block without importing CLI concerns into prompts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scripts.audit import module_size_policy_audit as audit

LEGACY_CORE_BAND = "legacy_core_floor_only"
PLAN_FLOOR_ONLY = "plan_floor_only"
PLAN_REVIEW_NEEDED = "plan_review_needed"
MISSING_DOSSIER = "missing_dossier"
INVALID_SIZE_POLICY = "invalid_size_policy"


def _record_to_dict(record: audit.SizePolicyRecord) -> dict[str, Any]:
    data = asdict(record)
    if record.metrics is not None:
        data["metrics"] = asdict(record.metrics)
    return data


def build_size_policy_for_plan(
    plan: Mapping[str, Any],
    *,
    plan_path: Path | None = None,
    actual_words: int | None = None,
) -> audit.SizePolicyRecord:
    """Resolve the effective advisory size policy for an already-loaded plan."""
    track = str(plan.get("level") or "").strip().lower()
    slug = str(plan.get("slug") or (plan_path.stem if plan_path else "")).strip()
    plan_floor = audit._as_int(plan.get("word_target"))
    plan_outline_words = audit._sum_outline_words(plan.get("content_outline"))
    module_path = audit._module_path(track, slug) if track and slug else None
    if actual_words is None and module_path is not None and module_path.exists():
        actual_words = audit.word_count(module_path)

    policy_uses_dossier_metrics = "size_policy" in plan or (
        track in audit.SEMINAR_TRACKS or track in audit.CORE_RESEARCH_TRACKS
    )
    dossier_path = (
        audit._dossier_path(track, slug, dict(plan))
        if track and slug and policy_uses_dossier_metrics
        else None
    )
    metrics = audit.dossier_metrics(dossier_path) if dossier_path else None
    override, override_errors = audit.explicit_size_policy_override(plan)
    displayed_plan_path = audit.display_path(plan_path) if plan_path else ""
    displayed_dossier_path = audit.display_path(dossier_path) if dossier_path else None
    displayed_module_path = (
        audit.display_path(module_path) if module_path and module_path.exists() else None
    )
    if override is not None:
        return audit.build_explicit_size_policy_record(
            track=track,
            slug=slug,
            plan_path=displayed_plan_path,
            dossier_path=displayed_dossier_path,
            module_path=displayed_module_path,
            plan_floor=plan_floor,
            plan_outline_words=plan_outline_words,
            actual_words=actual_words,
            metrics=metrics,
            override=override,
        )

    if track not in audit.SEMINAR_TRACKS and track not in audit.CORE_RESEARCH_TRACKS:
        notes = [
            "A1-B2 released core tracks use the plan floor only; dossier-led ceilings apply to seminar tracks and C1-C2 evidence packets."
        ]
        status = PLAN_FLOOR_ONLY
        if override_errors:
            status = INVALID_SIZE_POLICY
            notes.extend(
                [
                    "Explicit size_policy is invalid and cannot replace the plan-floor policy.",
                    *override_errors,
                ]
            )
        return audit.SizePolicyRecord(
            track=track,
            slug=slug,
            basis="plan_floor_fallback",
            plan_path=displayed_plan_path,
            dossier_path=displayed_dossier_path,
            module_path=displayed_module_path,
            plan_floor=plan_floor,
            plan_outline_words=plan_outline_words,
            actual_words=actual_words,
            density_band=LEGACY_CORE_BAND,
            band_min=plan_floor,
            band_max=None,
            effective_min=plan_floor,
            advisory_ceiling=None,
            status=status,
            notes=notes,
            metrics=metrics,
        )

    if metrics is not None:
        basis = "research_dossier"
        band = audit.classify_dossier(track, metrics)
    elif track in audit.CORE_RESEARCH_TRACKS:
        basis = "core_evidence_packet"
        band = audit.classify_core_evidence(dict(plan))
    else:
        basis = "missing_research_dossier"
        band = "sparse"

    band_min, band_max = audit.band_limits(band)
    advisory_ceiling = None
    if plan_floor is not None:
        advisory_ceiling = max(plan_floor, band_max) if band_max is not None else None
    status, notes = audit._status_and_notes(
        track=track,
        plan_floor=plan_floor,
        actual_words=actual_words,
        band=band,
        band_max=band_max,
        advisory_ceiling=advisory_ceiling,
        dossier_path=dossier_path,
    )
    if override_errors:
        status = INVALID_SIZE_POLICY
        notes.extend(
            [
                "Explicit size_policy is invalid and cannot replace generic density-band limits.",
                *override_errors,
            ]
        )

    return audit.SizePolicyRecord(
        track=track,
        slug=slug,
        basis=basis,
        plan_path=displayed_plan_path,
        dossier_path=displayed_dossier_path,
        module_path=displayed_module_path,
        plan_floor=plan_floor,
        plan_outline_words=plan_outline_words,
        actual_words=actual_words,
        density_band=band,
        band_min=band_min,
        band_max=band_max,
        effective_min=plan_floor,
        advisory_ceiling=advisory_ceiling,
        status=status,
        notes=notes,
        metrics=metrics,
    )


def size_policy_allows_auto_expansion(record: audit.SizePolicyRecord) -> bool:
    """Return whether build code may auto-request expansion for short drafts."""
    return record.status not in {PLAN_REVIEW_NEEDED, MISSING_DOSSIER, INVALID_SIZE_POLICY}


def size_policy_padding_diagnostic(record: audit.SizePolicyRecord) -> dict[str, Any]:
    """Return the advisory density-vs-padding review signal for diagnostics."""
    diagnostic: dict[str, Any] = {
        "status": "not_evaluated",
        "review_action": "no_count_available",
        "over_advisory_ceiling_words": 0,
    }
    if record.actual_words is None:
        return diagnostic

    if record.actual_words < (record.plan_floor or 0):
        diagnostic["status"] = "below_plan_floor"
        diagnostic["review_action"] = "do_not_pad; check whether plan floor exceeds sourced evidence"
        return diagnostic

    if record.advisory_ceiling is None:
        diagnostic["status"] = "no_advisory_ceiling"
        diagnostic["review_action"] = "exceptional_or_floor_only; require explicit source-backed justification for very long modules"
        return diagnostic

    over_by = max(0, record.actual_words - record.advisory_ceiling)
    diagnostic["over_advisory_ceiling_words"] = over_by
    if over_by:
        diagnostic["status"] = "over_advisory_ceiling"
        diagnostic["review_action"] = (
            "advisory_review_only; distinguish source-backed density from filler/padding"
        )
    else:
        diagnostic["status"] = "within_advisory_ceiling"
        diagnostic["review_action"] = "no_size_padding_signal; review pedagogy and source use normally"
    return diagnostic


def size_policy_summary(record: audit.SizePolicyRecord) -> dict[str, Any]:
    """Return a stable small summary suitable for JSON/YAML diagnostics."""
    data = _record_to_dict(record)
    data["auto_expand_allowed"] = size_policy_allows_auto_expansion(record)
    data["padding_diagnostic"] = size_policy_padding_diagnostic(record)
    if record.status == PLAN_REVIEW_NEEDED:
        data["expansion_permission"] = "plan_policy_review_required"
    elif record.status == MISSING_DOSSIER:
        data["expansion_permission"] = "blocked_until_research_dossier"
    elif record.status == INVALID_SIZE_POLICY:
        data["expansion_permission"] = "blocked_until_size_policy_is_valid"
    elif record.status == PLAN_FLOOR_ONLY:
        data["expansion_permission"] = "plan_floor_only"
    else:
        data["expansion_permission"] = "source_backed_only"
    return data


def render_writer_size_policy(record: audit.SizePolicyRecord) -> str:
    """Render a concise policy block for writer prompts."""
    summary = size_policy_summary(record)
    recommended = "-"
    if record.band_min is not None and record.band_max is not None:
        recommended = f"{record.band_min}-{record.band_max}"
    elif record.band_min is not None:
        recommended = f"{record.band_min}+"

    ceiling = str(record.advisory_ceiling) if record.advisory_ceiling is not None else "none"
    notes = record.notes or ["No additional policy notes."]
    note_lines = "\n".join(f"- {note}" for note in notes)
    return "\n".join(
        [
            f"- Basis: {record.basis}",
            f"- Density band: {record.density_band}",
            f"- Plan floor words: {record.plan_floor if record.plan_floor is not None else '-'}",
            f"- Recommended range: {recommended}",
            f"- Advisory ceiling words: {ceiling}",
            f"- Expansion permission: {summary['expansion_permission']}",
            f"- Status: {record.status}",
            "- Rule: meet the plan floor with complete coverage, but expand only when the added material is source-backed and pedagogically useful.",
            "- Rule: if grounded material runs out before the floor, emit `<!-- SIZE_POLICY_MISMATCH: plan floor exceeds sourced evidence -->` instead of inventing depth.",
            "- Rule: do not add repeated framing, generic exposition, uncited interpretation, or filler to chase old fixed multipliers.",
            "Notes:",
            note_lines,
        ]
    )


def render_reviewer_size_policy(record: audit.SizePolicyRecord) -> str:
    """Render the effective size policy for LLM reviewer prompts."""
    summary = size_policy_summary(record)
    padding = summary["padding_diagnostic"]
    base = render_writer_size_policy(record)
    return "\n".join(
        [
            base,
            "- Reviewer rule: do not fail or pass a module on word count alone; deterministic gates handled the floor.",
            "- Reviewer rule: if the padding diagnostic is `over_advisory_ceiling`, inspect whether the extra length is source-backed density, necessary pedagogy, or filler/padding.",
            "- Reviewer rule: source-backed density is acceptable evidence; repeated framing, generic exposition, uncited interpretation, and inflated transitions are padding evidence.",
            "Padding diagnostic:",
            f"- Status: {padding['status']}",
            f"- Over advisory ceiling words: {padding['over_advisory_ceiling_words']}",
            f"- Review action: {padding['review_action']}",
        ]
    )
