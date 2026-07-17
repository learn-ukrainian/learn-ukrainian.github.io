"""Cross-platform byte-deterministic ZIP writer (PR4 V3).

Pins the Python ``zipfile`` writer and normalizes ALL per-entry metadata so
double-assembly produces byte-identical archives across hosts:

- ``date_time`` fixed to DOS epoch (1980-01-01 00:00:00)
- ``create_system`` = 3 (Unix)
- ``external_attr`` = regular file 0o644 (Unix mode in high 16 bits)
- no extra fields
- stable entry ordering (caller supplies sorted paths)
- ``ZIP_DEFLATED`` at pinned compression level
- no ZIP64 unless required by size (prefer classic headers for small trees)

Proof: double-assembly byte-equality test in ``tests/test_lexicon_runner_pr4_finalize.py``.
"""

from __future__ import annotations

import hashlib
import zipfile
from collections.abc import Iterable
from pathlib import Path
from typing import BinaryIO

# DOS epoch — minimum legal ZIP local-header timestamp (spec V3).
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)

# Unix create_system value (PKZIP Appnote).
CREATE_SYSTEM_UNIX = 3

# Regular file mode 0o644 << 16 (Unix external_attr convention).
EXTERNAL_ATTR_FILE = 0o100644 << 16

# Pinned deflate level (matches gzip mtime=0 discipline in export_runtime_shards).
DEFAULT_COMPRESSLEVEL = 9

# Document the pinned writer for operators / audit.
ZIP_WRITER_PIN = {
    "module": "zipfile",
    "class": "ZipFile",
    "compression": "ZIP_DEFLATED",
    "compresslevel": DEFAULT_COMPRESSLEVEL,
    "date_time": list(ZIP_EPOCH),
    "create_system": CREATE_SYSTEM_UNIX,
    "external_attr": EXTERNAL_ATTR_FILE,
    "extra": "",
    "note": (
        "Python stdlib zipfile with fully normalized ZipInfo metadata; "
        "cross-platform byte equality is the acceptance proof (PR4 V3)."
    ),
}


def make_zipinfo(arcname: str, *, file_size: int | None = None) -> zipfile.ZipInfo:
    """Build a fully normalized :class:`zipfile.ZipInfo` for ``arcname``."""
    # Zip members always use forward slashes.
    name = arcname.replace("\\", "/").lstrip("/")
    info = zipfile.ZipInfo(filename=name, date_time=ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = CREATE_SYSTEM_UNIX
    info.create_version = 20
    info.extract_version = 20
    info.external_attr = EXTERNAL_ATTR_FILE
    info.internal_attr = 0
    info.extra = b""
    info.comment = b""
    info.flag_bits = 0
    if file_size is not None:
        info.file_size = int(file_size)
    return info


def write_deterministic_zip(
    archive_path: Path,
    members: Iterable[tuple[str, bytes]],
    *,
    compresslevel: int = DEFAULT_COMPRESSLEVEL,
) -> str:
    """Write ``(arcname, payload)`` members with normalized metadata; return sha256.

    Members should already be in stable order. Duplicate arcnames raise.
    """
    archive_path = Path(archive_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = archive_path.with_name(f".{archive_path.name}.tmp-{archive_path.stat().st_ino if archive_path.exists() else 'new'}")
    # Same-partition temp next to destination for atomic promote.
    tmp = archive_path.parent / f".{archive_path.name}.part"
    if tmp.exists():
        tmp.unlink()

    seen: set[str] = set()
    try:
        with zipfile.ZipFile(
            tmp,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
        ) as zf:
            for arcname, payload in members:
                name = arcname.replace("\\", "/").lstrip("/")
                if not name or name.endswith("/"):
                    raise ValueError(f"invalid zip member name: {arcname!r}")
                if name in seen:
                    raise ValueError(f"duplicate zip member: {name}")
                seen.add(name)
                info = make_zipinfo(name, file_size=len(payload))
                # compresslevel is supported on writestr since Python 3.7.
                zf.writestr(info, payload, compresslevel=compresslevel)
        digest = hashlib.sha256(tmp.read_bytes()).hexdigest()
        tmp.replace(archive_path)
        return digest
    except Exception:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def zip_tree_deterministic(
    tree_root: Path,
    archive_path: Path,
    *,
    arc_prefix: str = "",
    compresslevel: int = DEFAULT_COMPRESSLEVEL,
) -> str:
    """Zip every file under ``tree_root`` with normalized metadata; return sha256.

    Paths inside the archive are relative to ``tree_root`` (optionally under
    ``arc_prefix``). Stable sort by relative POSIX path.
    """
    tree_root = Path(tree_root)
    if not tree_root.is_dir():
        raise FileNotFoundError(f"tree root missing: {tree_root}")

    members: list[tuple[str, bytes]] = []
    for path in sorted(p for p in tree_root.rglob("*") if p.is_file()):
        rel = path.relative_to(tree_root).as_posix()
        arcname = f"{arc_prefix.rstrip('/')}/{rel}" if arc_prefix else rel
        members.append((arcname, path.read_bytes()))
    return write_deterministic_zip(archive_path, members, compresslevel=compresslevel)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_zip_normalized_view(archive: Path | BinaryIO) -> list[tuple[str, bytes, tuple]]:
    """Debug helper: return (name, payload, key-metadata) sorted by name."""
    out: list[tuple[str, bytes, tuple]] = []
    with zipfile.ZipFile(archive, "r") as zf:
        for name in sorted(n for n in zf.namelist() if not n.endswith("/")):
            info = zf.getinfo(name)
            out.append(
                (
                    name,
                    zf.read(name),
                    (
                        info.date_time,
                        info.create_system,
                        info.external_attr,
                        info.extra,
                        info.compress_type,
                    ),
                )
            )
    return out
