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
    "script",
    [
        "python3 -m venv /tmp/demo\n",
        "  python -m venv .sandbox\n",
        "#!/usr/bin/env bash\nset -euo pipefail\npython3 -m venv \"$VENV_DIR\"\n",
        '.venv/bin/python -m pytest tests/\n',
    ],
)
def test_allows_venv_bootstrap_and_project_interpreter(checker, script: str) -> None:
    assert checker.bare_python_hits(script) == []


@pytest.mark.parametrize(
    "script,line",
    [
        ("python3 scripts/build.py\n", 1),
        ("python scripts/build.py\n", 1),
        ("python3 scripts/build.py # -m venv\n", 1),
        ("python3 -m venv /tmp/demo && python3 scripts/build.py\n", 1),
        ("cmd; python3 scripts/build.py\n", 1),
    ],
)
def test_rejects_bare_python_including_venv_laundering(
    checker, script: str, line: int
) -> None:
    hits = checker.bare_python_hits(script)
    assert hits
    assert hits[0][0] == line


def test_files_mode_reports_path(checker, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "runner.sh"
    path.write_text("python3 scripts/build.py\n", encoding="utf-8")
    assert checker.check_files([path]) == 1
    err = capsys.readouterr().err
    assert "uses bare python/python3" in err
    assert "1:python3 scripts/build.py" in err
