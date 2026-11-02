"""Provider registry. Each provider module exposes:

build(spec: TaskSpec, env: dict[str, str]) -> Invocation
parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult
"""

from __future__ import annotations

from collections.abc import Mapping
from types import ModuleType

PROVIDERS = ("codex", "claude", "cursor", "agy", "muse", "opencode")

# Read-only must be unable to edit. These CLIs give a dispatched run no enforceable write lock, so
# read-only is refused before launch instead of trusting the model not to edit (probed 2026-10-28).
# AGY has none either; its read-only runs inside the dispatcher's bubblewrap boundary (agy_sandbox,
# C-3027) and is refused only where that boundary cannot start.
READ_ONLY_REFUSALS: dict[str, str] = {}


def read_only_refusal(name: str, env: Mapping[str, str] | None = None) -> str | None:
    """The typed refusal for read-only on ``name``, or None when its read-only argv carries a write lock.

    AGY is refused where its bubblewrap boundary cannot start. With the run's environment, Claude is
    also refused while any managed policy could widen its lock.
    """
    reason = READ_ONLY_REFUSALS.get(name)
    if reason is None and name == "agy":
        from scripts.dispatcher import agy_sandbox

        reason = agy_sandbox.unavailable()
    if reason is None and name == "claude" and env is not None:
        from scripts.dispatcher.providers import claude

        reason = claude.managed_policy(env)
    if reason is None:
        return None
    usable = ", ".join(provider for provider in PROVIDERS if provider not in READ_ONLY_REFUSALS and provider != name)
    return f"read_only_unenforceable: {name} cannot run --mode read-only: {reason}; use {usable}"


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
    else:
        raise ValueError(f"unknown agent {name!r}; known: {', '.join(PROVIDERS)}")
    return module
