"""Deterministic YAML and atomic file/sha256 sidecar writes (single writer).

Each replace is atomic; a crash between data and lock replacement is detected
by check(). This is an integrity sidecar, not a concurrency mutex.
"""

import hashlib
import os
import re
import tempfile
from pathlib import Path

import yaml

from . import codes


def yaml_bytes(data: object) -> bytes:
    """Sort mapping keys; callers supply record id order and VESUM form order."""
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=True, width=120).encode("utf-8")


def _mkdir(path: Path) -> None:
    if not path.exists():
        _mkdir(path.parent)
        path.mkdir(mode=0o755, exist_ok=True)
        path.chmod(0o755)


def atomic_write(path: Path, content: bytes, *, mode: int = 0o644) -> None:
    """Replace one file, with the temporary file on the same filesystem."""
    path = Path(path)
    _mkdir(path.parent)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write(path: Path, content: bytes | None = None) -> str:
    """Write optional file bytes and its exact `<sha256>\n` sidecar; return hash."""
    path = Path(path)
    if content is not None:
        atomic_write(path, content)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    atomic_write(Path(f"{path}.lock"), f"{digest}\n".encode("ascii"))
    return digest


def check(path: Path) -> bool:
    """Fail closed on absent, malformed, or mismatching sidecars."""
    path = Path(path)
    try:
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        recorded = Path(f"{path}.lock").read_bytes()
    except OSError:
        return False
    return bool(re.fullmatch(rb"[0-9a-f]{64}\n", recorded)) and recorded == f"{actual}\n".encode("ascii")


def require(path: Path) -> None:
    if not check(path):
        raise ValueError(f"{codes.LOCK_MISMATCH}: {str(path)!r}")
