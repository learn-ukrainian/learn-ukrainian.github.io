from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from scripts.audit.source_inventory_intake import read_source_inventory
from scripts.audit.source_inventory_review_decisions import source_inventory_key

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BOLSHAKOVA_INVENTORY = (
    PROJECT_ROOT / "data/lexicon/source-inventory/bolshakova-bukvar-keywords.yaml"
)
VASHULENKO_INVENTORY = (
    PROJECT_ROOT / "data/lexicon/source-inventory/vashulenko-grade3-headwords.yaml"
)
VASHULENKO_FAMILY_NUMERALS_INVENTORY = (
    PROJECT_ROOT / "data/lexicon/source-inventory/vashulenko-grade3-family-numerals.yaml"
)
VASHULENKO_MAP = PROJECT_ROOT / "docs/l2-uk-direct/textbook-map.yaml"
VASHULENKO_FAMILY_NUMERALS_LEDGER = (
    PROJECT_ROOT
    / "data/lexicon/source-inventory-review-decisions/2026-07-03-fifth-approved-textbook-ledger-batch.yaml"
)
BOLSHAKOVA_NOTES = (
    PROJECT_ROOT / "docs/l2-uk-direct/textbook-reading-notes/bolshakova-bukvar-mapping.md"
)
TEXTBOOK_INVENTORIES = [
    BOLSHAKOVA_INVENTORY,
    VASHULENKO_INVENTORY,
    VASHULENKO_FAMILY_NUMERALS_INVENTORY,
]

LOCATOR_PART_RE = re.compile(r"^([A-Za-z0-9_]+)(?:\[(\d+)\])?$")


def _records() -> list:
    records = []
    for path in TEXTBOOK_INVENTORIES:
        records.extend(read_source_inventory(path, project_root=PROJECT_ROOT))
    return records


def _resolve_locator(data: Any, locator: str) -> Any:
    current = data
    for part in locator.split("."):
        match = LOCATOR_PART_RE.fullmatch(part)
        assert match, locator
        current = current[match.group(1)]
        if match.group(2) is not None:
            current = current[int(match.group(2))]
    return current


def test_textbook_inventory_counts_and_source_paths_are_stable() -> None:
    records = _records()
    counts = Counter(record.source_id for record in records)

    assert len(records) == 114
    assert counts == {
        "bolshakova-bukvar-2025-part1-keywords": 40,
        "vashulenko-grade3-2020-family-vocabulary": 9,
        "vashulenko-grade3-2020-school-vocabulary": 7,
        "vashulenko-grade3-2020-interior-vocabulary": 17,
        "vashulenko-grade3-2020-marine-vocabulary": 6,
        "vashulenko-grade3-2020-birds-vocabulary": 10,
        "vashulenko-grade3-2020-numerals-vocabulary": 25,
    }
    for record in records:
        assert record.source_family == "textbook"
        assert record.source_path
        assert (PROJECT_ROOT / record.source_path).exists()
        assert record.source_locator
        assert record.context


def test_vashulenko_inventory_locators_resolve_to_tracked_source_map() -> None:
    textbook_map = yaml.safe_load(VASHULENKO_MAP.read_text(encoding="utf-8"))
    records = []
    for path in [VASHULENKO_INVENTORY, VASHULENKO_FAMILY_NUMERALS_INVENTORY]:
        records.extend(read_source_inventory(path, project_root=PROJECT_ROOT))

    for record in records:
        assert record.source_path == str(VASHULENKO_MAP.relative_to(PROJECT_ROOT))
        assert _resolve_locator(textbook_map, record.source_locator) == record.lemma


def test_vashulenko_family_numerals_approval_ledger_matches_inventory() -> None:
    records = {
        (record.lemma, record.source_locator): record
        for record in read_source_inventory(
            VASHULENKO_FAMILY_NUMERALS_INVENTORY,
            project_root=PROJECT_ROOT,
        )
    }
    ledger = yaml.safe_load(VASHULENKO_FAMILY_NUMERALS_LEDGER.read_text(encoding="utf-8"))
    rows = ledger["decisions"]

    assert ledger["production_outputs_updated"] == []
    assert ledger["source_queue"] == {
        "workflow": "source_inventory_publish_review_queue.v1",
        "generated_from_pr": 4202,
        "total_queue_rows": 34,
        "approved_in_queue": 34,
        "promotion_batch_size": 34,
    }
    assert len(rows) == 34
    assert Counter(row["source_inventory"]["source_id"] for row in rows) == {
        "vashulenko-grade3-2020-family-vocabulary": 9,
        "vashulenko-grade3-2020-numerals-vocabulary": 25,
    }

    for row in rows:
        source_inventory = row["source_inventory"]
        record = records[(row["lemma"], source_inventory["locator"])]

        assert row["decision"] == "approve_for_publish"
        assert row["approved_pos"] == record.pos
        assert row["approved_gloss"] == record.gloss
        assert source_inventory["path"] == str(
            VASHULENKO_FAMILY_NUMERALS_INVENTORY.relative_to(PROJECT_ROOT)
        )
        assert source_inventory["source_family"] == "textbook"
        assert source_inventory["source_id"] == record.source_id
        assert source_inventory["key"] == source_inventory_key(
            lemma=row["lemma"],
            inventory_path=source_inventory["path"],
            locator=source_inventory["locator"],
        )


def test_bolshakova_inventory_rows_are_backed_by_tracked_notes() -> None:
    notes = BOLSHAKOVA_NOTES.read_text(encoding="utf-8")
    records = read_source_inventory(BOLSHAKOVA_INVENTORY, project_root=PROJECT_ROOT)

    assert len(records) == 40
    for record in records:
        assert record.source_path == str(BOLSHAKOVA_NOTES.relative_to(PROJECT_ROOT))
        assert record.lemma in notes
