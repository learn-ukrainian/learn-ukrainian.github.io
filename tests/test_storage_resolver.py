"""Hermetic tests for the storage topology bulk-root / active-DB resolver."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.storage.topology import (
    REQUIRED_BULK_MARKERS,
    ActiveDatabaseNetworkError,
    is_network_filesystem_path,
    report_mac_cache,
    require_local_active_sources_db,
    resolve_active_sources_db,
    resolve_bulk_root,
    resolve_topology,
    unresolved_bulk_placeholder,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _project_python() -> Path:
    local = REPO_ROOT / ".venv" / "bin" / "python"
    if local.exists():
        return local
    primary = Path("/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python")
    if primary.exists():
        return primary
    return Path(sys.executable)


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


def test_network_path_heuristic() -> None:
    assert is_network_filesystem_path(Path("/Volumes/UkrainianData/raw-sources/x"))
    assert is_network_filesystem_path(Path("//server/UkrainianData/x"))
    assert not is_network_filesystem_path(Path("/tmp/local-only"))


def test_mac_cache_report_only_for_gdrive(tmp_path: Path) -> None:
    drive = _make_bulk_root(tmp_path / "drive")
    (drive / "literary_texts" / "a.jsonl").write_text("x\n", encoding="utf-8")
    bulk = resolve_bulk_root(env={}, smb_candidates=[], drive_candidates=[drive])
    report = report_mac_cache(bulk, max_entries=10)
    assert report.applicable is True
    assert report.sampled_entries >= 1
    assert "Remove Download" in report.remove_download_instruction

    smb = resolve_bulk_root(
        env={},
        smb_candidates=[_make_bulk_root(tmp_path / "smb")],
        drive_candidates=[],
    )
    smb_report = report_mac_cache(smb)
    assert smb_report.applicable is False


def test_topology_status_json_roundtrip(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "data").mkdir(parents=True)
    (repo / "scripts").mkdir()
    status = resolve_topology(
        repository_root=repo,
        env={},
        smb_candidates=[tmp_path / "missing-smb"],
        drive_candidates=[tmp_path / "missing-drive"],
    )
    payload = status.to_dict()
    assert payload["schema"] == "storage-topology.status.v1"
    assert payload["bulk_root"]["available"] is False
    assert payload["active_database"]["is_local"] is True
    # Ensure JSON serializable.
    json.dumps(payload)


def test_unresolved_placeholder_does_not_exist() -> None:
    placeholder = unresolved_bulk_placeholder()
    assert not placeholder.exists()


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


def test_wiki_config_uses_bulk_resolver(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """scripts/wiki/config.py must consume the single bulk-root resolver."""
    bulk = _make_bulk_root(tmp_path / "bulk")
    monkeypatch.setenv("LU_BULK_ROOT", str(bulk))
    import importlib

    import scripts.wiki.config as wiki_config

    importlib.reload(wiki_config)
    try:
        assert bulk == wiki_config.GDRIVE_DATA
        assert bulk / "literary_texts" == wiki_config.LITERARY_DIR
    finally:
        monkeypatch.delenv("LU_BULK_ROOT", raising=False)
        importlib.reload(wiki_config)
