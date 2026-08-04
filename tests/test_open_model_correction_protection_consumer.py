"""Phase 3 public consumer, recipe, and non-erasure harness tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import correction_protection_consumer as consumer

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/projects/open_model_data/release/correction_protection_v1"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_consumer_view_schema_is_strict_and_public_views_validate() -> None:
    schema = _json(consumer.VIEW_SCHEMA)
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    validator = Draft202012Validator(schema)
    views = _jsonl(RELEASE / "model_neutral_views.jsonl")
    assert len(views) == 194
    assert {row["view_type"] for row in views} == set(consumer.VIEW_TYPES)
    assert all(list(validator.iter_errors(row)) == [] for row in views)
    assert all(row["assurance_tier"] == "evidence_graded_non_gold" for row in views)
    assert all(row["evaluation_firewall"]["learning_eligible"] is False for row in views)
    filtering = [row for row in views if row["view_type"] == "filtering"]
    assert {row["action"] for row in filtering} <= {"retain", "exclude", "abstain"}
    assert all(row["proposal"] is None for row in filtering)


def test_public_non_erasure_benchmark_covers_known_answers_and_mandatory_canary() -> None:
    bundle = {name: _jsonl(RELEASE / f"{name}.jsonl") for name in consumer.PUBLIC_FILES}
    report = consumer.public_benchmark(bundle)
    assert report["passed"] is True
    assert report["counts"] == {
        "control_preserved": 37,
        "control_total": 37,
        "correction_detected": 9,
        "correction_total": 9,
        "protected_preserved": 53,
        "protected_total": 53,
    }
    assert report["mandatory_zvuchyt"] == {
        "narration_correction_detected": True,
        "quotation_protected": True,
    }
    assert report["by_category"]["russian_lexical_inflectional_intrusion"]["correction_precision"] == 1.0
    assert report["by_category"]["contextual_calque_government_valency"]["correction_coverage"] == 1.0
    assert report["by_category"]["surzhyk_contested_contact"]["abstention_emitted"] == 12
    assert report["held_back_strategy"]["public_repo_copy"] is False

    coverage = _json(RELEASE / "coverage.json")
    assert coverage["full_bundle"]["phenomenon"][
        "Source-blind Phase 2 stand-off candidate; no span-level linguistic claim"
    ] == 189150
    assert coverage["public_product"]["disagreement_by_category"] == {
        "contextual_calque_government_valency": 4
    }


def test_apply_recipe_corrects_narration_protects_quote_and_abstains(tmp_path: Path) -> None:
    input_path = tmp_path / "consumer.jsonl"
    rows = [
        {"id": "narration", "text": "Фраза звучит значно вишуканіше."},
        {"id": "quote", "text": "Автор навів: «Фраза звучит значно вишуканіше.»"},
        {"id": "control", "text": "Фраза звучить значно вишуканіше."},
    ]
    input_path.write_text("".join(consumer.canonical_json(row) + "\n" for row in rows), encoding="utf-8")
    output = tmp_path / "output"
    receipt = consumer.apply_corpus(
        input_path=input_path,
        release_dir=RELEASE,
        output_dir=output,
        authorized=True,
    )
    corrections = _jsonl(output / "correction.jsonl")
    filtering = _jsonl(output / "filtering.jsonl")
    protections = _jsonl(output / "protection.jsonl")
    abstentions = _jsonl(output / "abstention.jsonl")
    assert [(row["record_id"], row["original"]["surface"], row["proposal"]["replacement"]) for row in corrections] == [
        ("narration", "звучит", "звучить")
    ]
    assert [row["record_id"] for row in protections] == ["quote"]
    assert [row["record_id"] for row in filtering] == ["narration", "quote"]
    assert all(row["action"] == "retain" and row["proposal"] is None for row in filtering)
    assert [row["record_id"] for row in abstentions] == ["control"]
    assert corrections[0]["evaluation_firewall"]["learning_eligible"] is True
    assert receipt["source_mutated"] is False
    assert input_path.read_text(encoding="utf-8") == "".join(
        consumer.canonical_json(row) + "\n" for row in rows
    )


def test_evaluation_overlap_is_excluded_from_every_learning_view() -> None:
    firewall_version, registry = consumer.evaluation_version()
    bundle = {name: _jsonl(RELEASE / f"{name}.jsonl") for name in consumer.PUBLIC_FILES}
    output = consumer.apply_record(
        {"id": "heldout", "text": registry.v011_texts[0]},
        rules=consumer.correction_rules(bundle),
        firewall_version=firewall_version,
        registry=registry,
        authorized=True,
        validator=consumer.view_validator(),
    )
    assert len(output) == 1
    assert output[0]["disposition"] == "excluded"
    assert output[0]["evaluation_firewall"] == {
        "version": firewall_version,
        "overlap_state": "matched",
        "consumer_authorized_local_learning": True,
        "learning_eligible": False,
    }


def test_release_build_is_byte_identical_and_self_verifying(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    consumer.build_release(factory_public_dir=RELEASE, output_dir=first)
    consumer.build_release(factory_public_dir=RELEASE, output_dir=second)
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    assert consumer.verify_release(first)["verified"] is True


def test_heldback_artifact_requires_exact_operator_supplied_hash(tmp_path: Path) -> None:
    heldback = tmp_path / "heldback.jsonl"
    heldback.write_text('{"id":"private","text":"не публікується"}\n', encoding="utf-8")
    with pytest.raises(consumer.ConsumerError, match="hash mismatch"):
        consumer.benchmark_release(
            release_dir=RELEASE,
            output=tmp_path / "report.json",
            heldback=heldback,
            heldback_sha256="0" * 64,
        )
