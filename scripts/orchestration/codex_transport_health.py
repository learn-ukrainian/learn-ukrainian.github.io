"""Bounded fresh-process health probe for the Codex bridge transport.

The probe deliberately launches a new Codex CLI process through ``ask-codex``.
Static config checks cannot detect server-side reserved-tool schema rejection.
The resulting receipt is sanitized, TTL-cached runtime state; it never stores
the prompt, model response, or raw error text.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import tomllib
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.common.repo_root import main_checkout_root

SCHEMA_VERSION = "codex-transport-health.v1"
HEALTHY = "healthy"
DEGRADED = "degraded"
UNKNOWN = "unknown"
RESERVED_SCHEMA_FAILURE = "reserved_collaboration_schema"
EXPECTED_TOOL_NAMESPACE = "agents"
DEFAULT_TTL_SECONDS = 900
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_MODEL = "gpt-5.6-terra"
DEFAULT_EFFORT = "low"

SOURCE_REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_REPO_ROOT = main_checkout_root(SOURCE_REPO_ROOT)
DEFAULT_CONFIG_PATH = SOURCE_REPO_ROOT / "agents_extensions" / "codex" / "config.toml"
TRANSPORT_RECEIPT_PATH = (
    RUNTIME_REPO_ROOT / "batch_state" / "runtime" / "codex-transport-health.json"
)

CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
ReplyLoader = Callable[[str], list[dict[str, str]]]


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def configured_tool_namespace(config_path: Path = DEFAULT_CONFIG_PATH) -> str | None:
    """Return the configured V2 tool namespace without exposing other config."""
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return None
    features = config.get("features")
    if not isinstance(features, dict):
        return None
    multi_agent_v2 = features.get("multi_agent_v2")
    if not isinstance(multi_agent_v2, dict):
        return None
    namespace = multi_agent_v2.get("tool_namespace")
    return str(namespace) if namespace else None


def _sanitized_namespace(namespace: str | None) -> str | None:
    if namespace in {EXPECTED_TOOL_NAMESPACE, "collaboration"}:
        return namespace
    return "other" if namespace else None


def load_receipt(receipt_path: Path = TRANSPORT_RECEIPT_PATH) -> dict[str, Any] | None:
    try:
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        return None
    return payload


def _write_receipt(receipt: dict[str, Any], receipt_path: Path) -> None:
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=receipt_path.parent,
            prefix=f".{receipt_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(receipt, handle, indent=2, sort_keys=True)
            handle.write("\n")
            temporary_path = Path(handle.name)
        os.replace(temporary_path, receipt_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def current_transport_health(
    *,
    receipt_path: Path = TRANSPORT_RECEIPT_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return a sanitized read-only health snapshot; never launch a model."""
    checked_now = now or _utc_now()
    namespace = configured_tool_namespace(config_path)
    receipt = load_receipt(receipt_path)
    if receipt is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": DEGRADED if namespace != EXPECTED_TOOL_NAMESPACE else UNKNOWN,
            "fresh": False,
            "failure_class": (
                "invalid_tool_namespace"
                if namespace != EXPECTED_TOOL_NAMESPACE
                else "no_probe_receipt"
            ),
            "tool_namespace": _sanitized_namespace(namespace),
            "namespace_valid": namespace == EXPECTED_TOOL_NAMESPACE,
            "checked_at": None,
            "expires_at": None,
            "age_seconds": None,
            "source": "receipt",
        }

    checked_at = _parse_datetime(receipt.get("checked_at"))
    expires_at = _parse_datetime(receipt.get("expires_at"))
    fresh = bool(expires_at and checked_now <= expires_at)
    status = str(receipt.get("status") or UNKNOWN)
    if status not in {HEALTHY, DEGRADED, UNKNOWN}:
        status = UNKNOWN
    if not fresh:
        status = UNKNOWN
    if namespace != EXPECTED_TOOL_NAMESPACE:
        status = DEGRADED

    age_seconds = None
    if checked_at is not None:
        age_seconds = max(0, int((checked_now - checked_at).total_seconds()))

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "fresh": fresh,
        "failure_class": (
            "invalid_tool_namespace"
            if namespace != EXPECTED_TOOL_NAMESPACE
            else receipt.get("failure_class")
            if fresh
            else "stale_probe_receipt"
        ),
        "tool_namespace": _sanitized_namespace(namespace),
        "namespace_valid": namespace == EXPECTED_TOOL_NAMESPACE,
        "checked_at": receipt.get("checked_at"),
        "expires_at": receipt.get("expires_at"),
        "age_seconds": age_seconds,
        "model": receipt.get("model"),
        "effort": receipt.get("effort"),
        "source": "receipt",
    }


def _load_bridge_replies(task_id: str) -> list[dict[str, str]]:
    from scripts.ai_agent_bridge._db import get_db

    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT message_type, from_llm, to_llm, content
            FROM messages
            WHERE task_id = ?
            ORDER BY id
            """,
            (task_id,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "message_type": str(row[0]),
            "from_llm": str(row[1]),
            "to_llm": str(row[2]),
            "content": str(row[3]),
        }
        for row in rows
    ]


def _classify_failure(output: str, replies: list[dict[str, str]]) -> str:
    reply_text = "\n".join(reply.get("content", "") for reply in replies)
    combined = f"{output}\n{reply_text}".lower()
    if (
        "collaboration.spawn_agent" in combined
        and "reserved for use by this model" in combined
    ):
        return RESERVED_SCHEMA_FAILURE
    if "rate limited" in combined or "usage limit" in combined:
        return "codex_rate_limited"
    if "timeout" in combined or "timed out" in combined or "stalled" in combined:
        return "fresh_codex_probe_timeout"
    if "unavailable" in combined or "not found" in combined:
        return "codex_cli_unavailable"
    return "fresh_codex_probe_failed"


def _receipt(
    *,
    status: str,
    checked_at: datetime,
    ttl_seconds: int,
    model: str,
    effort: str,
    task_id: str,
    failure_class: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "checked_at": _isoformat_z(checked_at),
        "expires_at": _isoformat_z(checked_at + timedelta(seconds=ttl_seconds)),
        "model": model,
        "effort": effort,
        "task_id": task_id,
        "failure_class": failure_class,
        "source": "fresh_bridge_probe",
    }


def probe_codex_transport(
    *,
    receipt_path: Path = TRANSPORT_RECEIPT_PATH,
    config_path: Path = DEFAULT_CONFIG_PATH,
    runtime_repo_root: Path = RUNTIME_REPO_ROOT,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    model: str = DEFAULT_MODEL,
    effort: str = DEFAULT_EFFORT,
    force_fresh: bool = False,
    now: datetime | None = None,
    command_runner: CommandRunner = subprocess.run,
    reply_loader: ReplyLoader = _load_bridge_replies,
) -> dict[str, Any]:
    """Probe one genuinely fresh Codex worker or reuse an unexpired receipt."""
    checked_now = now or _utc_now()
    if not force_fresh:
        cached = current_transport_health(
            receipt_path=receipt_path,
            config_path=config_path,
            now=checked_now,
        )
        if cached["fresh"] and cached.get("model") == model:
            return cached

    namespace = configured_tool_namespace(config_path)
    task_id = f"codex-transport-probe-{uuid.uuid4().hex[:12]}"
    if namespace != EXPECTED_TOOL_NAMESPACE:
        receipt = _receipt(
            status=DEGRADED,
            checked_at=checked_now,
            ttl_seconds=ttl_seconds,
            model=model,
            effort=effort,
            task_id=task_id,
            failure_class="invalid_tool_namespace",
        )
        _write_receipt(receipt, receipt_path)
        return current_transport_health(
            receipt_path=receipt_path,
            config_path=config_path,
            now=checked_now,
        )

    sentinel = f"CODEX-TRANSPORT-OK-{uuid.uuid4().hex}"
    prompt = (
        "Transport health probe. Return exactly this sentinel and nothing else: "
        f"{sentinel}"
    )
    python_path = runtime_repo_root / ".venv" / "bin" / "python"
    bridge_path = runtime_repo_root / "scripts" / "ai_agent_bridge" / "__main__.py"
    command = [
        str(python_path),
        str(bridge_path),
        "ask-codex",
        "-",
        "--task-id",
        task_id,
        "--from",
        "health-probe",
        "--to-model",
        model,
        "--effort",
        effort,
        "--new-session",
    ]
    env = os.environ.copy()
    env["CODEX_BRIDGE_TIMEOUT"] = str(timeout_seconds)
    env["AB_REPO_ROOT"] = str(runtime_repo_root)

    output = ""
    try:
        completed = command_runner(
            command,
            cwd=runtime_repo_root,
            env=env,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_seconds + 15,
            check=False,
        )
        output = f"{completed.stdout}\n{completed.stderr}"
        replies = reply_loader(task_id)
        matched = any(
            reply.get("message_type") == "response"
            and reply.get("from_llm") == "codex"
            and reply.get("to_llm") == "health-probe"
            and reply.get("content", "").strip() == sentinel
            for reply in replies
        )
        if matched:
            status = HEALTHY
            failure_class = None
        else:
            status = DEGRADED
            failure_class = _classify_failure(output, replies)
    except subprocess.TimeoutExpired:
        status = DEGRADED
        failure_class = "fresh_codex_probe_timeout"
    except OSError:
        status = DEGRADED
        failure_class = "codex_cli_unavailable"

    receipt = _receipt(
        status=status,
        checked_at=checked_now,
        ttl_seconds=ttl_seconds,
        model=model,
        effort=effort,
        task_id=task_id,
        failure_class=failure_class,
    )
    _write_receipt(receipt, receipt_path)
    return current_transport_health(
        receipt_path=receipt_path,
        config_path=config_path,
        now=checked_now,
    )


def _exit_code(status: str) -> int:
    if status == HEALTHY:
        return 0
    if status == DEGRADED:
        return 3
    return 4


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Read the cached probe receipt")
    status.add_argument("--receipt", type=Path, default=TRANSPORT_RECEIPT_PATH)
    status.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    status.add_argument("--json", action="store_true")

    probe = subparsers.add_parser("probe", help="Run or reuse a fresh-process probe")
    probe.add_argument("--receipt", type=Path, default=TRANSPORT_RECEIPT_PATH)
    probe.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    probe.add_argument("--ttl-seconds", type=int, default=DEFAULT_TTL_SECONDS)
    probe.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    probe.add_argument("--model", default=DEFAULT_MODEL)
    probe.add_argument("--effort", default=DEFAULT_EFFORT)
    probe.add_argument("--fresh", action="store_true")
    probe.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "status":
        result = current_transport_health(
            receipt_path=args.receipt,
            config_path=args.config,
        )
    else:
        if args.ttl_seconds < 1 or args.timeout_seconds < 1:
            raise SystemExit("ttl-seconds and timeout-seconds must be positive")
        result = probe_codex_transport(
            receipt_path=args.receipt,
            config_path=args.config,
            ttl_seconds=args.ttl_seconds,
            timeout_seconds=args.timeout_seconds,
            model=args.model,
            effort=args.effort,
            force_fresh=args.fresh,
        )

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(
            f"status={result['status']} fresh={str(result['fresh']).lower()} "
            f"failure_class={result.get('failure_class') or 'none'}"
        )
    return _exit_code(str(result["status"]))


if __name__ == "__main__":
    raise SystemExit(main())
