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
