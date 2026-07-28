"""Three-tool MCP surface for weak TrailSpec drivers.

This server never offers a shell or a generic command tool.  Every request is
translated to one of the P3 ``trail_runner.py`` verbs, which remains the sole
owner of SQLite state and command execution.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRAIL_RUNNER = PROJECT_ROOT / "scripts" / "orchestration" / "trail_runner.py"
PYTHON_BIN = PROJECT_ROOT / ".venv" / "bin" / "python"
_RUNNER_TIMEOUT_SECONDS = 90

mcp = FastMCP(
    "trail",
    instructions=(
        "Weak drivers may only inspect a pinned trail, advance its exact current step, "
        "or inspect runner-created summons. The parent-owned TrailSpec runner executes commands."
    ),
)


class TrailMcpError(RuntimeError):
    """Raised when the parent-owned P3 runner did not return its JSON contract."""


def _require_identifier(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TrailMcpError(f"{field} must be a non-empty string")
    return value.strip()


def _run_runner(*args: str) -> dict[str, Any]:
    """Call one fixed P3 runner verb and preserve its JSON result verbatim."""
    if not PYTHON_BIN.is_file() or not TRAIL_RUNNER.is_file():
        raise TrailMcpError("parent-owned TrailSpec runner is unavailable")
    completed = subprocess.run(
        [str(PYTHON_BIN), str(TRAIL_RUNNER), *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        check=False,
        text=True,
        timeout=_RUNNER_TIMEOUT_SECONDS,
    )
    try:
        payload = json.loads((completed.stdout or "").strip())
    except json.JSONDecodeError as exc:
        raise TrailMcpError("parent-owned TrailSpec runner emitted invalid JSON") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "trail-run-result.v1":
        raise TrailMcpError("parent-owned TrailSpec runner violated its result contract")
    if payload.get("exit_class") != completed.returncode:
        raise TrailMcpError("parent-owned TrailSpec runner exit class does not match its result")
    return payload


@mcp.tool(name="trail_status", description="Read the SQLite-authoritative status of one TrailSpec run.")
def trail_status(run_id: str) -> dict[str, Any]:
    """Return the current cursor, state, and runner-created summons for ``run_id``."""
    return _run_runner("status", "--run-id", _require_identifier(run_id, field="run_id"))


@mcp.tool(name="trail_step", description="Ask the parent runner to execute the exact current TrailSpec step.")
def trail_step(run_id: str, expected_step: str) -> dict[str, Any]:
    """Advance only an exact cursor; P3 refuses skipped or invented steps."""
    return _run_runner(
        "step",
        "--run-id",
        _require_identifier(run_id, field="run_id"),
        "--expected-step",
        _require_identifier(expected_step, field="expected_step"),
    )


@mcp.tool(name="trail_summon", description="Read summons atomically created by the parent TrailSpec runner.")
def trail_summon(run_id: str) -> dict[str, Any]:
    """Return P3-created escalation records without granting a new mutation verb.

    P3 inserts a summon atomically when a step parks.  This tool therefore
    deliberately maps to ``status`` rather than creating an unbound local
    escalation or exposing P4's authority-resume mechanism.
    """
    return _run_runner("status", "--run-id", _require_identifier(run_id, field="run_id"))


def main() -> None:
    """Serve the fixed three-tool MCP contract over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
