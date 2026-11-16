"""Timeout contracts for the remaining #7213 slice 18 subprocess sites."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.generate_mdx import core as mdx_core
from scripts.generate_mdx import generate_plan_markdown

pytestmark = pytest.mark.reads_content


def _raise_timeout(calls: list[dict[str, Any]]):
    def fake_run(*args: object, **kwargs: Any) -> Any:
        calls.append({"args": args, **kwargs})
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    return fake_run


def test_mdx_validation_timeout_exits_nonzero(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(subprocess, "run", _raise_timeout(calls))
    monkeypatch.setattr(mdx_core, "get_modules_from_manifest", lambda *_args: [])
    monkeypatch.setattr(sys, "argv", ["generate_mdx.py", "--validate"])

    with pytest.raises(SystemExit) as raised:
        mdx_core.main()

    assert raised.value.code == 124
    assert calls[0]["timeout"] == mdx_core._VALIDATE_TIMEOUT_SECONDS == 60
    assert "MDX validation timed out after 60s" in capsys.readouterr().err


def test_plan_diff_timeout_exits_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    base_path = tmp_path / "project"
    archive = base_path / "docs" / "l2-uk-en" / "_archive" / "HIST-CURRICULUM-PLAN.md"
    archive.parent.mkdir(parents=True)
    archive.write_text("old\n", encoding="utf-8")
    fake_file = base_path / "scripts" / "generate_mdx" / "generate_plan_markdown.py"
    monkeypatch.setattr(generate_plan_markdown, "__file__", str(fake_file))
    monkeypatch.setattr(generate_plan_markdown, "generate_plan_markdown", lambda *_args: "new\n")
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(generate_plan_markdown.subprocess, "run", _raise_timeout(calls))
    monkeypatch.setattr(sys, "argv", ["generate_plan_markdown.py", "hist", "--diff"])

    with pytest.raises(SystemExit) as raised:
        generate_plan_markdown.main()

    assert raised.value.code == 124
    assert calls[0]["timeout"] == generate_plan_markdown._DIFF_TIMEOUT_SECONDS == 30
    assert "diff timed out after 30s" in capsys.readouterr().err
    assert not Path(calls[0]["args"][0][-1]).exists()
