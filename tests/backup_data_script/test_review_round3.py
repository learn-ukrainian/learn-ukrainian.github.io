"""Round-3 review fixes: path-inventory argv, mirror databases, file-list cleanup."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path

from scripts.lexicon.runner.durable_mirror import require_durable
from tests.backup_data_script._support import (
    SCRIPT,
    _file_sha256,
    _log,
    _logical_sha256,
    _make_database,
    _run,
    _use_local_restic,
    _write_executable,
)


def _receipt_function(source: str) -> str:
    return source.split("write_backup_receipt()", 1)[1].split("\nprepare_staging_tree()", 1)[0]


def _flush_function(source: str) -> str:
    return source.split("flush_database_batch()", 1)[1].split("\nrun_linux_backup()", 1)[0]


def test_count_scaled_jq_inventories_are_not_argv() -> None:
    """Pin: path, exclusion, archive, and database inventories are files, not argv."""
    source = SCRIPT.read_text(encoding="utf-8")
    receipt = _receipt_function(source)
    flush = _flush_function(source)
    for flag in (
        "--argjson paths",
        "--argjson exclusions",
        "--argjson archives",
        "--argjson current",
        "--args",
    ):
        assert flag not in receipt, flag
    for flag in (
        "--slurpfile paths",
        "--slurpfile exclusions",
        "--slurpfile archives",
        "--slurpfile database_inventory",
    ):
        assert flag in receipt, flag
    assert "--slurpfile previous" in flush
    assert "LINUX_DB_SNAPSHOTS" not in source
    assert "printf '%s\\n' \"$LINUX_DB_SNAPSHOTS\"" not in source


def _install_jq_argv_probe(environment: dict[str, str]) -> Path:
    real_jq = shutil.which("jq", path=os.environ["PATH"])
    assert real_jq
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    log = fake_bin.parent / "jq-argv.log"
    log.write_text("", encoding="utf-8")
    environment["JQ_ARGV_LOG"] = str(log)
    environment["REAL_JQ"] = real_jq
    _write_executable(
        fake_bin / "jq",
        """#!/bin/bash
set -eu
# --arg/--argjson take the name first and the value second, so inspect every
# argument. An inventory is a JSON value, not the flag that precedes it.
for argument in "$@"; do
  if ((${#argument} > 4096)); then
    printf 'oversized-arg bytes=%s\\n' "${#argument}" >> "$JQ_ARGV_LOG"
  fi
  if [[ "$argument" == *'"path":'* && "$argument" == *'"files":'* ]]; then
    printf 'path-inventory-on-argv\\n' >> "$JQ_ARGV_LOG"
  fi
  if [[ "$argument" == *'"snapshot_id":'* ]]; then
    printf 'database-inventory-on-argv\\n' >> "$JQ_ARGV_LOG"
  fi
done
exec "$REAL_JQ" "$@"
""",
    )
    return log


def _write_task_records(project: Path, count: int, *, stem_length: int) -> list[str]:
    tasks = project / "batch_state" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    stem = "r" * stem_length
    relatives: list[str] = []
    for index in range(count):
        relative = f"batch_state/tasks/{stem}-{index:04d}.json"
        (project / relative).write_text("{}\n", encoding="utf-8")
        relatives.append(relative)
    return relatives


def _run_backup(environment: dict[str, str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(SCRIPT), "backup", "--execute"],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=timeout,
    )


def _assert_task_inventory_completed(
    environment: dict[str, str],
    relatives: list[str],
    argv_log: Path,
) -> None:
    result = _run_backup(environment)
    assert result.returncode == 0, result.stderr
    assert "arg=<lu-part-complete>" in _log(environment)
    receipt = json.loads((Path(environment["FAKE_SNAPSHOT_DIR"]) / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    recorded = {entry["path"] for entry in receipt["paths"]}
    assert set(relatives) <= recorded
    assert len(json.dumps(receipt["paths"])) > 131072
    assert argv_log.read_text(encoding="utf-8") == ""


def test_twelve_hundred_task_records_publish_a_completion_marker(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    relatives = _write_task_records(source.parent, 1200, stem_length=64)
    argv_log = _install_jq_argv_probe(environment)

    _assert_task_inventory_completed(environment, relatives, argv_log)


def test_long_task_paths_publish_a_completion_marker(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, _staging, _legacy = backup_environment
    directory = source.parent / "batch_state" / "tasks"
    for _index in range(8):
        directory = directory / ("p" * 180)
    directory.mkdir(parents=True)
    relatives = []
    for index in range(100):
        path = directory / f"{index:04d}.json"
        path.write_text("{}\n", encoding="utf-8")
        relatives.append(path.relative_to(source.parent).as_posix())
    assert max(len(relative) for relative in relatives) > 1000
    argv_log = _install_jq_argv_probe(environment)

    _assert_task_inventory_completed(environment, relatives, argv_log)


def _sqlite_mirror(source: Path) -> tuple[Path, Path, bytes]:
    mirror = source / "lexicon" / "runner-mirror" / "run-20k"
    mirror.mkdir(parents=True)
    state = b"state\n"
    (mirror / "state.txt").write_bytes(state)
    database = _make_database(mirror / "ledger.sqlite", "mirror-row")
    database_bytes = database.read_bytes()
    files = [
        {"path": "state.txt", "bytes": len(state), "sha256": hashlib.sha256(state).hexdigest()},
        {
            "path": "ledger.sqlite",
            "bytes": len(database_bytes),
            "sha256": hashlib.sha256(database_bytes).hexdigest(),
        },
    ]
    (mirror / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "atlas-runner-mirror-manifest",
                "schema_version": 1,
                "generated_at": time.time(),
                "file_count": len(files),
                "total_bytes": sum(entry["bytes"] for entry in files),
                "files": files,
            }
        ),
        encoding="utf-8",
    )
    return mirror, database, state


def test_sqlite_runner_mirror_completes_and_restores_hash_matched(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    mirror, database, state = _sqlite_mirror(source)
    logical = _logical_sha256(database)

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    invocations = Path(environment["TEST_INVOCATION_LOG"]).read_text(encoding="utf-8")
    assert "backup lu-part-complete" in invocations
    require_durable(mirror)
    gate = json.loads((mirror.parent / "RESTIC-GATE-RECEIPT.json").read_text(encoding="utf-8"))
    assert gate["mirrors"]["run-20k"]["file_count"] == 2
    target = tmp_path / "restored"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
    assert restored.returncode == 0, restored.stderr
    mirror_copy = (target / "data").joinpath("lexicon", "runner-mirror", "run-20k")
    restored_state = mirror_copy / "state.txt"
    restored_database = mirror_copy / "ledger.sqlite"
    assert restored_state.read_bytes() == state
    assert _file_sha256(restored_state) == hashlib.sha256(state).hexdigest()
    assert _logical_sha256(restored_database) == logical
    receipt = json.loads((target / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    database_relative = "/".join(("data", "lexicon/runner-mirror/run-20k/ledger.sqlite"))
    assert database_relative in {entry["path"] for entry in receipt["linux_run"]["databases"]}


def test_runner_mirror_still_fails_closed_on_extra_missing_or_changed_files(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    case: str,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    mirror, _database, _state = _sqlite_mirror(source)
    state_path = mirror / "state.txt"
    if case == "extra":
        command = f"printf 'extra\\n' > {shlex.quote(str(mirror / 'extra.txt'))}"
    elif case == "missing":
        command = f"rm -f -- {shlex.quote(str(state_path))}"
    else:
        command = f"printf 'changed\\n' >> {shlex.quote(str(state_path))}"
    environment["TEST_MIRROR_MUTATION_AT"] = "backup lu-part-receipt"
    environment["TEST_MIRROR_MUTATION_CMD"] = command

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "refusing to write a durability receipt" in result.stderr
    invocations = Path(environment["TEST_INVOCATION_LOG"]).read_text(encoding="utf-8")
    assert "backup lu-part-complete" not in invocations
    assert not (mirror.parent / "RESTIC-GATE-RECEIPT.json").exists()


def pytest_generate_tests(metafunc) -> None:  # type: ignore[no-untyped-def]
    if "case" in metafunc.fixturenames:
        metafunc.parametrize("case", ["extra", "missing", "changed"])


def _file_roots_including_newline_glob(project: Path) -> None:
    tasks = project / "batch_state" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    (tasks / "note\n*.json").write_text("weird\n", encoding="utf-8")
    for index in range(50):
        (tasks / f"record-{index:02d}.json").write_text("{}\n", encoding="utf-8")


def _leftover_file_lists(staging: Path) -> list[str]:
    return sorted(
        path.relative_to(staging).as_posix()
        for path in staging.rglob("*")
        if path.name.startswith("learn-ukrainian-backup-files.")
    )


def _files_from_entries(environment: dict[str, str]) -> list[bytes]:
    entries = []
    for line in _log(environment).splitlines():
        if line.startswith("files_from="):
            entries.append(base64.b64decode(line.removeprefix("files_from=")))
    return entries


def test_many_file_roots_leave_no_file_list_after_success(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    _file_roots_including_newline_glob(source.parent)

    result = _run(environment, "backup", "--execute")

    assert result.returncode == 0, result.stderr
    assert "arg=<lu-part-complete>" in _log(environment)
    entries = _files_from_entries(environment)
    assert len(entries) > 50
    assert any(b"\n" in entry and b"*" in entry for entry in entries)
    assert _leftover_file_lists(staging) == []
    assert list(staging.iterdir()) == []


def test_many_file_roots_leave_no_file_list_after_failure(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
) -> None:
    environment, source, staging, _legacy = backup_environment
    _file_roots_including_newline_glob(source.parent)
    environment["FAKE_FILE_PHASE_EXIT"] = "1"

    result = _run(environment, "backup", "--execute")

    assert result.returncode != 0
    assert "arg=<lu-part-complete>" not in _log(environment)
    assert _leftover_file_lists(staging) == []
    assert list(staging.iterdir()) == []
