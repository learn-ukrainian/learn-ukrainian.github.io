#!/usr/bin/env bash

launcher_adapter_validate() { [ "$LC_HARNESS" = agy ] || { launcher_error 'Gemini supports only --harness agy.'; exit 2; }; }
launcher_adapter_preflight() { LC_AUTH_SOURCE='agy-managed-auth'; launcher_require_binary agy 'AGY executable is unavailable.' 3 || exit $?; }
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'gemini adapter: would run provider canary'; fi
  return 0
}
launcher_adapter_exec() {
  local cmd=(agy --model "$LC_MODEL")
  local arg prompt_flag="" core_placed=0
  local -a rest=()
  # AGY has no system-prompt flag and its GEMINI.md loading is unproven, so the
  # rules core leads the initial prompt: prepended to a forwarded -i/-p value,
  # otherwise seeded with -i ahead of the driver binding (or an ack).
  for arg in "${LC_FORWARD_ARGS[@]}"; do
    if [ -n "${LC_DRIVER_PROMPT:-}" ] && [ "$arg" = "$LC_DRIVER_PROMPT" ]; then
      continue
    fi
    if [ -n "$prompt_flag" ]; then
      rest+=("$(rules_core_prefix "$arg")")
      prompt_flag=""
      core_placed=1
      continue
    fi
    case "$arg" in
      -i|--prompt-interactive|-p|--print|--prompt)
        if [ -n "${LC_RULES_CORE:-}" ] && [ "$core_placed" = 0 ]; then prompt_flag="$arg"; fi
        ;;
      -i=*|--prompt-interactive=*|-p=*|--print=*|--prompt=*)
        if [ -n "${LC_RULES_CORE:-}" ] && [ "$core_placed" = 0 ]; then
          arg="${arg%%=*}=$(rules_core_prefix "${arg#*=}")"
          core_placed=1
        fi
        ;;
    esac
    rest+=("$arg")
  done
  # agy rejects positional prompts ("Prompts are read only from -p/-i/stdin").
  # -i seeds the drive-epic binding and keeps the TUI interactive; -p would exit.
  if [ "$core_placed" = 0 ] && [ -n "${LC_RULES_CORE:-}" ]; then
    cmd+=(-i "$(rules_core_prefix "${LC_DRIVER_PROMPT:-}")")
  elif [ -n "${LC_DRIVER_PROMPT:-}" ]; then
    cmd+=(-i "$LC_DRIVER_PROMPT")
  fi
  cmd+=(${rest[@]+"${rest[@]}"})
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; launcher_print_argv "${cmd[@]}"; printf '\n'; return 0; fi
  launcher_exec_command "${cmd[@]}"
}
