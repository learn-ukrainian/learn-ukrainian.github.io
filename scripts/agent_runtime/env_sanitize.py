"""Sanitize environment variables for spawned agent CLI processes.

Agent CLIs can run shell commands and inspect ``os.environ`` directly. The
runtime should therefore pass only ordinary process context plus the credential
for the provider being invoked, not the full orchestrator environment.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path

_SENSITIVE_NAME_RE = re.compile(
    r"TOKEN|SECRET|PASSWORD|PASSWD|PRIVATE|CREDENTIALS?|API_?KEY|"
    r"ACCESS_?KEY|AUTH|COOKIE",
    re.IGNORECASE,
)

_SENSITIVE_VALUE_RE = re.compile(
    r"(?:"
    r"github_pat_[A-Za-z0-9_]+|"
    r"gh[pousr]_[A-Za-z0-9_]+|"
    r"sk-[A-Za-z0-9_-]+|"
    r"xox[baprs]-[A-Za-z0-9-]+|"
    r"hf_[A-Za-z0-9_]+|"
    r"npm_[A-Za-z0-9_]+|"
    r"AKIA[A-Z0-9]{12,}|"
    r"AIza[A-Za-z0-9_-]+"
    r")"
)

_SAFE_NAME_ALLOWLIST = {
    "AGENT_ALLOW_MERGE",
    "AGENT_NO_MERGE",
    "HOME",
    "LANG",
    # Dispatch-worker identity markers (#7827): delegate.py exports these into
    # every worker environment; the SessionStart gate reads them to skip the
    # per-agent thread lease. Values are a task id and an agent lane name —
    # process-control metadata, never credentials.
    "LEARN_UKRAINIAN_DISPATCH_AGENT",
    "LEARN_UKRAINIAN_DISPATCH_TASK_ID",
    "LOGNAME",
    "PATH",
    "TMPDIR",
    "USER",
}

_SAFE_NAME_PREFIXES = (
    "AB_",
    "LC_",
    "LU_",
)

_GIT_TIMEOUT_SECONDS = 30
# `git config --unset-all` exit status when the key is not set.
_GIT_CONFIG_KEY_MISSING = 5

# Variables that could carry a push credential into a Kimi seat.
_PUSH_CREDENTIAL_NAMES = (
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GH_ENTERPRISE_TOKEN",
    "GITHUB_ENTERPRISE_TOKEN",
    "LU_AGENT_GITHUB_TOKEN",
    "GIT_ASKPASS",
    "SSH_ASKPASS",
    "SSH_AUTH_SOCK",
)

# These are process-control paths, not credentials. A task id such as
# ``task-4956`` contains the substring ``sk-`` and otherwise looks like an
# OpenAI key to the generic value redactor, so keep the tmp lease controls
# before the value-pattern filter. Their names remain narrowly allowlisted.
# The #7827 dispatch markers ride here for the same reason: a task id
# containing ``sk-`` must still reach the worker's SessionStart gate.
_SAFE_VALUE_NAME_ALLOWLIST = {
    "LEARN_UKRAINIAN_DISPATCH_AGENT",
    "LEARN_UKRAINIAN_DISPATCH_TASK_ID",
    "TMPDIR",
    "LU_RUNTIME_TMP_BASE_ROOT",
    "LU_RUNTIME_TMP_ROOT",
    "LU_SCRATCH_ROOT",
    "LU_X_AGENT_TRAILER",
}

# Launcher metadata whose names resemble credentials. Session fencing and
# context capacities are decimal counters; Git author fields are identity text.
# The dispatcher still excludes this parent context and rebuilds Git identity.
_CHILD_COUNTER_NAMES = {
    "SESSION_STREAM_FENCING_TOKEN",
    "LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS",
    "LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS",
    "LEARN_UKRAINIAN_COLD_START_BUDGET_TOKENS",
    "LEARN_UKRAINIAN_EXPECTED_MAIN_CONTEXT_WINDOW_TOKENS",
}
_CHILD_IDENTITY_NAMES = {"GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL"}
_DRIVER_GITHUB_IDENTITY_NAMES = {
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GH_ENTERPRISE_TOKEN",
    "GITHUB_ENTERPRISE_TOKEN",
    "LU_AGENT_GITHUB_TOKEN",
    "LU_AGENT_GITHUB_APP_ID",
    "LU_AGENT_GITHUB_APP_INSTALLATION_ID",
    "LU_AGENT_GITHUB_APP_PRIVATE_KEY",
    "LU_AGENT_GITHUB_APP_PRIVATE_KEY_FILE",
}

# Claude Code's config directory. Only the Claude adapter's labelled-account
# override sets it for a claude run (#10619); see build_agent_env.
CLAUDE_CONFIG_DIR_ENV = "CLAUDE_CONFIG_DIR"
# Claude Code prefers a non-empty legacy global config in that directory over
# its ``.claude.json``.
CLAUDE_LEGACY_GLOBAL_CONFIG = ".config.json"
# Linux managed policy, and the remote policy cache in the config directory.
_CLAUDE_MANAGED_SETTINGS_DIR = Path("/etc/claude-code")
_CLAUDE_REMOTE_SETTINGS = "remote-settings.json"
# The launch guard's exit status when the bound settings changed (EX_CONFIG).
CLAUDE_LAUNCH_GUARD_EXIT = 78

_PROVIDER_SECRET_ALLOWLIST = {
    "gemini": {
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "GOOGLE_GENERATIVE_AI_API_KEY",
    },
    "claude": {
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
    },
    "codex": {
        "CODEX_API_KEY",
        "OPENAI_API_KEY",
    },
    "kimi": {
        # Passed only to the KimiCC wrapper, which resolves the final route at
        # spawn and exports ANTHROPIC_AUTH_TOKEN solely to its exec child.
        "KIMICC_AUTH_TOKEN",
        "MOONSHOT_API_KEY",
        "KIMI_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
    },
    "cursor": {
        "CURSOR_API_KEY",
    },
    "acpx-cursor-shadow": {
        "CURSOR_API_KEY",
    },
}

# Dispatcher seats eligible for the early injected GitHub identity.
# Gemini aliases are excluded from this intermediate stage (#7020).
# The final CLI child resolves GitHub identity through child_credential_env.
GITHUB_TOKEN_SEATS = {
    "bridge",
    "claude",
    "codex",
    "cursor",
    "deepseek",
    "glm",
    "grok",
    "grok-build",
    "grok-hermes",
    "kimi",
}

_PROVIDER_SAFE_NAME_ALLOWLIST = {
    "acpx-codex-shadow": {
        # Non-secret acpx@0.13.0 auth-method selector. The literal value "1"
        # chooses the existing Codex ChatGPT login; no credential is carried
        # in this variable.
        "ACPX_AUTH_CHAT_GPT",
        # Adapter-resolved installed CLI; codex-acp otherwise launches its
        # bundled Codex, which can lag native dispatch's model support (#9273).
        "CODEX_PATH",
    },
    "acpx-claude-shadow": {
        # Adapter-resolved host Claude Code; claude-agent-acp otherwise launches
        # its bundled Claude Code, which can lag the catalogued models (#10500).
        "CLAUDE_CODE_EXECUTABLE",
        # The seat's fixed effort; ACPX has no effort flag. Never a credential.
        "CLAUDE_CODE_EFFORT_LEVEL",
        # Headless switches, as for the claude provider (#9690, #10083).
        "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS",
        "CLAUDE_CODE_DISABLE_ADVISOR_TOOL",
        # Tool switches the seat sets because ACPX cannot pass a tool deny.
        "CLAUDE_CODE_DISABLE_CRON",
        "CLAUDE_CODE_DISABLE_WORKFLOWS",
    },
    "acpx-grok-shadow": {
        # acpx@0.13.0 treats this as a non-secret auth-method selector:
        # the literal value "1" chooses Grok's agent-managed cached_token
        # method. It is not a cached token or credential value. Real XAI
        # API-key selectors remain outside every allowlist and are stripped.
        "ACPX_AUTH_CACHED_TOKEN",
    },
    "acpx-kimi-shadow": {
        # Non-secret acpx auth-method selector for the existing Kimi login.
        "ACPX_AUTH_LOGIN",
    },
    "acpx-kimicc-shadow": {
        # KimiCC K3 uses the same existing Kimi login through its fixed route.
        "ACPX_AUTH_LOGIN",
    },
    "acpx-glm-shadow": {
        # Non-secret selector for OpenCode's advertised ACP method ID
        # ``opencode-login``. The literal value is constrained to ``1`` by
        # build_agent_env below and carries no credential material.
        "ACPX_AUTH_OPENCODE_LOGIN",
        # Fixed non-secret OpenCode policy JSON: all tools and permissions are
        # denied for the native ACP participant.
        "OPENCODE_CONFIG_CONTENT",
    },
    "acpx-gemma-shadow": {
        # Same OpenCode ACP auth selector and deny-all policy JSON as the GLM
        # seat; both values are non-secret (#6805).
        "ACPX_AUTH_OPENCODE_LOGIN",
        "OPENCODE_CONFIG_CONTENT",
    },
    "acpx-deepseek-shadow": {
        # Same OpenCode ACP auth selector and deny-all policy JSON as the GLM
        # seat — the DeepSeek seat rides the native opencode ACP transport
        # since the Hermes removal (#6805).
        "ACPX_AUTH_OPENCODE_LOGIN",
        "OPENCODE_CONFIG_CONTENT",
    },
    "gemini": {
        "GEMINI_AUTH_MODE",
    },
    # The Claude adapter disables background work (#9690) and the interactive
    # advisor (#10083) on every headless run. These are feature switches,
    # never credentials.
    "claude": {
        "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS",
        "CLAUDE_CODE_DISABLE_ADVISOR_TOOL",
    },
    # CODEX_HOME must reach the codex subprocess so the V7 writer's
    # scoped config (materialized by
    # `linear_pipeline._ensure_codex_writer_home`) actually takes
    # effect. Without this allowlist entry the sanitizer dropped the
    # `env_overrides["CODEX_HOME"]` set by the codex adapter, the
    # subprocess fell back to `~/.codex/config.toml`, and writers
    # discovered the user's globally-registered MCP servers (e.g.
    # `mcp__node_repl__js`) — see writer-isolation #2228 / #2230 +
    # the 2026-05-22 ab ask-codex `codex-node-repl-leak-2026-05-22`
    # diagnosis.
    "codex": {
        "CODEX_HOME",
    },
    # AGY_APP_DATA_DIR must reach the agy subprocess so a receipt-recording
    # review attempt (#8617) keeps its app data (OAuth token link, transcripts)
    # in the per-attempt scoped home. It is a directory path, never a
    # credential; `HOME` already passes the global safe-name allowlist.
    "agy": {
        "AGY_APP_DATA_DIR",
    },
    "deepseek": {
        "HERMES_HOME",
    },
    # ask-hermes seat (OpenCode owns the bare ``deepseek`` dispatch key).
    "hermes-deepseek": {
        "HERMES_HOME",
    },
    # Demoted Hermes Grok path (was bare "grok" before the native-seat rename).
    "grok-hermes": {
        "HERMES_HOME",
    },
    "qwen": {
        "HERMES_HOME",
    },
    "kimi": {
        # Native CLI executable override; it is a path, never a credential.
        "KIMI_CODE_BIN",
        # KimiCC resolves its route and OAuth token inside the headless wrapper
        # immediately before it execs Claude Code. These are route selectors or
        # local credential-file paths, not token values.
        "KIMICC_ENDPOINT",
        "KIMICC_MODEL",
        "KIMICC_BASE_URL",
        "KIMICC_EFFORT_LEVEL",
        "KIMICC_CLAUDE_BIN",
        "KIMI_CODE_CREDENTIALS_PATH",
        "KIMI_CODE_OAUTH_HOST",
        "KIMI_CODE_OAUTH_MARGIN",
        # The KimiCC harness runs headless Claude Code and sets these like the
        # Claude adapter (#9690, #10083). The provider name is "kimi" for both Kimi
        # harnesses, so build_agent_env admits them only from adapter overrides:
        # the native Kimi CLI plan never sets them.
        "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS",
        "CLAUDE_CODE_DISABLE_ADVISOR_TOOL",
    },
}


def unneeded_env_var_names(env: Mapping[str, str], provider: str, *, harness: str | None = None) -> list[str]:
    """Names to omit from dispatcher and interactive CLI child environments.

    Preserve the dispatcher's provider allowlists and GitHub seat policy.
    Codex's Claude Code transport alone needs its route-derived auth token.
    """
    dispatcher_keys = set().union(*_PROVIDER_SECRET_ALLOWLIST.values()) if provider == "dispatcher" else set()
    drop: list[str] = []
    for var_name in env:
        upper = var_name.upper()
        if provider != "dispatcher" and (
            upper == "GITHUB_TOKEN" or (upper == "GH_TOKEN" and provider.lower() not in GITHUB_TOKEN_SEATS)
        ):
            drop.append(var_name)
            continue
        if upper == "ANTHROPIC_AUTH_TOKEN" and _normalized_provider(provider) == "codex":
            if harness != "claude-code":
                drop.append(var_name)
            continue
        if not (upper.endswith("_API_KEY") or upper.endswith("APIKEY")):
            continue
        if upper in dispatcher_keys or _is_provider_secret(var_name, provider):
            continue
        drop.append(var_name)
    return drop


def without_unneeded_secrets(env: Mapping[str, str], provider: str, *, harness: str | None = None) -> dict[str, str]:
    """Copy ``env`` using the shared CLI child credential policy."""
    dropped = set(unneeded_env_var_names(env, provider, harness=harness))
    return {name: value for name, value in env.items() if name not in dropped}


def _normalized_provider(provider: str) -> str:
    """Map runtime provider names to sanitizer policy keys.

    Permanent seat aliases (``grok-build`` → ``grok``) resolve so historical
    call sites keep matching the native-seat policy.
    """
    from .agent_identity import normalize_seat

    bare = provider.removesuffix("-tools").lower()
    return normalize_seat(bare) or bare


def _is_safe_name(name: str) -> bool:
    upper = name.upper()
    return upper in _SAFE_NAME_ALLOWLIST or upper.startswith(_SAFE_NAME_PREFIXES)


def _is_safe_value_name(name: str) -> bool:
    return name.upper() in _SAFE_VALUE_NAME_ALLOWLIST


def _is_provider_secret(name: str, provider: str) -> bool:
    allowed = _PROVIDER_SECRET_ALLOWLIST.get(_normalized_provider(provider), set())
    return name.upper() in allowed


def _is_provider_safe_name(name: str, provider: str) -> bool:
    allowed = _PROVIDER_SAFE_NAME_ALLOWLIST.get(_normalized_provider(provider), set())
    return name.upper() in allowed


def _looks_sensitive_name(name: str) -> bool:
    return bool(_SENSITIVE_NAME_RE.search(name))


def _looks_sensitive_value(value: str) -> bool:
    return bool(_SENSITIVE_VALUE_RE.search(value))


# #8645 part B: delegate.py exports PYTEST_PLUGINS so a worker that copies CI's
# `--override-ini addopts=-v` still loads the xdist cap. The agent CLI env is
# rebuilt here, so the variable must be re-applied — but only the known plugin,
# and only inside a dispatch. Any other comma-separated entry is dropped.
_DISPATCH_MARKER_ENV = "LEARN_UKRAINIAN_DISPATCH_TASK_ID"
_DISPATCH_CAP_PLUGIN = "ci.pytest_dispatch_cap"


def _dispatch_pytest_plugins(raw: Mapping[str, str]) -> str | None:
    """Return the known cap plugin, or None when it must not reach the CLI.

    The dispatch marker has to be present. Other plugin names are never
    forwarded, so an inherited ``PYTEST_PLUGINS`` cannot inject arbitrary code.
    """
    if not raw.get(_DISPATCH_MARKER_ENV, "").strip():
        return None
    plugins = [part.strip() for part in raw.get("PYTEST_PLUGINS", "").split(",") if part.strip()]
    if _DISPATCH_CAP_PLUGIN not in plugins:
        return None
    return _DISPATCH_CAP_PLUGIN


def _dispatch_pytest_pythonpath(raw: Mapping[str, str]) -> str | None:
    """Return the PYTHONPATH entries that actually host the cap plugin, or None.

    #8795: ``ci.pytest_dispatch_cap`` only resolves via pyproject.toml's
    rootdir-relative ``pythonpath = ["scripts"]``, which is inactive for a
    pytest process rooted elsewhere. ``_build_worker_env`` adds the plugin's
    real ``scripts`` directory to PYTHONPATH so it resolves regardless; this
    mirrors ``_dispatch_pytest_plugins`` to carry only that entry through the
    same rebuild, gated the same way, rather than the raw inherited value —
    an ambient PYTHONPATH must not inject an unrelated import path here.
    """
    if _dispatch_pytest_plugins(raw) is None:
        return None
    entries = [part for part in raw.get("PYTHONPATH", "").split(os.pathsep) if part]
    kept = [entry for entry in entries if (Path(entry) / "ci" / "pytest_dispatch_cap.py").is_file()]
    return os.pathsep.join(kept) if kept else None


def usable_host_gh_config_dir(path: str | None) -> str | None:
    """Return ``path`` only when it holds real gh auth material.

    Pre-#7166 / token-mode sandboxes create empty ``GH_CONFIG_DIR`` directories.
    If a parent shell inherits one of those and a no-token child passes it
    through, ``gh`` reports "not logged into any GitHub hosts" even when
    ``$HOME/.config/gh/hosts.yml`` is valid (#7472 review seats, #7166 workers).
    Reject empty or missing ``hosts.yml`` so the child falls back to the
    HOME-default config dir. Never reads or logs token values.
    """
    if not path or _looks_sensitive_value(path):
        return None
    try:
        hosts = Path(path) / "hosts.yml"
        if hosts.is_file() and hosts.stat().st_size > 0:
            return path
    except OSError:
        return None
    return None


def _isolated_git_env(
    home: str | None,
    github_token: str | None,
    host_gh_config_dir: str | None = None,
    *,
    no_credentials: bool = False,
) -> dict[str, str]:
    """Git ``--global`` config isolation for spawned agent CLIs (issue #2842).

    A stray ``git config`` write from an agent subprocess can brick git for the
    main checkout AND every linked worktree at once (e.g. ``core.bare true`` on
    the shared config). Point the subprocess's **global** config at a throwaway
    **copy** of the real one, so commit identity (``user.name`` / ``user.email``)
    and other global settings stay readable, but ``git config --global`` writes
    land in the copy instead of the developer's ``~/.gitconfig``.

    The GitHub extra header is always neutralized in the child process,
    including values inherited from system or repository config — it is where
    an embedded ``AUTHORIZATION: basic ...`` header would leak.  When an
    identity token exists, credential helpers are neutralized too and Git
    obtains the identity via a tiny ``GIT_ASKPASS`` helper that reads only the
    injected ``GH_TOKEN``.  This keeps ordinary ``git push`` working without
    exposing the operator's macOS keychain.

    When NO identity token resolves (job-host workers and read-only review
    seats: the ops account is logged in via ``gh auth login`` and no
    GH_TOKEN/App material exists), the child must still be able to ``gh pr
    create`` / ``gh pr comment`` (#7166, #7472).  In that case the host gh auth
    chain is preserved: credential helpers stay in the copied config (so
    ``gh auth git-credential`` keeps working) and ``GH_CONFIG_DIR`` is NOT
    redirected to an empty sandbox — a *usable* host ``GH_CONFIG_DIR`` (one
    with ``hosts.yml``) passes through, otherwise gh falls back to its default
    under the already-preserved ``HOME``.  Empty prior-sandbox dirs are
    rejected so nested dispatches recover.  No token value is ever logged or
    copied; gh reads its own ``hosts.yml`` at call time.

    ``no_credentials`` (Kimi seats) neutralizes credential helpers and points
    ``GH_CONFIG_DIR`` at an empty sandbox like the token case, but installs no
    ``GIT_ASKPASS``: the child has no GitHub credential at all.

    Never raises for other seats: isolation failure must not block spawning an
    agent. With ``no_credentials`` any failure raises ``OSError`` or
    ``subprocess.TimeoutExpired`` instead: an agent without credential
    isolation is not launched.
    """
    sandbox_dir: Path | None = None
    try:
        sandbox_dir = Path(tempfile.mkdtemp(prefix="lu-agent-runtime-git-"))
        sandbox_global = sandbox_dir / "agent.gitconfig"
        real_global = Path(
            os.environ.get("GIT_CONFIG_GLOBAL") or ((Path(home) if home else Path.home()) / ".gitconfig")
        )
        if real_global.is_file():
            shutil.copyfile(real_global, sandbox_global)
        elif not sandbox_global.exists():
            sandbox_global.write_text("", encoding="utf-8")
        strip_helpers = bool(github_token) or no_credentials
        keys_to_unset = ["http.https://github.com/.extraheader"]
        if strip_helpers:
            keys_to_unset.insert(0, "credential.helper")
        for key in keys_to_unset:
            unset = subprocess.run(
                ["git", "config", "--file", str(sandbox_global), "--unset-all", key],
                check=False,
                capture_output=True,
                timeout=_GIT_TIMEOUT_SECONDS,
            )
            if no_credentials and unset.returncode not in (0, _GIT_CONFIG_KEY_MISSING):
                raise OSError(f"git config --unset-all {key} failed (exit {unset.returncode})")
        env = {
            "GIT_CONFIG_GLOBAL": str(sandbox_global),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GH_PROMPT_DISABLED": "1",
        }
        if strip_helpers:
            env.update(
                {
                    "GIT_CONFIG_COUNT": "2",
                    "GIT_CONFIG_KEY_0": "credential.helper",
                    "GIT_CONFIG_VALUE_0": "",
                    "GIT_CONFIG_KEY_1": "http.https://github.com/.extraheader",
                    "GIT_CONFIG_VALUE_1": "",
                    "GH_CONFIG_DIR": str(sandbox_dir / "gh"),
                }
            )
            Path(env["GH_CONFIG_DIR"]).mkdir(mode=0o700)
        if github_token:
            askpass = sandbox_dir / "git-askpass.sh"
            askpass.write_text(
                "#!/bin/sh\n"
                'case "$1" in\n'
                "  *Username*) printf '%s\\n' x-access-token ;;\n"
                "  *Password*) printf '%s\\n' \"$GH_TOKEN\" ;;\n"
                "  *) printf '\\n' ;;\n"
                "esac\n",
                encoding="utf-8",
            )
            askpass.chmod(0o700)
            env["GIT_ASKPASS"] = str(askpass)
        elif not no_credentials:
            # #7166 / #7472 no-token fallback: keep the host gh auth chain
            # readable. The extraheader stays blanked even in this mode — it is
            # a secret carrier, unlike the gh hosts.yml / credential-helper
            # chain.
            env.update(
                {
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "http.https://github.com/.extraheader",
                    "GIT_CONFIG_VALUE_0": "",
                }
            )
            if host_gh_config_dir:
                env["GH_CONFIG_DIR"] = host_gh_config_dir
        return env
    except (OSError, subprocess.TimeoutExpired):
        if no_credentials:
            if sandbox_dir is not None:
                shutil.rmtree(sandbox_dir, ignore_errors=True)
            raise
        # Isolation failure must not re-open the operator's global Git config.
        # Losing the copied commit identity is safer than falling back to an
        # interactive credential helper.
        return {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }


def child_credential_env(
    raw: Mapping[str, str], provider: str, *, harness: str | None = None, driver_launcher: bool = False
) -> dict[str, str]:
    """Keep the seat's credentials; resolve GitHub identity only for workers.

    Ordinary launcher context remains available for stored login and driver
    hooks. build_agent_env further limits non-credential process context.
    Codex and GLM's derived Claude Code tokens are scoped to that transport.
    Driver launchers preserve raw GitHub variables without resolving or minting.
    Dispatched workers resolve identity as before and receive no signing key.
    """
    from .agent_github_identity import resolve_agent_github_identity
    from .kimi_admission import is_kimi_seat

    env = {}
    seat = _normalized_provider(provider)
    for name, value in raw.items():
        route_auth = name.upper() == "ANTHROPIC_AUTH_TOKEN" and seat in {"codex", "glm"} and harness == "claude-code"
        route_counter = (
            name == "CLAUDE_CODE_MAX_CONTEXT_TOKENS"
            and seat in {"glm", "kimi"}
            and harness == "claude-code"
            and value.isascii()
            and value.isdecimal()
        )
        driver_identity = driver_launcher and name in _DRIVER_GITHUB_IDENTITY_NAMES
        if (
            _is_provider_secret(name, provider)
            or route_auth
            or route_counter
            or driver_identity
            # Launcher paths can contain token-shaped task names. The dispatcher
            # applies its existing value filter again in build_agent_env.
            or name in {"PATH", "HOME", "PWD"}
            or _is_safe_value_name(name)
        ):
            env[name] = value
        elif _is_provider_safe_name(name, provider) and not _looks_sensitive_value(value):
            if not name.upper().startswith("ACPX_AUTH_") or value == "1":
                env[name] = value
        elif (
            (name in _CHILD_COUNTER_NAMES and value.isascii() and value.isdecimal())
            or (name in _CHILD_IDENTITY_NAMES and not _looks_sensitive_value(value))
            or (not _looks_sensitive_name(name) and not _looks_sensitive_value(value))
        ):
            env[name] = value

    identity = None if driver_launcher or is_kimi_seat(provider) else resolve_agent_github_identity(environment=raw)
    if identity is not None and identity.token:
        env["GH_TOKEN"] = identity.token
        env["LU_AGENT_GITHUB_IDENTITY_SOURCE"] = identity.source or "legacy"
    return env


def build_agent_env(
    *,
    provider: str,
    model: str | None = None,
    harness: str | None = None,
    overrides: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return a scrubbed env for a spawned agent CLI.

    ``overrides`` are applied to the parent environment before sanitization so
    adapter-supplied values are subject to the same policy as inherited values.
    ``model`` is the effective model selected for this invocation, never an
    inherited parent model. Cursor Auto or an absent model has Unknown identity.
    The runner applies explicit ``InvocationPlan.env_unsets`` after this call.
    A claude run's ``CLAUDE_CONFIG_DIR`` comes only from ``overrides``; when
    set it is the run's sole credential source (no Claude API key passes).
    For a Kimi seat it raises ``KimiAdmissionRefused`` when credential
    isolation (an empty ``GH_CONFIG_DIR``, the credential-helper and GitHub
    header resets) cannot be established: no partially isolated environment
    is returned.
    """
    raw = dict(os.environ)
    if _normalized_provider(provider) == "agy":
        # Only a receipt-recording review attempt's adapter override may carry
        # AGY_APP_DATA_DIR (#8617); an ambient export must not leak into an
        # ordinary dispatch.
        raw.pop("AGY_APP_DATA_DIR", None)
    if _normalized_provider(provider) == "kimi":
        # Only the KimiCC plan sets the Claude headless switches (#9690, #10083); an
        # ambient export (a dispatch started from a headless Claude worker's
        # shell) must not reach the native Kimi CLI.
        raw.pop("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS", None)
        raw.pop("CLAUDE_CODE_DISABLE_ADVISOR_TOOL", None)
    raw.update(overrides or {})
    raw.pop("LU_OPSEC_OVERRIDE", None)
    # Driver state belongs to the launcher session, never child/consult agents.
    raw.pop("LU_DRIVER_STATE_FILE", None)

    credentials = child_credential_env(raw, provider, harness=harness)
    env: dict[str, str] = {}
    for name, value in credentials.items():
        # Credential admission already happened in the shared child policy.
        if _looks_sensitive_name(name) and name not in _CHILD_COUNTER_NAMES | _CHILD_IDENTITY_NAMES:
            env[name] = value
            continue

        if _is_safe_value_name(name):
            env[name] = value
            continue
        if _looks_sensitive_value(value):
            continue
        if _is_provider_safe_name(name, provider) or (
            name == "ANTHROPIC_BASE_URL"
            and _normalized_provider(provider) in {"glm", "kimi"}
            and harness == "claude-code"
        ):
            if name.upper().startswith("ACPX_AUTH_") and value != "1":
                continue
            env[name] = value
            continue
        if _looks_sensitive_name(name):
            continue
        if _is_safe_name(name):
            env[name] = value

    pytest_plugins = _dispatch_pytest_plugins(raw)
    if pytest_plugins is None:
        env.pop("PYTEST_PLUGINS", None)
    else:
        env["PYTEST_PLUGINS"] = pytest_plugins

    pytest_pythonpath = _dispatch_pytest_pythonpath(raw)
    if pytest_pythonpath is None:
        env.pop("PYTHONPATH", None)
    else:
        env["PYTHONPATH"] = pytest_pythonpath

    login_dir = (overrides or {}).get(CLAUDE_CONFIG_DIR_ENV)
    if login_dir and _normalized_provider(provider) == "claude":
        # A labelled Claude account (#10619): the adapter's verified login
        # directory is the run's only credential source. The loop above never
        # admits a config directory, ambient or not, nor any Claude token
        # variable; drop the provider's API keys too. The path skips the
        # token-shape value filter, which would otherwise silently drop it.
        for name in [name for name in env if name.upper() in _PROVIDER_SECRET_ALLOWLIST["claude"]]:
            del env[name]
        env[CLAUDE_CONFIG_DIR_ENV] = login_dir

    if "PATH" not in env and "PATH" in raw and not _looks_sensitive_value(raw["PATH"]):
        env["PATH"] = raw["PATH"]
    if "HOME" not in env and "HOME" in raw and not _looks_sensitive_value(raw["HOME"]):
        env["HOME"] = raw["HOME"]

    # Git-config isolation (#2842) — applied last so it always wins; agents
    # cannot persist a repo-bricking core.bare write into system/global config.
    from .kimi_admission import is_kimi_seat

    # A Kimi seat never publishes: delegate commits and pushes its work after
    # the content check (kimi_boundary). It gets no GitHub identity, no
    # credential helper, an empty gh config, and every push URL rewritten below.
    no_push = is_kimi_seat(provider)
    token = credentials.get("GH_TOKEN")
    if no_push:
        for name in _PUSH_CREDENTIAL_NAMES:
            env.pop(name, None)

    try:
        isolation = _isolated_git_env(
            env.get("HOME") or raw.get("HOME"),
            token,
            host_gh_config_dir=None if no_push else usable_host_gh_config_dir(raw.get("GH_CONFIG_DIR")),
            no_credentials=no_push,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:  # raised only for a Kimi seat
        from .kimi_admission import KimiAdmissionRefused, format_refusal

        failure = f"a launch whose credential isolation could not be established ({exc})"
        raise KimiAdmissionRefused(format_refusal(provider, [failure])) from exc
    env.update(isolation)

    # Inherited GIT_* values are scrubbed above. Recreate both identities from
    # this lane after isolation so a driver's identity cannot leak to workers.
    from scripts.lib.git_identity import git_identity_env

    env.update(git_identity_env(provider, model))

    # Git reads this process-scoped config for ordinary child invocations,
    # including shell and Python subprocess wrappers. pushInsteadOf affects only
    # push; reviewers still need local clone/fetch for tests. Append after
    # identity isolation so its GIT_CONFIG_COUNT entries cannot replace this
    # rewrite. It prevents accidental pushes by ordinary git invocations, not
    # publication by code that edits its own environment. Reviewer-run Python,
    # scripts, or HTTP can publish with host credentials: a child can override
    # its git config to push, or call GitHub APIs directly. The deny list,
    # publish hook, and rewrite stop ordinary command forms only.
    if (
        _normalized_provider(provider) in {"claude", "grok"}
        and overrides
        and overrides.get("LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK") == "1"
    ):
        _append_push_rewrite(env, "file:///dev/null/claude-read-only/")
    if no_push:
        from .kimi_boundary import PUSH_BLOCK_URL

        _append_push_rewrite(env, f"{PUSH_BLOCK_URL}/")

    return env


def _append_push_rewrite(env: dict[str, str], target: str) -> None:
    """Rewrite every push URL to ``target`` through process-scoped git config."""
    count = int(env.get("GIT_CONFIG_COUNT", "0"))
    for prefix in ("https://", "http://", "ssh://", "git://", "git@", "file://", "/", "./", "../", "~"):
        env[f"GIT_CONFIG_KEY_{count}"] = f"url.{target}.pushInsteadOf"
        env[f"GIT_CONFIG_VALUE_{count}"] = prefix
        count += 1
    env["GIT_CONFIG_COUNT"] = str(count)
    env["GIT_TERMINAL_PROMPT"] = "0"


def _print_unneeded_env_var_names(provider: str, *, harness: str | None = None) -> int:
    """Print variable names the CLI child should omit for ``provider``."""
    for var_name in unneeded_env_var_names(os.environ, provider, harness=harness):
        if var_name.isidentifier():
            sys.stdout.write(f"{var_name}\n")
    return 0


# --- Labelled Claude account: settings inputs bound to the launch (#10619) ---


def _file_fingerprint(path: Path) -> str:
    """A content digest of ``path`` as Claude Code would read it, or why there is none."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC)
    except FileNotFoundError:
        return "absent"
    except OSError:
        return "unreadable"
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return "not_regular"
        digest = hashlib.sha256()
        while chunk := os.read(fd, 1 << 20):
            digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return "unreadable"
    finally:
        os.close(fd)


def _global_config_env_fingerprint(path: Path) -> str:
    """The global config's ``env`` map only: Claude Code rewrites the rest at every start."""
    fingerprint = _file_fingerprint(path)
    if len(fingerprint) != 64:
        return fingerprint
    try:
        data = json.loads(path.read_bytes())
    except (OSError, ValueError):
        return "invalid"
    env = data.get("env") if isinstance(data, dict) else "invalid"
    return hashlib.sha256(json.dumps(env, sort_keys=True).encode()).hexdigest()


def _checkout_settings_roots(cwd: Path) -> list[Path]:
    """Every directory whose ``.claude`` project or local settings a run in ``cwd`` may load.

    The working directory, its Git top level and, for a linked worktree, the
    main checkout (whose local file Claude Code also reads). Read from the
    ``.git`` files themselves, so the adapter and the launch guard find the
    same roots whatever ``git`` their ``PATH`` resolves.
    """
    roots = [cwd]
    for top in (cwd, *cwd.parents):
        marker = top / ".git"
        if marker.is_dir():
            roots.append(top)
            break
        if marker.is_file():
            roots.append(top)
            try:
                pointer = marker.read_text(encoding="utf-8").strip()
                gitdir = top / pointer.removeprefix("gitdir:").strip()
                common = gitdir / (gitdir / "commondir").read_text(encoding="utf-8").strip()
                roots.append(common.resolve().parent)
            except (OSError, ValueError):
                pass
            break
    return list(dict.fromkeys(roots))


def claude_labelled_inputs_digest(*, login_dir: str, cwd: Path, settings: str, setting_sources: str) -> str:
    """One digest over every settings input a labelled run's verification depended on (#10619).

    The run's ``--settings`` and ``--setting-sources`` values and login
    directory; that directory's user settings, global config ``env`` map,
    legacy global config and remote policy cache; managed policy; and the
    checkout's project and local settings files. The adapter binds it into
    the plan; ``run_claude_launch_guard`` recomputes it immediately before the
    CLI starts.
    """
    login, cwd = Path(login_dir), cwd.resolve()  # the guard sees the physical working directory
    managed_d = _CLAUDE_MANAGED_SETTINGS_DIR / "managed-settings.d"
    try:
        drop_ins = sorted(entry.name for entry in os.scandir(managed_d))
    except FileNotFoundError:
        drop_ins = []
    except OSError:
        drop_ins = ["<unreadable>"]
    inputs = {
        "settings": settings,
        "setting_sources": setting_sources,
        "login_dir": login_dir,
        "user_settings": _file_fingerprint(login / "settings.json"),
        "global_config_env": _global_config_env_fingerprint(login / ".claude.json"),
        "legacy_global_config": _file_fingerprint(login / CLAUDE_LEGACY_GLOBAL_CONFIG),
        "remote_settings": _file_fingerprint(login / _CLAUDE_REMOTE_SETTINGS),
        "managed": _file_fingerprint(_CLAUDE_MANAGED_SETTINGS_DIR / "managed-settings.json"),
        "managed_drop_ins": {name: _file_fingerprint(managed_d / name) for name in drop_ins},
        "checkout": {
            str(root / ".claude" / name): _file_fingerprint(root / ".claude" / name)
            for root in _checkout_settings_roots(cwd)
            for name in ("settings.json", "settings.local.json")
        },
    }
    return hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()


def _option_value(argv: list[str], name: str) -> str | None:
    """The value after ``name`` among ``argv``'s options (before any ``--``)."""
    options = argv[: argv.index("--")] if "--" in argv else argv
    return options[options.index(name) + 1] if name in options[:-1] else None


def run_claude_launch_guard(argv: list[str]) -> None:
    """Exec the labelled Claude CLI only if its bound settings inputs are unchanged (#10619).

    ``argv`` is ``<digest> -- <claude argv>``. Runs in the spawned process
    itself, so every launch (first spawn, retry, failover rebuild, resume)
    re-checks just before the CLI reads its files. On a mismatch it prints
    the registered code and exits ``CLAUDE_LAUNCH_GUARD_EXIT``; nothing else is
    printed.
    """
    digest, separator, cmd = (argv[0], argv[1], argv[2:]) if len(argv) > 2 else ("", "", [])
    login_dir = os.environ.get(CLAUDE_CONFIG_DIR_ENV)
    settings = _option_value(cmd, "--settings")
    sources = _option_value(cmd, "--setting-sources")
    if (
        separator != "--"
        or not cmd
        or not login_dir
        or settings is None
        or sources is None
        or claude_labelled_inputs_digest(
            login_dir=login_dir, cwd=Path.cwd(), settings=settings, setting_sources=sources
        )
        != digest
    ):
        os.write(2, b"CLAUDE_ACCOUNT_REFUSED: claude_account_settings_changed\n")
        os._exit(CLAUDE_LAUNCH_GUARD_EXIT)
    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    import argparse
    import sys

    # Launchers execute this file by path. Relative imports below need the
    # scripts package on sys.path and a package context.
    if __package__ in {None, ""}:
        _repo_dir = str(Path(__file__).resolve().parents[2])
        if _repo_dir not in sys.path:
            sys.path.insert(0, _repo_dir)
        _scripts_dir = str(Path(__file__).resolve().parents[1])
        if _scripts_dir not in sys.path:
            sys.path.insert(0, _scripts_dir)
        __package__ = "agent_runtime"

    parser = argparse.ArgumentParser(description="Print API-key names a child env must drop.")
    parser.add_argument("--provider", required=True)
    parser.add_argument("--harness", help="Effective child harness, including the Codex Claude Code route.")
    parser.add_argument(
        "--driver-launcher", action="store_true", help="Preserve the driver's raw GitHub identity without resolution."
    )
    parser.add_argument(
        "--exec", dest="command", nargs=argparse.REMAINDER, help="Exec the CLI with the shared seat credential policy."
    )
    parser.add_argument("--check-helper", action="store_true", help="Check the helper before supervising a child.")
    # Parse only our options. argparse's REMAINDER still interprets a later
    # literal --; the provider owns every argument after this boundary.
    arguments = sys.argv[1:]
    boundary = next((index for index, value in enumerate(arguments) if value in {"--exec", "--"}), len(arguments))
    args = parser.parse_args(arguments[:boundary])
    args.command = arguments[boundary + 1 :] if boundary < len(arguments) else None
    if args.check_helper or args.command:
        try:
            # Match the exec path's import closure before the shell claims a
            # lease. Import errors must not expose their exception diagnostics.
            from . import agent_github_identity, kimi_admission

            # Resolve the same members as the child policy without minting.
            _ = agent_github_identity.resolve_agent_github_identity, kimi_admission.is_kimi_seat

            if args.check_helper:
                raise SystemExit(0)
            child = child_credential_env(
                os.environ, args.provider, harness=args.harness, driver_launcher=args.driver_launcher
            )
            # exec preserves ignored signals; undo Python's startup defaults.
            for signal_name in ("SIGPIPE", "SIGXFSZ"):
                if (signal_number := getattr(signal, signal_name, None)) is not None:
                    signal.signal(signal_number, signal.SIG_DFL)
            os.execvpe(args.command[0], args.command, child)
        except Exception as exc:
            # Identity errors and executable diagnostics can contain secrets.
            sys.stderr.write(f"launcher child environment refused: {type(exc).__name__}\n")
            raise SystemExit(1) from None
    raise SystemExit(_print_unneeded_env_var_names(args.provider, harness=args.harness))
