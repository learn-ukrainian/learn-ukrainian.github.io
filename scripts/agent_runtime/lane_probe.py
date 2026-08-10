"""No-cost dispatch-lane self-test.

The probe exercises the same adapter selection and invocation construction as
``delegate.py``, then runs only the resolved CLI's ``--version`` command.  It
does not submit a prompt, create a delegate task, or make a provider request.

It is intentionally useful both as an operator diagnostic and from
SessionStart, where a single active lane can be checked inside the bounded
startup budget.  See #4879.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .registry import AGENTS, get_agent_entry

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
# Several legacy adapters retain top-level imports such as ``ai_llm`` and
# ``ai_agent_bridge``. Delegate adds this same source root before loading them;
# SessionStart runs this probe as ``scripts.agent_runtime`` and needs the
# compatibility import root too.
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_PROBE_PROMPT = "Dispatch adapter health probe; do not execute this prompt."
_DEFAULT_TIMEOUT_SECONDS = 3
_MAX_TIMEOUT_SECONDS = 30


def _mode_for_probe(adapter: Any) -> str:
    """Choose a supported mode without executing an agent request."""
    supported = getattr(adapter, "supported_modes", frozenset())
    if "read-only" in supported and getattr(adapter, "name", "") != "kimi":
        return "read-only"
    if "workspace-write" in supported:
        return "workspace-write"
    if "danger" in supported:
        return "danger"
    raise ValueError("adapter declares no supported invocation mode")


def _load_adapter(agent: str) -> Any:
    """Load the registered adapter without importing the full task runner.

    SessionStart imports this module as ``scripts.agent_runtime.lane_probe``.
    The normal runner also supports legacy ``agent_runtime`` top-level imports,
    but loading it here would make a binary-only health check depend on the
    runner's optional bridge-only imports.
    """
    entry = get_agent_entry(agent)
    module_name, class_name = entry["adapter"].split(":", 1)
    adapter_class = getattr(importlib.import_module(module_name), class_name)
    return adapter_class()


def _version_command(invocation: list[str]) -> list[str]:
    """Reduce an adapter command to its zero-cost CLI version invocation.

    Most adapters start with their executable.  Claude's retained fallback is
    ``npx <package>``, whose package token is part of the executable prefix;
    keeping it is essential for catching another broken npm shim rather than
    merely proving Node itself is installed.
    """
    if not invocation or not isinstance(invocation[0], str) or not invocation[0]:
        raise ValueError("adapter produced no executable command")
    executable = Path(invocation[0]).name.lower()
    if executable in {"npx", "npx.cmd"}:
        if len(invocation) < 2 or not isinstance(invocation[1], str) or not invocation[1]:
            raise ValueError("npx adapter command omitted its package")
        return [invocation[0], invocation[1], "--version"]
    return [invocation[0], "--version"]


def _probe_environment(plan: Any) -> dict[str, str]:
    """Apply the plan's child-only environment exactly as the runner would."""
    environment = os.environ.copy()
    for key in getattr(plan, "env_unsets", ()):
        environment.pop(key, None)
    environment.update(getattr(plan, "env_overrides", {}))
    return environment


def _cleanup_probe_output(plan: Any | None) -> None:
    """Remove the Codex output file created solely by this synthetic plan."""
    output_file = getattr(plan, "output_file", None)
    if not isinstance(output_file, Path) or not output_file.name.startswith("codex-runtime-lane-health-probe-"):
        return
    try:
        temp_root = Path(tempfile.gettempdir()).resolve()
        if output_file.resolve().is_relative_to(temp_root):
            output_file.unlink(missing_ok=True)
    except OSError:
        # Cleanup is best-effort. A failed probe must still report its real
        # adapter/binary verdict rather than turn into a false healthy signal.
        return


def probe_lane(agent: str, *, cwd: Path, timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Return one machine-readable health result for a runtime lane."""
    started = time.monotonic()
    result: dict[str, Any] = {"agent": agent, "status": "unhealthy"}
    try:
        entry = get_agent_entry(agent)
    except KeyError:
        result["reason"] = "agent is not registered"
        result["duration_ms"] = round((time.monotonic() - started) * 1000)
        return result

    if not entry["cli_available"]:
        result.update({"status": "skipped", "reason": "lane is disabled in the runtime registry"})
        result["duration_ms"] = round((time.monotonic() - started) * 1000)
        return result

    plan: Any | None = None
    try:
        adapter = _load_adapter(agent)
        mode = _mode_for_probe(adapter)
        plan = adapter.build_invocation(
            prompt=_PROBE_PROMPT,
            mode=mode,
            cwd=cwd,
            model=None,
            task_id="lane-health-probe",
            session_id=None,
            tool_config=None,
        )
        command = _version_command(plan.cmd)
        completed = subprocess.run(
            command,
            cwd=plan.cwd,
            env=_probe_environment(plan),
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        result["reason"] = f"version command exceeded {timeout_seconds}s"
    except Exception as exc:
        result["reason"] = f"{type(exc).__name__} while building or spawning the adapter"
    else:
        if completed.returncode == 0:
            result["status"] = "healthy"
        else:
            result["reason"] = f"version command exited {completed.returncode}"
    finally:
        _cleanup_probe_output(plan)
        result["duration_ms"] = round((time.monotonic() - started) * 1000)
    return result


def probe_lanes(agents: list[str], *, cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    """Probe the requested lanes and return a stable JSON document."""
    results = [probe_lane(agent, cwd=cwd, timeout_seconds=timeout_seconds) for agent in agents]
    return {
        "schema_version": "agent_runtime_lane_probe.v1",
        "probes": results,
        "summary": {
            "healthy": sum(result["status"] == "healthy" for result in results),
            "unhealthy": sum(result["status"] == "unhealthy" for result in results),
            "skipped": sum(result["status"] == "skipped" for result in results),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--agent", help="One registered runtime lane to probe")
    selection.add_argument("--all", action="store_true", help="Probe every runtime registry lane")
    parser.add_argument(
        "--cwd",
        type=Path,
        default=Path.cwd(),
        help="Directory passed to adapter build_invocation (default: current directory)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=_DEFAULT_TIMEOUT_SECONDS,
        help=f"Per-version-command timeout in seconds (1-{_MAX_TIMEOUT_SECONDS}; default: {_DEFAULT_TIMEOUT_SECONDS})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.cwd.is_dir():
        print(f"error: --cwd is not a directory: {args.cwd}", file=sys.stderr)
        return 2
    if not 1 <= args.timeout <= _MAX_TIMEOUT_SECONDS:
        print(f"error: --timeout must be between 1 and {_MAX_TIMEOUT_SECONDS}", file=sys.stderr)
        return 2

    agents = list(AGENTS) if args.all else [args.agent]
    payload = probe_lanes(agents, cwd=args.cwd.resolve(), timeout_seconds=args.timeout)
    json.dump(payload, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 1 if payload["summary"]["unhealthy"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
