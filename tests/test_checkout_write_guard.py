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


def test_sparse_prerequisite_skip_when_words_yaml_missing(tmp_path: Path) -> None:
    # In an environment where curriculum/l2-uk-en/evidence/a1/_words.yaml does not exist:
    code = (
        "import pytest\n"
        "from pathlib import Path\n"
        "ROOT = Path('/tmp/empty_fake_sparse_root')\n"
        "A1_STORE = ROOT / 'curriculum/l2-uk-en/evidence/a1/_words.yaml'\n"
        "if not A1_STORE.is_file():\n"
        "    pytest.skip(f'Missing repository-relative prerequisite: {A1_STORE}', allow_module_level=True)\n"
    )
    test_script = tmp_path / "test_skip.py"
    test_script.write_text(code, encoding="utf-8")
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-rs", str(test_script)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Pytest returns 5 (ExitCode.NO_TESTS_COLLECTED) when an entire module is skipped at module level
    assert res.returncode in (0, 5)
    assert "skipped" in res.stdout
    assert "Missing repository-relative prerequisite:" in res.stdout


def test_sparse_prerequisite_fails_when_words_yaml_malformed(tmp_path: Path) -> None:
    code = (
        "import pytest, yaml\n"
        "from pathlib import Path\n"
        f"A1_STORE = Path(r'{tmp_path / '_words.yaml'}')\n"
        "if not A1_STORE.is_file():\n"
        "    pytest.skip('missing', allow_module_level=True)\n"
        "STORE_WORDS = yaml.safe_load(A1_STORE.read_text(encoding='utf-8'))['words']\n"
    )
    bad_yaml = tmp_path / "_words.yaml"
    bad_yaml.write_text("invalid: yaml: [unclosed\n", encoding="utf-8")
    test_script = tmp_path / "test_malformed.py"
    test_script.write_text(code, encoding="utf-8")
    res = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_script)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode != 0
    assert "ScannerError" in res.stdout or "ParserError" in res.stdout


def test_guard_active_during_fresh_build_and_sources_samples() -> None:
    """Verify CheckoutWriteGuard and its pytest plugin run cleanly against rep tests."""
    with CheckoutWriteGuard() as guard:
        res = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-p",
                "tests.helpers.checkout_write_guard",
                "tests/build/test_fresh_runner.py",
                "-k",
                "test_runner_real_draft_report_has_numeric_single_lesson_totals",
                "tests/test_mcp_sources_server.py",
                "-k",
                "test_unknown_tool_returns_error",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=60,
        )
        assert res.returncode == 0, f"pytest failed:\n{res.stdout}\n{res.stderr}"
    assert guard.check() == []
