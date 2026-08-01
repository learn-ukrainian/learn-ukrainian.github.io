from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts.projects.open_model_data.prepare_treatment import (
    TreatmentError,
    build_safety_probes,
    project_loss_labels,
    split_bucket,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
TREATMENTS = ROOT / "data/projects/open_model_data/treatments"


def _validate(schema_name: str, artifact_name: str) -> dict:
    schema = json.loads((CONTRACTS / schema_name).read_text(encoding="utf-8"))
    artifact = json.loads((TREATMENTS / artifact_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(artifact)
    return artifact


def test_committed_stage0_artifacts_validate() -> None:
    preregistration = _validate(
        "treatment_preregistration_v1.schema.json",
        "gemma4_it_wikipedia_mask_ablation_preregistration_v1.json",
    )
    snapshot = _validate(
        "hf_model_snapshot_manifest_v1.schema.json",
        "gemma4_it_model_snapshot_manifest_v1.json",
    )
    probes = _validate(
        "treatment_safety_probe_receipt_v1.schema.json",
        "gemma4_it_safety_probe_receipt_v1.json",
    )
    _validate(
        "tokenizer_diagnostics_v1.schema.json",
        "gemma4_it_tokenizer_diagnostics_v1.json",
    )
    preflight = _validate(
        "treatment_stage0_preflight_v1.schema.json",
        "gemma4_it_stage0_preflight_v1.json",
    )
    assert preregistration["model"]["revision"] == snapshot["revision"]
    assert probes["counts"] == {
        "available_protected_spans": 3935,
        "clean_no_change": 120,
        "protected_span": 180,
        "total": 300,
        "validation_records_with_no_masks": 12,
    }
    assert preflight["decision"] == "REVISE"
    assert preflight["blockers"] == ["operator_authorization_pending", "immutable_model_snapshot_pending"]
    assert preflight["safety"] == {
        "model_call_performed": False,
        "publication_performed": False,
        "training_performed": False,
        "upload_performed": False,
    }


def test_project_loss_labels_handles_partial_adjacent_special_and_padding() -> None:
    input_ids = [1, 10, 11, 12, 13, 0]
    offsets = [(0, 0), (0, 2), (2, 5), (5, 7), (7, 9), (0, 0)]
    special = [1, 0, 0, 0, 0, 0]
    attention = [1, 1, 1, 1, 1, 0]
    masks = [{"start_char": 3, "end_char": 5}, {"start_char": 7, "end_char": 8}]
    assert project_loss_labels(
        input_ids,
        offsets,
        special,
        attention,
        masks,
        apply_character_masks=True,
    ) == [-100, 10, -100, 12, -100, -100]
    assert project_loss_labels(
        input_ids,
        offsets,
        special,
        attention,
        masks,
        apply_character_masks=False,
    ) == [-100, 10, 11, 12, 13, -100]


def test_project_loss_labels_rejects_length_and_span_drift() -> None:
    with pytest.raises(TreatmentError, match="length drift"):
        project_loss_labels([1], [], [0], [1], [], apply_character_masks=True)
    with pytest.raises(TreatmentError, match="invalid character mask"):
        project_loss_labels(
            [1],
            [(0, 1)],
            [0],
            [1],
            [{"start_char": 2, "end_char": 2}],
            apply_character_masks=True,
        )


def _validation_id(prefix: str) -> str:
    index = 0
    while True:
        candidate = f"{prefix}-{index}"
        if split_bucket(candidate) < 200:
            return candidate
        index += 1


def _training_id(prefix: str) -> str:
    index = 0
    while True:
        candidate = f"{prefix}-{index}"
        if split_bucket(candidate) >= 200:
            return candidate
        index += 1


def _view_row(source_id: str, text: str, masks: list[dict], representation: str) -> dict:
    return {
        "lineage": {"source_payload_id": source_id},
        "payload": {"character_mask_spans": masks, "text": text},
        "representation_view": representation,
    }


def test_safety_probe_builder_is_deterministic_and_partition_bound(tmp_path: Path) -> None:
    clean_id = _validation_id("clean")
    protected_id = _validation_id("protected")
    training_id = _training_id("training")
    clean_sentences = [f"Це перевірене українське речення номер {index} для незмінного контрольного прикладу." for index in range(120)]
    protected_sentences = [f"У цьому реченні захищено слово цитата{index} і решта контексту лишається видимою." for index in range(180)]
    clean_text = " ".join(clean_sentences)
    protected_text = " ".join(protected_sentences)
    masks: list[dict] = []
    cursor = 0
    for index, sentence in enumerate(protected_sentences):
        start = cursor + sentence.index(f"цитата{index}")
        end = start + len(f"цитата{index}")
        masks.append({"start_char": start, "end_char": end, "reason": "quoted_or_multilingual"})
        cursor += len(sentence) + 1
    faithful_rows = [
        _view_row(clean_id, clean_text, [], "faithful_literary"),
        _view_row(protected_id, protected_text, [], "faithful_literary"),
        _view_row(training_id, "Цей запис належить лише до тренувального розділу.", [], "faithful_literary"),
    ]
    modern_rows = [
        _view_row(clean_id, clean_text, [], "modern_literary_ukrainian"),
        _view_row(protected_id, protected_text, masks, "modern_literary_ukrainian"),
        _view_row(training_id, "Цей запис належить лише до тренувального розділу.", [], "modern_literary_ukrainian"),
    ]
    faithful_path = tmp_path / "faithful.jsonl"
    modern_path = tmp_path / "modern.jsonl"
    faithful_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in faithful_rows), encoding="utf-8")
    modern_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in modern_rows), encoding="utf-8")
    first_output = tmp_path / "first.jsonl"
    first_receipt = tmp_path / "first.receipt.json"
    second_output = tmp_path / "second.jsonl"
    second_receipt = tmp_path / "second.receipt.json"
    first = build_safety_probes(
        faithful_path=faithful_path,
        modern_path=modern_path,
        output_path=first_output,
        receipt_path=first_receipt,
    )
    second = build_safety_probes(
        faithful_path=faithful_path,
        modern_path=modern_path,
        output_path=second_output,
        receipt_path=second_receipt,
    )
    assert first == second
    assert first_output.read_bytes() == second_output.read_bytes()
    assert first_receipt.read_bytes() == second_receipt.read_bytes()
    assert first["counts"]["total"] == 300
    assert first["split"]["training_records"] == 1
    assert first["split"]["validation_records"] == 2
