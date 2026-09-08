"""Read-only CLI compatibility preflight for ACP routing (#7812).

Only version/help commands run here, never prompts or sessions.
Compatibility is not evidence of authentication, quota, or native dispatch
health. Probe each snapshot anew so repairing an executable restores the route.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .adapters import acpx


def probe_acp_health(cwd: Path) -> dict[str, dict[str, Any]]:
    """Return body-free admission health for the registered ACP participants.

    Shared runtime failure excludes every ACP lane immediately. Per-provider
    failures affect only routes that use that CLI. Unexpected probe errors are
    unknown and ineligible, never evidence of a healthy executable.
    """
    checked_at = datetime.now(UTC).isoformat()

    def result(*, code: str | None = None, unknown: bool = False) -> dict[str, Any]:
        return {
            "healthy": None if unknown else code is None,
            "eligible": code is None,
            "scope": "acp_cli_compatibility",
            "failure_code": code,
            "checked_at": checked_at,
        }

    participants = acpx.ACPX_SUPPORTED_PARTICIPANTS
    try:
        binary = acpx._resolve_acpx_binary(adapter_label="ACP routing", cwd=cwd)
        root_help = acpx._probe_cli_help(binary)
        if not root_help or any(flag not in root_help for flag in acpx._ACPX_REQUIRED_GLOBAL_FLAGS):
            raise acpx.AcpxShadowRefusalError("ACP root help unavailable", failure_code="cli_incompatible")
    except acpx.AcpxShadowRefusalError as exc:
        return {lane: result(code=exc.failure_code) for lane in participants}
    except Exception:
        return {lane: result(code="probe_unavailable", unknown=True) for lane in participants}

    # Generic exec is required only by custom-agent routes, not builtins.
    try:
        custom_exec_healthy = "--file" in acpx._probe_cli_help(binary, "exec")
    except acpx.AcpxShadowRefusalError:
        custom_exec_healthy = False
    except Exception:
        custom_exec_healthy = None
    # Several seats share OpenCode. Check its contract once per snapshot.
    providers: dict[str, dict[str, Any]] = {}
    for executable in set(acpx._PARTICIPANT_PROVIDER_BINARIES.values()):
        try:
            acpx._resolve_participant_binary(executable, adapter_label="ACP routing")
            providers[executable] = result()
        except acpx.AcpxShadowRefusalError as exc:
            providers[executable] = result(code=exc.failure_code)
        except Exception:
            providers[executable] = result(code="probe_unavailable", unknown=True)

    def probe(lane: str) -> tuple[str, dict[str, Any]]:
        try:
            executable = acpx._PARTICIPANT_PROVIDER_BINARIES.get(lane)
            if (executable or lane == "grok") and not custom_exec_healthy:
                unknown = custom_exec_healthy is None
                return lane, result(code="probe_unavailable" if unknown else "cli_incompatible", unknown=unknown)
            if executable:
                if lane == "agy":
                    acpx._require_text_agent(adapter_label="ACP routing")
                return lane, dict(providers[executable])
            if lane == "grok":
                grok = acpx._resolve_grok_binary()
                _, missing = acpx._probe_grok_cli_compatibility(grok)
                acpx._require_grok_profile()
            else:
                target = participants[lane]["agent"]
                help_text = acpx._probe_cli_help(binary, target, "exec")
                missing = not (f"{target} " in root_help and "--file" in help_text)
                if lane == "claude":
                    acpx._require_local_claude_acp_adapter(binary, adapter_label="ACP routing")
            return lane, result(code="cli_incompatible" if missing else None)
        except acpx.AcpxShadowRefusalError as exc:
            return lane, result(code=exc.failure_code)
        except Exception:
            return lane, result(code="probe_unavailable", unknown=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        return dict(pool.map(probe, participants))
