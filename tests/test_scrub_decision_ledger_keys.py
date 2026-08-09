from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.audit.lint_opsec_leaks import _PERSONAL_IDENTIFIER_PATTERNS
from scripts.audit.scrub_decision_ledger_keys import (
    DEFAULT_SCRUBBED_PATH,
    DEFAULT_SOURCE_LEDGER,
    migrate_ledger_to_shards,
    scrub_decision_row,
)
from scripts.audit.source_inventory_review_decisions import (
    source_inventory_key,
    validate_decision_file,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def migrated_shards(tmp_path_factory: pytest.TempPathFactory) -> list[Path]:
    tmp_dir = tmp_path_factory.mktemp("scrubbed_shards")
    return migrate_ledger_to_shards(
        source_ledger_path=DEFAULT_SOURCE_LEDGER,
        output_dir=tmp_dir,
        num_shards=10,
        scrubbed_inventory_path=DEFAULT_SCRUBBED_PATH,
    )


def test_scrubbed_key_formula() -> None:
    sample_row = {
        "lemma": "був",
        "decision": "approve_for_publish",
        "approved_pos": "noun",
        "approved_gloss": "був",
        "sense_note": "private teacher-lesson full-source intake (Alona document)",
        "source_inventory": {
            "key": "1c7aef76af3ca86a",
            "path": "data/lexicon/source-inventory/oneshot/private-teacher-lesson-vocabulary-alona-full.yaml",
            "locator": "private source unit 1000 paragraph 1",
            "source_id": "private-teacher-lesson-full-source",
            "source_family": "teacher_lesson",
        },
        "evidence_refs": ["private teacher-lesson document (Krisztian Ukr.docx)"],
        "surface_admission": {"daily": False, "practice": True, "cloze": False},
    }

    scrubbed = scrub_decision_row(sample_row, DEFAULT_SCRUBBED_PATH)
    expected_key = source_inventory_key(
        lemma="був",
        inventory_path=DEFAULT_SCRUBBED_PATH,
        locator="private source unit 1000 paragraph 1",
    )

    assert scrubbed["source_inventory"]["path"] == DEFAULT_SCRUBBED_PATH
    assert scrubbed["source_inventory"]["key"] == expected_key
    assert scrubbed["sense_note"] == "private teacher-lesson full-source intake (full document)"
    assert scrubbed["lemma"] == sample_row["lemma"]
    assert scrubbed["decision"] == sample_row["decision"]
    assert scrubbed["evidence_refs"] == sample_row["evidence_refs"]
    assert scrubbed["surface_admission"] == sample_row["surface_admission"]


def test_emitted_shards_contain_no_personal_identifier_substrings(
    migrated_shards: list[Path],
) -> None:
    assert len(migrated_shards) == 10

    latin_patterns = [pat for token, pat in _PERSONAL_IDENTIFIER_PATTERNS if token == "alona"]
    assert len(latin_patterns) > 0

    for shard_path in migrated_shards:
        text = shard_path.read_text(encoding="utf-8")
        # Ensure no Latin personal name tokens exist anywhere in the output file
        for pattern in latin_patterns:
            assert pattern.search(text) is None, f"Leak in {shard_path}: {pattern.search(text)}"

        payload = yaml.safe_load(text)
        # Check top-level metadata and paths explicitly
        for field in ("batch_id", "batch_label", "reviewer"):
            val = str(payload.get(field, ""))
            for pattern in latin_patterns:
                assert pattern.search(val) is None

        for row in payload["decisions"]:
            path_val = row["source_inventory"]["path"]
            sense_note_val = row.get("sense_note", "")
            for pattern in latin_patterns:
                assert pattern.search(path_val) is None
                assert pattern.search(sense_note_val) is None


def test_shards_concatenate_to_original_decisions(
    migrated_shards: list[Path],
) -> None:
    orig_payload = yaml.safe_load(DEFAULT_SOURCE_LEDGER.read_text(encoding="utf-8"))
    orig_decisions = orig_payload["decisions"]

    reconstructed_decisions: list[dict] = []
    for shard_path in migrated_shards:
        shard_payload = yaml.safe_load(shard_path.read_text(encoding="utf-8"))
        reconstructed_decisions.extend(shard_payload["decisions"])

    assert len(reconstructed_decisions) == len(orig_decisions)

    for recon, orig in zip(reconstructed_decisions, orig_decisions, strict=True):
        assert recon["lemma"] == orig["lemma"]
        assert recon["decision"] == orig["decision"]
        assert recon.get("approved_pos") == orig.get("approved_pos")
        assert recon.get("approved_gloss") == orig.get("approved_gloss")
        assert recon["source_inventory"]["locator"] == orig["source_inventory"]["locator"]
        assert recon["source_inventory"]["source_id"] == orig["source_inventory"]["source_id"]
        assert recon["source_inventory"]["source_family"] == orig["source_inventory"]["source_family"]
        assert recon["evidence_refs"] == orig["evidence_refs"]
        assert recon["surface_admission"] == orig["surface_admission"]
        assert recon["source_inventory"]["path"] == DEFAULT_SCRUBBED_PATH
        expected_key = source_inventory_key(
            lemma=orig["lemma"],
            inventory_path=DEFAULT_SCRUBBED_PATH,
            locator=orig["source_inventory"]["locator"],
        )
        assert recon["source_inventory"]["key"] == expected_key


def test_shards_independently_pass_validation(
    migrated_shards: list[Path],
) -> None:
    total_validated_rows = 0
    for shard_path in migrated_shards:
        summary = validate_decision_file(shard_path)
        assert summary["rows"] > 0
        total_validated_rows += summary["rows"]

    assert total_validated_rows == 11724
