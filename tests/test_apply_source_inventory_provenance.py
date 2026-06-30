from __future__ import annotations

from scripts.audit.apply_source_inventory_provenance import apply_existing_provenance_overlay
from scripts.audit.plan_source_inventory_promotion import ApprovedDecision, CandidateMatch


def decision(lemma: str, family: str = "ohoiko") -> ApprovedDecision:
    return ApprovedDecision(
        lemma=lemma,
        approved_pos="noun",
        approved_gloss="test gloss",
        sense_note="reviewed",
        source_inventory={
            "key": f"{family}-{lemma}",
            "path": f"data/lexicon/source-inventory/{family}.yaml",
            "locator": "sources[0].headwords[0]",
            "source_id": f"{family}-source",
            "source_family": family,
        },
        evidence_refs=(family,),
        review_queue_reasons=(),
        surface_admission={},
        batch_id="test-batch",
        batch_label="test batch",
        decision_file="decisions.yaml",
    )


def match(lemma: str, family: str = "ohoiko") -> CandidateMatch:
    return CandidateMatch(
        entry={
            "lemma": lemma,
            "source_provenance": [
                {
                    "source_family": family,
                    "source_id": f"{family}-source",
                    "source_locator": "letters[А].key_word",
                    "inventory_path": f"data/lexicon/source-inventory/{family}.yaml",
                    "inventory_locator": "sources[0].headwords[0]",
                }
            ],
        },
        bucket="auto_merge",
        reasons=(),
    )


def test_overlay_adds_source_provenance_to_existing_manifest_entry() -> None:
    manifest = {"entries": [{"lemma": "ананас", "primary_source": "built_vocabulary"}]}
    result = apply_existing_provenance_overlay(
        manifest,
        {"ohoiko-ананас": match("ананас")},
        [decision("ананас")],
        source_family="ohoiko",
    )

    assert result["counts"] == {
        "approved_decisions": 1,
        "filtered_decisions": 1,
        "updated_entries": 1,
        "added_provenance_refs": 1,
        "unchanged_existing": 0,
        "missing_candidates": 0,
        "missing_manifest_entries": 0,
    }
    assert manifest["entries"][0]["primary_source"] == "built_vocabulary"
    assert manifest["entries"][0]["source_provenance"] == match("ананас").entry["source_provenance"]


def test_overlay_is_idempotent_for_existing_provenance() -> None:
    provenance = match("ананас").entry["source_provenance"]
    manifest = {
        "entries": [
            {
                "lemma": "ананас",
                "primary_source": "built_vocabulary",
                "source_provenance": provenance.copy(),
            }
        ]
    }

    result = apply_existing_provenance_overlay(
        manifest,
        {"ohoiko-ананас": match("ананас")},
        [decision("ананас")],
        source_family="ohoiko",
    )

    assert result["counts"]["updated_entries"] == 0
    assert result["counts"]["unchanged_existing"] == 1
    assert manifest["entries"][0]["source_provenance"] == provenance


def test_overlay_source_family_filter_keeps_other_lanes_untouched() -> None:
    manifest = {
        "entries": [
            {"lemma": "ананас", "primary_source": "built_vocabulary"},
            {"lemma": "дошка", "primary_source": "built_vocabulary"},
        ]
    }

    result = apply_existing_provenance_overlay(
        manifest,
        {
            "ohoiko-ананас": match("ананас", "ohoiko"),
            "textbook-дошка": match("дошка", "textbook"),
        },
        [decision("ананас", "ohoiko"), decision("дошка", "textbook")],
        source_family="ohoiko",
    )

    assert result["counts"]["approved_decisions"] == 2
    assert result["counts"]["filtered_decisions"] == 1
    assert result["counts"]["updated_entries"] == 1
    assert manifest["entries"][0]["source_provenance"][0]["source_family"] == "ohoiko"
    assert "source_provenance" not in manifest["entries"][1]
