"""One bounded orientation packet per lane.

The packet reuses the cold-start board's 16384-byte ceiling. It does not
open a second store. Launchers inject the packet in a separate change.
"""

from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PACKET_MAX_BYTES = 16384
_ORDER_LIMIT = 500
_TEXT_LIMITS = (200, 80, 40, 24)


def json_bytes(payload: dict[str, Any], *, newline: bool = False) -> bytes:
    """Serialize the way Starlette's JSONResponse does, optionally plus a newline."""
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        indent=None,
        separators=(",", ":"),
    ).encode("utf-8")
    return raw + (b"\n" if newline else b"")


def _stamp(now: datetime | None) -> str:
    moment = now or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sections(text: str) -> list[tuple[str, list[str]]]:
    current: str | None = None
    buckets: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            buckets.append((current, []))
            continue
        if current is not None and line.strip():
            buckets[-1][1].append(line.strip())
    return buckets


def _clean_line(line: str) -> str:
    text = line.strip()
    if text.startswith(("- ", "* ")):
        return text[2:].strip()
    return text


def _entries(lines: list[str], prefix: str) -> list[dict[str, str]]:
    entries = []
    for index, line in enumerate(lines, start=1):
        text = _clean_line(line)
        if text:
            entries.append({"id": f"{prefix}-{index}", "text": text})
    return entries


def _collect_state(text: str) -> dict[str, list[dict[str, str]]]:
    found = {"goals": [], "next": [], "holds": [], "stops": []}
    for title, lines in _sections(text):
        key = title.lower()
        if key.startswith("current goal"):
            found["goals"].extend(_entries(lines, "goal"))
        elif key.startswith("next"):
            found["next"].extend(_entries(lines, "next"))
        elif key.startswith("hold"):
            found["holds"].extend(_entries(lines, "hold"))
        elif key.startswith("stop"):
            found["stops"].extend(_entries(lines, "stop"))
    return found


def _worker_target() -> int | str:
    from scripts.driver_state import minimum_workers

    value = minimum_workers()
    return value if isinstance(value, int) and value > 0 else "UNKNOWN"


def _plane_source(observed_at: str) -> dict[str, Any]:
    try:
        from scripts.fleet_comms.message_plane import resolve_plane_mode

        mode = str(resolve_plane_mode(None))
        return {
            "name": "plane",
            "locator": ".venv/bin/python -m scripts.fleet_comms plane-status",
            "observed_at": observed_at,
            "freshness": "live",
            "mode": mode,
        }
    except Exception:
        return {
            "name": "plane",
            "locator": ".venv/bin/python -m scripts.fleet_comms plane-status",
            "observed_at": None,
            "freshness": "unknown",
        }


def _default_orders(recipient: str) -> dict[str, Any]:
    from scripts.inbox_pending import probe

    result = probe(recipient, limit=_ORDER_LIMIT)
    return result if isinstance(result, dict) else {"probe": "unknown", "count": 0, "ids": [], "truncated": False}


def _default_session(root: Path, observed_at: str) -> dict[str, Any]:
    locator = "docs/session-state/current.md"
    try:
        from scripts.api.session_router import _assemble_session

        markdown, sections, digest = _assemble_session("orchestrator", root)
        safe_sections = {
            key: value for key, value in sections.items() if key in {"agent", "current", "router", "recent_handoffs"}
        }
        return {
            "hash": digest,
            "bytes": len(markdown.encode("utf-8")),
            "locator": locator,
            "sections": safe_sections,
            "observed_at": observed_at,
            "freshness": "live",
        }
    except Exception:
        return {
            "hash": None,
            "bytes": None,
            "locator": locator,
            "sections": {},
            "observed_at": None,
            "freshness": "unknown",
        }


def _shorten(entries: list[dict[str, str]], limit: int) -> int:
    changed = 0
    for entry in entries:
        text = entry.get("text") or ""
        if limit <= 0:
            if text:
                entry["text"] = ""
                changed += 1
            continue
        if len(text) > limit:
            entry["text"] = text[:limit]
            changed += 1
    return changed


def _note(packet: dict[str, Any], locator: str, count: int) -> None:
    packet["complete"] = False
    omitted = packet["omitted"]
    omitted["count"] += count
    if locator and locator not in omitted["locators"]:
        omitted["locators"].append(locator)


def _response_note(payload: dict[str, Any], locator: str) -> None:
    bound = payload.setdefault("orientation_bound", {"complete": False, "omitted": {"count": 0, "locators": []}})
    bound["omitted"]["count"] += 1
    bound["omitted"]["locators"].append(locator)


def _shed_source_reasons(payload: dict[str, Any], locator: str) -> None:
    # A source's diagnostic text must not crowd healthy work out of the packet.
    for index, source in enumerate(payload.get("sources") or []):
        if len(json_bytes(payload, newline=True)) <= PACKET_MAX_BYTES:
            break
        if isinstance(source, dict) and source.get("reason"):
            source.pop("reason")
            _response_note(payload, f"{locator}#/sources/{index}/reason")


def cap_response(payload: dict[str, Any], *, locator: str) -> dict[str, Any]:
    """Bound the whole JSON document, including metadata and omission notes.

    JSON Pointer fragments locate removed fields in the source response. If
    those notes themselves overflow, the source locator covers the entire
    omitted document, including its existing omission records.
    """
    if len(json_bytes(payload, newline=True)) <= PACKET_MAX_BYTES:
        return payload
    out = deepcopy(payload)
    _shed_source_reasons(out, locator)
    if len(json_bytes(out, newline=True)) <= PACKET_MAX_BYTES:
        return out

    candidates = sorted(
        (key for key in out if key != "orientation_bound"),
        key=lambda key: len(json_bytes({key: out[key]})),
        reverse=True,
    )
    for key in candidates:
        out.pop(key)
        pointer = str(key).replace("~", "~0").replace("/", "~1")
        _response_note(out, f"{locator}#/{pointer}")
        if len(json_bytes(out, newline=True)) <= PACKET_MAX_BYTES:
            return out
    return {
        "error": "orientation_overflow",
        "complete": False,
        "omitted": {"count": 1, "locators": [locator]},
    }


def _fit(packet: dict[str, Any], state_locator: str) -> dict[str, Any]:
    def oversized() -> bool:
        return len(json_bytes(packet, newline=True)) > PACKET_MAX_BYTES

    if not oversized():
        return packet

    session = packet.get("session") or {}
    if session.get("sections"):
        session["sections"] = {}
        _note(packet, str(session.get("locator") or "docs/session-state/current.md"), 1)
        if not oversized():
            return packet

    for limit in _TEXT_LIMITS:
        shed = _shorten(packet["goals"], limit) + _shorten(packet["next"], limit)
        if shed:
            _note(packet, state_locator, shed)
        if not oversized():
            return packet

    for limit in _TEXT_LIMITS:
        shed = _shorten(packet["holds"], limit) + _shorten(packet["stops"], limit)
        if shed:
            _note(packet, state_locator, shed)
        if not oversized():
            return packet

    if packet["next"]:
        _note(packet, state_locator, len(packet["next"]))
        packet["next"] = []
    if packet["goals"]:
        _note(packet, state_locator, len(packet["goals"]))
        packet["goals"] = [{"id": entry["id"], "text": ""} for entry in packet["goals"]]
    if not oversized():
        return packet

    # Prefer hold and stop indicators over order ids while their cardinality fits.
    shed = _shorten(packet["holds"], 0) + _shorten(packet["stops"], 0)
    if shed:
        _note(packet, state_locator, shed)
    if not oversized():
        return packet

    kept: list[dict[str, str]] = []
    dropped = 0
    for entry in packet["orders"]:
        trial = dict(packet)
        trial["orders"] = [*kept, entry]
        if len(json_bytes(trial, newline=True)) > PACKET_MAX_BYTES:
            dropped += 1
            continue
        kept.append(entry)
    if dropped:
        packet["orders"] = kept
        _note(packet, ".venv/bin/python -m scripts.fleet_comms deliveries --help", dropped)
        # The omission note is applied after the fit check. Drop further ids
        # until the note itself fits. Hold and stop ids are not in this list.
        while packet["orders"] and len(json_bytes(packet, newline=True)) > PACKET_MAX_BYTES:
            packet["orders"].pop()
            packet["omitted"]["count"] += 1
    # A section locator covers every omitted entry without an unbounded list
    # of ids. Reserve its bytes before dropping entries.
    for key in ("goals", "holds", "stops"):
        if not oversized():
            return packet
        if packet[key]:
            _note(packet, f"{state_locator}#{key}", 0)
        while packet[key] and oversized():
            packet[key].pop()
            packet["omitted"]["count"] += 1
    return cap_response(packet, locator=f".venv/bin/python -m scripts.driver_state packet --epic {packet['epic']}")


def build_packet(
    epic: str,
    *,
    root: Path | None = None,
    recipient: str | None = None,
    orders: dict[str, Any] | None = None,
    session: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Assemble one lane packet and enforce PACKET_MAX_BYTES."""
    from scripts.common.epic_selector import validate_epic
    from scripts.driver_state import state_path

    validate_epic(epic)
    generated_at = _stamp(now)
    explicit_state = os.environ.get("LU_DRIVER_STATE_FILE", "").strip()
    path = Path(explicit_state) if root is None and explicit_state else state_path(epic, root)
    base = root if root is not None else (path.resolve().parents[2] if path is not None else Path.cwd())
    state_locator = f".claude/{epic}-epic/DRIVER-STATE.md"
    state_freshness = "unknown"
    observed_at = None
    collected = {"goals": [], "next": [], "holds": [], "stops": []}
    if path is not None and path.is_file():
        collected = _collect_state(path.read_text(encoding="utf-8"))
        state_freshness = "live"
        observed_at = _stamp(datetime.fromtimestamp(path.stat().st_mtime, UTC))

    if orders is None:
        orders = (
            _default_orders(recipient) if recipient else {"probe": "unknown", "count": 0, "ids": [], "truncated": False}
        )
    probe_ok = orders.get("probe") == "ok"
    order_ids = [str(item) for item in orders.get("ids") or [] if isinstance(item, (str, int))]
    order_rows = [{"id": item} for item in order_ids]
    truncated = bool(orders.get("truncated"))
    reported = orders.get("count")
    missing_orders = 0
    if isinstance(reported, int) and reported > len(order_rows):
        missing_orders = reported - len(order_rows)

    if session is None:
        session = _default_session(base, generated_at)

    required_live = state_freshness == "live" and probe_ok and session.get("freshness") == "live"
    packet: dict[str, Any] = {
        "epic": epic,
        "generated_at": generated_at,
        "freshness": "live" if required_live else "unknown",
        "complete": bool(required_live and not truncated and missing_orders == 0),
        "omitted": {"count": missing_orders, "locators": []},
        "stops": collected["stops"],
        "holds": collected["holds"],
        "goals": collected["goals"],
        "next": collected["next"],
        "orders": order_rows,
        "runtime": {"worker_target": _worker_target()},
        "session": {
            "hash": session.get("hash"),
            "bytes": session.get("bytes"),
            "locator": session.get("locator") or "docs/session-state/current.md",
            "sections": session.get("sections") or {},
            "observed_at": session.get("observed_at"),
            "freshness": session.get("freshness") or "unknown",
        },
        "sources": [
            {
                "name": "driver_state",
                "locator": state_locator,
                "observed_at": observed_at,
                "freshness": state_freshness,
            },
            {
                "name": "orders",
                "locator": ".venv/bin/python -m scripts.fleet_comms deliveries --help",
                "observed_at": generated_at if probe_ok else None,
                "freshness": "live" if probe_ok else "unknown",
            },
            {
                "name": "session",
                "locator": session.get("locator") or "docs/session-state/current.md",
                "observed_at": session.get("observed_at"),
                "freshness": session.get("freshness") or "unknown",
            },
            {
                "name": "open_prs",
                "locator": "gh pr list --state open",
                "observed_at": None,
                "freshness": "unknown",
            },
            {
                "name": "live_workers",
                "locator": ".venv/bin/python -m scripts.delegate status",
                "observed_at": None,
                "freshness": "unknown",
            },
            _plane_source(generated_at),
        ],
    }
    if not probe_ok:
        packet["complete"] = False
        packet["omitted"]["locators"].append("pass --recipient for unconsumed order ids")
        packet["omitted"]["count"] += 1
    elif truncated or missing_orders:
        packet["complete"] = False
        packet["omitted"]["locators"].append(".venv/bin/python -m scripts.fleet_comms deliveries --help")
    if state_freshness != "live":
        packet["complete"] = False
        packet["omitted"]["locators"].append(state_locator)
        packet["omitted"]["count"] += 1
    runtime_keys = set(packet["runtime"])
    if runtime_keys != {"worker_target"}:
        raise RuntimeError("orientation runtime allowlist violated")
    return _fit(packet, state_locator)


def render_packet(epic: str, *, recipient: str | None = None) -> str:
    return json_bytes(build_packet(epic, recipient=recipient), newline=True).decode("utf-8")


def cap_projection(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep the highest-attention rows that fit in PACKET_MAX_BYTES.

    The caller has already limited ``items`` to one lane. Public counts stay
    when possible; dropped rows and metadata have source locators.
    """
    locator = "/api/work/v1/projection"
    if len(json_bytes(payload, newline=True)) > PACKET_MAX_BYTES:
        payload = deepcopy(payload)
        _shed_source_reasons(payload, locator)
    items = [item for item in payload.get("items") or [] if isinstance(item, dict)]
    attention = [row for row in payload.get("attention") or [] if isinstance(row, dict)]
    rank = {row.get("work_id"): index for index, row in enumerate(attention)}
    ordered = sorted(items, key=lambda item: rank.get(item.get("work_id"), 10**9))
    metadata = cap_response({**payload, "items": [], "attention": []}, locator=locator)
    if metadata.get("error") == "orientation_overflow":
        return metadata

    def assemble(kept: list[dict[str, Any]]) -> dict[str, Any]:
        ids = {item.get("work_id") for item in kept}
        out = dict(metadata)
        out["items"] = kept
        out["attention"] = [row for row in attention if row.get("work_id") in ids]
        if len(kept) != len(ordered):
            denominator = dict(metadata.get("denominator") or {})
            omissions = [row for row in (denominator.get("omissions") or []) if isinstance(row, dict)]
            omissions.append(
                {
                    "class": "orientation_bound",
                    "reason": "lane_projection_bytes",
                    "count": len(ordered) - len(kept),
                    "locator": f"{locator}#/items",
                }
            )
            denominator["omissions"] = omissions
            out["denominator"] = denominator
        return out

    if len(json_bytes(assemble(ordered))) <= PACKET_MAX_BYTES:
        return assemble(ordered)
    low, high, best = 0, len(ordered), 0
    while low <= high:
        mid = (low + high) // 2
        if len(json_bytes(assemble(ordered[:mid]))) <= PACKET_MAX_BYTES:
            best = mid
            low = mid + 1
        else:
            high = mid - 1
    return cap_response(assemble(ordered[:best]), locator=locator)
