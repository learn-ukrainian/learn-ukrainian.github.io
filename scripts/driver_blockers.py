"""Deterministic CTO-post deltas; the private sidecar is bookkeeping, not authority."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import stat
import sys
from datetime import datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common.safe_unit_install import InstallError, open_unit_dir, read_unit, write_unit

LEDGER_NAME = "CTO-BLOCKERS-LEDGER.json"
MAX_INPUT_BYTES = 1_048_576
ITEM_KEYS = frozenset({"id", "state", "owner", "waits_on", "action"})
ANCHOR_KEYS = frozenset({"message_id", "content_sha256", "created_at"})
UNKNOWN_SUMMARY = "none recorded (unknown: treat every current blocker as unreported)"
USAGE_RULE = (
    "Put every owned blocker in --current with complete: true; run "
    '`.venv/bin/python -m scripts.driver_blockers delta --epic "$SESSION_EPIC" --current blockers.json`; '
    "post each item that is not UNCHANGED with all its fields on one line, and each RESOLVED item with the exact case-sensitive standalone token RESOLVED <id> on its own non-active line (no other fields or prose); "
    "if delta fails or the baseline is unknown, post everything currently blocking; "
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


def validate_epic(epic: str) -> None:
    """Match handoff_identity.sh epic_name_valid: lowercase alnum, inner hyphens."""
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", epic):
        raise ValueError("epic must be a selector such as infra or 7919")


@contextlib.contextmanager
def _ledger_directory(path: Path, *, create: bool = False):
    directory_fd = open_unit_dir(path.parent, create=create, directory_mode=0o700)
    if create and directory_fd is None:
        raise ValueError("ledger directory vanished during creation")
    try:
        yield directory_fd
    finally:
        if directory_fd is not None:
            os.close(directory_fd)


def _check_directory(path: Path, directory_fd: int) -> None:
    """Refuse a moved or symlinked parent; all data I/O stays on the pinned fd."""
    with _ledger_directory(path) as current_fd:
        if current_fd is None:
            raise ValueError("ledger directory changed during operation")
        held, current = os.fstat(directory_fd), os.fstat(current_fd)
        if (held.st_dev, held.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("ledger directory changed during operation")


def load_ledger(path: Path, epic: str, *, directory_fd: int | None = None) -> dict | None:
    if directory_fd is None:
        with _ledger_directory(path) as held_fd:
            if held_fd is None:
                return None
            return load_ledger(path, epic, directory_fd=held_fd)
    # Unsafe filesystem entries are errors, never an unknown silence baseline.
    read_unit(directory_fd, f"{LEDGER_NAME}.lock")
    unit = read_unit(directory_fd, path.name)
    _check_directory(path, directory_fd)
    if unit is None:
        return None
    try:
        raw, _ = unit
        if len(raw) > MAX_INPUT_BYTES:
            return None
        return validate_ledger(json.loads(raw, object_pairs_hook=_unique_keys), epic)
    except (ValueError, UnicodeError, RecursionError):
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
    validate_epic(epic)
    from scripts.driver_state import STATE_ENV, state_path

    # A driver may run from a dispatch checkout while its launcher pins state
    # elsewhere. Use that exact epic's configured state; never another epic's.
    if os.environ.get("SESSION_EPIC") == epic and os.environ.get(STATE_ENV, "").strip():
        state = state_path()
    else:
        state = state_path(epic)
    return state.parent / LEDGER_NAME


def _atomic_write(path: Path, data: dict, *, directory_fd: int | None = None) -> None:
    if directory_fd is None:
        with _ledger_directory(path, create=True) as held_fd:
            assert held_fd is not None
            _atomic_write(path, data, directory_fd=held_fd)
        return
    raw = (json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("resulting ledger exceeds maximum byte size")
    _check_directory(path, directory_fd)
    read_unit(directory_fd, path.name)
    read_unit(directory_fd, f"{LEDGER_NAME}.lock")
    write_unit(directory_fd, path.name, raw, mode=0o600)


@contextlib.contextmanager
def _ledger_lock(directory_fd: int):
    name = f"{LEDGER_NAME}.lock"
    read_unit(directory_fd, name)
    lock_fd = os.open(
        name,
        os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
        0o600,
        dir_fd=directory_fd,
    )
    try:
        held = os.fstat(lock_fd)
        current = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if not stat.S_ISREG(held.st_mode) or (held.st_dev, held.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError("ledger lock is not a stable regular file")
        os.fchmod(lock_fd, 0o600)
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(lock_fd)


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
    # Lock a separate stable inode: locking the atomically replaced ledger
    # itself would let a second process lock the old inode and lose an update.
    with _ledger_directory(path, create=True) as directory_fd, _ledger_lock(directory_fd):
        _check_directory(path, directory_fd)
        stored = load_ledger(path, epic, directory_fd=directory_fd)
        if stored is None and read_unit(directory_fd, path.name) is not None:
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
        posted_text = posted
        for item in delta["items"]:
            if item["class"] == "UNCHANGED":
                continue
            item_id = item["id"]
            id_pattern = rf"(?<![A-Za-z0-9_.-]){re.escape(item_id)}(?![A-Za-z0-9_.-])"
            matching_lines = [line for line in posted_text.splitlines() if re.search(id_pattern, line)]
            if not matching_lines:
                raise ValueError(f"posted body omits {item['class']} item id {item_id!r} verbatim")
            if item["class"] in {"NEW", "CHANGED"}:
                item_values = [v for k, v in item.items() if k != "class"]
                line_matched = any(
                    all(
                        re.search(rf"(?<![A-Za-z0-9_.-]){re.escape(val)}(?![A-Za-z0-9_.-])", line)
                        for val in item_values
                    )
                    for line in matching_lines
                )
                if not line_matched:
                    raise ValueError(
                        f"posted body omits required fields for {item['class']} item {item_id!r} on the same line"
                    )
            elif item["class"] == "RESOLVED":
                # An exact standalone line cannot carry an active item's fields.
                line_matched = any(line.strip() == f"RESOLVED {item_id}" for line in matching_lines)
                if not line_matched:
                    raise ValueError(f"posted body omits exact token RESOLVED {item_id} on its own non-active line")
        updated = {
            "epic": epic,
            "generation": expect_generation + 1,
            "anchor": anchor,
            "items": {item["id"]: fingerprint(item) for item in observation["items"]},
        }
        _atomic_write(path, updated, directory_fd=directory_fd)
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
(ISO-8601 with timezone). BODY is the exact UTF-8 posted body: post each
non-UNCHANGED item with all its fields on one line, and each RESOLVED item with
the exact case-sensitive standalone token RESOLVED <id> on its own non-active
line (no other fields or prose).
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
    except (ValueError, OSError, TypeError, OverflowError, InstallError) as exc:
        # Do not expose private absolute locations through OSError diagnostics.
        reason = str(exc) if isinstance(exc, ValueError) else "data or sidecar operation failed"
        print(f"driver_blockers: {reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
