from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "site/src/data/lexicon-sentence-inventory.json"
DAILY_POOL = ROOT / "site/src/data/lexicon-daily-pool.json"


def test_daily_pool_examples_are_inventory_backed_and_cover_the_ship_floor() -> None:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    pool = json.loads(DAILY_POOL.read_text(encoding="utf-8"))

    assert inventory["schema"] == "atlas-sentence-inventory"
    rows = inventory["rows"]
    assert rows
    assert all(row["lemmaId"] and row["uses"] == ["example"] and row["provenance"] and row["license"] for row in rows)
    assert all(row["provenance"]["source"] in {"textbook", "ulp"} for row in rows)

    examples = [row for row in pool if row.get("example")]
    assert len(examples) / len(pool) >= 0.40
    assert all(row.get("exampleProvenance") and row.get("exampleLicense") for row in examples)
    assert all("clozemaster" not in json.dumps(row, ensure_ascii=False).casefold() for row in rows)


def test_ulp_inventory_rows_have_only_the_safe_provenance_shape() -> None:
    rows = json.loads(INVENTORY.read_text(encoding="utf-8"))["rows"]
    for row in rows:
        if row["provenance"]["source"] == "ulp":
            assert set(row["provenance"]) == {"source", "label"}
