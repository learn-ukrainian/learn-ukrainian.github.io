#!/usr/bin/env bash

launcher_adapter_validate() {
  case "$LC_HARNESS" in codex|claude-code) ;; *) launcher_error 'Codex supports --harness codex|claude-code.'; exit 2 ;; esac
}

launcher_codex_resolve_canonical_root() {
  local git_common_dir requested_root current_worktree record canonical_root=""
  git_common_dir="$(git -C "$LC_SESSION_ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || {
    launcher_error "could not resolve the Codex Git common directory."
    exit 1
  }
  requested_root="${CODEX_CANONICAL_REPO_ROOT:-}"

  if [ -n "$requested_root" ]; then
    canonical_root="$(cd "$requested_root" 2>/dev/null && pwd)" || {
      launcher_error "CODEX_CANONICAL_REPO_ROOT is not a directory: $requested_root"
      exit 1
    }
    if [ "$(git -C "$canonical_root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" != "$git_common_dir" ] \
      || [ "$(git -C "$canonical_root" rev-parse --show-toplevel 2>/dev/null)" != "$canonical_root" ]; then
      launcher_error "CODEX_CANONICAL_REPO_ROOT is not a checkout of this Git common directory."
      exit 1
    fi
  else
    while IFS= read -r -d '' record; do
      case "$record" in
        worktree\ *) current_worktree="${record#worktree }" ;;
        'branch refs/heads/main')
          if [ -n "${current_worktree:-}" ] \
            && [ "$(git -C "$current_worktree" rev-parse --show-toplevel 2>/dev/null)" = "$current_worktree" ]; then
            canonical_root="$current_worktree"
            break
          fi
          ;;
      esac
    done < <(git -C "$LC_SESSION_ROOT" worktree list --porcelain -z)
  fi

  if [ -z "$canonical_root" ] \
    && [ "$(git -C "$LC_SESSION_ROOT" branch --show-current 2>/dev/null)" = main ]; then
    canonical_root="$LC_SESSION_ROOT"
  fi
  if [ -z "$canonical_root" ]; then
    launcher_error "could not resolve a canonical main checkout for Codex."
    exit 1
  fi

  LC_CODEX_CANONICAL_ROOT="$canonical_root"
  export CODEX_CANONICAL_REPO_ROOT="$LC_CODEX_CANONICAL_ROOT"
}

launcher_codex_assert_primary_on_main() {
  local assertion="$LC_CODEX_CANONICAL_ROOT/scripts/guardrails/assert_primary_on_main.py"
  if [ -x "$LC_CODEX_CANONICAL_ROOT/.venv/bin/python" ] && [ -f "$assertion" ]; then
    if ! "$LC_CODEX_CANONICAL_ROOT/.venv/bin/python" "$assertion" \
        --cwd "$LC_CODEX_CANONICAL_ROOT" --quiet; then
      launcher_error "canonical primary checkout must be attached to main: $LC_CODEX_CANONICAL_ROOT"
      exit 1
    fi
  elif [ "$(git -C "$LC_CODEX_CANONICAL_ROOT" branch --show-current 2>/dev/null)" != main ]; then
    launcher_error "canonical checkout must be on main: $LC_CODEX_CANONICAL_ROOT"
    exit 1
  fi
}

launcher_codex_native_profile_preflight() {
  # Native Codex must supply a validated, trusted denominator before
  # SessionStart. The hook can observe the model too late to make a driver
  # lease safe on an ambiguous route.
  local deploy_failure_policy=fail
  launcher_codex_resolve_canonical_root
  launcher_codex_assert_primary_on_main
  export PROJECT_DIR="$LC_CODEX_CANONICAL_ROOT"

  # shellcheck source=scripts/lib/thread_rollover_link.sh
  source "$LC_ROOT/scripts/lib/thread_rollover_link.sh"
  clear_codex_launcher_rollover_env
  if [ "$LC_MODE" = interactive ]; then
    deploy_failure_policy=continue
  fi
  if [ "$LC_DRY_RUN" != 1 ]; then
    bootstrap_codex_checkout "$LC_CODEX_CANONICAL_ROOT" "$LC_SESSION_ROOT" "$deploy_failure_policy" || exit $?
  fi

  # shellcheck source=scripts/lib/profile_resolver.sh
  source "$LC_ROOT/scripts/lib/profile_resolver.sh"
  CLAUDE_PROFILE_RESOLVER_PYTHON="$LC_CODEX_CANONICAL_ROOT/.venv/bin/python"
  export CLAUDE_PROFILE_RESOLVER_PYTHON
  if ! resolve_context_profile native_codex "$LC_MODEL"; then
    launcher_error "failed to resolve the native Codex context profile."
    exit 1
  fi
  export CODEX_SESSION=1
  if [ "$LC_MODE" = driver ] && [ "$LEARN_UKRAINIAN_TRUSTED" != 1 ]; then
    LC_DRIVER_LEASE_ENABLED=0
  fi
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
    launcher_codex_native_profile_preflight
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
launcher_adapter_prelease() {
  if [ "$LC_HARNESS" != codex ] || [ "${LC_DRIVER_LEASE_ENABLED:-1}" != 1 ]; then
    return 0
  fi
  # shellcheck source=scripts/lib/thread_rollover_link.sh
  source "$LC_ROOT/scripts/lib/thread_rollover_link.sh"
  resolve_codex_pending_rollover "$LC_CODEX_CANONICAL_ROOT" "$SESSION_HANDOFF_AGENT"
}
launcher_adapter_canary() {
  local cmd=("$LC_ROOT/.venv/bin/python" -m scripts.session_canary.codex_lane)
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'codex adapter: would mint and bootstrap provider canary'; return 0; fi
  "${cmd[@]}" mint --epic "$LC_EPIC" && "${cmd[@]}" bootstrap --epic "$LC_EPIC"
}
launcher_adapter_exec() {
  local cmd
  if [ "$LC_HARNESS" = codex ]; then
    cmd=(
      codex --dangerously-bypass-approvals-and-sandbox --search
      -c 'tui.status_line=["model-with-reasoning","status","context-used","context-window-size","five-hour-limit","weekly-limit","git-branch","task-progress"]'
      -C "$LC_SESSION_ROOT" --model "$LC_MODEL"
    )
  else
    cmd=(claude --model "$LC_MODEL")
  fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; printf '%q ' "${cmd[@]}"; printf '\n'; return 0; fi
  exec "${cmd[@]}"
}
