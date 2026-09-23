"""Rank driver handoffs by one freshness date, then an own-lane tiebreak.

Mint used to walk a fixed name list and keep the first file that existed.
A stale ``INTERIM-DRIVER-HANDOFF.md`` therefore beat a newer
``CLAUDE-DRIVER-HANDOFF.md``. Selection is now:

1. An explicit ``--handoff`` path, when the caller supplies one. That path
   applies to the invocation only. Nothing writes it into ``mint_meta.json``.
2. The path a successful mint already recorded, when a later consumer is
   continuing that canary. ``mint_meta.json`` stores ``handoff`` (path or
   null), the selection inputs (``stream_limit`` and ``candidates``), and
   ``handoff_sha256`` as an informational digest. A recorded null is binding:
   consumers return ``(no handoff)`` and do not rank again, even if a handoff
   file appears later. A recorded path is not re-checked against the digest.
   The driver edits the handoff all session, and score stamps into it, so a
   mint-time hash cannot pin the bytes. Material edits after mint → re-mint
   to refresh facts. Score reports that as ``handoff_changed_since_mint``
   (true or false), a notice that does not fail the score. The read that
   actually consumes the recorded file raises
   :class:`RecordedHandoffMissingError` when that read finds the file missing
   or unreadable (``OSError``, ``UnicodeDecodeError``). Absent
   ``mint_meta.json`` is a cold start: consumers select as they did before
   any mint.
3. Otherwise :func:`select_handoff`. Ranking and selection share one read per
   candidate. Mint builds facts and the 10-anchor minimum from that same
   text. A board drawn before mint is a preview of those inputs, including
   ``--stream-limit``. After mint the board reads the recorded inputs.

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
from collections.abc import Callable, Mapping, Sequence
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
# Prefix used to rank candidates and to count the 10-anchor minimum.
# Hydrate, score, diary, and the board read the whole file past this prefix.
# A tail beyond the cap cannot change which path is selected.
SELECTION_TEXT_LIMIT = 120_000
# Historical name. Selection slices to :data:`SELECTION_TEXT_LIMIT`; consumers
# of a recorded path read the full file.
HANDOFF_TEXT_LIMIT = SELECTION_TEXT_LIMIT
NO_HANDOFF_LABEL = "(no handoff)"
REMINT_RULE = "Material edits after mint → re-mint to refresh facts."
STREAM_LIMIT_HELP = (
    "Max stream entries ranked into the anchor set. "
    "Board-before-mint and mint must pass the same value; after mint the board "
    "reads the recorded inputs. " + REMINT_RULE
)


def is_superseded_name(name: str) -> bool:
    """True for the epic folder's ``*.superseded.md`` archive copies."""
    return name.endswith(".superseded.md") or ".superseded." in name


def is_superseded_handoff(path: Path) -> bool:
    return is_superseded_name(path.name)


def is_lane_handoff_name(name: str) -> bool:
    """True for a live ``*-DRIVER-HANDOFF.md`` that is not an archive copy."""
    return name.endswith(_HANDOFF_SUFFIX) and not is_superseded_name(name)


def _session_date(text: str) -> date | None:
    """Newest ``## Session`` date inside the selection prefix."""
    found: list[date] = []
    for match in _SESSION_HEADING_RE.finditer(text[:SELECTION_TEXT_LIMIT]):
        try:
            found.append(datetime.strptime(match.group(1), "%Y-%m-%d").date())
        except ValueError:
            continue
    if not found:
        return None
    return max(found)


def newest_session_heading_date(path: Path) -> date | None:
    """Newest ``## Session YYYY-MM-DD`` heading date, if the file has one."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return _session_date(text)


def freshness_date(
    path: Path, *, text: str | None = None, loaded: bool = False
) -> tuple[bool, date]:
    """``(dated, date)``. Dated headings outrank every undated mtime date.

    ``loaded=True`` uses ``text`` from the selection read and does not open
    the file again.
    """
    session = _session_date(text or "") if loaded else newest_session_heading_date(path)
    if session is not None:
        return (True, session)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0
    return (False, datetime.fromtimestamp(mtime, UTC).date())


def _rank_key(
    path: Path,
    preferred_index: dict[str, int],
    *,
    text: str | None = None,
    loaded: bool = False,
) -> tuple[int, int, int, float]:
    """Higher sorts first: dated flag, freshness date, own-lane bias, mtime."""
    dated, day = freshness_date(path, text=text, loaded=loaded)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        mtime = 0.0
    own_bias = (
        len(preferred_index) - preferred_index[path.name] if path.name in preferred_index else 0
    )
    return (int(dated), day.toordinal(), own_bias, mtime)


def rank_handoff_candidates(
    paths: Sequence[Path],
    *,
    preferred: Sequence[str] = (),
    texts: Mapping[Path, str | None] | None = None,
) -> list[Path]:
    """Existing files by freshness, own-lane only tying a date, then missing names.

    Missing preferred names stay at the head of the missing tail so an empty
    directory still reports the lane's own filename first. When ``texts`` is
    provided, freshness comes from that mapping and this function does not
    read the files again.
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

    def sort_key(path: Path) -> tuple[int, int, int, float]:
        if texts is None:
            return _rank_key(path, preferred_index)
        return _rank_key(path, preferred_index, text=texts.get(path), loaded=True)

    existing.sort(key=sort_key, reverse=True)

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


@dataclass(frozen=True)
class LoadedCandidate:
    """One candidate and the only text ranking and selection may use for it."""

    path: Path
    text: str | None


def read_candidate_text(path: Path) -> str | None:
    """Full UTF-8 text of one candidate, or None when it cannot be read.

    Ranking and :func:`select_handoff` share this string. A later rewrite of
    the file must not be read again for that selection. ``None`` means missing
    or unreadable; selection skips the candidate. The recorded-file consumer
    read is :func:`read_consumed_handoff`, which raises instead of skipping.
    """
    try:
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def load_and_rank_candidates(
    repo: Path,
    epic: str,
    names: Sequence[str],
    *,
    preferred: Sequence[str] | None = None,
) -> list[LoadedCandidate]:
    """Read each candidate once, then rank from that text.

    Session dates and the anchor count both use
    ``text[:SELECTION_TEXT_LIMIT]`` from this read. Mint facts are built from
    the same string.
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
    paths = [base / name for name in ordered]
    texts: dict[Path, str | None] = {}
    for path in paths:
        if path.is_file():
            texts[path] = read_candidate_text(path)
    ranked = rank_handoff_candidates(paths, preferred=preferred_names, texts=texts)
    return [LoadedCandidate(path=path, text=texts.get(path)) for path in ranked]


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
    own-lane tiebreak, not a rank above a newer file. The read behind this
    ranking is the one :func:`load_and_rank_candidates` returns.
    """
    return [
        item.path
        for item in load_and_rank_candidates(repo, epic, names, preferred=preferred)
    ]


def chosen_handoff_path(candidates: Sequence[Path]) -> Path | None:
    """First existing ranked candidate. Does not rank by itself."""
    for path in candidates:
        if path.is_file() and not is_superseded_handoff(path):
            return path
    return None


class RecordedHandoffMissingError(RuntimeError):
    """The consumed read of a mint-recorded handoff found it missing or unreadable."""


class NoHandoff:
    """Mint recorded that no handoff file was selected. Binding until re-mint."""

    def __repr__(self) -> str:
        return NO_HANDOFF_LABEL


NO_HANDOFF = NoHandoff()


def text_sha256(text: str) -> str:
    """sha256 of Unicode text. Informational at mint; not a content pin."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_handoff_text(path: Path) -> str:
    """Strict UTF-8 read of the whole file.

    ``OSError`` (including ``PermissionError``) and ``UnicodeDecodeError``
    propagate. Selection must prefer :func:`read_candidate_text` so a candidate
    is skipped. A consumer of a recorded path must use
    :func:`read_consumed_handoff`, which turns those errors into
    :class:`RecordedHandoffMissingError`.
    """
    return path.read_text(encoding="utf-8")


def handoff_changed_since_mint(recorded_sha: object, current_text: str) -> bool:
    """Whether the living file differs from the informational mint digest.

    False when mint recorded no digest (no handoff, or a record without one).
    A true result is a notice. Material edits after mint → re-mint to refresh
    facts.
    """
    if not isinstance(recorded_sha, str) or not recorded_sha:
        return False
    return text_sha256(current_text) != recorded_sha


@dataclass(frozen=True)
class HandoffSelection:
    """One immutable pass over the candidate files.

    ``path`` is None when the stream alone supplied the anchors (``reason``
    is ``(no handoff)``) or when every candidate fell short (``reason`` is
    empty). ``text`` is the selection prefix that was measured — downstream
    fact building uses it and does not read the file again. ``sha256`` is an
    informational digest of the full file text from that same read, or None
    when no file was selected.
    """

    path: Path | None
    text: str
    sha256: str | None
    anchor_count: int
    reason: str
    attempts: tuple[tuple[str, int, int, int], ...]


def _candidate_cache(
    candidates: Sequence[LoadedCandidate | Path],
) -> tuple[list[Path], dict[Path, str | None]]:
    """Paths in rank order, plus text already read for each resolved path."""
    paths: list[Path] = []
    cache: dict[Path, str | None] = {}
    for item in candidates:
        if isinstance(item, LoadedCandidate):
            paths.append(item.path)
            cache[item.path.resolve()] = item.text
        else:
            paths.append(item)
    return paths, cache


def select_handoff(
    *,
    repo: Path,
    candidates: Sequence[LoadedCandidate | Path],
    measure: Callable[[str, str], tuple[int, int, int]],
    explicit: Path | None = None,
    min_anchors: int = 10,
) -> HandoffSelection:
    """First handoff whose selection prefix yields ``min_anchors``.

    ``candidates`` is already freshness-ranked from one read each. Pass
    :class:`LoadedCandidate` so this function does not read those files
    again. A bare path is read once here. ``explicit`` (``--handoff``) goes
    first and is not written into ``mint_meta.json`` by this function.
    ``measure(text, label)`` returns ``(anchors, next, hands-off)`` and must
    not read the file. Anchor counting uses ``text[:SELECTION_TEXT_LIMIT]``.
    A candidate that cannot be read is skipped. When no file exists, the
    empty text is measured once under ``(no handoff)``.
    """
    raw_paths, cache = _candidate_cache(candidates)
    ordered = ordered_mint_handoffs(raw_paths, explicit)
    considered: list[Path] = []
    for path in ordered:
        key = path.resolve()
        if key not in cache:
            cache[key] = read_candidate_text(path)
        if path.is_file() or cache[key] is not None:
            considered.append(path)
    sources: list[tuple[Path | None, str]] = (
        [(path, display_repo_path(repo, path)) for path in considered]
        if considered
        else [(None, NO_HANDOFF_LABEL)]
    )
    attempts: list[tuple[str, int, int, int]] = []
    for path, rel in sources:
        if path is None:
            full = ""
        else:
            full = cache.get(path.resolve())
            if full is None:
                attempts.append((rel, 0, 0, 0))
                continue
        prefix = full[:SELECTION_TEXT_LIMIT]
        anchors, next_n, hands_n = measure(prefix, rel)
        attempts.append((rel, anchors, next_n, hands_n))
        if anchors >= min_anchors:
            digest = None if path is None else text_sha256(full)
            return HandoffSelection(
                path=path,
                text=prefix,
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


def _missing_recorded(path: Path, meta_path: Path) -> RecordedHandoffMissingError:
    return RecordedHandoffMissingError(
        f"recorded mint handoff missing: {path} (recorded in {meta_path}); "
        "re-mint the canary — consumers must not re-rank handoffs"
    )


def _unreadable_recorded(path: Path, meta_path: Path, exc: BaseException) -> RecordedHandoffMissingError:
    return RecordedHandoffMissingError(
        f"recorded mint handoff unreadable: {path} ({type(exc).__name__}: {exc}); "
        f"recorded in {meta_path}; re-mint the canary — consumers must not re-rank handoffs"
    )


def read_consumed_handoff(path: Path, *, meta_path: Path) -> str:
    """Read the whole recorded file. This is the read that fails closed.

    Missing, superseded, ``OSError`` (including ``PermissionError``), and
    ``UnicodeDecodeError`` raise :class:`RecordedHandoffMissingError`. Callers
    must re-raise that error past broad handlers. The selection cap does not
    apply here.
    """
    try:
        if is_superseded_handoff(path) or not path.is_file():
            raise _missing_recorded(path, meta_path)
        return path.read_text(encoding="utf-8")
    except RecordedHandoffMissingError:
        raise
    except (OSError, UnicodeDecodeError) as exc:
        raise _unreadable_recorded(path, meta_path, exc) from exc


def recorded_mint_handoff(
    repo: Path, epic: str, out_dir: Path | None = None
) -> Path | NoHandoff | None:
    """Path a successful mint already recorded. Does not read that file.

    Returns None only when ``mint_meta.json`` is absent (no mint yet — cold
    start may select). Returns :data:`NO_HANDOFF` when the mint recorded a
    null path: that is binding, and a handoff file that appears later is not
    selected. A recorded path is returned without a content check. The
    consumer's own read uses :func:`read_consumed_handoff` and raises
    :class:`RecordedHandoffMissingError` when that read finds the file missing
    or unreadable. ``handoff_sha256`` is informational and is not compared.
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
    return path


def display_repo_path(repo: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def handoff_binding_line(*, preview: bool) -> str:
    """Board line: a pre-mint preview, or the path mint already recorded."""
    if preview:
        return (
            "**Handoff binding:** preview (not minted). "
            "Mint with the same --stream-limit to record this path. " + REMINT_RULE
        )
    return "**Handoff binding:** recorded path. " + REMINT_RULE


def board_handoff_view(
    repo: Path,
    epic: str,
    select: Callable[[], HandoffSelection],
    *,
    out_dir: Path | None = None,
) -> tuple[str, bool]:
    """``(label, preview)`` for a cold-start board.

    ``select`` runs only when mint has not already recorded a selection, and
    it must be the same :func:`select_handoff` mint runs, including the same
    ``--stream-limit``. That result is a preview. A recorded null is
    ``(no handoff)`` and does not select again. A recorded path is consumed
    with :func:`read_consumed_handoff`; missing or unreadable bytes raise
    :class:`RecordedHandoffMissingError`. Preview is false once mint has
    recorded a selection.
    """
    recorded = recorded_mint_handoff(repo, epic, out_dir)
    if isinstance(recorded, NoHandoff):
        return NO_HANDOFF_LABEL, False
    if isinstance(recorded, Path):
        read_consumed_handoff(recorded, meta_path=_mint_meta_path(repo, epic, out_dir))
        return display_repo_path(repo, recorded), False
    chosen = select()
    if chosen.path is None:
        return NO_HANDOFF_LABEL, True
    return display_repo_path(repo, chosen.path), True


def board_handoff_rel(
    repo: Path,
    epic: str,
    select: Callable[[], HandoffSelection],
    *,
    out_dir: Path | None = None,
) -> str:
    """Cold-start board label. See :func:`board_handoff_view`."""
    label, _preview = board_handoff_view(repo, epic, select, out_dir=out_dir)
    return label


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
