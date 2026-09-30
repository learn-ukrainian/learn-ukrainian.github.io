#!/usr/bin/env bash

launcher_adapter_validate() {
  case "$LC_HARNESS" in kimi-code|claude-code) ;; *) launcher_error 'Kimi supports --harness kimi-code|claude-code.'; exit 2 ;; esac
  case "$LC_ENDPOINT" in coding|platform) ;; *) launcher_error 'Kimi endpoint must be coding or platform.'; exit 2 ;; esac
  if [ "$LC_HARNESS" = kimi-code ] && _kimi_forward_args_bind_agent; then
    launcher_error "Kimi Code starts fresh sessions only: $_KIMI_BOUND_ARG would restore or pick an agent without the rules core. Kimi seats take fresh web/UI/backend coding tasks; start a new session."
    exit 2
  fi
}
launcher_adapter_preflight() {
  if [ "$LC_HARNESS" = kimi-code ]; then
    LC_AUTH_SOURCE='kimi-code-oauth'
    launcher_require_binary kimi 'Kimi Code executable is unavailable.' 3 || exit $?
    # Catalog-backed alias resolution (review finding on #5958 r3): the native
    # kimi CLI rejects bare aliases like "k3" ("not configured in config.toml");
    # resolve every alias to the configured native model id before exec.
    local py
    py="$(launcher_project_python)" || exit 3
    if ! LC_MODEL="$("$py" "$LC_ROOT/scripts/review/model_catalog.py" \
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
# Kimi Code binds an agent at session creation, and the rules core rides in on
# that agent (--agent-file). A resumed session restores its old agent and a custom
# agent replaces ours, so neither would carry the core; the launcher refuses both.
_kimi_forward_args_bind_agent() {
  local arg
  _KIMI_BOUND_ARG=""
  for arg in ${LC_FORWARD_ARGS[@]+"${LC_FORWARD_ARGS[@]}"}; do
    case "$arg" in
      --agent|--agent=*|--agent-file|--agent-file=*|-c|--continue|-S|--session|--session=*|-r|--resume|--resume=*)
        _KIMI_BOUND_ARG="${arg%%=*}"
        return 0
        ;;
    esac
  done
  return 1
}
launcher_adapter_exec() {
  local cmd agent_file
  if [ "$LC_HARNESS" = kimi-code ]; then
    cmd=(kimi --model "$LC_MODEL")
    # The agent file renders Kimi's default prompt (${base_prompt}) and appends the core.
    if [ -n "${LC_RULES_CORE:-}" ]; then
      if agent_file="$(rules_core_kimi_agent_file "$LC_DURABLE_HELPER_ROOT/.venv/bin/python" "$LC_ROOT")"; then
        cmd+=(--agent-file "$agent_file")
      else
        rules_core_warn "Kimi agent file could not be written"
      fi
    fi
  else
    cmd=(claude --model "$LEAD_MODEL")
    if [ -n "${LC_RULES_CORE:-}" ]; then
      cmd+=(--append-system-prompt "$LC_RULES_CORE")
    fi
  fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; launcher_print_argv "${cmd[@]}"; printf '\n'; return 0; fi
  exec "${cmd[@]}"
}
