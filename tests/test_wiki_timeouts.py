"""Unit tests for subprocess timeout bounds in scripts/wiki (#7213 slice 13).

Every bounded call site must pass an explicit ``timeout=`` — 30s for git
plumbing, 10s for the Darwin ``sysctl`` RAM probe, 300s for Codex concept
extraction, and the documented 1800s ceiling for a wiki track compile+review —
and must map ``subprocess.TimeoutExpired`` onto its documented degradation
instead of an uncaught traceback:

* ``backfill_generated_by_model.run_git``              → RuntimeError (check=True) / empty stdout (check=False)
* ``backfill_generated_by_model.load_head_text``       → fall back to the on-disk working-tree text
* ``backfill_generated_by_model.load_historical_meta`` → skip that commit (continue), like a non-zero rc
* ``corpus_gaps.audit.run_codex_concept_extraction``   → RuntimeError("Codex concept extraction failed: …")
* ``mlx_bridge.get_physical_ram``                      → return None (existing ``except Exception`` shape)
* ``rebuild._run_compile``                             → non-zero exit code 124, no traceback
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from wiki.backfill_generated_by_model import (
    GIT_TIMEOUT_S,
    load_head_text,
    load_historical_meta,
    run_git,
)
from wiki.diagnostics.corpus_gaps.audit import CODEX_TIMEOUT_S, run_codex_concept_extraction

from tests.project_python import project_python
from wiki import backfill_generated_by_model as backfill
from wiki import mlx_bridge, rebuild

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSCTL_TIMEOUT_S = 10


def _completed(
    cmd: list[str],
    *,
    returncode: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=cmd, returncode=returncode, stdout=stdout, stderr=stderr)


def _timed_out(cmd: list[str], **_kwargs: object) -> subprocess.TimeoutExpired:
    raise subprocess.TimeoutExpired(cmd, 30)


# ---------------------------------------------------------------------------
# backfill_generated_by_model.run_git
# ---------------------------------------------------------------------------


def test_run_git_passes_explicit_timeout() -> None:
    calls: list[dict[str, Any]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"cmd": cmd, **kwargs})
        return _completed(cmd, stdout="abc123\n")

    with patch("subprocess.run", side_effect=fake_run):
        assert run_git("log", "-1", "--format=%H") == "abc123\n"

    assert len(calls) == 1
    assert calls[0]["timeout"] == GIT_TIMEOUT_S == 30


def test_run_git_maps_timeout_to_runtime_error_when_check() -> None:
    with patch("subprocess.run", side_effect=_timed_out):
        with pytest.raises(RuntimeError, match="timed out after"):
            run_git("log", "--follow")


def test_run_git_timeout_returns_empty_stdout_when_check_false() -> None:
    with patch("subprocess.run", side_effect=_timed_out):
        assert run_git("log", "-1", check=False) == ""


# ---------------------------------------------------------------------------
# backfill_generated_by_model.load_head_text
# ---------------------------------------------------------------------------


@pytest.fixture
def article_root(tmp_path: Path) -> tuple[Path, Path]:
    """A fake project root holding one wiki article (created BEFORE patching)."""
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    article = wiki_dir / "article.md"
    article.write_text("working-tree text\n", encoding="utf-8")
    return tmp_path, article


def test_load_head_text_passes_explicit_timeout(article_root, monkeypatch) -> None:
    root, article = article_root
    monkeypatch.setattr(backfill, "PROJECT_ROOT", root)

    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        captured.update(kwargs)
        return _completed(cmd, stdout="head text\n")

    with patch("subprocess.run", side_effect=fake_run):
        assert load_head_text(article) == "head text\n"

    assert captured["timeout"] == GIT_TIMEOUT_S
    assert captured["cwd"] == root
    assert "HEAD:wiki/article.md" in captured["cmd"]


def test_load_head_text_maps_timeout_to_disk_fallback(article_root, monkeypatch) -> None:
    root, article = article_root
    monkeypatch.setattr(backfill, "PROJECT_ROOT", root)

    with patch("subprocess.run", side_effect=_timed_out):
        assert load_head_text(article) == "working-tree text\n"


# ---------------------------------------------------------------------------
# backfill_generated_by_model.load_historical_meta
# ---------------------------------------------------------------------------


def test_load_historical_meta_passes_explicit_timeout_on_every_call(
    article_root,
    monkeypatch,
) -> None:
    root, article = article_root
    monkeypatch.setattr(backfill, "PROJECT_ROOT", root)

    timeouts: list[Any] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        timeouts.append(kwargs.get("timeout"))
        if cmd[1] == "log":
            return _completed(cmd, stdout="c1\nc2\n")
        return _completed(cmd, stdout="<!-- wiki-meta\ngenerated_by_model: m\n-->")

    with patch("subprocess.run", side_effect=fake_run):  # type: ignore[arg-type]
        meta, origin = load_historical_meta(article)

    assert set(timeouts) == {GIT_TIMEOUT_S}
    assert len(timeouts) >= 2
    assert meta.get("generated_by_model") == "m"
    assert origin == "c1"


def test_load_historical_meta_maps_timeout_to_commit_skip(article_root, monkeypatch) -> None:
    root, article = article_root
    monkeypatch.setattr(backfill, "PROJECT_ROOT", root)

    def fake_run(cmd: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        if cmd[1] == "log":
            return _completed(cmd, stdout="c1\nc2\n")
        raise subprocess.TimeoutExpired(cmd, GIT_TIMEOUT_S)

    with patch("subprocess.run", side_effect=fake_run):
        meta, origin = load_historical_meta(article)

    assert meta == {}
    assert origin is None


# ---------------------------------------------------------------------------
# corpus_gaps.audit.run_codex_concept_extraction
# ---------------------------------------------------------------------------


def test_codex_extraction_passes_explicit_timeout() -> None:
    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["timeout"] = kwargs.get("timeout")
        output_idx = cmd.index("--output-last-message")
        Path(cmd[output_idx + 1]).write_text(json.dumps({"concepts": []}), encoding="utf-8")
        return _completed(cmd)

    with patch("subprocess.run", side_effect=fake_run):
        payload = run_codex_concept_extraction("prompt")

    assert payload == {"concepts": []}
    assert captured["timeout"] == CODEX_TIMEOUT_S == 300


def test_codex_extraction_maps_timeout_to_runtime_error() -> None:
    with patch("subprocess.run", side_effect=_timed_out):
        with pytest.raises(RuntimeError, match="Codex concept extraction failed"):
            run_codex_concept_extraction("prompt")


# ---------------------------------------------------------------------------
# mlx_bridge.get_physical_ram
# ---------------------------------------------------------------------------


def test_get_physical_ram_probe_passes_explicit_timeout(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    captured: dict[str, Any] = {}

    def fake_check_output(cmd: list[str], **kwargs: Any) -> str:
        captured.update(kwargs)
        return "17179869184\n"

    with patch("subprocess.check_output", side_effect=fake_check_output):
        assert mlx_bridge.get_physical_ram() == 17179869184

    assert captured["timeout"] == SYSCTL_TIMEOUT_S == 10


def test_get_physical_ram_maps_timeout_to_none(monkeypatch) -> None:
    """TimeoutExpired is an Exception — the existing degrade-to-None shape holds."""
    monkeypatch.setattr(sys, "platform", "darwin")

    def timed_out_check_output(cmd: list[str], **_kwargs: Any) -> str:
        raise subprocess.TimeoutExpired(cmd, SYSCTL_TIMEOUT_S)

    with patch("subprocess.check_output", side_effect=timed_out_check_output):
        assert mlx_bridge.get_physical_ram() is None


# ---------------------------------------------------------------------------
# rebuild._run_compile
# ---------------------------------------------------------------------------


def _task(slug: str | None = None) -> rebuild.TaskState:
    return rebuild.TaskState(phase=2, track="b1", slug=slug)


def test_run_compile_passes_documented_ceiling() -> None:
    captured: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        captured.update(kwargs)
        return _completed(cmd, returncode=0)

    with patch("subprocess.run", side_effect=fake_run):
        rc = rebuild._run_compile(_task())

    assert rc == 0
    assert captured["timeout"] == rebuild.COMPILE_TIMEOUT_S == 1800
    assert "--review" in captured["cmd"]


def test_run_compile_slug_task_extends_command() -> None:
    commands: list[list[str]] = []

    def fake_run(cmd: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        commands.append(cmd)
        return _completed(cmd, returncode=3)

    with patch("subprocess.run", side_effect=fake_run):
        rc = rebuild._run_compile(_task(slug="some-slug"))

    assert rc == 3
    assert commands[0][-2:] == ["--slug", "some-slug"]


def test_run_compile_maps_timeout_to_nonzero_rc_not_traceback(capsys) -> None:
    with patch("subprocess.run", side_effect=_timed_out):
        rc = rebuild._run_compile(_task())

    assert rc == 124
    err = capsys.readouterr().err
    assert "1800s" in err
    assert "ceiling" in err


def test_run_compile_keyboard_interrupt_still_returns_130() -> None:
    def interrupted(cmd: list[str], **_kwargs: object) -> None:
        raise KeyboardInterrupt

    with patch("subprocess.run", side_effect=interrupted):
        assert rebuild._run_compile(_task()) == 130


# ---------------------------------------------------------------------------
# Entry-point smoke (--help where a CLI exists; mlx_bridge has none)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("script", "needle"),
    [
        ("scripts/wiki/backfill_generated_by_model.py", "--write"),
        ("scripts/wiki/diagnostics/corpus_gaps/audit.py", "--tracks"),
        ("scripts/wiki/rebuild.py", "run"),
    ],
)
def test_entry_point_help_smoke(script: str, needle: str) -> None:
    """``--help`` parses and exits 0 for every wiki CLI touched by this slice.

    ``PYTHONPATH`` mirrors the interpreter layout pytest itself provides via
    pyproject ``pythonpath``: bare ``python scripts/wiki/<x>.py --help`` cannot
    resolve the ``scripts`` namespace on main either (pre-existing F007-class
    gap in scripts/storage/__init__.py, outside this slice's owned paths).
    """
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("PYTEST_") and key != "COV_CORE_SOURCE"
    }
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.run(
        [str(project_python()), str(REPO_ROOT / script), "--help"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env=env,
    )
    assert proc.returncode == 0, f"{script} --help failed:\n{proc.stdout}\n{proc.stderr}"
    assert needle in proc.stdout
