#!/usr/bin/env bash

launcher_adapter_validate() {
  [ "$LC_HARNESS" = claude-code ] || { launcher_error "Claude supports only --harness claude-code."; exit 2; }
}
launcher_adapter_preflight() {
  # shellcheck source=scripts/lib/profile_resolver.sh
  source "$LC_ROOT/scripts/lib/profile_resolver.sh"
  # Linked worktrees carry no venv (#6858); resolve through the validated
  # durable helper root (#9121).
  CLAUDE_PROFILE_RESOLVER_PYTHON="$LC_DURABLE_HELPER_ROOT/.venv/bin/python"
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
  local cmd=(claude)
  # Pin --model / --effort only when set: the driver defaults to Opus 5.5 at
  # high (launcher_defaults); interactive keeps the last TUI / user selection.
  if [ -n "${LC_MODEL:-}" ]; then
    cmd+=(--model "$LC_MODEL")
  fi
  if [ -n "${LC_EFFORT:-}" ]; then
    cmd+=(--effort "$LC_EFFORT")
  fi
  # CLI settings are scoped to this launch and cannot be inherited by children.
  # Print-mode invocations retain native compaction and the ordinary core prompt.
  local interactive=1 arg
  for arg in "${LC_FORWARD_ARGS[@]}"; do
    case "$arg" in -p|--print|--print=*) interactive=0 ;; esac
  done
  local system_prompt="${LC_RULES_CORE:-}"
  if [ "$interactive" = 1 ]; then
    local guard_settings="$LC_ROOT/agents_extensions/shared/settings/driver-compaction-guard.json"
    if [ ! -f "$guard_settings" ] || [ ! -r "$guard_settings" ]; then
      launcher_error "interactive Claude compaction guard settings are missing or unreadable."
      exit 2
    fi
    cmd+=(--settings "$guard_settings")
    system_prompt="${system_prompt:+$system_prompt$'\n'}Never compact a Claude driver; use thread-rollover to prepare the handoff, print HANDOFF-DONE <path>, and exit for a fresh launcher restart."
  fi
  if [ -n "$system_prompt" ]; then
    cmd+=(--append-system-prompt "$system_prompt")
  fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; launcher_print_argv "${cmd[@]}"; printf '\n'; return 0; fi
  launcher_exec_command "${cmd[@]}"
}
