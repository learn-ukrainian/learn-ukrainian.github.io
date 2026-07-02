from __future__ import annotations

from pathlib import Path

import yaml

from scripts.audit import source_inventory_review_decisions as decisions
from scripts.audit.source_inventory_intake import read_source_inventory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRIVATE_TEACHER_INVENTORY = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-seed.yaml"
)
PRIVATE_TEACHER_FIRST_LEDGER = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/"
    "2026-07-02-first-approved-teacher-lesson-ledger-batch.yaml"
)


def test_private_teacher_inventory_is_privacy_safe_review_metadata() -> None:
    records = read_source_inventory(PRIVATE_TEACHER_INVENTORY, project_root=PROJECT_ROOT)

    assert len(records) == 40
    assert {record.source_family for record in records} == {"teacher_lesson"}
    assert {record.extraction_mode for record in records} == {"curated_headword"}
    assert {record.source_id for record in records} == {
        "private-teacher-lesson-vocabulary-table-1-seed"
    }
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
    assert all(
        row["source_inventory"]["source_family"] == "teacher_lesson"
        for row in payload["decisions"]
    )
    assert all("surface_admission" not in row for row in payload["decisions"])

    ledger_text = PRIVATE_TEACHER_FIRST_LEDGER.read_text(encoding="utf-8")
    assert ".docx" not in ledger_text
