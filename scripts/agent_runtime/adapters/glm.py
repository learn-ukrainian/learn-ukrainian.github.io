"""GlmAdapter — wraps opencode CLI for Zhipu GLM-5.2 (glm-5.2).

GLM-5.2 is a strong cross-family code and review model.
LOCAL-ONLY: prompt data egresses to China — forbidden in CI.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from ..result import ParseResult
from .base import InvocationPlan

_logger = logging.getLogger(__name__)


class GlmAdapter:
    """Adapter for the opencode CLI with glm-5.2."""

    name: str = "glm"
    default_model: str = "glm-5.2"
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
        binary = shutil.which("opencode") or "opencode"
        target_model = model or self.default_model

        cmd = [binary, "run", "--model", target_model]
        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin=prompt,
            env_overrides={},
        )

    def parse_response(self, stdout: str, stderr: str, returncode: int) -> ParseResult:
        if returncode != 0:
            return ParseResult(
                ok=False,
                text="",
                error_message=stderr or stdout or f"opencode exit code {returncode}",
            )
        return ParseResult(
            ok=True,
            text=stdout.strip(),
        )
