"""Kimi K3 through the headless Claude Code harness.

The wrapper performs catalog, profile, guard, and credential resolution at
spawn. In particular, OAuth stays out of ``InvocationPlan.env_overrides`` so a
fresh token is exported only to the Claude Code child. ``--bare`` intentionally
makes this stateless: long calls must be relaunched before the roughly
15-minute Kimi OAuth access-token lifetime.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from scripts.review.model_catalog import ModelCatalogError, resolve_kimi_model

from ..result import ParseResult
from ..trail_isolation import (
    TrailIsolationError,
    assert_trail_isolation_config,
    trail_isolation_requested,
)
from .base import InvocationPlan
from .claude import ClaudeAdapter, _default_claude_bin, _ensure_supported_claude_cli_version

_HEADLESS_WRAPPER = Path(__file__).resolve().parents[1] / "kimicc_headless.sh"
_SUPPORTED_TOOL_CONFIG_KEYS = frozenset(
    {
        "agent",
        "allowed_tools",
        "max_budget_usd",
        "mcp_config_path",
        "tools",
        "strict_mcp_config",
        "setting_sources",
        "trail_isolation",
        "trail_isolation_cwd",
        "runtime_route",
    }
)
_TRAIL_ISOLATION_TOOL_CONFIG_KEYS = frozenset(
    {
        "allowed_tools",
        "harness",
        "mcp_config_path",
        "setting_sources",
        "strict_mcp_config",
        "tools",
        "trail_isolation",
        "trail_isolation_cwd",
    }
)


class KimiccHarness:
    """Build a stateless Claude Code invocation routed through KimiCC."""

    name = "kimicc"
    default_model = "k3"
    supported_modes = frozenset({"read-only", "workspace-write", "danger"})

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
        if mode not in self.supported_modes:
            raise ValueError(f"KimiccHarness: unsupported mode {mode!r}")
        if session_id is not None:
            raise ValueError("KimiccHarness is stateless (--bare) and does not support session resume")
        if not _HEADLESS_WRAPPER.is_file():
            raise RuntimeError(f"KimiccHarness wrapper not found: {_HEADLESS_WRAPPER}")

        requested_model = model or self.default_model
        try:
            _, route = resolve_kimi_model(requested_model)
        except ModelCatalogError as exc:
            raise ValueError(f"KimiccHarness: {exc}") from exc

        tc: dict[str, Any] = tool_config or {}
        if tc.get("review_isolation"):
            raise ValueError("KimiccHarness does not support sealed review isolation")
        trail_isolation = trail_isolation_requested(tc)
        if trail_isolation:
            if mode != "read-only":
                raise TrailIsolationError("KimiCC trail isolation requires mode='read-only'")
            assert_trail_isolation_config(tc, profile="kimicc")
            unsupported = sorted(set(tc) - _TRAIL_ISOLATION_TOOL_CONFIG_KEYS)
            if unsupported:
                raise TrailIsolationError(
                    f"KimiCC trail isolation refuses incompatible tool_config keys: {unsupported}"
                )
        unsupported = sorted(set(tc) - _SUPPORTED_TOOL_CONFIG_KEYS - {"harness"})
        if unsupported:
            raise ValueError(f"KimiccHarness: unsupported tool_config keys: {unsupported}")

        # The headless wrapper invokes the native Claude binary itself, but
        # resolve it here so a missing harness fails before a task is spawned.
        claude_bin = _default_claude_bin() or shutil.which("claude")
        if not claude_bin:
            raise RuntimeError("KimiccHarness requires the native `claude` CLI on PATH")
        _ensure_supported_claude_cli_version((claude_bin,))

        cmd = [
            str(_HEADLESS_WRAPPER),
            "--model",
            route["kimicc_alias"],
            "--mode",
            mode,
            "--prompt",
            prompt,
        ]
        if trail_isolation:
            cmd.extend(
                [
                    "--mcp-config",
                    str(tc["mcp_config_path"]),
                    "--allowedTools",
                    str(tc["allowed_tools"]),
                    "--tools",
                    str(tc["tools"]),
                    "--strict-mcp-config",
                    "--setting-sources",
                    str(tc["setting_sources"]),
                ]
            )
        elif isinstance(tc.get("mcp_config_path"), str) and tc.get("allowed_tools"):
            cmd.extend(["--mcp-config", str(tc["mcp_config_path"]), "--allowedTools", str(tc["allowed_tools"])])
        if tc.get("agent"):
            cmd.extend(["--agent", str(tc["agent"])])
        if tc.get("max_budget_usd") is not None:
            cmd.extend(["--max-budget-usd", f"{float(tc['max_budget_usd']):.2f}"])
        # KimiCC, unlike native Kimi Code, routes through Claude Code and
        # supports an invocation-scoped effort. K3's approved default is high;
        # an explicit runtime request remains the effective child argv value.
        effective_effort = effort or ("high" if route["kimicc_alias"] == "k3" else None)
        if effective_effort:
            cmd.extend(["--effort", effective_effort])

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            env_overrides={"KIMICC_CLAUDE_BIN": claude_bin},
            # --bare does not need or own a persistent Claude config. Removing
            # an inherited config keeps this headless route operator-config-free.
            env_unsets=("CLAUDE_CONFIG_DIR",),
            liveness_paths=(),
            metadata={
                "harness": "kimicc",
                "kimicc_alias": route["kimicc_alias"],
                "claude_bin": claude_bin,
                "task_id": task_id or "",
            },
        )

    def parse_response(self, **kwargs: Any) -> ParseResult:
        """Claude Code output uses the standard runtime stream-json contract."""
        return ClaudeAdapter().parse_response(**kwargs)

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        return tuple(plan.liveness_paths)
