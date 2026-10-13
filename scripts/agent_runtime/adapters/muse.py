"""Held Muse subscription CLI candidate; unproven guard modes fail closed (#10511)."""

from __future__ import annotations

import json
from pathlib import Path

from ..result import ParseResult
from .base import InvocationPlan


class MuseGuardParityRefused(ValueError):
    """No provider is contacted without native forbidden-action evidence."""

    code = "MUSE_GUARD_PARITY_UNPROVEN"


class MuseAdapter:
    """Parse native JSONL evidence, but refuse execution until guard qualification."""

    name = "muse"
    default_model = None
    # Keep recognized modes here so direct runtime requests reach the typed guard
    # refusal rather than a generic unsupported-mode error. Neither is enabled.
    supported_modes = frozenset({"read-only", "workspace-write"})

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
        """Refuse before creating a prompt file, argv, or subprocess."""
        safe_mode = mode if mode in self.supported_modes else "unsupported mode"
        raise MuseGuardParityRefused(
            f"{MuseGuardParityRefused.code}: {safe_mode} has no native forbidden-action proof; "
            "shell, credential, publish, destructive-command and filesystem guards remain unproven"
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
        """Require a complete terminal record; never infer identity from the request."""
        terminal = None
        terminal_kind = None
        malformed = False
        actual_model = None
        tokens = None
        reasoning_tokens = None
        calls = []
        for line in stdout.split("\n"):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict) or not isinstance(record.get("payload"), dict):
                    raise ValueError("invalid event")
                kind, payload = record.get("payload_type"), record["payload"]
                if not isinstance(kind, str):
                    raise ValueError("missing event type")
                if kind.startswith("run.terminal."):
                    if terminal is not None:
                        malformed = True
                    terminal = payload
                    terminal_kind = kind
                # Native task status facets attest the provider-observed model.
                # run.model.configured is only the requested configuration.
                if kind == "task.lifecycle.status":
                    event = payload.get("event") or {}
                    details = event.get("details") or {}
                    for facet in details.get("facets", []):
                        detail = facet.get("detail", {})
                        if facet.get("kind") == "producer" and detail.get("provider") == "meta":
                            observed = detail.get("model")
                            if isinstance(observed, str) and observed.strip():
                                actual_model = observed
                usage = payload.get("usage")
                if isinstance(usage, dict):
                    total = payload.get("totalTokens", usage.get("total_tokens"))
                    if total is None:
                        inp = usage.get("inputTokens", usage.get("input_tokens"))
                        out = usage.get("outputTokens", usage.get("output_tokens"))
                        if type(inp) is int and type(out) is int and inp >= 0 and out >= 0:
                            total = inp + out
                    if type(total) is int and total >= 0:
                        tokens = (tokens or 0) + total
                    reasoning = usage.get("reasoningTokens", usage.get("reasoning_tokens"))
                    if type(reasoning) is int and reasoning >= 0:
                        # Reasoning is a subset of output, never added twice.
                        reasoning_tokens = (reasoning_tokens or 0) + reasoning
                if kind == "task.lifecycle.proposed":
                    event = payload.get("event") or {}
                    tool = event.get("task_kind", "")
                    if isinstance(tool, str) and tool.startswith("tool."):
                        calls.append({"name": tool.removeprefix("tool.")})
            except (ValueError, TypeError, AttributeError):
                malformed = True
        text = terminal.get("text") if terminal else None
        ok = (
            returncode == 0
            and not malformed
            and terminal is not None
            and terminal_kind == "run.terminal.completed"
            and terminal.get("terminal") == "completed"
            and isinstance(text, str)
            and bool(text.strip())
        )
        attribution = {
            "requested_provider": "meta",
            "requested_model": None,
            "actual_provider": "meta",
            "actual_model": actual_model,
            "actual_model_known": actual_model is not None,
            "substituted": False,
            "source": "muse-provider-status" if actual_model else "unattested-harness",
            "marker": None,
            "reasoning_tokens": reasoning_tokens,
        }
        if plan is not None and "--model" in plan.cmd:
            attribution["requested_model"] = plan.cmd[plan.cmd.index("--model") + 1]
            attribution["substituted"] = bool(actual_model and actual_model != attribution["requested_model"])
        # Diagnostics are body-free. Raw provider and tool prose can contain
        # credentials or private paths and must not enter failure logs.
        return ParseResult(
            ok=ok,
            response=text if ok else "",
            tokens=tokens,
            tool_calls=calls,
            substitution=attribution,
            stderr_excerpt=None if ok else "Muse stream incomplete, malformed, or process failed",
            failure_code=None if ok else "provider_stream_incomplete",
            provider_error_text=None if ok else "",
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """JSONL stdout would provide the runner's liveness signal."""
        return ()
