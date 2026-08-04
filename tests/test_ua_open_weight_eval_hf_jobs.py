"""Contracts for the Issue #6273 Hugging Face Jobs Gemma 4 baseline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.projects.ua_open_weight_eval import (
    hf_jobs_baseline,
    hf_jobs_transport,
    hf_jobs_worker,
    response_integrity,
    suite_cli,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(suite_cli.canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def _write_fake_hf_cli(path: Path) -> None:
    path.write_text(
        '#!/bin/sh\nif [ "$1" = "--version" ]; then\n  echo 1.25.1\nelse\n  exit 1\nfi\n',
        encoding="utf-8",
    )
    path.chmod(0o700)


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
    assert config["canary"]["maximum_cost_usd"] == 0.6
    assert config["authorization"]["prior_provider_cost_usd"] == 3.750167
    assert config["authorization"]["incurred_provider_costs"][-1] == {
        "job_id": "6a701872a00abefd4b28ea7f",
        "mode": "full",
        "provider_billed_minutes": 14,
        "provider_derived_cost_usd": 0.42,
        "provider_running_seconds": 803,
        "stage": "COMPLETED",
    }
    assert config["authorization"]["recoverable_execution_retries_authorized"] is True
    assert config["authorization"]["validated_cpu_transport"]["job_id"] == "6a6fbf1b6b79c09949c1fa46"
    assert config["authorization"]["no_automatic_paid_retry"] is False
    assert config["runner"]["checkpoint_upload_every_cases"] == 25
    assert config["runner"]["structured_outputs"] == "json_schema"
    assert config["runner"]["structured_outputs_backend"] == "xgrammar"
    assert config["runner"]["structured_outputs_disable_any_whitespace"] is True
    assert config["runner"]["structured_outputs_ignore_eos_until_complete"] is True
    assert config["runner"]["structured_outputs_max_output_text_chars"] == 768
    assert config["runner"]["structured_outputs_escape_raw_control_tokens"] is True
    assert config["transport"] == {
        "cpu_preflight": {
            "container_amd64_digest": "sha256:8859bd6ca943079262c27e38b7119cdacede77c463139a15651dd340087a6cc9",
            "container_image": "python:3.12.8-slim",
            "flavor": "cpu-basic",
            "maximum_cost_usd": 0.001,
            "timeout_seconds": 300,
            "usd_per_hour": 0.01,
        },
        "mode": "private-dataset-direct-api",
        "mounted_volumes": 0,
        "staging_dataset_suffix": "ua-open-weight-eval-staging-6273",
    }


def test_invalid_run_disposition_requires_private_retention_and_semantic_publication_gate(
    tmp_path: Path,
) -> None:
    disposition = hf_jobs_baseline.load_disposition()
    retained = disposition["retained_artifact"]
    assert retained["visibility"] == "private"
    assert retained["repository_deleted"] is False
    assert retained["visibility_receipt"]["authenticated_repo_info_private"] is True
    assert retained["visibility_receipt"]["content_revision_preserved"] is True
    assert disposition["public_transparency"]["incident_record"].startswith("https://github.com/")
    assert disposition["publication_policy"] == {
        "scope": "future_hugging_face_result_repositories",
        "required_gate": "actual_saved_outputs_pass_source_aware_response_integrity",
        "required_verification_schema": "ua_open_weight_eval_results_verification.v2",
        "failure_action": (
            "keep result repository private and publish only the incident explanation and hashes on GitHub"
        ),
    }

    disposition["retained_artifact"]["visibility"] = "public"
    drifted = tmp_path / "disposition.json"
    drifted.write_text(json.dumps(disposition), encoding="utf-8")
    with pytest.raises(hf_jobs_baseline.BaselineError, match="must remain private"):
        hf_jobs_baseline.load_disposition(drifted)


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
    for corrupt in (
        reply[:-2] + "\x00" + reply[-2:],
        reply[:-2] + "\x01" + reply[-2:],
        reply[:-2] + "\x06\x15" + reply[-2:] + "</thead>",
        reply[:-2] + "\x00\x01\u04c0\u05ea" + reply[-2:] + "</thead>",
        reply.replace("Текст", "Те\x00кст"),
    ):
        with pytest.raises(hf_jobs_worker.WorkerError, match="exactly one JSON object"):
            hf_jobs_worker.parse_model_reply(corrupt)
    with pytest.raises(hf_jobs_worker.WorkerError, match="exactly one JSON object"):
        hf_jobs_worker.parse_model_reply(reply + " " + reply)


def test_response_integrity_is_source_aware_and_fail_closed(tmp_path: Path) -> None:
    sources = {
        "one": "Точний текст.",
        "two": "Архівний \x00 [multimodal] текст.",
    }
    valid = {
        "one": {"action": "correct", "output_text": "Виправлений текст."},
        "two": {"action": "preserve", "output_text": sources["two"]},
    }
    assert response_integrity.require_response_integrity(sources=sources, responses=valid)["status"] == "passed"

    corruptions = (
        {"one": {"action": "preserve", "output_text": "Точний текст. "}},
        {"one": {"action": "correct", "output_text": "Текст <unused42>"}},
        {"one": {"action": "correct", "output_text": "Текст </tr><pad>"}},
        {"one": {"action": "correct", "output_text": "Текст\x00"}},
    )
    for responses in corruptions:
        with pytest.raises(response_integrity.IntegrityError, match="semantic integrity failed"):
            response_integrity.require_response_integrity(sources=sources, responses=responses)

    requests = tmp_path / "requests.jsonl"
    responses = tmp_path / "responses.jsonl"
    _write_jsonl(
        requests,
        [
            {"type": "request_run"},
            {"type": "request", "item_id": "one", "source": sources["one"]},
        ],
    )
    _write_jsonl(
        responses,
        [{"type": "run"}, {"item_id": "one", "action": "correct", "output_text": "<unused7>"}],
    )
    assert response_integrity.main(["--responses", str(responses), "--requests", str(requests)]) == 2

    _write_jsonl(responses, [{"type": "run"}])
    assert response_integrity.main(["--responses", str(responses), "--requests", str(requests)]) == 2


def test_worker_structured_output_schema_keeps_the_strict_response_contract() -> None:
    schema = hf_jobs_worker.RESPONSE_JSON_SCHEMA
    frozen_sources = [str(case["source"]) for case in suite_cli.read_jsonl(suite_cli.CASES_PATH)]
    assert max(map(len, frozen_sources)) == 703
    assert max(map(len, frozen_sources)) < hf_jobs_worker.MAX_OUTPUT_TEXT_CHARS
    assert schema == {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["abstain", "correct", "preserve"]},
            "output_text": {"type": "string", "maxLength": 768},
        },
        "required": ["action", "output_text"],
        "additionalProperties": False,
    }
    assert set(schema["properties"]["action"]["enum"]) == hf_jobs_worker.ALLOWED_ACTIONS

    class Capture:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs

    config = hf_jobs_baseline.load_config()
    sampling = hf_jobs_worker.build_sampling_params(
        config["runner"], sampling_params_type=Capture, structured_outputs_type=Capture
    )
    assert sampling.kwargs["temperature"] == 0.0
    assert sampling.kwargs["seed"] == 0
    assert sampling.kwargs["ignore_eos"] is True
    assert sampling.kwargs["max_tokens"] == 160
    structured = sampling.kwargs["structured_outputs"]
    assert isinstance(structured, Capture)
    assert structured.kwargs == {"json": schema}

    model = hf_jobs_worker.build_llm(
        model_path=Path("/verified/model.gguf"),
        tokenizer_root=Path("/verified/tokenizer"),
        runner=config["runner"],
        llm_type=Capture,
    )
    assert model.kwargs["structured_outputs_config"] == {
        "backend": "xgrammar",
        "disable_any_whitespace": True,
    }


def test_worker_error_keeps_raw_diagnostics_private() -> None:
    diagnostic = {"item_id": "uaw-request-0001", "attempts": [{"raw_generation": "private"}]}
    error = hf_jobs_worker.WorkerError("parse failed", private_diagnostic=diagnostic)
    assert str(error) == "parse failed"
    assert error.private_diagnostic == diagnostic


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


def test_text_runtime_config_is_derived_after_verification_without_mutating_source(tmp_path: Path) -> None:
    tokenizer = tmp_path / "tokenizer"
    tokenizer.mkdir()
    source_config = {
        "architectures": ["Gemma4ForConditionalGeneration"],
        "model_type": "gemma4",
        "text_config": {
            "dtype": "bfloat16",
            "model_type": "gemma4_text",
            "num_hidden_layers": 60,
        },
        "vision_config": {"model_type": "gemma4_vision"},
    }
    (tokenizer / "config.json").write_text(json.dumps(source_config), encoding="utf-8")
    (tokenizer / "tokenizer_config.json").write_text(
        json.dumps({"tokenizer_class": "GemmaTokenizer"}), encoding="utf-8"
    )
    (tokenizer / "tokenizer.json").write_text("{}", encoding="utf-8")
    runtime_root, runtime_hash, runtime_tokenizer_hash = hf_jobs_worker.prepare_text_runtime_tokenizer(tokenizer)
    assert json.loads((tokenizer / "config.json").read_text(encoding="utf-8")) == source_config
    runtime_config = json.loads((runtime_root / "config.json").read_text(encoding="utf-8"))
    assert runtime_config == {
        "architectures": ["Gemma4ForCausalLM"],
        "dtype": "bfloat16",
        "model_type": "gemma4_text",
        "num_hidden_layers": 60,
    }
    assert "vision_config" not in runtime_config
    assert runtime_hash == hf_jobs_worker.sha256_file(runtime_root / "config.json")
    runtime_tokenizer_config = json.loads((runtime_root / "tokenizer_config.json").read_text(encoding="utf-8"))
    assert runtime_tokenizer_config["fix_mistral_regex"] is True
    assert runtime_tokenizer_hash == hf_jobs_worker.sha256_file(runtime_root / "tokenizer_config.json")


def test_gemma4_text_runtime_uses_the_pinned_gguf_architecture_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gguf = SimpleNamespace(MODEL_ARCH_NAMES={"GEMMA4": "gemma4"})
    monkeypatch.setitem(sys.modules, "gguf", gguf)
    receipt = hf_jobs_worker.enable_gemma4_text_gguf_alias()
    assert gguf.MODEL_ARCH_NAMES["GEMMA4"] == "gemma4_text"
    assert receipt == "GEMMA4:gemma4->gemma4_text"


def test_job_commands_use_hash_first_private_transport_without_volumes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = hf_jobs_baseline.load_config()
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    hf_cli = tmp_path / "hf"
    _write_fake_hf_cli(hf_cli)
    manifest = {
        "bundle_sha256": "b" * 64,
        "requests_sha256": "r" * 64,
        "source_commit": "d" * 40,
    }
    preflight_gate = {
        "schema_version": "ua_open_weight_eval_hf_jobs_canary_gate.v1",
        "status": "passed",
        "bundle_sha256": "b" * 64,
        "transport_repository": "operator/ua-open-weight-eval-staging-6273",
        "transport_revision": "a" * 40,
    }
    preflight_gate["gate_sha256"] = hf_jobs_baseline.sha256_text(hf_jobs_baseline.canonical_json(preflight_gate))
    monkeypatch.setattr(hf_jobs_baseline, "verify_bundle", lambda _: manifest)
    monkeypatch.setattr(hf_jobs_baseline, "load_config", lambda *args, **kwargs: config)
    command = hf_jobs_baseline.job_command(
        mode="canary",
        namespace="operator",
        bundle=bundle,
        transport_repo="operator/ua-open-weight-eval-staging-6273",
        transport_revision="a" * 40,
        transport_prefix=f"bundles/{'b' * 64}",
        hf_cli=hf_cli,
        timeout_seconds=1200,
        preflight_gate=preflight_gate,
    )
    joined = " ".join(command)
    assert "--flavor l40sx1" in joined
    assert "--timeout 20m" in joined
    assert config["runtime"]["container_amd64_digest"] in joined
    assert "operator/ua-open-weight-eval-staging-6273" in joined
    assert "--secrets HF_TOKEN" in joined
    assert "HF_TOKEN=" not in joined
    assert "--env UA_EVAL_HARDWARE_FLAVOR=l40sx1" in joined
    assert "--env ACCELERATOR=" not in joined
    assert "--volume" not in command
    assert "-v" not in command
    assert "hf://buckets/" not in joined
    assert "--expose" not in command
    assert "--ssh" not in command
    assert "--json" not in command
    separator = command.index("--")
    assert command[separator + 1] == (
        f"{config['runtime']['container_image']}@{config['runtime']['container_amd64_digest']}"
    )
    assert command[separator + 2 : separator + 4] == ["sh", "-lc"]
    shell_command = command[separator + 4]
    assert "python3 -c" in shell_command
    assert " python -c" not in shell_command
    assert "os.execvp('python3',['python3'" in hf_jobs_baseline._bootstrap_source()
    tampered_gate = {**preflight_gate, "preflight_cost_usd": 0.002}
    with pytest.raises(hf_jobs_baseline.BaselineError, match="gate SHA-256 drift"):
        hf_jobs_baseline.job_command(
            mode="canary",
            namespace="operator",
            bundle=bundle,
            transport_repo="operator/ua-open-weight-eval-staging-6273",
            transport_revision="a" * 40,
            transport_prefix=f"bundles/{'b' * 64}",
            hf_cli=hf_cli,
            timeout_seconds=1200,
            preflight_gate=tampered_gate,
        )

    preflight = hf_jobs_baseline.job_command(
        mode="preflight",
        namespace="operator",
        bundle=bundle,
        transport_repo="operator/ua-open-weight-eval-staging-6273",
        transport_revision="a" * 40,
        transport_prefix=f"bundles/{'b' * 64}",
        hf_cli=hf_cli,
        timeout_seconds=300,
    )
    preflight_joined = " ".join(preflight)
    assert "--flavor cpu-basic" in preflight_joined
    assert "--timeout 5m" in preflight_joined
    assert config["transport"]["cpu_preflight"]["container_amd64_digest"] in preflight_joined
    assert "--volume" not in preflight
    assert "--secrets HF_TOKEN" in preflight_joined
    assert "UA_EVAL_HARDWARE_FLAVOR=" not in preflight_joined
    with pytest.raises(hf_jobs_baseline.BaselineError, match="passed CPU preflight gate"):
        hf_jobs_baseline.job_command(
            mode="canary",
            namespace="operator",
            bundle=bundle,
            transport_repo="operator/ua-open-weight-eval-staging-6273",
            transport_revision="a" * 40,
            transport_prefix=f"bundles/{'b' * 64}",
            hf_cli=hf_cli,
            timeout_seconds=1200,
        )
    with pytest.raises(hf_jobs_baseline.BaselineError, match="bound to the bundle"):
        hf_jobs_baseline.job_command(
            mode="canary",
            namespace="operator",
            bundle=bundle,
            transport_repo="operator/ua-open-weight-eval-staging-6273",
            transport_revision="a" * 40,
            transport_prefix="bundles/deadbeef",
            hf_cli=hf_cli,
            timeout_seconds=1200,
            preflight_gate=preflight_gate,
        )


def test_launch_preview_is_free_but_invalid_disposition_blocks_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state.json"
    command = ["/absolute/hf", "jobs", "run"]
    first = hf_jobs_baseline.launch_once(command=command, mode="canary", state_path=state, execute=False)
    assert first["status"] == "prepared"
    assert not state.exists()
    monkeypatch.setattr(hf_jobs_baseline.subprocess, "run", lambda *args, **kwargs: pytest.fail("launched"))
    with pytest.raises(hf_jobs_baseline.BaselineError, match="blocked by the invalid-run disposition"):
        hf_jobs_baseline.launch_once(command=command, mode="canary", state_path=state, execute=True)
    assert not state.exists()


def test_transport_manifest_and_cpu_receipt_are_hash_bound_and_direct_uploaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    files = [
        {"path": name, "bytes": 1, "sha256": "a" * 64}
        for name in (
            "canary_selection.json",
            "hf_jobs_transport.py",
            "hf_jobs_worker.py",
            "requests.jsonl",
            "run_config.json",
        )
    ]
    unsigned = {
        "schema_version": "ua_open_weight_eval_hf_jobs_bundle.v1",
        "issue": 6273,
        "files": files,
    }
    digest = hf_jobs_transport.sha256_bytes(hf_jobs_transport.canonical_json(unsigned).encode())
    manifest = {**unsigned, "bundle_sha256": digest}
    assert hf_jobs_transport.verify_manifest(manifest, digest) == files
    with pytest.raises(hf_jobs_transport.TransportError, match="digest drift"):
        hf_jobs_transport.verify_manifest(manifest, "b" * 64)

    monkeypatch.setenv("JOB_ID", "c" * 24)
    monkeypatch.delenv("ACCELERATOR", raising=False)
    monkeypatch.setenv("HF_TOKEN", "not-a-real-token")
    monkeypatch.setattr(hf_jobs_transport, "upload_json", lambda **kwargs: "d" * 40)
    args = SimpleNamespace(
        transport_repo="operator/ua-open-weight-eval-staging-6273",
        transport_revision="e" * 40,
        transport_prefix=f"bundles/{digest}",
        artifact_prefix=f"artifacts/{digest}/preflight",
        bundle_sha256=digest,
    )
    receipt = hf_jobs_transport.run_preflight(args, files)
    assert receipt["status"] == "passed"
    assert receipt["accelerator_environment"] is None
    assert receipt["transport"]["mounted_volumes"] == 0
    assert receipt["transport"]["all_hashes_verified"] is True
    assert receipt["facts"]["receipt_uploaded_directly"] is True
    monkeypatch.setenv("ACCELERATOR", "l40sx1")
    with pytest.raises(hf_jobs_transport.TransportError, match="GPU accelerator"):
        hf_jobs_transport.run_preflight(args, files)


def test_transport_spawns_gpu_worker_with_available_python3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = hf_jobs_baseline.load_config()
    (tmp_path / "run_config.json").write_text(json.dumps(config), encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(command: list[str], *, check: bool) -> subprocess.CompletedProcess:
        assert check is False
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(hf_jobs_transport.subprocess, "run", fake_run)
    args = SimpleNamespace(
        mode="canary",
        requests_sha256="r" * 64,
        transport_repo="operator/ua-open-weight-eval-staging-6273",
        artifact_prefix="artifacts/bundle/canary",
    )
    assert hf_jobs_transport.run_worker(args, tmp_path) == 0
    assert calls[0][:4] == ["uv", "pip", "install", "--system"]
    assert calls[1][0] == "python3"
    assert calls[1][1] == str(tmp_path / "hf_jobs_worker.py")


def test_direct_artifact_uploads_fail_closed_if_dataset_is_not_private(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import huggingface_hub

    class PublicRepoApi:
        def __init__(self, *, token: str) -> None:
            assert token == "not-a-real-token"

        def repo_info(self, *, repo_id: str, repo_type: str) -> SimpleNamespace:
            assert repo_id == "operator/ua-open-weight-eval-staging-6273"
            assert repo_type == "dataset"
            return SimpleNamespace(private=False)

    monkeypatch.setenv("HF_TOKEN", "not-a-real-token")
    monkeypatch.setattr(huggingface_hub, "HfApi", PublicRepoApi)
    with pytest.raises(hf_jobs_transport.TransportError, match="not private"):
        hf_jobs_transport.upload_json(
            repo_id="operator/ua-open-weight-eval-staging-6273",
            path_in_repo="artifacts/receipt.json",
            value={"harmless": True},
            commit_message="test receipt",
        )
    with pytest.raises(hf_jobs_worker.WorkerError, match="not private"):
        hf_jobs_worker.HubArtifactStore(
            "operator/ua-open-weight-eval-staging-6273",
            "artifacts/bundle/canary",
        )


def test_partial_checkpoint_is_accepted_as_exact_prefix(tmp_path: Path) -> None:
    header = {"schema_version": "checkpoint.v1", "mode": "full"}
    selected = [
        {"item_id": f"item-{index}", "request_sha256": str(index) * 64, "source": "Текст"} for index in range(1, 4)
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


def test_generation_totals_keep_resumed_time_and_tokens_in_throughput() -> None:
    records = [
        {"generated_tokens": 10, "generation_seconds": 4.0},
        {"generated_tokens": 20, "generation_seconds": 6.0},
    ]
    assert hf_jobs_worker.generation_totals(records, resumed_count=1) == {
        "generated_tokens": 30,
        "generation_seconds": 10.0,
        "current_generation_seconds": 6.0,
        "resumed_case_count": 1,
    }
    with pytest.raises(hf_jobs_worker.WorkerError, match="metrics are invalid"):
        hf_jobs_worker.generation_totals([{"generated_tokens": 10}], resumed_count=0)


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
        "response_integrity": {
            "status": "passed",
            "checked_rows": 100,
            "violation_rows": 0,
            "copy_contract_violation_rows": 0,
            "reserved_marker_violation_rows": 0,
            "introduced_control_violation_rows": 0,
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
    config["authorization"]["prior_provider_cost_usd"] = 1.740167
    worker, provider = _canary_receipts(config, generation_seconds=120.0, running_seconds=210)
    worker["timing"]["current_generation_seconds"] = 60.0
    passed = hf_jobs_baseline.project_full_run(
        worker_receipt=worker,
        provider_receipt=provider,
        config=config,
    )
    assert passed["status"] == "passed"
    assert passed["projection"]["safety_margin_fraction"] == 0.25
    assert passed["projection"]["fixed_seconds"] == 150.0
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
    config["authorization"]["prior_provider_cost_usd"] = 1.740167
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
    _write_fake_hf_cli(hf_cli)
    monkeypatch.setattr(
        hf_jobs_baseline,
        "verify_bundle",
        lambda _: {"bundle_sha256": "b" * 64, "requests_sha256": "r" * 64},
    )
    monkeypatch.setattr(hf_jobs_baseline, "load_config", lambda *args, **kwargs: config)
    command = hf_jobs_baseline.job_command(
        mode="full",
        namespace="operator",
        bundle=bundle,
        transport_repo="operator/ua-open-weight-eval-staging-6273",
        transport_revision="a" * 40,
        transport_prefix=f"bundles/{'b' * 64}",
        hf_cli=hf_cli,
        timeout_seconds=maximum_timeout,
        projection=projection,
    )
    assert f"--timeout {maximum_timeout // 60}m" in " ".join(command)
    with pytest.raises(hf_jobs_baseline.BaselineError, match="remaining-budget projection"):
        hf_jobs_baseline.job_command(
            mode="full",
            namespace="operator",
            bundle=bundle,
            transport_repo="operator/ua-open-weight-eval-staging-6273",
            transport_revision="a" * 40,
            transport_prefix=f"bundles/{'b' * 64}",
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
            "name": "ua-open-weight-eval-gemma4-canary",
            "suite": config["suite"]["cases_sha256"][:16],
            "timeout_seconds": "1200",
            "transport": "c" * 16,
        },
        "status": {"stage": "COMPLETED", "expose_urls": None, "ssh_url": None},
        "durations": {"running_secs": 600},
        "secrets": ["HF_TOKEN"],
    }
    receipt = hf_jobs_baseline.reconcile_provider_inspection(
        inspection=inspection,
        mode="canary",
        config=config,
        bundle_manifest=manifest,
        transport_revision="c" * 40,
    )
    assert receipt["provider_derived_cost_usd"] == 0.3
    inspection["labels"]["c"] = ""
    with pytest.raises(hf_jobs_baseline.BaselineError, match="unexpected labels"):
        hf_jobs_baseline.reconcile_provider_inspection(
            inspection=inspection,
            mode="canary",
            config=config,
            bundle_manifest=manifest,
            transport_revision="c" * 40,
        )
    inspection["labels"].pop("c")
    inspection["status"]["expose_urls"] = ["https://example.invalid"]
    with pytest.raises(hf_jobs_baseline.BaselineError, match="exposed"):
        hf_jobs_baseline.reconcile_provider_inspection(
            inspection=inspection,
            mode="canary",
            config=config,
            bundle_manifest=manifest,
            transport_revision="c" * 40,
        )


def test_cpu_preflight_reconciliation_rounds_billing_by_started_minute() -> None:
    config = hf_jobs_baseline.load_config()
    inspection = {
        "id": "a" * 24,
        "flavor": "cpu-basic",
        "labels": {
            "bundle_sha256": "b" * 64,
            "issue": "6273",
            "mode": "preflight",
            "name": "ua-open-weight-eval-gemma4-preflight",
            "suite": config["suite"]["cases_sha256"][:16],
            "timeout_seconds": "300",
            "transport": "c" * 16,
        },
        "status": {"stage": "COMPLETED", "expose_urls": None, "ssh_url": None},
        "durations": {"running_secs": 61},
        "secrets": ["HF_TOKEN"],
        "volumes": [],
    }
    receipt = hf_jobs_baseline.reconcile_provider_inspection(
        inspection=inspection,
        mode="preflight",
        config=config,
        bundle_manifest={"bundle_sha256": "b" * 64},
        transport_revision="c" * 40,
    )
    assert receipt["provider_billed_minutes"] == 2
    assert receipt["provider_derived_cost_usd"] == 0.000333
    assert receipt["provider_derived_cost_usd"] <= 0.001

    verification = {
        "schema_version": "ua_open_weight_eval_hf_jobs_preflight_verification.v1",
        "status": "passed",
        "job_id": "a" * 24,
        "bundle_sha256": "b" * 64,
        "repository": "operator/ua-open-weight-eval-staging-6273",
        "transport_revision": "c" * 40,
    }
    gate = hf_jobs_baseline.gate_gpu_canary(
        verification=verification,
        provider_receipt=receipt,
        bundle_manifest={"bundle_sha256": "b" * 64},
        repo_id="operator/ua-open-weight-eval-staging-6273",
    )
    assert gate["status"] == "passed"
    assert gate["preflight_cost_usd"] == 0.000333
    assert gate["transport_revision"] == "c" * 40
    assert gate["gate_sha256"] == hf_jobs_baseline.sha256_text(
        hf_jobs_baseline.canonical_json({key: value for key, value in gate.items() if key != "gate_sha256"})
    )
    malformed = {**receipt, "labels": None}
    with pytest.raises(hf_jobs_baseline.BaselineError, match="labels are missing"):
        hf_jobs_baseline.gate_gpu_canary(
            verification=verification,
            provider_receipt=malformed,
            bundle_manifest={"bundle_sha256": "b" * 64},
            repo_id="operator/ua-open-weight-eval-staging-6273",
        )
    failed = {**receipt, "stage": "ERROR"}
    with pytest.raises(hf_jobs_baseline.BaselineError, match="did not complete"):
        hf_jobs_baseline.gate_gpu_canary(
            verification=verification,
            provider_receipt=failed,
            bundle_manifest={"bundle_sha256": "b" * 64},
            repo_id="operator/ua-open-weight-eval-staging-6273",
        )


def test_operator_canary_gate_binds_superseding_cpu_evidence_and_exact_gpu_bundle() -> None:
    config = hf_jobs_baseline.load_config()
    manifest = {"bundle_sha256": "b" * 64, "requests_sha256": "r" * 64, "source_commit": "d" * 40}
    gate = hf_jobs_baseline.operator_gate_gpu_canary(
        bundle_manifest=manifest,
        repo_id="operator/ua-open-weight-eval-staging-6273",
        transport_revision="c" * 40,
        config=config,
    )
    assert gate["schema_version"] == "ua_open_weight_eval_hf_jobs_operator_canary_gate.v1"
    assert gate["accepted_preflight_job_id"] == "6a6fbf1b6b79c09949c1fa46"
    assert gate["accepted_preflight_cost_usd"] == 0.000167
    assert gate["prior_provider_cost_usd"] == 3.750167
    assert gate["incurred_provider_job_ids"] == [
        "6a6fbf1b6b79c09949c1fa46",
        "6a6fcc80a00abefd4b28dfb6",
        "6a6fd2686b79c09949c1fb57",
        "6a6fd445a00abefd4b28e088",
        "6a6fd5aa6b79c09949c1fbc9",
        "6a6fd8236b79c09949c1fc35",
        "6a6fdeaaa00abefd4b28e281",
        "6a6fe1ba6b79c09949c1fe21",
        "6a6fe50b6b79c09949c1fe42",
        "6a6fe7676b79c09949c1fe54",
        "6a6fe9a26b79c09949c1fe68",
        "6a6fed30a00abefd4b28e51c",
        "6a6ff094a00abefd4b28e630",
        "6a6ff31d6b79c09949c2000b",
        "6a6ffedca00abefd4b28e89d",
        "6a7004b06b79c09949c20218",
        "6a7007246b79c09949c20228",
        "6a700e66a00abefd4b28e9b9",
        "6a7013d96b79c09949c2029b",
        "6a701872a00abefd4b28ea7f",
    ]
    assert gate["bundle_sha256"] == "b" * 64
    assert gate["bundle_source_commit"] == "d" * 40
    assert gate["accepted_cpu_fix_merge_commit"] == "80a6a273aa5619b41f2a9a21ea69c5b253e180b4"
    assert gate["transport_revision"] == "c" * 40
    assert gate["bindings"] == {
        "cases_sha256": config["suite"]["cases_sha256"],
        "model_revision": config["model"]["revision"],
        "model_sha256": config["model"]["artifact_sha256"],
        "hardware_flavor": "l40sx1",
        "mounted_volumes": 0,
    }
    unsigned = {key: value for key, value in gate.items() if key != "gate_sha256"}
    assert gate["gate_sha256"] == hf_jobs_baseline.sha256_text(hf_jobs_baseline.canonical_json(unsigned))


def test_job_command_accepts_only_untampered_operator_canary_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = hf_jobs_baseline.load_config()
    manifest = {"bundle_sha256": "b" * 64, "requests_sha256": "r" * 64, "source_commit": "d" * 40}
    gate = hf_jobs_baseline.operator_gate_gpu_canary(
        bundle_manifest=manifest,
        repo_id="operator/ua-open-weight-eval-staging-6273",
        transport_revision="c" * 40,
        config=config,
    )
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    hf_cli = tmp_path / "hf"
    _write_fake_hf_cli(hf_cli)
    monkeypatch.setattr(hf_jobs_baseline, "verify_bundle", lambda _: manifest)
    monkeypatch.setattr(hf_jobs_baseline, "load_config", lambda *args, **kwargs: config)
    command = hf_jobs_baseline.job_command(
        mode="canary",
        namespace="operator",
        bundle=bundle,
        transport_repo="operator/ua-open-weight-eval-staging-6273",
        transport_revision="c" * 40,
        transport_prefix=f"bundles/{'b' * 64}",
        hf_cli=hf_cli,
        timeout_seconds=1200,
        preflight_gate=gate,
    )
    assert "--flavor l40sx1" in " ".join(command)
    tampered = {**gate, "bundle_source_commit": "e" * 40}
    tampered["gate_sha256"] = hf_jobs_baseline.sha256_text(
        hf_jobs_baseline.canonical_json({key: value for key, value in tampered.items() if key != "gate_sha256"})
    )
    with pytest.raises(hf_jobs_baseline.BaselineError, match="source provenance drift"):
        hf_jobs_baseline.job_command(
            mode="canary",
            namespace="operator",
            bundle=bundle,
            transport_repo="operator/ua-open-weight-eval-staging-6273",
            transport_revision="c" * 40,
            transport_prefix=f"bundles/{'b' * 64}",
            hf_cli=hf_cli,
            timeout_seconds=1200,
            preflight_gate=tampered,
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
        "response_integrity": {
            "status": "passed",
            "checked_rows": 4000,
            "violation_rows": 0,
            "copy_contract_violation_rows": 0,
            "reserved_marker_violation_rows": 0,
            "introduced_control_violation_rows": 0,
        },
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
    assert result["schema_version"] == "ua_open_weight_eval_results_verification.v2"
    assert result["publication_eligible"] is True
    assert result["semantic_validation"]["status"] == "passed"
    assert result["semantic_validation"]["checked_rows"] == 4000
    assert result["semantic_validation"]["violation_rows"] == 0
    assert result["semantic_validation"]["responses_sha256"] == hf_jobs_baseline.sha256_file(responses)
    assert result["responses"] == 4000
    public_receipt = json.loads((output / "run_receipt.public.json").read_text(encoding="utf-8"))
    assert public_receipt["environment"]["launch_client"] == {
        "name": "huggingface_hub",
        "version": "1.25.1",
    }
    assert public_receipt["provider_phase"] == {
        "aggregate_provider_cost_usd": 3.750167,
        "maximum_provider_cost_usd": 6.0,
        "remaining_provider_budget_usd": 2.249833,
        "job_count": 20,
        "jobs": config["authorization"]["incurred_provider_costs"],
    }
    assert {path.name for path in output.iterdir()} == hf_jobs_baseline.PUBLIC_FILES
    published = suite_cli.read_jsonl(output / "responses.jsonl")
    assert len(published) == 4001
    assert all("raw_generation" not in row for row in published)
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert len(report["tracks"]) == 14
    assert report["scoring"]["global_quality_score"] is None
    assert len((output / "metrics.jsonl").read_text(encoding="utf-8").splitlines()) == 56

    invalid_responses = tmp_path / "invalid-responses.jsonl"
    invalid_rows = _complete_responses(config)
    invalid_rows[1]["output_text"] += "<unused99>"
    _write_jsonl(invalid_responses, invalid_rows)
    invalid_worker = json.loads(json.dumps(worker))
    invalid_worker["outputs"]["responses_sha256"] = hf_jobs_baseline.sha256_file(invalid_responses)
    invalid_worker_path = tmp_path / "invalid-worker.json"
    invalid_worker_path.write_text(json.dumps(invalid_worker), encoding="utf-8")
    invalid_output = tmp_path / "invalid-public"
    with pytest.raises(hf_jobs_baseline.BaselineError, match="semantic integrity failed"):
        hf_jobs_baseline.package_results(
            responses=invalid_responses,
            worker_receipt_path=invalid_worker_path,
            provider_receipt_path=provider_path,
            output_dir=invalid_output,
        )
    assert not invalid_output.exists()

    (output / "report.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(
        hf_jobs_baseline.BaselineError,
        match=r"manifest (byte|hash) drift|checksum drift",
    ):
        hf_jobs_baseline.verify_results_package(output)
