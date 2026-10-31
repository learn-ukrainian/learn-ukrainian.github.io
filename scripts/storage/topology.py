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

import functools
import os
import platform
import re
import stat
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Literal

from scripts.common.repo_root import main_checkout_root

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
ENV_VESUM_DB = "LU_VESUM_DB"
ENV_LEXDATA_DB = "LU_LEXDATA_DB"

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
    size_bytes: int | None = None
    journal_mode: str | None = None
    wal_bytes: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "exists": self.exists,
            "is_local": self.is_local,
            "refused_network": self.refused_network,
            "reason": self.reason,
            "size_bytes": self.size_bytes,
            "journal_mode": self.journal_mode,
            "wal_bytes": self.wal_bytes,
        }


def _sqlite_header_journal_mode(path: Path) -> str | None:
    """Read-only journal-mode probe from SQLite header bytes 18-19 (2,2 = WAL; 1,1 = rollback journal)."""
    try:
        with path.open("rb") as stream:
            header = stream.read(20)
    except OSError:
        return None
    if len(header) < 20 or header[:16] != b"SQLite format 3\x00":
        return None
    if header[18] == 2 and header[19] == 2:
        return "wal"
    if header[18] == 1 and header[19] == 1:
        return "delete"
    return "unknown"


def _database_facts(path: Path) -> dict[str, Any]:
    """Size, journal mode, and WAL sidecar size of an on-disk SQLite file (never opens a connection)."""
    if not path.is_file():
        return {"size_bytes": None, "journal_mode": None, "wal_bytes": None}
    # A selector's sidecars sit next to the generation it selects.
    path = path.resolve()
    wal = path.with_name(f"{path.name}-wal")
    return {
        "size_bytes": path.stat().st_size,
        "journal_mode": _sqlite_header_journal_mode(path),
        "wal_bytes": wal.stat().st_size if wal.is_file() else 0,
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


StoreId = Literal["sources", "vesum", "lexdata"]

# Logical store -> (filename under the primary checkout's data/, env override).
# The one mapping every admitted store comes from; lexdata is the derived
# lexical store written only by scripts/lexdata/build_store.py.
STORE_FILES: Mapping[str, tuple[str, str]] = MappingProxyType({
    "sources": ("sources.db", ENV_SOURCES_DB),
    "vesum": ("vesum.db", ENV_VESUM_DB),
    "lexdata": ("lexdata.db", ENV_LEXDATA_DB),
})


@dataclass(frozen=True)
class StoreBinding:
    """Validated local read input; open with readonly_sqlite.open_readonly."""

    store: StoreId
    path: Path
    access_mode: Literal["read"] = "read"
    provenance: str = "injected"


@dataclass(frozen=True)
class StoreRefusal:
    """Unavailable input. Deliberately carries no path, even for diagnostics."""

    store: StoreId
    reason: str


@dataclass(frozen=True)
class ExplicitStoreWriteTarget:
    """Unvalidated input, never a read binding or permission to mutate a store."""

    location: str | Path
    role: Literal["active", "staging", "shadow"] = "active"


@dataclass(frozen=True)
class _PreparedStoreWriteTarget(ExplicitStoreWriteTarget):
    provenance: str = "explicit"
    environment: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class WriteStoreBinding:
    """A write location; a live Sources binding is valid only during its lock."""

    store: StoreId
    path: Path
    intent: Literal["update", "create"]
    operation: Literal["sqlite", "replace"]
    role: Literal["active", "staging", "shadow"]
    provenance: str
    sqlite_uri: str | None
    access_mode: Literal["write"] = "write"


def unavailable_store_path(store: StoreId) -> Path:
    """Import-safe compatibility value, refused by both store boundaries."""
    if store not in STORE_FILES:
        raise ValueError("unsupported logical store")
    return Path("/__learn_ukrainian_unavailable_store__") / store


def _store_locality(path: Path) -> Literal["local", "network", "unknown"]:
    """Require filesystem evidence; legacy best-effort detection is unchanged."""
    if _path_looks_like_network(path):
        return "network"
    fs_type = _fs_type_for_path(path)
    if not fs_type:
        return "unknown"
    if fs_type in _NETWORK_FS_TYPES or any(token in fs_type for token in ("smb", "cifs", "nfs")):
        return "network"
    # Only positively identified local filesystems qualify. Unrecognized FUSE,
    # distributed, or provider filesystems remain unknown.
    if fs_type in {"ext2", "ext3", "ext4", "xfs", "btrfs", "zfs", "apfs", "hfs", "hfs+",
                   "overlay", "tmpfs", "ramfs", "ntfs", "vfat", "exfat", "ufs"}:
        return "local"
    return "unknown"


def store_locality(path: Path) -> Literal["local", "network", "unknown"]:
    """Public locality check for store writers; only ``"local"`` is admissible."""
    return _store_locality(path)


# --- Sources store selector (generations are published by scripts/storage/generations.py) ---

GENERATIONS_DIRNAME = "sources-generations"
SELECTOR_NAME = "sources.db"
_GENERATION_NAME = re.compile(r"sources\.\d{8}T\d{6}Z-[0-9a-f]{12}\.db")
_REPO_ROOT = Path(__file__).resolve().parents[2]

StoreKind = Literal["selector", "generation", "legacy_live", "other"]
Layout = Literal["selector", "legacy_file", "missing"]


def is_generation_name(name: str) -> bool:
    return bool(_GENERATION_NAME.fullmatch(name))


@dataclass(frozen=True)
class SelectorState:
    """What a selector path is right now; ``generation`` is the file it selects."""

    layout: Layout | Literal["invalid"]
    reason: str
    generation: Path | None = None


def inspect_selector(selector: Path) -> SelectorState:
    """Classify the selector without following anything outside the generation directory."""
    try:
        info = selector.lstat()
    except FileNotFoundError:
        return SelectorState("missing", "selector_missing")
    if stat.S_ISREG(info.st_mode):
        return SelectorState("legacy_file", "regular_file", selector)
    if not stat.S_ISLNK(info.st_mode):
        return SelectorState("invalid", "selector_not_file_or_link")
    # The link text itself must be exact: no "./", doubled or trailing slashes.
    text = os.readlink(selector)
    prefix = f"{GENERATIONS_DIRNAME}/"
    name = text[len(prefix):] if text.startswith(prefix) else ""
    if not is_generation_name(name):
        return SelectorState("invalid", "selector_target_outside_generations")
    directory = selector.parent / GENERATIONS_DIRNAME
    try:
        if not stat.S_ISDIR(directory.lstat().st_mode):
            return SelectorState("invalid", "generations_dir_not_real_directory")
        target_info = (directory / name).lstat()
    except FileNotFoundError:
        return SelectorState("invalid", "selected_generation_missing")
    if not stat.S_ISREG(target_info.st_mode):
        return SelectorState("invalid", "selected_generation_not_regular_file")
    return SelectorState("selector", "selector", directory / name)


@functools.cache
def live_store_path() -> Path:
    """The primary checkout's store path (selector, or the regular file before the bootstrap)."""
    return resolve_active_sources_db(main_checkout_root(_REPO_ROOT), env={}).path


@dataclass(frozen=True)
class StoreRef:
    """Whether a path names the Sources store; ``lock_dir`` holds its writer lock."""

    kind: StoreKind
    selector: Path | None = None
    lock_dir: Path | None = None


def store_kind(path: str | os.PathLike[str]) -> StoreRef:
    """Say whether ``path`` names the Sources store.

    A selector is a link named ``sources.db`` whose text starts with the
    generation directory. A generation is any path that resolves into a
    generation directory (a differently named link to one included). Before the
    bootstrap the store is the primary checkout's regular ``data/sources.db``.
    Every other path (fixtures, staged copies, temporary builds) is ``other``.
    """
    raw = Path(os.path.abspath(os.fspath(path)))
    try:
        if raw.name == SELECTOR_NAME and raw.is_symlink():
            parts = PurePosixPath(os.readlink(raw)).parts
            if parts and parts[0] == GENERATIONS_DIRNAME:
                return StoreRef("selector", raw, raw.parent)
        resolved = raw.resolve()
    except (OSError, RuntimeError, ValueError):
        return StoreRef("other")
    if resolved.parent.name == GENERATIONS_DIRNAME and is_generation_name(resolved.name):
        return StoreRef("generation", None, resolved.parent.parent)
    try:
        live = live_store_path()
        if resolved == live.resolve() and live.is_file() and not live.is_symlink():
            return StoreRef("legacy_live", live, live.parent)
    except (OSError, RuntimeError, ValueError):
        return StoreRef("other")
    return StoreRef("other")


def store_data_dir(path: str | os.PathLike[str]) -> Path:
    """The directory that holds the Sources store ``path`` names.

    The live store is a selector link into ``sources-generations/``, and callers
    often hold the already-followed generation path. Either way the store's
    directory is the selector's, never the generation directory, so nothing derived
    from it (a cache, a lock, a backup, a repository root) lands inside the
    generations. Any other path (a fixture or staged copy) keeps its own parent.
    """
    ref = store_kind(path)
    if ref.lock_dir is not None:
        return ref.lock_dir.resolve()
    return Path(path).resolve().parent


def _names_selector(path: Path) -> bool:
    """True for a symlink whose text points into a Sources generation directory."""
    if not path.is_symlink():
        return False
    parts = PurePosixPath(os.readlink(path)).parts
    return bool(parts) and parts[0] == GENERATIONS_DIRNAME


def resolve_store(
    store: StoreId,
    repository_root: Path | None = None,
    *,
    binding: StoreBinding | None = None,
    env: Mapping[str, str] | None = None,
) -> StoreBinding | StoreRefusal:
    """Resolve at call time: injected read binding, override, primary store.

    Invalid explicit inputs never fall back. A store in the calling linked
    worktree is refused even if an explicit input would otherwise be usable.
    No connections, files, or directories are created by resolution.
    """
    if store not in STORE_FILES:
        raise ValueError("unsupported logical store")
    try:
        root = default_repository_root(repository_root).resolve()
        primary = main_checkout_root(root).resolve()
        filename, key = STORE_FILES[store]
        own = root / "data" / filename
        if root != primary and (own.exists() or own.is_symlink()):
            return StoreRefusal(store, "worktree_local_store")
        environ = os.environ if env is None else env
        if binding is not None:
            if binding.store != store or binding.access_mode != "read":
                return StoreRefusal(store, "invalid_binding")
            raw = str(binding.path)
            provenance = "injected"
        elif key in environ:
            raw = environ[key]
            provenance = key
        else:
            raw = str(primary / "data" / filename)
            provenance = "primary_checkout"
        if not raw.strip():
            return StoreRefusal(store, "empty_override")
        if raw.lower().startswith("file:"):
            return StoreRefusal(store, "uri_override")
        path = Path(raw)
        if not path.is_absolute():
            return StoreRefusal(store, "relative_override")
        if store == "sources" and (provenance == "primary_checkout" or _names_selector(path)):
            # The primary store is a regular file (before the bootstrap) or a
            # selector confined to its generation directory, never another link.
            state = inspect_selector(path)
            if state.layout == "missing":
                return StoreRefusal(store, "store_missing")
            if state.layout == "invalid":
                return StoreRefusal(store, state.reason)
        path = path.resolve(strict=True)
        if not path.is_file():
            return StoreRefusal(store, "not_a_file")
        locality = _store_locality(path)
        if locality != "local":
            return StoreRefusal(store, f"locality_{locality}")
        return StoreBinding(store, path, provenance=provenance)
    except FileNotFoundError:
        return StoreRefusal(store, "store_missing")
    except (OSError, RuntimeError, ValueError):
        return StoreRefusal(store, "store_unavailable")


def _is_worktree_store_slot(path: Path, primary: Path) -> bool:
    if path.name not in {STORE_FILES["sources"][0], STORE_FILES["vesum"][0]} or path.parent.name != "data":
        return False
    root = path.parent.parent
    return root != primary and os.path.lexists(root / ".git")


def _validate_write_candidate(
    store: StoreId, path: Path, primary: Path, role: str, intent: str, operation: str,
    environment: Mapping[str, str], *, final: bool,
) -> Path | StoreRefusal:
    """Validate an already constructed candidate; never open or modify it."""
    def refuse(reason: str) -> StoreRefusal:
        return StoreRefusal(store, reason)
    if path == unavailable_store_path(store):
        return refuse("store_missing")
    if _is_worktree_store_slot(path, primary):
        return refuse("worktree_local_store")
    if operation == "replace" and path.is_symlink():
        return refuse("symlink_replace_target")
    parent = path.parent.resolve(strict=True)
    if not parent.is_dir():
        return refuse("parent_missing")
    resolved = parent / path.name
    if _is_worktree_store_slot(resolved, primary):
        return refuse("worktree_local_store")
    locality = _store_locality(parent)
    if locality != "local":
        return refuse(f"locality_{locality}")
    if role != "active":
        # Include absent slots, invalid selectors, configured stores and historical
        # generations. Changing a role cannot turn a live store into an output.
        for filename, key in (STORE_FILES["sources"], STORE_FILES["vesum"]):
            canonical = primary / "data" / filename
            active = [canonical]
            if key in environment:
                raw = environment[key]
                if not raw.strip():
                    return refuse("empty_override")
                if raw.lower().startswith("file:"):
                    return refuse("uri_override")
                configured = Path(raw)
                if not configured.is_absolute():
                    return refuse("relative_override")
                if not configured.exists():
                    return refuse("store_missing")
                if not configured.is_file():
                    return refuse("not_a_file")
                if key == ENV_SOURCES_DB and _names_selector(configured):
                    state = inspect_selector(configured)
                    if state.layout != "selector":
                        return refuse(state.reason)
                active.append(configured)
            for live in active:
                if path == live or resolved == live or path.resolve() == live.resolve():
                    return refuse("target_is_active_store")
                if live.exists() and path.exists() and path.samefile(live):
                    return refuse("target_is_active_store")
                if filename == STORE_FILES["sources"][0] and path.exists():
                    live_target = live.resolve()
                    generation_dir = live_target.parent if is_generation_name(live_target.name) else live.parent / GENERATIONS_DIRNAME
                    try:
                        generations = tuple(generation_dir.iterdir())
                    except FileNotFoundError:
                        generations = ()
                    for generation in generations:
                        if is_generation_name(generation.name) and path.samefile(generation):
                            return refuse("target_is_active_store")
                if live.exists() and _store_locality(live.resolve()) != "local":
                    return refuse("locality_" + _store_locality(live.resolve()))
        if GENERATIONS_DIRNAME in resolved.parts or GENERATIONS_DIRNAME in path.resolve().parts:
            return refuse("target_is_active_store")
    if path.is_symlink() and not path.exists():
        return refuse("store_missing")
    if not path.exists():
        return resolved if intent == "create" else refuse("store_missing")
    # Preflight does not select a generation for the caller. That decision is
    # made only by resolve_store_for_write, after store_writer has acquired it.
    if not final and store == "sources" and _names_selector(path):
        locality = _store_locality(path)
        if locality != "local":
            return refuse(f"locality_{locality}")
        return path
    resolved = path.resolve(strict=True)
    if _is_worktree_store_slot(resolved, primary):
        return refuse("worktree_local_store")
    if not resolved.is_file():
        return refuse("not_a_file")
    locality = _store_locality(resolved)
    if locality != "local":
        return refuse(f"locality_{locality}")
    return resolved


def _prepare_store_write_target(
    store: StoreId, repository_root: Path | None = None, *,
    intent: Literal["update", "create"], operation: Literal["sqlite", "replace"] = "sqlite",
    target: ExplicitStoreWriteTarget | None = None, env: Mapping[str, str] | None = None,
) -> ExplicitStoreWriteTarget | StoreRefusal:
    """Freeze selection and provenance before locking, without selecting a generation."""
    if store not in STORE_FILES:
        raise ValueError("unsupported logical store")
    if store == "lexdata":
        return StoreRefusal(store, "unsupported_write_store")
    if target is not None and not isinstance(target, ExplicitStoreWriteTarget):
        return StoreRefusal(store, "invalid_binding" if isinstance(target, (StoreBinding, WriteStoreBinding))
                            else "invalid_target")
    if intent not in {"update", "create"} or operation not in {"sqlite", "replace"}:
        return StoreRefusal(store, "invalid_target")
    role = target.role if target is not None else "active"
    if role not in {"active", "staging", "shadow"}:
        return StoreRefusal(store, "invalid_target")
    if store == "sources" and operation == "replace":
        return StoreRefusal(store, "sources_replace_forbidden")
    if role == "staging" and operation == "replace":
        return StoreRefusal(store, "invalid_target")
    try:
        root = default_repository_root(repository_root).resolve()
        primary = main_checkout_root(root).resolve()
        filename, key = STORE_FILES[store]
        own = root / "data" / filename
        if root != primary and os.path.lexists(own):
            return StoreRefusal(store, "worktree_local_store")
        if isinstance(target, _PreparedStoreWriteTarget):
            environment = dict(target.environment)
            raw, provenance = str(target.location), target.provenance
        else:
            environment = dict(os.environ if env is None else env)
            if target is not None:
                raw, provenance = str(target.location), "explicit"
            elif key in environment:
                raw, provenance = environment[key], key
            else:
                raw, provenance = str(primary / "data" / filename), "primary_checkout"
        if not raw.strip():
            return StoreRefusal(store, "empty_override")
        if raw.lower().startswith("file:"):
            return StoreRefusal(store, "uri_override")
        path = Path(raw)
        if ".." in path.parts:
            return StoreRefusal(store, "invalid_target")
        if not path.is_absolute():
            if role == "active" or provenance != "explicit":
                return StoreRefusal(store, "relative_override")
            path = root / path
        if _is_worktree_store_slot(path, primary) or _is_worktree_store_slot(path.parent.resolve() / path.name, primary):
            return StoreRefusal(store, "worktree_local_store")
        if role == "active" and intent == "create":
            return StoreRefusal(store, f"active_{store}_create_forbidden")
        checked = _validate_write_candidate(store, path, primary, role, intent, operation, environment, final=False)
        if isinstance(checked, StoreRefusal):
            return checked
        return _PreparedStoreWriteTarget(path, role, provenance,
                                         tuple((key, environment[key]) for _, key in STORE_FILES.values()
                                               if key in environment))
    except FileNotFoundError:
        return StoreRefusal(store, "parent_missing")
    except (OSError, RuntimeError, ValueError):
        return StoreRefusal(store, "store_unavailable")


def resolve_store_for_write(
    store: StoreId, repository_root: Path | None = None, *,
    intent: Literal["update", "create"], operation: Literal["sqlite", "replace"] = "sqlite",
    target: ExplicitStoreWriteTarget | None = None, env: Mapping[str, str] | None = None,
) -> WriteStoreBinding | StoreRefusal:
    """Resolve a write location without connection or mutation; Sources needs its owner's lock."""
    prepared = _prepare_store_write_target(store, repository_root, intent=intent, operation=operation,
                                          target=target, env=env)
    if isinstance(prepared, StoreRefusal):
        return prepared
    assert isinstance(prepared, _PreparedStoreWriteTarget)
    try:
        path = Path(prepared.location)
        primary = main_checkout_root(default_repository_root(repository_root).resolve()).resolve()
        if store == "sources":
            from scripts.lib.readonly_sqlite import (
                _store_writers,
                _store_writers_lock,
                inherited_store_writer,
                writable_store_refusal,
            )

            ref = store_kind(path)
            requires_lock = (prepared.provenance == "primary_checkout"
                             or path == primary / "data" / STORE_FILES["sources"][0]
                             or _names_selector(path))
            if requires_lock and (ref.kind not in {"selector", "legacy_live"}
                                  or ref.selector != path or ref.lock_dir != path.parent):
                return StoreRefusal(store, "store_unavailable")
            if ref.kind == "generation":
                return StoreRefusal(store, "generation_named_directly")
            if requires_lock or ref.kind in {"selector", "legacy_live"}:
                if ref.lock_dir is None:
                    return StoreRefusal(store, "writer_lock_not_held")
                with _store_writers_lock:
                    selector = _store_writers.get(os.path.realpath(ref.lock_dir))
                if selector is None:
                    inherited = inherited_store_writer(ref.lock_dir)
                    selector = None if inherited is None else inherited[1]
                if selector is None:
                    return StoreRefusal(store, "writer_lock_not_held")
                if Path(os.path.abspath(selector)) != Path(os.path.abspath(path)):
                    return StoreRefusal(store, "not_selected_generation")
                state = inspect_selector(path)
                if state.layout not in {"selector", "legacy_file"}:
                    return StoreRefusal(store, state.reason)
                if reason := writable_store_refusal(path):
                    return StoreRefusal(store, reason)
        checked = _validate_write_candidate(store, path, primary, prepared.role, intent, operation,
                                            dict(prepared.environment), final=True)
        if isinstance(checked, StoreRefusal):
            return checked
        uri = checked.as_uri() + ("?mode=rwc" if intent == "create" else "?mode=rw")
        return WriteStoreBinding(store, checked, intent, operation, prepared.role, prepared.provenance,
                                 uri if operation == "sqlite" else None)
    except FileNotFoundError:
        return StoreRefusal(store, "store_missing")
    except (OSError, RuntimeError, ValueError):
        return StoreRefusal(store, "store_unavailable")


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
            **_database_facts(path),
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
        **_database_facts(path),
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
