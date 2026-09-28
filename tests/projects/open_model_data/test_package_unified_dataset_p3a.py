"""External package boundary and committed release-snapshot checks."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.projects.open_model_data import package_unified_dataset as package
from scripts.storage.paths import MissingArtifactError


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


@pytest.mark.parametrize("state", ["missing", "corrupt"])
def test_managed_snapshot_failure_precedes_output_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    member = package.MANAGED_RELEASE_DIR / "uldr_v03_dialect/sft_dialect_protection_500.jsonl"
    if state == "missing":
        member.unlink()
    else:
        member.write_text("changed")
    output = tmp_path / "package"
    with pytest.raises(MissingArtifactError, match="hydrate --group open_model_release_payload"):
        package.build_unified_dataset(package.MANAGED_RELEASE_DIR, output)
    assert not output.exists()


@pytest.mark.parametrize(
    "absent",
    [
        "uldr_v03_dialect/dialect_corpus_expanded_1500.jsonl",
        "uldr_v05_grammar_valency/brown_uk_negative_control_eval.jsonl",
    ],
)
def test_absent_required_committed_selector_fails_before_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, absent: str
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    manifest_path = repo / "registry/artifacts" / f"{package.RELEASE_GROUP}.manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["entries"] = [entry for entry in manifest["entries"] if not entry["path"].endswith(absent)]
    manifest["set_descriptor"]["members"] = sorted(entry["path"][5:] for entry in manifest["entries"])
    manifest_path.write_text(json.dumps(manifest))
    output = tmp_path / "package"
    with pytest.raises(MissingArtifactError, match="hydrate --group open_model_release_payload") as exc:
        package.build_unified_dataset(package.MANAGED_RELEASE_DIR, output)
    assert absent in str(exc.value)
    assert not output.exists()


def test_partial_optional_general_assistant_release_fails_when_included(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    source = package.MANAGED_RELEASE_DIR / "uldr_v06_general_assistant/sft/sft_shard_001_of_001.jsonl"
    source.parent.mkdir(parents=True)
    content = b'{"id":"optional"}\n'
    source.write_bytes(content)
    manifest_path = repo / "registry/artifacts" / f"{package.RELEASE_GROUP}.manifest.json"
    manifest = json.loads(manifest_path.read_text())
    sha = hashlib.sha256(content).hexdigest()
    manifest["entries"].append(
        {"path": source.relative_to(repo).as_posix(), "sha256": sha, "store": sha, "size": len(content)}
    )
    manifest["set_descriptor"]["members"] = sorted(entry["path"][5:] for entry in manifest["entries"])
    manifest_path.write_text(json.dumps(manifest))
    output = tmp_path / "package"
    with pytest.raises(MissingArtifactError, match="uldr_v06_general_assistant/eval"):
        package.build_unified_dataset(package.MANAGED_RELEASE_DIR, output)
    assert not output.exists()
    result = package.build_unified_dataset(package.MANAGED_RELEASE_DIR, output, include_general_assistant=False)
    assert result["totals"]["sft_instructions"] == 2


def test_managed_reader_uses_committed_members_and_exports_external(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    stray = package.MANAGED_RELEASE_DIR / "uldr_v03_dialect/extra.jsonl"
    stray.write_text('{"id":"stray"}\n')
    output = tmp_path / "package"
    manifest = package.build_unified_dataset(package.MANAGED_RELEASE_DIR, output)
    assert manifest["totals"] == {"sft_instructions": 2, "dpo_pairs": 0, "eval_cases": 2}
    assert json.loads((output / "train.jsonl").read_text().splitlines()[0])["id"] == "one"
    assert (output / "dpo.jsonl").read_bytes() == b""
    assert len((output / "eval.jsonl").read_text().splitlines()) == 2
    assert (output / "README.md").is_file()
    assert (output / "manifest.json.sha256").read_text().startswith(package.sha256_file(output / "manifest.json"))
    assert stray.is_file()
    assert (repo / "data/projects/open_model_data/export").exists() is False


def test_external_fixture_reader_still_builds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _repo(tmp_path, monkeypatch)
    release = tmp_path / "fixture-release"
    source = release / "uldr_v03_dialect"
    source.mkdir(parents=True)
    (source / "sft_dialect_protection_500.jsonl").write_text('{"id":"fixture","query":"Q"}\n')
    output = tmp_path / "fixture-package"
    manifest = package.build_unified_dataset(release, output)
    assert manifest["totals"]["sft_instructions"] == 1
    assert json.loads((output / "train.jsonl").read_text())["id"] == "fixture"
