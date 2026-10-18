"""Refuse DeepSeek requests carrying private repository or agent-state inputs."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

_PRIVATE_STATE_COMPONENTS = frozenset({".claude", ".agent", ".codex"})


class DeepSeekAdmissionRefused(ValueError):
    """A DeepSeek request crossed the public-repository input boundary."""


def refuse_deepseek_if_disallowed(
    effective_participants: Iterable[str | None],
    effective_models: Iterable[str | None] = (),
    *,
    repo: str | None = None,
    prompt_file: str | None = None,
) -> None:
    """Refuse non-public repository roles and prompt files inside private agent state."""
    names = (str(value or "").strip().casefold() for value in (*effective_participants, *effective_models))
    if not any(
        name in {"deepseek", "hermes", "hermes-deepseek"}
        or name.startswith(("deepseek-", "deepseek/", "acpx-deepseek", "openrouter/deepseek"))
        for name in names
    ):
        return
    if repo is not None and repo != "public-monorepo":
        raise DeepSeekAdmissionRefused("DEEPSEEK PUBLIC-ONLY: repository role must be public-monorepo")
    if prompt_file and _PRIVATE_STATE_COMPONENTS.intersection(Path(prompt_file).expanduser().parts):
        raise DeepSeekAdmissionRefused("DEEPSEEK PUBLIC-ONLY: prompt file lives in agent-private state")
