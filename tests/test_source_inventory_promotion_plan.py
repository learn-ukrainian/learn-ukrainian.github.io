from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.audit import plan_source_inventory_promotion as planner
from scripts.audit import source_inventory_review_decisions as decisions
from scripts.audit.source_inventory_intake import SourceInventoryError
from scripts.lexicon.content_lexicon_reconciler import PROJECT_ROOT

FIRST_BATCH = decisions.DEFAULT_DECISION_DIR / "2026-06-29-first-approved-publish-batch.yaml"


def _first_decision() -> dict[str, object]:
    payload = yaml.safe_load(FIRST_BATCH.read_text(encoding="utf-8"))
    return payload["decisions"][0]


def _candidate_payload_for(row: dict[str, object]) -> dict[str, object]:
    source_inventory = row["source_inventory"]
    assert isinstance(source_inventory, dict)
    return {
        "generated_from": "fixture",
        "counts": {"total_delta": 1, "processed": 1, "auto_merge": 0, "needs_review": 1},
        "auto_merge": [],
        "needs_review": [
            {
                "reason": "heritage_status flags russian_shadow",
                "entry": {
                    "lemma": row["lemma"],
                    "pos": "noun",
                    "primary_source": "source_inventory_grow",
                    "source_provenance": [
                        {
                            "source_family": source_inventory["source_family"],
                            "inventory_path": source_inventory["path"],
                            "source_locator": source_inventory["locator"],
                            "source_id": source_inventory["source_id"],
                            "context": "fixture context",
                        }
                    ],
                    "enrichment": {
                        "translation": {"en": [row["approved_gloss"]]},
                        "meaning": {
                            "definitions": [
                                {"text": "dictionary definition must not replace approved gloss"}
                            ]
                        },
                    },
                },
            }
        ],
        "review_only": {"production_outputs_updated": []},
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_plan_maps_approved_decision_to_manifest_addition(tmp_path: Path) -> None:
    decision = _first_decision()
    candidates = tmp_path / "candidates.json"
    payload = _candidate_payload_for(decision)
    payload["needs_review"][0]["entry"]["source_provenance"].append(
        {
            "source_family": "textbook",
            "inventory_path": "data/lexicon/source-inventory/other.yaml",
            "source_locator": "topic_index.other.words[0]",
            "source_id": "unapproved-duplicate-source",
            "context": "fixture duplicate context",
        }
    )
    _write_json(candidates, payload)

    plan = planner.build_promotion_plan(
        candidates_path=candidates,
        decision_files=[FIRST_BATCH],
    )

    assert plan["production_outputs_updated"] == []
    assert plan["counts"]["approved_decisions"] == 20
    assert plan["counts"]["proposed_additions"] == 1
    assert plan["counts"]["missing_candidates"] == 19
    addition = plan["proposed_manifest_additions"][0]
    assert addition["lemma"] == decision["lemma"]
    assert addition["source_inventory_key"] == decision["source_inventory"]["key"]
    assert addition["approved_pos"] == decision["approved_pos"]
    assert addition["approved_gloss"] == decision["approved_gloss"]
    assert addition["candidate_bucket"] == "needs_review"
    assert addition["manifest_entry"]["lemma"] == decision["lemma"]
    assert addition["manifest_entry"]["pos"] == decision["approved_pos"]
    assert addition["manifest_entry"]["gloss"] == decision["approved_gloss"]
    assert addition["manifest_entry"]["primary_source"] == "source_inventory_grow"
    assert addition["manifest_entry"]["course_usage"] == []
    assert len(addition["manifest_entry"]["source_provenance"]) == 1
    assert addition["manifest_entry"]["source_provenance"][0]["source_id"] == (
        decision["source_inventory"]["source_id"]
    )


def test_plan_skips_existing_lemmas_when_manifest_supplied(tmp_path: Path) -> None:
    decision = _first_decision()
    candidates = tmp_path / "candidates.json"
    manifest = tmp_path / "manifest.json"
    _write_json(candidates, _candidate_payload_for(decision))
    _write_json(manifest, {"entries": [{"lemma": decision["lemma"]}]})

    plan = planner.build_promotion_plan(
        candidates_path=candidates,
        decision_files=[FIRST_BATCH],
        manifest_path=manifest,
    )

    assert plan["counts"]["proposed_additions"] == 0
    assert plan["counts"]["skipped_existing"] == 1
    assert plan["skipped_existing"][0]["reason"] == "already_in_manifest"


def test_candidate_matching_uses_stable_source_key_not_queue_id(tmp_path: Path) -> None:
    decision = _first_decision()
    candidates = tmp_path / "candidates.json"
    payload = _candidate_payload_for(decision)
    payload["needs_review"][0]["entry"]["queue_id"] = "source-inventory-publish-review-9999"
    _write_json(candidates, payload)

    plan = planner.build_promotion_plan(candidates_path=candidates, decision_files=[FIRST_BATCH])

    assert plan["counts"]["proposed_additions"] == 1
    assert plan["proposed_manifest_additions"][0]["source_inventory_key"] == (
        decision["source_inventory"]["key"]
    )


@pytest.mark.parametrize(
    "bad_path",
    [
        PROJECT_ROOT / "site/src/data/source-inventory-approved-promotion-plan.json",
        PROJECT_ROOT / "site/public/lexicon/source-inventory-approved-promotion-plan.json",
        PROJECT_ROOT / "data/telemetry/source-inventory-approved-promotion-plan.json",
        PROJECT_ROOT / "curriculum/l2-uk-en/a1/status/source-inventory-approved-promotion-plan.json",
        PROJECT_ROOT / "curriculum/l2-uk-en/a1/audit/source-inventory-approved-promotion-plan.md",
        PROJECT_ROOT / "curriculum/l2-uk-en/a1/review/source-inventory-approved-promotion-plan.md",
    ],
)
def test_plan_output_rejects_repository_paths(bad_path: Path) -> None:
    with pytest.raises(SourceInventoryError):
        planner.resolve_ephemeral_plan_output_path(bad_path)


def test_write_plan_and_report_stay_ephemeral(tmp_path: Path) -> None:
    plan = {
        "workflow": planner.WORKFLOW_ID,
        "policy": "fixture",
        "production_outputs_updated": [],
        "counts": {
            "approved_decisions": 0,
            "proposed_additions": 0,
            "skipped_existing": 0,
            "missing_candidates": 0,
        },
        "proposed_manifest_additions": [],
        "skipped_existing": [],
        "missing_candidates": [],
    }

    plan_path = planner.write_plan(plan, tmp_path / "plan.json")
    report_path = planner.write_report(plan, tmp_path / "plan.md")

    assert json.loads(plan_path.read_text(encoding="utf-8"))["production_outputs_updated"] == []
    assert "Source Inventory Approved Promotion Plan" in report_path.read_text(encoding="utf-8")



def test_plan_carries_surface_admission_to_manifest_entry(tmp_path: Path) -> None:
    payload = yaml.safe_load(FIRST_BATCH.read_text(encoding="utf-8"))
    decision = payload["decisions"][0]
    payload["decisions"] = [decision]
    decision["surface_admission"] = {"daily": False, "practice": True, "cloze": False}
    decision_path = tmp_path / "decision.yaml"
    decision_path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    candidates = tmp_path / "candidates.json"
    _write_json(candidates, _candidate_payload_for(decision))

    plan = planner.build_promotion_plan(candidates_path=candidates, decision_files=[decision_path])
    addition = plan["proposed_manifest_additions"][0]

    assert addition["surface_admission"] == {"daily": False, "practice": True, "cloze": False}
    assert addition["manifest_entry"]["surface_admission"] == {
        "daily": False,
        "practice": True,
        "cloze": False,
    }



def test_plan_drops_candidate_surface_admission_without_decision_opt_in(tmp_path: Path) -> None:
    decision = _first_decision()
    candidates_payload = _candidate_payload_for(decision)
    candidates_payload["needs_review"][0]["entry"]["surface_admission"] = {
        "daily": True,
        "practice": True,
        "cloze": True,
    }
    candidates = tmp_path / "candidates.json"
    _write_json(candidates, candidates_payload)

    plan = planner.build_promotion_plan(candidates_path=candidates, decision_files=[FIRST_BATCH])
    addition = plan["proposed_manifest_additions"][0]

    assert addition["surface_admission"] == {}
    assert "surface_admission" not in addition["manifest_entry"]
