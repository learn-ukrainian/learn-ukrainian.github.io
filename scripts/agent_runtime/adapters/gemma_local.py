"""GemmaLocalAdapter — local MLX-backed Gemma 4 smoke lane.

This adapter is intentionally non-production. It is for cheap prompt/pipeline
smoke runs when we want a fast local sanity check before spending Gemini quota.

Issue: #1284
"""
from __future__ import annotations

import re
from pathlib import Path

from ..result import ParseResult
from .base import InvocationPlan

_RATE_LIMIT_RE = re.compile(
    r"(rate limit|quota exceeded|too many requests|\b429\b)",
    re.IGNORECASE,
)


class GemmaLocalAdapter:
    """Adapter for the local Gemma 4 MLX smoke-writer CLI."""

    name: str = "gemma-local"
    default_model: str = "mlx-community/gemma-4-e4b-it-4bit"
    supported_modes: frozenset[str] = frozenset(
        {"read-only", "workspace-write", "danger"},
    )

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
        _ = mode
        _ = task_id
        _ = session_id
        _ = effort  # Gemma local lane has no effort knob; silently ignore.
        tc = tool_config or {}
        python_bin = Path(
            tc.get(
                "python_bin",
                str(Path.home() / ".venvs/gemma4-mlx/bin/python"),
            )
        )
        cli_script = Path(__file__).resolve().parent.parent / "gemma_local_cli.py"
        cmd = [
            str(python_bin),
            str(cli_script),
            "--model",
            model or self.default_model,
            "--max-tokens",
            str(int(tc.get("max_tokens", 4096))),
            "--temp",
            str(float(tc.get("temp", 1.0))),
            "--top-p",
            str(float(tc.get("top_p", 0.95))),
            "--top-k",
            str(int(tc.get("top_k", 64))),
        ]
        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt,
            output_file=None,
            env_overrides={},
            liveness_paths=(),
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
        _ = output_file
        _ = plan
        _ = call_start_time
        combined = f"{stdout}\n{stderr}"
        rate_limited = bool(_RATE_LIMIT_RE.search(combined))
        ok = returncode == 0 and bool(stdout.strip()) and not rate_limited
        stderr_excerpt = None
        if not ok:
            excerpt_source = stderr.strip() or stdout.strip() or ""
            stderr_excerpt = excerpt_source[:500] or None
        return ParseResult(
            ok=ok,
            response=stdout.strip() if ok else "",
            stderr_excerpt=stderr_excerpt,
            rate_limited=rate_limited,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        _ = plan
        return ()
