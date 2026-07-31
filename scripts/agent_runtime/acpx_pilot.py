"""Bounded native-plus-ACPX shadow comparison pilot (#6063).

The native Codex or Grok invocation is always authoritative. A single
read-only, stateless ACPX shadow call runs after it under one global
non-blocking lock. There is no queue, retry, session, dispatch, chat, review,
or failover behavior on this surface.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ``runner.py`` retains historical sibling imports such as ``ai_llm``. Make
# this module runnable both as ``scripts.agent_runtime.acpx_pilot`` and under
# the legacy ``PYTHONPATH=scripts`` package flavor.
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from scripts.guardrails.worktree_containment import classify_repo_path

from .adapters.acpx import (
    GROK_SHADOW_EFFORT,
    GROK_SHADOW_MODEL,
    TRANSPORT_ENV,
    _require_local_metadata_field,
)
from .errors import AgentStalledError, AgentTimeoutError, RateLimitedError
from .result import Result
from .runner import _invoke_direct_only, _invoke_native_once
from .usage import _usage_dir, write_record

PILOT_AGENT = "acpx-shadow-pilot"
PILOT_ENTRYPOINT = "acpx-pilot"
PILOT_EVENT = "acpx_shadow_comparison"
_PROMPT_MAX_CHARS = 100_000
_KNOWN_OUTCOMES = frozenset({"ok", "error", "rate_limited", "timeout"})


@dataclass(frozen=True)
class _Target:
    native_agent: str
    shadow_agent: str
    native_model: str | None
    shadow_model: str | None
    native_effort: str | None
    shadow_effort: str | None


_TARGETS = {
    "codex": _Target(
        native_agent="codex",
        shadow_agent="acpx-codex-shadow",
        native_model=None,
        shadow_model=None,
        native_effort=None,
        shadow_effort=None,
    ),
    "grok": _Target(
        native_agent="grok",
        shadow_agent="acpx-grok-shadow",
        native_model=GROK_SHADOW_MODEL,
        shadow_model=None,
        native_effort=GROK_SHADOW_EFFORT,
        shadow_effort=GROK_SHADOW_EFFORT,
    ),
}


@dataclass(frozen=True)
class PilotResult:
    """In-memory pilot result; responses are never persisted as evidence."""

    target: str
    executed: bool
    duplicate_suppressed: bool
    busy: bool
    native_outcome: str | None
    shadow_outcome: str | None
    classification_parity: bool | None
    native: Result | None
    shadow: Result | None


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _outcome(result: Result | None, error: BaseException | None) -> str:
    if isinstance(error, RateLimitedError):
        return "rate_limited"
    if isinstance(error, (AgentTimeoutError, AgentStalledError)):
        return "timeout"
    if error is not None or result is None:
        return "error"
    recorded = str(result.usage_record.get("outcome") or "")
    if recorded in _KNOWN_OUTCOMES:
        return recorded
    return "ok" if result.ok else "error"


def _tokens(result: Result | None) -> int | None:
    if result is None:
        return None
    value = result.usage_record.get("tokens")
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _comparison_record(
    *,
    target: str,
    idempotency_digest: str,
    correlation_digest: str,
    outcome: str,
    executed: bool,
    duplicate: bool,
    busy: bool,
    native_outcome: str | None = None,
    shadow_outcome: str | None = None,
    native: Result | None = None,
    shadow: Result | None = None,
) -> dict[str, Any]:
    native_duration = round(native.duration_s, 3) if native is not None else None
    shadow_duration = round(shadow.duration_s, 3) if shadow is not None else None
    duration = sum(value for value in (native_duration, shadow_duration) if value is not None)
    parity = (
        native_outcome == shadow_outcome
        if native_outcome is not None and shadow_outcome is not None
        else None
    )
    return {
        "ts": datetime.now(UTC).isoformat(),
        "agent": PILOT_AGENT,
        "entrypoint": PILOT_ENTRYPOINT,
        "event": PILOT_EVENT,
        "model": "native-plus-shadow",
        "mode": "read-only",
        "outcome": outcome,
        "target": target,
        "executed": executed,
        "duplicate": duplicate,
        "busy": busy,
        "native_outcome": native_outcome,
        "shadow_outcome": shadow_outcome,
        "classification_parity": parity,
        "duration_s": round(duration, 3),
        "native_duration_s": native_duration,
        "shadow_duration_s": shadow_duration,
        "native_tokens": _tokens(native),
        "shadow_tokens": _tokens(shadow),
        "correlation_digest": correlation_digest,
        "idempotency_digest": idempotency_digest,
    }


def _has_executed_digest(evidence_dir: Path, digest: str) -> bool:
    for path in evidence_dir.glob(f"usage_{PILOT_AGENT}-{PILOT_ENTRYPOINT}_*.jsonl"):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for raw in lines:
            try:
                record = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if (
                isinstance(record, dict)
                and record.get("event") == PILOT_EVENT
                and record.get("idempotency_digest") == digest
                and record.get("executed") is True
            ):
                return True
    return False


@contextmanager
def _pilot_lock(path: Path) -> Iterator[bool]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+", encoding="utf-8")  # noqa: SIM115
    acquired = False
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError:
            pass
        yield acquired
    finally:
        if acquired:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _invoke_captured(
    call: Callable[..., Result],
    agent_name: str,
    prompt: str,
    **kwargs: Any,
) -> tuple[Result | None, BaseException | None]:
    try:
        return call(agent_name, prompt, **kwargs), None
    except Exception as exc:
        return None, exc


def run_pilot(
    *,
    target: str,
    prompt: str,
    cwd: Path,
    task_id: str,
    correlation_id: str,
    idempotency_key: str,
    hard_timeout: int = 300,
    evidence_dir: Path | None = None,
    lock_path: Path | None = None,
    native_call: Callable[..., Result] = _invoke_native_once,
    shadow_call: Callable[..., Result] = _invoke_direct_only,
    record_sink: Callable[[dict[str, Any]], None] = write_record,
) -> PilotResult:
    """Run one authoritative native call followed by one observational shadow."""
    if target not in _TARGETS:
        raise ValueError(f"unsupported target {target!r}; choose from {sorted(_TARGETS)}")
    if os.environ.get(TRANSPORT_ENV) != "shadow":
        raise ValueError(f"{TRANSPORT_ENV}=shadow is required for the explicit comparison pilot")
    if not prompt.strip():
        raise ValueError("prompt must be non-empty")
    if len(prompt) > _PROMPT_MAX_CHARS:
        raise ValueError(f"prompt exceeds {_PROMPT_MAX_CHARS} characters")
    if hard_timeout < 1:
        raise ValueError("hard_timeout must be at least one second")

    resolved_cwd = cwd.resolve()
    path_class = classify_repo_path(resolved_cwd, cwd=resolved_cwd)
    if path_class not in {"dispatch_worktree", "other_worktree"}:
        raise ValueError(
            "ACPX comparison cwd must be a registered or dispatch worktree; "
            f"observed {path_class!r}"
        )
    validated_task = _require_local_metadata_field("task_id", task_id, adapter_label="AcpxPilot")
    validated_correlation = _require_local_metadata_field(
        "correlation_id", correlation_id, adapter_label="AcpxPilot"
    )
    validated_idempotency = _require_local_metadata_field(
        "idempotency_key", idempotency_key, adapter_label="AcpxPilot"
    )
    idempotency_digest = _digest(validated_idempotency)
    correlation_digest = _digest(validated_correlation)
    evidence_root = evidence_dir or _usage_dir()
    exclusive_path = lock_path or evidence_root.parent / "acpx_pilot" / "pilot.lock"

    with _pilot_lock(exclusive_path) as acquired:
        if not acquired:
            record_sink(
                _comparison_record(
                    target=target,
                    idempotency_digest=idempotency_digest,
                    correlation_digest=correlation_digest,
                    outcome="error",
                    executed=False,
                    duplicate=False,
                    busy=True,
                )
            )
            return PilotResult(target, False, False, True, None, None, None, None, None)

        if _has_executed_digest(evidence_root, idempotency_digest):
            record_sink(
                _comparison_record(
                    target=target,
                    idempotency_digest=idempotency_digest,
                    correlation_digest=correlation_digest,
                    outcome="ok",
                    executed=False,
                    duplicate=True,
                    busy=False,
                )
            )
            return PilotResult(target, False, True, False, None, None, None, None, None)

        spec = _TARGETS[target]
        native, native_error = _invoke_captured(
            native_call,
            spec.native_agent,
            prompt,
            mode="read-only",
            cwd=resolved_cwd,
            model=spec.native_model,
            task_id=validated_task,
            session_id=None,
            entrypoint="acpx-pilot-native",
            hard_timeout=hard_timeout,
            effort=spec.native_effort,
        )
        shadow, shadow_error = _invoke_captured(
            shadow_call,
            spec.shadow_agent,
            prompt,
            cwd=resolved_cwd,
            model=spec.shadow_model,
            task_id=validated_task,
            tool_config={
                "acpx_shadow": True,
                "target_agent": target,
                "correlation_id": validated_correlation,
                "idempotency_key": validated_idempotency,
            },
            hard_timeout=hard_timeout,
            effort=spec.shadow_effort,
        )
        native_outcome = _outcome(native, native_error)
        shadow_outcome = _outcome(shadow, shadow_error)
        parity = native_outcome == shadow_outcome
        record_sink(
            _comparison_record(
                target=target,
                idempotency_digest=idempotency_digest,
                correlation_digest=correlation_digest,
                outcome=native_outcome,
                executed=True,
                duplicate=False,
                busy=False,
                native_outcome=native_outcome,
                shadow_outcome=shadow_outcome,
                native=native,
                shadow=shadow,
            )
        )
        return PilotResult(
            target,
            True,
            False,
            False,
            native_outcome,
            shadow_outcome,
            parity,
            native,
            shadow,
        )


def _read_prompt(path: str) -> str:
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")


def _cli_payload(result: PilotResult) -> dict[str, Any]:
    return {
        "authority": "native",
        "target": result.target,
        "executed": result.executed,
        "duplicate_suppressed": result.duplicate_suppressed,
        "busy": result.busy,
        "classification_parity": result.classification_parity,
        "native": {
            "outcome": result.native_outcome,
            "response": result.native.response if result.native is not None else None,
        },
        "shadow": {
            "outcome": result.shadow_outcome,
            "response": result.shadow.response if result.shadow is not None else None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, choices=sorted(_TARGETS))
    parser.add_argument("--prompt-file", default="-", help="Prompt file, or - for stdin")
    parser.add_argument("--cwd", required=True, type=Path)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--correlation-id", required=True)
    parser.add_argument("--idempotency-key", required=True)
    parser.add_argument("--hard-timeout", type=int, default=300)
    args = parser.parse_args()
    result = run_pilot(
        target=args.target,
        prompt=_read_prompt(args.prompt_file),
        cwd=args.cwd,
        task_id=args.task_id,
        correlation_id=args.correlation_id,
        idempotency_key=args.idempotency_key,
        hard_timeout=args.hard_timeout,
    )
    print(json.dumps(_cli_payload(result), ensure_ascii=False))
    if result.busy:
        return 75
    if result.duplicate_suppressed:
        return 0
    return 0 if result.native_outcome == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
