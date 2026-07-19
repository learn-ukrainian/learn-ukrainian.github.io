"""Non-destructive legacy-handoff mirroring for dual-write migration."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .model import Entry, EntryRef, EntryType, Lease
from .store import SessionStreamStore

ATLAS_PROFILE = "atlas"
ATLAS_HANDOFF_PATH = Path(".claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md")

# Registry of known epic streams → primary file handoff paths for dual-write.
# Phase-2 migration: mirror these under an active lease without retiring files.
# Paths are relative to the repository root. First existing path wins per epic.
EPIC_HANDOFF_CANDIDATES: dict[str, tuple[str, ...]] = {
    "epic:4387": (
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
}


@dataclass(frozen=True)
class MirrorResult:
    profile: str
    source_path: str
    source_sha256: str
    source_bytes: int
    entry: Entry
    mirror_id: int


@dataclass(frozen=True)
class HandoffCandidate:
    stream_id: str
    path: Path
    exists: bool


def list_handoff_candidates(repo_root: Path) -> list[HandoffCandidate]:
    """List configured epic handoff paths and whether each file exists."""
    root = repo_root.resolve()
    out: list[HandoffCandidate] = []
    for stream_id, paths in EPIC_HANDOFF_CANDIDATES.items():
        for rel in paths:
            path = root / rel
            out.append(HandoffCandidate(stream_id=stream_id, path=path, exists=path.is_file()))
    return out


def resolve_handoff_path(stream_id: str, repo_root: Path) -> Path | None:
    """Return the first existing handoff path for a stream, if any."""
    root = repo_root.resolve()
    for rel in EPIC_HANDOFF_CANDIDATES.get(stream_id, ()):
        path = root / rel
        if path.is_file():
            return path
    return None


def mirror_atlas_handoff(
    store: SessionStreamStore,
    lease: Lease,
    *,
    repo_root: Path,
    stream_id: str,
    source_path: Path = ATLAS_HANDOFF_PATH,
    now: datetime | None = None,
) -> MirrorResult:
    """Mirror the Atlas file handoff into an explicitly selected epic stream."""
    return mirror_handoff_file(
        store,
        lease,
        profile=ATLAS_PROFILE,
        repo_root=repo_root,
        stream_id=stream_id,
        source_path=source_path,
        now=now,
    )


def mirror_handoff_file(
    store: SessionStreamStore,
    lease: Lease,
    *,
    profile: str,
    repo_root: Path,
    stream_id: str,
    source_path: Path,
    now: datetime | None = None,
) -> MirrorResult:
    """Append one stable legacy file image without editing or retiring the file."""
    if stream_id != lease.stream_id:
        raise ValueError("explicit mirror stream must match the supplied lease")
    root = repo_root.resolve()
    candidate = source_path if source_path.is_absolute() else root / source_path
    resolved = candidate.resolve(strict=True)
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("legacy handoff source must stay inside the selected repository root") from exc
    first = resolved.read_bytes()
    second = resolved.read_bytes()
    if first != second:
        raise RuntimeError("legacy handoff changed while it was being mirrored; retry the stable image")
    body = first.decode("utf-8")
    source_sha256 = hashlib.sha256(first).hexdigest()
    idempotency_key = f"legacy-mirror:{profile}:{relative}:{source_sha256}"
    entry = store.append_entry(
        lease,
        entry_type=EntryType.STATE,
        body=body,
        idempotency_key=idempotency_key,
        refs=(EntryRef(kind="legacy_source", uri=f"legacy://{relative}?sha256={source_sha256}"),),
        now=now,
    )
    mirror_id = store.record_legacy_mirror(
        lease,
        profile=profile,
        source_path=relative,
        source_sha256=source_sha256,
        source_bytes=len(first),
        entry=entry,
        now=now,
    )
    return MirrorResult(
        profile=profile,
        source_path=relative,
        source_sha256=source_sha256,
        source_bytes=len(first),
        entry=entry,
        mirror_id=mirror_id,
    )
