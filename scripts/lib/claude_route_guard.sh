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
  CLAUDE_CODE_USE_BEDROCK
  CLAUDE_CODE_USE_VERTEX
  CLAUDE_CODE_USE_FOUNDRY
  CLAUDE_CODE_USE_MANTLE
  CLAUDE_CODE_USE_ANTHROPIC_AWS
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
    else
      echo "Error: .venv/bin/python is required to inspect Claude settings at $settings_path." >&2
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
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
    "CLAUDE_CODE_USE_MANTLE",
    "CLAUDE_CODE_USE_ANTHROPIC_AWS",
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

# Refuse launch when any Claude settings scope that Claude Code actually loads
# would override process-scoped route env.
#
# Scopes inspected (user → project → local), matching
# https://code.claude.com/docs/en/settings :
#   1) ${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json
#   2) <project>/.claude/settings.json
#   3) <project>/.claude/settings.local.json
#
# CLAUDE_SETTINGS_PATH is NEVER trusted as a replacement for those real paths —
# an ambient redirect would let the guard inspect a clean decoy while Claude
# still loads the pinned scopes. If set, it is checked in addition only.
# Emergency only: CLAUDE_ROUTE_GUARD_ALLOW_SETTINGS_ENV=1.
assert_claude_settings_route_clean() {
  local route_name="${1:-alternate Claude route}"
  local project_dir="${2:-}"
  local config_dir="${CLAUDE_CONFIG_DIR:-${HOME}/.claude}"
  local settings_path conflict_output line git_common primary_root
  local -a settings_paths=()
  local -a conflicts=()
  local -a seen_paths=()
  local path_already_seen=0

  if [ "${CLAUDE_ROUTE_GUARD_ALLOW_SETTINGS_ENV:-0}" = "1" ]; then
    echo "Warning: CLAUDE_ROUTE_GUARD_ALLOW_SETTINGS_ENV=1 — settings.json env may override $route_name." >&2
    return 0
  fi

  settings_paths+=("${config_dir}/settings.json")
  if [ -n "$project_dir" ]; then
    settings_paths+=("${project_dir}/.claude/settings.json")
    settings_paths+=("${project_dir}/.claude/settings.local.json")
    # Linked worktrees: Claude Code resolves project/local settings against the
    # primary checkout (git common dir parent), not only the worktree path.
    # https://code.claude.com/docs/en/settings
    git_common="$(env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR \
      git -C "$project_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
    if [ -n "$git_common" ]; then
      primary_root="$(dirname "$git_common")"
      if [ -n "$primary_root" ] && [ "$primary_root" != "$project_dir" ]; then
        settings_paths+=("${primary_root}/.claude/settings.json")
        settings_paths+=("${primary_root}/.claude/settings.local.json")
      fi
    fi
  fi
  # Additional inspection only — never a substitute for the scopes above.
  if [ -n "${CLAUDE_SETTINGS_PATH:-}" ]; then
    settings_paths+=("$CLAUDE_SETTINGS_PATH")
  fi

  for settings_path in "${settings_paths[@]}"; do
    path_already_seen=0
    for seen in "${seen_paths[@]+"${seen_paths[@]}"}"; do
      if [ "$seen" = "$settings_path" ]; then
        path_already_seen=1
        break
      fi
    done
    if [ "$path_already_seen" = 1 ]; then
      continue
    fi
    seen_paths+=("$settings_path")

    conflict_output="$(claude_settings_conflicting_route_keys "$settings_path")" || return $?
    while IFS= read -r line; do
      [ -n "$line" ] && conflicts+=("$settings_path:$line")
    done <<< "$conflict_output"
  done

  if ((${#conflicts[@]} == 0)); then
    return 0
  fi

  echo "Error: $route_name refuses to launch because Claude settings pin route env keys:" >&2
  printf '  - %s\n' "${conflicts[@]}" >&2
  echo >&2
  echo "Claude Code merges user/project/local settings over process environment, so these" >&2
  echo "pins would hijack this launcher's allowlisted route. We do NOT rewrite those" >&2
  echo "files (config must stay operator-owned)." >&2
  echo >&2
  echo "Options:" >&2
  echo "  1) Remove those keys from the listed settings.json env blocks." >&2
  echo "  2) Point CLAUDE_CONFIG_DIR at a clean isolated directory and clear project/local pins." >&2
  echo "  3) Emergency only: CLAUDE_ROUTE_GUARD_ALLOW_SETTINGS_ENV=1 (not recommended)." >&2
  echo >&2
  echo "cc-switch and similar tools often write these keys — prefer project launchers" >&2
  echo "(./start-claude.sh, ./start-glmcc.sh, ./start-kimicc.sh) over global switches." >&2
  return 1
}
