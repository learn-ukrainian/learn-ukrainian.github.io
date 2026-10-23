"""Deterministic blocker-post deltas; the private sidecar is bookkeeping, not authority."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
import re
import stat
import sys
import unicodedata
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common.epic_selector import validate_epic as validate_epic
from scripts.common.safe_unit_install import InstallError, open_unit_dir, read_unit, write_unit

LEDGER_NAME = "CTO-BLOCKERS-LEDGER.json"
MAX_INPUT_BYTES = 1_048_576
# Internal dispatch records embed prompts; match the bounded task-record
# contract in scripts.fleet_comms.efficiency_metrics, not external inputs.
MAX_TASK_RECORD_BYTES = 32 * 1024 * 1024
ITEM_KEYS = frozenset({"id", "state", "owner", "waits_on", "action"})
ANCHOR_KEYS = frozenset({"message_id", "content_sha256", "created_at"})
REPORTING_TARGETS = ("epics", "cto")
UNKNOWN_SUMMARY = "none recorded (unknown: treat every current blocker as unreported)"
USAGE_RULE = (
    "Put every owned blocker in --current with complete: true; complete means exhaustive coverage "
    "including explicit unknown attention, not proven historical attribution. Generated rows retain "
    "current reporting custody only until positive exact-run status or other-stream proof; unsafe "
    "or lost source stops the lane and preserves its baseline. UNCHANGED means unchanged attention, "
    "not zero blockers. Measure actual observation, post, indented ledger and diagnostics bytes "
    "before posting; stop on overflow. Run "
    '`.venv/bin/python -m scripts.driver_blockers delta --epic "$SESSION_EPIC" --current blockers.json`; '
    "post ordinary reports to epics; select --reporting-target cto only for explicit operator escalation; "
    "post each item that is not UNCHANGED with all its fields on one line, and each RESOLVED item with the exact case-sensitive standalone token RESOLVED <id> on its own non-active line (no other fields or prose); "
    "With confirmed complete source coverage, if delta fails or the baseline is unknown, post everything currently blocking; "
    "a coverage failure stops the lane and requires escalation without replacing its baseline; "
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


def _safe_identity(value: object, *, task_id: bool = False) -> str:
    if (
        not _string(value)
        or value != value.strip()
        or ":" in value
        or any(unicodedata.category(c) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for c in value)
        or (not task_id and any(c in value for c in "/\\"))
        or (task_id and (value.startswith(("/", "\\")) or any(p in {".", ".."} for p in re.split(r"[/\\]", value))))
    ):
        raise ValueError("finalization task/run identity unsafe or ambiguous; attention is unknown")
    return value


def _task_identity(task: dict) -> tuple[str, str]:
    return _safe_identity(task.get("task_id"), task_id=True), _safe_identity(task.get("run_nonce"))


def _file_stamp(info: os.stat_result) -> tuple[int, ...]:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


class _CheckedTasks:
    """One ephemeral checked observation; no pathname body reads or winner selection."""

    def __init__(self, root: Path, stack: contextlib.ExitStack):
        self.root, self.stack = root, stack
        self.directories: dict[Path, tuple[int, tuple[int, ...]]] = {}
        self.files: dict[tuple[int, str], tuple[int, ...]] = {}
        self.hot_fd = self._directory(root)
        if self.hot_fd is None:
            raise ValueError("finalization task store unavailable; attention is unknown")
        self.hot = {name: self.read(self.hot_fd, name) for name in self.names(self.hot_fd) if name.endswith(".json")}
        self.archive: dict[str, dict] = {}
        self.archive_names: tuple[str, ...] | None = None
        self.archive_fd: int | None = None

    def _directory(self, path: Path) -> int | None:
        fd = open_unit_dir(path, create=False)
        if fd is not None:
            self.stack.callback(os.close, fd)
            self.directories[path] = (fd, _file_stamp(os.fstat(fd)))
        return fd

    @staticmethod
    def names(fd: int) -> tuple[str, ...]:
        with os.scandir(fd) as entries:
            return tuple(sorted(entry.name for entry in entries))

    def read(self, fd: int, name: str) -> dict:
        before = os.stat(name, dir_fd=fd, follow_symlinks=False)
        unit = read_unit(fd, name, max_bytes=MAX_TASK_RECORD_BYTES)
        after = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if unit is None or _file_stamp(before) != _file_stamp(after) or len(unit[0]) != after.st_size:
            raise ValueError("finalization source changed during read; attention is unknown")
        self.files[fd, name] = _file_stamp(after)
        try:
            task = json.loads(unit[0], object_pairs_hook=_unique_keys)
        except (UnicodeError, ValueError, RecursionError) as exc:
            raise ValueError("invalid task record; attention is unknown") from exc
        if not isinstance(task, dict):
            raise ValueError("invalid task record; attention is unknown")
        return task

    def exact_run(self, task_id: str, nonce: str) -> tuple[dict, int, int]:
        from scripts.orchestration.task_record_store import candidate_task_record_names

        if self.archive_names is None:
            self.archive_fd = self._directory(self.root / "archive")
            self.archive_names = () if self.archive_fd is None else self.names(self.archive_fd)
        selected = [self.hot[name] for name in candidate_task_record_names(task_id, self.hot)]
        archive_names = candidate_task_record_names(task_id, self.archive_names)
        for name in archive_names:
            if name not in self.archive:
                self.archive[name] = self.read(self.archive_fd, name)
            selected.append(self.archive[name])
        runs: dict[tuple[str, str], dict] = {}
        copies = 0
        for task in selected:
            identity = _task_identity(task)
            if identity[0] != task_id:
                raise ValueError("finalization exact-run stem has a foreign identity; attention is unknown")
            status = task.get("status")
            if not isinstance(status, str) or status not in _recognized_statuses():
                raise ValueError("finalization exact-run status unknown; attention is unknown")
            if identity in runs:
                if fingerprint(task) != fingerprint(runs[identity]):
                    raise ValueError("contradictory finalization exact-run copies; attention is unknown")
                copies += 1
            runs[identity] = task
        if (task_id, nonce) not in runs:
            raise ValueError("prior finalization exact run unavailable; authentic original restoration required")
        return runs[task_id, nonce], len(selected), copies

    def verify(self) -> None:
        for (fd, name), stamp in self.files.items():
            if _file_stamp(os.stat(name, dir_fd=fd, follow_symlinks=False)) != stamp:
                raise ValueError("finalization source changed during observation; attention is unknown")
        for path, (fd, stamp) in self.directories.items():
            current = open_unit_dir(path, create=False)
            if current is None:
                raise ValueError("finalization directory changed; attention is unknown")
            try:
                if _file_stamp(os.fstat(fd)) != stamp or _file_stamp(os.fstat(current)) != stamp:
                    raise ValueError("finalization directory changed; attention is unknown")
            finally:
                os.close(current)
        if self.archive_names is not None and self.archive_fd is None:
            try:
                os.stat("archive", dir_fd=self.hot_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise ValueError("finalization archive changed; attention is unknown")


@contextlib.contextmanager
def _checked_tasks(task_root: Path):
    try:
        with contextlib.ExitStack() as stack:
            source = _CheckedTasks(task_root, stack)
            yield source
            source.verify()
    except (UnicodeError, RecursionError) as exc:
        raise ValueError("invalid task record; attention is unknown") from exc
    except (OSError, InstallError) as exc:
        raise ValueError("finalization task store unreadable, unsafe or oversized; attention is unknown") from exc


def _finalization_tasks(task_root: Path) -> Iterator[dict]:
    """Compatibility iterator over the complete checked hot observation."""
    with _checked_tasks(task_root) as source:
        yield from source.hot.values()


def _recognized_statuses() -> frozenset[str]:
    from scripts.orchestration.worktree_claims import RELEASED_TASK_STATUSES

    return RELEASED_TASK_STATUSES | {"needs_finalize", "spawning", "running"}


def _registered_streams() -> tuple[dict[str, list[int]], dict[str, set[str]]]:
    from scripts.orchestration.handoff_slot_registry import registry_readable
    from scripts.orchestration.issue_stream_audit import load_registry
    from scripts.orchestration.launcher_aliases import load_launcher_bindings

    if not registry_readable():
        raise ValueError("finalization handoff registry unreadable; attention is unknown")
    registry = load_registry()
    lanes: dict[str, set[str]] = {}
    bindings = load_launcher_bindings()
    for selector in registry.keys() | bindings.keys():
        key, lane = bindings.get(selector, (selector.removeprefix("infra."), selector.removeprefix("infra.")))
        if key in registry:
            lanes.setdefault(lane, set()).add(key)
    return registry, lanes


def _slot_streams(slot: object, lanes: dict[str, set[str]]) -> set[str]:
    from scripts.orchestration.handoff_slot_registry import is_registered_slot

    if not _string(slot) or slot == "unknown":
        return set()
    if any(unicodedata.category(c) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for c in slot):
        raise ValueError("unsafe finalization initiator; attention is unknown")
    # Compare the complete recorded slot to each registered lane. The prefix is
    # not a provider allow-list; the existing roster must accept the full slot.
    matches = set()
    for lane, streams in lanes.items():
        suffix = f"-{lane}"
        if slot.endswith(suffix) and slot[: -len(suffix)] and is_registered_slot(slot):
            matches.update(streams)
    return matches


def _resolve_stream(epic: str, registry: dict[str, list[int]]) -> str:
    from scripts.orchestration.launcher_aliases import load_launcher_aliases

    key = load_launcher_aliases().get(epic, epic.removeprefix("infra."))
    matches = [name for name, numbers in registry.items() if name == key or (epic.isdecimal() and int(epic) in numbers)]
    if len(matches) != 1:
        raise ValueError("finalization stream scope unknown; restore launcher registry attribution")
    return matches[0]


def _reporting_scope(epic: str, initiator: str, member: int | None = None) -> tuple[str, tuple[int, ...]]:
    registry, lanes = _registered_streams()
    stream = _resolve_stream(epic, registry)
    if _slot_streams(initiator, lanes) != {stream}:
        raise ValueError("finalization reporting initiator must be an exact registered slot for the selected stream")
    if member is not None and (type(member) is not int or member not in registry[stream]):
        raise ValueError("finalization explicit member epic conflicts with registered stream scope")
    return initiator, tuple(registry[stream])


def _original_epic(task: dict) -> int | None:
    carrier = task.get("task_lifecycle")
    identity = carrier.get("identity") if isinstance(carrier, dict) else None
    epic = identity.get("stream_epic") if isinstance(identity, dict) else None
    return epic if type(epic) is int and epic > 0 else None


def _stream_membership(task: dict, stream: str, registry: dict[str, list[int]], lanes: dict[str, set[str]]) -> str:
    epic = _original_epic(task)
    if epic is not None:
        matches = {key for key, numbers in registry.items() if epic in numbers}
        if len(matches) > 1:
            raise ValueError("contradictory finalization stream membership; attention is unknown")
        if matches:
            return "owned" if stream in matches else "other_stream"
        return "unregistered"
    custody = _slot_streams(task.get("initiator"), lanes)
    return "custody" if custody == {stream} else "other_custody" if len(custody) == 1 else "possible_owned"


def _attention_item(task: dict, stream: str, membership: str) -> dict:
    from scripts.delegate import is_public_cause

    task_id, nonce = _task_identity(task)
    owner = task.get("initiator")
    owner = owner if _string(owner) else "unknown"
    if any(unicodedata.category(c) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for c in owner):
        raise ValueError("unsafe finalization initiator; attention is unknown")
    epic = _original_epic(task)
    reason = task.get("finalize_error") or task.get("last_error")
    if not is_public_cause(reason):
        reason = "finalization evidence unavailable; inspect private task diagnostics"
    try:
        terminal = f"; terminal={_timestamp(task.get('finished_at')).isoformat()}"
    except (ValueError, TypeError, OverflowError):
        terminal = ""
    unresolved = "; original_stream_membership=unknown" if membership == "unregistered" else ""
    return {
        "id": f"needs-finalize:{task_id}:{nonce}",
        "state": "needs_finalize",
        "owner": owner,
        "waits_on": f"pending finalization; original_initiator={owner}; original_stream_epic={epic if epic else 'unknown'}{unresolved}{terminal}; reason={reason}",
        "action": f"current reporting custody only: {stream}; inspect retained task/head and finalization diagnostics; repair the failing gate and retry normal publication",
    }


def _collect_finalization(
    observation: dict, scope: tuple[str, tuple[int, ...]], stored: dict | None
) -> tuple[dict, list[dict], dict]:
    from scripts.common.task_store_paths import tasks_dir

    initiator, epics = scope
    registry, lanes = _registered_streams()
    stream = _resolve_stream(observation["epic"], registry)
    if tuple(registry[stream]) != epics or _slot_streams(initiator, lanes) != {stream}:
        raise ValueError("finalization reporting scope conflicts with registered stream")
    previous = stored["items"] if stored else {}
    prior = {}
    for key in previous:
        if not key.startswith("needs-finalize:"):
            continue
        parts = key.split(":")
        if len(parts) != 3:
            raise ValueError("prior generated finalization id is ambiguous; attention is unknown")
        prior[key] = (_safe_identity(parts[1], task_id=True), _safe_identity(parts[2]))
    diagnostics = {
        "hot_units": 0,
        "hot_classes": {},
        "noncandidate_identity_unknown": 0,
        "noncandidate_conflicting_runs": 0,
        "same_run_copies": 0,
        "outside": 0,
        "below_threshold": 0,
        "exact_runs": [],
    }
    generated, ages = {}, []
    with _checked_tasks(tasks_dir()) as source:
        runs = {}
        noncandidates = {}
        conflicting_noncandidates = set()
        for task in source.hot.values():
            diagnostics["hot_units"] += 1
            status = task.get("status")
            category = status if isinstance(status, str) and status in _recognized_statuses() else "UNKNOWN"
            classes = diagnostics["hot_classes"]
            classes[category] = classes.get(category, 0) + 1
            if status != "needs_finalize":
                try:
                    identity = _task_identity(task)
                except ValueError:
                    diagnostics["noncandidate_identity_unknown"] += 1
                else:
                    if identity in noncandidates and fingerprint(task) != fingerprint(noncandidates[identity]):
                        conflicting_noncandidates.add(identity)
                    noncandidates[identity] = task
                continue
            identity = _task_identity(task)
            if identity in runs:
                if fingerprint(task) != fingerprint(runs[identity]):
                    raise ValueError("contradictory finalization candidate copies; attention is unknown")
                diagnostics["same_run_copies"] += 1
            runs[identity] = task
        diagnostics["noncandidate_conflicting_runs"] = len(conflicting_noncandidates)
        # A noncandidate copy of a candidate run is still a contradiction. No
        # identities are invented or required for unrelated noncandidates.
        for task in source.hot.values():
            identity = (task.get("task_id"), task.get("run_nonce"))
            if (
                all(isinstance(value, str) for value in identity)
                and identity in runs
                and fingerprint(task) != fingerprint(runs[identity])
            ):
                raise ValueError("contradictory finalization candidate copies; attention is unknown")
        for key, (task_id, nonce) in prior.items():
            task, units, copies = source.exact_run(task_id, nonce)
            diagnostics["exact_runs"].append({"id": key, "units": units, "same_run_copies": copies})
            if f"needs-finalize:{task['task_id']}:{task['run_nonce']}" != key:
                raise ValueError("prior generated finalization id does not round-trip")
            if task["status"] == "needs_finalize":
                runs[task_id, nonce] = task
        for identity, task in sorted(runs.items()):
            key = f"needs-finalize:{identity[0]}:{identity[1]}"
            membership = _stream_membership(task, stream, registry, lanes)
            if membership == "other_stream" or (membership == "other_custody" and key not in prior):
                diagnostics["outside"] += 1
                continue
            age = finalization_age(task)
            ages.append(
                {
                    "task_id": identity[0],
                    "run_nonce": identity[1],
                    **{k: age[k] for k in ("age_minutes", "age_state", "threshold_minutes", "configuration")},
                }
            )
            if (
                key not in prior
                and membership == "owned"
                and _string(task.get("initiator"))
                and task.get("initiator") != "unknown"
                and not age["attention"]
            ):
                diagnostics["below_threshold"] += 1
                continue
            generated[key] = _attention_item(task, stream, membership)
    current = {item["id"]: item for item in observation["items"]}
    for key, value in current.items():
        if key.startswith("needs-finalize:") and (key not in generated or generated[key] != value):
            raise ValueError("current snapshot conflicts with generated finalization attention")
    result = validate_observation({**observation, "items": list((current | generated).values())}, observation["epic"])
    if len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > MAX_INPUT_BYTES:
        raise ValueError("combined observation exceeds maximum byte size; nothing clipped")
    return result, ages, diagnostics


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


FINALIZE_AGE_ENV = "LU_NEEDS_FINALIZE_MAX_AGE_MINUTES"
DEFAULT_FINALIZE_AGE_MINUTES = 30.0


def finalization_age(task: dict, *, now: datetime | None = None) -> dict:
    """One clock and finite threshold contract for blockers and inbox alerts."""
    clock = now if now is not None else datetime.now(UTC)
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("finalization clock must include a timezone")
    configured = os.environ.get(FINALIZE_AGE_ENV, str(DEFAULT_FINALIZE_AGE_MINUTES))
    try:
        threshold = float(configured)
        valid = math.isfinite(threshold) and threshold > 0
    except (ValueError, TypeError, OverflowError):
        threshold, valid = None, False
    age, state, terminal = None, "unknown", None
    try:
        terminal = _timestamp(task.get("finished_at"))
        seconds = (clock - terminal).total_seconds()
        if seconds >= 0:
            age, state = seconds / 60, "known"
        else:
            state = "future"
    except (ValueError, TypeError, OverflowError):
        pass
    return {
        "age_minutes": age,
        "age_state": state,
        "terminal": terminal.isoformat() if state == "known" else None,
        "threshold_minutes": threshold if valid else None,
        "configuration": "valid" if valid else "unknown",
        "attention": not valid or age is None or age > threshold,
    }


def finalization_attention(
    task_root: Path,
    *,
    initiator: str,
    stream_epic: int,
    now: datetime | None = None,
) -> tuple[list[dict], list[dict]]:
    """Read only this driver's stream; age never uses a task file's mtime.

    Blocker fields contain a stable age lower bound and terminal timestamp.
    Exact observed ages are diagnostics, outside fingerprints, so an unchanged
    blocker does not need another post just because the clock advanced.
    """
    if not _string(initiator) or initiator == "unknown" or type(stream_epic) is not int or stream_epic < 1:
        raise ValueError("finalization scan requires a known initiator and positive stream epic")
    if now is not None and (now.tzinfo is None or now.utcoffset() is None):
        raise ValueError("finalization clock must include a timezone")
    items, observations = [], []
    unknown_owner = False
    for task in _finalization_tasks(task_root):
        if task.get("status") != "needs_finalize":
            continue
        owner = task.get("initiator")
        if not _string(owner) or owner == "unknown":
            # Diagnose known-owned attention first, but never certify a scan
            # that leaves a possible owner unresolved.
            unknown_owner = True
            continue
        if owner != initiator:
            continue
        carrier = task.get("task_lifecycle") or {}
        identity = carrier.get("identity", {}) if isinstance(carrier, dict) else {}
        task_epic = identity.get("stream_epic") if isinstance(identity, dict) else None
        if type(task_epic) is not int or task_epic < 1:
            raise ValueError("owned finalization task stream scope unknown; attention is unknown")
        if task_epic != stream_epic:
            continue
        task_id, nonce = task.get("task_id"), task.get("run_nonce")
        if not _string(task_id) or not _string(nonce):
            raise ValueError("scoped finalization task identity unavailable")
        age_info = finalization_age(task, now=now)
        age, age_state = age_info["age_minutes"], age_info["age_state"]
        threshold = age_info["threshold_minutes"]
        valid_config = age_info["configuration"] == "valid"
        observations.append(
            {
                "task_id": task_id,
                "run_nonce": nonce,
                **{key: age_info[key] for key in ("age_minutes", "age_state", "threshold_minutes", "configuration")},
            }
        )
        if not age_info["attention"]:
            continue
        from scripts.delegate import is_public_cause

        reason = task.get("finalize_error") or task.get("last_error")
        # Historical task records may predate the public-reason persistence
        # boundary. Their raw diagnostic text never belongs in a Fleet post.
        if not is_public_cause(reason):
            reason = "finalization evidence unavailable; inspect private task diagnostics"
        age_text = f"age > {threshold:g} minutes" if age is not None and valid_config else f"age unknown ({age_state})"
        if not valid_config:
            age_text = "age threshold configuration unknown"
        # A normalized valid timestamp is stable across observations. Never echo invalid input.
        since = f"; terminal={age_info['terminal']}" if age_state == "known" else ""
        items.append(
            {
                "id": f"needs-finalize:{task_id}:{nonce}",
                "state": "needs_finalize",
                "owner": initiator,
                "waits_on": f"{age_text}{since}; reason={reason}",
                "action": "inspect retained task/head and finalization diagnostics; repair the failing gate and retry normal publication",
            }
        )
    if unknown_owner:
        raise ValueError("finalization task initiator unknown; attention is unknown")
    return items, observations


def include_finalization_attention(
    observation: dict,
    *,
    initiator: str,
    stream_epic: int,
) -> tuple[dict, list[dict]]:
    """Merge scoped task attention into the caller's complete blocker snapshot."""
    from scripts.common.task_store_paths import tasks_dir

    items, ages = finalization_attention(tasks_dir(), initiator=initiator, stream_epic=stream_epic)
    current = {item["id"]: item for item in observation["items"]}
    for item in items:
        if item["id"] in current and current[item["id"]] != item:
            raise ValueError("current snapshot conflicts with finalization attention")
        current[item["id"]] = item
    result = {**observation, "items": list(current.values())}
    return validate_observation(result, observation["epic"]), ages


def driver_finalization_scope(epic: str) -> tuple[str, tuple[int, ...]] | None:
    """Resolve the launcher's exact driver identity and registered stream epics."""
    initiator = os.environ.get("SESSION_HANDOFF_AGENT", "").strip()
    if not initiator:
        return None  # Non-driver CLI use has no authority to infer another seat.
    if os.environ.get("SESSION_EPIC") != epic:
        raise ValueError("finalization reporting requires the launcher's matching epic")
    return _reporting_scope(epic, initiator)


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


def record(
    path: Path,
    epic: str,
    observation: dict,
    receipt: dict,
    body: bytes,
    expect_generation: int,
    *,
    reporting_target: str = "epics",
) -> dict:
    """Record an already validated observation without inferring driver scope."""
    return _record(path, epic, observation, receipt, body, expect_generation, reporting_target=reporting_target)


def _record(
    path: Path,
    epic: str,
    observation: dict,
    receipt: dict,
    body: bytes,
    expect_generation: int,
    *,
    reporting_target: str = "epics",
    scope: tuple[str, tuple[int, ...]] | None = None,
    diagnostics: dict | None = None,
) -> dict:
    """Validate the caller's target and exact posted bytes, then advance under a stable lock."""
    validate_observation(observation, epic)
    if not observation["complete"]:
        raise ValueError("record requires complete: true")
    if type(expect_generation) is not int or expect_generation < 0:
        raise ValueError("expected generation must be a non-negative integer")
    if reporting_target not in REPORTING_TARGETS:
        raise ValueError("reporting target must be epics or cto")
    if not isinstance(receipt, dict) or receipt.get("recipient") != reporting_target:
        raise ValueError(f"receipt recipient must be {reporting_target}")
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
        if (stored["generation"] if stored else 0) != expect_generation:
            raise ValueError("stale expected generation")
        if scope is not None:
            observation, ages, coverage = _collect_finalization(observation, scope, stored)
            if diagnostics is not None:
                diagnostics.update(finalization_attention=ages, finalization_coverage=coverage)
        delta = compute_delta(observation, stored)
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
    return f"Blocker baseline: generation {generation}; {len(stored['items'])} recorded blockers"


EPILOG = """Examples:
  .venv/bin/python -m scripts.driver_blockers delta --epic infra --current blockers.json
  .venv/bin/python -m scripts.driver_blockers record --epic infra --current blockers.json --receipt receipt.json --body-file posted.md --expect-generation 0
  .venv/bin/python -m scripts.driver_blockers show --epic infra
Outputs: delta emits JSON; show emits a bounded summary. Only record writes the
private CTO-BLOCKERS-LEDGER.json sidecar and its lock next to DRIVER-STATE.md.
No command sends a message. Driver sessions include the full registered stream
using SESSION_HANDOFF_AGENT and SESSION_EPIC; the initiator must be an exact
registered slot. Outside a driver session use --task-initiator codex-infra
--task-stream-epic 6943 on BOTH delta and record. The member epic selects its
entire registered stream, never just that epic. Explicit and launcher scope
must agree. With neither scope, non-driver use infers no task ownership.
Complete means exhaustive coverage including explicit unknown attention, not
proven historical attribution. Known lifecycle membership takes precedence;
otherwise exact registered slots assign current reporting custody only.
Unknown original fields remain unknown; unmatched custody remains possible-owned.
LU_NEEDS_FINALIZE_MAX_AGE_MINUTES defaults to 30 finite positive minutes for
initial fully attributed attention. Unknown age/configuration or attribution
is attention, not green. Recorded generated runs survive threshold increases
and archive moves until positive exact-run status or other-stream proof.
One checked hot read covers every JSON unit. Prior IDs check every exact-stem
canonical/stamped/PID/nested archive copy without choosing a newest winner.
Unknown statuses cannot prove resolution. Unsafe, unreadable, contradictory or
missing required source stops the lane and preserves its baseline. The Infra
driver escalates for authentic original restoration; .moving and .unplaced
residue is unavailable. Dated residual acceptance never supplies resolution
proof or unstops the lane. Caller absence still uses standalone RESOLVED.
UNCHANGED means unchanged attention, not zero blockers. Exact ages and coverage
classes are diagnostics outside row fingerprints. Measure actual combined
observation, changed/resolved post, indented ledger and diagnostics bytes BEFORE
posting; stop on overflow. Current, receipt, body, ledger and combined observation
are bounded to 1 MiB; checked internal task records to 32 MiB. Nothing clips.
Current: exactly {"epic":"infra","complete":true,"items":[...]}; each item has
exactly five non-empty strings: id, state, owner, waits_on, action. Receipt:
Fleet Comms JSON with recipient matching --reporting-target (default epics),
message_id, content_sha256, created_at
(ISO-8601 with timezone). BODY is the exact UTF-8 posted body: post each
non-UNCHANGED item with all its fields on one line, and each RESOLVED item with
the exact case-sensitive standalone token RESOLVED <id> on its own non-active
line (no other fields or prose).
Ordinary reports go to epics. Only explicit CTO operator escalation uses
--reporting-target cto. The receipt never selects the expected target.
Existing CTO anchors stay readable; the original sidecar name and schema stay
unchanged. Anchors have no recipient field, so show reports a neutral baseline.
Exit codes: 0 success; 1 invalid/unreadable data or rejected record (no classes
on delta failure, previous ledger untouched); 2 invalid/missing CLI arguments.
Related: scripts.driver_state; docs/runbooks/fleet-blocker-reporting.md;
issues #10362 and #10419, epic #7919.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare current owned blockers with the last recorded blocker post.\n"
        "Use on driver wakes before posting; never use partial or unknown data to suppress a blocker.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for name, description in (
        ("delta", "Emit NEW/CHANGED/RESOLVED/UNCHANGED classes before posting."),
        ("record", "Record a successful blocker post only after target/receipt/body validation."),
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
        if name != "show":
            cmd.add_argument(
                "--task-initiator",
                help="Exact accountable dispatch initiator, e.g. codex-infra; requires --task-stream-epic. Default: launcher driver identity.",
            )
            cmd.add_argument(
                "--task-stream-epic",
                type=int,
                help="Member lifecycle epic, e.g. 6943, selecting its full registered stream; requires --task-initiator. Default: launcher registered stream epics.",
            )
        if name == "record":
            cmd.add_argument(
                "--receipt",
                type=Path,
                required=True,
                help="Successful Fleet Comms receipt JSON for the selected target, e.g. receipt.json.",
            )
            cmd.add_argument("--body-file", type=Path, required=True, help="Exact bytes posted, e.g. posted.md.")
            cmd.add_argument(
                "--reporting-target",
                choices=REPORTING_TARGETS,
                default="epics",
                help="Expected receipt recipient: epics (default); cto only for explicit operator escalation.",
            )
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
            diagnostics = {}
            automatic = driver_finalization_scope(args.epic)
            if args.task_initiator is not None or args.task_stream_epic is not None:
                if args.task_initiator is None or args.task_stream_epic is None:
                    raise ValueError("explicit scope requires both task initiator and stream epic")
                scope = _reporting_scope(args.epic, args.task_initiator, args.task_stream_epic)
                if automatic is not None and automatic != scope:
                    raise ValueError("explicit scope conflicts with launcher identity")
            else:
                scope = automatic
            if args.command == "delta":
                stored = load_ledger(path, args.epic)
                if stored is None:
                    with _ledger_directory(path) as directory_fd:
                        if directory_fd is not None and read_unit(directory_fd, path.name) is not None:
                            raise ValueError("existing ledger is invalid; cannot reconcile generated attention")
                if scope is not None:
                    observation, ages, coverage = _collect_finalization(observation, scope, stored)
                    diagnostics.update(finalization_attention=ages, finalization_coverage=coverage)
                result = compute_delta(observation, stored)
            else:
                updated = _record(
                    path, args.epic, observation, _read_json(args.receipt),
                    _read_bytes(args.body_file), args.expect_generation,
                    reporting_target=args.reporting_target, scope=scope, diagnostics=diagnostics,
                )
                result = {"generation": updated["generation"], "recorded": True}
            result.update(diagnostics)
            print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, TypeError, OverflowError, InstallError) as exc:
        # Do not expose private absolute locations through OSError diagnostics.
        reason = str(exc) if isinstance(exc, ValueError) else "data or sidecar operation failed"
        print(f"driver_blockers: {reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
