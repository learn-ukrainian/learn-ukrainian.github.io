#!/usr/bin/env bash
# Shared guards for interactive Claude Code alternate routes (Claudex, KimiCC).
#
# Contract:
# - NEVER mutate ~/.claude/settings.json or other Claude config files.
# - Process-scoped env vars are the only routing mechanism (Moonshot Method 1 /
#   CLIProxyAPI pattern). This keeps ./start-claude.sh on the original Anthropic
#   configuration when run in parallel.
# - If settings.json already contains an `env` block with route keys, those
#   values OVERRIDE process env in Claude Code — refuse until the operator
#   clears them (or points CLAUDE_CONFIG_DIR at an isolated directory).

# Keys that third-party tools (cc-switch, hand-edited settings) may pin into
# ~/.claude/settings.json env, silently hijacking native Claude and our launchers.
CLAUDE_ROUTE_ENV_KEYS=(
  ANTHROPIC_BASE_URL
  ANTHROPIC_API_KEY
  ANTHROPIC_AUTH_TOKEN
  ANTHROPIC_MODEL
  ANTHROPIC_SMALL_FAST_MODEL
  ANTHROPIC_DEFAULT_OPUS_MODEL
  ANTHROPIC_DEFAULT_OPUS_MODEL_NAME
  ANTHROPIC_DEFAULT_SONNET_MODEL
  ANTHROPIC_DEFAULT_SONNET_MODEL_NAME
  ANTHROPIC_DEFAULT_HAIKU_MODEL
  ANTHROPIC_DEFAULT_HAIKU_MODEL_NAME
  ANTHROPIC_DEFAULT_FABLE_MODEL
  ANTHROPIC_DEFAULT_FABLE_MODEL_NAME
  CLAUDE_CODE_SUBAGENT_MODEL
  ENABLE_TOOL_SEARCH
  CLAUDE_CODE_MAX_CONTEXT_TOKENS
  CLAUDE_CODE_AUTO_COMPACT_WINDOW
  CLAUDE_CODE_EFFORT_LEVEL
)

# Print space-separated route keys present under settings.json env (if any).
# Uses the project venv when available; falls back to python3.
claude_settings_conflicting_route_keys() {
  local settings_path="${1:-${HOME}/.claude/settings.json}"
  local py_bin="${CLAUDE_ROUTE_GUARD_PYTHON:-}"
  local keys_csv
  local key

  if [ ! -f "$settings_path" ]; then
    return 0
  fi

  if [ -z "$py_bin" ]; then
    if [ -n "${PROJECT_DIR:-}" ] && [ -x "${PROJECT_DIR}/.venv/bin/python" ]; then
      py_bin="${PROJECT_DIR}/.venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
      py_bin="$(command -v python3)"
    else
      echo "Error: python3 is required to inspect Claude settings at $settings_path." >&2
      return 2
    fi
  fi

  keys_csv="$(
    "$py_bin" - "$settings_path" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception as exc:  # noqa: BLE001 — surface parse failures to the shell
    print(f"PARSE_ERROR:{exc}", file=sys.stderr)
    sys.exit(3)

env = data.get("env")
if not isinstance(env, dict):
    sys.exit(0)

keys = [
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_SMALL_FAST_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL_NAME",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL_NAME",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL_NAME",
    "ANTHROPIC_DEFAULT_FABLE_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODEL_NAME",
    "CLAUDE_CODE_SUBAGENT_MODEL",
    "ENABLE_TOOL_SEARCH",
    "CLAUDE_CODE_MAX_CONTEXT_TOKENS",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
    "CLAUDE_CODE_EFFORT_LEVEL",
]
present = [k for k in keys if k in env]
print(" ".join(present))
PY
  )" || return $?

  # shellcheck disable=SC2086
  for key in $keys_csv; do
    printf '%s\n' "$key"
  done
}

# Refuse launch when settings.json would override process-scoped route env.
# Pass-through when CLAUDE_CONFIG_DIR is set to a non-default isolated dir, or
# when CLAUDE_ROUTE_GUARD_ALLOW_SETTINGS_ENV=1 (explicit operator override).
assert_claude_settings_route_clean() {
  local route_name="${1:-alternate Claude route}"
  local settings_path="${CLAUDE_SETTINGS_PATH:-${HOME}/.claude/settings.json}"
  local config_dir="${CLAUDE_CONFIG_DIR:-}"
  local conflicts=()
  local line

  if [ "${CLAUDE_ROUTE_GUARD_ALLOW_SETTINGS_ENV:-0}" = "1" ]; then
    echo "Warning: CLAUDE_ROUTE_GUARD_ALLOW_SETTINGS_ENV=1 — settings.json env may override $route_name." >&2
    return 0
  fi

  # Isolated config dir means we are not reading the operator's live settings.
  if [ -n "$config_dir" ] && [ "$config_dir" != "${HOME}/.claude" ]; then
    return 0
  fi

  while IFS= read -r line; do
    [ -n "$line" ] && conflicts+=("$line")
  done < <(claude_settings_conflicting_route_keys "$settings_path")

  if ((${#conflicts[@]} == 0)); then
    return 0
  fi

  echo "Error: $route_name refuses to launch because $settings_path pins route env keys:" >&2
  printf '  - %s\n' "${conflicts[@]}" >&2
  echo >&2
  echo "Claude Code applies settings.json env OVER process environment, so these" >&2
  echo "pins would hijack native Claude and this launcher. We do NOT rewrite that" >&2
  echo "file (original config must stay operator-owned)." >&2
  echo >&2
  echo "Options:" >&2
  echo "  1) Remove those keys from settings.json env (recommended; keep Method-1 env routing)." >&2
  echo "  2) Launch with an isolated config dir, e.g. CLAUDE_CONFIG_DIR=\$HOME/.claude-kimicc" >&2
  echo "  3) Emergency only: CLAUDE_ROUTE_GUARD_ALLOW_SETTINGS_ENV=1 (not recommended)." >&2
  echo >&2
  echo "cc-switch and similar tools often write these keys — prefer project launchers" >&2
  echo "(./start-claude.sh, ./start-claudex.sh, ./start-kimicc.sh) over global switches." >&2
  return 1
}
