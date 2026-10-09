#!/usr/bin/env bash

launcher_adapter_validate() {
  # shellcheck disable=SC2153 # LC_MODE is supplied by launcher_core.sh.
  if [ "$LC_MODE" = driver ] && [ "$LC_HARNESS" = grok ]; then
    local forwarded
    for forwarded in "${LC_FORWARD_ARGS[@]}"; do
      case "$forwarded" in
        --session-id|--session-id=*|-s|-s?*|--resume|--resume=*|-r|-r?*|--continue|-c|--fork-session)
          launcher_error 'Grok driver session identity is launcher-bound; session overrides and replay are unavailable.'
          exit 2
          ;;
      esac
    done
  fi
  case "$LC_HARNESS" in
    grok) ;;
    hermes)
      launcher_hermes_validate
      LC_MODEL="${LC_MODEL:-grok-4.7}"
      # shellcheck disable=SC2034 # consumed by shared Hermes execution
      LC_HERMES_PROVIDER=xai-oauth
      case "$LC_EFFORT" in
        ""|low|medium|high|xhigh) ;;
        *) launcher_error 'Grok/Hermes supports only low|medium|high|xhigh effort.'; exit 2 ;;
      esac
      ;;
    *) launcher_error 'Grok supports only --harness grok or --harness hermes.'; exit 2 ;;
  esac
}
launcher_adapter_preflight() {
  if [ "$LC_HARNESS" = hermes ]; then launcher_hermes_preflight; return; fi
  LC_AUTH_SOURCE='grok-cli-oauth'
  launcher_require_binary grok 'Grok executable is unavailable.' 3 || exit $?
}
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'grok adapter: would run provider canary'; fi
  return 0
}
launcher_adapter_exec() {
  # Clear an inherited parent binding even on an interactive/Hermes launch.
  unset LU_GROK_DRIVER_SESSION_ID LU_GROK_SOURCE_ROOT LU_GROK_PROJECT_PYTHON
  if [ "$LC_HARNESS" = hermes ]; then launcher_hermes_exec; return; fi
  local cmd=(grok)
  if [ "$LC_MODE" = driver ]; then
    export LU_GROK_SOURCE_ROOT="$LC_ROOT"
    export LU_GROK_PROJECT_PYTHON="$LC_DURABLE_HELPER_ROOT/.venv/bin/python"
    LU_GROK_DRIVER_SESSION_ID="$("$LU_GROK_PROJECT_PYTHON" -c 'import uuid; print(uuid.uuid4())')" || return 2
    export LU_GROK_DRIVER_SESSION_ID
    cmd+=(--session-id "$LU_GROK_DRIVER_SESSION_ID")
  fi
  # Only pin --model / --reasoning-effort when the caller asked for them;
  # otherwise the Grok TUI keeps whatever was selected last in the session.
  if [ -n "${LC_MODEL:-}" ]; then
    cmd+=(--model "$LC_MODEL")
  fi
  if [ -n "${LC_EFFORT:-}" ]; then
    cmd+=(--reasoning-effort "$LC_EFFORT")
  fi
  # --rules appends to Grok's system prompt; native AGENTS.md loading is unproven.
  if [ -n "${LC_RULES_CORE:-}" ]; then
    cmd+=(--rules "$LC_RULES_CORE")
  fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; launcher_print_argv "${cmd[@]}"; printf '\n'; return 0; fi
  launcher_exec_command "${cmd[@]}"
}
