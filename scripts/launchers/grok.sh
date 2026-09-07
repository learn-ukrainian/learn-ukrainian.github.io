#!/usr/bin/env bash

launcher_adapter_validate() {
  case "$LC_HARNESS" in
    grok) ;;
    hermes)
      launcher_hermes_validate
      LC_MODEL="${LC_MODEL:-grok-4.6}"
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
  if [ "$LC_HARNESS" = hermes ]; then launcher_hermes_exec; return; fi
  local cmd=(grok)
  # Only pin --model / --reasoning-effort when the caller asked for them;
  # otherwise the Grok TUI keeps whatever was selected last in the session.
  if [ -n "${LC_MODEL:-}" ]; then
    cmd+=(--model "$LC_MODEL")
  fi
  if [ -n "${LC_EFFORT:-}" ]; then
    cmd+=(--reasoning-effort "$LC_EFFORT")
  fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; printf '%q ' "${cmd[@]}"; printf '\n'; return 0; fi
  launcher_exec_command "${cmd[@]}"
}
