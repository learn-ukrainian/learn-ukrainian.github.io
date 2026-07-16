#!/usr/bin/env python3
"""Deterministically age, protect, and delete archived Codex threads."""

from __future__ import annotations

import argparse
import dataclasses
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import tomllib
import uuid
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TextIO

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.orchestration.task_family import codex_state, rollover_registry

STATE_SCHEMA_VERSION = "archived-thread-cleanup-state.v1"
RECEIPT_SCHEMA_VERSION = "archived-thread-cleanup-receipt.v1"
RETENTION_DAYS = 30
OBSERVATION_INTERVAL_DAYS = 7
CURRENT_THREAD_ENV_VARS = (
    "LEARN_UKRAINIAN_SESSION_ID",
    "CODEX_THREAD_ID",
    "CODEX_SESSION_ID",
    "CODEX_SESSION",
)
UUID_PATTERN = re.compile(
    r"(?<![0-9A-Fa-f])"
    r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-"
    r"[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"
    r"(?![0-9A-Fa-f])"
)

DeleteRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
Sleep = Callable[[float], None]


class CleanupError(RuntimeError):
    """Base error for deterministic cleanup failures."""


class CleanupBusyError(CleanupError):
    """Another cleanup process owns the exclusive lock."""


class CleanupStateError(CleanupError):
    """Persisted observation state is missing required structure."""


@dataclass(frozen=True)
class ProtectionSnapshot:
    pinned_ids: frozenset[str]
    current_ids: frozenset[str]
    automation_ids: frozenset[str]
    rollover_ids: frozenset[str]
    relevant_roots: tuple[Path, ...]
    errors: tuple[str, ...]

    def reasons_for(self, thread_id: str) -> list[str]:
        reasons: list[str] = []
        if thread_id in self.pinned_ids:
            reasons.append("pinned")
        if thread_id in self.current_ids:
            reasons.append("current_thread")
        if thread_id in self.automation_ids:
            reasons.append("automation_reference")
        if thread_id in self.rollover_ids:
            reasons.append("live_rollover_reference")
        if self.errors:
            reasons.append("protection_registry_unavailable")
        return reasons


def _now_utc(now: datetime | None) -> datetime:
    value = now or datetime.now(UTC)
    if value.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return value.astimezone(UTC)


def _isoformat(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any, *, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise CleanupStateError(f"{field} must be a non-empty timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CleanupStateError(f"{field} is not an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise CleanupStateError(f"{field} must be timezone-aware")
    return parsed.astimezone(UTC)


def _normalize_uuid(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("thread id must be a string UUID")
    return str(uuid.UUID(value.strip()))


def _uuid_strings(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            found.update(_uuid_strings(key))
            found.update(_uuid_strings(child))
    elif isinstance(value, (list, tuple)):
        for child in value:
            found.update(_uuid_strings(child))
    elif isinstance(value, str):
        for match in UUID_PATTERN.finditer(value):
            found.add(str(uuid.UUID(match.group(0))))
    return found


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CleanupError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CleanupError(f"{label} must be a JSON object: {path}")
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


@contextmanager
def cleanup_lock(state_dir: Path) -> Iterable[TextIO]:
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(state_dir, 0o700)
    lock_path = state_dir / "cleanup-v1.lock"
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CleanupBusyError(f"cleanup lock is already held: {lock_path}") from exc
        yield handle
    finally:
        handle.close()


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": STATE_SCHEMA_VERSION, "observations": {}}
    payload = _read_json_object(path, label="cleanup state")
    if payload.get("schema_version") != STATE_SCHEMA_VERSION:
        raise CleanupStateError(f"unsupported cleanup state version in {path}")
    observations = payload.get("observations")
    if not isinstance(observations, dict):
        raise CleanupStateError(f"cleanup state observations must be an object: {path}")
    for raw_id, observation in observations.items():
        try:
            normalized = _normalize_uuid(raw_id)
        except (ValueError, AttributeError) as exc:
            raise CleanupStateError(f"cleanup state has invalid thread id: {raw_id!r}") from exc
        if normalized != raw_id or not isinstance(observation, dict):
            raise CleanupStateError(f"cleanup state has malformed observation for {raw_id!r}")
        fingerprint = observation.get("fingerprint")
        count = observation.get("observation_count")
        if not isinstance(fingerprint, str) or len(fingerprint) != 64:
            raise CleanupStateError(f"cleanup state fingerprint is invalid for {raw_id}")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise CleanupStateError(f"cleanup state observation count is invalid for {raw_id}")
        _parse_time(observation.get("first_observed_at"), field="first_observed_at")
        _parse_time(observation.get("last_observed_at"), field="last_observed_at")
    return payload


def _thread_fingerprint(record: codex_state.CleanupThreadRecord) -> str:
    serialized = json.dumps(
        dataclasses.asdict(record),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _load_global_state(codex_home: Path) -> tuple[set[str], set[Path], list[str]]:
    path = codex_home / ".codex-global-state.json"
    errors: list[str] = []
    try:
        payload = _read_json_object(path, label="Codex global state")
    except CleanupError as exc:
        return set(), set(), [str(exc)]

    pinned: set[str] = set()
    raw_pinned = payload.get("pinned-thread-ids")
    if not isinstance(raw_pinned, list):
        errors.append(f"pin registry is missing or malformed: {path}")
    else:
        for raw_id in raw_pinned:
            try:
                pinned.add(_normalize_uuid(raw_id))
            except (ValueError, AttributeError):
                errors.append(f"pin registry contains a non-UUID value: {raw_id!r}")

    roots: set[Path] = set()
    raw_roots = payload.get("active-workspace-roots", [])
    if not isinstance(raw_roots, list) or any(not isinstance(item, str) for item in raw_roots):
        errors.append(f"active workspace root registry is malformed: {path}")
    else:
        roots.update(Path(item).expanduser() for item in raw_roots)
    return pinned, roots, errors


def _load_automation_references(codex_home: Path) -> tuple[set[str], set[Path], list[str]]:
    automation_ids: set[str] = set()
    roots: set[Path] = set()
    errors: list[str] = []
    automations_dir = codex_home / "automations"
    if not automations_dir.exists():
        return automation_ids, roots, errors
    if not automations_dir.is_dir():
        return automation_ids, roots, [f"automation registry is not a directory: {automations_dir}"]
    for path in sorted(automations_dir.glob("**/automation.toml")):
        try:
            with path.open("rb") as handle:
                payload = tomllib.load(handle)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"cannot read automation {path}: {exc}")
            continue
        automation_ids.update(_uuid_strings(payload))
        cwds = payload.get("cwds", [])
        if isinstance(cwds, list) and all(isinstance(item, str) for item in cwds):
            roots.update(Path(item).expanduser() for item in cwds)
        elif "cwds" in payload:
            errors.append(f"automation cwds is malformed: {path}")
    return automation_ids, roots, errors


def _relevant_rollover_roots(paths: Iterable[Path]) -> tuple[Path, ...]:
    roots: set[Path] = set()
    for raw_path in paths:
        path = raw_path.expanduser()
        for candidate in (path, *path.parents):
            if (candidate / ".agent" / "thread-rollovers").is_dir():
                roots.add(candidate.resolve())
                break
    return tuple(sorted(roots))


def _load_live_rollover_references(roots: Iterable[Path]) -> tuple[set[str], list[str]]:
    protected: set[str] = set()
    errors: list[str] = []
    for root in roots:
        rollover_root = root / ".agent" / "thread-rollovers"
        for path in sorted(rollover_root.glob("*/*/lease.json")):
            try:
                payload = _read_json_object(path, label="rollover lease")
                record = rollover_registry.record_from_lease(root, path, payload)
                if rollover_registry.is_live_pending(record):
                    protected.update(_uuid_strings(payload))
            except (CleanupError, OSError, ValueError) as exc:
                errors.append(f"cannot classify rollover lease {path}: {exc}")
    return protected, errors


def load_protections(
    *,
    codex_home: Path,
    records: Iterable[codex_state.CleanupThreadRecord],
    environ: Mapping[str, str] | None = None,
    current_cwd: Path | None = None,
) -> ProtectionSnapshot:
    """Load all fail-closed protection registries for one cleanup observation."""
    environment = environ if environ is not None else os.environ
    pinned, global_roots, global_errors = _load_global_state(codex_home)
    automation_ids, automation_roots, automation_errors = _load_automation_references(codex_home)
    current_ids: set[str] = set()
    for name in CURRENT_THREAD_ENV_VARS:
        value = environment.get(name)
        if not value:
            continue
        try:
            current_ids.add(_normalize_uuid(value))
        except ValueError:
            # CODEX_SESSION is also used as a boolean marker by legacy scripts.
            if name != "CODEX_SESSION":
                global_errors.append(f"{name} does not contain an exact UUID")

    search_roots = {Path(record.cwd).expanduser() for record in records if record.cwd}
    search_roots.update(global_roots)
    search_roots.update(automation_roots)
    search_roots.add((current_cwd or Path.cwd()).expanduser())
    relevant_roots = _relevant_rollover_roots(search_roots)
    rollover_ids, rollover_errors = _load_live_rollover_references(relevant_roots)
    return ProtectionSnapshot(
        pinned_ids=frozenset(pinned),
        current_ids=frozenset(current_ids),
        automation_ids=frozenset(automation_ids),
        rollover_ids=frozenset(rollover_ids),
        relevant_roots=relevant_roots,
        errors=tuple(sorted({*global_errors, *automation_errors, *rollover_errors})),
    )


def _allocated_bytes(path_value: str) -> int:
    if not path_value:
        return 0
    path = Path(path_value).expanduser()
    try:
        stat = path.stat()
    except OSError:
        return 0
    blocks = getattr(stat, "st_blocks", 0)
    return int(blocks * 512) if blocks else int(stat.st_size)


def _default_runner(codex_home: Path) -> DeleteRunner:
    def run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(codex_home)
        return subprocess.run(
            list(command),
            capture_output=True,
            check=False,
            env=environment,
            text=True,
            timeout=120,
        )

    return run


def _reconcile_absent(
    db_path: Path,
    thread_id: str,
    *,
    attempts: int = 5,
    sleep: Sleep = time.sleep,
) -> bool:
    for attempt in range(attempts):
        try:
            codex_state.read_cleanup_thread_record(
                db_path,
                thread_id=thread_id,
                read_window_seconds=0.25,
            )
        except codex_state.CodexStateMissingTaskError:
            return True
        if attempt + 1 < attempts:
            sleep(0.1)
    return False


def _observe(
    previous: Mapping[str, Any] | None,
    *,
    fingerprint: str,
    now: datetime,
    observation_interval_days: int,
) -> tuple[dict[str, Any], bool]:
    now_text = _isoformat(now)
    if previous is None or previous.get("fingerprint") != fingerprint:
        return (
            {
                "fingerprint": fingerprint,
                "first_observed_at": now_text,
                "last_observed_at": now_text,
                "observation_count": 1,
            },
            False,
        )
    first = _parse_time(previous.get("first_observed_at"), field="first_observed_at")
    count = int(previous.get("observation_count", 0)) + 1
    observation = {
        "fingerprint": fingerprint,
        "first_observed_at": _isoformat(first),
        "last_observed_at": now_text,
        "observation_count": count,
    }
    mature = count >= 2 and now - first >= timedelta(days=observation_interval_days)
    return observation, mature


def _receipt_path(state_dir: Path, now: datetime) -> Path:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    return state_dir / "receipts" / "v1" / f"{stamp}-{os.getpid()}-{uuid.uuid4().hex[:12]}.json"


def run_cleanup(
    *,
    apply: bool = False,
    codex_home: Path | None = None,
    db_path: Path | None = None,
    state_dir: Path | None = None,
    now: datetime | None = None,
    runner: DeleteRunner | None = None,
    sleep: Sleep = time.sleep,
    codex_binary: str = "codex",
    environ: Mapping[str, str] | None = None,
    current_cwd: Path | None = None,
    retention_days: int = RETENTION_DAYS,
    observation_interval_days: int = OBSERVATION_INTERVAL_DAYS,
) -> dict[str, Any]:
    """Run one locked cleanup observation and optionally apply mature deletions."""
    clock = _now_utc(now)
    if retention_days < 1:
        raise ValueError("retention_days must be at least 1")
    if observation_interval_days < 1:
        raise ValueError("observation_interval_days must be at least 1")
    home = (codex_home or Path.home() / ".codex").expanduser()
    cleanup_dir = (state_dir or home / "thread-cleanup").expanduser()
    database = db_path or codex_state.discover_state_database(codex_home=home)
    delete_runner = runner or _default_runner(home)
    state_path = cleanup_dir / "state-v1.json"

    with cleanup_lock(cleanup_dir):
        state = _load_state(state_path)
        previous_observations = state["observations"]
        records = codex_state.list_archived_cleanup_threads(database)
        protections = load_protections(
            codex_home=home,
            records=records,
            environ=environ,
            current_cwd=current_cwd,
        )
        cutoff = int((clock - timedelta(days=retention_days)).timestamp())
        observations: dict[str, Any] = {}
        outcomes: list[dict[str, Any]] = []
        mature_ids: list[str] = []

        for record in records:
            fingerprint = _thread_fingerprint(record)
            entry: dict[str, Any] = {
                "thread_id": record.thread_id,
                "title": record.title,
                "archived_at": record.archived_at,
                "updated_at": record.updated_at,
                "fingerprint": fingerprint,
                "bytes_before": _allocated_bytes(record.rollout_path),
            }
            reasons = protections.reasons_for(record.thread_id)
            if record.archived_at is None:
                entry.update(outcome="protected", reasons=["invalid_archive_state", *reasons])
            elif record.archived_at > cutoff:
                entry.update(outcome="retained", reasons=["retention_period", *reasons])
            elif reasons:
                entry.update(outcome="protected", reasons=reasons)
            else:
                observation, mature = _observe(
                    previous_observations.get(record.thread_id),
                    fingerprint=fingerprint,
                    now=clock,
                    observation_interval_days=observation_interval_days,
                )
                observations[record.thread_id] = observation
                if mature:
                    mature_ids.append(record.thread_id)
                    entry.update(outcome="ready", reasons=[])
                else:
                    entry.update(outcome="observing", reasons=["two_observations_seven_days_apart"])
                entry["observation"] = observation
            outcomes.append(entry)

        state = {
            "schema_version": STATE_SCHEMA_VERSION,
            "updated_at": _isoformat(clock),
            "observations": observations if not protections.errors else {},
        }
        _write_json(state_path, state)

        outcome_by_id = {entry["thread_id"]: entry for entry in outcomes}
        if apply and not protections.errors:
            for thread_id in mature_ids:
                entry = outcome_by_id[thread_id]
                try:
                    refreshed = codex_state.read_cleanup_thread_record(database, thread_id=thread_id)
                except codex_state.CodexStateError as exc:
                    entry.update(outcome="refresh_failed", error=str(exc))
                    continue
                refreshed_fingerprint = _thread_fingerprint(refreshed)
                if (
                    refreshed_fingerprint != entry["fingerprint"]
                    or not refreshed.archived
                    or refreshed.archived_at is None
                    or refreshed.archived_at > cutoff
                ):
                    observations[thread_id], _ = _observe(
                        None,
                        fingerprint=refreshed_fingerprint,
                        now=clock,
                        observation_interval_days=observation_interval_days,
                    )
                    entry.update(outcome="changed_before_delete", refreshed_fingerprint=refreshed_fingerprint)
                    continue

                refreshed_protections = load_protections(
                    codex_home=home,
                    records=records,
                    environ=environ,
                    current_cwd=current_cwd,
                )
                refreshed_reasons = refreshed_protections.reasons_for(thread_id)
                if refreshed_reasons:
                    observations.pop(thread_id, None)
                    entry.update(outcome="protected_before_delete", reasons=refreshed_reasons)
                    continue

                bytes_before = _allocated_bytes(refreshed.rollout_path)
                command = (codex_binary, "delete", "--force", thread_id)
                try:
                    result = delete_runner(command)
                    returncode = int(result.returncode)
                    stderr = (result.stderr or "").strip()[-500:]
                except Exception as exc:
                    entry.update(outcome="delete_failed", error=f"runner failure: {exc}")
                    continue
                try:
                    absent = _reconcile_absent(database, thread_id, sleep=sleep)
                except codex_state.CodexStateError as exc:
                    entry.update(
                        command=list(command),
                        command_returncode=returncode,
                        stderr=stderr,
                        outcome="reconciliation_failed",
                        error=str(exc),
                    )
                    continue
                bytes_after = _allocated_bytes(refreshed.rollout_path)
                entry.update(
                    command=list(command),
                    command_returncode=returncode,
                    stderr=stderr,
                    bytes_before=bytes_before,
                    bytes_after=bytes_after,
                    reclaimed_bytes=max(0, bytes_before - bytes_after),
                    outcome=(
                        "deleted"
                        if absent and returncode == 0
                        else "deleted_with_cli_error"
                        if absent
                        else "reconciliation_failed"
                        if returncode == 0
                        else "delete_failed"
                    ),
                )
                if absent:
                    observations.pop(thread_id, None)

            state["observations"] = observations
            _write_json(state_path, state)
        elif apply:
            for thread_id in mature_ids:
                outcome_by_id[thread_id].update(
                    outcome="apply_blocked",
                    reasons=["protection_registry_unavailable"],
                )
        else:
            for thread_id in mature_ids:
                outcome_by_id[thread_id]["outcome"] = "ready_dry_run"

        summary: dict[str, int] = {}
        for entry in outcomes:
            outcome = str(entry["outcome"])
            summary[outcome] = summary.get(outcome, 0) + 1
        summary["archived_threads"] = len(records)
        summary["reclaimed_bytes"] = sum(int(entry.get("reclaimed_bytes", 0)) for entry in outcomes)
        receipt = {
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "mode": "apply" if apply else "dry-run",
            "started_at": _isoformat(clock),
            "policy": {
                "retention_days": retention_days,
                "observation_interval_days": observation_interval_days,
                "required_unchanged_observations": 2,
            },
            "codex_home": str(home),
            "database": str(database),
            "state_path": str(state_path),
            "protection_errors": list(protections.errors),
            "relevant_rollover_roots": [str(path) for path in protections.relevant_roots],
            "summary": summary,
            "outcomes": outcomes,
        }
        receipt_path = _receipt_path(cleanup_dir, clock)
        receipt["receipt_path"] = str(receipt_path)
        _write_json(receipt_path, receipt)
        return receipt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="apply mature deletions (default is a stateful dry-run observation)",
    )
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--db", type=Path, help="explicit Codex state_*.sqlite path")
    parser.add_argument("--state-dir", type=Path, help="override versioned state/receipt directory")
    parser.add_argument("--codex-binary", default="codex")
    parser.add_argument("--repo-root", type=Path, help="repository root used for rollover protection")
    parser.add_argument("--retention-days", type=int, default=RETENTION_DAYS)
    parser.add_argument(
        "--observation-interval-days",
        type=int,
        default=OBSERVATION_INTERVAL_DAYS,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        receipt = run_cleanup(
            apply=args.apply,
            codex_home=args.codex_home,
            db_path=args.db,
            state_dir=args.state_dir,
            codex_binary=args.codex_binary,
            current_cwd=args.repo_root,
            retention_days=args.retention_days,
            observation_interval_days=args.observation_interval_days,
        )
    except (CleanupError, codex_state.CodexStateError, OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": "blocked" if args.apply and receipt["protection_errors"] else "ok",
                "mode": receipt["mode"],
                "receipt_path": receipt["receipt_path"],
                "summary": receipt["summary"],
                "protection_errors": receipt["protection_errors"],
            },
            sort_keys=True,
        )
    )
    failed = sum(
        count
        for outcome, count in receipt["summary"].items()
        if outcome in {"apply_blocked", "delete_failed", "reconciliation_failed", "refresh_failed"}
    )
    return 2 if failed or (args.apply and receipt["protection_errors"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
