"""The nightly walks the allowlist and does not walk dropped trees."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

from tests.backup_data_script._allowlist import (
    expand_allowlist,
    is_sqlite_database,
    load_allowlist,
    parse_selection_manifest,
)
from tests.backup_data_script._support import (
    REPO_ROOT,
    SCRIPT,
    _fresh_runner_mirror,
    _logical_sha256,
    _make_database,
    _run,
    _use_local_restic,
)

RUNBOOK = REPO_ROOT / "docs" / "runbooks" / "data-backup.md"
SQLITE_HEADER = b"SQLite format 3\x00"


def _sample_hash(path: Path) -> str:
    if path.name.endswith((".db", ".sqlite", ".sqlite3")) and is_sqlite_database(path):
        return "sqlite:" + _logical_sha256(path)
    return "file:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _runbook_table(marker: str) -> list[list[str]]:
    rest = RUNBOOK.read_text(encoding="utf-8").split(marker, 1)[1]
    rows: list[list[str]] = []
    for line in rest.splitlines():
        if line.startswith("<!--") or line.startswith("#"):
            break
        if not line.startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"Path", "---"} or set(cells[0]) <= {"-", ":"}:
            continue
        rows.append(cells)
    return rows


def _seed_keep_samples(project: Path, source: Path) -> dict[str, str]:
    """One restored sample for every KEEP entry. The fixture already has the required roots."""
    samples: dict[str, str] = {}
    for entry in load_allowlist()["keep"]:
        if not isinstance(entry, dict):
            raise TypeError(entry)
        path = str(entry["path"])
        kind = str(entry["kind"])
        if path == ".claude/*-epic":
            sample = project / ".claude" / "atlas-epic" / "HANDOFF.md"
        elif path == ".agent":
            sample = project / ".agent" / "recovery-state.json"
        elif path == "batch_state/fleet-comms":
            sample = project / "batch_state" / "fleet-comms" / "state.txt"
        elif path == "data/lexicon/runner-mirror":
            sample = _fresh_runner_mirror(source) / "state.txt"
        elif kind == "glob_files" and path.endswith("/*.json"):
            sample = project.joinpath(*path.replace("*", "inventory").split("/"))
            sample.parent.mkdir(parents=True, exist_ok=True)
            sample.write_text("{}\n", encoding="utf-8")
        elif kind == "glob_files" and path == "data/wiki_*.db":
            sample = _make_database(project / "data" / "wiki_sample.db", "wiki")
        elif kind == "task_records":
            sample = project / "batch_state" / "tasks" / "job.json"
            sample.parent.mkdir(parents=True, exist_ok=True)
            sample.write_text('{"job": 1}\n', encoding="utf-8")
        elif kind == "file":
            sample = project / path
            if not (sample.is_file() and is_sqlite_database(sample)):
                if path.endswith((".db", ".sqlite", ".sqlite3")):
                    sample = _make_database(sample, path)
                else:
                    sample.parent.mkdir(parents=True, exist_ok=True)
                    sample.write_text(f"keep {path}\n", encoding="utf-8")
        elif kind == "tree":
            sample = project / path / "KEEP.txt"
            sample.parent.mkdir(parents=True, exist_ok=True)
            sample.write_text(f"keep {path}\n", encoding="utf-8")
        else:
            raise AssertionError(f"No sample for {path} ({kind})")
        samples[sample.relative_to(project).as_posix()] = _sample_hash(sample)
    return samples


def test_dropped_sqlite_trees_are_never_enumerated(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    preserved = project / "batch_state" / "preserved"
    codex_atlas = project / "batch_state" / "codex-atlas"
    for index in range(1000):
        preserved_path = preserved / f"bucket-{index // 100}" / f"{index}.sqlite"
        preserved_path.parent.mkdir(parents=True, exist_ok=True)
        preserved_path.write_bytes(SQLITE_HEADER)
        atlas_path = codex_atlas / f"{index}.db"
        atlas_path.parent.mkdir(parents=True, exist_ok=True)
        atlas_path.write_bytes(SQLITE_HEADER)
    assert len(list(preserved.rglob("*.sqlite"))) + len(list(codex_atlas.rglob("*.db"))) == 2000
    manifest_path = tmp_path / "selection.txt"
    environment["LU_BACKUP_SELECTION_MANIFEST"] = str(manifest_path)

    result = _run(environment, "backup")

    assert result.returncode == 0, result.stderr
    seen, staged, count = expand_allowlist(project)
    enumerated_count, manifest_seen, manifest_staged = parse_selection_manifest(manifest_path)
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert enumerated_count == count
    assert count < 50
    assert manifest_seen == seen
    assert manifest_staged == staged
    for relative in (
        "batch_state/preserved/bucket-0/0.sqlite",
        "batch_state/codex-atlas/0.db",
        "batch_state/preserved",
        "batch_state/codex-atlas",
    ):
        assert relative not in manifest_text
        assert relative not in manifest_seen
        assert relative not in manifest_staged


def test_every_keep_entry_restores_with_the_same_hash(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    project = source.parent
    samples = _seed_keep_samples(project, source)
    assert len(samples) == len(load_allowlist()["keep"])

    backed_up = subprocess.run(
        ["/bin/bash", str(SCRIPT), "backup", "--execute"],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=120,
    )
    assert backed_up.returncode == 0, backed_up.stderr
    target = tmp_path / "restored-allowlist"
    restored = subprocess.run(
        ["/bin/bash", str(SCRIPT), "restore", "latest", "--to", str(target), "--execute"],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=120,
    )

    assert restored.returncode == 0, restored.stderr
    for relative, expected in samples.items():
        assert _sample_hash(target / relative) == expected, relative


def test_ulif_raw_sqlite_uses_the_consistent_snapshot_path(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    database = _make_database(source / "lexicon" / "cache" / "ulif_raw.sqlite", "ulif")
    relative = "data/lexicon/cache/ulif_raw.sqlite"

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    log = Path(environment["FAKE_RESTIC_LOG"]).read_text(encoding="utf-8")
    assert f"Creating consistent SQLite snapshot: {relative}" in result.stdout
    assert f"db_file=<{relative}>" in log
    assert f"exclude=<{database}>" in log


def test_missing_required_path_aborts_and_missing_optional_path_does_not(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    optional = _run(environment, "backup")
    assert optional.returncode == 0, optional.stderr
    assert optional.stdout.count("==> Optional backup path is absent: data/movaua.db") == 1

    source.joinpath("sources.db").unlink()
    missing_database = _run(environment, "backup")
    assert missing_database.returncode != 0
    assert "ERROR: Required recovery path is missing: data/sources.db" in missing_database.stderr

    _make_database(source / "sources.db", "sources")
    shutil.rmtree(source.parent / "batch_state" / "fleet-comms")
    missing_comms = _run(environment, "backup")
    assert missing_comms.returncode != 0
    assert "ERROR: Required recovery path is missing: batch_state/fleet-comms" in missing_comms.stderr


def test_task_locks_and_snapshot_directories_are_not_staged(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    tasks = project / "batch_state" / "tasks"
    (tasks / "archive").mkdir(parents=True)
    (tasks / "job.json").write_text('{"job": 1}\n', encoding="utf-8")
    (tasks / "archive" / "note.txt").write_text("note\n", encoding="utf-8")
    (tasks / "job.lock").write_text("locked\n", encoding="utf-8")
    snapshot = tasks / "run.snapshots"
    snapshot.mkdir()
    (snapshot / "huge.sqlite").write_bytes(SQLITE_HEADER)
    manifest_path = tmp_path / "selection.txt"
    environment["LU_BACKUP_SELECTION_MANIFEST"] = str(manifest_path)

    result = _run(environment, "backup")

    assert result.returncode == 0, result.stderr
    _enumerated_count, seen, staged = parse_selection_manifest(manifest_path)
    assert "batch_state/tasks/job.json" in staged
    assert "batch_state/tasks/archive/note.txt" in staged
    assert "batch_state/tasks/job.lock" in seen
    assert "batch_state/tasks/job.lock" not in staged
    assert "batch_state/tasks/run.snapshots/huge.sqlite" not in seen
    assert "batch_state/tasks/run.snapshots/huge.sqlite" not in staged
    helper_seen, helper_staged, helper_count = expand_allowlist(project)
    manifest_count, manifest_seen, manifest_staged = parse_selection_manifest(manifest_path)
    assert manifest_count == helper_count
    assert manifest_seen == helper_seen
    assert manifest_staged == helper_staged


def test_runbook_tables_name_the_allowlist_paths() -> None:
    payload = load_allowlist()
    keep = payload["keep"]
    drop = payload["drop"]
    assert isinstance(keep, list)
    assert isinstance(drop, list)
    keep_rows = _runbook_table("<!-- backup-allowlist-keep -->")
    drop_rows = _runbook_table("<!-- backup-allowlist-drop -->")
    assert [row[0] for row in keep_rows] == [str(entry["path"]) for entry in keep]
    assert [row[1] == "yes" for row in keep_rows] == [bool(entry["required"]) for entry in keep]
    assert [row[0] for row in drop_rows] == [str(entry["path"]) for entry in drop]
