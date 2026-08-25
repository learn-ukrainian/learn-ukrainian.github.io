"""Timeout contracts for the #7213 slice 19 git/identity subprocess sites."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.agent_runtime import agent_github_identity, env_sanitize
from scripts.lexicon import fill_from_content
from scripts.migrate import rename_track
from scripts.projects.ua_eval_harness import build_heldout_manifest, run_codex_baseline


def _raise_timeout(calls: list[dict[str, Any]]):
    def fake_run(*args: object, **kwargs: Any) -> Any:
        calls.append({"args": args, **kwargs})
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    return fake_run


def test_repository_name_git_timeout_raises_identity_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(agent_github_identity.subprocess, "run", _raise_timeout(calls))

    with pytest.raises(agent_github_identity.GitHubIdentityError, match="cannot determine the repository"):
        agent_github_identity._repository_name(tmp_path)

    assert calls[0]["timeout"] == agent_github_identity._GIT_TIMEOUT_SECONDS == 30


def test_isolated_git_env_timeout_keeps_fail_closed_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(env_sanitize.subprocess, "run", _raise_timeout(calls))
    monkeypatch.delenv("GIT_CONFIG_GLOBAL", raising=False)
    monkeypatch.setenv("TMPDIR", str(tmp_path))

    env = env_sanitize._isolated_git_env(str(tmp_path), None)

    assert env == {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    assert calls[0]["timeout"] == env_sanitize._GIT_TIMEOUT_SECONDS == 30


def test_heldout_manifest_git_head_timeout_raises_manifest_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(build_heldout_manifest.subprocess, "run", _raise_timeout(calls))

    with pytest.raises(build_heldout_manifest.ManifestError, match="not a readable Git checkout"):
        build_heldout_manifest._git_head(tmp_path)

    assert calls[0]["timeout"] == build_heldout_manifest._GIT_TIMEOUT_SECONDS == 30


def test_codex_cli_version_probe_timeout_raises_runner_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(run_codex_baseline.subprocess, "run", _raise_timeout(calls))

    with pytest.raises(run_codex_baseline.RunnerError, match="cannot resolve Codex CLI version"):
        run_codex_baseline._cli_version("codex")

    assert calls[0]["timeout"] == run_codex_baseline._CLI_VERSION_TIMEOUT_SECONDS == 30


def test_rename_track_git_mv_timeout_returns_false(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(rename_track.subprocess, "run", _raise_timeout(calls))
    src = tmp_path / "plans"
    src.mkdir()

    assert rename_track.git_mv(src, tmp_path / "moved" / "renamed", dry_run=False) is False
    assert "[ERROR] git mv failed: TimeoutExpired after 30s" in capsys.readouterr().out
    assert calls[0]["timeout"] == rename_track._GIT_TIMEOUT_SECONDS == 30


def test_fill_from_content_enrichment_timeout_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(fill_from_content.subprocess, "run", _raise_timeout(calls))

    with pytest.raises(subprocess.TimeoutExpired):
        fill_from_content._run_enrichment()

    assert calls[0]["args"][0][1:] == ["scripts/lexicon/enrich_manifest.py"]
    assert calls[0]["timeout"] == fill_from_content._ENRICHMENT_TIMEOUT_SECONDS == 300
