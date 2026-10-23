from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.audit import source_inventory_review_decisions as decisions
from scripts.audit.source_inventory_intake import read_source_inventory
from scripts.lexicon.build_teacher_deck_cloze import (
    EXCLUDED_TEACHER_CLOZE_IDS,
    exclude_private_cloze_cards,
    public_teacher_lemmas,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRUBBED_PERSONAL_NAME_MARKERS = ("alona", "альона", "алёна")
PUBLIC_TEACHER_CLOZE_ASSET = PROJECT_ROOT / "site/src/data/lexicon-teacher-cloze.json"
PRIVATE_TEACHER_INVENTORY = (
    PROJECT_ROOT / "registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-seed.yaml"
)
PRIVATE_TEACHER_ROWS_99_118_INVENTORY = (
    PROJECT_ROOT / "registry/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-99-118.yaml"
)
PRIVATE_TEACHER_FIRST_LEDGER = (
    PROJECT_ROOT / "registry/lexicon/source-inventory-review-decisions/"
    "2026-07-02-first-approved-teacher-lesson-ledger-batch.yaml"
)
PRIVATE_TEACHER_SECOND_LEDGER = (
    PROJECT_ROOT / "registry/lexicon/source-inventory-review-decisions/"
    "2026-07-03-second-approved-teacher-lesson-ledger-batch.yaml"
)
def test_private_teacher_inventory_is_privacy_safe_review_metadata() -> None:
    records = read_source_inventory(PRIVATE_TEACHER_INVENTORY, project_root=PROJECT_ROOT)

    assert len(records) == 40
    assert {record.source_family for record in records} == {"teacher_lesson"}
    assert {record.extraction_mode for record in records} == {"curated_headword"}
    assert {record.source_id for record in records} == {"private-teacher-lesson-vocabulary-table-1-seed"}
    assert all(record.source_path is None for record in records)
    assert all(record.source_url is None for record in records)
    assert all(record.source_title for record in records)
    assert all(record.source_locator for record in records)
    assert all(record.context for record in records)
    assert all(record.pos for record in records)
    assert all(record.gloss for record in records)

    inventory_text = PRIVATE_TEACHER_INVENTORY.read_text(encoding="utf-8")
    assert ".docx" not in inventory_text


def test_private_teacher_inventory_uses_clean_headwords_not_raw_table_cells() -> None:
    records = read_source_inventory(PRIVATE_TEACHER_INVENTORY, project_root=PROJECT_ROOT)

    assert all("," not in record.lemma for record in records)
    assert all("/" not in record.lemma for record in records)
    assert "тарган" in {record.lemma for record in records}
    assert "вийти з ладу" in {record.lemma for record in records}


def test_private_teacher_rows_99_118_inventory_is_pending_review_metadata() -> None:
    records = read_source_inventory(
        PRIVATE_TEACHER_ROWS_99_118_INVENTORY,
        project_root=PROJECT_ROOT,
    )

    assert len(records) == 20
    assert {record.source_family for record in records} == {"teacher_lesson"}
    assert {record.extraction_mode for record in records} == {"curated_headword"}
    assert {record.source_id for record in records} == {"private-teacher-lesson-vocabulary-table-1-rows-99-118"}
    assert all(record.source_path is None for record in records)
    assert all(record.source_url is None for record in records)
    assert all(record.source_title for record in records)
    assert all(record.source_locator for record in records)
    assert all(record.context for record in records)
    assert all(record.pos for record in records)
    assert all(record.gloss for record in records)
    assert "постукати" in {record.lemma for record in records}
    assert "ЗМІ" in {record.lemma for record in records}
    assert "вони мені остогидли" in {record.lemma for record in records}
    assert "втручатися" in {record.lemma for record in records}
    assert all("," not in record.lemma for record in records)
    assert all("/" not in record.lemma for record in records)
    assert all("(" not in record.lemma and ")" not in record.lemma for record in records)
    assert all("surface_admission" not in record.provenance_payload() for record in records)

    inventory_text = PRIVATE_TEACHER_ROWS_99_118_INVENTORY.read_text(encoding="utf-8")
    assert ".docx" not in inventory_text
    assert all(marker not in inventory_text.casefold() for marker in SCRUBBED_PERSONAL_NAME_MARKERS)
    assert "native-reviewer-lessons" not in inventory_text


def test_private_teacher_first_decision_ledger_stays_review_only() -> None:
    summary = decisions.validate_committed_decision_files([PRIVATE_TEACHER_FIRST_LEDGER])
    payload = yaml.safe_load(PRIVATE_TEACHER_FIRST_LEDGER.read_text(encoding="utf-8"))

    assert summary == {
        "files": 1,
        "rows": 20,
        "decision_counts": {"approve_for_publish": 20},
    }
    assert payload["source_queue"]["promotion_batch_size"] == 20
    assert payload["production_outputs_updated"] == []
    assert all(row["source_inventory"]["source_family"] == "teacher_lesson" for row in payload["decisions"])
    assert all("surface_admission" not in row for row in payload["decisions"])

    ledger_text = PRIVATE_TEACHER_FIRST_LEDGER.read_text(encoding="utf-8")
    assert ".docx" not in ledger_text


def test_private_teacher_decision_ledgers_cover_seed_without_live_surfaces() -> None:
    records = read_source_inventory(PRIVATE_TEACHER_INVENTORY, project_root=PROJECT_ROOT)
    inventory_keys = {
        decisions.source_inventory_key(
            lemma=record.lemma,
            inventory_path="data/lexicon/source-inventory/private-teacher-lesson-vocabulary-seed.yaml",
            locator=record.source_locator,
        )
        for record in records
    }

    ledger_keys = set()
    for ledger in (PRIVATE_TEACHER_FIRST_LEDGER, PRIVATE_TEACHER_SECOND_LEDGER):
        payload = yaml.safe_load(ledger.read_text(encoding="utf-8"))
        ledger_keys.update(row["source_inventory"]["key"] for row in payload["decisions"])

    assert ledger_keys == inventory_keys


def test_public_teacher_cloze_build_scrubs_private_cards_and_distractors() -> None:
    cards = [
        {"clozeId": "teacher_cloze_57", "lemma": "private"},
        {"clozeId": "teacher_cloze_581", "lemma": "private"},
        {"clozeId": "teacher_cloze_1521", "lemma": "private"},
        {
            "clozeId": "teacher_cloze_safe_but_private_distractor",
            "lemma": "слово",
            "options": [{"lemmaId": "альона", "label": "Альона"}],
        },
        {"clozeId": "teacher_cloze_safe", "lemma": "слово"},
    ]

    assert exclude_private_cloze_cards(cards) == [
        {"clozeId": "teacher_cloze_safe", "lemma": "слово"},
    ]


def test_public_teacher_cloze_build_excludes_private_lemmas_before_distractors() -> None:
    assert public_teacher_lemmas([{"lemma": "альона"}, {"lemma": "місто"}]) == ["місто"]


@pytest.mark.needs_sparse_tree("site/src/data")
def test_public_teacher_cloze_build_filters_residual_cards_in_committed_asset() -> None:
    asset_text = PUBLIC_TEACHER_CLOZE_ASSET.read_text(encoding="utf-8")
    payload = json.loads(asset_text)
    filtered_cards = exclude_private_cloze_cards(payload["cloze"])
    filtered_text = json.dumps(filtered_cards, ensure_ascii=False)
    cloze_ids = {card["clozeId"] for card in filtered_cards}

    assert cloze_ids.isdisjoint(EXCLUDED_TEACHER_CLOZE_IDS)
    assert all(marker not in filtered_text.casefold() for marker in SCRUBBED_PERSONAL_NAME_MARKERS)
