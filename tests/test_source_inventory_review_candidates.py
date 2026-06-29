from __future__ import annotations

import json
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest

from scripts.audit import generate_source_inventory_review_candidates as review
from scripts.audit.source_inventory_intake import (
    SourceInventoryError,
    read_source_inventories,
    source_inventory_candidates,
)
from scripts.lexicon.content_lexicon_reconciler import PROJECT_ROOT

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
REQUIRED_REVIEW_SOURCE_FAMILIES = {"curriculum", "ohoiko", "textbook"}


def test_review_candidates_use_committed_inventories_and_keep_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    out = tmp_path / "atlas-source-inventory-review-candidates.json"
    records = read_source_inventories(
        review.COMMITTED_SOURCE_INVENTORIES,
        project_root=PROJECT_ROOT,
    )
    expected_candidates = source_inventory_candidates(records)
    expected_inventory_paths = [
        str(path.relative_to(PROJECT_ROOT)) for path in review.COMMITTED_SOURCE_INVENTORIES
    ]
    expected_lemmas = {candidate.lemma for candidate in expected_candidates}
    expected_pos = {candidate.pos for candidate in expected_candidates if candidate.pos}

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
        "total_delta": len(expected_candidates),
        "processed": len(expected_candidates),
        "auto_merge": len(expected_candidates),
        "needs_review": 0,
    }
    assert payload["review_only"] == {
        "workflow": review.WORKFLOW_ID,
        "source_inventory_paths": expected_inventory_paths,
        "candidate_output": str(out.resolve()),
        "production_outputs_updated": [],
    }
    assert payload["review_triage"]["workflow"] == review.TRIAGE_WORKFLOW_ID
    assert payload["review_triage"]["counts"]["total_candidates"] == len(expected_candidates)
    assert payload["review_triage"]["counts"]["grow_auto_merge"] == len(expected_candidates)
    assert not Path(payload["review_only"]["candidate_output"]).is_relative_to(
        review.LIVE_ATLAS_OUTPUT_DIR
    )

    entries = payload["auto_merge"]
    assert {entry["lemma"] for entry in entries} == expected_lemmas
    assert {entry["pos"] for entry in entries} == expected_pos
    assert expected_pos >= POS_BALANCED_POS
    entries_by_lemma = {entry["lemma"]: entry for entry in entries}
    assert entries_by_lemma["Україна"]["gloss"] == "Ukraine"

    provenance_families = set()
    provenance_inventory_paths = set()
    for entry in entries:
        assert entry["source_provenance"]
        for provenance in entry["source_provenance"]:
            assert provenance["inventory_path"].startswith(
                "data/lexicon/source-inventory/"
            )
            assert provenance["source_id"]
            assert provenance["source_title"]
            provenance_families.add(provenance["source_family"])
            provenance_inventory_paths.add(provenance["inventory_path"])
    assert provenance_families >= REQUIRED_REVIEW_SOURCE_FAMILIES
    assert provenance_inventory_paths >= set(expected_inventory_paths)


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


def test_review_triage_is_stricter_than_grow_auto_merge() -> None:
    payload = {
        "auto_merge": [
            {
                "lemma": "кіт",
                "pos": "noun",
                "gloss": "cat",
                "source_provenance": [{"source_family": "fixture"}],
            },
            {
                "lemma": "жабка",
                "pos": "noun",
                "source_provenance": [{"source_family": "fixture"}],
            },
            {
                "lemma": "безпос",
                "gloss": "has gloss",
                "source_provenance": [{"source_family": "fixture"}],
            },
        ],
        "needs_review": [
            {
                "entry": {
                    "lemma": "сумнів",
                    "pos": "noun",
                    "gloss": "doubt",
                    "source_provenance": [{"source_family": "fixture"}],
                },
                "reason": "missing dictionary definition",
            }
        ],
    }

    triage = review.build_review_triage(payload)

    assert triage["counts"] == {
        "total_candidates": 4,
        "grow_auto_merge": 3,
        "grow_needs_review": 1,
        "publish_ready": 1,
        "needs_publish_review": 3,
    }
    assert triage["needs_publish_review_reasons"] == {
        "grow_needs_review:missing dictionary definition": 1,
        "missing_english_anchor": 1,
        "missing_pos": 1,
    }
    assert triage["by_source_family"] == {"fixture": 4}
    assert triage["by_pos"] == {"noun": 3, "unknown": 1}
    assert triage["publish_ready_sample"][0]["lemma"] == "кіт"
    assert triage["needs_publish_review_sample"][0]["reasons"] == ["missing_pos"]


def test_review_triage_accepts_enrichment_translation_anchor() -> None:
    entry = {
        "lemma": "переклад",
        "pos": "noun",
        "source_provenance": [{"source_family": "fixture"}],
        "enrichment": {"translation": {"en": ["translation"]}},
    }

    assert review.publish_review_reasons(entry) == []


def test_review_triage_report_includes_publish_counts() -> None:
    payload = {
        "review_triage": {
            "counts": {"publish_ready": 2, "needs_publish_review": 1},
            "needs_publish_review_reasons": {"missing_english_anchor": 1},
        }
    }

    report = review.format_triage_report(payload)

    assert "publish_ready: 2" in report
    assert "needs_publish_review: 1" in report
    assert "- missing_english_anchor: 1" in report


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
    records = read_source_inventories(
        review.COMMITTED_SOURCE_INVENTORIES,
        project_root=PROJECT_ROOT,
    )
    assert source_inventory_candidates(records)


@pytest.mark.parametrize("production_output", review.LIVE_ATLAS_OUTPUTS)
def test_review_workflow_rejects_live_atlas_outputs(production_output: Path) -> None:
    with pytest.raises(SourceInventoryError, match="review-only source candidates"):
        review.resolve_review_output_path(production_output)


def test_review_workflow_rejects_live_atlas_output_directory() -> None:
    with pytest.raises(SourceInventoryError, match="site/src/data"):
        review.resolve_review_output_path(
            PROJECT_ROOT / "site/src/data/source-inventory-review-candidates.json"
        )


@pytest.mark.parametrize(
    "static_output",
    [
        PROJECT_ROOT / "site/public/lexicon/browse/а.json",
        PROJECT_ROOT / "site/public/lexicon/daily-pool.json",
        PROJECT_ROOT / "site/public/lexicon/practice-lexemes.A1.json",
        PROJECT_ROOT / "site/public/lexicon/cloze-lexemes.A1.json",
    ],
)
def test_review_workflow_rejects_static_lexicon_outputs(static_output: Path) -> None:
    with pytest.raises(SourceInventoryError, match="site/public/lexicon"):
        review.resolve_review_output_path(static_output)
