"""Rank driver handoffs by lane preference, then freshness.

Mint used to walk a fixed name list and keep the first file that existed.
A stale ``INTERIM-DRIVER-HANDOFF.md`` therefore beat a newer
``CLAUDE-DRIVER-HANDOFF.md``. Selection is now:

1. An explicit ``--handoff`` path, when the caller supplies one.
2. The lane's own handoff, when that file exists.
3. Every other existing candidate, newest first.

Freshness is the newest ``## Session YYYY-MM-DD`` heading when the file has
one, and the file mtime otherwise. A later mtime breaks equal session dates.
``*.superseded.md`` is never a candidate.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

# Names the Grok minter already searched, in historical list order. Freshness
# reorders the ones that exist; the tuple itself is not a priority.
GROK_FALLBACK_HANDOFF_NAMES: tuple[str, ...] = (
    "INTERIM-DRIVER-HANDOFF.md",
    "CLAUDE-DRIVER-HANDOFF.md",
    "CODEX-DRIVER-HANDOFF.md",
)

_SESSION_HEADING_RE = re.compile(
    r"^##[ \t]+Session\b.*?(\d{4}-\d{2}-\d{2})",
    re.IGNORECASE | re.MULTILINE,
)
_SESSION_SCAN_CHARS = 200_000


def is_superseded_name(name: str) -> bool:
    """True for the epic folder's ``*.superseded.md`` archive copies."""
    return name.endswith(".superseded.md") or ".superseded." in name


def is_superseded_handoff(path: Path) -> bool:
    return is_superseded_name(path.name)


def newest_session_heading_timestamp(path: Path) -> float | None:
    """UTC timestamp of the newest ``## Session YYYY-MM-DD`` heading, if any."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:_SESSION_SCAN_CHARS]
    except OSError:
        return None
    stamps: list[float] = []
    for match in _SESSION_HEADING_RE.finditer(text):
        try:
            day = datetime.strptime(match.group(1), "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            continue
        stamps.append(day.timestamp())
    if not stamps:
        return None
    return max(stamps)


def freshness_key(path: Path) -> tuple[float, float]:
    """Sort key, higher first: session heading when present, else mtime.

    Equal session dates fall through to mtime so a same-day rewrite still wins.
    """
    mtime = path.stat().st_mtime
    session = newest_session_heading_timestamp(path)
    primary = mtime if session is None else session
    return (primary, mtime)


def rank_handoff_candidates(paths: Sequence[Path], *, preferred: Sequence[str] = ()) -> list[Path]:
    """Existing preferred names, then other existing files newest-first, then missing names."""
    preferred_names = [name for name in preferred if name and not is_superseded_name(name)]
    preferred_index = {name: index for index, name in enumerate(preferred_names)}

    filtered: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        if is_superseded_handoff(path) or path.name in seen:
            continue
        seen.add(path.name)
        filtered.append(path)

    existing_preferred = [path for path in filtered if path.is_file() and path.name in preferred_index]
    existing_preferred.sort(key=lambda path: preferred_index[path.name])

    existing_rest = [path for path in filtered if path.is_file() and path.name not in preferred_index]
    existing_rest.sort(key=freshness_key, reverse=True)

    missing_preferred = [path for path in filtered if not path.is_file() and path.name in preferred_index]
    missing_preferred.sort(key=lambda path: preferred_index[path.name])
    missing_rest = [path for path in filtered if not path.is_file() and path.name not in preferred_index]
    return existing_preferred + existing_rest + missing_preferred + missing_rest


def lane_handoff_candidates(
    repo: Path,
    epic: str,
    names: Sequence[str],
    *,
    preferred: Sequence[str] | None = None,
) -> list[Path]:
    """Ranked handoff paths under ``.claude/<epic>-epic/``."""
    base = repo / ".claude" / f"{epic}-epic"
    preferred_names = [name for name in (preferred or ()) if name and not is_superseded_name(name)]
    ordered: list[str] = []
    seen: set[str] = set()
    for name in [*preferred_names, *names]:
        if not name or is_superseded_name(name) or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return rank_handoff_candidates([base / name for name in ordered], preferred=preferred_names)


def ordered_mint_handoffs(candidates: Sequence[Path], explicit: Path | None) -> list[Path]:
    """``--handoff`` first, then the ranked candidates. Superseded paths drop out."""
    ordered: list[Path] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        if is_superseded_handoff(path):
            return
        resolved = path.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        ordered.append(path)

    if explicit is not None:
        add(explicit)
    for candidate in candidates:
        add(candidate)
    return ordered
