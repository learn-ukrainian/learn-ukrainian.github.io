"""Bounded invariant selections bypass contention; full-tree runs stay locked (#9670)."""

from __future__ import annotations

import fcntl
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ci.pytest_dispatch_cap import DISPATCH_TASK_ENV, FULL_SUITE_BUSY, LOCK_ENV, is_full_suite

_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("paths", [[], ["."], ["tests"], [str(_REPO_ROOT / "tests")]])
@pytest.mark.parametrize(
    ("markexpr", "keyword", "expected"),
    [
        ("repo_wide", "", False),
        (" repo_wide ", "", False),
        ("repo_wide", "some_invariant", False),
        ("", "", True),
        ("", "some_invariant", True),
        ("not atlas_release", "", True),
        ("not repo_wide", "", True),
        ("repo_wide or slow", "", True),
        ("repo_wide and slow", "", True),
        ("unknown_marker", "", True),
    ],
)
def test_full_tree_filter_classification(paths: list[str], markexpr: str, keyword: str, expected: bool) -> None:
    source = SimpleNamespace(ARGS="args", TESTPATHS="testpaths")
    config = SimpleNamespace(
        args_source=source.ARGS if paths else source.TESTPATHS,
        ArgsSource=source,
        invocation_params=SimpleNamespace(dir=_REPO_ROOT),
        option=SimpleNamespace(markexpr=markexpr, keyword=keyword),
        getoption=lambda name: paths if name == "file_or_dir" else pytest.fail(f"unexpected option: {name}"),
    )
    assert is_full_suite(config) is expected


@pytest.mark.parametrize(
    ("args", "expected_passes"),
    [
        (["-m", "repo_wide"], 2),
        (["-m", "repo_wide", "-k", "first"], 1),
        (["-m", "repo_wide", "-p", "xdist", "-n", "2"], 2),
        ([], 0),
        (["-k", "first"], 0),
        (["-m", "not repo_wide"], 0),
        (["-m", "repo_wide or slow"], 0),
        (["-m", "unknown_marker"], 0),
    ],
)
def test_selection_while_another_full_suite_holds_lock(tmp_path: Path, args: list[str], expected_passes: int) -> None:
    """Exercise real pytest hooks with a held lock, including the xdist controller."""
    scripts = (_REPO_ROOT / "scripts").as_posix()
    (tmp_path / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        "testpaths = ['tests']\n"
        f"pythonpath = ['{scripts}']\n"
        "addopts = '-p ci.pytest_dispatch_cap'\n"
        "markers = ['repo_wide', 'slow']\n",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text(
        "import fcntl\n"
        "import os\n"
        "from pathlib import Path\n"
        "import pytest\n"
        "\n"
        "def record_execution(name):\n"
        "    with open(os.environ['LU_PYTEST_FULL_SUITE_LOCK'], 'r') as lock:\n"
        "        with pytest.raises(BlockingIOError):\n"
        "            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
        "    Path(name).touch()\n"
        "\n"
        "@pytest.mark.repo_wide\n"
        "def test_first():\n"
        "    record_execution('ran-first')\n"
        "\n"
        "@pytest.mark.repo_wide\n"
        "def test_second():\n"
        "    record_execution('ran-second')\n"
        "\n"
        "@pytest.mark.slow\n"
        "def test_unmarked():\n"
        "    record_execution('ran-unmarked')\n",
        encoding="utf-8",
    )
    lock_path = tmp_path / "full-suite.lock"
    env = os.environ.copy()
    env.update(
        {
            DISPATCH_TASK_ENV: "impl-9670-probe",
            LOCK_ENV: str(lock_path),
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTEST_PLUGINS": "ci.pytest_dispatch_cap",
        }
    )
    for name in ("PYTEST_ADDOPTS", "PYTEST_XDIST_WORKER", "PYTEST_XDIST_WORKER_COUNT", "PYTEST_XDIST_TESTRUNUID"):
        env.pop(name, None)
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", *args],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    combined = completed.stdout + completed.stderr
    if expected_passes:
        assert completed.returncode == 0, combined
        assert f"{expected_passes} passed" in completed.stdout, combined
        assert FULL_SUITE_BUSY not in combined
    else:
        assert completed.returncode == pytest.ExitCode.USAGE_ERROR, combined
        assert FULL_SUITE_BUSY in combined
    assert len(list(tmp_path.glob("ran-*"))) == expected_passes
    assert not (tmp_path / "ran-unmarked").exists()
