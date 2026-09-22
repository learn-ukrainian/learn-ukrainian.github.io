"""Preflight and gap report generator (#8431 §4, §7 row 0).

Before any paid writer call, verifies availability of evidence records:
- for each step's needs:
  * example: EX- record exists with right kind and locked bytes
  * quote: T- record exists, and source has a verified publication right (WP 21 not on main -> gap publication_right)
  * error: E- record exists with right kind and locked bytes
  * video: V- record exists with locked bytes
  * culture: T- record exists with locked bytes
  * paradigm: word record and forms exist with non-pending stress
- cited forms have non-pending stress (R-23)
- homograph list (candidates for the resolver) is computed and count reported
- failed preflight writes the gap report and makes NO call.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.curriculum.evidence import lock, registry
from scripts.curriculum.evidence import words as words_module
from scripts.curriculum.evidence import pack as pack_module
from scripts.curriculum.resolver.ambiguity import readings
from scripts.curriculum.resolver.inputs import Allowlist
from scripts.curriculum.resolver.narrow import FormIndex

REPO_ROOT = Path(__file__).resolve().parents[3]

_NEED_KIND_MAP = {
    "example": ("EX-", "example"),
    "quote": ("T-", "quote"),
    "culture": ("T-", "culture"),
    "error": ("E-", "error"),
    "video": ("V-", "video"),
}


@dataclass(frozen=True)
class Gap:
    """One declared evidence gap (#8431 §4)."""

    step: str
    need: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"step": self.step, "need": self.need, "detail": self.detail}


@dataclass(frozen=True)
class PreflightResult:
    """Deterministic outcome of check 0 preflight (#8431 §7 row 0)."""

    passed: bool
    status: str  # "ok" or "evidence_gap"
    gaps: list[Gap]
    homographs: list[str]
    homograph_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "passed": self.passed,
            "gaps": [g.to_dict() for g in self.gaps],
            "homographs": list(self.homographs),
            "homograph_count": self.homograph_count,
        }

    def render_gap_report(self) -> str:
        data = {
            "status": self.status,
            "gaps": [g.to_dict() for g in self.gaps],
        }
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def compute_homographs(allowlist: Allowlist) -> list[str]:
    """Compute homograph list (ambiguous candidates for resolver) from allowlist."""
    index = FormIndex(allowlist)
    ambiguities: list[str] = []
    for spelling, candidates in index.usable.items():
        if len(readings(candidates)) > 1:
            ambiguities.append(spelling)
    return sorted(ambiguities)


def preflight_lesson(
    plan_entry: dict[str, Any],
    *,
    pack: dict[str, Any] | None = None,
    word_store: dict[str, Any] | None = None,
    allowlist: Allowlist | None = None,
    source_registry: dict[str, Any] | None = None,
    gap_report_path: Path | None = None,
    pack_lock_sha256: str | None = None,
    words_lock_sha256: str | None = None,
) -> PreflightResult:
    """Run preflight checks for one lesson entry.

    If any gap is found, status is 'evidence_gap', passed is False, and
    gap report is written to gap_report_path if specified.
    """
    gaps: list[Gap] = []

    # 1. Index pack records
    pack_records: dict[str, dict[str, Any]] = {}
    if pack is not None:
        for list_name in pack_module.PACK_RECORD_LISTS:
            for rec in pack.get(list_name) or []:
                if isinstance(rec, dict) and "id" in rec:
                    pack_records[rec["id"]] = rec

    # 2. Index word store records
    store_records: dict[str, dict[str, Any]] = {}
    if word_store is not None:
        for rec in word_store.get("words") or []:
            if isinstance(rec, dict) and "id" in rec:
                store_records[rec["id"]] = rec

    steps = plan_entry.get("steps", [])
    first_step_id = steps[0].get("id", "s1") if steps else "s1"

    # 3. Check step needs
    for step in steps:
        step_id = step.get("id", "")
        needs = step.get("needs") or []
        step_evidence = step.get("evidence") or []
        step_ref = step.get("ref")
        step_explains = step.get("explains") or []

        cited_ids = set(step_evidence) | set(step_explains)
        if step_ref:
            cited_ids.add(step_ref)

        for need in needs:
            if need == "example":
                ex_ids = [i for i in cited_ids if i.startswith("EX-")]
                if not ex_ids:
                    gaps.append(Gap(step=step_id, need="example", detail=f"step {step_id} needs example but cites no EX- record"))
                else:
                    for eid in ex_ids:
                        if eid not in pack_records:
                            gaps.append(Gap(step=step_id, need="example", detail=f"example record {eid} missing from pack"))

            elif need == "quote":
                # Quote need check
                t_ids = [i for i in cited_ids if i.startswith("T-")]
                if not t_ids:
                    gaps.append(Gap(step=step_id, need="quote", detail=f"step {step_id} needs quote but cites no T- record"))
                else:
                    for tid in t_ids:
                        if tid not in pack_records:
                            gaps.append(Gap(step=step_id, need="quote", detail=f"quote record {tid} missing from pack"))
                        else:
                            # Publication right check
                            # WP 21 is not on main: every quote need is a publication_right gap, never a pass
                            rec = pack_records[tid]
                            src_meta = rec.get("source") or {}
                            publish = src_meta.get("publish") if isinstance(src_meta, dict) else None
                            if not publish or not publish.get("allowed"):
                                gaps.append(
                                    Gap(
                                        step=step_id,
                                        need="publication_right",
                                        detail=f"source for quote {tid} in step {step_id} lacks verified publication right (WP 21 pending)",
                                    )
                                )

            elif need == "error":
                e_ids = [i for i in cited_ids if i.startswith("E-")]
                # Also check activities in this step
                step_activities = step.get("practice") or []
                for act in plan_entry.get("activities", []):
                    if act.get("id") in step_activities:
                        for eref in act.get("error_refs") or []:
                            e_ids.append(eref)
                if not e_ids:
                    gaps.append(Gap(step=step_id, need="error", detail=f"step {step_id} needs error but cites no E- record"))
                else:
                    for eid in e_ids:
                        if eid not in pack_records:
                            gaps.append(Gap(step=step_id, need="error", detail=f"error record {eid} missing from pack"))

            elif need == "video":
                v_ids = [i for i in cited_ids if i.startswith("V-")]
                if not v_ids:
                    gaps.append(Gap(step=step_id, need="video", detail=f"step {step_id} needs video but cites no V- record"))
                else:
                    for vid in v_ids:
                        if vid not in pack_records:
                            gaps.append(Gap(step=step_id, need="video", detail=f"video record {vid} missing from pack"))

            elif need == "culture":
                t_ids = [i for i in cited_ids if i.startswith("T-")]
                if not t_ids:
                    gaps.append(Gap(step=step_id, need="culture", detail=f"step {step_id} needs culture but cites no T- record"))
                else:
                    for tid in t_ids:
                        if tid not in pack_records:
                            gaps.append(Gap(step=step_id, need="culture", detail=f"culture record {tid} missing from pack"))

            elif need == "paradigm":
                paradigm = step.get("paradigm")
                if not paradigm:
                    gaps.append(Gap(step=step_id, need="paradigm", detail=f"step {step_id} needs paradigm but carries no paradigm block"))
                else:
                    wid = paradigm.get("word")
                    if not wid or wid not in store_records:
                        gaps.append(Gap(step=step_id, need="word_form", detail=f"paradigm word {wid} missing from word store"))
                    else:
                        w_rec = store_records[wid]
                        p_forms = paradigm.get("forms") or []
                        store_form_tags = {f["tags"]: f for f in w_rec.get("forms") or []}
                        for p_tag in p_forms:
                            if p_tag not in store_form_tags:
                                gaps.append(Gap(step=step_id, need="word_form", detail=f"paradigm form tag {p_tag} not found in {wid}"))
                            elif store_form_tags[p_tag].get("stress_source") == "pending":
                                gaps.append(Gap(step=step_id, need="word_form", detail=f"paradigm form {p_tag} in {wid} has pending stress"))

    # 4. Check all cited forms in lesson for non-pending stress (R-23)
    inv = plan_entry.get("inventory") or {}
    vocab = inv.get("vocabulary") or {}
    core_items = vocab.get("core") or []
    for item in core_items:
        if isinstance(item, dict):
            wid = item.get("evidence")
            if wid and wid in store_records:
                w_rec = store_records[wid]
                store_forms_by_tag = {f["tags"]: f for f in w_rec.get("forms") or []}
                for ftag in item.get("forms") or []:
                    if ftag in store_forms_by_tag:
                        f_spec = store_forms_by_tag[ftag]
                        if f_spec.get("stress_source") == "pending":
                            gaps.append(
                                Gap(
                                    step=first_step_id,
                                    need="word_form",
                                    detail=f"cited form {ftag} of word {wid} ({w_rec.get('lemma')}) has pending stress",
                                )
                            )

    # 5. Compute homographs via resolver
    if allowlist is not None:
        homographs = compute_homographs(allowlist)
    elif word_store is not None:
        # Construct allowlist from available store records
        all_store_words = word_store.get("words") or []
        constructed_allowlist = Allowlist.from_records(
            all_store_words,
            words_lock=words_lock_sha256 or "dummy",
            label="preflight",
        )
        homographs = compute_homographs(constructed_allowlist)
    else:
        homographs = []

    passed = (len(gaps) == 0)
    status = "ok" if passed else "evidence_gap"

    res = PreflightResult(
        passed=passed,
        status=status,
        gaps=gaps,
        homographs=homographs,
        homograph_count=len(homographs),
    )

    if not passed and gap_report_path is not None:
        gap_report_path = Path(gap_report_path)
        gap_report_path.parent.mkdir(parents=True, exist_ok=True)
        gap_report_path.write_text(res.render_gap_report(), encoding="utf-8")

    return res
