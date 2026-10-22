#!/usr/bin/env bash

launcher_adapter_validate() {
  case "$LC_HARNESS" in
    grok)
      # shellcheck disable=SC2153 # LC_MODE is supplied by launcher_core.sh.
      if [ "$LC_MODE" = driver ]; then launcher_grok_validate_driver_args; fi
      ;;
    hermes)
      launcher_hermes_validate
      LC_MODEL="${LC_MODEL:-grok-4.7}"
      # shellcheck disable=SC2034 # consumed by shared Hermes execution
      LC_HERMES_PROVIDER=xai-oauth
      case "$LC_EFFORT" in
        ""|low|medium|high|xhigh) ;;
        *) launcher_error 'Grok/Hermes supports only low|medium|high|xhigh effort.'; exit 2 ;;
      esac
      ;;
    *) launcher_error 'Grok supports only --harness grok or --harness hermes.'; exit 2 ;;
  esac
}

launcher_grok_validate_driver_args() {
  # A bounded subset of `grok --help`, not a parser for Grok subcommands or
  # alternate prompt inputs. Keep caller text separate from option values.
  if [ "$LC_UNSEPARATED_PROVIDER_ARGS" = 1 ]; then
    launcher_error 'Native Grok driver provider options must follow --; put prompt text before it.'
    exit 2
  fi
  local arg option
  local -a args=("${LC_PROVIDER_ARGS[@]}")
  while [ "${#args[@]}" -gt 0 ]; do
    arg="${args[0]}"
    option="${arg%%=*}"
    case "$option" in
      --add-dir|--agent|--agents|--allow|--deny|--cwd|--debug-file|--disallowed-tools|--json-schema|--leader-socket|--max-turns|--output-format|--permission-mode|--rules|--session-id|--sandbox|--tools|--worktree-ref)
        if [ "$arg" = "$option" ]; then
          if [ "${#args[@]}" -lt 2 ] || [ -z "${args[1]}" ] || [[ "${args[1]}" = -* ]]; then
            launcher_error "Native Grok driver $option requires a value; use $option=VALUE for values starting with -."
            exit 2
          fi
          args=("${args[@]:1}")
        elif [ -z "${arg#*=}" ]; then
          launcher_error "Native Grok driver $option requires a nonempty value."
          exit 2
        fi
        ;;
      --resume|--worktree)
        if [ "$arg" = "$option" ] || [ -z "${arg#*=}" ]; then
          launcher_error "Native Grok driver requires $option=VALUE to avoid ambiguous optional values."
          exit 2
        fi
        ;;
      --always-approve|--continue|--debug|--disable-web-search|--fork-session|--fullscreen|--include-partial-messages|--minimal|--no-alt-screen|--no-plan|--no-subagents|--oauth|--restore-code|--verbatim)
        if [ "$arg" != "$option" ]; then
          launcher_error "Native Grok driver $option does not take a value."
          exit 2
        fi
        ;;
      *)
        launcher_error 'Unsupported native Grok driver provider argument. Put prompt text before --; use documented long session options after it, and launcher --model/--effort before it. Subcommands and alternate prompt inputs are unsupported.'
        exit 2
        ;;
    esac
    args=("${args[@]:1}")
  done
}
launcher_adapter_preflight() {
  if [ "$LC_HARNESS" = hermes ]; then launcher_hermes_preflight; return; fi
  LC_AUTH_SOURCE='grok-cli-oauth'
  launcher_require_binary grok 'Grok executable is unavailable.' 3 || exit $?
}
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'grok adapter: would run provider canary'; fi
  return 0
}
launcher_adapter_exec() {
  if [ "$LC_HARNESS" = hermes ]; then launcher_hermes_exec; return; fi
  local cmd=(grok)
  # Only pin --model / --reasoning-effort when the caller asked for them;
  # otherwise the Grok TUI keeps whatever was selected last in the session.
  if [ -n "${LC_MODEL:-}" ]; then
    cmd+=(--model "$LC_MODEL")
  fi
  if [ -n "${LC_EFFORT:-}" ]; then
    cmd+=(--reasoning-effort "$LC_EFFORT")
  fi
  # --rules appends to Grok's system prompt; native AGENTS.md loading is unproven.
  if [ -n "${LC_RULES_CORE:-}" ]; then
    cmd+=(--rules "$LC_RULES_CORE")
  fi
  if [ "$LC_MODE" = driver ]; then
    local prompt='' word separator=''
    for word in "${LC_CALLER_PROMPT_ARGS[@]}"; do
      prompt+="$separator$word"
      separator=' '
    done
    if [ "${#LC_CALLER_PROMPT_ARGS[@]}" -gt 0 ]; then prompt+=$'\n\n'; fi
    prompt+="$LC_DRIVER_PROMPT"
    # The provider separator protects even option-looking caller text. All
    # forwarded options retain their original argv boundaries before it.
    cmd+=("${LC_PROVIDER_ARGS[@]}" -- "$prompt")
  else
    cmd+=("${LC_FORWARD_ARGS[@]}")
  fi
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; launcher_print_argv "${cmd[@]}"; printf '\n'; return 0; fi
  launcher_exec_command "${cmd[@]}"
}
