from __future__ import annotations

from scripts.audit.apply_source_inventory_provenance import apply_existing_provenance_overlay
from scripts.audit.plan_source_inventory_promotion import ApprovedDecision, CandidateMatch
from scripts.audit.source_inventory_review_decisions import source_inventory_key

SOURCE_LOCATOR = "letters[А].key_word"


def decision(lemma: str, family: str = "ohoiko") -> ApprovedDecision:
    return ApprovedDecision(
        lemma=lemma,
        approved_pos="noun",
        approved_gloss="test gloss",
        sense_note="reviewed",
        source_inventory={
            "key": source_inventory_key(
                lemma=lemma,
                inventory_path=f"data/lexicon/source-inventory/{family}.yaml",
                locator=SOURCE_LOCATOR,
            ),
            "path": f"data/lexicon/source-inventory/{family}.yaml",
            "locator": SOURCE_LOCATOR,
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
                    "source_locator": SOURCE_LOCATOR,
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
    approved = decision("ананас")
    result = apply_existing_provenance_overlay(
        manifest,
        {approved.source_key: match("ананас")},
        [approved],
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
    approved = decision("ананас")
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
        {approved.source_key: match("ананас")},
        [approved],
        source_family="ohoiko",
    )

    assert result["counts"]["updated_entries"] == 0
    assert result["counts"]["unchanged_existing"] == 1
    assert manifest["entries"][0]["source_provenance"] == provenance


def test_overlay_source_family_filter_keeps_other_lanes_untouched() -> None:
    ohoiko_decision = decision("ананас", "ohoiko")
    textbook_decision = decision("дошка", "textbook")
    manifest = {
        "entries": [
            {"lemma": "ананас", "primary_source": "built_vocabulary"},
            {"lemma": "дошка", "primary_source": "built_vocabulary"},
        ]
    }

    result = apply_existing_provenance_overlay(
        manifest,
        {
            ohoiko_decision.source_key: match("ананас", "ohoiko"),
            textbook_decision.source_key: match("дошка", "textbook"),
        },
        [ohoiko_decision, textbook_decision],
        source_family="ohoiko",
    )

    assert result["counts"]["approved_decisions"] == 2
    assert result["counts"]["filtered_decisions"] == 1
    assert result["counts"]["updated_entries"] == 1
    assert manifest["entries"][0]["source_provenance"][0]["source_family"] == "ohoiko"
    assert "source_provenance" not in manifest["entries"][1]


def test_overlay_only_adds_approved_duplicate_source_ref() -> None:
    approved = decision("ананас", "ohoiko")
    candidate = match("ананас", "ohoiko")
    candidate.entry["source_provenance"].append(
        {
            "source_family": "textbook",
            "source_id": "textbook-source",
            "source_locator": "topic_index.fixture.words[0]",
            "inventory_path": "data/lexicon/source-inventory/textbook.yaml",
            "inventory_locator": "sources[0].headwords[0]",
        }
    )
    manifest = {"entries": [{"lemma": "ананас", "primary_source": "built_vocabulary"}]}

    result = apply_existing_provenance_overlay(
        manifest,
        {approved.source_key: candidate},
        [approved],
        source_family="ohoiko",
    )

    assert result["counts"]["added_provenance_refs"] == 1
    assert manifest["entries"][0]["source_provenance"] == [candidate.entry["source_provenance"][0]]
