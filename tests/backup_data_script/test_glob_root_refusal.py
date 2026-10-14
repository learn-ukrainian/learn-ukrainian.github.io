"""Project and staging roots must match the path allowlist before any snapshot.

On 91b4652540 a project root containing a backslash backed up with exit 0 and
the base snapshot stored batch_state/tasks/run-home/held.md as an explicit
source. find -path treats the backslash as an escape, so discovery did not
prune that home, and restic keeps an explicit path even when an exclude
matches it. The same commit already refused * ? [ ]. Those roots, plus
newline, space, a .. segment, and a relative path, now refuse before restic
is started.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

from tests.backup_data_script._restic_exclude_prune import path_is_excluded
from tests.backup_data_script._support import (
    REPO_ROOT,
    _make_database,
    _repository_snapshots,
    _run,
    _use_local_restic,
)

WAL_ONLY_ROW = "committed"
SCRIPT = REPO_ROOT / "scripts" / "backup-data.sh"
ALLOWLIST_MARK = "outside the backup path allowlist"

_ALLOWLIST_CHECKER = r"""
set -euo pipefail
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
extracted="$(awk '
  /^refuse_disallowed_root\(\)/ { capture = 1 }
  capture { print }
  capture && /^}$/ { exit }
' "$1")"
[[ -n "$extracted" ]]
eval "$extracted"
refuse_disallowed_root "$2" "$3"
"""


def _snapshot_files(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_symlink() or path.is_file()}


def _plant(scenario: str, project: Path) -> list[sqlite3.Connection]:
    connections: list[sqlite3.Connection] = []
    if scenario == "worker-home":
        database = _make_database(project / ".agent" / "worker-home" / "state.db", "main-file")
    elif scenario == "nested-home":
        database = _make_database(
            project / ".agent" / "batch_state" / "nested-home" / "state.db",
            "main-file",
        )
        database.with_name("note.json").write_text("keep the sibling\n", encoding="utf-8")
        secret = project / "batch_state" / "fleet-comms" / "scratch-home" / "secret.txt"
        secret.parent.mkdir(parents=True)
        secret.write_text("drop\n", encoding="utf-8")
    elif scenario == "ancestor-home":
        secret = project / "batch_state" / "real-home" / "secret.txt"
        secret.parent.mkdir(parents=True)
        secret.write_text("drop\n", encoding="utf-8")
        return connections
    elif scenario == "explicit-task":
        held = project / "batch_state" / "tasks" / "run-home" / "held.md"
        held.parent.mkdir(parents=True)
        held.write_text("excluded record\n", encoding="utf-8")
        kept = project / "batch_state" / "tasks" / "kept.md"
        kept.write_text("keep\n", encoding="utf-8")
        return connections
    else:
        raise AssertionError(scenario)
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA wal_autocheckpoint=0")
    connection.execute("INSERT INTO recovery_probe VALUES (?)", (WAL_ONLY_ROW,))
    connection.commit()
    assert database.with_name(f"{database.name}-wal").stat().st_size > 0
    connections.append(connection)
    return connections


def _allowlist_decision(label: str, root: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", "-c", _ALLOWLIST_CHECKER, "allowlist", str(SCRIPT), label, root],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _primary_checkout() -> Path:
    common = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--git-common-dir"],
        text=True,
        timeout=30,
    ).strip()
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = (REPO_ROOT / common_path).resolve()
    return common_path.parent


def _assert_refused_before_restic(
    result: subprocess.CompletedProcess[str], environment: dict[str, str], label: str
) -> None:
    assert result.returncode != 0, result.stderr
    assert f"Refusing to run: {label} is {ALLOWLIST_MARK}" in result.stderr
    log_path = Path(environment["TEST_INVOCATION_LOG"])
    assert not log_path.exists()
    assert _repository_snapshots(environment) == []


def _plant_held(project: Path) -> None:
    held = project / "batch_state" / "tasks" / "run-home" / "held.md"
    held.parent.mkdir(parents=True)
    held.write_text("excluded record\n", encoding="utf-8")
    kept = project / "batch_state" / "tasks" / "kept.md"
    kept.write_text("keep\n", encoding="utf-8")


def test_primary_checkout_and_worktree_roots_are_allowlisted() -> None:
    """The checkout running the tests and its primary checkout both pass."""
    for root in (REPO_ROOT, _primary_checkout()):
        decision = _allowlist_decision("project root", str(root))
        assert decision.returncode == 0, decision.stderr


@pytest.mark.parametrize(
    ("root", "reason"),
    [
        ("/fixture/ok\n/etc", "disallowed character"),
        ("/fixture/ok\n", "disallowed character"),
        ("/fixture/ok ", "disallowed character"),
        ("/fixture/ok\\bad", "disallowed character"),
        ("relative/path", "not absolute"),
        ("/fixture/foo/../bar", "dot-only segment"),
        ("/fixture/foo/./bar", "dot-only segment"),
        ("/fixture/.../bar", "dot-only segment"),
        ("/fixture/foo//bar", "empty segment"),
        ("/fixture/foo/", "empty segment"),
        ("/", "empty segment"),
        ("/fixture/foo+bar", "disallowed character"),
        ("/fixture/foo@bar", "disallowed character"),
    ],
)
def test_allowlist_function_rejects_the_whole_string(root: str, reason: str) -> None:
    decision = _allowlist_decision("project root", root)
    assert decision.returncode != 0
    assert ALLOWLIST_MARK in decision.stderr
    assert reason in decision.stderr


@pytest.mark.parametrize(
    ("backup_environment", "reason"),
    [
        ("proj\\ect", "disallowed character"),
        ("project*", "disallowed character"),
        ("project?", "disallowed character"),
        ("project[1]", "disallowed character"),
        ("proj]ect", "disallowed character"),
        ("my project", "disallowed character"),
    ],
    indirect=["backup_environment"],
)
def test_disallowed_project_root_refuses_before_upload(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    reason: str,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    _plant_held(source.parent)

    backed_up = _run(environment, "backup", "--execute")

    _assert_refused_before_restic(backed_up, environment, "project root")
    assert reason in backed_up.stderr


def test_staging_root_backslash_refuses_before_upload(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    staging_root = tmp_path / "stage\\root"
    staging_root.mkdir()
    environment["LU_BACKUP_TMPDIR"] = str(staging_root)

    backed_up = _run(environment, "backup", "--execute")

    _assert_refused_before_restic(backed_up, environment, "staging root")
    assert "disallowed character" in backed_up.stderr


def test_staging_root_space_refuses_before_upload(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    staging_root = tmp_path / "stage dir"
    staging_root.mkdir()
    environment["LU_BACKUP_TMPDIR"] = str(staging_root)

    backed_up = _run(environment, "backup", "--execute")

    _assert_refused_before_restic(backed_up, environment, "staging root")


@pytest.mark.parametrize(
    "mutate",
    [
        lambda root: f"{root}\n/etc",
        lambda root: f"{root}\n",
        lambda root: f"{root}/../{Path(root).name}",
        lambda _root: "relative/backup-root",
    ],
)
def test_newline_dotdot_and_relative_project_roots_refuse(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    mutate,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    environment["LU_BACKUP_PROJECT_ROOT"] = mutate(str(source.parent))

    backed_up = _run(environment, "backup", "--execute")

    _assert_refused_before_restic(backed_up, environment, "project root")


def test_newline_and_dotdot_staging_roots_refuse(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    environment, _source, staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    environment["LU_BACKUP_TMPDIR"] = f"{staging}\n"

    trailed = _run(environment, "backup", "--execute")
    _assert_refused_before_restic(trailed, environment, "staging root")

    environment["LU_BACKUP_TMPDIR"] = f"{staging}/../{staging.name}"
    dotted = _run(environment, "backup", "--execute")
    _assert_refused_before_restic(dotted, environment, "staging root")


@pytest.mark.parametrize("backup_environment", ["proj\\ect"], indirect=True)
@pytest.mark.parametrize("command", ["backup", "init", "doctor", "retention", "snapshots", "verify", "restore"])
def test_every_entry_point_refuses_a_backslash_project_root(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    command: str,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    _plant_held(source.parent)
    if command == "restore":
        arguments = ("restore", "latest", "--to", str(tmp_path / "restore-out"), "--execute")
    elif command in {"backup", "init"}:
        arguments = (command, "--execute")
    else:
        arguments = (command,)

    result = _run(environment, *arguments)

    _assert_refused_before_restic(result, environment, "project root")


@pytest.mark.parametrize(
    ("backup_environment", "scenario"),
    [
        ("project", "worker-home"),
        ("project", "nested-home"),
        ("batch_state/project-home/project", "ancestor-home"),
        ("project", "explicit-task"),
    ],
    indirect=["backup_environment"],
)
def test_fake_and_real_restic_select_the_same_files(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    scenario: str,
) -> None:
    """Home boundaries and an explicit task file agree on the fake and real restic."""
    environment, source, _staging, _legacy = backup_environment
    project = source.parent
    connections = _plant(scenario, project)
    try:
        fake_backup = _run(environment, "backup", "--execute")
        assert fake_backup.returncode == 0, fake_backup.stderr
        fake_files = _snapshot_files(Path(environment["FAKE_SNAPSHOT_DIR"]))

        _use_local_restic(environment, tmp_path)
        real_backup = _run(environment, "backup", "--execute")
        assert real_backup.returncode == 0, real_backup.stderr
        target = tmp_path / "real-restored"
        restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
        assert restored.returncode == 0, restored.stderr
    finally:
        for connection in connections:
            connection.close()

    real_files = _snapshot_files(target)
    assert fake_files == real_files, (
        f"only fake={sorted(fake_files - real_files)} only real={sorted(real_files - fake_files)}"
    )
    if scenario == "worker-home":
        assert ".agent/worker-home/state.db" in fake_files
        assert not any(path.endswith("state.db-wal") for path in fake_files)
    elif scenario == "nested-home":
        assert ".agent/batch_state/nested-home/note.json" in fake_files
        assert ".agent/batch_state/nested-home/state.db" in fake_files
        assert not any("scratch-home" in path for path in fake_files)
    elif scenario == "explicit-task":
        assert "batch_state/tasks/kept.md" in fake_files
        assert not any("run-home" in path for path in fake_files)
    else:
        assert "batch_state/fleet-comms/state.txt" in fake_files
        assert not any("real-home" in path for path in fake_files)


def test_fake_and_real_restic_follow_explicit_sources(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
) -> None:
    """An explicit file that matches an exclude is kept; unlisted files are not copied."""
    environment, _source, _staging, _legacy = backup_environment
    real_restic = shutil.which("restic", path=os.environ["PATH"])
    if real_restic is None:
        pytest.skip("restic unavailable")
    tree = tmp_path / "tree"
    held = tree / "batch_state" / "tasks" / "run-home" / "held.md"
    held.parent.mkdir(parents=True)
    held.write_text("explicit\n", encoding="utf-8")
    (tree / "batch_state" / "tasks" / "kept.md").write_text("kept\n", encoding="utf-8")
    (tree / "batch_state" / "tasks" / "other.md").write_text("not a source\n", encoding="utf-8")
    (tree / "data").mkdir()
    (tree / "data" / "note.txt").write_text("note\n", encoding="utf-8")
    (tree / "data" / "plain.db").write_bytes(b"not-sqlite")
    (tree / "extra").mkdir()
    (tree / "extra" / "nope.txt").write_text("nope\n", encoding="utf-8")
    listed = tmp_path / "files-from"
    listed.write_bytes(b"batch_state/tasks/kept.md\0")
    excludes = tmp_path / "excludes"
    excludes.write_text(f"{held}\n**/run-home/**\n**/*.db\n", encoding="utf-8")
    snapshot = tmp_path / "fake-snapshot"
    environment["FAKE_SNAPSHOT_DIR"] = str(snapshot)
    environment["FAKE_RESTIC_LOG"] = str(tmp_path / "fake-restic.log")
    arguments = [
        "backup",
        "batch_state/tasks/run-home/held.md",
        "data",
        "--files-from-raw",
        str(listed),
        "--host",
        "learn-ukrainian",
        "--tag",
        "learn-ukrainian-data",
        "--tag",
        "lu-part-base",
        "--json",
        "--exclude-file",
        str(excludes),
        "--option",
        "rclone.connections=1",
        "--retry-lock",
        "5m",
    ]
    fake_restic = Path(environment["PATH"].split(":", maxsplit=1)[0]) / "restic"
    fake = subprocess.run(
        [str(fake_restic), *arguments],
        cwd=tree,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert fake.returncode == 0, fake.stderr

    repository = tmp_path / "repo"
    password = environment["RESTIC_PASSWORD_FILE"]
    subprocess.run(
        [real_restic, "-r", str(repository), "--password-file", password, "init"],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    real = subprocess.run(
        [real_restic, "-r", str(repository), "--password-file", password, *arguments],
        cwd=tree,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert real.returncode == 0, real.stderr
    restored = tmp_path / "restored"
    subprocess.run(
        [
            real_restic,
            "-r",
            str(repository),
            "--password-file",
            password,
            "restore",
            "latest",
            "--target",
            str(restored),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )

    fake_files = _snapshot_files(snapshot)
    real_files = _snapshot_files(restored)
    assert fake_files == real_files, (
        f"only fake={sorted(fake_files - real_files)} only real={sorted(real_files - fake_files)}"
    )
    assert fake_files == {
        "batch_state/tasks/run-home/held.md",
        "batch_state/tasks/kept.md",
        "data/note.txt",
    }


def test_exclude_patterns_match_restic_home_boundaries() -> None:
    """Anchored patterns keep a nested home and drop only this project's batch_state home."""
    root = "/work/project"
    patterns = [
        f"{root}/batch_state/**/*-home",
        f"{root}/batch_state/**/*-home/**",
        f"{root}/batch_state/review-receipts/**/home",
        f"{root}/batch_state/review-receipts/**/home/**",
    ]
    assert not path_is_excluded(patterns, f"{root}/.agent/worker-home/state.db")
    assert not path_is_excluded(patterns, f"{root}/.agent/batch_state/nested-home/state.db")
    assert path_is_excluded(patterns, f"{root}/batch_state/fleet-comms/scratch-home/secret.txt")
    assert path_is_excluded(patterns, f"{root}/batch_state/real-home/secret.txt")
    escaped = root + "[1]"
    literal = escaped.replace("[", "\\[").replace("]", "\\]")
    bracket_patterns = [f"{literal}/batch_state/**/*-home"]
    assert path_is_excluded(bracket_patterns, f"{escaped}/batch_state/tasks/run-home/held.md")
    assert not path_is_excluded(bracket_patterns, f"{escaped}/.agent/batch_state/deeper/nested-home/state.db")
