"""An explicit ``--basetemp`` inside a directory the data backup reads is refused (#12153)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = ("pytester",)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _run_nested(pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch, basetemp: Path) -> pytest.RunResult:
    """Run a one-test session that loads the real scratch plugin with an explicit base temp."""
    monkeypatch.setenv("PYTHONPATH", str(_REPO_ROOT))
    pytester.makepyfile(test_probe="def test_probe(tmp_path):\n    assert tmp_path.is_dir()\n")
    return pytester.runpytest_subprocess("-q", "-p", "scripts.common.pytest_scratch", "--basetemp", str(basetemp))


def test_basetemp_under_a_checkouts_agent_dir_is_refused_before_anything_is_created(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = pytester.mkdir("primary")
    (checkout / ".git").mkdir()
    basetemp = checkout / ".agent" / "review-closeout" / "round" / "pt" / "bt"

    result = _run_nested(pytester, monkeypatch, basetemp)

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert "which the data backup reads" in result.stderr.str()
    assert not (checkout / ".agent").exists()


def test_basetemp_reached_through_a_symlink_then_dotdot_is_refused(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pytest collapses ``..`` before the link is followed, so ``link/../bt`` lands beside the link."""
    checkout = pytester.mkdir("primary")
    (checkout / ".git").mkdir()
    (checkout / ".agent").mkdir()
    (checkout / ".agent" / "link").symlink_to(pytester.mkdir("elsewhere"))

    result = _run_nested(pytester, monkeypatch, checkout / ".agent" / "link" / ".." / "bt")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert not (checkout / ".agent" / "bt").exists()


def test_basetemp_outside_every_kept_root_still_runs(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    checkout = pytester.mkdir("primary")
    (checkout / ".git").mkdir()
    basetemp = pytester.mkdir("scratch") / "bt"

    result = _run_nested(pytester, monkeypatch, basetemp)

    assert result.ret == pytest.ExitCode.OK
    assert basetemp.is_dir()
