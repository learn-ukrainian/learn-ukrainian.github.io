#!/usr/bin/env bash

launcher_adapter_validate() {
  case "$LC_HARNESS" in kimi-code|claude-code) ;; *) launcher_error 'Kimi supports --harness kimi-code|claude-code.'; exit 2 ;; esac
  case "$LC_ENDPOINT" in coding|platform) ;; *) launcher_error 'Kimi endpoint must be coding or platform.'; exit 2 ;; esac
}
launcher_adapter_preflight() {
  if [ "$LC_HARNESS" = kimi-code ]; then
    LC_AUTH_SOURCE='kimi-code-oauth'
    launcher_require_binary kimi 'Kimi Code executable is unavailable.' 3 || exit $?
    # Catalog-backed alias resolution (review finding on #5958 r3): the native
    # kimi CLI rejects bare aliases like "k3" ("not configured in config.toml");
    # resolve every alias to the configured native model id before exec.
    if ! LC_MODEL="$("$LC_ROOT/.venv/bin/python" "$LC_ROOT/scripts/review/model_catalog.py" \
        --resolve-kimi-model "$LC_MODEL" --format native)"; then
      launcher_error "unknown --model '$LC_MODEL' (use k3-256k, k3, k2.7, k2.7-highspeed)."
      exit 2
    fi
    return
  fi
  # shellcheck source=scripts/lib/kimicc_route.sh
  source "$LC_ROOT/scripts/lib/kimicc_route.sh"
  ENDPOINT="$LC_ENDPOINT" MODEL_ALIAS="$LC_MODEL" ISOLATE_CONFIG="$LC_ISOLATE_CONFIG"
  export ENDPOINT MODEL_ALIAS ISOLATE_CONFIG
  kimicc_configure_route "$LC_SESSION_ROOT" "$LC_SESSION_ROOT" "$LC_DURABLE_HELPER_ROOT" || exit $?
  LC_AUTH_SOURCE="$AUTH_SOURCE"
  launcher_require_binary claude 'Claude Code executable is unavailable for the Kimi harness.' 3 || exit $?
}
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'kimi adapter: would run provider canary'; fi
  return 0
}
launcher_adapter_exec() {
  local cmd
  if [ "$LC_HARNESS" = kimi-code ]; then cmd=(kimi --model "$LC_MODEL"); else cmd=(claude --model "$LEAD_MODEL"); fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; printf '%q ' "${cmd[@]}"; printf '\n'; return 0; fi
  exec "${cmd[@]}"
}
