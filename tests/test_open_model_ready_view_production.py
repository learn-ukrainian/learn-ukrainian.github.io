from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from tokenizers import Tokenizer, models, pre_tokenizers

from scripts.projects.open_model_data import model_ready_view_production as production


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(production.exporter.canonical_json(value) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(production.exporter.canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def artifact(path: Path, records: int) -> dict[str, Any]:
    return production.artifact(path, records=records)


def continued_pretraining_row(text: str, *, representation: str) -> dict[str, Any]:
    text_sha256 = production.exporter.sha256_text(text)
    return {
        "schema_version": "continued_pretraining_view_v1",
        "record_id": f"pretrain:{'a' * 64}",
        "representation_view": representation,
        "lineage": {
            "source_record_id": "record.wikipedia.000001",
            "source_record_sha256": "1" * 64,
            "source_content_sha256": text_sha256,
            "source_payload_id": "payload.wikipedia.000001",
            "source_payload_sha256": "2" * 64,
            "source_derivation_receipt_sha256": "3" * 64,
            "normalization_receipt_sha256": "4" * 64,
            "language_span_receipt_sha256": "5" * 64,
        },
        "origin": "human_authored",
        "payload": {
            "text": text,
            "text_sha256": text_sha256,
            "character_mask_spans": [
                {"start_char": 0, "end_char": len("Українська"), "reason": "context_uncertain"}
            ],
        },
        "permitted_destination": "continued_pretraining",
        "denied_destinations": [
            "supervised_correction",
            "pairwise_preference",
            "quality_filter",
            "heldout_evaluation",
        ],
        "eligibility": {
            "source_contract_admitted": True,
            "test_fixture": False,
            "model_training_eligible": True,
        },
    }


def signal(
    start: int,
    end: int,
    *,
    candidate_id: str = "candidate-1",
    category: str = "modern_narration_interference",
    reason: str = "russian_or_mixed_language",
) -> production.MaskSignal:
    return production.MaskSignal(
        start=start,
        end=end,
        candidate_id=candidate_id,
        category=category,
        disposition="mask",
        evidence_grade="unresolved",
        language_identity="russian",
        representation="standard_orthography",
        discourse_role="narration",
        reason=reason,
    )


def test_operational_partition_is_gap_free_and_masks_detector_cores() -> None:
    spans = production.operational_partition("abcdefghij", [signal(2, 5)])

    assert [(row["start"], row["end"]) for row in spans] == [(0, 2), (2, 5), (5, 10)]
    assert [row["modern_loss_action"] for row in spans] == [
        "retain",
        "mask_from_loss",
        "retain",
    ]
    assert "text" not in json.dumps(spans)


def test_operational_partition_resolves_overlap_by_frozen_priority() -> None:
    spans = production.operational_partition(
        "abcdefgh",
        [
            signal(1, 6, candidate_id="quoted", category="russian_quotation", reason="quoted_or_multilingual"),
            signal(3, 5, candidate_id="mixed"),
        ],
    )

    overlap = next(row for row in spans if row["start"] == 3 and row["end"] == 5)
    assert overlap["reason"] == "russian_or_mixed_language"


@pytest.mark.parametrize("start,end", [(-1, 1), (1, 1), (1, 11)])
def test_operational_partition_rejects_invalid_spans(start: int, end: int) -> None:
    with pytest.raises(production.ProductionError, match="outside source text"):
        production.operational_partition("abcdefghij", [signal(start, end)])


def test_merge_masks_coalesces_overlap_and_adjacency() -> None:
    merged, coalesced = production._merge_masks(
        [
            {"start_char": 4, "end_char": 7},
            {"start_char": 1, "end_char": 4},
            {"start_char": 6, "end_char": 9},
        ],
        10,
    )

    assert merged == [(1, 9)]
    assert coalesced == 2


def test_word_assignment_handles_leading_space_and_shared_byte_offsets() -> None:
    text = "Річка Дніпро 𐐷"
    words = list(production.WORD_RE.finditer(text))
    offsets = [(0, 5), (5, 9), (9, 11), (12, 13), (12, 13), (12, 13), (12, 13)]

    assignments, counts = production._assign_tokens_to_words(offsets, words)

    assert assignments == [1, 2]
    assert counts["assigned_non_special_tokens"] == 3
    assert counts["unassigned_non_special_tokens"] == 4


def test_mask_projection_masks_every_byte_fallback_piece() -> None:
    projected = production._project_masks_to_tokens(
        [(0, 1), (0, 1), (0, 1), (0, 1), (1, 2)],
        [(0, 1)],
    )

    assert projected["tokens_overlapping_masks"] == 4
    assert projected["tokens_fully_masked"] == 4
    assert projected["zero_loss_tokens"] == 4


def test_mask_projection_counts_partial_leading_space_overlap() -> None:
    projected = production._project_masks_to_tokens([(5, 9)], [(6, 9)])

    assert projected["tokens_partially_masked"] == 1
    assert projected["zero_loss_tokens"] == 1


def test_token_offsets_must_be_ordered() -> None:
    with pytest.raises(production.ProductionError, match="not ordered"):
        production._project_masks_to_tokens([(2, 3), (1, 2)], [])


def test_verify_words_batches_without_losing_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def fake_verify(words: list[str], *, db_path: Path) -> dict[str, list[dict[str, str]]]:
        assert db_path == Path("vesum.db")
        calls.append(words)
        return {word: [{"lemma": word, "pos": "noun", "tags": ""}] for word in words}

    monkeypatch.setattr(production, "verify_words", fake_verify)
    result = production._verify_words_batched(
        ["а", "б", "в", "г", "ґ"],
        db_path=Path("vesum.db"),
        batch_size=2,
    )

    assert calls == [["а", "б"], ["в", "г"], ["ґ"]]
    assert list(result) == ["а", "б", "в", "г", "ґ"]


def test_new_receipt_schemas_are_strict_and_valid() -> None:
    for path in (
        production.PAYLOAD_RECEIPT_SCHEMA,
        production.TOKENIZER_RECEIPT_SCHEMA,
        production.PRODUCTION_RECEIPT_SCHEMA,
    ):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False


def test_blocked_silver_lane_is_empty_without_human_dependency() -> None:
    lane = production._blocked_lane(739_503)

    assert lane["state"] == "blocked"
    assert lane["eligible"] == lane["emitted"] == 0
    assert lane["blocked"] == 739_503
    assert lane["blocked_reasons"] == ["no_eligible_records"]
    assert lane["artifact"] == {
        "records": 0,
        "bytes": 0,
        "sha256": production.EMPTY_SHA256,
    }


def test_word_regex_keeps_ukrainian_apostrophe_forms() -> None:
    assert [item.group(0) for item in re.finditer(production.WORD_RE, "п'ять п’ять пʼять")] == [
        "п'ять",
        "п’ять",
        "пʼять",
    ]


def test_prepare_payloads_runs_complete_admitted_scope_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_records_path = tmp_path / "source-records.jsonl"
    detector_candidates_path = tmp_path / "detector.jsonl"
    silver_records_path = tmp_path / "silver.jsonl"
    sources_db = tmp_path / "sources.db"
    output = tmp_path / "payloads.jsonl"
    receipt_output = tmp_path / "payload-receipt.json"
    detector_receipt_path = tmp_path / "detector-receipt.json"
    silver_receipt_path = tmp_path / "silver-receipt.json"
    admission_receipt_path = tmp_path / "admission-receipt.json"
    operator_packet_path = tmp_path / "operator-packet.json"

    source_records: list[dict[str, Any]] = []
    database_rows: list[tuple[int, str]] = []
    for record_id in range(1, 1030):
        text = f"Український текст {record_id}"
        database_rows.append((record_id, text))
        source_records.append(
            {
                "record_id": f"record.wikipedia.{record_id:06d}",
                "content": {"sha256": production.exporter.sha256_text(text)},
            }
        )
    write_jsonl(source_records_path, source_records)
    connection = sqlite3.connect(sources_db)
    try:
        connection.execute("CREATE TABLE wikipedia (id INTEGER PRIMARY KEY, text TEXT NOT NULL)")
        connection.executemany("INSERT INTO wikipedia (id, text) VALUES (?, ?)", database_rows)
        connection.commit()
    finally:
        connection.close()

    detector_candidates_path.write_text("{}\n", encoding="utf-8")
    silver_records_path.write_text("{}\n", encoding="utf-8")
    write_json(
        detector_receipt_path,
        {"outputs": {"review_candidates": artifact(detector_candidates_path, 1)}},
    )
    write_json(silver_receipt_path, {"output": artifact(silver_records_path, 1)})
    write_json(
        admission_receipt_path,
        {
            "outputs": {"source_records": artifact(source_records_path, 1029)},
            "dispositions": {"admitted": {"rows": 1029}},
        },
    )
    write_json(operator_packet_path, {"operator_decision_status": "accepted"})

    masks = {1: [signal(0, 1, candidate_id="candidate-mask")]}
    monkeypatch.setattr(production, "load_source_records", lambda _path: source_records)
    monkeypatch.setattr(
        production,
        "load_wikipedia_silver",
        lambda _path, *, expected: (masks, Counter({"wikipedia_silver_records": 1})),
    )

    receipt = production.prepare_payloads(
        source_records_path=source_records_path,
        sources_db=sources_db,
        detector_candidates_path=detector_candidates_path,
        silver_records_path=silver_records_path,
        output=output,
        receipt_output=receipt_output,
        detector_receipt_path=detector_receipt_path,
        silver_receipt_path=silver_receipt_path,
        admission_receipt_path=admission_receipt_path,
        operator_packet_path=operator_packet_path,
    )

    assert receipt["counts"]["source_records_processed"] == 1029
    assert receipt["counts"]["masked_records"] == 1
    assert receipt["output_payload"] == artifact(output, 1029)
    assert json.loads(receipt_output.read_text(encoding="utf-8")) == receipt
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.bak"))


def test_tokenizer_diagnostics_runs_real_entry_point(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = "Українська мова природна"
    faithful_view_path = tmp_path / "faithful.jsonl"
    modern_view_path = tmp_path / "modern.jsonl"
    faithful_receipt_path = tmp_path / "faithful-receipt.json"
    modern_receipt_path = tmp_path / "modern-receipt.json"
    tokenizer_path = tmp_path / "tokenizer"
    vesum_db = tmp_path / "vesum.db"
    output = tmp_path / "tokenizer-diagnostics.json"
    tokenizer_path.mkdir()

    write_jsonl(
        faithful_view_path,
        [continued_pretraining_row(text, representation="faithful_literary")],
    )
    write_jsonl(
        modern_view_path,
        [continued_pretraining_row(text, representation="modern_literary_ukrainian")],
    )
    write_json(faithful_receipt_path, {"output": artifact(faithful_view_path, 1)})
    write_json(modern_receipt_path, {"output": artifact(modern_view_path, 1)})

    tokenizer = Tokenizer(
        models.WordLevel(
            {"[UNK]": 0, "Українська": 1, "мова": 2, "природна": 3},
            unk_token="[UNK]",
        )
    )
    tokenizer.pre_tokenizer = pre_tokenizers.Whitespace()
    tokenizer.save(str(tokenizer_path / "tokenizer.json"))
    vesum_db.write_bytes(b"fixture-vesum")
    monkeypatch.setattr(
        production,
        "verify_words",
        lambda words, *, db_path: {
            word: [{"lemma": word, "pos": "noun", "tags": ""}] for word in words
        },
    )

    receipt = production.tokenizer_diagnostics(
        faithful_view_path=faithful_view_path,
        faithful_view_receipt_path=faithful_receipt_path,
        modern_view_path=modern_view_path,
        modern_view_receipt_path=modern_receipt_path,
        tokenizer_path=tokenizer_path,
        tokenizer_identifier="fixture/ukrainian-tokenizer",
        tokenizer_revision="a" * 40,
        vesum_db=vesum_db,
        output=output,
    )

    assert receipt["metrics"]["lexical_word_count"] == 3
    assert receipt["metrics"]["mask_projection"]["counters"]["zero_loss_tokens"] == 1
    assert json.loads(output.read_text(encoding="utf-8")) == receipt


def test_assemble_production_receipt_uses_payload_scoped_protection_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = {
        name: tmp_path / f"{name}.jsonl"
        for name in ("source", "detector", "silver", "payload", "faithful", "modern", "heldout")
    }
    for path in paths.values():
        path.write_text("{}\n", encoding="utf-8")
    artifacts = {
        name: artifact(path, 30 if name == "silver" else 1)
        for name, path in paths.items()
    }

    receipt_paths = {
        name: tmp_path / f"{name}-receipt.json"
        for name in ("detector", "silver", "admission", "payload", "faithful", "modern", "heldout")
    }
    write_json(receipt_paths["detector"], {"outputs": {"review_candidates": artifacts["detector"]}})
    write_json(
        receipt_paths["silver"],
        {
            "output": artifacts["silver"],
            "counts": {"by_evidence_grade": {"protected": 10, "unresolved": 20}},
        },
    )
    write_json(receipt_paths["admission"], {"outputs": {"source_records": artifacts["source"]}})
    write_json(
        receipt_paths["payload"],
        {
            "output_payload": artifacts["payload"],
            "counts": {
                "evidence_grade_counts": [
                    {"code": "protected", "records": 2, "spans": 3, "characters": 4},
                    {"code": "unresolved", "records": 5, "spans": 6, "characters": 7},
                ]
            },
        },
    )
    write_json(
        receipt_paths["faithful"],
        {
            "view_kind": "continued_pretraining",
            "output": artifacts["faithful"],
            "counts": {"input_records": 1, "exported_records": 1},
        },
    )
    write_json(
        receipt_paths["modern"],
        {
            "view_kind": "continued_pretraining",
            "output": artifacts["modern"],
            "counts": {"input_records": 1, "exported_records": 1},
        },
    )
    write_json(
        receipt_paths["heldout"],
        {"view_kind": "heldout_evaluation", "output": artifacts["heldout"]},
    )

    tokenizer_diagnostics_path = tmp_path / "tokenizer-diagnostics.json"
    faithful_recipe_path = tmp_path / "faithful-recipe.json"
    modern_recipe_path = tmp_path / "modern-recipe.json"
    operator_packet_path = tmp_path / "operator-packet.json"
    for path in (
        tokenizer_diagnostics_path,
        faithful_recipe_path,
        modern_recipe_path,
        operator_packet_path,
    ):
        path.write_text("{}\n", encoding="utf-8")

    original_validate = production.validate

    def skip_only_upstream_tokenizer_validation(value, active, label: str) -> None:
        if label != "tokenizer diagnostics":
            original_validate(value, active, label)

    monkeypatch.setattr(production, "validate", skip_only_upstream_tokenizer_validation)
    output = tmp_path / "production-receipt.json"
    receipt = production.assemble_production_receipt(
        source_records_path=paths["source"],
        detector_candidates_path=paths["detector"],
        silver_records_path=paths["silver"],
        payload_path=paths["payload"],
        payload_receipt_path=receipt_paths["payload"],
        faithful_view_path=paths["faithful"],
        faithful_view_receipt_path=receipt_paths["faithful"],
        modern_view_path=paths["modern"],
        modern_view_receipt_path=receipt_paths["modern"],
        heldout_view_path=paths["heldout"],
        heldout_view_receipt_path=receipt_paths["heldout"],
        tokenizer_diagnostics_path=tokenizer_diagnostics_path,
        faithful_recipe_path=faithful_recipe_path,
        modern_recipe_path=modern_recipe_path,
        output=output,
        detector_receipt_path=receipt_paths["detector"],
        silver_receipt_path=receipt_paths["silver"],
        admission_receipt_path=receipt_paths["admission"],
        operator_packet_path=operator_packet_path,
    )

    assert receipt["stratified_counts"]["evidence_grade"] == [
        {"category": "protected", "records": 10, "bytes": 0},
        {"category": "unresolved", "records": 20, "bytes": 0},
    ]
    assert receipt["stratified_counts"]["protected_unresolved"] == [
        {"category": "protected", "records": 2, "bytes": 0},
        {"category": "unresolved", "records": 5, "bytes": 0},
    ]
    assert json.loads(output.read_text(encoding="utf-8")) == receipt
