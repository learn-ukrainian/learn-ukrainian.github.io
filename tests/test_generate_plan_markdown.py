"""Coverage for the manually invoked legacy plan Markdown renderer."""

from __future__ import annotations

import sys

import pytest

from scripts.generate_mdx import generate_plan_markdown


def test_cli_renders_kept_hist_level_from_repository_root(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["generate_plan_markdown.py", "hist"])

    generate_plan_markdown.main()

    output = capsys.readouterr().out
    assert "# HIST Curriculum Plan" in output
    assert "## Phase Structure" in output
    assert "## Module Details (from YAML plans)" in output


@pytest.mark.parametrize("level", ["a1", "a2"])
def test_cli_refuses_retired_level_plans(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    level: str,
) -> None:
    monkeypatch.setattr(sys, "argv", ["generate_plan_markdown.py", level])

    with pytest.raises(SystemExit) as raised:
        generate_plan_markdown.main()

    assert raised.value.code == 1
    assert f"Level plan '{level}' was retired in #9252" in capsys.readouterr().err
