#!/usr/bin/env bash

launcher_adapter_validate() {
  [ "$LC_HARNESS" = claude-code ] || { launcher_error "Claude supports only --harness claude-code."; exit 2; }
  # Pure argument validation precedes provider preflight, lease acquisition,
  # and canary execution. Keep the exec-boundary check for direct adapter use.
  launcher_claude_forward_preflight "${LC_FORWARD_ARGS[@]}"
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

launcher_claude_forward_preflight() {
  # Audit: installed client 2.1.295 help and embedded option definitions.
  # Validate values before detecting print mode: --append-system-prompt --print
  # must be refused, rather than granting a headless exemption. Unknown syntax
  # fails closed; no user-supplied value is included in the error.
  local arg flag arity allowed value refused='' unknown=0 positional=0
  # The client scans the raw prefix for these switches, even when its option
  # parser would consume them as values. Inspect every element independently
  # of arity and print mode. Only the client's literal -- ends this scan;
  # everything following it remains unchanged prompt text.
  for arg in "$@"; do
    case "$arg" in
      --) break ;;
      --bare|--bare=*|--safe-mode|--safe-mode=*|--bg|--bg=*|--background|--background=*)
        launcher_error "forwarded ${arg%%=*} is refused in interactive Claude: hook-disabling switches are forbidden before the client --, to preserve launcher settings and compaction hooks."
        exit 2 ;;
    esac
  done
  LC_CLAUDE_INTERACTIVE=1
  while [ "$#" -gt 0 ]; do
    [ "$1" != -- ] || break # Only the literal client delimiter ends validation.
    arg="$1"; flag="${arg%%=*}"; arity=0; allowed=0
    shift
    case "$flag" in
      -p|--print) [ "$unknown" = 1 ] || LC_CLAUDE_INTERACTIVE=0; continue ;;
      --model|--effort|--append-system-prompt|--append-system-prompt-file|--agent|--session-id|--name|-n|--permission-mode)
        allowed=1; arity=1 ;;
      --resume|-r|--debug|-d) allowed=1; arity=optional ;;
      --continue|-c|--fork-session|--verbose|--dangerously-skip-permissions|--allow-dangerously-skip-permissions|--help|-h|--version|-v)
        allowed=1 ;;
      # Required and optional values from the full client surface, including
      # hidden flags, are consumed even on exempt headless invocations.
      --settings|--setting-sources|--managed-settings|--client-data-url|--project-config-root|--debug-file|--output-format|--json-schema|--input-format|--thinking|--thinking-display|--max-thinking-tokens|--max-turns|--max-budget-usd|--task-budget|--permission-prompt-tool|--permission-prompts|--system-prompt|--system-prompt-file|--system-prompt-snapshot|--append-subagent-system-prompt|--append-subagent-system-prompt-file|--plan-mode-instructions|--inherit-permission-mode|--watch-artifact|--watch-artifact-no-autoreact|--prefill|--deep-link-repo|--deep-link-last-fetch|--prefill-b64|--deep-link-cwd-b64|--resume-session-at|--resume-drops-turn|--rewind-files|--fallback-model|--workload|--agents|--plugin-dir|--plugin-dir-no-mcp|--plugin-url|--autocompact|--environment)
        arity=1 ;;
      --from-pr|--prompt-suggestions|--cloud|--teleport|--worktree|-w|--tmux) arity=optional ;;
      --allowedTools|--allowed-tools|--tools|--disallowedTools|--disallowed-tools|--mcp-config|--betas|--add-dir|--file)
        arity=variadic ;;
      --bare|--safe-mode|--restricted|--init|--init-only|--maintenance|--include-hook-events|--include-partial-messages|--forward-subagent-text|--session-mirror|--await-claim|--await-initialize|--replay-user-messages|--enable-auth-status|--exclude-dynamic-system-prompt-sections|--deep-link-origin|--no-session-persistence|--reply-on-resume|--ide|--desktop|--strict-mcp-config|--disable-slash-commands|--chrome|--no-chrome|--bg|--background|--brief|--ax-screen-reader) ;;
      -*)
        # The client's Boolean -c/-p clusters are also genuine print mode.
        # Optional/required-value short flags must not grant this exemption.
        if [[ "$arg" =~ ^-[cp]+$ && "$arg" == *p* ]]; then
          [ "$unknown" = 1 ] || LC_CLAUDE_INTERACTIVE=0
        else
          unknown=1
        fi
        ;;
      *)
        # A first positional command can attach to, or spawn, another session
        # instead of running the guarded invocation. A client -- makes it text.
        if [ "$positional" = 0 ]; then
          case "$arg" in
            agents|attach|auth|auto-mode|doctor|gateway|import|install|logs|mcp|plugin|plugins|purge|respawn|rm|setup-token|stop|kill|ultrareview|update|upgrade|daemon|remote-control|self-hosted-runner)
              [ -n "$refused" ] || refused="$arg" ;;
          esac
        fi
        positional=1
        continue ;;
    esac
    if [ "$allowed" = 0 ] && [ -z "$refused" ]; then
      # Only a syntactically safe option name can be quoted. In particular,
      # malformed flags containing whitespace/control characters stay private.
      if [[ "$flag" =~ ^--?[a-zA-Z][a-zA-Z0-9-]*$ ]]; then refused="$flag"; else refused='unrecognized option'; fi
    fi
    # An explicit option value must never look like another option. Optional
    # and variadic arguments without = consume only non-option tokens below;
    # bare --resume / -r therefore remain valid.
    value=''
    case "$arg" in
      *=*) [ "$arity" = 0 ] || value="${arg#*=}" ;;
      *) [ "$arity" != 1 ] || value="${1:-}" ;;
    esac
    if [[ "$value" == -* ]]; then
      launcher_error "forwarded $flag is refused in interactive Claude: option values must not start with '-', to preserve launcher settings and compaction hooks."
      exit 2
    fi
    if [ "$arity" = 1 ] && [ "$#" -eq 0 ] && [[ "$arg" != *=* ]]; then
      launcher_error "forwarded $flag is refused in interactive Claude: a value is required, to preserve launcher settings and compaction hooks."
      exit 2
    fi
    case "$arg" in *=*) continue ;; esac
    case "$arity" in
      1) [ "$#" -eq 0 ] || shift ;;
      optional) if [ "$#" -gt 0 ] && [[ "$1" != -* ]]; then shift; fi ;;
      variadic) while [ "$#" -gt 0 ] && [[ "$1" != -* ]]; do shift; done ;;
    esac
  done
  if [ "$LC_CLAUDE_INTERACTIVE" = 1 ] && [ -n "$refused" ]; then
    launcher_error "forwarded $refused is refused in interactive Claude: only audited session arguments are allowed, to preserve launcher settings and compaction hooks."
    exit 2
  fi
}

launcher_adapter_exec() {
  launcher_claude_forward_preflight "${LC_FORWARD_ARGS[@]}"
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
  local system_prompt="${LC_RULES_CORE:-}"
  if [ "$LC_CLAUDE_INTERACTIVE" = 1 ]; then
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
