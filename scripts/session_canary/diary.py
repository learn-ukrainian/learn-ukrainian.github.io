"""Driver-handoff diary helpers for Grok lane canary recovery.

The dual-write handoff file is the human SSOT that survives compact/rot.
This module keeps stamps mintable (Next Drive / Hands-off bullets) and
emits a fixed STATE AT HANDBACK block on FAIL or clean close.
"""

from __future__ import annotations

import fcntl
import os
import re
import stat
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path

from scripts.session_canary import handoff_select

DIARY_MARKER = "## 📔 Diary — reverse chrono (newest first)"
NEXT_DRIVE_MARKER = "## Next Drive"
WORKING_SET_MARKER = "## Active Working Set"
HANDS_OFF_MARKER = "## Hands-off"
HANDBACK_MARKER = "## STATE AT HANDBACK"
# Bound for compare-and-replace. Exhaustion raises; it never writes blind.
REWRITE_ATTEMPTS = 8


class HandoffRewriteConflictError(RuntimeError):
    """Compare-and-replace could not commit without dropping a newer version."""


_LAST_STAMP_RE = re.compile(
    r"^(\*\*Last diary stamp:\*\*)\s*.+$",
    re.MULTILINE,
)


def utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")


def resolve_handoff_path(
    repo: Path,
    epic: str,
    override: str | Path | None = None,
    preferred: list[str] | None = None,
    *,
    out_dir: Path | None = None,
) -> Path | handoff_select.NoHandoff:
    """Same selection as mint: explicit path, else the recorded mint file, else freshness.

    Own-lane (``preferred``) ties an equal freshness date. It does not outrank
    a newer handoff. A recorded mint path is returned without ranking again
    and without a content check. A recorded null is
    :data:`handoff_select.NO_HANDOFF` and is not re-selected. Absent
    ``mint_meta.json`` still ranks by freshness. An explicit override is this
    call only. The read that consumes a recorded file raises
    :class:`handoff_select.RecordedHandoffMissingError` when that file is
    missing or unreadable.
    """
    if override:
        p = Path(override)
        return p if p.is_absolute() else (repo / p)

    recorded = handoff_select.recorded_mint_handoff(repo, epic, out_dir)
    if isinstance(recorded, handoff_select.NoHandoff):
        return recorded
    if isinstance(recorded, Path):
        return recorded
    ranked = handoff_select.lane_handoff_candidates(
        repo,
        epic,
        handoff_select.LANE_HANDOFF_NAMES,
        preferred=list(preferred or []),
    )
    chosen = handoff_select.chosen_handoff_path(ranked)
    if chosen is not None:
        return chosen
    fallback = next(iter(preferred or ()), "INTERIM-DRIVER-HANDOFF.md")
    return repo / ".claude" / f"{epic}-epic" / fallback


def _ensure_section(text: str, heading: str, default_body: str) -> str:
    title = heading.lstrip("#").strip()
    if heading in text or re.search(
        rf"^##\s+.*{re.escape(title)}", text, re.MULTILINE | re.IGNORECASE
    ):
        return text
    return text.rstrip() + "\n\n" + heading + "\n" + default_body.rstrip() + "\n"


def ensure_diary_skeleton(text: str, *, epic: str, stream_id: str) -> str:
    """Ensure mintable sections exist (idempotent)."""
    if not text.strip():
        text = (
            f"# Driver handoff — epic `{epic}` / stream `{stream_id}`\n\n"
            f"> **Handoff = DIARY.** Stamp after every batch. Mint canary only after load.\n\n"
            f"**Last diary stamp:** never\n\n"
        )
    if "**Last diary stamp:**" not in text:
        # Insert after first heading
        lines = text.splitlines()
        if lines and lines[0].startswith("#"):
            lines.insert(1, "")
            lines.insert(2, "**Last diary stamp:** never")
            text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
        else:
            text = "**Last diary stamp:** never\n\n" + text

    text = _ensure_section(
        text,
        NEXT_DRIVE_MARKER,
        "1. (update after each batch — short bullets only; canary mints these)\n",
    )
    text = _ensure_section(
        text,
        WORKING_SET_MARKER,
        "- (promote load-bearing mid-flight facts here before compact risk)\n",
    )
    # Accept either "## Hands-off" or "## Hands-off / Out of scope"
    if not re.search(r"^##\s+Hands-off", text, re.MULTILINE | re.IGNORECASE):
        text = text.rstrip() + f"\n\n{HANDS_OFF_MARKER}\n- (lane boundaries)\n"
    if DIARY_MARKER not in text and not re.search(r"^##\s+.*Diary", text, re.MULTILINE | re.IGNORECASE):
        text = text.rstrip() + f"\n\n{DIARY_MARKER}\n\n"
    if "No secrets" not in text and "no secrets" not in text.lower():
        # Insert once near top (after title / stamp).
        lines = text.splitlines()
        insert_at = 0
        for i, line in enumerate(lines[:12]):
            if line.startswith("#"):
                insert_at = i + 1
                break
        banner = "> **No secrets / private teacher PII / API keys** in this file."
        lines.insert(insert_at, "")
        lines.insert(insert_at + 1, banner)
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return text


def _read_fd(fd: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        block = os.read(fd, 1024 * 1024)
        if not block:
            break
        chunks.append(block)
    return b"".join(chunks)


def _write_fd(fd: int, data: bytes) -> None:
    os.lseek(fd, 0, os.SEEK_SET)
    os.ftruncate(fd, 0)
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError(f"short write to handoff fd {fd}")
        view = view[written:]
    os.fsync(fd)


def _snapshot_path(path: Path) -> tuple[bytes | None, int | None]:
    """Fresh open of ``path``. Content ``None`` means the path is absent.

    The mode is :func:`stat.S_IMODE` (permission bits plus setuid, setgid, and
    sticky). An absent path returns mode ``None`` so creation keeps the
    process umask instead of forcing one.
    """
    try:
        fd = os.open(path, os.O_RDONLY)
    except FileNotFoundError:
        return None, None
    try:
        mode = stat.S_IMODE(os.fstat(fd).st_mode)
        return _read_fd(fd), mode
    finally:
        os.close(fd)


def _write_temp_file(directory: Path, data: bytes, mode: int | None) -> Path:
    """Write ``data`` in ``directory`` so ``os.replace`` stays on one filesystem.

    ``mode`` is the full :func:`stat.S_IMODE` of an existing target, applied
    with ``os.fchmod`` and not reduced to owner/group/other permission bits.
    ``None`` creates the file at ``0o644`` so the process umask applies.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = -1
    tmp: Path | None = None
    committed = False
    try:
        for _ in range(128):
            candidate = directory / f".handoff-{os.urandom(8).hex()}.tmp"
            try:
                fd = os.open(candidate, flags, 0o644)
            except FileExistsError:
                continue
            tmp = candidate
            break
        if tmp is None or fd < 0:
            raise OSError(f"could not create a handoff temp in {directory}")
        _write_fd(fd, data)
        if mode is not None:
            os.fchmod(fd, mode)
        os.fsync(fd)
        committed = True
        return tmp
    finally:
        if fd >= 0:
            os.close(fd)
        if tmp is not None and not committed:
            tmp.unlink(missing_ok=True)


def _missing_recorded(path: Path, recorded_meta: Path) -> handoff_select.RecordedHandoffMissingError:
    return handoff_select.RecordedHandoffMissingError(
        f"recorded mint handoff missing: {path} (recorded in {recorded_meta}); "
        "re-mint the canary — consumers must not re-rank handoffs"
    )


def _unreadable_recorded(
    path: Path, recorded_meta: Path, exc: BaseException
) -> handoff_select.RecordedHandoffMissingError:
    return handoff_select.RecordedHandoffMissingError(
        f"recorded mint handoff unreadable: {path} ({type(exc).__name__}: {exc}); "
        f"recorded in {recorded_meta}; re-mint the canary — consumers must not re-rank handoffs"
    )


def rewrite_handoff_locked(
    path: Path,
    transform: Callable[[str], str],
    *,
    recorded_meta: Path | None = None,
) -> None:
    """Compare-and-replace the handoff by path, for stamp and handback alike.

    Each attempt resolves ``path`` with ``os.path.realpath`` once, reads that
    target, writes the transformed bytes to a temp in the target's directory,
    and ``os.replace`` onto the target only when a second fresh read of that
    same target still matches. A symlink handoff is left in place, still
    pointing at the stamped file. A mismatch deletes the temp and retries.
    After :data:`REWRITE_ATTEMPTS` the function raises
    :class:`HandoffRewriteConflictError` and does not write.

    An existing target keeps its full mode, including setuid, setgid, and
    sticky. An absent target is created at ``0o644`` so the process umask
    applies.

    An exclusive flock on the parent directory serializes cooperating callers
    of this helper across ``os.replace``. The lock is not the safety property:
    a writer that never takes it is caught by the byte comparison.

    Accepted residual: the window between the final comparison and
    ``os.replace`` is not atomic against a non-cooperating editor. The threat
    model is human-speed editing and agent tool edits, not adversarial writers.

    ``recorded_meta`` marks a mint-recorded path: a missing or unreadable file
    raises :class:`handoff_select.RecordedHandoffMissingError` instead of
    creating a replacement.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if recorded_meta is not None and not path.is_file():
        raise _missing_recorded(path, recorded_meta)
    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        fcntl.flock(dir_fd, fcntl.LOCK_EX)
        for _attempt in range(REWRITE_ATTEMPTS):
            if recorded_meta is not None and not path.is_file():
                raise _missing_recorded(path, recorded_meta)
            # Once per attempt: read, compare, and replace this path only.
            # A symlink retarget after this point is the next attempt's read.
            target = Path(os.path.realpath(path))
            try:
                raw, mode = _snapshot_path(target)
            except OSError as exc:
                if recorded_meta is None:
                    raise
                raise _unreadable_recorded(path, recorded_meta, exc) from exc
            if raw is None:
                if recorded_meta is not None:
                    raise _missing_recorded(path, recorded_meta)
                text_bytes = b""
            else:
                text_bytes = raw
            try:
                if recorded_meta is not None:
                    text = text_bytes.decode("utf-8")
                else:
                    text = text_bytes.decode("utf-8", errors="replace")
            except UnicodeDecodeError as exc:
                if recorded_meta is None:
                    raise
                raise _unreadable_recorded(path, recorded_meta, exc) from exc
            updated = transform(text)
            if updated and not updated.endswith("\n"):
                updated += "\n"
            data = updated.encode("utf-8")
            tmp = _write_temp_file(target.parent, data, mode)
            try:
                try:
                    confirm, confirm_mode = _snapshot_path(target)
                except OSError as exc:
                    if recorded_meta is None:
                        raise
                    raise _unreadable_recorded(path, recorded_meta, exc) from exc
                if confirm != raw:
                    continue
                if confirm_mode != mode and confirm_mode is not None:
                    os.chmod(tmp, confirm_mode)
                # Accepted residual: this comparison and os.replace are not atomic
                # against a non-cooperating editor. The threat model is human-speed
                # editing and agent tool edits, not adversarial writers.
                os.replace(tmp, target)
                return
            finally:
                if tmp.exists():
                    tmp.unlink()
        raise HandoffRewriteConflictError(
            f"handoff rewrite lost the compare-and-replace race after {REWRITE_ATTEMPTS} attempts: {path}"
        )
    finally:
        fcntl.flock(dir_fd, fcntl.LOCK_UN)
        os.close(dir_fd)


def append_diary_stamp(
    path: Path,
    *,
    title: str,
    bullets: Sequence[str],
    next_drive: Sequence[str] | None = None,
    working_set: Sequence[str] | None = None,
    stamp: str | None = None,
    recorded_meta: Path | None = None,
) -> str:
    """Prepend a diary entry; optionally replace Next Drive / Active Working Set. Returns stamp used.

    The write is a path compare-and-replace (:func:`rewrite_handoff_locked`).
    ``recorded_meta`` is the mint record when ``path`` is that recorded file:
    the consumed read then raises :class:`handoff_select.RecordedHandoffMissingError`
    if the file is missing or unreadable.
    """
    stamp = stamp or utc_stamp()

    def transform(text: str) -> str:
        text = ensure_diary_skeleton(text, epic=path.parent.name.replace("-epic", ""), stream_id="epic:?")
        if _LAST_STAMP_RE.search(text):
            text = _LAST_STAMP_RE.sub(rf"\1 {stamp}", text, count=1)
        bullet_lines = "\n".join(f"- {b.strip()}" for b in bullets if b and b.strip())
        entry = f"### {stamp} — {title.strip()}\n{bullet_lines}\n\n"
        diary_re = re.compile(
            r"^(##\s+.*Diary[^\n]*\n\n)",
            re.MULTILINE | re.IGNORECASE,
        )
        match = diary_re.search(text)
        text = (
            text[: match.end()] + entry + text[match.end() :]
            if match
            else text.rstrip() + f"\n\n{DIARY_MARKER}\n\n" + entry
        )
        if next_drive is not None:
            text = replace_next_drive_bullets(text, next_drive)
        if working_set is not None:
            text = replace_working_set_bullets(text, working_set)
        return text

    rewrite_handoff_locked(path, transform, recorded_meta=recorded_meta)
    return stamp


def _replace_h2_section_bullets(
    text: str,
    *,
    heading_re: str,
    bullets: Sequence[str],
    numbered: bool,
) -> str:
    """Replace body under a ## heading until the next ## heading."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    matched = False
    while i < len(lines):
        out.append(lines[i])
        if re.match(heading_re, lines[i], re.IGNORECASE):
            matched = True
            i += 1
            while i < len(lines) and not re.match(r"^##\s+", lines[i]):
                i += 1
            for n, b in enumerate(bullets, start=1):
                b = b.strip()
                if not b:
                    continue
                if numbered:
                    if re.match(r"^\d+\.", b):
                        out.append(b + "\n")
                    else:
                        out.append(f"{n}. {b}\n")
                else:
                    if re.match(r"^[-*]\s+", b):
                        out.append(b + "\n")
                    else:
                        out.append(f"- {b}\n")
            out.append("\n")
            continue
        i += 1
    if not matched:
        # Append section so promotion never silently no-ops on old diaries.
        label = "Next Drive" if numbered else "Active Working Set"
        out.append(f"\n## {label}\n")
        for n, b in enumerate(bullets, start=1):
            b = b.strip()
            if not b:
                continue
            if numbered:
                out.append(f"{n}. {b}\n" if not re.match(r"^\d+\.", b) else b + "\n")
            else:
                out.append(f"- {b}\n" if not re.match(r"^[-*]\s+", b) else b + "\n")
        out.append("\n")
    return "".join(out)


def replace_next_drive_bullets(text: str, bullets: Sequence[str]) -> str:
    """Replace content under ## Next Drive until next ## heading."""
    return _replace_h2_section_bullets(
        text,
        heading_re=r"^##\s+Next Drive\b",
        bullets=bullets,
        numbered=True,
    )


def replace_working_set_bullets(text: str, bullets: Sequence[str]) -> str:
    """Replace content under ## Active Working Set until next ## heading."""
    return _replace_h2_section_bullets(
        text,
        heading_re=r"^##\s+Active Working Set\b",
        bullets=bullets,
        numbered=False,
    )


def format_canary_score_line(
    *,
    verdict: str,
    score_line: str,
    context_tokens: int,
    pass_ratio: float,
) -> str:
    tok = f"~{context_tokens} tok" if context_tokens else "tok=n/a"
    # SCORE line from context_canary is like: SCORE 9/10 pass=...
    short = score_line.replace("SCORE ", "").strip() if score_line else verdict
    return f"canary {verdict} {short} @ {tok} (pass-ratio {pass_ratio})"


def format_handback_block(
    *,
    stamp: str,
    epic: str,
    stream_id: str,
    reason: str,
    pins: Sequence[str],
    open_prs: Sequence[str],
    next_drive: Sequence[str],
    hands_off: Sequence[str],
    pending_user: Sequence[str],
    worktrees: Sequence[str],
    canary_line: str,
    notes: Sequence[str] = (),
) -> str:
    def bullets(items: Sequence[str]) -> str:
        items = [i.strip() for i in items if i and i.strip()]
        if not items:
            return "- (none)\n"
        return "".join(f"- {i}\n" for i in items)

    def numbered(items: Sequence[str]) -> str:
        items = [i.strip() for i in items if i and i.strip()]
        if not items:
            return "1. (none)\n"
        out = []
        for n, i in enumerate(items, start=1):
            if re.match(r"^\d+\.", i):
                out.append(i + "\n")
            else:
                out.append(f"{n}. {i}\n")
        return "".join(out)

    return (
        f"{HANDBACK_MARKER} — {stamp}\n\n"
        f"**Epic / stream:** `{epic}` / `{stream_id}`\n"
        f"**Reason:** {reason.strip()}\n"
        f"**Canary:** {canary_line.strip()}\n\n"
        f"### Pins\n{bullets(pins)}"
        f"\n### Open PRs / in flight\n{bullets(open_prs)}"
        f"\n### Next Drive (mintable)\n{numbered(next_drive)}"
        f"\n### Hands-off\n{bullets(hands_off)}"
        f"\n### Pending user\n{bullets(pending_user)}"
        f"\n### Worktrees\n{bullets(worktrees)}"
        f"\n### Notes\n{bullets(notes)}"
        f"\n> Successor: load this block + stream tail, then "
        f"`.venv/bin/python -m scripts.session_canary.grok_lane mint --epic {epic}`.\n"
        f"> Do **not** invent the queue from chat memory alone.\n"
    )


def append_handback(
    path: Path,
    *,
    epic: str,
    stream_id: str,
    reason: str,
    pins: Sequence[str],
    open_prs: Sequence[str],
    next_drive: Sequence[str],
    hands_off: Sequence[str],
    pending_user: Sequence[str],
    worktrees: Sequence[str],
    canary_line: str,
    notes: Sequence[str] = (),
    stamp: str | None = None,
    recorded_meta: Path | None = None,
) -> str:
    """Append STATE AT HANDBACK and a diary stamp. Sync Next Drive bullets.

    The write is a path compare-and-replace (:func:`rewrite_handoff_locked`).
    ``recorded_meta`` fails closed when the recorded file is missing or
    unreadable at this read.
    """
    stamp = stamp or utc_stamp()

    def transform(text: str) -> str:
        text = ensure_diary_skeleton(text, epic=epic, stream_id=stream_id)
        if _LAST_STAMP_RE.search(text):
            text = _LAST_STAMP_RE.sub(rf"\1 {stamp}", text, count=1)
        block = format_handback_block(
            stamp=stamp,
            epic=epic,
            stream_id=stream_id,
            reason=reason,
            pins=pins,
            open_prs=open_prs,
            next_drive=next_drive,
            hands_off=hands_off,
            pending_user=pending_user,
            worktrees=worktrees,
            canary_line=canary_line,
            notes=notes,
        )
        # Keep history: always append a new handback block (never delete prior ones).
        text = text.rstrip() + "\n\n" + block
        text = replace_next_drive_bullets(text, next_drive)
        diary_entry = (
            f"### {stamp} — STATE AT HANDBACK ({reason.strip()})\n"
            f"- {canary_line.strip()}\n"
            f"- Full block under `{HANDBACK_MARKER}` below/above.\n"
            f"- Successor must mint canary after loading this file + stream.\n\n"
        )
        diary_re = re.compile(r"^(##\s+.*Diary[^\n]*\n\n)", re.MULTILINE | re.IGNORECASE)
        match = diary_re.search(text)
        if match:
            text = text[: match.end()] + diary_entry + text[match.end() :]
        else:
            text = text.rstrip() + f"\n\n{DIARY_MARKER}\n\n" + diary_entry
        return text

    rewrite_handoff_locked(path, transform, recorded_meta=recorded_meta)
    return stamp


def try_stream_state_note(stream_id: str, body: str, *, idempotency_key: str) -> bool:
    """Best-effort append stream state under active env lease. Fail-open."""
    try:
        import os

        from agents_extensions.shared.session_streams.db import SessionStreamDatabase
        from agents_extensions.shared.session_streams.hooks import lease_from_environment
        from agents_extensions.shared.session_streams.model import EntryType
        from agents_extensions.shared.session_streams.store import SessionStreamStore

        if not os.environ.get("SESSION_STREAM_LEASE_ID"):
            return False
        store = SessionStreamStore(SessionStreamDatabase())
        lease = lease_from_environment()
        if lease.stream_id != stream_id:
            return False
        store.heartbeat(lease)
        store.append_entry(
            lease,
            entry_type=EntryType.STATE,
            body=body,
            idempotency_key=idempotency_key[:200],
        )
        return True
    except Exception:
        return False


def _section_from_heading(text: str, heading_re: str, stop_res: Sequence[str]) -> str:
    """Return text from a heading match until the next stop heading."""
    m = re.search(heading_re, text, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ""
    start = m.start()
    rest = text[m.end() :]
    end = len(text)
    for stop in stop_res:
        m2 = re.search(stop, rest, re.MULTILINE | re.IGNORECASE)
        if m2:
            end = m.end() + m2.start()
            break
    return text[start:end].strip()


def _recent_diary_stamps(text: str, *, max_stamps: int) -> str:
    """Newest N diary stamp bodies under the Diary heading."""
    m = re.search(r"^##\s+.*Diary[^\n]*\n", text, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ""
    body = text[m.end() :]
    # stop at next top-level ## that is not a stamp
    parts = re.split(r"(?=^###\s+)", body, flags=re.MULTILINE)
    stamps: list[str] = []
    for part in parts:
        if re.match(r"^###\s+", part):
            stamps.append(part.strip())
        if len(stamps) >= max_stamps:
            break
    return "\n\n".join(stamps).strip()


def _latest_handback_block(text: str) -> str:
    """Most recent STATE AT HANDBACK block if present."""
    matches = list(re.finditer(r"^##\s+STATE AT HANDBACK[^\n]*\n", text, re.MULTILINE | re.IGNORECASE))
    if not matches:
        return ""
    m = matches[-1]
    rest = text[m.end() :]
    m2 = re.search(r"^##\s+", rest, re.MULTILINE)
    end = m.end() + (m2.start() if m2 else len(rest))
    return text[m.start() : end].strip()


def approx_tokens(text: str) -> int:
    """Cheap token estimate (chars/4). Deterministic; no external tokenizer."""
    return max(0, (len(text) + 3) // 4)


def build_hydrate_capsule(
    diary_text: str,
    *,
    epic: str,
    stream_id: str,
    stream_tail: str = "",
    max_tokens: int = 1400,
    max_stamps: int = 3,
    stamp_token_cap: int = 250,
    stream_token_cap: int = 300,
) -> tuple[str, dict[str, object]]:
    """Build a Sol Option-D post-compact hydrate capsule (bounded).

    Packs whole sections by priority; drops lowest-priority whole items when
    over budget. Never silently truncates mid-item. Returns (capsule, meta).
    """
    max_tokens = max(200, min(int(max_tokens), 1600))

    session = _section_from_heading(
        diary_text,
        r"^##\s+.*SESSION HANDOFF[^\n]*\n",
        [r"^##\s+📌", r"^##\s+Standing", r"^##\s+.*Diary", r"^##\s+STATE AT HANDBACK"],
    )
    handback = _latest_handback_block(diary_text)
    # Prefer newest handback for identity if session block is stale? Sol order:
    # identity from handback OR session — include handback only if no session,
    # else prefer session as live board and handback only when session missing.
    identity_block = session or handback
    if not identity_block:
        identity_block = (
            f"# HYDRATE — epic `{epic}` / stream `{stream_id}`\n"
            "(no SESSION HANDOFF or STATE AT HANDBACK found — treat as FAIL-visible)\n"
        )

    pins = _section_from_heading(
        diary_text,
        r"^##\s+📌\s*Standing pins[^\n]*\n|^##\s+Standing pins[^\n]*\n",
        [r"^##\s+.*Diary", r"^##\s+STATE AT HANDBACK", r"^##\s+Next Drive"],
    )
    next_drive = _section_from_heading(
        diary_text,
        r"^###\s+Next drive[^\n]*\n|^##\s+Next Drive[^\n]*\n",
        [r"^###\s+", r"^##\s+"],
    )
    hands_off = _section_from_heading(
        diary_text,
        r"^##\s+Hands-off[^\n]*\n",
        [r"^##\s+"],
    )
    stamps = _recent_diary_stamps(diary_text, max_stamps=max_stamps)
    if stamps and approx_tokens(stamps) > stamp_token_cap:
        # drop oldest among selected stamps until under cap
        parts = re.split(r"(?=^###\s+)", stamps, flags=re.MULTILINE)
        kept: list[str] = []
        for part in parts:
            if not part.strip():
                continue
            trial = "\n\n".join([*kept, part.strip()]).strip()
            if approx_tokens(trial) > stamp_token_cap and kept:
                break
            kept.append(part.strip())
        stamps = "\n\n".join(kept).strip()

    stream = (stream_tail or "").strip()
    if stream and approx_tokens(stream) > stream_token_cap:
        # keep header + drop trailing lines whole
        lines = stream.splitlines()
        kept_lines: list[str] = []
        for line in lines:
            trial = "\n".join([*kept_lines, line])
            if approx_tokens(trial) > stream_token_cap and kept_lines:
                break
            kept_lines.append(line)
        stream = "\n".join(kept_lines).strip()

    working_set = _section_from_heading(
        diary_text,
        r"^##\s+Active Working Set[^\n]*\n|^###\s+Active Working Set[^\n]*\n",
        [r"^##\s+", r"^###\s+"],
    )

    # Priority pack: identity → next drive → active working set → pins → hands-off → stamps → stream
    # Canary PASS only proves anchors; this capsule is not full session memory.
    header = (
        f"# HYDRATE CAPSULE (post-compact)\n"
        f"**Epic / stream:** `{epic}` / `{stream_id}`\n"
        f"**Provenance:** diary dual-write + optional stream tail · "
        f"not a new SSOT · max_tokens={max_tokens}\n"
        f"**Protocol:** score canary FROM MEMORY first; hydrate once; "
        f"**then RE-GROUND** (see footer) — do not invent from chat.\n"
        f"**Canary scope:** PASS = durable anchors OK · **not** proof the mid-flight "
        f"working set survived compact.\n"
    )
    sections: list[tuple[str, str]] = [
        ("identity", identity_block),
        ("next_drive", next_drive),
        (
            "working_set",
            f"## Active Working Set (load-bearing; mintable)\n\n{working_set}"
            if working_set
            else "",
        ),
        ("pins", pins),
        ("hands_off", hands_off),
        ("recent_stamps", f"## Recent diary stamps (newest first)\n\n{stamps}" if stamps else ""),
        ("stream_tail", f"## Stream tail (bounded)\n\n{stream}" if stream else ""),
    ]

    # Mandatory re-ground footer: always pack (never drop) so PASS cannot mean blind continue.
    reground = (
        "## RE-GROUND CHECKLIST (mandatory after every compact — canary PASS is not enough)\n\n"
        "1. **Canary PASS** only proves durable anchors (identity / mintable Next Drive / Hands-off).\n"
        "2. Re-read **Next Drive** + **Active Working Set** from this capsule (or diary if missing).\n"
        "3. Open the **active phase receipt** named in Next Drive / Working Set "
        "(private `docs/entire/...` or stream pin) — do not resume from vibe.\n"
        "4. If the open task is **not** spelled in Next Drive or Active Working Set: "
        "**STOP inventing** — stamp dual-write or hand off / re-mint.\n"
        "5. Anything not dual-written before compact is **allowed to have evaporated**.\n"
    )
    # Reserve budget for footer so it is never squeezed out by stamps/stream.
    # Do not re-floor pack_max to 200: that can push final capsule over max_tokens.
    reground_tok = approx_tokens(reground)
    pack_max = max(0, int(max_tokens) - reground_tok)
    pack_char_ceiling = pack_max * 4

    included: list[str] = [header]
    dropped: list[str] = []
    for name, body in sections:
        body = body.strip()
        if not body:
            continue
        trial = "\n\n".join([*included, body]).strip() + "\n"
        if approx_tokens(trial) > pack_max or len(trial) > pack_char_ceiling:
            # Prefer keeping identity even if pack_max is tight; may still fit with footer.
            if name == "identity":
                with_id = "\n\n".join([*included, body, reground]).strip() + "\n"
                if approx_tokens(with_id) <= max_tokens:
                    included.append(body)
                else:
                    dropped.append("identity_truncated")
            else:
                dropped.append(name)
            continue
        included.append(body)

    included.append(reground)

    capsule = "\n\n".join(included).strip() + "\n"
    # Final bound: hard-cap at max_tokens (footer first, then minimal header).
    if approx_tokens(capsule) > max_tokens:
        mini_header = (
            f"# HYDRATE CAPSULE (post-compact)\n"
            f"**Epic / stream:** `{epic}` / `{stream_id}`\n"
            f"**Note:** budget-tight capsule; re-read diary Next Drive + Active Working Set.\n"
        )
        mini_reground = (
            "## RE-GROUND CHECKLIST (mandatory after every compact)\n\n"
            "1. Canary PASS = anchors only.\n"
            "2. Re-read Next Drive + Active Working Set from diary.\n"
            "3. Open active phase receipt; stop inventing if open task missing.\n"
        )
        capsule = "\n\n".join([mini_header, mini_reground]).strip() + "\n"
        # If still over pathological tiny budgets, keep only reground lines that fit.
        while approx_tokens(capsule) > max_tokens and len(capsule) > 80:
            capsule = "\n".join(capsule.splitlines()[:-1]).strip() + "\n"
        dropped = list(dict.fromkeys([*dropped, "budget_tight_minimal_reground"]))
    meta: dict[str, object] = {
        "epic": epic,
        "stream_id": stream_id,
        "max_tokens": max_tokens,
        "approx_tokens": approx_tokens(capsule),
        "chars": len(capsule),
        "dropped_sections": dropped,
        "has_identity": bool(session or handback),
        "has_next_drive": bool(next_drive),
        "has_working_set": bool(working_set),
        "has_reground_checklist": True,
        "capsule_sha256": __import__("hashlib").sha256(capsule.encode("utf-8")).hexdigest()[:16],
    }
    if not meta["has_identity"] or not meta["has_next_drive"]:
        meta["visible_gap"] = (
            "missing SESSION HANDOFF/STATE AT HANDBACK and/or Next Drive — "
            "do not invent queue; fix diary before driving"
        )
    return capsule, meta


def try_stream_tail_text(stream_id: str, *, limit: int = 5) -> str:
    """Best-effort formatted stream tail for hydrate. Fail-open to empty."""
    try:
        from agents_extensions.shared.session_streams.db import SessionStreamDatabase
        from agents_extensions.shared.session_streams.model import entry_as_dict
        from agents_extensions.shared.session_streams.store import SessionStreamStore

        store = SessionStreamStore(SessionStreamDatabase())
        digest = store.load_digest(stream_id, limit=limit)
        lines = [f"stream={stream_id} pinned={len(digest.pinned)} recent={len(digest.recent)}"]
        # Prefer recent state/next_action; include pin count only as summary
        for e in digest.recent[-limit:]:
            d = entry_as_dict(e) if not isinstance(e, dict) else e
            et = d.get("type") or d.get("entry_type") or "?"
            body = (d.get("body") or "").replace("\n", " ").strip()
            if len(body) > 220:
                body = body[:217] + "..."
            lines.append(f"- [{et}] {body}")
        return "\n".join(lines)
    except Exception:
        return ""
