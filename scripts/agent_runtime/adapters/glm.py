"""GlmAdapter — wraps opencode CLI for Zhipu GLM-5.2 (glm-5.2).

GLM-5.2 is a strong cross-family code and review model.
LOCAL-ONLY: prompt data egresses to China — forbidden in CI.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
from pathlib import Path

from ..errors import AgentRuntimeError
from ..result import ParseResult
from ..trail_isolation import TrailIsolationError, trail_isolation_requested
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

# Bare catalog model id → subscription-pinned opencode provider route.
_OPENCODE_MODEL_ROUTES: dict[str, str] = {"glm-5.2": "zai-coding-plan/glm-5.2"}

# Env vars whose presence indicates an automated/CI context where the
# China-egress constraint forbids invoking GLM (matches ask-glm backstop).
_CI_ENV_VARS: tuple[str, ...] = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL")

_RATE_LIMIT_RE = re.compile(
    r"rate limit|rate_limit|usage limit|quota exceeded|too many requests|resource_exhausted|\b429\b",
    re.IGNORECASE,
)


class GlmEgressForbiddenError(AgentRuntimeError, ValueError):
    """Refuse to run China-hosted GLM in a CI / automated context (data egress)."""


def assert_glm_egress_allowed(verb: str = "glm adapter") -> None:
    """Refuse to run China-hosted GLM in a CI / automated context (data egress)."""
    for var in _CI_ENV_VARS:
        if var in os.environ:
            raise GlmEgressForbiddenError(
                f"{verb}: refusing to run under {var}={os.environ[var]!r}. GLM is "
                "China-hosted (Zhipu/z.ai) → prompt data egresses to China; it "
                "is LOCAL-ONLY and must never run in CI / automated pipelines."
            )


_EFFORT_TO_VARIANT: dict[str, str] = {
    "low": "minimal",
    "medium": "high",
    "high": "high",
    "xhigh": "max",
    "max": "max",
}


def _extract_text_from_stdout(stdout: str) -> str:
    text = (stdout or "").strip()
    if not text:
        return ""
    if text.startswith("{") and text.endswith("}"):
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                if "text" in data and isinstance(data["text"], str):
                    return data["text"].strip()
                if "response" in data and isinstance(data["response"], str):
                    return data["response"].strip()
        except ValueError:
            pass
    return text


class GlmAdapter:
    """Adapter for the opencode CLI with glm-5.2."""

    name: str = "glm"
    # Fleet MODEL identity (must resolve in model_catalog.yaml). The Z.AI
    # Coding Plan provider pin is an opencode INVOCATION detail — applied in
    # build_invocation via _OPENCODE_MODEL_ROUTES, not stored as identity.
    default_model: str = "glm-5.2"
    # Operator 2026-08-13: omitted effort defaults to high (--variant high);
    # an explicit --effort always wins.
    default_effort: str = "high"
    supported_modes: frozenset[str] = frozenset({"read-only", "workspace-write", "danger"})

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None = None,
        task_id: str | None = None,
        session_id: str | None = None,
        tool_config: dict | None = None,
        effort: str | None = None,
    ) -> InvocationPlan:
        if trail_isolation_requested(tool_config):
            raise TrailIsolationError(
                "trail isolation refused for GLM: opencode does not enforce tool restrictions"
            )
        assert_glm_egress_allowed("GlmAdapter")

        if mode not in self.supported_modes:
            raise ValueError(f"GlmAdapter: unsupported mode {mode!r} (supported: {sorted(self.supported_modes)})")

        binary = shutil.which("opencode") or "opencode"
        target_model = model or self.default_model
        # Route bare catalog ids to the subscription-pinned opencode provider —
        # a bare "glm-5.2" would leave provider resolution to opencode and can
        # land off the Z.AI Coding Plan sub. Explicit provider-prefixed ids
        # pass through untouched. Keep in sync with
        # scripts/ai_agent_bridge/_opencode.py GLM_MODEL.
        invocation_model = _OPENCODE_MODEL_ROUTES.get(target_model, target_model)

        cmd: list[str] = [binary, "run", "--model", invocation_model]

        if mode in ("workspace-write", "danger"):
            cmd.append("--auto")

        effective_effort = effort or self.default_effort
        variant = _EFFORT_TO_VARIANT.get(effective_effort, effective_effort)
        cmd.extend(["--variant", variant])

        cmd.append("--")
        cmd.append(prompt)

        _logger.debug(
            "glm invocation: task=%s mode=%s model=%s effort=%s",
            task_id,
            mode,
            target_model,
            effective_effort,
        )

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload="",
            output_file=None,
            env_overrides={"OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX": "131072"},
            liveness_paths=self._liveness_paths(),
        )

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None = None,
        plan: InvocationPlan | None = None,
        call_start_time: float | None = None,
    ) -> ParseResult:
        _ = (output_file, call_start_time)
        rate_limited = bool(_RATE_LIMIT_RE.search(f"{stderr or ''}\n{stdout or ''}"))
        text = _extract_text_from_stdout(stdout)

        from ai_agent_bridge._opencode import read_opencode_turn_status

        cwd = plan.cwd if plan is not None else None
        turn_status = read_opencode_turn_status(stdout, cwd=cwd)

        usable = bool(text) and turn_status.outcome == "completed"
        ok = returncode == 0 and usable and not rate_limited

        stderr_excerpt: str | None = None
        if not ok:
            if turn_status.outcome in ("permission_rejected", "aborted") or (
                returncode == 0 and turn_status.outcome != "completed"
            ):
                stderr_excerpt = f"opencode turn aborted ({turn_status.outcome}/{turn_status.reason})"
            else:
                source = (stderr or "").strip() or (stdout or "").strip() or ""
                stderr_excerpt = source[:500] if source else f"opencode exit code {returncode}"

        return ParseResult(
            ok=ok,
            response=text if ok else "",
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
            session_id=turn_status.session_id,
            tokens=None,
            tool_calls=[],
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        _ = plan
        return self._liveness_paths()

    def _liveness_paths(self) -> tuple[Path, ...]:
        opencode_dir = Path.home() / ".config" / "opencode"
        return (opencode_dir,) if opencode_dir.exists() else ()
