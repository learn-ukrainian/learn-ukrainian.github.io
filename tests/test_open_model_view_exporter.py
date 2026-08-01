"""Safety and determinism tests for Foundry model-consumer views."""

from __future__ import annotations

import copy
import json
from collections import defaultdict
from itertools import product
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import correction_factory
from scripts.projects.open_model_data import model_view_exporter as exporter
from scripts.projects.open_model_data import validate_source_records as source_contract

ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXAMPLE = ROOT / "data/projects/open_model_data/contracts/source_record_v1.example.json"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(exporter.canonical_json(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def source_record(text: str, *, record_id: str = "record.synthetic-001") -> dict[str, Any]:
    record = json.loads(SOURCE_EXAMPLE.read_text(encoding="utf-8"))
    record["contract_schema_sha256"] = source_contract.load_schema()[1]
    record["record_id"] = record_id
    record["source_id"] = record_id.replace("record.", "source.")
    record["work_id"] = record_id.replace("record.", "work.")
    record["content"]["sha256"] = exporter.sha256_text(text)
    return record


def source_payload(
    text: str,
    *,
    payload_id: str = "payload.synthetic-001",
    record_id: str = "record.synthetic-001",
    private_data: str = "clear",
    spans: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    complete_spans = spans
    if complete_spans is None:
        complete_spans = [
            {
                "discourse_role": "narration",
                "end": len(text),
                "language_identity": "ukrainian",
                "modern_loss_action": "retain",
                "reason": "other_reviewed",
                "representation": "standard_orthography",
                "start": 0,
            }
        ]
    return {
        "derivation": {
            "kind": "full_source",
            "receipt_sha256": "c" * 64,
            "source_end_char": None,
            "source_start_char": None,
        },
        "language_span_review": {
            "character_spans": complete_spans,
            "receipt_sha256": "b" * 64,
            "reviewer_qualification": "Synthetic structural fixture reviewer",
            "status": "complete",
        },
        "normalization": {
            "receipt_sha256": "a" * 64,
            "status": "complete",
            "version": "fixture-normalization-v1",
        },
        "origin": "machine_generated",
        "origin_evidence": {
            "method": "synthetic-fixture-lineage",
            "receipt_sha256": "d" * 64,
            "status": "verified",
        },
        "payload_id": payload_id,
        "private_data": private_data,
        "private_data_review": {
            "method": "synthetic-fixture-screen",
            "receipt_sha256": "e" * 64,
            "status": "complete",
        },
        "schema_version": "foundry_source_payload_v1",
        "source_content_sha256": exporter.sha256_text(text),
        "source_record_id": record_id,
        "test_fixture": True,
        "text": text,
        "text_sha256": exporter.sha256_text(text),
    }


def evidence(query: str = "помилку") -> dict[str, Any]:
    return {
        "content_sha256": exporter.sha256_text("vesum-fixture"),
        "evidence_type": "form",
        "locator": "fixture:vesum",
        "official_url": None,
        "parser_status": "ok",
        "parser_version": "vesum-fixture-v1",
        "period": "modern",
        "query": query,
        "raw_payload_export_allowed": False,
        "register": "neutral",
        "rights_posture": "bounded_internal_reference",
        "sense_groups": [],
        "source": "vesum",
        "source_identity": "vesum-fixture",
        "status": "attested",
        "supports": "ukrainian_attestation",
    }


def candidate(
    text: str,
    *,
    candidate_id: str = "candidate.synthetic-001",
    source_record_id: str = "record.synthetic-001",
    span_text: str = "помилку",
) -> dict[str, Any]:
    registry = correction_factory.load_evaluation_registry()
    span_start = text.index(span_text)
    contamination = correction_factory.contamination_states(text, registry)
    contamination["registry_artifact_sha256"] = {
        "v0_1_1_manifest": registry.v011_manifest_sha256,
        "v0_2_packet": registry.v02_packet_sha256,
    }
    return {
        "candidate_id": candidate_id,
        "candidate_layers": ["grammar"],
        "detector": {
            "automatic_error_label": False,
            "kind": "combined",
            "model_output_used_as_gold": False,
            "producer": "fixture-detector-v1",
        },
        "evidence": [evidence(span_text)],
        "reconstructions": [],
        "review_state": "unresolved",
        "safety": {
            "contamination": contamination,
            "origin": "verified_synthetic",
            "permitted_use": "correction_eligible",
            "private_data": "clear",
            "provenance": "complete",
            "rights": "granted",
        },
        "schema_version": "correction_candidate_v1",
        "source": {
            "content_sha256": exporter.sha256_text(text),
            "context": {
                "end": len(text),
                "sha256": exporter.sha256_text(text),
                "start": 0,
                "text": text,
            },
            "genre": "fixture",
            "locator": f"fixture:{candidate_id}",
            "origin": "machine_generated",
            "period": "modern",
            "record_id": candidate_id.replace("candidate.", "row."),
            "region": "synthetic",
            "register": "neutral",
            "source_family": "fixture",
            "source_record_id": source_record_id,
        },
        "span": {
            "discourse_role": "narration",
            "downstream_disposition": "human_review_required",
            "end": span_start + len(span_text),
            "language_identity": "ukrainian",
            "representation": "standard_orthography",
            "start": span_start,
            "text": span_text,
        },
        "uncertainty": ["fixture_review_not_real_gold"],
        "upstream": {
            "candidate_schema_version": "review_candidate_v1",
            "candidate_sha256": exporter.sha256_text(f"upstream:{candidate_id}"),
            "profile_id": "fixture-profile-v1",
        },
        "views": {
            "correction": "candidate",
            "evaluation": "excluded_from_non_evaluation_views",
            "faithful_literary": "retain_original",
            "modern_literary_ukrainian": "retain_original",
            "preference": "candidate",
        },
    }


def projection(decision: str, correction: str | None = None) -> dict[str, Any]:
    is_correction = decision == "correction"
    return {
        "acceptable_alternatives": [correction] if correction else [],
        "accepted_correction": correction,
        "citations": [
            {
                "content_sha256": exporter.sha256_text("fixture-citation"),
                "locator": "fixture:review-source",
                "source_identity": "fixture-source",
                "source_kind": "dictionary",
                "supports": "Synthetic structural review evidence.",
            }
        ],
        "decision": decision,
        "discourse_role": "narration",
        "language_identity": "ukrainian",
        "rationale": "Synthetic structural review rationale; never human gold.",
        "representation": "standard_orthography",
        "uncertainty": ["fixture_review_not_real_gold"],
        "views": {
            "correction": "eligible_intake" if is_correction else "not_applicable",
            "evaluation": "excluded_from_non_evaluation_views",
            "faithful_literary": "retain_original",
            "modern_literary_ukrainian": "retain_original",
            "preference": "eligible_intake" if is_correction else "not_applicable",
        },
    }


def review(reviewer_id: str, final: dict[str, Any]) -> dict[str, Any]:
    return {
        "projection": copy.deepcopy(final),
        "reviewer": {
            "human": True,
            "independence_attested": True,
            "qualification_evidence": "Synthetic test fixture; never real qualification.",
            "reviewer_id": reviewer_id,
            "test_fixture": True,
            "ukrainian_qualification": "qualified_ukrainian_language_reviewer",
        },
    }


def correction_record(
    text: str,
    *,
    candidate_id: str = "candidate.synthetic-001",
    source_record_id: str = "record.synthetic-001",
    span_text: str = "помилку",
    decision_name: str = "correction",
    correction: str | None = "похибку",
) -> dict[str, Any]:
    candidate_row = candidate(
        text,
        candidate_id=candidate_id,
        source_record_id=source_record_id,
        span_text=span_text,
    )
    final = projection(decision_name, correction)
    decision = {
        "candidate_id": candidate_row["candidate_id"],
        "candidate_sha256": exporter.sha256_text(exporter.canonical_json(candidate_row)),
        "final": copy.deepcopy(final),
        "final_resolution": {"kind": "first_pass_agreement"},
        "first_pass_reviews": [
            review("fixture-reviewer-a", final),
            review("fixture-reviewer-b", final),
        ],
        "review_state": "adjudicated",
        "schema_version": "correction_reviewer_decision_v1",
    }
    return correction_factory.build_correction_record(candidate_row, decision)


def recipe_config(view_kind: str = "continued_pretraining") -> dict[str, Any]:
    template = "{{text}}" if view_kind == "continued_pretraining" else "{{payload}}"
    evaluation = view_kind == "heldout_evaluation"
    return {
        "base_model": {"identifier": "fixture/base-model", "revision": "1" * 40},
        "data_preparation": {
            "rendering_template": template,
            "rendering_template_sha256": exporter.sha256_text(template),
            "split": {
                "modulus": None if evaluation else 10_000,
                "namespace": "fixture-split-v1",
                "strategy": ("preserve_evaluation_release" if evaluation else "sha256_record_id_modulo"),
                "validation_buckets": None if evaluation else 100,
            },
            "target_loss_policy": exporter.TARGET_LOSS_POLICIES[view_kind],
        },
        "hyperparameters": {
            "epochs": "1",
            "gradient_accumulation_steps": 2,
            "learning_rate": "2e-5",
            "micro_batch_size": 1,
            "packing": False,
            "precision": "bf16",
            "seed": 42,
            "sequence_length": 1024,
            "weight_decay": "0.1",
        },
        "implementation": {
            "code_revision": "2" * 40,
            "dependency_lock_sha256": "3" * 64,
            "framework": "fixture-trainer",
            "framework_version": "1.0.0",
        },
        "objective": exporter.OBJECTIVES[view_kind],
        "recipe_id": "recipe.fixture-v1",
        "run_policy": {"execution_state": "not_run", "training_authorized": False},
        "schema_version": "training_recipe_config_v1",
        "tokenizer": {"identifier": "fixture/tokenizer", "revision": "4" * 40},
        "view_kind": view_kind,
    }


def export_fixture_pretraining(tmp_path: Path) -> tuple[Path, Path]:
    text = "Це синтетичний приклад для перевірки окремого тренувального виду."
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    output = tmp_path / "pretraining.jsonl"
    receipt = tmp_path / "pretraining.receipt.json"
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(payload_path, [source_payload(text)])
    exporter.export_pretraining(
        source_records_path=source_path,
        payloads_path=payload_path,
        origin="machine_generated",
        representation_view="faithful_literary",
        output=output,
        receipt_output=receipt,
        allow_test_fixtures=True,
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_evaluation_artifacts=(),
    )
    return output, receipt


def test_new_schemas_are_strict_and_meta_valid() -> None:
    schemas, _registry = exporter.schema_bundle()
    for path in exporter.NEW_SCHEMA_PATHS:
        Draft202012Validator.check_schema(schemas[path])
        assert schemas[path]["additionalProperties"] is False


def test_evaluation_view_is_separate_and_byte_stable(tmp_path: Path) -> None:
    outputs = []
    receipts = []
    for suffix in ("a", "b"):
        output = tmp_path / f"evaluation-{suffix}.jsonl"
        receipt = tmp_path / f"evaluation-{suffix}.receipt.json"
        exporter.export_evaluation(
            release="all",
            output=output,
            receipt_output=receipt,
            v011_manifest=exporter.DEFAULT_V011_MANIFEST,
            v02_packet=exporter.DEFAULT_V02_PACKET,
            extra_evaluation_artifacts=(),
        )
        outputs.append(output.read_bytes())
        receipts.append(receipt.read_bytes())
    assert outputs[0] == outputs[1]
    assert receipts[0] == receipts[1]
    rows = [json.loads(line) for line in outputs[0].decode().splitlines()]
    assert len(rows) == 691
    assert {row["schema_version"] for row in rows} == {"heldout_evaluation_view_v1"}
    assert all(row["model_training_eligible"] is False for row in rows)
    assert all("continued_pretraining" in row["denied_destinations"] for row in rows)
    receipt = json.loads(receipts[0])
    assert receipt["safety"]["test_fixture_mode"] is False


def test_v011_manifest_item_must_have_a_reference(tmp_path: Path) -> None:
    manifest = json.loads(exporter.DEFAULT_V011_MANIFEST.read_text(encoding="utf-8"))
    references_index = manifest["record_layouts"]["item"].index("references")
    manifest["items"][0][references_index] = []
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(
        exporter.ExportError,
        match=r"v0\.1\.1 evaluation item lacks references",
    ):
        exporter.v011_items(path)


def test_evaluation_recipe_preserves_order_and_never_projects_training_loss(
    tmp_path: Path,
) -> None:
    view = tmp_path / "evaluation.jsonl"
    receipt = tmp_path / "evaluation.receipt.json"
    exporter.export_evaluation(
        release="all",
        output=view,
        receipt_output=receipt,
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_evaluation_artifacts=(),
    )
    config_path = tmp_path / "recipe-config.json"
    config_path.write_text(json.dumps(recipe_config("heldout_evaluation")), encoding="utf-8")
    manifest = exporter.build_recipe_manifest(
        config_path=config_path,
        view_path=view,
        view_receipt_path=receipt,
        output=tmp_path / "recipe-manifest.json",
        allow_test_fixtures=False,
    )
    assert manifest["preparation"]["shuffle"] == ("not applicable; preserve held-out artifact order")
    assert manifest["preparation"]["loss_mask_projection"] == ("not applicable to this view")
    assert manifest["preparation"]["model_training_eligible_records"] == 0
    assert manifest["execution"]["training_authorized"] is False


def test_pretraining_preserves_faithful_text_and_masks_modern_loss(tmp_path: Path) -> None:
    text = "Він сказав «привет», а потім продовжив українською."
    start = text.index("привет")
    end = start + len("привет")
    spans = [
        {
            "discourse_role": "narration",
            "end": start,
            "language_identity": "ukrainian",
            "modern_loss_action": "retain",
            "reason": "other_reviewed",
            "representation": "standard_orthography",
            "start": 0,
        },
        {
            "discourse_role": "quotation",
            "end": end,
            "language_identity": "russian",
            "modern_loss_action": "mask_from_loss",
            "reason": "quoted_or_multilingual",
            "representation": "standard_orthography",
            "start": start,
        },
        {
            "discourse_role": "narration",
            "end": len(text),
            "language_identity": "ukrainian",
            "modern_loss_action": "retain",
            "reason": "other_reviewed",
            "representation": "standard_orthography",
            "start": end,
        },
    ]
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(payload_path, [source_payload(text, spans=spans)])
    results = {}
    for view in ("faithful_literary", "modern_literary_ukrainian"):
        output = tmp_path / f"{view}.jsonl"
        receipt = tmp_path / f"{view}.receipt.json"
        exporter.export_pretraining(
            source_records_path=source_path,
            payloads_path=payload_path,
            origin="machine_generated",
            representation_view=view,
            output=output,
            receipt_output=receipt,
            allow_test_fixtures=True,
            v011_manifest=exporter.DEFAULT_V011_MANIFEST,
            v02_packet=exporter.DEFAULT_V02_PACKET,
            extra_evaluation_artifacts=(),
        )
        results[view] = read_jsonl(output)[0]
    assert results["faithful_literary"]["payload"]["text"] == text
    assert results["faithful_literary"]["payload"]["character_mask_spans"] == []
    assert results["modern_literary_ukrainian"]["payload"]["character_mask_spans"] == [
        {"end_char": end, "reason": "quoted_or_multilingual", "start_char": start}
    ]
    assert results["modern_literary_ukrainian"]["eligibility"] == {
        "model_training_eligible": False,
        "source_contract_admitted": True,
        "test_fixture": True,
    }


def test_complete_language_review_cannot_leave_unclassified_text(
    tmp_path: Path,
) -> None:
    text = "Увесь рядок мусить мати явну мовну класифікацію."
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    payload = source_payload(text)
    payload["language_span_review"]["character_spans"][0]["start"] = 1
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(payload_path, [payload])
    with pytest.raises(exporter.ExportError, match="gap-free"):
        exporter.export_pretraining(
            source_records_path=source_path,
            payloads_path=payload_path,
            origin="machine_generated",
            representation_view="modern_literary_ukrainian",
            output=tmp_path / "output.jsonl",
            receipt_output=tmp_path / "receipt.json",
            allow_test_fixtures=True,
            v011_manifest=exporter.DEFAULT_V011_MANIFEST,
            v02_packet=exporter.DEFAULT_V02_PACKET,
            extra_evaluation_artifacts=(),
        )


def test_character_span_width_must_match_emitted_segment(tmp_path: Path) -> None:
    text = "Сегмент мусить відповідати оголошеним межам нормалізованого джерела."
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    payload = source_payload(text)
    payload["derivation"] = {
        "kind": "character_span",
        "receipt_sha256": "c" * 64,
        "source_end_char": len(text) + 1,
        "source_start_char": 0,
    }
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(payload_path, [payload])
    with pytest.raises(exporter.ExportError, match="span length"):
        exporter.export_pretraining(
            source_records_path=source_path,
            payloads_path=payload_path,
            origin="machine_generated",
            representation_view="faithful_literary",
            output=tmp_path / "output.jsonl",
            receipt_output=tmp_path / "receipt.json",
            allow_test_fixtures=True,
            v011_manifest=exporter.DEFAULT_V011_MANIFEST,
            v02_packet=exporter.DEFAULT_V02_PACKET,
            extra_evaluation_artifacts=(),
        )


@pytest.mark.parametrize(
    ("mutation", "expected_reason"),
    [
        (
            lambda record, payload: record["rights"]["model_training"].update(status="unknown"),
            "excluded_source_record_not_admitted",
        ),
        (lambda _record, payload: payload.update(private_data="present"), "excluded_private_data_not_clear"),
        (
            lambda _record, payload: payload["origin_evidence"].update(
                status="unresolved", method=None, receipt_sha256=None
            ),
            "excluded_origin_unverified",
        ),
        (
            lambda _record, payload: payload["private_data_review"].update(status="incomplete", receipt_sha256=None),
            "excluded_private_data_review_incomplete",
        ),
        (
            lambda _record, payload: payload["normalization"].update(status="incomplete", receipt_sha256=None),
            "excluded_normalization_incomplete",
        ),
    ],
)
def test_pretraining_denies_source_rights_private_and_incomplete_inputs(
    tmp_path: Path, mutation, expected_reason: str
) -> None:
    text = "Окремий синтетичний рядок для перевірки заборон експорту."
    record = source_record(text)
    payload = source_payload(text)
    mutation(record, payload)
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    output = tmp_path / "output.jsonl"
    receipt_path = tmp_path / "receipt.json"
    write_jsonl(source_path, [record])
    write_jsonl(payload_path, [payload])
    receipt = exporter.export_pretraining(
        source_records_path=source_path,
        payloads_path=payload_path,
        origin="machine_generated",
        representation_view="faithful_literary",
        output=output,
        receipt_output=receipt_path,
        allow_test_fixtures=True,
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_evaluation_artifacts=(),
    )
    assert output.read_bytes() == b""
    assert receipt["counts"][expected_reason] == 1
    assert receipt["safety"]["test_fixture_mode"] is False


def test_exact_and_near_evaluation_text_never_enter_pretraining(tmp_path: Path) -> None:
    evaluation_text = exporter.v011_items(exporter.DEFAULT_V011_MANIFEST)[0]["source"]
    near_text = evaluation_text[:-1] + ("!" if evaluation_text[-1] != "!" else ".")
    for index, text in enumerate((evaluation_text, near_text)):
        source_path = tmp_path / f"source-{index}.jsonl"
        payload_path = tmp_path / f"payload-{index}.jsonl"
        output = tmp_path / f"output-{index}.jsonl"
        receipt_path = tmp_path / f"receipt-{index}.json"
        write_jsonl(source_path, [source_record(text)])
        write_jsonl(payload_path, [source_payload(text)])
        receipt = exporter.export_pretraining(
            source_records_path=source_path,
            payloads_path=payload_path,
            origin="machine_generated",
            representation_view="faithful_literary",
            output=output,
            receipt_output=receipt_path,
            allow_test_fixtures=True,
            v011_manifest=exporter.DEFAULT_V011_MANIFEST,
            v02_packet=exporter.DEFAULT_V02_PACKET,
            extra_evaluation_artifacts=(),
        )
        assert output.read_bytes() == b""
        assert receipt["counts"]["excluded_records"] == 1
        assert any(key.startswith("excluded_evaluation_contamination_") for key in receipt["counts"])


def test_extensionless_evaluation_artifact_text_is_excluded(tmp_path: Path) -> None:
    text = "Розширення назви файла не повинно вимикати захист оцінювальних даних."
    evaluation_artifact = tmp_path / "HELDOUT"
    evaluation_artifact.write_text(text, encoding="utf-8")
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    output = tmp_path / "output.jsonl"
    receipt_path = tmp_path / "receipt.json"
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(payload_path, [source_payload(text)])
    receipt = exporter.export_pretraining(
        source_records_path=source_path,
        payloads_path=payload_path,
        origin="machine_generated",
        representation_view="faithful_literary",
        output=output,
        receipt_output=receipt_path,
        allow_test_fixtures=True,
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_evaluation_artifacts=(evaluation_artifact,),
    )
    assert output.read_bytes() == b""
    assert receipt["counts"]["excluded_evaluation_contamination_exact_normalized"] == 1
    assert any(
        artifact["logical_path"].startswith("external:")
        for artifact in receipt["evaluation_exclusion_registry"]["artifacts"]
    )


def test_distributed_edits_still_reach_character_sequence_check() -> None:
    reference = "".join(chr(ord("а") + index % 20) for index in range(240))
    candidate = "".join("я" if index % 20 == 19 else character for index, character in enumerate(reference))
    registry = exporter.EvaluationExclusionRegistry(
        exact_hashes=set(),
        near_texts=[],
        near_shingles=[],
        shingle_index=defaultdict(set),
        character_index=defaultdict(set),
        artifacts=[],
    )
    registry.add_text(reference, explicit_evaluation_text=True)
    match = registry.match(candidate)
    assert match.matched is True
    assert match.method == "character_sequence"


def test_character_sequence_upper_bound_skips_impossible_exact_ratio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = "спільний-" + ("а" * 240)
    candidate = "спільний-" + ("я" * 240)
    registry = exporter.empty_text_registry()
    registry.add_text(reference, explicit_evaluation_text=True)

    class UpperBoundOnly:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def quick_ratio(self) -> float:
            return 0.1

        def ratio(self) -> float:
            raise AssertionError("exact SequenceMatcher ratio must not run below its upper bound")

    monkeypatch.setattr(exporter, "SequenceMatcher", UpperBoundOnly)
    assert registry.match(candidate).matched is False


def test_qgram_bound_rejects_same_histogram_different_sequence() -> None:
    first = ("а" * 200) + ("б" * 200)
    second = "аб" * 200

    assert exporter.SequenceMatcher(None, first, second, autojunk=False).quick_ratio() == 1.0
    assert exporter.sequence_ratio_can_reach(first, second, threshold=0.9) is False


def test_qgram_bound_never_rejects_reachable_short_sequence_ratio() -> None:
    values = [
        "".join(characters)
        for length in range(1, 6)
        for characters in product("аб", repeat=length)
    ]
    for first in values:
        for second in values:
            ratio = exporter.SequenceMatcher(None, first, second, autojunk=False).ratio()
            if ratio >= 0.6:
                assert exporter.sequence_ratio_can_reach(first, second, threshold=0.6) is True


def test_long_character_sequence_detects_distributed_repetitive_edits() -> None:
    reference = "".join(chr(ord("а") + index % 20) for index in range(12_000))
    candidate = "".join(
        "я" if index % 10 == 9 else character
        for index, character in enumerate(reference)
    )

    assert exporter.character_sequence_matches(reference, candidate, threshold=0.9) is True


def test_long_character_sequence_rejects_anagram_like_frequency_match() -> None:
    first = ("а" * 5000) + ("б" * 5000)
    second = "аб" * 5000

    assert exporter.character_sequence_matches(first, second, threshold=0.9) is False


def test_containment_prefilter_preserves_exact_containment() -> None:
    reference = "три слова тут і ще кілька слів для надійної перевірки"
    candidate = f"Початок матеріалу. {reference}. Завершення матеріалу."
    registry = exporter.empty_text_registry()
    registry.add_text(reference, explicit_evaluation_text=True)

    match = registry.match(candidate)

    assert match.matched is True
    assert match.method == "character_containment"


def test_character_anchor_index_is_bounded_and_keeps_endpoints() -> None:
    normalized = "".join(chr(0x400 + index) for index in range(400))
    offsets = exporter.character_anchor_offsets(normalized)
    assert len(offsets) == exporter.MAX_CHARACTER_ANCHORS_PER_TEXT
    assert offsets[0] == 0
    assert offsets[-1] == len(normalized) - exporter.CANDIDATE_ANCHOR_CHARACTERS
    assert offsets == tuple(sorted(set(offsets)))

    registry = exporter.empty_text_registry()
    registry.add_text(normalized, explicit_evaluation_text=True)
    assert sum(len(indexes) for indexes in registry.character_index.values()) <= 64


def test_rollback_backup_path_remains_reserved(tmp_path: Path) -> None:
    destination = tmp_path / "view.jsonl"
    backup = exporter.reserved_rollback_path(destination)
    try:
        assert backup.exists()
        assert backup.parent == destination.parent
        assert backup.read_bytes() == b""
    finally:
        backup.unlink(missing_ok=True)


@pytest.mark.parametrize(
    "second_text",
    [
        "Повторний синтетичний запис не повинен двічі входити до одного виду.",
        "Повторний синтетичний запис не повинен двічі входити до одного виду!",
    ],
)
def test_intra_view_exact_and_near_duplicates_are_excluded(
    tmp_path: Path,
    second_text: str,
) -> None:
    first_text = "Повторний синтетичний запис не повинен двічі входити до одного виду."
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    output = tmp_path / "output.jsonl"
    receipt_path = tmp_path / "receipt.json"
    write_jsonl(
        source_path,
        [
            source_record(first_text, record_id="record.synthetic-001"),
            source_record(second_text, record_id="record.synthetic-002"),
        ],
    )
    write_jsonl(
        payload_path,
        [
            source_payload(
                first_text,
                payload_id="payload.synthetic-001",
                record_id="record.synthetic-001",
            ),
            source_payload(
                second_text,
                payload_id="payload.synthetic-002",
                record_id="record.synthetic-002",
            ),
        ],
    )
    receipt = exporter.export_pretraining(
        source_records_path=source_path,
        payloads_path=payload_path,
        origin="machine_generated",
        representation_view="faithful_literary",
        output=output,
        receipt_output=receipt_path,
        allow_test_fixtures=True,
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_evaluation_artifacts=(),
    )
    assert len(read_jsonl(output)) == 1
    assert receipt["counts"]["excluded_records"] == 1
    assert (
        sum(count for reason, count in receipt["counts"].items() if reason.startswith("excluded_intra_view_duplicate_"))
        == 1
    )
    assert receipt["admission"] == {
        "applied": True,
        "policy": "recompute source_record_v1 admission; unknown is denial",
        "source_records_admitted": 2,
        "source_records_denied": 0,
        "source_records_total": 2,
    }
    assert receipt["deduplication"]["accepted_fingerprints"] == 1
    assert receipt["safety"]["test_fixture_mode"] is True


def test_production_mode_rejects_fixtures_and_preserves_existing_output(
    tmp_path: Path,
) -> None:
    text = "Синтетичний рядок не є реально допущеним тренувальним записом."
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    output = tmp_path / "output.jsonl"
    receipt = tmp_path / "receipt.json"
    write_jsonl(source_path, [source_record(text)])
    good = source_payload(text, payload_id="payload.synthetic-001")
    bad = source_payload(text, payload_id="payload.synthetic-002")
    bad["text_sha256"] = "0" * 64
    write_jsonl(payload_path, [good, bad])
    output.write_text("sentinel\n", encoding="utf-8")
    receipt.write_text("sentinel-receipt\n", encoding="utf-8")
    with pytest.raises(exporter.ExportError, match="test fixture"):
        exporter.export_pretraining(
            source_records_path=source_path,
            payloads_path=payload_path,
            origin="machine_generated",
            representation_view="faithful_literary",
            output=output,
            receipt_output=receipt,
            allow_test_fixtures=False,
            v011_manifest=exporter.DEFAULT_V011_MANIFEST,
            v02_packet=exporter.DEFAULT_V02_PACKET,
            extra_evaluation_artifacts=(),
        )
    assert output.read_text(encoding="utf-8") == "sentinel\n"
    assert receipt.read_text(encoding="utf-8") == "sentinel-receipt\n"


def test_late_row_validation_failure_preserves_existing_output_and_receipt(
    tmp_path: Path,
) -> None:
    text = "Синтетичний рядок не є реально допущеним тренувальним записом."
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    output = tmp_path / "output.jsonl"
    receipt = tmp_path / "receipt.json"
    write_jsonl(source_path, [source_record(text)])
    good = source_payload(text, payload_id="payload.synthetic-001")
    bad = source_payload(text, payload_id="payload.synthetic-002")
    bad["text_sha256"] = "0" * 64
    write_jsonl(payload_path, [good, bad])
    output.write_text("sentinel\n", encoding="utf-8")
    receipt.write_text("sentinel-receipt\n", encoding="utf-8")
    with pytest.raises(exporter.ExportError, match="text hash mismatch"):
        exporter.export_pretraining(
            source_records_path=source_path,
            payloads_path=payload_path,
            origin="machine_generated",
            representation_view="faithful_literary",
            output=output,
            receipt_output=receipt,
            allow_test_fixtures=True,
            v011_manifest=exporter.DEFAULT_V011_MANIFEST,
            v02_packet=exporter.DEFAULT_V02_PACKET,
            extra_evaluation_artifacts=(),
        )
    assert output.read_text(encoding="utf-8") == "sentinel\n"
    assert receipt.read_text(encoding="utf-8") == "sentinel-receipt\n"


def test_receipt_commit_failure_rolls_back_view_and_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = "Синтетичний рядок перевіряє відновлення пари артефактів."
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    output = tmp_path / "output.jsonl"
    receipt = tmp_path / "receipt.json"
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(payload_path, [source_payload(text)])
    output.write_text("sentinel\n", encoding="utf-8")
    receipt.write_text("sentinel-receipt\n", encoding="utf-8")
    original_replace = exporter.os.replace

    def fail_receipt_commit(source, destination) -> None:
        source_path = Path(source)
        destination_path = Path(destination)
        if source_path.suffix == ".tmp" and destination_path == receipt:
            raise OSError("synthetic receipt rename failure")
        original_replace(source, destination)

    monkeypatch.setattr(exporter.os, "replace", fail_receipt_commit)
    with pytest.raises(OSError, match="synthetic receipt rename failure"):
        exporter.export_pretraining(
            source_records_path=source_path,
            payloads_path=payload_path,
            origin="machine_generated",
            representation_view="faithful_literary",
            output=output,
            receipt_output=receipt,
            allow_test_fixtures=True,
            v011_manifest=exporter.DEFAULT_V011_MANIFEST,
            v02_packet=exporter.DEFAULT_V02_PACKET,
            extra_evaluation_artifacts=(),
        )
    assert output.read_text(encoding="utf-8") == "sentinel\n"
    assert receipt.read_text(encoding="utf-8") == "sentinel-receipt\n"
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.bak"))


@pytest.mark.parametrize(
    ("view_kind", "expected_schema", "expected_destination"),
    [
        ("correction_instruction", "correction_instruction_view_v1", "supervised_correction"),
        ("preference", "preference_view_v1", "pairwise_preference"),
        ("quality_filter", "quality_filter_view_v1", "quality_filter"),
    ],
)
def test_correction_family_views_are_disjoint_and_fixture_ineligible(
    tmp_path: Path,
    view_kind: str,
    expected_schema: str,
    expected_destination: str,
) -> None:
    text = "У цьому синтетичному реченні є помилку для перевірки."
    source_path = tmp_path / f"source-{view_kind}.jsonl"
    correction_path = tmp_path / f"correction-{view_kind}.jsonl"
    output = tmp_path / f"output-{view_kind}.jsonl"
    receipt_path = tmp_path / f"receipt-{view_kind}.json"
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(correction_path, [correction_record(text)])
    receipt = exporter.export_correction_family(
        view_kind=view_kind,
        source_records_path=source_path,
        correction_records_path=correction_path,
        origin="machine_generated",
        output=output,
        receipt_output=receipt_path,
        allow_test_fixtures=True,
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_evaluation_artifacts=(),
    )
    row = read_jsonl(output)[0]
    assert row["schema_version"] == expected_schema
    assert row["permitted_destination"] == expected_destination
    assert row["eligibility"]["model_training_eligible"] is False
    assert receipt["counts"]["fixture_records"] == 1
    if view_kind == "correction_instruction":
        assert row["payload"]["target_text"] == text.replace("помилку", "похибку")
    if view_kind == "preference":
        assert row["payload"]["chosen"] == "похибку"
        assert row["payload"]["rejected"] == "помилку"
    if view_kind == "quality_filter":
        assert row["payload"]["label"] == "needs_correction"


def test_correction_export_preserves_packet_order_for_hash_derived_ids(
    tmp_path: Path,
) -> None:
    inputs = [
        (
            "У першому короткому прикладі є помилку.",
            "candidate.synthetic-001",
            "record.synthetic-001",
        ),
        (
            "Цілком інший контекст також містить помилку для окремої перевірки.",
            "candidate.synthetic-002",
            "record.synthetic-002",
        ),
    ]
    source_rows = [source_record(text, record_id=source_record_id) for text, _candidate_id, source_record_id in inputs]
    correction_rows = [
        correction_record(
            text,
            candidate_id=candidate_id,
            source_record_id=source_record_id,
        )
        for text, candidate_id, source_record_id in inputs
    ]
    correction_rows.sort(key=lambda row: row["record_id"], reverse=True)
    assert correction_rows[0]["record_id"] > correction_rows[1]["record_id"]

    source_path = tmp_path / "source.jsonl"
    correction_path = tmp_path / "correction.jsonl"
    output = tmp_path / "output.jsonl"
    receipt_path = tmp_path / "receipt.json"
    write_jsonl(source_path, source_rows)
    write_jsonl(correction_path, correction_rows)
    receipt = exporter.export_correction_family(
        view_kind="correction_instruction",
        source_records_path=source_path,
        correction_records_path=correction_path,
        origin="machine_generated",
        output=output,
        receipt_output=receipt_path,
        allow_test_fixtures=True,
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_evaluation_artifacts=(),
    )
    output_rows = read_jsonl(output)
    assert [row["lineage"]["correction_record_id"] for row in output_rows] == [
        row["record_id"] for row in correction_rows
    ]
    assert receipt["counts"]["exported_records"] == 2
    assert receipt["determinism"]["ordering"] == ("canonical upstream packet order; unique correction record ID")


def test_distinct_corrections_sharing_long_context_are_not_near_deduplicated(
    tmp_path: Path,
) -> None:
    text = (
        "У розгорнутому навчальному реченні навмисно залишено помилку, щоб "
        "перевірити перше незалежне виправлення, а наприкінці додано окремий "
        "недолік для другого незалежного виправлення в тому самому контексті."
    )
    correction_rows = [
        correction_record(
            text,
            candidate_id="candidate.synthetic-001",
            span_text="помилку",
            correction="похибку",
        ),
        correction_record(
            text,
            candidate_id="candidate.synthetic-002",
            span_text="недолік",
            correction="ваду",
        ),
    ]
    source_path = tmp_path / "source.jsonl"
    correction_path = tmp_path / "correction.jsonl"
    output = tmp_path / "output.jsonl"
    receipt_path = tmp_path / "receipt.json"
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(correction_path, correction_rows)
    receipt = exporter.export_correction_family(
        view_kind="correction_instruction",
        source_records_path=source_path,
        correction_records_path=correction_path,
        origin="machine_generated",
        output=output,
        receipt_output=receipt_path,
        allow_test_fixtures=True,
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_evaluation_artifacts=(),
    )
    assert len(read_jsonl(output)) == 2
    assert receipt["counts"]["exported_records"] == 2
    assert not any(reason.startswith("excluded_intra_view_duplicate_") for reason in receipt["counts"])


def test_quality_filter_accepts_resolved_acceptable_fixture_only_as_fixture(
    tmp_path: Path,
) -> None:
    text = "У цьому синтетичному реченні є помилку для перевірки."
    source_path = tmp_path / "source.jsonl"
    correction_path = tmp_path / "correction.jsonl"
    output = tmp_path / "output.jsonl"
    receipt_path = tmp_path / "receipt.json"
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(
        correction_path,
        [correction_record(text, decision_name="acceptable_as_is", correction=None)],
    )
    exporter.export_correction_family(
        view_kind="quality_filter",
        source_records_path=source_path,
        correction_records_path=correction_path,
        origin="machine_generated",
        output=output,
        receipt_output=receipt_path,
        allow_test_fixtures=True,
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_evaluation_artifacts=(),
    )
    row = read_jsonl(output)[0]
    assert row["payload"] == {
        "decision": "acceptable_as_is",
        "label": "acceptable",
        "text": text,
    }
    assert row["eligibility"]["model_training_eligible"] is False


def test_derived_correction_target_is_checked_for_evaluation_contamination(
    tmp_path: Path,
) -> None:
    text = "У цьому синтетичному реченні є помилку для перевірки."
    evaluation_text = exporter.v011_items(exporter.DEFAULT_V011_MANIFEST)[0]["source"]
    record = correction_record(text, correction=evaluation_text)
    source_path = tmp_path / "source.jsonl"
    correction_path = tmp_path / "correction.jsonl"
    output = tmp_path / "output.jsonl"
    receipt_path = tmp_path / "receipt.json"
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(correction_path, [record])
    receipt = exporter.export_correction_family(
        view_kind="correction_instruction",
        source_records_path=source_path,
        correction_records_path=correction_path,
        origin="machine_generated",
        output=output,
        receipt_output=receipt_path,
        allow_test_fixtures=True,
        v011_manifest=exporter.DEFAULT_V011_MANIFEST,
        v02_packet=exporter.DEFAULT_V02_PACKET,
        extra_evaluation_artifacts=(),
    )
    assert output.read_bytes() == b""
    assert receipt["counts"]["excluded_records"] == 1
    assert any(key.startswith("excluded_evaluation_contamination_") for key in receipt["counts"])


def test_recipe_binds_exact_fixture_view_but_never_authorizes_training(
    tmp_path: Path,
) -> None:
    view, receipt = export_fixture_pretraining(tmp_path)
    config_path = tmp_path / "recipe-config.json"
    output = tmp_path / "recipe-manifest.json"
    config_path.write_text(json.dumps(recipe_config()), encoding="utf-8")
    with pytest.raises(exporter.ExportError, match="fixture view"):
        exporter.build_recipe_manifest(
            config_path=config_path,
            view_path=view,
            view_receipt_path=receipt,
            output=output,
            allow_test_fixtures=False,
        )
    manifest = exporter.build_recipe_manifest(
        config_path=config_path,
        view_path=view,
        view_receipt_path=receipt,
        output=output,
        allow_test_fixtures=True,
    )
    assert manifest["view_artifact"]["sha256"] == exporter.sha256_file(view)
    assert manifest["view_receipt"]["sha256"] == exporter.sha256_file(receipt)
    assert manifest["execution"] == {
        "execution_state": "not_run",
        "model_call_performed": False,
        "test_fixture_mode": True,
        "training_authorized": False,
        "training_performed": False,
    }
    assert manifest["preparation"]["model_training_eligible_records"] == 0
    assert manifest["preparation"]["test_fixture_records"] == 1


def test_recipe_rejects_wrong_objective_and_moving_revision(tmp_path: Path) -> None:
    view, receipt = export_fixture_pretraining(tmp_path)
    config = recipe_config()
    config["objective"] = "pairwise_preference"
    config_path = tmp_path / "wrong-objective.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(exporter.ExportError, match="objective"):
        exporter.build_recipe_manifest(
            config_path=config_path,
            view_path=view,
            view_receipt_path=receipt,
            output=tmp_path / "manifest.json",
            allow_test_fixtures=True,
        )
    config = recipe_config()
    config["base_model"]["revision"] = "main"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(exporter.ExportError, match="schema violation"):
        exporter.build_recipe_manifest(
            config_path=config_path,
            view_path=view,
            view_receipt_path=receipt,
            output=tmp_path / "manifest.json",
            allow_test_fixtures=True,
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("learning_rate", "0", "learning_rate"),
        ("epochs", "0", "epochs"),
    ],
)
def test_recipe_rejects_non_positive_training_values(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    view, receipt = export_fixture_pretraining(tmp_path)
    config = recipe_config()
    config["hyperparameters"][field] = value
    config_path = tmp_path / "invalid-hyperparameter.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(exporter.ExportError, match=message):
        exporter.build_recipe_manifest(
            config_path=config_path,
            view_path=view,
            view_receipt_path=receipt,
            output=tmp_path / "manifest.json",
            allow_test_fixtures=True,
        )


def test_recipe_rejects_unbound_template_and_invalid_split(tmp_path: Path) -> None:
    view, receipt = export_fixture_pretraining(tmp_path)
    config = recipe_config()
    config_path = tmp_path / "invalid-preparation.json"
    config["data_preparation"]["rendering_template"] = "{{different_text}}"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(exporter.ExportError, match="template hash"):
        exporter.build_recipe_manifest(
            config_path=config_path,
            view_path=view,
            view_receipt_path=receipt,
            output=tmp_path / "manifest.json",
            allow_test_fixtures=True,
        )
    config = recipe_config()
    config["data_preparation"]["split"]["validation_buckets"] = 10_000
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(exporter.ExportError, match="validation split"):
        exporter.build_recipe_manifest(
            config_path=config_path,
            view_path=view,
            view_receipt_path=receipt,
            output=tmp_path / "manifest.json",
            allow_test_fixtures=True,
        )


def test_cli_returns_exit_two_for_fixture_without_explicit_switch(
    tmp_path: Path,
) -> None:
    text = "Синтетичний рядок для перевірки коду завершення."
    source_path = tmp_path / "source.jsonl"
    payload_path = tmp_path / "payload.jsonl"
    write_jsonl(source_path, [source_record(text)])
    write_jsonl(payload_path, [source_payload(text)])
    with pytest.raises(SystemExit) as exc:
        exporter.main(
            [
                "continued-pretraining",
                "--source-records",
                str(source_path),
                "--payloads",
                str(payload_path),
                "--origin",
                "machine_generated",
                "--representation-view",
                "faithful_literary",
                "--output",
                str(tmp_path / "output.jsonl"),
                "--receipt-output",
                str(tmp_path / "receipt.json"),
            ]
        )
    assert exc.value.code == 2
