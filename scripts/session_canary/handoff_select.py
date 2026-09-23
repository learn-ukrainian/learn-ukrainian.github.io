"""Rank driver handoffs by one freshness date, then an own-lane tiebreak.

Mint used to walk a fixed name list and keep the first file that existed.
A stale ``INTERIM-DRIVER-HANDOFF.md`` therefore beat a newer
``CLAUDE-DRIVER-HANDOFF.md``. Selection is now:

1. An explicit ``--handoff`` path, when the caller supplies one.
2. The selection a successful mint already recorded, when a later consumer is
   continuing that canary. ``mint_meta.json`` stores ``handoff`` (path or
   null) and ``handoff_sha256`` (digest or null). A recorded null is binding:
   consumers return ``(no handoff)`` and do not rank again, even if a handoff
   file appears later. A recorded path is read once and its sha256 is compared
   with the record. Missing, unreadable, or changed content raises
   :class:`RecordedHandoffMissingError`. Absent ``mint_meta.json`` is a cold
   start: consumers select as they did before any mint.
3. Otherwise :func:`select_handoff`. It reads each candidate once and returns
   that text. Mint and every cold-start board call it with the same inputs.
   Freshness ranks the candidates fed into it; own-lane is only a tiebreak.

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

import hashlib
import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
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
# Same window mint validates and later resolvers hash. A longer tail is not
# part of the recorded text.
HANDOFF_TEXT_LIMIT = 120_000
NO_HANDOFF_LABEL = "(no handoff)"


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
    """A mint-recorded handoff is gone, unreadable, or no longer the recorded bytes."""


class NoHandoff:
    """Mint recorded that no handoff file was selected. Binding until re-mint."""

    def __repr__(self) -> str:
        return NO_HANDOFF_LABEL


NO_HANDOFF = NoHandoff()


def text_sha256(text: str) -> str:
    """sha256 of the exact Unicode text a selector validated."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_handoff_text(path: Path) -> str:
    """Strict UTF-8 read of the text selection and verification both hash.

    ``OSError`` (including ``PermissionError``) and ``UnicodeDecodeError``
    propagate. Callers that are still choosing a candidate may skip the file;
    callers holding a recorded path must turn those into
    :class:`RecordedHandoffMissingError`.
    """
    return path.read_text(encoding="utf-8")[:HANDOFF_TEXT_LIMIT]


@dataclass(frozen=True)
class HandoffSelection:
    """One immutable pass over the candidate files.

    ``path`` is None when the stream alone supplied the anchors (``reason``
    is ``(no handoff)``) or when every candidate fell short (``reason`` is
    empty). ``text`` is the exact string that was measured — downstream fact
    building uses it and does not read the file again. ``sha256`` is None
    when no file was selected.
    """

    path: Path | None
    text: str
    sha256: str | None
    anchor_count: int
    reason: str
    attempts: tuple[tuple[str, int, int, int], ...]


def select_handoff(
    *,
    repo: Path,
    candidates: Sequence[Path],
    measure: Callable[[str, str], tuple[int, int, int]],
    explicit: Path | None = None,
    min_anchors: int = 10,
) -> HandoffSelection:
    """First handoff whose text yields ``min_anchors``, read once.

    ``candidates`` is already freshness-ranked; ``explicit`` (``--handoff``)
    goes first. ``measure(text, label)`` returns ``(anchors, next, hands-off)``
    and must not read the file. A candidate that cannot be read is skipped.
    When no file exists, the empty text is measured once under
    ``(no handoff)``.
    """
    ordered = ordered_mint_handoffs(list(candidates), explicit)
    existing = [path for path in ordered if path.is_file()]
    sources: list[tuple[Path | None, str]] = (
        [(path, display_repo_path(repo, path)) for path in existing]
        if existing
        else [(None, NO_HANDOFF_LABEL)]
    )
    attempts: list[tuple[str, int, int, int]] = []
    for path, rel in sources:
        if path is None:
            text = ""
        else:
            try:
                text = read_handoff_text(path)
            except (OSError, UnicodeDecodeError):
                attempts.append((rel, 0, 0, 0))
                continue
        anchors, next_n, hands_n = measure(text, rel)
        attempts.append((rel, anchors, next_n, hands_n))
        if anchors >= min_anchors:
            digest = None if path is None else text_sha256(text)
            return HandoffSelection(
                path=path,
                text=text,
                sha256=digest,
                anchor_count=anchors,
                reason=rel,
                attempts=tuple(attempts),
            )
    best = max((anchors for _rel, anchors, _next_n, _hands_n in attempts), default=0)
    return HandoffSelection(
        path=None,
        text="",
        sha256=None,
        anchor_count=best,
        reason="",
        attempts=tuple(attempts),
    )


def _mint_meta_path(repo: Path, epic: str, out_dir: Path | None) -> Path:
    base = out_dir if out_dir is not None else repo / ".claude" / f"{epic}-epic" / "canary"
    return base / "mint_meta.json"


def _verify_recorded_file(path: Path, recorded_sha: object, meta_path: Path) -> Path:
    """Read ``path`` once and require its sha256 to match the mint record."""
    if is_superseded_handoff(path):
        raise RecordedHandoffMissingError(
            f"recorded mint handoff missing: {path} (recorded in {meta_path}); "
            "re-mint the canary — consumers must not re-rank handoffs"
        )
    try:
        if not path.is_file():
            raise RecordedHandoffMissingError(
                f"recorded mint handoff missing: {path} (recorded in {meta_path}); "
                "re-mint the canary — consumers must not re-rank handoffs"
            )
        text = read_handoff_text(path)
    except RecordedHandoffMissingError:
        raise
    except (OSError, UnicodeDecodeError) as exc:
        raise RecordedHandoffMissingError(
            f"recorded mint handoff unreadable: {path} ({type(exc).__name__}: {exc}); "
            f"recorded in {meta_path}; re-mint the canary — consumers must not re-rank handoffs"
        ) from exc
    if not isinstance(recorded_sha, str) or not recorded_sha:
        raise RecordedHandoffMissingError(
            f"recorded mint handoff has no sha256: {path} (recorded in {meta_path}); "
            "re-mint the canary — consumers must not re-rank handoffs"
        )
    actual = text_sha256(text)
    if actual != recorded_sha:
        raise RecordedHandoffMissingError(
            f"recorded mint handoff changed: {path} (sha256 mismatch, recorded in {meta_path}); "
            "re-mint the canary — consumers must not re-rank handoffs"
        )
    return path


def recorded_mint_handoff(
    repo: Path, epic: str, out_dir: Path | None = None
) -> Path | NoHandoff | None:
    """Selection a successful mint already recorded.

    Returns None only when ``mint_meta.json`` is absent (no mint yet — cold
    start may select). Returns :data:`NO_HANDOFF` when the mint recorded a
    null path: that is binding, and a handoff file that appears later is not
    selected. A recorded path is returned only after its bytes match
    ``handoff_sha256``. Gone, unreadable, or changed content raises
    :class:`RecordedHandoffMissingError` naming the path and the cause.
    """
    meta_path = _mint_meta_path(repo, epic, out_dir)
    if not meta_path.is_file():
        return None
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecordedHandoffMissingError(
            f"recorded mint selection unreadable: {meta_path} ({exc}); "
            "re-mint the canary — consumers must not re-rank handoffs"
        ) from exc
    if not isinstance(payload, dict) or "handoff" not in payload:
        raise RecordedHandoffMissingError(
            f"recorded mint selection unreadable: {meta_path} (no handoff field); "
            "re-mint the canary — consumers must not re-rank handoffs"
        )
    raw = payload.get("handoff")
    if raw is None or raw == NO_HANDOFF_LABEL or (isinstance(raw, str) and not raw.strip()):
        return NO_HANDOFF
    if not isinstance(raw, str):
        raise RecordedHandoffMissingError(
            f"recorded mint selection unreadable: {meta_path} (handoff is not a path or null); "
            "re-mint the canary — consumers must not re-rank handoffs"
        )
    path = Path(raw)
    if not path.is_absolute():
        path = repo / path
    return _verify_recorded_file(path, payload.get("handoff_sha256"), meta_path)


def display_repo_path(repo: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def board_handoff_rel(
    repo: Path,
    epic: str,
    select: Callable[[], HandoffSelection],
) -> str:
    """Cold-start board label. A recorded mint selection is returned as-is.

    ``select`` runs only when mint has not already recorded a selection, and
    it must be the same :func:`select_handoff` mint runs, including the stream
    anchors. No file from that call — including a stream that stands alone —
    is ``(no handoff)``. A recorded null is the same label and does not select
    again. A recorded file that is missing, unreadable, or changed raises
    :class:`RecordedHandoffMissingError`.
    """
    recorded = recorded_mint_handoff(repo, epic)
    if isinstance(recorded, NoHandoff):
        return NO_HANDOFF_LABEL
    if isinstance(recorded, Path):
        return display_repo_path(repo, recorded)
    chosen = select()
    if chosen.path is None:
        return NO_HANDOFF_LABEL
    return display_repo_path(repo, chosen.path)


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
