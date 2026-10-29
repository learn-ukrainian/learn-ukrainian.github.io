"""Backup and restore of the Sources store selector and its selected generation."""

from __future__ import annotations

import json
import os
import shlex
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

from scripts.storage import generations
from tests.backup_data_script._support import REPO_ROOT, _run, _use_local_restic

# Publishes one new generation under the writer lock, built from the selected
# one plus a 'published' row. Run synchronously: as a fixture step, and from the
# fake restic at a named backup point (the barrier).
PUBLISH_SCRIPT = """\
import sqlite3, sys
from contextlib import closing
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.storage import generations

selector = Path(sys.argv[2])
with generations.writer_lock(selector) as held:
    candidate = selector.with_name("candidate.db")
    with closing(sqlite3.connect(f"file:{held.generation}?mode=ro", uri=True)) as source:
        with closing(sqlite3.connect(candidate)) as copy:
            source.backup(copy)
            copy.execute("PRAGMA journal_mode=DELETE")
            copy.execute("INSERT INTO recovery_probe VALUES ('published')")
            copy.commit()
    generations.publish_generation(candidate, held)
"""


def _rows(database: Path) -> list[str]:
    with closing(sqlite3.connect(f"file:{database}?mode=ro", uri=True)) as connection:
        return [row[0] for row in connection.execute("SELECT value FROM recovery_probe ORDER BY rowid")]


def _no_free_space_margin(environment: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    # The fixture filesystem is small; the publisher's margin is tested with the publisher.
    for name in ("LU_EVIDENCE_FREE_DISK_FLOOR_BYTES", "LU_EVIDENCE_WAL_CEILING_BYTES"):
        monkeypatch.setenv(name, "0")
        environment[name] = "0"
    environment["LU_BACKUP_PYTHON"] = sys.executable


def _bootstrap(selector: Path) -> Path:
    """Turn the fixture's regular sources.db into the first held WAL generation."""
    with closing(sqlite3.connect(selector)) as connection:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
    generations.hold_database(selector)
    with generations.writer_lock(selector) as held:
        generations.checkpoint_legacy_store(held)
        return generations.publish_generation(selector, held, mode="bootstrap").generation


def _publish_command(selector: Path, tmp_path: Path) -> list[str]:
    script = tmp_path / "publish_generation.py"
    script.write_text(PUBLISH_SCRIPT, encoding="utf-8")
    return [sys.executable, str(script), str(REPO_ROOT), str(selector)]


def _publish(selector: Path, tmp_path: Path, environment: dict[str, str]) -> None:
    subprocess.run(_publish_command(selector, tmp_path), check=True, env=environment, timeout=60)


def test_selector_backs_up_only_the_selected_generation_and_restores_the_selector(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    _no_free_space_margin(environment, monkeypatch)
    selector = source / "sources.db"
    retained = _bootstrap(selector)
    # A second publication: the first generation stays retained but unselected.
    _publish(selector, tmp_path, environment)
    selected = selector.resolve()
    assert selected != retained and retained.exists()

    backed_up = _run(environment, "backup", "--execute")

    assert backed_up.returncode == 0, backed_up.stderr
    target = tmp_path / "restored"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
    assert restored.returncode == 0, restored.stderr
    receipt = json.loads((target / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    relative = f"data/sources-generations/{selected.name}"
    assert receipt["sources_selector"] == {"path": "data/sources.db", "generation": relative}
    database_paths = {entry["path"] for entry in receipt["linux_run"]["databases"]}
    assert relative in database_paths
    assert not any(retained.name in path for path in database_paths)
    restored_files = {path.name for path in (target / "data" / "sources-generations").iterdir()}
    assert selected.name in restored_files and retained.name not in restored_files
    assert not any(name.endswith(("-wal", "-shm")) for name in restored_files)
    assert os.readlink(target / "data" / "sources.db") == f"sources-generations/{selected.name}"
    assert _rows(target / "data" / "sources.db") == ["sources", "published"]
    assert generations.is_held(target / relative)

    scoped_target = tmp_path / "restored-scoped"
    scoped = _run(
        environment, "restore", "latest", "--to", str(scoped_target), "--path", "data/sources.db", "--execute"
    )
    assert scoped.returncode == 0, scoped.stderr
    assert os.readlink(scoped_target / "data" / "sources.db") == f"sources-generations/{selected.name}"
    assert _rows(scoped_target / "data" / "sources.db") == ["sources", "published"]


def test_publication_during_backup_restores_the_generation_the_backup_selected(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    _use_local_restic(environment, tmp_path)
    _no_free_space_margin(environment, monkeypatch)
    selector = source / "sources.db"
    old = _bootstrap(selector)
    # Barrier: the fake restic runs this publication to completion, synchronously,
    # after the backup resolved the selector and before the database copy phase.
    environment["TEST_MIRROR_MUTATION_AT"] = "backup lu-part-base"
    environment["TEST_MIRROR_MUTATION_CMD"] = shlex.join(_publish_command(selector, tmp_path))

    backed_up = _run(environment, "backup", "--execute")

    assert backed_up.returncode == 0, backed_up.stderr
    new = selector.resolve()
    assert new != old and _rows(new) == ["sources", "published"]
    assert _rows(old) == ["sources"]
    target = tmp_path / "restored"
    restored = _run(environment, "restore", "latest", "--to", str(target), "--execute")
    assert restored.returncode == 0, restored.stderr
    receipt = json.loads((target / "BACKUP-RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["sources_selector"]["generation"] == f"data/sources-generations/{old.name}"
    assert os.readlink(target / "data" / "sources.db") == f"sources-generations/{old.name}"
    assert _rows(target / "data" / "sources.db") == ["sources"]
    assert not (target / "data" / "sources-generations" / new.name).exists()


@pytest.mark.parametrize(
    "link_text",
    [
        "elsewhere.db",
        "sources-generations/not-a-generation.db",
        "sources-generations/../sources-generations/sources.20261029T000000Z-000000000000.db",
        "sources-generations/sources.20261029T000000Z-000000000000.db",
    ],
)
def test_any_other_link_at_the_selector_path_stops_the_backup(
    backup_environment: tuple[dict[str, str], Path, Path, Path],
    link_text: str,
) -> None:
    environment, source, _staging, _legacy = backup_environment
    selector = source / "sources.db"
    (source / "elsewhere.db").write_bytes(selector.read_bytes())
    (source / "sources-generations").mkdir()
    selector.unlink()
    # The last case names a valid generation that does not exist.
    selector.symlink_to(link_text)

    preview = _run(environment, "backup")

    assert preview.returncode != 0
    assert "Required recovery path must not be a symlink: data/sources.db" in preview.stderr
