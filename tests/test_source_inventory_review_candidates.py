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
    assert "publish_review_queue" not in payload
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


def test_publish_review_queue_includes_auto_merge_and_grow_review_rows() -> None:
    payload = {
        "auto_merge": [
            {
                "lemma": "кіт",
                "pos": "noun",
                "gloss": "cat",
                "source_provenance": [
                    {
                        "source_family": "fixture",
                        "source_id": "source-a",
                        "source_locator": "row 1",
                    }
                ],
            },
            {
                "lemma": "жабка",
                "pos": "noun",
                "source_provenance": [
                    {
                        "source_family": "fixture",
                        "source_id": "source-a",
                        "source_locator": "row 2",
                    }
                ],
            },
        ],
        "needs_review": [
            {
                "entry": {
                    "lemma": "сумнів",
                    "pos": "noun",
                    "gloss": "doubt",
                    "source_provenance": [
                        {
                            "source_family": "textbook",
                            "source_id": "source-b",
                            "source_locator": "map 3",
                        }
                    ],
                },
                "reason": "missing dictionary definition",
            }
        ],
    }

    queue = review.build_publish_review_queue(payload)

    assert queue["workflow"] == review.PUBLISH_REVIEW_QUEUE_WORKFLOW_ID
    assert queue["counts"]["needs_publish_review"] == 2
    assert queue["needs_publish_review_reasons"] == {
        "grow_needs_review:missing dictionary definition": 1,
        "missing_english_anchor": 1,
    }
    assert [row["queue_id"] for row in queue["queue"]] == [
        "source-inventory-publish-review-0001",
        "source-inventory-publish-review-0002",
    ]
    rows_by_lemma = {row["lemma"]: row for row in queue["queue"]}
    assert "кіт" not in rows_by_lemma
    assert rows_by_lemma["жабка"]["bucket"] == "auto_merge"
    assert rows_by_lemma["жабка"]["reasons"] == ["missing_english_anchor"]
    assert rows_by_lemma["жабка"]["source_references"] == [
        "fixture / source-a / row 2"
    ]
    assert rows_by_lemma["сумнів"]["bucket"] == "needs_review"
    assert rows_by_lemma["сумнів"]["reasons"] == [
        "grow_needs_review:missing dictionary definition"
    ]


def test_publish_review_queue_ids_are_stable_for_duplicate_headwords() -> None:
    payload = {
        "auto_merge": [
            {
                "lemma": "жабка",
                "pos": "noun",
                "source_provenance": [
                    {
                        "source_family": "fixture",
                        "source_id": "source-z",
                        "source_locator": "row 2",
                    }
                ],
            },
            {
                "lemma": "жабка",
                "pos": "noun",
                "source_provenance": [
                    {
                        "source_family": "fixture",
                        "source_id": "source-a",
                        "source_locator": "row 1",
                    }
                ],
            },
        ],
        "needs_review": [],
    }

    queue = review.build_publish_review_queue(payload)

    assert [
        (row["queue_id"], row["source_references"])
        for row in queue["queue"]
    ] == [
        (
            "source-inventory-publish-review-0001",
            ["fixture / source-a / row 1"],
        ),
        (
            "source-inventory-publish-review-0002",
            ["fixture / source-z / row 2"],
        ),
    ]


def test_publish_review_queue_report_renders_markdown_rows() -> None:
    payload = {
        "auto_merge": [
            {
                "lemma": "жабка",
                "pos": "noun",
                "source_provenance": [
                    {
                        "source_family": "fixture",
                        "source_id": "source-a",
                        "source_locator": "row 2",
                    }
                ],
            }
        ],
        "needs_review": [],
    }

    report = review.format_publish_review_queue_report(payload)

    assert "# Source Inventory Publish Review Queue" in report
    assert "- needs_publish_review: 1" in report
    assert "`missing_english_anchor`: 1" in report
    assert (
        "| source-inventory-publish-review-0001 | жабка | noun | "
        "auto_merge | no | missing_english_anchor | "
        "fixture / source-a / row 2 |  |  |"
    ) in report


def test_publish_review_queue_report_handles_empty_queue() -> None:
    payload = {
        "auto_merge": [
            {
                "lemma": "кіт",
                "pos": "noun",
                "gloss": "cat",
                "source_provenance": [{"source_family": "fixture"}],
            }
        ],
        "needs_review": [],
    }

    report = review.format_publish_review_queue_report(payload)
    summary = review.format_publish_review_queue_summary(payload)

    assert "- needs_publish_review: 0" in report
    assert "- no rows" in report
    assert "publish_review_queue_rows: 0" in summary


def test_publish_review_queue_report_writes_only_ephemeral_paths(
    tmp_path: Path,
) -> None:
    payload = {
        "auto_merge": [
            {
                "lemma": "жабка",
                "pos": "noun",
                "source_provenance": [{"source_family": "fixture"}],
            }
        ],
        "needs_review": [],
    }
    out = tmp_path / "queue.md"

    output_path = review.write_publish_review_queue_report(payload, out)

    assert output_path == out.resolve()
    assert "# Source Inventory Publish Review Queue" in out.read_text(encoding="utf-8")


def test_publish_review_queue_report_rejects_repository_paths() -> None:
    with pytest.raises(SourceInventoryError, match="outside the repository"):
        review.resolve_ephemeral_review_output_path(
            PROJECT_ROOT / "docs/reports/source-inventory-review-queue.md"
        )


def test_publish_review_queue_report_rejects_traversal_into_repository() -> None:
    traversal_path = (
        PROJECT_ROOT
        / ".."
        / PROJECT_ROOT.name
        / "docs/reports/source-inventory-review-queue.md"
    )

    with pytest.raises(SourceInventoryError, match="outside the repository"):
        review.resolve_ephemeral_review_output_path(traversal_path)


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
