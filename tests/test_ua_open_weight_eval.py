"""Regression tests for the broad open-weight Ukrainian evaluation release."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import model_view_exporter
from scripts.projects.ua_open_weight_eval import suite_cli

ROOT = Path(__file__).resolve().parents[1]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(suite_cli.canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def test_release_is_balanced_reproducible_and_keeps_upstreams_frozen() -> None:
    receipt = suite_cli.verify_release()
    cases = suite_cli.read_jsonl(suite_cli.CASES_PATH)
    assert len(cases) == 4000
    assert Counter(case["category"] for case in cases) == {
        "correct_control": 1000,
        "error": 1000,
        "protected": 1000,
        "unresolved": 1000,
    }
    assert {track for case in cases for track in case["tracks"]} == set(
        suite_cli.read_json(suite_cli.CONFIG_PATH)["tracks"]
    )
    assert receipt["policy"] == {
        "closed_api_required": False,
        "closed_model_judge_allowed": False,
        "foundry_learning_eligible": False,
        "human_gold_anchor": "ua_eval_harness.v0.1.1",
        "human_gold_anchor_mutated": False,
        "parked_v0.2_mutated": False,
        "single_quality_score_produced": False,
    }


def test_source_only_requests_expose_no_gold(tmp_path: Path) -> None:
    output = tmp_path / "requests.jsonl"
    summary = suite_cli.prepare_requests(output)
    rows = suite_cli.read_jsonl(output)
    assert summary["requests"] == 4000
    assert rows[0]["gold_fields_supplied"] == []
    assert rows[0]["input_fields"] == [
        "item_id",
        "source",
        "source_sha256",
        "instruction_sha256",
    ]
    forbidden = {"expected", "target", "targets", "reference", "references", "edit", "edits"}
    assert all(not forbidden.intersection(row) for row in rows[1:])


def test_saved_output_scoring_is_per_track_without_global_score(tmp_path: Path) -> None:
    cases = suite_cli.read_jsonl(suite_cli.CASES_PATH)
    responses = tmp_path / "responses.jsonl"
    rows = [
        {
            "type": "run",
            "schema_version": suite_cli.RESPONSE_SCHEMA,
            "run_id": "deterministic-contract-fixture",
            "model": "local-fixture",
        }
    ]
    rows.extend(
        {
            "item_id": case["case_id"],
            "action": case["expected"]["action"],
            "output_text": case["expected"]["accepted_texts"][0],
        }
        for case in cases
    )
    _write_jsonl(responses, rows)
    output = tmp_path / "report.json"
    report = suite_cli.score_saved(responses, output)
    assert report["scoring"]["global_quality_score"] is None
    assert report["scoring"]["global_score_prohibited"] is True
    assert report["scoring"]["closed_model_judge_used"] is False
    assert set(report["tracks"]) == set(suite_cli.read_json(suite_cli.CONFIG_PATH)["tracks"])
    assert all(
        metric["action_accuracy"] in {1.0, None}
        for track in report["tracks"].values()
        for metric in track["categories"].values()
    )


def test_local_config_rejects_closed_services_and_requires_existing_weight(tmp_path: Path) -> None:
    closed = tmp_path / "closed.json"
    closed.write_text(
        json.dumps(
            {
                "backend": "custom_local",
                "provider": "openai",
                "model_path": str(tmp_path / "missing"),
                "model_revision": "x",
                "model_sha256": "0" * 64,
                "network_allowed": False,
                "command": ["runner", "{requests}", "{responses}"],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(suite_cli.SuiteError, match="provider must be local"):
        suite_cli.validate_run_config(closed)

    missing = tmp_path / "missing.json"
    missing.write_text(
        json.dumps(
            {
                "backend": "llama.cpp",
                "provider": "local",
                "model_path": str(tmp_path / "missing-model"),
                "model_revision": "pinned",
                "model_sha256": "0" * 64,
                "network_allowed": False,
                "command": ["runner", "{requests}", "{responses}"],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(suite_cli.SuiteError, match="already exist"):
        suite_cli.validate_run_config(missing)


def test_local_config_hashes_model_directories_and_allows_open_weight_gpt_oss(tmp_path: Path) -> None:
    model_path = tmp_path / "openai-gpt-oss-local"
    model_path.mkdir()
    (model_path / "config.json").write_text('{"model_type":"gpt_oss"}\n', encoding="utf-8")
    (model_path / "weights.bin").write_bytes(b"project-test-weight-fixture")
    runner = tmp_path / "local-runner"
    runner.write_text("fixture executable", encoding="utf-8")
    config_path = tmp_path / "local.json"
    config_path.write_text(
        json.dumps(
            {
                "backend": "custom_local",
                "provider": "local",
                "model_path": str(model_path),
                "model_revision": "consumer-pinned",
                "model_sha256": suite_cli.sha256_path(model_path),
                "network_allowed": False,
                "command": [str(runner), "{requests}", "{responses}"],
            }
        ),
        encoding="utf-8",
    )
    assert suite_cli.validate_run_config(config_path)["model_path"] == str(model_path)

    (model_path / "weights.bin").write_bytes(b"tampered")
    with pytest.raises(suite_cli.SuiteError, match="model path hash mismatch"):
        suite_cli.validate_run_config(config_path)


def test_foundry_firewall_loads_every_broad_eval_case() -> None:
    cases = suite_cli.read_jsonl(suite_cli.CASES_PATH)
    registry = model_view_exporter.build_exclusion_registry(
        v011_manifest=model_view_exporter.DEFAULT_V011_MANIFEST,
        v02_packet=model_view_exporter.DEFAULT_V02_PACKET,
    )
    assert any(
        artifact["logical_path"] == "data/projects/ua_open_weight_eval/v0.1.0/cases.jsonl"
        for artifact in registry.artifacts
    )
    assert all(registry.match(case["source"]).matched for case in cases)


def test_saved_response_schema_is_valid() -> None:
    schema = suite_cli.read_json(suite_cli.RELEASE_ROOT / "saved_response.schema.json")
    Draft202012Validator.check_schema(schema)
