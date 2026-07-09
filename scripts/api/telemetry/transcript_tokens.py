"""Parse Claude transcript JSONL usage for context-window telemetry."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class TranscriptTelemetry:
    """Context-window telemetry derived from assistant usage records."""

    tokens: int
    prev_tokens: int | None
    turn: int | None
    transcript_path: Path


def usage_input_tokens(usage: dict[str, Any]) -> int:
    """Return the statusline-compatible input-token sum for one usage block."""
    return (
        int(usage.get("input_tokens") or 0)
        + int(usage.get("cache_read_input_tokens") or 0)
        + int(usage.get("cache_creation_input_tokens") or 0)
    )


def parse_transcript_tokens(path: Path) -> TranscriptTelemetry | None:
    """Return latest and previous assistant context totals from a JSONL transcript."""
    latest: int | None = None
    previous: int | None = None
    turn = 0

    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("type") != "assistant":
                    continue
                message = obj.get("message")
                if not isinstance(message, dict):
                    continue
                usage = message.get("usage")
                if not isinstance(usage, dict):
                    continue
                tokens = usage_input_tokens(usage)
                if tokens <= 0:
                    continue
                previous = latest
                latest = tokens
                turn += 1
    except OSError:
        return None

    if latest is None:
        return None
    return TranscriptTelemetry(
        tokens=latest,
        prev_tokens=previous,
        turn=turn or None,
        transcript_path=path,
    )


def _claude_project_dir_name(project_root: Path) -> str:
    return str(project_root.resolve()).replace("/", "-")


def _newest_jsonl(paths: list[Path]) -> Path | None:
    candidates = [p for p in paths if p.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: (p.stat().st_mtime, str(p)))


def resolve_transcript_paths(project_root: Path, *, session: str | None = None) -> list[Path]:
    """Resolve candidate Claude transcript paths for this checkout.

    When ``session`` is given, resolve EXACTLY
    ``~/.claude/projects/<flat-root>/<session>.jsonl`` with no fallback
    globs and no cross-checkout scan.

    When ``session`` is omitted, honour ``LEARN_UKRAINIAN_TRANSCRIPT_PATH`` /
    ``CLAUDE_TRANSCRIPT_PATH`` (server-global test hook) then scan the
    checkout's project dir and legacy ``*learn-ukrainian*`` fallbacks.
    """
    if session:
        exact = Path.home() / ".claude" / "projects" / _claude_project_dir_name(project_root) / f"{session}.jsonl"
        return [exact] if exact.is_file() else []

    explicit = os.environ.get("LEARN_UKRAINIAN_TRANSCRIPT_PATH") or os.environ.get("CLAUDE_TRANSCRIPT_PATH")
    if explicit:
        path = Path(explicit).expanduser()
        return [path] if path.is_file() else []

    projects_dir = Path.home() / ".claude" / "projects"
    candidates: list[Path] = []
    exact_dir = projects_dir / _claude_project_dir_name(project_root)
    if exact_dir.is_dir():
        candidates.extend(exact_dir.glob("*.jsonl"))

    fallback_dirs = sorted(projects_dir.glob("*learn-ukrainian*"))
    for directory in fallback_dirs:
        if directory.is_dir():
            candidates.extend(directory.glob("*.jsonl"))

    unique = {path.resolve(): path for path in candidates if path.is_file()}
    return sorted(
        unique.values(),
        key=lambda p: (p.stat().st_mtime, str(p)),
        reverse=True,
    )


def resolve_transcript_path(
    project_root: Path,
    *,
    session: str | None = None,
) -> Path | None:
    """Resolve the newest Claude transcript path for this checkout."""
    return _newest_jsonl(resolve_transcript_paths(project_root, session=session))


def session_context_telemetry(
    project_root: Path,
    session: str,
) -> TranscriptTelemetry | None:
    """Resolve and parse telemetry for one explicit session transcript."""
    for path in resolve_transcript_paths(project_root, session=session):
        telemetry = parse_transcript_tokens(path)
        if telemetry is not None:
            return telemetry
    return None


def current_context_telemetry(project_root: Path) -> TranscriptTelemetry | None:
    """Resolve and parse the current transcript telemetry, if available."""
    for path in resolve_transcript_paths(project_root):
        telemetry = parse_transcript_tokens(path)
        if telemetry is not None:
            return telemetry
    return None
