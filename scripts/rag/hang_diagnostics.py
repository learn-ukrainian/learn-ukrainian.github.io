"""Where the sources MCP server writes thread dumps, and their retention (#10674).

The call governor (``scripts/rag/call_governor.py``) writes a
``slow-call-*.txt`` file with every thread's Python stack for a call that
runs too long.

The dump directory is ``LU_SOURCES_DUMP_DIR`` when set, otherwise
``batch_state/sources-dumps`` under the project root. The directory is ignored
by Git and owner-only. Stacks carry file names, line numbers and function
names, never argument values. The writer calls ``prune_dump_dir`` after it
creates its file, so the directory stays bounded without any other process.
"""

from __future__ import annotations

import contextlib
import os
import stat
from collections.abc import Mapping
from pathlib import Path

DUMP_DIR_ENV = "LU_SOURCES_DUMP_DIR"
DEFAULT_DUMP_SUBDIR = Path("batch_state") / "sources-dumps"
SLOW_CALL_PREFIX = "slow-call-"
DEFAULT_KEEP_DUMPS = 20
DEFAULT_MAX_DUMP_BYTES = 8 * 1024 * 1024


def resolve_dump_dir(project_root: Path, environ: Mapping[str, str] | None = None) -> Path:
    environ = os.environ if environ is None else environ
    override = environ.get(DUMP_DIR_ENV, "").strip()
    return Path(override) if override else project_root / DEFAULT_DUMP_SUBDIR


def ensure_dump_dir(dump_dir: Path) -> Path:
    dump_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(dump_dir, 0o700)
    return dump_dir


def prune_dump_dir(
    dump_dir: Path,
    *,
    keep: int | None = None,
    max_bytes: int | None = None,
) -> list[Path]:
    """Bound the dump directory; return what was removed.

    Keeps the newest ``keep`` slow-call dumps, then drops the oldest until
    the slow-call dumps total at most ``max_bytes`` (the newest is always
    kept). Defaults resolve at call time.

    The directory is opened once, without following a symlink, and every
    later step goes through that descriptor, so replacing the path while
    this runs cannot redirect a deletion. It removes nothing unless the
    path is a real directory owned by the current user. A symlink named
    like a dump is removed itself, never through its target.
    """
    keep = DEFAULT_KEEP_DUMPS if keep is None else keep
    max_bytes = DEFAULT_MAX_DUMP_BYTES if max_bytes is None else max_bytes
    try:
        dir_fd = os.open(dump_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError:
        return []
    removed: list[Path] = []
    try:
        if os.fstat(dir_fd).st_uid != os.getuid():
            return []
        # The names carry a UTC stamp, so name order is age order.
        sizes: dict[str, int] = {}
        for name in sorted(os.listdir(dir_fd)):
            if not (name.startswith(SLOW_CALL_PREFIX) and name.endswith(".txt")):
                continue
            with contextlib.suppress(OSError):
                info = os.stat(name, dir_fd=dir_fd, follow_symlinks=False)
                if stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode):
                    sizes[name] = info.st_size
        names = list(sizes)
        excess = max(0, len(names) - keep)
        total = sum(sizes[name] for name in names[excess:])
        # Beyond ``keep`` always; past that only while over the byte bound,
        # never the newest.
        for index, name in enumerate(names[: max(excess, len(names) - 1)]):
            if index >= excess and total <= max_bytes:
                break
            with contextlib.suppress(FileNotFoundError):
                os.unlink(name, dir_fd=dir_fd)
            removed.append(dump_dir / name)
            if index >= excess:
                total -= sizes[name]
    finally:
        os.close(dir_fd)
    return removed
