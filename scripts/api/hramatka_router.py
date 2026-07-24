"""Hramatka lesson-engine API boundary and local readiness checks.

The public repository owns the wire contract and the durable job lifecycle.
The private Hramatka service supplies authenticated job creation and the baker
which writes support sidecars.  Keeping those concerns separate prevents this
router from returning a lesson before the baker has completed every gate.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from jsonschema import Draft7Validator
from pydantic import BaseModel, Field, field_validator

from scripts.rag.config import VESUM_DB_PATH as DEFAULT_VESUM_DB_PATH
from scripts.verification import vesum

from .config import BATCH_STATE_DIR, PROJECT_ROOT
from .resilience import connect_sqlite

router = APIRouter(prefix="/api/hramatka", tags=["hramatka"])

HRAMATKA_STATE_DIR = Path(
    os.environ.get("HRAMATKA_STATE_DIR", str(BATCH_STATE_DIR / "hramatka"))
)
HRAMATKA_DB_PATH = Path(
    os.environ.get("HRAMATKA_DB_PATH", str(HRAMATKA_STATE_DIR / "lessons.sqlite3"))
)
SUPPORT_DIR = Path(
    os.environ.get("HRAMATKA_SUPPORT_DIR", str(HRAMATKA_STATE_DIR / "support"))
)
BAKER_STATE_PATH = Path(
    os.environ.get("HRAMATKA_BAKER_STATE_PATH", str(HRAMATKA_STATE_DIR / "baker-state.json"))
)
VESUM_DB_PATH = Path(os.environ.get("HRAMATKA_VESUM_DB_PATH", str(DEFAULT_VESUM_DB_PATH)))
SCHEMA_PATHS = (
    PROJECT_ROOT / "packages" / "activity-kit" / "src" / "lu.activity.v1.schema.json",
    PROJECT_ROOT / "packages" / "activity-kit" / "src" / "lu.lesson.v1.schema.json",
    PROJECT_ROOT / "packages" / "activity-kit" / "src" / "lu.lesson-support.v1.schema.json",
)
LESSON_SUPPORT_SCHEMA_PATH = SCHEMA_PATHS[-1]

MIGRATION_ID = "2026-07-24-hramatka-lessons-v1"
MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS hramatka_schema_migrations (
    migration_id TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hramatka_lesson_jobs (
    lesson_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('draft', 'queued', 'baking', 'ready', 'failed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

"""
MIGRATION_CHECKSUM = hashlib.sha256(MIGRATION_SQL.encode("utf-8")).hexdigest()


class LessonJobState(StrEnum):
    """Durable job states; ``queued`` is operational, not lesson JSON state."""

    DRAFT = "draft"
    QUEUED = "queued"
    BAKING = "baking"
    READY = "ready"
    FAILED = "failed"


_ALLOWED_TRANSITIONS: dict[LessonJobState, frozenset[LessonJobState]] = {
    LessonJobState.DRAFT: frozenset({LessonJobState.QUEUED, LessonJobState.BAKING}),
    LessonJobState.QUEUED: frozenset({LessonJobState.BAKING, LessonJobState.FAILED}),
    LessonJobState.BAKING: frozenset({LessonJobState.READY, LessonJobState.FAILED}),
    LessonJobState.READY: frozenset(),
    LessonJobState.FAILED: frozenset(),
}


@dataclass(frozen=True)
class LessonJob:
    lesson_id: str
    owner_id: str
    state: LessonJobState


class LessonTransitionError(ValueError):
    """Raised when a caller attempts to leave a terminal or invalid state."""


class LessonOwnershipError(ValueError):
    """Raised when a lesson id already belongs to another owner."""


class VerifyFormsRequest(BaseModel):
    forms: list[str] = Field(..., min_length=1, max_length=200)
    pos: str | None = Field(None, min_length=1, max_length=64)

    @field_validator("forms")
    @classmethod
    def forms_must_not_be_blank(cls, forms: list[str]) -> list[str]:
        normalized = [form.strip() for form in forms]
        if any(not form for form in normalized):
            raise ValueError("forms must not contain blank values")
        return normalized


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or HRAMATKA_DB_PATH
    return connect_sqlite(str(path), timeout=5.0, isolation_level=None)


def initialize_hramatka_store(db_path: Path | None = None) -> None:
    """Create the WAL-backed job store and record its immutable migration receipt."""
    path = db_path or HRAMATKA_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect(path)) as conn:
        conn.execute("PRAGMA busy_timeout=5000")
        journal_mode = str(conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower()
        if journal_mode != "wal":
            raise RuntimeError(f"Hramatka database did not enter WAL mode: {journal_mode}")
        conn.execute("PRAGMA foreign_keys=ON")
        # ``executescript`` commits any transaction already in progress, so put
        # the explicit transaction in its script rather than calling BEGIN first.
        conn.executescript(f"BEGIN IMMEDIATE;\n{MIGRATION_SQL}")
        try:
            receipt = conn.execute(
                "SELECT checksum FROM hramatka_schema_migrations WHERE migration_id = ?",
                (MIGRATION_ID,),
            ).fetchone()
            if receipt is None:
                conn.execute(
                    "INSERT INTO hramatka_schema_migrations (migration_id, checksum) VALUES (?, ?)",
                    (MIGRATION_ID, MIGRATION_CHECKSUM),
                )
            elif receipt[0] != MIGRATION_CHECKSUM:
                raise RuntimeError("Hramatka migration checksum mismatch")
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def transition_lesson_state(current: LessonJobState, target: LessonJobState) -> LessonJobState:
    """Validate and return one legal lifecycle transition."""
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise LessonTransitionError(f"cannot transition lesson from {current} to {target}")
    return target


def create_lesson_job(
    lesson_id: UUID | str,
    owner_id: str,
    state: LessonJobState = LessonJobState.DRAFT,
    *,
    db_path: Path | None = None,
) -> LessonJob:
    """Create an idempotent UUID-addressed job, preserving its owner on retry."""
    parsed_id = str(UUID(str(lesson_id)))
    if not owner_id.strip():
        raise ValueError("owner_id must not be blank")
    if state not in {LessonJobState.DRAFT, LessonJobState.QUEUED}:
        raise ValueError("new lesson jobs must start in draft or queued")

    initialize_hramatka_store(db_path)
    with closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT lesson_id, owner_id, state FROM hramatka_lesson_jobs WHERE lesson_id = ?",
            (parsed_id,),
        ).fetchone()
        if row is not None:
            if row[1] != owner_id:
                raise LessonOwnershipError("lesson id belongs to another owner")
            return LessonJob(row[0], row[1], LessonJobState(row[2]))
        conn.execute(
            "INSERT INTO hramatka_lesson_jobs (lesson_id, owner_id, state) VALUES (?, ?, ?)",
            (parsed_id, owner_id, state.value),
        )
        conn.commit()
    return LessonJob(parsed_id, owner_id, state)


def get_lesson_job(lesson_id: UUID | str, *, db_path: Path | None = None) -> LessonJob | None:
    """Return the persisted job without creating or repairing storage."""
    parsed_id = str(UUID(str(lesson_id)))
    with closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT lesson_id, owner_id, state FROM hramatka_lesson_jobs WHERE lesson_id = ?",
            (parsed_id,),
        ).fetchone()
    if row is None:
        return None
    return LessonJob(row[0], row[1], LessonJobState(row[2]))


def transition_lesson_job(
    lesson_id: UUID | str,
    target: LessonJobState,
    *,
    db_path: Path | None = None,
) -> LessonJob:
    """Atomically persist a legal job state transition."""
    parsed_id = str(UUID(str(lesson_id)))
    with closing(_connect(db_path)) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute(
                "SELECT lesson_id, owner_id, state FROM hramatka_lesson_jobs WHERE lesson_id = ?",
                (parsed_id,),
            ).fetchone()
            if row is None:
                raise KeyError(parsed_id)
            current = LessonJobState(row[2])
            transition_lesson_state(current, target)
            conn.execute(
                "UPDATE hramatka_lesson_jobs SET state = ?, updated_at = CURRENT_TIMESTAMP WHERE lesson_id = ?",
                (target.value, parsed_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return LessonJob(parsed_id, row[1], target)


def _load_support_schema() -> dict[str, Any]:
    return json.loads(LESSON_SUPPORT_SCHEMA_PATH.read_text(encoding="utf-8"))


def _support_path(lesson_id: UUID) -> Path:
    return SUPPORT_DIR / f"{lesson_id}.json"


@router.get("/lessons/{lesson_id}/support")
def lesson_support(lesson_id: UUID, x_hramatka_owner: str = Header(...)) -> dict[str, Any]:
    """Return a schema-valid sidecar only after the corresponding job is ready."""
    try:
        job = get_lesson_job(lesson_id)
    except (sqlite3.Error, OSError) as exc:
        raise HTTPException(status_code=503, detail="lesson store unavailable") from exc
    if job is None or job.owner_id != x_hramatka_owner:
        raise HTTPException(status_code=404, detail="lesson not found")
    if job.state is not LessonJobState.READY:
        raise HTTPException(status_code=409, detail="lesson is not ready")

    try:
        sidecar = json.loads(_support_path(lesson_id).read_text(encoding="utf-8"))
        errors = list(Draft7Validator(_load_support_schema()).iter_errors(sidecar))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail="lesson support unavailable") from exc
    if errors:
        raise HTTPException(status_code=503, detail="lesson support failed schema validation")
    return sidecar


@router.post("/linguistics/verify")
def verify_linguistics(payload: VerifyFormsRequest) -> dict[str, Any]:
    """Batch-attest up to 200 Ukrainian forms using the loaded VESUM dictionary."""
    try:
        attestations = vesum.verify_words(payload.forms, pos_filter=payload.pos, db_path=VESUM_DB_PATH)
    except (FileNotFoundError, OSError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503, detail="VESUM dictionary unavailable") from exc
    results = [
        {"form": form, "attested": bool(attestations[form]), "matches": attestations[form]}
        for form in payload.forms
    ]
    return {
        "results": results,
        "total": len(results),
        "attested_count": sum(1 for result in results if result["attested"]),
    }


def _check_database() -> tuple[bool, str]:
    try:
        with closing(_connect()) as conn:
            journal_mode = str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower()
            if journal_mode != "wal":
                return False, f"journal mode is {journal_mode}, expected wal"
            # BEGIN IMMEDIATE obtains SQLite's write reservation without
            # committing a synthetic probe row on every readiness poll.
            conn.execute("BEGIN IMMEDIATE")
            conn.rollback()
        return True, "SQLite WAL database accepted a write reservation"
    except (sqlite3.Error, OSError) as exc:
        logger.warning("database probe failed: %s", exc)
        return False, "database probe failed"


def _check_migrations() -> tuple[bool, str]:
    try:
        with closing(_connect()) as conn:
            row = conn.execute(
                "SELECT checksum FROM hramatka_schema_migrations WHERE migration_id = ?",
                (MIGRATION_ID,),
            ).fetchone()
    except (sqlite3.Error, OSError) as exc:
        logger.warning("migration check failed: %s", exc)
        return False, "migration check failed"
    if row is None:
        return False, "required Hramatka migration is not applied"
    if row[0] != MIGRATION_CHECKSUM:
        return False, "Hramatka migration checksum mismatch"
    return True, "required Hramatka migration is applied"


def _check_baker() -> tuple[bool, str]:
    try:
        state = json.loads(BAKER_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("baker state check failed: %s", exc)
        return False, "baker state file unreadable or invalid"
    if state.get("state") != "active":
        return False, "baker state is not active"
    return True, "baker state is active"


def _check_schemas() -> tuple[bool, str]:
    try:
        for schema_path in SCHEMA_PATHS:
            Draft7Validator.check_schema(json.loads(schema_path.read_text(encoding="utf-8")))
    except Exception as exc:  # jsonschema has several schema-specific exception classes.
        logger.warning("schema check failed: %s", exc)
        return False, "schema validation failed"
    return True, f"{len(SCHEMA_PATHS)} JSON schemas are valid"


def _check_vesum() -> tuple[bool, str]:
    try:
        conn = vesum.get_vesum_conn(VESUM_DB_PATH)
        count = int(conn.execute("SELECT COUNT(*) FROM forms").fetchone()[0])
    except (FileNotFoundError, OSError, sqlite3.Error) as exc:
        logger.warning("vesum check failed: %s", exc)
        return False, "vesum dictionary unreadable or invalid"
    if count < 1:
        return False, "VESUM dictionary has no forms"
    return True, f"VESUM dictionary loaded with {count} forms"


@router.get("/readyz")
def readiness() -> JSONResponse:
    """Report whether every prerequisite for safely serving lessons is active."""
    checks = {
        "database": _check_database(),
        "migrations": _check_migrations(),
        "baker": _check_baker(),
        "schemas": _check_schemas(),
        "vesum": _check_vesum(),
    }
    serialized_checks = {
        name: {"ok": ok, "detail": detail} for name, (ok, detail) in checks.items()
    }
    is_ready = all(check["ok"] for check in serialized_checks.values())
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={"ready": is_ready, "checks": serialized_checks},
    )
