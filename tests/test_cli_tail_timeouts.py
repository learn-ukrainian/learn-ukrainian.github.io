"""Timeout contracts for the six remaining CLI subprocess sites (#7213 slice 20)."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from scripts.ai_agent_bridge import _channels_cli
from scripts.bench import writer_matrix
from scripts.etymology import bulk_ocr_gemini
from scripts.fleet_comms import github_pr_metrics
from scripts.validate import verify_track
from scripts.vocab import rebuild_vocab_from_yaml


def _raise_timeout(calls: list[dict[str, object]]):
    def fake_run(*args: object, **kwargs: object) -> object:
        calls.append({"args": args, **kwargs})
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    return fake_run


def test_channel_context_timeout_returns_editor_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []
    context_path = tmp_path / "context.md"
    monkeypatch.setattr(_channels_cli._channels, "channel_context_path", lambda _name: context_path)
    monkeypatch.setenv("EDITOR", "test-editor")
    monkeypatch.setattr(_channels_cli.subprocess, "run", _raise_timeout(calls))

    result = _channels_cli._handle_channel_context(SimpleNamespace(name="test", edit=True))

    assert result == 1
    assert calls[0]["timeout"] == _channels_cli._EDITOR_TIMEOUT_SECONDS == 30
    assert "editor 'test-editor' timed out after 30s" in capsys.readouterr().err


def test_writer_matrix_timeout_returns_failed_bench_cell(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    calls: list[dict[str, object]] = []
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setattr(writer_matrix, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(writer_matrix.subprocess, "run", _raise_timeout(calls))

    cell = writer_matrix._run_one_cell("writer", "a1", "module", None, tmp_path / "out")

    assert cell.exit_code == 124
    assert cell.failure_class == "infra"
    assert calls[0]["timeout"] == writer_matrix._CELL_TIMEOUT_SECONDS == 1800
    assert "writer cell timed out after 1800s" in (tmp_path / "out/cell-logs/writer__a1__module.log").read_text()


def test_ocr_decode_timeout_maps_to_existing_runtime_error(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(bulk_ocr_gemini.subprocess, "run", _raise_timeout(calls))
    page = bulk_ocr_gemini.Page(
        1,
        1,
        tmp_path / "page.jp2",
        tmp_path / "page.png",
        tmp_path / "page.md",
    )

    with pytest.raises(RuntimeError, match=r"opj_decompress failed for vol1/p0001 rc=124") as raised:
        bulk_ocr_gemini.decode_pages([page])

    assert "TimeoutExpired after 120s" in str(raised.value)
    assert calls[0]["timeout"] == bulk_ocr_gemini._DECODE_TIMEOUT_SECONDS == 120


def test_github_metrics_timeout_returns_failed_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(github_pr_metrics.subprocess, "run", _raise_timeout(calls))

    result = github_pr_metrics.collect_github_pr_metrics(limit=5)

    assert result["ok"] is False
    assert result["content_included"] is False
    assert result["error"] == "gh timed out after 30s"
    assert calls[0]["timeout"] == github_pr_metrics._GH_TIMEOUT_SECONDS == 30


def test_verify_track_audit_timeout_returns_nonzero_tuple(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(verify_track.subprocess, "run", _raise_timeout(calls))

    result = verify_track.run_audit(tmp_path / "module.md", False, tmp_path)

    assert result == (124, "Audit timed out after 300s")
    assert calls[0]["timeout"] == verify_track._AUDIT_TIMEOUT_SECONDS == 300


def test_vocab_rebuild_timeout_reuses_initialization_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.setattr(rebuild_vocab_from_yaml, "DB_PATH", tmp_path / "vocabulary.db")
    monkeypatch.setattr(subprocess, "run", _raise_timeout(calls))

    assert rebuild_vocab_from_yaml.populate_database([], force=True) is None

    output = capsys.readouterr().out
    assert "Failed to initialize database" in output
    assert "TimeoutExpired after 300s" in output
    assert calls[0]["timeout"] == rebuild_vocab_from_yaml._VOCAB_INIT_TIMEOUT_SECONDS == 300
