"""Regression tests for the broad open-weight Ukrainian evaluation release."""

from __future__ import annotations

import json
import zipfile
from collections import Counter
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import model_view_exporter
from scripts.projects.ua_open_weight_eval import run_mlx_model, suite_cli

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
    assert [row["item_id"] for row in rows[1:]] == [suite_cli.request_item_id(position) for position in range(1, 4001)]
    assert all(
        not {"error", "correct_control", "protected", "unresolved"}.intersection(row["item_id"].split("-"))
        for row in rows[1:]
    )


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
            "item_id": suite_cli.request_item_id(position),
            "action": case["expected"]["action"],
            "output_text": case["expected"]["accepted_texts"][0],
        }
        for position, case in enumerate(cases, 1)
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


def test_publication_package_is_complete_rights_mapped_and_reproducible(tmp_path: Path) -> None:
    source_revision = "a" * 40
    first = tmp_path / "first"
    first_archive = tmp_path / "first.zip"
    receipt = suite_cli.package_publication(
        output_dir=first,
        source_revision=source_revision,
        archive_path=first_archive,
    )
    assert receipt["status"] == "passed"
    assert receipt["release_tag"] == "ua-open-weight-eval-v0.1.0"
    assert receipt["source_revision"] == source_revision

    manifest = suite_cli.read_json(first / "PUBLICATION_MANIFEST.json")
    file_names = {item["output_path"] for item in manifest["files"]}
    assert "cases.jsonl" in file_names
    assert "THIRD_PARTY_NOTICES.md" in file_names
    assert "README.md" in file_names
    assert "run_mlx_model.py" in file_names
    assert manifest["case_rights"]["rules"] == [
        {
            "case_id_prefix": "uaw-011-",
            "cases": 2000,
            "license_expression": "CC-BY-4.0",
            "notice": "UA-GEC-derived error and control rows; retain attribution and modification notice.",
        },
        {
            "case_id_prefix": "uaw-silver-",
            "cases": 2000,
            "license_expression": "MIT",
            "notice": "Project-authored controlled or source-backed silver rows; external evidence bytes are not included.",
        },
    ]
    assert all("provider raw output" not in item["source_path"] for item in manifest["files"])

    second = tmp_path / "second"
    second_archive = tmp_path / "second.zip"
    suite_cli.package_publication(
        output_dir=second,
        source_revision=source_revision,
        archive_path=second_archive,
    )
    assert suite_cli.sha256_file(first_archive) == suite_cli.sha256_file(second_archive)
    with zipfile.ZipFile(first_archive) as archive:
        assert all(name.startswith("ua-open-weight-eval-v0.1.0/") for name in archive.namelist())


def test_publication_verifier_rejects_tampering_and_extra_bytes(tmp_path: Path) -> None:
    package = tmp_path / "package"
    suite_cli.package_publication(output_dir=package, source_revision="b" * 40)
    (package / "cases.jsonl").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(suite_cli.SuiteError, match=r"byte count drift|hash drift"):
        suite_cli.verify_publication_package(package)

    package = tmp_path / "package-extra"
    suite_cli.package_publication(output_dir=package, source_revision="b" * 40)
    (package / "raw-provider-output.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(suite_cli.SuiteError, match="missing or extra files"):
        suite_cli.verify_publication_package(package)


def test_hugging_face_card_declares_test_split_and_discovery_metadata() -> None:
    card = (suite_cli.PUBLICATION_DOC_ROOT / "HUGGING_FACE_README.md").read_text(encoding="utf-8")
    _, metadata_text, _ = card.split("---", 2)
    metadata = yaml.safe_load(metadata_text)
    assert metadata["language"] == ["uk"]
    assert metadata["license"] == ["cc-by-4.0", "mit"]
    assert metadata["configs"] == [
        {
            "config_name": "default",
            "data_files": [{"path": "cases.jsonl", "split": "test"}],
        }
    ]
    assert "evaluation" in metadata["tags"]


def test_mlx_runner_loads_only_source_packet_and_resumes(tmp_path: Path) -> None:
    requests_path = tmp_path / "requests.jsonl"
    suite_cli.prepare_requests(requests_path)
    packet = run_mlx_model.read_jsonl(requests_path)
    packet[0]["case_count"] = 2
    packet = packet[:3]
    packet[0]["case_count"] = 4000
    fixture_request = packet[1]
    packet.extend({**fixture_request, "item_id": f"fixture-{index:04d}"} for index in range(3998))
    for row in packet[3:]:
        row["source_sha256"] = run_mlx_model.sha256_text(row["source"])
        payload = {
            "item_id": row["item_id"],
            "source": row["source"],
            "source_sha256": row["source_sha256"],
            "instruction_sha256": row["instruction_sha256"],
        }
        row["request_sha256"] = run_mlx_model.sha256_text(run_mlx_model.canonical_json(payload))
    _write_jsonl(requests_path, packet)

    model = tmp_path / "model"
    model.mkdir()
    (model / "config.json").write_text("{}\n", encoding="utf-8")
    state = tmp_path / "state.jsonl"
    responses = tmp_path / "responses.jsonl"
    args = run_mlx_model.parse_args(
        [
            "--requests",
            str(requests_path),
            "--responses",
            str(responses),
            "--state",
            str(state),
            "--model",
            str(model),
            "--model-id",
            "fixture/model",
            "--model-revision",
            "a" * 40,
            "--model-sha256",
            run_mlx_model.sha256_path(model),
            "--progress-every",
            "4000",
        ]
    )
    generated = 0

    def generator(_: str) -> str:
        nonlocal generated
        generated += 1
        return '{"action":"preserve","output_text":"fixture"}'

    assert run_mlx_model.run(args, generator=generator)["responses"] == 4000
    assert generated == 4000
    assert run_mlx_model.run(args, generator=generator)["responses"] == 4000
    assert generated == 4000
    response_rows = run_mlx_model.read_jsonl(responses)
    assert response_rows[0]["closed_api_used"] is False
    assert len(response_rows) == 4001


def test_mlx_runner_rejects_gold_and_ambiguous_model_replies(tmp_path: Path) -> None:
    assert run_mlx_model.parse_model_reply('```json\n{"action":"preserve","output_text":"Текст."}\n```') == {
        "action": "preserve",
        "output_text": "Текст.",
    }
    with pytest.raises(run_mlx_model.RunnerError, match="exactly one JSON object"):
        run_mlx_model.parse_model_reply(
            '{"action":"preserve","output_text":"A"} {"action":"correct","output_text":"B"}'
        )
    prompt = run_mlx_model.format_prompt("Текст.")
    assert "correct_control" not in prompt
    assert "uaw-request" not in prompt

    request_path = tmp_path / "gold.jsonl"
    instruction = "fixture"
    header = {
        "type": "request_run",
        "schema_version": run_mlx_model.REQUEST_SCHEMA,
        "release_id": "fixture",
        "case_count": 4000,
        "gold_fields_supplied": [],
        "input_fields": ["item_id", "source", "source_sha256", "instruction_sha256"],
        "instruction": instruction,
        "instruction_sha256": run_mlx_model.sha256_text(instruction),
    }
    source = "Текст."
    payload = {
        "item_id": "fixture-0000",
        "source": source,
        "source_sha256": run_mlx_model.sha256_text(source),
        "instruction_sha256": header["instruction_sha256"],
    }
    requests = []
    for index in range(4000):
        item_payload = {**payload, "item_id": f"fixture-{index:04d}"}
        requests.append(
            {
                "type": "request",
                **item_payload,
                "request_sha256": run_mlx_model.sha256_text(run_mlx_model.canonical_json(item_payload)),
                "expected": "secret",
            }
        )
    _write_jsonl(request_path, [header, *requests])
    with pytest.raises(run_mlx_model.RunnerError, match="gold field"):
        run_mlx_model.load_requests(request_path)
