from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from scripts.audit.curriculum_manifest_canary import (
    collect_curriculum_files,
    compute_root_tree_hash,
    main,
    verify_manifest,
    write_manifest,
)


def _setup_mock_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    manifest_path = repo / "curriculum" / "l2-uk-en" / "curriculum_manifest.sha256.json"

    # Create dummy curriculum files
    doc_dir = repo / "site" / "src" / "content" / "docs" / "a1"
    doc_dir.mkdir(parents=True)
    (doc_dir / "lesson-1.mdx").write_text("# Lesson 1\nПривіт!", encoding="utf-8")

    curr_dir = repo / "curriculum" / "l2-uk-en"
    curr_dir.mkdir(parents=True, exist_ok=True)
    (curr_dir / "curriculum.yaml").write_text("version: '1.0'\n", encoding="utf-8")
    (curr_dir / "module-mapping.json").write_text("{}", encoding="utf-8")

    plan_dir = curr_dir / "lesson-plans" / "a1"
    plan_dir.mkdir(parents=True)
    (plan_dir / "lesson-1.yaml").write_text("slug: lesson-1\n", encoding="utf-8")

    mod_dir = curr_dir / "a1" / "lesson-1"
    mod_dir.mkdir(parents=True)
    (mod_dir / "module.md").write_text("Prose content\n", encoding="utf-8")

    voc_dir = curr_dir / "a1" / "vocabulary"
    voc_dir.mkdir(parents=True)
    (voc_dir / "lesson-1.yaml").write_text("items: []\n", encoding="utf-8")

    # Excluded dirs should not be picked up
    archive_dir = curr_dir / "_archive"
    archive_dir.mkdir(parents=True)
    (archive_dir / "old.md").write_text("old\n", encoding="utf-8")

    return repo, manifest_path


def test_collect_curriculum_files(tmp_path: Path):
    repo, _ = _setup_mock_repo(tmp_path)
    entries = collect_curriculum_files(repo)
    paths = [e["path"] for e in entries]

    assert "curriculum/l2-uk-en/curriculum.yaml" in paths
    assert "curriculum/l2-uk-en/module-mapping.json" in paths
    assert "curriculum/l2-uk-en/lesson-plans/a1/lesson-1.yaml" in paths
    assert "curriculum/l2-uk-en/a1/lesson-1/module.md" in paths
    assert "curriculum/l2-uk-en/a1/vocabulary/lesson-1.yaml" in paths
    assert "site/src/content/docs/a1/lesson-1.mdx" in paths
    assert not any("_archive" in p for p in paths)


def test_compute_root_tree_hash():
    entries1 = [
        {"path": "a.md", "sha256": "1" * 64},
        {"path": "b.md", "sha256": "2" * 64},
    ]
    entries2 = [
        {"path": "a.md", "sha256": "1" * 64},
        {"path": "b.md", "sha256": "3" * 64},
    ]
    h1 = compute_root_tree_hash(entries1)
    h2 = compute_root_tree_hash(entries2)
    assert h1 != h2
    assert len(h1) == 64


def test_write_and_verify_manifest_success(tmp_path: Path):
    repo, manifest_path = _setup_mock_repo(tmp_path)
    write_manifest(manifest_path, repo)
    assert manifest_path.exists()

    res = verify_manifest(manifest_path, repo)
    assert res["valid"] is True
    assert res["total_files"] == 6
    assert res["expected_files"] == 6
    assert len(res["modified"]) == 0
    assert len(res["added"]) == 0
    assert len(res["deleted"]) == 0


def test_verify_manifest_detects_modification(tmp_path: Path):
    repo, manifest_path = _setup_mock_repo(tmp_path)
    write_manifest(manifest_path, repo)

    # Tamper with a file
    doc = repo / "site" / "src" / "content" / "docs" / "a1" / "lesson-1.mdx"
    doc.write_text("# Tampered lesson\nMalicious content", encoding="utf-8")

    res = verify_manifest(manifest_path, repo)
    assert res["valid"] is False
    assert len(res["modified"]) == 1
    assert res["modified"][0]["path"] == "site/src/content/docs/a1/lesson-1.mdx"


def test_verify_manifest_detects_added_file(tmp_path: Path):
    repo, manifest_path = _setup_mock_repo(tmp_path)
    write_manifest(manifest_path, repo)

    # Add an unmanifested file
    new_doc = repo / "site" / "src" / "content" / "docs" / "a1" / "unauthorized.mdx"
    new_doc.write_text("# Unauthorized\n", encoding="utf-8")

    res = verify_manifest(manifest_path, repo)
    assert res["valid"] is False
    assert len(res["added"]) == 1
    assert res["added"][0] == "site/src/content/docs/a1/unauthorized.mdx"


def test_verify_manifest_detects_deleted_file(tmp_path: Path):
    repo, manifest_path = _setup_mock_repo(tmp_path)
    write_manifest(manifest_path, repo)

    # Remove a manifested file
    doc = repo / "site" / "src" / "content" / "docs" / "a1" / "lesson-1.mdx"
    doc.unlink()

    res = verify_manifest(manifest_path, repo)
    assert res["valid"] is False
    assert len(res["deleted"]) == 1
    assert res["deleted"][0] == "site/src/content/docs/a1/lesson-1.mdx"


def test_allow_sparse_checkout(tmp_path: Path):
    repo = tmp_path / "sparse-repo"
    repo.mkdir()
    manifest_path = repo / "curriculum" / "l2-uk-en" / "curriculum_manifest.sha256.json"

    # Missing manifest and curriculum tree with allow_sparse
    res = verify_manifest(manifest_path, repo, allow_sparse=True)
    assert res["valid"] is True
    assert res.get("sparse_skipped") is True


def test_main_cli_flow(tmp_path: Path):
    repo, manifest_path = _setup_mock_repo(tmp_path)

    # Write via CLI
    exit_write = main(["--write", "--manifest-path", str(manifest_path), "--repo-root", str(repo)])
    assert exit_write == 0
    assert manifest_path.exists()

    # Check via CLI
    exit_check = main(["--check", "--manifest-path", str(manifest_path), "--repo-root", str(repo)])
    assert exit_check == 0

    # Check JSON output via CLI
    with patch("builtins.print") as mock_print:
        exit_json = main(["--check", "--json", "--manifest-path", str(manifest_path), "--repo-root", str(repo)])
        assert exit_json == 0
        mock_print.assert_called_once()
        parsed = json.loads(mock_print.call_args[0][0])
        assert parsed["valid"] is True
