#!/usr/bin/env bash

launcher_adapter_validate() {
  [ "$LC_HARNESS" = cursor-agent ] || {
    launcher_error 'Cursor supports only --harness cursor-agent.'
    exit 2
  }
}
launcher_adapter_preflight() {
  LC_AUTH_SOURCE='cursor-cli-oauth'
  # Prefer the unambiguous cursor-agent binary. A generic ``agent`` on PATH can
  # be a different tool (Grok Build TUI); mirror scripts/agent_runtime/adapters/cursor.py.
  if command -v cursor-agent >/dev/null 2>&1; then
    LC_CURSOR_BIN=cursor-agent
  elif command -v agent >/dev/null 2>&1; then
    LC_CURSOR_BIN=agent
  else
    LC_CURSOR_BIN=cursor-agent
  fi
  launcher_require_binary "$LC_CURSOR_BIN" 'Cursor agent executable (cursor-agent) is unavailable.' 3 || exit $?
}
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'cursor adapter: would run provider canary'; fi
  return 0
}
launcher_adapter_exec() {
  local cmd=("$LC_CURSOR_BIN")
  # Pin --model when set (default auto from launcher_defaults). Empty would keep
  # the last TUI selection, but the Cursor orchestrator seat defaults to Auto.
  if [ -n "${LC_MODEL:-}" ]; then
    cmd+=(--model "$LC_MODEL")
  fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then
    printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"
    printf '%q ' "${cmd[@]}"
    printf '\n'
    return 0
  fi
  launcher_exec_command "${cmd[@]}"
}
