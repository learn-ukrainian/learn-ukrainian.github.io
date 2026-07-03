from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit import apply_source_inventory_promotion as apply
from scripts.audit import plan_source_inventory_promotion as planner
from scripts.audit.source_inventory_intake import SourceInventoryError


def test_apply_promotion_plan_inserts_manifest_entries_in_order() -> None:
    manifest = _manifest([_entry("авто"), _entry("якір")])
    plan = _plan([_addition("мама")])

    result = apply.apply_promotion_plan(manifest, plan, expected_additions=1)

    assert [entry["lemma"] for entry in manifest["entries"]] == ["авто", "мама", "якір"]
    assert manifest["stats"]["lemmas_total"] == 3
    assert manifest["enrichment_generated"] is True
    assert result["counts"] == {
        "planned_additions": 1,
        "promoted": 1,
        "already_present": 0,
        "skipped_existing": 0,
    }
    assert result["production_outputs_updated"] == []


def test_apply_promotion_plan_is_idempotent_for_existing_entry() -> None:
    manifest = _manifest([_entry("мама")])
    plan = _plan([_addition("мама")])

    result = apply.apply_promotion_plan(manifest, plan, expected_additions=1)

    assert [entry["lemma"] for entry in manifest["entries"]] == ["мама"]
    assert result["counts"]["promoted"] == 0
    assert result["counts"]["already_present"] == 1
    assert result["already_present"][0]["reason"] == "already_in_manifest"


def test_apply_promotion_plan_rejects_missing_candidates() -> None:
    manifest = _manifest([])
    plan = _plan([])
    plan["missing_candidates"] = [{"lemma": "тест"}]

    with pytest.raises(SourceInventoryError, match="missing candidate"):
        apply.apply_promotion_plan(manifest, plan)


def test_apply_promotion_plan_allows_missing_production_outputs_key() -> None:
    manifest = _manifest([])
    plan = _plan([_addition("мама")])
    plan.pop("production_outputs_updated")

    result = apply.apply_promotion_plan(manifest, plan)

    assert result["counts"]["promoted"] == 1


def test_apply_promotion_plan_enforces_expected_counts() -> None:
    manifest = _manifest([])
    plan = _plan([_addition("мама")])

    with pytest.raises(SourceInventoryError, match="expected 2 planned additions"):
        apply.apply_promotion_plan(manifest, plan, expected_additions=2)


def test_apply_promotion_plan_filters_source_family() -> None:
    manifest = _manifest([])
    plan = _plan(
        [
            _addition("мама", source_family="teacher_lesson"),
            _addition("риба", source_family="textbook"),
        ],
        skipped=[_skipped("чверть", source_family="teacher_lesson")],
    )

    result = apply.apply_promotion_plan(
        manifest,
        plan,
        source_family="teacher_lesson",
        expected_additions=1,
        expected_skipped_existing=1,
    )

    assert [entry["lemma"] for entry in manifest["entries"]] == ["мама"]
    assert result["counts"]["skipped_existing"] == 1


def test_apply_existing_provenance_overlay_updates_existing_entries() -> None:
    manifest = _manifest([_entry("чверть", source_provenance=[])])
    result = apply.apply_promotion_plan(
        manifest,
        _plan([], skipped=[_skipped("чверть")]),
        expected_additions=0,
        expected_skipped_existing=1,
    )
    decision = _approved_decision("чверть")
    candidate_index = {
        decision.source_key: planner.CandidateMatch(
            entry={"source_provenance": [_provenance(locator="explicit vocabulary table row 14")]},
            bucket="needs_review",
            reasons=(),
        )
    }

    apply.apply_existing_provenance_overlay(
        manifest,
        result,
        candidate_index,
        [decision],
        source_family="teacher_lesson",
    )

    refs = manifest["entries"][0]["source_provenance"]
    assert len(refs) == 1
    assert refs[0]["source_family"] == "teacher_lesson"
    assert result["counts"]["overlay_updated_entries"] == 1
    assert result["counts"]["overlay_added_provenance_refs"] == 1


def test_format_report_uses_manifest_lemma_overlay_fallback() -> None:
    report = apply.format_report(
        {
            "workflow": apply.WORKFLOW_ID,
            "source_family": "teacher_lesson",
            "counts": {
                "planned_additions": 0,
                "promoted": 0,
                "already_present": 0,
                "skipped_existing": 0,
                "overlay_updated_entries": 1,
                "overlay_added_provenance_refs": 1,
            },
            "promoted_entries": [],
            "already_present": [],
            "skipped_existing": [],
            "existing_provenance_overlay": {
                "updated_entries": [
                    {
                        "manifest_lemma": "чверть",
                        "source_inventory_key": "key-чверть",
                        "added_provenance_refs": 1,
                    }
                ]
            },
            "production_outputs_updated": [],
        }
    )

    assert "`чверть`" in report


def test_apply_rejects_private_provenance_paths() -> None:
    manifest = _manifest([])
    addition = _addition("мама")
    addition["manifest_entry"]["source_provenance"][0]["inventory_path"] = (
        "/Users/example/native-reviewer-lessons/raw.docx"
    )

    with pytest.raises(SourceInventoryError, match=r"private source detail|committed inventory path"):
        apply.apply_promotion_plan(manifest, _plan([addition]))


def test_write_manifest_if_changed_writes_only_after_promotion(tmp_path: Path) -> None:
    manifest = _manifest([_entry("мама")])
    manifest_path = tmp_path / "manifest.json"
    fingerprint_path = tmp_path / "fingerprint.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    result = apply.apply_promotion_plan(manifest, _plan([_addition("риба")]))

    apply.write_manifest_if_changed(
        manifest,
        result,
        manifest_path=manifest_path,
        fingerprint_path=fingerprint_path,
        self_check=lambda _path: 0,
        fingerprint_writer=lambda path: path.write_text('{"fingerprint":"fixture"}\n', encoding="utf-8"),
    )

    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert [entry["lemma"] for entry in written["entries"]] == ["мама", "риба"]
    assert fingerprint_path.exists()
    assert result["production_outputs_updated"] == [
        str(manifest_path),
        str(fingerprint_path),
    ]


def _plan(
    additions: list[dict[str, object]],
    *,
    skipped: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "workflow": planner.WORKFLOW_ID,
        "production_outputs_updated": [],
        "proposed_manifest_additions": additions,
        "skipped_existing": skipped or [],
        "missing_candidates": [],
    }


def _addition(lemma: str, *, source_family: str = "teacher_lesson") -> dict[str, object]:
    return {
        "lemma": lemma,
        "source_inventory_key": f"key-{lemma}",
        "source_inventory": {"source_family": source_family},
        "decision_file": "fixture.yaml",
        "manifest_entry": _entry(lemma),
    }


def _skipped(lemma: str, *, source_family: str = "teacher_lesson") -> dict[str, object]:
    return {
        "lemma": lemma,
        "source_inventory_key": f"key-{lemma}",
        "source_inventory": {"source_family": source_family},
        "decision_file": "fixture.yaml",
        "reason": "already_in_manifest",
    }


def _manifest(entries: list[dict[str, object]]) -> dict[str, object]:
    return {
        "version": "fixture",
        "generated_at": "2026-07-02T00:00:00+00:00",
        "stats": {"lemmas_total": len(entries), "enriched_count": len(entries)},
        "entries": entries,
    }


def _entry(lemma: str, *, source_provenance: list[dict[str, object]] | None = None) -> dict[str, object]:
    return {
        "lemma": lemma,
        "url_slug": lemma,
        "gloss": lemma,
        "pos": "noun",
        "primary_source": "source_inventory_grow",
        "course_usage": [],
        "enrichment": {"meaning": {"definitions": [lemma]}},
        "source_provenance": [_provenance()] if source_provenance is None else source_provenance,
    }


def _provenance(*, locator: str = "explicit vocabulary table row 1") -> dict[str, object]:
    return {
        "source_family": "teacher_lesson",
        "inventory_path": "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-seed.yaml",
        "source_locator": locator,
        "source_id": "private-teacher-lesson-vocabulary-table-1-seed",
    }


def _approved_decision(lemma: str) -> planner.ApprovedDecision:
    inventory_path = "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-seed.yaml"
    locator = "explicit vocabulary table row 14"
    return planner.ApprovedDecision(
        lemma=lemma,
        approved_pos="noun",
        approved_gloss=lemma,
        sense_note="fixture",
        source_inventory={
            "key": planner.decisions.source_inventory_key(
                lemma=lemma,
                inventory_path=inventory_path,
                locator=locator,
            ),
            "path": inventory_path,
            "locator": locator,
            "source_id": "private-teacher-lesson-vocabulary-table-1-seed",
            "source_family": "teacher_lesson",
        },
        evidence_refs=("fixture",),
        review_queue_reasons=(),
        surface_admission={},
        batch_id="fixture",
        batch_label="fixture",
        decision_file="fixture.yaml",
    )
