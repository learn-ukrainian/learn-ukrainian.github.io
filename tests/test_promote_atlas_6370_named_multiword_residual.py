"""Tests for the #6370 residual-27 named multiword-expression admission (#M-4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests  # noqa: F401  # Declares promote_grow_candidates's transitive enrich_manifest HTTP dependency to the CI fastlane.

from scripts.audit import apply_source_inventory_promotion as apply
from scripts.audit import plan_source_inventory_promotion as planner
from scripts.lexicon.promote_atlas_6370_named_multiword_residual import (
    TARGET_ENTRY_TYPES,
    ZABOJATYSJA_LEMMA,
    _build_candidate,
    _scratch_decision_subset,
    build_candidates_and_decisions,
)

MULTIWORD_LEMMAS = sorted(TARGET_ENTRY_TYPES)


def test_target_entry_types_cover_exactly_the_named_eight() -> None:
    assert sorted(
        [
            "виходити заміж",
            "день тижня",
            "картопля фрі",
            "перед тим як",
            "сільське господарство",
            "так само",
            "такий самий",
            "час від часу",
        ]
    ) == MULTIWORD_LEMMAS


def test_multiword_entry_types_are_valid_atlas_types() -> None:
    assert set(TARGET_ENTRY_TYPES.values()) <= {"expression", "multiword_term", "phraseologism"}


def test_chas_vid_chasu_is_phraseologism_and_vyhodyty_zamizh_is_expression() -> None:
    # Only these two of the eight have dictionary idiom/fixed-collocation evidence
    # (see PR description / script module docstring); the rest default to
    # multiword_term per docs/runbooks/word-atlas-entry-model.md's tie-breaker.
    assert TARGET_ENTRY_TYPES["час від часу"] == "phraseologism"
    assert TARGET_ENTRY_TYPES["виходити заміж"] == "expression"
    non_default = {"час від часу", "виходити заміж"}
    for lemma in set(MULTIWORD_LEMMAS) - non_default:
        assert TARGET_ENTRY_TYPES[lemma] == "multiword_term"


@pytest.mark.parametrize("lemma", MULTIWORD_LEMMAS)
def test_build_candidate_from_committed_inventory(lemma: str) -> None:
    from scripts.lexicon.promote_atlas_6370_named_multiword_residual import (
        BIG_INVENTORY,
        LEG_INVENTORY,
    )

    inventory_path = LEG_INVENTORY if lemma == "виходити заміж" else BIG_INVENTORY
    candidate = _build_candidate(lemma, inventory_path, entry_type=TARGET_ENTRY_TYPES[lemma])
    assert candidate["lemma"] == lemma
    assert candidate["entry_type"] == TARGET_ENTRY_TYPES[lemma]
    assert (candidate["gloss"] or "").strip()
    assert candidate["heritage_status"]["vesum_attested"] is True
    assert candidate["heritage_status"]["is_russianism"] is False
    provenance = candidate["source_provenance"]
    assert provenance and all(item.get("inventory_path") for item in provenance)


def test_build_candidate_for_zabojatysja_has_no_explicit_entry_type() -> None:
    from scripts.lexicon.promote_atlas_6370_named_multiword_residual import (
        SPACE_COLLAPSE_INVENTORY,
    )

    candidate = _build_candidate(ZABOJATYSJA_LEMMA, SPACE_COLLAPSE_INVENTORY, entry_type=None)
    assert candidate["lemma"] == ZABOJATYSJA_LEMMA
    assert "entry_type" not in candidate
    assert candidate["pos"] == "verb"


def test_scratch_decision_subset_raises_on_missing_lemma(tmp_path: Path) -> None:
    from scripts.audit.source_inventory_intake import SourceInventoryError
    from scripts.lexicon.promote_atlas_6370_named_multiword_residual import BIG_DECISIONS

    with pytest.raises(SourceInventoryError):
        _scratch_decision_subset(BIG_DECISIONS, {"жоднийтакийлемма"}, tmp_path / "out.yaml")


def test_scratch_decision_subset_keeps_only_requested_rows(tmp_path: Path) -> None:
    from scripts.lexicon.promote_atlas_6370_named_multiword_residual import BIG_DECISIONS

    lemmas = {"день тижня", "так само"}
    out = _scratch_decision_subset(BIG_DECISIONS, lemmas, tmp_path / "out.yaml")
    import yaml

    doc = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert {row["lemma"] for row in doc["decisions"]} == lemmas
    assert doc["source_queue"]["promotion_batch_size"] == len(lemmas)


def test_end_to_end_promotion_plan_matches_all_nine_with_no_missing(tmp_path: Path) -> None:
    """Build the full plan against an empty manifest fixture: 9/9 match, 0 missing."""
    candidates_path, decision_files = build_candidates_and_decisions(tmp_path)
    empty_manifest = tmp_path / "manifest.json"
    empty_manifest.write_text(json.dumps({"entries": []}), encoding="utf-8")

    plan = planner.build_promotion_plan(
        candidates_path=candidates_path,
        decision_files=decision_files,
        manifest_path=empty_manifest,
    )
    counts = plan["counts"]
    assert counts["missing_candidates"] == 0
    assert counts["proposed_additions"] == len(TARGET_ENTRY_TYPES) + 1
    assert counts["skipped_existing"] == 0

    manifest_payload = {"entries": []}
    result = apply.apply_promotion_plan(
        manifest_payload,
        plan,
        expected_additions=len(TARGET_ENTRY_TYPES) + 1,
        expected_skipped_existing=0,
    )
    promoted_lemmas = {row["lemma"] for row in result["promoted_entries"]}
    assert promoted_lemmas == set(TARGET_ENTRY_TYPES) | {ZABOJATYSJA_LEMMA}

    entries_by_lemma = {e["lemma"]: e for e in manifest_payload["entries"]}
    for lemma, expected_type in TARGET_ENTRY_TYPES.items():
        entry = entries_by_lemma[lemma]
        assert entry["entry_type"] == expected_type
        assert " " in entry["lemma"], f"{lemma} must stay a genuine multiword lemma, not collapsed"
    zabojatysja = entries_by_lemma[ZABOJATYSJA_LEMMA]
    assert zabojatysja["pos"] == "verb"
    assert zabojatysja.get("entry_type") is None
