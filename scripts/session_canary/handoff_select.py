"""Rank driver handoffs by one freshness date, then an own-lane tiebreak.

Mint used to walk a fixed name list and keep the first file that existed.
A stale ``INTERIM-DRIVER-HANDOFF.md`` therefore beat a newer
``CLAUDE-DRIVER-HANDOFF.md``. Selection is now:

1. An explicit ``--handoff`` path, when the caller supplies one.
2. The file a successful mint already recorded, when a later consumer is
   continuing that canary. Consumers must pass that path through. They must
   not rank again: when ``mint_meta.json`` records a file that is gone or
   unreadable, :func:`recorded_mint_handoff` raises
   :class:`RecordedHandoffMissingError` instead of returning None.
3. Otherwise the candidate the shared anchor-yield selection picks. Mint and
   the cold-start board both run that one selection, so a handoff too short
   to yield 10 anchors is skipped identically in both places. Freshness ranks
   the candidates fed into it; own-lane is only a tiebreak.

Freshness is a single calendar date per file, never a mix of a session
timestamp and an mtime:

* When the file has a ``## Session YYYY-MM-DD`` heading, freshness is the
  newest of those heading dates.
* When it has none, freshness is the file mtime's UTC date.
* Every undated file ranks below every dated file. An undated file can win
  only when no candidate has a dated heading.
* On an equal freshness date, the lane's own handoff wins. It never takes
  first place over a newer date.
* A later mtime breaks a tie that the date and the own-lane flag do not.

``*.superseded.md`` is never a candidate. Every lane handoff name that exists
in the epic directory is a candidate, including ``GROK-DRIVER-HANDOFF.md``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime
from pathlib import Path

# Every lane handoff the selector knows by name. A file of this shape that
# exists in the epic directory is included even when a caller omits it.
LANE_HANDOFF_NAMES: tuple[str, ...] = (
    "GROK-DRIVER-HANDOFF.md",
    "CODEX-DRIVER-HANDOFF.md",
    "GEMINI-DRIVER-HANDOFF.md",
    "KIMI-DRIVER-HANDOFF.md",
    "GLM-DRIVER-HANDOFF.md",
    "INTERIM-DRIVER-HANDOFF.md",
    "CLAUDE-DRIVER-HANDOFF.md",
)

# Historical alias. Freshness ranks the names that exist; the tuple is not a priority.
GROK_FALLBACK_HANDOFF_NAMES: tuple[str, ...] = LANE_HANDOFF_NAMES

_HANDOFF_SUFFIX = "-DRIVER-HANDOFF.md"
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


def is_lane_handoff_name(name: str) -> bool:
    """True for a live ``*-DRIVER-HANDOFF.md`` that is not an archive copy."""
    return name.endswith(_HANDOFF_SUFFIX) and not is_superseded_name(name)


def newest_session_heading_date(path: Path) -> date | None:
    """Newest ``## Session YYYY-MM-DD`` heading date, if the file has one."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:_SESSION_SCAN_CHARS]
    except OSError:
        return None
    found: list[date] = []
    for match in _SESSION_HEADING_RE.finditer(text):
        try:
            found.append(datetime.strptime(match.group(1), "%Y-%m-%d").date())
        except ValueError:
            continue
    if not found:
        return None
    return max(found)


def freshness_date(path: Path) -> tuple[bool, date]:
    """``(dated, date)``. Dated headings outrank every undated mtime date."""
    session = newest_session_heading_date(path)
    if session is not None:
        return (True, session)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0
    return (False, datetime.fromtimestamp(mtime, UTC).date())


def _rank_key(path: Path, preferred_index: dict[str, int]) -> tuple[int, int, int, float]:
    """Higher sorts first: dated flag, freshness date, own-lane bias, mtime."""
    dated, day = freshness_date(path)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    own_bias = (
        len(preferred_index) - preferred_index[path.name] if path.name in preferred_index else 0
    )
    return (int(dated), day.toordinal(), own_bias, mtime)


def rank_handoff_candidates(paths: Sequence[Path], *, preferred: Sequence[str] = ()) -> list[Path]:
    """Existing files by freshness, own-lane only tying a date, then missing names.

    Missing preferred names stay at the head of the missing tail so an empty
    directory still reports the lane's own filename first.
    """
    preferred_names = [name for name in preferred if name and not is_superseded_name(name)]
    preferred_index = {name: index for index, name in enumerate(preferred_names)}

    filtered: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        if is_superseded_handoff(path) or path.name in seen:
            continue
        seen.add(path.name)
        filtered.append(path)

    existing = [path for path in filtered if path.is_file()]
    existing.sort(key=lambda path: _rank_key(path, preferred_index), reverse=True)

    missing_preferred = [path for path in filtered if not path.is_file() and path.name in preferred_index]
    missing_preferred.sort(key=lambda path: preferred_index[path.name])
    missing_rest = [path for path in filtered if not path.is_file() and path.name not in preferred_index]
    missing_rest.sort(key=lambda path: path.name)
    return existing + missing_preferred + missing_rest


def _discover_handoff_names(base: Path) -> list[str]:
    if not base.is_dir():
        return []
    names: list[str] = []
    try:
        entries = list(base.iterdir())
    except OSError:
        return []
    for path in entries:
        if path.is_file() and is_lane_handoff_name(path.name):
            names.append(path.name)
    names.sort()
    return names


def lane_handoff_candidates(
    repo: Path,
    epic: str,
    names: Sequence[str],
    *,
    preferred: Sequence[str] | None = None,
) -> list[Path]:
    """Ranked handoff paths under ``.claude/<epic>-epic/``.

    The candidate set is every known lane handoff name plus every
    ``*-DRIVER-HANDOFF.md`` that exists in the directory. ``preferred`` is the
    own-lane tiebreak, not a rank above a newer file.
    """
    base = repo / ".claude" / f"{epic}-epic"
    preferred_names = [name for name in (preferred or ()) if name and not is_superseded_name(name)]
    ordered: list[str] = []
    seen: set[str] = set()
    for name in [*preferred_names, *names, *LANE_HANDOFF_NAMES, *_discover_handoff_names(base)]:
        if not name or is_superseded_name(name) or not is_lane_handoff_name(name) or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return rank_handoff_candidates([base / name for name in ordered], preferred=preferred_names)


def chosen_handoff_path(candidates: Sequence[Path]) -> Path | None:
    """First existing ranked candidate. Does not rank by itself."""
    for path in candidates:
        if path.is_file() and not is_superseded_handoff(path):
            return path
    return None


class RecordedHandoffMissingError(RuntimeError):
    """A mint-recorded handoff is gone or unreadable; consumers must not re-rank."""


def recorded_mint_handoff(repo: Path, epic: str, out_dir: Path | None = None) -> Path | None:
    """Handoff path a successful mint already selected.

    Returns None only when no mint selection was recorded. When
    ``mint_meta.json`` exists but cannot be read, or the recorded file is
    gone or superseded, raise :class:`RecordedHandoffMissingError` naming the
    recorded path — falling back to a fresh ranking would let score/board
    drift from the minted canary.
    """
    meta_path = (out_dir if out_dir is not None else repo / ".claude" / f"{epic}-epic" / "canary") / "mint_meta.json"
    if not meta_path.is_file():
        return None
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecordedHandoffMissingError(
            f"recorded mint selection unreadable: {meta_path} ({exc}); "
            "re-mint the canary — consumers must not re-rank handoffs"
        ) from exc
    raw = payload.get("handoff") if isinstance(payload, dict) else None
    if not isinstance(raw, str) or not raw.strip() or raw == "(no handoff)":
        return None
    path = Path(raw)
    if not path.is_absolute():
        path = repo / path
    if not path.is_file() or is_superseded_handoff(path):
        raise RecordedHandoffMissingError(
            f"recorded mint handoff missing: {path} (recorded in {meta_path}); "
            "re-mint the canary — consumers must not re-rank handoffs"
        )
    return path


def display_repo_path(repo: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def board_handoff_rel(
    repo: Path,
    epic: str,
    select: Callable[[], Path | None],
    *,
    fallback_name: str,
) -> str:
    """Cold-start board path. A recorded mint selection is returned as-is.

    ``select`` runs only when mint has not already selected a file, and it
    must be the same anchor-yield selection mint runs, so the board cannot
    name a handoff mint would skip. A recorded file that has gone missing
    raises :class:`RecordedHandoffMissingError` instead of re-ranking.
    """
    recorded = recorded_mint_handoff(repo, epic)
    if recorded is not None:
        return display_repo_path(repo, recorded)
    chosen = select()
    if chosen is None:
        return f".claude/{epic}-epic/{fallback_name}"
    return display_repo_path(repo, chosen)


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
