"""Publish already validated, tracked open-model contract files.

These standalone K contracts have no artifact-set owner.  Their writers build
and validate the complete bundle before calling this narrow publisher.
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path


def publish_frozen_k_bundle(root: Path, outputs: Mapping[Path, bytes]) -> None:
    """Replace clean tracked registry files, preserving their Git file modes."""

    registry = root / "registry/projects/open_model_data"
    resolved_registry = registry.resolve()
    if resolved_registry != root.resolve() / "registry/projects/open_model_data":
        raise ValueError("open-model registry directory escapes repository")
    pending: dict[Path, bytes] = {}
    for target, content in outputs.items():
        if (
            not target.is_relative_to(registry)
            or not target.resolve().is_relative_to(resolved_registry)
            or target.is_symlink()
        ):
            raise ValueError(f"not a regular open-model registry output: {target}")
        mode = target.stat().st_mode
        if not stat.S_ISREG(mode):
            raise ValueError(f"not a regular open-model registry output: {target}")
        relative = target.relative_to(root).as_posix()
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=root,
            capture_output=True,
            check=False,
            timeout=30,
        )
        if tracked.returncode:
            raise ValueError(f"untracked registry output: {relative}")
        status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", relative],
            cwd=root,
            capture_output=True,
            check=True,
            timeout=30,
        )
        if status.stdout:
            raise ValueError(f"dirty tracked registry output: {relative}")
        if target.read_bytes() != content:
            pending[target] = content

    staged: dict[Path, Path] = {}
    try:
        for target, content in pending.items():
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", delete=False) as stream:
                staged[target] = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            staged[target].chmod(stat.S_IMODE(target.stat().st_mode))
        for target, temporary in staged.items():
            os.replace(temporary, target)
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
