#!/usr/bin/env bash

_glm_opencode_flash() {
  [ "${GLM_OPENCODE_FLASH:-0}" = 1 ]
}

launcher_adapter_validate() {
  if _glm_opencode_flash; then
    case "$LC_HARNESS" in
      opencode|claude-code) ;;
      native) launcher_error 'GLM supports only --harness claude-code; native is unsupported.'; exit 2 ;;
      *) launcher_error 'Flash OpenCode path rejects this harness; native is unsupported.'; exit 2 ;;
    esac
    return 0
  fi
  [ "$LC_HARNESS" = claude-code ] || { launcher_error 'GLM supports only --harness claude-code; native is unsupported.'; exit 2; }
  case "$LC_ENDPOINT" in coding|platform) ;; *) launcher_error 'GLM endpoint must be coding or platform.'; exit 2 ;; esac
}

launcher_adapter_preflight() {
  if _glm_opencode_flash; then
    LC_AUTH_SOURCE="opencode:zai-coding-plan"
    if [ "$LC_DRY_RUN" != 1 ]; then
      launcher_require_binary opencode 'OpenCode executable is unavailable for the GLM Flash harness.' 3 || exit $?
    fi
    return 0
  fi
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
  if _glm_opencode_flash; then
    local cmd=(opencode run --auto --format json -m zai-coding-plan/glm-5.3-flash)
    cmd+=("${LC_FORWARD_ARGS[@]}")
    if [ "$LC_DRY_RUN" = 1 ]; then
      printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"
      printf '%q ' "${cmd[@]}"
      printf '< /dev/null\n'
      return 0
    fi
    exec "${cmd[@]}" < /dev/null
  fi
  local cmd=(claude --model "$LEAD_MODEL")
  if [ -n "${LC_EFFORT:-}" ]; then
    cmd+=(--effort "$LC_EFFORT")
  fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; printf '%q ' "${cmd[@]}"; printf '\n'; return 0; fi
  exec "${cmd[@]}"
}
