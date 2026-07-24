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
WORKING_SET_MARKER = "## Active Working Set"
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


def append_diary_stamp(
    path: Path,
    *,
    title: str,
    bullets: Sequence[str],
    next_drive: Sequence[str] | None = None,
    working_set: Sequence[str] | None = None,
    stamp: str | None = None,
) -> str:
    """Prepend a diary entry; optionally replace Next Drive / Active Working Set. Returns stamp used."""
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
    if working_set is not None:
        text = replace_working_set_bullets(text, working_set)

    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
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
    reground_tok = approx_tokens(reground)
    pack_max = max(200, max_tokens - reground_tok)
    pack_char_ceiling = pack_max * 4

    included: list[str] = [header]
    dropped: list[str] = []
    for name, body in sections:
        body = body.strip()
        if not body:
            continue
        trial = "\n\n".join([*included, body]).strip() + "\n"
        if approx_tokens(trial) > pack_max or len(trial) > pack_char_ceiling:
            # never drop identity
            if name == "identity":
                included.append(body)
            else:
                dropped.append(name)
            continue
        included.append(body)

    included.append(reground)

    capsule = "\n\n".join(included).strip() + "\n"
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

