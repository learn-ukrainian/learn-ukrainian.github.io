#!/usr/bin/env bash

launcher_adapter_validate() {
  [ "$LC_HARNESS" = claude-code ] || { launcher_error "Claude supports only --harness claude-code."; exit 2; }
}
launcher_adapter_preflight() {
  # shellcheck source=scripts/lib/profile_resolver.sh
  source "$LC_ROOT/scripts/lib/profile_resolver.sh"
  CLAUDE_PROFILE_RESOLVER_PYTHON="$LC_ROOT/.venv/bin/python"
  export CLAUDE_PROFILE_RESOLVER_PYTHON
  if ! resolve_context_profile native_claude "$LC_MODEL"; then
    launcher_error "could not resolve the native Claude profile for '$LC_MODEL'."
    exit 2
  fi
  if [ "$LEARN_UKRAINIAN_TRUSTED" != 1 ] || [ "$LEARN_UKRAINIAN_PROFILE_ID" != native_claude ]; then
    launcher_error "native Claude profile did not resolve to a trusted contract."
    exit 2
  fi
  # Native Claude must keep its own context behavior. The profile is used for
  # provenance and validation only; alternate-route capacity overrides remain
  # absent after launcher_core clears ambient state.
  unset CLAUDE_CODE_MAX_CONTEXT_TOKENS CLAUDE_CODE_AUTO_COMPACT_WINDOW
  LC_AUTH_SOURCE='claude-cli-oauth'
  launcher_require_binary claude 'Claude Code executable is unavailable.' 3 || exit $?
}
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'claude adapter: would run provider canary'; fi
  return 0
}
launcher_adapter_exec() {
  local cmd=(claude --model "$LC_MODEL")
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; printf '%q ' "${cmd[@]}"; printf '\n'; return 0; fi
  exec "${cmd[@]}"
}
