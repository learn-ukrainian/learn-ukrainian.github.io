"""DeepSeekAdapter — wraps opencode CLI for first-party DeepSeek (deepseek).

Operator 2026-08-13: DeepSeek dispatch routes through OpenCode to first-party
``api.deepseek.com`` with ``--variant high`` by default, replacing the Hermes
dispatch default so runs get native Entire capture. ``deepseek-v4.1-flash`` is
the default; ``deepseek-v4-pro`` is reachable via an explicit ``--model
deepseek-v4-pro`` for hard implement tasks (complex multi-file, hard lookup)
per the 2026-08-13 operator GO (canary #6703) — Pro is not the default and
stays off the routine review ladder. The Hermes adapter (``hermes_deepseek.py``)
stays available for ``ask-hermes`` only.

2026-09-24 (#8514): the opencode first-party provider id is ``deepseek``
(models: ``deepseek-flash``, ``deepseek-v4-pro``); the original
``deepseek-direct/*`` pin resolves to ``ProviderModelNotFoundError`` on
opencode 1.18.x and failed every dispatch at start.

LOCAL-ONLY: prompt data egresses to China — forbidden in CI (same guard as
the Hermes route, via ``scripts.agent_runtime.routes``).
"""

from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path

from ..result import ParseResult
from ..routes import (
    deepseek_first_party_error,
    is_deepseek_first_party_forbidden_in_ci,
)
from ..trail_isolation import TrailIsolationError, trail_isolation_requested
from .base import InvocationPlan

_logger = logging.getLogger(__name__)

# Bare catalog model id → first-party opencode provider route. Flash is the
# dispatch default; Pro stays reachable only via an explicit --model override.
# Provider id ``deepseek`` is opencode's first-party api.deepseek.com provider
# (#8514: ``deepseek-direct`` does not exist on opencode 1.18.x).
DEEPSEEK_OPENCODE_MODEL_ROUTES: dict[str, str] = {
    "deepseek-v4.1-flash": "deepseek/deepseek-flash",
    "deepseek-v4-pro": "deepseek/deepseek-v4-pro",
}


def _cached_flash_name() -> str | None:
    """Read OpenCode's optional models.dev cache without refreshing it."""
    try:
        cache = json.loads(
            (Path.home() / ".cache" / "opencode" / "models.json").read_text(encoding="utf-8")
        )
        name = cache["deepseek"]["models"]["deepseek-flash"]["name"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return name if isinstance(name, str) else None

_RATE_LIMIT_RE = re.compile(
    r"rate limit|rate_limit|usage limit|quota exceeded|too many requests|resource_exhausted|\b429\b",
    re.IGNORECASE,
)

# Same uniform-effort → opencode variant mapping as GlmAdapter.
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


class DeepSeekAdapter:
    """Adapter for the opencode CLI with first-party DeepSeek."""

    name: str = "deepseek"
    # Fleet MODEL identity (bare catalog id). The ``deepseek`` provider pin
    # is an opencode INVOCATION detail — applied in build_invocation via
    # DEEPSEEK_OPENCODE_MODEL_ROUTES, not stored as identity.
    default_model: str = "deepseek-v4.1-flash"
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
                "trail isolation refused for DeepSeek: opencode does not enforce tool restrictions"
            )

        if mode not in self.supported_modes:
            raise ValueError(f"DeepSeekAdapter: unsupported mode {mode!r} (supported: {sorted(self.supported_modes)})")

        max_budget_usd = (tool_config or {}).get("max_budget_usd")
        if max_budget_usd is not None:
            _logger.warning(
                "non-claude adapter %s ignoring max_budget_usd=%s; use hard-timeout/silence-timeout instead",
                self.name,
                max_budget_usd,
            )

        binary = shutil.which("opencode") or "opencode"
        target_model = model or self.default_model
        if target_model in {
            "deepseek-v4-flash",
            "deepseek-v4-flash-legacy",
            "deepseek/deepseek-v4-flash",
        }:
            raise ValueError(
                "deepseek-v4-flash is retired for historical records; "
                "use deepseek-v4.1-flash for new first-party dispatches"
            )
        # Route bare catalog ids to the first-party opencode provider — a bare
        # "deepseek-v4.1-flash" would leave provider resolution to opencode and
        # can land off the api.deepseek.com account. Explicit provider-prefixed
        # ids pass through untouched.
        invocation_model = DEEPSEEK_OPENCODE_MODEL_ROUTES.get(target_model, target_model)
        if invocation_model == "deepseek/deepseek-flash":
            cached_name = _cached_flash_name()
            if cached_name is not None and cached_name != "DeepSeek V4.1 Flash":
                raise ValueError(
                    "deepseek/deepseek-flash alias drift: cached models.dev name "
                    f"is {cached_name!r}, expected 'DeepSeek V4.1 Flash'"
                )

        if is_deepseek_first_party_forbidden_in_ci("deepseek", invocation_model):
            raise ValueError(
                deepseek_first_party_error(
                    provider="deepseek",
                    model=invocation_model,
                    source="opencode deepseek adapter",
                )
            )

        cmd: list[str] = [binary, "run", "--model", invocation_model, "--format", "json"]

        if mode in ("workspace-write", "danger"):
            cmd.append("--auto")

        effective_effort = effort or self.default_effort
        variant = _EFFORT_TO_VARIANT.get(effective_effort, effective_effort)
        cmd.extend(["--variant", variant])

        cmd.append("--")
        cmd.append(prompt)

        _logger.debug(
            "deepseek invocation: task=%s mode=%s model=%s effort=%s",
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

        try:
            from scripts.ai_agent_bridge._opencode import _parse_opencode_stream, read_opencode_turn_status
        except ModuleNotFoundError:  # pragma: no cover - direct-script runs with only scripts/ on sys.path
            from ai_agent_bridge._opencode import _parse_opencode_stream, read_opencode_turn_status

        # Invocation pins --format json: stdout is an NDJSON event stream, so
        # the reply is the LAST assistant text part (#8514 — under the runner's
        # PTY, opencode 1.18.x writes the whole formatted transcript to stderr
        # and leaves stdout empty; the plain-text extraction below only serves
        # legacy/non-JSON output).
        text = _extract_text_from_stdout(_parse_opencode_stream(stdout).text)

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
