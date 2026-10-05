"""Tests for scripts/ci/check_large_files.py (#8510)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci.check_large_files import (
    DEFAULT_ALLOWLIST,
    THRESHOLD_BYTES,
    build_parser,
    load_allowlist,
)

_PYTHON = sys.executable
_GIT_BIN = os.environ.get("AGENT_REAL_GIT", "git")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_GIT_BIN, *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "commit.gpgsign", "false")

    # Initial commit
    init_file = repo / "README.md"
    init_file.write_text("# Test Repo\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "Initial commit")
    return repo


def _create_blob(repo: Path, rel_path: str, size: int) -> None:
    target = repo / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as f:
        if size > 0:
            f.seek(size - 1)
            f.write(b"x")


def test_new_oversized_blob_fails(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text("# empty allowlist\n", encoding="utf-8")

    # Create feature branch with oversized blob
    _git(repo, "checkout", "-b", "feature")
    _create_blob(repo, "data/large.bin", THRESHOLD_BYTES + 1)
    _git(repo, "add", "data/large.bin")
    _git(repo, "commit", "-m", "Add large blob")

    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 1
    assert "Large file guard violation" in res.stderr
    assert "'data/large.bin'" in res.stderr
    assert f"Size: {THRESHOLD_BYTES + 1} bytes" in res.stderr
    assert f"threshold: {THRESHOLD_BYTES} bytes" in res.stderr
    assert "scripts/storage/artifacts.py" in res.stderr


def test_allowlisted_oversized_blob_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text(
        f"data/large.bin\t{THRESHOLD_BYTES + 100}\texisting tracked data; leaves git through the data/ split\n",
        encoding="utf-8",
    )

    _git(repo, "checkout", "-b", "feature")
    _create_blob(repo, "data/large.bin", THRESHOLD_BYTES + 100)
    _git(repo, "add", "data/large.bin")
    _git(repo, "commit", "-m", "Add allowlisted blob")

    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 0
    assert "Large files check passed" in res.stdout


def test_modified_allowlisted_blob_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text(
        f"data/large.bin\t{THRESHOLD_BYTES + 100}\texisting tracked data; leaves git through the data/ split\n",
        encoding="utf-8",
    )

    # Base commit already has the large file
    _create_blob(repo, "data/large.bin", THRESHOLD_BYTES + 100)
    _git(repo, "add", "data/large.bin")
    _git(repo, "commit", "-m", "Base has large file")

    # Feature branch modifies the large file to even larger size
    _git(repo, "checkout", "-b", "feature")
    _create_blob(repo, "data/large.bin", THRESHOLD_BYTES + 5000)
    _git(repo, "add", "data/large.bin")
    _git(repo, "commit", "-m", "Modify large file")

    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 0
    assert "Large files check passed" in res.stdout


def test_renamed_oversized_blob_to_unallowlisted_destination_fails(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text(
        f"data/old_path.bin\t{THRESHOLD_BYTES + 100}\texisting tracked data; leaves git through the data/ split\n",
        encoding="utf-8",
    )

    # Base commit has old_path.bin
    _create_blob(repo, "data/old_path.bin", THRESHOLD_BYTES + 100)
    _git(repo, "add", "data/old_path.bin")
    _git(repo, "commit", "-m", "Base has old_path.bin")

    # Feature branch renames old_path.bin to new_path.bin
    _git(repo, "checkout", "-b", "feature")
    _git(repo, "mv", "data/old_path.bin", "data/new_path.bin")
    _git(repo, "commit", "-m", "Rename to new_path.bin")

    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 1
    assert "Large file guard violation" in res.stderr
    assert "'data/new_path.bin'" in res.stderr


def test_renamed_oversized_blob_to_allowlisted_destination_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text(
        f"data/new_path.bin\t{THRESHOLD_BYTES + 100}\texisting tracked data; leaves git through the data/ split\n",
        encoding="utf-8",
    )

    _create_blob(repo, "data/old_path.bin", THRESHOLD_BYTES + 100)
    _git(repo, "add", "data/old_path.bin")
    _git(repo, "commit", "-m", "Base has old_path.bin")

    _git(repo, "checkout", "-b", "feature")
    _git(repo, "mv", "data/old_path.bin", "data/new_path.bin")
    _git(repo, "commit", "-m", "Rename to new_path.bin")

    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 0
    assert "Large files check passed" in res.stdout


def test_small_blob_passes(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text("# empty\n", encoding="utf-8")

    _git(repo, "checkout", "-b", "feature")
    _create_blob(repo, "src/small.py", 1024)
    _git(repo, "add", "src/small.py")
    _git(repo, "commit", "-m", "Add small file")

    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 0
    assert "Large files check passed" in res.stdout


def test_deleted_blob_ignored(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text("# empty\n", encoding="utf-8")

    _create_blob(repo, "data/large_to_delete.bin", THRESHOLD_BYTES + 500)
    _git(repo, "add", "data/large_to_delete.bin")
    _git(repo, "commit", "-m", "Base with large file")

    _git(repo, "checkout", "-b", "feature")
    _git(repo, "rm", "data/large_to_delete.bin")
    _git(repo, "commit", "-m", "Delete large file")

    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 0
    assert "Large files check passed" in res.stdout


def test_exact_threshold_boundary(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text("# empty\n", encoding="utf-8")

    # Case 1: Exactly 5,242,880 bytes passes
    _git(repo, "checkout", "-b", "exact-pass")
    _create_blob(repo, "data/exact.bin", THRESHOLD_BYTES)
    _git(repo, "add", "data/exact.bin")
    _git(repo, "commit", "-m", "Add exact 5MB file")

    res_pass = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res_pass.returncode == 0, res_pass.stderr
    assert "Large files check passed" in res_pass.stdout

    # Case 2: 5,242,880 + 1 bytes fails
    _git(repo, "checkout", "main")
    _git(repo, "checkout", "-b", "boundary-fail")
    _create_blob(repo, "data/over_by_one.bin", THRESHOLD_BYTES + 1)
    _git(repo, "add", "data/over_by_one.bin")
    _git(repo, "commit", "-m", "Add 5MB + 1 byte file")

    res_fail = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res_fail.returncode == 1
    assert "Large file guard violation" in res_fail.stderr
    assert "'data/over_by_one.bin'" in res_fail.stderr
    assert f"Size: {THRESHOLD_BYTES + 1} bytes" in res_fail.stderr


def test_missing_base_ref_fails(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text("# empty\n", encoding="utf-8")

    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "non_existent_ref_12345",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 1
    assert "ERROR: Cannot resolve base ref 'non_existent_ref_12345' to a commit" in res.stderr


def test_sparse_checkout_independence(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text("# empty\n", encoding="utf-8")

    _git(repo, "checkout", "-b", "feature")
    _create_blob(repo, "sparse_dir/large.bin", THRESHOLD_BYTES + 500)
    _git(repo, "add", "sparse_dir/large.bin")
    _git(repo, "commit", "-m", "Add large in sparse_dir")

    # Enable sparse-checkout and exclude sparse_dir
    _git(repo, "sparse-checkout", "set", "--no-cone", "/README.md")

    # Ensure sparse_dir/large.bin is absent from the working tree
    assert not (repo / "sparse_dir" / "large.bin").exists()

    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 1
    assert "Large file guard violation" in res.stderr
    assert "'sparse_dir/large.bin'" in res.stderr


def test_filenames_containing_spaces(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text("# empty\n", encoding="utf-8")

    _git(repo, "checkout", "-b", "feature")
    path_with_spaces = "data/folder with spaces/file with spaces.bin"
    _create_blob(repo, path_with_spaces, THRESHOLD_BYTES + 200)
    _git(repo, "add", path_with_spaces)
    _git(repo, "commit", "-m", "Add file with spaces")

    # Should fail when unallowlisted
    res_fail = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res_fail.returncode == 1
    assert repr(path_with_spaces) in res_fail.stderr

    # Should pass when allowlisted
    allowlist.write_text(
        f"{path_with_spaces}\t{THRESHOLD_BYTES + 200}\texisting tracked data; leaves git through the data/ split\n",
        encoding="utf-8",
    )
    res_pass = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res_pass.returncode == 0
    assert "Large files check passed" in res_pass.stdout


def test_seed_allowlist_deterministic_excludes_branch_only(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST

    # Commit 1 on main: large file in data/
    _create_blob(repo, "data/main_data.jsonl", THRESHOLD_BYTES + 100)
    # Commit 2 on main: large file in curriculum archive
    _create_blob(repo, "curriculum/l2-uk-en/_archive/lit/session.json", THRESHOLD_BYTES + 200)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Add main large files")

    # Feature branch adds branch-only large file
    _git(repo, "checkout", "-b", "feature")
    _create_blob(repo, "data/branch_only.bin", THRESHOLD_BYTES + 300)
    _git(repo, "add", "data/branch_only.bin")
    _git(repo, "commit", "-m", "Add branch-only file")

    # Run seed allowlist targeting main branch
    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--seed-allowlist",
            "--seed-ref",
            "main",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 0
    assert "Seeded 2 entries" in res.stdout

    entries = load_allowlist(allowlist)
    assert len(entries) == 2
    assert "data/main_data.jsonl" in entries
    assert "curriculum/l2-uk-en/_archive/lit/session.json" in entries
    assert "data/branch_only.bin" not in entries

    assert entries["data/main_data.jsonl"].reason == "existing tracked data; leaves git through the data/ split"
    assert (
        entries["curriculum/l2-uk-en/_archive/lit/session.json"].reason
        == "existing tracked data; archived session record"
    )


def test_malformed_allowlist_fails(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)

    # Case 1: Missing tab delimiter
    allowlist.write_text("data/file.bin 1234567 some reason\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed allowlist entry"):
        load_allowlist(allowlist)

    # Case 2: Non-integer size
    allowlist.write_text("data/file.bin\tnot-a-number\tsome reason\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid size"):
        load_allowlist(allowlist)

    # Case 3: Empty reason
    allowlist.write_text("data/file.bin\t1234567\t\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Empty path or reason"):
        load_allowlist(allowlist)


def test_git_failure_propagation(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    allowlist.write_text("# empty\n", encoding="utf-8")

    # Run check against invalid base ref
    res = subprocess.run(
        [
            _PYTHON,
            "-m",
            "scripts.ci.check_large_files",
            "--changed-vs-base",
            "invalid_base_ref_abc",
            "--repo-root",
            str(repo),
            "--allowlist",
            str(allowlist),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert res.returncode == 1
    assert "ERROR:" in res.stderr


def test_cli_help_standards() -> None:
    parser = build_parser()
    help_text = parser.format_help()

    # Description standard: 2 lines
    assert "Guard repository against untracked large blobs over 5 MB." in help_text
    assert "Use in CI checks and merge queue" in help_text

    # Options with defaults
    assert "--changed-vs-base" in help_text
    assert "--seed-allowlist" in help_text
    assert "--threshold" in help_text
    assert "5242880" in help_text
    assert "--seed-ref" in help_text
    assert "origin/main" in help_text

    # Epilog standards: Examples, Outputs, Exit codes, Related
    assert "Examples:" in help_text
    assert "Outputs:" in help_text
    assert "Exit codes:" in help_text
    assert "Related:" in help_text
