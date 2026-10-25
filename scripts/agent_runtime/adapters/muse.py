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
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from scripts.common.jsonl import jsonl_lines
from scripts.guardrails.worktree_containment import _require_real_directories, is_dispatch_worktree

from ..env_sanitize import _is_provider_safe_name, build_probe_env
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


def require_muse_execution_model(model: str | None) -> str:
    """Apply the existing catalog lifecycle and transport gate before any probe."""
    from scripts.review.model_catalog import require_execution_model

    return require_execution_model(resolve_muse_model(model), transport="native_muse")


def _workspace(cwd: Path, nonce: str, *, preview: bool = False) -> Path:
    """Validate both the existing and planned dispatch paths before resolution."""
    if not isinstance(nonce, str) or re.fullmatch(r"[0-9a-f]{16}", nonce) is None:
        raise ValueError("muse_worker_nonce_required")
    if (
        not cwd.is_absolute()
        or any(unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"} for char in str(cwd))
    ):
        raise ValueError("muse_dispatch_worktree_required")
    existing = cwd
    if preview:
        while not existing.exists() and not existing.is_symlink():
            existing = existing.parent
    _require_real_directories(existing)
    workspace = cwd.resolve(strict=not preview)
    if cwd != workspace or not is_dispatch_worktree(workspace):
        raise ValueError("muse_dispatch_worktree_required")
    return workspace


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
class MuseRunEvidence:
    """Validated CLI accounting, never backend or effective-policy attestation."""

    task_id: str
    run_nonce: str
    provider_session_id: str
    provider_run_id: str
    requested_selector: str
    usage_model: str
    cli_version: str
    cli_sha256: bytes
    prompt_sha256: bytes
    declared_mode: str
    declared_profile: str
    declared_toolset: tuple[str, ...]
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    reasoning_tokens: int
    calls: int
    completed_calls: int
    total_tokens: int
    workspace_matches: Literal[True] = True
    children_included: Literal[False] = False
    failed_calls: Literal[0] = 0
    cancelled_calls: Literal[0] = 0
    effective_permissions: Literal["unknown"] = "unknown"
    observed_model: None = None
    identity_state: Literal["unknown"] = "unknown"

    def projection(self) -> dict:
        """Return a body-free receipt shared by usage and task mirrors."""
        fields = asdict(self)
        fields["declared_toolset"] = list(self.declared_toolset)
        # Only the validated, locally computed launch digests use byte arrays.
        # All string fields retain the existing sinks' normal sanitization.
        fields["cli_sha256"] = list(self.cli_sha256)
        fields["prompt_sha256"] = list(self.prompt_sha256)
        digest = hashlib.sha256(json.dumps(fields, sort_keys=True, separators=(",", ":")).encode()).digest()
        return {**fields, "receipt_ref": f"muse-run:{self.provider_session_id}:{self.provider_run_id}",
                "receipt_sha256": list(digest)}


@dataclass(frozen=True)
class MuseParseResult(ParseResult):
    # Native task events have not been qualified as tool-call telemetry.
    tool_calls_total: int | None = None
    muse_run: MuseRunEvidence | None = None


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
        if set(config) - {
            "muse_worker", "muse_role", "run_nonce", "muse_tmp_root", "read_only_tmp_root",
            "max_model_steps", "max_tool_output_bytes",
        }:
            raise ValueError("muse_worker_configuration_refused")
        require_muse_execution_model(model)
        if model != self.default_model or (config.get("muse_role"), mode) not in {
            ("implementation", "workspace-write"), ("investigation", "read-only"),
        }:
            raise ValueError("muse_worker_role_mode_refused")
        nonce = config.get("run_nonce")
        workspace = _workspace(cwd, nonce)
        return self._plan(
            prompt=prompt,
            mode=mode,
            workspace=workspace,
            model=model,
            task_id=task_id,
            nonce=nonce,
            scratch_root=config.get("muse_tmp_root"),
            effort=effort,
            max_model_steps=config.get("max_model_steps"),
            max_tool_output_bytes=config.get("max_tool_output_bytes"),
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
            workspace=_workspace(cwd, run_nonce, preview=True),
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
        max_model_steps: object = None,
        max_tool_output_bytes: object = None,
    ) -> InvocationPlan:
        if mode not in self.supported_modes or (effort is not None and effort not in _EFFORTS):
            raise ValueError("muse_worker_mode_or_effort_refused")
        if not task_id:
            raise ValueError("muse_delegate_worker_required")
        if max_model_steps is not None and (type(max_model_steps) is not int or max_model_steps < 1):
            raise ValueError("muse_model_step_budget_invalid")
        if max_tool_output_bytes is not None and (
            type(max_tool_output_bytes) is not int
            or (max_tool_output_bytes != 0 and max_tool_output_bytes < 9)
        ):
            raise ValueError("muse_tool_output_budget_invalid")
        require_muse_execution_model(model)
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
            env=build_probe_env(provider="muse", overrides={"MUSE_NO_AUTO_UPDATE": "1"}),
            cwd=workspace if not preview else scratch,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout.strip()
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
        if max_model_steps is not None:
            cmd.extend(["--max-model-steps", str(max_model_steps)])
        if max_tool_output_bytes is not None:
            cmd.extend(["--max-tool-output-bytes", str(max_tool_output_bytes)])
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
                "max_model_steps": max_model_steps,
                "max_tool_output_bytes": max_tool_output_bytes,
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
            mode = plan.metadata["mode"]
            if (
                mode not in _TOOLS
                or plan.metadata["permission_profile"] != _PROFILES[mode]
                or plan.metadata["toolset"] != list(_TOOLS[mode])
            ):
                raise ValueError("muse_permission_binding_invalid")
            session = plan.metadata["provider_session_id"]
            UUID(str(session))
            command = None
            linked = started = False
            tasks: dict[str, str | None] = {}
            usage = terminal = workspace = None
            sequences: dict[tuple[str, str], int] = {}
            ids: set[str] = set()
            for line in jsonl_lines(stdout.removesuffix("\n")):
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
                    raise ValueError(
                        f"muse_event_schema_unknown: cli_version={plan.metadata.get('cli_version', 'unknown')[:128]}"
                    )
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
                if sequence != sequences.get(key, 0) + 1:
                    raise ValueError("muse_event_order_invalid")
                sequences[key] = sequence
                kind, payload = record["payload_type"], record["payload"]
                if kind == "runtime.command.accepted":
                    if command is not None or sequence != 1 or stream["kind"] != "session":
                        raise ValueError("muse_multiple_runs")
                    if payload["kind"] != "command_accepted" or payload["command_kind"] != "turn.submit":
                        raise ValueError("muse_run_binding_invalid")
                    command = payload["command_id"]
                    UUID(command)
                if command is None or payload.get("command_id") != command or record.get("causation_id") != command:
                    raise ValueError("muse_run_binding_invalid")
                if (kind == "run.usage") != (stream["kind"] == "exec.usage"):
                    raise ValueError("muse_usage_binding_invalid")
                if kind == "session.run.linked":
                    if linked:
                        raise ValueError("muse_multiple_runs")
                    linked = True
                    if payload["run_stream"] != {"kind": "run", "id": command}:
                        raise ValueError("muse_run_binding_invalid")
                if kind != "runtime.command.accepted" and not linked:
                    raise ValueError("muse_run_binding_invalid")
                if kind not in {"runtime.command.accepted", "session.workspace_branch.observed"} and (
                    payload.get("run_stream") != {"kind": "run", "id": command}
                ):
                    raise ValueError("muse_run_binding_invalid")
                if kind == "run.lifecycle.started":
                    if started or workspace is None:
                        raise ValueError("muse_run_binding_invalid")
                    started = True
                if kind == "task.stream.linked" or kind.startswith("task.lifecycle."):
                    if not started:
                        raise ValueError("muse_task_binding_invalid")
                    task = payload["task_id"]
                    UUID(task)
                    if payload["task_stream"] != {"kind": "task", "id": task}:
                        raise ValueError("muse_task_binding_invalid")
                    if kind == "task.stream.linked":
                        if task in tasks:
                            raise ValueError("muse_task_binding_invalid")
                        tasks[task] = None
                    else:
                        event = payload["event"]
                        stage = kind.removeprefix("task.lifecycle.")
                        if task not in tasks or event["task_id"] != task or event["kind"] != stage:
                            raise ValueError("muse_task_binding_invalid")
                        # These are the lifecycle stages in the preserved exec
                        # stream, not MSP notifications or tool authorization.
                        previous = {
                            "proposed": None, "accepted": "proposed", "scheduled": "accepted",
                            "side_effect_intent": "scheduled", "started": "side_effect_intent",
                            "completed": "started",
                        }
                        if stage not in previous or tasks[task] != previous[stage]:
                            raise ValueError("muse_task_order_invalid")
                        tasks[task] = stage
                if kind == "session.workspace_branch.observed":
                    if workspace is not None or payload["record"]["command_id"] != command:
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
            if (
                not started or not tasks or any(stage != "completed" for stage in tasks.values())
                or workspace != plan.metadata["workspace"] or usage is None or terminal is None
            ):
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
            task_id, nonce = plan.metadata["task_id"], plan.metadata["run_nonce"]
            if (
                not isinstance(task_id, str) or not 0 < len(task_id) <= 100
                or not isinstance(nonce, str) or re.fullmatch(r"[0-9a-f]{16}", nonce) is None
                or not isinstance(plan.metadata["cli_version"], str)
                or not 0 < len(plan.metadata["cli_version"]) <= 128
                or any(re.fullmatch(r"[0-9a-f]{64}", plan.metadata[key]) is None
                       for key in ("cli_sha256", "prompt_sha256"))
            ):
                raise ValueError("muse_launch_binding_invalid")
            evidence = MuseRunEvidence(
                task_id=task_id, run_nonce=nonce, provider_session_id=session, provider_run_id=command,
                requested_selector=plan.metadata["model"], usage_model=counters["model"],
                cli_version=plan.metadata["cli_version"], cli_sha256=bytes.fromhex(plan.metadata["cli_sha256"]),
                prompt_sha256=bytes.fromhex(plan.metadata["prompt_sha256"]), declared_mode=mode,
                declared_profile=_PROFILES[mode], declared_toolset=_TOOLS[mode],
                input_tokens=input_tokens, output_tokens=output_tokens,
                cached_tokens=counters["cached_tokens"], reasoning_tokens=counters["reasoning_tokens"],
                calls=calls, completed_calls=usage["completed_calls"], total_tokens=input_tokens + output_tokens,
            )
            return MuseParseResult(
                ok=True, response=response, session_id=session,
                tokens=input_tokens + output_tokens, muse_run=evidence,
            )
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            return MuseParseResult(
                ok=False,
                response="",
                failure_code="provider_stream_incomplete",
                stderr_excerpt=(str(exc) if str(exc).startswith("muse_event_schema_unknown:")
                                else "muse_worker_evidence_incomplete"),
                provider_error_text="",
            )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        return ()
