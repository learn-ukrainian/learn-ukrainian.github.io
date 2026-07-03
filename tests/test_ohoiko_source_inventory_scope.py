from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import yaml

from scripts.audit import source_inventory_review_decisions as decisions
from scripts.audit.source_inventory_intake import read_source_inventory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ABETKA_DIR = PROJECT_ROOT / "curriculum/l2-uk-direct/a1"
OHOIKO_INVENTORY = PROJECT_ROOT / "data/lexicon/source-inventory/ohoiko-abetka-keywords.yaml"
DECISION_DIR = PROJECT_ROOT / "data/lexicon/source-inventory-review-decisions"
OHOIKO_DECISION_BATCH = (
    DECISION_DIR / "2026-07-03-second-approved-ohoiko-ledger-batch.yaml"
)
ULP_SCHEMA = PROJECT_ROOT / "docs/resources/EXTERNAL_RESOURCES_SCHEMA.md"
ULP_BLOG_DB = PROJECT_ROOT / "docs/resources/ukrainianlessons/blog_db.json"


def _abetka_key_words() -> Counter[tuple[str, str]]:
    rows: Counter[tuple[str, str]] = Counter()
    for path in sorted(ABETKA_DIR.glob("abetka-*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for row in data["letters"]:
            key_word = row.get("key_word")
            if key_word:
                rows[(str(path.relative_to(PROJECT_ROOT)), key_word)] += 1
    return rows


def test_ohoiko_abetka_inventory_covers_all_committed_key_words() -> None:
    records = read_source_inventory(OHOIKO_INVENTORY, project_root=PROJECT_ROOT)
    ohoiko_rows = Counter(
        (record.source_path, record.lemma)
        for record in records
        if record.source_family == "ohoiko"
    )

    assert _abetka_key_words() == ohoiko_rows
    assert sum(ohoiko_rows.values()) == 33


def test_ohoiko_abetka_inventory_has_review_decisions_for_all_rows() -> None:
    records = read_source_inventory(OHOIKO_INVENTORY, project_root=PROJECT_ROOT)
    inventory_rows = Counter(
        (record.source_id, record.lemma)
        for record in records
        if record.source_family == "ohoiko"
    )
    approved_rows: Counter[tuple[str, str]] = Counter()
    for path in sorted(DECISION_DIR.glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        for row in payload.get("decisions", []):
            source_inventory = row.get("source_inventory", {})
            if (
                row.get("decision") == "approve_for_publish"
                and source_inventory.get("source_family") == "ohoiko"
                and source_inventory.get("path")
                == "data/lexicon/source-inventory/ohoiko-abetka-keywords.yaml"
            ):
                approved_rows[(source_inventory["source_id"], row["lemma"])] += 1

    assert inventory_rows == approved_rows
    assert sum(approved_rows.values()) == 33

    summary = decisions.validate_committed_decision_files([OHOIKO_DECISION_BATCH])
    assert summary == {
        "files": 1,
        "rows": 23,
        "decision_counts": {"approve_for_publish": 23},
    }


def test_ulp_resource_policy_remains_link_only_for_lexicon_scope() -> None:
    schema = ULP_SCHEMA.read_text(encoding="utf-8")

    assert "ULP (Ukrainian Lessons Podcast)" in schema
    assert "Inspiration only" in schema
    assert "Never copy content" in schema


def test_ulp_blog_database_is_metadata_not_headword_corpus() -> None:
    payload = json.loads(ULP_BLOG_DB.read_text(encoding="utf-8"))
    articles = payload["articles"]

    assert len(articles) >= 400
    for article in articles:
        assert {"id", "url", "title", "topics"} <= set(article)
        assert not {
            "body",
            "content",
            "headwords",
            "lesson_notes",
            "text",
            "transcript",
            "vocabulary",
        } & set(article)
