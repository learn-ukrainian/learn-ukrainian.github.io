"""Preflight and gap report generator (#8431 §4, §7 row 0).

Before any paid writer call, verifies availability of evidence records:
- for each step's needs:
  * example: EX- record exists with right kind ('example') and locked bytes
  * quote: T- record exists with kind 'quote'; until WP 21 lands, every quote need
    is ALWAYS a publication_right gap, whatever the pack record says
  * error: E- record exists with right kind ('error') and locked bytes
  * video: V- record exists with right kind ('video') and locked bytes
  * culture: T- record exists with right kind ('culture') and locked bytes
  * paradigm: word record and forms exist with non-pending stress
- cited forms have non-pending stress (R-23)
- homograph list (candidates for the resolver) is computed over the lesson's allowed words
- failed preflight writes the gap report atomically (mode 0o644) and makes NO call.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.curriculum.evidence import lesson_lock, lock
from scripts.curriculum.evidence import pack as pack_module
from scripts.curriculum.resolver.ambiguity import readings
from scripts.curriculum.resolver.inputs import Allowlist
from scripts.curriculum.resolver.narrow import FormIndex

REPO_ROOT = Path(__file__).resolve().parents[3]

_NEED_KIND_MAP: dict[str, tuple[str, str]] = {
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
    pack_path: Path | None = None,
    words_path: Path | None = None,
    level: str | None = None,
    slug: str | None = None,
    pack_lock_sha256: str | None = None,
    words_lock_sha256: str | None = None,
    learner_state: Any = None,
) -> PreflightResult:
    """Run preflight checks for one lesson entry.

    Verifies availability, record kind, and lock integrity.
    If any gap is found, status is 'evidence_gap', passed is False, and
    gap report is written atomically (0o644) to gap_report_path if specified.
    """
    gaps: list[Gap] = []
    steps = plan_entry.get("steps", [])
    first_step_id = steps[0].get("id", "s1") if steps else "s1"

    # 1. Lock integrity checks (#8431 §4, Finding 3)
    if pack_path is not None:
        if not pack_path.is_file():
            gaps.append(Gap(step=first_step_id, need="pack_missing", detail=f"pack file {pack_path} does not exist"))
        elif not lock.check(pack_path):
            gaps.append(Gap(step=first_step_id, need="pack_lock", detail=f"pack lock mismatch for {pack_path}"))

    if words_path is not None:
        if not words_path.is_file():
            gaps.append(Gap(step=first_step_id, need="words_missing", detail=f"word store {words_path} does not exist"))
        elif not lock.check(words_path):
            gaps.append(Gap(step=first_step_id, need="words_lock", detail=f"words lock mismatch for {words_path}"))

    if level is not None and slug is not None:
        ok, diff = lesson_lock.check_lesson_lock(level, slug)
        if not ok:
            gaps.append(
                Gap(
                    step=first_step_id,
                    need="lesson_lock",
                    detail=f"lesson lock check failed for {level}/{slug}: {diff}",
                )
            )

    # Fail closed if pack or word_store is missing
    if pack is None and pack_path is None:
        gaps.append(Gap(step=first_step_id, need="pack_missing", detail="pack dictionary not provided"))
    if word_store is None and words_path is None:
        gaps.append(Gap(step=first_step_id, need="words_missing", detail="word store dictionary not provided"))

    # 2. Index pack records
    pack_records: dict[str, dict[str, Any]] = {}
    if pack is not None:
        for list_name in pack_module.PACK_RECORD_LISTS:
            for rec in pack.get(list_name) or []:
                if isinstance(rec, dict) and "id" in rec:
                    pack_records[rec["id"]] = rec

    # 3. Index word store records
    store_records: dict[str, dict[str, Any]] = {}
    if word_store is not None:
        for rec in word_store.get("words") or []:
            if isinstance(rec, dict) and "id" in rec:
                store_records[rec["id"]] = rec

    # 4. Check step needs by record kind and existence
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
            if need in _NEED_KIND_MAP:
                id_prefix, expected_kind = _NEED_KIND_MAP[need]
                matching_ids = [i for i in cited_ids if i.startswith(id_prefix)]

                # For error need, also inspect step activities error_refs
                if need == "error":
                    step_activities = step.get("practice") or []
                    for act in plan_entry.get("activities", []):
                        if act.get("id") in step_activities:
                            for eref in act.get("error_refs") or []:
                                if eref.startswith(id_prefix):
                                    matching_ids.append(eref)

                if not matching_ids:
                    gaps.append(
                        Gap(
                            step=step_id,
                            need=need,
                            detail=f"step {step_id} needs {need} but cites no {id_prefix} record",
                        )
                    )
                else:
                    for rid in matching_ids:
                        if rid not in pack_records:
                            gaps.append(
                                Gap(
                                    step=step_id,
                                    need=need,
                                    detail=f"{need} record {rid} missing from pack",
                                )
                            )
                        else:
                            rec = pack_records[rid]
                            rec_kind = rec.get("kind")
                            if rec_kind is not None and rec_kind != expected_kind:
                                gaps.append(
                                    Gap(
                                        step=step_id,
                                        need=need,
                                        detail=f"record {rid} cited for {need} has kind {rec_kind!r}, expected {expected_kind!r}",
                                    )
                                )

                            # Finding 2: Until WP 21 lands, a quote need is ALWAYS a publication_right gap,
                            # whatever the pack record says. No publish.allowed branch.
                            if need == "quote":
                                gaps.append(
                                    Gap(
                                        step=step_id,
                                        need="publication_right",
                                        detail=f"source for quote {rid} in step {step_id} lacks verified publication right (WP 21 pending)",
                                    )
                                )

            elif need == "paradigm":
                paradigm = step.get("paradigm")
                if not paradigm:
                    gaps.append(
                        Gap(
                            step=step_id,
                            need="paradigm",
                            detail=f"step {step_id} needs paradigm but carries no paradigm block",
                        )
                    )
                else:
                    wid = paradigm.get("word")
                    if not wid or wid not in store_records:
                        gaps.append(
                            Gap(step=step_id, need="word_form", detail=f"paradigm word {wid} missing from word store")
                        )
                    else:
                        w_rec = store_records[wid]
                        p_forms = paradigm.get("forms") or []
                        store_form_tags = {f["tags"]: f for f in w_rec.get("forms") or []}
                        for p_tag in p_forms:
                            if p_tag not in store_form_tags:
                                gaps.append(
                                    Gap(
                                        step=step_id,
                                        need="word_form",
                                        detail=f"paradigm form tag {p_tag} not found in {wid}",
                                    )
                                )
                            elif store_form_tags[p_tag].get("stress_source") == "pending":
                                gaps.append(
                                    Gap(
                                        step=step_id,
                                        need="word_form",
                                        detail=f"paradigm form {p_tag} in {wid} has pending stress",
                                    )
                                )

    # 5. Check all cited forms in lesson for non-pending stress (R-23)
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

    # 6. Compute homographs via resolver restricted to lesson's allowed words (#8431 §8.2, Finding 12)
    if allowlist is not None:
        homographs = compute_homographs(allowlist)
    elif word_store is not None:
        lesson_wids: set[str] = set()
        if learner_state is not None:
            if hasattr(learner_state, "all_allowed_ids"):
                lesson_wids.update(learner_state.all_allowed_ids)
            elif isinstance(learner_state, dict):
                lesson_wids.update(learner_state.get("all_allowed_ids", []))
                lesson_wids.update(learner_state.get("base_ids", []))
                lesson_wids.update(learner_state.get("core_ids", {}).keys())
                lesson_wids.update(learner_state.get("name_ids", {}).keys())

        # Collect word IDs cited in inventory
        for item in vocab.get("core", []):
            if isinstance(item, dict) and "evidence" in item:
                lesson_wids.add(item["evidence"])
        for item in vocab.get("incidental", []):
            if isinstance(item, dict) and "evidence" in item:
                lesson_wids.add(item["evidence"])
        for r in vocab.get("recycled") or []:
            lesson_wids.add(r)

        # Collect words in paradigms
        for step in steps:
            paradigm = step.get("paradigm")
            if isinstance(paradigm, dict) and "word" in paradigm:
                lesson_wids.add(paradigm["word"])

        # Construct allowlist only from lesson's allowed records
        store_words_all = word_store.get("words") or []
        filtered_words = [w for w in store_words_all if w.get("id") in lesson_wids] if lesson_wids else store_words_all

        constructed_allowlist = Allowlist.from_records(
            filtered_words,
            words_lock=words_lock_sha256 or "dummy",
            label="preflight",
        )
        homographs = compute_homographs(constructed_allowlist)
    else:
        homographs = []

    passed = len(gaps) == 0
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
        # Atomic write with mode 0o644 (#8431 §4, Finding 4 & 11)
        lock.atomic_write(gap_report_path, res.render_gap_report().encode("utf-8"))

    return res
