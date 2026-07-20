"""Driver-handoff diary helpers for Grok lane canary recovery.

The dual-write handoff file is the human SSOT that survives compact/rot.
This module keeps stamps mintable (Next Drive / Hands-off bullets) and
emits a fixed STATE AT HANDBACK block on FAIL or clean close.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

DIARY_MARKER = "## 📔 Diary — reverse chrono (newest first)"
NEXT_DRIVE_MARKER = "## Next Drive"
HANDS_OFF_MARKER = "## Hands-off"
HANDBACK_MARKER = "## STATE AT HANDBACK"

_LAST_STAMP_RE = re.compile(
    r"^(\*\*Last diary stamp:\*\*)\s*.+$",
    re.MULTILINE,
)


def utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")


def resolve_handoff_path(repo: Path, epic: str, override: str | Path | None = None) -> Path:
    if override:
        p = Path(override)
        return p if p.is_absolute() else (repo / p)
    base = repo / ".claude" / f"{epic}-epic"
    for name in (
        "INTERIM-DRIVER-HANDOFF.md",
        "CLAUDE-DRIVER-HANDOFF.md",
        "CODEX-DRIVER-HANDOFF.md",
    ):
        cand = base / name
        if cand.is_file():
            return cand
    # Prefer INTERIM as write target for Grok interim drivers.
    return base / "INTERIM-DRIVER-HANDOFF.md"


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


def append_diary_stamp(
    path: Path,
    *,
    title: str,
    bullets: Sequence[str],
    next_drive: Sequence[str] | None = None,
    stamp: str | None = None,
) -> str:
    """Prepend a diary entry; optionally replace Next Drive bullets. Returns stamp used."""
    stamp = stamp or utc_stamp()
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    text = ensure_diary_skeleton(text, epic=path.parent.name.replace("-epic", ""), stream_id="epic:?")

    # Update last stamp
    if _LAST_STAMP_RE.search(text):
        text = _LAST_STAMP_RE.sub(rf"\1 {stamp}", text, count=1)

    bullet_lines = "\n".join(f"- {b.strip()}" for b in bullets if b and b.strip())
    entry = f"### {stamp} — {title.strip()}\n{bullet_lines}\n\n"

    # Insert under diary marker
    diary_re = re.compile(
        r"^(##\s+.*Diary[^\n]*\n\n)",
        re.MULTILINE | re.IGNORECASE,
    )
    m = diary_re.search(text)
    text = (
        text[: m.end()] + entry + text[m.end() :]
        if m
        else text.rstrip() + f"\n\n{DIARY_MARKER}\n\n" + entry
    )

    if next_drive is not None:
        text = replace_next_drive_bullets(text, next_drive)

    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    return stamp


def replace_next_drive_bullets(text: str, bullets: Sequence[str]) -> str:
    """Replace content under ## Next Drive until next ## heading."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        out.append(lines[i])
        if re.match(r"^##\s+Next Drive\b", lines[i], re.IGNORECASE):
            i += 1
            # skip old body until next ##
            while i < len(lines) and not re.match(r"^##\s+", lines[i]):
                i += 1
            for n, b in enumerate(bullets, start=1):
                b = b.strip()
                if not b:
                    continue
                # Prefer numbered list for mint friendliness
                if re.match(r"^\d+\.", b):
                    out.append(b + "\n")
                else:
                    out.append(f"{n}. {b}\n")
            out.append("\n")
            continue
        i += 1
    return "".join(out)


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
) -> str:
    """Append STATE AT HANDBACK and a diary stamp. Sync Next Drive bullets."""
    stamp = stamp or utc_stamp()
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
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

    # Diary stamp pointing at handback
    diary_entry = (
        f"### {stamp} — STATE AT HANDBACK ({reason.strip()})\n"
        f"- {canary_line.strip()}\n"
        f"- Full block under `{HANDBACK_MARKER}` below/above.\n"
        f"- Successor must mint canary after loading this file + stream.\n\n"
    )
    diary_re = re.compile(r"^(##\s+.*Diary[^\n]*\n\n)", re.MULTILINE | re.IGNORECASE)
    m = diary_re.search(text)
    if m:
        text = text[: m.end()] + diary_entry + text[m.end() :]
    else:
        text = text.rstrip() + f"\n\n{DIARY_MARKER}\n\n" + diary_entry

    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
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
