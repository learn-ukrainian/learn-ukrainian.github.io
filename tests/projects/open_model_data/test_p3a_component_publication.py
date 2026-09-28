"""Managed component producers publish whole A/K sets in isolated repositories."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.projects.open_model_data import build_decolonization_cases as decol
from scripts.projects.open_model_data import build_grammar_component_8342 as grammar
from scripts.storage import artifacts, paths

GRAMMAR = "projects/open_model_data/components/grammar"
DECOL = "projects/open_model_data/components/decolonization"
GROUP = "open_model_component_payload"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, timeout=30)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "fixture"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    rows = []
    for relative in (
        f"{GRAMMAR}/grammar_train_shard_01_of_02.jsonl",
        f"{GRAMMAR}/grammar_train_shard_02_of_02.jsonl",
        f"{GRAMMAR}/candidate_exclusion_accounting.json",
        f"{DECOL}/decolonization_train.jsonl",
        f"{DECOL}/decolonization_eval.jsonl",
    ):
        path = repo / "data" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"old\n")
        rows.append((f"data/{relative}", "100644", "", 4, "A", GROUP, "fixture", "test"))
    for relative in (GRAMMAR, DECOL):
        for name in ("cases.json", "manifest.json"):
            path = repo / "registry" / relative / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"{}\n")
    table = repo / "registry/artifacts/classification-v1.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    with table.open("w", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(("path", "mode", "blob", "size", "class", "group", "reason", "judgment"))
        writer.writerows(rows)
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture K and A baseline")
    assert artifacts.manifest_build(repo, GROUP, "HEAD") == len(rows)
    manifest = paths.load_manifest(GROUP, repo)
    manifest["registration_patterns"] = [
        f"data/{GRAMMAR}/grammar_train_shard_*_of_*.jsonl",
        f"data/{GRAMMAR}/grammar_eval_shard_*_of_*.jsonl",
    ]
    artifacts._json_write(paths.manifest_path(GROUP, repo), manifest)
    _git(repo, "add", "registry/artifacts")
    _git(repo, "commit", "-qm", "fixture manifest")
    return repo


def _grammar_stage(stage: Path, *shards: str) -> None:
    stage.mkdir(parents=True, exist_ok=True)
    payloads = {name: (f'{{"shard":"{name}"}}\n').encode() for name in shards}
    payloads["candidate_exclusion_accounting.json"] = b'{"count":1}\n'
    for name, data in payloads.items():
        (stage / name).write_bytes(data)
    (stage / "cases.json").write_bytes(b"[]\n")
    (stage / "manifest.json").write_text(
        json.dumps({"payload_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}})
        + "\n"
    )


def test_grammar_callable_shrinks_and_reactivates_retired_shard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(grammar, "PROJECT_ROOT", repo)

    def build(*args: object) -> dict:
        _grammar_stage(args[-1], "grammar_train_shard_01_of_02.jsonl")
        return {"dataset_name": "grammar_v1"}

    monkeypatch.setattr(grammar, "_build_grammar_dataset_direct", build)
    assert grammar.build_grammar_dataset(output_dir=repo / "data" / GRAMMAR)["dataset_name"] == "grammar_v1"
    retired = f"data/{GRAMMAR}/grammar_train_shard_02_of_02.jsonl"
    assert not (repo / retired).exists()
    assert any(entry["path"] == retired for entry in paths.load_manifest(GROUP, repo)["retired"])
    _git(repo, "add", "registry")
    _git(repo, "commit", "-qm", "committed first publication K baseline")

    def regrow(*args: object) -> dict:
        _grammar_stage(args[-1], "grammar_train_shard_01_of_02.jsonl", "grammar_train_shard_02_of_02.jsonl")
        return {"dataset_name": "grammar_v1"}

    monkeypatch.setattr(grammar, "_build_grammar_dataset_direct", regrow)
    assert grammar.main(["--output-dir", str(repo / "registry" / GRAMMAR)]) == 0
    snapshot = paths.artifact_set(GROUP, repo=repo)
    assert f"{GRAMMAR}/grammar_train_shard_02_of_02.jsonl" in snapshot.artifacts
    assert snapshot.companions[f"registry/{GRAMMAR}/manifest.json"]


def test_grammar_invalid_stage_never_mutates_managed_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(grammar, "PROJECT_ROOT", repo)
    before = (repo / "data" / GRAMMAR / "grammar_train_shard_01_of_02.jsonl").read_bytes()

    def invalid(*args: object) -> dict:
        _grammar_stage(args[-1], "grammar_train_shard_01_of_02.jsonl")
        (args[-1] / "manifest.json").write_bytes(b'{"payload_sha256":{}}')
        return {}

    monkeypatch.setattr(grammar, "_build_grammar_dataset_direct", invalid)
    with pytest.raises(ValueError, match="payload hashes disagree"):
        grammar.build_grammar_dataset(output_dir=repo / "data" / GRAMMAR)
    assert (repo / "data" / GRAMMAR / "grammar_train_shard_01_of_02.jsonl").read_bytes() == before


def test_grammar_corrupt_group_member_refuses_before_install(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(grammar, "PROJECT_ROOT", repo)
    corrupt = repo / "data" / DECOL / "decolonization_eval.jsonl"
    corrupt.write_bytes(b"corrupt\n")
    before = (repo / "data" / GRAMMAR / "grammar_train_shard_01_of_02.jsonl").read_bytes()

    def build(*args: object) -> dict:
        _grammar_stage(args[-1], "grammar_train_shard_01_of_02.jsonl")
        return {}

    monkeypatch.setattr(grammar, "_build_grammar_dataset_direct", build)
    with pytest.raises(paths.MissingArtifactError, match="hydrate --group open_model_component_payload"):
        grammar.build_grammar_dataset(output_dir=repo / "data" / GRAMMAR)
    assert (repo / "data" / GRAMMAR / "grammar_train_shard_01_of_02.jsonl").read_bytes() == before


def test_decolonization_cli_build_and_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(decol, "REPO_ROOT", repo)
    monkeypatch.setattr(decol, "build_all_cases", lambda: [object()])
    monkeypatch.setattr(
        decol, "generate_dataset_records", lambda cases: ([{"is_erroneous": True}], [{"is_erroneous": False}])
    )
    monkeypatch.setattr(decol, "asdict", lambda case: {"case_id": "fixture"})
    assert decol.main(["--check", "--output-dir", str(repo / "data" / DECOL)]) == 0
    assert (repo / "data" / DECOL / "decolonization_train.jsonl").read_bytes() == b"old\n"
    assert decol.main(["--output-dir", str(repo / "data" / DECOL)]) == 0
    snapshot = paths.artifact_set(GROUP, repo=repo)
    manifest = json.loads(snapshot.companions[f"registry/{DECOL}/manifest.json"])
    assert (
        manifest["payload_sha256"]["decolonization_train.jsonl"]
        == hashlib.sha256(snapshot.artifacts[f"{DECOL}/decolonization_train.jsonl"]).hexdigest()
    )


def test_missing_brown_input_gives_hydrate_guidance(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="hydrate the required artifact group"):
        grammar.load_brown_uk_controls(tmp_path / "missing.jsonl")


def test_external_output_and_symlink_alias(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _repo(tmp_path)
    monkeypatch.setattr(decol, "REPO_ROOT", repo)
    monkeypatch.setattr(decol, "build_all_cases", lambda: [object()])
    monkeypatch.setattr(decol, "generate_dataset_records", lambda cases: ([{"is_erroneous": True}], []))
    monkeypatch.setattr(decol, "asdict", lambda case: {"case_id": "fixture"})
    export = tmp_path / "external-export"
    assert decol.main(["--output-dir", str(export)]) == 0
    assert (export / "decolonization_train.jsonl").is_file()
    alias = tmp_path / "managed-alias"
    alias.symlink_to(repo / "data" / DECOL, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        decol.main(["--output-dir", str(alias)])
