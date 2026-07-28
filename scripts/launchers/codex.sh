#!/usr/bin/env bash

launcher_adapter_validate() {
  case "$LC_HARNESS" in codex|claude-code) ;; *) launcher_error 'Codex supports --harness codex|claude-code.'; exit 2 ;; esac
}
launcher_codex_transport_probe() {
  local probe=("$LC_ROOT/.venv/bin/python" -m scripts.orchestration.codex_transport_health probe --ttl-seconds "${CODEX_TRANSPORT_PROBE_TTL_SECONDS:-900}" --timeout-seconds "${CODEX_TRANSPORT_PROBE_TIMEOUT_SECONDS:-120}" --model "$LC_MODEL" --effort low --json)
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'codex adapter: would probe '; printf '%q ' "${probe[@]}"; printf '\n'; return 0; fi
  if ! "${probe[@]}"; then
    launcher_error 'Codex transport is degraded; do not retry Codex, route this cycle through the external fleet/epic roster.'
    exit 5
  fi
}
launcher_adapter_preflight() {
  if [ "$LC_HARNESS" = codex ]; then
    LC_AUTH_SOURCE='codex-cli-oauth'
    command -v codex >/dev/null 2>&1 || { launcher_error 'Codex executable is unavailable.'; exit 3; }
  else
    # shellcheck source=scripts/lib/codex_cc_route.sh
    source "$LC_ROOT/scripts/lib/codex_cc_route.sh"
    codex_cc_configure_route "$LC_MODEL" || exit $?
    LC_AUTH_SOURCE="$CODEX_CC_AUTH_SOURCE"
    command -v claude >/dev/null 2>&1 || { launcher_error 'Claude Code executable is unavailable for the Codex harness.'; exit 3; }
  fi
  if [ "$LC_MODE" = driver ]; then launcher_codex_transport_probe; fi
  return 0
}
launcher_adapter_canary() {
  local cmd=("$LC_ROOT/.venv/bin/python" -m scripts.session_canary.codex_lane)
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'codex adapter: would mint and bootstrap provider canary'; return 0; fi
  "${cmd[@]}" mint --epic "$LC_EPIC" && "${cmd[@]}" bootstrap --epic "$LC_EPIC"
}
launcher_adapter_exec() {
  local cmd
  if [ "$LC_HARNESS" = codex ]; then cmd=(codex --dangerously-bypass-approvals-and-sandbox --search -C "$LC_SESSION_ROOT" --model "$LC_MODEL"); else cmd=(claude --model "$LC_MODEL"); fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; printf '%q ' "${cmd[@]}"; printf '\n'; return 0; fi
  exec "${cmd[@]}"
}
