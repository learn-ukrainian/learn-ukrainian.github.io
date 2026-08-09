from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from scripts.audit.lint_opsec_leaks import (
    _PERSONAL_IDENTIFIER_PATTERNS,
    _SCRUBBED_PERSONAL_IDENTIFIER_TOKENS,
)
from scripts.audit.scrub_decision_ledger_keys import (
    DEFAULT_SCRUBBED_PATH,
    DEFAULT_SOURCE_LEDGER,
    load_source_ledger_payload,
    migrate_ledger_to_shards,
    scrub_decision_row,
)
from scripts.audit.source_inventory_review_decisions import (
    validate_decision_file,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

_SafeLoader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

_LATIN_STEM = _SCRUBBED_PERSONAL_IDENTIFIER_TOKENS[0]
_TITLE_STEM = _LATIN_STEM.title()


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
        "sense_note": f"private teacher-lesson full-source intake ({_TITLE_STEM} document)",
        "source_inventory": {
            "key": "1c7aef76af3ca86a",
            "path": f"data/lexicon/source-inventory/oneshot/private-teacher-lesson-vocabulary-{_LATIN_STEM}-full.yaml",
            "locator": "private source unit 1000 paragraph 1",
            "source_id": "private-teacher-lesson-full-source",
            "source_family": "teacher_lesson",
        },
        "evidence_refs": ["private teacher-lesson document (sample-intake.docx)"],
        "surface_admission": {"daily": False, "practice": True, "cloze": False},
    }

    scrubbed = scrub_decision_row(sample_row, DEFAULT_SCRUBBED_PATH)

    # Independent hashlib.sha256 formula calculation (no circular reuse of source_inventory_key)
    key_material = f"був\0{DEFAULT_SCRUBBED_PATH}\0private source unit 1000 paragraph 1".encode()
    expected_key = hashlib.sha256(key_material).hexdigest()[:16]

    assert scrubbed["source_inventory"]["path"] == DEFAULT_SCRUBBED_PATH
    assert scrubbed["source_inventory"]["key"] == expected_key
    assert scrubbed["source_inventory"]["key"] == "783d50decd9ffa7f"
    assert scrubbed["sense_note"] == "private teacher-lesson full-source intake (full document)"
    assert scrubbed["lemma"] == sample_row["lemma"]
    assert scrubbed["decision"] == sample_row["decision"]
    assert scrubbed["evidence_refs"] == sample_row["evidence_refs"]
    assert scrubbed["surface_admission"] == sample_row["surface_admission"]


def test_emitted_shards_contain_no_personal_identifier_substrings(
    migrated_shards: list[Path],
) -> None:
    assert len(migrated_shards) == 10

    all_patterns = [pat for _, pat in _PERSONAL_IDENTIFIER_PATTERNS]
    assert len(all_patterns) > 0

    for shard_path in migrated_shards:
        text = shard_path.read_text(encoding="utf-8")
        # Ensure no personal name tokens (Latin or Cyrillic) exist anywhere in the output file
        for pattern in all_patterns:
            assert pattern.search(text) is None, f"Leak in {shard_path}: {pattern.search(text)}"

        payload = yaml.load(text, Loader=_SafeLoader)
        for field in ("batch_id", "batch_label", "reviewer"):
            val = str(payload.get(field, ""))
            for pattern in all_patterns:
                assert pattern.search(val) is None, f"Leak in {field}: {val}"

        for row in payload["decisions"]:
            path_val = row["source_inventory"]["path"]
            sense_note_val = row.get("sense_note", "")
            lemma_val = row["lemma"]
            gloss_val = row.get("approved_gloss", "")
            for pattern in all_patterns:
                assert pattern.search(path_val) is None, f"Leak in path: {path_val}"
                assert pattern.search(sense_note_val) is None, f"Leak in sense_note: {sense_note_val}"
                assert pattern.search(lemma_val) is None, f"Leak in lemma: {lemma_val}"
                assert pattern.search(gloss_val) is None, f"Leak in gloss: {gloss_val}"


def test_shards_concatenate_to_original_decisions(
    migrated_shards: list[Path],
) -> None:
    orig_payload = load_source_ledger_payload(DEFAULT_SOURCE_LEDGER)
    orig_decisions = orig_payload["decisions"]

    reconstructed_decisions: list[dict] = []
    for shard_path in migrated_shards:
        shard_payload = yaml.load(shard_path.read_text(encoding="utf-8"), Loader=_SafeLoader)
        reconstructed_decisions.extend(shard_payload["decisions"])

    assert len(reconstructed_decisions) == len(orig_decisions)

    for recon, orig in zip(reconstructed_decisions, orig_decisions, strict=True):
        expected_lemma = orig["lemma"]
        for _, pattern in _PERSONAL_IDENTIFIER_PATTERNS:
            expected_lemma = pattern.sub("[REDACTED]", expected_lemma)

        assert recon["lemma"] == expected_lemma
        assert recon["decision"] == orig["decision"]
        assert recon.get("approved_pos") == orig.get("approved_pos")

        if "approved_gloss" in orig:
            expected_gloss = orig["approved_gloss"]
            for _, pattern in _PERSONAL_IDENTIFIER_PATTERNS:
                expected_gloss = pattern.sub("[REDACTED]", expected_gloss)
            assert recon["approved_gloss"] == expected_gloss

        assert recon["source_inventory"]["locator"] == orig["source_inventory"]["locator"]
        assert recon["source_inventory"]["source_id"] == orig["source_inventory"]["source_id"]
        assert recon["source_inventory"]["source_family"] == orig["source_inventory"]["source_family"]
        assert recon["surface_admission"] == orig["surface_admission"]
        assert recon["source_inventory"]["path"] == DEFAULT_SCRUBBED_PATH

        key_material = f"{expected_lemma}\0{DEFAULT_SCRUBBED_PATH}\0{orig['source_inventory']['locator']}".encode()
        expected_key = hashlib.sha256(key_material).hexdigest()[:16]
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
