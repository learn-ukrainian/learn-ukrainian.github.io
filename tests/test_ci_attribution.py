"""Unit tests for CI test timeout attribution and per-worker breadcrumb hooks."""

import os
import subprocess
import sys
from pathlib import Path

from tests.conftest import _get_breadcrumb_file, pytest_runtest_logfinish, pytest_runtest_logstart


def test_get_breadcrumb_file_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PYTEST_BREADCRUMB_DIR", raising=False)
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)

    breadcrumb_file = _get_breadcrumb_file()
    assert breadcrumb_file is not None
    assert breadcrumb_file.name == "breadcrumb_master.txt"
    assert breadcrumb_file.parent.name == ".pytest_breadcrumbs"


def test_get_breadcrumb_file_custom_dir_and_worker(tmp_path: Path, monkeypatch) -> None:
    bdir = tmp_path / "custom_breadcrumbs"
    monkeypatch.setenv("PYTEST_BREADCRUMB_DIR", str(bdir))
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw2")

    breadcrumb_file = _get_breadcrumb_file()
    assert breadcrumb_file is not None
    assert breadcrumb_file.name == "breadcrumb_gw2.txt"
    assert breadcrumb_file.parent == bdir


def test_breadcrumb_logstart_and_logfinish(tmp_path: Path, monkeypatch) -> None:
    bdir = tmp_path / "breadcrumbs"
    monkeypatch.setenv("PYTEST_BREADCRUMB_DIR", str(bdir))
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")

    pytest_runtest_logstart("tests/test_foo.py::test_bar", ("tests/test_foo.py", 1, "test_bar"))
    breadcrumb_file = bdir / "breadcrumb_gw0.txt"
    assert breadcrumb_file.exists()
    assert breadcrumb_file.read_text(encoding="utf-8") == "START tests/test_foo.py::test_bar\n"

    pytest_runtest_logfinish("tests/test_foo.py::test_bar", ("tests/test_foo.py", 1, "test_bar"))
    lines = breadcrumb_file.read_text(encoding="utf-8").splitlines()
    assert lines == [
        "START tests/test_foo.py::test_bar",
        "FINISH tests/test_foo.py::test_bar",
    ]


def test_breadcrumb_subprocess_pytest_run(tmp_path: Path) -> None:
    repo_root = Path(__file__).parents[1]
    bdir = tmp_path / "breadcrumbs"
    test_file = repo_root / "tests" / "_temp_breadcrumb_test.py"
    try:
        test_file.write_text("def test_one(): pass\ndef test_two(): pass\n", encoding="utf-8")

        env = os.environ.copy()
        env["PYTEST_BREADCRUMB_DIR"] = str(bdir)
        env["PYTEST_XDIST_WORKER"] = "gw1"

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(test_file),
            "-o",
            f"cache_dir={tmp_path / '.pytest_cache'}",
        ]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False, cwd=str(repo_root), timeout=30)
        assert res.returncode == 0, f"stdout: {res.stdout}\nstderr: {res.stderr}"

        breadcrumb_file = bdir / "breadcrumb_gw1.txt"
        assert breadcrumb_file.exists(), (
            f"Breadcrumb file missing in {bdir}. Files present: {list(bdir.glob('*')) if bdir.exists() else 'bdir missing'}\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )
        lines = breadcrumb_file.read_text(encoding="utf-8").splitlines()
        assert "START tests/_temp_breadcrumb_test.py::test_one" in lines
        assert "FINISH tests/_temp_breadcrumb_test.py::test_one" in lines
        assert "START tests/_temp_breadcrumb_test.py::test_two" in lines
        assert "FINISH tests/_temp_breadcrumb_test.py::test_two" in lines
    finally:
        if test_file.exists():
            test_file.unlink()
