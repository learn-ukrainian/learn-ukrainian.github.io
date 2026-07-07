"""Deterministic probe for initial-response failover rotation.

The probe installs an in-process fake adapter, points runner failover at a
throwaway config/cooldown DB, and spawns real subprocesses:

- ``no-first-byte``: primary route emits no output and sleeps; the initial
  response timeout should cool it and rotate to the fallback route.
- ``streaming-silence``: primary route emits one line, then sleeps; this is a
  mid-stream silence timeout and must not rotate.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
SCRIPTS_DIR = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_runtime import runner as runner_mod
from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.errors import AgentStalledError
from agent_runtime.failover import FAILOVER_CONFIG_ENV, FAILOVER_COOLDOWN_DB_ENV
from agent_runtime.result import ParseResult
from agent_runtime.routes import RUNTIME_ROUTE_TOOL_CONFIG_KEY
from agent_runtime.telemetry import InvocationTelemetry

PROBE_AGENT = "stall-probe"
PRIMARY_MODEL = "primary-stall"
FALLBACK_MODEL = "fallback-ok"
PRIMARY_PROVIDER = "primary-provider"
FALLBACK_PROVIDER = "fallback-provider"
SUCCESS_TEXT = "stall failover ok"


class ProbeError(RuntimeError):
    """Expected probe/configuration failure."""


@dataclass
class _ProbeAdapter:
    """Small fake adapter that turns failover routes into subprocess shapes."""

    case: str
    attempts: list[str] = field(default_factory=list)

    name = PROBE_AGENT
    default_model = PRIMARY_MODEL
    supported_modes = frozenset({"read-only"})

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str | None,
        session_id: str | None,
        tool_config: dict | None,
        effort: str | None = None,
    ) -> InvocationPlan:
        _ = prompt
        _ = mode
        _ = task_id
        _ = session_id
        _ = effort
        route = dict((tool_config or {}).get(RUNTIME_ROUTE_TOOL_CONFIG_KEY) or {})
        route_model = str(route.get("model") or model or self.default_model)
        self.attempts.append(route_model)
        if route_model == FALLBACK_MODEL:
            shell = f"printf '%s\\n' {SUCCESS_TEXT!r}"
        elif self.case == "streaming-silence":
            shell = "printf '%s\\n' 'partial output'; sleep 60"
        else:
            shell = "sleep 60"
        return InvocationPlan(
            cmd=["/bin/sh", "-c", shell],
            cwd=cwd,
            metadata={"route_model": route_model},
        )

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None,
        plan: InvocationPlan | None = None,
        call_start_time: float | None = None,
    ) -> ParseResult:
        _ = stderr
        _ = returncode
        _ = output_file
        _ = plan
        _ = call_start_time
        if SUCCESS_TEXT in stdout:
            return ParseResult(ok=True, response=stdout.strip(), stderr_excerpt=None)
        return ParseResult(ok=False, response="", stderr_excerpt=None)

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        _ = plan
        return ()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Probe runner-level failover behavior for no-first-byte stalls "
            "using an isolated failover config and cooldown DB."
        )
    )
    parser.add_argument(
        "--case",
        choices=("no-first-byte", "streaming-silence"),
        default="no-first-byte",
        help="Probe case to run. Default: no-first-byte.",
    )
    parser.add_argument(
        "--cooldown-db",
        type=Path,
        help="Throwaway SQLite cooldown DB path. Defaults to a temp directory.",
    )
    parser.add_argument(
        "--initial-response-timeout",
        type=int,
        default=1,
        help="Initial response timeout seconds. Default: 1.",
    )
    parser.add_argument(
        "--stdout-silence-timeout",
        type=int,
        default=1,
        help="Composite silence timeout seconds for streaming-silence. Default: 1.",
    )
    parser.add_argument(
        "--hard-timeout",
        type=int,
        default=30,
        help="Hard timeout seconds. Default: 30.",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        default=REPO_ROOT,
        help="Working directory for probe subprocesses. Default: repo root.",
    )
    return parser


def _write_probe_config(path: Path) -> Path:
    config_path = path / "agent_runtime_failover.yaml"
    config_path.write_text(
        "\n".join(
            [
                "chains:",
                f"  {PROBE_AGENT}:",
                "    cooldown_ttl_s: 60",
                "    routes:",
                f"      - provider: {PRIMARY_PROVIDER}",
                f"        model: {PRIMARY_MODEL}",
                f"      - provider: {FALLBACK_PROVIDER}",
                f"        model: {FALLBACK_MODEL}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def _patch_runtime(adapter: _ProbeAdapter, events: list[dict[str, Any]]) -> None:
    def fake_has_headroom(_agent: str, _model: str) -> tuple[bool, str]:
        return True, ""

    def fake_write_record(record: dict[str, Any]) -> None:
        events.append({"event_name": "usage_record", **record})

    def fake_resolve_invocation_telemetry(**_kwargs: Any) -> InvocationTelemetry:
        return InvocationTelemetry(
            model=adapter.attempts[-1] if adapter.attempts else PRIMARY_MODEL,
            effort="unknown",
            cli_version="probe",
        )

    runner_mod._ADAPTER_CACHE[PROBE_AGENT] = adapter
    runner_mod.has_headroom = fake_has_headroom
    runner_mod.write_record = fake_write_record
    runner_mod.resolve_invocation_telemetry = fake_resolve_invocation_telemetry


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    temp_dir = tempfile.TemporaryDirectory(prefix="agent-runtime-stall-probe-")
    root = Path(temp_dir.name)
    if args.cooldown_db is None:
        cooldown_db = root / "cooldowns.sqlite3"
    else:
        cooldown_db = args.cooldown_db.expanduser().resolve()
        cooldown_db.parent.mkdir(parents=True, exist_ok=True)
        if cooldown_db.exists():
            temp_dir.cleanup()
            raise ProbeError(
                f"cooldown DB already exists; pass an isolated path: {cooldown_db}"
            )

    old_config = os.environ.get(FAILOVER_CONFIG_ENV)
    old_cooldown = os.environ.get(FAILOVER_COOLDOWN_DB_ENV)
    old_cache_entry = runner_mod._ADAPTER_CACHE.get(PROBE_AGENT)
    old_has_headroom = runner_mod.has_headroom
    old_write_record = runner_mod.write_record
    old_resolve_invocation_telemetry = runner_mod.resolve_invocation_telemetry
    events: list[dict[str, Any]] = []
    adapter = _ProbeAdapter(case=args.case)

    try:
        config_path = _write_probe_config(root)
        os.environ[FAILOVER_CONFIG_ENV] = str(config_path)
        os.environ[FAILOVER_COOLDOWN_DB_ENV] = str(cooldown_db)
        _patch_runtime(adapter, events)

        def event_sink(event_name: str, **fields: Any) -> None:
            events.append({"event_name": event_name, **fields})

        if args.case == "streaming-silence":
            try:
                runner_mod.invoke(
                    PROBE_AGENT,
                    "probe",
                    mode="read-only",
                    cwd=args.cwd.expanduser().resolve(),
                    task_id="stall-failover-probe-streaming-silence",
                    entrypoint="runtime",
                    hard_timeout=args.hard_timeout,
                    initial_response_timeout=args.initial_response_timeout,
                    stdout_silence_timeout=args.stdout_silence_timeout,
                    event_sink=event_sink,
                )
            except AgentStalledError as exc:
                if exc.kind != "stdout_silence_timeout":
                    raise ProbeError(
                        f"expected stdout_silence_timeout, got {exc.kind!r}"
                    ) from exc
                usage_substitution = [
                    event.get("substitution")
                    for event in events
                    if event.get("event_name") == "usage_record"
                    and isinstance(event.get("substitution"), dict)
                ]
                if usage_substitution:
                    raise ProbeError(
                        "streaming-silence unexpectedly persisted substitution"
                    ) from exc
                if adapter.attempts != [PRIMARY_MODEL]:
                    raise ProbeError(
                        f"streaming-silence rotated unexpectedly: {adapter.attempts!r}"
                    ) from exc
                return {
                    "ok": True,
                    "case": args.case,
                    "attempts": adapter.attempts,
                    "cooldown_db": str(cooldown_db),
                    "rotated": False,
                    "stalled_kind": exc.kind,
                }
            raise ProbeError("streaming-silence did not raise AgentStalledError")

        result = runner_mod.invoke(
            PROBE_AGENT,
            "probe",
            mode="read-only",
            cwd=args.cwd.expanduser().resolve(),
            task_id="stall-failover-probe-no-first-byte",
            entrypoint="runtime",
            hard_timeout=args.hard_timeout,
            initial_response_timeout=args.initial_response_timeout,
            stdout_silence_timeout=None,
            event_sink=event_sink,
        )
        substitution = result.substitution
        if not isinstance(substitution, dict) or not substitution.get("substituted"):
            raise ProbeError(f"missing failover substitution: {substitution!r}")
        if substitution.get("source") != "agent-runtime-failover:transport":
            raise ProbeError(f"unexpected substitution source: {substitution!r}")
        usage_records = [
            event for event in events if event.get("event_name") == "usage_record"
        ]
        if not usage_records or not isinstance(
            usage_records[-1].get("substitution"), dict
        ):
            raise ProbeError("usage record did not persist substitution")
        usage_substitution = usage_records[-1]["substitution"]
        if adapter.attempts != [PRIMARY_MODEL, FALLBACK_MODEL]:
            raise ProbeError(f"unexpected route attempts: {adapter.attempts!r}")
        return {
            "ok": True,
            "case": args.case,
            "attempts": adapter.attempts,
            "cooldown_db": str(cooldown_db),
            "response": result.response,
            "rotated": True,
            "substitution": substitution,
            "usage_substitution": usage_substitution,
            "usage_record_surfaced": True,
        }
    finally:
        if old_config is None:
            os.environ.pop(FAILOVER_CONFIG_ENV, None)
        else:
            os.environ[FAILOVER_CONFIG_ENV] = old_config
        if old_cooldown is None:
            os.environ.pop(FAILOVER_COOLDOWN_DB_ENV, None)
        else:
            os.environ[FAILOVER_COOLDOWN_DB_ENV] = old_cooldown
        if old_cache_entry is None:
            runner_mod._ADAPTER_CACHE.pop(PROBE_AGENT, None)
        else:
            runner_mod._ADAPTER_CACHE[PROBE_AGENT] = old_cache_entry
        runner_mod.has_headroom = old_has_headroom
        runner_mod.write_record = old_write_record
        runner_mod.resolve_invocation_telemetry = old_resolve_invocation_telemetry
        temp_dir.cleanup()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = run_probe(args)
    except ProbeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(
            f"ERROR: unexpected probe failure: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
