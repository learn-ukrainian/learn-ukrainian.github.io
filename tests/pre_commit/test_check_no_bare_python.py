"""Regression tests for the no-bare-python pre-commit checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "pre_commit"
    / "check_no_bare_python.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("check_no_bare_python", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def checker():
    return _load()


@pytest.mark.parametrize(
    "script,line",
    [
        ("python3 scripts/build.py\n", 1),
        ("python scripts/build.py\n", 1),
        ("python3 scripts/build.py # -m venv\n", 1),
        ("python3 -m venv /tmp/demo && python3 scripts/build.py\n", 1),
        ("cmd; python3 scripts/build.py\n", 1),
        # Mid-token / escaped hashes are NOT comments in bash — must still catch
        # the bare-python command that follows on the same line.
        ("echo foo#bar; python3 scripts/build.py\n", 1),
        (r"echo \#; python3 scripts/build.py" + "\n", 1),
        # Escaped whitespace / semicolon are not word boundaries before #.
        (r"echo foo\ #bar; python3 scripts/build.py" + "\n", 1),
        (r"echo foo\;#bar; python3 scripts/build.py" + "\n", 1),
    ],
)
def test_rejects_bare_python_including_venv_laundering(
    checker, script: str, line: int
) -> None:
    hits = checker.bare_python_hits(script)
    assert hits
    assert hits[0][0] == line
