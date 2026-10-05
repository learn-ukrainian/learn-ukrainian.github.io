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
    batch_check_blob_sizes,
    build_parser,
    check_changed_vs_base,
    load_allowlist,
    parse_classification_table,
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


def _write_classification_table(repo: Path, rows: list[tuple[str, str]]) -> None:
    """Write registry/artifacts/classification-v1.tsv with header and given (path, class) rows."""
    tsv_path = repo / "registry" / "artifacts" / "classification-v1.tsv"
    tsv_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["path\tmode\tblob\tsize\tclass\tgroup\treason\tjudgment"]
    for path, cls in rows:
        lines.append(f"{path}\t100644\t0123456789abcdef0123456789abcdef01234567\t1000\t{cls}\tgroup_x\treason_y\trule")
    tsv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_seed_allowlist_deterministic_excludes_branch_only(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST

    # Commit 1 on main: large file in data/ and classification table
    _create_blob(repo, "data/main_data.jsonl", THRESHOLD_BYTES + 100)
    _create_blob(repo, "curriculum/l2-uk-en/_archive/lit/session.json", THRESHOLD_BYTES + 200)
    _write_classification_table(repo, [("data/main_data.jsonl", "A")])
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


def test_seed_allowlist_reasons_and_only_class_a_leaves_git(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST

    _create_blob(repo, "data/class_a.bin", THRESHOLD_BYTES + 10)
    _create_blob(repo, "data/class_k.bin", THRESHOLD_BYTES + 20)
    _create_blob(repo, "data/class_s.bin", THRESHOLD_BYTES + 30)
    _create_blob(repo, "data/absent_row.bin", THRESHOLD_BYTES + 40)
    _create_blob(repo, "registry/lexicon/review.yaml", THRESHOLD_BYTES + 50)
    _create_blob(repo, "site/src/data/manifest.json", THRESHOLD_BYTES + 60)
    _create_blob(repo, "curriculum/l2-uk-en/_archive/lit/session.json", THRESHOLD_BYTES + 70)
    _create_blob(repo, "tools/other/binary.dat", THRESHOLD_BYTES + 80)

    _write_classification_table(
        repo,
        [
            ("data/class_a.bin", "A"),
            ("data/class_k.bin", "K"),
            ("data/class_s.bin", "S"),
        ],
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Commit diverse oversized files")

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
    entries = load_allowlist(allowlist)
    assert len(entries) == 8

    # Verify fact-derived reason per path category
    assert entries["data/class_a.bin"].reason == "existing tracked data; leaves git through the data/ split"
    assert entries["data/class_k.bin"].reason == "existing tracked data; kept in git as class K under the data/ split"
    assert (
        entries["data/class_s.bin"].reason
        == "existing tracked data; class S placeholder/control under the data/ split (not class A)"
    )
    assert (
        entries["data/absent_row.bin"].reason
        == "existing tracked data; absent from classification-v1.tsv; no split migration established"
    )
    assert (
        entries["registry/lexicon/review.yaml"].reason
        == "existing tracked data; kept in git as class K under the data/ split"
    )
    assert entries["site/src/data/manifest.json"].reason == "existing tracked data; grandfathered site-input"
    assert (
        entries["curriculum/l2-uk-en/_archive/lit/session.json"].reason
        == "existing tracked data; archived session record"
    )
    assert entries["tools/other/binary.dat"].reason == "existing tracked file, no migration planned"

    # Only class A path receives the split-migration reason
    split_paths = [p for p, e in entries.items() if "leaves git through the data/ split" in e.reason]
    assert split_paths == ["data/class_a.bin"]


def test_seed_reads_from_seed_commit_ignoring_worktree_and_branch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST

    _create_blob(repo, "data/item.bin", THRESHOLD_BYTES + 100)
    _write_classification_table(repo, [("data/item.bin", "A")])
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Main commit with class A")

    # Checkout branch and alter working tree / branch classification table to class K
    _git(repo, "checkout", "-b", "feature")
    _write_classification_table(repo, [("data/item.bin", "K")])
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Branch commit with class K")

    # Also make working tree dirty with corrupt classification table
    (repo / "registry" / "artifacts" / "classification-v1.tsv").write_text("CORRUPTED", encoding="utf-8")

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
    entries = load_allowlist(allowlist)
    assert entries["data/item.bin"].reason == "existing tracked data; leaves git through the data/ split"


def test_seed_fails_and_preserves_allowlist_on_missing_or_malformed_table(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)
    initial_content = "prior/file.bin\t6000000\tprior preserved reason\n"
    allowlist.write_text(initial_content, encoding="utf-8")

    def run_seed() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
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

    # 1. Missing table object on main
    res1 = run_seed()
    assert res1.returncode != 0
    assert "Failed to read or parse classification table" in res1.stderr
    assert allowlist.read_text(encoding="utf-8") == initial_content

    # 2. Empty table file
    tsv_path = repo / "registry" / "artifacts" / "classification-v1.tsv"
    tsv_path.parent.mkdir(parents=True, exist_ok=True)
    tsv_path.write_text("", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Empty table")
    res2 = run_seed()
    assert res2.returncode != 0
    assert allowlist.read_text(encoding="utf-8") == initial_content

    # 3. Missing required column 'class'
    tsv_path.write_text("path\tmode\tblob\tsize\tgroup\treason\tjudgment\ndata/x\t1\t2\t3\tg\tr\tj\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Missing class column")
    res3 = run_seed()
    assert res3.returncode != 0
    assert "missing required 'class' column" in res3.stderr
    assert allowlist.read_text(encoding="utf-8") == initial_content

    # 4. Unsupported class code 'Z'
    tsv_path.write_text(
        "path\tmode\tblob\tsize\tclass\tgroup\treason\tjudgment\ndata/x\t1\t2\t3\tZ\tg\tr\tj\n", encoding="utf-8"
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Unsupported class code")
    res4 = run_seed()
    assert res4.returncode != 0
    assert "Unsupported class code 'Z'" in res4.stderr
    assert allowlist.read_text(encoding="utf-8") == initial_content

    # 5. Duplicate path in table
    tsv_path.write_text(
        "path\tmode\tblob\tsize\tclass\tgroup\treason\tjudgment\n"
        "data/x\t1\t2\t3\tA\tg\tr\tj\n"
        "data/x\t1\t2\t3\tK\tg\tr\tj\n",
        encoding="utf-8",
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Duplicate path")
    res5 = run_seed()
    assert res5.returncode != 0
    assert "Duplicate path classification" in res5.stderr
    assert allowlist.read_text(encoding="utf-8") == initial_content

    # 6. Column count mismatch / malformed row
    tsv_path.write_text("path\tmode\tblob\tsize\tclass\tgroup\treason\tjudgment\ndata/x\t1\t2\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Malformed row")
    res6 = run_seed()
    assert res6.returncode != 0
    assert "column count mismatch" in res6.stderr
    assert allowlist.read_text(encoding="utf-8") == initial_content


def test_batch_check_many_files_and_repeated_shas(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)
    allowlist = repo / DEFAULT_ALLOWLIST
    allowlist.parent.mkdir(parents=True, exist_ok=True)

    _git(repo, "checkout", "-b", "feature")

    # Create 10 distinct small files
    for i in range(10):
        _create_blob(repo, f"src/small_{i}.txt", 100 + i)

    # Create 10 small files sharing the exact same blob content
    shared_small_content = b"identical small content"
    for i in range(10):
        p = repo / f"src/shared_small_{i}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(shared_small_content)

    # Create 4 large files sharing identical oversized content
    shared_large_target = repo / "data/large_shared_0.bin"
    shared_large_target.parent.mkdir(parents=True, exist_ok=True)
    with shared_large_target.open("wb") as f:
        f.seek(THRESHOLD_BYTES + 500)
        f.write(b"z")
    shared_large_bytes = shared_large_target.read_bytes()

    for i in range(1, 4):
        p = repo / f"data/large_shared_{i}.bin"
        p.write_bytes(shared_large_bytes)

    # Create 1 large file with unusual path (spaces and unicode)
    path_with_spaces = "data/folder with space/oversized файл.bin"
    _create_blob(repo, path_with_spaces, THRESHOLD_BYTES + 1000)

    # Create 1 unique large file
    _create_blob(repo, "data/unique_large.bin", THRESHOLD_BYTES + 2000)

    # Allowlist one of the shared large files and the unique large file
    allowlist.write_text(
        f"data/large_shared_0.bin\t{THRESHOLD_BYTES + 501}\texempt\n"
        f"data/unique_large.bin\t{THRESHOLD_BYTES + 2001}\texempt\n",
        encoding="utf-8",
    )

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "Add many files with repeated blobs")

    # Count git cat-file --batch-check subprocess calls
    batch_check_calls = 0
    orig_run = subprocess.run

    def tracked_run(*args, **kwargs):
        nonlocal batch_check_calls
        cmd = args[0] if args else kwargs.get("args", [])
        if len(cmd) >= 3 and cmd[0] == "git" and cmd[1] == "cat-file" and cmd[2] == "--batch-check":
            batch_check_calls += 1
        return orig_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", tracked_run)

    violations = check_changed_vs_base("main", allowlist, repo)

    # Must invoke git cat-file --batch-check exactly once for the whole diff!
    assert batch_check_calls == 1

    violation_paths = {v[0] for v in violations}
    assert violation_paths == {
        "data/large_shared_1.bin",
        "data/large_shared_2.bin",
        "data/large_shared_3.bin",
        path_with_spaces,
    }


def test_batch_check_blob_sizes_failure_modes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _init_repo(tmp_path)

    # 1. Invalid object ID format
    with pytest.raises(RuntimeError, match="Invalid object ID"):
        batch_check_blob_sizes(["not-a-valid-sha"], cwd=repo)
    with pytest.raises(RuntimeError, match="Invalid object ID"):
        batch_check_blob_sizes(["0123456789abcdef0123456789abcdef01234567; rm -rf"], cwd=repo)

    # 2. Empty list returns empty dict without running git
    assert batch_check_blob_sizes([], cwd=repo) == {}

    valid_sha1 = "0123456789abcdef0123456789abcdef01234567"
    valid_sha2 = "fedcba9876543210fedcba9876543210fedcba98"

    def mock_batch_output(stdout_text: str, returncode: int = 0):
        def fake_run(*args, **kwargs):
            return subprocess.CompletedProcess(
                args=args[0] if args else kwargs.get("args"),
                returncode=returncode,
                stdout=stdout_text.encode("utf-8"),
                stderr=b"error" if returncode != 0 else b"",
            )

        monkeypatch.setattr(subprocess, "run", fake_run)

    # 3. Missing object in batch output
    mock_batch_output(f"{valid_sha1} missing\n")
    with pytest.raises(RuntimeError, match="Git object missing in batch-check"):
        batch_check_blob_sizes([valid_sha1], cwd=repo)

    # 4. Malformed output line (not 3 tokens)
    mock_batch_output(f"{valid_sha1} invalid_tokens_here\n")
    with pytest.raises(RuntimeError, match="Malformed git cat-file --batch-check output"):
        batch_check_blob_sizes([valid_sha1], cwd=repo)

    # 5. Incomplete output (fewer lines than requested)
    mock_batch_output(f"{valid_sha1} blob 100\n")
    with pytest.raises(RuntimeError, match="response count mismatch"):
        batch_check_blob_sizes([valid_sha1, valid_sha2], cwd=repo)

    # 6. Extra output lines
    mock_batch_output(f"{valid_sha1} blob 100\n{valid_sha2} blob 200\nextra_line\n")
    with pytest.raises(RuntimeError, match="response count mismatch"):
        batch_check_blob_sizes([valid_sha1, valid_sha2], cwd=repo)

    # 7. Mismatched object SHA
    mock_batch_output(f"{valid_sha2} blob 100\n")
    with pytest.raises(RuntimeError, match="Mismatched batch-check response object"):
        batch_check_blob_sizes([valid_sha1], cwd=repo)

    # 8. Non-blob object type (e.g. tree)
    mock_batch_output(f"{valid_sha1} tree 100\n")
    with pytest.raises(RuntimeError, match="Expected blob object type"):
        batch_check_blob_sizes([valid_sha1], cwd=repo)

    # 9. Invalid size
    mock_batch_output(f"{valid_sha1} blob not_an_int\n")
    with pytest.raises(RuntimeError, match="Invalid blob size"):
        batch_check_blob_sizes([valid_sha1], cwd=repo)
    mock_batch_output(f"{valid_sha1} blob -5\n")
    with pytest.raises(RuntimeError, match="Invalid blob size"):
        batch_check_blob_sizes([valid_sha1], cwd=repo)

    # 10. Subprocess failure
    mock_batch_output("", returncode=1)
    with pytest.raises(RuntimeError, match="Git cat-file --batch-check failed"):
        batch_check_blob_sizes([valid_sha1], cwd=repo)


def test_parse_classification_table_unit() -> None:
    # Valid
    tsv = "path\tmode\tblob\tsize\tclass\tgroup\treason\tjudgment\ndata/x\t1\t2\t3\tA\tg\tr\tj\n"
    res = parse_classification_table(tsv)
    assert res == {"data/x": "A"}

    # Duplicate column
    with pytest.raises(ValueError, match="duplicate 'path' or 'class' column"):
        parse_classification_table("path\tclass\tclass\ndata/x\tA\tA\n")

    # Missing column
    with pytest.raises(ValueError, match="missing required 'path' column"):
        parse_classification_table("other\tclass\nfoo\tA\n")

    # Empty content
    with pytest.raises(ValueError, match="content is empty"):
        parse_classification_table("   \n")
