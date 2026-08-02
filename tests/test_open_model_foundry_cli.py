"""End-to-end tests for the public, portable Ukrainian Data Foundry CLI."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import foundry_cli as foundry
from scripts.projects.open_model_data import model_view_exporter as exporter

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "data/projects/open_model_data/examples/portable-corpus-v1.jsonl"
COST = ROOT / "data/projects/open_model_data/examples/portable-cost-v1.json"


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(foundry.canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def sample_records() -> list[dict[str, object]]:
    return read_jsonl(EXAMPLE)


def run_example(tmp_path: Path, suffix: str) -> foundry.PreparedRun:
    return foundry.prepare(
        input_path=EXAMPLE,
        output_dir=tmp_path / suffix,
        max_records=100,
        evaluation_artifacts=(),
        tokenizer_path=None,
        tokenizer_identifier=None,
        tokenizer_revision=None,
        cost_path=COST,
    )


def test_portable_contracts_are_strict_and_meta_valid() -> None:
    for path in (foundry.INPUT_SCHEMA, foundry.RECEIPT_SCHEMA):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False


def test_example_runs_end_to_end_without_model_or_private_database(tmp_path: Path) -> None:
    result = run_example(tmp_path, "run")
    receipt = result.receipt

    assert receipt["input"]["records"] == 8
    assert receipt["capability_summary"]["local_model_learning"] == {
        "allowed": 7,
        "denied": 1,
        "unknown": 0,
        "not_applicable": 0,
    }
    assert receipt["views"]["canonical_records"]["records"] == 8
    assert receipt["views"]["faithful_source"]["records"] == 7
    assert receipt["views"]["modern_learning"]["records"] == 5
    assert receipt["views"]["silver_correction"]["records"] == 1
    assert receipt["views"]["preference"]["records"] == 1
    assert receipt["views"]["heldout_evaluation"]["records"] == 1
    assert receipt["evidence_summary"]["by_track"]["calques"] >= 1
    assert receipt["evidence_summary"]["by_track"]["quoted_russian"] >= 1
    assert receipt["evidence_summary"]["by_track"]["historical_archaic"] >= 1
    assert receipt["evaluation_firewall"]["learning_views_contain_matched_records"] is False
    assert receipt["recipe"]["training_authorized"] is False
    assert receipt["cost"]["results"] == {
        "wall_clock_hours": "2.777778",
        "compute_usd": "6.944444",
        "storage_usd": "1.000000",
        "evaluation_usd": "2.000000",
        "failed_run_allowance_usd": "0.994444",
        "total_usd": "10.938889",
    }
    assert receipt["safety"] == {
        "original_text_preserved": True,
        "automatic_rewrite_performed": False,
        "model_call_performed": False,
        "model_download_performed": False,
        "training_performed": False,
        "optimizer_executed": False,
        "adapter_created": False,
        "weights_uploaded": False,
        "closed_api_required": False,
        "publication_authorized": False,
    }

    input_by_id = {row["record_id"]: row for row in sample_records()}
    canonical_by_id = {
        row["record_id"]: row for row in read_jsonl(result.output_dir / "canonical-records.jsonl")
    }
    assert set(input_by_id) == set(canonical_by_id)
    for record_id, source in input_by_id.items():
        assert canonical_by_id[record_id]["original_text"] == source["text"]
        assert canonical_by_id[record_id]["source"]["locators"] == source["source"]["locators"]

    modern_by_id = {
        row["record_id"]: row for row in read_jsonl(result.output_dir / "modern-learning.jsonl")
    }
    assert "example.dialect" not in modern_by_id
    assert "example.historical" not in modern_by_id
    assert modern_by_id["example.russian-interference"]["character_mask_spans"]
    assert modern_by_id["example.quoted-russian"]["character_mask_spans"] == []


def test_outputs_are_byte_stable_and_self_verifying(tmp_path: Path) -> None:
    first = run_example(tmp_path, "first")
    second = run_example(tmp_path, "second")

    assert first.receipt == second.receipt
    for artifact in first.receipt["reproduction"]["artifacts"].values():
        logical_path = artifact["logical_path"]
        assert (first.output_dir / logical_path).read_bytes() == (second.output_dir / logical_path).read_bytes()
    verification = foundry.verify(first.output_dir)
    assert verification["status"] == "passed"
    assert verification["artifacts_checked"] == len(first.receipt["reproduction"]["artifacts"])

    with (first.output_dir / "faithful-source.jsonl").open("a", encoding="utf-8") as handle:
        handle.write("{}\n")
    with pytest.raises(foundry.FoundryError, match="hash mismatch") as exc_info:
        foundry.verify(first.output_dir)
    assert exc_info.value.code == "FNDY-E007"


def test_exact_eval_text_is_denied_from_every_learning_view(tmp_path: Path) -> None:
    record = copy.deepcopy(sample_records()[0])
    evaluation_text = exporter.v011_items(foundry.DEFAULT_V011_MANIFEST)[0]["source"]
    record["record_id"] = "consumer.eval-contamination"
    record["text"] = evaluation_text
    record["evidence"] = []
    input_path = tmp_path / "input.jsonl"
    write_jsonl(input_path, [record])

    result = foundry.prepare(
        input_path=input_path,
        output_dir=tmp_path / "out",
        max_records=1,
        evaluation_artifacts=(),
        tokenizer_path=None,
        tokenizer_identifier=None,
        tokenizer_revision=None,
        cost_path=None,
    )

    assert result.receipt["evaluation_firewall"]["matched_records"] == 1
    assert result.receipt["views"]["faithful_source"]["records"] == 0
    assert result.receipt["views"]["modern_learning"]["records"] == 0
    filter_row = read_jsonl(result.output_dir / "quality-filter.jsonl")[0]
    assert filter_row["evaluation_firewall_matched"] is True
    assert filter_row["automatic_deletion_authorized"] is False


def test_allowed_capability_requires_its_own_evidence(tmp_path: Path) -> None:
    record = sample_records()[0]
    record["capabilities"]["dataset_publication"]["evidence"] = []
    input_path = tmp_path / "input.jsonl"
    write_jsonl(input_path, [record])

    with pytest.raises(foundry.FoundryError, match="allows dataset_publication without evidence") as exc_info:
        foundry.read_records(input_path, max_records=1)
    assert exc_info.value.code == "FNDY-E002"


def test_public_parser_exposes_one_prepare_and_verify_cli() -> None:
    help_text = foundry.build_parser().format_help()
    assert "ukrainian-data-foundry" in help_text
    assert "prepare" in help_text
    assert "verify" in help_text
