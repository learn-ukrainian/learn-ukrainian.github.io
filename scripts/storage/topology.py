"""Deterministic storage topology resolver for bulk sources and active SQLite.

Contract (storage topology v1):

- Active ``data/sources.db`` is always repository-local and never opened from
  SMB / network filesystems.
- Bulk raw-source root prefers a marker-valid Windows ``UkrainianData`` SMB
  mirror, then a marker-valid Google Drive File Provider path.
- Ambiguous or missing roots yield a structured unavailable state (no guessing).
- Status / cache reporting is read-only and never materializes cloud-only files.
"""

from __future__ import annotations

import os
import platform
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Required top-level directories that identify a learn-ukrainian bulk root.
# Both rebuild consumers and the Windows mirror use these as presence markers.
REQUIRED_BULK_MARKERS: tuple[str, ...] = ("literary_texts", "textbook_chunks")

# Conventional share / folder names from the approved topology (not host/IP).
SMB_SHARE_NAME = "UkrainianData"
BULK_LEAF_NAME = "learn-ukrainian-data"
BULK_RELATIVE_UNDER_SHARE = Path("raw-sources") / BULK_LEAF_NAME
DRIVE_RELATIVE = Path("My Drive") / "Projects" / BULK_LEAF_NAME

ENV_BULK_ROOT = "LU_BULK_ROOT"
ENV_SMB_BULK_ROOT = "LU_SMB_BULK_ROOT"
ENV_GDRIVE_DATA = "LU_GDRIVE_DATA"
ENV_SOURCES_DB = "LU_SOURCES_DB"

# macOS UF_DATALESS — cloud-only / File Provider stub (never open to inspect).
_UF_DATALESS = 0x40000000

_NETWORK_FS_TYPES = frozenset(
    {
        "smbfs",
        "nfs",
        "afpfs",
        "cifs",
        "webdav",
        "fuse",
        "osxfusefs",
        "macfuse",
        "sshfs",
    }
)


@dataclass(frozen=True)
class CandidateReport:
    """One probed bulk-root candidate."""

    kind: str
    path: str | None
    present: bool
    marker_valid: bool
    reason: str
    missing_markers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BulkRootResolution:
    """Result of bulk raw-source root resolution."""

    available: bool
    path: Path | None
    source: str
    reason: str
    candidates: tuple[CandidateReport, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "path": None if self.path is None else str(self.path),
            "source": self.source,
            "reason": self.reason,
            "candidates": [c.to_dict() for c in self.candidates],
        }


@dataclass(frozen=True)
class ActiveDatabaseResolution:
    """Repository-local active sources.db (never network/SMB)."""

    path: Path
    exists: bool
    is_local: bool
    refused_network: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "exists": self.exists,
            "is_local": self.is_local,
            "refused_network": self.refused_network,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class MacCacheReport:
    """Read-only Mac File Provider / dataless cache summary.

    Never opens file contents and never triggers materialization.
    """

    applicable: bool
    bulk_source: str
    sampled_entries: int
    local_or_unknown: int
    dataless_or_cloud_only: int
    reason: str
    remove_download_instruction: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TopologyStatus:
    """Full read-only topology status payload."""

    schema: str
    repository_root: str
    active_database: ActiveDatabaseResolution
    bulk_root: BulkRootResolution
    mac_cache: MacCacheReport
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "repository_root": self.repository_root,
            "active_database": self.active_database.to_dict(),
            "bulk_root": self.bulk_root.to_dict(),
            "mac_cache": self.mac_cache.to_dict(),
            "notes": list(self.notes),
        }


class ActiveDatabaseNetworkError(ValueError):
    """Raised when a caller tries to use a network path as active sources.db."""


def default_repository_root(start: Path | None = None) -> Path:
    """Resolve the repository root containing ``data/`` and ``scripts/``."""
    cur = start.expanduser().resolve() if start is not None else Path.cwd().resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / "scripts").is_dir() and (candidate / "data").is_dir():
            return candidate
        if (candidate / "scripts").is_dir() and (candidate / "AGENTS.md").is_file():
            return candidate
    return cur


def _is_marker_valid(root: Path, markers: Sequence[str] = REQUIRED_BULK_MARKERS) -> tuple[bool, tuple[str, ...]]:
    if not root.is_dir():
        return False, tuple(markers)
    missing = tuple(m for m in markers if not (root / m).is_dir())
    return (not missing, missing)


def _candidate(
    kind: str,
    path: Path | None,
    *,
    reason: str,
    markers: Sequence[str] = REQUIRED_BULK_MARKERS,
) -> CandidateReport:
    if path is None:
        return CandidateReport(
            kind=kind,
            path=None,
            present=False,
            marker_valid=False,
            reason=reason,
            missing_markers=tuple(markers),
        )
    present = path.is_dir()
    if not present:
        return CandidateReport(
            kind=kind,
            path=str(path),
            present=False,
            marker_valid=False,
            reason=reason,
            missing_markers=tuple(markers),
        )
    valid, missing = _is_marker_valid(path, markers)
    return CandidateReport(
        kind=kind,
        path=str(path),
        present=True,
        marker_valid=valid,
        reason="marker_valid" if valid else "missing_markers",
        missing_markers=missing,
    )


def discover_smb_bulk_candidates(
    *,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> list[Path]:
    """Return ordered SMB bulk-root candidates without validating markers."""
    del home  # reserved for future user-level mounts; avoid unused-arg noise
    environ = os.environ if env is None else env
    out: list[Path] = []
    seen: set[str] = set()

    def _add(path: Path) -> None:
        key = str(path)
        if key not in seen:
            seen.add(key)
            out.append(path)

    explicit = environ.get(ENV_SMB_BULK_ROOT)
    if explicit:
        _add(Path(explicit).expanduser())

    # Conventional volume mount of the UkrainianData share (share name only).
    _add(Path("/Volumes") / SMB_SHARE_NAME / BULK_RELATIVE_UNDER_SHARE)
    if platform.system() == "Linux":
        _add(Path("/mnt") / SMB_SHARE_NAME / BULK_RELATIVE_UNDER_SHARE)
        _add(Path("/media") / SMB_SHARE_NAME / BULK_RELATIVE_UNDER_SHARE)

    return out


def discover_drive_bulk_candidates(
    *,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> list[Path]:
    """Return ordered Google Drive File Provider bulk-root candidates."""
    environ = os.environ if env is None else env
    home_path = Path.home() if home is None else home
    out: list[Path] = []
    seen: set[str] = set()

    def _add(path: Path) -> None:
        key = str(path)
        if key not in seen:
            seen.add(key)
            out.append(path)

    explicit = environ.get(ENV_GDRIVE_DATA)
    if explicit:
        _add(Path(explicit).expanduser())
        return out

    cloudstorage = home_path / "Library" / "CloudStorage"
    if cloudstorage.is_dir():
        for mount in sorted(cloudstorage.glob("GoogleDrive-*")):
            _add(mount / DRIVE_RELATIVE)

    return out


def resolve_bulk_root(
    *,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
    smb_candidates: Iterable[Path] | None = None,
    drive_candidates: Iterable[Path] | None = None,
) -> BulkRootResolution:
    """Resolve the bulk raw-source root.

    Precedence (fail-closed at each override step):

    1. ``LU_BULK_ROOT`` — must be marker-valid or bulk is unavailable
    2. Marker-valid SMB candidates (caller list or discovery)
    3. ``LU_GDRIVE_DATA`` — env path is authoritative over caller
       ``drive_candidates``; invalid/missing markers fail closed (no silent
       fallback to auto-discovered Drive roots)
    4. Auto / caller Drive candidates when the env override is unset
    5. Unavailable
    """
    environ = os.environ if env is None else env
    reports: list[CandidateReport] = []

    explicit = environ.get(ENV_BULK_ROOT)
    if explicit:
        path = Path(explicit).expanduser()
        report = _candidate("override", path, reason="LU_BULK_ROOT")
        reports.append(report)
        if report.marker_valid:
            return BulkRootResolution(
                available=True,
                path=path,
                source="override",
                reason="LU_BULK_ROOT marker-valid",
                candidates=tuple(reports),
            )
        return BulkRootResolution(
            available=False,
            path=None,
            source="unavailable",
            reason="override_not_marker_valid",
            candidates=tuple(reports),
        )

    smb_list = (
        list(smb_candidates)
        if smb_candidates is not None
        else discover_smb_bulk_candidates(env=environ, home=home)
    )
    valid_smb: list[Path] = []
    for cand in smb_list:
        report = _candidate("smb", cand, reason="smb_probe")
        reports.append(report)
        if report.marker_valid:
            valid_smb.append(cand)

    if len(valid_smb) == 1:
        return BulkRootResolution(
            available=True,
            path=valid_smb[0],
            source="smb",
            reason="marker_valid_smb_mirror",
            candidates=tuple(reports),
        )
    if len(valid_smb) > 1:
        return BulkRootResolution(
            available=False,
            path=None,
            source="unavailable",
            reason="ambiguous_smb_roots",
            candidates=tuple(reports),
        )

    # Explicit LU_GDRIVE_DATA always wins over caller/auto drive candidates.
    # Invalid override is fail-closed (do not fall through to other Drive roots).
    explicit_drive = environ.get(ENV_GDRIVE_DATA)
    if explicit_drive:
        path = Path(explicit_drive).expanduser()
        report = _candidate("gdrive", path, reason="LU_GDRIVE_DATA")
        reports.append(report)
        if report.marker_valid:
            return BulkRootResolution(
                available=True,
                path=path,
                source="gdrive",
                reason="LU_GDRIVE_DATA marker-valid",
                candidates=tuple(reports),
            )
        return BulkRootResolution(
            available=False,
            path=None,
            source="unavailable",
            reason="drive_override_not_marker_valid",
            candidates=tuple(reports),
        )

    drive_list = (
        list(drive_candidates)
        if drive_candidates is not None
        else discover_drive_bulk_candidates(env=environ, home=home)
    )

    valid_drive: list[Path] = []
    for cand in drive_list:
        report = _candidate("gdrive", cand, reason="gdrive_probe")
        reports.append(report)
        if report.marker_valid:
            valid_drive.append(cand)

    if len(valid_drive) == 1:
        return BulkRootResolution(
            available=True,
            path=valid_drive[0],
            source="gdrive",
            reason="marker_valid_gdrive_fallback",
            candidates=tuple(reports),
        )
    if len(valid_drive) > 1:
        return BulkRootResolution(
            available=False,
            path=None,
            source="unavailable",
            reason="ambiguous_gdrive_roots",
            candidates=tuple(reports),
        )

    return BulkRootResolution(
        available=False,
        path=None,
        source="unavailable",
        reason="no_marker_valid_bulk_root",
        candidates=tuple(reports),
    )


def _path_looks_like_network(path: Path) -> bool:
    """Best-effort network/SMB detection without mounting or reading content."""
    resolved = str(path.expanduser())
    if resolved.startswith("//") or resolved.startswith("\\\\"):
        return True
    lower = resolved.lower()
    if "/volumes/ukrainiandata" in lower or "\\ukrainiandata\\" in lower:
        return True
    # UNC-style /Volumes/server/share is network when share is UkrainianData.
    parts = Path(resolved).parts
    return len(parts) >= 3 and parts[1] == "Volumes" and parts[2] == SMB_SHARE_NAME


def _fs_type_for_path(path: Path) -> str | None:
    """Return filesystem type for *path* when ``psutil`` is available."""
    try:
        import psutil  # type: ignore
    except ImportError:
        return None
    try:
        parts = psutil.disk_partitions(all=True)
    except Exception:
        return None
    best: str | None = None
    best_len = -1
    path_s = str(path.resolve()) if path.exists() else str(path)
    for part in parts:
        mount = part.mountpoint.rstrip("/") or part.mountpoint
        if (
            (path_s == mount or path_s.startswith(mount.rstrip("/") + "/"))
            and len(mount) > best_len
        ):
            best = (part.fstype or "").lower()
            best_len = len(mount)
    return best


def is_network_filesystem_path(path: Path) -> bool:
    """True when *path* is on SMB/network storage or a conventional share path."""
    if _path_looks_like_network(path):
        return True
    fs_type = _fs_type_for_path(path)
    if fs_type is None:
        return False
    if fs_type in _NETWORK_FS_TYPES:
        return True
    return "smb" in fs_type or "cifs" in fs_type or "nfs" in fs_type


def resolve_active_sources_db(
    repository_root: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    refuse_network: bool = True,
) -> ActiveDatabaseResolution:
    """Resolve the active sources.db path; refuse network/SMB locations."""
    environ = os.environ if env is None else env
    root = default_repository_root(repository_root)
    override = environ.get(ENV_SOURCES_DB)
    if override:
        path = Path(override).expanduser()
        if refuse_network and is_network_filesystem_path(path):
            local = root / "data" / "sources.db"
            return ActiveDatabaseResolution(
                path=local,
                exists=local.is_file(),
                is_local=True,
                refused_network=True,
                reason="refused_network_sources_db_override",
            )
        return ActiveDatabaseResolution(
            path=path,
            exists=path.is_file(),
            is_local=not is_network_filesystem_path(path),
            refused_network=False,
            reason="LU_SOURCES_DB",
        )

    path = root / "data" / "sources.db"
    network = is_network_filesystem_path(path)
    if refuse_network and network:
        return ActiveDatabaseResolution(
            path=path,
            exists=False,
            is_local=False,
            refused_network=True,
            reason="repository_data_on_network_filesystem",
        )
    return ActiveDatabaseResolution(
        path=path,
        exists=path.is_file(),
        is_local=not network,
        refused_network=False,
        reason="repository_local_data_sources_db",
    )


def require_local_active_sources_db(
    repository_root: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Return the active DB path or raise if a network location was requested."""
    result = resolve_active_sources_db(repository_root, env=env, refuse_network=True)
    if result.refused_network:
        raise ActiveDatabaseNetworkError(
            "Active sources.db must remain on local storage; "
            f"refused network path ({result.reason}). Use repository data/sources.db."
        )
    return result.path


def _entry_is_dataless(path: Path) -> bool | None:
    """Return True/False when dataless state is known; None when unknown.

    Uses ``st_flags & UF_DATALESS`` on macOS when available. Never opens the
    file for reading (which could trigger File Provider materialization).
    """
    try:
        st = path.lstat()
    except OSError:
        return None
    flags = getattr(st, "st_flags", None)
    if flags is None:
        return None
    return bool(flags & _UF_DATALESS)


def report_mac_cache(
    bulk: BulkRootResolution,
    *,
    max_entries: int = 200,
) -> MacCacheReport:
    """Report materialized vs dataless state without materializing files."""
    instruction = (
        "In Finder, select cloud-only items under the Drive project folder, "
        "then File → Remove Download. Do not run unsupported eviction CLIs; "
        "do not delete cloud objects or the SMB mirror."
    )
    if not bulk.available or bulk.path is None:
        return MacCacheReport(
            applicable=False,
            bulk_source=bulk.source,
            sampled_entries=0,
            local_or_unknown=0,
            dataless_or_cloud_only=0,
            reason="bulk_root_unavailable",
            remove_download_instruction=instruction,
        )
    if bulk.source not in {"gdrive", "override"}:
        return MacCacheReport(
            applicable=False,
            bulk_source=bulk.source,
            sampled_entries=0,
            local_or_unknown=0,
            dataless_or_cloud_only=0,
            reason="cache_report_applies_to_gdrive_file_provider_paths",
            remove_download_instruction=instruction,
        )

    sampled = 0
    localish = 0
    dataless = 0
    root = bulk.path
    try:
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            # Do not descend into huge trees beyond the sample budget.
            dirnames.sort()
            filenames.sort()
            for name in filenames:
                if sampled >= max_entries:
                    break
                entry = Path(dirpath) / name
                sampled += 1
                state = _entry_is_dataless(entry)
                if state is True:
                    dataless += 1
                else:
                    # False or unknown — report as local_or_unknown (never open).
                    localish += 1
            if sampled >= max_entries:
                break
    except OSError as exc:
        return MacCacheReport(
            applicable=True,
            bulk_source=bulk.source,
            sampled_entries=sampled,
            local_or_unknown=localish,
            dataless_or_cloud_only=dataless,
            reason=f"walk_error:{exc.__class__.__name__}",
            remove_download_instruction=instruction,
        )

    return MacCacheReport(
        applicable=True,
        bulk_source=bulk.source,
        sampled_entries=sampled,
        local_or_unknown=localish,
        dataless_or_cloud_only=dataless,
        reason="read_only_dataless_flag_sample",
        remove_download_instruction=instruction,
    )


def resolve_topology(
    repository_root: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
    smb_candidates: Iterable[Path] | None = None,
    drive_candidates: Iterable[Path] | None = None,
) -> TopologyStatus:
    """Build a full read-only topology status object."""
    root = default_repository_root(repository_root)
    active = resolve_active_sources_db(root, env=env)
    bulk = resolve_bulk_root(
        env=env,
        home=home,
        smb_candidates=smb_candidates,
        drive_candidates=drive_candidates,
    )
    cache = report_mac_cache(bulk)
    notes = [
        "Active SQLite remains repository-local; Sources MCP is unaffected by SMB outage.",
        "Bulk consumers prefer marker-valid SMB, then marker-valid Google Drive.",
        "Windows maintenance uses rclone copy (never sync) on local NTFS only.",
        "Mac cache is report-only; use Finder Remove Download for eviction.",
    ]
    return TopologyStatus(
        schema="storage-topology.status.v1",
        repository_root=str(root),
        active_database=active,
        bulk_root=bulk,
        mac_cache=cache,
        notes=tuple(notes),
    )


def unresolved_bulk_placeholder() -> Path:
    """Non-existent placeholder path for import-safe GDRIVE_DATA fallbacks."""
    return (
        Path.home()
        / "Library"
        / "CloudStorage"
        / "GoogleDrive-UNSET"
        / "My Drive"
        / "Projects"
        / BULK_LEAF_NAME
    )
