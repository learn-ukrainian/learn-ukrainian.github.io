"""Explicit Entire 0.8.42 status/capability refresh and read-only caches."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.entire.private_mode_preflight import preflight as private_mode_preflight

from .model import SchemaError, validate_identity
from .paths import provider_capabilities_path, provider_status_path

REQUIRED_ENTIRE_VERSION = "0.8.42"
PROVIDER_STATUS_MAX_AGE_SECONDS = 900
PROVIDER_CAPABILITIES_MAX_AGE_SECONDS = 3600
_SOURCE_REPOSITORY_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$"
)
_SEARCH_COUNT_FIELDS = ("repos", "checkpoints", "commits", "prs", "sessions")
_DISPATCH_TOTAL_FIELDS = (
    "checkpoints",
    "used_checkpoint_count",
    "branches",
    "files_touched",
)
_DISPATCH_WARNING_FIELDS = (
    "access_denied_count",
    "pending_count",
    "failed_count",
    "unknown_count",
    "uncategorized_count",
    "truncated_count",
)


def _now_text() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["entire", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _run_with_input(
    repo_root: Path,
    args: list[str],
    input_text: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["entire", *args],
        cwd=repo_root,
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _agent_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = "-".join(value.strip().lower().split())
    try:
        validate_identity(normalized, field_name="agent")
    except SchemaError:
        return None
    return normalized


def _count(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return 0


def _count_map(value: object, fields: tuple[str, ...]) -> dict[str, int]:
    source = value if isinstance(value, dict) else {}
    return {field: _count(source.get(field)) for field in fields}


def _json_object(result: subprocess.CompletedProcess[str]) -> dict[str, Any] | None:
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _http_status(result: subprocess.CompletedProcess[str]) -> int | None:
    combined = f"{result.stderr}\n{result.stdout}"
    match = re.search(r"(?m)^HTTP/\S+ ([1-5]\d\d)(?:\s|$)", combined)
    if match is None:
        match = re.search(r"(?i)\bHTTP(?: status)?\s+([1-5]\d\d)\b", combined)
    return int(match.group(1)) if match else None


def _failure_reason(result: subprocess.CompletedProcess[str]) -> str:
    status = _http_status(result)
    if status == 401:
        return "authentication_failed"
    if status == 403:
        return "authorization_failed"
    if status == 404:
        return "repository_unavailable_or_region"
    if status == 429:
        return "rate_limited"
    return "provider_error"


def _private_recall_policy(root: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads((root / ".entire/private-recall.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _probe_cloud_search(root: Path, source_repo: str, query: str) -> dict[str, Any]:
    try:
        result = _run(
            root,
            "search",
            query,
            "--json",
            "--limit",
            "10",
            "--repo",
            source_repo,
        )
    except subprocess.TimeoutExpired:
        return {"reachable": False, "indexed_history": False, "reason": "timeout"}
    except OSError:
        return {"reachable": False, "indexed_history": False, "reason": "provider_error"}
    payload = _json_object(result)
    if payload is None:
        return {
            "reachable": False,
            "indexed_history": False,
            "reason": _failure_reason(result),
            "http_status": _http_status(result),
        }
    counts = _count_map(payload.get("counts"), _SEARCH_COUNT_FIELDS)
    indexed = sum(counts[field] for field in ("checkpoints", "commits", "sessions")) > 0
    return {
        "reachable": True,
        "indexed_history": indexed,
        "reason": None if indexed else "no_indexed_history",
        "result_count": _count(payload.get("total")),
        "counts": counts,
    }


def _probe_cloud_dispatch(root: Path, source_repo: str) -> dict[str, Any]:
    now = datetime.now(UTC)
    request = {
        "repos": [source_repo],
        "since": (now - timedelta(days=7)).isoformat().replace("+00:00", "Z"),
        "until": now.isoformat().replace("+00:00", "Z"),
        "generate": False,
    }
    try:
        result = _run_with_input(
            root,
            [
                "api",
                "-X",
                "POST",
                "/api/v1/dispatches/generate",
                "--input",
                "-",
                "--include",
            ],
            json.dumps(request, separators=(",", ":")),
        )
    except subprocess.TimeoutExpired:
        return {"reachable": False, "history_available": False, "reason": "timeout"}
    except OSError:
        return {"reachable": False, "history_available": False, "reason": "provider_error"}
    payload = _json_object(result)
    if payload is None:
        return {
            "reachable": False,
            "history_available": False,
            "reason": _failure_reason(result),
            "http_status": _http_status(result),
        }
    totals = _count_map(payload.get("totals"), _DISPATCH_TOTAL_FIELDS)
    warnings = _count_map(payload.get("warnings"), _DISPATCH_WARNING_FIELDS)
    history_available = totals["checkpoints"] > 0
    return {
        "reachable": True,
        "history_available": history_available,
        "reason": None if history_available else "no_checkpoint_history",
        "totals": totals,
        "warnings": warnings,
    }


def refresh_provider_capabilities(
    repo_root: Path,
    *,
    query: str,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Explicitly probe private-boundary, cloud-search, and dispatch capability.

    The search query and every provider body stay in memory. The persisted
    receipt contains only booleans, bounded reason codes, HTTP status, and
    aggregate counts. Dispatch uses ``generate:false`` so this health probe
    never asks the service to create or return an AI-generated summary.
    """
    root = Path(repo_root).expanduser().resolve()
    target = output_path or provider_capabilities_path(root)
    if not isinstance(query, str) or not query.strip() or len(query.encode("utf-8")) > 256:
        return {"available": False, "reason": "query_invalid"}
    try:
        preflight = private_mode_preflight(root)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        preflight = {"ready": False, "checks": {}, "issues": ["preflight_unavailable"]}
    candidate_checks = preflight.get("checks") if isinstance(preflight, dict) else None
    raw_checks = candidate_checks if isinstance(candidate_checks, dict) else {}
    checks = {
        key: value
        for key, value in sorted(raw_checks.items())
        if isinstance(key, str) and isinstance(value, bool)
    }
    raw_issues = preflight.get("issues") if isinstance(preflight, dict) else []
    preflight_shape_valid = (
        isinstance(preflight, dict)
        and isinstance(preflight.get("ready"), bool)
        and isinstance(candidate_checks, dict)
        and bool(candidate_checks)
        and len(checks) == len(candidate_checks)
        and isinstance(raw_issues, list)
        and all(isinstance(issue, str) for issue in raw_issues)
    )
    boundary_ready = (
        preflight_shape_valid
        and preflight.get("ready") is True
        and all(checks.values())
        and not raw_issues
    )
    boundary = {
        "ready": boundary_ready,
        "reason": (
            None
            if boundary_ready
            else "preflight_unavailable"
            if not preflight_shape_valid
            else "preflight_failed"
        ),
        "checks": checks,
        "issue_count": (
            len(raw_issues)
            if preflight_shape_valid
            else max(1, len(raw_issues) if isinstance(raw_issues, list) else 0)
        ),
    }
    payload: dict[str, Any] = {
        "schema": "entire-provider-capabilities.v1",
        "available": True,
        "generated_at": _now_text(),
        "private_boundary": boundary,
        "cloud": {
            "probed": False,
            "reason": "private_boundary_not_ready",
        },
    }
    policy = _private_recall_policy(root)
    source_repo = policy.get("source_repo") if isinstance(policy, dict) else None
    if boundary["ready"] and isinstance(source_repo, str) and _SOURCE_REPOSITORY_PATTERN.fullmatch(
        source_repo
    ):
        payload["cloud"] = {
            "probed": True,
            "search": _probe_cloud_search(root, source_repo, query.strip()),
            "dispatch": _probe_cloud_dispatch(root, source_repo),
        }
    elif boundary["ready"]:
        payload["cloud"] = {"probed": False, "reason": "source_repository_invalid"}
    _atomic_write(target, payload)
    return payload


def refresh_provider_status(
    repo_root: Path,
    *,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Run an explicit bounded CLI probe and persist only allowlisted fields."""
    root = Path(repo_root).expanduser().resolve()
    target = output_path or provider_status_path(root)
    try:
        version_result = _run(root, "version")
    except (OSError, subprocess.TimeoutExpired):
        return {"available": False, "reason": "entire_cli_unavailable"}
    version_line = version_result.stdout.splitlines()[0] if version_result.stdout else ""
    version = version_line.removeprefix("Entire CLI ").strip()
    if version_result.returncode != 0 or version != REQUIRED_ENTIRE_VERSION:
        return {
            "available": False,
            "reason": "entire_version_mismatch",
            "required_version": REQUIRED_ENTIRE_VERSION,
        }
    try:
        status_result = _run(root, "status", "--json")
        raw = json.loads(status_result.stdout) if status_result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        raw = None
    if not isinstance(raw, dict):
        return {"available": False, "reason": "entire_status_unavailable"}
    agents = [agent_id for agent in raw.get("agents", []) if (agent_id := _agent_id(agent))]
    active_sessions = []
    for session in raw.get("active_sessions", []):
        if not isinstance(session, dict):
            continue
        agent = _agent_id(session.get("agent"))
        status = session.get("status")
        if agent is not None and status in {"active", "ended", "unknown"}:
            active_sessions.append({"agent": agent, "status": status})
    payload = {
        "schema": "entire-provider-status.v1",
        "available": True,
        "generated_at": _now_text(),
        "version": version,
        "required_version": REQUIRED_ENTIRE_VERSION,
        "enabled": raw.get("enabled") is True,
        "installed_agents": sorted(set(agents)),
        "active_sessions": sorted(
            active_sessions, key=lambda item: (item["agent"], item["status"])
        ),
        "source": "entire-cli",
    }
    _atomic_write(target, payload)
    return payload


def load_provider_status(
    repo_root: Path,
    *,
    status_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Read the sanitized local cache without invoking Entire or the network."""
    target = status_path or provider_status_path(repo_root)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"available": False, "reason": "provider_status_missing"}
    if not isinstance(payload, dict) or payload.get("schema") != "entire-provider-status.v1":
        return {"available": False, "reason": "provider_status_unreadable"}
    try:
        generated = datetime.fromisoformat(str(payload["generated_at"]).replace("Z", "+00:00"))
        age = max(0, int(((now or datetime.now(UTC)) - generated).total_seconds()))
    except (KeyError, TypeError, ValueError):
        return {"available": False, "reason": "provider_status_unreadable"}
    safe = {
        key: payload[key]
        for key in (
            "schema",
            "available",
            "generated_at",
            "version",
            "required_version",
            "enabled",
            "installed_agents",
            "active_sessions",
            "source",
        )
        if key in payload
    }
    safe.update(
        {
            "age_seconds": age,
            "stale": age > PROVIDER_STATUS_MAX_AGE_SECONDS,
        }
    )
    return safe


def load_provider_capabilities(
    repo_root: Path,
    *,
    capabilities_path: Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Read the body-free provider-capability cache without invoking Entire."""
    target = capabilities_path or provider_capabilities_path(repo_root)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"available": False, "reason": "provider_capabilities_missing"}
    if not isinstance(payload, dict) or payload.get("schema") != "entire-provider-capabilities.v1":
        return {"available": False, "reason": "provider_capabilities_unreadable"}
    if payload.get("available") is not True:
        return {"available": False, "reason": "provider_capabilities_unreadable"}
    try:
        generated = datetime.fromisoformat(str(payload["generated_at"]).replace("Z", "+00:00"))
        age = max(0, int(((now or datetime.now(UTC)) - generated).total_seconds()))
    except (KeyError, TypeError, ValueError):
        return {"available": False, "reason": "provider_capabilities_unreadable"}
    raw_boundary = payload.get("private_boundary")
    raw_cloud = payload.get("cloud")
    if not isinstance(raw_boundary, dict) or not isinstance(raw_cloud, dict):
        return {"available": False, "reason": "provider_capabilities_unreadable"}
    raw_checks = raw_boundary.get("checks")
    raw_issue_count = raw_boundary.get("issue_count")
    if (
        not isinstance(raw_boundary.get("ready"), bool)
        or not isinstance(raw_checks, dict)
        or not all(
            isinstance(key, str) and isinstance(value, bool)
            for key, value in raw_checks.items()
        )
        or type(raw_issue_count) is not int
        or raw_issue_count < 0
        or not isinstance(raw_cloud.get("probed"), bool)
    ):
        return {"available": False, "reason": "provider_capabilities_unreadable"}
    checks = {key: value for key, value in sorted(raw_checks.items())}
    boundary_ready = raw_boundary.get("ready") is True
    raw_boundary_reason = raw_boundary.get("reason")
    if boundary_ready and (
        not checks
        or not all(checks.values())
        or raw_issue_count != 0
        or raw_boundary_reason is not None
    ):
        return {"available": False, "reason": "provider_capabilities_unreadable"}
    if not boundary_ready and raw_boundary_reason not in {
        "preflight_failed",
        "preflight_unavailable",
    }:
        return {"available": False, "reason": "provider_capabilities_unreadable"}
    boundary = {
        "ready": boundary_ready,
        "reason": raw_boundary_reason,
        "checks": checks,
        "issue_count": raw_issue_count,
    }
    cloud: dict[str, Any] = {"probed": raw_cloud.get("probed") is True}
    if cloud["probed"]:
        if not boundary_ready:
            return {"available": False, "reason": "provider_capabilities_unreadable"}
        raw_search = raw_cloud.get("search")
        raw_dispatch = raw_cloud.get("dispatch")
        if (
            not isinstance(raw_search, dict)
            or not isinstance(raw_dispatch, dict)
            or not isinstance(raw_search.get("reachable"), bool)
            or not isinstance(raw_search.get("indexed_history"), bool)
            or not isinstance(raw_dispatch.get("reachable"), bool)
            or not isinstance(raw_dispatch.get("history_available"), bool)
        ):
            return {"available": False, "reason": "provider_capabilities_unreadable"}
        search_reachable = raw_search.get("reachable") is True
        search_indexed = raw_search.get("indexed_history") is True
        dispatch_reachable = raw_dispatch.get("reachable") is True
        dispatch_history = raw_dispatch.get("history_available") is True
        search_reason = raw_search.get("reason")
        dispatch_reason = raw_dispatch.get("reason")
        if (
            (search_indexed and (not search_reachable or search_reason is not None))
            or (
                search_reachable
                and not search_indexed
                and search_reason != "no_indexed_history"
            )
            or (
                not search_reachable
                and (search_indexed or search_reason in {None, "no_indexed_history"})
            )
            or (dispatch_history and (not dispatch_reachable or dispatch_reason is not None))
            or (
                dispatch_reachable
                and not dispatch_history
                and dispatch_reason != "no_checkpoint_history"
            )
            or (
                not dispatch_reachable
                and (dispatch_history or dispatch_reason in {None, "no_checkpoint_history"})
            )
        ):
            return {"available": False, "reason": "provider_capabilities_unreadable"}
        search = {
            "reachable": search_reachable,
            "indexed_history": search_indexed,
            "reason": search_reason
            if search_reason
            in {
                None,
                "no_indexed_history",
                "authentication_failed",
                "authorization_failed",
                "repository_unavailable_or_region",
                "rate_limited",
                "timeout",
                "provider_error",
            }
            else "provider_error",
        }
        dispatch = {
            "reachable": dispatch_reachable,
            "history_available": dispatch_history,
            "reason": dispatch_reason
            if dispatch_reason
            in {
                None,
                "no_checkpoint_history",
                "authentication_failed",
                "authorization_failed",
                "repository_unavailable_or_region",
                "rate_limited",
                "timeout",
                "provider_error",
            }
            else "provider_error",
        }
        if search_reachable:
            search.update(
                {
                    "result_count": _count(raw_search.get("result_count")),
                    "counts": _count_map(raw_search.get("counts"), _SEARCH_COUNT_FIELDS),
                }
            )
        if dispatch_reachable:
            dispatch.update(
                {
                    "totals": _count_map(raw_dispatch.get("totals"), _DISPATCH_TOTAL_FIELDS),
                    "warnings": _count_map(
                        raw_dispatch.get("warnings"), _DISPATCH_WARNING_FIELDS
                    ),
                }
            )
        if (
            type(raw_search.get("http_status")) is int
            and 100 <= raw_search["http_status"] <= 599
        ):
            search["http_status"] = raw_search["http_status"]
        if (
            type(raw_dispatch.get("http_status")) is int
            and 100 <= raw_dispatch["http_status"] <= 599
        ):
            dispatch["http_status"] = raw_dispatch["http_status"]
        cloud.update({"search": search, "dispatch": dispatch})
    else:
        expected_reason = (
            "source_repository_invalid" if boundary_ready else "private_boundary_not_ready"
        )
        if raw_cloud.get("reason") != expected_reason:
            return {"available": False, "reason": "provider_capabilities_unreadable"}
        cloud["reason"] = expected_reason
    return {
        "schema": "entire-provider-capabilities.v1",
        "available": True,
        "generated_at": payload["generated_at"],
        "age_seconds": age,
        "stale": age > PROVIDER_CAPABILITIES_MAX_AGE_SECONDS,
        "private_boundary": boundary,
        "cloud": cloud,
    }
