from __future__ import annotations

from pathlib import Path

from scripts.audit.source_inventory_intake import read_source_inventory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRIVATE_TEACHER_INVENTORY = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-seed.yaml"
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
