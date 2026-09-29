"""Fixture tests for the venv versus lock comparison."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.maintenance import venv_lock_drift


def test_fixture_freeze_and_lock_reports_all_difference_kinds(tmp_path: Path) -> None:
    project = tmp_path / "package"
    project.mkdir()
    (project / "pyproject.toml").write_text('[project]\nname = "Example_Local"\nversion = "1.0"\n')
    lock = venv_lock_drift.parse_lock(
        "# fixture\nAlpha==1.0\nbeta==2.0\n./package\n"
        "source @ git+https://example.invalid/repo@abc123#subdirectory=src\n",
        directory=tmp_path,
    )
    freeze = venv_lock_drift.parse_freeze(
        "alpha==2.0\nEXAMPLE-local==1.0\nextra==3.0\nsource==4.0\n"
    )
    assert venv_lock_drift.compare(freeze, lock) == (["beta"], ["extra"], ["alpha"])


def test_equal_fixture_handles_normalized_names(tmp_path: Path) -> None:
    lock = venv_lock_drift.parse_lock("Some_Package==1.2.3\nsome-package==1.2.3\n", directory=tmp_path)
    freeze = venv_lock_drift.parse_freeze("some-package==1.2.3\n")
    assert venv_lock_drift.compare(freeze, lock) == ([], [], [])


@pytest.mark.parametrize("text", ["package>=1\n", "package==1\npackage==2\n", "broken line\n"])
def test_invalid_lock_fails_closed(tmp_path: Path, text: str) -> None:
    with pytest.raises(ValueError):
        venv_lock_drift.parse_lock(text, directory=tmp_path)


def test_invalid_freeze_fails_closed() -> None:
    with pytest.raises(ValueError):
        venv_lock_drift.parse_freeze("editable @ file:///tmp/example\n")


def test_main_exits_on_drift(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    interpreter = tmp_path / "interpreter"
    interpreter.touch()
    lock = tmp_path / "requirements-lock.txt"
    lock.write_text("alpha==1\n")

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args[0], 0, stdout="alpha==2\n", stderr="")

    monkeypatch.setattr(venv_lock_drift.subprocess, "run", fake_run)
    assert venv_lock_drift.main(["--python", str(interpreter), "--lock", str(lock)]) == 1
    assert "version=1 (alpha)" in capsys.readouterr().out
