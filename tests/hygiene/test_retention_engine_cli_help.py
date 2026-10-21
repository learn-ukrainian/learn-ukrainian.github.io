"""retention_engine --help meets the CLI help standard (#9737 review)."""

from __future__ import annotations

import argparse

import pytest

from scripts.hygiene import retention_engine


def _help(argv: list[str], capsys: pytest.CaptureFixture[str]) -> str:
    with pytest.raises(SystemExit) as exc:
        retention_engine.main(argv)
    assert exc.value.code == 0
    return capsys.readouterr().out


def test_top_level_help_has_examples_outputs_exit_codes_and_related(capsys: pytest.CaptureFixture[str]) -> None:
    out = _help(["--help"], capsys)
    assert ".venv/bin/python scripts/hygiene/retention_engine.py plan" in out
    for section in ("Outputs:", "Exit codes:", "Related:"):
        assert section in out
    assert "4 plan digest mismatch" in out


def test_every_argument_has_help() -> None:
    parser = retention_engine.build_parser()
    subparsers = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
    for name, sub in subparsers.choices.items():
        for action in sub._actions:
            if isinstance(action, argparse._HelpAction):
                continue
            assert action.help, f"{name} {action.option_strings} has no help"


def test_invalid_usage_exits_2(capsys: pytest.CaptureFixture[str]) -> None:
    for argv in ([], ["apply"], ["plan", "--stale-hours", "soon"]):
        with pytest.raises(SystemExit) as exc:
            retention_engine.main(argv)
        assert exc.value.code == 2, argv
    capsys.readouterr()
