"""Deferred historical generators refuse before touching managed A or K files."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.projects.open_model_data import (
    v4_production_shards_assembly as production,
)
from scripts.projects.open_model_data import (
    v5_mine_kyivan_rus_epigraphy as kyivan,
)
from scripts.projects.open_model_data import (
    v5_mine_middle_ukrainian as middle,
)
from scripts.projects.open_model_data.p3b_refusal import HistoricalProducerDeferredError
from scripts.storage.paths import ArtifactSet


def _tree_state(root: Path) -> dict[str, tuple[bytes | None, int, int, int]]:
    """Include directory membership, bytes, mode, and access/modify timestamps."""
    state = {}
    for path in sorted(root.rglob("*")):
        content = path.read_bytes() if path.is_file() else None
        stat = path.stat()
        state[path.relative_to(root).as_posix()] = (
            content,
            stat.st_mode,
            stat.st_atime_ns,
            stat.st_mtime_ns,
        )
    return state


def _guard_mutations(monkeypatch: pytest.MonkeyPatch, attempts: list[str]) -> None:
    """Trip on every mutation primitive used by these three producers."""

    def refuse(name: str):
        def guarded(*args: object, **kwargs: object) -> None:
            attempts.append(name)
            raise AssertionError(f"{name} attempted before P3b refusal")

        return guarded

    for name in ("mkdir", "write_text", "write_bytes", "unlink", "rename", "replace"):
        monkeypatch.setattr(Path, name, refuse(name))

    original_open = Path.open

    def guarded_open(path: Path, mode: str = "r", *args: object, **kwargs: object):
        if any(flag in mode for flag in "wax+"):
            return refuse("open for write")(path, mode, *args, **kwargs)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)


@pytest.fixture
def managed_bases(tmp_path: Path) -> tuple[Path, Path]:
    data = tmp_path / "data" / "projects" / "open_model_data"
    registry = tmp_path / "registry" / "projects" / "open_model_data"
    for base in (data, registry):
        (base / "archive" / "existing").mkdir(parents=True)
        (base / "archive" / "existing" / "receipt.json").write_bytes(b"preserve me\n")
    for release in (
        "quarantined_historical/uldr_v04a_kyivan_rus",
        "quarantined_historical/uldr_v04b_middle_ukrainian",
        "uldr_v1_production",
    ):
        (data / "archive" / release / "sft").mkdir(parents=True)
        (data / "archive" / release / "sft" / "sft_shard_001_of_030.jsonl").write_bytes(b'{"payload":1}\n')
        (registry / "archive" / release).mkdir(parents=True)
        (registry / "archive" / release / "release_receipt.json").write_bytes(b'{"receipt":1}\n')
        (registry / "archive" / release / "release_receipt.json.sha256").write_bytes(b"existing hash\n")
    return data, registry


@pytest.mark.parametrize("module", [kyivan, middle])
@pytest.mark.parametrize("explicit", [False, True])
def test_historical_cli_refuses_before_mutation(
    monkeypatch: pytest.MonkeyPatch,
    managed_bases: tuple[Path, Path],
    module: object,
    explicit: bool,
) -> None:
    data, registry = managed_bases
    source = data.parent.parent.parent / "sources.db"
    with sqlite3.connect(source) as conn:
        conn.execute(
            "CREATE TABLE historical_source_records (id INTEGER, source_record_id TEXT, title TEXT, "
            "original_transcription TEXT, interpretative_edition TEXT, source_language_label TEXT, "
            "min_year INTEGER, max_year INTEGER, commentary_ukr TEXT, metadata_json TEXT)"
        )
        conn.execute(
            "CREATE TABLE literary_texts (id INTEGER, chunk_id TEXT, work_id TEXT, work TEXT, "
            "author TEXT, year INTEGER, genre TEXT, text TEXT, char_count INTEGER, "
            "language_period TEXT, source_file TEXT)"
        )
    vesum = source.with_name("vesum.db")
    with sqlite3.connect(vesum):
        pass
    output = data / "archive" / "new_release"
    monkeypatch.setattr(module, "DEFAULT_RELEASE_DIR", output)
    argv = ["historical", "--sources-db", str(source), "--vesum-db", str(vesum)]
    if explicit:
        argv.extend(["--output-dir", str(output)])
    monkeypatch.setattr(sys, "argv", argv)
    before = (_tree_state(data), _tree_state(registry))
    attempts: list[str] = []
    with monkeypatch.context() as guarded:
        _guard_mutations(guarded, attempts)
        with pytest.raises(HistoricalProducerDeferredError, match="P3b deferred historical regeneration"):
            module.main()
    assert attempts == []
    assert (_tree_state(data), _tree_state(registry)) == before
    assert not output.exists()


@pytest.mark.parametrize("explicit", [False, True])
def test_production_cli_refuses_before_mutation(
    monkeypatch: pytest.MonkeyPatch, managed_bases: tuple[Path, Path], explicit: bool
) -> None:
    data, registry = managed_bases
    output = data / "staging" / "production_assembly"
    monkeypatch.setattr(production, "DEFAULT_OUTPUT_DIR", output)
    argv = ["production"]
    if explicit:
        argv.extend(["--output-dir", str(output)])
    monkeypatch.setattr(sys, "argv", argv)
    before = (_tree_state(data), _tree_state(registry))
    attempts: list[str] = []
    with monkeypatch.context() as guarded:
        _guard_mutations(guarded, attempts)
        with pytest.raises(HistoricalProducerDeferredError, match="P3b deferred historical regeneration"):
            production.main()
    assert attempts == []
    assert (_tree_state(data), _tree_state(registry)) == before
    assert not output.exists()


def test_imported_production_writers_refuse_before_mutation(
    monkeypatch: pytest.MonkeyPatch, managed_bases: tuple[Path, Path]
) -> None:
    data, registry = managed_bases
    output = data / "staging" / "production_assembly"
    before = (_tree_state(data), _tree_state(registry))
    attempts: list[str] = []
    with monkeypatch.context() as guarded:
        _guard_mutations(guarded, attempts)
        with pytest.raises(HistoricalProducerDeferredError, match="P3b deferred historical regeneration"):
            production.assemble_production_shards(output_dir=output)
        with pytest.raises(HistoricalProducerDeferredError, match="P3b deferred historical regeneration"):
            production.assemble_production_shards()
        with pytest.raises(HistoricalProducerDeferredError, match="P3b deferred historical regeneration"):
            production.write_jsonl(output / "sft" / "sft_shard_001_of_012.jsonl", [{"valid": True}])
    assert attempts == []
    assert (_tree_state(data), _tree_state(registry)) == before
    assert not output.exists()


def test_archive_generation_remains_prohibited() -> None:
    with pytest.raises(ValueError, match="Prohibited assembly output generation on archived/quarantined path"):
        production.assemble_production_shards(output_dir=production.HISTORICAL_ARCHIVE_DIR)


@pytest.mark.parametrize("script", [production, kyivan, middle])
def test_actual_cli_refusal_keeps_managed_bases_unchanged(managed_bases: tuple[Path, Path], script: object) -> None:
    data, registry = managed_bases
    output = data / "new_release"
    source = data.parent.parent.parent / "sources.db"
    vesum = source.with_name("vesum.db")
    with sqlite3.connect(source), sqlite3.connect(vesum):
        pass
    before = (_tree_state(data), _tree_state(registry))
    result = subprocess.run(
        [
            sys.executable,
            str(Path(script.__file__)),
            "--output-dir",
            str(output),
            "--sources-db",
            str(source),
            "--vesum-db",
            str(vesum),
        ],
        cwd=Path(__file__).resolve().parents[3],
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode != 0
    assert "P3b deferred historical regeneration" in result.stderr
    assert (_tree_state(data), _tree_state(registry)) == before
    assert not output.exists()


def test_verify_reader_uses_committed_snapshot_instead_of_reopening_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(production, "REPO_ROOT", tmp_path)
    path = tmp_path / "data" / "projects" / "open_model_data" / "archive" / "uldr_v1_production" / "sft" / "one.jsonl"
    rel = path.relative_to(tmp_path / "data").as_posix()
    calls: list[str] = []

    def snapshot(group: str, *, repo: Path) -> ArtifactSet:
        assert repo == tmp_path
        calls.append(group)
        return ArtifactSet({}, {rel: b'{"verified":true}\n'}, {})

    monkeypatch.setattr(production, "artifact_set", snapshot)
    snapshots: dict[str, ArtifactSet] = {}
    assert production._verified_artifact_bytes(path, "open_model_archive_payload", snapshots) == b'{"verified":true}\n'
    assert production._verified_artifact_bytes(path, "open_model_archive_payload", snapshots) == b'{"verified":true}\n'
    assert calls == ["open_model_archive_payload"]
    assert not path.exists()


def test_verify_reader_missing_group_has_hydrate_guidance(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(production, "REPO_ROOT", tmp_path)
    path = tmp_path / "data" / "projects" / "open_model_data" / "archive" / "missing.jsonl"

    def missing(group: str, *, repo: Path) -> ArtifactSet:
        raise FileNotFoundError(group)

    monkeypatch.setattr(production, "artifact_set", missing)
    with pytest.raises(RuntimeError, match="artifacts hydrate --group open_model_archive_payload"):
        production._verified_artifact_bytes(path, "open_model_archive_payload", {})


def test_verify_reader_explicit_missing_member_has_hydrate_guidance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(production, "REPO_ROOT", tmp_path)
    path = tmp_path / "data" / "projects" / "open_model_data" / "archive" / "missing.jsonl"
    snapshots = {"open_model_archive_payload": ArtifactSet({}, {}, {})}
    with pytest.raises(RuntimeError, match="artifacts hydrate --group open_model_archive_payload"):
        production._verified_artifact_bytes(path, "open_model_archive_payload", snapshots)


def test_middle_replay_requires_verified_member(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(middle, "REPO_ROOT", tmp_path)

    def missing(group: str, *, repo: Path) -> ArtifactSet:
        raise FileNotFoundError(group)

    monkeypatch.setattr(middle, "artifact_set", missing)
    with pytest.raises(RuntimeError, match="artifacts hydrate --group open_model_release_payload"):
        middle.load_replay_buffer(tmp_path / "vesum.db", quota=2)
