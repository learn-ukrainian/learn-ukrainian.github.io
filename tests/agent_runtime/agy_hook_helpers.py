"""Explicit positive-path registrations for the real AGY startup gate."""

import json
from pathlib import Path

from scripts.agent_runtime.agy_hook_config import GUARD_NAME, guard_registration


def register_agy_hooks(cwd: Path, *, home: Path | None = None) -> None:
    paths = [cwd / ".agents/hooks.json"]
    if home is not None:
        paths.append(home / ".gemini/config/hooks.json")
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({GUARD_NAME: guard_registration()}), encoding="utf-8")
