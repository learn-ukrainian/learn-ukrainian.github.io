"""Manifest-derived session-stream inventory (Sol PR-H / #5512).

The hard-coded four-epic list must not remain authoritative. Inventory is
derived from ``scripts/config/issue_streams.yaml`` so every stream epic can
participate in dual-write / cutover tracking without code edits per epic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_STREAMS_YAML = Path("scripts/config/issue_streams.yaml")

# Optional explicit handoff path overrides (relative to repo root).
# First existing path wins when resolving a live mirror source.
# Keys are stream ids ``epic:<number>``.
HANDOFF_PATH_OVERRIDES: dict[str, tuple[str, ...]] = {
    "epic:4387": (
        ".claude/atlas-epic/INTERIM-DRIVER-HANDOFF.md",
        ".claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md",
    ),
    "epic:4700": (
        ".claude/atlas-epic/INTERIM-DRIVER-HANDOFF.md",
        ".claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md",
    ),
    "epic:4707": (
        ".claude/harness-epic/CLAUDE-DRIVER-HANDOFF.md",
        "docs/session-state/current.claude-infra.md",
    ),
    "epic:4542": (
        ".claude/hramatka-epic/CLAUDE-DRIVER-HANDOFF.md",
        "docs/session-state/current.claude-hramatka.md",
    ),
    "epic:4706": (
        ".claude/bio-epic/CLAUDE-DRIVER-HANDOFF.md",
        "docs/session-state/current.claude-bio.md",
    ),
    "epic:2836": (
        ".claude/folk-epic/CLAUDE-DRIVER-HANDOFF.md",
        "docs/session-state/current.claude-folk.md",
    ),
    "epic:4431": (
        ".claude/bio-epic/CLAUDE-DRIVER-HANDOFF.md",
        "docs/session-state/current.claude-bio.md",
    ),
}

# Map issue-stream *names* → conventional .claude/<slug>-epic/ directories.
_STREAM_NAME_TO_CLAUDE_DIR: dict[str, str] = {
    "atlas-practice": "atlas",
    "atlas-intake": "atlas",
    "infra-harness": "harness",
    "hramatka": "hramatka",
    "seminars-folk": "folk",
    "seminars-bio": "bio",
    "corpus-channels": "bio",
    "core-quality": "core",
    "eval-harness": "harness",
    "benchmark-2156": "harness",
    "seminars-cross": "folk",
}


@dataclass(frozen=True, slots=True)
class StreamEpicRecord:
    """One epic that may host a session stream."""

    stream_id: str  # epic:4387
    epic_number: int
    stream_name: str  # atlas-practice
    title: str
    handoff_candidates: tuple[str, ...]


def _load_streams_doc(path: Path) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"issue_streams.yaml must be a mapping: {path}")
    streams = raw.get("streams")
    if not isinstance(streams, dict):
        raise ValueError(f"issue_streams.yaml missing streams map: {path}")
    return streams


def _handoff_candidates_for(stream_name: str, epic_number: int) -> tuple[str, ...]:
    stream_id = f"epic:{epic_number}"
    if stream_id in HANDOFF_PATH_OVERRIDES:
        return HANDOFF_PATH_OVERRIDES[stream_id]
    slug = _STREAM_NAME_TO_CLAUDE_DIR.get(stream_name, stream_name.replace("_", "-"))
    return (
        f".claude/{slug}-epic/CLAUDE-DRIVER-HANDOFF.md",
        f".claude/{slug}-epic/INTERIM-DRIVER-HANDOFF.md",
        f"docs/session-state/current.claude-{slug}.md",
    )


def load_stream_epic_inventory(
    repo_root: Path,
    *,
    streams_yaml: Path | None = None,
) -> tuple[StreamEpicRecord, ...]:
    """Return every epic registered in issue_streams.yaml as a stream candidate.

    Deduplicates epic numbers (an epic listed under multiple stream names keeps
    the first registration order from the YAML file).
    """
    root = repo_root.resolve()
    path = streams_yaml if streams_yaml is not None else root / DEFAULT_STREAMS_YAML
    if not path.is_absolute():
        path = root / path
    streams = _load_streams_doc(path)
    seen: set[int] = set()
    out: list[StreamEpicRecord] = []
    for stream_name, body in streams.items():
        if not isinstance(body, dict):
            continue
        title = str(body.get("title") or stream_name)
        epics = body.get("epics") or []
        if not isinstance(epics, list):
            continue
        for raw in epics:
            try:
                num = int(raw)
            except (TypeError, ValueError):
                continue
            if num in seen:
                continue
            seen.add(num)
            out.append(
                StreamEpicRecord(
                    stream_id=f"epic:{num}",
                    epic_number=num,
                    stream_name=str(stream_name),
                    title=title,
                    handoff_candidates=_handoff_candidates_for(str(stream_name), num),
                )
            )
    return tuple(out)


def epic_handoff_map(
    repo_root: Path,
    *,
    streams_yaml: Path | None = None,
) -> dict[str, tuple[str, ...]]:
    """Map ``epic:<n>`` → handoff candidate paths (replaces hard-coded four-epic dict)."""
    return {
        rec.stream_id: rec.handoff_candidates
        for rec in load_stream_epic_inventory(repo_root, streams_yaml=streams_yaml)
    }


def inventory_covers_issue_streams(
    repo_root: Path,
    *,
    streams_yaml: Path | None = None,
) -> tuple[bool, list[str]]:
    """Return (ok, missing_stream_ids) vs issue_streams.yaml epic numbers."""
    records = load_stream_epic_inventory(repo_root, streams_yaml=streams_yaml)
    present = {r.epic_number for r in records}
    root = repo_root.resolve()
    path = streams_yaml if streams_yaml is not None else root / DEFAULT_STREAMS_YAML
    if not path.is_absolute():
        path = root / path
    streams = _load_streams_doc(path)
    expected: set[int] = set()
    for body in streams.values():
        if not isinstance(body, dict):
            continue
        for raw in body.get("epics") or []:
            try:
                expected.add(int(raw))
            except (TypeError, ValueError):
                continue
    missing = sorted(f"epic:{n}" for n in expected - present)
    return (not missing, missing)
