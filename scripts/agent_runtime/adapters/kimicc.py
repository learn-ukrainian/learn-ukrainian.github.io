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

from scripts.review.model_catalog import (
    ModelCatalogError,
    kimi_model_aliases,
    load_model_catalog,
    resolve_kimi_model,
)

from ..read_only_tmp import validate_read_only_tmp_root
from ..result import ParseResult
from ..trail_isolation import (
    TrailIsolationError,
    assert_trail_isolation_config,
    trail_isolation_requested,
)
from .base import InvocationPlan
from .claude import ClaudeAdapter, _default_claude_bin, _ensure_supported_claude_cli_version

_HEADLESS_WRAPPER = Path(__file__).resolve().parents[1] / "kimicc_headless.sh"
# Keys delegate.py adds on read-only and review attempts. Agent-specific
# homes (codex/agy) are ignored here; rejecting them would make a shared
# review tool_config unusable on this harness.
_DELEGATE_READ_ONLY_AND_REVIEW_KEYS = frozenset(
    {
        "agy_home_override",
        "attempt_id",
        "codex_home_override",
        "mcp_server_names",
        "read_only_tmp_root",
        "review_id",
    }
)
_SUPPORTED_TOOL_CONFIG_KEYS = (
    frozenset(
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
    | _DELEGATE_READ_ONLY_AND_REVIEW_KEYS
)
_TRAIL_ISOLATION_TOOL_CONFIG_KEYS = (
    frozenset(
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
    | _DELEGATE_READ_ONLY_AND_REVIEW_KEYS
)


def kimicc_routable_model_ids(catalog: dict[str, Any] | None = None) -> tuple[str, ...]:
    """Canonical ids listed on the catalog's kimicc endpoint, in catalog order."""
    source = catalog or load_model_catalog()
    raw = source["review_scheduler"]["endpoints"]["kimicc"].get("models", [])
    if not isinstance(raw, list) or not raw or not all(isinstance(item, str) and item.strip() for item in raw):
        raise ValueError("KimiccHarness: catalog kimicc endpoint lists no routable models")
    return tuple(item.strip() for item in raw)


def kimicc_default_model(catalog: dict[str, Any] | None = None) -> str:
    """Omitted ``--model`` on kimicc. The first routable endpoint id (kimi-code/k3 today)."""
    return kimicc_routable_model_ids(catalog)[0]


def kimicc_routable_aliases(catalog: dict[str, Any] | None = None) -> frozenset[str]:
    """Every alias that resolves to a model on the kimicc endpoint."""
    source = catalog or load_model_catalog()
    routable_ids = set(kimicc_routable_model_ids(source))
    names = set(routable_ids)
    for alias, model_id in kimi_model_aliases(source).items():
        if model_id in routable_ids:
            names.add(alias)
    return frozenset(names)


def resolve_kimicc_dispatch_model(model: str | None, catalog: dict[str, Any] | None = None) -> str:
    """Model id for a kimicc dispatch. Blank means the catalog default, not native k3-256k."""
    if model is None or not str(model).strip():
        return kimicc_default_model(catalog)
    return str(model).strip()


class KimiccHarness:
    """Build a stateless Claude Code invocation routed through KimiCC."""

    name = "kimicc"
    # First routable id on the catalog kimicc endpoint. Not the native k3-256k default.
    default_model = kimicc_default_model()
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

        requested_model = resolve_kimicc_dispatch_model(model)
        try:
            model_id, route = resolve_kimi_model(requested_model)
        except ModelCatalogError as exc:
            raise ValueError(f"KimiccHarness: {exc}") from exc
        if model_id not in kimicc_routable_model_ids():
            raise ValueError(
                "KimiccHarness: "
                f"{requested_model!r} is not a routable kimicc model in the catalog "
                f"(resolved {model_id!r}). "
                "The coding endpoint rejects unverified ids such as k3-256k "
                "([claude-code:unrecognized_model], #8745). "
                f"Routable models: {list(kimicc_routable_model_ids())}."
            )
        coding_model_id = route.get("coding_model_id")
        if not isinstance(coding_model_id, str) or not coding_model_id.strip():
            raise ValueError(f"KimiccHarness: catalog model {model_id!r} has no coding_model_id")

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
        # Same order as CodexAdapter: refuse a bad read-only lease before any
        # CLI probe, next to the isolation checks above.
        read_only_tmp = validate_read_only_tmp_root(tc, cwd, mode, adapter="KimiccHarness")

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
        elif tc.get("strict_mcp_config") and isinstance(tc.get("mcp_config_path"), str):
            cmd.extend(["--mcp-config", str(tc["mcp_config_path"]), "--strict-mcp-config"])
            if tc.get("allowed_tools"):
                cmd.extend(["--allowedTools", str(tc["allowed_tools"])])
        elif isinstance(tc.get("mcp_config_path"), str) and tc.get("allowed_tools"):
            # Read-only kimicc reviews. --bare does not load .mcp.json, so the
            # dispatch passes the checkout file Claude reviews discover, plus
            # the sources --allowedTools grant. Write modes do not set these.
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

        env_overrides = {"KIMICC_CLAUDE_BIN": claude_bin}
        if read_only_tmp is not None:
            env_overrides["TMPDIR"] = str(read_only_tmp)
        if effective_effort:
            # The wrapper derives Claude Code's environment default from this
            # value. Mirror the exact child argv so an explicit override does
            # not depend on undocumented environment-versus-flag precedence.
            env_overrides["KIMICC_EFFORT_LEVEL"] = effective_effort

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            env_overrides=env_overrides,
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
