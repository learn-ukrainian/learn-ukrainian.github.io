#!/usr/bin/env bash

launcher_adapter_validate() { [ "$LC_HARNESS" = agy ] || { launcher_error 'Gemini supports only --harness agy.'; exit 2; }; }
launcher_adapter_preflight() { LC_AUTH_SOURCE='agy-managed-auth'; launcher_require_binary agy 'AGY executable is unavailable.' 3 || exit $?; }
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'gemini adapter: would run provider canary'; fi
  return 0
}
launcher_adapter_exec() {
  local cmd=(agy --model "$LC_MODEL")
  local arg
  # agy rejects positional prompts ("Prompts are read only from -p/-i/stdin").
  # -i seeds the drive-epic binding and keeps the TUI interactive; -p would exit.
  if [ -n "${LC_DRIVER_PROMPT:-}" ]; then
    cmd+=(-i "$LC_DRIVER_PROMPT")
  fi
  # Driver seats must not hang on interactive tool approval (AgyAdapter
  # headless uses the same flag). Interactive start-gemini.sh stays gated.
  if [ "${LC_MODE:-}" = driver ]; then
    cmd+=(--dangerously-skip-permissions)
  fi
  for arg in "${LC_FORWARD_ARGS[@]}"; do
    if [ -n "${LC_DRIVER_PROMPT:-}" ] && [ "$arg" = "$LC_DRIVER_PROMPT" ]; then
      continue
    fi
    cmd+=("$arg")
  done
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; printf '%q ' "${cmd[@]}"; printf '\n'; return 0; fi
  launcher_exec_command "${cmd[@]}"
}
