"""Persistent storage for LLM quality-gate results.

The pipeline may still emit ``llm_qg.json`` artifacts for debugging or
promotion workflows, but durable gate state belongs in a local SQLite store.
This keeps generated QG files out of PR diffs while still giving the Monitor
API and certification code a queryable source of truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from collections import Counter
from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from scripts.api.config import PROJECT_ROOT
from scripts.api.resilience import connect_sqlite

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "telemetry" / "llm_qg.db"
DB_ENV_VAR = "LEARN_UKRAINIAN_LLM_QG_DB"
DEFAULT_CIRCUIT_STATE_PATH = PROJECT_ROOT / "data" / "telemetry" / "llm_qg_live_circuit.json"
CIRCUIT_ENV_VAR = "LEARN_UKRAINIAN_LLM_QG_CIRCUIT"
CIRCUIT_SCHEMA_VERSION = "llm_qg_live_circuit.v1"
CIRCUIT_WINDOW_SIZE = 30
CIRCUIT_FAILURE_RATE_THRESHOLD = 0.15
CIRCUIT_TERMINAL_FAILURE_STATUSES = frozenset(
    {
        "provider_error",
        "parse_failure",
        "schema_failure",
        "RETRY_EXHAUSTED",
        "timeout",
    }
)
CONTENT_FILES = ("module.md", "activities.yaml", "vocabulary.yaml", "resources.yaml")
EVIDENCE_SCHEMA_VERSION = "llm_qg_evidence.v1"
SUPPORTED_EVIDENCE_GATE_VERSIONS = frozenset({"v7.llm_qg.1"})
DIMENSION_ORDER = ("pedagogical", "naturalness", "decolonization", "engagement", "tone")
TOOL_EVENT_KEYS = ("tool", "input", "status", "tool_call_id", "output")


@dataclass(frozen=True, slots=True)
class StoredQG:
    """One persisted LLM-QG run."""

    run_id: str
    level: str
    slug: str
    content_sha: str
    gate_version: str
    prompt_hash: str | None
    checker_version: str | None
    level_policy_family: str | None
    reviewer_model: str | None
    reviewer_family: str | None
    source: str
    payload: dict[str, Any]
    created_at: str
    tool_call_count: int = 0
    tools_used: tuple[str, ...] = ()
    route_name: str | None = None
    tool_events: tuple[dict[str, Any], ...] | None = None
    raw_response: str | None = None
    raw_response_sha256: str | None = None
    dispatch_metadata: dict[str, Any] | None = None
    retry_history: tuple[dict[str, Any], ...] | None = None
    gate_outcomes: dict[str, Any] | None = None
    attempt_id: int | None = None

    def is_current_for(self, module_dir: Path) -> bool:
        return self.content_sha == content_sha_for_module(module_dir)


def db_path(path: Path | None = None) -> Path:
    """Return the configured QG database path."""
    if path is not None:
        return path
    return Path(os.environ.get(DB_ENV_VAR, str(DEFAULT_DB_PATH)))


def circuit_state_path(path: Path | None = None) -> Path:
    """Return the configured live Tier-2 circuit state path."""
    if path is not None:
        return path
    return Path(os.environ.get(CIRCUIT_ENV_VAR, str(DEFAULT_CIRCUIT_STATE_PATH)))


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_pretty(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_sha_for_module(module_dir: Path) -> str:
    """Hash the learner-facing source artifacts for one module directory."""
    h = hashlib.sha256()
    for name in CONTENT_FILES:
        path = module_dir / name
        if not path.exists():
            continue
        h.update(name.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def llm_qg_file_is_current_for_module(module_dir: Path, path: Path | None = None) -> bool:
    """Return True when a module-local QG artifact is not older than content.

    File artifacts do not carry a content hash. Treat them as a fallback only
    when their mtime is at least as new as every learner-facing source file.
    """
    qg_path = path or module_dir / "llm_qg.json"
    try:
        artifact_mtime_ns = qg_path.stat().st_mtime_ns
    except OSError:
        return False

    for name in CONTENT_FILES:
        content_path = module_dir / name
        if not content_path.exists():
            continue
        try:
            if content_path.stat().st_mtime_ns > artifact_mtime_ns:
                return False
        except OSError:
            return False
    return True


def prompt_hash_for_text(prompt: str | None) -> str | None:
    """Return a stable hash for a prompt body, if present."""
    if prompt is None:
        return None
    return _sha256_bytes(prompt.encode("utf-8"))


def init_db(path: Path | None = None) -> Path:
    """Create the LLM-QG persistence schema if needed."""
    resolved = db_path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect_sqlite(str(resolved))) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS llm_qg_runs (
                run_id          TEXT PRIMARY KEY,
                created_at      TEXT NOT NULL,
                level           TEXT NOT NULL,
                slug            TEXT NOT NULL,
                content_sha     TEXT NOT NULL,
                gate_version    TEXT NOT NULL,
                prompt_hash     TEXT,
                checker_version TEXT,
                level_policy_family TEXT,
                reviewer_model  TEXT,
                reviewer_family TEXT,
                source          TEXT NOT NULL,
                verdict         TEXT,
                terminal_verdict TEXT,
                min_score       REAL,
                min_dim         TEXT,
                payload_json    TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_llm_qg_level_slug_created
                ON llm_qg_runs(level, slug, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_llm_qg_level_slug_content
                ON llm_qg_runs(level, slug, content_sha, created_at DESC);

            CREATE TABLE IF NOT EXISTS llm_qg_findings (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id          TEXT NOT NULL,
                category        TEXT,
                severity        TEXT,
                file            TEXT,
                quote           TEXT,
                replacement     TEXT,
                payload_json    TEXT NOT NULL,
                FOREIGN KEY(run_id) REFERENCES llm_qg_runs(run_id)
                    ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_llm_qg_findings_run
                ON llm_qg_findings(run_id, id);
            CREATE INDEX IF NOT EXISTS idx_llm_qg_findings_category
                ON llm_qg_findings(category, severity);
            """
        )
        _ensure_composite_columns(conn)
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_llm_qg_composite
                ON llm_qg_runs(
                    level, slug, content_sha, gate_version, prompt_hash,
                    checker_version, level_policy_family, reviewer_model,
                    created_at DESC
                )
            """
        )
        conn.commit()
    return resolved


def live_tier2_circuit_status(path: Path | None = None) -> dict[str, Any]:
    """Return deterministic live Tier-2 circuit state from the sidecar file."""
    state = _read_circuit_state(path)
    return _circuit_status_from_state(state)


def live_tier2_circuit_open_message(path: Path | None = None) -> str:
    """Return the operator-facing message for an open live Tier-2 circuit."""
    status = live_tier2_circuit_status(path)
    message = status.get("operator_message")
    if isinstance(message, str) and message:
        return message
    return _circuit_open_message(status)


def reset_live_tier2_circuit(path: Path | None = None) -> dict[str, Any]:
    """Clear the live Tier-2 circuit until new live outcomes trip it again."""
    resolved = circuit_state_path(path)
    state = _empty_circuit_state()
    now = _now_z()
    state["reset_at"] = now
    state["updated_at"] = now
    _write_circuit_state(resolved, state)
    return _circuit_status_from_state(state)


def record_live_tier2_outcome(
    *,
    level: str,
    slug: str,
    gate_version: str,
    reviewer_model: str | None,
    reviewer_family: str | None,
    route_name: str | None,
    status: str,
    reason: str | None = None,
    path: Path | None = None,
) -> dict[str, Any]:
    """Persist one completed live Tier-2 passage outcome for circuit accounting."""
    resolved = circuit_state_path(path)
    state = _read_circuit_state(resolved)
    outcome_status = status.strip()
    now = _now_z()
    outcome = {
        "created_at": now,
        "level": level.strip().lower(),
        "slug": slug.strip(),
        "gate_version": gate_version,
        "reviewer_model": reviewer_model,
        "reviewer_family": reviewer_family,
        "route_name": route_name,
        "status": outcome_status,
        "reason": reason,
        "terminal_failure": live_tier2_status_is_terminal_failure(outcome_status),
    }
    outcomes = [item for item in state.get("live_outcomes", []) if isinstance(item, Mapping)]
    outcomes.append(outcome)
    state["live_outcomes"] = outcomes[-CIRCUIT_WINDOW_SIZE:]
    state["updated_at"] = now
    status_payload = _circuit_status_from_state(state)
    if status_payload["open"] and not state.get("opened_at"):
        state["opened_at"] = now
    state["operator_message"] = _circuit_open_message(status_payload) if status_payload["open"] else None
    _write_circuit_state(resolved, state)
    return _circuit_status_from_state(state)


def live_tier2_status_is_terminal_failure(status: str) -> bool:
    """Return True for infra/provider terminal failures that trip the circuit."""
    return status.strip() in CIRCUIT_TERMINAL_FAILURE_STATUSES


def _empty_circuit_state() -> dict[str, Any]:
    return {
        "schema_version": CIRCUIT_SCHEMA_VERSION,
        "window_size": CIRCUIT_WINDOW_SIZE,
        "failure_rate_threshold": CIRCUIT_FAILURE_RATE_THRESHOLD,
        "opened_at": None,
        "operator_message": None,
        "live_outcomes": [],
    }


def _read_circuit_state(path: Path | None = None) -> dict[str, Any]:
    resolved = circuit_state_path(path)
    if not resolved.exists():
        return _empty_circuit_state()
    try:
        loaded = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_circuit_state()
    if not isinstance(loaded, dict) or loaded.get("schema_version") != CIRCUIT_SCHEMA_VERSION:
        return _empty_circuit_state()
    state = _empty_circuit_state()
    state.update(loaded)
    outcomes = state.get("live_outcomes")
    state["live_outcomes"] = outcomes if isinstance(outcomes, list) else []
    return state


def _write_circuit_state(path: Path, state: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json_pretty(dict(state)) + "\n", encoding="utf-8")


def _circuit_status_from_state(state: Mapping[str, Any]) -> dict[str, Any]:
    raw_outcomes = state.get("live_outcomes")
    outcomes = [item for item in raw_outcomes if isinstance(item, Mapping)] if isinstance(raw_outcomes, list) else []
    window = outcomes[-CIRCUIT_WINDOW_SIZE:]
    failure_count = sum(1 for item in window if item.get("terminal_failure") is True)
    attempted = len(window)
    failure_rate = (failure_count / attempted) if attempted else 0.0
    threshold_exceeded = attempted >= CIRCUIT_WINDOW_SIZE and failure_rate > CIRCUIT_FAILURE_RATE_THRESHOLD
    opened_at = state.get("opened_at") if isinstance(state.get("opened_at"), str) else None
    is_open = bool(opened_at) or threshold_exceeded
    status = {
        "schema_version": CIRCUIT_SCHEMA_VERSION,
        "open": is_open,
        "opened_at": opened_at,
        "window_size": CIRCUIT_WINDOW_SIZE,
        "attempted": attempted,
        "terminal_failures": failure_count,
        "failure_rate": round(failure_rate, 6),
        "failure_rate_threshold": CIRCUIT_FAILURE_RATE_THRESHOLD,
        "operator_message": None,
    }
    if is_open:
        status["operator_message"] = (
            state.get("operator_message")
            if isinstance(state.get("operator_message"), str) and state.get("operator_message")
            else _circuit_open_message(status)
        )
    return status


def _circuit_open_message(status: Mapping[str, Any]) -> str:
    failures = int(status.get("terminal_failures") or 0)
    attempted = int(status.get("attempted") or 0)
    threshold = float(status.get("failure_rate_threshold") or CIRCUIT_FAILURE_RATE_THRESHOLD)
    return (
        "live Tier-2 circuit_open: "
        f"{failures}/{attempted} recent live passages ended in terminal provider/parse/schema/"
        f"timeout failures (> {threshold:.0%}). Fix or reroute the reviewer lane, then reset with "
        ".venv/bin/python scripts/audit/qg_workflow.py --reset-circuit."
    )


def _ensure_composite_columns(conn: sqlite3.Connection) -> None:
    """Backfill optional composite-key columns on older local stores."""
    rows = conn.execute("PRAGMA table_info(llm_qg_runs)").fetchall()
    existing = {str(row[1]) for row in rows}
    additions = {
        "checker_version": "TEXT",
        "level_policy_family": "TEXT",
        # #2156: transport identity in the composite cache key + tool telemetry.
        "route_name": "TEXT",
        "tool_call_count": "INTEGER",
        "tools_used_json": "TEXT",
        "tool_events_json": "TEXT",
        # Nullable replay data preserves backward compatibility for existing
        # workflow caches.  Missing values make an old row non-production.
        "raw_response": "TEXT",
        "raw_response_sha256": "TEXT",
        "dispatch_json": "TEXT",
        "retry_history_json": "TEXT",
        "gate_outcomes_json": "TEXT",
        "attempt_id": "INTEGER",
    }
    for name, column_type in additions.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE llm_qg_runs ADD COLUMN {name} {column_type}")


def _aggregate(payload: dict[str, Any]) -> dict[str, Any]:
    aggregate = payload.get("aggregate")
    return aggregate if isinstance(aggregate, dict) else {}


def _iter_findings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    findings = payload.get("findings")
    if isinstance(findings, list):
        return [item for item in findings if isinstance(item, dict)]
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, dict):
        return []
    out: list[dict[str, Any]] = []
    for dim, entry in dimensions.items():
        if not isinstance(entry, dict):
            continue
        dim_findings = entry.get("findings")
        if isinstance(dim_findings, list):
            for item in dim_findings:
                if isinstance(item, dict):
                    out.append({"dimension": dim, **item})
    return out


def _finding_category(item: dict[str, Any]) -> Any:
    return (
        item.get("category")
        or item.get("issue_id")
        or item.get("issue_type")
        or item.get("type")
        or item.get("kind")
    )


def _normalize_tool_events(tool_events: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Return the replayable subset of normalized dispatch tool events."""
    normalized: list[dict[str, Any]] = []
    for event in tool_events:
        if not isinstance(event, Mapping):
            continue
        normalized.append({key: event.get(key) for key in TOOL_EVENT_KEYS})
    return tuple(normalized)


def record_llm_qg(
    *,
    level: str,
    slug: str,
    module_dir: Path,
    payload: dict[str, Any],
    gate_version: str,
    prompt_hash: str | None = None,
    checker_version: str | None = None,
    level_policy_family: str | None = None,
    reviewer_model: str | None = None,
    reviewer_family: str | None = None,
    route_name: str | None = None,
    tool_call_count: int = 0,
    tools_used: Sequence[str] = (),
    tool_events: Sequence[Mapping[str, Any]] = (),
    raw_response: str | None = None,
    raw_response_sha256: str | None = None,
    dispatch_metadata: Mapping[str, Any] | None = None,
    retry_history: Sequence[Mapping[str, Any]] | None = None,
    gate_outcomes: Mapping[str, Any] | None = None,
    attempt_id: int | None = None,
    source: str = "pipeline",
    run_id: str | None = None,
    path: Path | None = None,
) -> StoredQG:
    """Persist one LLM-QG run and return the stored record."""
    resolved = init_db(path)
    clean_level = level.strip().lower()
    clean_slug = slug.strip()
    clean_run_id = run_id or f"llm-qg-{uuid4().hex}"
    created_at = _now_z()
    content_sha = content_sha_for_module(module_dir)
    aggregate = _aggregate(payload)
    findings = _iter_findings(payload)
    tools_used_tuple = tuple(str(tool) for tool in tools_used)
    tool_call_count_int = int(tool_call_count)
    normalized_tool_events = _normalize_tool_events(tool_events)
    normalized_dispatch = dict(dispatch_metadata) if isinstance(dispatch_metadata, Mapping) else None
    normalized_history = (
        [dict(item) for item in retry_history if isinstance(item, Mapping)]
        if retry_history is not None
        else None
    )
    normalized_gate_outcomes = dict(gate_outcomes) if isinstance(gate_outcomes, Mapping) else None

    with closing(connect_sqlite(str(resolved))) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        _ensure_composite_columns(conn)
        conn.execute(
            """
            INSERT INTO llm_qg_runs (
                run_id, created_at, level, slug, content_sha, gate_version,
                prompt_hash, checker_version, level_policy_family,
                reviewer_model, reviewer_family, route_name,
                tool_call_count, tools_used_json, tool_events_json,
                raw_response, raw_response_sha256, dispatch_json,
                retry_history_json, gate_outcomes_json, attempt_id,
                source, verdict, terminal_verdict,
                min_score, min_dim, payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                created_at = excluded.created_at,
                level = excluded.level,
                slug = excluded.slug,
                content_sha = excluded.content_sha,
                gate_version = excluded.gate_version,
                prompt_hash = excluded.prompt_hash,
                checker_version = excluded.checker_version,
                level_policy_family = excluded.level_policy_family,
                reviewer_model = excluded.reviewer_model,
                reviewer_family = excluded.reviewer_family,
                route_name = excluded.route_name,
                tool_call_count = excluded.tool_call_count,
                tools_used_json = excluded.tools_used_json,
                tool_events_json = excluded.tool_events_json,
                raw_response = excluded.raw_response,
                raw_response_sha256 = excluded.raw_response_sha256,
                dispatch_json = excluded.dispatch_json,
                retry_history_json = excluded.retry_history_json,
                gate_outcomes_json = excluded.gate_outcomes_json,
                attempt_id = excluded.attempt_id,
                source = excluded.source,
                verdict = excluded.verdict,
                terminal_verdict = excluded.terminal_verdict,
                min_score = excluded.min_score,
                min_dim = excluded.min_dim,
                payload_json = excluded.payload_json
            """,
            (
                clean_run_id,
                created_at,
                clean_level,
                clean_slug,
                content_sha,
                gate_version,
                prompt_hash,
                checker_version,
                level_policy_family,
                reviewer_model,
                reviewer_family,
                route_name,
                tool_call_count_int,
                _json_dumps(list(tools_used_tuple)),
                _json_dumps(list(normalized_tool_events)),
                raw_response,
                raw_response_sha256,
                _json_dumps(normalized_dispatch) if normalized_dispatch is not None else None,
                _json_dumps(normalized_history) if normalized_history is not None else None,
                _json_dumps(normalized_gate_outcomes) if normalized_gate_outcomes is not None else None,
                attempt_id,
                source,
                aggregate.get("verdict"),
                aggregate.get("terminal_verdict"),
                aggregate.get("min_score"),
                aggregate.get("min_dim"),
                _json_dumps(payload),
            ),
        )
        conn.execute("DELETE FROM llm_qg_findings WHERE run_id = ?", (clean_run_id,))
        conn.executemany(
            """
            INSERT INTO llm_qg_findings (
                run_id, category, severity, file, quote, replacement, payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    clean_run_id,
                    _finding_category(item),
                    item.get("severity"),
                    item.get("file"),
                    item.get("quote"),
                    item.get("replacement"),
                    _json_dumps(item),
                )
                for item in findings
            ],
        )
        conn.commit()

    return StoredQG(
        run_id=clean_run_id,
        level=clean_level,
        slug=clean_slug,
        content_sha=content_sha,
        gate_version=gate_version,
        prompt_hash=prompt_hash,
        checker_version=checker_version,
        level_policy_family=level_policy_family,
        reviewer_model=reviewer_model,
        reviewer_family=reviewer_family,
        source=source,
        payload=payload,
        created_at=created_at,
        tool_call_count=tool_call_count_int,
        tools_used=tools_used_tuple,
        route_name=route_name,
        tool_events=normalized_tool_events,
        raw_response=raw_response,
        raw_response_sha256=raw_response_sha256,
        dispatch_metadata=normalized_dispatch,
        retry_history=tuple(normalized_history) if normalized_history is not None else None,
        gate_outcomes=normalized_gate_outcomes,
        attempt_id=attempt_id,
    )


def _row_key(row: sqlite3.Row, key: str) -> Any:
    """Return a column value if present, else None (legacy rows lack new cols)."""
    try:
        return row[key]
    except (IndexError, KeyError):
        return None


def _tools_used_from_row(row: sqlite3.Row) -> tuple[str, ...]:
    raw = _row_key(row, "tools_used_json")
    if not raw:
        return ()
    try:
        loaded = json.loads(str(raw))
    except (json.JSONDecodeError, ValueError):
        return ()
    if not isinstance(loaded, list):
        return ()
    return tuple(str(item) for item in loaded)


def _tool_events_from_row(row: sqlite3.Row) -> tuple[dict[str, Any], ...] | None:
    raw = _row_key(row, "tool_events_json")
    if raw is None:
        return None
    try:
        loaded = json.loads(str(raw))
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(loaded, list):
        return None
    return _normalize_tool_events(item for item in loaded if isinstance(item, Mapping))


def _mapping_from_row(row: sqlite3.Row, column: str) -> dict[str, Any] | None:
    raw = _row_key(row, column)
    if raw is None:
        return None
    try:
        loaded = json.loads(str(raw))
    except (json.JSONDecodeError, ValueError):
        return None
    return dict(loaded) if isinstance(loaded, Mapping) else None


def _history_from_row(row: sqlite3.Row) -> tuple[dict[str, Any], ...] | None:
    raw = _row_key(row, "retry_history_json")
    if raw is None:
        return None
    try:
        loaded = json.loads(str(raw))
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(loaded, list) or not all(isinstance(item, Mapping) for item in loaded):
        return None
    return tuple(dict(item) for item in loaded)


def _row_to_record(row: sqlite3.Row) -> StoredQG:
    raw_tool_count = _row_key(row, "tool_call_count")
    return StoredQG(
        run_id=str(row["run_id"]),
        level=str(row["level"]),
        slug=str(row["slug"]),
        content_sha=str(row["content_sha"]),
        gate_version=str(row["gate_version"]),
        prompt_hash=row["prompt_hash"],
        checker_version=row["checker_version"],
        level_policy_family=row["level_policy_family"],
        reviewer_model=row["reviewer_model"],
        reviewer_family=row["reviewer_family"],
        source=str(row["source"]),
        payload=json.loads(str(row["payload_json"])),
        created_at=str(row["created_at"]),
        tool_call_count=int(raw_tool_count) if raw_tool_count is not None else 0,
        tools_used=_tools_used_from_row(row),
        route_name=_row_key(row, "route_name"),
        tool_events=_tool_events_from_row(row),
        raw_response=_row_key(row, "raw_response"),
        raw_response_sha256=_row_key(row, "raw_response_sha256"),
        dispatch_metadata=_mapping_from_row(row, "dispatch_json"),
        retry_history=_history_from_row(row),
        gate_outcomes=_mapping_from_row(row, "gate_outcomes_json"),
        attempt_id=(int(_row_key(row, "attempt_id")) if _row_key(row, "attempt_id") is not None else None),
    )


def latest_llm_qg(
    level: str,
    slug: str,
    *,
    content_sha: str | None = None,
    gate_version: str | None = None,
    prompt_hash: str | None = None,
    checker_version: str | None = None,
    level_policy_family: str | None = None,
    reviewer_model: str | None = None,
    route_name: str | None = None,
    path: Path | None = None,
) -> StoredQG | None:
    """Return the newest persisted QG run for a module, optionally hash-bound."""
    resolved = db_path(path)
    if not resolved.exists():
        return None
    params: list[Any] = [level.strip().lower(), slug.strip()]
    where = "level = ? AND slug = ?"
    for column, value in (
        ("content_sha", content_sha),
        ("gate_version", gate_version),
        ("prompt_hash", prompt_hash),
        ("checker_version", checker_version),
        ("level_policy_family", level_policy_family),
        ("reviewer_model", reviewer_model),
        ("route_name", route_name),
    ):
        if value is not None:
            where += f" AND {column} = ?"
            params.append(value)
    try:
        with closing(connect_sqlite(str(resolved))) as conn:
            _ensure_composite_columns(conn)
            conn.commit()
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                f"""
                SELECT *
                FROM llm_qg_runs
                WHERE {where}
                ORDER BY created_at DESC, run_id DESC
                LIMIT 1
                """,
                params,
            ).fetchone()
        return _row_to_record(row) if row else None
    except (json.JSONDecodeError, OSError, sqlite3.DatabaseError, ValueError):
        return None


def current_llm_qg_for_module(
    level: str,
    slug: str,
    module_dir: Path,
    *,
    gate_version: str | None = None,
    prompt_hash: str | None = None,
    checker_version: str | None = None,
    level_policy_family: str | None = None,
    reviewer_model: str | None = None,
    route_name: str | None = None,
    path: Path | None = None,
) -> StoredQG | None:
    """Return the newest QG run whose content hash matches current artifacts."""
    return latest_llm_qg(
        level,
        slug,
        content_sha=content_sha_for_module(module_dir),
        gate_version=gate_version,
        prompt_hash=prompt_hash,
        checker_version=checker_version,
        level_policy_family=level_policy_family,
        reviewer_model=reviewer_model,
        route_name=route_name,
        path=path,
    )


def current_payload_for_module(
    level: str,
    slug: str,
    module_dir: Path,
    *,
    gate_version: str | None = None,
    prompt_hash: str | None = None,
    checker_version: str | None = None,
    level_policy_family: str | None = None,
    reviewer_model: str | None = None,
    path: Path | None = None,
) -> dict[str, Any] | None:
    """Return the current QG payload for a module, or ``None`` if missing/stale."""
    record = current_llm_qg_for_module(
        level,
        slug,
        module_dir,
        gate_version=gate_version,
        prompt_hash=prompt_hash,
        checker_version=checker_version,
        level_policy_family=level_policy_family,
        reviewer_model=reviewer_model,
        path=path,
    )
    if record is None:
        return None
    return {
        **record.payload,
        "_store": {
            "run_id": record.run_id,
            "created_at": record.created_at,
            "content_sha": record.content_sha,
            "gate_version": record.gate_version,
            "prompt_hash": record.prompt_hash,
            "checker_version": record.checker_version,
            "level_policy_family": record.level_policy_family,
            "reviewer_model": record.reviewer_model,
            "source": record.source,
        },
    }


def compact_evidence_for_record(
    record: StoredQG,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    """Return a compact, git-friendly evidence snapshot for one stored run."""
    aggregate = _aggregate(record.payload)
    raw_dimensions = record.payload.get("dimensions")
    dimensions: dict[str, dict[str, Any]] = {}
    if isinstance(raw_dimensions, dict):
        ordered_dims = [
            *[dim for dim in DIMENSION_ORDER if dim in raw_dimensions],
            *sorted(dim for dim in raw_dimensions if dim not in DIMENSION_ORDER),
        ]
        for dim in ordered_dims:
            entry = raw_dimensions.get(dim)
            if not isinstance(entry, dict):
                continue
            compact_entry: dict[str, Any] = {}
            if isinstance(entry.get("score"), int | float):
                compact_entry["score"] = float(entry["score"])
            if isinstance(entry.get("verdict"), str):
                compact_entry["verdict"] = entry["verdict"]
            if compact_entry:
                dimensions[dim] = compact_entry

    findings_summary = _findings_summary(record.payload)
    result: dict[str, Any] = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "level": record.level,
        "slug": record.slug,
        "content_sha": record.content_sha,
        "gate_version": record.gate_version,
        "prompt_hash": record.prompt_hash,
        "checker_version": record.checker_version,
        "level_policy_family": record.level_policy_family,
        "provenance": {
            "created_at": record.created_at,
            "run_id": record.run_id,
            "source": record.source,
        },
        "reviewer": {
            "family": record.reviewer_family,
            "model": record.reviewer_model,
        },
        "verdict": aggregate.get("verdict"),
        "terminal_verdict": aggregate.get("terminal_verdict"),
        "min_score": aggregate.get("min_score"),
        "min_dim": aggregate.get("min_dim"),
        "dimensions": dimensions,
        "findings_summary": findings_summary,
    }
    if profile:
        result["profile"] = profile
    return result


def _findings_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return count-only finding metadata safe to persist in git."""
    by_category: Counter[str] = Counter()
    by_severity: Counter[str] = Counter()
    total = 0
    raw_dimensions = payload.get("dimensions")
    if isinstance(raw_dimensions, Mapping):
        for entry in raw_dimensions.values():
            if not isinstance(entry, Mapping):
                continue
            findings = entry.get("findings")
            if not isinstance(findings, list):
                continue
            for finding in findings:
                if not isinstance(finding, Mapping):
                    continue
                total += 1
                category = finding.get("category") or finding.get("issue_id") or "uncategorized"
                severity = finding.get("severity") or "unknown"
                by_category[str(category)] += 1
                by_severity[str(severity)] += 1
    return {
        "total": total,
        "by_category": dict(sorted(by_category.items())),
        "by_severity": dict(sorted(by_severity.items())),
    }


def current_evidence_for_module(
    level: str,
    slug: str,
    module_dir: Path,
    *,
    profile: str | None = None,
    path: Path | None = None,
) -> dict[str, Any] | None:
    """Return a compact evidence snapshot for the current module hash."""
    record = current_llm_qg_for_module(level, slug, module_dir, path=path)
    if record is None:
        return None
    return compact_evidence_for_record(record, profile=profile)


def evidence_record_is_current_for_module(
    evidence: Mapping[str, Any],
    module_dir: Path,
) -> bool:
    """Return True when a compact evidence record matches module content."""
    return evidence.get("content_sha") == content_sha_for_module(module_dir)


def evidence_record_passes_for_module(
    evidence: Mapping[str, Any],
    module_dir: Path,
    *,
    supported_gate_versions: set[str] | frozenset[str] = SUPPORTED_EVIDENCE_GATE_VERSIONS,
) -> bool:
    """Return True when evidence is current and acceptable for promotion."""
    return (
        evidence.get("schema_version") == EVIDENCE_SCHEMA_VERSION
        and str(evidence.get("terminal_verdict", "")).upper() == "PASS"
        and evidence.get("gate_version") in supported_gate_versions
        and evidence_record_is_current_for_module(evidence, module_dir)
    )


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export/check compact LLM-QG evidence records.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-record", action="store_true", help="Export current DB evidence as compact JSON.")
    mode.add_argument("--check-record", action="store_true", help="Check compact JSON content_sha against a module.")
    parser.add_argument("--level", help="Curriculum level, e.g. b1.")
    parser.add_argument("--slug", help="Module slug.")
    parser.add_argument("--module-dir", type=Path, required=True, help="Module artifact directory.")
    parser.add_argument("--profile", help="Optional curriculum profile label.")
    parser.add_argument("--db", type=Path, help="Optional LLM-QG SQLite path.")
    parser.add_argument("--out", type=Path, help="Output JSON path for --emit-record.")
    parser.add_argument("--record", type=Path, help="Input JSON path for --check-record.")
    args = parser.parse_args(argv)

    if args.emit_record:
        if not args.level or not args.slug or not args.out:
            parser.error("--emit-record requires --level, --slug, and --out")
        evidence = current_evidence_for_module(
            args.level,
            args.slug,
            args.module_dir,
            profile=args.profile,
            path=args.db,
        )
        if evidence is None:
            print("No current LLM-QG DB record for module content")
            return 1
        _write_json(args.out, evidence)
        return 0

    if not args.record:
        parser.error("--check-record requires --record")
    evidence = json.loads(args.record.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict) or not evidence_record_passes_for_module(
        evidence,
        args.module_dir,
    ):
        print("LLM-QG evidence record is stale or not acceptable for module content")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
