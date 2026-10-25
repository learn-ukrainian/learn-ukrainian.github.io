"""Provider registry. Each provider module exposes:

build(spec: TaskSpec, env: dict[str, str]) -> Invocation
parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult
"""

from __future__ import annotations

import importlib
from types import ModuleType

PROVIDERS = ("codex", "claude", "cursor", "agy", "muse", "opencode", "hermes")


def load(name: str) -> ModuleType:
    if name not in PROVIDERS:
        raise ValueError(f"unknown agent {name!r}; known: {', '.join(PROVIDERS)}")
    return importlib.import_module(f"scripts.dispatcher.providers.{name}")
