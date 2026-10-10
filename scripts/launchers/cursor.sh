#!/usr/bin/env bash

launcher_adapter_validate() {
  [ "$LC_HARNESS" = cursor-agent ] || {
    launcher_error 'Cursor supports only --harness cursor-agent.'
    exit 2
  }
}
launcher_adapter_preflight() {
  LC_AUTH_SOURCE='cursor-cli-oauth'
  # Shell-side exception to resolve_cursor_agent_binary() (#9322): a shell
  # script cannot call the Python resolver. Require exactly cursor-agent and
  # exit non-zero when it is missing. A generic agent on PATH is a different
  # tool (Grok Build TUI) and must not claim this seat (#6969).
  LC_CURSOR_BIN=cursor-agent
  launcher_require_binary "$LC_CURSOR_BIN" 'Cursor agent executable (cursor-agent) is unavailable.' 3 || exit $?
}
launcher_adapter_canary() {
  # No launcher semantic canary exists for this adapter.
  # shellcheck disable=SC2034 # Read by launcher_bind_drive_epic in the shared core.
  LC_PROVIDER_CANARY_RAN=0
  echo 'cursor adapter: provider canary: not run'
  return 0
}
launcher_adapter_exec() {
  # launcher_validate_cursor_pin has certified LC_MODEL in every mode (#9274);
  # always pass it so cursor-agent cannot fall back to Auto or a Fast variant.
  local cmd=("$LC_CURSOR_BIN" --model "$LC_MODEL")
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
