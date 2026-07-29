"""Tests for the provider-neutral, source-only UA evaluation model runner."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from scripts.projects.ua_eval_harness import run_model_batch as runner
from scripts.projects.ua_eval_harness.evaluate_model import (
    import_model_responses,
    load_manifest,
    load_saved_responses,
    prepare_requests,
)


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_once(path: Path, text: str) -> None:
    if path.exists():
        assert path.read_text(encoding="utf-8") == text
        return
    path.write_text(text, encoding="utf-8")


def _packet(tmp_path: Path, *, extra_field: str | None = None) -> tuple[Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "prompt.txt"
    _write_once(prompt, "Correct each source sentence.")
    prompt_sha = _sha(prompt.read_text(encoding="utf-8"))
    header = {
        "type": "request_run",
        "schema_version": runner.REQUEST_SCHEMA,
        "manifest_id": "public-test-packet",
        "manifest_payload_sha256": "a" * 64,
        "prompt_path": "public/prompt.txt",
        "prompt_sha256": prompt_sha,
        "input_fields": ["item_id", "source", "source_sha256", "prompt_sha256"],
        "gold_fields_supplied": [],
        "request_count": runner.EXPECTED_REQUEST_COUNT,
    }
    rows: list[dict[str, object]] = [header]
    for number in range(runner.EXPECTED_REQUEST_COUNT):
        source = f"source sentence {number}"
        payload = {
            "item_id": f"item-{number:04d}",
            "source": source,
            "source_sha256": _sha(source),
            "prompt_sha256": prompt_sha,
        }
        row = {
            "type": "request",
            **payload,
            "request_sha256": _sha(_canonical(payload)),
        }
        if number == 0 and extra_field:
            row[extra_field] = "forbidden"
        rows.append(row)
    path = tmp_path / "requests.jsonl"
    _write_once(path, "".join(_canonical(row) + "\n" for row in rows))
    return path, prompt


def _config(tmp_path: Path, **overrides: object) -> Path:
    config: dict[str, object] = {
        "schema_version": runner.CONFIG_SCHEMA,
        "run_id": "public-test-run",
        "provider": "test-provider",
        "route": "test-route",
        "model": "test-model",
        "model_version": "test-revision",
        "alias_resolution": {
            "requested": "test-model",
            "resolved": "test-revision",
            "evidence": "test fixture",
        },
        "command_identity": {"name": "fake-provider", "version": "1.0"},
        "decoding": {
            "temperature": "not_exposed",
            "top_p": "not_exposed",
            "top_k": "not_exposed",
            "seed": "not_exposed",
            "max_output_tokens": "not_exposed",
            "stop": "not_exposed",
            "safety": "not_exposed",
        },
        "auth_environment": ["FAKE_LOG", "FAKE_MODE"],
    }
    config.update(overrides)
    path = tmp_path / "config.json"
    _write_once(path, json.dumps(config))
    return path


def _fake_script(tmp_path: Path) -> Path:
    path = tmp_path / "fake_provider.py"
    _write_once(
        path,
        """import json
import os
import pathlib
import sys

log = pathlib.Path(os.environ["FAKE_LOG"])
old = log.read_text() if log.exists() else ""
log.write_text(old + os.getcwd() + "\\n")
mode = os.environ.get("FAKE_MODE", "success")
if mode == "fail_first" and not old:
    raise SystemExit(9)
if mode == "malformed":
    print("not json")
    raise SystemExit(0)
prompt = sys.stdin.read() if os.environ.get("FAKE_STDIN") else sys.argv[-1]
data = json.loads(prompt.split("\\n\\n", 1)[1])
responses = [
    {"item_id": row["item_id"], "raw_response": row["source"]}
    for row in data["records"]
]
if mode == "duplicate":
    responses[1]["item_id"] = responses[0]["item_id"]
if mode == "missing":
    responses.pop()
if mode == "unknown":
    responses[0]["item_id"] = "unknown-id"
if mode == "out_of_order":
    responses.reverse()
if mode == "extra":
    responses[0]["extra"] = "no"
payload = {"responses": responses}
text = json.dumps(payload, ensure_ascii=False)
if mode == "ndjson":
    event = {
        "type": "event",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
        },
    }
    print(json.dumps(event))
elif mode == "thought":
    print("<think>provider trace</think>" + text)
else:
    print(text)
""",
    )
    return path


def _venv_python() -> Path:
    executable = Path(".venv/bin/python").resolve()
    assert executable.is_file(), "tests require the repository .venv/bin/python"
    return executable


def _run(
    tmp_path: Path,
    *,
    mode: str = "success",
    retries: int = 0,
    batch_size: int = 677,
    prompt_mode: str = "argument",
) -> tuple[Path, Path, Path, Path]:
    requests, prompt = _packet(tmp_path)
    environment = {
        "FAKE_MODE": mode,
    }
    config_overrides: dict[str, object] = {}
    if prompt_mode == "stdin":
        environment["FAKE_STDIN"] = "1"
        config_overrides["auth_environment"] = [
            "FAKE_LOG",
            "FAKE_MODE",
            "FAKE_STDIN",
        ]
    config = _config(tmp_path, **config_overrides)
    script = _fake_script(tmp_path)
    log = tmp_path / "calls.log"
    environment["FAKE_LOG"] = str(log)
    previous = {name: os.environ.get(name) for name in environment}
    os.environ.update(environment)
    raw = tmp_path / "raw.jsonl"
    output = tmp_path / "output.jsonl"
    metadata = tmp_path / "metadata.json"
    state = tmp_path / "state"
    try:
        runner.run(
            requests_path=requests,
            prompt_path=prompt,
            config_path=config,
            executable=str(_venv_python()),
            command_args=[str(script.resolve())],
            prompt_mode=prompt_mode,
            raw_output_path=raw,
            output_path=output,
            metadata_path=metadata,
            state_dir=state,
            batch_size=batch_size,
            workers=1,
            timeout=10,
            retries=retries,
        )
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
    return raw, output, metadata, state


@pytest.mark.parametrize("prompt_mode", ["argument", "stdin"])
def test_runs_source_only_batches_outside_repository_and_writes_metadata(
    tmp_path: Path,
    prompt_mode: str,
) -> None:
    raw, output, metadata_path, _ = _run(
        tmp_path,
        mode="ndjson",
        batch_size=300,
        prompt_mode=prompt_mode,
    )

    outputs = [json.loads(line) for line in output.read_text().splitlines()]
    raw_rows = [json.loads(line) for line in raw.read_text().splitlines()]
    metadata = json.loads(metadata_path.read_text())
    generation = metadata["generation_metadata"]
    assert len(outputs) == runner.EXPECTED_REQUEST_COUNT
    assert len(raw_rows) == 3
    assert metadata["schema_version"] == runner.METADATA_SCHEMA
    assert metadata["run_id"] == "public-test-run"
    assert set(metadata["decoding"]) == runner.DECODING_FIELDS
    assert generation["gold_fields_supplied"] == []
    assert generation["response_count"] == runner.EXPECTED_REQUEST_COUNT
    assert len(generation["batch_receipts"]) == 3
    assert generation["retry_counts"] == {"0": 0, "1": 0, "2": 0}
    call_paths = (tmp_path / "calls.log").read_text().splitlines()
    assert call_paths
    assert all(
        not Path(path).resolve().is_relative_to(runner.ROOT) for path in call_paths
    )
    assert all(Path(path).is_dir() for path in call_paths)


def test_packet_firewall_rejects_unknown_and_gold_shaped_fields(
    tmp_path: Path,
) -> None:
    for field in ("unexpected", "target"):
        requests, _ = _packet(tmp_path / field, extra_field=field)
        with pytest.raises(runner.RunnerError):
            runner.load_source_only_packet(requests)


def test_committed_packet_and_example_config_match_runner_contract() -> None:
    packet = Path(
        "data/projects/ua_eval_harness/baselines/v1/generation_requests.jsonl"
    )
    header, requests, packet_sha256 = runner.load_source_only_packet(packet)
    config = runner.load_run_config(
        Path("data/projects/ua_eval_harness/model_run_config.example.json")
    )

    assert header["request_count"] == runner.EXPECTED_REQUEST_COUNT
    assert len(requests) == runner.EXPECTED_REQUEST_COUNT
    assert len(packet_sha256) == 64
    assert config["schema_version"] == runner.CONFIG_SCHEMA
    assert set(config["decoding"]) == runner.DECODING_FIELDS


def test_run_config_requires_exact_alias_decoding_and_tool_receipts(
    tmp_path: Path,
) -> None:
    for index, override in enumerate(
        (
        {"alias_resolution": "ambiguous"},
        {"decoding": {"temperature": 0}},
        {"command_identity": {"name": "missing-version"}},
        )
    ):
        config_dir = tmp_path / str(index)
        config_dir.mkdir()
        config = _config(config_dir, **override)
        with pytest.raises(runner.RunnerError):
            runner.load_run_config(config)


def test_accepts_only_narrow_machine_response_wrappers() -> None:
    payload = '{"responses":[{"item_id":"item-1","raw_response":"fixed"}]}'
    assert runner.parse_provider_response(
        f"<think>provider trace</think>{payload}",
        ["item-1"],
    ) == [{"item_id": "item-1", "raw_response": "fixed"}]
    with pytest.raises(runner.RunnerError):
        runner.parse_provider_response(f"Explanation: {payload}", ["item-1"])


@pytest.mark.parametrize(
    "mode",
    ["malformed", "duplicate", "missing", "unknown", "out_of_order", "extra"],
)
def test_rejects_nonexact_responses_without_final_outputs(
    tmp_path: Path,
    mode: str,
) -> None:
    with pytest.raises(runner.RunnerError):
        _run(tmp_path, mode=mode)
    assert not (tmp_path / "raw.jsonl").exists()
    assert not (tmp_path / "output.jsonl").exists()
    assert not (tmp_path / "metadata.json").exists()
    call_paths = (tmp_path / "calls.log").read_text().splitlines()
    assert call_paths and all(Path(path).is_dir() for path in call_paths)


def test_retries_and_preserves_failure_receipts(tmp_path: Path) -> None:
    _, _, metadata_path, state_dir = _run(
        tmp_path,
        mode="fail_first",
        retries=1,
    )
    metadata = json.loads(metadata_path.read_text())
    generation = metadata["generation_metadata"]
    assert generation["retry_counts"] == {"0": 1}
    assert len(generation["failed_attempts"]) == 1
    assert generation["failed_attempts"][0] == {
        "batch_index": 0,
        "attempt": 1,
        "attempted_at": generation["failed_attempts"][0]["attempted_at"],
        "error_class": "RunnerError",
        "message_tail": "provider command returned nonzero status 9",
    }
    state = json.loads((state_dir / "batch-0000.json").read_text())
    assert state["failed_attempts"] == generation["failed_attempts"]


def test_resume_is_idempotent_and_does_not_reinvoke_provider(tmp_path: Path) -> None:
    raw, output, metadata, state = _run(tmp_path)
    calls_before = (tmp_path / "calls.log").read_text()
    artifacts_before = {
        path: path.read_bytes() for path in (raw, output, metadata, state / "batch-0000.json")
    }
    _run(tmp_path)
    assert (tmp_path / "calls.log").read_text() == calls_before
    assert {
        path: path.read_bytes() for path in artifacts_before
    } == artifacts_before


def test_completed_state_binding_mismatch_is_a_hard_failure(tmp_path: Path) -> None:
    raw, output, metadata, state = _run(tmp_path)
    requests, prompt = _packet(tmp_path)
    different_config = tmp_path / "different-config"
    different_config.mkdir()
    config = _config(different_config, model="different-model")
    script = _fake_script(tmp_path)
    with pytest.raises(runner.RunnerError, match="binding mismatch"):
        runner.run(
            requests_path=requests,
            prompt_path=prompt,
            config_path=config,
            executable=str(_venv_python()),
            command_args=[str(script.resolve())],
            prompt_mode="argument",
            raw_output_path=raw,
            output_path=output,
            metadata_path=metadata,
            state_dir=state,
            batch_size=677,
            timeout=10,
        )


def test_runner_metadata_imports_and_saved_response_validates(tmp_path: Path) -> None:
    requests_path = tmp_path / "requests.jsonl"
    requests = prepare_requests()
    requests_path.write_text(
        "".join(_canonical(row) + "\n" for row in requests),
        encoding="utf-8",
    )
    prompt = (
        Path("data/projects/ua_eval_harness/minimal_edit_prompt_v1.txt").resolve()
    )
    config = _config(tmp_path)
    script = _fake_script(tmp_path)
    log = tmp_path / "calls.log"
    old_log = os.environ.get("FAKE_LOG")
    os.environ["FAKE_LOG"] = str(log)
    raw = tmp_path / "raw.jsonl"
    output = tmp_path / "output.jsonl"
    metadata = tmp_path / "metadata.json"
    state = tmp_path / "state"
    try:
        runner.run(
            requests_path=requests_path,
            prompt_path=prompt,
            config_path=config,
            executable=str(_venv_python()),
            command_args=[str(script.resolve())],
            prompt_mode="argument",
            raw_output_path=raw,
            output_path=output,
            metadata_path=metadata,
            state_dir=state,
            batch_size=677,
            timeout=10,
        )
    finally:
        if old_log is None:
            os.environ.pop("FAKE_LOG", None)
        else:
            os.environ["FAKE_LOG"] = old_log
    imported = import_model_responses(
        requests_path=requests_path,
        model_output_path=output,
        metadata_path=metadata,
    )
    saved = tmp_path / "saved.jsonl"
    saved.write_text(
        "".join(_canonical(row) + "\n" for row in imported),
        encoding="utf-8",
    )
    manifest, items = load_manifest()
    header, responses = load_saved_responses(saved, manifest=manifest, items=items)
    assert header["generation_metadata"]["route"] == "test-route"
    assert len(responses) == runner.EXPECTED_REQUEST_COUNT
