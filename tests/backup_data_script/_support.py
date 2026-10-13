from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import time
from pathlib import Path

import pytest

from tests._host_path_guard import FIXTURE_HOME

REPO_ROOT = Path(__file__).resolve().parents[2]


SCRIPT = REPO_ROOT / "scripts" / "backup-data.sh"


# Last base before database batching; its reader accepts receipt schemas 1 and 2 only.
PRE_BATCHING_BASE_SHA = "7e639123fc2d8270e8f9bf78ba1ae66f5bb18359"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o700)


def _run(
    environment: dict[str, str],
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    # Load-sensitive wall clock; the assertions never depend on time.
    return subprocess.run(
        ["/bin/bash", str(SCRIPT), *arguments],
        check=False,
        capture_output=True,
        env=environment,
        text=True,
        timeout=120,
    )


def _log(environment: dict[str, str]) -> str:
    path = Path(environment["FAKE_RESTIC_LOG"])
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _use_local_restic(
    environment: dict[str, str],
    tmp_path: Path,
) -> None:
    """Route the fake `restic` on PATH to a real local restic repository."""
    real_restic = shutil.which("restic", path=os.environ["PATH"])
    if real_restic is None:
        pytest.skip("restic unavailable")
    repository = tmp_path / "local-restic-repository"
    # Load-sensitive wall clock; the assertions never depend on time.
    subprocess.run(
        [real_restic, "-r", str(repository), "init"],
        env={**os.environ, "RESTIC_PASSWORD_FILE": environment["RESTIC_PASSWORD_FILE"]},
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    environment["TEST_LOCAL_RESTIC_REPOSITORY"] = str(repository)
    environment["TEST_REAL_RESTIC"] = real_restic
    environment["TEST_PEAK_LOG"] = str(tmp_path / "peak.log")
    environment["TEST_INVOCATION_LOG"] = str(tmp_path / "restic-invocations.log")
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(
        fake_bin / "restic",
        r"""#!/bin/bash
set -eu
args=()
while [[ "$#" -gt 0 ]]; do
  if [[ "$1" == "--option" && "${2:-}" == rclone.connections=* ]]; then
    shift 2
    continue
  fi
  args+=("$1")
  shift
done
if [[ "${args[0]:-}" == "backup" ]]; then
  for argument in "${args[@]}"; do
    if [[ "$argument" == "--stdin" || "$argument" == "lu-part-db" ]]; then
      count="$(find "$LU_BACKUP_TMPDIR" -type f \( -name '*.db' -o -name '*.sqlite*' \) | wc -l)"
      printf '%s\n' "$count" >> "$TEST_PEAK_LOG"
      break
    fi
  done
fi
part=""
for argument in "${args[@]}"; do
  [[ "$argument" != lu-part-* ]] || part="$argument"
done
if [[ "${args[0]:-}" == "check" ]]; then
  case "${TEST_FAIL_CHECK:-}" in
    always) exit 70 ;;
    after-marker) ! grep -qx 'backup lu-part-complete' "$TEST_INVOCATION_LOG" || exit 70 ;;
  esac
fi
if [[ "$part" == lu-part-db && -n "${TEST_MUTATE_FILE:-}" ]]; then
  # The file-phase snapshot is already written: the live copy now differs.
  printf 'changed during backup\n' >> "$TEST_MUTATE_FILE"
fi
# Fault hooks keyed by "<subcommand> <part>", for example "check " or
# "backup lu-part-complete".
point="${args[0]:-} $part"
hold() {
  touch "$TEST_HOLD_FILE"
  while [[ ! -e "$TEST_HOLD_FILE.release" ]]; do sleep 0.05; done
}
[[ "$point" != "${TEST_HOLD_BEFORE:-}" ]] || hold
if [[ "$point" == "${TEST_READONLY_SNAPSHOTS_AT:-}" ]]; then
  chmod a-w "$TEST_LOCAL_RESTIC_REPOSITORY/snapshots"
fi
printf '%s %s\n' "${args[0]:-}" "$part" >> "$TEST_INVOCATION_LOG"
export RESTIC_REPOSITORY="$TEST_LOCAL_RESTIC_REPOSITORY"
if [[ "$point" == "${TEST_CORRUPT_SUMMARY_AT:-}" ]]; then
  "$TEST_REAL_RESTIC" "${args[@]}" | sed -E 's/"snapshot_id":"[0-9a-f]{64}"/"snapshot_id":"not-a-snapshot-id"/'
  exit "${PIPESTATUS[0]}"
fi
if [[ "$point" == "${TEST_CORRUPT_PACKS_AFTER:-}" ]]; then
  packs="$TEST_LOCAL_RESTIC_REPOSITORY/data"
  before="$(find "$packs" -type f | LC_ALL=C sort)"
  status=0
  "$TEST_REAL_RESTIC" "${args[@]}" || status=$?
  comm -13 <(printf '%s\n' "$before") <(find "$packs" -type f | LC_ALL=C sort) |
    while IFS= read -r pack; do
      chmod u+w "$pack"
      printf 'corrupted' | dd of="$pack" bs=1 seek=40 conv=notrunc status=none
    done
  exit "$status"
fi
if [[ "$point" == "${TEST_HOLD_AFTER:-}" ]]; then
  status=0
  "$TEST_REAL_RESTIC" "${args[@]}" || status=$?
  hold
  exit "$status"
fi
exec "$TEST_REAL_RESTIC" "${args[@]}"
""",
    )


def _dangling_recovery_links(project: Path) -> dict[str, Path]:
    """Create dangling links in each allowlisted recovery root; return them by label."""
    nested = project / "batch_state" / "fleet-comms" / "session" / "pytest-RC"
    nested.mkdir(parents=True)
    dataset = project / "data" / "datasets"
    dataset.mkdir(parents=True)
    links = {
        "batch_state/fleet-comms": nested / "dispatch-storescurrent",
        ".agent": project / ".agent" / "stale-pointer",
        ".claude/atlas-epic": project / ".claude" / "atlas-epic" / "gone[1]*?.md",
        "data/datasets": dataset / "moved-dataset",
    }
    links["batch_state/fleet-comms"].symlink_to("../../../../../.worktrees/removed/stores")
    links[".agent"].symlink_to("missing-target")
    links[".claude/atlas-epic"].symlink_to("HANDOFF-old.md")
    links["data/datasets"].symlink_to("missing-target")
    return links


MANIFEST_ID = "0" * 64


BASE_ID = "b" * 64


ATLAS_ID = "a" * 64


OTHER_ID = "c" * 64


GIB = 1024**3


def _write_fake_run(environment: dict[str, str], schema_version: int = 2) -> Path:
    """Publish a Linux run (manifest, base, two databases) in the fake repository."""
    snapshot = Path(environment["FAKE_SNAPSHOT_DIR"])
    databases = {"data/atlas.db": ATLAS_ID, "data/other.db": OTHER_ID}
    for relative, snapshot_id in databases.items():
        database = snapshot / "by-id" / snapshot_id / relative
        database.parent.mkdir(parents=True)
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE recovery_probe(value TEXT)")
    (snapshot / "by-id" / BASE_ID / "data").mkdir(parents=True)
    (snapshot / "by-id" / BASE_ID / "data" / "notes.txt").write_text("base\n", encoding="utf-8")
    receipt = {
        "schema_version": schema_version,
        "linux_run": {
            "run_id": "run-1",
            "base_snapshot_id": BASE_ID,
            "databases": [
                {"path": path, "snapshot_id": snapshot_id, "mode": "600"} for path, snapshot_id in databases.items()
            ],
        },
    }
    (snapshot / "BACKUP-RECEIPT.json").write_text(json.dumps(receipt), encoding="utf-8")
    (snapshot / "by-id" / MANIFEST_ID).mkdir(parents=True)
    shutil.copy(snapshot / "BACKUP-RECEIPT.json", snapshot / "by-id" / MANIFEST_ID)
    return snapshot


def _fake_free_space(environment: dict[str, str], available_bytes: int) -> None:
    fake_bin = Path(environment["PATH"].split(":", maxsplit=1)[0])
    _write_executable(
        fake_bin / "df",
        "#!/bin/bash\n"
        "printf '%s\\n' 'Filesystem 1024-blocks Used Available Capacity Mounted on'\n"
        f"printf 'testfs 8388608 0 %s 0%% /scratch\\n' {available_bytes // 1024}\n",
    )


def _restore_ids(environment: dict[str, str]) -> list[str]:
    return [
        line.split("arg=<restore> arg=<", 1)[1].split(">", 1)[0]
        for line in _log(environment).splitlines()
        if "arg=<restore>" in line
    ]


def _snapshot(
    snapshot_id: str,
    run_id: str | None,
    parts: list[str],
    time: str,
) -> list[dict[str, object]]:
    tags = ["learn-ukrainian-data"]
    if run_id is not None:
        tags.append(f"lu-run-{run_id}")
    return [
        {
            "id": snapshot_id,
            "time": time,
            "hostname": "learn-ukrainian",
            "tags": [*tags, f"lu-part-{part}"],
            "paths": [f"{FIXTURE_HOME}/learn-ukrainian"],
        }
        for part in parts
    ]


def _run_snapshots(
    run_id: str,
    day: str,
    parts: list[str] | None = None,
    id_byte: str = "a",
) -> list[dict[str, object]]:
    parts = parts or ["base", "complete"]
    snapshots: list[dict[str, object]] = []
    for index, part in enumerate(parts):
        snapshot_id = f"{id_byte}{index:063x}"[-64:]
        snapshots.extend(_snapshot(snapshot_id, run_id, [part], f"{day}T03:30:0{index}Z"))
    return snapshots


def _write_snapshots(
    environment: dict[str, str],
    tmp_path: Path,
    snapshots: list[dict[str, object]] | str,
) -> None:
    fixture = tmp_path / "snapshots.json"
    if isinstance(snapshots, str):
        fixture.write_text(snapshots, encoding="utf-8")
    else:
        fixture.write_text(json.dumps(snapshots), encoding="utf-8")
    environment["FAKE_SNAPSHOTS_JSON"] = str(fixture)


def _forget_ids(environment: dict[str, str]) -> list[str]:
    ids: list[str] = []
    for line in _log(environment).splitlines():
        if "arg=<forget>" not in line:
            continue
        ids.extend(argument[5:-1] for argument in line.split(" ") if re.fullmatch(r"arg=<[0-9a-f]{64}>", argument))
    return ids


def _make_database(path: Path, value: str = "row") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE IF NOT EXISTS recovery_probe (value TEXT NOT NULL)")
        connection.execute("INSERT INTO recovery_probe VALUES (?)", (value,))
        connection.commit()
    finally:
        connection.close()
    return path


def _base_backup_lines(log: str) -> list[str]:
    return [line for line in log.splitlines() if "arg=<backup>" in line and "arg=<lu-part-base>" in line]


def _uploaded_databases(log: str) -> set[str]:
    return set(re.findall(r"db_file=<([^>]*\.(?:db|sqlite3?))>", log))


def _write_archive(project: Path, name: str, databases: list[Path], *, archive_bytes: int | None = None) -> Path:
    archive_dir = project / "batch_state" / "branch-archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive = archive_dir / name
    archive.write_bytes(b"\x28\xb5\x2f\xfd fixture archive bytes")
    lines = [
        "# lu-backup-db-archive v1",
        f"# archive_bytes: {archive.stat().st_size if archive_bytes is None else archive_bytes}",
        f"# files: {len(databases)}",
    ]
    for database in databases:
        stat = database.stat()
        lines.append(f"{stat.st_size}\t{int(stat.st_mtime)}\t{database.relative_to(project)}")
    (archive_dir / f"{name}.manifest").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return archive


def _logical_sha256(database: Path) -> str:
    """Hash a database's logical content (schema and rows), independent of page layout."""
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        return hashlib.sha256("\n".join(connection.iterdump()).encode()).hexdigest()
    finally:
        connection.close()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _backup_invocations(environment: dict[str, str]) -> list[str]:
    log = Path(environment["TEST_INVOCATION_LOG"]).read_text(encoding="utf-8")
    return [line.strip() for line in log.splitlines() if line.startswith("backup ")]


def _many_database_fixture(tmp_path: Path, fixture_runs: int = 30) -> tuple[dict[str, str], dict[str, str]]:
    """Representative recovery tree: many small fixture databases plus live ones."""
    databases = [tmp_path / "data" / "datasets" / "corpus.db", tmp_path / "data" / "atlas.db"]
    databases += [
        tmp_path / "batch_state" / "open-model-data" / f"run-{index:02d}" / "corpus.db" for index in range(fixture_runs)
    ]
    databases += [
        tmp_path / ".agent" / "session-streams" / "v1" / "session-streams.sqlite3",
        tmp_path / ".claude" / "atlas-epic" / "state.db",
    ]
    for index, database in enumerate(databases):
        _make_database(database, f"row-{index}")
    with sqlite3.connect(tmp_path / "data" / "atlas.db") as connection:
        connection.executemany(
            "INSERT INTO recovery_probe VALUES (?)", ((f"bulk-{index:06d}" * 8,) for index in range(5000))
        )
    (tmp_path / "data" / "atlas.db").chmod(0o600)
    sources = tmp_path / "data" / "sources.db"
    databases.append(sources)
    _make_database(tmp_path / "batch_state" / "fleet-comms" / "pytest-of-ops" / "pytest-1" / "scratch.db")
    (tmp_path / "data" / "datasets" / "ordinary.txt").write_text("recover me\n", encoding="utf-8")
    database_hashes = {database.relative_to(tmp_path).as_posix(): _logical_sha256(database) for database in databases}
    file_hashes = {
        relative: _file_sha256(tmp_path / relative)
        for relative in (
            "data/datasets/ordinary.txt",
            "batch_state/fleet-comms/state.txt",
            ".agent/recovery-state.json",
            ".claude/atlas-epic/HANDOFF.md",
        )
    }
    return database_hashes, file_hashes


def _assert_restored(target: Path, database_hashes: dict[str, str], file_hashes: dict[str, str]) -> None:
    for relative, expected in database_hashes.items():
        with sqlite3.connect(target / relative) as connection:
            assert connection.execute("PRAGMA integrity_check").fetchone() == ("ok",), relative
        assert _logical_sha256(target / relative) == expected, relative
    for relative, expected in file_hashes.items():
        assert _file_sha256(target / relative) == expected, relative
    restored_databases = {
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file() and path.suffix in {".db", ".sqlite3"}
    }
    assert restored_databases == set(database_hashes)


def _real_restic_snapshot(
    environment: dict[str, str],
    run_id: str,
    cwd: Path,
    *arguments: str,
    stdin: bytes | None = None,
) -> str:
    """Write one snapshot of run ``run_id`` with the real restic CLI; return its ID."""
    output = subprocess.run(
        [
            environment["TEST_REAL_RESTIC"],
            "-r",
            environment["TEST_LOCAL_RESTIC_REPOSITORY"],
            "--password-file",
            environment["RESTIC_PASSWORD_FILE"],
            "backup",
            *arguments,
            "--host",
            "learn-ukrainian",
            "--tag",
            "learn-ukrainian-data",
            "--tag",
            f"lu-run-{run_id}",
            "--json",
        ],
        input=stdin,
        cwd=cwd,
        check=True,
        capture_output=True,
        timeout=60,
    ).stdout.decode()
    return next(json.loads(line) for line in output.splitlines() if '"summary"' in line)["snapshot_id"]


def _real_restic_base_snapshot(
    environment: dict[str, str], run_id: str, project: Path, databases: list[str], tmp_path: Path
) -> str:
    """The file-phase snapshot of a run: every recovery root minus its databases."""
    excludes = tmp_path / f"{run_id}-excludes"
    excludes.write_text("".join(f"{project / relative}\n" for relative in databases), encoding="utf-8")
    return _real_restic_snapshot(
        environment,
        run_id,
        project,
        "data",
        "batch_state",
        ".agent",
        ".claude/atlas-epic",
        "--tag",
        "lu-part-base",
        "--exclude-file",
        str(excludes),
        "--exclude",
        str(project / "batch_state" / "fleet-comms" / "pytest-of-ops"),
    )


def _real_restic_complete_snapshot(environment: dict[str, str], run_id: str, project: Path, receipt: dict) -> str:
    return _real_restic_snapshot(
        environment,
        run_id,
        project,
        "--stdin",
        "--stdin-filename",
        "BACKUP-RECEIPT.json",
        "--tag",
        "lu-part-complete",
        stdin=json.dumps(receipt).encode(),
    )


def _restored_files(target: Path) -> list[str]:
    return sorted(path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file())


def _fresh_runner_mirror(source: Path) -> Path:
    """A runner mirror whose manifest the pre-wipe gate accepts as fresh."""
    mirror = source / "lexicon" / "runner-mirror" / "run-20k"
    mirror.mkdir(parents=True)
    (mirror / "state.txt").write_text("state\n", encoding="utf-8")
    (mirror / "manifest.json").write_text(
        json.dumps(
            {
                "schema": "atlas-runner-mirror-manifest",
                "schema_version": 1,
                "generated_at": time.time(),
                "file_count": 1,
                "total_bytes": 6,
                "files": [{"path": "state.txt", "bytes": 6, "sha256": hashlib.sha256(b"state\n").hexdigest()}],
            }
        ),
        encoding="utf-8",
    )
    return mirror


def _real_restic(environment: dict[str, str], *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run the real restic CLI against the local test repository without a cache."""
    return subprocess.run(
        [
            environment["TEST_REAL_RESTIC"],
            "-r",
            environment["TEST_LOCAL_RESTIC_REPOSITORY"],
            "--password-file",
            environment["RESTIC_PASSWORD_FILE"],
            "--no-cache",
            *arguments,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _repository_snapshots(environment: dict[str, str]) -> list[dict]:
    listed = _real_restic(environment, "snapshots", "--json")
    assert listed.returncode == 0, listed.stderr
    return json.loads(listed.stdout)


def _run_id(snapshot: dict) -> str:
    return next(tag.removeprefix("lu-run-") for tag in snapshot["tags"] if tag.startswith("lu-run-"))


def _completed_run_ids(environment: dict[str, str]) -> list[str]:
    return sorted(
        _run_id(snapshot) for snapshot in _repository_snapshots(environment) if "lu-part-complete" in snapshot["tags"]
    )


def _run_interrupted(environment: dict[str, str], signal_number: int) -> subprocess.CompletedProcess[str]:
    """Run a backup, then signal its whole process group at TEST_HOLD_FILE."""
    hold = Path(environment["TEST_HOLD_FILE"])
    process = subprocess.Popen(
        ["/bin/bash", str(SCRIPT), "backup", "--execute"],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 60
        while not hold.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert hold.exists(), process.communicate(timeout=60)
        os.killpg(process.pid, signal_number)
        stdout, stderr = process.communicate(timeout=60)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=60)
    return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)


def _restored_run_id(environment: dict[str, str], target: Path) -> str:
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
    assert restored.returncode == 0, restored.stderr
    return json.loads((target / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))["linux_run"]["run_id"]


PRE_COMPLETION_FAULTS = [
    "check-fails",
    "pending-summary-invalid",
    "mirror-mutated",
    "pending-pack-corrupted",
    "term-in-gate-staging",
    "gate-staging-fails",
    "completion-upload-fails",
    "sigkill-before-completion",
]
