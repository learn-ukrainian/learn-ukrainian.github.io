from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "batch_state" / "phase3-run-cycle007-public-canaries-v1.py"


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("cycle007_public_canaries_test", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_cli_requires_explicit_provider_bin(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    runner = _load_runner()
    monkeypatch.setattr(
        sys,
        "argv",
        [str(RUNNER), "--provider", "gemini", "--receipt", str(tmp_path / "receipt.json")],
    )

    assert runner.main() == 2
    assert json.loads(capsys.readouterr().out) == {
        "failure_code": "provider_bin_required_for_real_mode",
        "ok": False,
        "text_free": True,
    }


def test_gemini_schema_decisions_are_all_known_to_evidence_validator() -> None:
    runner = _load_runner()
    rows = runner.fixture_rows()
    schema = runner.gemini_schema(rows, "challenge")

    positions = schema["properties"]["labels_by_position"]["properties"]
    for position in ("p01", "p02"):
        decision_enum = set(positions[position]["properties"]["decision_code"]["enum"])
        assert decision_enum == runner.SOURCE.REJECTS
        assert decision_enum <= runner.validator.KNOWN_DECISIONS


def test_real_cli_passes_explicit_provider_bin(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_runner()
    provider = (tmp_path / "agy").resolve()
    receipt = tmp_path / "receipt.json"
    observed: dict[str, object] = {}

    def fake_invoke(provider_name: str, provider_bin: Path, **kwargs: object) -> dict[str, object]:
        observed.update(provider_name=provider_name, provider_bin=provider_bin, **kwargs)
        return {"ok": True, "text_free": True}

    monkeypatch.setattr(runner, "invoke_canary", fake_invoke)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(RUNNER),
            "--provider",
            "gemini",
            "--provider-bin",
            str(provider),
            "--receipt",
            str(receipt),
        ],
    )

    assert runner.main() == 0
    assert observed["provider_name"] == "gemini"
    assert observed["provider_bin"] == provider
    assert observed["execution_mode"] == "real"
    assert observed["receipt_path"] == receipt


def test_real_invoke_rejects_relative_and_symlink_provider(tmp_path: Path) -> None:
    runner = _load_runner()
    with pytest.raises(runner.CanaryError, match="provider_executable_not_absolute"):
        runner.invoke_canary("gemini", Path("agy"), execution_mode="real")

    target = tmp_path / "agy-real"
    target.write_bytes(b"#!/bin/sh\n")
    target.chmod(0o700)
    link = tmp_path / "agy"
    link.symlink_to(target)
    with pytest.raises(runner.CanaryError, match="invalid_executable"):
        runner.invoke_canary("gemini", link, execution_mode="real")


def test_canary_accepts_one_strict_response_json_and_rejects_ambiguity() -> None:
    runner = _load_runner()
    payload = {"labels_by_position": {"p01": {}, "p02": {}}, "liveness_challenge": "challenge"}

    decoded, transport = runner._strict_result_payload({"response": json.dumps(payload)})
    assert decoded == payload
    assert transport == "response_json"

    with pytest.raises(runner.CanaryStructuralError, match="structured_output_missing"):
        runner._strict_result_payload({"response": [json.dumps(payload), json.dumps(payload)]})


def test_batch_runner_accepts_one_fenced_response_json() -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_batch_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    payload = {"labels_by_position": {"p01": {}, "p02": {}}}

    assert runner._strict_result_payload({"response": f"```json\n{json.dumps(payload)}\n```"}) == payload


def test_batch_stream_input_command_has_no_print_prompt() -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_batch_command_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)

    command = runner._command(Path("/provider"), Path("/schema.json"), Path("/agy.log"))

    assert command.count("--input-format") == 1
    assert command[command.index("--input-format") + 1] == "stream-json"
    assert command.count("--output-format") == 1
    assert command[command.index("--output-format") + 1] == "stream-json"
    assert "--print" not in command
    assert "--new-project" in command


def test_grok_commands_use_only_the_reviewed_cli_isolation_flags() -> None:
    canary = _load_runner()
    path = ROOT / "batch_state" / "phase3-run-cycle007-grok-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_grok_batch_command_test", path)
    assert spec is not None and spec.loader is not None
    batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(batch)

    expected_isolation_flags = {"--permission-mode", "--no-alt-screen", "--no-subagents", "--disable-web-search"}
    prompt_path = Path("/private/prompt")
    for command in (
        canary._grok_command(Path("/provider"), prompt_path),
        batch._provider_command(Path("/provider"), prompt_path),
    ):
        assert expected_isolation_flags <= set(command)
        assert "--no-memory" not in command
        assert command.count("--prompt-file") == 1
        assert command[command.index("--prompt-file") + 1] == str(prompt_path)


def test_grok_batch_binds_and_removes_private_prompt_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-grok-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_grok_batch_prompt_test", path)
    assert spec is not None and spec.loader is not None
    batch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(batch)
    observed: dict[str, Path] = {}

    def fake_run(command: list[str], **kwargs: object) -> object:
        prompt_path = Path(command[command.index("--prompt-file") + 1])
        observed["prompt_path"] = prompt_path
        assert prompt_path.parent == tmp_path
        assert prompt_path.read_bytes() == b"public prompt"
        assert prompt_path.stat().st_mode & 0o777 == 0o600
        assert kwargs["input"] == b"public prompt"
        return batch.subprocess.CompletedProcess(command, 0, stdout=b"{}", stderr=b"")

    monkeypatch.setattr(batch.subprocess, "run", fake_run)
    result = batch._run_provider(Path("/provider"), b"public prompt", tmp_path)

    assert result.returncode == 0
    assert not observed["prompt_path"].exists()


def test_batch_stream_rejects_reported_cwd_mismatch(tmp_path: Path) -> None:
    path = ROOT / "batch_state" / "phase3-run-cycle007-gemini-label-provider-batch-v1.py"
    spec = importlib.util.spec_from_file_location("cycle007_gemini_batch_cwd_test", path)
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    raw = (
        runner.canonical({"event": "init", "init": {"model": runner.MODEL, "cwd": str(tmp_path)}})
        + runner.canonical(
            {
                "event": "result",
                "result": {
                    "status": "SUCCESS",
                    "structured_output": {"labels_by_position": {"p01": {}}},
                },
            }
        )
    )

    assert runner._extract(raw, expected_cwd=tmp_path) == {"labels_by_position": {"p01": {}}}
    with pytest.raises(runner.Error, match="structured_output_envelope_drift"):
        runner._extract(raw, expected_cwd=tmp_path.parent)
