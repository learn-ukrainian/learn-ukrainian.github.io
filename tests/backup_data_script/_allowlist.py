"""Expand scripts/config/backup-allowlist.json the way scripts/backup-data.sh does.

The script is the authority. This helper exists so tests can compare a selection
manifest with the same keep entries, prune rules, sidecars, and task-record
rules. It does not apply archive manifests: those tests set
LU_BACKUP_DB_ARCHIVE_DIR themselves and do not use this helper.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST_PATH = REPO_ROOT / "scripts" / "config" / "backup-allowlist.json"
SQLITE_HEADER = b"SQLite format 3\x00"
EPIC_LABEL = re.compile(r"^[a-z0-9-]+-epic$")
TRANSIENT_SQLITE = re.compile(r"(^|.*/)pytest-[^/]+/")
TASK_RECORD_SUFFIXES = (".json", ".result", ".diag", ".md", ".prompt")
# Same list as SNAPSHOT_EXCLUDE_ROOTS in scripts/backup-data.sh. Snapshot
# directories are excluded only under these roots.
SNAPSHOT_EXCLUDE_ROOTS = ("batch_state/tasks",)


def load_allowlist(path: Path = ALLOWLIST_PATH) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"Allowlist root must be an object: {path}")
    return payload


def is_sqlite_database(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(16) == SQLITE_HEADER
    except OSError:
        return False


def is_backup_sidecar(relative: str) -> bool:
    base = relative.rsplit("/", 1)[-1]
    if base == ".DS_Store":
        return True
    if base.endswith((".db-wal", ".db-shm", ".db-journal")):
        return True
    return any(base.endswith(suffix) and ".sqlite" in base[: -len(suffix)] for suffix in ("-wal", "-shm", "-journal"))


def task_record_is_staged(relative: str) -> bool:
    base = relative.rsplit("/", 1)[-1]
    if base.endswith(".lock"):
        return False
    if relative.startswith("batch_state/tasks/archive/"):
        return True
    return base.endswith(TASK_RECORD_SUFFIXES)


def is_transient_sqlite_path(path: Path, relative: str) -> bool:
    return TRANSIENT_SQLITE.search(relative) is not None and is_sqlite_database(path)


def _should_prune(directory: Path, name: str, project: Path) -> bool:
    if name == "__pycache__" or name.endswith("-home"):
        return True
    if name.endswith(".snapshots"):
        parent = directory.relative_to(project).as_posix()
        return any(parent == root or parent.startswith(f"{root}/") for root in SNAPSHOT_EXCLUDE_ROOTS)
    if name != "home":
        return False
    parent = directory.relative_to(project).as_posix()
    return parent == "batch_state/review-receipts" or parent.startswith("batch_state/review-receipts/")


def walk_tree_files(root: Path, project: Path, tmp_root: Path | None) -> list[Path]:
    """Regular files under root, without following symlinks or pruned directories."""
    found: list[Path] = []
    if not root.is_dir() or root.is_symlink():
        return found
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(directory)
        if tmp_root is not None and current == tmp_root:
            dirnames[:] = []
            continue
        dirnames[:] = [name for name in dirnames if not _should_prune(current, name, project)]
        for name in filenames:
            path = current / name
            if path.is_symlink() or not path.is_file():
                continue
            if tmp_root is not None and tmp_root in path.parents:
                continue
            found.append(path)
    return found


def expand_allowlist(
    project: Path,
    allowlist: dict[str, object] | None = None,
    *,
    tmp_root: Path | None = None,
) -> tuple[list[str], list[str], int]:
    """Return sorted seen paths, sorted staged paths, and the raw enumerated count."""
    payload = allowlist if allowlist is not None else load_allowlist()
    keep = payload["keep"]
    if not isinstance(keep, list):
        raise TypeError("Allowlist keep must be a list")
    enumerated: list[str] = []
    candidates: list[str] = []

    def note(path: Path) -> None:
        relative = path.relative_to(project).as_posix()
        enumerated.append(relative)
        if is_backup_sidecar(relative):
            return
        if relative.startswith("batch_state/tasks/") and not task_record_is_staged(relative):
            return
        candidates.append(relative)

    for entry in keep:
        if not isinstance(entry, dict):
            raise TypeError("Allowlist keep entry must be an object")
        path = str(entry["path"])
        kind = str(entry["kind"])
        if kind == "epic_glob":
            claude = project / ".claude"
            if not claude.is_dir():
                continue
            for epic in sorted(claude.glob("*-epic")):
                if epic.is_symlink() or not epic.is_dir() or EPIC_LABEL.fullmatch(epic.name) is None:
                    continue
                for child in walk_tree_files(epic, project, tmp_root):
                    note(child)
        elif kind in {"tree", "task_records"}:
            root = project / path
            if root.is_symlink() or not root.is_dir():
                continue
            for child in walk_tree_files(root, project, tmp_root):
                note(child)
        elif kind == "file":
            candidate = project / path
            if candidate.is_symlink() or not candidate.is_file():
                continue
            note(candidate)
        elif kind == "glob_files":
            directory = project / path.rsplit("/", 1)[0]
            base = path.rsplit("/", 1)[1]
            if directory.is_symlink() or not directory.is_dir():
                continue
            for match in sorted(directory.glob(base)):
                if match.is_symlink() or not match.is_file():
                    continue
                note(match)
        else:
            raise ValueError(f"Unknown allowlist kind: {kind}")

    staged = [relative for relative in candidates if not is_transient_sqlite_path(project / relative, relative)]
    return sorted(set(enumerated)), sorted(set(staged)), len(enumerated)


def parse_selection_manifest(path: Path) -> tuple[int, list[str], list[str]]:
    enumerated_count: int | None = None
    seen: list[str] = []
    staged: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        kind, _, value = line.partition(" ")
        if kind == "enumerated":
            enumerated_count = int(value)
        elif kind == "seen":
            seen.append(value)
        elif kind == "staged":
            staged.append(value)
        else:
            raise ValueError(f"Unknown selection manifest line: {line}")
    if enumerated_count is None:
        raise ValueError(f"Selection manifest has no enumerated count: {path}")
    return enumerated_count, seen, staged
