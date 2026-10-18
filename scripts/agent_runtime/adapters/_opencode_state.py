"""Keep OpenCode's writable config and caches in dispatch-owned scratch."""

from __future__ import annotations

import os
import shlex
import tempfile
from pathlib import Path


def opencode_command(cmd: list[str], *, cwd: Path) -> list[str]:
    """Apply state selectors after runtime env sanitization, without changing auth.

    OpenCode installs plugin dependencies in discovered project config dirs.
    Merely setting OPENCODE_CONFIG_DIR still discovers checkout .opencode dirs,
    so project config discovery must also be disabled (#10959). Keep HOME and
    the global config/data paths intact for the existing login mechanism.
    """
    scratch = Path(os.environ.get("LU_RUNTIME_TMP_ROOT") or os.environ.get("TMPDIR") or tempfile.gettempdir())
    state = scratch.resolve() / "opencode"
    checkout = cwd.resolve()
    paths = {name: (state / name).resolve() for name in ("config", "cache", "state")}
    if any(path.is_relative_to(checkout) for path in paths.values()):
        raise ValueError("OpenCode state must be outside the worker checkout")

    # These selectors are not admitted by the shared runtime env sanitizer.
    # A launcher also forwards --version probes of plan.cmd[0] to OpenCode.
    prefix = [
        "env",
        f"OPENCODE_CONFIG_DIR={paths['config']}",
        "OPENCODE_DISABLE_PROJECT_CONFIG=1",
        f"XDG_CACHE_HOME={paths['cache']}",
        f"XDG_STATE_HOME={paths['state']}",
        cmd[0],
    ]
    state.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", prefix="launch-", suffix=".sh", dir=state, delete=False
    ) as launcher:
        launcher.write(f'#!/bin/sh\nexec {shlex.join(prefix)} "$@"\n')
    path = Path(launcher.name)
    path.chmod(0o700)
    return [str(path), *cmd[1:]]
