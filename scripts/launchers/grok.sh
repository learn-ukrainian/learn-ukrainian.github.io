#!/usr/bin/env bash

launcher_adapter_validate() { [ "$LC_HARNESS" = grok ] || { launcher_error 'Grok supports only --harness grok.'; exit 2; }; }
launcher_adapter_preflight() { LC_AUTH_SOURCE='grok-cli-oauth'; launcher_require_binary grok 'Grok executable is unavailable.' 3 || exit $?; }
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'grok adapter: would run provider canary'; fi
  return 0
}
launcher_adapter_exec() {
  local cmd=(grok --model "$LC_MODEL")
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; printf '%q ' "${cmd[@]}"; printf '\n'; return 0; fi
  exec "${cmd[@]}"
}
