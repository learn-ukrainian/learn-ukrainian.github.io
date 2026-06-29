from __future__ import annotations

import json
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import generate_source_inventory_review_candidates as review
from scripts.audit.source_inventory_intake import SourceInventoryError
from scripts.lexicon.content_lexicon_reconciler import PROJECT_ROOT

POS_BALANCED_LEMMAS = {
    "школа",
    "море",
    "великий",
    "гарний",
    "один",
    "два",
    "ніхто",
    "себе",
    "робити",
    "читати",
    "швидко",
    "добре",
    "щодо",
    "через",
    "і",
    "але",
    "не",
    "хіба",
    "ой",
    "ура",
}
POS_BALANCED_POS = {
    "noun",
    "adjective",
    "numeral",
    "pronoun",
    "verb",
    "adverb",
    "preposition",
    "conjunction",
    "particle",
    "interjection",
}


def test_review_candidates_use_committed_inventories_and_keep_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = tmp_path / "atlas-source-inventory-review-candidates.json"

    monkeypatch.setattr(review.grow, "_source_connection", lambda path: nullcontext(object()))
    monkeypatch.setattr(review.grow, "_preserve_wiki_reference_cache", lambda: nullcontext())
    monkeypatch.setattr(review.grow.enrich_manifest, "_load_kaikki_lookup", lambda: {})
    monkeypatch.setattr(review.grow.enrich_manifest, "_sum11_has_flag_columns", lambda conn: False)
    monkeypatch.setattr(
        review.grow,
        "build_skeleton_entry",
        lambda lemma: {"lemma": lemma},
    )

    def fake_enrich_entry(
        entry: dict[str, Any],
        conn: object,
        kaikki_lookup: dict[str, Any],
        *,
        has_sum11_flags: bool,
    ) -> bool:
        entry["heritage_status"] = {
            "classification": "standard",
            "is_russianism": False,
            "russian_shadow": False,
        }
        entry["enrichment"] = {
            "meaning": {"definitions": [f"{entry['lemma']} fixture definition"]}
        }
        return True

    monkeypatch.setattr(review.grow.enrich_manifest, "enrich_entry", fake_enrich_entry)

    payload = review.generate_review_candidates(out=out)

    assert payload["counts"] == {
        "total_delta": len(POS_BALANCED_LEMMAS),
        "processed": len(POS_BALANCED_LEMMAS),
        "auto_merge": len(POS_BALANCED_LEMMAS),
        "needs_review": 0,
    }
    assert payload["review_only"] == {
        "workflow": review.WORKFLOW_ID,
        "source_inventory_paths": [
            "data/lexicon/source-inventory/pos-balanced-grammar-sample.yaml",
        ],
        "candidate_output": str(out.resolve()),
        "production_outputs_updated": [],
    }
    assert not Path(payload["review_only"]["candidate_output"]).is_relative_to(
        review.LIVE_ATLAS_OUTPUT_DIR
    )

    entries = payload["auto_merge"]
    assert {entry["lemma"] for entry in entries} == POS_BALANCED_LEMMAS
    assert {entry["pos"] for entry in entries} == POS_BALANCED_POS
    for entry in entries:
        assert entry["source_provenance"]
        for provenance in entry["source_provenance"]:
            assert provenance["inventory_path"].startswith(
                "data/lexicon/source-inventory/"
            )
            assert provenance["source_id"]
            assert provenance["source_title"]


def test_review_workflow_validates_source_provenance_in_needs_review() -> None:
    payload = {
        "auto_merge": [{"lemma": "риба", "source_provenance": [{"source_id": "ok"}]}],
        "needs_review": [
            {
                "entry": {
                    "lemma": "кіт",
                    "source_provenance": [{"source_id": "ok"}],
                },
                "reason": "fixture",
            }
        ],
    }

    review.validate_source_provenance(payload)


def test_review_workflow_rejects_missing_source_provenance_before_final_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = tmp_path / "atlas-source-inventory-review-candidates.json"

    def fake_generate_candidates(
        *,
        inventory_paths: tuple[Path, ...],
        limit: int | None,
        out: Path,
    ) -> dict[str, Any]:
        payload = {
            "counts": {
                "total_delta": 1,
                "processed": 1,
                "auto_merge": 1,
                "needs_review": 0,
            },
            "limit": limit,
            "auto_merge": [{"lemma": "кіт", "source_provenance": []}],
            "needs_review": [],
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    monkeypatch.setattr(review.grow, "generate_candidates", fake_generate_candidates)

    with pytest.raises(SourceInventoryError, match="missing source_provenance: кіт"):
        review.generate_review_candidates(out=out)

    assert not out.exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_review_workflow_defaults_outside_repo() -> None:
    resolved = review.resolve_review_output_path(review.DEFAULT_OUT)

    assert resolved == review.DEFAULT_OUT.resolve()
    assert not resolved.is_relative_to(PROJECT_ROOT)
    assert all(path.exists() for path in review.COMMITTED_SOURCE_INVENTORIES)


@pytest.mark.parametrize("production_output", review.LIVE_ATLAS_OUTPUTS)
def test_review_workflow_rejects_live_atlas_outputs(production_output: Path) -> None:
    with pytest.raises(SourceInventoryError, match="review-only source candidates"):
        review.resolve_review_output_path(production_output)


def test_review_workflow_rejects_live_atlas_output_directory() -> None:
    with pytest.raises(SourceInventoryError, match="site/src/data"):
        review.resolve_review_output_path(
            PROJECT_ROOT / "site/src/data/source-inventory-review-candidates.json"
        )
