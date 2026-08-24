"""Pydantic models for fleet worker rows (monitor-project-state.v2)."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

WORKER_KINDS = frozenset({"driver", "delegate", "observer", "job", "service"})
WORKER_STATES = frozenset({"live", "starting", "zombie", "needs_attention"})
SEAT_MODELS = frozenset({"single", "multi"})
WORKER_SOURCES = frozenset({"driver", "delegate", "observer", "job", "marker", "project_state"})
MAX_WORKERS_PER_REPORT = 200

_AGENT_RE = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")
_RUN_ID_RE = re.compile(r"^[0-9a-f]{8}$")
_EPIC_RE = re.compile(r"^epic:[1-9][0-9]{0,6}$")

WorkerKind = Literal["driver", "delegate", "observer", "job", "service"]
WorkerState = Literal["live", "starting", "zombie", "needs_attention"]
SeatModel = Literal["single", "multi"]


class WorkerRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: WorkerKind
    agent: str
    harness: str | None = None
    id: str
    run_id: str | None = None
    epic: str | None = None
    state: WorkerState
    age_s: int = Field(ge=0, le=604_800)
    seat_model: SeatModel | None = None

    @field_validator("agent", "harness", mode="before")
    @classmethod
    def _validate_agentish(cls, value: object) -> object:
        if value is None:
            return None
        text = str(value).strip()
        if not _AGENT_RE.fullmatch(text):
            raise ValueError("invalid agent token")
        return text

    @field_validator("id", mode="before")
    @classmethod
    def _validate_id(cls, value: object) -> str:
        text = str(value).strip()
        if not _ID_RE.fullmatch(text):
            raise ValueError("invalid id")
        return text

    @field_validator("run_id", mode="before")
    @classmethod
    def _validate_run_id(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not _RUN_ID_RE.fullmatch(text):
            raise ValueError("invalid run_id")
        return text

    @field_validator("epic", mode="before")
    @classmethod
    def _validate_epic(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not _EPIC_RE.fullmatch(text):
            raise ValueError("invalid epic")
        return text

    @field_validator("seat_model", mode="before")
    @classmethod
    def _validate_seat_model(cls, value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if text not in SEAT_MODELS:
            raise ValueError("invalid seat_model")
        return text


def worker_row_dict(row: WorkerRow) -> dict[str, object]:
    return row.model_dump(mode="json")
