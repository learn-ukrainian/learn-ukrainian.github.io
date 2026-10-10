"""Deterministic CTO-post deltas; the private sidecar is bookkeeping, not authority."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

LEDGER_NAME = "CTO-BLOCKERS-LEDGER.json"
MAX_INPUT_BYTES = 1_048_576
ITEM_KEYS = frozenset({"id", "state", "owner", "waits_on", "action"})
ANCHOR_KEYS = frozenset({"message_id", "content_sha256", "created_at"})
UNKNOWN_SUMMARY = "none recorded (unknown: treat every current blocker as unreported)"
USAGE_RULE = (
    "Put every owned blocker in --current with complete: true; run "
    '`.venv/bin/python -m scripts.driver_blockers delta --epic "$SESSION_EPIC" --current blockers.json`; '
    "post each item that is not UNCHANGED; if delta fails or the baseline is unknown, post everything currently blocking; "
    "after the post succeeds, record with the receipt and the exact posted body using "
    '`.venv/bin/python -m scripts.driver_blockers record --epic "$SESSION_EPIC" --current blockers.json '
    "--receipt receipt.json --body-file posted.md --expect-generation N` (N is the generation from delta)."
)


def _string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _timestamp(value: object) -> datetime:
    if not _string(value):
        raise ValueError("anchor created_at must be an ISO-8601 timestamp with timezone")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("anchor created_at must be an ISO-8601 timestamp with timezone") from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("anchor created_at must include a timezone")
    return stamp


def _unique_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _read_bytes(path: Path) -> bytes:
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except OSError as exc:
        raise ValueError("input is unreadable") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("input exceeds maximum byte size; nothing clipped")
    return raw


def _read_json(path: Path) -> dict:
    try:
        return json.loads(_read_bytes(path), object_pairs_hook=_unique_keys)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("input is not valid UTF-8 JSON") from exc


def validate_observation(data: object, epic: str) -> dict:
    """Reject incomplete schemas; completeness itself may legitimately be false."""
    if not isinstance(data, dict) or set(data) != {"epic", "complete", "items"}:
        raise ValueError("observation requires exactly epic, complete and items")
    if data["epic"] != epic or type(data["complete"]) is not bool or not isinstance(data["items"], list):
        raise ValueError("observation epic, complete or items is invalid")
    seen = set()
    for item in data["items"]:
        if not isinstance(item, dict) or set(item) != ITEM_KEYS or not all(_string(v) for v in item.values()):
            raise ValueError("each item requires exactly five non-empty strings: id, state, owner, waits_on, action")
        if item["id"] in seen:
            raise ValueError("duplicate blocker id")
        seen.add(item["id"])
    return data


def fingerprint(item: dict) -> str:
    """Hash sorted UTF-8 JSON without normalizing any field's Unicode."""
    raw = json.dumps(item, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _anchor(data: object) -> dict:
    if not isinstance(data, dict) or set(data) != ANCHOR_KEYS:
        raise ValueError("anchor requires exactly message_id, content_sha256 and created_at")
    if not _string(data["message_id"]) or not _digest(data["content_sha256"]):
        raise ValueError("invalid message anchor")
    _timestamp(data["created_at"])
    return data


def validate_ledger(data: object, epic: str) -> dict | None:
    """Missing or inconsistent anchors cannot establish a silence baseline."""
    try:
        if not isinstance(data, dict) or set(data) != {"epic", "generation", "anchor", "items"}:
            return None
        if data["epic"] != epic or type(data["generation"]) is not int or data["generation"] < 1:
            return None
        _anchor(data["anchor"])
        if not isinstance(data["items"], dict) or not all(
            _string(key) and _digest(value) for key, value in data["items"].items()
        ):
            return None
    except (ValueError, TypeError, OverflowError):
        return None
    return data


def load_ledger(path: Path, epic: str) -> dict | None:
    try:
        return validate_ledger(_read_json(path), epic)
    except ValueError:
        return None


def compute_delta(observation: dict, ledger: object = None) -> dict:
    """Classify a validated snapshot against only a validated complete baseline."""
    epic = observation["epic"]
    validate_observation(observation, epic)
    stored = validate_ledger(ledger, epic)
    baseline = stored if observation["complete"] else None
    previous = baseline["items"] if baseline else {}
    items = []
    current_ids = set()
    for item in observation["items"]:
        key = item["id"]
        current_ids.add(key)
        kind = "NEW" if key not in previous else "UNCHANGED" if previous[key] == fingerprint(item) else "CHANGED"
        items.append({**item, "class": kind})
    items.extend({"id": key, "class": "RESOLVED"} for key in sorted(previous.keys() - current_ids))
    return {
        "epic": epic,
        "baseline": "valid" if baseline else "unknown",
        "generation": stored["generation"] if stored else 0,
        "items": items,
        "post_required": baseline is None or any(item["class"] != "UNCHANGED" for item in items),
    }


def ledger_path(epic: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", epic):
        raise ValueError("epic must be a selector such as infra or 7919")
    from scripts.driver_state import STATE_ENV, state_path

    # A driver may run from a dispatch checkout while its launcher pins state
    # elsewhere. Use that exact epic's configured state; never another epic's.
    if os.environ.get("SESSION_EPIC") == epic and os.environ.get(STATE_ENV, "").strip():
        state = state_path()
    else:
        state = state_path(epic)
    return state.parent / LEDGER_NAME


def _atomic_write(path: Path, data: dict) -> None:
    raw = (json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("resulting ledger exceeds maximum byte size")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=f".{LEDGER_NAME}.", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def record(path: Path, epic: str, observation: dict, receipt: dict, body: bytes, expect_generation: int) -> dict:
    """Bind the posted set to exact body bytes, then advance under a stable lock."""
    validate_observation(observation, epic)
    if not observation["complete"]:
        raise ValueError("record requires complete: true")
    if type(expect_generation) is not int or expect_generation < 0:
        raise ValueError("expected generation must be a non-negative integer")
    if not isinstance(receipt, dict) or receipt.get("recipient") != "cto":
        raise ValueError("receipt recipient must be cto")
    anchor = _anchor({key: receipt.get(key) for key in ANCHOR_KEYS})
    if hashlib.sha256(body).hexdigest() != anchor["content_sha256"]:
        raise ValueError("posted body hash does not match receipt")
    try:
        posted = body.decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("posted body must be UTF-8") from exc
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Lock a separate stable inode: locking the atomically replaced ledger
    # itself would let a second process lock the old inode and lose an update.
    with (path.parent / f"{LEDGER_NAME}.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        stored = load_ledger(path, epic)
        if stored is None and path.exists():
            raise ValueError("existing ledger is invalid; generation and anchor cannot be checked safely")
        delta = compute_delta(observation, stored)
        if delta["generation"] != expect_generation:
            raise ValueError("stale expected generation")
        if stored:
            old = stored["anchor"]
            if anchor["message_id"] == old["message_id"]:
                raise ValueError("receipt message_id was already recorded")
            if _timestamp(anchor["created_at"]) <= _timestamp(old["created_at"]):
                raise ValueError("receipt created_at must be later than recorded anchor")
        for item in delta["items"]:
            if item["class"] != "UNCHANGED" and not all(
                value in posted for key, value in item.items() if key != "class"
            ):
                raise ValueError("posted body omits a non-UNCHANGED item or RESOLVED id verbatim")
        updated = {
            "epic": epic,
            "generation": expect_generation + 1,
            "anchor": anchor,
            "items": {item["id"]: fingerprint(item) for item in observation["items"]},
        }
        _atomic_write(path, updated)
    return updated


def show_summary(path: Path, epic: str) -> str:
    stored = load_ledger(path, epic)
    if stored is None:
        return UNKNOWN_SUMMARY
    generation = str(stored["generation"])
    if len(generation) > 32:
        generation = "[large integer]"
    return f"CTO blockers: generation {generation}; {len(stored['items'])} recorded blockers"


EPILOG = """Examples:
  .venv/bin/python -m scripts.driver_blockers delta --epic infra --current blockers.json
  .venv/bin/python -m scripts.driver_blockers record --epic infra --current blockers.json --receipt receipt.json --body-file posted.md --expect-generation 0
  .venv/bin/python -m scripts.driver_blockers show --epic infra
Outputs: delta emits JSON; show emits a bounded summary. Only record writes the
private CTO-BLOCKERS-LEDGER.json sidecar and its lock next to DRIVER-STATE.md.
No command sends a message. Input files are bounded to 1 MiB, never clipped.
Current: exactly {"epic":"infra","complete":true,"items":[...]}; each item has
exactly five non-empty strings: id, state, owner, waits_on, action. Receipt:
Fleet Comms JSON with recipient="cto", message_id, content_sha256, created_at
(ISO-8601 with timezone). BODY is the exact UTF-8 posted body: include every
field value of each non-UNCHANGED item and every RESOLVED id verbatim.
Exit codes: 0 success; 1 invalid/unreadable data or rejected record (no classes
on delta failure, previous ledger untouched); 2 invalid/missing CLI arguments.
Related: scripts.driver_state; issue #10362, epic #7919.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare current owned blockers with the last recorded CTO post.\n"
        "Use on driver wakes before posting; never use partial or unknown data to suppress a blocker.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, description in (
        ("delta", "Emit NEW/CHANGED/RESOLVED/UNCHANGED classes before posting."),
        ("record", "Record a successful CTO post only after receipt/body validation."),
        ("show", "Show the bounded baseline summary without filesystem paths."),
    ):
        cmd = sub.add_parser(
            name,
            help=description,
            description=description,
            epilog=EPILOG,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        cmd.add_argument("--epic", required=True, help="Exact epic selector, e.g. infra or 7919.")
        if name != "show":
            cmd.add_argument(
                "--current", type=Path, required=True, help="Current observation JSON, e.g. blockers.json."
            )
        if name == "record":
            cmd.add_argument(
                "--receipt",
                type=Path,
                required=True,
                help="Successful Fleet Comms CTO receipt JSON, e.g. receipt.json.",
            )
            cmd.add_argument("--body-file", type=Path, required=True, help="Exact bytes posted to CTO, e.g. posted.md.")
            cmd.add_argument(
                "--expect-generation",
                type=int,
                required=True,
                help="Generation from delta, e.g. 0 for an unknown/absent ledger.",
            )
    args = parser.parse_args(argv)
    try:
        path = ledger_path(args.epic)
        if args.command == "show":
            print(show_summary(path, args.epic))
        else:
            observation = validate_observation(_read_json(args.current), args.epic)
            if args.command == "delta":
                result = compute_delta(observation, load_ledger(path, args.epic))
            else:
                updated = record(
                    path,
                    args.epic,
                    observation,
                    _read_json(args.receipt),
                    _read_bytes(args.body_file),
                    args.expect_generation,
                )
                result = {"generation": updated["generation"], "recorded": True}
            print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, TypeError, OverflowError) as exc:
        # Do not expose private absolute locations through OSError diagnostics.
        reason = str(exc) if isinstance(exc, ValueError) else "data or sidecar operation failed"
        print(f"driver_blockers: {reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
