"""Tests for checkout_write_guard helper and regression tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tests.helpers.checkout_write_guard import (
    PROJECT_ROOT,
    CheckoutWriteError,
    CheckoutWriteGuard,
)


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, capture_output=True, check=True, timeout=30)


def test_guard_detects_tracked_file_edit_in_fixture_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("initial content\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    guard = CheckoutWriteGuard(repo_root=tmp_path)
    tracked.write_text("modified content\n", encoding="utf-8")

    with pytest.raises(CheckoutWriteError) as exc_info:
        guard.verify()
    assert "tracked file modified: tracked.txt" in str(exc_info.value)


def test_guard_detects_request_log_creation_in_fixture_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("logs/\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "add gitignore"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    guard = CheckoutWriteGuard(repo_root=tmp_path)
    log_file = tmp_path / "logs" / "mcp-sources-requests.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text('{"tool": "test"}\n', encoding="utf-8")

    with pytest.raises(CheckoutWriteError) as exc_info:
        guard.verify()
    assert "guarded checkout artifact created: logs/mcp-sources-requests.jsonl" in str(exc_info.value)


def test_guard_detects_request_log_append_in_fixture_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("logs/\n", encoding="utf-8")
    log_file = tmp_path / "logs" / "mcp-sources-requests.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.write_text('{"tool": "test1"}\n', encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    guard = CheckoutWriteGuard(repo_root=tmp_path)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write('{"tool": "test2"}\n')

    with pytest.raises(CheckoutWriteError) as exc_info:
        guard.verify()
    assert "guarded checkout artifact modified/appended: logs/mcp-sources-requests.jsonl" in str(exc_info.value)


def test_guard_detects_manifest_creation_in_fixture_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("site/src/data/lexicon-manifest.json\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    guard = CheckoutWriteGuard(repo_root=tmp_path)
    manifest = tmp_path / "site" / "src" / "data" / "lexicon-manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text('{"entries": []}\n', encoding="utf-8")

    with pytest.raises(CheckoutWriteError) as exc_info:
        guard.verify()
    assert "guarded checkout artifact created: site/src/data/lexicon-manifest.json" in str(exc_info.value)


def test_guard_accepts_unchanged_run_in_fixture_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    dummy = tmp_path / "file.txt"
    dummy.write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    with CheckoutWriteGuard(repo_root=tmp_path) as guard:
        # Writing to exempt cache directory must not trigger guard
        cache_file = tmp_path / ".pytest_cache" / "cache.json"
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text("{}", encoding="utf-8")

    assert guard.check() == []


def test_guard_accounts_for_preexisting_changes_and_sparse_files(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    dirty = tmp_path / "dirty.txt"
    dirty.write_text("v1\n", encoding="utf-8")
    sparse_tracked = tmp_path / "sparse.txt"
    sparse_tracked.write_text("sparse\n", encoding="utf-8")
    subprocess.run(["git", "add", "dirty.txt", "sparse.txt"], cwd=tmp_path, capture_output=True, check=True, timeout=30)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True, timeout=30)

    # Simulate dirty state before guard starts
    dirty.write_text("v2-uncommitted\n", encoding="utf-8")
    # Simulate sparse checkout: tracked file is missing from working tree
    sparse_tracked.unlink()

    with CheckoutWriteGuard(repo_root=tmp_path) as guard:
        pass

    assert guard.check() == []


@pytest.mark.parametrize("malformed", [False, True], ids=["missing", "malformed"])
def test_sparse_store_is_loaded_only_by_dependent_tests(tmp_path: Path, malformed: bool) -> None:
    """Exercise the actual lazy reader, rather than a copied skip implementation."""
    store = tmp_path / "_words.yaml"
    if malformed:
        store.write_text("invalid: yaml: [unclosed\n", encoding="utf-8")
    sample = tmp_path / "test_store.py"
    sample.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(PROJECT_ROOT)!r})\n"
        "from pathlib import Path\n"
        "from tests.build import test_fresh_a1_choice_checks as choices\n"
        f"choices.A1_STORE = Path({str(store)!r})\n"
        "def test_independent():\n"
        "    assert choices._record(1, 'sample', [])['id'] == 'W-1'\n"
        "def test_store():\n"
        "    choices._store_record('W-061')\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-rs", str(sample)],
        cwd=tmp_path, capture_output=True, text=True, timeout=60,
    )
    assert "collected 2 items" in result.stdout, result.stdout + result.stderr
    if malformed:
        assert result.returncode == 1, result.stdout + result.stderr
        assert "1 failed, 1 passed" in result.stdout
        assert "ScannerError" in result.stdout or "ParserError" in result.stdout
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "1 passed, 1 skipped" in result.stdout
        assert "Missing repository-relative prerequisite: curriculum/l2-uk-en/evidence/a1/_words.yaml" in result.stdout


@pytest.mark.parametrize("workers", [0, 2], ids=["serial", "xdist"])
@pytest.mark.parametrize("write", [False, True], ids=["unchanged", "planted-write"])
def test_registered_guard_enforces_normal_pytest_session(tmp_path: Path, write: bool, workers: int) -> None:
    """No -p: temporary conftest registration must fail a passing writer test."""
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("logs/\n", encoding="utf-8")
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "existing.jsonl").write_text('{}\n', encoding="utf-8")
    plugin = (PROJECT_ROOT / "tests/helpers/checkout_write_guard.py").read_text(encoding="utf-8")
    (tmp_path / "checkout_write_guard.py").write_text(
        plugin.replace("Path(__file__).resolve().parents[2]", "Path(__file__).resolve().parent"),
        encoding="utf-8",
    )
    (tmp_path / "conftest.py").write_text('pytest_plugins = ["checkout_write_guard"]\n', encoding="utf-8")
    (tmp_path / "test_sample.py").write_text(
        "from pathlib import Path\n"
        "def test_sample():\n" + (
            "    Path('logs/mcp-sources-requests.jsonl').write_text('{}\\n')\n" if write else "    assert True\n"
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "test_sample.py", *(["-n", str(workers)] if workers else [])],
        cwd=tmp_path, capture_output=True, text=True, timeout=60,
    )
    assert "1 passed" in result.stdout, result.stdout + result.stderr
    if write:
        assert result.returncode == 1, result.stdout + result.stderr
        assert "ERROR: checkout mutations detected by checkout_write_guard" in result.stdout
        assert "guarded checkout artifact created: logs/mcp-sources-requests.jsonl" in result.stdout
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert "checkout mutations detected" not in result.stdout


@pytest.mark.parametrize("change", ["unchanged", "append", "new"], ids=["unchanged-log", "append-log", "new-log"])
def test_guard_baselines_preexisting_ignored_logs(tmp_path: Path, change: str) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("logs/\n", encoding="utf-8")
    logs = tmp_path / "logs/nested"
    logs.mkdir(parents=True)
    existing = logs / "existing.jsonl"
    existing.write_text('{}\n', encoding="utf-8")
    guard = CheckoutWriteGuard(repo_root=tmp_path)
    if change == "append":
        with existing.open("a", encoding="utf-8") as stream:
            stream.write('{}\n')
        assert guard.check() == ["pre-existing checkout log modified/appended: logs/nested/existing.jsonl"]
    elif change == "new":
        (logs / "new.jsonl").write_text('{}\n', encoding="utf-8")
        assert guard.check() == ["unexpected file created in checkout logs/: logs/nested/new.jsonl"]
    else:
        assert guard.check() == []


def test_guard_active_during_fresh_build_and_sources_samples() -> None:
    """Verify CheckoutWriteGuard and its pytest plugin run cleanly against rep tests."""
    with CheckoutWriteGuard() as guard:
        res = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "--trace-config",
                "tests/build/test_fresh_runner.py",
                "tests/test_mcp_sources_server.py",
                "-k",
                "test_runner_real_draft_report_has_numeric_single_lesson_totals or test_unknown_tool_returns_error",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )
        assert res.returncode == 0, f"pytest failed:\n{res.stdout}\n{res.stderr}"
        assert "2 passed" in res.stdout
        assert "module 'tests.helpers.checkout_write_guard'" in res.stdout
    assert guard.check() == []
