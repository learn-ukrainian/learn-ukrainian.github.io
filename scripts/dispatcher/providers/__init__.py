"""Provider registry. Each provider module exposes:

build(spec: TaskSpec, env: dict[str, str]) -> Invocation
parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult
"""

from __future__ import annotations

from types import ModuleType

PROVIDERS = ("codex", "claude", "cursor", "agy", "muse", "opencode", "hermes")


def load(name: str) -> ModuleType:
    if name == "codex":
        from scripts.dispatcher.providers import codex as module
    elif name == "claude":
        from scripts.dispatcher.providers import claude as module
    elif name == "cursor":
        from scripts.dispatcher.providers import cursor as module
    elif name == "agy":
        from scripts.dispatcher.providers import agy as module
    elif name == "muse":
        from scripts.dispatcher.providers import muse as module
    elif name == "opencode":
        from scripts.dispatcher.providers import opencode as module
    elif name == "hermes":
        from scripts.dispatcher.providers import hermes as module
    else:
        raise ValueError(f"unknown agent {name!r}; known: {', '.join(PROVIDERS)}")
    return module
