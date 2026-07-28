#!/usr/bin/env bash

launcher_adapter_validate() {
  [ "$LC_HARNESS" = claude-code ] || { launcher_error 'GLM supports only --harness claude-code; native is unsupported.'; exit 2; }
  case "$LC_ENDPOINT" in coding|platform) ;; *) launcher_error 'GLM endpoint must be coding or platform.'; exit 2 ;; esac
}
launcher_adapter_preflight() {
  # shellcheck source=scripts/lib/glmcc_route.sh
  source "$LC_ROOT/scripts/lib/glmcc_route.sh"
  ENDPOINT="$LC_ENDPOINT" MODEL_ALIAS="$LC_MODEL" ISOLATE_CONFIG="$LC_ISOLATE_CONFIG"
  export ENDPOINT MODEL_ALIAS ISOLATE_CONFIG
  glmcc_configure_route "$LC_SESSION_ROOT" || exit $?
  LC_AUTH_SOURCE="$GLMCC_AUTH_SOURCE"
  launcher_require_binary claude 'Claude Code executable is unavailable for the GLM harness.' 3 || exit $?
}
launcher_adapter_canary() { return 0; }
launcher_adapter_exec() {
  local cmd=(claude --model "$LEAD_MODEL")
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; printf '%q ' "${cmd[@]}"; printf '\n'; return 0; fi
  exec "${cmd[@]}"
}
