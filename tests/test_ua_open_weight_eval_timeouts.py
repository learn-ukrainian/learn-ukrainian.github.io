"""Every ua_open_weight_eval subprocess call passes an explicit timeout (#7213 slice 11)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.projects.ua_open_weight_eval import (
    hf_jobs_baseline,
    hf_jobs_transport,
    suite_cli,
)


def _write_fake_hf_cli(path: Path) -> None:
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o700)


def _canary_bundle_fixtures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
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
    monkeypatch.setattr(hf_jobs_baseline, "verify_bundle", lambda _: manifest)
    monkeypatch.setattr(hf_jobs_baseline, "load_config", lambda *args, **kwargs: config)
    return hf_cli


def test_source_commit_bounds_git_and_maps_timeout_to_baseline_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout=f"{'a' * 40}\n", stderr="")

    monkeypatch.setattr(hf_jobs_baseline.subprocess, "run", fake_run)
    assert hf_jobs_baseline.source_commit() == "a" * 40
    assert captured["timeout"] == 30

    def hanging_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        raise subprocess.TimeoutExpired(cmd=["git", "rev-parse", "HEAD"], timeout=30)

    monkeypatch.setattr(hf_jobs_baseline.subprocess, "run", hanging_run)
    with pytest.raises(hf_jobs_baseline.BaselineError, match="timed out"):
        hf_jobs_baseline.source_commit()


def test_job_command_bounds_hf_version_probe_and_maps_timeout_to_baseline_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hf_cli = _canary_bundle_fixtures(monkeypatch, tmp_path)
    config = hf_jobs_baseline.load_config()
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        observed.update(kwargs)
        return subprocess.CompletedProcess(
            command, 0, stdout=config["runtime"]["huggingface_hub_cli_version"] + "\n", stderr=""
        )

    monkeypatch.setattr(hf_jobs_baseline.subprocess, "run", fake_run)
    command = hf_jobs_baseline.job_command(
        mode="preflight",
        namespace="operator",
        bundle=tmp_path / "bundle",
        transport_repo="operator/ua-open-weight-eval-staging-6273",
        transport_revision="a" * 40,
        transport_prefix=f"bundles/{'b' * 64}",
        hf_cli=hf_cli,
        timeout_seconds=300,
    )
    assert "--timeout 5m" in " ".join(command)
    assert observed["timeout"] == 30

    def hanging_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        raise subprocess.TimeoutExpired(cmd=[str(hf_cli), "--version"], timeout=30)

    monkeypatch.setattr(hf_jobs_baseline.subprocess, "run", hanging_run)
    with pytest.raises(hf_jobs_baseline.BaselineError, match="version probe timed out"):
        hf_jobs_baseline.job_command(
            mode="preflight",
            namespace="operator",
            bundle=tmp_path / "bundle",
            transport_repo="operator/ua-open-weight-eval-staging-6273",
            transport_revision="a" * 40,
            transport_prefix=f"bundles/{'b' * 64}",
            hf_cli=hf_cli,
            timeout_seconds=300,
        )


def test_launch_once_bounds_detach_handshake_and_maps_timeout_to_reconcile_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(
        hf_jobs_baseline,
        "load_disposition",
        lambda *args, **kwargs: {"rerun_authorized": True},
    )
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        observed.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout=f"{'a' * 24}\n", stderr="")

    monkeypatch.setattr(hf_jobs_baseline.subprocess, "run", fake_run)
    launched = hf_jobs_baseline.launch_once(
        command=["/absolute/hf", "jobs", "run", "--detach"],
        mode="canary",
        state_path=state_path,
        execute=True,
    )
    assert launched["status"] == "launched"
    assert observed["timeout"] == 120

    def hanging_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        raise subprocess.TimeoutExpired(cmd=["/absolute/hf", "jobs", "run", "--detach"], timeout=120)

    state_path = tmp_path / "timeout-state.json"
    monkeypatch.setattr(hf_jobs_baseline.subprocess, "run", hanging_run)
    with pytest.raises(hf_jobs_baseline.BaselineError, match="launch timed out"):
        hf_jobs_baseline.launch_once(
            command=["/absolute/hf", "jobs", "run", "--detach"],
            mode="canary",
            state_path=state_path,
            execute=True,
        )
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["runs"]["canary"]["status"] == "launch_response_failed_reconcile_required"


def test_run_worker_bounds_install_and_worker_and_maps_timeout_to_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = hf_jobs_baseline.load_config()
    plugin = config["runtime"]["vllm_gguf_plugin"]
    (tmp_path / "run_config.json").write_text(json.dumps(config), encoding="utf-8")
    (tmp_path / plugin["filename"]).write_bytes(b"wheel")
    (tmp_path / "hf_jobs_worker.py").write_text("print('worker')\n", encoding="utf-8")
    (tmp_path / "requests.jsonl").write_text("{}\n", encoding="utf-8")
    (tmp_path / "canary_selection.json").write_text("{}\n", encoding="utf-8")
    timeouts: list[object] = []
    calls: list[list[str]] = []

    def fake_run(command: list[str], *, check: bool = False, **kwargs: object) -> subprocess.CompletedProcess:
        assert check is False
        timeouts.append(kwargs.get("timeout"))
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
    assert timeouts == [hf_jobs_transport.PLUGIN_INSTALL_TIMEOUT_SECONDS, hf_jobs_transport.WORKER_TIMEOUT_SECONDS]
    assert timeouts == [300, 3600]

    def hanging_install(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        raise subprocess.TimeoutExpired(cmd=["uv", "pip", "install", "--system"], timeout=300)

    monkeypatch.setattr(hf_jobs_transport.subprocess, "run", hanging_install)
    with pytest.raises(hf_jobs_transport.TransportError, match="installation timed out"):
        hf_jobs_transport.run_worker(args, tmp_path)

    worker_invocations: list[list[str]] = []

    def hanging_worker(command: list[str], *, check: bool = False, **kwargs: object) -> subprocess.CompletedProcess:
        worker_invocations.append(command)
        if len(worker_invocations) == 1:
            return subprocess.CompletedProcess(command, 0)
        raise subprocess.TimeoutExpired(cmd=command, timeout=3600)

    monkeypatch.setattr(hf_jobs_transport.subprocess, "run", hanging_worker)
    assert hf_jobs_transport.run_worker(args, tmp_path) == 124


def _valid_local_run_config(tmp_path: Path) -> tuple[Path, Path, Path]:
    model = tmp_path / "model.gguf"
    model.write_bytes(b"offline-model-bytes")
    runner = tmp_path / "local_runner"
    runner.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    runner.chmod(0o700)
    requests = tmp_path / "requests.jsonl"
    requests.write_text("{}\n", encoding="utf-8")
    responses = tmp_path / "responses.jsonl"
    config = {
        "backend": "transformers",
        "command": [str(runner), "--requests", "{requests}", "--responses", "{responses}"],
        "model_path": str(model),
        "model_revision": "main",
        "model_sha256": hashlib.sha256(model.read_bytes()).hexdigest(),
        "network_allowed": False,
        "provider": None,
    }
    config_path = tmp_path / "local_run_config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path, requests, responses


def test_run_local_bounds_offline_runner_and_maps_timeout_to_suite_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path, requests, responses = _valid_local_run_config(tmp_path)
    observed: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
        observed.update(kwargs)
        responses.write_text('{"item_id":"uaw-request-0001"}\n', encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(suite_cli.subprocess, "run", fake_run)
    receipt = suite_cli.run_local(config_path, requests, responses, tmp_path / "receipt.json")
    assert receipt["closed_api_used"] is False
    assert observed["timeout"] == suite_cli.LOCAL_RUNNER_TIMEOUT_SECONDS == 1800

    def hanging_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        raise subprocess.TimeoutExpired(cmd="local-runner", timeout=1800)

    monkeypatch.setattr(suite_cli.subprocess, "run", hanging_run)
    with pytest.raises(suite_cli.SuiteError, match=r"timed out after 1800s"):
        suite_cli.run_local(config_path, requests, responses, tmp_path / "receipt-timeout.json")


def test_timeout_bounded_modules_keep_their_entry_point_contracts(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    for module in (hf_jobs_baseline, hf_jobs_transport, suite_cli):
        assert module.__doc__
    for argv in (["--help"], ["verify", "--help"]):
        with pytest.raises(SystemExit) as exc:
            suite_cli.parse_args(argv)
        assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        hf_jobs_baseline.parse_args(["--help"])
    assert exc.value.code == 0
    monkeypatch.setattr(sys, "argv", ["hf_jobs_transport.py", "--help"])
    with pytest.raises(SystemExit) as exc:
        hf_jobs_transport.parse_args()
    assert exc.value.code == 0
    capsys.readouterr()
