"""Hermetic tests for the storage topology bulk-root / active-DB resolver."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from scripts.storage.topology import (
    REQUIRED_BULK_MARKERS,
    ActiveDatabaseNetworkError,
    require_local_active_sources_db,
    resolve_active_sources_db,
    resolve_bulk_root,
    resolve_topology,
)
from tests.helpers.python import project_python

REPO_ROOT = Path(__file__).resolve().parents[1]


def _project_python() -> str:
    """The shared project interpreter (the one running pytest)."""
    return project_python()


def _make_bulk_root(path: Path, *, markers: tuple[str, ...] = REQUIRED_BULK_MARKERS) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    for marker in markers:
        (path / marker).mkdir(parents=True, exist_ok=True)
    return path


def test_smb_preferred_when_marker_valid(tmp_path: Path) -> None:
    smb = _make_bulk_root(tmp_path / "smb")
    drive = _make_bulk_root(tmp_path / "drive")
    result = resolve_bulk_root(
        env={},
        smb_candidates=[smb],
        drive_candidates=[drive],
    )
    assert result.available is True
    assert result.source == "smb"
    assert result.path == smb


def test_drive_fallback_when_smb_absent(tmp_path: Path) -> None:
    missing_smb = tmp_path / "smb-missing"
    drive = _make_bulk_root(tmp_path / "drive")
    result = resolve_bulk_root(
        env={},
        smb_candidates=[missing_smb],
        drive_candidates=[drive],
    )
    assert result.available is True
    assert result.source == "gdrive"
    assert result.path == drive


def test_unavailable_when_neither_present(tmp_path: Path) -> None:
    result = resolve_bulk_root(
        env={},
        smb_candidates=[tmp_path / "no-smb"],
        drive_candidates=[tmp_path / "no-drive"],
    )
    assert result.available is False
    assert result.source == "unavailable"
    assert result.path is None
    assert result.reason == "no_marker_valid_bulk_root"


def test_smb_present_but_missing_markers_falls_through_to_drive(tmp_path: Path) -> None:
    smb = tmp_path / "smb"
    smb.mkdir()
    (smb / "literary_texts").mkdir()
    # textbook_chunks intentionally absent
    drive = _make_bulk_root(tmp_path / "drive")
    result = resolve_bulk_root(
        env={},
        smb_candidates=[smb],
        drive_candidates=[drive],
    )
    assert result.available is True
    assert result.source == "gdrive"
    assert result.path == drive
    smb_reports = [c for c in result.candidates if c.kind == "smb"]
    assert smb_reports
    assert smb_reports[0].marker_valid is False
    assert "textbook_chunks" in smb_reports[0].missing_markers


def test_ambiguous_drive_roots_unavailable(tmp_path: Path) -> None:
    d1 = _make_bulk_root(tmp_path / "drive1")
    d2 = _make_bulk_root(tmp_path / "drive2")
    result = resolve_bulk_root(
        env={},
        smb_candidates=[],
        drive_candidates=[d1, d2],
    )
    assert result.available is False
    assert result.reason == "ambiguous_gdrive_roots"


def test_lu_bulk_root_override(tmp_path: Path) -> None:
    override = _make_bulk_root(tmp_path / "explicit")
    other = _make_bulk_root(tmp_path / "smb")
    result = resolve_bulk_root(
        env={"LU_BULK_ROOT": str(override)},
        smb_candidates=[other],
        drive_candidates=[],
    )
    assert result.available is True
    assert result.source == "override"
    assert result.path == override


def test_lu_gdrive_data_override_wins_over_caller_drive_candidates(
    tmp_path: Path,
) -> None:
    """LU_GDRIVE_DATA must beat caller drive_candidates (env first)."""
    env_root = _make_bulk_root(tmp_path / "env-drive")
    caller_root = _make_bulk_root(tmp_path / "caller-drive")
    result = resolve_bulk_root(
        env={"LU_GDRIVE_DATA": str(env_root)},
        smb_candidates=[],
        drive_candidates=[caller_root],
    )
    assert result.available is True
    assert result.source == "gdrive"
    assert result.path == env_root
    assert result.reason == "LU_GDRIVE_DATA marker-valid"
    # Caller candidate must not be selected when env override is set.
    assert result.path != caller_root


def test_invalid_lu_gdrive_data_fails_closed_no_drive_fallback(
    tmp_path: Path,
) -> None:
    """Invalid LU_GDRIVE_DATA must not fall through to other Drive roots."""
    invalid = tmp_path / "invalid-drive"
    invalid.mkdir()
    (invalid / "literary_texts").mkdir()
    # textbook_chunks intentionally absent → not marker-valid
    fallback = _make_bulk_root(tmp_path / "auto-drive")
    result = resolve_bulk_root(
        env={"LU_GDRIVE_DATA": str(invalid)},
        smb_candidates=[],
        drive_candidates=[fallback],
    )
    assert result.available is False
    assert result.path is None
    assert result.source == "unavailable"
    assert result.reason == "drive_override_not_marker_valid"
    gdrive_reports = [c for c in result.candidates if c.kind == "gdrive"]
    assert len(gdrive_reports) == 1
    assert gdrive_reports[0].path == str(invalid)
    assert gdrive_reports[0].marker_valid is False


def test_refuse_network_sources_db_override(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "data").mkdir(parents=True)
    (repo / "scripts").mkdir()
    (repo / "data" / "sources.db").write_bytes(b"sqlite")
    network = Path("/Volumes/UkrainianData/raw-sources/learn-ukrainian-data/sources.db")
    result = resolve_active_sources_db(
        repo,
        env={"LU_SOURCES_DB": str(network)},
        refuse_network=True,
    )
    assert result.refused_network is True
    assert result.is_local is True
    assert result.path == repo / "data" / "sources.db"
    with pytest.raises(ActiveDatabaseNetworkError):
        require_local_active_sources_db(
            repo,
            env={"LU_SOURCES_DB": str(network)},
        )


def test_cli_status_json_subprocess(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "data").mkdir(parents=True)
    (repo / "scripts").mkdir()
    env = os.environ.copy()
    env["LU_BULK_ROOT"] = str(tmp_path / "missing-bulk")
    env.pop("LU_SMB_BULK_ROOT", None)
    env.pop("LU_GDRIVE_DATA", None)
    proc = subprocess.run(
        [
            str(_project_python()),
            "-m",
            "scripts.storage",
            "status",
            "--json",
            "--repo",
            str(repo),
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["schema"] == "storage-topology.status.v1"
    assert "active_database" in payload
    assert "bulk_root" in payload


def test_status_reports_sources_db_size_and_journal_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "data").mkdir(parents=True)
    (repo / "scripts").mkdir()
    db = repo / "data" / "sources.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        assert conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    payload = resolve_topology(
        repository_root=repo,
        env={},
        smb_candidates=[tmp_path / "missing-smb"],
        drive_candidates=[tmp_path / "missing-drive"],
    ).to_dict()
    active = payload["active_database"]
    assert active["journal_mode"] == "wal"
    assert active["size_bytes"] == db.stat().st_size > 0
    assert isinstance(active["wal_bytes"], int)
    json.dumps(payload)

    missing = resolve_topology(
        repository_root=tmp_path / "elsewhere",
        env={},
        smb_candidates=[],
        drive_candidates=[],
    ).to_dict()["active_database"]
    assert (missing["size_bytes"], missing["journal_mode"], missing["wal_bytes"]) == (None, None, None)
