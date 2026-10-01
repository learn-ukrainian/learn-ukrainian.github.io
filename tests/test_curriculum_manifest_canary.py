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

    readings_dir = repo / "site" / "src" / "content" / "readings"
    readings_dir.mkdir(parents=True)
    (readings_dir / "shevchenko-test.mdx").write_text("# Думи мої\n", encoding="utf-8")

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
    (mod_dir / "vocabulary.yaml").write_text("items: []\n", encoding="utf-8")
    (mod_dir / "activities.yaml").write_text("activities: []\n", encoding="utf-8")
    (mod_dir / "resources.yaml").write_text("resources: []\n", encoding="utf-8")

    # Module with 'review' in slug should NOT be excluded
    rev_mod_dir = curr_dir / "b1" / "motion-base-review"
    rev_mod_dir.mkdir(parents=True)
    (rev_mod_dir / "module.md").write_text("Motion review\n", encoding="utf-8")

    # Excluded dirs should not be picked up
    archive_dir = curr_dir / "_archive"
    archive_dir.mkdir(parents=True)
    (archive_dir / "old.md").write_text("old\n", encoding="utf-8")

    orch_dir = mod_dir / "orchestration"
    orch_dir.mkdir(parents=True)
    (orch_dir / "run.md").write_text("run\n", encoding="utf-8")

    review_dir = mod_dir / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "critique.md").write_text("critique\n", encoding="utf-8")

    return repo, manifest_path


def test_collect_curriculum_files(tmp_path: Path):
    repo, _ = _setup_mock_repo(tmp_path)
    entries = collect_curriculum_files(repo)
    paths = [e["path"] for e in entries]

    assert "curriculum/l2-uk-en/curriculum.yaml" in paths
    assert "curriculum/l2-uk-en/module-mapping.json" in paths
    assert "curriculum/l2-uk-en/lesson-plans/a1/lesson-1.yaml" in paths
    assert "curriculum/l2-uk-en/a1/lesson-1/module.md" in paths
    assert "curriculum/l2-uk-en/a1/lesson-1/vocabulary.yaml" in paths
    assert "curriculum/l2-uk-en/a1/lesson-1/activities.yaml" in paths
    assert "curriculum/l2-uk-en/a1/lesson-1/resources.yaml" in paths
    assert "curriculum/l2-uk-en/b1/motion-base-review/module.md" in paths
    assert "site/src/content/docs/a1/lesson-1.mdx" in paths
    assert "site/src/content/readings/shevchenko-test.mdx" in paths

    # Excluded dirs must not be present
    assert not any("_archive" in p for p in paths)
    assert not any("/orchestration/" in p for p in paths)
    assert not any("/review/" in p for p in paths)


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
    payload = write_manifest(manifest_path, repo)
    assert manifest_path.exists()
    assert payload["total_files"] == 10

    res = verify_manifest(manifest_path, repo)
    assert res["valid"] is True
    assert res["total_files"] == 10
    assert res["expected_files"] == 10
    assert len(res["modified"]) == 0
    assert len(res["added"]) == 0
    assert len(res["deleted"]) == 0


def test_verify_manifest_detects_modification(tmp_path: Path):
    repo, manifest_path = _setup_mock_repo(tmp_path)
    write_manifest(manifest_path, repo)

    # Tamper with a reading
    doc = repo / "site" / "src" / "content" / "readings" / "shevchenko-test.mdx"
    doc.write_text("# Tampered reading\nMalicious content", encoding="utf-8")

    res = verify_manifest(manifest_path, repo)
    assert res["valid"] is False
    assert len(res["modified"]) == 1
    assert res["modified"][0]["path"] == "site/src/content/readings/shevchenko-test.mdx"


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

    # 1. Missing manifest and curriculum tree with allow_sparse
    res1 = verify_manifest(manifest_path, repo, allow_sparse=True)
    assert res1["valid"] is True
    assert res1.get("sparse_skipped") is True

    # 2. Manifest exists, but 0 live curriculum files present in sparse worktree
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({
            "schema_version": 1,
            "scope": "test",
            "root_tree_hash": "abc",
            "total_files": 1,
            "files": [{"path": "curriculum/l2-uk-en/curriculum.yaml", "sha256": "123"}],
        }),
        encoding="utf-8",
    )
    res2 = verify_manifest(manifest_path, repo, allow_sparse=True)
    assert res2["valid"] is True
    assert res2.get("sparse_skipped") is True


def test_verify_manifest_malformed_payload(tmp_path: Path):
    repo = tmp_path / "repo-malformed"
    repo.mkdir()
    manifest_path = repo / "curriculum_manifest.json"

    # Non-JSON content
    manifest_path.write_text("not json", encoding="utf-8")
    res = verify_manifest(manifest_path, repo)
    assert res["valid"] is False
    assert "Failed to parse manifest JSON" in res["error"]

    # Root is not dict
    manifest_path.write_text("[]", encoding="utf-8")
    res = verify_manifest(manifest_path, repo)
    assert res["valid"] is False
    assert "root must be a JSON object" in res["error"]

    # files is not list
    manifest_path.write_text('{"files": "invalid"}', encoding="utf-8")
    res = verify_manifest(manifest_path, repo)
    assert res["valid"] is False
    assert "'files' field must be a list" in res["error"]

    # Entry missing 'path'
    manifest_path.write_text('{"files": [{"sha256": "abc"}]}', encoding="utf-8")
    res = verify_manifest(manifest_path, repo)
    assert res["valid"] is False
    assert "missing required 'path' or 'sha256' field" in res["error"]


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

    # Tamper and check non-JSON error output via CLI
    tampered_file = repo / "curriculum" / "l2-uk-en" / "a1" / "lesson-1" / "vocabulary.yaml"
    tampered_file.write_text("tampered: true\n", encoding="utf-8")

    exit_tampered = main(["--check", "--manifest-path", str(manifest_path), "--repo-root", str(repo)])
    assert exit_tampered == 1
