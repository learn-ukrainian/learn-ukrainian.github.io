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
  # cursor-agent has no system-prompt flag and its AGENTS.md loading is
  # unproven: the rules core leads the drive-epic binding (or an ack).
  local arg core_placed=0
  if [ -n "${LC_RULES_CORE:-}" ]; then
    for arg in "${LC_FORWARD_ARGS[@]}"; do
      if [ "$core_placed" = 0 ] && [ -n "${LC_DRIVER_PROMPT:-}" ] && [ "$arg" = "$LC_DRIVER_PROMPT" ]; then
        cmd+=("$(rules_core_prefix "$arg")")
        core_placed=1
      else
        cmd+=("$arg")
      fi
    done
    if [ "$core_placed" = 0 ]; then
      cmd+=("$(rules_core_prefix "")")
    fi
  else
    cmd+=("${LC_FORWARD_ARGS[@]}")
  fi
  if [ "$LC_DRY_RUN" = 1 ]; then
    printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"
    launcher_print_argv "${cmd[@]}"
    printf '\n'
    return 0
  fi
  launcher_exec_command "${cmd[@]}"
}
