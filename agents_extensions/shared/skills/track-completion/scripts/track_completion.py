#!/usr/bin/env python3
"""Deterministic state and ledger helper for the track-completion skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from filelock import FileLock, Timeout
from jsonschema import Draft202012Validator

try:  # The script is also loaded directly by focused tests.
    from . import certification_evidence as certification
except ImportError:
    import importlib.util

    _CERTIFICATION_SPEC = importlib.util.spec_from_file_location(
        "track_completion_certification_evidence",
        Path(__file__).with_name("certification_evidence.py"),
    )
    assert _CERTIFICATION_SPEC is not None and _CERTIFICATION_SPEC.loader is not None
    certification = importlib.util.module_from_spec(_CERTIFICATION_SPEC)
    sys.modules[_CERTIFICATION_SPEC.name] = certification
    _CERTIFICATION_SPEC.loader.exec_module(certification)

SKILL_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from scripts.orchestration import curriculum_readiness

DEFAULT_CONFIG_PATH = SKILL_ROOT / "config" / "track-completion.v1.yaml"
CONFIG_SCHEMA_PATH = SKILL_ROOT / "schema" / "track-completion-config.v1.schema.json"
LEDGER_SCHEMA_PATH = SKILL_ROOT / "schema" / "progress-ledger.v1.schema.json"

SELECTOR_RE = re.compile(r"^(?P<track>[a-z0-9-]+)/(?P<slug>[a-z0-9-]+)$")
MATERIAL_SEVERITIES = frozenset({"blocker", "high", "medium"})
MUTATING_STATES = frozenset(
    {
        "PLAN_REPAIR_REQUIRED",
        "BUILD_REQUIRED",
        "PARTIAL_RECOVERY_REQUIRED",
        "REPAIR_REQUIRED",
        "AUDIT_TOOLING_REQUIRED",
        "REVIEWER_INSTABILITY",
    }
)


class CompletionError(RuntimeError):
    """Raised when a completion transition cannot be proven safe."""


@dataclass(frozen=True, slots=True)
class TargetSnapshot:
    selector: str
    track: str
    slug: str
    family: str
    module_state: str
    layout: str
    review_files: dict[str, str]
    observed_files: dict[str, str]
    commands: dict[str, Any]
    track_policy: dict[str, Any]


def stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(value: object, schema_path: Path, label: str) -> None:
    schema = read_json(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        detail = "; ".join(
            f"{'.'.join(str(part) for part in error.path) or '<root>'}: {error.message}" for error in errors[:8]
        )
        raise CompletionError(f"Invalid {label}: {detail}")


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CompletionError(f"Track-completion config must be a mapping: {path}")
    _validate(value, CONFIG_SCHEMA_PATH, "track-completion config")
    return value


def _repo_path(repo_root: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        raise CompletionError(f"Configured repository path must be relative: {raw}")
    resolved = (repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise CompletionError(f"Configured path escapes repository: {raw}") from exc
    return resolved


def _display_path(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _render_command(command: Sequence[str], track: str, slug: str) -> list[str]:
    return [str(part).format(track=track, slug=slug) for part in command]


def _parse_selector(selector: str) -> tuple[str, str]:
    match = SELECTOR_RE.fullmatch(selector.strip().lower())
    if match is None:
        raise CompletionError("Target must be one lowercase track/slug selector")
    return match["track"], match["slug"]


def _manifest(config: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    path = _repo_path(repo_root, str(config["manifest_path"]))
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("levels"), dict):
        raise CompletionError(f"Curriculum manifest has no levels mapping: {path}")
    return value


def _existing_unique(candidates: Sequence[Path], label: str) -> Path | None:
    existing = sorted({path.resolve() for path in candidates if path.exists()})
    if len(existing) > 1:
        shown = ", ".join(path.as_posix() for path in existing)
        raise CompletionError(f"Ambiguous {label}: {shown}")
    return existing[0] if existing else None


def _existing_paths(candidates: Sequence[Path]) -> list[Path]:
    return sorted({path.resolve() for path in candidates if path.exists()})


def resolve_target(
    selector: str,
    *,
    repo_root: Path = PROJECT_ROOT,
    config: Mapping[str, Any] | None = None,
) -> TargetSnapshot:
    config = dict(config or load_config())
    track, slug = _parse_selector(selector)
    manifest = _manifest(config, repo_root)
    levels = manifest["levels"]
    entry = levels.get(track)
    if not isinstance(entry, dict):
        raise CompletionError(f"Track is not active in curriculum.yaml: {track}")
    modules = entry.get("modules")
    if not isinstance(modules, list) or slug not in modules:
        raise CompletionError(f"Module is not active in curriculum.yaml: {track}/{slug}")
    manifest_type = str(entry.get("type") or "").strip().lower()
    family_map = config["family_for_manifest_type"]
    family = family_map.get(manifest_type)
    if family not in config["families"]:
        raise CompletionError(f"Unknown completion family for manifest type {manifest_type!r}")

    curriculum = repo_root / "curriculum" / "l2-uk-en"
    plan = curriculum / "plans" / track / f"{slug}.yaml"
    if not plan.exists():
        raise CompletionError(f"Missing plan: {_display_path(plan, repo_root)}")
    track_dir = curriculum / track
    module_dir = track_dir / slug
    content_candidates = [
        module_dir / "module.md",
        track_dir / f"{slug}.md",
        *track_dir.glob(f"[0-9]*-{slug}.md"),
    ]
    content_existing = _existing_paths(content_candidates)

    if len(content_existing) > 1:
        content = None
        layout = "ambiguous"
    else:
        content = content_existing[0] if content_existing else None
        layout = (
            "directory"
            if content is not None and content.name == "module.md" and content.parent == module_dir.resolve()
            else "flat"
            if content is not None
            else "none"
        )

    sidecar_candidates: dict[str, list[Path]] = {
        "activities": [module_dir / "activities.yaml", track_dir / "activities" / f"{slug}.yaml"],
        "vocabulary": [module_dir / "vocabulary.yaml", track_dir / "vocabulary" / f"{slug}.yaml"],
        "resources": [module_dir / "resources.yaml", track_dir / "resources" / f"{slug}.yaml"],
        "meta": [module_dir / "meta.yaml", track_dir / "meta" / f"{slug}.yaml"],
        "mdx": [repo_root / "site" / "src" / "content" / "docs" / track / f"{slug}.mdx"],
    }
    observed: dict[str, str] = {"plan": _display_path(plan, repo_root)}
    review_files: dict[str, str] = {"plan": observed["plan"]}
    for index, candidate in enumerate(content_existing, start=1):
        key = "content" if len(content_existing) == 1 else f"content_candidate_{index}"
        observed[key] = _display_path(candidate, repo_root)
        if key == "content":
            review_files[key] = observed[key]
    for name, candidates in sidecar_candidates.items():
        existing = _existing_paths(candidates)
        if len(existing) > 1:
            layout = "ambiguous"
            for index, candidate in enumerate(existing, start=1):
                observed[f"{name}_candidate_{index}"] = _display_path(candidate, repo_root)
            continue
        if existing:
            observed[name] = _display_path(existing[0], repo_root)
            if name != "mdx":
                review_files[name] = observed[name]

    artifact_keys = set(observed) - {"plan"}
    if layout == "ambiguous":
        module_state = "PARTIAL"
    elif content is not None:
        module_state = "BUILT"
    elif artifact_keys:
        module_state = "PARTIAL"
    else:
        module_state = "UNBUILT"

    family_config = config["families"][family]
    commands = {
        "plan_review_skill": family_config["plan_review_skill"],
        "plan_fix_skill": family_config["plan_fix_skill"],
        "plan_validation_commands": [
            _render_command(command, track, slug) for command in family_config["plan_validation_commands"]
        ],
        "build_command": _render_command(family_config["build_command"], track, slug),
        "shippability_command": _render_command(family_config["shippability_command"], track, slug),
    }
    override = dict(config.get("track_overrides", {}).get(track) or {})
    return TargetSnapshot(
        selector=f"{track}/{slug}",
        track=track,
        slug=slug,
        family=family,
        module_state=module_state,
        layout=layout,
        review_files=review_files,
        observed_files=observed,
        commands=commands,
        track_policy=override,
    )


def build_identity(
    snapshot: TargetSnapshot,
    *,
    repo_root: Path = PROJECT_ROOT,
    config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    config = dict(config or load_config())
    target_hashes = {
        name: sha256_file(_repo_path(repo_root, path)) for name, path in sorted(snapshot.observed_files.items())
    }
    workflow_hashes: dict[str, str] = {}
    manifest_path = str(config["manifest_path"])
    identity_paths = [manifest_path, *config["identity_paths"]]
    for raw in dict.fromkeys(str(path) for path in identity_paths):
        path = _repo_path(repo_root, raw)
        if not path.is_file():
            raise CompletionError(f"Missing workflow identity input: {raw}")
        workflow_hashes[raw] = sha256_file(path)
    payload = {
        "module_state": snapshot.module_state,
        "layout": snapshot.layout,
        "target_hashes": target_hashes,
        "workflow_hashes": workflow_hashes,
    }
    return {"sha256": sha256_bytes(stable_json(payload).encode("utf-8")), **payload}


def inspect_target(
    selector: str,
    *,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    identity = build_identity(snapshot, repo_root=repo_root, config=config)
    profile = certification_profile_for(snapshot, repo_root=repo_root, config=config)
    return {
        "target": {
            "selector": snapshot.selector,
            "track": snapshot.track,
            "slug": snapshot.slug,
            "family": snapshot.family,
        },
        "module_state": snapshot.module_state,
        "layout": snapshot.layout,
        "review_files": snapshot.review_files,
        "observed_files": snapshot.observed_files,
        "commands": snapshot.commands,
        "track_policy": snapshot.track_policy,
        "certification_profile": profile,
        "identity": identity,
    }


def certification_profile_for(
    snapshot: TargetSnapshot, *, repo_root: Path, config: Mapping[str, Any]
) -> dict[str, Any]:
    """Resolve only a registered, schema-valid profile; absent profiles are unsafe."""
    profile_path = _repo_path(repo_root, str(config["readiness_profiles_path"]))
    schema_path = _repo_path(repo_root, str(config["readiness_profiles_schema_path"]))
    if not profile_path.is_file() or not schema_path.is_file():
        raise CompletionError("Certification readiness profile contract is missing")
    value = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CompletionError("Certification readiness profile contract must be a mapping")
    _validate(value, schema_path, "certification readiness profiles")
    manifest = _manifest(config, repo_root)
    manifest_type = str(manifest["levels"][snapshot.track].get("type") or "")
    selectors = value["selectors"]
    profile_id = selectors["tracks"].get(snapshot.track) or selectors["manifest_types"].get(manifest_type)
    if not isinstance(profile_id, str) or profile_id not in value["profiles"]:
        raise CompletionError("No registered certification profile applies to this target")
    profile = value["profiles"][profile_id]
    qg = profile["certification"]["production_qg"]
    if qg["mode"] == "armed-canary":
        for key in ("qualification_artifact", "human_arming_artifact"):
            artifact = _repo_path(repo_root, str(qg[key]))
            if not artifact.is_file():
                raise CompletionError(f"Armed certification profile requires {key}")
    return {
        "id": profile_id,
        "version": profile["version"],
        "family": profile["family"],
        "certification": profile["certification"],
    }


def _declared_hashes(repo_root: Path, paths: Sequence[str], *, label: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for raw in paths:
        path = _repo_path(repo_root, raw)
        if not path.is_file():
            raise CompletionError(f"Missing declared {label} identity input: {raw}")
        hashes[str(raw)] = sha256_file(path)
    return hashes


def _identity(hashes: Mapping[str, str]) -> str:
    return sha256_bytes(stable_json(dict(sorted(hashes.items()))).encode("utf-8"))


def certification_inputs(
    selector: str,
    *,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive current certification bindings from source, never caller input."""
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    profile = certification_profile_for(snapshot, repo_root=repo_root, config=config)
    try:
        readiness = curriculum_readiness.evaluate_preparation(snapshot.track, snapshot.slug, repo_root=repo_root)
    except curriculum_readiness.ReadinessError as exc:
        raise CompletionError(f"Current preparation cannot be evaluated: {exc}") from exc
    if readiness["family"] != snapshot.family or readiness["profile_id"] != profile["id"]:
        raise CompletionError("Readiness profile contradicts the completion target family/profile")
    if not readiness["preparation_identity"] or not all(item["passed"] for item in readiness["requirements"]):
        raise CompletionError("Current declared preparation and plan requirements must pass")
    learner_hashes = {
        name: sha256_file(_repo_path(repo_root, raw))
        for name, raw in sorted(snapshot.review_files.items())
        if name != "plan"
    }
    if not learner_hashes:
        raise CompletionError("Certification requires a complete learner bundle")
    mutation_events = (
        []
        if ledger is None
        else [
            event for event in ledger.get("history", []) if event.get("event") in {"BUILD_RECORDED", "CHANGE_RECORDED"}
        ]
    )
    mutation_identity = sha256_bytes(
        stable_json(
            {"authors": [] if ledger is None else ledger.get("author_families", []), "events": mutation_events}
        ).encode("utf-8")
    )
    declarations = config["certification_identity_paths"]
    pbr_workflow_hashes = _declared_hashes(repo_root, declarations["pbr"], label="PBR")
    qg_identity = {
        name: _identity(_declared_hashes(repo_root, paths, label=f"production-QG {name}"))
        for name, paths in declarations["production_qg"].items()
    }
    qg_identity["profile"] = sha256_bytes(stable_json(profile["certification"]["production_qg"]).encode("utf-8"))
    return {
        "target": snapshot.selector,
        "profile": {"id": profile["id"], "version": profile["version"]},
        "preparation_identity": readiness["preparation_identity"],
        "learner_hashes": learner_hashes,
        "plan_hash": sha256_file(_repo_path(repo_root, snapshot.review_files["plan"])),
        "workflow_hashes": pbr_workflow_hashes,
        "pbr_dependency_identity": curriculum_readiness.dependent_evidence_identity(
            "post-build", readiness["preparation_identity"], pbr_workflow_hashes
        ),
        "mutation_identity": mutation_identity,
        "qg_identity": qg_identity,
        "profile_config": profile,
    }


def _primary_checkout(repo_root: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        return repo_root.resolve()
    common = Path(result.stdout.strip()).resolve()
    return common.parent if common.name == ".git" else repo_root.resolve()


def ledger_path_for(
    snapshot: TargetSnapshot,
    *,
    repo_root: Path,
    config: Mapping[str, Any],
    ledger_root: Path | None = None,
) -> Path:
    root = ledger_root or (_primary_checkout(repo_root) / str(config["runtime_root"]))
    return root / snapshot.track / f"{snapshot.slug}.json"


def _atomic_write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _read_ledger(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = read_json(path)
    if not isinstance(value, dict):
        raise CompletionError(f"Ledger must be a JSON object: {path}")
    _validate(value, LEDGER_SCHEMA_PATH, "track-completion ledger")
    return value


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime) -> str:
    return value.isoformat()


def _parse_time(raw: str) -> datetime:
    value = datetime.fromisoformat(raw)
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _renew_lease(ledger: dict[str, Any], config: Mapping[str, Any]) -> None:
    now = _now()
    ledger["run"]["updated_at"] = _iso(now)
    ledger["run"]["lease_expires_at"] = _iso(now + timedelta(seconds=int(config["lease_seconds"])))


def _require_run(ledger: dict[str, Any], run_id: str, config: Mapping[str, Any]) -> None:
    run = ledger["run"]
    if run["run_id"] != run_id:
        raise CompletionError("Run id does not own this module ledger")
    if run["status"] != "active":
        raise CompletionError(f"Completion run is not active: {run['status']}")
    if _parse_time(run["lease_expires_at"]) <= _now():
        raise CompletionError("Completion lease expired; resume the exact run id first")
    _renew_lease(ledger, config)


def _event_id(event: str, payload: object) -> str:
    raw = stable_json({"event": event, "payload": payload}).encode("utf-8")
    return f"{event.lower()}-{sha256_bytes(raw)[:24]}"


def _event_exists(ledger: Mapping[str, Any], event_id: str) -> bool:
    return any(item.get("event_id") == event_id for item in ledger.get("history", []))


def _append_event(
    ledger: dict[str, Any],
    *,
    event_id: str,
    event: str,
    to_state: str,
    identity: Mapping[str, Any],
    details: Mapping[str, Any],
) -> None:
    if _event_exists(ledger, event_id):
        return
    before = ledger["state"]
    ledger["history"].append(
        {
            "sequence": len(ledger["history"]) + 1,
            "event_id": event_id,
            "event": event,
            "at": _iso(_now()),
            "from_state": before,
            "to_state": to_state,
            "identity_sha256": identity["sha256"],
            "details": dict(details),
        }
    )
    ledger["state"] = to_state
    ledger["current_identity"] = dict(identity)


def _initial_state(module_state: str) -> str:
    return {
        "UNBUILT": "PLAN_REVIEW_REQUIRED",
        "PARTIAL": "PARTIAL_RECOVERY_REQUIRED",
        "BUILT": "POST_BUILD_REVIEW_REQUIRED",
    }[module_state]


def _target_record(snapshot: TargetSnapshot) -> dict[str, str]:
    return {
        "selector": snapshot.selector,
        "track": snapshot.track,
        "slug": snapshot.slug,
        "family": snapshot.family,
    }


def _with_lock(path: Path) -> FileLock:
    return FileLock(str(path.with_suffix(path.suffix + ".lock")), timeout=0)


def start_run(
    selector: str,
    *,
    owner: str,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    if not owner.strip():
        raise CompletionError("Ledger owner must be non-empty")
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    identity = build_identity(snapshot, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    try:
        with _with_lock(path):
            existing = _read_ledger(path)
            if existing is not None:
                run = existing["run"]
                if run["status"] == "completed" and existing["current_identity"]["sha256"] == identity["sha256"]:
                    return path, existing
                if run["status"] == "active" and _parse_time(run["lease_expires_at"]) > _now():
                    if run["owner"] == owner:
                        _renew_lease(existing, config)
                        _atomic_write_json(path, existing)
                        return path, existing
                    raise CompletionError(f"Module lease is held by {run['owner']} until {run['lease_expires_at']}")
                raise CompletionError("A prior ledger exists; resume its exact run id or archive it after adjudication")
            now = _now()
            state = _initial_state(snapshot.module_state)
            ledger: dict[str, Any] = {
                "schema_version": str(config["ledger_schema_version"]),
                "workflow_version": str(config["workflow_version"]),
                "target": _target_record(snapshot),
                "run": {
                    "run_id": uuid.uuid4().hex,
                    "owner": owner,
                    "status": "active",
                    "started_at": _iso(now),
                    "updated_at": _iso(now),
                    "lease_expires_at": _iso(now + timedelta(seconds=int(config["lease_seconds"]))),
                },
                "state": state,
                "current_identity": identity,
                "author_families": [],
                "history": [],
                "reviews": [],
                "certification_evidence": [],
                "routing": None,
                "publication": None,
            }
            ledger["history"].append(
                {
                    "sequence": 1,
                    "event_id": _event_id("STARTED", {"run_id": ledger["run"]["run_id"]}),
                    "event": "STARTED",
                    "at": _iso(now),
                    "from_state": None,
                    "to_state": state,
                    "identity_sha256": identity["sha256"],
                    "details": {"module_state": snapshot.module_state, "owner": owner},
                }
            )
            _validate(ledger, LEDGER_SCHEMA_PATH, "track-completion ledger")
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CompletionError(f"Concurrent ledger update in progress: {path}") from exc


def resume_run(
    selector: str,
    *,
    run_id: str,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    identity = build_identity(snapshot, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    try:
        with _with_lock(path):
            ledger = _read_ledger(path)
            if ledger is None or ledger["run"]["run_id"] != run_id:
                raise CompletionError("No matching completion run to resume")
            if ledger["run"]["status"] != "active":
                raise CompletionError("Completed runs cannot be resumed")
            drifted = ledger["current_identity"]["sha256"] != identity["sha256"]
            if drifted and ledger["state"] not in MUTATING_STATES:
                raise CompletionError("Unrecorded identity drift outside a mutation state; adjudicate stale evidence")
            _renew_lease(ledger, config)
            eid = _event_id("RESUMED", {"run_id": run_id, "identity": identity["sha256"]})
            if not _event_exists(ledger, eid):
                _append_event(
                    ledger,
                    event_id=eid,
                    event="RESUMED",
                    to_state=ledger["state"],
                    identity=ledger["current_identity"] if drifted else identity,
                    details={"pending_identity_drift": drifted},
                )
            _validate(ledger, LEDGER_SCHEMA_PATH, "track-completion ledger")
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CompletionError(f"Concurrent ledger update in progress: {path}") from exc


def _evidence_record(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CompletionError(f"Evidence file does not exist: {path}")
    return {"path": str(path.resolve()), "sha256": sha256_file(path)}


def _load_for_update(
    selector: str,
    run_id: str,
    *,
    repo_root: Path,
    config_path: Path,
    ledger_root: Path | None,
) -> tuple[dict[str, Any], TargetSnapshot, dict[str, Any], Path, dict[str, Any]]:
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    identity = build_identity(snapshot, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    ledger = _read_ledger(path)
    if ledger is None:
        raise CompletionError("Start the completion ledger before recording progress")
    _require_run(ledger, run_id, config)
    if ledger["target"] != _target_record(snapshot):
        raise CompletionError("Ledger target does not match the resolved target")
    return config, snapshot, identity, path, ledger


def record_plan_review(
    selector: str,
    *,
    run_id: str,
    verdict: str,
    evidence: Path,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    verdict = verdict.upper()
    if verdict not in {"PASS", "REVISE"}:
        raise CompletionError("Plan-review verdict must be PASS or REVISE")
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    evidence_record = _evidence_record(evidence)
    eid = _event_id("PLAN_REVIEWED", {"verdict": verdict, **evidence_record})
    try:
        with _with_lock(path):
            config, snapshot, identity, path, ledger = _load_for_update(
                selector, run_id, repo_root=repo_root, config_path=config_path, ledger_root=ledger_root
            )
            if _event_exists(ledger, eid):
                return path, ledger
            if ledger["state"] != "PLAN_REVIEW_REQUIRED":
                raise CompletionError(f"Plan review is not allowed from {ledger['state']}")
            if identity["sha256"] != ledger["current_identity"]["sha256"]:
                raise CompletionError("Unrecorded plan/workflow drift makes plan-review evidence stale")
            to_state = "BUILD_REQUIRED" if verdict == "PASS" else "PLAN_REPAIR_REQUIRED"
            _append_event(
                ledger,
                event_id=eid,
                event="PLAN_REVIEWED",
                to_state=to_state,
                identity=identity,
                details={"verdict": verdict, "evidence": evidence_record},
            )
            _validate(ledger, LEDGER_SCHEMA_PATH, "track-completion ledger")
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CompletionError(f"Concurrent ledger update in progress: {path}") from exc


def _record_author(ledger: dict[str, Any], family: str, config: Mapping[str, Any]) -> None:
    normalized = family.strip().lower()
    if not normalized or normalized in {"unknown", "mixed"}:
        raise CompletionError("Record one known author model family")
    _review_group(normalized, config)
    ledger["author_families"] = sorted(set(ledger["author_families"]) | {normalized})


def record_change(
    selector: str,
    *,
    run_id: str,
    owner_kind: str,
    author_family: str,
    summary: str,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    if owner_kind not in {"built_artifact", "plan_workflow", "audit_tooling"}:
        raise CompletionError("Unknown repair owner")
    if not summary.strip():
        raise CompletionError("Change summary must be non-empty")
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    try:
        with _with_lock(path):
            config, snapshot, identity, path, ledger = _load_for_update(
                selector, run_id, repo_root=repo_root, config_path=config_path, ledger_root=ledger_root
            )
            eid = _event_id(
                "CHANGE_RECORDED",
                {"identity": identity["sha256"], "owner": owner_kind, "summary": summary.strip()},
            )
            if _event_exists(ledger, eid):
                return path, ledger
            allowed_states = {
                "PLAN_REPAIR_REQUIRED",
                "REPAIR_REQUIRED",
                "AUDIT_TOOLING_REQUIRED",
                "REVIEWER_INSTABILITY",
            }
            if ledger["state"] not in allowed_states:
                raise CompletionError(f"A repair change is not allowed from {ledger['state']}")
            if identity["sha256"] == ledger["current_identity"]["sha256"]:
                raise CompletionError("No target or workflow identity changed; refusing a no-op repair")
            if ledger["state"] == "PLAN_REPAIR_REQUIRED" and owner_kind != "plan_workflow":
                raise CompletionError("Plan-repair state only accepts plan_workflow changes")
            if ledger["state"] == "REVIEWER_INSTABILITY" and owner_kind != "audit_tooling":
                raise CompletionError("Reviewer instability only accepts audit_tooling changes")
            if ledger["routing"] is not None and owner_kind not in ledger["routing"]["owners"]:
                raise CompletionError(f"Repair owner {owner_kind} was not routed by the review")
            _record_author(ledger, author_family, config)
            to_state = "PLAN_REVIEW_REQUIRED" if owner_kind == "plan_workflow" else "POST_BUILD_REVIEW_REQUIRED"
            _append_event(
                ledger,
                event_id=eid,
                event="CHANGE_RECORDED",
                to_state=to_state,
                identity=identity,
                details={
                    "owner_kind": owner_kind,
                    "author_family": author_family.strip().lower(),
                    "summary": summary.strip(),
                },
            )
            ledger["routing"] = None
            _validate(ledger, LEDGER_SCHEMA_PATH, "track-completion ledger")
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CompletionError(f"Concurrent ledger update in progress: {path}") from exc


def record_build(
    selector: str,
    *,
    run_id: str,
    author_family: str,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    try:
        with _with_lock(path):
            config, snapshot, identity, path, ledger = _load_for_update(
                selector, run_id, repo_root=repo_root, config_path=config_path, ledger_root=ledger_root
            )
            eid = _event_id("BUILD_RECORDED", {"identity": identity["sha256"], "author_family": author_family})
            if _event_exists(ledger, eid):
                return path, ledger
            if ledger["state"] not in {"BUILD_REQUIRED", "PARTIAL_RECOVERY_REQUIRED"}:
                raise CompletionError(f"Build completion is not allowed from {ledger['state']}")
            if snapshot.module_state != "BUILT":
                raise CompletionError("Build did not produce a unique built content target")
            if identity["sha256"] == ledger["current_identity"]["sha256"]:
                raise CompletionError("Build produced no fresh target/workflow identity")
            _record_author(ledger, author_family, config)
            _append_event(
                ledger,
                event_id=eid,
                event="BUILD_RECORDED",
                to_state="POST_BUILD_REVIEW_REQUIRED",
                identity=identity,
                details={"author_family": author_family.strip().lower()},
            )
            _validate(ledger, LEDGER_SCHEMA_PATH, "track-completion ledger")
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CompletionError(f"Concurrent ledger update in progress: {path}") from exc


def _load_post_build_result(result_path: Path) -> dict[str, Any]:
    result = read_json(result_path)
    if not isinstance(result, dict):
        raise CompletionError("Post-build result must be a JSON object")
    from scripts.audit import post_build_review as pbr

    try:
        pbr.validate_result(result)
    except Exception as exc:
        raise CompletionError(f"Invalid canonical post-build result: {exc}") from exc
    if result.get("schema_version") != pbr.CURRENT_RESULT_SCHEMA_VERSION:
        raise CompletionError("Post-build result is historical; allocate and finalize a current review")
    policy = pbr.load_track_policy()
    for version_field in (
        "review_protocol_version",
        "deterministic_contract_version",
        "semantic_prompt_version",
        "track_policy_version",
    ):
        if str(result.get(version_field)) != str(policy[version_field]):
            raise CompletionError(f"Post-build result {version_field} is not current")
    return result


def _review_stability_key(result: Mapping[str, Any], target_identity_sha256: str) -> str:
    reviewer = result["reviewer"]
    payload = {
        "source_hashes": result["source_hashes"],
        "prompt_sha256": result["prompt_sha256"],
        "review_protocol_version": result["review_protocol_version"],
        "deterministic_contract_version": result["deterministic_contract_version"],
        "semantic_prompt_version": result["semantic_prompt_version"],
        "track_policy_version": result["track_policy_version"],
        "target_identity_sha256": target_identity_sha256,
        "reviewer": {
            "agent": reviewer["agent"],
            "family": reviewer["family"],
            "model": reviewer["model"],
            "effort": reviewer["effort"],
            "capabilities": reviewer["capabilities"],
        },
    }
    return sha256_bytes(stable_json(payload).encode("utf-8"))


def _material_fingerprint(result: Mapping[str, Any]) -> str:
    material = []
    for finding in result.get("findings", []):
        if finding.get("severity") not in MATERIAL_SEVERITIES:
            continue
        material.append(
            {
                "id": finding.get("id"),
                "source": finding.get("source"),
                "category": finding.get("category"),
                "severity": finding.get("severity"),
                "message": finding.get("message"),
                "evidence": finding.get("evidence"),
                "location": finding.get("location"),
            }
        )
    payload = {
        "status": result["combined_disposition"]["status"],
        "findings": sorted(material, key=stable_json),
    }
    return sha256_bytes(stable_json(payload).encode("utf-8"))


def route_findings(
    result: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    routing = config["routing"]
    plan_categories = set(routing["plan_categories"])
    tooling_categories = set(routing["audit_tooling_categories"])
    built_categories = set(routing["built_artifact_categories"])
    tooling_prefixes = tuple(routing["audit_tooling_id_prefixes"])
    routed: list[dict[str, Any]] = []
    owners: set[str] = set()
    status = str(result["combined_disposition"]["status"])
    if status == "INCOMPLETE":
        owners.add("audit_tooling")
    for finding in result.get("findings", []):
        if finding.get("severity") not in MATERIAL_SEVERITIES:
            continue
        category = str(finding.get("category") or "")
        location = str(finding.get("location") or "")
        finding_id = str(finding.get("id") or "")
        source = str(finding.get("source") or "")
        if location.startswith("curriculum/l2-uk-en/plans/") or category in plan_categories:
            owner = "plan_workflow"
        elif (
            category in tooling_categories
            or finding_id.startswith(tooling_prefixes)
            or location.startswith(("scripts/", "agents_extensions/", ".codex/", ".claude/"))
        ):
            owner = "audit_tooling"
        elif category in built_categories or location.startswith("curriculum/l2-uk-en/"):
            owner = "built_artifact"
        elif source in {"deterministic", "track_policy"}:
            owner = "audit_tooling"
        else:
            owner = "audit_tooling"
        owners.add(owner)
        routed.append(
            {
                "finding_id": finding_id,
                "category": category,
                "location": location,
                "owner": owner,
            }
        )
    if status != "PASS" and not owners:
        owners.add("audit_tooling")
    return {"owners": sorted(owners), "findings": routed}


def record_review(
    selector: str,
    *,
    run_id: str,
    result_path: Path,
    stability_check: bool = False,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    resolved_result = result_path.resolve()
    try:
        resolved_result.relative_to(repo_root.resolve())
    except ValueError:
        pass
    else:
        raise CompletionError("Canonical post-build result must remain outside the repository")
    result = _load_post_build_result(resolved_result)
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    result_sha = sha256_file(resolved_result)
    eid = _event_id("POST_BUILD_REVIEWED", {"result_sha256": result_sha})
    try:
        with _with_lock(path):
            config, snapshot, identity, path, ledger = _load_for_update(
                selector, run_id, repo_root=repo_root, config_path=config_path, ledger_root=ledger_root
            )
            if _event_exists(ledger, eid):
                return path, ledger
            allowed_state = ledger["state"] == "POST_BUILD_REVIEW_REQUIRED"
            stability_state = stability_check and ledger["state"] in {
                "REPAIR_REQUIRED",
                "AUDIT_TOOLING_REQUIRED",
            }
            if not (allowed_state or stability_state):
                raise CompletionError(f"Post-build review is not allowed from {ledger['state']}")
            if identity["sha256"] != ledger["current_identity"]["sha256"]:
                raise CompletionError("Unrecorded target/workflow drift makes review evidence stale")
            if result["target"]["track"] != snapshot.track or result["target"]["slug"] != snapshot.slug:
                raise CompletionError("Post-build result target does not match the ledger target")
            if dict(result["target"]["files"]) != snapshot.review_files:
                raise CompletionError("Post-build result file set is stale or does not match the target")
            current_source_hashes = {
                name: sha256_file(_repo_path(repo_root, raw)) for name, raw in sorted(snapshot.review_files.items())
            }
            if dict(result["source_hashes"]) != current_source_hashes:
                raise CompletionError("Post-build result source hashes are stale")
            semantic = result.get("semantic_response")
            inputs: dict[str, Any] | None = None
            if result["combined_disposition"]["status"] == "PASS":
                try:
                    inputs = certification_inputs(selector, repo_root=repo_root, config_path=config_path, ledger=ledger)
                except CompletionError:
                    # The legacy process cursor remains usable, but a record without
                    # the derived bindings is never certification authority.
                    inputs = None
                if inputs is not None and (
                    not isinstance(semantic, Mapping) or not isinstance(semantic.get("raw_sha256"), str)
                ):
                    raise CompletionError("Current PBR result has no exact raw semantic response hash")

            stability_key = _review_stability_key(result, identity["sha256"])
            fingerprint = _material_fingerprint(result)
            reviewer = result["reviewer"]
            review_record = {
                "result_path": str(resolved_result),
                "result_sha256": result_sha,
                "reproducibility_key": result["reproducibility_key"],
                "stability_key": stability_key,
                "material_fingerprint": fingerprint,
                "status": result["combined_disposition"]["status"],
                "reviewer_family": reviewer["family"],
                "reviewer_model": reviewer["model"],
                "target_identity_sha256": identity["sha256"],
                **(
                    {
                        "certification": {
                            "profile": inputs["profile"],
                            "preparation_identity": inputs["preparation_identity"],
                            "learner_hashes": inputs["learner_hashes"],
                            "plan_hash": current_source_hashes["plan"],
                            "raw_response_sha256": semantic["raw_sha256"],
                            "dependency_hashes": inputs["workflow_hashes"],
                            "dependency_identity": inputs["pbr_dependency_identity"],
                        }
                    }
                    if inputs is not None
                    else {}
                ),
            }
            unstable = any(
                prior["stability_key"] == stability_key and prior["material_fingerprint"] != fingerprint
                for prior in ledger["reviews"]
            )
            ledger["reviews"].append(review_record)
            status = str(result["combined_disposition"]["status"])
            if unstable:
                to_state = "REVIEWER_INSTABILITY"
                routing = {"owners": ["audit_tooling"], "findings": []}
            elif status == "PASS":
                routing = None
                if ledger["author_families"]:
                    to_state = "INDEPENDENT_REVIEW_REQUIRED"
                else:
                    mode = inputs["profile_config"]["certification"]["production_qg"]["mode"] if inputs else "pending"
                    to_state = {
                        "disabled": "CERTIFIED_FINAL",
                        "pending": "PBR_PASS_QG_PENDING",
                        "armed-canary": "PRODUCTION_QG_REQUIRED",
                    }[mode]
                    if to_state == "CERTIFIED_FINAL":
                        ledger["run"]["status"] = "completed"
            else:
                routing = route_findings(result, config=config)
                to_state = "AUDIT_TOOLING_REQUIRED" if routing["owners"] == ["audit_tooling"] else "REPAIR_REQUIRED"
            ledger["routing"] = routing
            _append_event(
                ledger,
                event_id=eid,
                event="POST_BUILD_REVIEWED",
                to_state=to_state,
                identity=identity,
                details={
                    "result": review_record,
                    "reviewer_instability": unstable,
                    "stability_check": stability_check,
                    "routing": routing,
                },
            )
            _validate(ledger, LEDGER_SCHEMA_PATH, "track-completion ledger")
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CompletionError(f"Concurrent ledger update in progress: {path}") from exc


def _review_group(family: str, config: Mapping[str, Any]) -> str:
    normalized = family.strip().lower()
    group = config["review_family_groups"].get(normalized)
    if not group:
        raise CompletionError(f"Unknown review family: {family}")
    return str(group)


def record_instability_adjudication(
    selector: str,
    *,
    run_id: str,
    evidence: Path,
    summary: str,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    if not summary.strip():
        raise CompletionError("Instability adjudication summary must be non-empty")
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    evidence_record = _evidence_record(evidence)
    eid = _event_id("INSTABILITY_ADJUDICATED", {"summary": summary.strip(), **evidence_record})
    try:
        with _with_lock(path):
            config, snapshot, identity, path, ledger = _load_for_update(
                selector,
                run_id,
                repo_root=repo_root,
                config_path=config_path,
                ledger_root=ledger_root,
            )
            if _event_exists(ledger, eid):
                return path, ledger
            if ledger["state"] != "REVIEWER_INSTABILITY":
                raise CompletionError(f"Instability adjudication is not allowed from {ledger['state']}")
            if identity["sha256"] != ledger["current_identity"]["sha256"]:
                raise CompletionError("Record audit_tooling changes before adjudicating reviewer instability")
            _append_event(
                ledger,
                event_id=eid,
                event="INSTABILITY_ADJUDICATED",
                to_state="POST_BUILD_REVIEW_REQUIRED",
                identity=identity,
                details={"summary": summary.strip(), "evidence": evidence_record},
            )
            ledger["routing"] = None
            _validate(ledger, LEDGER_SCHEMA_PATH, "track-completion ledger")
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CompletionError(f"Concurrent ledger update in progress: {path}") from exc


def record_independent_review(
    selector: str,
    *,
    run_id: str,
    reviewer_family: str,
    verdict: str,
    evidence: Path,
    owner_kind: str | None = None,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    verdict = verdict.upper()
    if verdict not in {"PASS", "CHANGES_REQUESTED"}:
        raise CompletionError("Independent-review verdict must be PASS or CHANGES_REQUESTED")
    if verdict == "PASS" and owner_kind is not None:
        raise CompletionError("A passing independent review cannot route a repair owner")
    if verdict == "CHANGES_REQUESTED" and owner_kind not in {
        "built_artifact",
        "plan_workflow",
        "audit_tooling",
    }:
        raise CompletionError("Changes requested must name one repair owner")
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    evidence_record = _evidence_record(evidence)
    eid = _event_id(
        "INDEPENDENT_REVIEWED",
        {
            "reviewer_family": reviewer_family,
            "verdict": verdict,
            "owner_kind": owner_kind,
            **evidence_record,
        },
    )
    try:
        with _with_lock(path):
            config, snapshot, identity, path, ledger = _load_for_update(
                selector, run_id, repo_root=repo_root, config_path=config_path, ledger_root=ledger_root
            )
            if _event_exists(ledger, eid):
                return path, ledger
            if ledger["state"] != "INDEPENDENT_REVIEW_REQUIRED":
                raise CompletionError(f"Independent review is not allowed from {ledger['state']}")
            if identity["sha256"] != ledger["current_identity"]["sha256"]:
                raise CompletionError("Target/workflow changed after post-build review")
            reviewer_group = _review_group(reviewer_family, config)
            author_groups = {
                _review_group(family, config)
                for family in ledger["author_families"]
                if _review_group(family, config) != "human"
            }
            if reviewer_group in author_groups:
                raise CompletionError("Independent reviewer is from an author model family")
            override = snapshot.track_policy
            forbidden = {str(item).lower() for item in override.get("forbidden_reviewer_families", [])}
            if reviewer_family.strip().lower() in forbidden:
                raise CompletionError(f"Reviewer family is forbidden for {snapshot.track}")
            allowed_groups = set(override.get("allowed_reviewer_groups", []))
            if allowed_groups and reviewer_group not in allowed_groups:
                raise CompletionError(f"Reviewer group is not allowed for {snapshot.track}")
            if verdict == "PASS":
                to_state = "INTEGRATION_REQUIRED"
                routing = None
            else:
                routing = {"owners": [owner_kind], "findings": []}
                to_state = {
                    "built_artifact": "REPAIR_REQUIRED",
                    "plan_workflow": "PLAN_REPAIR_REQUIRED",
                    "audit_tooling": "AUDIT_TOOLING_REQUIRED",
                }[owner_kind]
            ledger["routing"] = routing
            _append_event(
                ledger,
                event_id=eid,
                event="INDEPENDENT_REVIEWED",
                to_state=to_state,
                identity=identity,
                details={
                    "reviewer_family": reviewer_family.strip().lower(),
                    "reviewer_group": reviewer_group,
                    "verdict": verdict,
                    "owner_kind": owner_kind,
                    "evidence": evidence_record,
                },
            )
            _validate(ledger, LEDGER_SCHEMA_PATH, "track-completion ledger")
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CompletionError(f"Concurrent ledger update in progress: {path}") from exc


def record_published(
    selector: str,
    *,
    run_id: str,
    pr: int,
    merge_sha: str,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    if pr <= 0 or re.fullmatch(r"[0-9a-f]{7,40}", merge_sha) is None:
        raise CompletionError("Publication requires a PR number and 7-40 character merge SHA")
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    eid = _event_id("PUBLISHED", {"pr": pr, "merge_sha": merge_sha})
    try:
        with _with_lock(path):
            config, snapshot, identity, path, ledger = _load_for_update(
                selector, run_id, repo_root=repo_root, config_path=config_path, ledger_root=ledger_root
            )
            if _event_exists(ledger, eid):
                return path, ledger
            if ledger["state"] not in {"PUBLISH_REQUIRED", "INTEGRATION_REQUIRED"}:
                raise CompletionError(f"Publication is not allowed from {ledger['state']}")
            if identity["sha256"] != ledger["current_identity"]["sha256"]:
                raise CompletionError("Target/workflow changed after the independent review")
            recorded_at = _iso(_now())
            ledger["publication"] = {"pr": pr, "merge_sha": merge_sha, "recorded_at": recorded_at}
            _append_event(
                ledger,
                event_id=eid,
                event="PUBLISHED",
                to_state="COMPLETE",
                identity=identity,
                details={"pr": pr, "merge_sha": merge_sha},
            )
            ledger["run"]["status"] = "completed"
            _validate(ledger, LEDGER_SCHEMA_PATH, "track-completion ledger")
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CompletionError(f"Concurrent ledger update in progress: {path}") from exc


def record_certification_evidence(
    selector: str,
    *,
    run_id: str,
    evidence: Path,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Append one strictly parsed evidence artifact; projection decides its authority."""
    artifact = certification.read_evidence(evidence)
    try:
        artifact.path.relative_to(repo_root.resolve())
    except ValueError:
        pass
    else:
        raise CompletionError("Runtime certification evidence must remain outside the repository")
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    eid = _event_id("CERTIFICATION_EVIDENCE_RECORDED", {"sha256": artifact.sha256})
    try:
        with _with_lock(path):
            _config, _snapshot, identity, path, ledger = _load_for_update(
                selector, run_id, repo_root=repo_root, config_path=config_path, ledger_root=ledger_root
            )
            if _event_exists(ledger, eid):
                return path, ledger
            record = {"path": str(artifact.path), "sha256": artifact.sha256, "value": artifact.value}
            ledger.setdefault("certification_evidence", []).append(record)
            _append_event(
                ledger,
                event_id=eid,
                event="CERTIFICATION_EVIDENCE_RECORDED",
                to_state=ledger["state"],
                identity=identity,
                details={"evidence": {"kind": artifact.value["kind"], "sha256": artifact.sha256}},
            )
            _validate(ledger, LEDGER_SCHEMA_PATH, "track-completion ledger")
            _atomic_write_json(path, ledger)
            return path, ledger
    except Timeout as exc:
        raise CompletionError(f"Concurrent ledger update in progress: {path}") from exc


def _ledger_artifacts(ledger: Mapping[str, Any], kind: str) -> list[certification.EvidenceArtifact]:
    artifacts: list[certification.EvidenceArtifact] = []
    for item in ledger.get("certification_evidence", []):
        value = item.get("value")
        if isinstance(value, dict) and value.get("kind") == kind:
            artifacts.append(certification.EvidenceArtifact(Path(str(item["path"])), str(item["sha256"]), value))
    return artifacts


def _current_pbr_reviews(ledger: Mapping[str, Any], inputs: Mapping[str, Any]) -> tuple[bool, str, bool]:
    """Return PASS/current-state/instability from canonical PBR review records only."""
    fingerprints: dict[str, set[str]] = {}
    passed = False
    state = "missing"
    for review in ledger.get("reviews", []):
        binding = review.get("certification")
        if not isinstance(binding, Mapping):
            continue  # v1 ledger compatibility: legacy review is deliberately provisional.
        if (
            binding.get("profile") != inputs["profile"]
            or binding.get("preparation_identity") != inputs["preparation_identity"]
            or binding.get("learner_hashes") != inputs["learner_hashes"]
            or binding.get("plan_hash") != inputs["plan_hash"]
            or binding.get("dependency_hashes") != inputs["workflow_hashes"]
            or binding.get("dependency_identity") != inputs["pbr_dependency_identity"]
            or not re.fullmatch(r"[0-9a-f]{64}", str(binding.get("raw_response_sha256", "")))
        ):
            state = "stale"
            continue
        key = str(review.get("stability_key", ""))
        fingerprint = str(review.get("material_fingerprint", ""))
        fingerprints.setdefault(key, set()).add(fingerprint)
        if review.get("status") == "PASS":
            passed, state = True, "current"
        else:
            state = "fail"
    return passed, state, any(len(values) > 1 for values in fingerprints.values())


def certification_projection(
    selector: str,
    *,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> dict[str, Any]:
    """Derive the certification state afresh; no cursor state or publication is authority."""
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    ledger = _read_ledger(path)
    if ledger is None:
        raise CompletionError(f"No completion ledger for {selector}")
    try:
        inputs = certification_inputs(selector, repo_root=repo_root, config_path=config_path, ledger=ledger)
    except CompletionError as exc:
        return {
            "state": "POST_BUILD_REVIEW_REQUIRED",
            "post_build": "preparation-stale",
            "independent_review": "pending",
            "integration": "pending",
            "production_qg": "pending",
            "final": "not-certified",
            "reason": str(exc),
        }
    profile = inputs["profile_config"]
    expected = {key: inputs[key] for key in ("target", "profile", "preparation_identity", "learner_hashes")}

    pbr_ok, pbr_state, pbr_unstable = _current_pbr_reviews(ledger, inputs)
    if pbr_unstable:
        return {
            "state": "REVIEWER_INSTABILITY",
            "post_build": "instability",
            "independent_review": "pending",
            "integration": "pending",
            "production_qg": "pending",
            "final": "not-certified",
        }
    if not pbr_ok:
        return {
            "state": "POST_BUILD_REVIEW_REQUIRED",
            "post_build": pbr_state,
            "independent_review": "pending",
            "integration": "pending",
            "production_qg": "pending",
            "final": "not-certified",
        }

    mutation_required = bool(ledger.get("author_families"))
    author_groups = {_review_group(family, config) for family in ledger.get("author_families", [])}
    independent_ok = not mutation_required
    independent_state = "not-required" if not mutation_required else "pending"
    if mutation_required:
        for artifact in _ledger_artifacts(ledger, "independent-review"):
            try:
                certification.require_current(artifact, kind="independent-review", expected=expected)
                if artifact.value.get("mutation_identity") != inputs["mutation_identity"]:
                    independent_state = "stale"
                elif certification.independent_review_passes(
                    artifact,
                    author_groups=author_groups,
                    author_families=set(ledger.get("author_families", [])),
                    config=config,
                    track_policy=snapshot.track_policy,
                ):
                    independent_ok, independent_state = True, "current"
                else:
                    independent_state = "unresolved"
            except certification.CertificationEvidenceError:
                independent_state = "malformed"
    if not independent_ok:
        return {
            "state": "INDEPENDENT_REVIEW_REQUIRED",
            "post_build": "current",
            "independent_review": independent_state,
            "integration": "pending",
            "production_qg": "pending",
            "final": "not-certified",
        }

    integration_ok = not mutation_required
    integration_state = "not-required" if not mutation_required else "pending"
    if mutation_required:
        independent_shas = {
            artifact.sha256: artifact.value.get("diff_sha256")
            for artifact in _ledger_artifacts(ledger, "independent-review")
            if artifact.value.get("mutation_identity") == inputs["mutation_identity"]
            and artifact.value.get("diff_sha256")
            and certification.independent_review_passes(
                artifact,
                author_groups=author_groups,
                author_families=set(ledger.get("author_families", [])),
                config=config,
                track_policy=snapshot.track_policy,
            )
        }
        for artifact in _ledger_artifacts(ledger, "integration"):
            try:
                certification.require_current(artifact, kind="integration", expected=expected)
                if artifact.value.get("mutation_identity") != inputs["mutation_identity"]:
                    integration_state = "stale"
                elif (
                    certification.integration_passes(artifact)
                    and artifact.value.get("diff_sha256")
                    and independent_shas.get(artifact.value.get("independent_evidence_sha256"))
                    == artifact.value.get("diff_sha256")
                ):
                    integration_ok, integration_state = True, "current"
                else:
                    integration_state = "malformed"
            except certification.CertificationEvidenceError:
                integration_state = "malformed"
    if not integration_ok:
        return {
            "state": "INTEGRATION_REQUIRED",
            "post_build": "current",
            "independent_review": independent_state,
            "integration": integration_state,
            "production_qg": "pending",
            "final": "not-certified",
        }

    qg = profile["certification"]["production_qg"]
    if qg["mode"] == "disabled":
        return {
            "state": "CERTIFIED_FINAL",
            "post_build": "current",
            "independent_review": independent_state,
            "integration": integration_state,
            "production_qg": "disabled",
            "final": "final",
        }
    if qg["mode"] == "pending":
        return {
            "state": "PBR_PASS_QG_PENDING",
            "post_build": "current",
            "independent_review": independent_state,
            "integration": integration_state,
            "production_qg": "pending",
            "final": "provisional",
        }

    passing = False
    qg_state = "required"
    fingerprints: dict[str, set[str]] = {}
    for artifact in _ledger_artifacts(ledger, "production-qg"):
        try:
            certification.require_current(artifact, kind="production-qg", expected=expected)
            authorization = certification.load_authorization(
                qg, repo_root=repo_root, expected_profile=inputs["profile"], expected_identity=inputs["qg_identity"]
            )
            if (
                artifact.value["authorization"]["qualification_sha256"] != authorization["qualification_sha256"]
                or artifact.value["authorization"]["human_arming_sha256"] != authorization["human_arming_sha256"]
            ):
                qg_state = "stale"
                continue
            qg_key = certification.production_qg_stability_key(artifact)
            fingerprints.setdefault(qg_key, set()).add(certification.production_qg_material_fingerprint(artifact))
            if certification.production_qg_passes(
                artifact,
                expected_identity=inputs["qg_identity"],
                seminar=profile["family"] == "seminar",
                authorization=authorization,
            ):
                passing, qg_state = True, "pass"
            else:
                qg_state = "fail"
        except certification.CertificationEvidenceError:
            qg_state = "malformed"
    if any(len(values) > 1 for values in fingerprints.values()):
        return {
            "state": "REVIEWER_INSTABILITY",
            "post_build": "current",
            "independent_review": independent_state,
            "integration": integration_state,
            "production_qg": "instability",
            "final": "not-certified",
        }
    return {
        "state": "CERTIFIED_FINAL" if passing else "PRODUCTION_QG_REQUIRED",
        "post_build": "current",
        "independent_review": independent_state,
        "integration": integration_state,
        "production_qg": qg_state,
        "final": "final" if passing else "not-certified",
    }


def status_run(
    selector: str,
    *,
    repo_root: Path = PROJECT_ROOT,
    config_path: Path = DEFAULT_CONFIG_PATH,
    ledger_root: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    config = load_config(config_path)
    snapshot = resolve_target(selector, repo_root=repo_root, config=config)
    identity = build_identity(snapshot, repo_root=repo_root, config=config)
    path = ledger_path_for(snapshot, repo_root=repo_root, config=config, ledger_root=ledger_root)
    ledger = _read_ledger(path)
    if ledger is None:
        raise CompletionError(f"No completion ledger for {selector}")
    result = dict(ledger)
    result["status_probe"] = {
        "current_identity_sha256": identity["sha256"],
        "recorded_identity_sha256": ledger["current_identity"]["sha256"],
        "identity_drift": identity["sha256"] != ledger["current_identity"]["sha256"],
        "lease_expired": _parse_time(ledger["run"]["lease_expires_at"]) <= _now(),
    }
    result["certification"] = certification_projection(
        selector, repo_root=repo_root, config_path=config_path, ledger_root=ledger_root
    )
    return path, result


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("target", help="One active track/slug target")
    parser.add_argument("--repo-root", type=Path, default=PROJECT_ROOT, help=argparse.SUPPRESS)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help=argparse.SUPPRESS)
    parser.add_argument("--ledger-root", type=Path, default=None, help=argparse.SUPPRESS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect and advance one canonical curriculum track-completion ledger."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect = subparsers.add_parser("inspect", help="Resolve module state and configured commands")
    _add_common_options(inspect)
    start = subparsers.add_parser("start", help="Create or idempotently reopen a module ledger")
    _add_common_options(start)
    start.add_argument("--owner", required=True)
    resume = subparsers.add_parser("resume", help="Renew the exact recorded run lease")
    _add_common_options(resume)
    resume.add_argument("--run-id", required=True)
    status = subparsers.add_parser("status", help="Read the durable ledger and current drift status")
    _add_common_options(status)
    status.add_argument("--preparation-identity")
    plan_review = subparsers.add_parser("record-plan-review", help="Record family plan-review evidence")
    _add_common_options(plan_review)
    plan_review.add_argument("--run-id", required=True)
    plan_review.add_argument("--verdict", required=True, choices=("PASS", "REVISE"))
    plan_review.add_argument("--evidence", required=True, type=Path)
    change = subparsers.add_parser("record-change", help="Record one routed repair mutation")
    _add_common_options(change)
    change.add_argument("--run-id", required=True)
    change.add_argument("--owner-kind", required=True, choices=("built_artifact", "plan_workflow", "audit_tooling"))
    change.add_argument("--author-family", required=True)
    change.add_argument("--summary", required=True)
    build = subparsers.add_parser("record-build", help="Record a completed fresh module build")
    _add_common_options(build)
    build.add_argument("--run-id", required=True)
    build.add_argument("--author-family", required=True)
    review = subparsers.add_parser("record-review", help="Record one canonical post-build result")
    _add_common_options(review)
    review.add_argument("--run-id", required=True)
    review.add_argument("--result", required=True, type=Path)
    review.add_argument(
        "--stability-check",
        action="store_true",
        help="Compare one unchanged-source repeat after a non-PASS result",
    )
    instability = subparsers.add_parser(
        "record-instability-adjudication",
        help="Record evidence that permits a different reviewer route",
    )
    _add_common_options(instability)
    instability.add_argument("--run-id", required=True)
    instability.add_argument("--evidence", required=True, type=Path)
    instability.add_argument("--summary", required=True)
    independent = subparsers.add_parser(
        "record-independent-review", help="Record the outside-author-family implementation review"
    )
    _add_common_options(independent)
    independent.add_argument("--run-id", required=True)
    independent.add_argument("--reviewer-family", required=True)
    independent.add_argument("--verdict", required=True, choices=("PASS", "CHANGES_REQUESTED"))
    independent.add_argument("--evidence", required=True, type=Path)
    independent.add_argument("--owner-kind", choices=("built_artifact", "plan_workflow", "audit_tooling"))
    published = subparsers.add_parser("record-published", help="Record merged PR evidence and complete")
    _add_common_options(published)
    published.add_argument("--run-id", required=True)
    published.add_argument("--pr", required=True, type=int)
    published.add_argument("--merge-sha", required=True)
    evidence = subparsers.add_parser("record-certification-evidence", help="Append one strict certification artifact")
    _add_common_options(evidence)
    evidence.add_argument("--run-id", required=True)
    evidence.add_argument("--evidence", required=True, type=Path)
    projection = subparsers.add_parser(
        "certification-status", help="Recompute the authoritative certification projection"
    )
    _add_common_options(projection)
    return parser


def _result_payload(path: Path | None, value: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(value)
    if path is not None:
        payload = {"ledger_path": str(path.resolve()), **payload}
    return payload


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    common = {
        "repo_root": args.repo_root.resolve(),
        "config_path": args.config.resolve(),
    }
    if hasattr(args, "ledger_root"):
        common["ledger_root"] = args.ledger_root.resolve() if args.ledger_root else None
    try:
        if args.command == "inspect":
            value = inspect_target(args.target, repo_root=common["repo_root"], config_path=common["config_path"])
            path = None
        elif args.command == "start":
            path, value = start_run(args.target, owner=args.owner, **common)
        elif args.command == "resume":
            path, value = resume_run(args.target, run_id=args.run_id, **common)
        elif args.command == "status":
            path, value = status_run(args.target, **common)
        elif args.command == "record-plan-review":
            path, value = record_plan_review(
                args.target, run_id=args.run_id, verdict=args.verdict, evidence=args.evidence, **common
            )
        elif args.command == "record-change":
            path, value = record_change(
                args.target,
                run_id=args.run_id,
                owner_kind=args.owner_kind,
                author_family=args.author_family,
                summary=args.summary,
                **common,
            )
        elif args.command == "record-build":
            path, value = record_build(args.target, run_id=args.run_id, author_family=args.author_family, **common)
        elif args.command == "record-review":
            path, value = record_review(
                args.target,
                run_id=args.run_id,
                result_path=args.result,
                stability_check=args.stability_check,
                **common,
            )
        elif args.command == "record-instability-adjudication":
            path, value = record_instability_adjudication(
                args.target,
                run_id=args.run_id,
                evidence=args.evidence,
                summary=args.summary,
                **common,
            )
        elif args.command == "record-independent-review":
            path, value = record_independent_review(
                args.target,
                run_id=args.run_id,
                reviewer_family=args.reviewer_family,
                verdict=args.verdict,
                evidence=args.evidence,
                owner_kind=args.owner_kind,
                **common,
            )
        elif args.command == "record-published":
            path, value = record_published(
                args.target, run_id=args.run_id, pr=args.pr, merge_sha=args.merge_sha, **common
            )
        elif args.command == "record-certification-evidence":
            path, value = record_certification_evidence(
                args.target, run_id=args.run_id, evidence=args.evidence, **common
            )
        elif args.command == "certification-status":
            value = certification_projection(args.target, **common)
            path = None
        else:
            raise CompletionError(f"Unknown command: {args.command}")
    except (CompletionError, OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"track-completion: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(_result_payload(path, value), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
