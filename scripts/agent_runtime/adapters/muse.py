"""Native Muse workers. Driver and review admission are deliberately separate.

The exec JSONL envelope is not the MSP notification schema. Only the native
run terminal and its run-scoped usage can establish transport completion.
Neither establishes that a worker's answer is correct.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from scripts.guardrails.worktree_containment import is_dispatch_worktree

from ..env_sanitize import _is_provider_safe_name
from ..read_only_tmp import validate_read_only_tmp_root
from ..result import ParseResult
from .base import InvocationPlan

MUSE_MODELS = frozenset({"muse-wonder-full-1.0", "muse-spark-1.3"})
_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})
_MAX_JSONL_BYTES = 16 * 1024 * 1024
_TOOLS = {
    "read-only": ("read_file",),
    "workspace-write": ("read_file", "write_file", "edit_file"),
}
_PROFILES = {"read-only": ":read-only", "workspace-write": ":ask-me"}
_PASSIVE_EVENTS = frozenset(
    {
        "runtime.command.accepted",
        "session.run.linked",
        "turn.input.user",
        "run.lifecycle.started",
        "run.output.delta",
        "task.stream.linked",
        "task.lifecycle.proposed",
        "task.lifecycle.accepted",
        "task.lifecycle.scheduled",
        "task.lifecycle.side_effect_intent",
        "task.lifecycle.started",
        "task.lifecycle.completed",
    }
)


def resolve_muse_model(model: str | None) -> str:
    requested = model or MuseAdapter.default_model
    if requested not in MUSE_MODELS:
        raise ValueError("muse_worker_model_refused")
    return requested


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("muse_duplicate_json_member")
        result[key] = value
    return result


def _counter(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("muse_usage_counter_invalid")
    return value


@dataclass(frozen=True)
class MuseParseResult(ParseResult):
    # Native task events have not been qualified as tool-call telemetry.
    tool_calls_total: int | None = None


class MuseAdapter:
    """File-tool workers with native profiles, no shell or subordinate agents."""

    name = "muse"
    default_model = "muse-wonder-full-1.0"
    default_effort = "high"
    supported_modes = frozenset(_TOOLS)

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
        model = resolve_muse_model(model)
        config = tool_config or {}
        if mode not in self.supported_modes:
            raise ValueError("muse_worker_mode_refused")
        if effort is not None and effort not in _EFFORTS:
            raise ValueError("muse_worker_effort_refused")
        if session_id or config.get("muse_worker") is not True or not task_id:
            raise ValueError("muse_delegate_worker_required")
        if not _is_provider_safe_name("MUSE_NO_AUTO_UPDATE", "muse"):
            raise ValueError("muse_child_environment_not_admitted")
        if set(config) - {"muse_worker", "run_nonce", "muse_tmp_root", "read_only_tmp_root"}:
            raise ValueError("muse_worker_configuration_refused")
        nonce = config.get("run_nonce")
        if not isinstance(nonce, str) or re.fullmatch(r"[0-9a-f]{16}", nonce) is None:
            raise ValueError("muse_worker_nonce_required")
        if not cwd.is_absolute() or cwd.is_symlink() or not is_dispatch_worktree(cwd):
            raise ValueError("muse_dispatch_worktree_required")
        workspace = cwd.resolve(strict=True)
        return self._plan(
            prompt=prompt,
            mode=mode,
            workspace=workspace,
            model=model,
            task_id=task_id,
            nonce=nonce,
            scratch_root=config.get("muse_tmp_root"),
            effort=effort,
        )

    def preview_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str,
        run_nonce: str,
        scratch_root: str,
        effort: str | None,
    ) -> InvocationPlan:
        """Plan a not-yet-created worktree without granting execution admission."""
        return self._plan(
            prompt=prompt,
            mode=mode,
            workspace=cwd.resolve(),
            model=resolve_muse_model(model),
            task_id=task_id,
            nonce=run_nonce,
            scratch_root=scratch_root,
            effort=effort,
            preview=True,
        )

    def _plan(
        self,
        *,
        prompt: str,
        mode: str,
        workspace: Path,
        model: str,
        task_id: str,
        nonce: str,
        scratch_root: object,
        effort: str | None,
        preview: bool = False,
    ) -> InvocationPlan:
        if mode not in self.supported_modes or (effort is not None and effort not in _EFFORTS):
            raise ValueError("muse_worker_mode_or_effort_refused")
        # Use the existing lease validator for both modes' private transport.
        scratch = validate_read_only_tmp_root(
            {"read_only_tmp_root": scratch_root}, workspace, "read-only", adapter="muse"
        )
        if scratch is None:
            raise ValueError("muse_worker_tmp_lease_required")
        binary = shutil.which("muse")
        if binary is None:
            raise ValueError("muse_cli_unavailable")
        binary = str(Path(binary).resolve(strict=True))
        version = subprocess.run(
            [binary, "--version"],
            env={**os.environ, "MUSE_NO_AUTO_UPDATE": "1"},
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()
        if not re.fullmatch(r"Muse Code 1\.4\.11 \(1\.4\.11-R6667\.1\)", version):
            raise ValueError("muse_cli_compatibility_unknown")
        provider_session = str(uuid4())
        prompt_path = str(scratch / f"muse-prompt-{provider_session}.txt")
        fd = os.open(prompt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(prompt)
        cmd = [
            binary,
            "exec",
            "--json",
            "--provider",
            "meta",
            "--model",
            model,
            "--reasoning-effort",
            effort or self.default_effort,
            "--contributor-mode",
            "off",
            "--session-id",
            provider_session,
            "--workspace",
            str(workspace),
            "--worktree",
            "off",
            "--permission-profile",
            _PROFILES[mode],
            "--disable-shell",
            "--disable-web-tools",
            "--disable-reminders",
            "--disable-request-user-input",
            "--no-foreign-personal-context",
            "--config",
            "run.toolset=" + json.dumps(_TOOLS[mode]),
        ]
        if mode == "read-only":
            cmd.append("--disable-write")
        cmd.extend(["--prompt-file", prompt_path])
        return InvocationPlan(
            cmd=cmd,
            cwd=workspace,
            env_overrides={"MUSE_NO_AUTO_UPDATE": "1"},
            env_unsets=("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "SSH_AUTH_SOCK"),
            metadata={
                "task_id": task_id,
                "run_nonce": nonce,
                "provider_session_id": provider_session,
                "model": model,
                "workspace": str(workspace),
                "mode": mode,
                "cli_version": version,
                "cli_sha256": hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "permission_profile": _PROFILES[mode],
                "toolset": list(_TOOLS[mode]),
                "preview": preview,
            },
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
    ) -> MuseParseResult:
        # Stderr can contain prompts, tool output and path diagnostics. It never
        # supplies a success, quota classification or usage counter.
        try:
            if plan is None or plan.metadata.get("preview") is not False or returncode != 0:
                raise ValueError("muse_process_failed")
            if len(stdout.encode("utf-8")) > _MAX_JSONL_BYTES:
                raise ValueError("muse_stream_too_large")
            session = plan.metadata["provider_session_id"]
            UUID(str(session))
            command = None
            usage = terminal = workspace = None
            sequences: dict[tuple[str, str], int] = {}
            ids: set[str] = set()
            for line in stdout.splitlines():
                if terminal is not None:
                    raise ValueError("muse_event_after_terminal")
                record = json.loads(line, object_pairs_hook=_unique_object)
                if (
                    not isinstance(record, dict)
                    or type(record.get("schema_version")) is not int
                    or record["schema_version"] != 1
                    or type(record.get("payload_schema_version")) is not int
                    or record["payload_schema_version"] != 1
                ):
                    raise ValueError("muse_event_schema_unknown")
                event_id = record["id"]
                UUID(event_id)
                if event_id in ids:
                    raise ValueError("muse_duplicate_event")
                ids.add(event_id)
                stream = record["stream"]
                if stream["id"] != session or stream["kind"] not in {"session", "exec.usage"}:
                    raise ValueError("muse_foreign_session")
                key = (stream["kind"], stream["id"])
                sequence = _counter(record["sequence"])
                if sequence <= sequences.get(key, 0):
                    raise ValueError("muse_event_order_invalid")
                sequences[key] = sequence
                kind, payload = record["payload_type"], record["payload"]
                if kind == "session.run.linked":
                    if command is not None:
                        raise ValueError("muse_multiple_runs")
                    command = payload["command_id"]
                    UUID(command)
                    if payload["run_stream"] != {"kind": "run", "id": command}:
                        raise ValueError("muse_run_binding_invalid")
                if kind in {"run.usage", "run.terminal.completed", "session.workspace_branch.observed"} and (
                    command is None or payload.get("command_id") != command or record.get("causation_id") != command
                ):
                    raise ValueError("muse_run_binding_invalid")
                if kind == "session.workspace_branch.observed":
                    if workspace is not None:
                        raise ValueError("muse_workspace_changed")
                    workspace = payload["record"]["workspace_root"]
                elif kind == "run.usage":
                    if (
                        usage is not None
                        or terminal is not None
                        or stream["kind"] != "exec.usage"
                        or payload.get("kind") != "run_usage"
                    ):
                        raise ValueError("muse_usage_binding_invalid")
                    usage = payload
                elif kind.startswith("run.terminal."):
                    if (
                        terminal is not None
                        or kind != "run.terminal.completed"
                        or payload.get("terminal") != "completed"
                        or payload.get("kind") != "run_terminal"
                        or payload.get("reason") is not None
                        or payload.get("command_id") != command
                        or record.get("causation_id") != command
                    ):
                        raise ValueError("muse_run_failed")
                    terminal = payload
                elif kind not in _PASSIVE_EVENTS:
                    raise ValueError("muse_event_type_unknown")
            if workspace != plan.metadata["workspace"] or usage is None or terminal is None:
                raise ValueError("muse_evidence_incomplete")
            if (
                terminal.get("run_stream") != {"kind": "run", "id": command}
                or usage.get("run_stream") != terminal["run_stream"]
            ):
                raise ValueError("muse_run_binding_invalid")
            if (
                usage.get("children_included") is not False
                or _counter(usage["failed_calls"])
                or _counter(usage["cancelled_calls"])
            ):
                raise ValueError("muse_usage_incomplete")
            models = usage["models"]
            if not isinstance(models, list) or len(models) != 1 or models[0]["model"] != plan.metadata["model"]:
                raise ValueError("muse_usage_model_unknown")
            counters = models[0]
            calls = _counter(usage["calls"])
            if calls < 1 or calls != _counter(usage["completed_calls"]) or calls != _counter(counters["calls"]):
                raise ValueError("muse_usage_incomplete")
            # Meta cache hits are part of input; reasoning is part of output.
            input_tokens, output_tokens = _counter(counters["input_tokens"]), _counter(counters["output_tokens"])
            if (
                _counter(counters["cached_tokens"]) > input_tokens
                or _counter(counters["reasoning_tokens"]) > output_tokens
            ):
                raise ValueError("muse_usage_counter_invalid")
            response = terminal["text"]
            if not isinstance(response, str) or not response.strip() or input_tokens + output_tokens < 1:
                raise ValueError("muse_evidence_incomplete")
            return MuseParseResult(
                ok=True, response=response, tokens=input_tokens + output_tokens, session_id=str(session)
            )
        except (ValueError, TypeError, KeyError, AttributeError):
            return MuseParseResult(
                ok=False,
                response="",
                failure_code="provider_stream_incomplete",
                stderr_excerpt="muse_worker_evidence_incomplete",
                provider_error_text="",
            )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        return ()
