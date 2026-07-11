"""ADR-011 P3 — privacy-safe research consumption + surfacing telemetry.

Two distinct signals, both routed through the *existing* central JSONL emitter
(``scripts/telemetry/emit.py``) — this module creates no new event store and no
new task store:

* **Surfacing** (``research_pointer_surfaced``): a bounded pointer was injected
  into a task/prompt/cold-start context. It says "the agent was *shown* this id".
* **Consumption** (``research_record_consumed``): the agent actually fetched a
  record body on demand (``/api/knowledge/record/{id}`` → 200 or a cache-backed
  304) *and* the request carried a validated, still-active task id. It says "the
  agent *used* this id". Surfaced ≠ consumed.

Task correlation is validated **conservatively** and fails closed. An invalid,
missing, finished, or unknown task never raises, never changes the HTTP response
(the caller serves per its own API policy regardless), and never reveals whether
a task exists — it simply produces no consumption event. The task store reused is
the delegate task store as read/written by ``scripts.api.delegate_router`` (imported
lazily so non-API callers that only emit surface events pay nothing) — no third
store is created.

A public ``content_hash``/ETag alone is not proof of consumption: a caller who
merely *saw* a pointer (via ``/api/knowledge/manifest`` or the cold-start
projection) already knows the record's ETag and could replay it as
``If-None-Match`` to manufacture a `304` without ever fetching the body. A `200`
therefore persists minimal evidence (``{research_id: etag}``) into the same
validated task's state file; a `304` only counts as consumption when that
evidence already shows a matching prior `200` for the same record.

Payload allowlist (ADR-011 P3 privacy contract): exactly
``{task_id, research_id, surface, status}`` on top of the emitter's required
envelope. Never a digest body, title, summary, source URL, prompt, role,
task family, track, owned paths, or context fingerprint.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

try:  # package-path tolerant, mirrors emit.py's own import guard
    from scripts.telemetry.emit import emit_event
except ImportError:  # pragma: no cover - alternate import path
    from telemetry.emit import emit_event

# Event types (stable strings; consumers key on these).
CONSUMED_EVENT = "research_record_consumed"
SURFACED_EVENT = "research_pointer_surfaced"

# Task-attributed surfacing begins at dispatch, where a real task_id exists.
# Cold-start orient (``GET /api/orient?role=``) has no task in flight yet — there
# is nothing trustworthy to attribute a surface event to — so it never calls
# ``emit_surface``; only the dispatch path does. If a future surface gains a real
# task correlation, add its constant here rather than fabricating one now.
# "record" is reserved for consumption.
SURFACE_DISPATCH = "dispatch"
_CONSUMED_SURFACE = "record"

# Task-id validation: bounded length + a conservative safe shape. Slugs, agent
# prefixes, and dashed ids pass; traversal (``..``), whitespace, and control
# characters do not. The exact stored-id match below is the real authority — this
# only bounds work and rejects obviously hostile input before any file lookup.
MAX_TASK_ID_LEN = 128
_TASK_ID_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9._/-]{0,126}[A-Za-z0-9])?$")

# Only these derived states count as an active, attributable task. "spawning" and
# "running" are live; "zombie" (running status with a dead pid), "done", and every
# terminal state are rejected so a finished task cannot be spoofed for attribution.
_ACTIVE_STATES = frozenset({"spawning", "running"})


def _looks_like_task_id(task_id: str) -> bool:
    if not isinstance(task_id, str):
        return False
    if len(task_id) > MAX_TASK_ID_LEN:
        return False
    if ".." in task_id:
        return False
    return _TASK_ID_RE.fullmatch(task_id) is not None


def validate_active_task(task_id: str | None) -> str | None:
    """Return the task id iff it names a real, still-active delegate task.

    Fails closed to ``None`` for: absent/blank id, oversize/malformed id, an id
    whose sanitized state file is missing or corrupt, a stored ``task_id`` that
    does not match the request byte-for-byte (defeats collisions and path games),
    a task not in an active spawning/running state (defeats finished-task
    spoofing), or a spawning/running task with no live PID (defeats a state file
    that never got a real worker attached — the parent writes the Popen PID into
    the state file immediately after spawn, so a genuinely active task always has
    one; see ``_derived_task_status``). Never raises and never distinguishes "no
    such task" from "inactive task" to the caller — both simply return ``None``.
    """
    if not task_id or not _looks_like_task_id(task_id):
        return None
    try:
        # Lazy import: only the API record endpoint validates tasks; surface-only
        # emitters (delegate) never pull the API package in.
        from scripts.api.delegate_router import (
            _derived_task_status,
            _read_task_state,
            _task_state_path,
        )

        state = _read_task_state(_task_state_path(task_id))
        if not isinstance(state, dict):
            return None
        if state.get("task_id") != task_id:
            return None
        derived_status, alive = _derived_task_status(state)
        if derived_status not in _ACTIVE_STATES or not alive:
            return None
    except Exception:
        # Attribution is best-effort observability: any unexpected failure means
        # "no consumption event", never a broken record fetch.
        return None
    return task_id


def _allowlisted(payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {"task_id", "research_id", "surface", "status"}
    return {key: value for key, value in payload.items() if key in allowed and value is not None}


def emit_consumption(*, task_id: str, research_id: str, status: int) -> None:
    """Emit one consumption event for a validated active task. Best-effort."""
    emit_event(
        CONSUMED_EVENT,
        _allowlisted(
            {
                "task_id": task_id,
                "research_id": research_id,
                "surface": _CONSUMED_SURFACE,
                "status": status,
            }
        ),
    )


_EVIDENCE_FIELD = "research_consumption_evidence"


def _persist_200_evidence(task_id: str, research_id: str, etag: str) -> None:
    """Record ``{research_id: etag}`` in the task's own state file (best-effort).

    Reuses the existing delegate task-state JSON — no third store — via the same
    write-rename atomic pattern ``delegate.py`` already uses for that file. Never
    raises: a lost write under a concurrent worker update just means a later `304`
    for this record isn't attributable, which is the safe (fail-closed) direction.
    """
    try:
        from scripts.api.delegate_router import _read_task_state, _task_state_path

        path = _task_state_path(task_id)
        state = _read_task_state(path)
        if not isinstance(state, dict):
            return
        evidence = state.get(_EVIDENCE_FIELD)
        if not isinstance(evidence, dict):
            evidence = {}
        evidence[research_id] = etag
        state[_EVIDENCE_FIELD] = evidence
        tmp = path.with_suffix(f".json.tmp.{os.getpid()}")
        tmp.write_text(json.dumps(state, indent=2, default=str))
        os.replace(tmp, path)
    except Exception:
        pass


def _has_prior_200_evidence(task_id: str, research_id: str, etag: str) -> bool:
    """True iff this task's state already records a matching prior `200` fetch."""
    try:
        from scripts.api.delegate_router import _read_task_state, _task_state_path

        state = _read_task_state(_task_state_path(task_id))
        if not isinstance(state, dict):
            return False
        evidence = state.get(_EVIDENCE_FIELD)
        if not isinstance(evidence, dict):
            return False
        return evidence.get(research_id) == etag
    except Exception:
        return False


def record_consumption(task_id: str | None, research_id: str, *, status: int, etag: str) -> str | None:
    """Validate ``task_id`` then emit a consumption event; return the attributed id.

    The one call site the record endpoint needs: it validates, emits on success,
    and reports back the attributed task id (or ``None``) purely for logging/tests
    — the HTTP response must not branch on it and is computed before this call.

    A `200` always counts (the caller demonstrably received the body) and persists
    ``etag`` as evidence for this task/record. A `304` only counts when this same
    task already has matching `200` evidence for ``research_id`` — otherwise a
    caller could replay the record's publicly-visible ``content_hash`` as
    ``If-None-Match`` and manufacture a consumption event without ever fetching the
    body ("manufactured 304").
    """
    attributed = validate_active_task(task_id)
    if attributed is None:
        return None
    if status == 200:
        emit_consumption(task_id=attributed, research_id=research_id, status=200)
        _persist_200_evidence(attributed, research_id, etag)
        return attributed
    if status == 304:
        if not _has_prior_200_evidence(attributed, research_id, etag):
            return None
        emit_consumption(task_id=attributed, research_id=research_id, status=304)
        return attributed
    return None


def emit_surface(*, research_id: str, surface: str, task_id: str | None = None) -> None:
    """Emit one pointer-surfaced event (distinct from consumption). Best-effort.

    Surfacing does not require an active-task check — it records that a pointer was
    shown, not used. ``task_id`` is included only when the surface knows it
    (dispatch does; cold start does not).
    """
    emit_event(
        SURFACED_EVENT,
        _allowlisted(
            {
                "task_id": task_id,
                "research_id": research_id,
                "surface": surface,
            }
        ),
    )
