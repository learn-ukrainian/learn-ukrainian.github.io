#!/usr/bin/env python3
"""Crash-safe, manifest-ordered coordinator above one-module track completion."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from filelock import FileLock, Timeout
from jsonschema import Draft202012Validator, FormatChecker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.common.repo_root import main_checkout_root
from scripts.orchestration.curriculum_readiness import (
    ReadinessError,
    evaluate_preparation,
    load_manifest_track,
    module_bundle_state,
)

DEFAULT_CONFIG_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/curriculum-lifecycle/config/coordinator.v1.yaml"
)
CONFIG_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/curriculum-lifecycle/schema/coordinator-config.v1.schema.json"
)
LEDGER_SCHEMA_PATH = (
    PROJECT_ROOT / "agents_extensions/shared/curriculum-lifecycle/schema/coordinator-ledger.v1.schema.json"
)
_TARGET_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SCOPES = frozenset({"all", "built", "unbuilt", "stale", "one"})
_TERMINAL_DISPOSITIONS = frozenset({"complete", "no-change"})

HealthProbe = Callable[[], Mapping[str, Any]]
ReadinessEvaluator = Callable[[str, str], Mapping[str, Any]]


class CoordinatorError(RuntimeError):
    """Raised when coordinator state cannot advance safely."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _parse_time(raw: str) -> datetime:
    try:
        value = datetime.fromisoformat(raw)
    except (TypeError, ValueError) as exc:
        raise CoordinatorError(f"invalid coordinator timestamp: {raw!r}") from exc
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CoordinatorError(f"invalid JSON document {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CoordinatorError(f"JSON document must be an object: {path}")
    return value


def _validate(value: Mapping[str, Any], schema_path: Path, label: str) -> None:
    schema = _load_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        raise CoordinatorError(f"invalid JSON schema for {label}: {exc}") from exc
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        key=lambda item: tuple(str(part) for part in item.path),
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise CoordinatorError(f"{label} failed schema validation at {location}: {error.message}")


def _repo_relative_path(repo_root: Path, raw: str) -> Path:
    path = Path(raw)
    if not raw or path.is_absolute() or ".." in path.parts or "\\" in raw or raw.startswith("~"):
        raise CoordinatorError(f"configured path must be repository-relative: {raw!r}")
    resolved = (repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise CoordinatorError(f"configured path escapes repository: {raw!r}") from exc
    return resolved


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and semantically validate the versioned coordinator policy."""
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8", errors="strict"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise CoordinatorError(f"invalid coordinator config {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CoordinatorError(f"coordinator config must be a mapping: {path}")
    _validate(value, CONFIG_SCHEMA_PATH, "coordinator config")
    if value["default_wave_size"] > value["maximum_wave_size"]:
        raise CoordinatorError("default_wave_size cannot exceed maximum_wave_size")
    group_ids = [group["id"] for group in value["health"]["capability_groups"]]
    if len(group_ids) != len(set(group_ids)):
        raise CoordinatorError("health capability group ids must be unique")
    for group in value["health"]["capability_groups"]:
        if group["minimum_available"] > len(group["lanes"]):
            raise CoordinatorError(
                f"health group {group['id']} requires more lanes than it declares"
            )
    return value


def _runtime_root(
    repo_root: Path,
    config: Mapping[str, Any],
    override: Path | None,
) -> Path:
    if override is not None:
        return override.resolve()
    return _repo_relative_path(main_checkout_root(repo_root), str(config["runtime_root"]))


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    return _load_json(path) if path.is_file() else None


def _lock(runtime_root: Path) -> FileLock:
    runtime_root.mkdir(parents=True, exist_ok=True)
    return FileLock(str(runtime_root / "coordinator.lock"), timeout=0)


def _locked(runtime_root: Path) -> FileLock:
    try:
        return _lock(runtime_root)
    except Timeout as exc:
        raise CoordinatorError("curriculum coordinator is busy; retry the exact operation") from exc


def _ledger_path(runtime_root: Path, run_id: str) -> Path:
    if not re.fullmatch(r"clc-[0-9a-f]{24}", run_id):
        raise CoordinatorError(f"invalid coordinator run id: {run_id!r}")
    return runtime_root / "runs" / f"{run_id}.json"


def _lease_path(runtime_root: Path, kind: str, name: str = "mutation") -> Path:
    if kind not in {"global", "track", "module"}:
        raise CoordinatorError(f"invalid lease kind: {kind}")
    if not _TARGET_RE.fullmatch(name.replace("--", "-")):
        raise CoordinatorError(f"invalid lease name: {name!r}")
    directory = {"global": "global", "track": "tracks", "module": "modules"}[kind]
    return runtime_root / "leases" / directory / f"{name}.json"


def _lease_document(
    *,
    run_id: str,
    owner: str,
    lease_seconds: int,
    track: str,
    slug: str | None = None,
) -> dict[str, Any]:
    now = _now()
    return {
        "run_id": run_id,
        "owner": owner,
        "track": track,
        "slug": slug,
        "renewed_at": _iso(now),
        "expires_at": _iso(now + timedelta(seconds=lease_seconds)),
    }


def _claim_lease(
    path: Path,
    *,
    run_id: str,
    owner: str,
    lease_seconds: int,
    track: str,
    slug: str | None = None,
) -> None:
    existing = _read_optional_json(path)
    if existing is not None and existing.get("run_id") != run_id:
        state = "stale" if _parse_time(str(existing.get("expires_at"))) <= _now() else "active"
        raise CoordinatorError(
            f"{state} lease belongs to run {existing.get('run_id')}; adjudicate it instead of stealing"
        )
    _atomic_write_json(
        path,
        _lease_document(
            run_id=run_id,
            owner=owner,
            lease_seconds=lease_seconds,
            track=track,
            slug=slug,
        ),
    )


def _require_live_lease(path: Path, run_id: str, label: str) -> dict[str, Any]:
    lease = _read_optional_json(path)
    if lease is None or lease.get("run_id") != run_id:
        raise CoordinatorError(f"{label} lease is not owned by run {run_id}; resume the exact run")
    if _parse_time(str(lease.get("expires_at"))) <= _now():
        raise CoordinatorError(f"{label} lease expired; resume the exact run id")
    return lease


def _release_owned_lease(path: Path, run_id: str) -> None:
    lease = _read_optional_json(path)
    if lease is not None and lease.get("run_id") == run_id:
        path.unlink()
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


def _event_id(event: str, details: Mapping[str, Any]) -> str:
    return f"{event.lower().replace('_', '-')}-{_sha256({'event': event, 'details': details})[:24]}"


def _append_event(ledger: dict[str, Any], event: str, details: Mapping[str, Any]) -> bool:
    event_id = _event_id(event, details)
    if any(item["event_id"] == event_id for item in ledger["history"]):
        return False
    ledger["history"].append(
        {
            "sequence": len(ledger["history"]) + 1,
            "event_id": event_id,
            "event": event,
            "at": _iso(_now()),
            "details": dict(details),
        }
    )
    return True


def _validate_ledger(ledger: Mapping[str, Any]) -> None:
    _validate(ledger, LEDGER_SCHEMA_PATH, "coordinator ledger")
    expected_request_sha = _sha256(
        {
            "owner": ledger["owner"],
            "request": ledger["request"],
            "authority": ledger["authority"],
        }
    )
    if ledger["request_sha256"] != expected_request_sha:
        raise CoordinatorError("coordinator request identity does not match its authority and selector")
    if ledger["run_id"] != f"clc-{expected_request_sha[:24]}":
        raise CoordinatorError("coordinator run id does not match its request identity")
    queue = ledger["queue"]
    slugs = [item["slug"] for item in queue]
    if len(slugs) != len(set(slugs)):
        raise CoordinatorError("coordinator queue contains duplicate modules")
    wave_size = ledger["request"]["wave_size"]
    for position, item in enumerate(queue):
        expected_prerequisites = [] if position == 0 else [queue[position - 1]["slug"]]
        if item["position"] != position or item["wave"] != position // wave_size + 1:
            raise CoordinatorError("coordinator queue positions or waves are not canonical")
        if item["track"] != ledger["request"]["track"]:
            raise CoordinatorError("coordinator queue contains a module from another track")
        if position and item["manifest_index"] <= queue[position - 1]["manifest_index"]:
            raise CoordinatorError("coordinator queue is not in manifest order")
        if item["prerequisites"] != expected_prerequisites:
            raise CoordinatorError("coordinator queue prerequisites are not canonical")
    for sequence, event in enumerate(ledger["history"], start=1):
        if event["sequence"] != sequence:
            raise CoordinatorError("coordinator event sequence is not contiguous")
        if event["event_id"] != _event_id(event["event"], event["details"]):
            raise CoordinatorError("coordinator event identity does not match its payload")
    _validate_event_transitions(ledger)


def _validate_event_transitions(ledger: Mapping[str, Any]) -> None:
    history: list[Mapping[str, Any]] = []
    queue = ledger["queue"]
    for event in ledger["history"]:
        state = derive_state({**ledger, "history": history})
        name = event["event"]
        details = event["details"]
        incomplete = next(
            (item for item in queue if state["modules"][item["slug"]] != "complete"),
            None,
        )
        if name == "RUN_STARTED":
            if history or details["request_sha256"] != ledger["request_sha256"]:
                raise CoordinatorError("RUN_STARTED must be the first event and bind the request identity")
        elif not history:
            raise CoordinatorError("coordinator history must begin with RUN_STARTED")
        elif state["status"] == "abandoned":
            raise CoordinatorError("an abandoned coordinator run cannot advance")
        elif name == "RUN_ABANDONED":
            if (
                details["prior_status"] != state["status"]
                or details["current_module"] != state["current_module"]
                or details["recorded_manifest_sha256"] != ledger["authority"]["manifest_sha256"]
                or not details["manifest_changed"]
            ):
                raise CoordinatorError("run abandonment evidence does not match replay state")
        elif name == "RUN_PAUSED":
            if state["current_module"] is not None or incomplete is None or details["wave"] != incomplete["wave"]:
                raise CoordinatorError("RUN_PAUSED does not match the next safe wave boundary")
        elif name == "RUN_RESUMED":
            if state["status"] == "complete":
                raise CoordinatorError("a completed coordinator run cannot resume")
            if details["reason"] == "wave-health-restored" and state["status"] != "paused":
                raise CoordinatorError("wave-health restoration requires a paused run")
        elif name == "WAVE_HEALTH_ACCEPTED":
            if (
                state["current_module"] is not None
                or incomplete is None
                or details["wave"] != incomplete["wave"]
                or details["wave"] in state["accepted_waves"]
            ):
                raise CoordinatorError("wave health acceptance is duplicated or out of order")
        elif name == "MODULE_ACQUIRED":
            if (
                state["current_module"] is not None
                or incomplete is None
                or details["slug"] != incomplete["slug"]
                or details["track"] != incomplete["track"]
                or details["manifest_index"] != incomplete["manifest_index"]
                or details["wave"] != incomplete["wave"]
                or details["attempt"]
                != 1
                + sum(
                    prior["event"] == "MODULE_ACQUIRED"
                    and prior["details"].get("slug") == details["slug"]
                    for prior in history
                )
                or details["wave"] not in state["accepted_waves"]
                or any(state["modules"].get(slug) != "complete" for slug in incomplete["prerequisites"])
            ):
                raise CoordinatorError("module acquisition violates queue, wave, or prerequisite order")
        elif name == "MODULE_FINISHED":
            active_acquisition = next(
                (
                    prior
                    for prior in reversed(history)
                    if prior["event"] == "MODULE_ACQUIRED"
                    and prior["details"]["slug"] == details["slug"]
                ),
                None,
            )
            if (
                state["current_module"] != details["slug"]
                or details["track"] != ledger["request"]["track"]
                or active_acquisition is None
                or details["attempt"] != active_acquisition["details"]["attempt"]
            ):
                raise CoordinatorError("module result does not match the active acquisition")
        elif name == "WAVE_COMPLETED":
            wave = int(details["wave"])
            wave_items = [item for item in queue if item["wave"] == wave]
            if (
                not wave_items
                or wave in state["completed_waves"]
                or any(state["modules"][item["slug"]] != "complete" for item in wave_items)
            ):
                raise CoordinatorError("wave completion is duplicated or premature")
        elif name == "RUN_COMPLETED" and (
            state["status"] == "complete"
            or details["module_count"] != len(queue)
            or state["current_module"] is not None
            or any(value != "complete" for value in state["modules"].values())
        ):
            raise CoordinatorError("run completion is premature")
        history.append(event)
    if not history or history[0]["event"] != "RUN_STARTED":
        raise CoordinatorError("coordinator history must begin with RUN_STARTED")


def _read_ledger(path: Path) -> dict[str, Any]:
    ledger = _load_json(path)
    _validate_ledger(ledger)
    return ledger


def _boundary_index(raw: str | None, modules: Sequence[str], *, default: int) -> int:
    if raw is None:
        return default
    if raw.isdigit():
        index = int(raw) - 1
        if index < 0 or index >= len(modules):
            raise CoordinatorError(f"manifest boundary is outside 1..{len(modules)}: {raw}")
        return index
    if raw not in modules:
        raise CoordinatorError(f"manifest boundary is not active: {raw}")
    return modules.index(raw)


def _readiness_snapshot(
    track: str,
    slug: str,
    evaluator: ReadinessEvaluator,
) -> dict[str, Any]:
    try:
        result = evaluator(track, slug)
    except ReadinessError as exc:
        raise CoordinatorError(f"preparation readiness failed for {track}/{slug}: {exc}") from exc
    required = {"module_state", "preparation_state", "state", "next_action", "preparation_identity"}
    if not isinstance(result, Mapping) or not required.issubset(result):
        raise CoordinatorError(f"invalid preparation readiness result for {track}/{slug}")
    return {key: result[key] for key in sorted(required)}


def _build_queue(
    *,
    repo_root: Path,
    track: str,
    scope: str,
    module: str | None,
    start: str | None,
    end: str | None,
    wave_size: int,
    manifest_path: Path,
    readiness_evaluator: ReadinessEvaluator,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    manifest, ordered = load_manifest_track(repo_root, track, manifest_path)
    modules = list(ordered)
    if scope == "one":
        if module is None or module not in modules:
            raise CoordinatorError("scope=one requires one active --module")
        if start is not None or end is not None:
            raise CoordinatorError("scope=one cannot be combined with range boundaries")
        candidates = [module]
    else:
        if module is not None:
            raise CoordinatorError("--module is only valid with scope=one")
        first = _boundary_index(start, modules, default=0)
        last = _boundary_index(end, modules, default=len(modules) - 1)
        if first > last:
            raise CoordinatorError("manifest range start occurs after its end")
        candidates = modules[first : last + 1]

    selected: list[tuple[str, str, str, str | None]] = []
    for slug in candidates:
        bundle_state = module_bundle_state(repo_root, track, slug)
        preparation_state = "not-evaluated"
        preparation_identity = None
        if scope == "stale":
            readiness = _readiness_snapshot(track, slug, readiness_evaluator)
            preparation_state = str(readiness["preparation_state"])
            preparation_identity = readiness["preparation_identity"]
            if preparation_state != "stale":
                continue
        elif (scope == "built" and bundle_state != "built") or (
            scope == "unbuilt" and bundle_state != "unbuilt"
        ):
            continue
        selected.append((slug, bundle_state, preparation_state, preparation_identity))
    if not selected:
        raise CoordinatorError("selector produced an empty curriculum queue")

    queue: list[dict[str, Any]] = []
    for position, (slug, bundle_state, preparation_state, preparation_identity) in enumerate(selected):
        queue.append(
            {
                "position": position,
                "manifest_index": modules.index(slug),
                "track": track,
                "slug": slug,
                "wave": position // wave_size + 1,
                "prerequisites": [] if position == 0 else [selected[position - 1][0]],
                "initial_module_state": bundle_state,
                "initial_preparation_state": preparation_state,
                "initial_preparation_identity": preparation_identity,
            }
        )
    authority = {
        "manifest_path": Path(manifest["path"]).resolve().relative_to(repo_root.resolve()).as_posix(),
        "manifest_sha256": str(manifest["sha256"]),
    }
    return queue, authority


def _manifest_authority(repo_root: Path, track: str, manifest_path: Path) -> dict[str, str]:
    manifest, _ordered = load_manifest_track(repo_root, track, manifest_path)
    return {
        "manifest_path": Path(manifest["path"]).resolve().relative_to(repo_root.resolve()).as_posix(),
        "manifest_sha256": str(manifest["sha256"]),
    }


def derive_state(ledger: Mapping[str, Any]) -> dict[str, Any]:
    """Replay immutable events into compact run and per-module state."""
    modules = {item["slug"]: "pending" for item in ledger["queue"]}
    current_module: str | None = None
    paused = False
    completed = False
    abandoned = False
    accepted_waves: set[int] = set()
    completed_waves: set[int] = set()
    for event in ledger["history"]:
        details = event["details"]
        if event["event"] == "RUN_PAUSED":
            paused = True
        elif event["event"] == "RUN_RESUMED":
            paused = False
        elif event["event"] == "WAVE_HEALTH_ACCEPTED":
            accepted_waves.add(int(details["wave"]))
        elif event["event"] == "MODULE_ACQUIRED":
            current_module = str(details["slug"])
            modules[current_module] = "active"
        elif event["event"] == "MODULE_FINISHED":
            slug = str(details["slug"])
            disposition = str(details["disposition"])
            modules[slug] = "complete" if disposition in _TERMINAL_DISPOSITIONS else "blocked"
            if current_module == slug:
                current_module = None
        elif event["event"] == "WAVE_COMPLETED":
            completed_waves.add(int(details["wave"]))
        elif event["event"] == "RUN_COMPLETED":
            completed = True
            paused = False
        elif event["event"] == "RUN_ABANDONED":
            if current_module is not None:
                modules[current_module] = "blocked"
            current_module = None
            abandoned = True
            paused = False
    if abandoned:
        status = "abandoned"
    elif completed:
        status = "complete"
    elif current_module is not None:
        status = "active"
    elif paused:
        status = "paused"
    elif "blocked" in modules.values():
        status = "blocked"
    else:
        status = "active"
    return {
        "status": status,
        "current_module": current_module,
        "modules": modules,
        "accepted_waves": sorted(accepted_waves),
        "completed_waves": sorted(completed_waves),
    }


def compact_status(ledger: Mapping[str, Any]) -> dict[str, Any]:
    """Return the small durable status record suitable for a rollover packet."""
    state = derive_state(ledger)
    counts = {
        module_state: sum(value == module_state for value in state["modules"].values())
        for module_state in ("pending", "active", "blocked", "complete")
    }
    next_item = next(
        (item for item in ledger["queue"] if state["modules"][item["slug"]] != "complete"),
        None,
    )
    return {
        "run_id": ledger["run_id"],
        "owner": ledger["owner"],
        "track": ledger["request"]["track"],
        "scope": ledger["request"]["scope"],
        "status": state["status"],
        "current_module": state["current_module"],
        "next_module": next_item["slug"] if next_item else None,
        "next_wave": next_item["wave"] if next_item else None,
        "counts": counts,
        "completed_waves": state["completed_waves"],
        "last_event": ledger["history"][-1]["event"],
        "event_count": len(ledger["history"]),
    }


def default_health_probe() -> Mapping[str, Any]:
    """Refresh CodexBar-backed quota plus lane circuit health for a model wave."""
    from scripts.api.state_router import compute_routing_budget

    return compute_routing_budget(fresh_codexbar=True)


def _health_assessment(
    snapshot: Mapping[str, Any],
    health_config: Mapping[str, Any],
) -> tuple[bool, dict[str, Any]]:
    agents = snapshot.get("agents")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(agents, Mapping) or not isinstance(diagnostics, Mapping):
        return False, {"reason": "invalid-health-snapshot", "groups": []}
    snapshot_stale = bool(diagnostics.get("stale"))
    acceptable = set(health_config["acceptable_statuses"])
    groups: list[dict[str, Any]] = []
    all_groups_pass = True
    relevant_lane_stale = False
    for group in health_config["capability_groups"]:
        lanes: list[dict[str, Any]] = []
        available = 0
        for lane in group["lanes"]:
            record = agents.get(lane)
            if not isinstance(record, Mapping):
                lanes.append({"lane": lane, "status": "missing", "healthy": False, "stale": True})
                relevant_lane_stale = True
                continue
            status = str(record.get("status", "unknown"))
            health = record.get("health")
            healthy = bool(health.get("healthy")) if isinstance(health, Mapping) else False
            codexbar = record.get("codexbar")
            stale = bool(codexbar.get("stale")) if isinstance(codexbar, Mapping) else False
            relevant_lane_stale = relevant_lane_stale or stale
            lane_available = status in acceptable and healthy and not stale
            available += int(lane_available)
            lanes.append({"lane": lane, "status": status, "healthy": healthy, "stale": stale})
        passed = available >= int(group["minimum_available"])
        all_groups_pass = all_groups_pass and passed
        groups.append(
            {
                "id": group["id"],
                "minimum_available": group["minimum_available"],
                "available": available,
                "passed": passed,
                "lanes": lanes,
            }
        )
    fresh = not snapshot_stale and not relevant_lane_stale
    passed = all_groups_pass and (fresh or not health_config["require_fresh_snapshot"])
    return passed, {
        "reason": "accepted" if passed else "quota-or-health-unavailable",
        "generated_at": snapshot.get("generated_at"),
        "fresh": fresh,
        "groups": groups,
    }


def _default_readiness(repo_root: Path) -> ReadinessEvaluator:
    return lambda track, slug: evaluate_preparation(track, slug, repo_root=repo_root)


def start_run(
    track: str,
    *,
    owner: str,
    scope: str = "all",
    module: str | None = None,
    start: str | None = None,
    end: str | None = None,
    wave_size: int | None = None,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    runtime_root: Path | None = None,
    readiness_evaluator: ReadinessEvaluator | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Create one deterministic run or return its exact active retry."""
    track = track.strip().lower()
    owner = owner.strip()
    scope = scope.strip().lower()
    module = module.strip().lower() if module else None
    start = start.strip().lower() if start else None
    end = end.strip().lower() if end else None
    if not _TARGET_RE.fullmatch(track) or not owner:
        raise CoordinatorError("track and owner must be non-empty repository identifiers")
    if scope not in _SCOPES:
        raise CoordinatorError(f"unsupported curriculum selector scope: {scope}")
    config = load_config(config_path)
    selected_wave_size = wave_size or int(config["default_wave_size"])
    if selected_wave_size < 1 or selected_wave_size > int(config["maximum_wave_size"]):
        raise CoordinatorError(
            f"wave size must be within 1..{config['maximum_wave_size']}"
        )
    request = {
        "track": track,
        "scope": scope,
        "module": module,
        "start": start,
        "end": end,
        "wave_size": selected_wave_size,
    }
    manifest_path = Path(str(config["manifest_path"]))
    authority = _manifest_authority(repo_root, track, manifest_path)
    request_sha = _sha256({"owner": owner, "request": request, "authority": authority})
    run_id = f"clc-{request_sha[:24]}"
    root = _runtime_root(repo_root, config, runtime_root)
    path = _ledger_path(root, run_id)
    evaluator = readiness_evaluator or _default_readiness(repo_root)
    try:
        with _locked(root):
            existing = _read_optional_json(path)
            if existing is not None:
                _path, existing = _load_owned_run(
                    root=root, run_id=run_id, owner=owner, repo_root=repo_root
                )
                if existing["owner"] != owner or existing["request_sha256"] != request_sha:
                    raise CoordinatorError("run identity collision with a different request")
                if derive_state(existing)["status"] == "complete":
                    _release_owned_lease(_lease_path(root, "track", track), run_id)
                    return path, existing
                track_lease = _lease_path(root, "track", track)
                lease = _require_live_lease(track_lease, run_id, "track")
                _claim_lease(
                    track_lease,
                    run_id=run_id,
                    owner=owner,
                    lease_seconds=int(config["lease_seconds"]),
                    track=track,
                )
                state = derive_state(existing)
                if state["current_module"] is not None:
                    item = next(
                        row for row in existing["queue"] if row["slug"] == state["current_module"]
                    )
                    _renew_active_module_leases(root, existing, item, config)
                assert lease["run_id"] == run_id
                return path, existing
            queue, queue_authority = _build_queue(
                repo_root=repo_root,
                track=track,
                scope=scope,
                module=module,
                start=start,
                end=end,
                wave_size=selected_wave_size,
                manifest_path=manifest_path,
                readiness_evaluator=evaluator,
            )
            if queue_authority != authority:
                raise CoordinatorError("curriculum manifest changed while the run queue was being built")
            ledger: dict[str, Any] = {
                "ledger_version": "curriculum-coordinator-ledger.v1",
                "run_id": run_id,
                "owner": owner,
                "created_at": _iso(_now()),
                "request": request,
                "request_sha256": request_sha,
                "authority": authority,
                "queue": queue,
                "history": [],
            }
            _append_event(ledger, "RUN_STARTED", {"request_sha256": request_sha})
            _validate_ledger(ledger)
            track_lease = _lease_path(root, "track", track)
            _claim_lease(
                track_lease,
                run_id=run_id,
                owner=owner,
                lease_seconds=int(config["lease_seconds"]),
                track=track,
            )
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CoordinatorError("curriculum coordinator is busy; retry the exact start") from exc


def _load_owned_run(
    *,
    root: Path,
    run_id: str,
    owner: str,
    repo_root: Path,
    require_current_authority: bool = True,
) -> tuple[Path, dict[str, Any]]:
    path = _ledger_path(root, run_id)
    if not path.is_file():
        raise CoordinatorError(f"coordinator run does not exist: {run_id}")
    ledger = _read_ledger(path)
    if ledger["owner"] != owner.strip():
        raise CoordinatorError(f"coordinator run is owned by {ledger['owner']!r}")
    manifest_path = _repo_relative_path(repo_root, ledger["authority"]["manifest_path"])
    current_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest() if manifest_path.is_file() else None
    if require_current_authority and current_sha != ledger["authority"]["manifest_sha256"]:
        raise CoordinatorError("curriculum manifest changed after run start; adjudicate and start a fresh run")
    return path, ledger


def _renew_active_module_leases(
    root: Path,
    ledger: Mapping[str, Any],
    item: Mapping[str, Any],
    config: Mapping[str, Any],
) -> None:
    """Heartbeat live same-run mutation leases without reviving expired work."""
    run_id = str(ledger["run_id"])
    owner = str(ledger["owner"])
    track = str(ledger["request"]["track"])
    slug = str(item["slug"])
    global_path = _lease_path(root, "global")
    module_path = _lease_path(root, "module", f"{track}--{slug}")
    _require_live_lease(global_path, run_id, "global mutation")
    _require_live_lease(module_path, run_id, "module")
    lease_seconds = int(config["lease_seconds"])
    _claim_lease(
        global_path,
        run_id=run_id,
        owner=owner,
        lease_seconds=lease_seconds,
        track=track,
        slug=slug,
    )
    _claim_lease(
        module_path,
        run_id=run_id,
        owner=owner,
        lease_seconds=lease_seconds,
        track=track,
        slug=slug,
    )


def resume_run(
    run_id: str,
    *,
    owner: str,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    runtime_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Renew only the exact run's leases and reconstruct missing same-run leases."""
    config = load_config(config_path)
    root = _runtime_root(repo_root, config, runtime_root)
    try:
        with _locked(root):
            path, ledger = _load_owned_run(
                root=root, run_id=run_id, owner=owner, repo_root=repo_root
            )
            state = derive_state(ledger)
            if state["status"] == "complete":
                _release_owned_lease(
                    _lease_path(root, "track", ledger["request"]["track"]), run_id
                )
                return path, ledger
            track = ledger["request"]["track"]
            _claim_lease(
                _lease_path(root, "track", track),
                run_id=run_id,
                owner=owner,
                lease_seconds=int(config["lease_seconds"]),
                track=track,
            )
            current = state["current_module"]
            if current is not None:
                _claim_lease(
                    _lease_path(root, "global"),
                    run_id=run_id,
                    owner=owner,
                    lease_seconds=int(config["lease_seconds"]),
                    track=track,
                    slug=current,
                )
                _claim_lease(
                    _lease_path(root, "module", f"{track}--{current}"),
                    run_id=run_id,
                    owner=owner,
                    lease_seconds=int(config["lease_seconds"]),
                    track=track,
                    slug=current,
                )
            if state["status"] != "paused":
                _append_event(
                    ledger,
                    "RUN_RESUMED",
                    {"after_sequence": ledger["history"][-1]["sequence"], "reason": "exact-run-resume"},
                )
            _validate_ledger(ledger)
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CoordinatorError("curriculum coordinator is busy; retry the exact resume") from exc


def adjudicate_run(
    run_id: str,
    *,
    owner: str,
    reason: str,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    runtime_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Explicitly abandon an unrecoverable drifted or stale run without lease theft."""
    reason = reason.strip()
    if not reason or len(reason) > 500:
        raise CoordinatorError("adjudication reason must contain 1..500 characters")
    config = load_config(config_path)
    root = _runtime_root(repo_root, config, runtime_root)
    try:
        with _locked(root):
            path, ledger = _load_owned_run(
                root=root,
                run_id=run_id,
                owner=owner,
                repo_root=repo_root,
                require_current_authority=False,
            )
            state = derive_state(ledger)
            if state["status"] in {"complete", "abandoned"}:
                return path, ledger
            track = ledger["request"]["track"]
            manifest_path = _repo_relative_path(repo_root, ledger["authority"]["manifest_path"])
            current_sha = (
                hashlib.sha256(manifest_path.read_bytes()).hexdigest()
                if manifest_path.is_file()
                else None
            )
            manifest_changed = current_sha != ledger["authority"]["manifest_sha256"]
            track_lease_path = _lease_path(root, "track", track)
            track_lease = _read_optional_json(track_lease_path)
            lease_stale = (
                track_lease is None
                or track_lease.get("run_id") != run_id
                or _parse_time(str(track_lease.get("expires_at"))) <= _now()
            )
            if not manifest_changed:
                raise CoordinatorError(
                    "current-authority run cannot be abandoned; use exact-run resume for a stale lease"
                )
            _append_event(
                ledger,
                "RUN_ABANDONED",
                {
                    "reason": reason,
                    "prior_status": state["status"],
                    "current_module": state["current_module"],
                    "manifest_changed": manifest_changed,
                    "recorded_manifest_sha256": ledger["authority"]["manifest_sha256"],
                    "current_manifest_sha256": current_sha,
                    "track_lease_stale": lease_stale,
                },
            )
            _validate_ledger(ledger)
            _atomic_write_json(path, ledger)
            if state["current_module"] is not None:
                _release_owned_lease(
                    _lease_path(root, "module", f"{track}--{state['current_module']}"), run_id
                )
            _release_owned_lease(_lease_path(root, "global"), run_id)
            _release_owned_lease(track_lease_path, run_id)
            return path, ledger
    except Timeout as exc:
        raise CoordinatorError("curriculum coordinator is busy; retry the exact adjudication") from exc


def _probe_health(probe: HealthProbe, config: Mapping[str, Any]) -> tuple[bool, dict[str, Any]]:
    try:
        snapshot = probe()
    except Exception as exc:
        return False, {"reason": "health-probe-error", "error_type": type(exc).__name__, "groups": []}
    if not isinstance(snapshot, Mapping):
        return False, {"reason": "invalid-health-snapshot", "groups": []}
    return _health_assessment(snapshot, config["health"])


def acquire_next(
    run_id: str,
    *,
    owner: str,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    runtime_root: Path | None = None,
    health_probe: HealthProbe = default_health_probe,
    readiness_evaluator: ReadinessEvaluator | None = None,
) -> tuple[Path, dict[str, Any], dict[str, Any] | None]:
    """Acquire the next prerequisite-safe module, pausing cleanly on fleet health."""
    config = load_config(config_path)
    root = _runtime_root(repo_root, config, runtime_root)
    evaluator = readiness_evaluator or _default_readiness(repo_root)
    try:
        with _locked(root):
            path, ledger = _load_owned_run(
                root=root, run_id=run_id, owner=owner, repo_root=repo_root
            )
            state = derive_state(ledger)
            if state["status"] == "complete":
                return path, ledger, None
            track = ledger["request"]["track"]
            _require_live_lease(_lease_path(root, "track", track), run_id, "track")
            if state["current_module"] is not None:
                item = next(row for row in ledger["queue"] if row["slug"] == state["current_module"])
                _renew_active_module_leases(root, ledger, item, config)
                return path, ledger, item
            planned_item = next(
                (row for row in ledger["queue"] if state["modules"][row["slug"]] != "complete"),
                None,
            )
            if planned_item is None:
                raise CoordinatorError("run has no incomplete module but lacks RUN_COMPLETED")
            planned_wave = int(planned_item["wave"])
            needs_health = planned_wave not in state["accepted_waves"]

        passed = True
        assessment: dict[str, Any] | None = None
        if needs_health:
            passed, assessment = _probe_health(health_probe, config)
        readiness = (
            _readiness_snapshot(track, planned_item["slug"], evaluator) if passed else None
        )

        with _locked(root):
            path, ledger = _load_owned_run(
                root=root, run_id=run_id, owner=owner, repo_root=repo_root
            )
            state = derive_state(ledger)
            if state["status"] == "complete":
                return path, ledger, None
            _require_live_lease(_lease_path(root, "track", track), run_id, "track")
            if state["current_module"] is not None:
                item = next(row for row in ledger["queue"] if row["slug"] == state["current_module"])
                _renew_active_module_leases(root, ledger, item, config)
                return path, ledger, item
            item = next(
                (row for row in ledger["queue"] if state["modules"][row["slug"]] != "complete"),
                None,
            )
            if item is None or item["slug"] != planned_item["slug"]:
                raise CoordinatorError("coordinator state changed during routing; retry the exact acquisition")
            wave = int(item["wave"])
            if needs_health and wave not in state["accepted_waves"]:
                assert assessment is not None
                if not passed:
                    _append_event(ledger, "RUN_PAUSED", {"wave": wave, "health": assessment})
                    _validate_ledger(ledger)
                    _atomic_write_json(path, ledger)
                    return path, ledger, None
                if state["status"] == "paused":
                    _append_event(
                        ledger,
                        "RUN_RESUMED",
                        {"after_sequence": ledger["history"][-1]["sequence"], "reason": "wave-health-restored"},
                    )
                _append_event(ledger, "WAVE_HEALTH_ACCEPTED", {"wave": wave, "health": assessment})
            elif not passed:
                raise CoordinatorError("wave health changed during routing; retry the exact acquisition")
            unmet = [slug for slug in item["prerequisites"] if state["modules"].get(slug) != "complete"]
            if unmet:
                raise CoordinatorError(f"module prerequisites are not complete: {', '.join(unmet)}")
            assert readiness is not None
            lease_seconds = int(config["lease_seconds"])
            _claim_lease(
                _lease_path(root, "global"),
                run_id=run_id,
                owner=owner,
                lease_seconds=lease_seconds,
                track=track,
                slug=item["slug"],
            )
            try:
                _claim_lease(
                    _lease_path(root, "module", f"{track}--{item['slug']}"),
                    run_id=run_id,
                    owner=owner,
                    lease_seconds=lease_seconds,
                    track=track,
                    slug=item["slug"],
                )
            except Exception:
                _release_owned_lease(_lease_path(root, "global"), run_id)
                raise
            _append_event(
                ledger,
                "MODULE_ACQUIRED",
                {
                    "track": track,
                    "slug": item["slug"],
                    "manifest_index": item["manifest_index"],
                    "wave": wave,
                    "attempt": 1
                    + sum(
                        event["event"] == "MODULE_ACQUIRED"
                        and event["details"].get("slug") == item["slug"]
                        for event in ledger["history"]
                    ),
                    "readiness": readiness,
                },
            )
            _validate_ledger(ledger)
            _atomic_write_json(path, ledger)
            return path, ledger, item
    except Timeout as exc:
        raise CoordinatorError("curriculum coordinator is busy; retry module acquisition") from exc


def _integration_record(integration: Mapping[str, Any] | None) -> dict[str, Any]:
    defaults = {
        "issue": None,
        "worktree": None,
        "branch": None,
        "pr": None,
        "merge_sha": None,
        "cleanup": "not-required",
        "evidence": None,
    }
    record = {**defaults, **dict(integration or {})}
    if set(record) != set(defaults):
        unknown = sorted(set(record) - set(defaults))
        raise CoordinatorError(f"unknown integration identity fields: {unknown}")
    return record


def _validate_integration(disposition: str, integration: Mapping[str, Any]) -> None:
    evidence = integration["evidence"]
    if not isinstance(evidence, str) or not evidence.strip():
        raise CoordinatorError("every module disposition requires a non-empty evidence identity")
    if disposition == "no-change":
        identity_keys = ("issue", "worktree", "branch", "pr", "merge_sha")
        if any(integration[key] is not None for key in identity_keys) or integration["cleanup"] != "not-required":
            raise CoordinatorError("no-change disposition must not fabricate issue, branch, PR, or cleanup work")
    elif disposition == "complete":
        if not isinstance(integration["issue"], int) or integration["issue"] < 1:
            raise CoordinatorError("completed repair requires an issue number")
        if not isinstance(integration["pr"], int) or integration["pr"] < 1:
            raise CoordinatorError("completed repair requires a PR number")
        for key in ("worktree", "branch"):
            if not isinstance(integration[key], str) or not integration[key].strip():
                raise CoordinatorError(f"completed repair requires {key} identity")
        worktree = Path(integration["worktree"])
        if (
            worktree.is_absolute()
            or len(worktree.parts) != 4
            or worktree.parts[:2] != (".worktrees", "dispatch")
            or not _TARGET_RE.fullmatch(worktree.parts[2])
            or not _TARGET_RE.fullmatch(worktree.parts[3])
        ):
            raise CoordinatorError("completed repair worktree must use .worktrees/dispatch/<agent>/<task>")
        expected_branch = f"{worktree.parts[2]}/{worktree.parts[3]}"
        if integration["branch"] != expected_branch:
            raise CoordinatorError("completed repair branch must align with its dispatch worktree")
        if not isinstance(integration["merge_sha"], str) or not _SHA_RE.fullmatch(integration["merge_sha"]):
            raise CoordinatorError("completed repair requires a 40-character merge SHA")
        if integration["cleanup"] != "complete":
            raise CoordinatorError("completed repair requires proof of post-merge cleanup")
    elif disposition == "blocked" and integration["cleanup"] not in {"not-required", "pending"}:
        raise CoordinatorError("blocked disposition cleanup must be not-required or pending")


def _finish_events(ledger: dict[str, Any], item: Mapping[str, Any]) -> None:
    state = derive_state(ledger)
    wave = int(item["wave"])
    wave_items = [row for row in ledger["queue"] if row["wave"] == wave]
    if all(state["modules"][row["slug"]] == "complete" for row in wave_items):
        _append_event(ledger, "WAVE_COMPLETED", {"wave": wave})
    state = derive_state(ledger)
    if all(value == "complete" for value in state["modules"].values()):
        _append_event(ledger, "RUN_COMPLETED", {"module_count": len(ledger["queue"])})


def record_module(
    run_id: str,
    *,
    owner: str,
    slug: str,
    disposition: str,
    integration: Mapping[str, Any] | None,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    runtime_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Persist a module outcome exactly once and release only its owned leases."""
    disposition = disposition.strip().lower()
    slug = slug.strip().lower()
    if not _TARGET_RE.fullmatch(slug):
        raise CoordinatorError("module result requires one repository slug")
    if disposition not in {"complete", "no-change", "blocked"}:
        raise CoordinatorError(f"unsupported module disposition: {disposition}")
    identity = _integration_record(integration)
    _validate_integration(disposition, identity)
    config = load_config(config_path)
    root = _runtime_root(repo_root, config, runtime_root)
    try:
        with _locked(root):
            path, ledger = _load_owned_run(
                root=root, run_id=run_id, owner=owner, repo_root=repo_root
            )
            state = derive_state(ledger)
            track = ledger["request"]["track"]
            details: dict[str, Any]
            if state["current_module"] is None:
                matching = [
                    event
                    for event in ledger["history"]
                    if event["event"] == "MODULE_FINISHED"
                    and event["details"].get("slug") == slug
                    and event["details"].get("disposition") == disposition
                    and event["details"].get("integration") == identity
                ]
                if not matching:
                    raise CoordinatorError("no module is acquired; conflicting replay is not allowed")
                _release_owned_lease(_lease_path(root, "module", f"{track}--{slug}"), run_id)
                _release_owned_lease(_lease_path(root, "global"), run_id)
                if derive_state(ledger)["status"] == "complete":
                    _release_owned_lease(_lease_path(root, "track", track), run_id)
                return path, ledger
            if state["current_module"] != slug:
                raise CoordinatorError(
                    f"acquired module is {state['current_module']}; refusing result for {slug}"
                )
            item = next(row for row in ledger["queue"] if row["slug"] == slug)
            acquisition = next(
                event
                for event in reversed(ledger["history"])
                if event["event"] == "MODULE_ACQUIRED" and event["details"]["slug"] == slug
            )
            _require_live_lease(_lease_path(root, "global"), run_id, "global mutation")
            _require_live_lease(_lease_path(root, "module", f"{track}--{slug}"), run_id, "module")
            details = {
                "track": track,
                "slug": slug,
                "wave": item["wave"],
                "attempt": acquisition["details"]["attempt"],
                "disposition": disposition,
                "integration": identity,
            }
            _append_event(ledger, "MODULE_FINISHED", details)
            if disposition in _TERMINAL_DISPOSITIONS:
                _finish_events(ledger, item)
            _validate_ledger(ledger)
            _atomic_write_json(path, ledger)
            _release_owned_lease(_lease_path(root, "module", f"{track}--{slug}"), run_id)
            _release_owned_lease(_lease_path(root, "global"), run_id)
            if derive_state(ledger)["status"] == "complete":
                _release_owned_lease(_lease_path(root, "track", track), run_id)
            return path, ledger
    except Timeout as exc:
        raise CoordinatorError("curriculum coordinator is busy; retry the exact module result") from exc


def status_run(
    run_id: str,
    *,
    owner: str,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    root = _runtime_root(repo_root, config, runtime_root)
    _path, ledger = _load_owned_run(
        root=root,
        run_id=run_id,
        owner=owner,
        repo_root=repo_root,
        require_current_authority=False,
    )
    result = compact_status(ledger)
    manifest_path = _repo_relative_path(repo_root, ledger["authority"]["manifest_path"])
    current_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest() if manifest_path.is_file() else None
    result["manifest_current"] = current_sha == ledger["authority"]["manifest_sha256"]
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Create or replay one ordered run")
    start_parser.add_argument("--track", required=True)
    start_parser.add_argument("--owner", required=True)
    start_parser.add_argument("--scope", choices=sorted(_SCOPES), default="all")
    start_parser.add_argument("--module")
    start_parser.add_argument("--start")
    start_parser.add_argument("--end")
    start_parser.add_argument("--wave-size", type=int)

    for command in ("resume", "acquire-next", "status"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--run-id", required=True)
        command_parser.add_argument("--owner", required=True)

    adjudicate_parser = subparsers.add_parser("adjudicate-run")
    adjudicate_parser.add_argument("--run-id", required=True)
    adjudicate_parser.add_argument("--owner", required=True)
    adjudicate_parser.add_argument("--reason", required=True)

    record_parser = subparsers.add_parser("record-module")
    record_parser.add_argument("--run-id", required=True)
    record_parser.add_argument("--owner", required=True)
    record_parser.add_argument("--module", required=True)
    record_parser.add_argument("--disposition", choices=["complete", "no-change", "blocked"], required=True)
    record_parser.add_argument("--integration-json", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    common = {
        "repo_root": args.repo_root.resolve(),
        "config_path": args.config.resolve(),
        "runtime_root": None,
    }
    try:
        if args.command == "start":
            path, ledger = start_run(
                args.track,
                owner=args.owner,
                scope=args.scope,
                module=args.module,
                start=args.start,
                end=args.end,
                wave_size=args.wave_size,
                **common,
            )
            result = {"ledger": str(path), "status": compact_status(ledger)}
        elif args.command == "resume":
            path, ledger = resume_run(args.run_id, owner=args.owner, **common)
            result = {"ledger": str(path), "status": compact_status(ledger)}
        elif args.command == "acquire-next":
            path, ledger, item = acquire_next(args.run_id, owner=args.owner, **common)
            result = {"ledger": str(path), "status": compact_status(ledger), "acquired": item}
        elif args.command == "record-module":
            integration = json.loads(args.integration_json)
            if not isinstance(integration, dict):
                raise CoordinatorError("--integration-json must be a JSON object")
            path, ledger = record_module(
                args.run_id,
                owner=args.owner,
                slug=args.module,
                disposition=args.disposition,
                integration=integration,
                **common,
            )
            result = {"ledger": str(path), "status": compact_status(ledger)}
        elif args.command == "adjudicate-run":
            path, ledger = adjudicate_run(
                args.run_id,
                owner=args.owner,
                reason=args.reason,
                **common,
            )
            result = {"ledger": str(path), "status": compact_status(ledger)}
        else:
            result = status_run(args.run_id, owner=args.owner, **common)
    except (CoordinatorError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
