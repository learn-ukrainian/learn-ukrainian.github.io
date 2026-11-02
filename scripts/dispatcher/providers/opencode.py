"""DeepSeek V4.1 Flash through OpenCode, on the direct DeepSeek API (default) or OpenRouter."""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path

from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec

# OpenCode allows edits and every shell command by default and has no OS sandbox, so read-only
# carries its own permission rules (https://opencode.ai/docs/permissions/): ``edit`` covers the
# edit, write and patch tools, and for bash the last matching pattern wins. Only read-only git
# forms run; a redirect, or an option that writes a file or starts an external diff program, stays
# denied (a redirect is not a separate command, so ``git log *`` alone would admit ``> file``). OpenCode
# merges ``OPENCODE_PERMISSION`` over the loaded config's ``permission``.
_READ_ONLY_PERMISSION = json.dumps(
    {
        "edit": "deny",
        "task": "deny",
        "bash": {
            "*": "deny",
            **{f"git {verb}{rest}": "allow" for verb in ("diff", "log", "show", "status") for rest in ("", " *")},
            "* --output*": "deny",
            "* --ext-diff*": "deny",
            "*>*": "deny",
        },
    },
    separators=(",", ":"),
)


# The endpoint is chosen explicitly with ``--provider`` and recorded on the task record; nothing
# switches it. Both run V4.1 Flash only (core P2). The OpenRouter route is pinned to the V4.1 Flash
# line and to the US provider allow-list in model-assignment.md, with no provider fallback.
DEFAULT_ENDPOINT = "deepseek"
MODELS = {"deepseek": "deepseek/deepseek-flash", "openrouter": "openrouter/deepseek/deepseek-v4.1-flash"}
OPENROUTER_PROVIDERS = ("fireworks/us", "baseten/us", "inference-net/us")
_OPENROUTER_MODEL_ID = MODELS["openrouter"].removeprefix("openrouter/")
_ROUTING = {"only": list(OPENROUTER_PROVIDERS), "allow_fallbacks": False, "data_collection": "deny"}
# OpenCode deep-merges this over the operator's and the checkout's config, and the merge keeps
# inherited keys (https://opencode.ai/docs/config/). So it pins what decides each call: only the
# OpenRouter provider is enabled and only the pinned model exists on it, under its own id. Routing
# sits in the model options (title calls) and the high variant, which OpenCode applies last. The
# title, summary and compaction agents use the same model. Whatever this cannot pin is checked on
# the resolved config before spawn (``_config_conflict``).
_OPENROUTER_PROVIDER = {
    "whitelist": [_OPENROUTER_MODEL_ID],
    "models": {_OPENROUTER_MODEL_ID: {
        "id": _OPENROUTER_MODEL_ID, "options": {"provider": _ROUTING}, "variants": {"high": {"provider": _ROUTING}},
    }},
}
_PINNED_AGENTS = ("build", "title", "summary", "compaction")
_OPENROUTER_CONFIG = json.dumps(
    {
        "enabled_providers": ["openrouter"],
        "small_model": MODELS["openrouter"],
        "agent": {name: {"model": MODELS["openrouter"]} for name in _PINNED_AGENTS},
        "provider": {"openrouter": _OPENROUTER_PROVIDER},
    },
    separators=(",", ":"),
)
# OpenCode merges a checkout's own config files and directory below the injected config.
_PROJECT_CONFIG = ("opencode.json", "opencode.jsonc", ".opencode")
_BUDGETS = Path(__file__).resolve().parents[2] / "config" / "agent_budgets.yaml"
_PROBE_TIMEOUT_S = 10.0
_CONFIG_TIMEOUT_S = 60.0


def endpoint(provider: str | None) -> str:
    """The endpoint a ``--provider`` value selects; an unknown one is refused, never mapped."""
    selected = provider or DEFAULT_ENDPOINT
    if selected not in MODELS:
        raise ValueError(f"opencode_endpoint_unknown: --provider {provider!r}; use one of {', '.join(MODELS)}")
    return selected


def _remaining_usd(selected: str, key: str) -> float | None:
    """The endpoint's remaining prepaid USD, or None when it cannot be read. Keys are never logged."""
    from scripts.api import subscription_usage as usage

    if selected == "deepseek":
        account = usage._probe_deepseek_native(timeout_s=_PROBE_TIMEOUT_S)
        if account.get("probe_state") != "ok" or str(account.get("currency") or "").upper() != "USD":
            return None
        return 0.0 if account.get("is_available") is False else account.get("total_balance")
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    status, payload, _ = usage._http_json_request(
        "GET", "https://openrouter.ai/api/v1/credits", headers=headers, timeout_s=_PROBE_TIMEOUT_S
    )
    data = payload.get("data") if isinstance(payload, dict) else None
    if status != 200 or not isinstance(data, dict):
        return None
    total, used = (usage._coerce_float(data.get(name)) for name in ("total_credits", "total_usage"))
    if total is None or used is None:
        return None
    # A key spending cap can be lower than the account balance.
    status, payload, _ = usage._http_json_request(
        "GET", "https://openrouter.ai/api/v1/key", headers=headers, timeout_s=_PROBE_TIMEOUT_S
    )
    data = payload.get("data") if isinstance(payload, dict) else None
    if status != 200 or not isinstance(data, dict):
        return None
    # OpenRouter reports a key without a cap as both fields null; anything else unreadable is unknown.
    if "limit" not in data or "limit_remaining" not in data:
        return None
    if data["limit"] is None and data["limit_remaining"] is None:
        return total - used
    cap = usage._coerce_float(data["limit_remaining"])
    return None if cap is None else min(total - used, cap)


def _config_conflict(resolved: object) -> str | None:
    """Why OpenCode's resolved config could reach another model or provider route, or None."""
    if not isinstance(resolved, dict):
        return "the resolved config could not be read"
    if resolved.get("enabled_providers") != ["openrouter"]:
        return "enabled_providers is overridden"
    if resolved.get("plugin"):
        return "a plugin is configured"
    if resolved.get("small_model") != MODELS["openrouter"]:
        return "small_model is overridden"
    if (resolved.get("provider") or {}).get("openrouter") != _OPENROUTER_PROVIDER:
        return "the openrouter provider block is overridden"
    for kind in ("agent", "mode"):
        entries = resolved.get(kind) or {}
        if not isinstance(entries, dict):
            return f"{kind} could not be read"
        for name, entry in entries.items():
            # Agent options are merged over the model's routing options on every call.
            if not isinstance(entry, dict) or entry.get("options"):
                return f"{kind} {name!r} sets request options"
            if name in _PINNED_AGENTS and entry.get("model", MODELS["openrouter"]) != MODELS["openrouter"]:
                return f"{kind} {name!r} sets another model"
    return None


def _resolved_config(env: dict[str, str]) -> object:
    """OpenCode's resolved config under the OpenRouter launch environment, or None. Never logged."""
    try:
        done = subprocess.run(
            ["opencode", "debug", "config"], env={**env, "OPENCODE_CONFIG_CONTENT": _OPENROUTER_CONFIG},
            cwd=env.get("HOME") or Path.home(), capture_output=True, text=True, timeout=_CONFIG_TIMEOUT_S, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    try:
        return json.loads(done.stdout) if done.returncode == 0 else None
    except ValueError:
        return None


def _project_config(worktree: Path, repo: Path | None, sha: str | None) -> list[str] | None:
    """The checkout's OpenCode config paths (existing directory or start commit), or None when unreadable."""
    found = [name for name in _PROJECT_CONFIG if (worktree / name).exists()]
    if repo is not None and sha:
        try:
            done = subprocess.run(
                ["git", "-C", str(repo), "ls-tree", "--name-only", sha, "--", *_PROJECT_CONFIG],
                capture_output=True, text=True, timeout=_CONFIG_TIMEOUT_S, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if done.returncode:
            return None
        found += done.stdout.split()
    return sorted(set(found))


def endpoint_refusal(
    provider: str | None, env: dict[str, str] | None = None, *,
    worktree: Path | None = None, repo: Path | None = None, sha: str | None = None,
) -> str | None:
    """The typed refusal for the selected endpoint before spawn, or None when it may run.

    An endpoint with no configured access, an unreadable balance or a balance below its
    ``dispatch_floor_usd`` is refused; the other endpoint is never tried instead. The OpenRouter
    endpoint is also refused when the checkout carries OpenCode config or the resolved config
    could still route a call off the pinned model or provider allow-list.
    """
    import yaml

    from scripts.api import subscription_usage as usage

    selected = endpoint(provider)
    loader = usage._load_deepseek_api_key if selected == "deepseek" else usage._load_openrouter_api_key
    key = loader()
    if not key:
        return f"opencode_endpoint_no_access: {selected} has no configured API key"
    if selected == "openrouter":
        project = _project_config(worktree, repo, sha) if worktree is not None else []
        if project is None:
            return "opencode_endpoint_config_conflict: openrouter: the checkout's OpenCode config could not be read"
        if project:
            return f"opencode_endpoint_config_conflict: openrouter: the checkout carries OpenCode config {', '.join(project)}"
        if conflict := _config_conflict(_resolved_config(env or {})):
            return f"opencode_endpoint_config_conflict: openrouter: {conflict}"
    floor = float((yaml.safe_load(_BUDGETS.read_text(encoding="utf-8")) or {})[selected]["dispatch_floor_usd"])
    remaining = _remaining_usd(selected, key)
    if not isinstance(remaining, (int, float)) or isinstance(remaining, bool) or not math.isfinite(remaining):
        return f"opencode_endpoint_balance_unknown: {selected} balance could not be read"
    if remaining < floor:
        return f"opencode_endpoint_below_floor: {selected} balance ${remaining:.2f} is below the ${floor:.2f} floor"
    return None


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    selected = endpoint(spec.provider)
    argv = ["opencode", "run", "--model", MODELS[selected], "--format", "json", "--variant", "high"]
    child_env = env.copy()
    if selected == "openrouter":
        child_env["OPENCODE_CONFIG_CONTENT"] = _OPENROUTER_CONFIG
    if spec.mode == "workspace-write":
        argv.append("--auto")
    elif spec.mode == "read-only":
        child_env["OPENCODE_PERMISSION"] = _READ_ONLY_PERMISSION
    else:
        raise ValueError(f"opencode: unsupported mode {spec.mode!r}")
    argv += ["--", spec.prompt_file.read_text(encoding="utf-8")]
    return Invocation(argv, None, child_env, None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    text, chunks, usage, reason = None, [], None, None
    error = f"opencode exited with code {returncode}" if returncode else None
    for line in jsonl_lines(stdout):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        part = event.get("part") or {}
        if not isinstance(part, dict):
            part = {}
        if kind == "error" or event.get("error") is not None:
            error = error or "opencode terminal error"
        if kind == "text" and isinstance(part.get("text"), str):
            chunks.append(part["text"])
        elif chunks and kind in ("tool", "tool_use", "step_start", "step_finish", "step-start", "step-finish"):
            text, chunks = "".join(chunks).strip(), []
        if kind in ("step_finish", "step-finish") or part.get("type") in ("step_finish", "step-finish"):
            reason = part.get("reason") or event.get("reason")
            if reason not in ("stop", "completed", "tool-calls"):
                error = error or "opencode terminal failure"
            if isinstance(part.get("tokens"), dict):
                usage = part["tokens"]
        state = part.get("state")
        rejected = ("rejected", "cancelled", "permission_denied", "permission_rejected")
        if kind in ("tool", "tool_use") and isinstance(state, dict) and state.get("status") in rejected:
            error = error or "opencode tool permission rejected"
    text = "".join(chunks).strip() if chunks else text
    if reason is not None and reason not in ("stop", "completed"):
        error = error or "opencode incomplete terminal outcome"
    return ParsedResult(text or None, usage, error or (None if text else "opencode missing final response"))
