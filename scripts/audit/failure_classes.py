"""Shared failure-class records for build and audit gates."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class FailureClass(StrEnum):
    INFRA_CONTEXT_CONTAMINATION = "infra_context_contamination"
    MCP_TOOLS_NEVER_INVOKED = "mcp_tools_never_invoked"
    # Card 2 extends this enum with content/recovery failure classes.


@dataclass
class FailureRecord:
    failure_class: FailureClass
    sub_class: str | None
    gate: str
    severity: str  # "TERMINAL" | "HARD" | "WARN"
    recovery_action: str  # "none" | "atomic_fix" | "writer_correct" | "reviewer_fix"
    evidence: dict[str, Any]
    terminal: bool
