"""Atomic file I/O helpers for build scripts."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def write_text_atomic(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    """Write text atomically via a temp file in the destination directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.stem}-",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


def write_json_atomic(
    path: Path,
    data: Any,
    *,
    encoding: str = "utf-8",
    **dump_kwargs: Any,
) -> None:
    """Serialize JSON and write it atomically."""
    write_text_atomic(
        path,
        json.dumps(data, **dump_kwargs),
        encoding=encoding,
    )


def plan_hash(plan_path: Path) -> str:
    """Return the SHA256 hex digest of a plan YAML file."""
    return hashlib.sha256(plan_path.read_bytes()).hexdigest()
