"""Shared types for the minimal dispatcher (frozen interface; identical in every PR)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypedDict

ReviewAccess = Literal["isolated", "full"]


class ReviewAttempt(TypedDict):
    review_id: str
    attempt_id: str
    manifest_sha256: str


@dataclass(frozen=True)
class TaskSpec:
    task_id: str
    agent: str  # provider module: codex|claude|cursor|agy|muse|opencode|hermes
    model: str
    effort: str | None
    mode: str  # "read-only" | "workspace-write"
    worktree: Path
    prompt_file: Path
    final_file: Path  # where the final message ends up
    claude_account: str | None = None  # "a" | "b" for agent claude
    provider: str | None = None  # explicit upstream such as openrouter; never a fallback
    options: dict[str, str] = field(default_factory=dict)  # provider extras, e.g. {"contributor_mode": "on"}


@dataclass(frozen=True)
class Invocation:
    argv: list[str]
    stdin: bytes | None
    env: dict[str, str]
    final_file: Path | None  # file the CLI writes its final message to, if it does


@dataclass(frozen=True)
class ParsedResult:
    text: str | None
    usage: dict | None
    error: str | None  # set when the run must not count as success
    resolved_model: str | None = None  # runtime observation only; None includes conflicting reports
