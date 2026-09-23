#!/usr/bin/env bash

launcher_adapter_validate() {
  [ "$LC_HARNESS" = cursor-agent ] || {
    launcher_error 'Cursor supports only --harness cursor-agent.'
    exit 2
  }
}
launcher_adapter_preflight() {
  LC_AUTH_SOURCE='cursor-cli-oauth'
  # Require the unambiguous cursor-agent binary. A generic ``agent`` on PATH can
  # be a different tool (Grok Build TUI) and must not claim this seat (#6969).
  LC_CURSOR_BIN=cursor-agent
  launcher_require_binary "$LC_CURSOR_BIN" 'Cursor agent executable (cursor-agent) is unavailable.' 3 || exit $?
}
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'cursor adapter: would run provider canary'; fi
  return 0
}
launcher_adapter_exec() {
  local cmd=("$LC_CURSOR_BIN")
  # Driver defaults LC_MODEL to grok-4.7-high. Always pass a set model so
  # cursor-agent cannot fall back to Auto or a fast variant.
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
