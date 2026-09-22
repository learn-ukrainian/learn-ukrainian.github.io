"""Tests for fresh build engine Part E2 CLI entry and --help standard compliance (#8431 r3)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.build.fresh.cli import _build_parser

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_cli_parser_help_standard_compliance():
    """Verify that main parser and all subparsers meet cli-help-standard.md."""
    parser = _build_parser()

    # 1. Main parser
    assert parser.description is not None
    assert "\n" in parser.description, "description must have at least two lines"
    assert parser.epilog is not None
    for section in ("Examples:", "Outputs:", "Exit codes:", "Related:"):
        assert section in parser.epilog, f"main parser epilog missing {section}"

    # 2. Subparsers
    subparsers_action = next(a for a in parser._actions if isinstance(a, type(parser.add_subparsers())))
    assert "render-prompt" in subparsers_action.choices
    assert "preflight" in subparsers_action.choices
    assert "write" in subparsers_action.choices

    for cmd_name, subp in subparsers_action.choices.items():
        assert subp.description is not None, f"subparser {cmd_name} missing description"
        assert "\n" in subp.description, f"subparser {cmd_name} description must have at least two lines"
        assert subp.epilog is not None, f"subparser {cmd_name} missing epilog"
        for section in ("Examples:", "Outputs:", "Exit codes:", "Related:"):
            assert section in subp.epilog, f"subparser {cmd_name} epilog missing {section}"
        for action in subp._actions:
            if action.dest != "help":
                assert action.help is not None and len(action.help) > 0, (
                    f"argument {action.dest} in subparser {cmd_name} missing help"
                )


@pytest.mark.parametrize("subcmd", [None, "render-prompt", "preflight", "write"])
def test_cli_subprocess_help(subcmd):
    """Run CLI --help in a clean subprocess with explicit timeout."""
    cmd = [sys.executable, "-m", "scripts.build.fresh.cli"]
    if subcmd:
        cmd.extend([subcmd, "--help"])
    else:
        cmd.append("--help")

    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=10, check=False)
    assert proc.returncode == 0
    assert "Examples:" in proc.stdout
    assert "Outputs:" in proc.stdout
    assert "Exit codes:" in proc.stdout
    assert "Related:" in proc.stdout


def test_main_module_forwarding():
    """Verify that python -m scripts.build.fresh --help also works and returns code 0."""
    cmd = [sys.executable, "-m", "scripts.build.fresh", "--help"]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=10, check=False)
    assert proc.returncode == 0
    assert "Fresh build engine E2" in proc.stdout
