"""Forced-failure probe for Hermes fallback substitution surfacing."""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
SCRIPTS_DIR = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[2]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from agent_runtime.runner import invoke

DEFAULT_MODELS = {
    "deepseek": "deepseek-v4-pro",
    "grok": "grok-4.5",
    "qwen": "qwen/qwen3.6-plus",
}


class ProbeError(RuntimeError):
    """Expected probe/configuration failure."""


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run a trivial Hermes-backed agent invocation against an isolated "
            "HERMES_HOME and assert that configured fallback substitution is "
            "surfaced in runtime result, usage telemetry, and event telemetry."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  .venv/bin/python scripts/agent_runtime/probe_fallback.py \\
    --hermes-home /tmp/hermes-fallback-probe \\
    --agent deepseek \\
    --expected-fallback-provider openrouter \\
    --expected-fallback-model deepseek/deepseek-v3.2

Outputs:
  Prints one JSON object with ok=true, the non-secret substitution payload,
  and booleans for runtime/result/telemetry surfacing. It never prints
  Hermes config contents, API keys, or environment values.

Exit codes:
  0  probe succeeded
  1  unexpected runtime error
  2  probe assertion or isolated-config validation failed

Related docs:
  docs/references/private/hermes-usage.md § Automation adoption plan
  (gitignored machine-local doc; tracked stub: docs/best-practices/hermes-usage.md)
""",
    )
    parser.add_argument(
        "--hermes-home",
        required=True,
        type=Path,
        help=(
            "Isolated Hermes home containing config.yaml with a deliberately "
            "broken primary route and fallback_providers. Refuses ~/.hermes."
        ),
    )
    parser.add_argument(
        "--agent",
        choices=sorted(DEFAULT_MODELS),
        default="deepseek",
        help="Hermes-backed runtime agent to invoke. Default: deepseek.",
    )
    parser.add_argument(
        "--model",
        help="Requested primary model. Defaults to the selected agent's runtime default.",
    )
    parser.add_argument(
        "--expected-fallback-provider",
        required=True,
        help="Provider expected after Hermes fallback, for example openrouter.",
    )
    parser.add_argument(
        "--expected-fallback-model",
        required=True,
        help="Model expected after Hermes fallback.",
    )
    parser.add_argument(
        "--prompt",
        default="Reply with exactly: fallback probe ok",
        help="Trivial prompt for the probe. Do not include secrets.",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        default=REPO_ROOT,
        help="Working directory for the runtime invocation. Default: repo root.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Hard timeout in seconds. Default: 180.",
    )
    return parser


def _validate_isolated_hermes_home(hermes_home: Path) -> Path:
    home = hermes_home.expanduser().resolve()
    live_home = (Path.home() / ".hermes").resolve()
    if home == live_home:
        raise ProbeError(
            "Refusing to probe against live ~/.hermes. Pass a temporary "
            "--hermes-home with its own config.yaml."
        )
    if not (home / "config.yaml").is_file():
        raise ProbeError(f"Missing isolated Hermes config: {home / 'config.yaml'}")
    return home


def _substitution_from_result(result: Any) -> dict[str, Any] | None:
    substitution = getattr(result, "substitution", None)
    if isinstance(substitution, dict):
        return substitution
    usage_record = getattr(result, "usage_record", None)
    if isinstance(usage_record, dict) and isinstance(
        usage_record.get("substitution"),
        dict,
    ):
        return usage_record["substitution"]
    return None


def run_probe(
    args: argparse.Namespace,
    *,
    invoke_fn: Callable[..., Any] = invoke,
) -> dict[str, Any]:
    """Run the fallback probe and return a non-secret summary."""
    hermes_home = _validate_isolated_hermes_home(args.hermes_home)
    requested_model = args.model or DEFAULT_MODELS[args.agent]
    events: list[dict[str, Any]] = []

    def event_sink(event_name: str, **fields: Any) -> None:
        events.append({"event_name": event_name, **fields})

    result = invoke_fn(
        args.agent,
        args.prompt,
        mode="read-only",
        cwd=args.cwd.expanduser().resolve(),
        model=requested_model,
        task_id=f"hermes-fallback-probe-{args.agent}",
        tool_config={"hermes_home": str(hermes_home)},
        entrypoint="runtime",
        hard_timeout=args.timeout,
        event_sink=event_sink,
    )
    substitution = _substitution_from_result(result)
    if not substitution:
        raise ProbeError("Runtime result did not include a substitution field.")
    if not substitution.get("substituted"):
        raise ProbeError(f"Hermes did not report fallback substitution: {substitution!r}")

    actual_provider = str(substitution.get("actual_provider") or "")
    actual_model = str(substitution.get("actual_model") or "")
    expected_provider = str(args.expected_fallback_provider)
    expected_model = str(args.expected_fallback_model)
    if actual_provider.lower() != expected_provider.lower():
        raise ProbeError(
            "Fallback provider mismatch: "
            f"expected {expected_provider!r}, got {actual_provider!r}"
        )
    if actual_model != expected_model:
        raise ProbeError(
            "Fallback model mismatch: "
            f"expected {expected_model!r}, got {actual_model!r}"
        )

    usage_record = getattr(result, "usage_record", None)
    usage_substitution = (
        usage_record.get("substitution")
        if isinstance(usage_record, dict)
        else None
    )
    if not isinstance(usage_substitution, dict) or not usage_substitution.get(
        "substituted"
    ):
        raise ProbeError("Usage record did not persist the substitution field.")

    telemetry_event_seen = any(
        event.get("event_name") == "agent_runtime_substitution"
        and isinstance(event.get("substitution"), dict)
        and event["substitution"].get("substituted")
        for event in events
    )
    if not telemetry_event_seen:
        raise ProbeError("Substitution telemetry event was not emitted.")

    return {
        "ok": True,
        "agent": args.agent,
        "requested_model": requested_model,
        "result_model": getattr(result, "model", None),
        "substitution": substitution,
        "usage_record_surfaced": True,
        "telemetry_event_seen": True,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""
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
