"""External package boundary and committed release-snapshot checks."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.projects.open_model_data import package_unified_dataset as package
from scripts.projects.open_model_data.paths import QuarantinedArtifactError


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "checkout"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True, timeout=30)
    monkeypatch.setattr(package, "REPO_ROOT", repo)
    monkeypatch.setattr(package, "MANAGED_RELEASE_DIR", repo / "data/projects/open_model_data/release")
    release = package.MANAGED_RELEASE_DIR
    sources = {
        "uldr_v03_dialect/sft_dialect_protection_500.jsonl": b'{"id":"one","query":"Q","final_response":"A"}\n',
        "uldr_v03_dialect/dialect_corpus_expanded_1500.jsonl": b'{"eval_id":"two","query":"Q"}\n',
        "uldr_v05_grammar_valency/sft/sft_shard_001_of_001.jsonl": b'{"id":"three","query":"Q"}\n',
        "uldr_v05_grammar_valency/brown_uk_negative_control_eval.jsonl": b'{"eval_id":"four","query":"Q"}\n',
    }
    entries = []
    for relative, content in sources.items():
        member = release / relative
        member.parent.mkdir(parents=True, exist_ok=True)
        member.write_bytes(content)
        sha = hashlib.sha256(content).hexdigest()
        entries.append({"path": member.relative_to(repo).as_posix(), "sha256": sha, "store": sha, "size": len(content)})
    manifest = {
        "schema": 1,
        "group": package.RELEASE_GROUP,
        "entries": entries,
        "set_descriptor": {
            "members": sorted(entry["path"][5:] for entry in entries),
            "companions": {},
        },
    }
    directory = repo / "registry/artifacts"
    directory.mkdir(parents=True)
    (directory / f"{package.RELEASE_GROUP}.manifest.json").write_text(json.dumps(manifest))
    return repo


@pytest.mark.parametrize("alias", [False, True])
def test_callable_rejects_checkout_and_alias_before_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alias: bool
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    destination = repo / "data/projects/open_model_data/export/uldr_v02"
    destination.mkdir(parents=True)
    existing = destination / "train.jsonl"
    existing.write_bytes(b"pre-existing export")
    before = existing.stat()
    if alias:
        link = tmp_path / "alias"
        link.symlink_to(repo, target_is_directory=True)
        destination = link / "data/projects/open_model_data/export/uldr_v02"
    with pytest.raises(ValueError, match="outside the checkout"):
        package.build_unified_dataset(package.MANAGED_RELEASE_DIR, destination)
    assert existing.read_bytes() == b"pre-existing export"
    assert existing.stat().st_mtime_ns == before.st_mtime_ns


def test_callable_rejects_artifact_store_alias_before_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _repo(tmp_path, monkeypatch)
    store = tmp_path / "managed-store"
    store.mkdir()
    monkeypatch.setenv("LU_ARTIFACT_STORE", str(store))
    alias = tmp_path / "store-alias"
    alias.symlink_to(store, target_is_directory=True)
    with pytest.raises(ValueError, match="managed artifact storage"):
        package.build_unified_dataset(package.MANAGED_RELEASE_DIR, alias / "export")
    assert list(store.iterdir()) == []


def test_external_directory_cannot_write_through_file_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _repo(tmp_path, monkeypatch)
    existing = repo / "data/projects/open_model_data/export/uldr_v02/train.jsonl"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(b"pre-existing export")
    output = tmp_path / "external"
    output.mkdir()
    (output / "train.jsonl").symlink_to(existing)
    with pytest.raises(ValueError, match="outside the checkout"):
        package.build_unified_dataset(package.MANAGED_RELEASE_DIR, output)
    assert existing.read_bytes() == b"pre-existing export"
    assert sorted(path.name for path in output.iterdir()) == ["train.jsonl"]


def test_cli_requires_external_output_and_rejects_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setattr(sys, "argv", ["package_unified_dataset.py"])
    with pytest.raises(SystemExit) as exc:
        package.main()
    assert exc.value.code == 2
    alias = tmp_path / "alias"
    alias.symlink_to(repo, target_is_directory=True)
    monkeypatch.setattr(sys, "argv", ["package_unified_dataset.py", "--output-dir", str(alias / "export")])
    with pytest.raises(ValueError, match="outside the checkout"):
        package.main()
    assert not (repo / "export").exists()


@pytest.mark.parametrize("source", ["managed", "external"])
def test_quarantined_release_inputs_refuse_before_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str
) -> None:
    """Every release set the packager reads is sealed (#9607), managed snapshot or external copy alike."""
    _repo(tmp_path, monkeypatch)
    release = package.MANAGED_RELEASE_DIR
    if source == "external":
        release = tmp_path / "fixture-release"
        (release / "uldr_v03_dialect").mkdir(parents=True)
        (release / "uldr_v03_dialect/sft_dialect_protection_500.jsonl").write_text('{"id":"fixture","query":"Q"}\n')
    output = tmp_path / "package"
    with pytest.raises(QuarantinedArtifactError, match="Refusing ULDR packaging"):
        package.build_unified_dataset(release, output)
    assert not output.exists()
