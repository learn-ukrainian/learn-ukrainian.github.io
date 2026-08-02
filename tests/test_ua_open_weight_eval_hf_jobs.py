"""Contracts for the Issue #6273 Hugging Face Jobs Gemma 4 baseline."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.projects.ua_open_weight_eval import hf_jobs_baseline, hf_jobs_worker, suite_cli


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(suite_cli.canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def test_config_freezes_official_qat_artifact_runtime_and_budget() -> None:
    config = hf_jobs_baseline.load_config()
    assert config["model"] == {
        "artifact_bytes": 17651001568,
        "artifact_filename": "gemma-4-31B_q4_0-it.gguf",
        "artifact_sha256": "179cfb99212709597eae5929112cfca677e1bbf566178b479ae1da0c4772874b",
        "license": "apache-2.0",
        "multimodal_projector_used": False,
        "repository": "google/gemma-4-31B-it-qat-q4_0-gguf",
        "revision": "59dde24573e7e61570dba08b18a2e1fe246955ed",
    }
    assert config["runtime"]["container_amd64_digest"] == (
        "sha256:770fe65b2c73ee74a5c42165cf3433de4048cc2cd9c57a937ca4e35aba5aa87b"
    )
    assert config["runtime"]["vllm_version"] == "0.26.0"
    assert config["runtime"]["huggingface_hub_cli_version"] == "1.25.1"
    assert config["pricing"]["usd_per_hour"] == 1.8
    assert config["pricing"]["usd_per_minute"] == 0.03
    assert config["authorization"]["maximum_provider_cost_usd"] == 6.0
    assert config["authorization"]["no_automatic_paid_retry"] is True


def test_balanced_canary_is_deterministic_category_balanced_and_track_covering() -> None:
    config = hf_jobs_baseline.load_config()
    cases = suite_cli.read_jsonl(suite_cli.CASES_PATH)
    first = hf_jobs_baseline.balanced_canary(cases, config)
    second = hf_jobs_baseline.balanced_canary(cases, config)
    assert first == second
    assert first["case_count"] == 100
    assert len(first["item_ids"]) == len(set(first["item_ids"])) == 100
    assert first["category_counts"] == {
        "correct_control": 25,
        "error": 25,
        "protected": 25,
        "unresolved": 25,
    }
    assert set(first["track_membership_counts"]) == set(config["suite"]["tracks"])
    unsigned = {key: value for key, value in first.items() if key != "selection_sha256"}
    assert first["selection_sha256"] == hf_jobs_baseline.sha256_text(hf_jobs_baseline.canonical_json(unsigned))


def test_worker_prompt_and_parser_match_the_reviewed_local_runner() -> None:
    from scripts.projects.ua_open_weight_eval import run_mlx_model

    source = "У записі сказано: «Текст»."
    assert hf_jobs_worker.format_prompt(source) == run_mlx_model.format_prompt(source)
    reply = '{"action":"preserve","output_text":"У записі сказано: «Текст»."}'
    assert hf_jobs_worker.parse_model_reply(reply) == run_mlx_model.parse_model_reply(reply)
    with pytest.raises(hf_jobs_worker.WorkerError, match="exactly one JSON object"):
        hf_jobs_worker.parse_model_reply(reply + " " + reply)


def test_worker_source_packet_and_selection_stay_gold_blind(tmp_path: Path) -> None:
    requests = tmp_path / "requests.jsonl"
    suite_cli.prepare_requests(requests)
    _, rows = hf_jobs_worker.load_requests(requests)
    config = hf_jobs_baseline.load_config()
    selection_value = hf_jobs_baseline.balanced_canary(suite_cli.read_jsonl(suite_cli.CASES_PATH), config)
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps(selection_value), encoding="utf-8")
    selected, _ = hf_jobs_worker.select_requests(rows, selection)
    assert len(selected) == 100
    assert [row["item_id"] for row in selected] == selection_value["item_ids"]
    assert all(not {"expected", "target", "reference", "category", "tracks"}.intersection(row) for row in selected)


def test_tokenizer_verifier_checks_git_blobs_and_lfs_hashes(tmp_path: Path) -> None:
    plain = tmp_path / "config.json"
    plain.write_text("{}\n", encoding="utf-8")
    lfs = tmp_path / "tokenizer.json"
    lfs.write_bytes(b"tokenizer-fixture")
    config = {
        "allowed_files": {
            "config.json": {
                "bytes": plain.stat().st_size,
                "blob_id": hf_jobs_worker.git_blob_id(plain),
            },
            "tokenizer.json": {
                "bytes": lfs.stat().st_size,
                "blob_id": "pointer-id-is-not-the-content-id",
                "sha256": hf_jobs_worker.sha256_file(lfs),
            },
        }
    }
    result = hf_jobs_worker.verify_tokenizer_files(tmp_path, config)
    assert len(result["files"]) == 2
    lfs.write_bytes(b"tampered")
    with pytest.raises(hf_jobs_worker.WorkerError, match=r"byte drift|SHA-256 drift"):
        hf_jobs_worker.verify_tokenizer_files(tmp_path, config)


def test_job_command_is_pinned_private_and_has_no_secret_surface(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = hf_jobs_baseline.load_config()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    hf_cli = tmp_path / "hf"
    hf_cli.write_text("#!/bin/sh\necho 1.25.1\n", encoding="utf-8")
    hf_cli.chmod(0o700)
    manifest = {
        "bundle_sha256": "b" * 64,
        "requests_sha256": "r" * 64,
    }
    monkeypatch.setattr(hf_jobs_baseline, "verify_bundle", lambda _: manifest)
    monkeypatch.setattr(hf_jobs_baseline, "load_config", lambda *args, **kwargs: config)
    command = hf_jobs_baseline.job_command(
        mode="canary",
        namespace="operator",
        bucket="ua-open-weight-eval-6273",
        bundle=bundle,
        hf_cli=hf_cli,
        timeout_seconds=1200,
    )
    joined = " ".join(command)
    assert "--flavor l40sx1" in joined
    assert "--timeout 20m" in joined
    assert config["runtime"]["container_amd64_digest"] in joined
    assert "hf://buckets/operator/ua-open-weight-eval-6273:/output:rw" in joined
    assert "--expose" not in command
    assert "--ssh" not in command
    assert "--json" not in command
    assert "HF_TOKEN" not in joined
    assert "--selection /workspace/canary_selection.json" in joined


def test_launch_preview_is_free_but_execute_prevents_any_second_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state.json"
    command = ["/absolute/hf", "jobs", "run"]
    first = hf_jobs_baseline.launch_once(command=command, mode="canary", state_path=state, execute=False)
    assert first["status"] == "prepared"
    assert not state.exists()
    monkeypatch.setattr(
        hf_jobs_baseline.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, "id=aaaaaaaaaaaaaaaaaaaaaaaa url=https://huggingface.co/jobs/operator/id\n", ""
        ),
    )
    launched = hf_jobs_baseline.launch_once(command=command, mode="canary", state_path=state, execute=True)
    assert launched["status"] == "launched"
    with pytest.raises(hf_jobs_baseline.BaselineError, match="automatic retry is prohibited"):
        hf_jobs_baseline.launch_once(command=command, mode="canary", state_path=state, execute=True)


def test_partial_checkpoint_is_accepted_as_exact_prefix(tmp_path: Path) -> None:
    header = {"schema_version": "checkpoint.v1", "mode": "full"}
    selected = [
        {"item_id": f"item-{index}", "request_sha256": str(index) * 64}
        for index in range(1, 4)
    ]
    records = [
        {
            "item_id": request["item_id"],
            "request_sha256": request["request_sha256"],
            "raw_generation": '{"action":"preserve","output_text":"Текст"}',
            "response": {"action": "preserve", "output_text": "Текст"},
        }
        for request in selected[:2]
    ]
    checkpoint = tmp_path / "checkpoint.jsonl"
    _write_jsonl(checkpoint, [header, *records])
    assert hf_jobs_worker.load_checkpoint(checkpoint, header, selected) == records


def _canary_receipts(config: dict, *, generation_seconds: float, running_seconds: int) -> tuple[dict, dict]:
    worker = {
        "status": "completed",
        "mode": "canary",
        "suite": {"case_count": 100},
        "timing": {
            "download_seconds": 60.0,
            "generation_seconds": generation_seconds,
            "wall_seconds": generation_seconds + 75.0,
            "mean_seconds_per_case": generation_seconds / 100,
        },
        "throughput": {
            "generated_tokens": 2000,
            "generated_tokens_per_second": 2000 / generation_seconds,
            "mean_generated_tokens_per_case": 20.0,
        },
    }
    provider = {
        "stage": "COMPLETED",
        "mode": "canary",
        "provider_running_seconds": running_seconds,
        "provider_derived_cost_usd": running_seconds * config["pricing"]["usd_per_minute"] / 60,
    }
    return worker, provider


def test_projection_applies_25_percent_margin_and_budget_ceiling() -> None:
    config = hf_jobs_baseline.load_config()
    worker, provider = _canary_receipts(config, generation_seconds=120.0, running_seconds=210)
    passed = hf_jobs_baseline.project_full_run(
        worker_receipt=worker,
        provider_receipt=provider,
        config=config,
    )
    assert passed["status"] == "passed"
    assert passed["projection"]["safety_margin_fraction"] == 0.25
    assert passed["authorization"]["combined_projected_cost_usd"] <= 6.0

    worker, provider = _canary_receipts(config, generation_seconds=1100.0, running_seconds=1190)
    blocked = hf_jobs_baseline.project_full_run(
        worker_receipt=worker,
        provider_receipt=provider,
        config=config,
    )
    assert blocked["status"] == "blocked"
    assert blocked["authorization"]["combined_projected_cost_usd"] > 6.0


def test_full_launch_timeout_is_bound_to_passed_projection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = hf_jobs_baseline.load_config()
    worker, provider = _canary_receipts(config, generation_seconds=120.0, running_seconds=210)
    projection = hf_jobs_baseline.project_full_run(
        worker_receipt=worker,
        provider_receipt=provider,
        config=config,
    )
    maximum_timeout = projection["authorization"]["maximum_full_timeout_seconds"]
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    hf_cli = tmp_path / "hf"
    hf_cli.write_text("#!/bin/sh\necho 1.25.1\n", encoding="utf-8")
    hf_cli.chmod(0o700)
    monkeypatch.setattr(
        hf_jobs_baseline,
        "verify_bundle",
        lambda _: {"bundle_sha256": "b" * 64, "requests_sha256": "r" * 64},
    )
    monkeypatch.setattr(hf_jobs_baseline, "load_config", lambda *args, **kwargs: config)
    command = hf_jobs_baseline.job_command(
        mode="full",
        namespace="operator",
        bucket="ua-open-weight-eval-6273",
        bundle=bundle,
        hf_cli=hf_cli,
        timeout_seconds=maximum_timeout,
        projection=projection,
    )
    assert f"--timeout {maximum_timeout // 60}m" in " ".join(command)
    with pytest.raises(hf_jobs_baseline.BaselineError, match="remaining-budget projection"):
        hf_jobs_baseline.job_command(
            mode="full",
            namespace="operator",
            bucket="ua-open-weight-eval-6273",
            bundle=bundle,
            hf_cli=hf_cli,
            timeout_seconds=maximum_timeout + 60,
            projection=projection,
        )


def test_provider_reconciliation_uses_server_duration_and_refuses_endpoints() -> None:
    config = hf_jobs_baseline.load_config()
    manifest = {"bundle_sha256": "b" * 64}
    inspection = {
        "id": "a" * 24,
        "flavor": "l40sx1",
        "labels": {
            "bundle_sha256": "b" * 64,
            "issue": "6273",
            "mode": "canary",
            "suite": config["suite"]["cases_sha256"][:16],
            "timeout_seconds": "1200",
        },
        "status": {"stage": "COMPLETED", "expose_urls": None, "ssh_url": None},
        "durations": {"running_secs": 600},
    }
    receipt = hf_jobs_baseline.reconcile_provider_inspection(
        inspection=inspection,
        mode="canary",
        config=config,
        bundle_manifest=manifest,
    )
    assert receipt["provider_derived_cost_usd"] == 0.3
    inspection["status"]["expose_urls"] = ["https://example.invalid"]
    with pytest.raises(hf_jobs_baseline.BaselineError, match="exposed"):
        hf_jobs_baseline.reconcile_provider_inspection(
            inspection=inspection,
            mode="canary",
            config=config,
            bundle_manifest=manifest,
        )


def _complete_responses(config: dict) -> list[dict]:
    cases = suite_cli.read_jsonl(suite_cli.CASES_PATH)
    rows = [
        {
            "type": "run",
            "schema_version": suite_cli.RESPONSE_SCHEMA,
            "release_id": config["suite"]["release_id"],
            "model": config["model"]["repository"],
            "model_revision": config["model"]["revision"],
            "model_artifact": config["model"]["artifact_filename"],
            "model_sha256": config["model"]["artifact_sha256"],
            "tokenizer": config["tokenizer"]["repository"],
            "tokenizer_revision": config["tokenizer"]["revision"],
            "tokenizer_tree_sha256": "t" * 64,
            "backend": "vllm",
            "backend_version": config["runtime"]["vllm_version"],
            "decoding": {"temperature": 0.0, "seed": 0, "max_tokens": 160, "parse_retries": 2},
            "network_allowed_during_generation": False,
            "closed_api_used": False,
            "job_id": "a" * 24,
            "hardware_flavor": "l40sx1",
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
    return rows


def test_results_package_includes_complete_responses_but_not_private_generations(tmp_path: Path) -> None:
    config = hf_jobs_baseline.load_config()
    responses = tmp_path / "responses.jsonl"
    _write_jsonl(responses, _complete_responses(config))
    worker = {
        "status": "completed",
        "mode": "full",
        "job": {"id": "a" * 24},
        "suite": {"requests_sha256": "q" * 64},
        "model": config["model"],
        "tokenizer": {
            "repository": config["tokenizer"]["repository"],
            "revision": config["tokenizer"]["revision"],
            "tree_sha256": "t" * 64,
            "files": [],
        },
        "environment": {
            "container_amd64_digest": config["runtime"]["container_amd64_digest"],
            "runner_sha256": "r" * 64,
            "versions": {"vllm": config["runtime"]["vllm_version"]},
        },
        "decoding": {"temperature": 0.0, "seed": 0, "max_tokens": 160, "parse_retries": 2},
        "timing": {"wall_seconds": 1000.0},
        "throughput": {"generated_tokens": 10000, "generated_tokens_per_second": 10.0},
        "outputs": {"responses_sha256": hf_jobs_baseline.sha256_file(responses)},
        "facts": {
            "closed_model_judge_used": False,
            "foundry_learning_eligible": False,
            "global_quality_score_produced": False,
            "model_weights_uploaded": False,
            "training_performed": False,
        },
    }
    provider = {
        "schema_version": "ua_open_weight_eval_hf_jobs_provider_receipt.v1",
        "job_id": "a" * 24,
        "mode": "full",
        "stage": "COMPLETED",
        "provider_derived_cost_usd": 3.0,
        "provider_running_seconds": 6000,
    }
    worker_path = tmp_path / "worker.json"
    provider_path = tmp_path / "provider.json"
    worker_path.write_text(json.dumps(worker), encoding="utf-8")
    provider_path.write_text(json.dumps(provider), encoding="utf-8")
    output = tmp_path / "public"
    result = hf_jobs_baseline.package_results(
        responses=responses,
        worker_receipt_path=worker_path,
        provider_receipt_path=provider_path,
        output_dir=output,
    )
    assert result["status"] == "passed"
    assert result["responses"] == 4000
    public_receipt = json.loads((output / "run_receipt.public.json").read_text(encoding="utf-8"))
    assert public_receipt["environment"]["launch_client"] == {
        "name": "huggingface_hub",
        "version": "1.25.1",
    }
    assert {path.name for path in output.iterdir()} == hf_jobs_baseline.PUBLIC_FILES
    published = suite_cli.read_jsonl(output / "responses.jsonl")
    assert len(published) == 4001
    assert all("raw_generation" not in row for row in published)
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert len(report["tracks"]) == 14
    assert report["scoring"]["global_quality_score"] is None
    assert len((output / "metrics.jsonl").read_text(encoding="utf-8").splitlines()) == 56

    (output / "report.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        hf_jobs_baseline.BaselineError,
        match=r"manifest (byte|hash) drift|checksum drift",
    ):
        hf_jobs_baseline.verify_results_package(output)
